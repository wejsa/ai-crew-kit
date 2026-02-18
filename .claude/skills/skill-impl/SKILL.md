---
name: skill-impl
description: 구현 - 스텝별 개발 + PR 생성
disable-model-invocation: false
allowed-tools: Bash(git:*), Bash(./gradlew:*), Bash(npm:*), Bash(yarn:*), Read, Write, Edit, Glob, Grep, Task
argument-hint: "[--next|--all]"
---

# skill-impl: 구현

## 실행 조건
- 사용자가 `/skill-impl` 또는 "개발 진행해줘" 요청 시
- 사전 조건: 계획 파일 존재 + Task 상태 `in_progress`

## 명령어 옵션
```
/skill-impl          # 현재 스텝 개발
/skill-impl --next   # 다음 스텝 개발 (이전 PR 머지 확인)
/skill-impl --all    # 모든 스텝 연속 개발
```

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

# [REQUIRED] 3. in_progress Task 존재
# backlog.json에서 status: in_progress인 Task가 있어야 함

# [REQUIRED] 4. 계획 파일 존재: .claude/temp/{taskId}-plan.md
if [ ! -f ".claude/temp/${TASK_ID}-plan.md" ]; then
  echo "❌ 계획 파일이 없습니다. /skill-plan을 먼저 실행하세요."
  exit 1
fi

# [REQUIRED] 5. 현재 스텝 상태: pending
# backlog.json에서 steps[currentStep].status == "pending"

# [REQUIRED] 6. origin/develop 동기화 검증
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

### --next 사용 시 추가 조건
- [REQUIRED] 이전 스텝 PR이 머지되어 있어야 함
- [REQUIRED] develop 최신 상태 동기화 (worktree 시 merge origin/develop)

## Intent 복구 (사전 점검)

스킬 진입 시 `.claude/temp/*-complete-intent.json` 파일이 존재하면:
1. `skill-merge-pr`의 "Intent 기반 복구" 절차에 따라 미완료 처리를 먼저 복구
2. 복구 완료 후 정상 플로우 진행
3. "⚠️ 이전 세션의 미완료 처리를 복구했습니다: {taskId}" 출력

## 워크플로우 상태 추적

스킬 진입/완료 시 해당 Task의 `workflowState`를 업데이트한다:

**진입 시:**
```json
"workflowState": {
  "currentSkill": "skill-impl",
  "lastCompletedSkill": "{이전 스킬}",
  "prNumber": null,
  "autoChainArgs": "{--next|--all 등}",
  "updatedAt": "{현재 시각}"
}
```

**완료 시 (PR 생성 후):**
```json
"workflowState": {
  "currentSkill": "skill-review-pr",
  "lastCompletedSkill": "skill-impl",
  "prNumber": {생성된 PR 번호},
  "autoChainArgs": "{--auto-fix}",
  "updatedAt": "{현재 시각}"
}
```

## 실행 플로우

### 1. 환경 준비
```bash
# develop 최신 상태 동기화
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
GIT_COMMON_DIR=$(git rev-parse --git-common-dir 2>/dev/null)
if [ "$GIT_DIR" != "$GIT_COMMON_DIR" ]; then
  # Worktree 모드: 현재 브랜치(CS브랜치)를 feature 브랜치로 직접 사용
  git fetch origin develop
  git merge origin/develop
else
  git checkout develop
  git pull origin develop
  # 스텝 브랜치 생성
  git checkout -b feature/{taskId}-step{N}
fi
```

### 2. 계획 파일 참조
참고자료 로드 순서:
1. 도메인 참고자료 (`.claude/domains/{domain}/docs/`)
2. 공통 컨벤션 (`.claude/domains/_base/conventions/`)
3. 계획 파일 (`.claude/temp/{taskId}-plan.md`)

`.claude/temp/{taskId}-plan.md`에서 현재 스텝 내용 확인:
- 생성/수정할 파일 목록
- 구현 내용 상세
- 테스트 항목

