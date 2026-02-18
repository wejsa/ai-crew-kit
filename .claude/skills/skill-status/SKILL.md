---
name: skill-status
description: 프로젝트 상태 확인 - 현재 작업 진행상황, 백로그 요약, Git 상태, 시스템 건강 점검
disable-model-invocation: true
allowed-tools: Bash(git:*), Bash(gh:*), Bash(python3:*), Read, Glob
argument-hint: "[--health|--locks]"
---

# skill-status: 프로젝트 상태 확인

## 실행 조건
- 사용자가 `/skill-status` 또는 "상태 확인해줘" 요청 시

## 명령어 옵션
```
/skill-status            # 기본 상태 확인
/skill-status --locks    # 병렬 작업 잠금 현황 포함
/skill-status --health   # 시스템 건강 점검
```

## 실행 플로우

### 1. Git 상태 확인
```bash
git branch --show-current
git status --short
git log --oneline -5
```

### 2. 프로젝트 설정 확인
`.claude/state/project.json` 파일에서:
- **도메인**: 현재 프로젝트 도메인 (fintech, ecommerce, general 등)
- **기술 스택**: 백엔드, 프론트엔드, DB 등
- **활성 에이전트**: 사용 가능한 에이전트 목록
- **Kit 버전**: kitVersion 필드 (미기록 시 "미설정" 표시)

### 3. 백로그 상태 요약
`.claude/state/backlog.json` 파일에서:
- **todo**: 대기 중인 Task 수
- **in_progress**: 진행 중인 Task (Task ID, 제목, 현재 스텝)
- **done**: 완료된 Task 수

### 4. 계획 파일 확인
`.claude/temp/` 디렉토리에서 진행 중인 계획 파일 확인

### 4.5 워크플로우 상태 점검

`backlog.json`의 `in_progress` Task에서 `workflowState`를 확인:

**Stale 감지 기준**: `workflowState.updatedAt`이 30분 이상 경과

```
### 워크플로우 상태
| Task | 현재 스킬 | PR | 마지막 갱신 | 상태 |
|------|----------|-----|-----------|------|
| TASK-001 | skill-review-pr | #42 | 5분 전 | 🔄 정상 |
| TASK-003 | skill-impl | - | 45분 전 | ⚠️ Stale |
```

**Stale 감지 시 복구 안내:**
```
⚠️ TASK-003의 워크플로우가 45분간 미갱신 (stale)

마지막 상태:
- 현재 스킬: skill-impl
- 이전 완료: skill-plan
- PR: 없음

복구 방법:
1. `/skill-impl` — 중단된 구현 재개
2. `/skill-backlog update TASK-003 --status=todo` — Task 초기화
```

### 5. 활성 PR 상태

```bash
gh pr list --state open --json number,title,reviewDecision,statusCheckRollup,headRefName --limit 10
```

```
### 활성 PR
| PR | 제목 | 브랜치 | 리뷰 | CI |
|----|------|--------|------|-----|
| #42 | feat: TASK-001 Step 1 | feature/TASK-001-step1 | ✅ APPROVED | ✅ |
| #43 | feat: TASK-002 Step 1 | feature/TASK-002-step1 | ⏳ PENDING | 🔄 |
```

### 5.5 시스템 건강 점검 (--health 옵션)

`/skill-status --health` 실행 시 추가 점검:

```bash
# JSON 유효성 검증
for f in .claude/state/*.json .claude/domains/_registry.json; do
  python3 -c "import sys,json; json.load(open('$f'))" 2>/dev/null || echo "❌ $f"
done

# 필수 파일 존재 확인
REQUIRED_FILES=(
  ".claude/state/project.json"
  ".claude/domains/_registry.json"
  ".claude/schemas/project.schema.json"
  ".claude/schemas/backlog.schema.json"
  ".claude/templates/CLAUDE.md.tmpl"
  "CLAUDE.md"
)

# 스킬 디렉토리 완전성
ls .claude/skills/*/SKILL.md

# Git 원격 동기화 상태
git fetch --dry-run origin 2>&1
```

