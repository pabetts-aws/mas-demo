# Component Design — CSV to JSON CLI Tool

## Overview

The tool is a single-purpose command-line utility implemented in Python,
using only the standard library (`csv`, `json`, `argparse`, `sys`). Given the
small scope (convert CSV to JSON, no persistence, no network, no concurrency)
a single-process, single-package design with a clear internal module
boundary between **CLI/IO concerns** and **conversion logic** is sufficient.
This boundary exists specifically so the conversion logic can be unit-tested
in isolation from process argv/stdio (NFR1, Story 6).

Package layout (workspace root):

```
csv2json/
  __init__.py
  converter.py     # pure conversion logic (Component: Converter)
  cli.py           # argument parsing, I/O wiring (Component: CLI)
  __main__.py      # `python -m csv2json` entry point
tests/
  test_converter.py
  test_cli.py
  fixtures/
    *.csv
setup.cfg / pyproject.toml   # packaging + console-script entry point
docs/
  usage.md
```

## Component: Converter (`csv2json/converter.py`)

**Responsibility**: Pure, deterministic transformation of CSV text/rows into
a JSON-serializable list of row objects. No file I/O, no argv, no stdout —
this is what makes it independently unit-testable per NFR1/Story 6.

**Public interface**:

```python
def csv_rows_to_json_records(reader: csv.DictReader) -> list[dict[str, str | None]]:
    """Consume a csv.DictReader and return a list of plain dicts.

    - Preserves column order via the header row (dict insertion order).
    - Empty string fields are preserved as empty strings "" (see Decision D4).
    - Rows are returned in the same order as they appear in the source.
    - A header-only CSV (no data rows) returns [].
    """

def convert_csv_text_to_json_string(csv_text: str, *, indent: int | None = 2) -> str:
    """Convenience wrapper: parse csv_text (must have header row) and
    return a JSON string (via json.dumps) of the row-object array.
    Raises CsvConversionError on malformed CSV structural issues that
    csv.DictReader itself cannot silently recover from (see Decision D5).
    """

class CsvConversionError(Exception):
    """Raised for conversion-level failures (e.g. unreadable/empty header)."""
```

**Traces to**: FR2, FR3, FR4, NFR1 (Stories 2, 3, 4, 6).

**Failure modes owned here**:
- Empty file / missing header row → `CsvConversionError("CSV has no header row")`.
- Quoting/newline handling is delegated entirely to Python's `csv` module
  (RFC 4180-style dialect), not reimplemented — see Decision D3.

## Component: CLI (`csv2json/cli.py`, `csv2json/__main__.py`)

**Responsibility**: Process-boundary concerns only: argument parsing, opening
the input file, choosing stdout vs. output-file, writing bytes/text, setting
the process exit code. Contains no CSV/JSON transformation logic itself —
it calls into Converter.

**Public interface**:

```python
def build_arg_parser() -> argparse.ArgumentParser: ...

def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns a process exit code (0 success, non-zero on error).
    Does not call sys.exit() itself, so it stays testable in-process
    (tests call main([...]) and assert on the returned code + captured output)."""
```

**CLI contract**:

| Argument | Required | Meaning |
|---|---|---|
| `input_path` (positional) | Yes | Path to the input CSV file (FR1). |
| `-o, --output PATH` | No | Output file path. If omitted, JSON is written to stdout (FR5). |
| `--indent N` | No (default 2) | JSON pretty-print indent; `--indent 0` disables indentation. |

**Traces to**: FR1, FR5 (Stories 1, 5).

**Exit codes** (Decision D6):
| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Input file not found / not readable |
| 2 | CSV conversion error (e.g., empty file, no header) raised by Converter |

## Component boundary summary

```
      argv / files / stdout           in-memory objects only
   ┌───────────────────────┐      ┌───────────────────────────┐
   │   CLI (cli.py)        │ ---> │  Converter (converter.py)  │
   │  - parses args        │      │  - csv.DictReader -> list │
   │  - opens files        │      │  - json.dumps              │
   │  - writes stdout/file │      │  - no I/O, no argv         │
   │  - maps exceptions to │      │  - raises CsvConversionError│
   │    exit codes         │      │                             │
   └───────────────────────┘      └───────────────────────────┘
```

This is the only boundary in the system. It is drawn at the I/O edge because
that is the one seam every story needs: Stories 1/5 (CLI-facing behavior)
only need to exercise argv/exit-codes/streams; Stories 2/3/4/6 (conversion
correctness) only need to exercise Converter with in-memory CSV text and
assert on returned Python data / JSON strings, with no filesystem or
subprocess overhead. Two components is deliberately the ceiling for this
scope — see Decision D1.

## Data model

Row objects are plain `dict[str, str | None]`:
- Keys = header column names, in header order (Python dicts preserve
  insertion order, so JSON array element key order matches the CSV header).
- Values = the field's string value, or `""` for an empty field present in
  the row, per Decision D4. `csv.DictReader` may map a genuinely
  **missing/short row** trailing field to `None`; this is passed through
  unchanged and serializes to JSON `null` — documented in `docs/usage.md`.

No additional domain model, no ORM, no database — the tool is stateless
per invocation.

## Testing component map

| Test file | Exercises | Requirements covered |
|---|---|---|
| `tests/test_converter.py` | `converter.py` directly, in-memory strings/`DictReader` | FR2, FR3, FR4, NFR1 |
| `tests/test_cli.py` | `cli.main()` in-process with `argv`, tmp files, captured stdout | FR1, FR5 |

Every requirement (FR1–FR5, NFR1) has at least one owning test file above,
satisfying the requirement-driven testing floor.
