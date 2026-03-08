---
name: skill-plan
description: 계획 수립 - Task 선택 + 설계 분석 + 스텝 분리 계획. 사용자가 "다음 작업 가져와", "계획 세워줘" 또는 /skill-plan을 요청할 때 사용합니다.
disable-model-invocation: false
allowed-tools: Bash(git:*), Read, Write, Glob, Grep, Task
argument-hint: "[taskId]"
---

# skill-plan: 계획 수립

## 실행 조건
- 사용자가 `/skill-plan` 또는 "다음 작업 가져와" 요청 시
- 특정 Task 지정: `/skill-plan {taskId}`

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

# [REQUIRED] 3. origin/develop 동기화 검증
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

## 경량 점검

MUST-EXECUTE-FIRST 완료 후, 워크플로우 진행 표시 전에 실행한다.
CLAUDE.md의 "스킬 진입 시 경량 점검 프로토콜" 상세 절차를 따르되, 핵심 3단계:

1. **PR-backlog 상태 일치 확인**: step.prNumber가 있고 step.status == "pr_created"면
   `gh pr view {prNumber} --json state,mergedAt`으로 확인 → MERGED면 done 보정, CLOSED면 pending 보정
   (네트워크 실패 시 스킵)
2. **Stale workflow 감지**: workflowState.updatedAt < 30분 전이면
   AskUserQuestion으로 "이어서 진행 / 처음부터 / 다른 Task" 선택지 제공
3. **Intent 파일 복구**: `.claude/temp/*-complete-intent.json` 존재하면
   skill-merge-pr "Intent 기반 복구" 절차로 미완료 처리 복구 후 파일 삭제

## 워크플로우 진행 표시

경량 점검 완료 후, 다음 진행바를 출력한다:
- Task의 workflowState 읽기
- "설계 분석 및 스텝 분리 중"으로 현재 단계 표시
- steps가 없는 초기 상태면: `⬜ plan → ⬜ impl → ⬜ review → ⬜ merge` 출력
- CLAUDE.md의 "워크플로우 진행 표시 프로토콜" 포맷을 따른다

## 과거 학습 반영

경량 점검 완료 후, 워크플로우 진행 표시 후, 실행 플로우 시작 전에 수행한다.

### 절차

1. `.claude/state/lessons-learned.json` 존재 확인 → 없으면 스킵
2. 존재하면 파일 Read
3. 현재 Task의 도메인/키워드와 관련된 학습 항목 필터링:
   - `tags`가 현재 Task의 요구사항 키워드와 매칭되는 항목
   - `impact`가 "high"인 항목 우선
   - 최대 5개까지 선별
4. 선별된 항목을 설계 분석 시 참고사항으로 반영:

