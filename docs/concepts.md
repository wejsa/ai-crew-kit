# 핵심 개념

> [← README로 돌아가기](../README.md)

## 지원 도메인

| 도메인 | 설명 | 기본 스택 | 컴플라이언스 |
|--------|------|----------|-------------|
| 🏦 **fintech** | 결제, 정산, 금융 서비스 | Spring Boot + MySQL + Redis | PCI-DSS, 전자금융감독규정 |
| 🛒 **ecommerce** | 이커머스, 마켓플레이스 | Spring Boot + MySQL + Redis | 전자상거래법, 소비자보호법 |
| 🔧 **general** | 범용 프로젝트 | Spring Boot + MySQL | - |

각 도메인에는 전용 **체크리스트**, **참고자료**, **코드 템플릿**이 포함됩니다.

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
│             │  │ devops      │  │ docs        │
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
| **agent-devops** | CI/CD, 인프라 | 선택적 |

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
| **Layered Override** | `_base` → `{domain}` → `project.json` 순서로 설정 적용 |
| **Agent Orchestration** | PM이 워크플로우에 따라 에이전트 자동 분배 |
| **Zero-Config Start** | `/skill-init` 한 번으로 즉시 가동 |

## Layered Override

설정은 다음 순서로 오버라이드됩니다:

```
1. project.json (사용자 설정)      ← 최우선
2. domains/{domain}/domain.json   ← 도메인 설정
3. domains/_base/                 ← 공통 기본값
4. 하드코딩 기본값                  ← 최하위
```
