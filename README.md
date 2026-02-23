# AI Crew Kit v1.19.0

> 도메인 선택 → 자동 셋업 → 에이전트 팀 즉시 가동

AI 에이전트 팀 기반 소프트웨어 개발 키트입니다. 도메인을 선택하면 해당 분야에 특화된 에이전트 팀과 체크리스트, 참고자료가 자동으로 구성됩니다.

---

## 목차

- [빠른 시작](#빠른-시작)
- [설치](#설치)
- [지원 도메인](#지원-도메인)
- [주요 명령어](#주요-명령어)
- [에이전트 팀](#에이전트-팀)
- [워크플로우](#워크플로우)
- [디렉토리 구조](#디렉토리-구조)
- [프레임워크 업그레이드](#프레임워크-업그레이드)
- [도메인 확장](#도메인-확장)

---

## 빠른 시작

```bash
# 1. 저장소 클론
git clone https://github.com/wejsa/ai-crew-kit.git my-project
cd my-project

# 2. Claude Code 실행
claude

# 3. 프로젝트 초기화 (대화형)
/skill-init

# 4. 첫 기능 기획
/skill-feature "사용자 인증"
```

초기화 과정에서 **도메인**, **기술 스택**, **에이전트 팀**을 대화형으로 선택하고, 프로젝트 전용 `README.md`와 `VERSION`(0.1.0)이 자동 생성됩니다.

---

## 설치

### 요구사항

| 구분 | 요구사항 |
|------|---------|
| **필수** | [Claude Code](https://claude.ai/download) CLI |
| **권장** | Git 2.30+ |

> **참고**: Claude Code가 파일을 읽고 직접 수행하므로 Node.js, Python 등 외부 런타임은 불필요합니다.

### 설치 단계

**Step 1: 저장소 클론**
```bash
git clone https://github.com/wejsa/ai-crew-kit.git my-project
cd my-project
```

**Step 2: Claude Code 실행**
```bash
claude
```

**Step 3: 프로젝트 초기화**
```bash
/skill-init
```

### 초기화 흐름

```
/skill-init 실행
    │
    ├── 1. 환경 검증 (Git 저장소 확인)
    │
    ├── 2. 프로젝트 정보 입력 (이름, 설명)
    │
    ├── 3. 도메인 선택
    │       ├── 🏦 fintech (결제/정산)
    │       ├── 🛒 ecommerce (이커머스)
    │       └── 🔧 general (범용)
    │
    ├── 4. 기술 스택 선택 (Backend, DB, Cache 등)
    │
    ├── 5. 에이전트 팀 구성 (필수 3개 + 선택 6개)
    │
    └── 6. 설정 파일 자동 생성
            ├── .claude/state/project.json
            ├── .claude/state/backlog.json
            ├── CLAUDE.md
            ├── README.md  (프로젝트 전용)
            └── VERSION    (0.1.0)
```

---

## 지원 도메인

| 도메인 | 설명 | 기본 스택 | 컴플라이언스 |
|--------|------|----------|-------------|
| 🏦 **fintech** | 결제, 정산, 금융 서비스 | Spring Boot + MySQL + Redis | PCI-DSS, 전자금융감독규정 |
| 🛒 **ecommerce** | 이커머스, 마켓플레이스 | Spring Boot + MySQL + Redis | 전자상거래법, 소비자보호법 |
| 🔧 **general** | 범용 프로젝트 | Spring Boot + MySQL | - |

각 도메인에는 전용 **체크리스트**, **참고자료**, **코드 템플릿**이 포함됩니다.

---

## 주요 명령어

### 자주 사용하는 명령어

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

### 전체 명령어 목록

| 명령어 | 설명 |
|--------|------|
| `/skill-init` | 프로젝트 초기화 |
| `/skill-status` | 현재 상태 확인 |
| `/skill-backlog` | 백로그 조회/관리 |
| `/skill-feature` | 새 기능 기획 |
| `/skill-plan` | 설계 + 스텝 계획 수립 |
| `/skill-impl` | 코드 구현 (스텝별) |
| `/skill-impl --next` | 다음 스텝 진행 |
| `/skill-review` | 코드 리뷰 |
| `/skill-review-pr {번호}` | PR 리뷰 |
| `/skill-review-pr {번호} --auto-fix` | PR 리뷰 + CRITICAL 이슈 자동 수정 |
| `/skill-fix {번호}` | CRITICAL 이슈 수정 |
| `/skill-merge-pr {번호}` | PR 머지 |
| `/skill-docs` | 참고자료 조회 |
| `/skill-retro` | 완료 Task 회고 + 학습 반영 |
| `/skill-retro {TASK-ID}` | 특정 Task 회고 |
| `/skill-retro --summary` | 전체 회고 요약 |
| `/skill-hotfix "{설명}"` | main 긴급 수정 |
| `/skill-rollback {태그\|PR번호}` | 릴리스/PR 롤백 |
| `/skill-report` | 프로젝트 메트릭 리포트 |
| `/skill-report --full` | 전체 히스토리 리포트 |
| `/skill-domain` | 도메인 관리 |
| `/skill-upgrade` | 프레임워크 업그레이드 |
| `/skill-upgrade --dry-run` | 변경 사항 미리보기 |

---

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
| **agent-pm** | 오케스트레이션, 워크플로우 관리 | ✅ 항상 |
| **agent-backend** | 백엔드 코드 구현 | ✅ 기본 |
| **agent-code-reviewer** | 5관점 통합 코드 리뷰 | ✅ 기본 |
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

---

## 워크플로우

### 일반 개발 흐름 (자동 체이닝)

`/skill-feature`로 시작하면 승인 시점마다 **다음 스킬이 자동 호출**됩니다.

```
"사용자 인증 기능 만들어줘"
        │
        ▼
┌──────────────────────────────────────┐
│ 1. 기획 (skill-feature)               │  ← 유일한 수동 실행
│    └── 요구사항 문서 생성             │
│    └── 사용자 승인 대기               │
│    └── 승인 시 → skill-plan 자동 호출 │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│ 2. 설계 (skill-plan)                  │  ← 자동
│    └── 설계 + 스텝 분리 (Step 1,2,3) │
│    └── 사용자 승인 대기               │
│    └── 승인 시 → skill-impl 자동 호출 │
└──────────────┬───────────────────────┘
               ▼
┌══════════════════════════════════════┐
║   스텝별 반복 (3→4→5 자동 진행)       ║
╠══════════════════════════════════════╣
║                                      ║
║  ┌────────────────────────────────┐  ║
║  │ 3. 개발 (skill-impl)           │  ║
║  │    └── 현재 스텝 코드 구현      │  ║
║  │    └── PR 생성                 │  ║
║  │    └── PR 생성 완료 시          │  ║
║  │        → skill-review-pr       │  ║
║  │          --auto-fix 호출       │  ║
║  └──────────────┬─────────────────┘  ║
║                 ▼                    ║
║  ┌────────────────────────────────┐  ║
║  │ 4. 리뷰 (skill-review-pr)      │  ║
║  │    └── 5관점 코드 리뷰          │  ║
║  │    └── CRITICAL 발견 시         │  ║
║  │        → skill-fix 호출        │  ║
║  │    └── 리뷰 통과 시             │  ║
║  │        → skill-merge-pr 호출   │  ║
║  └──────────────┬─────────────────┘  ║
║                 ▼                    ║
║  ┌────────────────────────────────┐  ║
║  │ 5. 머지 (skill-merge-pr)       │  ║
║  │    └── Squash 머지 실행        │  ║
║  │    └── 다음 스텝 존재 시        │  ║
║  │        → skill-impl 호출 (반복)│  ║
║  │    └── 모든 스텝 완료 시        │  ║
║  │        → 워크플로우 종료       │  ║
║  └────────────────────────────────┘  ║
║                                      ║
╚══════════════════════════════════════╝
```

> **최신 버전**: `/skill-feature`만 수동 실행하면 전체 워크플로우가 자동 진행됩니다. 1-2단계는 승인 필요, 3-5단계는 완전 자동입니다.

### 워크플로우 유형

| 워크플로우 | 트리거 | 설명 |
|-----------|--------|------|
| **full-feature** | "새 기능 만들어줘" | 기획 → 설계 → 개발 → 리뷰 → 완료 |
| **quick-fix** | "버그 고쳐줘" | 개발 → 리뷰 |
| **migration** | "마이그레이션 해줘" | 기획 → 개발 → 리뷰 |
| **review-only** | "리뷰해줘" | 리뷰만 진행 |
| **review-auto-fix** | "--auto-fix로 리뷰" | 리뷰 → CRITICAL 자동 수정 → 재리뷰 |
| **hotfix** | "긴급 수정해줘" | main 핫픽스 → 패치 릴리스 |
| **rollback** | "v1.2.3 롤백해줘" | git revert → 패치 릴리스 |
| **docs-only** | "문서 업데이트해줘" | 문서 작업만 |

---

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

---

## 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **Domain-Driven Kit** | 도메인 선택이 전체 키트 동작 결정 |
| **Layered Override** | `_base` → `{domain}` → `project.json` 순서로 설정 적용 |
| **Agent Orchestration** | PM이 워크플로우에 따라 에이전트 자동 분배 |
| **Zero-Config Start** | `/skill-init` 한 번으로 즉시 가동 |

---

## 실행 모델

AI Crew Kit은 **프롬프트 기반 시스템**입니다.

### 별도 런타임 없음

- Node.js, Python 등 외부 런타임 **불필요**
- Claude Code가 SKILL.md, workflow YAML을 읽고 직접 수행
- 모든 설정 파일은 "명세"이며, Claude가 이해하고 따름

### 상태 저장

| 경로 | 용도 | Git 관리 |
|------|------|----------|
| `.claude/state/` | 영구 상태 (backlog, project) | ✅ |
| `.claude/temp/` | 임시 산출물 | ❌ |

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

---

## 품질 게이트

워크플로우 진행 중 품질 게이트를 통과해야 다음 단계로 진행됩니다.

| 게이트 | 조건 | 실패 시 |
|--------|------|---------|
| `user_approval` | 사용자 승인 | 대기 |
| `build_success` | 빌드 통과 | 수정 요청 |
| `critical_zero` | CRITICAL 이슈 0개 | 수정 요청 |
| `test_pass` | 테스트 통과 + 커버리지 80% | 수정 요청 |

---

## 코드 리뷰 관점

agent-code-reviewer는 5가지 관점에서 통합 리뷰를 수행합니다.

| 관점 | 체크 항목 |
|------|----------|
| **컴플라이언스** | 업종별 규정, 감사로그, 개인정보보호 |
| **도메인 로직** | 상태머신, 금액/수량 정밀도, 멱등성 |
| **아키텍처** | Circuit Breaker, 장애격리, 레이어 분리 |
| **보안** | 민감정보 로깅금지, SQL Injection, XSS |
| **테스트 품질** | 커버리지 80%, 실패 케이스 |

> 도메인 선택 시 해당 도메인의 특화 체크리스트가 자동 로딩됩니다.
>
> v1.5.0부터 5관점 리뷰가 3개 병렬 subagent로 분할 실행됩니다:
> pr-reviewer-security (보안+컴플라이언스) / pr-reviewer-domain (도메인+아키텍처) / pr-reviewer-test (테스트 품질)

---

## Git 브랜치 전략

```
main (운영)
  ├── hotfix/HOT-NNN-긴급수정 (main에서 분기 → main PR)
  ├── revert/{대상} (main에서 분기 → main PR)
  └── develop (개발 통합)
        ├── feature/TASK-XXX-stepN (스텝별 개발)
        └── bugfix/BUG-XXX (버그 수정)
```

### PR 규칙
- **스텝별 PR 생성** (500라인 미만)
- develop 브랜치로 PR 생성
- 리뷰 승인 후 Squash 머지

### 자기 PR 처리

GitHub 정책상 자신의 PR은 승인할 수 없습니다. AI Crew Kit은 이를 자동 감지하여 처리합니다.

| 구분 | 동작 |
|------|------|
| **타인 PR** | `--approve` → `skill-merge-pr` |
| **자기 PR** | `--comment` (리뷰 완료) → `skill-merge-pr` |

> 자기 PR의 경우 승인을 건너뛰고 COMMENT만 남긴 후 머지를 진행합니다.

---

## 프레임워크 업그레이드

AI Crew Kit이 업데이트되면, 기존 프로젝트에서 프레임워크 파일만 선택적으로 업그레이드할 수 있습니다.
프로젝트 코드, 상태 파일(backlog, project.json), 커스텀 설정은 보존됩니다.

### 업그레이드 실행

```bash
# 변경 사항 미리보기 (실제 변경 없음)
/skill-upgrade --dry-run

# 최신 버전으로 업그레이드
/skill-upgrade

# 특정 버전으로 업그레이드
/skill-upgrade --version v1.7.0

# 소스 지정 (기본값은 project.json의 kitSource)
/skill-upgrade --source https://github.com/wejsa/ai-crew-kit.git
```

### 최초 업그레이드 (skill-upgrade가 없는 프로젝트)

v1.6.0 이전에 초기화된 프로젝트에는 skill-upgrade 스킬이 없습니다.
아래 명령으로 1회성 부트스트랩 후 사용하세요:

```bash
# 1. ai-crew-kit 최신 버전 클론
git clone --depth 1 https://github.com/wejsa/ai-crew-kit.git /tmp/ai-crew-kit-latest

# 2. skill-upgrade 스킬만 복사
cp -r /tmp/ai-crew-kit-latest/.claude/skills/skill-upgrade .claude/skills/

# 3. 임시 파일 정리
rm -rf /tmp/ai-crew-kit-latest

# 4. 이후 skill-upgrade 사용 가능
/skill-upgrade
```

### 업그레이드 시 보존되는 항목

| 구분 | 항목 | 보존 방식 |
|------|------|----------|
| **프로젝트 상태** | project.json, backlog.json | 완전 보존 |
| **프로젝트 코드** | src/, docs/, VERSION 등 | 완전 보존 |
| **CLAUDE.md 커스텀 규칙** | `CUSTOM_SECTION` 마커 사이 내용 | 추출 → 재생성 → 복원 |
| **도메인 커스텀 파일** | add-doc, add-checklist로 추가한 파일 | 자동 감지 → 복원 |
| **도구 권한 설정** | settings.json 커스텀 권한 | 머지 (기존 보존 + 새 항목 추가) |

### 롤백

문제 발생 시 즉시 이전 상태로 복원할 수 있습니다:

```bash
# 가장 최근 백업에서 롤백
/skill-upgrade --rollback

# 특정 백업 지정
/skill-upgrade --rollback .claude/temp/upgrade-backup-20260208-143052/
```

---

## 도메인 확장

### 참고자료 추가

```bash
# 로컬 파일 추가
/skill-domain add-doc docs/my-guide.md

# URL에서 추가
/skill-domain add-doc "https://example.com/api-guide.md"
```

### 체크리스트 추가

```bash
/skill-domain add-checklist docs/my-checklist.md
```

**체크리스트 형식:**
```markdown
| 항목 | 설명 | 심각도 |
|------|------|--------|
| 항목1 | 설명1 | CRITICAL |
| 항목2 | 설명2 | MAJOR |
```

### 새 도메인 생성

**방법 1: 기존 도메인 복제 (권장)**
```bash
/skill-domain export my-custom-domain
```

**방법 2: 수동 생성**
```bash
# 1. 디렉토리 생성
mkdir -p .claude/domains/my-domain/{docs,checklists,templates}

# 2. domain.json 작성
# 3. _registry.json에 등록
```

### 도메인 전환

```bash
# 현재 도메인 확인
/skill-domain

# 도메인 목록 조회
/skill-domain list

# 도메인 전환
/skill-domain switch ecommerce
```

---

## Layered Override

설정은 다음 순서로 오버라이드됩니다:

```
1. project.json (사용자 설정)      ← 최우선
2. domains/{domain}/domain.json   ← 도메인 설정
3. domains/_base/                 ← 공통 기본값
4. 하드코딩 기본값                  ← 최하위
```

---

## 변경 로그

자세한 변경 이력은 [CHANGELOG.md](./CHANGELOG.md)를 참조하세요.

---

## 라이선스

MIT License

---

## 관련 링크

- [상세 문서](./docs/)
- [이슈 리포트](https://github.com/wejsa/ai-crew-kit/issues)
