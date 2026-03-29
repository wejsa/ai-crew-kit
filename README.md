<div align="center">

# AI Crew Kit

**도메인 선택 → 자동 셋업 → 에이전트 팀 즉시 가동**

AI 에이전트 팀 기반 소프트웨어 개발 키트

[![Version](https://img.shields.io/badge/version-v1.35.1-blue?style=flat-square)](./CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](./LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/wejsa/ai-crew-kit?style=flat-square)](https://github.com/wejsa/ai-crew-kit)
[![Built with Claude Code](https://img.shields.io/badge/built_with-Claude_Code-blueviolet?style=flat-square)](https://claude.ai/download)

[빠른 시작](#-빠른-시작) · [도메인](#-지원-도메인) · [명령어](#-주요-명령어) · [문서](#-상세-문서)

</div>

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

초기화 과정에서 **도메인**, **기술 스택**, **에이전트 팀**을 선택하고, 프로젝트 전용 `README.md`와 `VERSION`(0.1.0)이 자동 생성됩니다.

**이미 코드베이스가 있는 프로젝트라면:**

```bash
git clone https://github.com/wejsa/ai-crew-kit.git
cp -r ai-crew-kit/.claude my-existing-project/
cd my-existing-project
claude
/skill-onboard
```

> 코드베이스를 자동 스캔하여 기술 스택과 도메인을 감지하고 설정을 생성합니다.
> 자세한 내용은 [기존 프로젝트 온보딩](./docs/getting-started.md#기존-프로젝트-온보딩)을 참조하세요.

---

## 🌐 지원 도메인

| 도메인 | 설명 | 기본 스택 | 컴플라이언스 |
|--------|------|----------|-------------|
| 🏦 **fintech** | 결제, 정산, 금융 서비스 | Spring Boot + MySQL + Redis | PCI-DSS, 전자금융감독규정 |
| 🛒 **ecommerce** | 이커머스, 마켓플레이스 | Spring Boot + MySQL + Redis | 전자상거래법, 소비자보호법 |
| 🔧 **general** | 범용 프로젝트 | Spring Boot + MySQL | - |

---

## ⚡ 주요 명령어

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

전체 23개 명령어와 자연어 매핑은 [스킬 레퍼런스](./docs/skill-reference.md)를 참조하세요.

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

## 💡 핵심 원칙

> **Domain-Driven Kit** — 도메인 선택이 전체 키트 동작 결정
>
> **Layered Override** — `_base` → `{domain}` → `project.json` 순서로 설정 적용
>
> **Agent Orchestration** — PM이 워크플로우에 따라 에이전트 자동 분배
>
> **Zero-Config Start** — `/skill-init` 한 번으로 즉시 가동

---

## 📖 상세 문서

| 문서 | 내용 |
|------|------|
| [설치 및 시작하기](./docs/getting-started.md) | 설치 상세, 초기화 흐름, 온보딩 |
| [핵심 개념](./docs/concepts.md) | 도메인, 에이전트 팀, 디렉토리 구조, 실행 모델 |
| [스킬 레퍼런스](./docs/skill-reference.md) | 22개 스킬 전체 목록, 자연어 매핑 |
| [워크플로우 가이드](./docs/workflow-guide.md) | 자동 체이닝, 7가지 워크플로우, 품질 게이트, Git 전략 |
| [도메인 확장](./docs/customization.md) | 참고자료/체크리스트 추가, 새 도메인 생성, Layered Override |
| [프레임워크 업그레이드](./docs/upgrade-guide.md) | 업그레이드, 보존 항목, 롤백 |

---

## 📋 요구사항

| 구분 | 요구사항 |
|------|---------|
| **필수** | [Claude Code](https://claude.ai/download) CLI |
| **권장** | Git 2.30+ |

> Node.js, Python 등 외부 런타임은 불필요합니다. Claude Code가 모든 것을 처리합니다.

---

<div align="center">

[MIT License](./LICENSE) · [변경 로그](./CHANGELOG.md) · [이슈 리포트](https://github.com/wejsa/ai-crew-kit/issues)

</div>
