## Requirements for CSV to JSON CLI Tool

### Functional Requirements
1. **FR1**: The tool must accept an input CSV file path as a command-line argument.
   - Priority: Must-Have
   - Test: Verify that the tool accepts a valid CSV file path.
2. **FR2**: The tool must read the input CSV file and parse it into a data structure.
   - Priority: Must-Have
   - Test: Verify that the tool correctly parses a sample CSV file.
3. **FR3**: The tool must handle CSV files with a header row and convert them into a JSON array of row objects.
   - Priority: Must-Have
   - Test: Verify that the tool converts a sample CSV with a header row into a valid JSON array.
4. **FR4**: The tool must handle quoted fields and empty values in the CSV file.
   - Priority: Must-Have
   - Test: Verify that the tool correctly handles quoted fields and empty values in the CSV file.
5. **FR5**: The tool must emit the JSON array to stdout or an output file specified by the user.
   - Priority: Must-Have
   - Test: Verify that the tool emits the JSON array to stdout or an output file.

### Non-Functional Requirements
1. **NFR1**: The tool must have unit tests for the conversion logic.
   - Priority: Must-Have
   - Test: Verify that the pytest suite passes with zero failures.

### Constraints
1. **C1**: The tool must be implemented in Python.
   - Priority: Must-Have

### Assumptions
1. **A1**: The input CSV file will have a header row.
   - Priority: Must-Have