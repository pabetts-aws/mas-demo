# Component Design — CSV to JSON CLI Tool

## Overview

A single small Python package with three internal components, each with one
clear responsibility, plus a thin executable entry point. The design keeps
conversion logic free of I/O and CLI concerns so it can be unit-tested
directly (Story 1–3, 5) while the CLI/I/O layer is tested separately for
routing and error behavior (Story 1 AC4, Story 4).

```
repo root/
├── csv2json/
│   ├── __init__.py        # package marker, re-exports public API
│   ├── converter.py        # Component A: CSV → records (pure logic)
│   ├── io_handler.py        # Component B: file/stdout I/O + error mapping
│   └── cli.py               # Component C: argument parsing + orchestration
├── run.py                   # Component D: executable entry point (thin)
├── test_converter.py         # unit tests for Component A
├── test_io_handler.py        # unit tests for Component B
├── test_cli.py                # tests for Component C (end-to-end argument
│                                behavior, exit codes, output routing)
├── docs/
│   └── usage.md              # usage document (authored in construction)
└── README.md                  # points to docs/usage.md
```

Rationale for this split is recorded in `docs/decisions.md`; this document
defines the boundaries and contracts developers implement against.

---

## Component A — `converter.py` (Conversion Core)

**Responsibility:** Pure transformation of already-open CSV text input into
an in-memory list of ordered dict records. No file I/O, no stdout, no
`sys.exit`. This is the only component that must satisfy FR1, FR2, FR3, and
the correctness half of NFR1 (Story 5's "no dropped/malformed rows").

**Public interface:**

```python
def csv_rows_to_records(csv_file: TextIO) -> list[dict[str, str]]:
    """
    Read CSV text from an open, readable text-mode file-like object whose
    first row is a header row, and return a list of dicts — one per data
    row — mapping header names to string values, in file order.

    Uses the header row to determine keys; if a data row has fewer or more
    fields than the header, csv.DictReader's standard behavior applies
    (missing trailing fields become "" via `restval=""`; this must be set
    explicitly, not left as None, to satisfy FR3 / Story 3 AC1-2).

    Empty cells (leading, middle, or trailing) are represented as "" in the
    resulting dict — never omitted, never null. This is the single
    documented rule (Story 3 AC1-2).

    Raises:
        csv.Error: on structurally malformed CSV that Python's csv module
            cannot parse (e.g. unterminated quote).
        ValueError: if the file is empty (no header row at all).
    """
```

**Design contract developers must follow:**
- Implemented using the standard-library `csv` module (`csv.DictReader`)
  configured with `restval=""` — never a hand-rolled parser. This directly
  satisfies FR2 (quoting, embedded commas/newlines, escaped quotes are the
  `csv` module's job, not ours) and removes an entire class of bugs.
- A completely blank line in the input is skipped (this is `csv.reader`'s
  default behavior for blank lines) — this is the "documented, consistent
  rule" required by Story 3 AC3. It must be stated in the usage doc.
- The function must not read the whole file into a `str` first if avoidable;
  pass the file object directly to `csv.DictReader` so the `csv` module can
  stream rows. The *result* is still fully materialized as a list (JSON
  arrays require the full structure), but parsing itself is streamed — this
  is the "reasonable streaming/parsing approach" required by Story 5 AC2.
- Row order in the output list must equal row order in the input (Story 1
  AC3) — `DictReader` iteration order already guarantees this; no
  re-ordering or sorting is permitted anywhere in this component.

---

## Component B — `io_handler.py` (I/O Boundary)

**Responsibility:** All contact with the filesystem and stdio. Owns opening
the input file, choosing between stdout and an output file for the result,
and translating OS-level failures into a small, well-defined set of typed
errors that Component C turns into exit codes and stderr messages. Nothing
in this component parses CSV or builds JSON structure — it moves bytes/text
across boundaries and serializes the final structure.

**Public interface:**

```python
class InputError(Exception):
    """Input file missing, unreadable, or not decodable as text."""

class OutputError(Exception):
    """Output path's directory missing/not writable, or write failed."""

def open_input(path: str) -> TextIO:
    """
    Open `path` for reading in text mode (utf-8, newline='' so csv module
    handles embedded newlines in quoted fields correctly — a required
    setting, not optional, for Story 2 AC2). Raise InputError with a
    human-readable message if the file does not exist or cannot be opened.
    """

def write_output(records: list[dict[str, str]], output_path: str | None) -> None:
    """
    Serialize `records` to a JSON array (json.dumps(records, indent=2)) and:
      - if output_path is None: write to stdout, and stdout carries ONLY the
        JSON (Story 4 AC1) — no logging/diagnostics mixed in;
      - else: write to the file at output_path, creating/truncating it.
        Raise OutputError (with the underlying OSError's message) if the
        parent directory does not exist or is not writable (Story 4 AC3).
    Never let JSON output share a stream with error/diagnostic text.
    """
```

**Design contract developers must follow:**
- All diagnostics, warnings, and error messages go to `stderr` exclusively.
  `stdout` is reserved for JSON output and nothing else, in both modes
  (Story 4 AC1–AC2).
- `InputError` / `OutputError` are the *only* exception types Component C is
  allowed to catch and translate into exit codes; any other exception
  (e.g. `csv.Error` from Component A) is caught at the CLI layer, not here.
- File open for input uses `newline=''` (required by the `csv` module docs
  for correct multi-line quoted-field handling — directly enables Story 2
  AC2).

---

## Component C — `cli.py` (Argument Parsing & Orchestration)

**Responsibility:** Define the command-line contract, call Components A and
B in sequence, and map every failure mode to a non-zero exit code plus a
clear stderr message. This is the only component allowed to call
`sys.exit`, so Components A and B stay unit-testable without a process
boundary.

**Command-line contract:**

```
usage: csv2json INPUT_CSV [-o OUTPUT_JSON | --output OUTPUT_JSON]

positional arguments:
  INPUT_CSV             path to the input CSV file (must have a header row)

optional arguments:
  -o, --output OUTPUT_JSON   path to write JSON output; if omitted, JSON is
                              written to stdout
```

**Public interface:**

```python
def build_parser() -> argparse.ArgumentParser: ...

def main(argv: list[str] | None = None) -> int:
    """
    Parse argv, run the input->convert->output pipeline, and return a
    process exit code (0 on success). Does not call sys.exit directly so
    it is testable by asserting on the return value; the `run.py` entry
    point is the only place that calls sys.exit(main()).

    Exit code contract:
      0  — success, full JSON array produced
      1  — input error (missing file, unreadable, not valid CSV structure)
      2  — output error (bad output path/permissions)
    All non-zero exits print a one-line, human-readable error to stderr
    and print nothing to stdout (Story 1 AC4, Story 4 AC3).
    """
```

**Design contract developers must follow:**
- `main()` never raises to its caller under expected failure conditions
  (missing file, bad CSV, bad output path); it must catch `InputError`,
  `OutputError`, and `csv.Error`/`ValueError` from Component A, print to
  stderr, and return the matching exit code. Unexpected exceptions are
  allowed to propagate (fail loudly rather than mask bugs).
- No business logic (parsing rules, empty-value rules) lives in this file —
  it is a coordinator only. If a developer finds themselves writing a CSV
  or JSON rule here, it belongs in Component A or B instead.

---

## Component D — `run.py` (Entry Point)

**Responsibility:** The only file that touches `sys.exit`/`sys.argv`
directly at import time.

```python
#!/usr/bin/env python3
import sys
from csv2json.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

Invocation for users: `python run.py sample.csv` or
`python run.py sample.csv -o out.json`.

---

## Data Flow

```
run.py
  → cli.main(argv)
      → build_parser().parse_args(argv)
      → io_handler.open_input(input_path)   ──► InputError on failure
      → converter.csv_rows_to_records(fh)   ──► csv.Error / ValueError on failure
      → io_handler.write_output(records, output_path) ──► OutputError on failure
      → return 0
  (any caught error above → print to stderr, return 1 or 2)
```

Every arrow in this diagram is a component boundary; no component reaches
"around" another (e.g. Component C never opens a file directly — it must go
through Component B; Component A never sees a path or stdout, only an
already-open file object).

## Traceability (Component → Requirement/Story)

| Component | Requirements | Stories |
|---|---|---|
| A: converter.py | FR1, FR2, FR3, C1, A1, NFR1 (correctness) | Story 1, 2, 3, 5 |
| B: io_handler.py | FR2 (multiline quoting via newline=''), FR4 | Story 2 (AC2), Story 4 |
| C: cli.py | FR1 (error handling), FR4, all error ACs | Story 1 (AC4), Story 4 (AC3) |
| D: run.py | — (wiring only) | — |

## Test Plan Mapping (informs, does not replace, code-gen stage)

| Test file | Covers |
|---|---|
| `test_converter.py` | T1 (basic conversion), T2 (quoting), T3 (empty values), part of T5 (10,000-row correctness + timing assertion) |
| `test_io_handler.py` | Story 4 AC1–AC3 (stdout vs file, bad output path), Story 2 AC2 (newline handling round-trip) |
| `test_cli.py` | Story 1 AC4 (missing/invalid input → exit code + stderr), Story 4 AC1–AC3 via `main()` return codes, full-pipeline smoke test satisfying the objective success criterion ("CLI converts a sample CSV... into a JSON array") |
