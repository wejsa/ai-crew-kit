#!/usr/bin/env bash
# test-session-start-git.sh — TFT §4 #1,2,7: jq/git/비-git 환경 graceful skip

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./_lib.sh
source "$SCRIPT_DIR/_lib.sh"

print_header "session-start.sh graceful skip 시나리오"

SANDBOX="$(mk_sandbox)"
trap 'rm -rf "$SANDBOX"' EXIT

fail=0

# 1. 비-git 디렉토리 (H002 수정 검증 — git 설치 + .git 부재 + rev-parse 실패)
output="$(cd "$SANDBOX" && CLAUDE_PROJECT_DIR="$SANDBOX" \
  bash "$SANDBOX/.claude/hooks/session-start.sh" <<< '{}' 2>&1)"
rc=$?
assert_eq 0 "$rc" "exit 0 on non-git directory" || fail=$((fail + 1))
assert_contains "$output" "not a git directory" "non-git warning logged" || fail=$((fail + 1))

# 2. jq 미설치 환경 시뮬레이션 — 격리된 bin 디렉토리에 jq 제외한 필수 도구만 심볼릭 링크
printf '{"tasks":[]}' > "$SANDBOX/.claude/state/backlog.json"
FAKE_BIN="$SANDBOX/nojq-bin"
mkdir -p "$FAKE_BIN"
for tool in bash sh git date mkdir printf cat stat rm mv head cut tr wc dirname basename realpath stty; do
  real="$(command -v "$tool" 2>/dev/null || true)"
  [ -n "$real" ] && ln -sf "$real" "$FAKE_BIN/$tool"
done
output="$(cd "$SANDBOX" && CLAUDE_PROJECT_DIR="$SANDBOX" PATH="$FAKE_BIN" \
  "$FAKE_BIN/bash" "$SANDBOX/.claude/hooks/session-start.sh" <<< '{}' 2>&1)"
rc=$?
assert_eq 0 "$rc" "exit 0 when jq missing" || fail=$((fail + 1))
assert_contains "$output" "jq not installed" "jq missing warning logged" || fail=$((fail + 1))

# 3. continuation-plan 존재 → stdout 출력 확인
printf '# Resume work\n\n- T1: 테스트\n' > "$SANDBOX/.claude/state/continuation-plan.md"
output="$(cd "$SANDBOX" && CLAUDE_PROJECT_DIR="$SANDBOX" \
  bash "$SANDBOX/.claude/hooks/session-start.sh" <<< '{}' 2>&1)"
rc=$?
assert_eq 0 "$rc" "exit 0 with continuation-plan" || fail=$((fail + 1))
assert_contains "$output" "Resume work" "continuation-plan content on stdout" || fail=$((fail + 1))

# 4. 네트워크 git 호출 timeout 래핑 (v4.8.0) — 정적 가드
# 네트워크 블랙홀 시뮬은 불가하므로 래퍼 존재 + 네트워크 호출 3곳의 래퍼 사용을 정적 검증.
HOOK_SRC="$(cat "$SANDBOX/.claude/hooks/session-start.sh")"
assert_contains "$HOOK_SRC" "net_git()" "net_git wrapper defined" || fail=$((fail + 1))
assert_contains "$HOOK_SRC" "timeout 8 git" "wrapper uses timeout 8" || fail=$((fail + 1))
# 래핑 호출 3곳(fetch×2, pull×1) + 라인 선두의 비래핑 네트워크 호출 0 (로그 문자열 내
# "git pull 실패" 류는 호출이 아니므로 라인 선두 패턴으로만 검사)
WRAPPED_NET="$(grep -cE '^\s*net_git (fetch|pull)\b' "$SANDBOX/.claude/hooks/session-start.sh")"
NAKED_NET="$(grep -cE '^\s*git (fetch|pull)\b' "$SANDBOX/.claude/hooks/session-start.sh")"
assert_eq 3 "$WRAPPED_NET" "3 network git calls wrapped via net_git" || fail=$((fail + 1))
assert_eq 0 "$NAKED_NET" "no naked network git invocations" || fail=$((fail + 1))

if [ "$fail" -gt 0 ]; then
  printf '\n💥 %d assertion(s) failed\n' "$fail" >&2
  exit 1
fi
echo "✓ PASS"
