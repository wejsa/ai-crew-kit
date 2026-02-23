---
name: skill-merge-pr
description: PR 머지 - 승인된 PR을 Squash 머지하고 상태 업데이트. 사용자가 "PR 머지해줘" 또는 /skill-merge-pr을 요청할 때 사용합니다.
disable-model-invocation: false
allowed-tools: Bash(git:*), Bash(gh:*), Read, Write, Glob
argument-hint: "{PR번호}"
---

# skill-merge-pr: PR 머지

## 실행 조건
- 사용자가 `/skill-merge-pr {번호}` 또는 "PR {번호} 머지해줘" 요청 시

## 사전 조건 검증 (MUST-EXECUTE-FIRST)

실패 시 즉시 중단 + 사용자 보고. 절대 다음 단계 진행 금지.

```bash
# [REQUIRED] 1. project.json 존재
if [ ! -f ".claude/state/project.json" ]; then
  echo "❌ project.json이 없습니다. /skill-init을 먼저 실행하세요."
  exit 1
fi

# [REQUIRED] 2. backlog.json 존재 + 유효 JSON
if [ ! -f ".claude/state/backlog.json" ]; then
  echo "❌ backlog.json이 없습니다. /skill-init을 먼저 실행하세요."
  exit 1
fi
cat .claude/state/backlog.json | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null || {
  echo "❌ backlog.json이 유효한 JSON이 아닙니다."
  exit 1
}

# [REQUIRED] 3. PR 승인 상태: Approved (또는 자기 PR)
# [REQUIRED] 4. CI 통과: 모든 체크 성공
# [REQUIRED] 5. 충돌 없음: Mergeable 상태
# [REQUIRED] 6. Draft 아님: Ready for review

# [REQUIRED] 7. origin/develop 동기화 검증
git fetch origin develop --quiet
BEHIND=$(git rev-list --count HEAD..origin/develop)
if [ "$BEHIND" -gt 5 ]; then
  echo "❌ origin/develop보다 ${BEHIND}커밋 뒤처져 있습니다."
  echo "→ git merge origin/develop 실행 후 재시도하세요."
  exit 1
elif [ "$BEHIND" -gt 0 ]; then
  echo "⚠️ origin/develop보다 ${BEHIND}커밋 뒤처짐 — 자동 동기화 중..."
  git merge origin/develop --no-edit
fi
```

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

## 워크플로우 상태 추적

스킬 진입/완료 시 해당 Task의 `workflowState`를 업데이트한다:

**진입 시:**
```json
"workflowState": {
  "currentSkill": "skill-merge-pr",
  "lastCompletedSkill": "skill-review-pr",
  "prNumber": {PR 번호},
  "autoChainArgs": "",
  "updatedAt": "{현재 시각}"
}
```

**완료 시 (다음 스텝 있음):**
```json
"workflowState": {
  "currentSkill": "skill-impl",
  "lastCompletedSkill": "skill-merge-pr",
  "prNumber": null,
  "autoChainArgs": "--next",
  "updatedAt": "{현재 시각}"
}
```

**완료 시 (마지막 스텝):**
```json
"workflowState": null
```

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

**backlog.json 쓰기 시 반드시 `skill-backlog`의 "backlog.json 쓰기 프로토콜" 준수:**
- `metadata.version` 1 증가 + `metadata.updatedAt` 갱신
- 쓰기 후 JSON 유효성 검증 필수

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

마지막 스텝 머지 완료 시, **원자적 다중 파일 업데이트 프로토콜**을 따른다.

#### 5.0 Intent 파일 생성 (복구 지점)

모든 상태 파일 변경 전에 intent 파일을 먼저 생성한다.
세션 중단 시 이 파일을 기반으로 완료 처리를 재개할 수 있다.

