# Merge Gate Explained

> [← Back to README](../README.md) · Try it live: [examples/merge-gate-demo](../examples/merge-gate-demo/)

**TL;DR** — AI Crew Kit blocks `gh pr merge` for any PR whose last review posted an unresolved
CRITICAL finding. The block is not a prompt, a convention, or an instruction the model is asked
to follow — it is a **bash PreToolUse hook that exits 2 before the command runs**. Claude cannot
talk its way past it, and it cannot bypass it from inside the session.

---

## 1. The problem: prose is not enforcement

Every AI coding workflow has some version of this rule:

> *"If the review finds a CRITICAL issue, do not merge the PR."*

In most frameworks that rule lives in a prompt. The model reads it, usually follows it — and
occasionally doesn't. A long instruction file, a compacted context window, an ambiguous review
summary, and a single wrong branch later, a PR with a known CRITICAL defect is auto-merged.
Nobody chose that; the prose just didn't hold.

AI Crew Kit treats this rule as too important for prose. The merge decision is delegated to the
one layer in a Claude Code session that is fully deterministic: a **hook**.

```
Claude decides to run:  gh pr merge 42 --squash
        │
        ▼
PreToolUse hook (bash) ── reads .claude/state/backlog.json
        │                  reads GitHub reviewDecision (best-effort)
        │
        ├── unresolved CRITICAL?  ──► exit 2  ──► command NEVER runs
        │                                          Claude receives the denial reason
        └── otherwise             ──► exit 0  ──► command proceeds normally
```

The hook is `.claude/hooks/pre-tool-use.sh` (~160 lines of plain bash). It is registered for the
`Bash` tool matcher, ignores every command except `gh pr merge`, and never calls an LLM.

For how this hook fits into the kit's hook taxonomy (bookkeeping vs gate, and why bookkeeping
hooks must never block), see the SSOT table in
[`.claude/hooks/README.md`](../.claude/hooks/README.md) — not duplicated here.

---

## 2. How it decides: two signals

### Signal A — workflow state (offline, deterministic)

The kit's review skill records its verdict in `backlog.json`. The gate looks up the task that
*owns* the PR being merged and reads that verdict:

```jq
.tasks[]?
| select(
    (.workflowState.prNumber // -1) == $n          # recorded by the review workflow
    or any((.steps // [])[]?; (.prNumber // -1) == $n)   # recorded at PR creation (SSOT)
  )
| .workflowState.lastReviewDecision
```

If the owning task's `lastReviewDecision` is exactly `"REQUEST_CHANGES"`, the merge is blocked.
Two details matter:

- **The join is double-keyed.** PR numbers are recorded both at PR creation
  (`steps[].prNumber`) and by the review workflow (`workflowState.prNumber`). The gate matches
  either, so it fires regardless of which field a given workflow populated.
- **Types are strict.** `prNumber` must be a JSON integer. The schema rejects `"42"` (string),
  and the gate's `jq --argjson` comparison would never match it. This is enforced by
  `backlog.schema.json` in CI.

Signal A needs **no network, no GitHub account, and no real PR**. That is what makes the
[5-minute demo](../examples/merge-gate-demo/) possible: a single fixture file is enough to make
the gate fire.

### Signal B — GitHub review decision (best-effort, networked)

If Signal A does not block, the gate asks GitHub:

```bash
timeout 8 gh pr view <N> --json reviewDecision
```

If GitHub reports `CHANGES_REQUESTED` — for example a human reviewer requested changes on a
teammate's PR that has no local backlog state — the merge is blocked too. Any failure here
(no `gh`, no network, no auth, timeout) is silently ignored: Signal B is an extra net, not a
dependency. Set `CCK_GATE_NO_GH=1` to skip it entirely (air-gapped environments, deterministic
tests).

Signal A wins ties: if it already blocked, Signal B is never consulted.

---

## 3. Fail-open by design

The gate has one job: *block a merge when a signal clearly says "blocked."* It refuses to have a
second job — breaking your workflow when the gate itself is degraded. Every infrastructure
failure resolves to **allow**:

