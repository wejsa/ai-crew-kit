#!/usr/bin/env bash
# hi04-exempt: gate-hook  (설계상 블로킹 — exit 2로 머지 차단. HI-04 exit-2 검사 면제)
# pre-tool-use.sh — PreToolUse 훅 (Bash 매처): 머지 품질 게이트 (v2.4.0)
#
# 목적:
#   `gh pr merge` 실행 직전, 해당 PR에 미해결 CRITICAL이 있으면 결정적으로 차단한다.
#   기존엔 "CRITICAL은 머지 차단"이 prose 지시(aick-merge-pr/CLAUDE.md)였으나 LLM이
#   519줄 분기를 한 번만 잘못 따라도 나쁜 PR이 auto-merge되는 구멍이 있었다(W2).
#   여기서 hook이 직접 deny한다 — 프레임워크의 핵심 게이트를 결정적 레이어로 이동.
#
# 게이트 신호 (하나라도 차단 판정이면 deny):
#   A. (state) PR N을 소유한 Task(= step.prNumber==N 또는 workflowState.prNumber==N)의
#      workflowState.lastReviewDecision == "REQUEST_CHANGES"  → 미해결 CRITICAL 게시됨.
#      PR 번호의 결정적 SSOT는 step.prNumber(aick-impl Step 8)이므로 거기서도 join해야
#      프로덕션에서 발동한다(workflowState.prNumber만 보면 no-op — 자체 리뷰 finding #1).
#   A2. (transient state, v4.8.0) backlog Task가 없는 PR(핫픽스·ad-hoc 리뷰)의 결정 —
#      .claude/state/review-decisions.json (aick-hotfix Step 7 / aick-review-pr Step 6.5
#      소유 Task 부재 시 기록, 로컬 전용·gitignore). 오프라인 결정적, 파싱 실패 fail-open.
#   B. (GitHub, best-effort) gh pr view reviewDecision == "CHANGES_REQUESTED"
#      — 타인 PR에서 GitHub가 기록한 request-changes. 네트워크/인증 실패 시 fail-open.
#
# ⚠️ Hook 카테고리 구분 (hooks/README.md SSOT):
#   - Bookkeeping 훅(session-start/post-tool-use/stop): R4 = 절대 비블로킹(exit 0).
#   - Gate 훅(본 스크립트): 설계상 블로킹(exit 2)이 정당하다. 단,
#       * 인프라 실패(jq/git/gh 부재, 파싱 불가, backlog 부재, 네트워크)는 fail-open(allow).
#         게이트 자체 장애가 정상 머지를 막아선 안 된다.
#       * 명시 우회: CCK_GATE_BYPASS=1 (의도적 1회 머지) / CCK_MERGE_GATE=off (게이트 비활성).
#
# 차단 메커니즘: exit 2 + stderr 사유 (PreToolUse가 도구 호출을 막고 사유를 Claude에 전달).

# shellcheck disable=SC2015

HOOK_NAME="pre-tool-use"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
cd "$PROJECT_DIR" 2>/dev/null || exit 0

# 비대화형 git/gh 강제 (다른 훅과 일관 — credential 프롬프트로 인한 hang 방지)
export GIT_TERMINAL_PROMPT=0
export GIT_ASKPASS=/bin/true
export GCM_INTERACTIVE=never

STATE_DIR=".claude/state"
ERROR_LOG="$STATE_DIR/hook-errors.log"
BACKLOG="$STATE_DIR/backlog.json"

log_err() {
  printf '[%s] [%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$HOOK_NAME" "$1" >> "$ERROR_LOG" 2>/dev/null || true
}

# ── 게이트 전역 비활성 ────────────────────────────────
# off/false/0/no 모두 허용 (사용자 오타 관용)
case "${CCK_MERGE_GATE:-on}" in
  off|OFF|false|FALSE|0|no|NO) exit 0 ;;
esac

