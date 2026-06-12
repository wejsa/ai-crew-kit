#!/usr/bin/env bash
# test-session-start-contract-warnings.sh — SessionStart 머지 게이트 데이터 계약 경고 (v4.8.0)
#
# 검증: session-start.sh §3.5가 in_progress Task의 게이트 무력화 데이터 결함을 가시화하는지.
#   C1: prNumber/fixLoopCount 문자열 (v2.4.1 실사고 sleeper — 게이트 숫자 join 불능)
#   C2: review-pr 완료 + lastReviewDecision null (게이트 신호 A null 읽기 = fail-open)
#   C3: step pr_created + prNumber null (신호 A join 원천 부재)
# 정상 데이터에선 경고 섹션 자체가 출력되지 않아야 하고(오탐 0), 훅은 항상 exit 0(R4).
# 비-git sandbox라 git sync는 자연 스킵 — backlog 섹션만 검증 대상.

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./_lib.sh
. "$SCRIPT_DIR/_lib.sh"

HOOK="$HOOK_DIR/session-start.sh"
fails=0

SANDBOXES=()
cleanup_all() { for d in "${SANDBOXES[@]:-}"; do [ -n "$d" ] && rm -rf "$d"; done; }
trap cleanup_all EXIT
new_sandbox() { local d; d="$(mk_sandbox)"; SANDBOXES+=("$d"); printf '%s' "$d"; }

# 훅 실행 → stdout 반환. exit code는 호출부에서 $?로 수신
# (command substitution의 종료 코드 = 치환된 명령의 종료 코드)
run_hook_out() {
  local dir="$1"
  CLAUDE_PROJECT_DIR="$dir" bash "$HOOK" 2>/dev/null
}

write_backlog_raw() {
  local dir="$1" tasks_json="$2"
  cat > "$dir/.claude/state/backlog.json" <<EOF
{
  "metadata": { "lastTaskNumber": 1, "version": 1, "createdAt": "2026-06-12T00:00:00Z", "updatedAt": "2026-06-12T00:00:00Z" },
  "tasks": $tasks_json
}
EOF
}

S=$(new_sandbox)

# ── 1. C1: 문자열 prNumber → 경고 ──────────────────────────
print_header "1. C1: workflowState.prNumber / step.prNumber 문자열 → 경고"
write_backlog_raw "$S" '{
  "TASK-001": {
    "id": "TASK-001", "title": "t", "status": "in_progress", "priority": "high", "createdAt": "2026-06-12T00:00:00Z",
    "steps": [ { "number": 1, "title": "s", "status": "pr_created", "prNumber": "42" } ],
    "workflowState": { "currentSkill": "aick-review-pr", "prNumber": "42", "lastReviewDecision": "REQUEST_CHANGES", "updatedAt": "2026-06-12T00:00:00Z" }
  }
}'
out="$(run_hook_out "$S")"; rc=$?
assert_eq "0" "$rc" "exit 0 (R4)" || fails=$((fails+1))
assert_contains "$out" "Merge-gate data contract warnings" "경고 헤더 출력" || fails=$((fails+1))
assert_contains "$out" "workflowState.prNumber is a string" "C1 workflowState 경고" || fails=$((fails+1))
assert_contains "$out" "step.prNumber is a string" "C1 step 경고" || fails=$((fails+1))

# ── 2. C2: review 완료 + lastReviewDecision null → 경고 ────
print_header "2. C2: lastCompletedSkill=*review-pr + lastReviewDecision null → 경고"
write_backlog_raw "$S" '{
  "TASK-001": {
    "id": "TASK-001", "title": "t", "status": "in_progress", "priority": "high", "createdAt": "2026-06-12T00:00:00Z",
    "steps": [ { "number": 1, "title": "s", "status": "pr_created", "prNumber": 42 } ],
    "workflowState": { "currentSkill": "aick-merge-pr", "lastCompletedSkill": "aick-review-pr", "prNumber": 42, "lastReviewDecision": null, "updatedAt": "2026-06-12T00:00:00Z" }
  }
}'
out="$(run_hook_out "$S")"
assert_contains "$out" "lastReviewDecision not recorded" "C2 경고" || fails=$((fails+1))
assert_contains "$out" "PR #42" "C2 경고에 PR 번호 포함" || fails=$((fails+1))

