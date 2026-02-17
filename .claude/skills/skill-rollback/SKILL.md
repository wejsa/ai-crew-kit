---
name: skill-rollback
description: 릴리스 롤백 - git revert 기반 안전한 릴리스/PR 롤백 + 감사 추적
disable-model-invocation: false
allowed-tools: Bash(git:*), Bash(gh:*), Read, Write, Edit, Glob
argument-hint: "\"{태그 또는 PR번호}\""
---

# skill-rollback: 릴리스 롤백

## 실행 조건
- 사용자가 `/skill-rollback v1.2.3` 또는 "v1.2.3 롤백해줘" 요청 시
- 사용자가 `/skill-rollback #123` 또는 "PR 123 롤백해줘" 요청 시

## 사전 조건 검증 (MUST-EXECUTE-FIRST)

실패 시 즉시 중단 + 사용자 보고. 절대 다음 단계 진행 금지.

```bash
# [REQUIRED] 1. project.json 존재
if [ ! -f ".claude/state/project.json" ]; then
  echo "❌ project.json이 없습니다. /skill-init을 먼저 실행하세요."
  exit 1
fi

# [REQUIRED] 2. clean working tree
if [ -n "$(git status --porcelain)" ]; then
  echo "❌ 커밋되지 않은 변경사항이 있습니다. 먼저 정리해주세요."
  exit 1
fi

# [REQUIRED] 3. main 브랜치 접근 가능
git rev-parse --verify main >/dev/null 2>&1 || {
  echo "❌ main 브랜치가 존재하지 않습니다."
  exit 1
}

# [REQUIRED] 4. VERSION 파일 존재
if [ ! -f "VERSION" ]; then
  echo "❌ VERSION 파일이 없습니다."
  exit 1
fi

# [REQUIRED] 5. Worktree 모드 차단
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
GIT_COMMON_DIR=$(git rev-parse --git-common-dir 2>/dev/null)
if [ "$GIT_DIR" != "$GIT_COMMON_DIR" ]; then
  echo "❌ Worktree 환경에서는 rollback을 실행할 수 없습니다."
  echo "메인 레포지토리에서 실행해주세요: $(git rev-parse --git-common-dir)"
  exit 1
fi
```

## 실행 로그 기록 (시작)

`.claude/state/execution-log.json`에 추가:
```json
{
  "timestamp": "{현재 시각}",
  "taskId": "ROLLBACK",
  "skill": "skill-rollback",
  "action": "rollback_started",
  "details": {"target": "{태그 또는 PR번호}"}
}
```

## 실행 플로우

### 1. 타겟 식별

#### 태그 기반 (v1.2.3)
```bash
# 태그 존재 확인
git rev-parse --verify "v1.2.3" >/dev/null 2>&1 || {
  echo "❌ 태그 v1.2.3이 존재하지 않습니다."
  exit 1
}

# 태그가 가리키는 커밋 SHA
TARGET_SHA=$(git rev-list -1 "v1.2.3")

# merge commit 여부 확인
PARENT_COUNT=$(git cat-file -p "$TARGET_SHA" | grep -c "^parent")
IS_MERGE=$( [ "$PARENT_COUNT" -gt 1 ] && echo "true" || echo "false" )
```

#### PR 번호 기반 (#123)
```bash
# PR 정보 조회
PR_INFO=$(gh pr view 123 --json mergeCommit,state,baseRefName,title)
PR_STATE=$(echo "$PR_INFO" | python3 -c "import json,sys; print(json.load(sys.stdin)['state'])")

# PR이 머지되었는지 확인
if [ "$PR_STATE" != "MERGED" ]; then
  echo "❌ PR #123은 아직 머지되지 않았습니다 (현재: $PR_STATE)."
  exit 1
fi

# merge commit SHA
TARGET_SHA=$(echo "$PR_INFO" | python3 -c "import json,sys; print(json.load(sys.stdin)['mergeCommit']['oid'])")

# merge commit 여부 확인
PARENT_COUNT=$(git cat-file -p "$TARGET_SHA" | grep -c "^parent")
IS_MERGE=$( [ "$PARENT_COUNT" -gt 1 ] && echo "true" || echo "false" )
```

### 2. Revert 브랜치 생성

```bash
# main 최신 상태 확인
git fetch origin main
git checkout main
git pull origin main

# revert 브랜치 생성
TARGET_LABEL=$(echo "{target}" | tr '/#' '-')
BRANCH_NAME="revert/${TARGET_LABEL}"
git checkout -b "$BRANCH_NAME"
```

### 3. Git Revert 실행

```bash
if [ "$IS_MERGE" == "true" ]; then
  # merge commit: --mainline 1 필수
  git revert "$TARGET_SHA" --mainline 1 --no-edit
else
  # 일반 commit
  git revert "$TARGET_SHA" --no-edit
fi
```

