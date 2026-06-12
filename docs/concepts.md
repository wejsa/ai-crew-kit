# 핵심 개념

> [← README로 돌아가기](../README.md)

## 적용 범위

AI Crew Kit은 특정 도메인에 종속되지 않는 **범용 AI 크루 개발 프레임워크**입니다. 모든 프로젝트 유형에 적용할 수 있으며, 공통 컨벤션·체크리스트·헬스체크(`.claude/domains/_base/`)가 기본 적용됩니다. 프로젝트별 커스텀은 `project.json` 및 `CLAUDE.md`의 `CUSTOM_SECTION`에서 자유롭게 추가합니다.

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

### 구조 — 메인 세션이 오케스트레이션, 에이전트는 품질 분석 전담

구현·기획·문서화는 **메인 세션(스킬 체이닝)**의 몫입니다. 에이전트는 스킬이 필요한
시점에 호출하는 **품질 분석 전문가**입니다 (v4.8.0: 미배선 에이전트 pm·planner·
backend·frontend·docs 제거 — 12종 → 실동작 7종, [docs/archive/agents/](./archive/agents/) 참조).

```
        메인 세션 (스킬 체이닝이 오케스트레이션)
  feature → plan → impl → review-pr → merge-pr
              │       │        │
              ▼       ▼        ▼
        ┌──────────┐ ┌──────────────────┐ ┌──────────────────────┐
        │ 설계 분석 │ │ 구현 중 분석      │ │ PR 리뷰 (다관점)      │
        ├──────────┤ ├──────────────────┤ ├──────────────────────┤
        │db-designer│ │qa                │ │pr-reviewer-architecture│
        │          │ │docs-impact-      │ │pr-reviewer-security   │
        │          │ │analyzer          │ │pr-reviewer-test       │
        └──────────┘ └──────────────────┘ └──────────────────────┘
                              + agent-code-reviewer (리뷰 가이드 문서)
```

### 에이전트 7종 (전부 실호출 경로 보유)

| | 에이전트 | 호출 스킬 | 역할 | 기본 활성화 |
|---|---------|----------|------|------------|
| 🟣 | **pr-reviewer-architecture** | aick-review-pr | 아키텍처 + 비즈니스 로직 일관성 리뷰 | 무조건 호출 |
| 🔴 | **pr-reviewer-security** | aick-review-pr | 보안 리뷰 | 무조건 호출 |
| 🔵 | **pr-reviewer-test** | aick-review-pr | 테스트 품질 리뷰 | 무조건 호출 (Tier에 따라) |
| 📝 | **docs-impact-analyzer** | aick-impl | 문서 영향도 분석 + 초안 제안 | 무조건 호출 |
| 🧪 | **agent-qa** | aick-impl | 테스트 품질 분석 (백그라운드) | `agents.enabled`에 `qa` (기본 ON) |
| 🗃️ | **agent-db-designer** | aick-plan | DB 설계 분석 (병렬) | `agents.enabled`에 `db-designer` (기본 OFF) |
| 👀 | **agent-code-reviewer** | aick-review-pr | 4관점 통합 리뷰 가이드 (참조 문서 — 직접 호출 없음) | 기본 |

> 분석 에이전트는 전부 읽기 전용(Read/Glob/Grep)이며, 스킬을 통해서만 호출됩니다.

## 디렉토리 구조

```
.claude/
├── agents/           # 에이전트 정의
├── skills/           # 스킬 정의
├── domains/          # 공통 컨벤션 + 기본 템플릿
│   ├── _base/          # 공통 컨벤션 + 체크리스트
│   │   ├── conventions/  # 개발 컨벤션
│   │   └── checklists/   # 리뷰 체크리스트
│   └── general/        # 기본 docs (getting-started 등)
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

# 프로젝트 루트 (aick-init 시 자동 생성)
CLAUDE.md               # AI 에이전트 지시문
README.md               # 프로젝트 README (템플릿 기반)
VERSION                 # 프로젝트 버전 (0.1.0부터 시작)

# ai-crew-kit clone에서 시작한 경우 aick-init/aick-onboard가 다음을 자동 삭제
# (kit dev 잡티 — 사용자 프로젝트에 불필요):
#   CHANGELOG.md, docs/, examples/, tests/, scripts/, .github/, memory/, LICENSE,
#   README.md, README.ko.md, CLAUDE.md, VERSION (Step 6에서 사용자용 새로 생성),
#   .claude/temp/, .claude/hooks/tests/, .claude/state/, .claude/settings.local.json

docs/
├── retro/              # 회고 리포트 (aick-retro)
└── reports/            # 메트릭 리포트 (aick-report)
```

## 실행 모델

AI Crew Kit은 **프롬프트 기반 시스템**입니다.

### 별도 런타임 없음

- Node.js, Python 등 외부 런타임 **불필요**
- Claude Code가 SKILL.md, workflow YAML을 읽고 직접 수행
- 모든 설정 파일은 "명세"이며, Claude가 이해하고 따름

### 결정론 레이어 (훅 4종)

프롬프트 기반 코어 주위에 작은 **결정론 레이어**가 있습니다:

| 훅 | 시점 | 역할 |
|-----|------|------|
| session-start | 세션 시작 | git sync, continuation-plan 재생, 진행 중 Task 안내 |
| pre-tool-use | 모든 Bash 직전 | **머지 품질 게이트** — 미해결 CRITICAL PR의 `gh pr merge`를 exit 2로 거부 |
| post-tool-use | Edit/Write 직후 | lock 하트비트(file-membership), 무한 루프 방어 |
| stop | 응답 종료마다 | lock TTL 만료 정리, continuation-plan 작성 |

> Bookkeeping 훅(3종)은 절대 비차단(exit 0). 게이트 훅은 설계상 차단하되 인프라 실패에는 **fail-open**이며, 우회는 명시적·사람 전용·감사 기록됩니다. 상세: [merge-gate-explained.md](./merge-gate-explained.md)

### 상태 저장

| 경로 | 용도 | Git 관리 |
|------|------|----------|
| `.claude/state/` | 영구 상태 (backlog, project) | O |
| `.claude/temp/` | 임시 산출물 | X |

### 세션 재개

세션이 끊기고 다시 시작할 때:

```bash
# 상태 확인 (권장)
/aick-status

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
- `/aick-status --locks`로 상태 확인
- `/aick-backlog unlock {taskId} --force`로 긴급 해제

## 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **Stack-Aware Kit** | 스택 인지로 빌드·리뷰·추천 자동 조정 |
| **Layered Override** | `domains/_base/`(공통 기본값) → `project.json`(프로젝트 설정) → `CLAUDE.md` `CUSTOM_SECTION`(프로젝트 커스텀) 순서로 설정 적용 |
| **Agent Orchestration** | PM이 워크플로우에 따라 에이전트 자동 분배 |
| **Zero-Config Start** | `/aick-init` 한 번으로 즉시 가동 |

## Layered Override

설정은 다음 순서로 오버라이드됩니다:

```
1. CLAUDE.md CUSTOM_SECTION (프로젝트 커스텀) ← 최우선
2. project.json                               ← 프로젝트 설정
3. domains/_base/                             ← 공통 기본값
   ──────────────────────────────────────────
   하드코딩 기본값                             ← baseline (카운트 외)
```

> 자세한 커스터마이징 방법은 [docs/customization.md](./customization.md) 참조.

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
