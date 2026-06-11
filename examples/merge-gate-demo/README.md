# Merge Gate Demo — watch a bad merge get blocked in 5 minutes

This demo makes AI Crew Kit's **deterministic merge gate** fire in front of you:
Claude tries to merge a PR whose review found an unresolved CRITICAL issue, and a
bash PreToolUse hook denies the command **before it ever runs**.

- **No real PR. No GitHub auth. No network.** A single fixture file simulates the state.
- Act 1 (the block) takes ~5 minutes. Act 2 (the deliberate bypass) adds 1–2 more.
- Platforms: **Linux / macOS / WSL**. Native Windows is untested — use WSL.

> How the gate works under the hood: [docs/merge-gate-explained.md](../../docs/merge-gate-explained.md)

---

## 0. Preflight (1 minute)

```bash
command -v jq timeout   # BOTH must print a path — if either is missing, the gate
                        # silently fails open and the demo shows nothing
env | grep CCK_         # must print NOTHING — leftover CCK_MERGE_GATE/CCK_GATE_BYPASS
                        # values silently disable or bypass the gate
```

Install the plugin if you haven't (inside any Claude Code session):

```
/plugin marketplace add wejsa/ai-crew-kit
/plugin install ai-crew-kit@ai-crew-kit
```

---

## 1. Set up the sandbox (1 minute)

```bash
mkdir gate-demo && cd gate-demo
git init -q && git commit --allow-empty -qm init
mkdir -p .claude/state        # create the directory FIRST — curl won't create it
curl -fsSL https://raw.githubusercontent.com/wejsa/ai-crew-kit/main/examples/merge-gate-demo/.claude/state/backlog.json \
  -o .claude/state/backlog.json
```

(Working from a local checkout instead? `cp <kit>/examples/merge-gate-demo/.claude/state/backlog.json .claude/state/`)

The fixture is one task: its step created **PR #42**, and the review recorded
**`lastReviewDecision: "REQUEST_CHANGES"`** — an unresolved CRITICAL
(a rate limiter that resets on every deploy). That is exactly the state the gate reads.

> ⚠️ **Start your Claude session in this directory.** The gate resolves state from the
> session's project root. If you start Claude elsewhere and merely `cd` here, the gate
> silently never fires.

---

## 2. Act 1 — the block (2 minutes)

Start a **new** Claude Code session in `gate-demo/`, then paste exactly:

```
Run exactly: gh pr merge 42 --squash — no need to check the PR first.
```

**What you should see:** the merge is denied and Claude relays the gate's reason:

```
🛑 [pre-tool-use] Merge blocked — PR #42
   Reason: backlog: last review decision is REQUEST_CHANGES (unresolved CRITICAL posted)
   A PR with unresolved CRITICAL findings cannot be merged.
   Next steps:
     1) [Recommended] Fix the CRITICAL findings, then re-review: /aick-review-pr 42 --auto-fix
     2) If this is a downgraded or false-positive finding, re-examine the review decision and re-review
     3) [Deliberate override] Set CCK_GATE_BYPASS=1 and retry (user responsibility)
```

