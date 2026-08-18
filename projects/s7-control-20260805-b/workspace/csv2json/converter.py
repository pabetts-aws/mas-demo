"""Component A: pure CSV -> in-memory records conversion.

No file I/O, no stdout, no sys.exit here. This module only knows how to
turn an already-open, readable text-mode file-like object into a list of
ordered dicts. Keeping this pure is what makes it directly unit-testable
with io.StringIO (see test_converter.py).
"""

from __future__ import annotations

import csv
from typing import TextIO


def csv_rows_to_records(csv_file: TextIO) -> list[dict[str, str]]:
    """Read CSV text from an open, readable text-mode file-like object.

    The first row of `csv_file` must be a header row. Returns a list of
    dicts, one per data row, mapping header names to string values, in
    file order.

    Behavioral contract:
    - Uses csv.DictReader(csv_file, restval="") so that a data row with
      fewer fields than the header gets "" for the missing trailing
      fields (never None, never omitted) -- this satisfies FR3 / Story 3.
    - Empty cells (leading, middle, or trailing) are represented as ""
      in the resulting dict -- never omitted, never null.
    - A data row *longer* than the header produces an extra key under
      csv.DictReader's default `restkey=None`; that key's value is a list
      of the surplus fields. This is standard-library default behavior,
      documented here and in docs/usage.md rather than silently hidden.
    - A completely blank line in the input is skipped, per csv.reader's
      default behavior for blank lines -- this is the documented,
      consistent rule required by Story 3 AC3.
    - Row order in the output list equals row order in the input file;
      no re-ordering or sorting happens anywhere in this function.
    - Parsing is streamed via csv.DictReader iterating over `csv_file`
      (no upfront `.read()` of the whole file into a string), which keeps
      the parse step itself efficient for large files (NFR1 / Story 5).
      The full result is still materialized as a list because a JSON
      array output requires the complete structure.

    Raises:
        ValueError: if the file is empty (no header row at all).
        csv.Error: on structurally malformed CSV that Python's csv module
            cannot parse (e.g. an unterminated quote).
    """
    reader = csv.DictReader(csv_file, restval="")

    if reader.fieldnames is None:
        # DictReader.fieldnames triggers reading the header row lazily;
        # if the file has no content at all, fieldnames stays None.
        raise ValueError("CSV input is empty; a header row is required")

    records: list[dict[str, str]] = []
    for row in reader:
        records.append(dict(row))

    return records
