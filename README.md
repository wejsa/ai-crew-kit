<div align="center">

# AI Crew Kit v4.0.0

**범용 AI 크루 개발 프레임워크 — 오케스트레이션 · 품질 게이트 · 스택 인지**

AI 에이전트 팀 기반 소프트웨어 개발 프로세스 관리 프레임워크

[![Version](https://img.shields.io/badge/version-v4.0.0-blue?style=flat-square)](./CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](./LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/wejsa/ai-crew-kit?style=flat-square)](https://github.com/wejsa/ai-crew-kit)
[![Built with Claude Code](https://img.shields.io/badge/built_with-Claude_Code-blueviolet?style=flat-square)](https://claude.ai/download)

[빠른 시작](#-빠른-시작) · [지원 스택](#-지원-기술-스택) · [명령어](#-주요-명령어) · [문서](#-상세-문서)

</div>

> **프레임워크 철학** — AI Crew Kit은 **"어떻게 짜는지"가 아니라 "어떤 프로세스로 만드는지"**를 관리합니다. 코드 작성과 기술 판단은 Claude가 담당하고, 프레임워크는 워크플로우 자동화·품질 게이트·팀 컨벤션을 제공합니다. REST, WebSocket, GraphQL, gRPC 등 모든 프로토콜의 코드를 Claude가 작성할 수 있으며, 프레임워크는 그 과정의 품질을 보장합니다.

---

## 🚀 빠른 시작

### 방법 1 — 플러그인으로 설치 (신규)

AI Crew Kit은 이제 **Claude Code 플러그인 마켓플레이스**로 설치할 수 있습니다. 22개 스킬 + 12개 에이전트 + 품질 게이트 훅(SessionStart / PreToolUse / PostToolUse / Stop)이 한 번에 등록됩니다.

```bash
# Claude Code 세션 안에서
/plugin marketplace add wejsa/ai-crew-kit
/plugin install ai-crew-kit@ai-crew-kit
```

설치 후 어느 프로젝트에서나 `/crew-init`로 셋업을 시작합니다. clone과 달리 kit 잔여 파일 정리가 필요 없어 **잡티 0**으로 시작됩니다.

### 방법 2 — clone 후 초기화

```bash
git clone https://github.com/wejsa/ai-crew-kit.git my-project
cd my-project
claude
/crew-init --quick
```

> [!TIP]
> `/crew-init --quick`은 제로 결정 모드로 5분 안에 체험할 수 있습니다.
> 모든 설정을 직접 선택하려면 `/crew-init`을 사용하세요.

`/crew-init`은 ai-crew-kit clone을 자동 감지하여 다음을 한 번에 처리합니다 (사용자 추가 확인 없음):

1. kit git 히스토리 제거 + 새 사용자 리포 초기화
2. kit 잔여 파일 자동 정리 (14종): `CHANGELOG.md`, `docs/`, `examples/`, `tests/`, `scripts/`, `.github/`, `memory/`, `LICENSE`, `README.md`, `CLAUDE.md`, `VERSION`, `.claude/temp/`, `.claude/hooks/tests/`, `.claude/state/`, `.claude/settings.local.json`
3. **요구사항 자유 서술 → 기술 스택 LLM 추천 → 에이전트 팀 선택**
4. **백로그 자동 분해 (opt-in)** — Phase 4-카테고리 템플릿으로 10~25개 Task를 즉시 준비, `/crew-plan`/`/crew-impl` 체인으로 바로 진입
5. 사용자 프로젝트용 `CLAUDE.md`/`README.md`/`VERSION`(0.1.0) 새로 생성
6. `KIT_SOURCE_URL`을 `project.json`의 `kitSource`로 기록 (crew-upgrade가 GitHub에서 kit 가이드 fetch)

> [!NOTE]
> kit clone 자동 정리는 두 안전장치를 통과해야 실행됩니다 — (1) origin URL 정규식 + initial commit fingerprint 일치, (2) 더티/미푸시/비-main 브랜치 가드. 사용자 시나리오에는 영향이 없으며 kit 개발자 환경 사고만 방지합니다.

> [!TIP]
> **요구사항 우선 플로우** — 한 줄 또는 여러 문단의 요구사항을 입력하면 기술 스택을 LLM이 추천하고 백로그까지 자동으로 분해합니다. 입력 신뢰 경계(prompt injection 방어)·sanitization(셸/path traversal 차단)·Hard limits(phase당 ≤10, 전체 ≤30)가 기본 적용됩니다.

**이미 코드베이스가 있는 프로젝트라면:**

```bash
# 권장: kit의 .claude/만 기존 프로젝트에 복사 (잡티 0)
git clone https://github.com/wejsa/ai-crew-kit.git /tmp/ai-crew-kit
cp -r /tmp/ai-crew-kit/.claude my-existing-project/
cd my-existing-project
claude
/crew-onboard
```

> 코드베이스를 자동 스캔하여 기술 스택을 감지하고 설정을 생성합니다. kit clone에 사용자 코드를 함께 둔 경우(시나리오 B)도 `/crew-onboard`가 위와 동일한 자동 정리를 사전에 수행합니다 (사용자 코드 보통 `src/`/`app/` 등 비충돌 경로면 안전; 동일 경로 충돌 의심 시 사전 백업 권장).
> 자세한 내용은 [기존 프로젝트 온보딩](./docs/getting-started.md#기존-프로젝트-온보딩)을 참조하세요.

### 기존 사용자 — 업데이트

> **자동 업데이트되지 않습니다.** AI Crew Kit은 커뮤니티 마켓플레이스라 기본적으로 수동 업데이트입니다.

- **플러그인으로 설치한 경우** — `/plugin update`로 최신 버전을 받습니다 (또는 `/plugin` UI에서 이 마켓플레이스의 auto-update를 켜면 다음 세션 시작 시 자동 적용).
- **clone / seed 프로젝트인 경우** — 본인 프로젝트의 업그레이드 스킬로 업그레이드합니다.

> [!IMPORTANT]
> **v3.x → v4.0.0은 BREAKING** — 스킬 명령이 `/skill-*` → `/crew-*`로 바뀌었습니다 (예: `/skill-impl` → `/crew-impl`). v3.x 시드에는 아직 구 `/skill-upgrade`만 있으므로 **첫 업그레이드는 `/skill-upgrade --version v4.0.0`로 실행**하세요 (이 명령이 `.claude/skills/`를 통째 교체하며 스스로를 `crew-upgrade`로 바꿉니다). 이후부터 `/crew-upgrade`를 사용합니다. 업그레이드 후 검증은 `/crew-validate`를 한 번 직접 실행해 마무리하세요. 본인 스크립트·문서·`CLAUDE.md` `CUSTOM_SECTION`의 `/skill-*` 명령은 직접 `/crew-*`로 바꿔야 합니다. 상세·주의사항은 [업그레이드 가이드](./docs/upgrade-guide.md)를 참조하세요.
>
> **v1.x → v2.0.0 사용자**: [마이그레이션 가이드](./docs/v2/migration-guide.md) 참조.

---

## 🛠 지원 기술 스택

| 구분 | 스택 |
|------|------|
| **백엔드** | Spring Boot (Kotlin · Java), Node.js (TypeScript), Python (FastAPI · Django), Go |
| **프론트엔드** | Next.js, React (Vite), Vue, Nuxt, Astro |
| **데이터베이스** | MySQL, PostgreSQL, MongoDB, SQLite |
| **인프라** | Redis, RabbitMQ, Docker Compose |

> 프레임워크는 기술 스택에 중립적입니다. 위 스택은 빌드/테스트 자동 감지와 컨벤션이 제공되는 목록이며, Claude는 이 외의 기술(WebSocket, GraphQL, gRPC, Elasticsearch 등)도 자유롭게 구현합니다.

---

## ⚡ 주요 명령어

| 명령어 | 설명 | 자연어 예시 |
|--------|------|------------|
| `/crew-status` | 프로젝트 상태 확인 | "상태 확인해줘" |
| `/crew-feature` | 새 기능 기획 | "새 기능 기획해줘" |
| `/crew-plan` | 설계 및 스텝 계획 | "다음 작업 가져와줘" |
| `/crew-impl` | 코드 구현 + PR 생성 | "개발 진행해줘" |
| `/crew-impl --next` | 다음 스텝 진행 | "이어서 진행해줘" |
| `/crew-backlog` | 백로그 조회/관리 | "백로그 보여줘" |
| `/crew-review-pr` | PR 리뷰 ([Tier 분류·confidence 채점](./docs/skill-reference.md)) | "PR 123 리뷰해줘" |
| `/crew-merge-pr` | PR 머지 | "PR 123 머지해줘" |
| `/crew-retro` | 완료 Task 회고 | "회고 해줘" |
| `/crew-hotfix` | main 긴급 수정 | "긴급 수정해줘" |
| `/crew-rollback` | 릴리스 롤백 | "v1.2.3 롤백해줘" |
| `/crew-report` | 프로젝트 메트릭 리포트 | "리포트 생성해줘" |
| `/crew-health-check` | 코드베이스 건강 검진 | "헬스체크 해줘" |

전체 명령어와 자연어 매핑은 [스킬 레퍼런스](./docs/skill-reference.md)를 참조하세요.

---

## 🛡 머지 품질 게이트 (v2.4+)

"CRITICAL은 머지 차단"이 더 이상 프롬프트 지시(prose)에 의존하지 않습니다. `gh pr merge` 직전 **PreToolUse 훅이 미해결 CRITICAL PR을 결정적으로 차단**합니다.

| 신호 | 출처 | 동작 |
|------|------|------|
| **A (state)** | `workflowState.lastReviewDecision == REQUEST_CHANGES` + `step.prNumber` join | 오프라인 결정적 차단 |
| **B (GitHub)** | `reviewDecision == CHANGES_REQUESTED` | best-effort 차단 |

> 인프라 실패(jq/git/gh 부재·네트워크 등)는 **fail-open** — 게이트 자체 장애가 정상 머지를 막지 않습니다. 제어 env: `CCK_MERGE_GATE=off`(전면 비활성) · `CCK_GATE_BYPASS=1`(1회 우회) · `CCK_GATE_NO_GH=1`(신호 B 스킵).

---

## 🏥 건강 검진 (Health Check)

에이전트가 생성한 코드와 문서 간 드리프트를 탐지하고, 엔트로피 축적을 조기에 발견합니다.

| 카테고리 | 설명 | 기본 가중치 |
|----------|------|------------|
| doc-sync | 문서 ↔ 코드 동기화 | 35% |
| state-integrity | 상태 파일 정합성 | 25% |
| security | 기본 보안 검사 | 25% |
| agent-config | 에이전트 설정 유효성 | 15% |

`/crew-health-check --fix`로 자동 수정 가능한 항목을 즉시 반영할 수 있습니다.

---

## ✨ 주요 기능

| 기능 | 사용자 가치 |
|------|------|
| **Claude Code 네이티브 훅** (SessionStart / PreToolUse / PostToolUse / Stop) | 세션 진입 자동 git sync, lock heartbeat 자동 갱신, 응답 완료 시 continuation-plan 자동 작성, 미해결 CRITICAL PR 머지 결정적 차단 |
| **스킬 프로파일 + 토큰 힌트 + 모델 라우팅** | 프로파일(`full` / `developer` / `docs-only` / `custom`)로 CLAUDE.md 노출 스킬 제어 + complexity-hint 토큰 예산 가이드 + 스킬별 모델 라우팅(구현 `sonnet`·품질 판단 `opus`) |
| **자동 Tier 분류 PR 리뷰** | PR 특성으로 T0~T3 자동 라우팅(작은 PR은 경량, 보안/대규모는 풀 리뷰) + severity × confidence 매트릭스 false-positive 필터(CRITICAL은 강등 게시·드롭 X) |
| **Layered Override 컨벤션** | `_base` 공통 컨벤션·체크리스트를 `project.json`으로 덮어쓰는 계층형 설정 — PR 리뷰가 프로젝트 컨벤션을 자동 인식 |
| **AgentShield-lite 시크릿 스캐너** | 하드코딩 시크릿(API 키/AWS/GitHub/Slack) + `.env` 노출 게이트를 CRITICAL로 검출 |
| **lessons-learned 회귀 보호** | `crew-retro` 학습 데이터에 schema 검증 + secrets 필터(토큰/이메일 자동 redact) + impact 정량(상/중/하) |

> 머지 품질 게이트 상세는 [위 섹션](#-머지-품질-게이트-v24)을, **버전별 누적 변경 이력은 [CHANGELOG](./CHANGELOG.md)**를 참조하세요.
>
> **examples 안내** — `examples/` 디렉토리는 범용 최소 예제를 제공합니다. 어떤 기술 스택의 프로젝트든 `/crew-init`로 동일하게 초기화할 수 있습니다.

---

## 💡 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **프로세스 관리** | 프레임워크는 워크플로우·품질 게이트·컨벤션을 담당하고, 코드 작성·기술 판단은 Claude가 담당 |
| **스택 인지** | 기술 스택을 자동 감지해 빌드/테스트 게이트와 컨벤션을 맞춤 적용 |
| **Layered Override** | `_base` → `project.json` 순서로 설정 적용 |
| **Agent Orchestration** | PM이 워크플로우에 따라 에이전트 자동 분배 |
| **결정적 품질 게이트** | 신뢰 가능한 레이어(hook)가 핵심 게이트(머지 차단)를 담당하고, prose+LLM에 의존하지 않음 |
| **Zero-Config Start** | `/crew-init` 한 번으로 즉시 가동 |

---

## 📖 상세 문서

| 문서 | 내용 |
|------|------|
| [설치 및 시작하기](./docs/getting-started.md) | 설치 상세, 초기화 흐름, 온보딩, **첫 기능 만들기** |
| [핵심 개념](./docs/concepts.md) | 에이전트 팀, 디렉토리 구조, 실행 모델 |
| [스킬 레퍼런스](./docs/skill-reference.md) | 전체 스킬 목록, 자연어 매핑, Tier 분류 매트릭스 |
| [워크플로우 가이드](./docs/workflow-guide.md) | 자동 체이닝, 7가지 워크플로우, 품질 게이트, Git 전략 |
| [토큰 최적화](./docs/token-optimization.md) | 스킬 프로파일, 모델 라우팅, 리뷰 Tier, 1M 실패 대응 Q&A |
| [커스터마이징](./docs/customization.md) | 참고자료/체크리스트 추가, DB·마이그레이션 도구 변경, Layered Override |
| [Cowork 플러그인](./docs/cowork-plugin.md) | Cowork 환경에서 kit 활용 |
| [프레임워크 업그레이드](./docs/upgrade-guide.md) | 업그레이드, 보존 항목, 롤백 |
| [v1.x → v2.0.0 마이그레이션 가이드](./docs/v2/migration-guide.md) | v2.0 변경 사항, 자동 마이그레이션, FAQ, 롤백 매뉴얼 |
| [예제 프로젝트](./examples/) | 범용 최소 예제 |
| [프레임워크 제거 (Eject)](./docs/eject-guide.md) | 제거 절차, 보존 항목, 체크리스트 |
| [변경 로그](./CHANGELOG.md) | 전체 버전별 변경 이력 |

---

## 📋 요구사항

| 구분 | 요구사항 |
|------|---------|
| **필수** | [Claude Code](https://claude.ai/download) CLI |
| **권장** | Claude Code v2.1.49+ (네이티브 git worktree 지원), Git 2.30+ |

> 프레임워크 자체는 외부 런타임 없이 동작합니다. 프로젝트 빌드/테스트에 필요한 런타임(Node.js, Python, Go, JDK 등)은 선택한 기술 스택에 따라 별도 설치합니다.

> 병렬 작업 시 `claude --worktree <name>` (Claude Code v2.1.49+) 또는 Claude Squad 같은 외부 오케스트레이터를 사용할 수 있습니다. 모든 스킬이 워크트리 환경을 자동 감지합니다.

---

<div align="center">

[MIT License](./LICENSE) · [변경 로그](./CHANGELOG.md) · [이슈 리포트](https://github.com/wejsa/ai-crew-kit/issues)

</div>
