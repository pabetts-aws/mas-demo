"""Integration tests for textstats.cli.main — end-to-end CLI behavior.

Traces to: FR1, FR2, FR3, FR4, Story 1, Story 2, Story 3, Story 4, Story 5,
Story 6.

Uses tmp_path fixtures to create throwaway files, keeping the suite
hermetic and fast (no dependency on real production files).
"""

import json
import subprocess
import sys

import pytest

from textstats.cli import main


def _write(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return str(path)


def _has_total_row(output: str) -> bool:
    """True if any output line's first column is the literal label 'total'.

    Deliberately stricter than a bare substring check: pytest's tmp_path
    fixture embeds the test's own name in the temp directory path (e.g.
    ".../test_single_file_no_total_row0/a.txt"), which can itself contain
    the substring "total" and produce a false positive.
    """
    return any(line.split()[0] == "total" for line in output.splitlines() if line.strip())


def test_single_file_happy_path(tmp_path, capsys):
    file_path = _write(tmp_path, "a.txt", "hello world\nfoo\n")

    exit_code = main([file_path])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert file_path in captured.out
    assert not _has_total_row(captured.out)


def test_multiple_files_show_total_row(tmp_path, capsys):
    file_a = _write(tmp_path, "a.txt", "hello world\n")
    file_b = _write(tmp_path, "b.txt", "one\n")

    exit_code = main([file_a, file_b])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert _has_total_row(captured.out)
    assert file_a in captured.out
    assert file_b in captured.out


def test_single_file_no_total_row(tmp_path, capsys):
    file_path = _write(tmp_path, "a.txt", "hello world\n")

    exit_code = main([file_path])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert not _has_total_row(captured.out)


def test_missing_file_error_and_exit_code(tmp_path, capsys):
    missing_path = str(tmp_path / "does_not_exist.txt")

    exit_code = main([missing_path])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert missing_path in captured.err
    assert "file not found" in captured.err.lower()


def test_mixed_existing_and_missing_files_fails_closed(tmp_path, capsys):
    existing = _write(tmp_path, "a.txt", "hello\n")
    missing_path = str(tmp_path / "does_not_exist.txt")

    exit_code = main([existing, missing_path])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""  # no partial success
    assert missing_path in captured.err


def test_json_flag_produces_valid_json_on_stdout_only(tmp_path, capsys):
    file_path = _write(tmp_path, "a.txt", "hello world\nfoo\n")

    exit_code = main(["--json", file_path])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["files"][0]["file"] == file_path
    assert "total" not in payload


def test_json_flag_with_multiple_files_includes_total(tmp_path, capsys):
    file_a = _write(tmp_path, "a.txt", "hello world\n")
    file_b = _write(tmp_path, "b.txt", "one\n")

    exit_code = main(["--json", file_a, file_b])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert len(payload["files"]) == 2
    assert "total" in payload


def test_json_flag_with_missing_file_errors_on_stderr_as_plain_text(tmp_path, capsys):
    missing_path = str(tmp_path / "does_not_exist.txt")

    exit_code = main(["--json", missing_path])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "file not found" in captured.err.lower()
    with pytest.raises(json.JSONDecodeError):
        json.loads(captured.err)


def test_no_arguments_usage_error(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main([])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "usage" in captured.err.lower()


def test_console_script_smoke(tmp_path):
    """Optional subprocess smoke test proving the packaged wiring works
    end-to-end outside the in-process test harness (docs/decisions.md D10).
    """
    file_path = _write(tmp_path, "a.txt", "hello world\n")

    result = subprocess.run(
        [sys.executable, "-m", "textstats", file_path],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert file_path in result.stdout