### 3. 코드 구현
계획에 따라 코드 작성:
- 파일 생성/수정
- 테스트 코드 작성
- 문서 업데이트 (필요 시)

### 4. 라인 수 검증
```bash
git diff --stat
```

| 라인 수 | 처리 |
|---------|------|
| < 300 | ✅ 진행 |
| 300~500 | ⚠️ 경고 표시 후 진행 |
| 500~700 | ⚠️ 강력 경고 + 사용자 확인 |
| > 700 | ❌ 차단 - 스텝 분리 필요 |

### 5. 빌드 & 테스트

**스택별 빌드 명령** (`.claude/state/project.json`의 `techStack.backend` 참조):

| 스택 | 빌드 | 테스트 | 린트 |
|------|------|--------|------|
| spring-boot-kotlin | `./gradlew build` | `./gradlew test` | `./gradlew ktlintCheck` |
| spring-boot-java | `./gradlew build` | `./gradlew test` | `./gradlew checkstyleMain` |
| nodejs-typescript | `npm run build` | `npm test` | `npm run lint` |
| go | `go build ./...` | `go test ./...` | `golangci-lint run` |

```bash
# Spring Boot (Kotlin) 예시
./gradlew build
./gradlew test
./gradlew ktlintCheck
```

실패 시:
- 오류 분석 및 수정
- 재실행
- 3회 실패 시 사용자에게 보고

### 5.5 의존성 취약점 검사 (선택적)

빌드 성공 후, 프로젝트에 의존성 관리 도구가 있으면 취약점 검사 실행:

| 스택 | 명령 | 조건 |
|------|------|------|
| nodejs-typescript | `npm audit --audit-level=high` | package-lock.json 존재 |
| spring-boot-* | `./gradlew dependencyCheckAnalyze` (OWASP) | 플러그인 설정 시 |
| go | `govulncheck ./...` | govulncheck 설치 시 |

**동작 규칙:**
- 도구 미설치/미설정 시 조용히 스킵 (빌드 차단 안 함)
- HIGH/CRITICAL 취약점 발견 시 경고 표시 + PR body에 포함
- 취약점이 빌드를 차단하지는 않음 (정보 제공 목적)

```
### 의존성 취약점 검사
⚠️ 취약점 발견: HIGH 2개, CRITICAL 0개
- lodash@4.17.20: Prototype Pollution (HIGH)
- express@4.17.1: Open Redirect (HIGH)

권장: `npm audit fix` 또는 수동 업데이트
```

### 6. 커밋 & 푸시
```bash
git add .
git commit -m "feat: {taskId} Step {N} - {스텝 제목}"
if [ "$GIT_DIR" != "$GIT_COMMON_DIR" ]; then
  git push -u origin HEAD
else
  git push -u origin feature/{taskId}-step{N}
fi
```

### 7. PR 생성

#### 7.1 PR body 템플릿 로드

**Layered Override:** 도메인 템플릿(`.claude/domains/{domain}/templates/pr-body.md.tmpl`)이 있으면 우선 사용, 없으면 기본 템플릿(`.claude/templates/pr-body.md.tmpl`) 사용.

#### 7.2 마커 치환

| 마커 | 값 |
|------|-----|
| `{{TASK_TITLE}}` | 현재 Task 제목 (backlog.json) |
| `{{STEP_NUMBER}}` | 현재 스텝 번호 |
| `{{STEP_TOTAL}}` | 전체 스텝 수 |
| `{{CHANGES_LIST}}` | `git diff --stat` 기반 변경 사항 bullet 목록 |

치환 후 남은 `{{...}}` 패턴은 빈 문자열로 대체.

#### 7.3 PR 생성
```bash
gh pr create \
  --base develop \
  --title "feat: {taskId} Step {N} - {스텝 제목}" \
  --body "{치환된 PR body}"
```

### 8. 상태 업데이트

**backlog.json 쓰기 시 반드시 `skill-backlog`의 "backlog.json 쓰기 프로토콜" 준수:**
- `metadata.version` 1 증가 + `metadata.updatedAt` 갱신
- 쓰기 후 JSON 유효성 검증 필수

