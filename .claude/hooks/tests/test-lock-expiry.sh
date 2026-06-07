#!/usr/bin/env bash
# test-lock-expiry.sh — stop.sh 만료 잠금 해제 (v4.5.0: (lockedAt // assignedAt) + lockTTL < now)

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./_lib.sh
source "$SCRIPT_DIR/_lib.sh"

print_header "stop.sh 만료 잠금 해제 시나리오 (lockTTL 윈도우 + assignedAt 폴백)"

SANDBOX="$(mk_sandbox)"
trap 'rm -rf "$SANDBOX"' EXIT
BACKLOG="$SANDBOX/.claude/state/backlog.json"

fail=0

# 시간 픽스처: lockTTL=3600 기준. 만료=2시간 전(7200s>3600), 미만료=1분 전(60s<3600)
now_epoch="$(date -u +%s)"
expired_iso="$(date -u -d "@$((now_epoch - 7200))" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date -u -r "$((now_epoch - 7200))" '+%Y-%m-%dT%H:%M:%SZ')"
fresh_iso="$(date -u -d "@$((now_epoch - 60))" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date -u -r "$((now_epoch - 60))" '+%Y-%m-%dT%H:%M:%SZ')"

# T1 만료(lockedAt) / T2 미만료(lockedAt) / T3 비-ISO8601
# T4 lockedAt=null·assignedAt 만료 → 폴백 만료 / T5 lockedAt=null·assignedAt 미만료 → 폴백 유지
cat > "$BACKLOG" <<EOF
{
  "workflowState": "active",
  "tasks": {
    "T1": {"id": "T1", "status": "in_progress", "lockedAt": "$expired_iso", "lockedBy": "alice@host", "lockTTL": 3600},
    "T2": {"id": "T2", "status": "in_progress", "lockedAt": "$fresh_iso", "lockedBy": "bob@host", "lockTTL": 3600},
    "T3": {"id": "T3", "status": "in_progress", "lockedAt": "garbage-not-iso", "lockedBy": "carol@host", "lockTTL": 3600},
    "T4": {"id": "T4", "status": "in_progress", "lockedAt": null, "assignedAt": "$expired_iso", "lockedBy": "dave@host", "lockTTL": 3600},
    "T5": {"id": "T5", "status": "in_progress", "lockedAt": null, "assignedAt": "$fresh_iso", "lockedBy": "erin@host", "lockTTL": 3600}
  }
}
EOF

# stop.sh 실행 (stop_hook_active=false → 정상 진행)
(cd "$SANDBOX" && CLAUDE_PROJECT_DIR="$SANDBOX" \
  bash "$SANDBOX/.claude/hooks/stop.sh" <<< '{"stop_hook_active":false}' >/dev/null 2>&1)

t1="$(jq -r '.tasks["T1"].lockedAt' "$BACKLOG")"; t1b="$(jq -r '.tasks["T1"].lockedBy' "$BACKLOG")"
t2="$(jq -r '.tasks["T2"].lockedAt' "$BACKLOG")"
t3="$(jq -r '.tasks["T3"].lockedAt' "$BACKLOG")"
t4b="$(jq -r '.tasks["T4"].lockedBy' "$BACKLOG")"
t5b="$(jq -r '.tasks["T5"].lockedBy' "$BACKLOG")"

assert_eq "null" "$t1" "T1 (lockedAt+lockTTL 만료) lockedAt 해제됨" || fail=$((fail + 1))
assert_eq "null" "$t1b" "T1 lockedBy도 해제됨" || fail=$((fail + 1))
assert_eq "$fresh_iso" "$t2" "T2 (fresh) 잠금 유지됨" || fail=$((fail + 1))
# T3 (비-ISO8601): fromdateiso8601 실패 → 0 폴백 → 즉시 만료 (현 동작, M002 트래킹)
assert_eq "null" "$t3" "T3 (invalid ISO8601) — 현재 동작: 해제됨 (M002)" || fail=$((fail + 1))
assert_eq "null" "$t4b" "T4 (lockedAt=null, assignedAt 만료 → 폴백 만료) lockedBy 해제됨" || fail=$((fail + 1))
assert_eq "erin@host" "$t5b" "T5 (lockedAt=null, assignedAt fresh → 폴백 유지) lockedBy 유지됨" || fail=$((fail + 1))

# 상태는 비파괴: stop.sh는 status를 건드리지 않는다 (전체 회수는 스킬 reclaim 담당)
assert_eq "in_progress" "$(jq -r '.tasks["T1"].status' "$BACKLOG")" "T1 status는 in_progress 유지 (비파괴)" || fail=$((fail + 1))

if [ "$fail" -gt 0 ]; then
  printf '\n💥 %d assertion(s) failed\n' "$fail" >&2
  exit 1
fi
echo "✓ PASS"