# 구 프리픽스(crew-review-pr)도 suffix 매치로 잡혀야 함
write_backlog_raw "$S" '{
  "TASK-001": {
    "id": "TASK-001", "title": "t", "status": "in_progress", "priority": "high", "createdAt": "2026-06-12T00:00:00Z",
    "workflowState": { "currentSkill": "crew-merge-pr", "lastCompletedSkill": "crew-review-pr", "prNumber": 7, "lastReviewDecision": null, "updatedAt": "2026-06-12T00:00:00Z" }
  }
}'
out="$(run_hook_out "$S")"
assert_contains "$out" "lastReviewDecision not recorded" "C2 레거시 프리픽스(crew-)도 감지" || fails=$((fails+1))

# ── 3. C3: pr_created + prNumber null → 경고 ───────────────
print_header "3. C3: step pr_created + prNumber null → 경고"
write_backlog_raw "$S" '{
  "TASK-001": {
    "id": "TASK-001", "title": "t", "status": "in_progress", "priority": "high", "createdAt": "2026-06-12T00:00:00Z",
    "steps": [ { "number": 2, "title": "s", "status": "pr_created", "prNumber": null } ],
    "workflowState": { "currentSkill": "aick-impl", "updatedAt": "2026-06-12T00:00:00Z" }
  }
}'
out="$(run_hook_out "$S")"
assert_contains "$out" "pr_created without prNumber" "C3 경고" || fails=$((fails+1))

# ── 4. 정상 데이터 → 경고 섹션 무출력 (오탐 0) ──────────────
print_header "4. 정상 fixture → 경고 미출력"
# 게이트 테스트와 동일한 실제 shape (정수 prNumber, 결정 기록됨)
write_backlog_raw "$S" '{
  "TASK-001": {
    "id": "TASK-001", "title": "t", "status": "in_progress", "priority": "high", "createdAt": "2026-06-12T00:00:00Z",
    "steps": [ { "number": 1, "title": "s", "status": "pr_created", "prNumber": 42 } ],
    "workflowState": { "currentSkill": "aick-review-pr", "lastCompletedSkill": "aick-impl", "lastReviewDecision": "REQUEST_CHANGES", "updatedAt": "2026-06-12T00:00:00Z" }
  }
}'
out="$(run_hook_out "$S")"; rc=$?
assert_eq "0" "$rc" "exit 0 (R4)" || fails=$((fails+1))
if [[ "$out" == *"Merge-gate data contract warnings"* ]]; then
  printf '  ✗ 정상 데이터에서 경고 오탐\n' >&2; fails=$((fails+1))
else
  printf '  ✓ 정상 데이터 경고 미출력\n'
fi
# done Task의 결함은 검사 대상 아님 (in_progress 한정)
write_backlog_raw "$S" '{
  "TASK-001": {
    "id": "TASK-001", "title": "t", "status": "done", "priority": "high", "createdAt": "2026-06-12T00:00:00Z",
    "steps": [ { "number": 1, "title": "s", "status": "pr_created", "prNumber": null } ],
    "workflowState": null
  }
}'
out="$(run_hook_out "$S")"
if [[ "$out" == *"Merge-gate data contract warnings"* ]]; then
  printf '  ✗ done Task가 경고를 유발 (in_progress 한정 위반)\n' >&2; fails=$((fails+1))
else
  printf '  ✓ done Task 미검사' && printf '\n'
fi

# ── 5. 견고성: backlog 부재/깨진 JSON → 무출력 + exit 0 ─────
print_header "5. backlog 부재·malformed → 경고 없음 + exit 0"
S5=$(new_sandbox)
out="$(run_hook_out "$S5")"; rc=$?
assert_eq "0" "$rc" "backlog 부재 exit 0" || fails=$((fails+1))
printf 'not json{{{' > "$S5/.claude/state/backlog.json"
out="$(run_hook_out "$S5")"; rc=$?
assert_eq "0" "$rc" "malformed JSON exit 0" || fails=$((fails+1))
if [[ "$out" == *"Merge-gate data contract warnings"* ]]; then
  printf '  ✗ malformed JSON에서 경고 출력\n' >&2; fails=$((fails+1))
else
  printf '  ✓ malformed JSON 경고 미출력 (fail-silent)\n'
fi

printf '\n'
if [ "$fails" -eq 0 ]; then
  printf '✅ test-session-start-contract-warnings: 전체 통과\n'; exit 0
else
  printf '❌ test-session-start-contract-warnings: %d개 실패\n' "$fails"; exit 1
fi