`backlog.json` 업데이트:
```json
{
  "steps": [
    {"number": 1, "status": "pr_created", "prNumber": 123}
  ]
}
```

### 8.5 실행 로그 기록

`skill-status`의 "실행 로그 프로토콜"에 따라 `.claude/state/execution-log.json`에 추가:
```json
{"timestamp": "{현재시각}", "taskId": "{taskId}", "skill": "skill-impl", "action": "pr_created", "details": {"prNumber": {number}, "stepNumber": {N}}}
```

### 9. skill-review-pr 자동 호출

**PR 생성 완료 후 반드시 수행:**
```
Skill tool 사용: skill="skill-review-pr", args="{prNumber} --auto-fix"
```

**중요:**
- PR 생성 및 상태 업데이트 후 skill-review-pr 호출
- skill-review-pr 호출 없이 직접 리뷰 진행 **금지**
- 반드시 Skill tool을 사용하여 skill-review-pr 스킬 실행

**출력 예시:**
```
✅ PR #{number} 생성 완료
🔄 코드 리뷰를 자동 시작합니다...
```

### 10. 문서 영향도 분석 (백그라운드 Task)

PR 생성 후 skill-review-pr 호출과 동시에 docs-impact-analyzer 백그라운드 실행:

```
Task tool (subagent_type: "general-purpose", run_in_background: true, description: "📝 문서 영향도 분석"):
  prompt: |
    .claude/agents/docs-impact-analyzer.md 파일을 Read로 읽고,
    해당 지침에 따라 아래 PR을 분석하세요.

    PR #{number} ({title})의 변경 파일을 분석하여
    문서 업데이트 필요 여부를 판단하세요.

    ## 변경 파일
    {git diff --stat 결과}
```

**동작 규칙:**
- skill-review-pr 호출과 **병렬 실행** (메인 플로우 차단 금지)
- 분석 완료 후 문서 업데이트 필요 시 출력에 `📝 문서 업데이트 권장` 알림 포함
- Task 실패 시 무시하고 진행 (백그라운드이므로 메인 플로우 영향 없음)

### 10.5 테스트 품질 분석 (백그라운드 Task)

`.claude/state/project.json`의 `agents.enabled`에 `"qa"`가 포함된 경우에만 실행합니다.

PR 생성 후 docs-impact-analyzer와 함께 **병렬 백그라운드** 실행:

```
Task tool (subagent_type: "general-purpose", run_in_background: true, description: "🟢 테스트 품질 분석"):
  prompt: |
    .claude/agents/agent-qa.md 파일을 Read로 읽고,
    해당 지침에 따라 아래 PR의 테스트 품질을 분석하세요.

    PR #{number} ({title})
    도메인: {domain}

    ## 변경 파일
    {git diff --stat 결과}
```

**동작 규칙:**
- docs-impact-analyzer와 **동시에 병렬 실행** (메인 플로우 차단 금지)
- `run_in_background: true` 사용
- Task 실패 시 무시하고 진행 (백그라운드이므로 메인 플로우 영향 없음)
- agents.enabled에 미포함 시: Task 호출 스킵

## 출력 포맷

```
## 🚀 구현 완료: {Task ID} Step {N}

### 변경 사항
- 생성: {N}개 파일
- 수정: {N}개 파일
- 삭제: {N}개 파일
- 총 라인: +{added} / -{removed}

### 검증 결과
- ✅ 빌드 성공
- ✅ 테스트 통과 ({N}/{N})
- ✅ 린트 통과

### PR 생성
🔗 PR #{number}: {제목}
   {PR URL}

### 백그라운드 분석
📝 문서 영향도: {필요/불필요}
🧪 테스트 품질: {분석 완료/스킵} (agents.enabled에 qa 포함 시)

### 자동 진행
🔄 `/skill-review-pr {number} --auto-fix` 자동 실행 중...

### 전체 워크플로우
1. ✅ PR 생성 완료
2. 🔄 `/skill-review-pr --auto-fix` - 코드 리뷰 + 자동 수정 (자동)
3. ⏳ `/skill-merge-pr` - PR 머지
4. ⏳ `/skill-impl --next` - 다음 스텝

---
남은 스텝: {N}개
```