**revert 충돌 발생 시**:
```
## ⚠️ Revert 충돌 발생

### 충돌 파일
{충돌 파일 목록}

### 해결 방법
1. 충돌 파일을 수동으로 해결하세요
2. `git add {파일}` → `git revert --continue`
3. 또는 `/skill-rollback` 재실행

### 현재 상태
revert 브랜치: {브랜치명}
```

### 4. 빌드/테스트 검증

```bash
# project.json에서 스택 확인 후 빌드
STACK=$(python3 -c "import json; print(json.load(open('.claude/state/project.json')).get('techStack',{}).get('backend',''))")

case "$STACK" in
  *spring*|*kotlin*|*java*)
    ./gradlew build test
    ;;
  *node*|*typescript*|*express*|*nest*)
    npm test
    ;;
  *)
    echo "⚠️ 빌드 도구 미감지 - 수동 검증 필요"
    ;;
esac
```

### 5. Revert PR 생성

```bash
git push -u origin "$BRANCH_NAME"

gh pr create \
  --base main \
  --title "revert: ${TARGET_LABEL} 롤백" \
  --body "$(cat <<'EOF'
## Summary
- {target} 변경사항 롤백

## Reverted Changes
- 원본: {원본 커밋/PR/태그 정보}
- SHA: {TARGET_SHA}

## Reason
- {롤백 사유}

## Test Plan
- [ ] 빌드 통과
- [ ] revert 후 정상 동작 확인

⏪ Revert PR - 안전한 롤백
🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### 6. PR 머지

```bash
gh pr merge $PR_NUMBER --squash --delete-branch
```

### 7. 패치 버전 범프 + CHANGELOG

```bash
# main 브랜치로 이동
git checkout main
git pull origin main

# 패치 버전 증가
CURRENT_VERSION=$(cat VERSION)
NEW_VERSION=$(echo "$CURRENT_VERSION" | awk -F. '{print $1"."$2"."$3+1}')
echo "$NEW_VERSION" > VERSION
```

CHANGELOG.md 업데이트 (`[Unreleased]`와 이전 버전 사이에 삽입):
```markdown
## [{NEW_VERSION}] - {YYYY-MM-DD}

### Reverted
- {target}: {롤백 대상 설명}

### Fixed
- {revert로 해결된 문제 설명}
```

README.md 제목 버전 업데이트.

### 8. 릴리스 커밋 + 태그

```bash
git add VERSION CHANGELOG.md README.md
git commit -m "$(cat <<'EOF'
release: v{NEW_VERSION} revert - {target} 롤백

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"

# 태그 생성
git tag -a "v${NEW_VERSION}" -m "Release v${NEW_VERSION} - revert ${target}"
```

### 9. develop 백머지

```bash
git checkout develop
git pull origin develop
git merge main --no-edit
```

**충돌 발생 시**: develop(최신) 우선, VERSION/CHANGELOG는 main 우선.

### 10. Push all

```bash
git push origin main
git push origin "v${NEW_VERSION}"
git push origin develop
```

## 실행 로그 기록 (완료)

```json
{
  "timestamp": "{현재 시각}",
  "taskId": "ROLLBACK",
  "skill": "skill-rollback",
  "action": "rollback_completed",
  "details": {
    "target": "{태그 또는 PR번호}",
    "revertSha": "{revert 커밋 SHA}",
    "prNumber": {PR번호},
    "version": "{NEW_VERSION}"
  }
}
```

## 출력 포맷

### 성공
```
## ⏪ 롤백 완료: {target}

### 롤백 정보
- **대상**: {target} ({SHA 앞 7자리})
- **Revert PR**: #{PR번호}
- **브랜치**: {revert 브랜치} → main

### 릴리스
- **이전 버전**: v{이전 버전}
- **신규 버전**: v{신규 버전}
- **태그**: v{신규 버전}

### 백머지
- ✅ develop 브랜치에 백머지 완료

### 다음 단계
- 배포 확인
- 원본 변경사항 수정 후 재배포 필요 시 `/skill-hotfix` 사용
```

### 실패
```
## ❌ 롤백 실패

### 단계
{실패한 단계}

### 에러
{에러 메시지}

### 복구 방법
{복구 절차}
```

## 자동 체이닝
- 없음 (독립 실행)

## 주의사항
- `git revert`를 사용하여 히스토리를 보존하는 안전한 롤백
- `git reset`이나 `--force` 푸시는 **절대 사용 금지**
- PR 기반 감사 추적 (revert 사유/내용 기록)
- main 브랜치에 직접 PR (`--base main`)
- develop 백머지 필수
- Worktree 환경에서는 실행 불가
