---
name: skill-merge-pr
description: PR 머지 - 승인된 PR을 Squash 머지하고 상태 업데이트
disable-model-invocation: true
allowed-tools: Bash(git:*), Bash(gh:*), Read, Write, Glob
argument-hint: "{PR번호}"
---

# skill-merge-pr: PR 머지

## 실행 조건
- 사용자가 `/skill-merge-pr {번호}` 또는 "PR {번호} 머지해줘" 요청 시

## 사전 조건 검증

### 필수 조건
1. **PR 승인 상태**: Approved
2. **CI 통과**: 모든 체크 성공
3. **충돌 없음**: Mergeable 상태
4. **Draft 아님**: Ready for review

```bash
# 상태 확인
gh pr view 123 --json state,reviewDecision,mergeable,statusCheckRollup
```

## 실행 플로우

### 1. PR 상태 확인
```bash
gh pr view 123 --json title,state,reviewDecision,mergeable,headRefName,baseRefName
```

**검증 실패 시**:
```
## ❌ 머지 불가

### 원인
- [ ] PR 미승인 (현재: REVIEW_REQUIRED)
- [ ] CI 실패
- [ ] 충돌 발생

### 해결 방법
1. `/skill-review-pr 123` 으로 리뷰 요청
2. 충돌 해결 후 재시도
```

### 2. Squash 머지 실행
```bash
gh pr merge 123 --squash --delete-branch
```

머지 커밋 메시지:
```
feat: {Task ID} Step {N} - {스텝 제목} (#123)

* 변경 사항 요약
* Co-authored-by: ...
```

### 3. 로컬 동기화
```bash
# develop 브랜치로 이동
git checkout develop

# 최신 상태 동기화
git pull origin develop

# 로컬 브랜치 정리 (삭제된 원격 브랜치)
git fetch --prune
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
git push origin develop
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

### 다음 단계
`/skill-impl --next` 또는 "다음 스텝 진행해줘"
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
1. PR 브랜치 체크아웃: `gh pr checkout 123`
2. develop 머지: `git merge develop`
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
- 반드시 리뷰 승인 후 머지
- Squash 머지만 사용 (커밋 히스토리 정리)
- 머지 후 로컬 브랜치 자동 정리
- Task 완료 시 상태 파일 커밋 필수
- 머지 시 lockedFiles 자동 해제 확인
