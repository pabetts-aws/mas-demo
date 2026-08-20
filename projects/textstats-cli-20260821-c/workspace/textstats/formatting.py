"""Pure presentation logic for the Text Statistics CLI Tool.

Turns (label, Stats) pairs plus an optional total into either a
human-readable table string or a JSON string. No file I/O, no argv, no
exit codes — data in, string out. See docs/decisions.md D5 (JSON schema)
and D6 (human table format).
"""

from __future__ import annotations

import json
from typing import Any

from textstats.counter import Stats

FileResult = tuple[str, Stats]  # (file_label, stats)


def format_human(results: list[FileResult], total: Stats | None) -> str:
    """Render a human-readable table.

    One row per file (in the order given), plus a 'total' row when `total`
    is not None. Columns are always ordered Lines, Words, Chars, matching
    FR1's stated order.
    """
    header = ("File", "Lines", "Words", "Chars")
    rows: list[tuple[str, str, str, str]] = [header]
    for label, stats in results:
        rows.append((label, str(stats.lines), str(stats.words), str(stats.chars)))
    if total is not None:
        rows.append(("total", str(total.lines), str(total.words), str(total.chars)))

    col_widths = [
        max(len(row[col]) for row in rows) for col in range(len(header))
    ]

    lines = []
    for row in rows:
        first = row[0].ljust(col_widths[0])
        rest = "  ".join(
            value.rjust(col_widths[i]) for i, value in enumerate(row) if i > 0
        )
        lines.append(f"{first}  {rest}")
    return "\n".join(lines)


def format_json(results: list[FileResult], total: Stats | None) -> str:
    """Render the same numbers as a single JSON document.

    Schema (docs/decisions.md D5):
        {
          "files": [{"file": <label>, "lines": .., "words": .., "chars": ..}, ...],
          "total": {"lines": .., "words": .., "chars": ..}   # only if total is not None
        }
    """
    payload: dict[str, Any] = {
        "files": [
            {
                "file": label,
                "lines": stats.lines,
                "words": stats.words,
                "chars": stats.chars,
            }
            for label, stats in results
        ]
    }
    if total is not None:
        payload["total"] = {
            "lines": total.lines,
            "words": total.words,
            "chars": total.chars,
        }
    return json.dumps(payload)
