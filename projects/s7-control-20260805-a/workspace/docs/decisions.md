# Architecture Decisions — CSV to JSON CLI Tool

Each decision follows Context → Decision → Consequences. Decisions are
numbered D1–D8 and are referenced from `docs/components.md`.

## D1 — Two components, not more, not fewer

**Context**: The tool has exactly two concerns that can vary independently:
"how does a user invoke this at a shell" and "how do CSV rows become JSON
objects." Requirements Stories 2/3/4/6 need conversion logic testable without
touching disk or argv; Stories 1/5 need process-boundary behavior (exit
codes, stdout vs. file) testable without re-testing conversion correctness.

**Decision**: Split into exactly two components — `Converter` (pure
transformation) and `CLI` (I/O wiring) — packaged as a small module, not a
framework of pluggable parsers/writers/formatters.

**Consequences**: Fast, dependency-free unit tests for the conversion logic;
CLI tests only need a couple of process-level cases. Reversible: if future
scope adds e.g. a TSV reader or an XML writer, a third component (`readers/`
or `writers/`) can be split out later without touching the boundary drawn
here. Adding more components now would violate "simplest architecture that
satisfies the requirements."

## D2 — Standard library only, no third-party dependencies

**Context**: C1 mandates Python. The conversion needed (CSV parsing with
quoting/empty-value handling, JSON emission) is fully covered by Python's
built-in `csv` and `json` modules — no header inference, schema validation,
or streaming-at-scale requirement exists in FR1–FR5/NFR1.

**Decision**: Use only `csv`, `json`, `argparse`, `sys`, `pathlib` from the
standard library. No `pandas`, no third-party CSV/JSON libraries, no CLI
framework (e.g. `click`/`typer`).

**Consequences**: Zero install friction, zero dependency-version risk, small
attack surface, fast test runs. Trade-off: less ergonomic CLI help text /
argument validation than `click`/`typer` would give, but `argparse` fully
covers FR1/FR5's contract. Easily reversible later if richer CLI UX is
required — swapping `argparse` for `click` only touches `cli.py`.

## D3 — Delegate CSV quoting/dialect handling entirely to `csv` module

**Context**: FR4 requires correct handling of quoted fields (including
embedded commas, escaped quotes, embedded newlines) and empty values.
Hand-rolling a CSV tokenizer is a well-known source of subtle bugs (this
mirrors persona Sam's stated pain with "ad-hoc parsing bugs").

**Decision**: Use `csv.DictReader` with the default Excel dialect
(comma-delimited, double-quote quoting, `QUOTE_MINIMAL`-compatible reading)
rather than writing custom parsing logic. Do not expose a `--delimiter` or
custom-dialect flag in v1 scope — not requested by any requirement.

**Consequences**: Correctness for FR4 is inherited from a battle-tested
standard-library implementation instead of re-implemented and re-tested from
scratch; our tests assert *behavior* (given this CSV text, get this JSON) not
tokenizer internals. If a future requirement needs custom delimiters, D3 is
revisited by exposing a dialect parameter on Converter — a backward-compatible,
reversible extension.

## D4 — Empty CSV field values serialize as JSON empty string, not null

**Context**: FR4 requires "handling ... empty values." CSV has no native way
to distinguish "empty string" from "null" — an empty field between two
commas (`a,,c`) is just zero characters. `csv.DictReader` yields `""` for
such a field.

**Decision**: An empty field present in a row is preserved as `""` in the
JSON output (not converted to JSON `null`). JSON `null` is reserved
exclusively for the distinct, rarer case of a **short row** — fewer fields
than headers — where `csv.DictReader` fills the missing trailing key(s) with
Python `None`, which `json.dumps` renders as `null`. This distinction is
documented in `docs/usage.md` so users aren't surprised by it.

**Consequences**: Deterministic, testable rule with a single line of
reasoning ("what did the CSV module actually give us"), rather than
inventing header-based schema/null-inference logic that no requirement asks
for. Test fixtures in `tests/test_converter.py` cover both the empty-field
(`""`) and short-row (`null`) cases explicitly so this decision is a checked
fact, not an assumption.

## D5 — Converter raises a dedicated exception; CLI translates it to an exit code

**Context**: FR2/FR3 imply the tool must behave sensibly (not crash with a
raw traceback) on structurally invalid input, e.g. a completely empty file
with no header row (violates assumption A1). The Converter component must
stay I/O-agnostic (D1), so it cannot itself decide exit codes or print error
messages.

**Decision**: `converter.py` defines and raises `CsvConversionError` for
conversion-level failures (currently: no header row present). `cli.py`
catches `CsvConversionError` and `OSError`/`FileNotFoundError` at the
boundary and maps each to a distinct process exit code and a one-line
message on stderr; it never lets an unhandled traceback escape `main()`.

**Consequences**: Converter's unit tests assert on exception type/message
directly (fast, no subprocess); CLI's tests assert on exit code + stderr
text via `main(argv)` return value. Clear, single place (`cli.py`) owns the
exception→exit-code mapping, so a developer extending error handling knows
exactly where to add a case.

## D6 — Exit code contract

**Context**: FR5/Story 5 require the tool to "emit ... with correct exit
codes" for scripting reliability (persona Sam's automation use case).

**Decision**: Fix exit codes as: `0` success, `1` input-file-not-found or
unreadable, `2` CSV conversion error (see D5). No other exit codes in v1
scope.

**Consequences**: Predictable, documented contract for shell scripts
(`if csv2json in.csv -o out.json; then ...`). Documented in
`docs/usage.md` and asserted directly in `tests/test_cli.py`.

## D7 — Output selection: stdout by default, `-o/--output` to write a file

**Context**: FR5 requires emitting to "stdout or an output file specified by
the user." Persona Dana wants pipeline-friendly behavior (i.e., stdout by
default so the tool composes with shell pipes); explicit opt-in file output
via a flag is the least surprising convention (mirrors common Unix CLI
tools).

**Decision**: No output flag → write JSON to stdout. `-o PATH`/`--output
PATH` → write JSON to that file (UTF-8, overwriting if it exists) and print
nothing to stdout on success.

**Consequences**: Matches Unix pipeline conventions Dana needs; simple,
single flag, no ambiguity about precedence since only one output mode is
ever active. Testable by asserting captured stdout in the no-flag case and
file contents in the `-o` case.

## D8 — Distribution as a runnable module with a console-script entry point

**Context**: The tool needs to be invocable both during development/testing
and, per the quality bar, have a documented "how to run" story.

**Decision**: Ship as an installable package (`pyproject.toml`) exposing
both `python -m csv2json ...` (via `__main__.py`) and a console-script entry
point `csv2json = csv2json.cli:main` installable via `pip install -e .`.
Tests invoke `cli.main()` in-process (fast, no subprocess) rather than
shelling out; `docs/usage.md` additionally documents the installed-CLI
invocation for end users.

**Consequences**: Keeps the test suite fast and deterministic (no
subprocess/PATH concerns) while still giving users/persona Sam a real,
installable command-line tool consistent with the "small CLI tool" framing
of the task.
