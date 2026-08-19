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
- **This repo as the target (future)**: this repo is PRIVATE (AWS org
  policy) and the platform's sandbox clones anonymously — deliberately,
  since no credential should ever enter a sandbox that executes generated
  code. Until the platform grows authenticated fetch (backlog:
  harness-side tarball staging with the token kept outside the sandbox),
  live brownfield tasks target public repos; this repo stays the
  provenance showroom.

## Roadmap tie-in

The platform's third task class, **brownfield-feature** ("add capability
X to an existing repo, tests included, suite stays green"), shipped
2026-08-18 as pure knowledge-pack data (the C1d plasticity claim,
exercised for real). Its live eval targets the public pinned Flask
benchmark because this repo must stay private; once authenticated fetch
lands, projects here graduate from one-shot builds to software MAS keeps
evolving — submit, fetch, commit, repeat.
