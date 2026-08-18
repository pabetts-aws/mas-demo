#!/usr/bin/env python3
"""Component D: thin executable entry point.

The only file that touches sys.exit/sys.argv directly at import/run
time. All actual logic lives in the csv2json package.

Usage:
    python run.py sample.csv
    python run.py sample.csv -o out.json
"""

import sys

from csv2json.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
