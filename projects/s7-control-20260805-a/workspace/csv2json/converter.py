"""Pure CSV -> JSON conversion logic (Component: Converter).

No file I/O, no argv, no stdout/stderr access happens in this module. It
consumes CSV text or an already-constructed csv.DictReader and returns
plain Python data / JSON strings. This is what makes it independently
unit-testable per NFR1 (see docs/components.md, docs/decisions.md D1/D3/D4).
"""

from __future__ import annotations

import csv
import io
import json


class CsvConversionError(Exception):
    """Raised for conversion-level failures.

    Currently the only case: the CSV input has no header row at all
    (an empty file, or a file with no columns), which violates assumption
    A1 ("the input CSV file will have a header row").
    """


def csv_rows_to_json_records(
    reader: csv.DictReader[str],
) -> list[dict[str, str | None]]:
    """Consume a csv.DictReader and return a list of plain dicts.

    - Preserves column order via the header row (dict insertion order
      matches header order because csv.DictReader builds each row dict by
      iterating fieldnames in header order).
    - An empty field present in a row is preserved as ``""`` (Decision D4).
    - A short row (fewer fields than headers) yields ``None`` for the
      missing trailing key(s), passed through unchanged (Decision D4);
      this serializes to JSON ``null``.
    - Extra fields beyond the header (csv.DictReader's ``restkey``,
      normally ``None``-keyed) are dropped, since they cannot be
      represented as a named JSON key.
    - Rows are returned in the same order as they appear in the source.
    - A header-only CSV (headers present, zero data rows) returns [].

    Raises:
        CsvConversionError: if the reader has no header row (fieldnames is
            falsy), meaning the CSV had no header/columns at all.
    """
    if not reader.fieldnames:
        raise CsvConversionError("CSV has no header row")

    records: list[dict[str, str | None]] = []
    for row in reader:
        # csv.DictReader may add a None key (restkey) for rows with extra
        # fields beyond the header; drop it since it has no JSON-safe name.
        row.pop(None, None)
        records.append(dict(row))
    return records


def convert_csv_text_to_json_string(
    csv_text: str,
    *,
    indent: int | None = 2,
) -> str:
    """Parse csv_text (must have a header row) and return a JSON string.

    Args:
        csv_text: The full CSV file content, including the header row.
            May contain quoted fields with embedded commas, escaped quotes
            (``""``), and embedded newlines.
        indent: Passed through to json.dumps. ``None`` produces compact
            single-line JSON; an int pretty-prints with that indent.

    Returns:
        A JSON string encoding a JSON array of row objects.

    Raises:
        CsvConversionError: if csv_text has no header row (e.g. empty
            input).

    Note:
        The input is wrapped in ``io.StringIO`` (not ``str.splitlines()``)
        before being handed to ``csv.reader``/``csv.DictReader`` so that
        quoted fields spanning multiple physical lines (embedded newlines)
        are reassembled correctly by the csv module, per Decision D3.
    """
    reader: csv.DictReader[str] = csv.DictReader(io.StringIO(csv_text))
    records = csv_rows_to_json_records(reader)
    return json.dumps(records, indent=indent)
