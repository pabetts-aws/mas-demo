"""Unit tests for csv2json.converter (Component A).

Covers T1 (basic conversion), T2 (quoted fields), T3 (empty values), and
part of T5 (10,000-row correctness + timing), per docs/requirements.md
and docs/stories.md Story 1, 2, 3, 5.
"""

from __future__ import annotations

import io
import time

import pytest

from csv2json.converter import csv_rows_to_records


def test_basic_conversion():
    """T1 / Story 1: header row + data rows -> list of dicts, in order."""
    csv_text = "name,age,city\nAlice,30,Springfield\nBob,25,Shelbyville\n"
    records = csv_rows_to_records(io.StringIO(csv_text))

    assert records == [
        {"name": "Alice", "age": "30", "city": "Springfield"},
        {"name": "Bob", "age": "25", "city": "Shelbyville"},
    ]


def test_row_count_matches_data_rows():
    """Story 1 AC2: number of JSON objects equals number of data rows."""
    csv_text = "a,b\n1,2\n3,4\n5,6\n"
    records = csv_rows_to_records(io.StringIO(csv_text))
    assert len(records) == 3


def test_row_order_preserved():
    """Story 1 AC3: row order in output matches row order in input."""
    csv_text = "id\n3\n1\n2\n"
    records = csv_rows_to_records(io.StringIO(csv_text))
    assert [r["id"] for r in records] == ["3", "1", "2"]


def test_quoted_field_with_comma():
    """T2 / Story 2 AC1: quoted field with an embedded comma stays intact."""
    csv_text = 'name,age\n"Smith, John",42\n'
    records = csv_rows_to_records(io.StringIO(csv_text))
    assert records == [{"name": "Smith, John", "age": "42"}]


def test_quoted_field_with_newline():
    """T2 / Story 2 AC2: quoted field with an embedded newline is preserved."""
    csv_text = 'name,note\n"Alice","line one\nline two"\n'
    records = csv_rows_to_records(io.StringIO(csv_text))
    assert records == [{"name": "Alice", "note": "line one\nline two"}]


def test_quoted_field_with_escaped_quote():
    """T2 / Story 2 AC3: escaped double quote decodes to a literal quote."""
    csv_text = 'quote,count\n"She said ""hi""",5\n'
    records = csv_rows_to_records(io.StringIO(csv_text))
    assert records == [{"quote": 'She said "hi"', "count": "5"}]


def test_mixed_quoted_and_unquoted_fields():
    """T2 / Story 2 AC4: quoted and unquoted fields coexist in one row."""
    csv_text = 'a,b,c\n"x,y",plain,"z""z"\n'
    records = csv_rows_to_records(io.StringIO(csv_text))
    assert records == [{"a": "x,y", "b": "plain", "c": 'z"z'}]


def test_empty_middle_value():
    """T3 / Story 3 AC1: empty field between two commas -> "" , key present."""
    csv_text = "a,b,c\n1,,3\n"
    records = csv_rows_to_records(io.StringIO(csv_text))
    assert records == [{"a": "1", "b": "", "c": "3"}]


def test_empty_trailing_value():
    """T3 / Story 3 AC2: empty trailing field -> "" for the last key."""
    csv_text = "a,b,c\n1,2,\n"
    records = csv_rows_to_records(io.StringIO(csv_text))
    assert records == [{"a": "1", "b": "2", "c": ""}]


def test_empty_leading_value():
    """T3: empty leading field -> "" for the first key."""
    csv_text = "a,b,c\n,2,3\n"
    records = csv_rows_to_records(io.StringIO(csv_text))
    assert records == [{"a": "", "b": "2", "c": "3"}]


def test_short_row_padded_with_restval():
    """T3 / Story 3: a data row shorter than the header gets "" via restval."""
    csv_text = "a,b,c\n1\n"
    records = csv_rows_to_records(io.StringIO(csv_text))
    assert records == [{"a": "1", "b": "", "c": ""}]


def test_blank_line_is_skipped():
    """T3 / Story 3 AC3: a completely blank line does not crash the tool
    and does not produce a spurious record (documented, consistent rule).
    """
    csv_text = "a,b\n1,2\n\n3,4\n"
    records = csv_rows_to_records(io.StringIO(csv_text))
    assert records == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]


def test_empty_file_raises_value_error():
    """An entirely empty input (no header row) raises ValueError."""
    with pytest.raises(ValueError):
        csv_rows_to_records(io.StringIO(""))


def test_header_only_file_yields_empty_list():
    """A header row with no data rows yields an empty list, not an error."""
    records = csv_rows_to_records(io.StringIO("a,b,c\n"))
    assert records == []


def test_large_file_performance_and_correctness():
    """T5 / Story 5: 10,000 rows convert within 10 seconds, correctly and
    in order.
    """
    header = "id,name,value\n"
    rows = [f"{i},name-{i},value-{i}\n" for i in range(10_000)]
    csv_text = header + "".join(rows)

    start = time.monotonic()
    records = csv_rows_to_records(io.StringIO(csv_text))
    elapsed = time.monotonic() - start

    assert elapsed < 10.0
    assert len(records) == 10_000
    assert records[0] == {"id": "0", "name": "name-0", "value": "value-0"}
    assert records[-1] == {
        "id": "9999",
        "name": "name-9999",
        "value": "value-9999",
    }
    # order preserved
    assert [r["id"] for r in records] == [str(i) for i in range(10_000)]
