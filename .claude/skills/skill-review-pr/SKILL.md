---
name: skill-review-pr
description: PR 리뷰 - GitHub PR에 대한 5관점 통합 리뷰 수행. 사용자가 "PR 리뷰해줘" 또는 /skill-review-pr을 요청할 때 사용합니다.
disable-model-invocation: false
allowed-tools: Bash(git:*), Bash(gh:*), Read, Glob, Grep, Task, AskUserQuestion
argument-hint: "{PR번호} [--auto-fix]"
---

# skill-review-pr: PR 리뷰

## 실행 조건
- 사용자가 `/skill-review-pr {번호}` 또는 "PR {번호} 리뷰해줘" 요청 시

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
  echo "❌ PR 번호를 지정해주세요. 예: /skill-review-pr 123"
  exit 1
fi

# [REQUIRED] 4. PR 존재 + OPEN 상태
PR_STATE=$(gh pr view $PR_NUMBER --json state --jq '.state' 2>/dev/null)
if [ "$PR_STATE" != "OPEN" ]; then
  echo "❌ PR #$PR_NUMBER 이 OPEN 상태가 아닙니다 (현재: $PR_STATE)."
  exit 1
fi

# [REQUIRED] 5. Draft가 아님
IS_DRAFT=$(gh pr view $PR_NUMBER --json isDraft --jq '.isDraft' 2>/dev/null)
if [ "$IS_DRAFT" == "true" ]; then
  echo "❌ PR #$PR_NUMBER 은 Draft 상태입니다. Ready for review 후 재시도하세요."
  exit 1
fi
```

## 명령어 옵션
```
/skill-review-pr 123           # PR 리뷰
/skill-review-pr 123 --auto-fix # CRITICAL 이슈 자동 수정 후 재리뷰
```

## 워크플로우 상태 추적

스킬 진입/완료 시 해당 Task의 `workflowState`를 업데이트한다:

**진입 시:**
```json
"workflowState": {
  "currentSkill": "skill-review-pr",
  "lastCompletedSkill": "skill-impl",
  "prNumber": {PR 번호},
  "autoChainArgs": "{--auto-fix 여부}",
  "updatedAt": "{현재 시각}"
}
```

**완료 시 (APPROVED):**
```json
"workflowState": {
  "currentSkill": "skill-merge-pr",
  "lastCompletedSkill": "skill-review-pr",
  "prNumber": {PR 번호},
  "autoChainArgs": "",
  "updatedAt": "{현재 시각}"
}
```

## 실행 플로우

### 1. PR 정보 수집
```bash
# PR 상세 정보
gh pr view 123 --json title,body,author,state,baseRefName,headRefName,files,additions,deletions

# PR 변경 내용
gh pr diff 123

# PR 체크 상태
gh pr checks 123
```

### 2. 체크리스트 검증

#### 자동 검증 항목
| 항목 | 검증 방법 | 필수 |
|------|----------|------|
| 빌드 성공 | CI 결과 확인 | ✅ |
| 테스트 통과 | CI 결과 확인 | ✅ |
| 린트 통과 | CI 결과 확인 | ⚠️ |
| 라인 수 제한 | diff 분석 | ⚠️ |
| 충돌 없음 | mergeable 확인 | ✅ |

```
## ✅ 체크리스트

- [x] 빌드 성공
- [x] 테스트 통과 (45/45)
- [x] 린트 통과
- [x] 라인 수 적정 (287 라인)
- [x] 충돌 없음
```

### 3. 5관점 병렬 리뷰 (Task sub-agent)

#### 3.1 사전 준비 (현재 세션)

**Step 1: 도메인 확인**
```bash
cat .claude/state/project.json
```
→ `domain` 필드 추출

**Step 2: PR diff 수집**
```bash
gh pr diff {number}
```
→ 변수 `{diff}`에 저장

#### 3.2 병렬 리뷰 실행

3개 전문 subagent를 **하나의 메시지에서 동시 호출**하여 병렬 실행.
각 Task는 `.claude/agents/pr-reviewer-*.md`의 지침을 Read로 로드하여 따릅니다.

**서브에이전트 호출 프로토콜 (3개 공통):**
| 항목 | 값 |
|------|-----|
| timeout | 60초 (TaskOutput timeout: 60000) |
| retry | 0회 자동 재시도 (사용자 요청 시 1회 재시도 허용) |
| fallback | "⚠️ {에이전트명} 분석 불가 — 수동 확인 필요" + 진행 |
| partial_result | 형식 불일치 시 원문 그대로 포함 + ⚠️ 마크 |

**Task 1: 🔐 보안 + 컴플라이언스**
```
Task tool (subagent_type: "general-purpose", description: "🔐 보안/컴플라이언스 리뷰"):
  prompt: |
    .claude/agents/pr-reviewer-security.md 파일을 Read로 읽고,
    해당 지침에 따라 아래 PR을 리뷰하세요.

    PR #{number}: {title}
    브랜치: {head} → {base}
    도메인: {domain}

    ## PR Diff
    {diff}
