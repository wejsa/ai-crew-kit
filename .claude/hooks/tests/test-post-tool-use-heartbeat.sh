#!/usr/bin/env bash
# test-post-tool-use-heartbeat.sh — file-membership heartbeat (v4.5.0):
#   편집 파일이 in_progress Task의 lockedFiles에 속하면 lockedAt 갱신, 아니면 미갱신.
#   (스킬이 session_id를 못 얻어 lockedBy=session_id 매칭이 불가하므로 file-membership 사용.)

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./_lib.sh
source "$SCRIPT_DIR/_lib.sh"

print_header "post-tool-use.sh file-membership heartbeat + 대조군"

SANDBOX="$(mk_sandbox)"
ln -s "$HOOK_DIR/post-tool-use.sh" "$SANDBOX/.claude/hooks/post-tool-use.sh"
TMP_ISO="$(mktemp -d -t ack-post-tool-hb.XXXXXX)"
trap 'rm -rf "$SANDBOX" "$TMP_ISO"' EXIT

BACKLOG="$SANDBOX/.claude/state/backlog.json"

# T1: in_progress + src/App.kt ∈ lockedFiles  → 편집 시 갱신
# T2: in_progress + 다른 파일만 lockedFiles    → src/App.kt 편집 시 미갱신
# T3: done + src/App.kt ∈ lockedFiles          → 상태가 in_progress 아니므로 미갱신
cat > "$BACKLOG" <<EOF
{
  "workflowState": "active",
  "tasks": {
    "T1": {"id": "T1", "status": "in_progress", "lockedAt": "2020-01-01T00:00:00Z", "lockedBy": "alice@host", "lockedFiles": ["src/App.kt"]},
    "T2": {"id": "T2", "status": "in_progress", "lockedAt": "2020-01-01T00:00:00Z", "lockedBy": "bob@host", "lockedFiles": ["src/Other.kt"]},
    "T3": {"id": "T3", "status": "done", "lockedAt": "2020-01-01T00:00:00Z", "lockedBy": "alice@host", "lockedFiles": ["src/App.kt"]}
  }
}
EOF

fail=0

# 1) src/App.kt 편집 → T1만(in_progress+lockedFiles 멤버) heartbeat 갱신
(cd "$SANDBOX" && CLAUDE_PROJECT_DIR="$SANDBOX" TMPDIR="$TMP_ISO" \
  bash "$SANDBOX/.claude/hooks/post-tool-use.sh" \
  <<<"{\"session_id\":\"any-session-1\",\"tool_input\":{\"file_path\":\"src/App.kt\"}}" \
  >/dev/null 2>&1)

t1="$(jq -r '.tasks["T1"].lockedAt' "$BACKLOG")"
t2="$(jq -r '.tasks["T2"].lockedAt' "$BACKLOG")"
t3="$(jq -r '.tasks["T3"].lockedAt' "$BACKLOG")"

if [ "$t1" != "2020-01-01T00:00:00Z" ] && [ "$t1" != "null" ]; then
  echo "  ✓ T1 (in_progress + App.kt∈lockedFiles) lockedAt 갱신됨 → $t1"
else
  echo "  ✗ T1 갱신 실패: $t1" >&2
  fail=$((fail + 1))
fi
assert_eq "2020-01-01T00:00:00Z" "$t2" "T2 (App.kt가 lockedFiles에 없음) 미갱신" || fail=$((fail + 1))
assert_eq "2020-01-01T00:00:00Z" "$t3" "T3 (done — in_progress 아님) 미갱신" || fail=$((fail + 1))

# 2) 어떤 Task의 lockedFiles에도 없는 파일 편집 → 쓰기 발생 안 함 (mtime 불변)
rm -f "$TMP_ISO"/*.lock 2>/dev/null
BEFORE_MTIME="$(stat -c %Y "$BACKLOG" 2>/dev/null || stat -f %m "$BACKLOG" 2>/dev/null || echo 0)"
sleep 1
(cd "$SANDBOX" && CLAUDE_PROJECT_DIR="$SANDBOX" TMPDIR="$TMP_ISO" \
  bash "$SANDBOX/.claude/hooks/post-tool-use.sh" \
  <<<"{\"session_id\":\"any-session-2\",\"tool_input\":{\"file_path\":\"src/Unrelated.kt\"}}" \
  >/dev/null 2>&1)
AFTER_MTIME="$(stat -c %Y "$BACKLOG" 2>/dev/null || stat -f %m "$BACKLOG" 2>/dev/null || echo 0)"
assert_eq "$BEFORE_MTIME" "$AFTER_MTIME" "lockedFiles 미스 → backlog 쓰기 스킵 (mtime 불변)" || fail=$((fail + 1))

# 3) 빈 stdin → graceful exit 0
rm -f "$TMP_ISO"/*.lock 2>/dev/null
if (cd "$SANDBOX" && CLAUDE_PROJECT_DIR="$SANDBOX" TMPDIR="$TMP_ISO" \
    bash "$SANDBOX/.claude/hooks/post-tool-use.sh" </dev/null >/dev/null 2>&1); then
  echo "  ✓ 빈 stdin graceful exit 0"
else
  echo "  ✗ 빈 stdin 비정상 종료" >&2
  fail=$((fail + 1))
fi

if [ "$fail" -gt 0 ]; then
  printf '\n💥 %d assertion(s) failed\n' "$fail" >&2
  exit 1
fi
echo "✓ PASS"