```json
// .claude/temp/{taskId}-complete-intent.json
{
  "taskId": "{taskId}",
  "action": "task_complete",
  "timestamp": "{현재 시각}",
  "prNumber": {number},
  "stepNumber": {N},
  "pending": ["completed.json", "backlog.json", "execution-log.json", "plan-file"],
  "done": []
}
```

#### 5.1 completed.json에 먼저 추가 (데이터 보존 우선)
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
→ intent의 `done`에 `"completed.json"` 추가, `pending`에서 제거

#### 5.2 backlog.json 업데이트
```json
{
  "status": "done",
  "completedAt": "{timestamp}"
}
```
→ intent의 `done`에 `"backlog.json"` 추가, `pending`에서 제거

#### 5.3 교차 검증: backlog-completed 정합성

```bash
# backlog.json의 status=="done"인 모든 Task ID 수집
# completed.json의 모든 Task ID 수집
# 차집합(backlog done - completed) 존재 시:
#   → 누락된 Task를 completed.json에 자동 복구
#   → 경고 메시지 출력: "⚠️ {N}건 completed.json 누락 복구됨"
```

누락 복구 시 completed.json에 최소 정보를 자동 추가:
```json
{
  "{taskId}": {
    "id": "{taskId}",
    "title": "{backlog에서 가져온 제목}",
    "completedAt": "{backlog의 completedAt 또는 현재 시각}",
    "steps": [],
    "totalPRs": 0,
    "recoveredAt": "{현재 시각}"
  }
}
```

#### 5.4 계획 파일 삭제
```bash
rm .claude/temp/{taskId}-plan.md
```
→ intent의 `done`에 `"plan-file"` 추가, `pending`에서 제거

#### 5.5 Phase 상태 자동 갱신

완료된 Task의 phase 번호를 확인하고, 해당 Phase에 속한 모든 Task의 상태를 조회:

```
완료된 Task의 phase 번호 확인
해당 phase에 속한 모든 Task의 status 조회:
- 전부 "done"     → phases[N].status = "done"
- 하나라도 "in_progress" → phases[N].status = "in_progress"
- 그 외           → phases[N].status = "todo"
```

#### 5.6 상태 파일 커밋 & 푸시 (단일 커밋으로 원자성 확보)
```bash
git add .claude/state/ .claude/temp/
git commit -m "chore: {taskId} 완료 처리"
if [ "$GIT_DIR" != "$GIT_COMMON_DIR" ]; then
  git push -u origin HEAD
else
  git push origin develop
fi
```

#### 5.7 Intent 파일 삭제
```bash
rm .claude/temp/{taskId}-complete-intent.json
```

모든 상태 파일 업데이트가 커밋된 후에만 intent 파일을 삭제한다.

#### Intent 기반 복구 (세션 재개 시)

스킬 진입 시 `.claude/temp/*-complete-intent.json` 파일이 존재하면:

```
1. intent 파일 읽기
2. pending 배열의 각 항목에 대해:
   - "completed.json": completed.json에 taskId 존재 여부 확인 → 없으면 추가
   - "backlog.json": backlog.json의 task status 확인 → "done" 아니면 변경
   - "execution-log.json": 해당 action 로그 존재 여부 확인 → 없으면 추가
   - "plan-file": 계획 파일 존재 시 삭제
3. 복구 완료 후 커밋 & 푸시
4. intent 파일 삭제
5. "⚠️ 이전 세션의 미완료 처리를 복구했습니다: {taskId}" 출력
```

### 5.5 실행 로그 기록

`skill-status`의 "실행 로그 프로토콜"에 따라 `.claude/state/execution-log.json`에 추가:
- 머지 시: `{"action": "merged", "details": {"prNumber": {number}, "stepNumber": {N}}}`
- Task 완료 시: `{"action": "task_completed", "details": {"prNumber": {number}, "stepNumber": {N}}}`

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
- `/skill-plan` 또는 "다음 작업 가져와"로 새 Task 시작
- 💡 회고를 실행하려면: `/skill-retro {taskId}`
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
