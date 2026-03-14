# Shared Protocols

스킬 간 공통 프로토콜 정의. 각 스킬의 MUST-EXECUTE-FIRST 등에서 "Protocol X를 적용한다"로 참조한다.

---

## Protocol A: 프로젝트 상태 기본 검증

project.json + backlog.json 존재 및 유효성 확인. 대부분의 스킬에서 사용.

```bash
# [REQUIRED] 1. project.json 존재
if [ ! -f ".claude/state/project.json" ]; then
  echo "❌ project.json이 없습니다"
  echo "   원인: 프로젝트가 초기화되지 않았습니다"
  echo "   해결: /skill-init을 먼저 실행하세요"
  exit 1
fi

# [REQUIRED] 2. backlog.json 존재 + 유효 JSON
if [ ! -f ".claude/state/backlog.json" ]; then
  echo "❌ backlog.json이 없습니다"
  echo "   원인: 백로그가 초기화되지 않았습니다"
  echo "   해결: /skill-init을 먼저 실행하세요"
  exit 1
fi
cat .claude/state/backlog.json | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null || {
  echo "❌ backlog.json이 유효한 JSON이 아닙니다"
  echo "   원인: JSON 파싱 실패"
  echo "   해결: /skill-validate --fix를 실행하세요"
  exit 1
}
```

---

## Protocol B: 완료 Task 검증

project.json + completed.json 존재 및 유효성 확인. skill-retro, skill-report에서 사용.

```bash
# [REQUIRED] 1. project.json 존재
if [ ! -f ".claude/state/project.json" ]; then
  echo "❌ project.json이 없습니다"
  echo "   원인: 프로젝트가 초기화되지 않았습니다"
  echo "   해결: /skill-init을 먼저 실행하세요"
  exit 1
fi

# [REQUIRED] 2. completed.json 존재 + 유효 JSON
if [ ! -f ".claude/state/completed.json" ]; then
  echo "❌ completed.json이 없습니다"
  echo "   원인: 완료된 Task가 없습니다"
  echo "   해결: Task를 완료한 후 다시 시도하세요 (/skill-impl → /skill-merge-pr 워크플로우)"
  exit 1
fi
cat .claude/state/completed.json | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null || {
  echo "❌ completed.json이 유효한 JSON이 아닙니다"
  echo "   원인: JSON 파싱 실패"
  echo "   해결: /skill-validate --fix를 실행하세요"
  exit 1
}
```

---

## Protocol C: 운영 환경 검증

clean tree + main 브랜치 + VERSION + Worktree 차단. skill-hotfix, skill-rollback, skill-release에서 사용.

```bash
# [REQUIRED] 1. project.json 존재
if [ ! -f ".claude/state/project.json" ]; then
  echo "❌ project.json이 없습니다"
  echo "   원인: 프로젝트가 초기화되지 않았습니다"
  echo "   해결: /skill-init을 먼저 실행하세요"
  exit 1
fi

# [REQUIRED] 2. clean working tree
if [ -n "$(git status --porcelain)" ]; then
  echo "❌ 커밋되지 않은 변경사항이 있습니다"
  echo "   원인: 스테이징되지 않은 파일이 존재합니다"
  echo "   해결: git stash 또는 git commit으로 정리 후 재시도하세요"
  exit 1
fi

# [REQUIRED] 3. main 브랜치 접근 가능
git rev-parse --verify main >/dev/null 2>&1 || {
  echo "❌ main 브랜치가 존재하지 않습니다"
  echo "   원인: main 브랜치가 로컬에 없습니다"
  echo "   해결: git fetch origin main && git branch main origin/main"
  exit 1
}

# [REQUIRED] 4. VERSION 파일 존재
if [ ! -f "VERSION" ]; then
  echo "❌ VERSION 파일이 없습니다"
  echo "   원인: 버전 관리 파일이 초기화되지 않았습니다"
  echo "   해결: /skill-init을 먼저 실행하세요"
  exit 1
fi

# [REQUIRED] 5. Worktree 모드 차단
# → Protocol E 적용 (차단 모드)
```

---

## Protocol D: origin/develop 동기화

원격 develop과의 동기화 확인 + 자동 머지. skill-plan, skill-impl, skill-merge-pr에서 사용.

```bash
git fetch origin develop --quiet
BEHIND=$(git rev-list --count HEAD..origin/develop)
if [ "$BEHIND" -gt 5 ]; then
  echo "❌ origin/develop보다 ${BEHIND}커밋 뒤처져 있습니다"
  echo "   원인: 다른 세션에서 다수의 커밋이 추가되었습니다"
  echo "   해결: git merge origin/develop 실행 후 재시도하세요"
  exit 1
elif [ "$BEHIND" -gt 0 ]; then
  echo "⚠️ origin/develop보다 ${BEHIND}커밋 뒤처짐 — 자동 동기화 중..."
  git merge origin/develop --no-edit
fi
```

---

## Protocol E: Worktree 감지

Git worktree 환경 감지. **차단 모드**(hotfix/rollback/release)와 **조건 분기 모드**(impl/plan/feature)가 있다.

### 감지 코드 (공통)

```bash
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
GIT_COMMON_DIR=$(git rev-parse --git-common-dir 2>/dev/null)
IS_WORKTREE=$( [ "$GIT_DIR" != "$GIT_COMMON_DIR" ] && echo "true" || echo "false" )
```

### 차단 모드

main/develop을 직접 조작하는 스킬에서 사용. Worktree 감지 시 즉시 중단.

