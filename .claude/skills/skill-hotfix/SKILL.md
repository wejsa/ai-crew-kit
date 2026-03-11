---
name: skill-hotfix
description: main 긴급 수정 - 핫픽스 브랜치 + 보안 리뷰 + 패치 릴리스 + develop 백머지. 사용자가 "긴급 수정해줘" 또는 /skill-hotfix를 요청할 때 사용합니다.
disable-model-invocation: false
allowed-tools: Bash(git:*), Bash(gh:*), Bash(./gradlew:*), Bash(npm:*), Read, Write, Edit, Glob, Grep
argument-hint: "\"{긴급 수정 설명}\""
---

# skill-hotfix: main 긴급 수정

## 실행 조건
- 사용자가 `/skill-hotfix "설명"` 또는 "긴급 수정해줘: 설명" 요청 시
- main 브랜치 장애/보안 이슈 발생 시

## 사전 조건 검증 (MUST-EXECUTE-FIRST)

실패 시 즉시 중단 + 사용자 보고. 절대 다음 단계 진행 금지.

**공통 프로토콜 적용** (`.claude/docs/shared-protocols.md` 참조):
- Protocol C: 운영 환경 검증 (project.json + clean tree + main + VERSION + Worktree 차단)
  - Worktree 차단 메시지의 `{스킬명}` → `hotfix`

## 실행 로그 기록 (시작)

`.claude/state/execution-log.json`에 추가:
```json
{
  "timestamp": "{현재 시각}",
  "taskId": "HOTFIX",
  "skill": "skill-hotfix",
  "action": "hotfix_started",
  "details": {"description": "{수정 설명}"}
}
```

## 실행 플로우

### 1. Hotfix 번호 생성

```bash
# 기존 hotfix 브랜치 번호 확인
LAST_HOT=$(git branch -a --list '*hotfix/HOT-*' | grep -oP 'HOT-\K\d+' | sort -n | tail -1)
NEXT_HOT=$(printf "%03d" $(( ${LAST_HOT:-0} + 1 )))
HOTFIX_ID="HOT-${NEXT_HOT}"
```

### 2. Hotfix 브랜치 생성

```bash
# main 최신 상태 확인
git fetch origin main
git checkout main
git pull origin main

# hotfix 브랜치 생성
BRANCH_NAME="hotfix/${HOTFIX_ID}-${DESCRIPTION_SLUG}"
git checkout -b "$BRANCH_NAME"
```

### 3. 코드 수정

- 사용자가 제공한 수정 설명을 분석
- 관련 코드 탐색 (Glob, Grep, Read)
- 수정 코드 작성 (Edit, Write)
- 최소한의 변경만 수행 (긴급 수정 원칙)

### 4. 빌드/테스트 검증

```bash
# buildCommands 우선 참조 → techStack 폴백
BUILD_CMD=$(python3 -c "import json; d=json.load(open('.claude/state/project.json')); print(d.get('buildCommands',{}).get('build',''))" 2>/dev/null)
TEST_CMD=$(python3 -c "import json; d=json.load(open('.claude/state/project.json')); print(d.get('buildCommands',{}).get('test',''))" 2>/dev/null)

if [ -z "$BUILD_CMD" ]; then
  STACK=$(python3 -c "import json; print(json.load(open('.claude/state/project.json')).get('techStack',{}).get('backend',''))")
  case "$STACK" in
    *spring*|*kotlin*|*java*)
      BUILD_CMD="./gradlew build"; TEST_CMD="${TEST_CMD:-./gradlew test}";;
    *node*|*typescript*|*express*|*nest*)
      BUILD_CMD="npm run build"; TEST_CMD="${TEST_CMD:-npm test}";;
    *go*)
      BUILD_CMD="go build ./..."; TEST_CMD="${TEST_CMD:-go test ./...}";;
    *)
      echo "⚠️ 빌드 도구 미감지 - 수동 검증 필요";;
  esac
fi

[ -n "$BUILD_CMD" ] && eval "$BUILD_CMD"
[ -n "$TEST_CMD" ] && eval "$TEST_CMD"
```

### 5. 커밋

```bash
git add -A
git commit -m "$(cat <<'EOF'
hotfix: {HOTFIX_ID} - {수정 설명}

- {변경 사항 요약}

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

### 6. PR 생성 (main 대상)

```bash
git push -u origin "$BRANCH_NAME"