| # | Condition | Behavior |
|---|-----------|----------|
| 1 | `CCK_MERGE_GATE=off` (also `false`/`0`/`no`) | gate disabled — allow |
| 2 | Project directory inaccessible | allow |
| 3 | No stdin payload from the harness | allow |
| 4 | `timeout` binary missing (stdin read uses it) | allow |
| 5 | `jq` not installed | allow |
| 6 | No command string in the tool input | allow |
| 7 | Command is not `gh pr merge` | allow (out of scope) |
| 8 | `CCK_GATE_BYPASS=1` | allow — **logged + banner** |
| 9 | PR number can't be extracted (e.g. current-branch merge) | allow — logged |
| 10 | `backlog.json` absent | Signal A skipped |
| 11 | `backlog.json` unparseable | Signal A skipped |
| 12 | No task owns this PR / decision is `APPROVED`·`COMMENT`·null | no block |
| 13 | Signal B: `gh` missing, network/auth failure, 8s timeout, or `CCK_GATE_NO_GH=1` | Signal B skipped |

Why not fail-closed? Because a gate that blocks merges when `jq` is missing punishes you for its
own dependencies, and a gate that people learn to disable is worse than no gate. The trade-off
is explicit: **a degraded gate is silent**. If you demo it and "nothing happens," walk the table
above — the demo's [troubleshooting section](../examples/merge-gate-demo/) does exactly that.

---

## 4. Bypass and control

Three environment variables, three different intents:

| Variable | Intent | Scope |
|----------|--------|-------|
| `CCK_GATE_BYPASS=1` | *"I understand, merge anyway."* One deliberate override. Logged to the audit trail and announced with a 🔓 banner. | full bypass |
| `CCK_MERGE_GATE=off` | *"Don't run this gate at all."* | full disable |
| `CCK_GATE_NO_GH=1` | *"Never call the network."* Signal A still enforces. | partial — disables Signal B only |

A property worth knowing: **the bypass cannot be triggered from inside the session.** The hook
reads its *own* process environment — the one Claude Code was started with. A command-string
prefix (`CCK_GATE_BYPASS=1 gh pr merge 42`) or an `export` in a previous Bash call never reaches
the hook process, so the merge is still blocked. To actually bypass, a human has to either
restart the CLI as `CCK_GATE_BYPASS=1 claude` or put the variable in `settings.json` `env`.
In other words: *Claude cannot bypass its own merge gate — only you can.*

---

## 5. Audit trail

Every consequential gate event is appended to `.claude/state/hook-errors.log`:

```
[2026-06-11T09:14:02Z] [pre-tool-use] merge blocked: PR #42 — backlog: last review decision is REQUEST_CHANGES (unresolved CRITICAL posted)
[2026-06-11T09:16:40Z] [pre-tool-use] merge gate bypassed (CCK_GATE_BYPASS) — cmd: gh pr merge 42 --squash
```

Blocks and bypasses are both recorded, so "who overrode the gate and when" is answerable after
the fact. (PR-number extraction failures are logged too, since they fail open.)

---

## 6. Try it standalone (no Claude session required)

The hook is plain bash reading JSON on stdin, so you can exercise it directly from a checkout of
this repo:

```bash
# from the ai-crew-kit repo root
D=$(mktemp -d) && mkdir -p "$D/.claude/state"
cp examples/merge-gate-demo/.claude/state/backlog.json "$D/.claude/state/"

# blocked: PR 42 has an unresolved CRITICAL in the fixture
echo '{"tool_input":{"command":"gh pr merge 42 --squash"}}' \
  | CLAUDE_PROJECT_DIR="$D" CCK_GATE_NO_GH=1 bash .claude/hooks/pre-tool-use.sh; echo "exit=$?"   # → 2

# allowed: PR 99 is owned by nobody
echo '{"tool_input":{"command":"gh pr merge 99"}}' \
  | CLAUDE_PROJECT_DIR="$D" CCK_GATE_NO_GH=1 bash .claude/hooks/pre-tool-use.sh; echo "exit=$?"   # → 0
```

