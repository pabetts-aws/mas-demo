# Code Generation Plan — CSV to JSON CLI Tool

This plan maps every implementation step to the requirement(s) and/or
story(ies) it satisfies, per `docs/requirements.md`, `docs/stories.md`,
`docs/components.md`, and `docs/decisions.md`. Test files are authored in
this stage, alongside the code they test (never deferred to a later stage).

## Coverage matrix (step → story/requirement → test)

| # | Step | Implements | Test file / case |
|---|---|---|---|
| 1 | `csv2json/__init__.py` — package marker, re-export `main` | Constraint: workspace-root package layout (ADR-4/8) | n/a (import smoke-tested transitively by test_cli.py) |
| 2 | `csv2json/converter.py` — `csv_rows_to_records()` using `csv.DictReader(fh, restval="")` | FR1, FR2, FR3, C1, A1, NFR1-correctness (Story 1, 2, 3, 5) | `test_converter.py::test_basic_conversion` (T1), `::test_quoted_field_with_comma`, `::test_quoted_field_with_newline`, `::test_quoted_field_with_escaped_quote`, `::test_mixed_quoted_and_unquoted` (T2/Story 2), `::test_empty_middle_value`, `::test_empty_trailing_value`, `::test_blank_line_is_skipped` (T3/Story 3), `::test_row_order_preserved`, `::test_empty_file_raises_value_error` |
| 3 | `csv2json/converter.py` — 10,000-row performance path (no custom buffering, rely on `DictReader` streaming) | NFR1 (Story 5) | `test_converter.py::test_large_file_performance_and_correctness` (T5) — generates 10,000 rows, asserts wall-clock `< 10s` and row count/order correctness |
| 4 | `csv2json/io_handler.py` — `InputError`, `OutputError`, `open_input()` with `newline=''` | FR2 (multiline quoting, Story 2 AC2), FR1 error path (Story 1 AC4) | `test_io_handler.py::test_open_input_success`, `::test_open_input_missing_file_raises_input_error`, `::test_open_input_preserves_embedded_newlines` |
| 5 | `csv2json/io_handler.py` — `write_output()` (stdout vs file, JSON-only stdout, `OutputError` on bad path) | FR4 (Story 4) | `test_io_handler.py::test_write_output_to_stdout`, `::test_write_output_to_file`, `::test_write_output_bad_directory_raises_output_error` |
| 6 | `csv2json/cli.py` — `build_parser()`, `main(argv)` with 0/1/2 exit-code contract, stderr-only diagnostics | FR1 (error handling), FR4, all error ACs (Story 1 AC4, Story 4 AC3) | `test_cli.py::test_main_success_writes_json_to_stdout`, `::test_main_success_writes_json_to_file`, `::test_main_missing_input_returns_exit_code_1_and_stderr_message`, `::test_main_bad_output_dir_returns_exit_code_2`, `::test_main_stdout_contains_only_json_on_success` |
| 7 | `run.py` — thin entry point calling `sys.exit(main(sys.argv[1:]))` | Wiring only (ADR-6) | `test_cli.py::test_run_py_end_to_end_subprocess` — the one subprocess-based smoke test satisfying the objective success criterion ("CLI converts a sample CSV... into a JSON array") |
| 8 | `docs/usage.md` — how to run the tool and its tests, documented edge-case rules (blank-line skip, `restkey=None` on long rows) | Quality criterion: usage document | n/a (documentation, not code) |
| 9 | `README.md` — pointer to `docs/usage.md` | Quality criterion: usage document discoverability | n/a |

## Ordering rationale

Steps 1–3 (converter) are implemented and tested first because Component A
has no dependency on B or C (per the one-way dependency rule in ADR-4) and
covers the largest share of functional requirements (FR1–FR3, NFR1). Steps
4–5 (io_handler) follow, independently testable via `io.StringIO`/`tmp_path`
fixtures without invoking the CLI. Step 6 (cli.py) is implemented last among
the code components since it composes A and B and is where the exit-code
contract (ADR-6) is enforced and tested via return-value assertions (no
subprocess needed except the single end-to-end smoke test in step 7).

## Test strategy

Per the greenfield-dev task class (minimal/standard floor: every requirement
maps to at least one test), this plan authors:
- One or more tests per functional requirement (FR1–FR4) and the
  non-functional requirement (NFR1), each traceable back to `docs/
  requirements.md` T1–T5.
- Component-level unit tests for A and B (no process boundary — fast,
  deterministic) plus CLI-level tests for C that assert on `main()`'s
  return value (no `SystemExit`/subprocess needed except one true
  end-to-end smoke test via `run.py`, which is the direct check for the
  stated objective success criterion: "CLI converts a sample CSV file with
  a header row into a JSON array of row objects").
- No test is deferred to the build-and-test stage; that stage verifies and
  may extend, but every requirement already has a test file/case landing in
  this stage.

## Files created in this stage

```
csv2json/__init__.py
csv2json/converter.py
csv2json/io_handler.py
csv2json/cli.py
run.py
test_converter.py
test_io_handler.py
test_cli.py
docs/usage.md
README.md
```

All application and test code lands in the task workspace root (or the
`csv2json/` package directory beneath it), per the stage rule that
application code never goes into the record/artifact directory.