```

**Task 2: 🏛️ 도메인 + 아키텍처**
```
Task tool (subagent_type: "general-purpose", description: "🏛️ 도메인/아키텍처 리뷰"):
  prompt: |
    .claude/agents/pr-reviewer-domain.md 파일을 Read로 읽고,
    해당 지침에 따라 아래 PR을 리뷰하세요.

    PR #{number}: {title}
    브랜치: {head} → {base}
    도메인: {domain}

    ## PR Diff
    {diff}
```

**Task 3: 🧪 테스트 품질**
```
Task tool (subagent_type: "general-purpose", description: "🧪 테스트 품질 리뷰"):
  prompt: |
    .claude/agents/pr-reviewer-test.md 파일을 Read로 읽고,
    해당 지침에 따라 아래 PR을 리뷰하세요.

    PR #{number}: {title}
    브랜치: {head} → {base}
    도메인: {domain}

    ## PR Diff
    {diff}
```

#### 3.3 오류 처리

**1개 서브에이전트 실패 시:**

실패 에이전트 정보를 표시하고 AskUserQuestion으로 사용자에게 선택지 제공:

```
⚠️ 서브에이전트 실패: {에이전트명}
   원인: {타임아웃/에러 메시지}
   영향: {해당 관점} 분석 결과 누락
```

AskUserQuestion 선택지:
- **[재시도]** 해당 에이전트 1회 재실행 (재시도도 실패 시 자동 스킵)
- **[스킵]** "⚠️ {에이전트명} 분석 불가 — 수동 확인 필요" 표기 후 진행
- **[중단]** 리뷰 전체 중단

**--auto-fix 체인 모드**: 사용자 질문 없이 자동 [재시도] → 실패 시 자동 [스킵]

**결과 형식 불일치 시:**
원문 그대로 포함 + ⚠️ 마크 (사용자 선택 없이 진행)

**2개 이상 서브에이전트 실패 시:**
표준 에러 포맷 적용 (사용자 선택 없이 즉시 중단):
```
❌ 리뷰 중단: 서브에이전트 2개 이상 실패
   원인: {실패한 에이전트 목록}
   해결: 네트워크/시스템 상태 확인 후 `/skill-review-pr {number}` 재실행
```

**실행 로그 기록 (실패 시):**
execution-log.json에 `subagent_failed` 액션 추가:
```json
{
  "timestamp": "{현재 시각}",
  "taskId": "{TASK-ID}",
  "skill": "skill-review-pr",
  "action": "subagent_failed",
  "details": {"prNumber": "{number}", "failedAgent": "{에이전트명}", "reason": "{실패 원인}", "userChoice": "{재시도|스킵|중단}", "retryResult": "{성공|실패|N/A}"}
}
```

#### 3.4 결과 병합

3개 sub-agent 결과를 수집하여 통합 리뷰 테이블 생성:

| 관점 | 담당 | CRITICAL | MAJOR | MINOR |
|------|------|----------|-------|-------|
| 🔐 컴플라이언스 | pr-reviewer-security | | | |
| 🏛️ 도메인 | pr-reviewer-domain | | | |
| 🏛️ 아키텍처 | pr-reviewer-domain | | | |
| 🔐 보안 | pr-reviewer-security | | | |
| 🧪 테스트 | pr-reviewer-test | | | |

병합 규칙:
- 이슈 ID 재채번: CRITICAL → C001~, MAJOR → H001~, MINOR → M001~
- 위반 항목 통합 테이블 생성 (체크리스트, 항목, 심각도, 파일:라인)
- CRITICAL 1개 이상 → 전체 REQUEST_CHANGES

### 4. PR 코멘트 작성

#### 전체 요약 코멘트
```bash
gh pr comment 123 --body "$(cat <<EOF
## 📝 코드 리뷰 결과

### 요약
| 관점 | 상태 | 이슈 |
|------|------|------|
| 컴플라이언스 | ✅ | 0개 |
| 도메인 | ⚠️ | 2개 |
| 아키텍처 | ✅ | 0개 |
| 보안 | ✅ | 0개 |
| 테스트 | ⚠️ | 1개 |

### 체크리스트 검토 결과
**적용된 체크리스트:**
- _base: common.md, security-basic.md, architecture.md
- {domain}: {domain checklists}

