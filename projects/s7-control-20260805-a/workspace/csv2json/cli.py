"""Argument parsing and process I/O wiring (Component: CLI).

Contains no CSV/JSON transformation logic itself (see docs/decisions.md D1) —
it opens files, calls into csv2json.converter, and writes stdout/a file,
mapping exceptions to exit codes (see docs/decisions.md D5/D6). ``main()``
never calls ``sys.exit()`` itself, so it stays testable in-process: tests
call ``main([...])`` and assert on the returned exit code plus captured
stdout/stderr/file contents.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from csv2json.converter import CsvConversionError, convert_csv_text_to_json_string

EXIT_OK = 0
EXIT_INPUT_ERROR = 1
EXIT_CONVERSION_ERROR = 2


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the argparse parser implementing the CLI contract (FR1, FR5)."""
    parser = argparse.ArgumentParser(
        prog="csv2json",
        description=(
            "Convert a CSV file with a header row into a JSON array of "
            "row objects, printed to stdout or written to an output file."
        ),
    )
    parser.add_argument(
        "input_path",
        help="Path to the input CSV file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        default=None,
        help="Output file path. If omitted, JSON is written to stdout.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help=(
            "JSON pretty-print indent width. Use --indent 0 to disable "
            "indentation (compact single-line JSON). Default: 2."
        ),
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Entry point. Returns a process exit code; does not call sys.exit().

    Args:
        argv: Command-line arguments (excluding the program name). Defaults
            to ``sys.argv[1:]`` when ``None``.
        stdout: Stream to write successful JSON output to. Defaults to the
            *current* ``sys.stdout`` at call time (resolved lazily so that
            tests using ``capsys``/monkeypatched streams still work).
        stderr: Stream to write error messages to. Defaults to the current
            ``sys.stderr`` at call time, for the same reason.

    Returns:
        0 on success, 1 if the input file cannot be found/read, 2 if the
        CSV content could not be converted (per docs/decisions.md D6).
    """
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr

    parser = build_arg_parser()
    args = parser.parse_args(argv)

    indent: int | None = args.indent if args.indent and args.indent > 0 else None

    input_path = Path(args.input_path)
    try:
        csv_text = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: could not read input file '{args.input_path}': {exc}", file=err)
        return EXIT_INPUT_ERROR

    try:
        json_text = convert_csv_text_to_json_string(csv_text, indent=indent)
    except CsvConversionError as exc:
        print(f"error: {exc}", file=err)
        return EXIT_CONVERSION_ERROR

    if args.output:
        output_path = Path(args.output)
        try:
            output_path.write_text(json_text + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"error: could not write output file '{args.output}': {exc}", file=err)
            return EXIT_INPUT_ERROR
    else:
        print(json_text, file=out)

    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