```
━━━ 📚 과거 학습 반영 ━━━━━━━━━━━━━━━━
 관련 학습 {N}건 발견:
 • [L-001] {제목} (quality, high) — 적용 {N}회
 • [L-003] {제목} (architecture, medium)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

5. 설계 분석(섹션 3)과 스텝 분리(섹션 4)에서 관련 학습 항목을 고려하여 계획 수립
6. 계획 파일에 "참고 학습 항목" 섹션 추가

**학습 항목 없음 시:** 출력 없이 정상 진행 (스킵)

## 실행 플로우

### 1. Task 선택

**자동 선택 기준** (taskId 미지정 시):
1. `status: todo` 인 Task 중
2. `dependencies` 모두 충족된 Task 중
3. `lockedFiles` 충돌 없는 Task 중
4. `priority` 높은 순서대로
5. 같은 우선순위면 `phase` 낮은 순서

**선택 불가 조건**:
- 의존성 미충족 Task는 `blocked` 표시
- 같은 파일을 수정하는 `in_progress` Task 존재 시 경고

**병렬 작업 가능 조건**:
- 의존성 체인에 없는 Task
- 다른 `in_progress` Task의 `lockedFiles`와 겹치지 않음

### 1.5 조기 잠금 (중복 선택 방지)

Task 선택 직후, 다른 세션의 중복 선택을 방지하기 위해 **즉시** backlog.json을 업데이트하고 push한다.

**1단계: backlog.json 업데이트**
```json
{
  "status": "in_progress",
  "assignee": "{user}@{hostname}-{YYYYMMDD-HHmmss}",
  "assignedAt": "{ISO 8601 timestamp}",
  "lockTTL": 1800,
  "lockedFiles": [],
  "updatedAt": "{timestamp}"
}
```
- `lockTTL: 1800` (30분) — planning 전용 TTL. 승인 후 동적 TTL로 갱신됨
- `lockedFiles: []` — 아직 스텝 분리 전이므로 비어있음
- `metadata.version` 1 증가 + `metadata.updatedAt` 갱신

**2단계: Git push** (하단 "Git 동기화 프로토콜" 절차 준수)
- 커밋 메시지: `chore: claim {TASK-ID}`

**3단계: Push 실패 시 충돌 해소**
- `git pull --rebase` 후 선택한 Task의 remote 상태 확인
- 해당 Task가 이미 다른 세션에 의해 `in_progress`이면:
  → 로컬 변경 취소 (`git checkout -- .claude/state/backlog.json`)
  → **섹션 1로 돌아가 다음 우선순위 Task 재선택**
- 해당 Task가 여전히 `todo`이면: 정상 push 재시도

**4단계: 출력**
```
🔒 {TASK-ID} 선점 완료 — 다른 세션에서 선택 불가
```

**Push 성공 확인 후에만 다음 단계(섹션 2)로 진행한다.** Push 미확인 상태로 진행 금지.

### 2. 요구사항 확인
선택된 Task의 `specFile` 읽기:
```
docs/requirements/{taskId}-spec.md
```

### 3.0 DB 설계 분석 (병렬 Task)

`.claude/state/project.json`의 `agents.enabled`에 `"db-designer"`가 포함된 경우에만 실행합니다.

**실행 방법:**
- 섹션 3의 설계 분석과 **병렬로** Task tool 호출 (`run_in_background: true`)
- Task tool (subagent_type: "general-purpose")로 agent-db-designer 실행
- 섹션 3 완료 후 Task 결과를 수거하여 계획 파일의 "데이터 모델" 섹션에 통합

**호출 패턴:**

```
Task tool (subagent_type: "general-purpose", run_in_background: true, description: "🟠 DB 설계 분석"):
  prompt: |
    .claude/agents/agent-db-designer.md 파일을 Read로 읽고,
    해당 지침에 따라 아래 요구사항의 DB 설계를 분석하세요.

    도메인: {domain}
    요구사항: {specFile 내용 요약}
```

**서브에이전트 호출 프로토콜:**
| 항목 | 값 |
|------|-----|
| timeout | 60초 (TaskOutput timeout: 60000) |
| retry | 0회 (재시도 없이 1회 실행) |
| fallback | "⚠️ DB 설계 분석 불가 — 수동 확인 필요" + 메인 컨텍스트에서 직접 작성 |
| partial_result | 형식 불일치 시 원문 그대로 포함 + ⚠️ 마크 |

**결과 수거:**
- 섹션 3 설계 분석 완료 후 TaskOutput(timeout: 60000)으로 db-designer Task 결과 확인
- 결과가 준비되면 계획 파일의 "데이터 모델" 섹션에 통합

**오류 처리:**
- Task 실패/타임아웃 시: 계획 파일에 "⚠️ DB 설계 분석 불가 — 수동 확인 필요" 표기 후 진행
- Task 결과 형식 불일치 시: 원문 그대로 포함 + ⚠️ 마크
- agents.enabled에 미포함 시: Task 호출 스킵, 메인 컨텍스트에서 직접 작성

### 3. 설계 분석
요구사항 기반으로 분석:

**도메인 템플릿 참조**:
- `.claude/state/project.json`에서 현재 도메인 확인
- `.claude/domains/{domain}/templates/` 디렉토리에서 관련 템플릿 활용
- `.claude/domains/_base/templates/`의 공통 템플릿 참조

#### 3.1 컴포넌트 설계
- 생성/수정할 파일 목록
- 각 파일의 역할과 책임
- 패키지/모듈 구조

#### 3.2 시퀀스 다이어그램
- 주요 플로우 시각화
- 컴포넌트 간 상호작용

#### 3.3 API 설계 (해당 시)
- 엔드포인트 정의
- 요청/응답 스키마
- 에러 코드

#### 3.4 데이터 모델
- 엔티티/DTO 정의
- 관계 설계

### 4. 스텝 분리 계획
**분리 기준**:
- 각 스텝 **500라인 미만**
- 논리적 단위로 분리
- 각 스텝은 독립적으로 빌드/테스트 가능

**스텝 구조**:
```
Step 1: {제목}
- 파일: {파일 목록}
- 참조 컨벤션: {관련 컨벤션 파일명 목록}
- 예상 라인: {N}
- 내용: {상세 설명}

