"""Unit tests for textstats.formatting — pure presentation logic.

Traces to: FR2, FR3, Story 2, Story 3, Story 6.
"""

import json

from textstats.counter import Stats
from textstats.formatting import format_human, format_json


def test_format_human_single_file_no_total_row():
    results = [("a.txt", Stats(lines=3, words=10, chars=42))]
    output = format_human(results, None)
    lines = output.splitlines()
    assert lines[0].split() == ["File", "Lines", "Words", "Chars"]
    assert "a.txt" in lines[1]
    assert "3" in lines[1] and "10" in lines[1] and "42" in lines[1]
    assert not any("total" in line for line in lines)


def test_format_human_multiple_files_with_total_row():
    results = [
        ("a.txt", Stats(lines=3, words=10, chars=42)),
        ("b.txt", Stats(lines=1, words=2, chars=8)),
    ]
    total = Stats(lines=4, words=12, chars=50)
    output = format_human(results, total)
    lines = output.splitlines()
    assert len(lines) == 4  # header + 2 files + total
    assert lines[-1].startswith("total")
    assert "4" in lines[-1] and "12" in lines[-1] and "50" in lines[-1]


def test_format_json_single_file_no_total_key():
    results = [("a.txt", Stats(lines=3, words=10, chars=42))]
    output = format_json(results, None)
    payload = json.loads(output)
    assert payload["files"] == [
        {"file": "a.txt", "lines": 3, "words": 10, "chars": 42}
    ]
    assert "total" not in payload


def test_format_json_multiple_files_with_total_key():
    results = [
        ("a.txt", Stats(lines=3, words=10, chars=42)),
        ("b.txt", Stats(lines=1, words=2, chars=8)),
    ]
    total = Stats(lines=4, words=12, chars=50)
    output = format_json(results, total)
    payload = json.loads(output)
    assert payload["files"] == [
        {"file": "a.txt", "lines": 3, "words": 10, "chars": 42},
        {"file": "b.txt", "lines": 1, "words": 2, "chars": 8},
    ]
    assert payload["total"] == {"lines": 4, "words": 12, "chars": 50}


def test_format_json_output_is_valid_json_document():
    results = [("a.txt", Stats(lines=1, words=1, chars=1))]
    output = format_json(results, None)
    # Must not raise, and must be a single JSON document.
    parsed = json.loads(output)
    assert isinstance(parsed, dict)


def test_format_json_matches_format_human_numbers():
    results = [
        ("a.txt", Stats(lines=3, words=10, chars=42)),
        ("b.txt", Stats(lines=1, words=2, chars=8)),
    ]
    total = Stats(lines=4, words=12, chars=50)

    human_output = format_human(results, total)
    json_output = json.loads(format_json(results, total))

    for label, stats in results:
        assert str(stats.lines) in human_output
        assert str(stats.words) in human_output
        assert str(stats.chars) in human_output

    assert json_output["total"]["lines"] == total.lines
    assert json_output["total"]["words"] == total.words
    assert json_output["total"]["chars"] == total.chars
