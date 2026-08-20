## Requirements for Text Statistics CLI Tool

### Functional Requirements
1. **FR1:** The tool must report line, word, and character counts for one or more input text files.
   - **Priority:** Must-have
   - **Testable:** Yes, by providing sample text files and verifying the output.

2. **FR2:** The tool must include a totals row when multiple files are given.
   - **Priority:** Must-have
   - **Testable:** Yes, by providing multiple text files and verifying the totals.

3. **FR3:** The tool must support a `--json` flag that emits the same numbers as a JSON object to stdout.
   - **Priority:** Must-have
   - **Testable:** Yes, by running the tool with the `--json` flag and verifying the JSON output.

4. **FR4:** The tool must handle missing files with a clear error message and a non-zero exit code.
   - **Priority:** Must-have
   - **Testable:** Yes, by providing a non-existent file and verifying the error message and exit code.

### Non-Functional Requirements
1. **NFR1:** The tool must have unit tests for the counting and JSON output logic.
   - **Priority:** Must-have
   - **Testable:** Yes, by running the unit tests and verifying they pass.

### Constraints
1. **C1:** The tool must be a small CLI application.
   - **Priority:** Must-have

### Assumptions
1. **A1:** The input text files will be in a format that the tool can read (e.g., UTF-8 encoded).
   - **Priority:** Must-have