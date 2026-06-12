# Getting Started

> [← Back to README](../README.md) · 한국어 원문 (상세판): [getting-started.md](./getting-started.md)

## Requirements

| | |
|---|---|
| **Required** | [Claude Code](https://claude.ai/download) CLI |
| **Recommended** | Git 2.30+ · `jq` (the merge gate needs it; without it the gate fails open) |

> No external runtime needed — Claude Code reads the framework's files and executes them directly. Node.js, Python, etc. are only needed for *your project's* stack.

## Install

**Step 1 — install the plugin** (inside any Claude Code session):

```bash
/plugin marketplace add wejsa/ai-crew-kit
/plugin install ai-crew-kit@ai-crew-kit
```

This registers 22 skills + 7 agents + the quality-gate hooks in one step, available in any project. (Cloning the repo directly also works — see "Onboarding, scenario B" below — but the plugin is the recommended path.)

> The CLI command installs **user-wide**. If you install through the `/plugin` UI and pick *project* scope, the plugin stays in that one project.

**Step 2 — start Claude Code in your project directory:**

```bash
cd my-project   # a new directory, or an existing codebase
claude
```

**Step 3 — initialize:**

```bash
/aick-init            # interactive — choose everything yourself
/aick-init --quick    # zero-decision — auto-detection + defaults, running in ~5 minutes
```

## What `/aick-init` does

```
/aick-init
    │
    ├── 1. Environment checks (+ automatic kit-clone cleanup, when applicable)
    ├── 2. Free-form requirements input ★ — one line or several paragraphs
    │       e.g. "B2B SaaS kanban board for teams. Multi-tenancy required,
    │             50 companies / 100 users each, GDPR."
    ├── 3. Up to 3 follow-up questions (only if the input was lean)
    ├── 4. Project metadata auto-derived (name / task prefix / description)
    ├── 5. Domain + stack recommendation ★ — accept / adjust / pick manually
    ├── 6. Agent team composition (stack-based defaults + your choice)
    ├── 7. Workflow profile (standard / fast)
    ├── 8. Skill profile (full / developer / docs-only / custom)
    ├── 9. Backlog auto-decomposition (opt-in) ★ — 10–25 tasks across
    │       4 fixed phases: foundation → core domain → extras → ops/quality
    ├── 10. File generation — .claude/state/project.json, backlog.json,
    │        CLAUDE.md, README.md, VERSION (0.1.0)
    └── 11. Done — next-step guidance
```

- `--quick` skips steps 2–9 with auto-detection and defaults; re-configure later with `/aick-init --reset`.
- **Reproducibility**: the same requirements produce the same domain/backend/database/phase structure deterministically; task count (±2) and wording vary with LLM sampling.
- **Trust boundary**: requirements input gets prompt-injection defenses, shell/path-traversal sanitization, and hard limits (≤10 tasks per phase, ≤30 total).
- **Kit-clone cleanup**: if you started from a clone of `ai-crew-kit` itself, init detects it (origin URL + commit fingerprint, with dirty/unpushed/non-main guards) and removes kit-dev residue (CHANGELOG, docs/, examples/, tests/, scripts/, .github/, memory/, LICENSE, README.md, README.ko.md, CLAUDE.md, VERSION, .claude/temp/, .claude/hooks/tests/, .claude/state/, .claude/settings.local.json) so you start with a clean user project.

### Starting a Python project

```bash
/aick-init   # → backend: python-fastapi → generates pyproject.toml, app/, tests/conftest.py, alembic/
/aick-init   # → backend: python-django  → generates pyproject.toml, manage.py, config/, apps/
```

Four Python conventions apply automatically: `python-project-structure`, `python-testing`, `python-dependency`, `python-patterns`.

## Onboarding an existing codebase

Use `/aick-onboard` to apply AI Crew Kit to a project that already has code.

**Scenario A (recommended — plugin install):** just install the plugin, `cd` into your project, run `/aick-onboard`.

**Scenario B (clone-based):** clone the kit as your project root, copy your code into non-conflicting paths (`src/`, `app/`, `lib/`), then run `/aick-onboard` — it auto-detects the kit clone and performs the cleanup above first. If your own `docs/`/`tests/`/`scripts/` would collide, back them up first:
`tar czf .pre-onboard-backup-$(date +%s).tar.gz docs tests scripts .github`

What onboarding does:

```
/aick-onboard
    ├── 1. Codebase auto-scan — package manager, frontend framework, database,
    │       cache/queue, build·test·lint commands, domain suggestion
    ├── 2. You review/correct the scan results
    ├── 3. Extra info — project description, agent selection
    ├── 4. Backs up existing files (README.md → README.md.bak)
    ├── 5. Generates .claude/state/project.json, backlog.json, CLAUDE.md,
    │       README.md (project-specific), VERSION (0.1.0)
    └── 6. Done — next steps
```

Options: `/aick-onboard --scan-only` runs the scan without generating anything — useful to preview detection before committing.

**After onboarding:**

```bash
/aick-feature "existing feature name"   # register existing features as backlog tasks
/aick-backlog                           # review the backlog
/aick-plan                              # start working
```

| | `/aick-init` | `/aick-onboard` |
|---|---|---|
| Target | new project | existing codebase |
| Input | interactive Q&A | automatic scan |
| Existing files | none | backed up, then generated |

## Your first feature — the 5-step loop

```bash
/aick-feature "user authentication"
```
Creates a requirements doc (`docs/requirements/{TASK-ID}-spec.md`) and a backlog task. Approve it, and the chain continues:

```bash
/aick-plan          # design + step breakdown → .claude/temp/{TASK-ID}-plan.md
                    # review the steps (files, estimated lines, dependencies),
                    # approve → implementation starts automatically
/aick-impl          # (auto-invoked) feature branch + code + PR
/aick-review-pr N   # (auto-invoked) multi-perspective review;
                    # CRITICAL findings → auto-fix loop (aick-fix)
/aick-merge-pr N    # (auto-invoked) squash merge + state update
                    # more steps remaining? loops back to impl
```

Each phase has a user-approval gate, and `gh pr merge` is additionally guarded by the [deterministic merge gate](./merge-gate-explained.md) — a PR whose review posted an unresolved CRITICAL cannot be merged, no matter what the model decides.

## When you get stuck

| Situation | Do this |
|---|---|
| Build failure | check the error log, fix, then "continue" or `/aick-impl --retry` |
| Skip a step (build failures only) | `/aick-impl --skip` |
| Where am I? | `/aick-status` |
| Backlog overview | `/aick-backlog dashboard` |
| Session died mid-task | restart `claude` — the continuation plan replays; say "이어서 진행해줘" / "continue the task" |
| Other errors | `CLAUDE.md` ships an error-recovery protocol covering 10 error classes |

→ Next: [Core concepts](./concepts.en.md) · [Merge gate explained](./merge-gate-explained.md) · full Korean docs: [getting-started.md](./getting-started.md)
