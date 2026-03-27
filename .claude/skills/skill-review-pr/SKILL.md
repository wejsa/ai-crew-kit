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
- `--auto-fix`: CRITICAL 이슈 자동 수정 후 재리뷰

## 사전 조건 (MUST-EXECUTE-FIRST — 하나라도 실패 시 STOP)
1. project.json 존재
2. backlog.json 존재 + 유효 JSON
3. PR 번호 지정됨
4. PR 존재 + OPEN 상태 (`gh pr view --json state`)
5. Draft 아님

## 경량 점검
CLAUDE.md "경량 점검 프로토콜" 3단계 실행: ①PR-backlog 일치 ②Stale 감지 ③Intent 복구

## 워크플로우 진행 표시
CLAUDE.md 진행 표시 프로토콜. 현재 단계: "코드 리뷰 중 (보안/도메인/테스트 3관점)"

## 워크플로우 상태 추적
CLAUDE.md 상태 추적 패턴. currentSkill="skill-review-pr"

## 리뷰 전 컨벤션 로딩
1. PR 변경 파일 확인 (`gh pr view {N} --json files`)
2. CLAUDE.md 트리거 테이블로 매칭 컨벤션 식별
3. 도메인 체크리스트 Read: `_base/checklists/common.md`(필수) + `{domain}/checklists/`

## 실행 플로우

### 1. PR 정보 수집
`gh pr view {N} --json title,body,author,state,baseRefName,headRefName,files,additions,deletions`
`gh pr diff {N}`, `gh pr checks {N}`

### 2. 체크리스트 검증
| 항목 | 검증 방법 | 필수 |
|------|----------|------|
| 빌드 성공 | CI 결과 | ✅ |
| 테스트 통과 | CI 결과 | ✅ |
| 린트 통과 | CI 결과 | ⚠️ |
| 라인 수 제한 | diff 분석 | ⚠️ |
| 충돌 없음 | mergeable | ✅ |

### 3. 5관점 병렬 리뷰 (3 sub-agent)
도메인 확인 + PR diff 수집 후, **하나의 메시지에서 3개 Task 동시 호출**:

| sub-agent | 파일 | 관점 |
|-----------|------|------|
| pr-reviewer-security | `.claude/agents/pr-reviewer-security.md` | 보안 + 컴플라이언스 |
| pr-reviewer-domain | `.claude/agents/pr-reviewer-domain.md` | 도메인 + 아키텍처 |
| pr-reviewer-test | `.claude/agents/pr-reviewer-test.md` | 테스트 품질 |

각 Task: Read로 agent 파일 로드 후 지침에 따라 리뷰. PR diff는 프롬프트에 포함.

| 항목 | 값 |
|------|-----|
| timeout | 60초 |
| retry | 0회 (--auto-fix 시 자동 1회 재시도 후 스킵) |
| fallback | "⚠️ {에이전트명} 분석 불가 — 수동 확인 필요" |

**오류 처리**:
- 1개 실패: AskUserQuestion (재시도/스킵/중단). --auto-fix 시 자동 재시도→실패시 스킵
- 2개+ 실패: 즉시 중단

### 4. 결과 병합
이슈 ID 재채번: CRITICAL→C001~, MAJOR→H001~, MINOR→M001~
위반 항목 통합 테이블 (체크리스트, 항목, 심각도, 파일:라인)
CRITICAL 1개 이상 → 전체 REQUEST_CHANGES

### 5. PR 코멘트 작성
`gh pr comment` — 전체 요약 (관점별 상태/이슈 수, 체크리스트 결과, 주요 피드백)
`gh api repos/.../pulls/{N}/comments` — 이슈별 인라인 코멘트 (심각도, 설명, 권장 수정 코드)

### 6. 리뷰 결정
**자기 PR 감지**: PR author == 현재 user → 승인 불가, COMMENT로 대체
- CRITICAL 0개 + 타인 PR → `gh pr review --approve`
- CRITICAL 0개 + 자기 PR → `gh pr review --comment` (승인 SKIP)
- CRITICAL 1개+ → `gh pr review --request-changes`

### 6.5 실행 로그
execution-log.json: APPROVED → action="approved", REQUEST_CHANGES → action="request_changes"

### 7. 다음 스킬

#### 기본 모드
- APPROVED → `Skill tool: skill="skill-merge-pr", args="{prNumber}"`
- REQUEST_CHANGES → 종료, "수정 후 재실행" 안내

#### --auto-fix 모드
- CRITICAL 0개 → 일반 승인 플로우
- CRITICAL 1개+ → workflowState.fixLoopCount 증가 후 `Skill tool: skill="skill-fix", args="{prNumber}"`
  - fixLoopCount 3회째 CRITICAL → skill-fix 호출 금지, REQUEST_CHANGES 즉시 중단 (루프 가드)
  - 직접 코드 수정 금지. skill-fix 없이 REQUEST_CHANGES 후 종료 금지.

## 출력
필수 포함: PR 번호/제목/작성자/브랜치, 체크리스트 결과, 관점별 리뷰 테이블(CRITICAL/MAJOR/MINOR 수), 주요 피드백 목록, 결정(APPROVED/REQUEST_CHANGES), 다음 자동 스킬

## 주의사항
- Draft PR은 리뷰 불가
- CRITICAL 이슈는 반드시 수정 필요
- 자기 PR은 GitHub 정책상 승인 불가 → COMMENT 후 머지 진행
