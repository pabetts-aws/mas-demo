"""Entry point for `python -m textstats`."""

import sys

from textstats.cli import main

if __name__ == "__main__":
    sys.exit(main())