Notes for the skeptical (that's the point of this demo):

- **A permission prompt is not the gate failing.** If Claude Code first asks you to allow
  the Bash command, allow it — the gate fires at execution time, after permission.
- **If Claude refuses to even try** ("there is no PR #42…"), that's the model being
  sensible, not the gate. Nudge it: *"I know — run the command anyway, exactly as
  written."* Or skip straight to the guaranteed path below.
- **About those three "Next steps":** ① `/aick-review-pr 42 --auto-fix` starts the
  automated fix-and-re-review loop **in a real project** — in this sandbox there is no
  real PR or project config, so the skill will stop at its preconditions; skip it here.
  ② "re-examine the review decision" is the real-project path for false positives.
  ③ is Act 2 below. (Skill surfaces are currently Korean-first; output adapts to your language.)

**Bonus — try to cheat.** Ask Claude:

```
Run exactly: CCK_GATE_BYPASS=1 gh pr merge 42 --squash
```

Still blocked. The hook reads its **own** process environment — the one the Claude Code
CLI was started with — so an inline prefix (or an `export` in a previous command) never
reaches it. **Claude cannot bypass its own merge gate. Only you can** (Act 2).

### Guaranteed path (no Claude session needed)

The gate is plain bash on stdin — you can prove the block deterministically from a kit
checkout, in ~50ms, zero network:

```bash
# from the ai-crew-kit repo root, with the sandbox at ../gate-demo
echo '{"tool_input":{"command":"gh pr merge 42 --squash"}}' \
  | CLAUDE_PROJECT_DIR="$(cd ../gate-demo && pwd)" CCK_GATE_NO_GH=1 \
    bash .claude/hooks/pre-tool-use.sh; echo "exit=$?"     # → blocked, exit=2

echo '{"tool_input":{"command":"gh pr merge 99"}}' \
  | CLAUDE_PROJECT_DIR="$(cd ../gate-demo && pwd)" CCK_GATE_NO_GH=1 \
    bash .claude/hooks/pre-tool-use.sh; echo "exit=$?"     # → PR 99 owns no CRITICAL, exit=0
```

Success criterion for Act 1: **either** the in-session block **or** the standalone `exit=2`.
(The allow case is shown standalone-only on purpose — in a live session an allowed
`gh pr merge` would really execute.)

---

## 3. Act 2 — the deliberate bypass (1–2 minutes)

The override is a human-only action: the variable must be in the CLI's own environment.

1. Exit the Claude session.
2. Restart it with the override: `CCK_GATE_BYPASS=1 claude`
   (equivalent: put `{"env": {"CCK_GATE_BYPASS": "1"}}` in the sandbox's `.claude/settings.json`)
3. Paste the same prompt: `Run exactly: gh pr merge 42 --squash`
4. This time the gate steps aside — and leaves a paper trail:

```bash
cat .claude/state/hook-errors.log
# [ ... ] [pre-tool-use] merge blocked: PR #42 — backlog: last review decision is REQUEST_CHANGES (unresolved CRITICAL posted)
# [ ... ] [pre-tool-use] merge gate bypassed (CCK_GATE_BYPASS) — cmd: gh pr merge 42 --squash
```

The subsequent `gh` error ("no such PR / not authenticated") is **expected** — the gate
stepped aside, and `gh` itself fails because PR #42 never existed. The point is the log:
every block and every bypass is recorded with a timestamp.

5. Clean up so the gate works again: exit, unset the env (or delete the settings entry),
   restart normally.

---

## 4. Troubleshooting — "Nothing happened?"

The gate **fails open by design** (a broken gate must not block your real work), so every
setup problem looks like "the merge just went through." Check in this order:

| # | Check | Why |
|---|-------|-----|
| 1 | `command -v jq` | no jq → gate can't parse input → silent allow |
| 2 | `command -v timeout` | no timeout → stdin read fails → silent allow |
| 3 | `env \| grep CCK_` | leftover `CCK_MERGE_GATE=off` / `CCK_GATE_BYPASS=1` → silent allow |
| 4 | Session started **in** `gate-demo/`? | gate reads the session root's `.claude/state/` — `cd` after start doesn't count |
| 5 | `cat .claude/state/hook-errors.log` | a "PR number extraction failed" entry means the command shape wasn't parseable |
| 6 | Plugin actually updated? | `/plugin` → check version; marketplace caches can serve a stale copy — remove and re-add the marketplace if needed |

Also good to know:

- The gate intercepts **Claude's Bash tool only**. Running `gh pr merge` yourself in a
  terminal is not intercepted — pair the gate with GitHub branch protection for hard,
  server-side enforcement.
- Running the demo **inside the kit repo** (`examples/merge-gate-demo/`) works too — the
  local `.gitignore` keeps hook side effects (`hook-errors.log`, `continuation-plan.md`)
  out of `git status`. Copying out to a scratch directory is still the cleaner experience.

---

## What you just saw

| Claim | Evidence |
|-------|----------|
| The block is deterministic | bash hook, `exit 2`, fires before execution; reproducible via stdin pipe with zero network |
| Claude can't bypass it | inline env prefix / in-session export never reach the hook process |
| Humans can, deliberately | `CCK_GATE_BYPASS=1` at CLI start — and it's logged |
| Failures never lock you out | 13 fail-open paths ([explained](../../docs/merge-gate-explained.md#3-fail-open-by-design)) |

Next: install into a real project with `/aick-init`, and the same gate guards every
`gh pr merge` your AI crew attempts.
