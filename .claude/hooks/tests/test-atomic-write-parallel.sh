#!/usr/bin/env bash
# test-atomic-write-parallel.sh — TFT §4 #6: 워크트리 동시 Write (flock 직렬화)

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./_lib.sh
source "$SCRIPT_DIR/_lib.sh"

print_header "atomic_write 병렬 5회 동시 실행 → 파일 손상 없음"

SANDBOX="$(mk_sandbox)"
trap 'rm -rf "$SANDBOX"' EXIT

fail=0
TARGET="$SANDBOX/.claude/state/counter.json"
echo '{"counter":0}' > "$TARGET"

# shellcheck source=../lib/atomic-write.sh
source "$SANDBOX/.claude/hooks/lib/atomic-write.sh"

# 병렬 10회 increment
for i in $(seq 1 10); do
  (
    atomic_write "$TARGET" jq --argjson n "$i" '.counter = (.counter // 0) + 1' "$TARGET"
  ) &
done
wait

# 파일이 여전히 유효한 JSON인지 확인
if ! python3 -c "import json,sys; json.load(open('$TARGET'))" 2>/dev/null; then
  echo "  ✗ target is corrupted JSON" >&2
  fail=$((fail + 1))
else
  echo "  ✓ target JSON valid after 10 parallel writes"
fi

# counter가 최소 1, 최대 10 (병렬 직렬화로 1~10 사이 값 중 하나)
final="$(jq -r '.counter' "$TARGET" 2>/dev/null || echo 0)"
if [ "$final" -ge 1 ] && [ "$final" -le 10 ]; then
  echo "  ✓ counter in valid range (got $final)"
else
  echo "  ✗ counter out of range: $final" >&2
  fail=$((fail + 1))
fi

# 임시 파일(.tmp.*)이 남아있지 않아야 함
leftover="$(find "$SANDBOX/.claude/state" -name '*.tmp.*' 2>/dev/null | wc -l)"
assert_eq 0 "$leftover" "no *.tmp.* leftover files" || fail=$((fail + 1))

# ── 스테일 mkdir 뮤텍스 회수 (v4.8.0) ──────────────────────────
# 크래시 잔재(약 2분 초과 mutex 디렉토리 — -mmin +1 절사 의미론)가 있어도 쓰기가 성공하고 mutex가 정리돼야 함.
# ACK_MUTEX_IMPL=mkdir 시임으로 flock 환경에서도 mkdir 경로 강제.
TARGET2="$SANDBOX/.claude/state/stale-test.json"
echo '{"v":0}' > "$TARGET2"
mkdir "$TARGET2.mutex.d"
# mtime을 2분 전으로 — 스테일 판정(-mmin +1 = age≥2분) 경계 충족
touch -d '2 minutes ago' "$TARGET2.mutex.d" 2>/dev/null || touch -t "$(date -d '2 minutes ago' +%Y%m%d%H%M.%S 2>/dev/null || echo 197001010000)" "$TARGET2.mutex.d"
(
  cd "$SANDBOX"
  export ACK_HOOK_ERROR_LOG="$SANDBOX/.claude/state/hook-errors.log"
  export ACK_MUTEX_IMPL=mkdir
  source "$SANDBOX/.claude/hooks/lib/atomic-write.sh"
  atomic_write "$TARGET2" jq '.v = 1' "$TARGET2"
)
stale_v="$(jq -r '.v' "$TARGET2" 2>/dev/null || echo 0)"
assert_eq 1 "$stale_v" "stale mutex reclaimed — write succeeded" || fail=$((fail + 1))
if [ -d "$TARGET2.mutex.d" ]; then
  echo "  ✗ stale mutex dir not cleaned" >&2; fail=$((fail + 1))
else
  echo "  ✓ stale mutex dir cleaned after write"
fi
assert_contains "$(cat "$SANDBOX/.claude/state/hook-errors.log" 2>/dev/null)" "stale mkdir mutex reclaimed" "reclaim logged" || fail=$((fail + 1))

# 신선한(스테일 아닌) mutex는 회수하지 않고 timeout으로 보호돼야 함 — 빠른 검증:
# 방금 만든 mutex(age<2분)에서 atomic_write가 파일을 변경하지 못하고 timeout 로그를 남김
TARGET3="$SANDBOX/.claude/state/fresh-test.json"
echo '{"v":0}' > "$TARGET3"
mkdir "$TARGET3.mutex.d"
(
  cd "$SANDBOX"
  export ACK_HOOK_ERROR_LOG="$SANDBOX/.claude/state/hook-errors.log"
  export ACK_MUTEX_IMPL=mkdir
  source "$SANDBOX/.claude/hooks/lib/atomic-write.sh"
  atomic_write "$TARGET3" jq '.v = 1' "$TARGET3"
)
fresh_v="$(jq -r '.v' "$TARGET3" 2>/dev/null || echo -1)"
assert_eq 0 "$fresh_v" "fresh mutex NOT reclaimed (write blocked as designed)" || fail=$((fail + 1))
rmdir "$TARGET3.mutex.d" 2>/dev/null || true

if [ "$fail" -gt 0 ]; then
  printf '\n💥 %d assertion(s) failed\n' "$fail" >&2
  exit 1
fi
echo "✓ PASS"