**위반 항목:**
| 심각도 | 체크리스트 | 항목 | 파일 |
|--------|-----------|------|------|
| {CRITICAL/MAJOR} | {출처} | {항목명} | {파일:라인} |

### 주요 이슈
1. **[MAJOR]** 예외 처리 누락 - \`Service.kt:45\`
2. **[MINOR]** 테스트 케이스 추가 권장

### 결론
수정 사항 반영 후 재검토 요청드립니다.
EOF
)"
```

#### 인라인 코멘트 (이슈별)
```bash
gh api repos/{owner}/{repo}/pulls/123/comments \
  -f body="🟠 **MAJOR**: 예외 처리가 누락되었습니다.

\`\`\`kotlin
// 권장 수정
try {
    service.execute()
} catch (e: Exception) {
    logger.error(\"Failed to execute\", e)
    throw ServiceException(e)
}
\`\`\`" \
  -f path="src/main/kotlin/Service.kt" \
  -f line=45 \
  -f side="RIGHT"
```

### 5. 리뷰 결정

#### 승인 조건
- CRITICAL 이슈: 0개
- MAJOR 이슈: 0개 또는 논의 후 승인

#### 자기 PR 감지
```bash
# PR 작성자와 현재 사용자 비교
PR_AUTHOR=$(gh pr view {number} --json author --jq '.author.login')
CURRENT_USER=$(gh api user --jq '.login')

if [ "$PR_AUTHOR" == "$CURRENT_USER" ]; then
  IS_SELF_PR=true
else
  IS_SELF_PR=false
fi
```

#### 리뷰 제출
```bash
# 자기 PR인 경우 (GitHub 정책상 승인 불가)
if [ "$IS_SELF_PR" == "true" ]; then
  gh pr review 123 --comment --body "✅ 셀프 리뷰 완료. CRITICAL 이슈 없음."
  # 승인 SKIP → 바로 머지 진행
fi

# 다른 사람 PR인 경우
if [ "$IS_SELF_PR" == "false" ]; then
  # 승인
  gh pr review 123 --approve --body "LGTM! 코드 품질이 좋습니다."
fi

# 변경 요청 (자기/타인 무관)
gh pr review 123 --request-changes --body "위 이슈들 수정 후 재검토 요청드립니다."
```

### 5.5 실행 로그 기록

`skill-status`의 "실행 로그 프로토콜"에 따라 `.claude/state/execution-log.json`에 추가:
- APPROVED 시: `{"action": "approved", "details": {"prNumber": {number}, "criticalCount": 0}}`
- REQUEST_CHANGES 시: `{"action": "request_changes", "details": {"prNumber": {number}, "criticalCount": {N}}}`

### 6. skill-merge-pr 자동 호출 (승인 시)

**리뷰 결과가 APPROVED일 때 반드시 수행:**
```
Skill tool 사용: skill="skill-merge-pr", args="{prNumber}"
```

**조건:**
- APPROVED 상태일 때만 자동 호출
- REQUEST_CHANGES면 수정 대기 (자동 호출 안 함)

**중요:**
- 리뷰 제출 후 APPROVED 판정 시 skill-merge-pr 호출
- skill-merge-pr 호출 없이 직접 머지 진행 **금지**
- 반드시 Skill tool을 사용하여 skill-merge-pr 스킬 실행

**출력 예시 (APPROVED - 타인 PR):**
```
✅ 리뷰 완료: APPROVED
🔄 PR 머지를 자동 시작합니다...
```

**출력 예시 (APPROVED - 자기 PR):**
```
✅ 리뷰 완료: 셀프 리뷰 (승인 불필요)
📝 리뷰 코멘트 추가됨
🔄 PR 머지를 자동 시작합니다...
```

**출력 예시 (REQUEST_CHANGES):**
```
⚠️ 리뷰 완료: REQUEST_CHANGES
수정 후 `/skill-review-pr {number}` 재실행
```

### 7. 옵션별 워크플로우

#### 7.1 기본 모드 (--auto-fix 없음)

```
/skill-review-pr {number}
    │
    ├─[1] PR 정보 수집
    ├─[2] 자기 PR 여부 확인
    ├─[3] 체크리스트 검증
    ├─[4] 5관점 병렬 리뷰 (3 sub-agent)
    ├─[5] PR 코멘트 작성
    ├─[6] 리뷰 결정
    │
    ▼
┌─────────────────────────────────────┐
│         CRITICAL 이슈 존재?          │
└─────────────────────────────────────┘
    │
    ├─ YES → REQUEST_CHANGES → ⏸️ 종료
    │            └─ 출력: "수정 후 /skill-review-pr {number} 재실행"
    │
    └─ NO  → 자기 PR인가?
              │
              ├─ YES → --comment "셀프 리뷰 완료"
              │        승인 SKIP → skill-merge-pr 호출
              │
              └─ NO  → --approve "LGTM!"
                       skill-merge-pr 호출
```