Step 2: {제목}
- 파일: {파일 목록}
- 참조 컨벤션: {관련 컨벤션 파일명 목록}
- 예상 라인: {N}
- 내용: {상세 설명}
- 의존: Step 1
```

**참조 컨벤션 자동 식별**: CLAUDE.md의 "도메인 컨벤션 참조" 트리거 테이블을 참고하여 각 Step의 작업 내용에 매칭되는 컨벤션을 자동 식별한다. skill-impl이 해당 컨벤션을 Read로 로드하여 코딩 표준을 준수한다.

### 4.5 파일 충돌 검사

계획 수립 완료 후, 다른 `in_progress` Task와 파일 충돌 검사:

1. 스텝별 수정 예정 파일 목록 추출
2. backlog.json의 다른 `in_progress` Task `lockedFiles` 조회
3. 교집합 검사

**충돌 없음**: 정상 진행

**충돌 발생 시**:
```
⚠️ 파일 충돌 경고

다음 파일이 다른 Task에서 수정 중입니다:
- src/auth/JwtService.kt
  └── TASK-002 (dev@OTHER-PC-20260203-100000) Step 2 진행 중

옵션:
1. 순차 처리 - 해당 Task 완료 대기 (권장)
2. 강제 진행 ⚠️
   - 머지 시 수동 충돌 해결 필요
   - 같은 파일 동시 수정으로 코드 손실 가능
   - 정말 진행하시겠습니까? ("yes" 입력)
```

**강제 진행 시**: 계획 파일에 충돌 경고 명시

---

### 5. 계획 파일 생성
`.claude/temp/{taskId}-plan.md` 생성:

```markdown
# {Task ID}: {제목} - 개발 계획

## 요구사항 요약
{요구사항 핵심 내용}

## 설계

### 컴포넌트 구조
```
{패키지/파일 구조}
```

### 시퀀스 다이어그램
```mermaid
sequenceDiagram
{다이어그램}
```

### API 설계
{API 정의}

### 데이터 모델
{모델 정의}

## 스텝별 계획

### Step 1: {제목}
- **파일**: {파일 목록}
- **예상 라인**: {N}
- **내용**:
  - {작업 1}
  - {작업 2}
- **테스트**:
  - {테스트 항목}

### Step 2: {제목}
...

## 예상 일정
- 전체 스텝: {N}개
- 예상 PR: {N}개

## 리스크 & 고려사항
- {리스크 1}
- {리스크 2}
```

### 6. 사용자 검토/승인 요청
- 설계와 스텝 계획 제시
- 수정 의견 수렴
- **승인 받을 때까지 개발 진행하지 않음**

**거절/취소 시 롤백:**
1. backlog.json 업데이트:
   ```json
   {
     "status": "todo",
     "assignee": null,
     "assignedAt": null,
     "lockTTL": null,
     "lockedFiles": []
   }
   ```
   - `metadata.version` 1 증가 + `metadata.updatedAt` 갱신
2. Git push (하단 "Git 동기화 프로토콜" 절차 준수)
   - 커밋 메시지: `chore: release {TASK-ID}`
3. 출력: `🔓 {TASK-ID} 잠금 해제 — 다른 세션에서 선택 가능`
4. 사용자에게 다음 옵션 제시:
   - 다른 Task 선택 (`/skill-plan`)
   - 종료

### 7. 상태 업데이트 (승인 후)

> `status`, `assignee`는 섹션 1.5(조기 잠금)에서 이미 설정됨. 여기서는 **파일 잠금 + 스텝 정보만 갱신**.

`backlog.json` 업데이트:
```json
{
  "assignedAt": "{현재 ISO 8601 timestamp}",
  "lockTTL": 3600,
  "lockedFiles": ["src/auth/JwtService.kt", "src/auth/TokenValidator.kt"],
  "steps": [
    {"number": 1, "title": "...", "status": "pending", "files": ["JwtService.kt"]},
    {"number": 2, "title": "...", "status": "pending", "files": ["TokenValidator.kt"]}
  ],
  "currentStep": 1,
  "updatedAt": "{timestamp}"
}
```
- `assignedAt` 갱신: TTL 기준점을 승인 시점으로 리셋 (planning 중 경과 시간 제외)

**lockTTL 산정** (`skill-backlog`의 "동적 TTL" 규칙 참조):
```
lockedFiles 수에 따라:
- ≤ 3개 → lockTTL = 3600  (1시간)
- 4~8개 → lockTTL = 7200  (2시간)
- ≥ 9개 → lockTTL = 10800 (3시간)
```

### 8. skill-impl 자동 호출

**"Y" 승인 시 반드시 수행:**
```
Skill tool 사용: skill="skill-impl"
```

**중요:**
- backlog.json 업데이트 후 skill-impl 호출
- skill-impl 호출 없이 직접 개발 진행 **금지**
- 반드시 Skill tool을 사용하여 skill-impl 스킬 실행

**출력 예시:**
```
✅ 계획 승인 완료
🔄 Step 1 개발을 자동 시작합니다...
```

## 출력 포맷

```
## 📋 계획 수립: {Task ID}

