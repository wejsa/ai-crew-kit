---
name: skill-merge-pr
description: PR 머지 - 승인된 PR을 Squash 머지하고 상태 업데이트
disable-model-invocation: false
allowed-tools: Bash(git:*), Bash(gh:*), Read, Write, Glob
argument-hint: "{PR번호}"
---

# skill-merge-pr: PR 머지

## 실행 조건
- 사용자가 `/skill-merge-pr {번호}` 또는 "PR {번호} 머지해줘" 요청 시

## 사전 조건 검증

### 필수 조건
1. **PR 승인 상태**: Approved (또는 자기 PR)
2. **CI 통과**: 모든 체크 성공
3. **충돌 없음**: Mergeable 상태
4. **Draft 아님**: Ready for review

```bash
# 상태 확인
gh pr view 123 --json state,reviewDecision,mergeable,statusCheckRollup,author

# 자기 PR 여부 확인
PR_AUTHOR=$(gh pr view 123 --json author --jq '.author.login')
CURRENT_USER=$(gh api user --jq '.login')
IS_SELF_PR=$([[ "$PR_AUTHOR" == "$CURRENT_USER" ]] && echo "true" || echo "false")
```

### 자기 PR 예외 처리
- 자기 PR은 GitHub 정책상 승인 불가
- `reviewDecision`이 `APPROVED`가 아니어도 머지 허용
- 대신 **skill-review-pr에서 COMMENT 리뷰 완료** 확인

## 실행 플로우

### 1. PR 상태 확인
```bash
gh pr view 123 --json title,state,reviewDecision,mergeable,headRefName,baseRefName,author
```

**자기 PR 감지 및 승인 조건 처리**:
```bash
# 자기 PR 여부 확인
PR_AUTHOR=$(gh pr view 123 --json author --jq '.author.login')
CURRENT_USER=$(gh api user --jq '.login')

if [ "$PR_AUTHOR" == "$CURRENT_USER" ]; then
  # 자기 PR: reviewDecision 검사 스킵, CI와 충돌만 확인
  echo "자기 PR 감지 - 승인 조건 스킵"
else
  # 타인 PR: reviewDecision == APPROVED 필수
  REVIEW_DECISION=$(gh pr view 123 --json reviewDecision --jq '.reviewDecision')
  if [ "$REVIEW_DECISION" != "APPROVED" ]; then
    echo "PR 미승인 (현재: $REVIEW_DECISION)"
    exit 1
  fi
fi
```

**검증 실패 시**:
```
## ❌ 머지 불가

### 원인
- [ ] PR 미승인 (현재: REVIEW_REQUIRED) ← 타인 PR만 해당
- [ ] CI 실패
- [ ] 충돌 발생

### 해결 방법
1. `/skill-review-pr 123` 으로 리뷰 요청
2. 충돌 해결 후 재시도

※ 자기 PR은 승인 없이도 머지 가능 (셀프 리뷰 완료 시)
```

### 2. Squash 머지 실행
```bash
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
GIT_COMMON_DIR=$(git rev-parse --git-common-dir 2>/dev/null)
if [ "$GIT_DIR" != "$GIT_COMMON_DIR" ]; then
  # Worktree 모드: CS 브랜치 삭제 금지 (CS가 관리)
  gh pr merge 123 --squash
else
  gh pr merge 123 --squash --delete-branch
fi
```

머지 커밋 메시지:
```
feat: {Task ID} Step {N} - {스텝 제목} (#123)

* 변경 사항 요약
* Co-authored-by: ...
```

### 3. 로컬 동기화
```bash
if [ "$GIT_DIR" != "$GIT_COMMON_DIR" ]; then
  # Worktree 모드: CS 브랜치에 develop 변경사항 머지
  git fetch origin develop --prune
  git merge origin/develop
else
  # develop 브랜치로 이동
  git checkout develop
  # 최신 상태 동기화
  git pull origin develop
  # 로컬 브랜치 정리 (삭제된 원격 브랜치)
  git fetch --prune
fi
```

### 4. 계획 파일 상태 업데이트
`.claude/temp/{taskId}-plan.md` 또는 `backlog.json` 업데이트:

```json
{
  "steps": [
    {"number": 1, "status": "merged", "prNumber": 123, "mergedAt": "..."},
    {"number": 2, "status": "pending"}
  ],
  "currentStep": 2
}
```

### 5. Task 완료 처리 (마지막 스텝인 경우)

마지막 스텝 머지 완료 시:

#### 5.1 backlog.json 업데이트
```json
{
  "status": "done",
  "completedAt": "{timestamp}"
}
```

#### 5.2 completed.json에 이동
```json
{
  "{taskId}": {
    "id": "{taskId}",
    "title": "{제목}",
    "completedAt": "{timestamp}",
    "steps": [...],
    "totalPRs": {N}
  }
}
```