# ── stdin JSON 수신 (timeout 1초로 hang 방지) ─────────
INPUT=""
if [ ! -t 0 ]; then
  INPUT="$(timeout 1 cat 2>/dev/null || true)"
fi
exec 0</dev/null
[ -z "$INPUT" ] && exit 0   # 입력 없음 — 판단 불가, allow

# jq 없으면 게이트 판정 불가 → fail-open
if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

CMD="$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || echo '')"
[ -z "$CMD" ] && exit 0

# ── 대상 명령 필터: `gh pr merge` 만 관심 ─────────────
# 공백 정규화 후 부분 매치. 그 외 모든 Bash 명령은 즉시 allow (의견 없음).
CMD_NORM="$(printf '%s' "$CMD" | tr '\n\t' '  ' | sed -e 's/  */ /g')"
case "$CMD_NORM" in
  *"gh pr merge "*|*"gh pr merge") : ;;   # 매치 — 게이트 진입
  *) exit 0 ;;                            # 비대상 — allow
esac

# ── 의도적 우회 ───────────────────────────────────────
case "${CCK_GATE_BYPASS:-0}" in
  1|true|TRUE|yes|YES)
    log_err "merge gate bypassed (CCK_GATE_BYPASS) — cmd: $CMD_NORM"
    printf '🔓 [%s] Merge gate bypassed (CCK_GATE_BYPASS). Proceeding under user responsibility.\n' "$HOOK_NAME" >&2
    exit 0
    ;;
esac

