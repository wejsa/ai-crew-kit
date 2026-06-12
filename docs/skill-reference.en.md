# Skill Reference

> [← Back to README](../README.md) · 한국어판: [skill-reference.md](./skill-reference.md)

## Which skill, when?

Start from your situation — the chain handles the rest:

| Your situation | Start here |
|---|---|
| "I want to build something new" | `/aick-feature "..."` → approve the spec → plan → impl → review → merge chain runs with approval gates |
| "Just give me the next task" | `/aick-plan` (picks the highest-priority unblocked task) |
| "Continue what I was doing" | `/aick-status` to orient, then `/aick-impl --next` — or just say "continue" |
| "Review / merge this PR" | `/aick-review-pr N` · `/aick-merge-pr N` |
| "Production is broken" | `/aick-hotfix "..."` (emergency fix from main) · `/aick-rollback vX.Y.Z` (audited release rollback) |
| "Is everything healthy?" | `/aick-status --health` (~5 s) → `/aick-health-check` (deep scan, ~30 s) |
| "How are we doing / what did we learn?" | `/aick-report` (metrics) · `/aick-retro` (lessons, fed back into planning) |
| "Set up or maintain the kit" | `/aick-init` (new) · `/aick-onboard` (existing code) · `/aick-upgrade` (then `/aick-validate` runs automatically) |

## Frequently used commands

| Command | What it does | Natural-language trigger (any language works) |
|---------|--------------|--------------------------------|
| `/aick-status` | project status, backlog summary, lock state | "what's the status?" |
| `/aick-feature` | plan a new feature → spec + backlog task | "plan a new feature" |
| `/aick-plan` | design analysis + step breakdown (approval gate) | "give me the next task" |
| `/aick-impl` | implement step by step + open PRs | "start implementing" |
| `/aick-review-pr` | multi-perspective PR review | "review PR 123" |
| `/aick-merge-pr` | squash merge + state update | "merge PR 123" |
| `/aick-retro` | retrospective on completed tasks | "run a retro" |
| `/aick-hotfix` | emergency fix on main | "hotfix this" |
| `/aick-rollback` | release/PR rollback | "roll back v1.2.3" |
| `/aick-report` | project metrics report | "generate a report" |
| `/aick-health-check` | codebase health scan (score + grade) | "health check" |

## Skill tiers (by usage frequency)

| Tier | Skills | Notes |
|------|--------|-------|
| 🔵 **Daily** | status, plan, impl, review-pr, merge-pr, hotfix | the core workflow loop |
| 🟢 **Weekly** | feature, backlog, report, health-check, retro | periodic management + analysis |
| ⚙️ **Setup** | init, onboard, upgrade, create, estimate, docs, validate | initial setup + extension |

> New here? Learn the **six Daily skills** first. Everything else is reference material for when you need it.

## Full command list

### Project management ⚙️

| Command | Description |
|---------|-------------|
| `/aick-init` | initialize a project (**v2.1+** requirements-first flow: free-form description → LLM stack recommendation → opt-in backlog auto-decomposition; auto-cleans kit residue when run inside an `ai-crew-kit` clone) |
| `/aick-init --quick` | zero-decision init (directory-name matching → file detection → empty backlog) |
| `/aick-init --reset` | reset existing config (auto-backup to `.claude/temp/reset-backup-{ts}-{pid}/` with a `MANIFEST.txt` checksum record) |
| `/aick-status` | current status |
| `/aick-status --health` | system health check |
| `/aick-status --health --fix` | health check + orphan auto-recovery |
| `/aick-health-check` | codebase health scan (score + grade) |
| `/aick-health-check --quick` | CRITICAL items only |
| `/aick-health-check --scope {category}` | scan one category |
| `/aick-health-check --fix` | scan with auto-fixes |
| `/aick-backlog` | view/manage the backlog |
| `/aick-onboard` | apply AI Crew Kit to an existing codebase (auto-cleans kit-clone residue) |
| `/aick-onboard --scan-only` | scan only, generate nothing |

### Development workflow 🔵

