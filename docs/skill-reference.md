# 스킬 레퍼런스

> [← README로 돌아가기](../README.md)

## 자주 사용하는 명령어

| 명령어 | 설명 | 자연어 예시 |
|--------|------|------------|
| `/aick-status` | 프로젝트 상태 확인 | "상태 확인해줘" |
| `/aick-feature` | 새 기능 기획 | "새 기능 기획해줘" |
| `/aick-plan` | 설계 및 스텝 계획 | "다음 작업 가져와줘" |
| `/aick-impl` | 코드 구현 + PR 생성 | "개발 진행해줘" |
| `/aick-review-pr` | PR 리뷰 | "PR 123 리뷰해줘" |
| `/aick-merge-pr` | PR 머지 | "PR 123 머지해줘" |
| `/aick-retro` | 완료 Task 회고 | "회고 해줘" |
| `/aick-hotfix` | main 긴급 수정 | "긴급 수정해줘" |
| `/aick-rollback` | 릴리스 롤백 | "v1.2.3 롤백해줘" |
| `/aick-report` | 프로젝트 메트릭 리포트 | "리포트 생성해줘" |
| `/aick-health-check` | 코드베이스 건강 검진 | "헬스체크 해줘" |

## 스킬 티어 (사용 빈도 기준)

| 티어 | 스킬 | 설명 |
|------|------|------|
| 🔵 **일상 (Daily)** | status, plan, impl, review-pr, merge-pr, hotfix | 매일 사용하는 핵심 워크플로우 |
| 🟢 **주간 (Weekly)** | feature, backlog, report, health-check, retro | 주기적 관리 + 분석 |
| ⚙️ **설정 (Setup)** | init, onboard, upgrade, create, estimate, docs, validate | 초기 설정 + 확장 |

> 처음이라면 **일상 티어 6개**만 익히면 됩니다. 나머지는 필요할 때 참조하세요.

## 전체 명령어 목록

### 프로젝트 관리 ⚙️

| 명령어 | 설명 |
|--------|------|
| `/aick-init` | 프로젝트 초기화 (**v2.1+** 요구사항 우선 플로우: 자유 서술 → LLM 스택 추천 → 백로그 자동 분해 opt-in. ai-crew-kit clone 감지 시 kit 잔여 자동 정리) |
| `/aick-init --quick` | 제로 결정 빠른 초기화 (디렉토리명 매칭 → 파일 감지 → 빈 백로그) |
| `/aick-init --reset` | 기존 설정 초기화 (`.claude/temp/reset-backup-{ts}-{pid}/`로 자동 백업 + `MANIFEST.txt` 체크섬 기록) |
| `/aick-status` | 현재 상태 확인 |
| `/aick-status --health` | 시스템 건강 점검 |
| `/aick-status --health --fix` | 건강 점검 + Orphan 자동 복구 |
| `/aick-health-check` | 코드베이스 건강 검진 (점수 + 등급) |
| `/aick-health-check --quick` | CRITICAL 항목만 빠른 검사 |
| `/aick-health-check --scope {카테고리}` | 특정 카테고리만 검사 |
| `/aick-health-check --fix` | 자동 수정 포함 검사 |
| `/aick-backlog` | 백로그 조회/관리 |
| `/aick-onboard` | 기존 프로젝트에 AI Crew Kit 적용 (kit clone 감지 시 자동 정리) |
| `/aick-onboard --scan-only` | 스캔만 수행 (설정 생성 없음) |