The fixture (snapshot below — the canonical copy lives in
[`examples/merge-gate-demo/.claude/state/backlog.json`](../examples/merge-gate-demo/.claude/state/backlog.json))
is a single task whose step created PR #42 and whose review recorded `REQUEST_CHANGES`:

```json
{
  "steps": [{ "number": 1, "title": "Rate limiter middleware", "status": "pr_created", "prNumber": 42 }],
  "workflowState": { "prNumber": 42, "lastReviewDecision": "REQUEST_CHANGES" }
}
```

The gate's behavior is pinned by a regression suite —
[`.claude/hooks/tests/test-pre-tool-use-merge-gate.sh`](../.claude/hooks/tests/test-pre-tool-use-merge-gate.sh)
covers blocking, allowing, bypass, fail-open paths, and PR-number extraction edge cases
(URLs, flags, embedded digits, leading zeros), and runs in CI.

---

## 7. What the gate does *not* do (honest edition)

A deterministic gate is only as good as the boundary it sits on. Know the edges:

- **It enforces the decision, not the signal.** Signal A reads state that the review workflow
  *writes*. If a review never ran — or never recorded `lastReviewDecision` — Signal A has
  nothing to enforce and falls back to Signal B. The gate makes "merge despite a recorded
  CRITICAL" impossible; it does not conjure reviews that didn't happen.
- **It gates Claude's Bash tool, not your terminal.** Typing `gh pr merge 42` yourself in a
  shell outside Claude Code is not intercepted — this is a Claude Code hook, not a server-side
  rule. For team-wide hard enforcement, combine it with GitHub branch protection; the gate is
  the in-session layer.
- **Workflow paths that never register a backlog task** (e.g. an emergency hotfix created
  outside the standard plan→impl→review chain) are covered by Signal B only.
- **Bypass is a feature.** `CCK_GATE_BYPASS=1` exists on purpose, is user-only (see §4), and is
  logged. A gate without a deliberate exit teaches people to disable it permanently.

---

## 8. FAQ

**The demo did nothing — the merge just went through. Why?**
Walk the fail-open table (§3) in order: ① `command -v jq timeout` — both must exist.
② `env | grep CCK_` — a leftover `CCK_MERGE_GATE=off` or `CCK_GATE_BYPASS=1` silently allows.
③ You must start the Claude session **in the directory that contains `.claude/state/backlog.json`**
— the hook resolves state from the session's project root (`CLAUDE_PROJECT_DIR`), so `cd`-ing
into a demo folder mid-session does not count. ④ Check `.claude/state/hook-errors.log` for an
extraction-failure entry.

**Does blocking need the network?**
No. Signal A is pure local file reads — the demo blocks in ~50ms with zero network calls.
Signal B is the only networked step, is best-effort, and is skippable with `CCK_GATE_NO_GH=1`.

**Can Claude set `CCK_GATE_BYPASS=1` and merge anyway?**
No. Inline prefixes and in-session `export`s don't reach the hook's process environment (§4).
Restarting the CLI with the variable — the only effective route — is a human action.

**Why `exit 2` and not a permission prompt?**
`exit 2` from a PreToolUse hook is Claude Code's deny contract: the tool call is rejected and
stderr is fed back to Claude as the reason. The model sees *why* it was blocked and can act on
the suggested next steps (fix and re-review, or ask you to bypass).

**Is the whole framework this deterministic?**
No, and we won't pretend otherwise. The merge gate, lock heartbeat/expiry, schema validation,
and hook-safety static checks are deterministic; most workflow steps are still LLM-followed
instructions. The kit's design principle is to move the *highest-stakes* decisions into the
deterministic layer first — the merge gate is the flagship of that approach.

---

*See also: [examples/merge-gate-demo](../examples/merge-gate-demo/) (5-minute hands-on) ·
[`.claude/hooks/README.md`](../.claude/hooks/README.md) (hook taxonomy SSOT) ·
[workflow guide](./workflow-guide.md) (where the review verdict comes from).*
