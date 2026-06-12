#!/usr/bin/env bash
# diagnose.sh — v2.1.3: read-only hook 진단 도구
#
# 목적:
#   네이티브 훅(SessionStart/PostToolUse/Stop)의 현재 상태와 자동 비활성화 영향을
#   한 번에 점검. 모든 파일은 read-only — backlog.json, flag, counter, plan 어느 것도
#   mutate하지 않는다.
#
# 사용:
#   bash .claude/hooks/diagnose.sh
#
# 출력 구조:
#   [등록 상태]   settings.json hook 등록 + 스크립트 존재 여부
#   [PostToolUse] flag/counter 상태 + 추정 원인
#   [Stop]        continuation-plan + 만료 임박 lock 후보
#   [영향 평가]   PostToolUse 비활성 시 진행 중 작업이 받는 영향
#   [행동 옵션]   복구/임계값 조정/방치 중 선택 가이드
#
# 규약:
#   - 모든 실패 경로 exit 0 (graceful skip). 사용법 오류만 exit 1.
#   - 외부 도구 미설치(jq/git)는 가용 항목만 출력.

set -u

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
cd "$PROJECT_DIR" 2>/dev/null || { echo "❌ cannot enter directory: $PROJECT_DIR" >&2; exit 1; }

STATE_DIR=".claude/state"
HOOKS_DIR=".claude/hooks"
SETTINGS=".claude/settings.json"
BACKLOG="$STATE_DIR/backlog.json"
FLAG="$STATE_DIR/hook-disabled.flag"
COUNTER="$STATE_DIR/hook-trigger-count"
ERROR_LOG="$STATE_DIR/hook-errors.log"
CONT_PLAN="$STATE_DIR/continuation-plan.md"

have_jq=0; command -v jq >/dev/null 2>&1 && have_jq=1

# Effective threshold/window — post-tool-use.sh와 동일한 fallback 규칙.
# "추정 원인" 메시지에 반영해서 env override 의도와 일관된 출력 보장 (M001).
EFFECTIVE_THRESHOLD="${CCK_HOOK_THRESHOLD:-3}"
EFFECTIVE_WINDOW="${CCK_HOOK_WINDOW_SEC:-10}"
case "$EFFECTIVE_THRESHOLD" in ''|*[!0-9]*) EFFECTIVE_THRESHOLD=3 ;; esac
case "$EFFECTIVE_WINDOW"    in ''|*[!0-9]*) EFFECTIVE_WINDOW=10 ;; esac
[ "$EFFECTIVE_THRESHOLD" -lt 1 ] 2>/dev/null && EFFECTIVE_THRESHOLD=3
[ "$EFFECTIVE_WINDOW"    -lt 1 ] 2>/dev/null && EFFECTIVE_WINDOW=10

# Unix epoch → ISO8601 (UTC). date -u 호환(GNU/BSD).
to_iso() {
  local ep="$1"
  if date -u -d "@$ep" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null; then return; fi
  if date -u -r "$ep" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null; then return; fi
  printf '(epoch=%s)' "$ep"
}

age_human() {
  local then_ep="$1" now_ep
  now_ep="$(date -u +%s)"
  local diff=$((now_ep - then_ep))
  [ "$diff" -lt 0 ] && diff=0
  if [ "$diff" -lt 60 ]; then printf '%ds ago' "$diff"
  elif [ "$diff" -lt 3600 ]; then printf '%dm ago' $((diff / 60))
  elif [ "$diff" -lt 86400 ]; then printf '%dh ago' $((diff / 3600))
  else printf '%dd ago' $((diff / 86400))
  fi
}

stat_mtime() {
  stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null || echo 0
}

printf '== ai-crew-kit hook diagnosis (%s) ==\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
printf 'project: %s\n\n' "$PROJECT_DIR"

