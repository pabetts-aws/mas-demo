# Personas for CSV to JSON CLI Tool

## Persona 1: Dana the Data Engineer
- **Role**: Builds and maintains data pipelines that ingest data from various sources.
- **Goals**: Quickly convert ad-hoc CSV exports (from spreadsheets, databases, or third-party tools) into JSON so they can be fed into downstream JSON-based systems (APIs, NoSQL stores, log processors).
- **Technical comfort**: High. Comfortable with command-line tools, shell scripting, and automation pipelines.
- **Pain points**: CSV files often have quoted fields with embedded commas/newlines and empty values that break naive parsers. Needs a tool she can trust and drop into scripts without babysitting it.
- **Usage context**: Runs the tool many times a day, often piping output into other CLI tools or redirecting to files as part of larger shell scripts.

## Persona 2: Sam the Support/Ops Analyst
- **Role**: Handles support tickets and operational reports; regularly receives CSV exports from customers or internal systems.
- **Goals**: Convert a one-off CSV file into JSON to inspect it more easily, attach it to a bug report, or feed it into a JSON-aware internal tool.
- **Technical comfort**: Medium. Can run command-line tools with documented flags but does not want to write code or debug parser internals.
- **Pain points**: Needs a simple, predictable command with clear usage instructions; doesn't want to worry about how quoting or empty fields are handled — just wants correct output every time.
- **Usage context**: Runs the tool occasionally, typically once per file, and expects either console output to eyeball or a JSON file to attach elsewhere.

## Persona 3: Priya the Platform/Automation Engineer
- **Role**: Wires small utilities into CI/CD pipelines and automation jobs.
- **Goals**: Use the CLI as a reliable, scriptable step in a larger automated workflow (e.g., convert a nightly CSV export to JSON before uploading to an API).
- **Technical comfort**: High. Cares about exit codes, error handling, and performance under load (larger files).
- **Pain points**: Needs the tool to behave predictably at scale (thousands of rows) and to fail loudly (non-zero exit code, clear error message) rather than silently producing bad output.
- **Usage context**: Invokes the tool non-interactively from scripts/pipelines; needs deterministic behavior and reasonable performance guarantees.
