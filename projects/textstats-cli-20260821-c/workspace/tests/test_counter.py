"""Unit tests for textstats.counter — pure counting logic.

Traces to: FR1, FR2, Story 1, Story 2, Story 6.
"""

from textstats.counter import Stats, count_stats, total_stats


def test_count_stats_empty_text():
    """Empty text has 0 lines, 0 words, 0 chars."""
    result = count_stats("")
    assert result == Stats(lines=0, words=0, chars=0)


def test_count_stats_no_trailing_newline():
    """A final line without a trailing newline still counts as a line."""
    text = "a\nb"
    result = count_stats(text)
    assert result.lines == 2
    assert result.words == 2
    assert result.chars == len(text)


def test_count_stats_with_trailing_newline():
    """Trailing newline does not add an extra (empty) line."""
    text = "a\nb\n"
    result = count_stats(text)
    assert result.lines == 2
    assert result.words == 2
    assert result.chars == len(text)


def test_count_stats_whitespace_only():
    """Whitespace-only text has 0 words but is not necessarily 0 lines."""
    text = "   \n  \n"
    result = count_stats(text)
    assert result.words == 0
    assert result.lines == 2
    assert result.chars == len(text)


def test_count_stats_happy_path_multi_line_multi_word():
    text = "hello world\nfoo bar baz\n"
    result = count_stats(text)
    assert result.lines == 2
    assert result.words == 5
    assert result.chars == len(text)


def test_total_stats_sums_across_multiple_stats():
    stats_list = [
        Stats(lines=3, words=10, chars=42),
        Stats(lines=1, words=2, chars=8),
    ]
    result = total_stats(stats_list)
    assert result == Stats(lines=4, words=12, chars=50)


def test_total_stats_single_stats_is_identity():
    stats_list = [Stats(lines=5, words=7, chars=20)]
    result = total_stats(stats_list)
    assert result == Stats(lines=5, words=7, chars=20)


def test_total_stats_empty_iterable_is_zero():
    result = total_stats([])
    assert result == Stats(lines=0, words=0, chars=0)
