# mas-demo — the MAS showroom

This repo holds software **built by the MAS platform**
(https://github.com/pabetts-aws/mas) — a team of AI agents that plans,
writes, tests, and self-heals its way to working code. The platform lives
in the `mas` repo (private); the things it produces live here, in public.

## How this repo is written to (read this first)

This repo is public, and org policy blocks its maintainers from pushing
to public repos from their workstations. That is not an accident — it is
the design:

- **Reads are anonymous.** The MAS sandbox clones this repo by public
  tarball at a pinned commit, with zero credentials. No credential ever
  enters a sandbox that executes generated code.
- **Writes belong to the platform.** New projects land here when MAS
  itself pushes them from AWS (git integration, spec S10 — in progress).
  Until S10 ships, the content below is frozen exactly as seeded, with
  full provenance.
- The projects currently here were seeded by the original courier
  workflow (IDE assistant fetched the build artifacts from the platform's
  artifact store and committed them) before the repo went public; their
  `workspace-manifest.json` sha256 fingerprints prove the files are
  byte-identical to what MAS built.

## How a project lands here (greenfield, once S10 ships)

1. Open your IDE with the MAS MCP server registered — setup guide:
   `mas` repo README.
2. Ask your assistant to submit a greenfield task, e.g.:

   > "Using the MAS platform, submit a greenfield task: build a small CLI
   > tool that converts CSV files to JSON, with unit tests."

3. The platform builds and tests it in a sandbox (typically 5–10 minutes,
   $1.30–$3.50), then pushes the finished project to
   `projects/<task_id>/` here — commit provenance links back to the run.
4. Watch it happen live (and suspend/cancel if you want) in the MAS
   console — URL and login are in the `mas` repo README.

## Layout

```
mas-demo/
├── projects/            one folder per MAS-built project, named by task_id
│   └── <task_id>/       the code + tests + the run's workspace manifest
└── brownfield/          imported public code used to demo bugfix tasks
```

Each project folder keeps its `workspace-manifest.json` — it carries
the sha256 fingerprints proving the files match what MAS built, and the
task_id links back to the full decision audit trail in the platform.

## Brownfield demos

Two ways to show MAS working on EXISTING code:

- **Public repo, directly**: the platform's brownfield classes clone a
  public repo inside the sandbox at a pinned ref, make the stated change,
  and prove it against the repo's own test suite (the bugfix benchmark is
  a pinned Flask defect; the first feature-class run added
  `flask routes --json` at the same ref).
- **This repo as the target**: now that it is public, the sandbox can
  clone it anonymously — brownfield tasks can point at the MAS-built
  projects in `projects/` and evolve them. The showroom becomes its own
  brownfield corpus: software MAS built, extended by MAS, with the whole
  decision trail on record.

## Roadmap tie-in

The platform's third task class, **brownfield-feature** ("add capability
X to an existing repo, tests included, suite stays green"), shipped
2026-08-18 as pure knowledge-pack data (the C1d plasticity claim,
exercised for real) and passed its live eval the next day. With this repo
public it becomes the natural feature-class target; once S10 (platform
git integration) ships, projects here graduate from one-shot builds to
software MAS keeps evolving — submit, build, push, repeat.
