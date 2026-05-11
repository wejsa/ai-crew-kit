# 스킬 레퍼런스

> [← README로 돌아가기](../README.md)

## 자주 사용하는 명령어

| 명령어 | 설명 | 자연어 예시 |
|--------|------|------------|
| `/skill-status` | 프로젝트 상태 확인 | "상태 확인해줘" |
| `/skill-feature` | 새 기능 기획 | "새 기능 기획해줘" |
| `/skill-plan` | 설계 및 스텝 계획 | "다음 작업 가져와줘" |
| `/skill-impl` | 코드 구현 + PR 생성 | "개발 진행해줘" |
| `/skill-review-pr` | PR 리뷰 | "PR 123 리뷰해줘" |
| `/skill-merge-pr` | PR 머지 | "PR 123 머지해줘" |
| `/skill-retro` | 완료 Task 회고 | "회고 해줘" |
| `/skill-hotfix` | main 긴급 수정 | "긴급 수정해줘" |
| `/skill-rollback` | 릴리스 롤백 | "v1.2.3 롤백해줘" |
| `/skill-report` | 프로젝트 메트릭 리포트 | "리포트 생성해줘" |
| `/skill-health-check` | 코드베이스 건강 검진 | "헬스체크 해줘" |

## 스킬 티어 (사용 빈도 기준)

| 티어 | 스킬 | 설명 |
|------|------|------|
| 🔵 **일상 (Daily)** | status, plan, impl, review-pr, merge-pr, hotfix | 매일 사용하는 핵심 워크플로우 |
| 🟢 **주간 (Weekly)** | feature, backlog, report, health-check, retro | 주기적 관리 + 분석 |
| ⚙️ **설정 (Setup)** | init, onboard, domain, upgrade, create, estimate, docs, validate | 초기 설정 + 확장 |

> 처음이라면 **일상 티어 6개**만 익히면 됩니다. 나머지는 필요할 때 참조하세요.

## 전체 명령어 목록

### 프로젝트 관리 ⚙️

| 명령어 | 설명 |
|--------|------|
| `/skill-init` | 프로젝트 초기화 (**v2.1+** 요구사항 우선 플로우: 자유 서술 → LLM 도메인/스택 추천 → 백로그 자동 분해 opt-in. ai-crew-kit clone 감지 시 kit 잔여 자동 정리) |
| `/skill-init --quick` | 제로 결정 빠른 초기화 (디렉토리명 매칭 → 파일 감지 → 빈 백로그) |
| `/skill-init --reset` | 기존 설정 초기화 (`.claude/temp/reset-backup-{ts}-{pid}/`로 자동 백업 + `MANIFEST.txt` 체크섬 기록) |
| `/skill-status` | 현재 상태 확인 |
| `/skill-status --health` | 시스템 건강 점검 |
| `/skill-status --health --fix` | 건강 점검 + Orphan 자동 복구 |
| `/skill-health-check` | 코드베이스 건강 검진 (점수 + 등급) |
| `/skill-health-check --quick` | CRITICAL 항목만 빠른 검사 |
| `/skill-health-check --scope {카테고리}` | 특정 카테고리만 검사 |
| `/skill-health-check --fix` | 자동 수정 포함 검사 |
| `/skill-backlog` | 백로그 조회/관리 |
| `/skill-onboard` | 기존 프로젝트에 AI Crew Kit 적용 (kit clone 감지 시 자동 정리) |
| `/skill-onboard --scan-only` | 스캔만 수행 (설정 생성 없음) |

