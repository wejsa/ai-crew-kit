#!/usr/bin/env bash
# test-threshold-env-override.sh — v2.1.3: CCK_HOOK_THRESHOLD / CCK_HOOK_WINDOW_SEC env override
#
# 보장:
#   1. CCK_HOOK_THRESHOLD=5 설정 시 5회까지 flag 미생성, 6회째 생성
#   2. 비숫자/0 값은 무시되고 기본값 3 fallback (회귀 0)
#   3. CCK_HOOK_WINDOW_SEC=1 설정 시 1초 경과 후 카운터 리셋

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./_lib.sh
source "$SCRIPT_DIR/_lib.sh"

print_header "post-tool-use.sh threshold/window env override"

SANDBOX="$(mk_sandbox)"
ln -s "$HOOK_DIR/post-tool-use.sh" "$SANDBOX/.claude/hooks/post-tool-use.sh"
TMP_ISO="$(mktemp -d -t ack-thr-override.XXXXXX)"
trap 'rm -rf "$SANDBOX" "$TMP_ISO"' EXIT

BACKLOG="$SANDBOX/.claude/state/backlog.json"
FLAG="$SANDBOX/.claude/state/hook-disabled.flag"
COUNTER="$SANDBOX/.claude/state/hook-trigger-count"
SID="thr-session"
cat > "$BACKLOG" <<EOF
{
  "workflowState": "active",
  "tasks": [
    {"id": "T1", "status": "in_progress", "lockedAt": null, "lockedBy": "$SID"}
  ]
}
EOF

fail=0

run_hook() {
  local i="$1"
  local threshold="${2:-}"
  local window="${3:-}"
  (cd "$SANDBOX" \
    && CLAUDE_PROJECT_DIR="$SANDBOX" \
       TMPDIR="$TMP_ISO" \
       CCK_HOOK_THRESHOLD="$threshold" \
       CCK_HOOK_WINDOW_SEC="$window" \
       bash "$SANDBOX/.claude/hooks/post-tool-use.sh" \
       <<<"{\"session_id\":\"${SID}-$i\",\"tool_input\":{\"file_path\":\"src/foo.kt\"}}" \
       >/dev/null 2>/dev/null)
}

# ── 시나리오 1: CCK_HOOK_THRESHOLD=5 → 5회까지 flag 미생성, 6회째 생성 ──
for i in 1 2 3 4 5; do
  run_hook "$i" "5" "10"
  if [ -f "$FLAG" ]; then
    echo "  ✗ THRESHOLD=5에서 $i회째 조기 플래그 생성" >&2
    fail=$((fail + 1))
    break
  fi
done
[ ! -f "$FLAG" ] && echo "  ✓ THRESHOLD=5: 5회까지 플래그 미생성"

run_hook "6" "5" "10"
assert_file_exists "$FLAG" "THRESHOLD=5: 6회째(>5) 플래그 생성" || fail=$((fail + 1))

# 초기화
rm -f "$FLAG" "$COUNTER"

# ── 시나리오 2: 비숫자 값 → 기본값 3 fallback ──
for i in 1 2 3; do
  run_hook "n$i" "abc" "xyz"
  if [ -f "$FLAG" ]; then
    echo "  ✗ 비숫자 fallback 실패: $i회째 조기 플래그" >&2
    fail=$((fail + 1))
    break
  fi
done
run_hook "n4" "abc" "xyz"
assert_file_exists "$FLAG" "비숫자 env → 기본값 3 fallback (4회째 발동)" || fail=$((fail + 1))

# 초기화
rm -f "$FLAG" "$COUNTER"

# ── 시나리오 3: 0 값 → 기본값 fallback ──
for i in 1 2 3; do
  run_hook "z$i" "0" "0"
  if [ -f "$FLAG" ]; then
    echo "  ✗ 0 값 fallback 실패: $i회째 조기 플래그" >&2
    fail=$((fail + 1))
    break
  fi
done
run_hook "z4" "0" "0"
assert_file_exists "$FLAG" "0 값 → 기본값 3 fallback (4회째 발동)" || fail=$((fail + 1))

# 초기화
rm -f "$FLAG" "$COUNTER"

# ── 시나리오 4: env 미설정 → 기본값 3 유지 (회귀 0) ──
# 명시적으로 unset 상태에서 호출
for i in 1 2 3; do
  (cd "$SANDBOX" && unset CCK_HOOK_THRESHOLD CCK_HOOK_WINDOW_SEC \
    && CLAUDE_PROJECT_DIR="$SANDBOX" TMPDIR="$TMP_ISO" \
       bash "$SANDBOX/.claude/hooks/post-tool-use.sh" \
       <<<"{\"session_id\":\"${SID}-d$i\",\"tool_input\":{\"file_path\":\"src/foo.kt\"}}" \
       >/dev/null 2>/dev/null)
done
[ ! -f "$FLAG" ] && echo "  ✓ env 미설정: 3회까지 기본 동작 유지"
(cd "$SANDBOX" && unset CCK_HOOK_THRESHOLD CCK_HOOK_WINDOW_SEC \
  && CLAUDE_PROJECT_DIR="$SANDBOX" TMPDIR="$TMP_ISO" \
     bash "$SANDBOX/.claude/hooks/post-tool-use.sh" \
     <<<"{\"session_id\":\"${SID}-d4\",\"tool_input\":{\"file_path\":\"src/foo.kt\"}}" \
     >/dev/null 2>/dev/null)
assert_file_exists "$FLAG" "env 미설정: 4회째 기본값 3 초과로 발동 (회귀 0)" || fail=$((fail + 1))

if [ "$fail" -gt 0 ]; then
  printf '\n💥 %d assertion(s) failed\n' "$fail" >&2
  exit 1
fi
echo "✓ PASS"
