<div align="center">

# AI Crew Kit v2.3.1

**도메인 선택 → 자동 셋업 → 에이전트 팀 즉시 가동**

AI 에이전트 팀 기반 소프트웨어 개발 프로세스 관리 프레임워크

[![Version](https://img.shields.io/badge/version-v2.3.1-blue?style=flat-square)](./CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](./LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/wejsa/ai-crew-kit?style=flat-square)](https://github.com/wejsa/ai-crew-kit)
[![Built with Claude Code](https://img.shields.io/badge/built_with-Claude_Code-blueviolet?style=flat-square)](https://claude.ai/download)

[빠른 시작](#-빠른-시작) · [지원 스택](#-지원-기술-스택) · [도메인](#-지원-도메인) · [명령어](#-주요-명령어) · [문서](#-상세-문서)

</div>

> **프레임워크 철학** — AI Crew Kit은 **"어떻게 짜는지"가 아니라 "어떤 프로세스로 만드는지"**를 관리합니다. 코드 작성과 기술 판단은 Claude가 담당하고, 프레임워크는 워크플로우 자동화·품질 게이트·팀 컨벤션을 제공합니다. REST, WebSocket, GraphQL, gRPC 등 모든 프로토콜의 코드를 Claude가 작성할 수 있으며, 프레임워크는 그 과정의 품질을 보장합니다.

---

## 🚀 빠른 시작

```bash
git clone https://github.com/wejsa/ai-crew-kit.git my-project
cd my-project
claude
/skill-init --quick
```

> [!TIP]
> `/skill-init --quick`은 제로 결정 모드로 5분 안에 체험할 수 있습니다.
> 모든 설정을 직접 선택하려면 `/skill-init`을 사용하세요.

`/skill-init`은 ai-crew-kit clone을 자동 감지하여 다음을 한 번에 처리합니다 (사용자 추가 확인 없음):

1. kit git 히스토리 제거 + 새 사용자 리포 초기화
2. kit 잔여 파일 자동 정리 (14종): `CHANGELOG.md`, `docs/`, `examples/`, `tests/`, `scripts/`, `.github/`, `memory/`, `LICENSE`, `README.md`, `CLAUDE.md`, `VERSION`, `.claude/temp/`, `.claude/hooks/tests/`, `.claude/state/`, `.claude/settings.local.json`
3. 도메인·기술 스택·에이전트 팀 선택
4. 사용자 프로젝트용 `CLAUDE.md`/`README.md`/`VERSION`(0.1.0) 새로 생성
5. `KIT_SOURCE_URL`을 `project.json`의 `kitSource`로 기록 (skill-upgrade가 GitHub에서 kit 가이드 fetch)

> [!NOTE]
> kit clone 자동 정리는 두 안전장치를 통과해야 실행됩니다 — (1) origin URL 정규식 + initial commit fingerprint 일치, (2) 더티/미푸시/비-main 브랜치 가드. 사용자 시나리오에는 영향이 없으며 kit 개발자 환경 사고만 방지합니다.

**이미 코드베이스가 있는 프로젝트라면:**

```bash
# 권장: kit의 .claude/만 기존 프로젝트에 복사 (잡티 0)
git clone https://github.com/wejsa/ai-crew-kit.git /tmp/ai-crew-kit
cp -r /tmp/ai-crew-kit/.claude my-existing-project/
cd my-existing-project
claude
/skill-onboard
```

> 코드베이스를 자동 스캔하여 기술 스택과 도메인을 감지하고 설정을 생성합니다. kit clone에 사용자 코드를 함께 둔 경우(시나리오 B)도 `/skill-onboard`가 위와 동일한 자동 정리를 사전에 수행합니다 (사용자 코드 보통 `src/`/`app/` 등 비충돌 경로면 안전; 동일 경로 충돌 의심 시 사전 백업 권장).
> 자세한 내용은 [기존 프로젝트 온보딩](./docs/getting-started.md#기존-프로젝트-온보딩)을 참조하세요.

---

## 🛠 지원 기술 스택

| 구분 | 스택 |
|------|------|
| **백엔드** | Spring Boot (Kotlin · Java), Node.js (TypeScript), Python (FastAPI · Django), Go |
| **프론트엔드** | Next.js, React (Vite), Vue, Nuxt, Astro |
| **데이터베이스** | MySQL, PostgreSQL, MongoDB |
| **인프라** | Redis, RabbitMQ, Docker Compose |

> 프레임워크는 기술 스택에 중립적입니다. 위 스택은 빌드/테스트 자동 감지와 컨벤션이 제공되는 목록이며, Claude는 이 외의 기술(WebSocket, GraphQL, gRPC, Elasticsearch 등)도 자유롭게 구현합니다.

---

## 🌐 지원 도메인

| 도메인 | 설명 | 기본 스택 | 컴플라이언스 |
|--------|------|----------|-------------|
| 🏦 **fintech** | 결제, 정산, 오픈뱅킹, 마이데이터 | Spring Boot + MySQL + Redis | PCI-DSS, 전자금융감독규정, 오픈뱅킹규정, 신용정보법 |
| 🛒 **ecommerce** | 이커머스, 마켓플레이스, 구독 커머스 | Spring Boot + Next.js + MySQL + Redis | 전자상거래법, 소비자보호법, 통신판매중개의무 |
| ☁️ **saas** | 멀티테넌시, 구독 결제, SaaS 플랫폼 | Spring Boot + Next.js + PostgreSQL + Redis | GDPR, SOC2, 정보통신망법 |
| 🏥 **healthcare** | PHI 보호, 진료기록, 처방, 보험 청구 | Spring Boot + Next.js + PostgreSQL + Redis | HIPAA, 의료법, 생명윤리법 |
| 🔧 **general** | 범용 프로젝트 | Spring Boot + MySQL | - |

---

## ⚡ 주요 명령어

| 명령어 | 설명 | 자연어 예시 |
|--------|------|------------|
| `/skill-status` | 프로젝트 상태 확인 | "상태 확인해줘" |
| `/skill-feature` | 새 기능 기획 | "새 기능 기획해줘" |
| `/skill-plan` | 설계 및 스텝 계획 | "다음 작업 가져와줘" |
| `/skill-impl` | 코드 구현 + PR 생성 | "개발 진행해줘" |
| `/skill-impl --retry` | 실패 스텝 재시작 | "이어서 진행해줘" |
| `/skill-backlog dashboard` | Phase 진행률 현황 | "대시보드 보여줘" |
| `/skill-review-pr` | PR 리뷰 ([모드 설정](./docs/skill-reference.md#개발-워크플로우)) | "PR 123 리뷰해줘" |
| `/skill-merge-pr` | PR 머지 | "PR 123 머지해줘" |
| `/skill-retro` | 완료 Task 회고 | "회고 해줘" |
| `/skill-hotfix` | main 긴급 수정 | "긴급 수정해줘" |
| `/skill-rollback` | 릴리스 롤백 | "v1.2.3 롤백해줘" |
| `/skill-report` | 프로젝트 메트릭 리포트 | "리포트 생성해줘" |
| `/skill-health-check` | 코드베이스 건강 검진 | "헬스체크 해줘" |

전체 명령어와 자연어 매핑은 [스킬 레퍼런스](./docs/skill-reference.md)를 참조하세요.

---

## 🏥 건강 검진 (Health Check)

에이전트가 생성한 코드와 문서 간 드리프트를 탐지하고, 엔트로피 축적을 조기에 발견합니다.

| 카테고리 | 설명 | 기본 가중치 |
|----------|------|------------|
| doc-sync | 문서 ↔ 코드 동기화 | 35% |
| state-integrity | 상태 파일 정합성 | 25% |
| security | 기본 보안 검사 | 25% |
| agent-config | 에이전트 설정 유효성 | 15% |
| compliance | 컴플라이언스 준수 (fintech) | 도메인 선택 시 자동 추가 |

`/skill-health-check --fix`로 자동 수정 가능한 항목을 즉시 반영할 수 있습니다.

---

## ✨ v2.0 신규 기능

| 기능 | Phase | 사용자 가치 |
|------|:-----:|------|
| **Claude Code 네이티브 훅** (SessionStart / PostToolUse / Stop) | Phase 1 | 세션 진입 자동 git sync, lockedAt heartbeat 자동 갱신, 응답 완료 시 continuation-plan 자동 작성 — 미사용 시 v1.x 동작 100% 유지 |
| **스킬 프로파일 + 토큰 힌트** | Phase 2/3 | 5종 프로파일(`default` ≡ `full` / `developer` / `docs-only` / `custom`)로 CLAUDE.md 노출 스킬 제어. complexity-hint(heavy/medium/light) 토큰 예산 가이드 |
| **4층 Layered Override + 도메인×언어 rules** | Phase 4 | PR 리뷰가 `.claude/rules/{domain}/{language}/*.md`의 도메인 비즈니스 제약(MUST/MUST NOT)을 자동 인식 — 사용자가 rule 1건 추가하는 즉시 활성. v2.0.0 GA는 메커니즘만 제공(빌트인 콘텐츠 0개) |
| **AgentShield-lite 시크릿 스캐너** (SEC-05/06/07) | Phase 5 | 하드코딩 시크릿(API 키/AWS/GitHub/Slack) + `.env` 노출 게이트 + 도메인별 민감 데이터(PAN Luhn / SSN / 한국 주민·사업자) CRITICAL 검출 |
| **lessons-learned 회귀 보호** | Phase 7 | `skill-retro` 학습 데이터에 schema 검증 + secrets 필터(토큰/이메일 자동 redact) + impact 정량(상/중/하) + 33 pytest cases 회귀 보호 |
| **v1→v2 자동 마이그레이션 + R6 1차 방어선** | Phase 8 | `/skill-upgrade --version v2.0.0` 한 번으로 모든 변경 자동 흡수. R6 자동 검증 9 tests across 4 fixtures (parametrize) — 라운드트립 + 비-trivial 멱등성 + cumulative+filter + fail-fast |

> **GA examples 안내 (OQ-04)** — v2.0.0 GA 시점 `examples/` 디렉토리는 **`fintech-gateway` (Spring Boot Kotlin) / `ecommerce-shop` (Node.js TypeScript)** 두 도메인만 제공합니다. **`saas` / `healthcare` 도메인은 `tests/upgrade/fixtures/` 단위 fixture 검증만 완료** — 실제 example project는 v2.1+ 후속 범위. 두 도메인 사용자는 `/skill-init`로 동일하게 초기화 가능하나 example 참조용 코드는 v2.1+에서 추가됩니다.
>
> **v1.x 사용자**: [v1.x → v2.0.0 마이그레이션 가이드](./docs/v2/migration-guide.md) 참조 — 자동 4 add_field, 수동 작업 거의 없음, 점수 영향 ≤1점.
>
> **Phase 6 (`skill-compliance-report`) v2.1+ 보류** — 옵션 D 채택(2026-05-01). 위반 탐지 Phase 4/5 중복 + 실수요 미검증으로 보류, 재진입 조건은 [phase-6-compliance.md](./docs/v2/phase-6-compliance.md) §보류 결정 참조.

---

## 💡 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **프로세스 관리** | 프레임워크는 워크플로우·품질 게이트·컨벤션을 담당하고, 코드 작성·기술 판단은 Claude가 담당 |
| **Domain-Driven Kit** | 도메인 선택이 컨벤션, 체크리스트, 참고 문서 전체를 결정 |
| **Layered Override** | `_base` → `{domain}` → `project.json` 순서로 설정 적용 |
| **Agent Orchestration** | PM이 워크플로우에 따라 에이전트 자동 분배 |
| **Zero-Config Start** | `/skill-init` 한 번으로 즉시 가동 |

---

## 📖 상세 문서

| 문서 | 내용 |
|------|------|
| [설치 및 시작하기](./docs/getting-started.md) | 설치 상세, 초기화 흐름, 온보딩, **첫 기능 만들기** |
| [핵심 개념](./docs/concepts.md) | 도메인, 에이전트 팀, 디렉토리 구조, 실행 모델 |
| [스킬 레퍼런스](./docs/skill-reference.md) | 23개 스킬 전체 목록, 자연어 매핑 |
| [워크플로우 가이드](./docs/workflow-guide.md) | 자동 체이닝, 7가지 워크플로우, 품질 게이트, Git 전략 |
| [도메인 확장](./docs/customization.md) | 참고자료/체크리스트 추가, 새 도메인 생성, Layered Override |
| [프레임워크 업그레이드](./docs/upgrade-guide.md) | 업그레이드, 보존 항목, 롤백 |
| [v1.x → v2.0.0 마이그레이션 가이드](./docs/v2/migration-guide.md) | v2.0 변경 사항, 자동 마이그레이션, FAQ, 롤백 매뉴얼 |
| [예제 프로젝트](./examples/) | fintech-gateway, ecommerce-shop (saas/healthcare는 v2.1+ 후속) |
| [프레임워크 제거 (Eject)](./docs/eject-guide.md) | 제거 절차, 보존 항목, 체크리스트 |

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
