# Code Generation Plan — CSV to JSON CLI Tool

This plan maps every implementation step to the story/requirement it
satisfies, per `docs/components.md` and `docs/decisions.md`. Test files are
authored in this same stage (mandatory), not deferred to build-and-test.

## Step → Story/Requirement coverage

| # | Step | File(s) | Story | Requirement(s) |
|---|---|---|---|---|
| 1 | Create package skeleton (`csv2json/__init__.py`) | `csv2json/__init__.py` | — | Packaging (D8) |
| 2 | Implement pure conversion logic: `csv_rows_to_json_records`, `convert_csv_text_to_json_string`, `CsvConversionError` | `csv2json/converter.py` | Story 2, 3, 4 | FR2, FR3, FR4 |
| 3 | Implement CLI argument parsing (`build_arg_parser`) — positional `input_path`, `-o/--output`, `--indent` | `csv2json/cli.py` | Story 1, 5 | FR1, FR5 |
| 4 | Implement `main(argv) -> int`: read input file, call Converter, write stdout/file, map exceptions to exit codes 0/1/2 | `csv2json/cli.py` | Story 1, 3, 4, 5 | FR1, FR3, FR4, FR5 |
| 5 | Implement `__main__.py` module entry point (`python -m csv2json`) | `csv2json/__main__.py` | — | Packaging (D8) |
| 6 | Add `pyproject.toml` with console-script entry point `csv2json = csv2json.cli:main` | `pyproject.toml` | — | C1, Packaging (D8) |
| 7 | Unit tests for Converter: header+rows→JSON, quoted fields (commas/quotes/newlines), empty field → `""`, short row → `null`, header-only file → `[]`, missing-header → `CsvConversionError` | `tests/test_converter.py` | Story 2, 3, 4, 6 | FR2, FR3, FR4, NFR1 |
| 8 | Unit tests for CLI: valid path → exit 0 + stdout JSON, `-o` writes file, missing file → exit 1, malformed CSV (no header) → exit 2, `--indent` behavior | `tests/test_cli.py` | Story 1, 5, 6 | FR1, FR5, NFR1 |
| 9 | Sample fixture CSV (with quoted fields, embedded comma, empty value) used by an end-to-end CLI test to satisfy the "CLI converts a sample CSV... into a JSON array" success criterion | `tests/fixtures/sample.csv`, referenced from `tests/test_cli.py` | Story 3, 4, 5 | FR3, FR4, FR5 |
| 10 | Usage documentation: install, run via `python -m csv2json` / console script, flags, exit codes, null-vs-empty-string semantics, how to run tests | `docs/usage.md` | Story 1, 5, 6 | FR1, FR5, NFR1 |

## Coverage check (plan gate)

- FR1 (accept CSV path arg) → Steps 3, 4, 8
- FR2 (read/parse CSV) → Steps 2, 7
- FR3 (header row → JSON array of objects) → Steps 2, 4, 7, 8, 9
- FR4 (quoted fields, empty values) → Steps 2, 4, 7, 9
- FR5 (emit to stdout or output file) → Steps 3, 4, 8, 9
- NFR1 (unit tests for conversion logic, pytest zero-failure) → Steps 7, 8
- C1 (Python implementation) → Steps 1–6 (stdlib only, per Decision D2)
- A1 (input has header row) → Step 7 (missing-header case is the negative
  test that documents/enforces this assumption via `CsvConversionError`)

Every requirement has at least one owning implementation step and at least
one owning test step. No step lacks a traced story/requirement.

## Test authoring commitment

All test files listed above (`tests/test_converter.py`, `tests/test_cli.py`,
plus the `tests/fixtures/sample.csv` fixture) are authored in full in this
stage, not stubbed — satisfying the "tests are authored in code generation"
rule and the minimal/happy-path-plus-key-edge-cases floor for a
greenfield-dev task class (empty values and quoted fields are explicitly
called out by the task's success criteria, so they are treated as
requirement-level, not merely nice-to-have, test cases).

## Non-goals (explicitly out of scope, confirmed against requirements)

- No custom CSV delimiter/dialect flag (not requested; Decision D3).
- No streaming/large-file optimization (no NFR requests it).
- No schema validation / type coercion of field values beyond str/None
  (Decision D4 fixes the null-vs-empty-string rule; nothing else is asked).
