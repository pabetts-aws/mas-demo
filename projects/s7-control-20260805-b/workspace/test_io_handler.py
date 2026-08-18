"""Unit tests for csv2json.io_handler (Component B).

Covers Story 4 AC1-AC3 (stdout vs file, bad output path) and Story 2 AC2
(newline handling via open_input's newline='' setting), per
docs/requirements.md and docs/components.md's test plan mapping.
"""

from __future__ import annotations

import json

import pytest

from csv2json.io_handler import (
    InputError,
    OutputError,
    open_input,
    write_output,
)


def test_open_input_success(tmp_path):
    path = tmp_path / "sample.csv"
    path.write_text("a,b\n1,2\n", encoding="utf-8")

    fh = open_input(str(path))
    try:
        assert fh.read() == "a,b\n1,2\n"
    finally:
        fh.close()


def test_open_input_missing_file_raises_input_error(tmp_path):
    missing_path = tmp_path / "does_not_exist.csv"

    with pytest.raises(InputError):
        open_input(str(missing_path))


def test_open_input_preserves_embedded_newlines(tmp_path):
    """Story 2 AC2: newline='' means the csv module -- not universal
    newline translation -- controls newlines inside quoted fields.
    """
    path = tmp_path / "multiline.csv"
    raw = 'name,note\n"Alice","line one\nline two"\n'
    path.write_bytes(raw.encode("utf-8"))

    fh = open_input(str(path))
    try:
        content = fh.read()
    finally:
        fh.close()

    assert content == raw


def test_write_output_to_stdout(capsys):
    records = [{"a": "1", "b": "2"}]
    write_output(records, None)

    captured = capsys.readouterr()
    assert json.loads(captured.out) == records
    assert captured.err == ""


def test_write_output_to_file(tmp_path):
    output_path = tmp_path / "out.json"
    records = [{"a": "1", "b": "2"}, {"a": "3", "b": ""}]

    write_output(records, str(output_path))

    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written == records


def test_write_output_bad_directory_raises_output_error(tmp_path):
    bad_path = tmp_path / "no_such_dir" / "out.json"

    with pytest.raises(OutputError):
        write_output([{"a": "1"}], str(bad_path))