```
### 시스템 건강 상태

| 항목 | 상태 | 상세 |
|------|------|------|
| JSON 유효성 | ✅ | 8/8 파일 정상 |
| 필수 파일 | ✅ | 6/6 존재 |
| 스킬 디렉토리 | ✅ | 15/15 SKILL.md 존재 |
| Git 원격 동기화 | ⚠️ | 2 커밋 behind origin/develop |
| 도메인 레지스트리 | ✅ | 3 도메인 정상 |
| 실행 로그 | ✅ | 최근 47건 |
| backlog-completed 정합성 | ✅ | 일치 |
```

#### backlog-completed 정합성 검증

```bash
# backlog.json에서 status=="done"인 Task ID 목록
# completed.json에서 Task ID 목록
# 차이가 있으면:
#   ⚠️ 정합성 불일치: backlog done {N}건 중 completed.json 미기록 {M}건
#   → /skill-merge-pr 실행 시 자동 복구됩니다.
```

```
### backlog-completed 정합성
⚠️ 정합성 불일치: backlog done 15건 중 completed.json 미기록 2건
  - TASK-005: backlog done, completed.json 누락
  - TASK-011: backlog done, completed.json 누락
→ /skill-merge-pr 실행 시 자동 복구됩니다.
```

#### Orphan Intent 감지

`.claude/temp/` 디렉토리에서 `*-complete-intent.json` 파일을 검색:

```bash
ls .claude/temp/*-complete-intent.json 2>/dev/null
```

**Intent 파일 발견 시:**
```
### Orphan Intent 감지
⚠️ 미완료 Task 완료 처리 발견: {N}건

| Task ID | 액션 | 생성 시각 | pending 항목 |
|---------|------|----------|-------------|
| TASK-005 | task_complete | 2026-02-18 14:30 | backlog.json, plan-file |

→ 다음 스킬 실행 시 자동 복구됩니다.
→ 즉시 복구: `/skill-merge-pr` 실행
```

**Intent 파일 없음 시:**
```
| Orphan Intent | ✅ | 미완료 처리 없음 |
```

각 intent 파일의 `pending` 배열을 읽어 미처리 항목 수를 표시합니다.

**문제 발견 시:**
```
### 시스템 건강 상태

⚠️ 문제 발견: 2건

1. ❌ backlog.json — JSON 파싱 실패
   → `/skill-validate --fix` 실행 또는 수동 수정

2. ⚠️ Git 원격 동기화 — 3 커밋 behind
   → `git pull origin develop` 실행 권장
```

### 6. 출력 포맷

```
## 📊 프로젝트 상태

### 프로젝트 설정
- **도메인**: {도메인명} ({도메인ID})
- **기술 스택**: {백엔드} / {프론트엔드} / {DB}
- **활성 에이전트**: {에이전트 목록}
- **Task 접두사**: {taskPrefix}
- **Kit 버전**: v{kitVersion} (kitVersion 미기록 시 "미설정" 표시)

### Git 상태
- **현재 브랜치**: {브랜치명}
- **최근 커밋**: {커밋 메시지}
- **변경 파일**: {수}개

### 백로그 요약
| 상태 | 수량 |
|------|------|
| 📋 대기 (todo) | {N}개 |
| 🔄 진행 중 (in_progress) | {N}개 |
| ✅ 완료 (done) | {N}개 |

### 진행 중인 작업
- **{Task ID}**: {제목}
  - 현재 스텝: Step {N}/{Total}
  - 브랜치: feature/{Task ID}-step{N}

### 다음 단계 추천
- `/skill-plan`: 새 작업 시작
- `/skill-impl`: 현재 스텝 개발 진행
- `/skill-impl --next`: 다음 스텝 진행
```

### 병렬 작업 현황 (--locks 옵션)

`/skill-status --locks` 실행 시 추가 출력:

