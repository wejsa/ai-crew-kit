<div align="center">

# AI Crew Kit v4.8.0

**A general-purpose AI crew framework — orchestration · quality gates · stack awareness**

Process management for AI-agent-team software development, native to Claude Code

[![Version](https://img.shields.io/badge/version-v4.8.0-blue?style=flat-square)](./CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](./LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/wejsa/ai-crew-kit?style=flat-square)](https://github.com/wejsa/ai-crew-kit)
[![Built with Claude Code](https://img.shields.io/badge/built_with-Claude_Code-blueviolet?style=flat-square)](https://claude.ai/download)

[Try it](#-try-it-in-5-minutes) · [Quick start](#-quick-start) · [Merge gate](#-the-merge-quality-gate) · [Commands](#-commands) · [Docs](#-documentation)

English · [**한국어**](./README.ko.md)

</div>

![The merge gate in action — the block, the failed bypass, and the audited human override (captured from a real session)](./docs/assets/merge-gate-demo.svg)

<!-- PARITY: this Try-it section pairs with README.ko.md "5분 체험 (Try it)" — always update both together -->

## ⚡ Try it in 5 minutes

Watch the **deterministic merge gate** stop a bad merge — no real PR, no GitHub auth needed; the gate decision itself runs fully offline.

```bash
# 1. Install the plugin (inside any Claude Code session).
#    This CLI command installs USER-WIDE (works in any folder). If you instead used
#    the /plugin UI and picked "project" scope, the plugin does NOT follow you to
#    other folders — re-run these two commands inside the demo session at step 3.
/plugin marketplace add wejsa/ai-crew-kit
/plugin install ai-crew-kit@ai-crew-kit
```

```bash
# 2. In a regular terminal (not the Claude prompt), anywhere you like:
#    create a throwaway sandbox — unrelated to step 1's directory — and seed it
#    with the demo fixture (simulates PR #42 with an unresolved CRITICAL review).
mkdir gate-demo && cd gate-demo && git init -q && git commit --allow-empty -qm init
mkdir -p .claude/state
BASE=https://raw.githubusercontent.com/wejsa/ai-crew-kit/main/examples/merge-gate-demo
curl -fsSL "$BASE/.claude/state/backlog.json" -o .claude/state/backlog.json
curl -fsSL "$BASE/CLAUDE.md" -o CLAUDE.md   # tells the session to run commands literally
```

**3.** Start `claude` **in that directory** (the gate reads the session root's state; `jq` and `timeout` must be installed — without them the gate fails open. macOS: `brew install coreutils`, which installs it as `gtimeout` — add the gnubin dir to `PATH`) and paste:

> Do not use any skill. Run this exact bash command as-is: `gh pr merge 42 --squash`

**4.** The merge is stopped. `cat .claude/state/hook-errors.log` tells you **which layer** stopped it:

| You saw | Layer that fired | hook-errors.log |
|---------|------------------|-----------------|
| 🛑 `Merge blocked — PR #42` denial before execution | **deterministic hook** — the demo's point | `merge blocked` line present |
| Claude invoked a merge skill / declined on its own | prose layer — the hook never got the chance | empty or absent |

Either way the bad merge is stopped (defense in depth) — but **only the hook is guaranteed**. Live-model routing varies run to run, and that variance is exactly why the gate is a bash hook, not a prompt. To watch the hook fire **deterministically — same result for every user, every time** (run inside `gate-demo/`):

```bash
curl -fsSL https://raw.githubusercontent.com/wejsa/ai-crew-kit/main/.claude/hooks/pre-tool-use.sh -o /tmp/gate.sh
echo '{"tool_input":{"command":"gh pr merge 42 --squash"}}' \
  | CLAUDE_PROJECT_DIR="$PWD" bash /tmp/gate.sh; echo "exit=$?"   # → 🛑 + exit=2 (the gate decision makes zero network calls)
```

**No model in the decision loop** — the merge verdict is a bash hook reading recorded review state, not LLM prose: same state, same verdict, every time. ([What it does and doesn't guarantee](./docs/merge-gate-explained.md#7-what-the-gate-does-not-do-honest-edition))

→ Full walkthrough (all outcomes, bypass, troubleshooting): [examples/merge-gate-demo](./examples/merge-gate-demo/) · How it works: [docs/merge-gate-explained.md](./docs/merge-gate-explained.md)

---

> **Philosophy** — AI Crew Kit manages *how software gets made*, not *how code gets written*. Claude owns the code and the technical judgment; the framework provides workflow automation, quality gates, and team conventions. Any protocol, any library — the framework guards the process around it.

---

<!-- PARITY: this Why section pairs with README.ko.md "그냥 Claude Code만 쓰면 안 되나?" — always update both together -->
## 🧭 Why not just plain Claude Code?

Claude Code alone already writes excellent code. What it doesn't give you is a *process* that holds up across sessions, branches, and contributors:

| Plain Claude Code | With AI Crew Kit |
|---|---|
| "Don't merge with unresolved CRITICALs" is a prompt — holds until the model has a bad day | A bash PreToolUse hook denies `gh pr merge` *before it runs* — **no model in the decision loop** |
| Workflow context lives in chat history — gone when the session ends | Backlog, task locks, review decisions, continuation plans live in versioned state files — sessions resume, teammates see the same state |
| Phase transitions happen implicitly | feature → plan → impl → review → merge chains automatically, with explicit human approval gates recorded in state |
| Conventions get re-pasted every session | Stack-aware conventions and review checklists resolve automatically — reviews load them without being asked |

If all you need is code generation, you don't need this kit. If you want the *process around the code* to be inspectable and enforced, that's what it adds.

---

## 🚀 Quick start

Installs as a **Claude Code plugin** — 22 skills + 7 agents + quality-gate hooks (SessionStart / PreToolUse / PostToolUse / Stop) registered in one step.

```bash
# inside a Claude Code session
/plugin marketplace add wejsa/ai-crew-kit
/plugin install ai-crew-kit@ai-crew-kit
```

Then, in any project:

```bash
/aick-init --quick     # zero-decision mode — running in ~5 minutes
/aick-init             # interactive — choose everything yourself
/aick-onboard          # existing codebase — auto-scan the stack, generate config
```

`/aick-init` takes you from a free-form requirements description → LLM stack recommendation → agent team → an opt-in auto-decomposed backlog of 10–25 tasks, ready for the `/aick-plan` → `/aick-impl` chain. Requirements input passes a trust boundary: prompt-injection defenses, shell/path-traversal sanitization, hard limits (≤10 tasks per phase, ≤30 total).

**Updating** (manual — community marketplace, no auto-update):

```
/plugin marketplace update ai-crew-kit     # ① refresh the catalog first
/plugin update ai-crew-kit@ai-crew-kit      # ② update the plugin
/reload-plugins                             # ③ apply to the current session
```

Then run `/aick-upgrade` once in each project that uses the kit — it applies project-local migrations (`.gitignore` entries, `kitVersion`, `CLAUDE.md` regeneration) that a plugin cache swap can't reach (v4.8.0+).

> [!IMPORTANT]
> **v4.5.x → v4.6.0 is BREAKING**: skill commands were renamed `/crew-*` → `/aick-*`. Coming from a v4.0–4.5 seed, run `/crew-upgrade --version v4.6.0` once (it replaces itself with `aick-upgrade`), then use `/aick-*`. Details: [upgrade guide (Korean)](./docs/upgrade-guide.md) · update troubleshooting: [한국어 안내](./README.ko.md#기존-사용자--업데이트)

---

## 🛡 The merge quality gate

"Unresolved CRITICAL findings block the merge" is not a prompt instruction here — it is a **bash PreToolUse hook** that denies `gh pr merge` with `exit 2` *before the command runs*.

| Signal | Source | Behavior |
|--------|--------|----------|
| **A (state)** | `workflowState.lastReviewDecision == REQUEST_CHANGES`, joined on `step.prNumber` | deterministic, fully offline |
| **A2 (transient state)** | hotfix/ad-hoc review decision in `review-decisions.json` | deterministic, fully offline, local-only |
| **B (GitHub)** | `reviewDecision == CHANGES_REQUESTED` | best-effort, networked |

Infrastructure failures **fail open** — a broken gate must never block legitimate work. Bypass is explicit, human-only, and audited: `CCK_GATE_BYPASS=1` must be in the CLI's own environment, and inline prefixes never reach the hook — **Claude cannot bypass its own gate**. Every block and bypass lands in `hook-errors.log`.

→ Deep dive: [docs/merge-gate-explained.md](./docs/merge-gate-explained.md)

---

## ✨ What you get

| | |
|---|---|
| **Native Claude Code hooks** | session git sync · lock heartbeats · continuation plans · deterministic merge blocking |
| **Workflow chaining** | feature → plan → impl → review → merge, with user-approval gates between phases |
| **Tiered PR review** | T0–T3 auto-routing by PR shape + severity×confidence false-positive filter — CRITICALs are downgraded-but-posted, never dropped |
| **Skill profiles & model routing** | `full` / `developer` / `docs-only` profiles · implementation on `sonnet`, quality judgment pinned to `opus` |
| **Layered conventions** | `_base` conventions & checklists, overridden per project via `project.json` — reviews pick them up automatically |
| **Secrets scanner** | hardcoded keys (AWS / GitHub / Slack / …) and `.env` exposure flagged as CRITICAL |
| **Health check** | doc↔code drift, state integrity, security, agent config — scored, trended, `--fix`-able |
| **Concurrency safety** | task locks + TTL + file-membership heartbeats for safe multi-session work |

## ⚡ Commands

| Command | What it does |
|---------|--------------|
| `/aick-status` | project status, backlog summary, lock state |
| `/aick-feature` | plan a new feature → requirements doc + backlog task |
| `/aick-plan` | design analysis + step breakdown (user-approval gate) |
| `/aick-impl` | implement step by step, open PRs (`--next` for the next step) |
| `/aick-review-pr` | multi-perspective PR review (tiered, confidence-scored) |
| `/aick-merge-pr` | squash-merge + state update |
| `/aick-hotfix` · `/aick-rollback` | emergency main fix · audited release rollback |
| `/aick-retro` · `/aick-report` · `/aick-health-check` | retrospectives · metrics · codebase health |

Natural-language triggers work too ("review PR 123"). Full list + "which skill, when?" guide: [skill reference](./docs/skill-reference.en.md) ([KO](./docs/skill-reference.md)).

## 🛠 Supported stacks

Spring Boot (Kotlin · Java) · Node.js (TypeScript) · Python (FastAPI · Django) · Go — Next.js · React · Vue · Nuxt · Astro — MySQL · PostgreSQL · MongoDB · SQLite — Redis · RabbitMQ · Docker Compose

> The framework is stack-neutral. The list above gets automatic build/test detection and conventions; Claude implements everything else (WebSocket, GraphQL, gRPC, …) just as well — the framework guards the process, not the technology.

---

## 📖 Documentation

| Document | Language |
|----------|----------|
| [Getting started](./docs/getting-started.en.md) | **EN** · [KO (full)](./docs/getting-started.md) |
| [Core concepts](./docs/concepts.en.md) | **EN** · [KO (full)](./docs/concepts.md) |
| [Merge gate explained](./docs/merge-gate-explained.md) | **EN** · [KO](./docs/merge-gate-explained.ko.md) |
| [Merge gate demo (5 min)](./examples/merge-gate-demo/) | **EN** · [KO](./examples/merge-gate-demo/README.ko.md) |
| [Skill reference](./docs/skill-reference.en.md) | **EN** · [KO](./docs/skill-reference.md) |
| [Workflow guide](./docs/workflow-guide.md) | KO |
| [Token optimization](./docs/token-optimization.md) | KO |
| [Customization](./docs/customization.md) | KO |
| [Upgrade guide](./docs/upgrade-guide.md) | KO |
| [Eject guide](./docs/eject-guide.md) | KO |
| [Changelog](./CHANGELOG.md) | KO |

## 📋 Requirements

| | |
|---|---|
| **Required** | [Claude Code](https://claude.ai/download) CLI |
| **Recommended** | Claude Code v2.1.49+ (native git worktrees) · Git 2.30+ · `jq` + `timeout` (the merge gate needs both to evaluate — without them it fails open; macOS: `brew install coreutils` installs it as `gtimeout` — add gnubin to `PATH`) |

> No external runtime — the framework is prose, bash, and JSON Schema. Your project's stack brings its own toolchain (Node.js, Python, Go, JDK, …). For parallel work, `claude --worktree <name>` and external orchestrators are auto-detected by all skills.

---

<div align="center">

[MIT License](./LICENSE) · [Changelog](./CHANGELOG.md) · [Issues](https://github.com/wejsa/ai-crew-kit/issues) · [한국어 README](./README.ko.md)

</div>
