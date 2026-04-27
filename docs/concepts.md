# 핵심 개념

> [← README로 돌아가기](../README.md)

## 지원 도메인

| 도메인 | 설명 | 기본 스택 | 컴플라이언스 |
|--------|------|----------|-------------|
| 🏦 **fintech** | 결제, 정산, 오픈뱅킹, 마이데이터 | Spring Boot + MySQL + Redis | PCI-DSS, 전자금융감독규정, 오픈뱅킹규정, 신용정보법 |
| 🛒 **ecommerce** | 이커머스, 마켓플레이스, 구독 커머스 | Spring Boot + Next.js + MySQL + Redis | 전자상거래법, 소비자보호법, 통신판매중개의무 |
| ☁️ **saas** | 멀티테넌시, 구독 결제, SaaS 플랫폼 | Spring Boot + PostgreSQL + Redis | GDPR, SOC2, 정보통신망법 |
| 🏥 **healthcare** | PHI 보호, 진료기록, 처방, 보험 청구 | Spring Boot + PostgreSQL + Redis | HIPAA, 의료법, 생명윤리법 |
| 🔧 **general** | 범용 프로젝트 | Spring Boot + MySQL | - |

각 도메인에는 전용 **체크리스트**, **참고자료**, **코드 템플릿**이 포함됩니다.

## 지원 기술 스택

### 백엔드

| 스택 | 빌드 | 테스트 | 특징 |
|------|------|--------|------|
| Spring Boot (Kotlin) | `./gradlew build` | `./gradlew test` | 기본 스택, 가장 풍부한 컨벤션 |
| Spring Boot (Java) | `./gradlew build` | `./gradlew test` | Maven도 지원 |
| Node.js (TypeScript) | `npm run build` | `npm test` | Express/Fastify/NestJS |
| **Python (FastAPI)** | `pip install -e '.[dev]'` | `pytest --cov=app` | 비동기 API, Pydantic, SQLAlchemy |
| **Python (Django)** | `pip install -e '.[dev]'` | `pytest --cov` | DRF, Django ORM, 관리자 패널 |
| Go | `go build ./...` | `go test ./...` | Gin/Echo |

### 프론트엔드

| 스택 | 유형 | 빌드 |
|------|------|------|
| Next.js | SSR/SSG | `npm run build` |
| React + Vite | SPA | `npm run build` |
| Vue / Nuxt | SPA/SSR | `npm run build` |
| Astro | 정적 사이트 | `npm run build` |

> Python 상세 컨벤션: `python-project-structure.md`, `python-testing.md`, `python-dependency.md`, `python-patterns.md` 참조

## 에이전트 팀

### 에이전트 구조

```
              ┌───────────────────┐
              │     agent-pm      │  ← 총괄 오케스트레이터 (항상 활성)
              │ 요청 분석 → 분배  │
              └─────────┬─────────┘
                        │
       ┌────────────────┼────────────────┐
       │                │                │
       ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ 기획/설계   │  │    개발     │  │    검증     │
├─────────────┤  ├─────────────┤  ├─────────────┤
│ planner     │  │ backend     │  │ code-reviewer│
│ db-designer │  │ frontend    │  │ qa          │
│             │  │             │  │ docs        │
└─────────────┘  └─────────────┘  └─────────────┘
```

### 에이전트 역할

| 에이전트 | 역할 | 기본 활성화 |
|---------|------|------------|
| **agent-pm** | 오케스트레이션, 워크플로우 관리 | 항상 |
| **agent-backend** | 백엔드 코드 구현 | 기본 |
| **agent-code-reviewer** | 5관점 통합 코드 리뷰 | 기본 |
| **agent-planner** | 요구사항 정의, 기획 | 선택적 |
| **agent-frontend** | 프론트엔드 구현 | 선택적 |
| **agent-db-designer** | DB 설계 분석 (sub-agent) | 선택적 |
| **agent-qa** | 테스트 품질 분석 (sub-agent) | 선택적 |
| **agent-docs** | 문서 자동화 | 선택적 |

### Sub-Agent (스킬에서 자동 호출)

| | 에이전트 | 호출 스킬 | 역할 |
|---|---------|----------|------|
| 🔴 | **pr-reviewer-security** | skill-review-pr | 보안 + 컴플라이언스 리뷰 |
| 🟣 | **pr-reviewer-domain** | skill-review-pr | 도메인 + 아키텍처 리뷰 |
| 🔵 | **pr-reviewer-test** | skill-review-pr | 테스트 품질 리뷰 |
| 📝 | **docs-impact-analyzer** | skill-impl | 문서 영향도 분석 + 초안 제안 |
| 🟠 | **agent-db-designer** | skill-plan | DB 설계 분석 (병렬) |
| 🟢 | **agent-qa** | skill-impl | 테스트 품질 분석 (백그라운드) |

> Sub-agent는 읽기 전용(Read/Glob/Grep)으로 동작하며, 스킬을 통해서만 호출됩니다.
> agent-db-designer, agent-qa는 `project.json`의 `agents.enabled`에 포함된 경우에만 실행됩니다.

## 디렉토리 구조

