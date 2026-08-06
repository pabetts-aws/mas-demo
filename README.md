# mas-demo — the MAS showroom

This repo holds software **built by the MAS platform**
(https://github.com/pabetts-aws/mas) — a team of AI agents that plans,
writes, tests, and self-heals its way to working code. The platform lives
in the `mas` repo; the things it produces live here.

## How a project lands here (greenfield)

1. Open this repo in Kiro (or Claude Code) with the MAS MCP server
   registered — setup guide: `mas` repo README.
2. Ask your assistant to submit a task, e.g.:

   > "Using the MAS platform, submit a greenfield task: build a small CLI
   > tool that converts CSV files to JSON, with unit tests. Poll until it
   > finishes, then fetch the artifacts into `projects/<task_id>/`."

3. The platform builds and tests it in a sandbox (typically 5–10 minutes,
   $1.30–$3.50). Your assistant pulls the finished files into
   `projects/<task_id>/` and you commit them.
4. Watch it happen live (and suspend/cancel if you want) in the MAS
   console — URL and login are in the `mas` repo README.

Note: MAS itself never pushes to git (by design). Your IDE assistant is
the courier — that IS the intended workflow.

## Layout

```
mas-demo/
├── projects/            one folder per MAS-built project, named by task_id
│   └── <task_id>/       the code + tests + the run's workspace manifest
└── brownfield/          imported public code used to demo bugfix tasks
```

Each project folder should keep its `workspace-manifest.json` — it carries
the sha256 fingerprints proving the files match what MAS built, and the
task_id links back to the full decision audit trail in the platform.

## Brownfield demos

Two ways to show MAS working on EXISTING code:

- **Public repo, directly**: the platform's brownfield class clones a
  public repo inside its sandbox, fixes a stated defect, and proves it
  against the repo's own test suite (the benchmark instance is a pinned
  Flask bug). Nothing needs to live here for that.
- **This repo as the target**: vendor a small piece of public code into
  `brownfield/` (keep its license header), or — better — use a project MAS
  already built in `projects/`. Since this repo is public, MAS can clone
  it in the sandbox: file a bugfix task pointing at it, get the fix back,
  apply and commit. The showroom becomes its own brownfield corpus.

## Roadmap tie-in

The platform's next planned task class is **brownfield-feature** ("add
capability X to this repo, tests included, suite stays green"). When it
ships, projects in this repo graduate from one-shot builds to software
that MAS keeps evolving — submit, fetch, commit, repeat.
