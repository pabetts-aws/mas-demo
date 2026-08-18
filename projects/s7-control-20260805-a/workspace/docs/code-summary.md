# Code Summary — CSV to JSON CLI Tool

## What was built

A stdlib-only Python CLI, `csv2json`, converting a CSV file with a header
row into a JSON array of row objects, matching the two-component design in
`docs/components.md` and the decisions in `docs/decisions.md`.

## Files produced (workspace root)

```
csv2json/
  __init__.py       # package init; re-exports converter public API
  converter.py       # Component: Converter — pure CSV text -> JSON string logic
  cli.py              # Component: CLI — argparse, file/stdout I/O, exit codes
  __main__.py         # `python -m csv2json` entry point
tests/
  test_converter.py   # 15 tests exercising converter.py directly
  test_cli.py          # 9 tests exercising cli.main() in-process
  fixtures/
    sample.csv         # sample CSV with quoted/comma/empty fields (FR3/FR4/FR5 e2e)
pyproject.toml        # packaging + console-script entry point (csv2json = csv2json.cli:main)
docs/
  usage.md             # install/run/test instructions, CLI contract, exit codes
```

## Component implementation notes

### Converter (`csv2json/converter.py`)
- `csv_rows_to_json_records(reader: csv.DictReader) -> list[dict[str, str | None]]`:
  consumes a `csv.DictReader`, drops the `restkey`-collected extra-field
  bucket (dict key `None`), and returns row dicts in header-column order.
  Raises `CsvConversionError` if `reader.fieldnames` is falsy (no header
  row) — satisfies A1/FR2.
- `convert_csv_text_to_json_string(csv_text, *, indent=2) -> str`: wraps
  `csv_text` in `io.StringIO` (not `str.splitlines()`) before handing it to
  `csv.DictReader`, so that quoted fields containing embedded newlines are
  reassembled correctly by the stdlib `csv` module's own multi-line quote
  handling — this was verified empirically via
  `test_quoted_field_with_embedded_newline_is_preserved_as_single_field`.
  Delegates all quoting/escaping to the `csv` module per Decision D3.
- Empty field → `""`; short row → `None` → JSON `null`, exactly per
  Decision D4, and both cases have dedicated tests.

### CLI (`csv2json/cli.py`, `csv2json/__main__.py`)
- `build_arg_parser()` implements the contract from `docs/components.md`:
  positional `input_path`, `-o/--output`, `--indent` (default `2`;
  `--indent 0` → compact JSON via `indent=None`).
- `main(argv=None, *, stdout=None, stderr=None) -> int` never calls
  `sys.exit()`. `stdout`/`stderr` default to `None` and are resolved to the
  *current* `sys.stdout`/`sys.stderr` inside the function body (not bound
  as a mutable default argument) — this was a deliberate fix so that
  `pytest`'s `capsys` fixture (which monkeypatches `sys.stdout` after
  import time) correctly captures output in tests.
- Exception → exit-code mapping exactly per Decision D5/D6:
  `OSError` reading input → `1`; `CsvConversionError` → `2`; success → `0`.
- No output flag → JSON printed to stdout with a trailing newline (via
  `print`); `-o PATH` → JSON written to that file (UTF-8) and nothing
  printed to stdout, per Decision D7.

## Tests authored (24 total, all passing)

| File | Count | Covers |
|---|---|---|
| `tests/test_converter.py` | 15 | FR2, FR3, FR4, NFR1 — header/row parsing, column order, row order, header-only file, quoted commas, escaped quotes, embedded newlines, empty field → `""`, short row → `null`, quoted empty field, missing-header error (both via the string API and the raw `csv.DictReader` API), indent behavior |
| `tests/test_cli.py` | 9 | FR1, FR4, FR5, NFR1 — valid path → exit 0, missing file → exit 1 with stderr message, stdout output + JSON shape, `-o`/`--output` file writing (both flag spellings), end-to-end fixture with quotes/commas/empty values, no-header CSV → exit 2, `--indent 0` compact output, missing required arg → `SystemExit` |

Requirement traceability (cross-checked against `docs/requirements.md` and
`docs/code-generation-plan.md`):

- FR1 → `test_main_returns_zero_for_valid_csv_path`, `test_main_returns_one_for_missing_input_file`
- FR2 → `test_simple_csv_converts_to_list_of_dicts_preserving_order`, `test_rows_preserved_in_source_order`
- FR3 → `test_row_object_keys_follow_header_order`, `test_header_only_csv_returns_empty_json_array`, `test_main_end_to_end_with_sample_fixture_handles_quotes_and_empty_values`
- FR4 → all `test_quoted_*` and `test_*empty_field*`/`test_short_row*` tests in `test_converter.py`, plus the fixture e2e CLI test
- FR5 → `test_main_writes_json_array_to_stdout_by_default`, `test_main_writes_json_array_to_output_file_when_dash_o_given`, `test_main_long_form_output_flag_also_works`
- NFR1 → the full pytest suite (24/24 passing, see verification below)
- A1 → `test_empty_csv_text_raises_csv_conversion_error`, `test_csv_rows_to_json_records_raises_on_missing_header_directly`, `test_main_returns_two_for_empty_csv_with_no_header`

Every requirement has at least one owning test; no orphan test files.

## Verification performed in this stage

```
$ pip install -e .                    # installs csv2json + console script
$ pytest -q                           # 24 passed
$ ruff check csv2json tests           # All checks passed!
$ mypy csv2json                       # Success: no issues found in 4 source files
$ python -m csv2json tests/fixtures/sample.csv
[... valid JSON array of 3 row objects, quotes/commas/empty value correct ...]
$ python -m csv2json nope.csv         # exit code 1, stderr message
$ python -m csv2json tests/fixtures/sample.csv -o /tmp/out.json   # writes file, exit 0
```

All success criteria for this task are met:
- pytest suite passes with zero failures (24/24).
- The CLI converts a sample CSV with a header row (including quoted
  fields and empty values) into a valid JSON array, both to stdout and to
  an output file.

## Deviations from the design docs

None. Implementation follows `docs/components.md` and `docs/decisions.md`
exactly, including the exit-code contract (D6), the `""`-vs-`null` rule
(D4), and stdlib-only dependencies (D2). The only addition not explicitly
spelled out in the design is the `stdout`/`stderr` "resolve current
sys.stream at call time" detail in `cli.main()`, which is an
implementation-level fix needed to make the design's own stated goal
("stays testable in-process... tests call main([...]) and assert on the
returned code + captured output") actually work correctly under pytest's
`capsys`.
