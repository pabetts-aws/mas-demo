# Architecture Decisions — Text Statistics CLI Tool

Each decision follows: Context → Decision → Consequences. Decisions are
numbered D1..D10 and referenced from `docs/components.md`.

---

## D1: Language, runtime, and dependency footprint

**Context:** C1 requires a "small CLI application"; NFR1 requires unit
tests; no other technology constraint was given.

**Decision:** Implement in Python 3 (stdlib only: `argparse`, `json`,
`dataclasses`, `sys`, `pathlib`), tested with `pytest`. No third-party
runtime dependency (no `click`, no `typer`).

**Consequences:**
- Zero install footprint beyond Python + pytest; satisfies "small".
- `argparse` gives free, well-tested usage-error behavior (exit code 2,
  stderr usage message) which directly satisfies Story 5 without custom code.
- Reversible: swapping to `click`/`typer` later would only touch `cli.py`.

---

## D2: Package layout — pure logic separated from I/O and wiring

**Context:** NFR1 demands unit tests for "the counting and JSON output
logic" specifically, implying that logic must be testable in isolation
from file I/O, argv, and process exit codes.

**Decision:** Split into four modules with one-directional dependencies:
`counter.py` (pure counting) → `formatting.py` (pure presentation, depends
only on `counter.Stats`) → `cli.py` (I/O + argv + exit codes, depends on
both) → `__main__.py` (process wiring, depends on `cli.py`).

**Consequences:**
- `test_counter.py` and `test_formatting.py` need no filesystem or
  subprocess fixtures — fast, deterministic unit tests.
- `cli.py` is the only place that can violate testability by touching
  real I/O; kept intentionally thin so `test_cli.py` stays manageable.
- Two components (`counter`, `formatting`) never need to change together
  with argv parsing — confirms they're separate components per the
  "least coupling" principle, not just files split for style.

---

## D3: Where files land in the workspace

**Context:** Quality criteria require code "in the task workspace root
with tests alongside."

**Decision:** `textstats/` package and `tests/` directory both live at the
task workspace root (not nested under `src/`), alongside `pyproject.toml`
and `docs/`.

**Consequences:**
- `pytest` run from the workspace root discovers `tests/` with no config
  beyond a minimal `pyproject.toml`/`pytest.ini` needed for `import
  textstats` to resolve (addressed by an editable/local install or a
  `pyproject.toml` `[tool.pytest.ini_options]` `pythonpath` setting during
  construction).
- Simpler than a `src/` layout for a tool this small; reversible later if
  the tool grows a public distribution story.

---

## D4: Counting rules (must be exact, testable, and documented)

**Context:** FR1 and Story 1 require line/word/char counts with a defined
rule for files without a trailing newline; Story 6 requires tests for
empty files, no-trailing-newline files, and whitespace-only files.

**Decision:**
- **Lines** = `len(text.splitlines())`. This counts a final line even when
  it has no trailing `\n` (so `"a\nb"` and `"a\nb\n"` both count as 2
  lines), and an empty file counts as 0 lines. This is chosen over a raw
  `\n`-count (which would under-count a trailing-newline-less final line)
  because it matches the plain-English notion of "how many lines of text
  are here," and gives one unambiguous, easy-to-test rule.
- **Words** = `len(text.split())` (Python's whitespace-split with no
  arguments): splits on any run of whitespace, ignores leading/trailing
  whitespace, so a whitespace-only file counts as 0 words.
- **Chars** = `len(text)`: raw character count of the file's text content
  exactly as decoded, including all whitespace and newline characters.

**Consequences:**
- Differs slightly from POSIX `wc` (`wc -l` counts `\n` bytes, not logical
  lines), which is a deliberate, documented deviation — this tool is not
  claiming `wc` compatibility, only internal consistency, and this must be
  stated in `docs/usage.md`.
- Fully deterministic and stdlib-only; no locale or encoding ambiguity for
  the tokenization rule.
- Each rule has a direct, one-to-one unit test case named for the edge
  case it covers (empty / no-trailing-newline / whitespace-only), per
  Story 6's acceptance criteria.

---

## D5: JSON output schema

**Context:** FR3 and Story 3 require `--json` to emit "the same numbers"
as a single valid JSON document on stdout, with per-file entries and a
totals entry when multiple files are given, and no totals key required
for a single file.

**Decision:** Fixed schema:

```json
{
  "files": [
    {"file": "a.txt", "lines": 3, "words": 10, "chars": 42},
    {"file": "b.txt", "lines": 1, "words": 2, "chars": 8}
  ],
  "total": {"lines": 4, "words": 12, "chars": 50}
}
```

- `files` is always present, always an array, always in the order files
  were given on argv.
- `total` key is present **only when more than one file was given**; for
  a single file it is omitted entirely (chosen over duplicating the
  single file's numbers, to keep the schema's meaning of `total`
  unambiguous: "present iff more than one file contributed to it").
- Field names are fixed lowercase strings (`file`, `lines`, `words`,
  `chars`, `files`, `total`) — no configurability.

**Consequences:**
- `json.dumps` of a plain dict/list structure built from `Stats` — no
  custom encoder needed.
- Automation (Priya persona) can rely on `total` presence/absence as a
  signal for "was this a multi-file run," matching Story 3's acceptance
  criterion precisely.
