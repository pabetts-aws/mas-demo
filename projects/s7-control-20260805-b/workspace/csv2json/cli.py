"""Component C: argument parsing and orchestration.

This is the only component allowed to decide process exit codes. It
calls Component B (io_handler) to open the input and write the output,
and Component A (converter) to do the actual CSV -> records conversion.
No CSV/JSON business rules live here -- if a developer finds themselves
writing a parsing or formatting rule in this file, it belongs in
converter.py or io_handler.py instead.
"""

from __future__ import annotations

import argparse
import csv
import sys

from csv2json.converter import csv_rows_to_records
from csv2json.io_handler import InputError, OutputError, open_input, write_output

EXIT_SUCCESS = 0
EXIT_INPUT_ERROR = 1
EXIT_OUTPUT_ERROR = 2


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the csv2json CLI."""
    parser = argparse.ArgumentParser(
        prog="csv2json",
        description=(
            "Convert a CSV file with a header row into a JSON array of "
            "row objects."
        ),
    )
    parser.add_argument(
        "input_csv",
        metavar="INPUT_CSV",
        help="path to the input CSV file (must have a header row)",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        metavar="OUTPUT_JSON",
        default=None,
        help=(
            "path to write JSON output; if omitted, JSON is written to "
            "stdout"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse argv, run the input->convert->output pipeline, return an exit code.

    Does not call sys.exit directly, so it stays testable by asserting on
    the return value; run.py is the only place that calls
    sys.exit(main(sys.argv[1:])).

    Exit code contract:
        0 -- success, full JSON array produced.
        1 -- input error (missing file, unreadable, not valid CSV
             structure/no header row).
        2 -- output error (bad output path/permissions).

    All non-zero exits print a one-line, human-readable error to stderr
    and print nothing to stdout (Story 1 AC4, Story 4 AC3).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        input_file = open_input(args.input_csv)
    except InputError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_INPUT_ERROR

    try:
        with input_file:
            try:
                records = csv_rows_to_records(input_file)
            except (csv.Error, ValueError) as exc:
                print(f"Invalid CSV input '{args.input_csv}': {exc}", file=sys.stderr)
                return EXIT_INPUT_ERROR

        write_output(records, args.output)
    except OutputError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_OUTPUT_ERROR

    return EXIT_SUCCESS
