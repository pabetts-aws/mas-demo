# Code Summary — Text Statistics CLI Tool

Implementation of the `code-generation` stage per `docs/code-generation-plan.md`,
`docs/components.md`, and `docs/decisions.md`. All application code lives at
the task workspace root (never under `docs/`), with tests alongside it.

## What was built

### Application code (`textstats/` package, workspace root)

| File | Purpose |
|---|---|
| `textstats/__init__.py` | Package marker; re-exports `Stats`, `count_stats`, `total_stats`, `format_human`, `format_json`, `main`. |
| `textstats/counter.py` | Pure counting logic: `Stats` dataclass, `count_stats(text) -> Stats`, `total_stats(all_stats) -> Stats`. No I/O. |
| `textstats/formatting.py` | Pure presentation logic: `format_human(results, total) -> str`, `format_json(results, total) -> str`. No I/O. |
| `textstats/cli.py` | Orchestrator: `read_file_text(path) -> str`, `main(argv=None) -> int`. Only module touching argv, filesystem, stdout/stderr. |
| `textstats/__main__.py` | `python -m textstats` entry point; bridges `main()`'s return value to `sys.exit`. |
| `pyproject.toml` | Packaging metadata, `[project.scripts] textstats = "textstats.cli:main"` console-script entry point, `pytest` config (`pythonpath = "."`, `testpaths = ["tests"]`). |

### Tests (`tests/`, workspace root)

| File | Covers | Traces to |
|---|---|---|
| `tests/test_counter.py` (8 tests) | Empty text, no-trailing-newline, whitespace-only, multi-line/multi-word happy path, `total_stats` over multiple/single/zero `Stats`. | FR1, FR2, Story 1, Story 2, Story 6 |
| `tests/test_formatting.py` (6 tests) | Human table with/without totals row, JSON with/without `total` key, JSON is valid/parseable, JSON numbers match human numbers. | FR2, FR3, Story 2, Story 3, Story 6 |
| `tests/test_cli.py` (10 tests) | Single-file happy path, multi-file with totals row, single-file no-totals-row, missing file (stderr + exit 1), mixed existing/missing (fail closed), `--json` happy path (stdout-only valid JSON), `--json` multi-file totals, `--json` + missing file (plain-text stderr, not JSON), zero-args usage error (exit 2), console-script subprocess smoke test. | FR1–FR4, Story 1–6 |

**Total: 24 tests, all passing.**

## Verification performed in this stage

```bash
pytest -q            # 24 passed
ruff check textstats tests   # All checks passed
mypy textstats                # Success: no issues found in 5 source files
```

Manual smoke checks of the built CLI (`python -m textstats`) were also run
against real temp files for: single file, multiple files with totals,
`--json` output, a missing file (exit 1, stderr message), and zero
arguments (exit 2, argparse usage message) — all matched the documented
behavior contract in `docs/components.md` / `docs/decisions.md`.

## Requirement / story → test traceability

| Requirement | Story | Test evidence |
|---|---|---|
| FR1 (line/word/char counts) | Story 1 | `test_counter.py::test_count_stats_*`, `test_cli.py::test_single_file_happy_path` |
| FR2 (totals row for multiple files) | Story 2 | `test_counter.py::test_total_stats_*`, `test_formatting.py::test_format_human_multiple_files_with_total_row`, `test_cli.py::test_multiple_files_show_total_row`, `test_single_file_no_total_row` |
| FR3 (`--json` flag) | Story 3 | `test_formatting.py::test_format_json_*`, `test_cli.py::test_json_flag_*` |
| FR4 (missing file → clear error + non-zero exit) | Story 4 | `test_cli.py::test_missing_file_error_and_exit_code`, `test_mixed_existing_and_missing_files_fails_closed`, `test_json_flag_with_missing_file_errors_on_stderr_as_plain_text` |
| FR1/FR4 (usage error on invalid invocation) | Story 5 | `test_cli.py::test_no_arguments_usage_error` |
| NFR1 (unit tests for counting/JSON logic) | Story 6 | Full suite; `pytest -q` exits 0 with 24 passed |
| C1 (small CLI, no runtime deps) | — | stdlib-only imports throughout; verified by `pyproject.toml` having no `[project.dependencies]` |
| A1 (UTF-8 input) | — | `read_file_text` opens with `encoding="utf-8"`; documented gap for non-UTF-8 input in `docs/usage.md` |

Every requirement (FR1–FR4, NFR1, C1, A1) and every story (1–6) is backed by
at least one passing, named test case — no requirement is untraced.

## Documentation produced

- `docs/usage.md` — how to run the tool (`python -m textstats`, optional
  installed `textstats` console script), how to run the tests (`pytest`),
  the exact counting rules and their documented deviation from `wc`
  semantics, the exit-code table, and the UTF-8-only encoding scope gap.

## Known, documented scope gaps (carried from design, not defects)

- Non-UTF-8 / binary input files raise an uncaught `UnicodeDecodeError`
  rather than a clean, tested CLI error path (per `docs/decisions.md` D9 —
  no requirement covers this case).
- No stdin (`-`) or directory input support (explicit non-goal in
  `docs/components.md`).
- No streaming/chunked reads for very large files (explicit non-goal,
  consistent with C1's "small CLI tool" constraint).

## Next stage

Ready for `build-and-test` to independently re-run `pytest` (and any
additional integration/regression checks) against this code as the
objective success signal, per platform principle D10 ("Build and test
results are the only success signal").
