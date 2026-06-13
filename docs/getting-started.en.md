# Getting Started

> [← Back to README](../README.md) · 한국어 원문 (상세판): [getting-started.md](./getting-started.md)

## Requirements

| | |
|---|---|
| **Required** | [Claude Code](https://claude.ai/download) CLI |
| **Recommended** | Git 2.30+ · `jq` + `timeout` (the merge gate needs both; without them it fails open — macOS: `brew install coreutils` installs it as `gtimeout` — add gnubin to `PATH`) |

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

## Team adoption

The kit's state lives in git (`.claude/state/project.json`, `backlog.json`, `CLAUDE.md`), so a team shares it like any other code:

1. **One person initializes.** Run `/aick-init` (or `/aick-onboard`) in the project, review the generated files, commit and push them.
2. **Everyone else installs the plugin** (user-wide, two commands), pulls the project, and runs `/aick-status` — no further setup. Same plugin version across the team is recommended (`/plugin update`). After a plugin update, run `/aick-upgrade` once in the project — it applies project-local migrations (`.gitignore` entries, `kitVersion`, `CLAUDE.md` regeneration) that a plugin cache swap can't reach (v4.8.0+).
3. **Parallel work is lock-protected.** `/aick-plan` claims a task with a lock (TTL + activity heartbeat); two sessions cannot claim the same task, and expired locks self-release. On one machine, use `claude --worktree <name>` for parallel sessions.
4. **One rule for hotfix/ad-hoc PRs:** finish the merge on the machine where the review ran. Those verdicts are recorded locally only (gate signal A2, gitignored) — merging from another clone falls back to GitHub's review state alone. Workflow-chain PRs (plan→impl→review) are unaffected: their state travels through git. ([details](./merge-gate-explained.md#7-what-the-gate-does-not-do-honest-edition))

## FAQ

**Does it conflict with our existing CI/CD (GitHub Actions, GitLab CI, …)?**
No. The kit runs only inside Claude Code sessions on a developer's machine — your CI pipeline is untouched and keeps triggering on push/PR exactly as before. The merge gate guards Claude's own `gh pr merge` calls *in-session*; it is not a server-side rule. For team-wide hard enforcement, combine it with branch protection.

**A skill stopped mid-way (network error, closed laptop). Do I redo everything?**
No. Restart `claude` in the project and say "continue" — the continuation plan and the task lock pick up where you left off. If the *plan file* itself was lost (`.claude/temp/` is local-only, so machine moves or temp cleanup can drop it), run `/aick-plan {TASK-ID}`: it voids the stale approval and re-plans deterministically.

**What does it cost in tokens?**
Depends on project size and PR shape — there is no official benchmark, so treat any absolute number with suspicion. Structurally: the review step is the most expensive (2–3 sub-agents read the diff independently on T2/T3 PRs), implementation scales with step count, and everything else is light. Small PRs are automatically routed to cheap review tiers (T0/T1) — keeping PRs small is the single biggest cost lever. Measure with `/usage`; tuning levers (profiles, model routing, context size): [token optimization (Korean)](./token-optimization.md).

**Can I uninstall it later without losing my project?**
Yes — your code, git history, and generated docs are plain files. Removing the plugin removes the skills/hooks; the state files (`.claude/state/`) stay inert. Full removal checklist: [eject guide (Korean)](./eject-guide.md).

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