# ── [등록 상태] ───────────────────────────────────────────────
printf '[Registration]\n'
if [ -f "$SETTINGS" ]; then
  if [ "$have_jq" -eq 1 ]; then
    for hook in SessionStart PostToolUse Stop; do
      cnt="$(jq -r --arg h "$hook" '.hooks[$h] // [] | length' "$SETTINGS" 2>/dev/null || echo 0)"
      printf '  %-13s registered=%s\n' "$hook" "$cnt"
    done
  else
    printf '  (jq not installed — settings.json parsing skipped)\n'
  fi
else
  printf '  ⚠️  %s missing — hooks not configured\n' "$SETTINGS"
fi
for script in session-start.sh post-tool-use.sh stop.sh; do
  if [ -x "$HOOKS_DIR/$script" ]; then
    printf '  ✓ %s/%s\n' "$HOOKS_DIR" "$script"
  elif [ -f "$HOOKS_DIR/$script" ]; then
    printf '  ⚠️  %s/%s (not executable)\n' "$HOOKS_DIR" "$script"
  else
    printf '  ✗ %s/%s missing\n' "$HOOKS_DIR" "$script"
  fi
done

# ── [PostToolUse] ────────────────────────────────────────────
printf '\n[PostToolUse]\n'
if [ -f "$FLAG" ]; then
  flag_mtime="$(stat_mtime "$FLAG")"
  printf '  status: 🔴 DISABLED since %s (%s)\n' "$(to_iso "$flag_mtime")" "$(age_human "$flag_mtime")"
else
  printf '  status: 🟢 ENABLED\n'
fi
if [ -f "$COUNTER" ]; then
  read -r win_start cnt < "$COUNTER" 2>/dev/null || { win_start=0; cnt=0; }
  # 비숫자/공백 sanitize — counter 파일 오염 방지 (M005 방어적 일관성)
  case "${win_start:-}" in ''|*[!0-9]*) win_start=0 ;; esac
  case "${cnt:-}"       in ''|*[!0-9]*) cnt=0 ;; esac
  printf '  trigger-count: window_start=%s count=%s\n' "$(to_iso "$win_start")" "$cnt"
  if [ "$cnt" -gt "$EFFECTIVE_THRESHOLD" ] 2>/dev/null; then
    printf '  likely cause: %s Edit/Write calls per response (window %ss, threshold %s exceeded)\n' \
      "$cnt" "$EFFECTIVE_WINDOW" "$EFFECTIVE_THRESHOLD"
  fi
else
  printf '  trigger-count: (no file — no recent trigger evidence)\n'
fi
if [ -f "$ERROR_LOG" ]; then
  last_disable="$(grep -e 'auto-disable triggered' -e '자동 비활성화 발동' "$ERROR_LOG" 2>/dev/null | tail -1)"
  [ -n "$last_disable" ] && printf '  last disable log: %s\n' "$last_disable"
fi
# 환경변수 override 가시화
if [ -n "${CCK_HOOK_THRESHOLD:-}" ] || [ -n "${CCK_HOOK_WINDOW_SEC:-}" ]; then
  printf '  env override: CCK_HOOK_THRESHOLD=%s CCK_HOOK_WINDOW_SEC=%s\n' \
    "${CCK_HOOK_THRESHOLD:-(unset)}" "${CCK_HOOK_WINDOW_SEC:-(unset)}"
fi

# ── [Stop] ───────────────────────────────────────────────────
printf '\n[Stop]\n'
if [ -f "$CONT_PLAN" ]; then
  cp_mtime="$(stat_mtime "$CONT_PLAN")"
  printf '  continuation-plan.md: present (updated %s)\n' "$(age_human "$cp_mtime")"
else
  printf '  continuation-plan.md: absent (may be normal — idle/zero-task skip policy)\n'