> **ai-crew-kit clone 자동 정리** (`/aick-init`, `/aick-onboard` 공통): origin URL 정규식 + initial commit fingerprint 둘 다 일치 + 더티/미푸시/비-main 가드 통과 시 kit 잔여 14종(`CHANGELOG.md`, `docs/`, `examples/`, `tests/`, `scripts/`, `.github/`, `memory/`, `LICENSE`, `README.md`, `CLAUDE.md`, `VERSION`, `.claude/temp/`, `.claude/hooks/tests/`, `.claude/state/`, `.claude/settings.local.json`)을 추가 확인 없이 자동 삭제. README.md/CLAUDE.md/VERSION은 Step 10에서 사용자 프로젝트용으로 새로 생성. 가드 미통과 시 정리 SKIP하고 일반 진행 (kit 개발자 환경 보호).
>
> **v2.1+ 요구사항 우선 플로우** (`/aick-init` 일반 모드): Step 2 요구사항 자유 서술 → Step 3 lean 시 최대 3질문 → Step 4 메타 자동 결정(+sanitization) → Step 5 LLM 스택 추천 + 차순위 → Step 6~8 에이전트/프로필 → Step 9 백로그 자동 분해 (opt-in, Phase 4-카테고리 + Hard limits ≤30 + priority 반영). 입력 신뢰 경계 섹션이 prompt injection 방어. 재현성 표 (결정적 vs 경험적 관측 분리). 자세히는 [aick-init/SKILL.md](https://github.com/wejsa/ai-crew-kit/blob/main/.claude/skills/aick-init/SKILL.md) 참조.

### 개발 워크플로우 🔵

| 명령어 | 설명 |
|--------|------|
| `/aick-feature` | 새 기능 기획 |
| `/aick-plan` | 설계 + 스텝 계획 수립 |
| `/aick-impl` | 코드 구현 (스텝별) |
| `/aick-impl --next` | 다음 스텝 진행 |
| `/aick-review` | 비-PR 로컬 코드 리뷰 (지정 경로 — 머지 게이트·결정 기록과 무관. PR 리뷰는 `/aick-review-pr`) |
| `/aick-review-pr {번호}` | PR 리뷰 (v2.3+: PR 특성 기반 자동 Tier 분류 + confidence 채점) |
| `/aick-review-pr {번호} --auto-fix` | PR 리뷰 + CRITICAL 이슈 자동 수정 |
| `/aick-review-pr {번호} --mode standard` | standard 모드로 리뷰 (일회성, 자동 Tier 분류 우회) |
| `/aick-review-pr config` | 리뷰 모드 설정 확인 (review 섹션 유무에 따라 자동 분류/명시 설정 표시) |
| `/aick-review-pr config --mode standard` | 프리셋 변경 (아키텍처·로직+보안, 에이전트 슬롯: domain+security) |
| `/aick-review-pr config --mode full` | 프리셋 변경 (전체 3 에이전트) |
| `/aick-review-pr config --agents architecture,test` | 커스텀 에이전트 조합 (architecture 슬롯 = 아키텍처·로직 리뷰어, 레거시 `domain` 별칭도 허용) |
| `/aick-review-pr config --reset` | `review` 섹션 삭제 (자동 Tier 분류 활성화) |
| `/aick-fix {번호}` | CRITICAL 이슈 수정 |
| `/aick-merge-pr {번호}` | PR 머지 |

#### v2.3+ 자동 Tier 분류 (`review` 미설정 디폴트)

`project.json`에 `review.mode`/`review.agents` 명시 안 하면 PR 특성으로 sub-agent 호출 수 자동 결정:

| Tier | 조건 | sub-agent |
|------|------|-----------|
| **T1a** Test-only | 100% 테스트 파일 · ≤200줄 · 보안 키워드 0 | 1 (`pr-reviewer-test`) |
| **T1b** Deps-only | 100% 의존성 매니페스트 · src/ 변경 0 · 보안 키워드 0 | 1 (`pr-reviewer-security`) |
| **T0** Trivial | ≤50줄 · src/ 변경 0 · 보안 키워드 0 | 0 (직접 리뷰) |
| **T3** Full | >200줄 OR 보안 키워드 | 3 (domain+security+test) |
| **T2** Standard | 그 외 (catch-all) | 2 (domain+security) |

흔한 작은 PR(테스트 추가, deps bump, docs 변경)이 헤비 경로를 자동 우회. 보안/대규모 변경은 여전히 T3 풀 리뷰.

#### v2.3+ Confidence 채점 + 결정 매트릭스 (옵셔널 외부화)

sub-agent 도출 이슈에 0-100 점수 부여 후 severity × confidence 매트릭스로 게시·결정 결정:

| 조건 | 처리 |
|------|------|
| CRITICAL × conf ≥ critical 임계치 | 게시 + REQUEST_CHANGES |
| CRITICAL × conf < critical | **MAJOR 강등 게시** (드롭 X, 누락 방지) + 자기 PR이면 자동 chain 차단 |
| MAJOR × conf < major | 드롭 |
| MINOR × conf < minor | 드롭 |

임계치 커스텀 (디폴트 80/60/50):
```json
{
  "review": {
    "thresholds": {
      "critical": 85,
      "major": 65,
      "minor": 55
    }
  }
}
```

각 키 독립 fallback — 일부만 명시해도 나머지는 디폴트 적용. critical ≥ 50 강제(false-positive 게이트 무력화 차단).

> 자세한 분류 매트릭스·rubric은 [aick-review-pr SKILL.md](https://github.com/wejsa/ai-crew-kit/blob/main/.claude/skills/aick-review-pr/SKILL.md) 참조.

### 운영/인프라 🔵

| 명령어 | 설명 |
|--------|------|
| `/aick-hotfix "{설명}"` | main 긴급 수정 |
| `/aick-rollback {태그\|PR번호}` | 릴리스/PR 롤백 |
| `/aick-release` | 버전 릴리스 |

### 분석/문서 🟢

| 명령어 | 설명 |
|--------|------|
| `/aick-docs` | 참고자료 조회 |
| `/aick-retro` | 완료 Task 회고 |
| `/aick-retro {TASK-ID}` | 특정 Task 회고 |
| `/aick-retro --summary` | 전체 회고 요약 |
| `/aick-report` | 프로젝트 메트릭 리포트 |
| `/aick-report --full` | 전체 히스토리 리포트 |
| `/aick-estimate` | 작업 복잡도 추정 |

### 설정/확장 ⚙️

| 명령어 | 설명 |
|--------|------|
| `/aick-create` | 커스텀 스킬 생성 |
| `/aick-upgrade` | 프레임워크 업그레이드 |
| `/aick-upgrade --dry-run` | 변경 사항 미리보기 |
| `/aick-validate` | 업그레이드 후 검증 |

## 자연어 매핑

명령어를 모르더라도 자연어로 요청할 수 있습니다:

| 자연어 | 매핑되는 스킬 |
|--------|-------------|
| "새 기능 기획해줘" | `/aick-feature` |
| "다음 작업 가져와줘" | `/aick-plan` |
| "개발 진행해줘" | `/aick-impl` |
| "PR 123 리뷰해줘" | `/aick-review-pr 123` |
| "PR 123 머지해줘" | `/aick-merge-pr 123` |
| "상태 확인해줘" | `/aick-status` |
| "회고 해줘" | `/aick-retro` |
| "리포트 생성해줘" | `/aick-report` |
| "작업량 추정해줘" | `/aick-estimate` |
| "긴급 수정해줘" | `/aick-hotfix` |
| "v1.2.3 롤백해줘" | `/aick-rollback v1.2.3` |
| "참고자료 보여줘" | `/aick-docs` |
| "스킬 만들어줘" | `/aick-create` |
| "프로젝트 온보딩해줘" | `/aick-onboard` |
| "헬스체크 해줘" | `/aick-health-check` |
| "정리해줘" | `/aick-health-check --fix` |

## 어떤 검증 도구를 사용해야 하나요?

| 상황 | 명령어 | 소요 시간 |
|------|--------|----------|
| 매일 세션 시작할 때 | `/aick-status --health` | ~5초 |
| "뭔가 이상한데?" 싶을 때 | `/aick-health-check --quick` | ~15초 |
| 릴리스 전 전수 점검 | `/aick-health-check` | ~30초 |
| 프레임워크 업그레이드 후 | `/aick-validate` (자동 실행됨) | ~10초 |
| 문제를 수정할 때 | `/aick-health-check --fix` | ~30초 |
| 주간 팀 리포트 | `/aick-report` | ~30초 |
