# Core Concepts

> [← Back to README](../README.md) · 한국어 원문 (상세판): [concepts.md](./concepts.md)

## What this is

AI Crew Kit is a **general-purpose process-management framework** for AI-agent-team development, native to Claude Code. It is domain-neutral: common conventions, review checklists, and health checks (`.claude/domains/_base/`) apply to every project, and per-project customization lives in `project.json` and the `CUSTOM_SECTION` of your `CLAUDE.md`.

The role split is strict:

| Area | Framework owns | Claude owns |
|------|----------------|-------------|
| Workflow | feature → plan → impl → review → merge chaining | — |
| Quality gates | build/test/review enforcement, deterministic merge blocking | — |
| Team conventions | coding style, security rules, architecture principles (SSOT) | — |
| Writing code | — | every language, protocol, library |
| Technical judgment | — | architecture patterns, library choices, optimization |

Why: Claude already knows WebSocket, GraphQL, gRPC, CQRS — re-teaching them in a framework only creates maintenance cost and conflicts with the model's newer knowledge. Processes don't age the way technology conventions do. The kit deliberately does **not**: teach protocol-specific code (WebSocket, gRPC, …), define library usage (socket.io, Apollo, …), or mandate architecture patterns (event sourcing, CQRS, …) — those belong to Claude's knowledge and your project's requirements.

## Supported stacks

| Backend | Build | Test |
|---------|-------|------|
| Spring Boot (Kotlin / Java) | `./gradlew build` | `./gradlew test` |
| Node.js (TypeScript) | `npm run build` | `npm test` |
| Python (FastAPI / Django) | `pip install -e '.[dev]'` | `pytest --cov` |
| Go | `go build ./...` | `go test ./...` |

Frontend: Next.js · React + Vite · Vue / Nuxt · Astro (all `npm run build`). These get automatic build/test gate detection and conventions; anything else works too — Claude implements it, and the process around it stays identical.

## The agent team

### Structure — the main session orchestrates; agents do quality analysis

Implementation, planning, and documentation belong to the **main session** (skill chaining).
Agents are **quality-analysis specialists** that skills invoke at the right moment
(v4.8.0: the unwired agents pm·planner·backend·frontend·docs were removed — 12 → 7 that
actually run; see [docs/archive/agents/](./archive/agents/)).

```
        main session (skill chaining orchestrates)
  feature → plan → impl → review-pr → merge-pr
              │       │        │
              ▼       ▼        ▼
        ┌──────────┐ ┌──────────────────┐ ┌──────────────────────┐
        │ design    │ │ in-flight        │ │ PR review (multi-     │
        │ analysis  │ │ analysis         │ │ perspective)          │
        ├──────────┤ ├──────────────────┤ ├──────────────────────┤
        │db-designer│ │qa                │ │pr-reviewer-architecture│
        │          │ │docs-impact-      │ │pr-reviewer-security   │
        │          │ │analyzer          │ │pr-reviewer-test       │
        └──────────┘ └──────────────────┘ └──────────────────────┘
                          + agent-code-reviewer (review guide document)
```

### The 7 agents (6 spawned + 1 review guide)

| Agent | Invoked by | Role | Activation |
|-------|------------|------|------------|
| **pr-reviewer-architecture** | `aick-review-pr` | architecture + business-logic consistency | auto (per tier/mode) |
| **pr-reviewer-security** | `aick-review-pr` | security review | auto (per tier/mode) |
| **pr-reviewer-test** | `aick-review-pr` | test quality review | auto (per tier/mode) |
| **docs-impact-analyzer** | `aick-impl` | docs impact analysis + draft suggestions | always |
| **agent-qa** | `aick-impl` | test quality analysis (background) | `qa` in `agents.enabled` (default ON) |
| **agent-db-designer** | `aick-plan` | DB design analysis (parallel) | `db-designer` in `agents.enabled` (default OFF) |
| **agent-code-reviewer** | `aick-review-pr` | 4-perspective review guide (reference doc — never spawned) | default |

All analysis agents are read-only (Read/Glob/Grep), and are invoked only through skills.
`agent-db-designer` and `agent-qa` run only when listed in `project.json` → `agents.enabled`.

## Directory layout

```
.claude/
├── agents/           # agent definitions
├── skills/           # the 22 skills (SKILL.md each)
├── domains/_base/    # shared conventions + review checklists
├── templates/        # CLAUDE.md / README.md generation templates
├── workflows/        # workflow definitions (YAML)
├── schemas/          # JSON Schemas (backlog, project, …) — CI-validated
├── hooks/            # the deterministic layer (4 bash hooks)
├── state/            # persistent state, git-tracked
│   ├── project.json  #   project configuration
│   ├── backlog.json  #   tasks, steps, locks, workflow state
│   └── completed.json#   history
└── temp/             # scratch artifacts (.gitignored)

CLAUDE.md · README.md · VERSION   # generated per user project by /aick-init
```

## Execution model

**There is no runtime.** Claude Code reads `SKILL.md` prose, workflow YAML, and JSON state, and acts on them. Around that probabilistic core sits a small **deterministic layer**:

| Hook | Event | Job |
|------|-------|-----|
| session-start | session begins | git sync, replay continuation plan, list in-progress tasks |
| pre-tool-use | before any Bash call | **merge quality gate** — denies `gh pr merge` for PRs with unresolved CRITICAL reviews (`exit 2`) |
| post-tool-use | after Edit/Write | lock heartbeat (file-membership), loop protection |
| stop | each response ends | lock-TTL expiry cleanup, continuation-plan write |

Bookkeeping hooks never block (`exit 0` always); the gate hook blocks by design but **fails open** on infrastructure errors — and provides an explicit, audited, human-only bypass. Details: [merge-gate-explained.md](./merge-gate-explained.md).

State files under `.claude/state/` are git-tracked and schema-validated (`additionalProperties: false`, enums, ranges) in CI.

## Sessions and parallel work

**Resume**: when a session dies, restart `claude` — the Stop hook has been writing a continuation plan every turn, and SessionStart replays it. `/aick-status` shows where you are; "continue the task" picks it back up.

**Parallel sessions** are allowed for tasks with no shared `dependencies` and no overlapping `lockedFiles`:

- Claiming a task locks it (`lockedBy`, `lockTTL` 1–4 h scaled by file count)
- Edits inside `lockedFiles` refresh the heartbeat automatically (PostToolUse)
- Expired locks are released non-destructively; `/aick-status --locks` to inspect, `/aick-backlog unlock {taskId} --force` for emergencies
- `claude --worktree <name>` (Claude Code 2.1.49+) is auto-detected by all skills

## Core principles

| Principle | Meaning |
|-----------|---------|
| **Stack-aware** | the detected stack tunes builds, reviews, and recommendations |
| **Layered override** | `domains/_base/` → `project.json` → `CLAUDE.md` `CUSTOM_SECTION` |
| **Agent orchestration** | the PM distributes agents according to the workflow |
| **Zero-config start** | one `/aick-init` and you're running |

## Layered override

```
1. CLAUDE.md CUSTOM_SECTION   ← project custom (highest priority)
2. project.json               ← project configuration
3. domains/_base/             ← shared defaults
```

Add your own conventions, checklists, or skills without forking the kit — see [customization (Korean)](./customization.md).

→ Next: [Getting started](./getting-started.en.md) · [Merge gate explained](./merge-gate-explained.md) · full Korean docs: [concepts.md](./concepts.md)
