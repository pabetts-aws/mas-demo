# Code Generation Plan — Text Statistics CLI Tool

This plan maps every implementation step to the requirement(s)/story(ies) it
implements, per `docs/components.md` and `docs/decisions.md`. Tests are
authored in this same stage, alongside the code they verify (never deferred).

## Coverage matrix (requirement/story → code → test)

| Req / Story | Implementation step | Test file / case |
|---|---|---|
| FR1 (single & multi file counts), Story 1 | `textstats/counter.py`: `Stats`, `count_stats()` | `tests/test_counter.py::test_count_stats_*` |
| FR2 (totals row), Story 2 | `textstats/counter.py`: `total_stats()`; `textstats/cli.py` totals wiring (only when `len(files) > 1`, D8) | `tests/test_counter.py::test_total_stats_*`, `tests/test_cli.py::test_multiple_files_show_total_row`, `test_single_file_no_total_row` |
| FR3 (`--json` flag), Story 3 | `textstats/formatting.py`: `format_json()`; `textstats/cli.py` `--json` argparse flag + dispatch | `tests/test_formatting.py::test_format_json_*`, `tests/test_cli.py::test_json_flag_*` |
| FR1/FR2 human output, D6 | `textstats/formatting.py`: `format_human()` | `tests/test_formatting.py::test_format_human_*` |
| FR4 (missing file → error + non-zero exit), Story 4 | `textstats/cli.py`: `read_file_text()` (propagates `FileNotFoundError`), `main()` fail-closed missing-file handling → stderr + exit 1 (D7) | `tests/test_cli.py::test_missing_file_*`, `test_mixed_existing_and_missing_files` |
| FR1/FR4 (no-args usage error), Story 5 | `textstats/cli.py`: `argparse` `nargs='+'` on `files` (argparse raises usage error, exit 2 natively) | `tests/test_cli.py::test_no_arguments_usage_error` |
| NFR1 (unit tests for counting + JSON logic), Story 6 | All of the above test files | `tests/test_counter.py`, `tests/test_formatting.py`, `tests/test_cli.py` — full suite must pass with zero failures |
| C1 (small CLI, no runtime deps), D1 | stdlib-only imports throughout; `pyproject.toml` with no runtime dependencies | N/A (verified by inspection / no install failures) |
| A1 (UTF-8 input), D9 | `read_file_text()` opens with `encoding="utf-8"`, strict errors | Not separately tested (explicit documented gap per D9); covered implicitly by all happy-path tests using UTF-8 fixtures |
| Entry point wiring | `textstats/__main__.py`; `pyproject.toml` `[project.scripts] textstats = "textstats.cli:main"` | `tests/test_cli.py::test_console_script_smoke` (optional subprocess smoke test, D10) |
| Usage documentation (quality bar) | `docs/usage.md` | N/A — human-readable doc, not code |

## Implementation steps (in order)

1. **Scaffold package** — create `textstats/__init__.py` (package marker),
   `textstats/counter.py`, `textstats/formatting.py`, `textstats/cli.py`,
   `textstats/__main__.py`.
2. **`counter.py`** (pure, no I/O) — implement `Stats` dataclass and
   `count_stats(text) -> Stats`, `total_stats(all_stats) -> Stats` exactly per
   D4's rules (`splitlines()`, `split()`, `len()`).
3. **`formatting.py`** (pure, no I/O) — implement `format_human(results,
   total)` and `format_json(results, total)` per D5 (JSON schema) and D6
   (table format). `total=None` omits the totals row/key uniformly (D8).
4. **`cli.py`** — implement `read_file_text(path)` and `main(argv=None) ->
   int` per the behavior contract in `docs/components.md` Component 3 and the
   exit-code table in D7: build argparse parser (`files` `nargs='+'`,
   `--json` flag); read all files first, collecting missing paths; on any
   missing file print one stderr line per missing path and return 1; on
   success compute totals conditionally, format, print to stdout, return 0.
5. **`__main__.py`** — `sys.exit(main())` bridge for `python -m textstats`.
6. **`pyproject.toml`** — package metadata, `[project.scripts]` entry point,
   pytest config (`[tool.pytest.ini_options]` with `pythonpath = "."` so
   `tests/` can `import textstats` without an install step), per D3.
7. **Tests** (authored now, not deferred):
   - `tests/test_counter.py` — empty text, no-trailing-newline text,
     whitespace-only text, multi-line/multi-word happy path, `total_stats`
     across 2–3 `Stats` instances.
   - `tests/test_formatting.py` — single-file human output (no total row),
     multi-file human output (with total row), single-file JSON (no
     `total` key), multi-file JSON (with `total` key), JSON round-trips via
     `json.loads` and matches expected numeric values.
   - `tests/test_cli.py` — happy path single file (`capsys`, `tmp_path`),
     happy path multiple files with total row, missing single file (exit 1,
     stderr message, empty stdout), mixed existing/missing files (exit 1,
     no partial success), `--json` happy path (stdout is valid JSON, no
     other stdout content), `--json` with missing file (error still on
     stderr as plain text, not JSON), zero arguments (exit 2, stderr usage
     message), optional console-script subprocess smoke test.
   - `tests/conftest.py` — none required; `tmp_path` is a built-in pytest
     fixture, no shared fixtures complex enough to warrant a conftest.
8. **Run `pytest`** and fix any failures until the suite is green.
9. **Run a linter/type-checker sensor** (e.g. `python -m py_compile` /
   `python -m compileall` plus a light static check) to confirm no errors on
   generated code, per the quality bar.
10. **Author `docs/usage.md`** — how to run the tool (`python -m textstats`,
    installed `textstats` console script) and how to run tests (`pytest`),
    including the documented `wc`-semantics deviation (D4) and the UTF-8
    strict-decoding gap (D9).
11. **Author `docs/code-summary.md`** — record what was built and where, for
    the stage gate and for downstream build-and-test/review stages.

## Test strategy level

`greenfield-dev` + NFR1 + Story 6 call for full unit coverage of counting and
JSON logic (not just a happy-path floor): every counting rule edge case
(empty, no-trailing-newline, whitespace-only) and every documented CLI
outcome (success, missing file, mixed missing, zero-args usage error,
`--json` on/off) gets at least one explicit test case, satisfying "every
requirement maps to at least one test."
