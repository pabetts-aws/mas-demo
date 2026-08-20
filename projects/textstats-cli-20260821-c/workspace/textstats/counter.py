"""Pure counting logic for the Text Statistics CLI Tool.

No file I/O, no argv handling, no printing — just string-in, Stats-out.
See docs/decisions.md D4 for the exact counting-rule rationale.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Stats:
    """Line, word, and character counts for a single piece of text."""

    lines: int
    words: int
    chars: int


def count_stats(text: str) -> Stats:
    """Count lines, words, and chars in a string of file content.

    Rules (docs/decisions.md D4):
      - lines = len(text.splitlines()) — counts a final line even without a
        trailing newline; empty text -> 0 lines.
      - words = len(text.split()) — whitespace-delimited tokens; consecutive
        whitespace collapses; whitespace-only text -> 0 words.
      - chars = len(text) — raw character count, including whitespace and
        newline characters.
    """
    return Stats(
        lines=len(text.splitlines()),
        words=len(text.split()),
        chars=len(text),
    )


def total_stats(all_stats: Iterable[Stats]) -> Stats:
    """Sum lines/words/chars across multiple Stats.

    Given zero Stats, returns Stats(0, 0, 0).
    """
    total_lines = 0
    total_words = 0
    total_chars = 0
    for stats in all_stats:
        total_lines += stats.lines
        total_words += stats.words
        total_chars += stats.chars
    return Stats(lines=total_lines, words=total_words, chars=total_chars)
