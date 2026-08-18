# User Stories for CSV to JSON CLI Tool

Each story traces to one or more requirements from `docs/requirements.md`.

---

## Story 1: Convert a CSV file with a header row into a JSON array
**Traces to**: FR1, C1, A1 (T1)

**As** Dana the Data Engineer,
**I want** to run the CLI tool against a CSV file that has a header row,
**so that** I get a JSON array of objects, one per data row, keyed by the header column names.

### Acceptance Criteria
- Given a valid CSV file whose first row is a header row, when I run the CLI with that file as input, then the tool emits a JSON array where each element is an object mapping header names to that row's values.
- The number of JSON objects in the array equals the number of data rows in the CSV (excluding the header row).
- The order of JSON objects in the array matches the order of rows in the CSV file.
- If the input file does not exist or is not a valid CSV with a header row, the tool exits with a non-zero status and prints a clear error message (does not silently produce empty/incorrect output).

---

## Story 2: Correctly handle quoted CSV fields
**Traces to**: FR2 (T2)

**As** Dana the Data Engineer,
**I want** the tool to correctly parse fields that are wrapped in double quotes, including quoted fields containing commas, newlines, or escaped quotes,
**so that** my structured text data isn't corrupted or split incorrectly when converted to JSON.

### Acceptance Criteria
- Given a CSV row containing a quoted field with an embedded comma (e.g. `"Smith, John",42`), when converted, the JSON object contains the comma-inclusive value as a single field.
- Given a CSV row containing a quoted field with an embedded newline, when converted, the JSON object contains the field value with the newline preserved.
- Given a CSV row containing a quoted field with an escaped double quote (e.g. `"She said ""hi""",5`), when converted, the JSON value contains a literal `"` character correctly unescaped.
- Unquoted fields continue to be parsed normally alongside quoted fields in the same row.

---

## Story 3: Correctly handle empty values
**Traces to**: FR3 (T3)

**As** Sam the Support/Ops Analyst,
**I want** empty CSV cells to be represented sensibly in the JSON output,
**so that** I can tell the difference between "no value" and a value that happens to look empty, without the tool crashing or misaligning columns.

### Acceptance Criteria
- Given a CSV row with an empty field between two commas (e.g. `a,,c`), when converted, the corresponding JSON object has that key present with an empty string value (`""`), not omitted, `null` by default, or shifted to the wrong key.
- Given a CSV row where the trailing field is empty (e.g. `a,b,`), the resulting JSON object still has all header keys present with the last one set to `""`.
- A completely empty line in the CSV (if present) does not crash the tool; it is handled per a documented, consistent rule (e.g. skipped or represented as a row of empty strings).

---

## Story 4: Choose stdout or a file for JSON output
**Traces to**: FR4 (T4)

**As** Priya the Platform/Automation Engineer,
**I want** to control whether the tool prints JSON to stdout or writes it to a specified output file,
**so that** I can pipe the output into another program or save it as an artifact in an automated pipeline.

### Acceptance Criteria
- Given no output-file option is specified, when I run the CLI, then the JSON array is written to stdout and nothing else pollutes stdout (diagnostics/errors go to stderr).
- Given an output-file option (e.g. `--output out.json`) is specified, when I run the CLI, then the JSON array is written to that file and stdout remains empty (or only shows a short confirmation on stderr), and the file contains valid JSON matching the CSV content.
- If the specified output path's directory does not exist or is not writable, the tool exits with a non-zero status and a clear error message rather than failing silently.

---

## Story 5: Process large CSV files within a reasonable time
**Traces to**: NFR1 (T5)

**As** Priya the Platform/Automation Engineer,
**I want** the tool to convert CSV files with up to 10,000 rows in under 10 seconds,
**so that** I can rely on it as a non-blocking step in automated pipelines without custom timeout handling.

### Acceptance Criteria
- Given a CSV file with 10,000 data rows and a header row, when converted on typical developer/CI hardware, the tool completes (writes full JSON output) in under 10 seconds.
- The tool does not load the entire result into memory in a way that causes excessive slowdown for files of this size (reasonable streaming/parsing approach).
- Correctness (all rows converted, in order) is preserved at this scale — performance must not come at the cost of dropped or malformed rows.

---

## Traceability Summary

| Story | Requirement(s) | Test(s) |
|---|---|---|
| Story 1 | FR1, C1, A1 | T1 |
| Story 2 | FR2 | T2 |
| Story 3 | FR3 | T3 |
| Story 4 | FR4 | T4 |
| Story 5 | NFR1 | T5 |