gh pr create \
  --base main \
  --title "hotfix: ${HOTFIX_ID} - ${수정 설명}" \
  --body "$(cat <<'EOF'
## Summary
- {수정 내용 요약}

## Root Cause
- {원인 분석}

## Fix
- {수정 방법}

## Test Plan
- [ ] 빌드 통과
- [ ] 수정 검증

🔥 Hotfix PR - main 브랜치 긴급 수정
🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### 7. 보안 리뷰 (pr-reviewer-security 서브에이전트)

핫픽스는 보안 리뷰만 수행 (빠른 머지를 위해 최소 리뷰):

```
Task tool 사용:
  subagent_type: "general-purpose"
  prompt: |
    pr-reviewer-security 에이전트 파일을 읽고 보안 리뷰를 수행하세요.
    Read .claude/agents/pr-reviewer-security.md
    PR #{PR번호} 리뷰
```

**CRITICAL 발견 시**: 수정 후 재리뷰
**CRITICAL 없음**: 머지 진행

### 8. Squash 머지

```bash
gh pr merge $PR_NUMBER --squash --delete-branch
```

### 9. 패치 버전 범프

```bash
# main 브랜치로 이동
git checkout main
git pull origin main

# 현재 버전 확인
CURRENT_VERSION=$(cat VERSION)
# patch 버전 증가
NEW_VERSION=$(echo "$CURRENT_VERSION" | awk -F. '{print $1"."$2"."$3+1}')

# VERSION 파일 업데이트
echo "$NEW_VERSION" > VERSION
```

### 10. CHANGELOG 업데이트

`CHANGELOG.md`에 핫픽스 항목 추가:

```markdown
## [{NEW_VERSION}] - {YYYY-MM-DD}

### Fixed
- {HOTFIX_ID}: {수정 설명}
```

**주의**: `[Unreleased]` 섹션과 이전 버전 섹션 사이에 삽입.

### 11. README 버전 업데이트

```bash
# README.md 제목의 버전 업데이트
# "# {프로젝트명} v{OLD}" → "# {프로젝트명} v{NEW}"
```

### 12. 릴리스 커밋 + 태그

```bash
git add VERSION CHANGELOG.md README.md
git commit -m "$(cat <<'EOF'
release: v{NEW_VERSION} hotfix - {수정 설명}

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"

# 태그 생성
git tag -a "v${NEW_VERSION}" -m "Release v${NEW_VERSION} - hotfix"
```

### 13. develop 백머지

```bash
git checkout develop
git pull origin develop
git merge main --no-edit
```

**충돌 발생 시**:
- develop(최신)을 우선으로 해결
- VERSION, CHANGELOG.md는 main(hotfix) 버전 우선

### 14. Push all

```bash
git push origin main
git push origin "v${NEW_VERSION}"
git push origin develop
```

## 실행 로그 기록 (완료)

```json
{
  "timestamp": "{현재 시각}",
  "taskId": "HOTFIX",
  "skill": "skill-hotfix",
  "action": "hotfix_completed",
  "details": {
    "hotfixId": "{HOTFIX_ID}",
    "prNumber": {PR번호},
    "version": "{NEW_VERSION}",
    "description": "{수정 설명}"
  }
}
```

## 출력 포맷

### 성공
```
## 🔥 Hotfix 완료: {HOTFIX_ID}

### 수정 정보
- **설명**: {수정 설명}
- **PR**: #{PR번호}
- **브랜치**: {hotfix 브랜치} → main

### 릴리스
- **이전 버전**: v{이전 버전}
- **신규 버전**: v{신규 버전}
- **태그**: v{신규 버전}

### 백머지
- ✅ develop 브랜치에 백머지 완료

### 다음 단계
- 배포 확인
- 모니터링
```

### 실패
```
## ❌ Hotfix 실패

### 단계
{실패한 단계}

### 에러
{에러 메시지}

### 복구 방법
{복구 절차}
```

## 자동 체이닝
- 없음 (독립 실행)
- 롤백이 필요한 경우: `/skill-rollback v{버전}` 안내

## 주의사항
- main 브랜치에서 직접 분기하는 **유일한** 스킬
- PR은 반드시 `--base main`으로 생성
- 최소한의 변경만 수행 (긴급 수정 원칙)
- develop 백머지 필수 (main과 develop 동기화)
- Worktree 환경에서는 실행 불가 (메인 레포에서 실행)
- 보안 리뷰만 수행 (전체 리뷰 대신 빠른 머지 우선)
