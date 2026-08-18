# csv2json

A small CLI tool that converts a CSV file with a header row into a JSON
array of row objects.

See [`docs/usage.md`](docs/usage.md) for how to run the tool and its
test suite, the exit-code contract, and the documented behavior for
quoted fields, empty values, and edge cases.

Quick start:

```
python run.py sample.csv
python run.py sample.csv -o output.json
pytest
```