```
.claude/
├── agents/           # 에이전트 정의
├── skills/           # 스킬 정의
├── domains/          # 도메인 템플릿
│   ├── _registry.json  # 도메인 카탈로그
│   ├── _base/          # 공통 컨벤션 + 체크리스트
│   │   ├── conventions/  # 개발 컨벤션 (9개)
│   │   └── checklists/   # 리뷰 체크리스트
│   ├── fintech/        # 핀테크 도메인
│   ├── ecommerce/      # 이커머스 도메인
│   └── general/        # 범용 도메인
├── templates/        # 파일 생성 템플릿
│   ├── CLAUDE.md.tmpl    # CLAUDE.md 템플릿
│   └── README.md.tmpl   # README.md 템플릿
├── workflows/        # 워크플로우 정의
├── schemas/          # JSON 스키마
├── state/            # 프로젝트 상태 (Git 관리)
│   ├── project.json    # 프로젝트 설정
│   ├── backlog.json    # 백로그
│   └── completed.json  # 완료 이력
└── temp/             # 임시 파일 (.gitignore)

# 프로젝트 루트 (skill-init 시 자동 생성)
CLAUDE.md               # AI 에이전트 지시문
README.md               # 프로젝트 README (템플릿 기반)
VERSION                 # 프로젝트 버전 (0.1.0부터 시작)

docs/
├── retro/              # 회고 리포트 (skill-retro)
└── reports/            # 메트릭 리포트 (skill-report)
```

## 실행 모델

AI Crew Kit은 **프롬프트 기반 시스템**입니다.

### 별도 런타임 없음

- Node.js, Python 등 외부 런타임 **불필요**
- Claude Code가 SKILL.md, workflow YAML을 읽고 직접 수행
- 모든 설정 파일은 "명세"이며, Claude가 이해하고 따름

### 상태 저장

| 경로 | 용도 | Git 관리 |
|------|------|----------|
| `.claude/state/` | 영구 상태 (backlog, project) | O |
| `.claude/temp/` | 임시 산출물 | X |

### 세션 재개

세션이 끊기고 다시 시작할 때:

```bash
# 상태 확인 (권장)
/skill-status

# 자동으로 진행 중인 Task 찾아서 재개
"이어서 진행해줘"

# 특정 Task 지정
"TASK-001 이어서 진행해줘"
```

### 병렬 작업

여러 Claude 세션에서 독립적인 Task를 동시에 진행할 수 있습니다.

**허용 조건:**
- 의존성(`dependencies`)이 없는 Task
- 수정 파일(`lockedFiles`)이 겹치지 않는 Task

**세션 식별:**
```
{user}@{hostname}-{YYYYMMDD-HHmmss}
예: dev@DESKTOP-ABC-20260203-143052
```

**잠금 관리:**
- 기본 TTL: 1시간
- 만료 시 다른 세션에서 인계 가능
- `/skill-status --locks`로 상태 확인
- `/skill-backlog unlock {taskId} --force`로 긴급 해제

## 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **Domain-Driven Kit** | 도메인 선택이 전체 키트 동작 결정 |
| **Layered Override** | `_base` → `{domain}` → `{domain}/{language}` → `project.json` 순서로 설정 적용 (Phase 4부터 4층) |
| **Agent Orchestration** | PM이 워크플로우에 따라 에이전트 자동 분배 |
| **Zero-Config Start** | `/skill-init` 한 번으로 즉시 가동 |

## Layered Override

설정은 다음 순서로 오버라이드됩니다 (v2.0.0-alpha.3 / Phase 4부터 4층):

```
1. project.json (사용자 설정)              ← 최우선
2. .claude/rules/{domain}/{language}/      ← 도메인 × 언어 교차 (Phase 4 신설)
3. domains/{domain}/domain.json            ← 도메인 설정
4. domains/_base/                          ← 공통 기본값
   ─────────────────────────────────────────
   하드코딩 기본값                          ← baseline (카운트 외)
```

> 2층(`rules`)은 **PR 리뷰 컨텍스트 한정 적용** — 도메인 비즈니스 제약(MUST/MUST NOT) 표현용. 기존 conventions/checklists/health 영역의 로드 구조는 변경되지 않습니다(2~3층 그대로 유지).
> 자세한 사용법은 [docs/customization.md](./customization.md#도메인--언어-rules)와 [.claude/rules/README.md](../.claude/rules/README.md) 참조.

## 설계 철학: 프레임워크와 AI의 역할 분리

AI Crew Kit은 **프로세스 관리 프레임워크**이지 코드 생성 도구가 아닙니다.

| 영역 | 프레임워크 책임 | Claude 책임 |
|------|---------------|------------|
| 워크플로우 | feature→plan→impl→review→merge 자동 체이닝 | — |
| 품질 게이트 | 빌드/테스트/리뷰 통과 강제 | — |
| 팀 컨벤션 | 코딩 스타일, 보안 규칙, 아키텍처 원칙 SSOT | — |
| 코드 작성 | — | 모든 언어, 프로토콜, 라이브러리 |
| 기술 판단 | — | 아키텍처 패턴, 라이브러리 선택, 최적화 |

### 왜 이렇게 분리하는가?

1. **중복 방지** — Claude는 WebSocket, GraphQL, gRPC 등 모든 기술을 이미 학습하고 있습니다. 프레임워크가 이를 다시 가르치면 유지보수 비용만 발생하고, Claude의 최신 지식과 충돌할 수 있습니다.
2. **기술 중립성** — 프레임워크가 특정 프로토콜/라이브러리의 컨벤션을 정의하면, 그 컨벤션이 노후화됩니다. 프로세스(워크플로우)는 기술 변화에 영향받지 않습니다.
3. **확장성** — 새로운 기술(예: HTTP/3, QUIC)이 등장해도 프레임워크 수정 없이 Claude가 즉시 대응합니다.

### 프레임워크가 하지 않는 것

- 특정 프로토콜(WebSocket, gRPC 등)의 코드 작성법을 가르치지 않습니다
- 특정 라이브러리(socket.io, Apollo 등)의 사용법을 정의하지 않습니다
- 특정 아키텍처 패턴(이벤트 소싱, CQRS 등)을 강제하지 않습니다

이들은 모두 Claude의 기술 지식 영역이며, 프로젝트 요구사항에 따라 Claude가 적절히 판단합니다.
