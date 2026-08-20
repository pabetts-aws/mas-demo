# User Stories

Each story traces to one or more requirements from `docs/requirements.md`.

---

## Story 1: Report counts for a single file
**Traces to:** FR1

**As** Dana the DevOps Engineer,
**I want** to run the CLI on a single text file,
**so that** I can quickly see its line, word, and character counts.

### Acceptance Criteria
- Given a single existing text file, when I run `textstats <file>`, then the output shows the line count, word count, and character count for that file.
- The output clearly labels which counts belong to which metric (line/word/char) and identifies the file by name.
- Line count matches the number of newline-terminated lines in the file (consistent with a defined, documented counting rule for a trailing-newline-less final line).
- Word count matches the number of whitespace-separated tokens in the file.
- Character count matches the total number of characters (including whitespace and newlines) in the file.
- Running with zero arguments does not report file counts; it produces a usage error (see Story 5's non-zero-exit-code precedent) since at least one file is required.

---

## Story 2: Report counts for multiple files with a totals row
**Traces to:** FR1, FR2

**As** Dana the DevOps Engineer,
**I want** to run the CLI on multiple text files at once,
**so that** I can see per-file counts as well as a combined total.

### Acceptance Criteria
- Given two or more existing text files, when I run `textstats <file1> <file2>...`, then the output shows a row of line/word/char counts per file, in the order the files were given.
- When more than one file is given, an additional "total" row is shown summing line, word, and character counts across all given files.
- When exactly one file is given, no totals row is shown (only the single file's counts).
- The totals row is clearly labeled (e.g., "total") and distinguishable from per-file rows.

---

## Story 3: Emit machine-readable JSON output
**Traces to:** FR3

**As** Priya the Automation/Build Engineer,
**I want** to pass a `--json` flag to the CLI,
**so that** I get the same counts as a JSON object on stdout that my scripts can parse.

### Acceptance Criteria
- Given one or more existing text files, when I run `textstats --json <file1> [<file2>...]`, then stdout contains a single valid JSON document (parseable by a standard JSON parser) and nothing else on stdout.
- The JSON output includes, for each input file, its name/path and its line, word, and character counts.
- When multiple files are given, the JSON output also includes a "total" entry with summed line, word, and character counts, structured consistently with per-file entries.
- When exactly one file is given with `--json`, the JSON output does not need a totals entry distinct from the single file's own counts (no totals key required, or a totals key equal to the single file's counts — behavior is documented).
- The JSON output numbers exactly match the numbers shown in the non-JSON (human-readable) mode for the same input files.
- `--json` can be combined with any valid file argument list and produces exit code 0 on success.

---

## Story 4: Clear error and non-zero exit code for missing files
**Traces to:** FR4

**As** Sam the Support/Docs Analyst,
**I want** the CLI to tell me clearly when a file doesn't exist,
**so that** I immediately understand what went wrong instead of getting a confusing crash or silent failure.

### Acceptance Criteria
- Given a file path that does not exist on disk, when I run `textstats <missing-file>`, then the tool prints a clear, human-readable error message identifying the missing file path to stderr.
- The process exits with a non-zero exit code when any input file is missing.
- When a mix of existing and missing files is given, the tool reports the error for the missing file(s) and exits with a non-zero exit code (it does not silently skip missing files and report partial success).
- This missing-file error behavior is consistent whether or not `--json` is passed (error reporting still goes to stderr as plain text, not as JSON, so automated tooling can reliably distinguish error output from JSON success output on stdout).

---

## Story 5: Helpful usage error for invalid invocation
**Traces to:** FR1, FR4 (supports overall CLI usability and fail-fast/clear-error requirements)

**As** Sam the Support/Docs Analyst,
**I want** a clear message when I run the tool without any file arguments,
**so that** I know how to use it correctly.

### Acceptance Criteria
- Given no file arguments, when I run `textstats` (with or without `--json`), then the tool prints a usage/help message to stderr indicating at least one file path is required.
- The process exits with a non-zero exit code when invoked with no file arguments.

---

## Story 6: Confidence via automated unit tests
**Traces to:** NFR1

**As** Priya the Automation/Build Engineer,
**I want** the counting and JSON-output logic to be covered by automated unit tests,
**so that** I can trust the tool's numbers and safely rely on it in CI pipelines.

### Acceptance Criteria
- Unit tests exist that verify line, word, and character counting logic against known sample inputs (happy path and edge cases such as empty file, file without trailing newline, file with only whitespace).
- Unit tests exist that verify the totals-row/aggregation logic across multiple files.
- Unit tests exist that verify the JSON output structure and values match expected counts.
- Unit tests exist that verify missing-file handling produces the expected error and non-zero exit code.
- Running the test suite (`pytest`) completes with zero failures.