# Architecture Decisions — CSV to JSON CLI Tool

Each decision follows Context → Decision → Consequences. Decisions are
numbered ADR-1..ADR-n and are referenced by number from `docs/components.md`
where relevant.

---

## ADR-1: Language and runtime — Python 3, standard library only

**Context:** The tool must parse CSV (including RFC-4180-style quoting,
embedded commas/newlines, escaped quotes) and emit JSON, run as a CLI, and
be delivered with unit tests, in a sandbox with no guarantee of external
package installation beyond what's already available.

**Decision:** Implement in Python 3 using only the standard library
(`csv`, `json`, `argparse`, `sys`), test with `pytest`.

**Consequences:**
- No dependency-management risk (no `requirements.txt` resolution needed
  beyond `pytest` itself for the test runner).
- `csv` module already implements correct RFC-4180 quote/escape/embedded-
  delimiter handling, which directly satisfies FR2 without hand-rolled
  parsing — the single highest-risk area of a "write your own CSV parser"
  approach is eliminated.
- Reversible: swapping to another language later would require a full
  rewrite, but given the tool's small size this is a low-cost reversal if
  ever needed.

---

## ADR-2: Use `csv.DictReader` with `restval=""`, not a custom parser or
`csv.reader` + manual zip

**Context:** FR3 requires empty values (leading/middle/trailing, and rows
shorter than the header) to appear as `""` in every case, never omitted or
`null`, and requires header-name keys per FR1.

**Decision:** Use `csv.DictReader(fh, restval="")`. Do not use bare
`csv.reader` + manual `dict(zip(header, row))`, which would require
re-implementing DictReader's short-row/long-row handling ourselves and risk
subtle divergence from Story 3's rule.

**Consequences:**
- Header-to-value mapping and short-row padding are handled by a
  well-tested standard-library class, reducing the surface for bugs.
- A row *longer* than the header produces an extra key (`None`) by
  `DictReader` default (`restkey=None`); this is called out explicitly as
  an edge case to document in `docs/usage.md` during construction, rather
  than silently accepted — Component A's docstring must state the behavior.
- Easily reversible: the call site is one line in `converter.py`.

---

## ADR-3: Open input files with `newline=''`

**Context:** Story 2 AC2 requires that a quoted field containing an embedded
newline round-trips correctly. Python's `csv` module documentation
specifically requires the file be opened with `newline=''` so the module
itself controls line-ending/newline interpretation inside quoted fields;
opening in normal text mode causes `\r\n` translation that can corrupt
multi-line quoted fields on some platforms.

**Decision:** All input files are opened via `open(path, 'r', newline='',
encoding='utf-8')` inside Component B (`io_handler.open_input`) — never
opened ad hoc elsewhere.

**Consequences:**
- Correct behavior across platforms for the embedded-newline case is
  guaranteed by construction, not by hoping the OS defaults line up.
- Centralizing file-opening in one function means there is exactly one
  place to get this right, and one place to unit-test it.

---

## ADR-4: Separate conversion logic (Component A) from I/O (Component B)
from CLI orchestration (Component C)

**Context:** The quality bar requires unit tests for "the conversion
logic" specifically, plus CLI-level behavior (exit codes, stdout/stderr
routing) per Story 1 AC4 and Story 4. Mixing parsing, file I/O, and
`argparse`/`sys.exit` in one function/script makes the conversion logic
untestable without spinning up subprocesses for every test, which is slow
and brittle, and it blurs which code owns which failure mode.

**Decision:** Three components with one-way dependencies:
`cli.py → io_handler.py` and `cli.py → converter.py`; `converter.py` and
`io_handler.py` never import each other or `cli.py`. `converter.py` accepts
and returns only in-memory Python objects (file handle in, list of dicts
out) — no paths, no `sys.exit`. `io_handler.py` owns all filesystem/stdio
contact and raises two narrow exception types. `cli.py` is the only place
argument parsing and exit-code decisions happen.

**Consequences:**
- `test_converter.py` can test FR1/FR2/FR3/NFR1-correctness by passing
  `io.StringIO` objects directly — no temp files, no subprocess, fast and
  deterministic (supports the 10,000-row performance test, T5, running
  quickly as a pure in-memory unit test).
- Component boundaries double as test boundaries: a developer adding a new
  CSV edge case never needs to touch `cli.py`, and a developer adding a new
  output destination never needs to touch `converter.py`.
- Slightly more files than a single-script solution, but each file is
  small (well under 100 lines); this is judged the simplest architecture
  that still satisfies "every requirement maps to a test" without
  sacrificing testability. A single-file version was considered and
  rejected (ADR-5).

---

## ADR-5: Rejected alternative — single-file script

**Context:** A CSV→JSON CLI of this scope could be written as one script
with a `main()` containing `argparse`, file I/O, and conversion inline.

**Decision:** Rejected in favor of the three-component split (ADR-4).