```bash
if [ "$IS_WORKTREE" == "true" ]; then
  MAIN_REPO=$(git rev-parse --git-common-dir | sed 's/\/.git$//')
  echo "❌ Worktree 환경에서는 {스킬명}을 실행할 수 없습니다"
  echo ""
  echo "📌 이유: {스킬명}은 main/develop 브랜치를 직접 조작하므로"
  echo "   워크트리의 독립 브랜치 구조와 충돌합니다."
  echo ""
  echo "💡 대안:"
  echo "  1. 메인 레포에서 실행: cd $MAIN_REPO"
  echo "  2. Claude Squad에서: cs switch main → 실행 → cs switch back"
  exit 1
fi
```

### 조건 분기 모드

push/commit 동작이 Worktree 여부에 따라 달라지는 스킬에서 사용.

```bash
if [ "$IS_WORKTREE" == "true" ]; then
  # Worktree: 현재 브랜치에 push
  git push -u origin HEAD
else
  # 일반: develop에 push
  git push origin develop
fi
```

---

## Protocol F: 빌드 명령어 결정

project.json의 buildCommands 우선, 미설정 시 techStack 기반 폴백.

```bash
# 1단계: project.json의 buildCommands 확인
BUILD_CMD=$(python3 -c "import json; d=json.load(open('.claude/state/project.json')); print(d.get('buildCommands',{}).get('build',''))" 2>/dev/null)
TEST_CMD=$(python3 -c "import json; d=json.load(open('.claude/state/project.json')); print(d.get('buildCommands',{}).get('test',''))" 2>/dev/null)
LINT_CMD=$(python3 -c "import json; d=json.load(open('.claude/state/project.json')); print(d.get('buildCommands',{}).get('lint',''))" 2>/dev/null)

# 2단계: 미설정 시 techStack 기반 폴백
if [ -z "$BUILD_CMD" ]; then
  STACK=$(python3 -c "import json; print(json.load(open('.claude/state/project.json')).get('techStack',{}).get('backend',''))")
  case "$STACK" in
    *spring*|*kotlin*|*java*)
      BUILD_CMD="./gradlew build"
      TEST_CMD="${TEST_CMD:-./gradlew test}"
      LINT_CMD="${LINT_CMD:-./gradlew ktlintCheck}"
      ;;
    *node*|*typescript*|*express*|*nest*)
      BUILD_CMD="npm run build"
      TEST_CMD="${TEST_CMD:-npm test}"
      LINT_CMD="${LINT_CMD:-npm run lint}"
      ;;
    *go*)
      BUILD_CMD="go build ./..."
      TEST_CMD="${TEST_CMD:-go test ./...}"
      LINT_CMD="${LINT_CMD:-golangci-lint run}"
      ;;
  esac
fi
```

---

## Protocol G: 에러 메시지 표준 포맷

모든 스킬의 에러 메시지는 다음 3줄 형식을 따른다:

```
❌ {무엇이 실패했는지}
   원인: {왜 실패했는지}
   해결: {사용자가 해야 할 행동}
```

**규칙:**
- 첫 줄(❌)은 현상만 기술, 원인을 혼합하지 않음
- "해결" 줄에는 구체적 명령어 또는 슬래시 커맨드 포함
- 복구 불가능한 에러도 다음 단계를 안내 (예: "수동 확인 필요")

**예시:**
```
❌ backlog.json이 유효한 JSON이 아닙니다
   원인: JSON 파싱 실패
   해결: /skill-validate --fix를 실행하세요
```

---

## Protocol H: 사용자 승인 요청 표준

사용자 확인/선택이 필요한 경우 **AskUserQuestion** 도구를 사용한다.

### 이진 승인 (Y/N)

```
AskUserQuestion:
  question: "{작업 요약}을 승인하시겠습니까?"
  options:
    - "승인 — {승인 시 다음 액션 설명}"
    - "거절 — {거절 시 다음 액션 설명}"
    - "수정 — 수정사항을 입력해주세요"
```

### 다지선다

```
AskUserQuestion:
  question: "{상황 설명}"
  options:
    - "{옵션 1 설명}"
    - "{옵션 2 설명}"
    - "{옵션 3 설명}"
```

**규칙:**
- 텍스트 기반 `Y/N` 프롬프트 대신 AskUserQuestion 사용
- 각 옵션에 결과 행동을 명시
- 기본 선택지는 첫 번째에 배치

---

## Protocol I: 진행 표시

### 체이닝 스킬 (plan, impl, review-pr, fix, merge-pr, feature)

CLAUDE.md의 "워크플로우 진행 표시 프로토콜"을 따른다:

```
━━━ {TASK_ID} "{TASK_TITLE}" ━━━━━━━━━━━
 ✅ plan → ✅ impl(1/N) → 🔄 review → ⬜ merge → ⬜ impl(2/N)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 📍 현재: {현재 스킬 설명}
```

### 독립 스킬 (retro, report, estimate, create, onboard)

체이닝이 아닌 독립 스킬은 간소화된 진행 표시를 사용한다:

```
━━━ {스킬명} ━━━━━━━━━━━━━━━━━━━━
 📍 {현재 수행 중인 작업 설명}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**예시:**
```
━━━ skill-retro ━━━━━━━━━━━━━━━━━━
 📍 TASK-001 회고 분석 중
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━ skill-report ━━━━━━━━━━━━━━━━━
 📍 프로젝트 메트릭 수집 중 (최근 7일)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━ skill-estimate ━━━━━━━━━━━━━━━
 📍 TASK-003 복잡도 분석 중 (5팩터)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
