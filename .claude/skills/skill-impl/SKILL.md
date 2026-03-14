---
name: skill-impl
description: 구현 - 스텝별 개발 + PR 생성. 사용자가 "개발 진행해줘", "구현해줘" 또는 /skill-impl을 요청할 때 사용합니다.
disable-model-invocation: false
allowed-tools: Bash(git:*), Bash(./gradlew:*), Bash(npm:*), Bash(yarn:*), Read, Write, Edit, Glob, Grep, Task
argument-hint: "[--next|--all]"
---

# skill-impl: 구현

## 실행 조건
- 사용자가 `/skill-impl` 또는 "개발 진행해줘" 요청 시
- `--next`: 다음 스텝 (이전 PR 머지 확인 필수)
- `--all`: 모든 스텝 연속 실행

## 사전 조건 (MUST-EXECUTE-FIRST — 하나라도 실패 시 STOP)
1. project.json 존재
2. backlog.json 존재 + 유효 JSON
3. in_progress Task 존재
4. 계획 파일 `.claude/temp/{taskId}-plan.md` 존재
5. 현재 스텝 status == pending
6. origin/develop 동기화: >5 뒤처짐 → STOP, 1-5 → 자동 merge
- `--next` 추가 조건: 이전 스텝 PR 머지 완료 + develop 최신 동기화

## 경량 점검
CLAUDE.md "경량 점검 프로토콜" 3단계 실행: ①PR-backlog 일치 ②Stale 감지 ③Intent 복구

## 워크플로우 진행 표시
CLAUDE.md 진행 표시 프로토콜. 현재 단계: "코드 구현 중 (Step {N}/{total} — {스텝명})"

## 워크플로우 상태 추적
CLAUDE.md 상태 추적 패턴. currentSkill="skill-impl"

## 컨벤션 로딩
계획 파일의 "참조 컨벤션" 필드 → Read로 로드. 없으면 CLAUDE.md 트리거 테이블로 자동 식별.

## 실행 플로우

### 1. 환경 준비
CLAUDE.md 워크트리 프로토콜 참조.
- **일반 모드**: develop checkout + pull → `feature/{taskId}-step{N}` 브랜치 생성
  - 브랜치 이미 존재 시: PR MERGED → 다음 Step 스킵, OPEN → 기존 브랜치에서 이어서 작업
- **워크트리 모드**: CS 브랜치 직접 사용, fetch + merge origin/develop
- merge 후 step 재검증: backlog.json 재읽기 → done/merged면 스킵, 다른 세션 in_progress면 경고

### 2. 계획 파일 참조
로드 순서: 도메인 참고자료 → 공통 컨벤션 → 계획 파일. 현재 스텝의 파일/구현/테스트 확인.

### 3. 코드 구현
계획에 따라 파일 생성/수정, 테스트 작성, 문서 업데이트(필요 시)

### 4. 라인 수 검증
`project.json`의 `conventions.workflowProfile` 확인:

| 프로필 | 진행 | 경고 | 차단 |
|--------|------|------|------|
| standard | <300 | 300-500 / 500-700(강력) | >700 |
| fast | <500 | 500-1000 | >1000 |

### 5. 빌드 & 테스트
`project.json`의 `buildCommands` 우선 → 미설정 시 `techStack` 기반 폴백:

| 스택 | 빌드 | 테스트 | 린트 |
|------|------|--------|------|
| spring-boot-kotlin | `./gradlew build` | `./gradlew test` | `./gradlew ktlintCheck` |
| nodejs-typescript | `npm run build` | `npm test` | `npm run lint` |
| go | `go build ./...` | `go test ./...` | `golangci-lint run` |

실패 시 수정 후 재실행, 3회 실패 시 사용자 보고.

### 5.5 의존성 취약점 검사 (선택)
빌드 성공 후, 도구 존재 시만 실행 (미설치 시 스킵). HIGH/CRITICAL 발견 → 경고 + PR body 포함. 빌드 차단 안 함.

### 6. 커밋 & 푸시
CLAUDE.md 워크트리 프로토콜 참조. push 전 develop 동기화 필수.
- 커밋: `feat: {taskId} Step {N} - {스텝 제목}`
- push 실패 시: pull --rebase → backlog.json 충돌은 서로 다른 Task 모두 유지, `metadata.version = max + 1` → 재시도 (최대 2회)

### 7. PR 생성
1. PR body 템플릿: 도메인 `.claude/domains/{domain}/templates/pr-body.md.tmpl` 우선 → 기본 템플릿 폴백
2. 마커 치환: `{{TASK_TITLE}}`, `{{STEP_NUMBER}}`, `{{STEP_TOTAL}}`, `{{CHANGES_LIST}}`
3. `gh pr create --base develop --title "feat: {taskId} Step {N} - {제목}" --body "{치환된 body}"`

### 8. 상태 업데이트
`skill-backlog` 쓰기 프로토콜 준수 (metadata.version +1, JSON 검증 필수).
step status → "pr_created", prNumber 기록. assignedAt 갱신 (lock heartbeat).

### 8.5 실행 로그
`.claude/state/execution-log.json`에 추가: action="pr_created", prNumber, stepNumber

### 9. 다음 스킬 호출 (프로필별)
- **standard**: `Skill tool: skill="skill-review-pr", args="{prNumber} --auto-fix"`
- **fast**: `Skill tool: skill="skill-merge-pr", args="{prNumber}"` (review 생략)
- 직접 리뷰/머지 금지. 반드시 Skill tool 사용.

### 10. 백그라운드 분석 (PR 생성 후 병렬)
| 분석 | 조건 | 서브에이전트 | timeout |
|------|------|-------------|---------|
| 문서 영향도 | 항상 | docs-impact-analyzer | 60초 |
| 테스트 품질 | agents.enabled에 "qa" 포함 | agent-qa | 60초 |

각 Task `run_in_background: true`. 실패 시 "⚠️ 분석 불가" 출력 후 진행.

## --all 옵션
모든 스텝 연속 실행: impl → review-pr → merge-pr → impl --next (반복)
중단 조건: CRITICAL auto-fix 실패, 빌드 3회 실패, 라인 수 초과

## lockedFiles 관리
- 스텝 시작: 계획 파일의 files → lockedFiles 추가 + assignedAt 갱신
- 파일 수정: 실제 수정 파일 감지 → lockedFiles/files 갱신
- 스텝 완료: lockedFiles 유지 (머지 전까지 보호)
- 장시간 작업: 코드 수정/커밋 시 assignedAt 자동 갱신. 동적 TTL은 skill-backlog 참조.

## 출력
필수 포함: Task ID, Step N/M, 변경 파일 수(생성/수정/삭제), 빌드/테스트/린트 결과, PR 링크, 백그라운드 분석 결과, 다음 자동 스킬, 남은 스텝 수

## 주의사항
- 계획 파일 없이 구현 금지
- 빌드/테스트 통과 필수
- 병렬 작업 시 파일 충돌 주의
