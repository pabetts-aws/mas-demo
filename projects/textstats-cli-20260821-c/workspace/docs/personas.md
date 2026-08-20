# Personas

## Persona 1: Dana the DevOps Engineer
- **Role:** Writes shell scripts and CI pipelines that need quick text metrics.
- **Goals:** Get line/word/char counts for one or more files fast, from the command line, without writing custom parsing code.
- **Pain points:** Existing tools like `wc` don't provide a totals row across files in a single clean summary, and don't offer machine-readable output for downstream tooling.
- **Technical proficiency:** High — comfortable with CLI flags, exit codes, and piping output into other tools.

## Persona 2: Priya the Automation/Build Engineer
- **Role:** Integrates tooling into automated build and CI/CD pipelines.
- **Goals:** Needs deterministic, machine-parseable output (JSON) to feed into scripts and dashboards, and needs the tool to fail loudly (non-zero exit code) when input files are missing so pipelines halt correctly.
- **Pain points:** Tools that silently succeed on bad input or emit inconsistent human-readable formats break automated pipelines.
- **Technical proficiency:** High — writes automation scripts that consume JSON and check exit codes.

## Persona 3: Sam the Support/Docs Analyst
- **Role:** Occasionally inspects text/log/documentation files to gauge size and content volume.
- **Goals:** Wants a simple, readable summary of file statistics without needing to remember complex flags.
- **Pain points:** Needs clear, human-readable error messages when a file path is mistyped or missing.
- **Technical proficiency:** Moderate — comfortable running CLI commands with documented flags but relies on clear help text and error messages.