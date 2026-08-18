"""Enables `python -m csv2json ...` as the CLI entry point."""

import sys

from csv2json.cli import main

if __name__ == "__main__":
    sys.exit(main())
