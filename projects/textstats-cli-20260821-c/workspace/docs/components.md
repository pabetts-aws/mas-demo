# Component Design — Text Statistics CLI Tool

## Overview

The tool is a single small Python package, `textstats`, split into four
narrowly-scoped modules plus a thin entry point. Each module has one reason
to change, and the boundaries are drawn along the "pure logic vs. I/O vs.
presentation vs. wiring" seams so that the counting and formatting logic
(which NFR1 requires unit tests for) has zero dependency on argparse, the
filesystem, or stdout/stderr.

```
textstats/
├── __init__.py          # package marker, re-exports public API (optional)
├── __main__.py          # `python -m textstats` entry point → calls cli.main()
├── counter.py           # pure counting logic (no I/O)
├── formatting.py        # pure presentation logic (human table + JSON), no I/O
├── cli.py               # argument parsing, file I/O, error handling, orchestration
tests/
├── test_counter.py      # unit tests for counter.py
├── test_formatting.py   # unit tests for formatting.py
└── test_cli.py          # integration-style tests for cli.py (subprocess / CliRunner-style calls)
pyproject.toml           # packaging + console_scripts entry point `textstats`
docs/usage.md            # how to run the tool and its tests (produced later, referenced here)
```

Dependencies flow one direction only: `cli.py` → `formatting.py` → `counter.py`.
Neither `counter.py` nor `formatting.py` ever imports `cli.py`, and neither
performs file or process I/O. This is what makes FR1–FR3's logic testable
without touching the filesystem (Story 6).

---

## Component 1: Counting Engine (`textstats/counter.py`)

**Responsibility:** Given the raw text content of one file, compute line,
word, and character counts. Given a collection of per-file results, compute
the aggregate totals. Pure functions only — no file access, no argv, no
printing.

**Public interface:**

```python
@dataclass(frozen=True)
class Stats:
    lines: int
    words: int
    chars: int

def count_stats(text: str) -> Stats:
    """Count lines, words, and chars in a string of file content."""

def total_stats(all_stats: Iterable[Stats]) -> Stats:
    """Sum lines/words/chars across multiple Stats."""
```

**Counting rules (must be documented and tested per-rule — see decisions.md D4):**
- `lines` = `len(text.splitlines())` — i.e. the number of logical lines,
  whether or not the file ends with a trailing newline. Empty text → 0 lines.
- `words` = `len(text.split())` — whitespace-delimited tokens; consecutive
  whitespace collapses, leading/trailing whitespace does not create empty
  tokens.
- `chars` = `len(text)` — total character count of the content exactly as
  read (includes spaces, tabs, and newline characters).

**Depends on:** nothing (stdlib `dataclasses`, `typing` only).
**Depended on by:** `formatting.py`, `cli.py`, `tests/test_counter.py`.

---

## Component 2: Formatter (`textstats/formatting.py`)

**Responsibility:** Turn a list of `(label, Stats)` pairs (plus an optional
total `Stats`) into either the human-readable table string or the JSON
string. No knowledge of files, argv, or exit codes — it receives data, it
returns a string.

**Public interface:**

```python
FileResult = tuple[str, Stats]   # (file_label, stats) — label is the path as given on argv

def format_human(results: list[FileResult], total: Stats | None) -> str:
    """Render a human-readable table: one row per file, plus a 'total'
    row when `total` is not None (i.e. when len(results) > 1)."""

def format_json(results: list[FileResult], total: Stats | None) -> str:
    """Render the same numbers as a single JSON document (see decisions.md
    D5 for exact schema). `total` is included only when not None."""
```

**Depends on:** `counter.Stats` (type only).
**Depended on by:** `cli.py`, `tests/test_formatting.py`.

---

## Component 3: CLI / Orchestrator (`textstats/cli.py`)

**Responsibility:** The only component allowed to touch argv, the
filesystem, stdout/stderr, and `sys.exit` codes. Parses arguments, reads
each file, calls the Counting Engine and Formatter, writes output, and
decides the process exit code. This is where FR4 (missing-file handling)
and Story 5 (usage error) live.

**Public interface:**

