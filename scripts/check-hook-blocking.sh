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

    # Gate 훅 예외 (v2.4.0): 마커 `# hi04-exempt: gate-hook`를 선언한 파일은
    # 설계상 블로킹(exit 2)이 정당하다(PreToolUse 품질 게이트). exit-2 검사만 면제.
    # set -e 검사는 게이트 훅에도 동일 적용(인프라 실패 시 fail-open 보장 위함).
    # 마커는 **파일 헤더(첫 5줄)에서만** 인정 — 본문 어디서나 매치하면 heredoc/문자열/
    # 경고 주석에 우연히 들어간 문구로 전체 파일이 무단 면제되는 footgun(2차 리뷰 #2).
    if head -n 5 "$file" 2>/dev/null | grep -qE '^#[[:space:]]*hi04-exempt:[[:space:]]*gate-hook'; then
      echo "ℹ️  HI-04 면제(gate-hook) — exit 2 허용: $file"
    else
      # exit 2 검출. `^[^#]*` = 줄에서 첫 `#` 이전 영역에서만 매치 → 단독 `  exit 2`,
      # `foo && exit 2`, `exit 2;` 모두 포착하면서, 전체 주석(`# ... exit 2`)과
      # 후행 주석(`cmd  # ... exit 2`)은 자연 제외(구 정규식의 단독-누락도, awk의 후행-오탐도 회피).
      # 알려진 한계(2차 리뷰 #1, 구 정규식도 동일·회귀 아님): 같은 줄에서 `exit 2` *앞에*
      # 문자열/정규식 리터럴 속 `#`이 있으면(`grep '#x' && exit 2`) 매치가 거기서 잘려 놓친다.
      # grep만으로 셸 토큰을 렉싱할 수 없어 감수 — 훅에서 이런 형태는 극히 드물고, 본 검사가
      # 막으려는 주 케이스(무심코 추가한 단독 `exit 2`)는 정상 포착됨.
      if grep -nE '^[^#]*\bexit[[:space:]]+2\b' "$file" > /dev/null 2>&1; then
        echo "❌ HI-04 위반 — exit 2 검출:" >&2
        grep -nE '^[^#]*\bexit[[:space:]]+2\b' "$file" | sed "s|^|   $file:|" >&2
        echo "   (의도적 게이트 훅이면 파일 상단에 '# hi04-exempt: gate-hook' 선언)" >&2
        violations=$((violations + 1))
      fi
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