#### 5.3 계획 파일 삭제
```bash
rm .claude/temp/{taskId}-plan.md
```

#### 5.4 커밋 & 푸시
```bash
git add .claude/state/
git commit -m "chore: {taskId} 완료 처리"
if [ "$GIT_DIR" != "$GIT_COMMON_DIR" ]; then
  git push -u origin HEAD
else
  git push origin develop
fi
```

### 6. 다음 스텝 자동 진행

**남은 스텝이 있을 때 반드시 수행:**
```
Skill tool 사용: skill="skill-impl", args="--next"
```

**조건:**
- 남은 스텝 있음: skill-impl --next 자동 호출
- 마지막 스텝 완료: Task 완료 처리 후 종료

**중요:**
- PR 머지 및 상태 업데이트 후 skill-impl 호출
- skill-impl 호출 없이 직접 개발 진행 **금지**
- 반드시 Skill tool을 사용하여 skill-impl 스킬 실행

**출력 예시 (중간 스텝):**
```
✅ PR #{number} 머지 완료
🔄 Step {N+1} 개발을 자동 시작합니다...
```

**출력 예시 (마지막 스텝):**
```
🎉 Task 완료!
다음 작업: `/skill-plan` 또는 "다음 작업 가져와"
```

## 출력 포맷

### 중간 스텝 머지 완료
```
## ✅ PR 머지 완료: #{number}

### 머지 정보
- **PR**: #{number} - {제목}
- **브랜치**: {head} → {base}
- **머지 방식**: Squash

### Task 진행 상황
- **Task**: {taskId} - {제목}
- **완료 스텝**: Step {N}/{Total}
- **남은 스텝**: {remaining}개

### 자동 진행
🔄 `/skill-impl --next` 자동 실행 중...

남은 스텝: {remaining}개
```

### 마지막 스텝 머지 완료
```
## 🎉 Task 완료: {taskId}

### 완료 정보
- **Task**: {taskId} - {제목}
- **전체 스텝**: {N}개
- **전체 PR**: {N}개
- **완료 시각**: {timestamp}

### 작업 요약
| Step | 제목 | PR |
|------|------|-----|
| 1 | {제목} | #{number} |
| 2 | {제목} | #{number} |

### 다음 단계
`/skill-plan` 또는 "다음 작업 가져와"로 새 Task 시작
```

## 에러 처리

### 머지 실패 시
```
## ❌ 머지 실패

### 에러
{에러 메시지}

### 가능한 원인
1. 권한 부족
2. 브랜치 보호 규칙
3. 필수 리뷰어 미승인

### 해결 방법
{해결 방법}
```

### 충돌 발생 시
```
## ⚠️ 충돌 발생

### 충돌 파일
- {파일 1}
- {파일 2}

### 해결 방법
1. PR 브랜치 체크아웃: `gh pr checkout 123` (worktree 모드에서는 불필요)
2. develop 머지: `git merge develop` (worktree: `git fetch origin develop && git merge origin/develop`)
3. 충돌 해결
4. 커밋 & 푸시
5. 재시도: `/skill-merge-pr 123`
```

## lockedFiles 해제

PR 머지 완료 시:

### 해제 로직

```
1. 머지된 PR의 변경 파일 목록 조회
2. 해당 파일들 lockedFiles에서 제거
3. 다음 스텝이 있으면:
   - currentStep 증가
   - steps[currentStep].status = "pending"
   - 다음 스텝 files는 lockedFiles 유지
4. 마지막 스텝이면:
   - lockedFiles 전체 제거
   - assignee, assignedAt 제거
   - status = "done"
5. Git 커밋 & 푸시
```

### 예시

```
초기 상태:
- Step 1: A.kt, B.kt (in_progress)
- Step 2: C.kt (pending)
- lockedFiles: [A.kt, B.kt, C.kt]

Step 1 PR 머지 후:
- Step 1: A.kt, B.kt (done)
- Step 2: C.kt (pending)
- lockedFiles: [C.kt]  ← A.kt, B.kt 해제

Step 2 PR 머지 후:
- Task 완료
- lockedFiles: []  ← 전체 해제
- assignee: null
- status: "done"
```

## 주의사항
- 반드시 리뷰 완료 후 머지 (타인 PR: 승인 필수, 자기 PR: 셀프 리뷰 코멘트 완료)
- **자기 PR은 GitHub 정책상 승인 불가 → 승인 조건 스킵하고 머지 허용**
- Squash 머지만 사용 (커밋 히스토리 정리)
- 머지 후 로컬 브랜치 자동 정리
- Task 완료 시 상태 파일 커밋 필수
- 머지 시 lockedFiles 자동 해제 확인