## --all 옵션 플로우
모든 스텝을 사용자 개입 없이 연속 실행:
```
Step 1 개발 → PR 생성 → [skill-review-pr --auto-fix + docs 분석] → skill-merge-pr → 자동 진행
  ↓
Step 2 개발 → PR 생성 → [skill-review-pr --auto-fix + docs 분석] → skill-merge-pr → 자동 진행
  ↓
(반복)
  ↓
마지막 스텝 완료 → Task 완료 처리
```

### 자동 진행 원칙
- 각 스텝 완료 후 사용자 확인 없이 다음 스텝으로 자동 진행
- 개별 스킬 간 체이닝 규칙을 그대로 따름:
  - skill-impl → skill-review-pr --auto-fix (PR 생성 후 자동)
  - skill-review-pr → skill-merge-pr (APPROVED 시 자동)
  - skill-merge-pr → skill-impl --next (남은 스텝 시 자동)

### 중단 조건 (이 경우에만 멈추고 사용자에게 보고)
- CRITICAL 이슈 auto-fix 실패
- 빌드 실패 (3회 재시도 후)
- 라인 수 700 초과 (스텝 분리 필요)

## 에러 처리

### 빌드 실패 시
```
## ❌ 빌드 실패

### 에러 내용
{에러 메시지}

### 분석
{원인 분석}

### 수정 방안
{수정 방법}

수정 후 재시도하시겠습니까? (Y/N)
```

### 라인 수 초과 시
```
## ⚠️ 라인 수 초과 경고

현재 변경: {N} 라인 (권장: 500 미만)

### 권장 조치
현재 스텝을 분리하는 것을 권장합니다:
- Step {N}-1: {내용}
- Step {N}-2: {내용}

분리하시겠습니까? (Y/N/무시하고 계속)
```

## lockedFiles 관리

### 갱신 시점

| 시점 | 액션 |
|------|------|
| 스텝 시작 | 계획된 파일을 `lockedFiles`에 추가 |
| 파일 수정 | 실제 수정 파일로 `lockedFiles` 갱신 |
| 스텝 완료 (PR 생성) | `lockedFiles` 유지 (머지 전까지) |
| `assignedAt` 갱신 | 작업 중 자동 연장 |

### 갱신 로직

```
스텝 시작 시:
1. 현재 스텝의 files 배열 → lockedFiles에 추가
2. assignedAt 현재 시각으로 갱신
3. Git 커밋 & 푸시

파일 수정 시:
1. 실제 수정된 파일 감지 (git diff --name-only)
2. 현재 스텝 files에 없는 파일 → lockedFiles에 추가
3. 현재 스텝 files 갱신

스텝 완료 시 (PR 생성):
1. steps[currentStep].status = "pr_created"
2. lockedFiles 유지 (머지까지 보호)
3. Git 커밋 & 푸시
```

### assignedAt 연장

장시간 작업 시 잠금 만료 방지:
- 코드 수정/커밋 시 자동으로 `assignedAt` 갱신
- 명시적 연장: `/skill-impl --extend-lock` → `lockTTL`에 +3600초 추가 (최대 14400초=4시간)

**동적 TTL 참조**: `skill-backlog`의 "동적 TTL" 규칙에 따라 `lockTTL` 값이 결정됨.
스텝 전환 시(다음 스텝 시작) lockedFiles 수 변경에 맞춰 `lockTTL`도 재산정.

## 주의사항
- 계획 파일 없이 구현 진행 금지
- 라인 수 제한 준수
- 빌드/테스트 통과 필수
- PR 생성 후 리뷰 진행
- 병렬 작업 시 파일 충돌 주의
