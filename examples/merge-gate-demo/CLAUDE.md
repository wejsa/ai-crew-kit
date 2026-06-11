# Merge Gate Demo Sandbox

This folder is a **demo sandbox** for AI Crew Kit's deterministic merge gate. There is no
real codebase here — only a state fixture (`.claude/state/backlog.json`) that simulates
PR #42 whose review recorded an unresolved CRITICAL issue.

Session rules while this sandbox is the project root:

- When the user asks to run a shell command, run the **literal bash command exactly as
  given** with the Bash tool.
- Do **not** route the request to workflow skills (`aick-*`) here. The point of this demo
  is to watch the PreToolUse hook intercept the raw command — routing to a merge skill
  would stop the merge in prose before the hook ever fires, which defeats the demo.
- If a command is denied by a hook, relay the denial message to the user verbatim.
- Do not try to "fix" the fixture state or investigate the missing PR — the missing PR is
  intentional; the gate blocks from local state alone.
