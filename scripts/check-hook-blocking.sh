#!/usr/bin/env bash
# check-hook-blocking.sh — HI-04 자가 검사 (Phase 1 Step 2, Step 5 선행)
#
# 훅 스크립트 비블로킹 규칙 위반 정적 검사:
#   - `exit 2` 금지 (Claude Code "블록" 시그널)
#   - `set -e` 단독 금지 (의도치 않은 세션 차단 유발)
#
# 주석 라인(#)은 제외. `|| true` 동반 `set -e`는 향후 허용 예정.
#
# 사용:
#   bash scripts/check-hook-blocking.sh               # 기본: .claude/hooks/
#   bash scripts/check-hook-blocking.sh path1 path2   # 커스텀 경로
#
# 종료 코드: 위반 발견 시 1, 정상 0.

set -u

TARGETS=("$@")
if [ "${#TARGETS[@]}" -eq 0 ]; then
  TARGETS=(".claude/hooks")
fi

violations=0
files_scanned=0

for target in "${TARGETS[@]}"; do
  if [ ! -e "$target" ]; then
    echo "⚠️  대상 없음: $target (스킵)" >&2
    continue
  fi
  while IFS= read -r -d '' file; do
    # 테스트 fixture는 검사 대상 아님 (heredoc 위반 fixture 생성 포함)
    case "$file" in */tests/*) continue ;; esac
    files_scanned=$((files_scanned + 1))

    # exit 2 검출 (주석 제외)
    if grep -nE '^[[:space:]]*[^#[:space:]][^#]*\bexit[[:space:]]+2\b' "$file" > /dev/null 2>&1; then
      echo "❌ HI-04 위반 — exit 2 검출:" >&2
      grep -nE '^[[:space:]]*[^#[:space:]][^#]*\bexit[[:space:]]+2\b' "$file" | sed "s|^|   $file:|" >&2
      violations=$((violations + 1))
    fi

    # set -e 단독 검출 (set -eu 등 조합 포함, 주석/문자열은 완벽하지 않으나 실용 수준)
    if grep -nE '^[[:space:]]*set[[:space:]]+[^#]*-[a-zA-Z]*e([^a-zA-Z]|$)' "$file" | grep -v '|| true' > /dev/null 2>&1; then
      echo "❌ HI-04 위반 — set -e 검출 (|| true 동반 없음):" >&2
      grep -nE '^[[:space:]]*set[[:space:]]+[^#]*-[a-zA-Z]*e([^a-zA-Z]|$)' "$file" | grep -v '|| true' | sed "s|^|   $file:|" >&2
      violations=$((violations + 1))
    fi
  done < <(find "$target" -type f -name '*.sh' -print0 2>/dev/null)
done

if [ "$violations" -gt 0 ]; then
  echo "" >&2
  echo "💥 HI-04 위반 $violations건 (스캔 $files_scanned파일)" >&2
  exit 1
fi

echo "✓ HI-04 통과 — 스캔 $files_scanned파일, 위반 0건"
exit 0