```python
def read_file_text(path: str) -> str:
    """Read a file as UTF-8 text. Raises FileNotFoundError (propagated,
    not swallowed) if the path does not exist."""

def main(argv: list[str] | None = None) -> int:
    """Parse argv, run the tool, print to stdout/stderr, and return the
    process exit code (does not call sys.exit itself — see decisions.md D7
    for why, and how __main__.py bridges to sys.exit)."""
```

**Behavior contract (traces to stories 1–5):**
1. Build an `argparse.ArgumentParser` requiring `files: list[str]` (`nargs='+'`)
   and an optional `--json` boolean flag. Zero files → argparse itself
   raises a usage error to stderr and exits code `2` (Story 5).
2. For each file path in the order given: call `read_file_text`. If any
   raise `FileNotFoundError`, collect the missing path(s) — do **not**
   process partial success (Story 4).
3. If any file was missing: print one clear line per missing file to
   **stderr** (e.g. `textstats: error: file not found: <path>`), never to
   stdout, and return exit code `1` (Story 4) — this holds identically
   whether `--json` was passed or not.
4. If all files were read successfully: call `counter.count_stats` per
   file, compute `total_stats` only when `len(files) > 1` (Stories 2 & 3),
   then call `formatting.format_json` or `formatting.format_human`
   depending on `--json`, print the result to **stdout**, and return `0`.

**Depends on:** `counter.py`, `formatting.py`, stdlib `argparse`, `sys`.
**Depended on by:** `textstats/__main__.py`, `tests/test_cli.py`.

---

## Component 4: Entry Point (`textstats/__main__.py` + `pyproject.toml`)

**Responsibility:** Bridge the pure `main(argv) -> int` function to an
actual OS process exit code, for both invocation styles:
- `python -m textstats <args>`
- `textstats <args>` (installed console script)

```python
# textstats/__main__.py
import sys
from textstats.cli import main

if __name__ == "__main__":
    sys.exit(main())
```

`pyproject.toml` declares `[project.scripts] textstats = "textstats.cli:main"`
so the installed console script also gets `main`'s return value as its exit
code (setuptools' generated script wrapper calls `sys.exit(main())`
automatically).

**Depends on:** `cli.py`.
**Depended on by:** the OS / the person or script invoking the tool.

---

## Component 5: Test Suite (`tests/`)

**Responsibility:** Objective proof that each component contract holds.
Mirrors the module boundaries so failures point at one component:

| Test file | Targets | Traces to |
|---|---|---|
| `tests/test_counter.py` | `count_stats`, `total_stats` — empty file, no trailing newline, whitespace-only file, multi-file totals | Story 1, Story 2, Story 6 |
| `tests/test_formatting.py` | `format_human`, `format_json` — single-file (no total), multi-file (with total), JSON parses and matches human numbers | Story 2, Story 3, Story 6 |
| `tests/test_cli.py` | `main()` end-to-end via temp files: happy path, missing file → exit 1 + stderr text, zero args → exit 2, `--json` on stdout only, mixed existing/missing files | Story 4, Story 5, Story 6 |

No test touches real production files; `tests/test_cli.py` uses `tmp_path`
fixtures to create throwaway files, keeping the suite hermetic and fast.

---

## Data flow summary

```
argv ──▶ cli.main()
           ├─▶ read_file_text(path) for each path        (I/O boundary)
           │      └─ FileNotFoundError ──▶ stderr + exit 1
           ├─▶ counter.count_stats(text) for each file    (pure)
           ├─▶ counter.total_stats(all)  if >1 file       (pure)
           ├─▶ formatting.format_json | format_human(...) (pure)
           └─▶ stdout.write(result) ──▶ exit 0
```

## Explicit non-goals (kept out to stay "small")

- No third-party dependencies (argparse + json + dataclasses from stdlib
  suffice for this scope — see decisions.md D1).
- No streaming/chunked reads for huge files — files are read whole into
  memory (acceptable per C1's "small CLI tool" constraint; revisit only if
  a future requirement demands large-file support).
- No support for stdin (`-`) or directories as input — out of scope for
  the stated requirements; `read_file_text` only accepts a path to an
  existing regular file.