> **ai-crew-kit clone 자동 정리** (`/skill-init`, `/skill-onboard` 공통): origin URL 정규식 + initial commit fingerprint 둘 다 일치 + 더티/미푸시/비-main 가드 통과 시 kit 잔여 14종(`CHANGELOG.md`, `docs/`, `examples/`, `tests/`, `scripts/`, `.github/`, `memory/`, `LICENSE`, `README.md`, `CLAUDE.md`, `VERSION`, `.claude/temp/`, `.claude/hooks/tests/`, `.claude/state/`, `.claude/settings.local.json`)을 추가 확인 없이 자동 삭제. README.md/CLAUDE.md/VERSION은 Step 10에서 사용자 프로젝트용으로 새로 생성. 가드 미통과 시 정리 SKIP하고 일반 진행 (kit 개발자 환경 보호).
>
> **v2.1+ 요구사항 우선 플로우** (`/skill-init` 일반 모드): Step 2 요구사항 자유 서술 → Step 3 lean 시 최대 3질문 → Step 4 메타 자동 결정(+sanitization) → Step 5 LLM 추천 + 차순위 → Step 6~8 에이전트/프로필 → Step 9 백로그 자동 분해 (opt-in, Phase 4-카테고리 + Hard limits ≤30 + 컴플라이언스 priority 강제). 입력 신뢰 경계 섹션이 prompt injection 방어. 재현성 표 (결정적 vs 경험적 관측 분리). 자세히는 [skill-init/SKILL.md](https://github.com/wejsa/ai-crew-kit/blob/main/.claude/skills/skill-init/SKILL.md) 참조.

### 개발 워크플로우 🔵

| 명령어 | 설명 |
|--------|------|
| `/skill-feature` | 새 기능 기획 |
| `/skill-plan` | 설계 + 스텝 계획 수립 |
| `/skill-impl` | 코드 구현 (스텝별) |
| `/skill-impl --next` | 다음 스텝 진행 |
| `/skill-review` | 코드 리뷰 |
| `/skill-review-pr {번호}` | PR 리뷰 |
| `/skill-review-pr {번호} --auto-fix` | PR 리뷰 + CRITICAL 이슈 자동 수정 |
| `/skill-review-pr {번호} --mode standard` | standard 모드로 리뷰 (일회성) |
| `/skill-review-pr config` | 리뷰 모드 설정 확인 |
| `/skill-review-pr config --mode standard` | 프리셋 변경 (domain+security) |
| `/skill-review-pr config --mode full` | 프리셋 변경 (전체 3 에이전트) |
| `/skill-review-pr config --agents domain,test` | 커스텀 에이전트 조합 |
| `/skill-review-pr config --reset` | 디폴트(full) 복원 |
| `/skill-fix {번호}` | CRITICAL 이슈 수정 |
| `/skill-merge-pr {번호}` | PR 머지 |

### 운영/인프라 🔵

| 명령어 | 설명 |
|--------|------|
| `/skill-hotfix "{설명}"` | main 긴급 수정 |
| `/skill-rollback {태그\|PR번호}` | 릴리스/PR 롤백 |
| `/skill-release` | 버전 릴리스 |

### 분석/문서 🟢

| 명령어 | 설명 |
|--------|------|
| `/skill-docs` | 참고자료 조회 |
| `/skill-retro` | 완료 Task 회고 |
| `/skill-retro {TASK-ID}` | 특정 Task 회고 |
| `/skill-retro --summary` | 전체 회고 요약 |
| `/skill-report` | 프로젝트 메트릭 리포트 |
| `/skill-report --full` | 전체 히스토리 리포트 |
| `/skill-estimate` | 작업 복잡도 추정 |

### 설정/확장 ⚙️

| 명령어 | 설명 |
|--------|------|
| `/skill-domain` | 도메인 관리 |
| `/skill-domain list` | 도메인 목록 조회 |
| `/skill-domain switch {도메인}` | 도메인 전환 |
| `/skill-domain add-doc {경로}` | 참고자료 추가 |
| `/skill-domain add-checklist {경로}` | 체크리스트 추가 |
| `/skill-create` | 커스텀 스킬 생성 |
| `/skill-upgrade` | 프레임워크 업그레이드 |
| `/skill-upgrade --dry-run` | 변경 사항 미리보기 |
| `/skill-validate` | 업그레이드 후 검증 |

## 자연어 매핑

명령어를 모르더라도 자연어로 요청할 수 있습니다:

| 자연어 | 매핑되는 스킬 |
|--------|-------------|
| "새 기능 기획해줘" | `/skill-feature` |
| "다음 작업 가져와줘" | `/skill-plan` |
| "개발 진행해줘" | `/skill-impl` |
| "PR 123 리뷰해줘" | `/skill-review-pr 123` |
| "PR 123 머지해줘" | `/skill-merge-pr 123` |
| "상태 확인해줘" | `/skill-status` |
| "회고 해줘" | `/skill-retro` |
| "리포트 생성해줘" | `/skill-report` |
| "작업량 추정해줘" | `/skill-estimate` |
| "긴급 수정해줘" | `/skill-hotfix` |
| "v1.2.3 롤백해줘" | `/skill-rollback v1.2.3` |
| "참고자료 보여줘" | `/skill-docs` |
| "스킬 만들어줘" | `/skill-create` |
| "프로젝트 온보딩해줘" | `/skill-onboard` |
| "헬스체크 해줘" | `/skill-health-check` |
| "정리해줘" | `/skill-health-check --fix` |

## 어떤 검증 도구를 사용해야 하나요?

| 상황 | 명령어 | 소요 시간 |
|------|--------|----------|
| 매일 세션 시작할 때 | `/skill-status --health` | ~5초 |
| "뭔가 이상한데?" 싶을 때 | `/skill-health-check --quick` | ~15초 |
| 릴리스 전 전수 점검 | `/skill-health-check` | ~30초 |
| 프레임워크 업그레이드 후 | `/skill-validate` (자동 실행됨) | ~10초 |
| 문제를 수정할 때 | `/skill-health-check --fix` | ~30초 |
| 주간 팀 리포트 | `/skill-report` | ~30초 |
