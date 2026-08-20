# Usage — Text Statistics CLI Tool

A small command-line tool that reports line, word, and character counts for
one or more input text files.

## Requirements

- Python 3.9+
- `pytest` (for running the test suite; not required to run the tool itself)

No third-party runtime dependencies — the tool uses only the Python
standard library (`argparse`, `json`, `dataclasses`).

## Running the tool

From the workspace root, without installing anything:

```bash
python -m textstats <file1> [<file2> ...]
```

### Human-readable output (default)

```bash
$ python -m textstats sample1.txt
File          Lines  Words  Chars
sample1.txt       2      4     20
```

With multiple files, per-file rows are followed by a `total` row:

```bash
$ python -m textstats sample1.txt sample2.txt
File          Lines  Words  Chars
sample1.txt       2      4     20
sample2.txt       1      3     14
total             3      7     34
```

A single file never gets a `total` row — only the file's own counts are
shown.

### JSON output (`--json`)

```bash
$ python -m textstats --json sample1.txt sample2.txt
{"files": [{"file": "sample1.txt", "lines": 2, "words": 4, "chars": 20}, {"file": "sample2.txt", "lines": 1, "words": 3, "chars": 14}], "total": {"lines": 3, "words": 7, "chars": 34}}
```

- The `files` array always lists per-file results in the order given on the
  command line.
- The `total` key is present **only when more than one file is given**; for
  a single file it is omitted.
- Numbers in JSON output always match the numbers shown in human-readable
  output for the same inputs.
- `--json` output goes to stdout only; nothing else is printed to stdout.

### Missing files

If any input file does not exist, the tool prints one error line per
missing file to **stderr** (never stdout, even with `--json`) and exits
with code `1`. It never reports partial success — if any file is missing,
no counts are printed for the others either:

```bash
$ python -m textstats does-not-exist.txt
textstats: error: file not found: does-not-exist.txt
$ echo $?
1
```

### No file arguments

Running the tool with zero file arguments produces a standard `argparse`
usage message on stderr and exits with code `2`:

```bash
$ python -m textstats
usage: textstats [-h] [--json] files [files ...]
textstats: error: the following arguments are required: files
$ echo $?
2
```

### Exit codes summary

| Condition | Exit code |
|---|---|
| All files read and reported successfully | `0` |
| One or more input files missing | `1` |
| Invalid invocation (e.g. zero file arguments) | `2` |

### Installing the console script (optional)

The tool can also be installed so the `textstats` command is available
directly (equivalent to `python -m textstats`):

```bash
pip install -e .
textstats sample1.txt sample2.txt
```

## Counting rules

- **Lines** = number of logical lines (`str.splitlines()`), so a file's
  final line is counted whether or not it ends with a trailing newline.
  An empty file has 0 lines.
- **Words** = number of whitespace-separated tokens (`str.split()`), so a
  whitespace-only file has 0 words.
- **Characters** = total character count of the file's content exactly as
  read (`len(text)`), including all whitespace and newline characters.

**Note:** This deliberately differs from POSIX `wc` (e.g. `wc -l` counts
raw `\n` bytes, not logical lines). This tool does not claim `wc`
compatibility — only internal consistency between its own human-readable
and JSON output.

## Encoding

Files are read as UTF-8 text (Python's default strict decoding). A
non-UTF-8 or binary file will raise an uncaught `UnicodeDecodeError`
rather than a specially-handled, clean CLI error — this is a known,
documented scope gap (no requirement covers non-UTF-8 input).

## Running the tests

From the workspace root:

```bash
pip install pytest   # if not already installed
pytest -q
```

This runs the full suite (`tests/test_counter.py`, `tests/test_formatting.py`,
`tests/test_cli.py`) covering:

- Counting logic edge cases (empty file, no trailing newline, whitespace-only
  file, multi-line/multi-word happy path, totals aggregation).
- Human-readable and JSON formatting (single file / multiple files, totals
  row/key presence rules, JSON-vs-human numeric parity).
- End-to-end CLI behavior (happy path, missing file, mixed existing/missing
  files, `--json` on/off, zero-argument usage error, and one subprocess
  smoke test that exercises `python -m textstats` as an actual OS process).

The suite is expected to complete with **zero failures**; `pytest`'s exit
code is the objective pass/fail signal for this tool.

### Optional lint / type-check

The code has been verified against `ruff` and `mypy` with zero reported
issues:

```bash
pip install ruff mypy
ruff check textstats tests
mypy textstats
```