**분기 조건:**
- CRITICAL 이슈 1개 이상 → REQUEST_CHANGES
- CRITICAL 이슈 0개 + 자기 PR → COMMENT 후 머지
- CRITICAL 이슈 0개 + 타인 PR → APPROVE 후 머지

#### 7.2 자동수정 모드 (--auto-fix)

```
/skill-review-pr {number} --auto-fix
    │
    ├─[1] PR 정보 수집
    ├─[2] 체크리스트 검증
    ├─[3] 5관점 병렬 리뷰 (3 sub-agent)
    │
    ▼
┌─────────────────────────────────────┐
│         CRITICAL 이슈 존재?          │
└─────────────────────────────────────┘
    │
    ├─ NO  → [4] PR 코멘트 작성
    │        [5] APPROVED
    │        [6] skill-merge-pr 호출
    │
    └─ YES → [4] skill-fix 호출 (Skill tool)
             │
             └─ skill-fix 완료 후 자동으로
                skill-review-pr 재호출됨
```

**분기 조건:**
- CRITICAL 이슈 0개 → 일반 승인 플로우
- CRITICAL 이슈 1개 이상 → skill-fix 호출

#### 7.3 skill-fix 호출 방법

**반드시 Skill tool 사용:**
```
Skill tool 사용: skill="skill-fix", args="{prNumber}"
```

**출력 (skill-fix 호출 시):**
```
⚠️ CRITICAL 이슈 {N}개 발견
🔧 자동 수정을 시작합니다...
🔄 `/skill-fix {number}` 실행 중...
```

**금지 사항:**
- --auto-fix 시 직접 코드 수정 금지
- skill-fix 없이 REQUEST_CHANGES 후 종료 금지

## 출력 포맷

```
## 🔍 PR 리뷰: #{number}

### PR 정보
- **제목**: {제목}
- **작성자**: {author}
- **브랜치**: {head} → {base}
- **변경**: +{additions} / -{deletions}

### 체크리스트
- [x] 빌드 성공
- [x] 테스트 통과
- [ ] 린트 통과 ⚠️
- [x] 라인 수 적정

### 리뷰 결과
| 관점 | 상태 | CRITICAL | MAJOR | MINOR |
|------|------|----------|-------|-------|
| 컴플라이언스 | ✅ | 0 | 0 | 0 |
| 도메인 | ⚠️ | 0 | 1 | 1 |
| 아키텍처 | ✅ | 0 | 0 | 1 |
| 보안 | ✅ | 0 | 0 | 0 |
| 테스트 | ⚠️ | 0 | 1 | 0 |

### 주요 피드백
1. 🟠 **[M001]** {파일}:{라인} - {설명}
2. 🟡 **[m001]** {파일}:{라인} - {설명}

### 결정
- **리뷰 결과**: {APPROVED | Request Changes}
- **필수 수정**: {N}개
- **선택 수정**: {N}개

### 자동 진행 (APPROVED 시)
🔄 `/skill-merge-pr {number}` 자동 실행 중...

### 다음 단계 (REQUEST_CHANGES 시)
수정 후 `/skill-review-pr {number}` 재실행
```

## 에이전트 활용

PR 리뷰 시 3개 전문 subagent를 병렬 호출합니다:

| subagent | 파일 | 관점 | 도구 |
|----------|------|------|------|
| pr-reviewer-security | `.claude/agents/pr-reviewer-security.md` | 1️⃣ + 4️⃣ | Read, Glob, Grep |
| pr-reviewer-domain | `.claude/agents/pr-reviewer-domain.md` | 2️⃣ + 3️⃣ | Read, Glob, Grep |
| pr-reviewer-test | `.claude/agents/pr-reviewer-test.md` | 5️⃣ | Read, Glob, Grep |

각 subagent는 독립 컨텍스트에서 실행되며, 체크리스트를 직접 Read하여 로드합니다.
PR diff는 호출 시 프롬프트에 포함되어 전달됩니다.

## 주의사항
- PR이 Draft 상태면 리뷰 불가
- CI 실패 시 리뷰 보류 권장
- CRITICAL 이슈는 반드시 수정 필요
- auto-fix는 신중하게 사용
- **자기 PR은 GitHub 정책상 승인 불가 → COMMENT로 대체 후 머지 진행**
