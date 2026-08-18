"""Tests for csv2json.cli (Component C) and the run.py entry point.

Covers Story 1 AC4 (missing/invalid input -> exit code + stderr), Story 4
AC1-AC3 (stdout vs file routing, bad output path) via main()'s return
value, and one full end-to-end subprocess smoke test satisfying the
objective success criterion: "CLI converts a sample CSV with a header
row into a JSON array".
"""

from __future__ import annotations

import json
import subprocess
import sys

from csv2json.cli import main


def test_main_success_writes_json_to_stdout(tmp_path, capsys):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("name,age\nAlice,30\nBob,25\n", encoding="utf-8")

    exit_code = main([str(csv_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == [
        {"name": "Alice", "age": "30"},
        {"name": "Bob", "age": "25"},
    ]
    assert captured.err == ""


def test_main_stdout_contains_only_json_on_success(tmp_path, capsys):
    """Story 4 AC1: stdout carries ONLY the JSON, nothing else."""
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("a,b\n1,2\n", encoding="utf-8")

    exit_code = main([str(csv_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    # The full stdout content must parse as JSON on its own -- no extra
    # log lines mixed in before/after it.
    json.loads(captured.out)


def test_main_success_writes_json_to_file(tmp_path, capsys):
    csv_path = tmp_path / "sample.csv"
    out_path = tmp_path / "out.json"
    csv_path.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")

    exit_code = main([str(csv_path), "-o", str(out_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert written == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]


def test_main_missing_input_returns_exit_code_1_and_stderr_message(
    tmp_path, capsys
):
    missing_path = tmp_path / "does_not_exist.csv"

    exit_code = main([str(missing_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() != ""


def test_main_empty_csv_returns_exit_code_1(tmp_path, capsys):
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("", encoding="utf-8")

    exit_code = main([str(csv_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() != ""


def test_main_bad_output_dir_returns_exit_code_2(tmp_path, capsys):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("a,b\n1,2\n", encoding="utf-8")
    bad_output = tmp_path / "no_such_dir" / "out.json"

    exit_code = main([str(csv_path), "-o", str(bad_output)])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert captured.err.strip() != ""


def test_run_py_end_to_end_subprocess(tmp_path):
    """Objective success criterion: CLI converts a sample CSV with a
    header row into a JSON array of row objects, via the real run.py
    entry point in a subprocess (no in-process shortcuts).
    """
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(
        "name,age,city\nAlice,30,\"Springfield, USA\"\nBob,,Shelbyville\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "run.py", str(csv_path)],
        capture_output=True,
        text=True,
        cwd=".",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == [
        {"name": "Alice", "age": "30", "city": "Springfield, USA"},
        {"name": "Bob", "age": "", "city": "Shelbyville"},
    ]


def test_run_py_end_to_end_missing_file_nonzero_exit():
    result = subprocess.run(
        [sys.executable, "run.py", "definitely_missing.csv"],
        capture_output=True,
        text=True,
        cwd=".",
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.strip() != ""
