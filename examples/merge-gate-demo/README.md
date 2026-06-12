<!-- PARITY: this document pairs with README.ko.md (Korean) — always update both together -->

# Merge Gate Demo — watch a bad merge get blocked in 5 minutes

English · [한국어](./README.ko.md)

This demo makes AI Crew Kit's **deterministic merge gate** fire in front of you:
Claude tries to merge a PR whose review found an unresolved CRITICAL issue, and a
bash PreToolUse hook denies the command **before it ever runs**.

- **No real PR. No GitHub auth.** The gate itself makes zero network calls — a single fixture file simulates the state (setup fetches it once, or copy it from a local checkout).
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

> **Scope matters.** The CLI command above installs **user-wide** — it works in any folder.
> If you installed through the `/plugin` UI and picked **project** (or local) scope, the
> plugin does **not** follow you to other directories. In the demo session, confirm
> `/plugin list --enabled` shows `ai-crew-kit`; if it doesn't, run the two commands above
> inside that session.

---

## 1. Set up the sandbox (1 minute)

In a **regular terminal** (not the Claude prompt), anywhere you like — this is a throwaway
folder, unrelated to wherever you installed the plugin:

```bash
mkdir gate-demo && cd gate-demo
git init -q && git commit --allow-empty -qm init
mkdir -p .claude/state        # create the directory FIRST — curl won't create it
BASE=https://raw.githubusercontent.com/wejsa/ai-crew-kit/main/examples/merge-gate-demo
curl -fsSL "$BASE/.claude/state/backlog.json" -o .claude/state/backlog.json
curl -fsSL "$BASE/CLAUDE.md" -o CLAUDE.md
```

The second file, `CLAUDE.md`, instructs the session to run requested commands **literally**
instead of routing them to the kit's own workflow skills — without it, Claude often invokes
`aick-merge-pr` and stops the merge in prose before the hook can fire (see the outcome
table in Act 1).

(Working from a local checkout instead? `cp <kit>/examples/merge-gate-demo/.claude/state/backlog.json .claude/state/ && cp <kit>/examples/merge-gate-demo/CLAUDE.md .`)

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
Do not use any skill. Run this exact bash command as-is: gh pr merge 42 --squash
```

(The "Do not use any skill" part matters — it suppresses routing to the kit's own merge
skill, which would otherwise stop the merge in prose before the hook fires.)

**What you should see** (measured in a real session): the Bash tool call itself fails with
the hook's denial — Claude Code renders it as a `PreToolUse:Bash hook error` block under the
tool call, and Claude then relays the reason in its reply:

```
● Bash(gh pr merge 42 --squash)
  ⎿  Error: PreToolUse:Bash hook error: [bash ".../pre-tool-use.sh"]:
🛑 [pre-tool-use] Merge blocked — PR #42
   Reason: backlog: last review decision is REQUEST_CHANGES (unresolved CRITICAL posted)
   A PR with unresolved CRITICAL findings cannot be merged.
   Next steps:
     1) [Recommended] Fix the CRITICAL findings, then re-review: /aick-review-pr 42 --auto-fix
     2) If this is a downgraded or false-positive finding, re-examine the review decision and re-review
     3) [Deliberate override] Set CCK_GATE_BYPASS=1 and retry (user responsibility)
```

**Which layer actually stopped it?** Live-model routing varies run to run — three outcomes
are possible. **All three stop the bad merge; none of them means your setup is broken.**
The table only tells you *which layer* did it (`cat .claude/state/hook-errors.log` is the
discriminator) — row 1 is the deterministic layer this demo exists to show:

| Outcome | Layer that fired | hook-errors.log |
|---------|------------------|-----------------|
| 🛑 denial before execution (message above) | **deterministic hook** — what this demo is about | `merge blocked: PR #42` line |
| Claude invokes `aick-merge-pr`, reads the backlog, refuses | prose layer — defense in depth worked, but the hook never fired | empty / absent |
| Claude declines ("there is no PR #42…") | the model being sensible on its own | empty / absent |

Rows 2–3 still stop the bad merge — but through the *probabilistic* layer. To see the
deterministic one, re-paste the exact prompt above (its "Do not use any skill" prefix plus
the sandbox `CLAUDE.md` suppress skill routing), or jump to the guaranteed path below.
Seeing the prose layer first and the hook second is the framework's thesis demonstrated
twice: the model usually does the right thing — the hook is for when it doesn't.

Notes for the skeptical (that's the point of this demo):

- **A permission prompt is not the gate failing.** If Claude Code first asks you to allow
  the Bash command, allow it — the gate fires at execution time, after permission.
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

No kit checkout? Fetch the hook itself and run it right inside `gate-demo/`:

```bash
curl -fsSL https://raw.githubusercontent.com/wejsa/ai-crew-kit/main/.claude/hooks/pre-tool-use.sh -o /tmp/gate.sh
echo '{"tool_input":{"command":"gh pr merge 42 --squash"}}' \
  | CLAUDE_PROJECT_DIR="$PWD" bash /tmp/gate.sh; echo "exit=$?"   # → 2 (gate decision: zero network calls)
```

Success criterion for Act 1: **either** the in-session block *with a `merge blocked` line in
`hook-errors.log`*, **or** the standalone `exit=2`.
(The allow case is shown standalone-only on purpose — in a live session an allowed
`gh pr merge` would really execute.)

---

## 3. Act 2 — the deliberate bypass (1–2 minutes)

The override is a human-only action: the variable must be in the CLI's own environment.

1. Exit the Claude session.
2. Restart it with the override: `CCK_GATE_BYPASS=1 claude`
   (equivalent: put `{"env": {"CCK_GATE_BYPASS": "1"}}` in the sandbox's `.claude/settings.json`)
3. Paste the same Act 1 prompt: `Do not use any skill. Run this exact bash command as-is: gh pr merge 42 --squash`
4. This time the gate steps aside. Two things about what you'll see (measured in a real session):

- You will **not** see the 🔓 bypass banner in the UI — it goes to the hook's stderr, and
  Claude Code only surfaces hook stderr for *blocking* (exit 2) hooks. Don't wait for it.
- The visible signal is the **error's provenance shifting**: in Act 1 the failure was a
  `PreToolUse:Bash hook error … Merge blocked` (the command never ran); now the command
  **actually executes** and `gh` itself fails (`no git remotes found` — PR #42 never
  existed). That shift — hook error → gh error — *is* the bypass working.

And it leaves a paper trail:

```bash
cat .claude/state/hook-errors.log
# [ ... ] [pre-tool-use] merge blocked: PR #42 — backlog: last review decision is REQUEST_CHANGES (unresolved CRITICAL posted)
# [ ... ] [pre-tool-use] merge gate bypassed (CCK_GATE_BYPASS) — cmd: gh pr merge 42 --squash
```

Every block and every bypass is recorded with a timestamp — a human can open the gate,
but never silently.

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
| 7 | Plugin enabled for **this** session? | `/plugin list --enabled` must show `ai-crew-kit` — **project/local-scope installs don't carry over** to new folders; install user-wide (CLI command) or enable it in this session |
| 8 | Merge stopped but log is empty? | the **prose layer** (skill routing / model judgment) stopped it, not the hook — re-paste the exact Act 1 prompt to exercise the hook |

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
| Failures never lock you out | 14 fail-open paths ([explained](../../docs/merge-gate-explained.md#3-fail-open-by-design)) |

Next: install into a real project with `/aick-init`, and the same gate guards every
`gh pr merge` your AI crew attempts.