```
### 현재 진행 중인 Task

| Task ID | 제목 | 담당자 | 스텝 | 잠금 파일 | 상태 |
|---------|------|--------|------|----------|------|
| TASK-001 | JWT 서비스 | dev@PC1-... | 2/3 | 3개 | 🔄 정상 |
| TASK-003 | Rate Limiter | qa@PC2-... | 1/2 | 2개 | ⚠️ 만료임박 |
| TASK-005 | 캐시 설정 | dev@PC3-... | 1/1 | 1개 | 🔴 만료 (1h 초과) |

### 잠금 상세

**TASK-001** (dev@DESKTOP-ABC-20260203-143052)
- 할당: 2026-02-03 14:30 (1시간 23분 전)
- 잠금 파일:
  - src/domain/jwt/JwtService.kt
  - src/domain/jwt/TokenValidator.kt
  - src/infrastructure/security/JwtFilter.kt

**TASK-005** 🔴 만료
- 할당: 2026-02-03 10:15 (5시간 38분 전)
- ⚠️ lockTTL 초과 - 인계 가능 (동적 TTL: lockedFiles 수 기반)
- 잠금 파일:
  - src/config/CacheConfig.kt
```

### 만료 표시 기준

| 상태 | 조건 | 아이콘 |
|------|------|--------|
| 정상 | 남은시간 > 30분 | 🔄 |
| 만료임박 | 남은시간 <= 30분 | ⚠️ |
| 만료 | lockTTL 초과 (동적: 1~3시간) | 🔴 |

### 6. 실행 로그 확인

`.claude/state/execution-log.json` 파일이 존재하면 최근 실행 이력 표시:

```
### 최근 실행 이력 (최근 10건)
| 시각 | Task | 스킬 | 액션 | 상세 |
|------|------|------|------|------|
| 14:30 | TASK-001 | skill-impl | pr_created | PR #42 |
| 14:25 | TASK-001 | skill-review-pr | approved | CRITICAL: 0 |
| 14:20 | TASK-001 | skill-merge-pr | merged | PR #41 |
```

## 실행 로그 프로토콜

### 로그 파일
`.claude/state/execution-log.json` (append-only JSON array)

### 형식
```json
[
  {
    "timestamp": "2026-02-15T14:30:00Z",
    "taskId": "TASK-001",
    "skill": "skill-impl",
    "action": "pr_created",
    "details": {"prNumber": 42, "stepNumber": 1}
  }
]
```

### 스킬별 로그 항목

| 스킬 | action | details |
|------|--------|---------|
| skill-impl | `started`, `pr_created` | `{stepNumber, prNumber}` |
| skill-review-pr | `review_started`, `approved`, `request_changes` | `{prNumber, criticalCount}` |
| skill-fix | `fix_started`, `fix_completed` | `{prNumber, issueCount}` |
| skill-merge-pr | `merge_started`, `merged`, `task_completed` | `{prNumber, stepNumber}` |
| skill-retro | `retro_started`, `retro_completed`, `checklist_updated` | `{reportFile}`, `{files}` |
| skill-hotfix | `hotfix_started`, `hotfix_completed` | `{description}`, `{hotfixId, prNumber, version}` |
| skill-rollback | `rollback_started`, `rollback_completed` | `{target}`, `{revertSha, prNumber, version}` |

### 쓰기 규칙
- 각 스킬 완료 시 로그 항목 1개 추가 (append)
- 파일 미존재 시 `[]`로 생성
- 500건 초과 시 아카이브 로테이션 실행 (아래 참조)

### 아카이브 로테이션

실행 로그가 500건을 초과하면 자동으로 정리:

```
1. 현재 execution-log.json 읽기
2. 최근 200건만 유지 (배열 끝에서 200개)
3. 나머지(오래된 항목)를 아카이브 파일로 이동:
   .claude/state/execution-log-archive-{YYYYMMDD}.json
4. execution-log.json을 최근 200건으로 덮어쓰기
5. 30일 이상 된 아카이브 파일 삭제:
   find .claude/state/ -name "execution-log-archive-*.json" -mtime +30 -delete
```

**로테이션 실행 시점**: 모든 스킬의 로그 쓰기 직후, 건수 확인 → 500건 초과 시 자동 실행.
별도 스킬 호출 불필요.

### 읽기 규칙
- `skill-status`에서 최근 10건 표시
- 기존 `completed.json`, `backlog.json`과 보완 관계 (대체 아님)

## 주의사항
- 읽기 전용 작업만 수행
- 상태 파일이 없으면 초기 상태로 간주
- 문제 발견 시 `.claude/docs/troubleshooting.md` 참조 안내