# ── PR 번호 추출 ──────────────────────────────────────
# `gh pr merge` 토큰 직후부터, **순수 숫자 토큰**(또는 URL의 마지막 경로 세그먼트)을
# 첫 번째로 채택. free-form 명령 전체를 정규식으로 긁지 않는다(자체 리뷰 finding #2):
#   - 순수-숫자 토큰만 인정 → `repo123`/`r2`/SHA `abc123` 같은 임베드 숫자 오추출 방지.
#   - URL `.../pull/42`는 마지막 `/` 뒤 세그먼트만 취함.
#   - `gh pr merge` 토큰 첫 출현 직후부터 스캔 → 후행 주석/반복 문구의 greedy 흡수 방지.
# 추출 실패(번호 없는 current-branch 머지 등) 시 fail-open.
PRN="$(printf '%s' "$CMD_NORM" | awk '
  {
    start=0
    for (i=1; i<=NF; i++) if ($i=="gh" && $(i+1)=="pr" && $(i+2)=="merge") { start=i+3; break }
    if (start==0) exit
    for (i=start; i<=NF; i++) { t=$i; sub(/^.*\//,"",t); if (t ~ /^[0-9]+$/) { print t; exit } }
  }')"
if [ -z "$PRN" ]; then
  log_err "PR number extraction failed — fail-open allow. cmd: $CMD_NORM"
  exit 0
fi
# 선행 0 정규화: jq --argjson과 gh는 `042` 같은 비표준 JSON/번호를 거부(jq<1.7)하므로
# base-10으로 강제 정규화(`042`→42). PRN은 위 awk에서 순수 숫자만 통과하므로 안전.
PRN=$((10#$PRN))

BLOCK=0
REASON=""

# ── 신호 A: backlog lastReviewDecision (결정적, 오프라인) ──
# PR N을 "소유"하는 Task를 찾아 그 Task의 마지막 리뷰 결정을 읽는다. PR 번호는
# 두 곳에 기록될 수 있어 둘 다 매칭한다(자체 리뷰 finding #1):
#   - step.prNumber: aick-impl Step 8이 결정적으로 기록(SSOT — schema step.prNumber).
#   - workflowState.prNumber: CLAUDE.md workflowState 프로토콜 템플릿 필드(LLM 갱신, 보조).
# step.prNumber만 보던 초안은 신호 A가 프로덕션에서 발동하지 못했음.
if [ -f "$BACKLOG" ]; then
  DECISION="$(jq -r --argjson n "$PRN" '
    first(
      .tasks[]?
      | select(
          (.workflowState.prNumber // -1) == $n
          or any((.steps // [])[]?; (.prNumber // -1) == $n)
        )
      | .workflowState.lastReviewDecision // empty
    ) // empty
  ' "$BACKLOG" 2>/dev/null || echo '')"
  if [ "$DECISION" = "REQUEST_CHANGES" ]; then
    BLOCK=1
    REASON="backlog: last review decision is REQUEST_CHANGES (unresolved CRITICAL posted)"
  fi
fi

# ── 신호 A2: transient review decision (결정적, 오프라인) ──
# backlog Task가 없는 PR(핫픽스·ad-hoc 리뷰)의 리뷰 결정. aick-hotfix Step 7 /
# aick-review-pr Step 6.5(소유 Task 부재 시)가 기록, 머지 성공 시 삭제.
# 형식 SSOT: .claude/schemas/review-decisions.schema.json (키 = PR 번호 십진 문자열).
# 로컬 전용(gitignore) — 다른 세션/머신에 비전파. 파싱 실패는 fail-open.
DECISIONS="$STATE_DIR/review-decisions.json"
if [ "$BLOCK" -eq 0 ] && [ -f "$DECISIONS" ]; then
  TDECISION="$(jq -r --arg n "$PRN" '.[$n].decision // empty' "$DECISIONS" 2>/dev/null || echo '')"
  if [ "$TDECISION" = "REQUEST_CHANGES" ]; then
    BLOCK=1
    REASON="transient review state: last review decision is REQUEST_CHANGES (hotfix/ad-hoc review)"
  fi
fi

# ── 신호 B: GitHub reviewDecision (best-effort, 네트워크) ──
# 신호 A가 이미 차단이면 생략. gh 부재/네트워크/인증 실패는 fail-open(무시).
# CCK_GATE_NO_GH=1: 네트워크 호출 전면 스킵 (오프라인/에어갭 환경, 또는 테스트 결정성).
NO_GH=0
case "${CCK_GATE_NO_GH:-0}" in 1|true|TRUE|yes|YES) NO_GH=1 ;; esac
if [ "$BLOCK" -eq 0 ] && [ "$NO_GH" -eq 0 ] && command -v gh >/dev/null 2>&1; then
  GH_DECISION="$(timeout 8 gh pr view "$PRN" --json reviewDecision -q '.reviewDecision' 2>/dev/null || echo '')"
  if [ "$GH_DECISION" = "CHANGES_REQUESTED" ]; then
    BLOCK=1
    REASON="GitHub: reviewDecision=CHANGES_REQUESTED"
  fi
fi

# ── 판정 ──────────────────────────────────────────────
# NOTE: 아래 차단 메시지는 README.md(Try-it)·examples/merge-gate-demo/README.md에
# verbatim 인용됨 — 문구 수정 시 두 문서도 함께 갱신할 것 (test:108은 "Merge blocked"만 고정).
if [ "$BLOCK" -eq 1 ]; then
  log_err "merge blocked: PR #$PRN — $REASON"
  {
    printf '🛑 [%s] Merge blocked — PR #%s\n' "$HOOK_NAME" "$PRN"
    printf '   Reason: %s\n' "$REASON"
    printf '   A PR with unresolved CRITICAL findings cannot be merged.\n'
    printf '   Next steps:\n'
    printf '     1) [Recommended] Fix the CRITICAL findings, then re-review: /aick-review-pr %s --auto-fix\n' "$PRN"
    printf '     2) If this is a downgraded or false-positive finding, re-examine the review decision and re-review\n'
    printf '     3) [Deliberate override] Set CCK_GATE_BYPASS=1 and retry (user responsibility)\n'
  } >&2
  exit 2
fi

exit 0