**Consequences of rejecting it:** Slightly more files to navigate, but
unit-testing the conversion rules (FR2 quoting edge cases, FR3 empty-value
edge cases) would otherwise require either (a) invoking the whole CLI via
subprocess for every test case — slow and produces poor failure
diagnostics — or (b) monkeypatching `sys.exit`/stdout inside tests, which
is fragile. The split avoids both. This decision is easily reversible by
inlining the modules later if the tool's scope never grows.

---

## ADR-6: Exit code contract — 0 / 1 / 2, not exceptions, at the process
boundary

**Context:** Story 1 AC4 and Story 4 AC3 both require "exits with a
non-zero status and prints a clear error message" for distinct failure
classes (bad input vs. bad output destination). Priya's persona (CI/CD use)
specifically needs distinguishable, deterministic exit codes.

**Decision:** `cli.main()` returns an `int`: `0` success, `1` input-related
failure (missing file, unreadable, malformed CSV), `2` output-related
failure (bad output path/permissions). `run.py` is the only place that
converts this to `sys.exit()`. All error text goes to stderr; stdout is
never polluted with error text (needed for Story 4 AC1's stdout-piping use
case).

**Consequences:**
- CI pipelines (Priya) can branch on exit code without parsing stderr text.
- `main()` stays a plain function returning an `int`, so `test_cli.py` can
  assert on return values directly instead of using `pytest.raises(SystemExit)`
  or subprocess capture for every case — subprocess-based tests are
  reserved for the one end-to-end smoke test that exercises `run.py`
  itself, satisfying the objective success criterion.
- Extending the contract later (e.g. exit code 3 for a new failure class)
  is additive and backward compatible — reversible without breaking
  existing callers who only check "zero vs. non-zero."

---

## ADR-7: JSON output formatting

**Context:** FR1/FR4 require a JSON array of row objects, written to stdout
or a file. No requirement specifies pretty-printing vs. compact output.

**Decision:** Use `json.dumps(records, indent=2)` for both stdout and file
output, for human-readable diffs (useful for Sam's manual/ops use case and
for git-diffable fixture files in tests) at negligible performance cost
relative to the 10,000-row / 10-second budget (NFR1).

**Consequences:**
- Slightly larger output size than compact JSON; acceptable since NFR1's
  budget is generous relative to `json.dumps` throughput at this scale.
- If a future requirement demands compact output for pipe efficiency, this
  is a one-line change in `io_handler.write_output`, isolated from every
  other component — low-cost to reverse.

---

## ADR-8: No packaging/entry-point installation for this task

**Context:** The tool could be shipped as an installable package with a
`console_scripts` entry point (`pip install .` → `csv2json` command), or as
a script invoked directly with `python run.py`.

**Decision:** Ship as a plain script (`run.py`) plus an importable package
(`csv2json/`) invoked as `python run.py INPUT_CSV [-o OUT]`, with no
`setup.py`/`pyproject.toml` packaging metadata for this task's scope.

**Consequences:**
- Zero packaging overhead, nothing to install beyond `pytest` for running
  tests; matches "code lands in the task workspace root" quality
  criterion directly.
- If future scope requires a distributable CLI, adding `pyproject.toml`
  with a console-script entry point pointing at `csv2json.cli:main` is a
  additive, low-risk change — the `main(argv)` signature was designed
  (ADR-6) to be entry-point-compatible from day one.

---

## ADR-9: Performance approach for NFR1 (10,000 rows / 10 seconds)

**Context:** Story 5 requires 10,000-row conversion within 10 seconds
without sacrificing correctness, and without loading data in a way that
causes "excessive slowdown."

**Decision:** Rely on `csv.DictReader`'s native streaming iteration over
the file object (no manual line-splitting, no reading the whole file into
a string first) for the parse step; accept that the *result* list is fully
materialized in memory before serialization, since a JSON array output
requires the complete structure. Do not introduce chunked/incremental JSON
writing — at 10,000 rows this is well within comfortable memory and time
budgets on ordinary hardware, and adding streaming JSON output would add
complexity (ADR consequence trade-off) without a corresponding requirement.

**Consequences:**
- Simplicity preserved: no streaming JSON writer, no chunking logic to
  test or maintain.
- If a future requirement raises the row-count ceiling by orders of
  magnitude, this decision would need revisiting (streaming JSON array
  writer) — flagged here as the reversibility boundary of this decision.
- `test_converter.py` includes a generated 10,000-row fixture with a wall-
  clock assertion (`< 10s`) to keep this decision honest against T5/NFR1.

---

## Decision Traceability

| ADR | Requirement(s)/Story(ies) addressed |
|---|---|
| ADR-1 | FR1–FR4, NFR1 (feasibility) |
| ADR-2 | FR1, FR3, Story 1, Story 3 |
| ADR-3 | FR2, Story 2 AC2 |
| ADR-4 | All (testability of every FR/NFR) |
| ADR-5 | (rejected alternative, informs ADR-4) |
| ADR-6 | Story 1 AC4, Story 4 AC3 |
| ADR-7 | FR4, Story 4 |
| ADR-8 | Constraint: workspace-root code layout |
| ADR-9 | NFR1, Story 5 |