| Command | Description |
|---------|-------------|
| `/aick-feature` | plan a new feature |
| `/aick-plan` | design + step plan (also auto-unblocks tasks whose dependencies completed) |
| `/aick-impl` | implement (per step) |
| `/aick-impl --next` | next step |
| `/aick-review` | non-PR local code review (a given path — no merge-gate/state recording; for PRs use `/aick-review-pr`) |
| `/aick-review-pr {N}` | PR review (v2.3+: auto tier classification by PR shape + confidence scoring) |
| `/aick-review-pr {N} --auto-fix` | review + auto-fix loop for CRITICAL findings |
| `/aick-review-pr {N} --mode standard` | one-off standard mode (bypasses auto-tiering) |
| `/aick-review-pr config` | show review-mode configuration |
| `/aick-review-pr config --mode standard\|full` | change preset |
| `/aick-review-pr config --agents architecture,test` | custom agent combination |
| `/aick-review-pr config --reset` | remove the `review` section (re-enable auto-tiering) |
| `/aick-fix {N}` | fix CRITICAL findings |
| `/aick-merge-pr {N}` | merge the PR |

#### Auto tier classification (default when `review` is unset)

| Tier | Condition | sub-agents |
|------|-----------|-----------|
| **T1a** test-only | 100% test files · ≤200 lines · no security keywords | 1 (`pr-reviewer-test`) |
| **T1b** deps-only | 100% dependency manifests · no src/ changes · no security keywords | 1 (`pr-reviewer-security`) |
| **T0** trivial | ≤50 lines · no src/ changes · no security keywords | 0 (direct review) |
| **T3** full | >200 lines OR security keywords | 3 (architecture+security+test) |
| **T2** standard | everything else | 2 (architecture+security) |

Small everyday PRs (tests, deps bumps, docs) automatically skip the heavy path; security-relevant or large changes still get the full T3 review.

#### Confidence scoring + decision matrix

Each sub-agent finding gets a 0–100 confidence score; severity × confidence decides posting:

| Condition | Handling |
|-----------|----------|
| CRITICAL × conf ≥ critical threshold | posted + REQUEST_CHANGES |
| CRITICAL × conf < critical | **downgraded to MAJOR but still posted** (never dropped) + auto-chain blocked on your own PRs |
| MAJOR / MINOR below threshold | dropped |

Thresholds are customizable in `project.json` (`review.thresholds`, defaults 80/60/50, each key falls back independently; `critical ≥ 50` is enforced).

### Operations 🔵

| Command | Description |
|---------|-------------|
| `/aick-hotfix "{description}"` | emergency fix on main (security-reviewed; merge on the machine where the review ran — the verdict is recorded locally) |
| `/aick-rollback {tag\|PR}` | release/PR rollback |
| `/aick-release` | version release |

### Analysis / docs 🟢

| Command | Description |
|---------|-------------|
| `/aick-docs` | browse project reference material |
| `/aick-retro` · `/aick-retro {TASK-ID}` · `/aick-retro --summary` | retrospectives |
| `/aick-report` · `/aick-report --full` | metrics reports |
| `/aick-estimate` | task complexity estimation |

### Setup / extension ⚙️

| Command | Description |
|---------|-------------|
| `/aick-create` | scaffold a custom skill |
| `/aick-upgrade` · `/aick-upgrade --dry-run` | framework upgrade (preview with `--dry-run`) |
| `/aick-validate` | post-upgrade integrity verification (runs automatically after upgrade) |
| `/aick-validate --fix` | auto-fix safe items (missing `metadata.version`, malformed state timestamps) |

## Which verification tool, when?

| Situation | Command | Takes |
|-----------|---------|-------|
| Start of a daily session | `/aick-status --health` | ~5 s |
| "Something feels off" | `/aick-health-check --quick` | ~15 s |
| Pre-release full sweep | `/aick-health-check` | ~30 s |
| After a framework upgrade | `/aick-validate` (automatic) | ~10 s |
| Fixing problems | `/aick-health-check --fix` | ~30 s |
| Weekly team report | `/aick-report` | ~30 s |
