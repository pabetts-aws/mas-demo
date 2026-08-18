"""Unit tests for csv2json.converter (pure conversion logic).

Traces to: FR2, FR3, FR4, NFR1 (Stories 2, 3, 4, 6) — see
docs/components.md "Testing component map" and docs/code-generation-plan.md
step 7.
"""

from __future__ import annotations

import csv
import io
import json

import pytest

from csv2json.converter import (
    CsvConversionError,
    convert_csv_text_to_json_string,
    csv_rows_to_json_records,
)

# ---------------------------------------------------------------------------
# FR2/FR3: parsing a CSV with a header row into a JSON array of row objects
# ---------------------------------------------------------------------------


def test_simple_csv_converts_to_list_of_dicts_preserving_order():
    csv_text = "name,age\nAda,36\nBram,28\n"

    result = json.loads(convert_csv_text_to_json_string(csv_text))

    assert result == [
        {"name": "Ada", "age": "36"},
        {"name": "Bram", "age": "28"},
    ]


def test_row_object_keys_follow_header_order():
    csv_text = "c,a,b\n1,2,3\n"

    result = json.loads(convert_csv_text_to_json_string(csv_text))

    assert list(result[0].keys()) == ["c", "a", "b"]


def test_header_only_csv_returns_empty_json_array():
    csv_text = "name,age\n"

    result = json.loads(convert_csv_text_to_json_string(csv_text))

    assert result == []


def test_rows_preserved_in_source_order():
    csv_text = "id\n3\n1\n2\n"

    result = json.loads(convert_csv_text_to_json_string(csv_text))

    assert [row["id"] for row in result] == ["3", "1", "2"]


# ---------------------------------------------------------------------------
# FR4: quoted fields (embedded commas, escaped quotes, embedded newlines)
# ---------------------------------------------------------------------------


def test_quoted_field_with_embedded_comma_is_kept_as_one_field():
    csv_text = 'name,notes\nAda,"first, computer programmer"\n'

    result = json.loads(convert_csv_text_to_json_string(csv_text))

    assert result == [{"name": "Ada", "notes": "first, computer programmer"}]


def test_quoted_field_with_escaped_double_quotes():
    csv_text = 'name,notes\nChen,"loves ""quotes"" a lot"\n'

    result = json.loads(convert_csv_text_to_json_string(csv_text))

    assert result[0]["notes"] == 'loves "quotes" a lot'


def test_quoted_field_with_embedded_newline_is_preserved_as_single_field():
    csv_text = 'name,bio\nDana,"Line one\nLine two"\n'

    result = json.loads(convert_csv_text_to_json_string(csv_text))

    assert len(result) == 1
    assert result[0]["name"] == "Dana"
    assert "Line one" in result[0]["bio"]
    assert "Line two" in result[0]["bio"]


# ---------------------------------------------------------------------------
# FR4: empty values, and the empty-string-vs-null distinction (Decision D4)
# ---------------------------------------------------------------------------


def test_empty_field_between_commas_becomes_empty_string_not_null():
    csv_text = "a,b,c\n1,,3\n"

    result = json.loads(convert_csv_text_to_json_string(csv_text))

    assert result == [{"a": "1", "b": "", "c": "3"}]


def test_short_row_missing_trailing_fields_becomes_null():
    csv_text = "a,b,c\n1\n"

    result = json.loads(convert_csv_text_to_json_string(csv_text))

    assert result == [{"a": "1", "b": None, "c": None}]


def test_quoted_empty_field_becomes_empty_string():
    csv_text = 'a,b\nAda,""\n'

    result = json.loads(convert_csv_text_to_json_string(csv_text))

    assert result == [{"a": "Ada", "b": ""}]


# ---------------------------------------------------------------------------
# NFR1 / A1: error handling for malformed input
# ---------------------------------------------------------------------------


def test_empty_csv_text_raises_csv_conversion_error():
    with pytest.raises(CsvConversionError):
        convert_csv_text_to_json_string("")


def test_csv_rows_to_json_records_raises_on_missing_header_directly():
    reader = csv.DictReader(io.StringIO(""))

    with pytest.raises(CsvConversionError):
        csv_rows_to_json_records(reader)


def test_csv_rows_to_json_records_accepts_pre_built_dictreader():
    reader = csv.DictReader(io.StringIO("x,y\n1,2\n"))

    records = csv_rows_to_json_records(reader)

    assert records == [{"x": "1", "y": "2"}]


# ---------------------------------------------------------------------------
# indent behavior
# ---------------------------------------------------------------------------


def test_indent_none_produces_compact_single_line_json():
    csv_text = "a\n1\n"

    compact = convert_csv_text_to_json_string(csv_text, indent=None)

    assert "\n" not in compact
    assert json.loads(compact) == [{"a": "1"}]


def test_default_indent_pretty_prints():
    csv_text = "a\n1\n"

    pretty = convert_csv_text_to_json_string(csv_text)

    assert "\n" in pretty
    assert json.loads(pretty) == [{"a": "1"}]
