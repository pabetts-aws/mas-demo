# Usage — CSV to JSON CLI Tool

A small command-line tool that converts a CSV file with a header row
into a JSON array of row objects, handling quoted fields and empty
values correctly.

## Requirements

- Python 3.9+ (uses only the standard library for the tool itself)
- `pytest` to run the test suite

Install `pytest` if it isn't already available:

```
pip install pytest
```

## Running the tool

From the repository root:

```
python run.py INPUT.csv
```

This prints the resulting JSON array to stdout. Example:

```
$ cat sample.csv
name,age,city
Alice,30,"Springfield, USA"
Bob,,Shelbyville

$ python run.py sample.csv
[
  {
    "name": "Alice",
    "age": "30",
    "city": "Springfield, USA"
  },
  {
    "name": "Bob",
    "age": "",
    "city": "Shelbyville"
  }
]
```

To write the JSON to a file instead of stdout:

```
python run.py sample.csv -o output.json
python run.py sample.csv --output output.json
```

When `-o`/`--output` is given, nothing is written to stdout on success;
the JSON goes to the specified file instead.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success — the full JSON array was produced. |
| 1 | Input error — the input file is missing, unreadable, or not valid CSV (e.g. empty file with no header row). |
| 2 | Output error — the given output path's directory does not exist or is not writable. |

On any non-zero exit, a one-line error message is printed to **stderr**
(never stdout), so stdout is always safe to pipe into another program or
redirect straight into a JSON file.

## Behavioral rules (documented, not left implicit)

- The first row of the input CSV **must** be a header row; its values
  become the JSON object keys for every subsequent row.
- Quoted fields are parsed per standard CSV rules: a quoted field may
  contain commas, embedded newlines, and doubled quotes (`""` decodes
  to a literal `"`).
- Empty cells (leading, middle, or trailing) become an empty string
  `""` in the JSON output — they are never omitted and never `null`.
- A data row with **fewer** fields than the header is padded with `""`
  for the missing trailing fields.
- A data row with **more** fields than the header gets an extra key
  (Python's `csv` module default: the key `None`, whose value is a list
  of the surplus fields). This is standard-library default behavior,
  called out here so it is never a surprise.
- A completely blank line in the input is skipped; it does not produce
  an empty record and does not crash the tool.

## Running the tests

From the repository root:

```
pytest
```

This runs:
- `test_converter.py` — conversion-logic unit tests (basic conversion,
  quoted fields, empty values, a 10,000-row performance/correctness
  check).
- `test_io_handler.py` — I/O boundary tests (stdout vs. file output,
  bad input/output paths, embedded-newline preservation).
- `test_cli.py` — CLI-level tests asserting on exit codes and
  stdout/stderr routing, plus one end-to-end subprocess test that
  invokes `run.py` directly against a sample CSV file.

All tests should pass with zero failures; this is the objective success
signal for this tool (see `docs/requirements.md` and the task's success
criteria).