### 선택된 Task
- **ID**: {taskId}
- **제목**: {제목}
- **Phase**: {phase}
- **우선순위**: {priority}

### 설계 요약
{설계 핵심 내용}

### 스텝 계획
| Step | 제목 | 예상 라인 | 주요 파일 |
|------|------|----------|----------|
| 1 | {제목} | {N} | {파일} |
| 2 | {제목} | {N} | {파일} |

### 계획 파일
📄 `.claude/temp/{taskId}-plan.md` 생성 완료

---
설계와 스텝 계획을 검토해주세요.
승인하시면 개발을 시작합니다.

승인하시겠습니까?

> Y: 상태 업데이트 후 `/skill-impl` 자동 실행 (Step 1 시작)
> N: 계획 거절 — Task 잠금 해제 후 종료
> 수정사항 입력: 해당 부분만 반영하여 계획 수정 (예: "Step 2 파일 분리해줘", "API 응답 형식 변경")
```

## 라인 수 가이드라인
| 예상 라인 | 상태 | 조치 |
|----------|------|------|
| < 300 | ✅ 양호 | 진행 |
| 300~500 | ⚠️ 주의 | 가능하면 분리 권장 |
| > 500 | ❌ 초과 | 반드시 분리 |

## Git 동기화 프로토콜

**backlog.json 쓰기 시 반드시 `skill-backlog`의 "backlog.json 쓰기 프로토콜" 준수:**
- `metadata.version` 1 증가 + `metadata.updatedAt` 갱신
- 쓰기 후 JSON 유효성 검증 필수
- 검증 실패 시 `git checkout -- .claude/state/backlog.json`으로 롤백

상태 업데이트 시:
```bash
# Worktree 감지
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
GIT_COMMON_DIR=$(git rev-parse --git-common-dir 2>/dev/null)

if [ "$GIT_DIR" != "$GIT_COMMON_DIR" ]; then
  # Worktree 모드
  git fetch origin develop
  git merge origin/develop
  git add .claude/state/backlog.json
  git commit -m "chore: start TASK-001"
  git push -u origin HEAD
else
  # 일반 모드
  git pull origin develop --rebase
  git add .claude/state/backlog.json
  git commit -m "chore: start TASK-001"
  git push origin develop
fi

# 푸시 실패 시 (충돌)
git pull --rebase
# 충돌 해소 후, 선택한 Task의 remote 상태 확인:
# - 같은 Task가 이미 다른 세션에 의해 in_progress → 로컬 변경 취소 + 재선택
# - 서로 다른 Task 변경 → 두 변경 모두 유지 (정상 머지)
if [ "$GIT_DIR" != "$GIT_COMMON_DIR" ]; then
  git push -u origin HEAD
else
  git push origin develop
fi
```

## 주의사항
- 계획 파일은 Git에서 제외됨 (`.claude/temp/`)
- 계획 승인 전 코드 작성 금지
- 의존성 있는 스텝은 순서 명시
- 각 스텝은 PR 생성 단위
- 병렬 작업 시 `lockedFiles` 충돌 주의
