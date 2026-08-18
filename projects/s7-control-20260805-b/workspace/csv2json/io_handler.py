"""Component B: the I/O boundary.

Owns every point of contact with the filesystem and stdio: opening the
input file, choosing between stdout and an output file for the JSON
result, and translating OS-level failures into two narrow exception
types that Component C (cli.py) turns into exit codes and stderr
messages. Nothing here parses CSV or builds JSON structure beyond final
serialization.
"""

from __future__ import annotations

import json
import sys
from typing import TextIO


class InputError(Exception):
    """Input file missing, unreadable, or not decodable as text."""


class OutputError(Exception):
    """Output path's directory missing/not writable, or write failed."""


def open_input(path: str) -> TextIO:
    """Open `path` for reading in text mode.

    Uses newline='' so the csv module (not the platform's universal
    newline translation) controls newline interpretation inside quoted
    fields -- required for correct handling of embedded newlines in
    quoted fields (Story 2 AC2).

    Raises:
        InputError: if the file does not exist, is a directory, or
            cannot be opened/decoded for any other OS-level reason.
    """
    try:
        return open(path, "r", newline="", encoding="utf-8")
    except OSError as exc:
        raise InputError(f"Could not read input file '{path}': {exc}") from exc


def write_output(records: list[dict[str, str]], output_path: str | None) -> None:
    """Serialize `records` to a JSON array and write it to the destination.

    - If output_path is None: write to stdout. stdout carries ONLY the
      JSON output (Story 4 AC1) -- no logging or diagnostic text is ever
      mixed into stdout by this function or its callers.
    - Otherwise: write to the file at output_path, creating it if it does
      not exist or truncating it if it does.

    Raises:
        OutputError: if output_path's parent directory does not exist,
            is not writable, or the write otherwise fails at the OS
            level. The underlying OSError's message is included.
    """
    payload = json.dumps(records, indent=2)

    if output_path is None:
        sys.stdout.write(payload)
        sys.stdout.write("\n")
        return

    try:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(payload)
            fh.write("\n")
    except OSError as exc:
        raise OutputError(
            f"Could not write output file '{output_path}': {exc}"
        ) from exc
