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

## 사전 조건 검증

### 필수 조건
1. **계획 파일 존재**: `.claude/temp/{taskId}-plan.md`
2. **Task 상태**: `in_progress`
3. **현재 스텝**: `pending` 상태

### --next 사용 시 추가 조건
- 이전 스텝 PR이 머지되어 있어야 함
- develop 최신 상태 동기화 (worktree 시 merge origin/develop)

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
`backlog.json` 업데이트:
```json
{
  "steps": [
    {"number": 1, "status": "pr_created", "prNumber": 123}
  ]
}
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

### 문서 분석 (백그라운드)
📝 문서 업데이트 {필요/불필요}

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
- 명시적 연장: `/skill-impl --extend-lock`

## 주의사항
- 계획 파일 없이 구현 진행 금지
- 라인 수 제한 준수
- 빌드/테스트 통과 필수
- PR 생성 후 리뷰 진행
- 병렬 작업 시 파일 충돌 주의
