"""CLI orchestrator for the Text Statistics CLI Tool.

The only component that touches argv, the filesystem, stdout/stderr, and
process exit codes. See docs/components.md Component 3 and
docs/decisions.md D7 for the full behavior contract.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from textstats.counter import Stats, count_stats, total_stats
from textstats.formatting import FileResult, format_human, format_json

PROG_NAME = "textstats"


def read_file_text(path: str) -> str:
    """Read a file as UTF-8 text.

    Raises FileNotFoundError (propagated, not swallowed) if the path does
    not exist. Other I/O errors (e.g. permission errors, decode errors)
    are also propagated, not swallowed (docs/decisions.md D9).
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG_NAME,
        description=(
            "Report line, word, and character counts for one or more "
            "input text files."
        ),
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="One or more paths to input text files.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the counts as a JSON object on stdout instead of a table.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse argv, run the tool, print to stdout/stderr, and return the
    process exit code.

    Does not call sys.exit itself; see textstats/__main__.py for the bridge
    to an actual OS exit code (docs/decisions.md D7).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)
    # argparse itself handles zero-file-arguments (nargs='+') by printing a
    # usage message to stderr and calling sys.exit(2) -- Story 5 is
    # satisfied natively, no custom code needed here.

    file_paths: list[str] = args.files

    contents: list[str] = []
    missing_paths: list[str] = []
    for path in file_paths:
        try:
            contents.append(read_file_text(path))
        except FileNotFoundError:
            missing_paths.append(path)

    if missing_paths:
        for path in missing_paths:
            print(
                f"{PROG_NAME}: error: file not found: {path}",
                file=sys.stderr,
            )
        return 1

    results: list[FileResult] = [
        (path, count_stats(text)) for path, text in zip(file_paths, contents)
    ]
    all_stats: list[Stats] = [stats for _, stats in results]
    total: Stats | None = total_stats(all_stats) if len(results) > 1 else None

    if args.json:
        output = format_json(results, total)
    else:
        output = format_human(results, total)

    print(output)
    return 0
