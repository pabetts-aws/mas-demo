"""csv2json — convert CSV files (with a header row) to a JSON array of objects.

Public API re-exported for convenience:

    from csv2json import convert_csv_text_to_json_string, CsvConversionError
"""

from csv2json.converter import (
    CsvConversionError,
    convert_csv_text_to_json_string,
    csv_rows_to_json_records,
)

__all__ = [
    "CsvConversionError",
    "convert_csv_text_to_json_string",
    "csv_rows_to_json_records",
]

__version__ = "1.0.0"
