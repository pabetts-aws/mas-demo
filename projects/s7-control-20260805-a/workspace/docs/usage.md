# Usage — csv2json

A small command-line tool that converts a CSV file (with a header row) into
a JSON array of row objects.

## Install

From the task workspace root:

```bash
pip install -e .
```

This installs the `csv2json` console script and the `csv2json` Python
package. No third-party dependencies are required (standard library only —
see `docs/decisions.md` D2).

## Run

Either the installed console script, or the module form, both work:

```bash
csv2json path/to/input.csv
# or, without installing:
python -m csv2json path/to/input.csv
```

### Example

Given `people.csv`:

```csv
name,city,notes
Ada,London,"first, computer programmer"
Bram,Amsterdam,""
Chen,Beijing,"loves ""quotes"" and, commas"
```

Running:

```bash
python -m csv2json people.csv
```

Prints to stdout:

```json
[
  {
    "name": "Ada",
    "city": "London",
    "notes": "first, computer programmer"
  },
  {
    "name": "Bram",
    "city": "Amsterdam",
    "notes": ""
  },
  {
    "name": "Chen",
    "city": "Beijing",
    "notes": "loves \"quotes\" and, commas"
  }
]
```

## CLI flags

| Flag | Required | Meaning |
|---|---|---|
| `input_path` (positional) | Yes | Path to the input CSV file. |
| `-o, --output PATH` | No | Write JSON to this file instead of stdout. |
| `--indent N` | No (default `2`) | Pretty-print indent width. `--indent 0` produces compact single-line JSON. |

## Output semantics

- Each JSON array element is an object whose keys are the CSV header
  columns, in header order.
- An **empty field** (e.g. `a,,c`) becomes an empty string `""` in the JSON
  output.
- A **short row** (fewer fields than there are header columns) has its
  missing trailing field(s) rendered as JSON `null` — this is distinct from
  an empty field (see `docs/decisions.md` D4).
- Quoted fields — including those containing commas, escaped double quotes
  (`""`), or embedded newlines — are parsed correctly via Python's standard
  `csv` module (see `docs/decisions.md` D3).

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Input file not found or not readable |
| `2` | CSV could not be converted (e.g. the file has no header row) |

## Run the tests

```bash
pip install -e .
pytest
```

All conversion-logic tests live in `tests/test_converter.py` and exercise
`csv2json/converter.py` directly with in-memory CSV strings (no filesystem
or subprocess overhead). All CLI-facing tests live in `tests/test_cli.py`
and call `csv2json.cli.main(argv)` in-process, using `pytest`'s `tmp_path`
and `capsys` fixtures to exercise real file I/O and captured stdout/stderr
without shelling out.
