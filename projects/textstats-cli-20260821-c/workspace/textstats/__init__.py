"""Text Statistics CLI Tool.

A small package that reports line, word, and character counts for one or
more input text files, with optional JSON output.

Public API re-exported for convenience:
    textstats.counter.Stats / count_stats / total_stats
    textstats.formatting.format_human / format_json
    textstats.cli.main
"""

from textstats.cli import main
from textstats.counter import Stats, count_stats, total_stats
from textstats.formatting import format_human, format_json

__all__ = [
    "Stats",
    "count_stats",
    "format_human",
    "format_json",
    "main",
    "total_stats",
]
