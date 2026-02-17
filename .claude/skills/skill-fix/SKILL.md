---
name: skill-fix
description: PR 수정 - CRITICAL 이슈 자동 수정
disable-model-invocation: false
allowed-tools: Bash(git:*), Bash(gh:*), Bash(./gradlew:*), Bash(npm:*), Read, Write, Edit, Glob, Grep
argument-hint: "{PR번호}"
---

# skill-fix: PR 수정

## 실행 조건
- skill-review-pr --auto-fix에서 CRITICAL 이슈 발견 시 자동 호출
- 또는 사용자가 `/skill-fix {번호}` 직접 호출

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

# [REQUIRED] 3. PR 번호 지정됨
if [ -z "$PR_NUMBER" ]; then
  echo "❌ PR 번호를 지정해주세요. 예: /skill-fix 123"
  exit 1
fi

# [REQUIRED] 4. PR 존재 + OPEN 상태
PR_STATE=$(gh pr view $PR_NUMBER --json state --jq '.state' 2>/dev/null)
if [ "$PR_STATE" != "OPEN" ]; then
  echo "❌ PR #$PR_NUMBER 이 OPEN 상태가 아닙니다 (현재: $PR_STATE)."
  exit 1
fi

# [REQUIRED] 5. CRITICAL 이슈가 존재
# PR 리뷰 코멘트에서 CRITICAL 태그가 있는 코멘트 확인
```

## 워크플로우 상태 추적

스킬 진입/완료 시 해당 Task의 `workflowState`를 업데이트한다:

**진입 시:**
```json
"workflowState": {
  "currentSkill": "skill-fix",
  "lastCompletedSkill": "skill-review-pr",
  "prNumber": {PR 번호},
  "autoChainArgs": "",
  "updatedAt": "{현재 시각}"
}
```

**완료 시 (재리뷰 호출):**
```json
"workflowState": {
  "currentSkill": "skill-review-pr",
  "lastCompletedSkill": "skill-fix",
  "prNumber": {PR 번호},
  "autoChainArgs": "",
  "updatedAt": "{현재 시각}"
}
```

## 입력
- PR 번호 (필수)

## 실행 플로우

### 1. PR 브랜치 체크아웃
```bash
gh pr checkout {number}
```

### 2. CRITICAL 이슈 목록 파싱
**PR 리뷰 코멘트에서 직접 파싱** (독립 호출 가능, 결합도 낮음):
```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments
```

파싱 대상:
- `🔴 **CRITICAL**` 또는 `[CRITICAL]` 태그가 붙은 코멘트
- 파일 경로 (`path` 필드)
- 라인 번호 (`line` 필드)
- 이슈 내용 (`body` 필드)

### 3. 이슈별 코드 수정
각 CRITICAL 이슈에 대해:
1. 해당 파일 읽기
2. 문제 분석
3. 수정 코드 작성
4. Edit tool로 적용

### 4. 빌드 검증
```bash
# 프로젝트 스택에 따라
./gradlew build   # Spring Boot
npm run build     # Node.js
```

실패 시:
- 수정 재시도 (최대 3회)
- 3회 실패 → 에러 보고 후 종료

### 5. 테스트 검증
```bash
./gradlew test    # Spring Boot
npm test          # Node.js
```

실패 시:
- 수정 재시도 (최대 3회)
- 3회 실패 → 에러 보고 후 종료

### 6. 커밋 & 푸시
```bash
git add .
git commit -m "fix: 코드 리뷰 피드백 반영

- [C001] {이슈 설명}
- [C002] {이슈 설명}

Co-Authored-By: Claude <noreply@anthropic.com>"

git push
```

### 6.5 실행 로그 기록

`skill-status`의 "실행 로그 프로토콜"에 따라 `.claude/state/execution-log.json`에 추가:
```json
{"timestamp": "{현재시각}", "taskId": "{taskId}", "skill": "skill-fix", "action": "fix_completed", "details": {"prNumber": {number}, "issueCount": {N}}}
```

### 7. skill-review-pr 재호출

**반드시 Skill tool 사용:**
```
Skill tool 사용: skill="skill-review-pr", args="{prNumber}"
```

**중요:**
- --auto-fix 플래그 없이 재호출 (무한루프 방지)
- 재리뷰에서 CRITICAL 남아있으면 REQUEST_CHANGES로 종료

## 출력 포맷

```
## 🔧 PR 수정: #{number}

### 수정된 이슈
| ID | 파일 | 라인 | 설명 | 상태 |
|----|------|------|------|------|
| C001 | {파일} | {라인} | {설명} | ✅ |
| C002 | {파일} | {라인} | {설명} | ✅ |

### 변경 사항
- 수정: {N}개 파일
- 총 라인: +{added} / -{removed}

### 검증 결과
- ✅ 빌드 성공
- ✅ 테스트 통과 ({N}/{N})

### 커밋
- SHA: {commit_sha}
- 메시지: fix: 코드 리뷰 피드백 반영

### 자동 진행
🔄 `/skill-review-pr {number}` 재리뷰 실행 중...
```

## 에러 처리

### 빌드/테스트 실패 시
```
## ❌ 수정 실패

### 실패 원인
{에러 메시지}

### 시도 내역
- 1차 시도: {내용} → 실패
- 2차 시도: {내용} → 실패
- 3차 시도: {내용} → 실패

### 수동 개입 필요
자동 수정이 실패했습니다. 수동으로 수정 후:
1. 코드 수정
2. git push
3. /skill-review-pr {number}
```

## 주의사항
- 반드시 기존 PR 브랜치에서 작업 (새 브랜치 생성 금지)
- 빌드/테스트 통과 필수
- 재리뷰 시 --auto-fix 없이 호출 (무한루프 방지)