- This is a public contract once shipped; changing field names later is a
  breaking change for consumers — flagged as the one output-format
  decision worth getting right now rather than iterating post-hoc.

---

## D6: Human-readable output format

**Context:** FR1/FR2 and Stories 1–2 require per-file rows and a clearly
labeled totals row only when multiple files are given; Sam persona needs
this to be readable without technical parsing.

**Decision:** A simple space-aligned table with a header row:

```
File      Lines  Words  Chars
a.txt         3     10     42
b.txt         1      2      8
total         4     12     50
```

Column order is always `Lines, Words, Chars` (matches JSON field order
and FR1's stated order "line, word, and character counts"). The `total`
row is appended only when `len(files) > 1`, uses the literal label
`total`, and is otherwise formatted identically to file rows (no special
divider) to keep the formatter simple and the output easy to grep.

**Consequences:**
- No third-party table-formatting library needed; plain `str.format`
  with computed column widths.
- Deterministic string output makes `test_formatting.py` simple exact-
  match assertions rather than fuzzy pattern matching.

---

## D7: Exit codes and error-channel discipline

**Context:** FR4 and Stories 4–5 require a clear error message and a
non-zero exit code for missing files, and a usage error for zero
arguments; Story 4 also requires error text to go to stderr even in
`--json` mode so stdout stays parseable.

**Decision:** Three distinct outcomes:

| Condition | stdout | stderr | Exit code |
|---|---|---|---|
| All files read successfully | table or JSON | (nothing) | `0` |
| Zero file arguments given | (nothing) | argparse usage message | `2` |
| One or more files missing | (nothing) | one line per missing file: `textstats: error: file not found: <path>` | `1` |

`cli.main(argv) -> int` never calls `sys.exit` itself; it returns the
code, and only `__main__.py` (and the packaged console-script wrapper)
calls `sys.exit(main())`. This keeps `main` directly unit-testable (call
it, assert the returned int and captured stdout/stderr) without needing
`pytest.raises(SystemExit)` or subprocess spawning for most cases.

**Consequences:**
- Code `2` for usage errors vs. `1` for missing-file errors gives callers
  a way to distinguish "you used it wrong" from "the input didn't exist"
  if they ever care to — a low-cost, easily-reversible convention.
- Mixed existing/missing file lists always fail closed (report all
  missing paths, exit 1, print nothing to stdout) — never partial
  success, satisfying Story 4's explicit acceptance criterion.
- stdout is guaranteed parseable-JSON-or-nothing when `--json` is passed
  and the process exits 0; any error text is guaranteed to be on stderr,
  regardless of `--json`, satisfying automation needs (Priya persona).

---

## D8: Totals computed only when multiple files are given

**Context:** Story 2's acceptance criterion: "When exactly one file is
given, no totals row is shown," and Story 3's: "no totals key required"
for a single file.

**Decision:** `cli.py` computes `total_stats(...)` and passes a non-None
total to the formatters **only when `len(files) > 1`**; for exactly one
file it passes `None`, and both formatters treat `None` as "omit the
totals row/key" uniformly.

**Consequences:**
- Single source of truth for the "is this multi-file" branch lives in
  `cli.py`, not duplicated in both formatter functions.
- `formatting.py` functions have one simple, testable contract: totals
  shown iff `total is not None` — no need for either formatter to know
  about `len(files)` directly.

---

## D9: Encoding handling

**Context:** A1 assumes UTF-8-encoded input files; no requirement covers
non-UTF-8 or binary files.

**Decision:** `read_file_text` opens files with `encoding="utf-8"` and no
explicit error handler override (Python default `errors="strict"`), so a
non-UTF-8 file raises `UnicodeDecodeError`. This is treated the same as
other unexpected read errors — not specifically required or tested by any
story, so it is explicitly out of scope for special-casing; it will
surface as an uncaught exception with a non-zero exit rather than a
clean, tested error path. This gap is called out in `docs/usage.md`
rather than silently ignored.

**Consequences:**
- No silent data corruption from a lenient decode; matches A1's stated
  assumption instead of trying to guess encodings.
- If a future requirement demands graceful handling of non-UTF-8 input,
  this is a small, isolated, reversible change confined to
  `read_file_text`.

---

## D10: Test strategy and framework

**Context:** NFR1 and Story 6 require unit tests for counting and JSON
logic, gated on `pytest` passing with zero failures (D10 of the platform
principles: build/test results are the only success signal).

**Decision:** `pytest` as the sole test runner; tests split by component
per `docs/components.md`'s test-suite table. `test_cli.py` calls
`cli.main(argv)` directly (in-process) using `capsys`/`tmp_path` fixtures
rather than spawning subprocesses, except optionally one smoke test that
does invoke the packaged console script end-to-end to prove wiring
(D2/D7) actually works outside the test harness.

**Consequences:**
- Fast test suite (no subprocess overhead for the bulk of cases).
- Every requirement (FR1–FR4, NFR1) has at least one directly-traceable
  test file/case per the table in `docs/components.md`, satisfying the
  "every requirement maps to at least one test" quality bar.
- The one subprocess-based smoke test (if included) is the only place a
  real process exit code is observed, closing the gap between "main()
  returns the right int" and "the OS process actually exits with it."