fi
# 만료 임박/만료된 lock 후보 — stop.sh와 동일 만료 의미론(v4.5.0):
# (lockedAt // assignedAt) + (lockTTL // 3600) < now. 구 600s 고정은 v4.5.0 이전 잔재였음.
# v4.8.0 (M002 해소): 파싱 불가 타임스탬프는 만료 아님 — 별도 카운트로 가시화.
expired_count=0; near_count=0; badts_count=0
if [ "$have_jq" -eq 1 ] && [ -f "$BACKLOG" ]; then
  now_ep="$(date -u +%s)"
  expired_count="$(jq --argjson now "$now_ep" '
    [.tasks[]? | select(
      .status == "in_progress" and
      ((((.lockedAt // .assignedAt // "") | fromdateiso8601?) // null) != null) and
      (((((.lockedAt // .assignedAt) | fromdateiso8601?) // 0) + (.lockTTL // 3600)) < $now)
    )] | length' "$BACKLOG" 2>/dev/null || echo 0)"
  near_count="$(jq --argjson now "$now_ep" '
    [.tasks[]? | select(
      .status == "in_progress" and
      ((((.lockedAt // .assignedAt // "") | fromdateiso8601?) // null) != null) and
      (((((.lockedAt // .assignedAt) | fromdateiso8601?) // 0) + (.lockTTL // 3600)) >= $now) and
      (((((.lockedAt // .assignedAt) | fromdateiso8601?) // 0) + (.lockTTL // 3600)) < ($now + 120))
    )] | length' "$BACKLOG" 2>/dev/null || echo 0)"
  badts_count="$(jq '
    [.tasks[]? | select(
      .status == "in_progress" and
      ((.lockedAt != null) or (.assignedAt != null)) and
      ((((.lockedAt // .assignedAt) | fromdateiso8601?) // null) == null)
    )] | length' "$BACKLOG" 2>/dev/null || echo 0)"
  printf '  expired locks (released on next stop turn): %s\n' "$expired_count"
  printf '  locks expiring soon (within 2m): %s\n' "$near_count"
  if [ "$badts_count" != "0" ]; then
    printf '  🟡 locks with unparseable timestamps (never auto-expire): %s — fix via /aick-validate --fix\n' "$badts_count"
  fi
fi

# ── [영향 평가] ──────────────────────────────────────────────
printf '\n[Impact]\n'
in_progress_total=0; with_lock=0
if [ "$have_jq" -eq 1 ] && [ -f "$BACKLOG" ]; then
  in_progress_total="$(jq -r '[.tasks[]? | select(.status == "in_progress")] | length' "$BACKLOG" 2>/dev/null || echo 0)"
  with_lock="$(jq -r '[.tasks[]? | select(.status == "in_progress" and (.lockedBy // "") != "")] | length' "$BACKLOG" 2>/dev/null || echo 0)"
fi
printf '  in_progress tasks: %s (with lockedBy: %s)\n' "$in_progress_total" "$with_lock"

if [ -f "$FLAG" ]; then
  if [ "$with_lock" = "0" ]; then
    printf '  🟢 verdict: PostToolUse disable has no impact (0 owned locks). Recovery optional.\n'
  else
    printf '  🟡 verdict: lock-holding work is auto-released once its lockTTL expires (stop policy).\n'
    printf '         Short tasks are safe; recover if working long.\n'
  fi
else
  printf '  🟢 verdict: PostToolUse healthy — heartbeat refreshes on every Edit/Write.\n'
fi

# ── [행동 옵션] ──────────────────────────────────────────────
printf '\n[Options]\n'
if [ -f "$FLAG" ]; then
  printf '  [A] continue as-is — safe for solo/short work\n'
  printf '  [B] recover     — rm %s %s\n' "$FLAG" "$COUNTER"
  printf '  [C] relax threshold — export CCK_HOOK_THRESHOLD=8 (frequent multi-edit responses)\n'
  printf '                  persist: settings.json env or shell rc\n'
else
  printf '  healthy — no action needed\n'
  printf '  If auto-disable fires often due to multi-file edits:\n'
  printf '    export CCK_HOOK_THRESHOLD=8  # raise per-response Edit allowance\n'
fi

# ── [참고] Stop 동작을 실제로 확인하려면 ─────────────────────
printf '\n[Note] To actively exercise the Stop hook (may mutate — use with care):\n'
printf '  echo \"{\\\"stop_hook_active\\\": false}\" | bash %s/stop.sh\n' "$HOOKS_DIR"

exit 0
