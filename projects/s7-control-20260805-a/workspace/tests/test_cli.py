"""Unit/integration tests for csv2json.cli (Component: CLI).

Traces to: FR1, FR5, NFR1 (Stories 1, 5, 6) — see docs/components.md
"Testing component map" and docs/code-generation-plan.md step 8. Tests call
``cli.main()`` in-process (no subprocess) per Decision D8.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from csv2json.cli import EXIT_CONVERSION_ERROR, EXIT_INPUT_ERROR, EXIT_OK, main

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# FR1: accept a valid input CSV file path as a CLI argument
# ---------------------------------------------------------------------------


def test_main_returns_zero_for_valid_csv_path(tmp_path, capsys):
    csv_path = tmp_path / "in.csv"
    csv_path.write_text("name,age\nAda,36\n", encoding="utf-8")

    exit_code = main([str(csv_path)])

    assert exit_code == EXIT_OK


def test_main_returns_one_for_missing_input_file(tmp_path, capsys):
    missing_path = tmp_path / "does-not-exist.csv"

    exit_code = main([str(missing_path)])
    captured = capsys.readouterr()

    assert exit_code == EXIT_INPUT_ERROR
    assert "does-not-exist.csv" in captured.err


# ---------------------------------------------------------------------------
# FR5: emit the JSON array to stdout (default) or to an output file (-o)
# ---------------------------------------------------------------------------


def test_main_writes_json_array_to_stdout_by_default(tmp_path, capsys):
    csv_path = tmp_path / "in.csv"
    csv_path.write_text("name,age\nAda,36\nBram,28\n", encoding="utf-8")

    exit_code = main([str(csv_path)])
    captured = capsys.readouterr()

    assert exit_code == EXIT_OK
    payload = json.loads(captured.out)
    assert payload == [
        {"name": "Ada", "age": "36"},
        {"name": "Bram", "age": "28"},
    ]


def test_main_writes_json_array_to_output_file_when_dash_o_given(tmp_path, capsys):
    csv_path = tmp_path / "in.csv"
    csv_path.write_text("name,age\nAda,36\n", encoding="utf-8")
    out_path = tmp_path / "out.json"

    exit_code = main([str(csv_path), "-o", str(out_path)])
    captured = capsys.readouterr()

    assert exit_code == EXIT_OK
    assert captured.out == ""  # nothing on stdout when writing to a file
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload == [{"name": "Ada", "age": "36"}]


def test_main_long_form_output_flag_also_works(tmp_path):
    csv_path = tmp_path / "in.csv"
    csv_path.write_text("a\n1\n", encoding="utf-8")
    out_path = tmp_path / "out.json"

    exit_code = main([str(csv_path), "--output", str(out_path)])

    assert exit_code == EXIT_OK
    assert json.loads(out_path.read_text(encoding="utf-8")) == [{"a": "1"}]


# ---------------------------------------------------------------------------
# FR4 (via CLI): quoted fields and empty values survive end-to-end
# ---------------------------------------------------------------------------


def test_main_end_to_end_with_sample_fixture_handles_quotes_and_empty_values(capsys):
    sample_path = FIXTURES_DIR / "sample.csv"

    exit_code = main([str(sample_path)])
    captured = capsys.readouterr()

    assert exit_code == EXIT_OK
    payload = json.loads(captured.out)
    assert payload == [
        {"name": "Ada", "city": "London", "notes": "first, computer programmer"},
        {"name": "Bram", "city": "Amsterdam", "notes": ""},
        {"name": "Chen", "city": "Beijing", "notes": 'loves "quotes" and, commas'},
    ]


# ---------------------------------------------------------------------------
# Exit code 2: CSV conversion errors (e.g. no header row)
# ---------------------------------------------------------------------------


def test_main_returns_two_for_empty_csv_with_no_header(tmp_path, capsys):
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("", encoding="utf-8")

    exit_code = main([str(csv_path)])
    captured = capsys.readouterr()

    assert exit_code == EXIT_CONVERSION_ERROR
    assert "error" in captured.err.lower()


# ---------------------------------------------------------------------------
# --indent flag
# ---------------------------------------------------------------------------


def test_main_indent_zero_produces_compact_json(tmp_path, capsys):
    csv_path = tmp_path / "in.csv"
    csv_path.write_text("a\n1\n", encoding="utf-8")

    exit_code = main([str(csv_path), "--indent", "0"])
    captured = capsys.readouterr()

    assert exit_code == EXIT_OK
    assert "\n" not in captured.out.strip()
    assert json.loads(captured.out) == [{"a": "1"}]


def test_main_with_no_args_raises_systemexit_from_argparse():
    with pytest.raises(SystemExit):
        main([])
