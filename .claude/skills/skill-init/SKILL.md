---
name: skill-init
description: 프로젝트 초기화 - 도메인 선택 + 자동 셋업. /skill-init으로 호출합니다.
disable-model-invocation: true
allowed-tools: Bash(git:*), Read, Write, Glob, AskUserQuestion
argument-hint: "[--quick] [--reset]"
---

# skill-init: 프로젝트 초기화

## 실행 조건
- 사용자가 `/skill-init` 또는 "프로젝트 시작해줘" 요청 시

## 옵션
```
/skill-init           # 새 프로젝트 초기화 (대화형)
/skill-init --quick   # 제로 결정 빠른 초기화 (자동 감지 + 기본값)
/skill-init --reset   # 기존 설정 초기화 (재설정)
/skill-init --quick --reset  # 기존 설정 초기화 + 빠른 재설정
```

## --quick vs 일반 모드

| 단계 | 일반 모드 | --quick 모드 |
|------|----------|-------------|
| Step 1: 환경 검증 | 그대로 | 그대로 |
| Step 2: 프로젝트 정보 | AskUserQuestion 2회 | 디렉토리명 → name, 설명 빈칸 |
| Step 2.5: 스택 추천 | 설명 분석 → 도메인+스택 추천 (수락/수정/수동) | 디렉토리명 키워드 매칭 (무음) |
| Step 3: 도메인 선택 | 추천 수락 시 스킵 / 수동 시 AskUserQuestion 1회 | 자동 감지 → fallback: general |
| Step 4: 기술 스택 | 추천 수락 시 스킵 / 수동 시 AskUserQuestion 5+회 | 자동 감지 → 감지 실패 시 백엔드 1회 질문 |
| Step 5: 에이전트 팀 | AskUserQuestion multi-select | 스택 기반 자동: pm + backend/frontend + code-reviewer |
| Step 5.5: 워크플로우 프로필 | AskUserQuestion 1회 | standard 기본값 |
| Step 5.6: 스킬 프로파일 | AskUserQuestion 1회 | full 기본값 |
| Step 6-7 | 그대로 | + "설정 변경: /skill-init --reset" 안내 |

### 케이스별 흐름 요약

| Case | 모드 | 대상 사용자 | 흐름 | 질문 횟수 |
|------|------|-----------|------|----------|
| 1. 추천 수락 | 일반 | 초심자 | Step 2 → 2.5(A) → 5 → 5.5 → 5.6 → 6 | **5회** |
| 2. 일부 수정 | 일반 | 중급자 | Step 2 → 2.5(B) → 항목 수정 → 5 → 5.5 → 5.6 → 6 | **6-8회** |
| 3. 직접 선택 | 일반 | 경력자 | Step 2 → 2.5(C) → 3 → 4 → 5 → 5.5 → 5.6 → 6 | 11+회 |
| 4. 설명 미입력 | 일반 | 경력자 | Step 2 → (2.5 스킵) → 3 → 4 → 5 → 5.5 → 5.6 → 6 | 10+회 |
| 5. 파일 감지 성공 | --quick | 기존 프로젝트 | 파일 감지 → 자동 | **0회** |
| 6. 디렉토리명 매칭 | --quick | 빈 디렉토리 | 디렉토리명 → 도메인 defaultStack | **0회** |
| 7. 폴백 | --quick | 빈 디렉토리 | 백엔드 1회 질문 → 자동 | 1회 |

- Case 1~2: Step 2.5 추천 기능으로 도메인+스택 선택을 간소화 (Step 3, 4 건너뜀)
- Case 3~4: 기존 플로우와 100% 동일 (경력자 경험 유지)
- Case 5~7: --quick 모드 기존 동작 유지 + Case 6에서 디렉토리명 매칭 추가

### --quick 자동 감지

**디렉토리명 도메인 매칭** (파일 감지 전 실행):
1. 디렉토리명을 `-`, `_`, 공백으로 분리하여 토큰화
2. `_registry.json`의 각 도메인 keywords와 토큰 매칭
3. 2개 이상 토큰 매칭 시 해당 도메인의 defaultStack 적용 (무음, 추가 질문 없음)
4. 매칭 실패 → 아래 파일 기반 감지로 진행

예: `patient-appointment` → healthcare ("patient" + "appointment") / `tenant-billing-app` → saas ("tenant" + "billing")

**백엔드**:
- `build.gradle.kts` → spring-boot-kotlin
- `build.gradle` → spring-boot-java
- `pom.xml` → spring-boot-java (Maven)
- `go.mod` → go
- `pyproject.toml` / `requirements.txt` → python (FastAPI/Django 자동 판별)
- `package.json` + express/fastify/nestjs 의존성 → nodejs-typescript

**프론트엔드** (package.json 의존성 또는 설정 파일):
- `next.config.*` → nextjs
- `vite.config.*` + react 의존성 → react-vite
- `nuxt.config.*` → vue-nuxt
- `astro.config.*` → astro
- `vue.config.*` / vue 의존성 → vue

**감지 실패 시 (빈 디렉토리)**: 백엔드 프레임워크 1회 질문:
```
감지된 파일이 없습니다. 백엔드를 선택하세요:
1. Spring Boot (Kotlin)
2. Spring Boot (Java)
3. Node.js (TypeScript)
4. Python (FastAPI)
5. Python (Django)
6. Go
7. 없음 (프론트엔드 전용)
8. 직접 설정 (/skill-init)
```
선택 후 해당 백엔드 + 도메인 기본 DB/캐시/인프라 적용. 프론트엔드는 `none` 기본 (7번 선택 시 프론트엔드 추가 질문).

---

## 실행 플로우 (일반 모드)

### Step 1: 환경 검증

| 항목 | 조건 | 처리 |
|------|------|------|
| Git 저장소 | 없음 | `git init -b main` |
| Git remote origin | ai-crew-kit 가리킴 | `rm -rf .git && git init -b main` (히스토리 초기화) |
| Git remote origin | 사용자 저장소 가리킴 | 유지 |
| project.json | 있음 | 재초기화 경고 (--reset 없으면) |
| CLAUDE.md | 있음 | 백업 여부 확인 |

ai-crew-kit origin인 경우 KIT_SOURCE_URL 저장 (skill-upgrade kitSource로 사용)

### Step 2: 프로젝트 정보 수집
AskUserQuestion: 프로젝트 이름, 설명

### Step 2.5: 서비스 설명 기반 추천

**트리거**: Step 2에서 수집한 description이 5자 이상이면 실행. 미만이면 건너뛰고 Step 3으로.

**절차**:

1. **도메인 매칭**: `domains/_registry.json` 키워드 + 각 `domains/{id}/domain.json`의 keyword triggers 스캔
   - 정확 매칭: 3점 (예: "결제" → fintech)
   - 의미 매칭: 2점 (예: "food delivery" → ecommerce의 "배송"/"주문")
   - 최고 점수 도메인 선택. 동점 시 더 구체적인 도메인 우선
   - 0점이면 `general`
   - 복수 도메인 강하게 매칭 시 컴플라이언스 우선순위: healthcare > fintech > saas > ecommerce > general
   - `keywordPolicy.knownOverlaps` 참조하여 중복 키워드 해소

2. **스택 추천**: 서비스 설명에서 추론한 특성을 아래 의사결정 테이블에 대입. 명확한 신호가 없으면 매칭된 도메인의 `defaultStack` 사용.

**Backend 의사결정**:

| 서비스 특성 | 추천 | 이유 |
|------------|------|------|
| 금융 트랜잭션, 높은 안정성 | spring-boot-kotlin | 타입 안전성, 트랜잭션 생태계 |
| 실시간 처리, 고동시성 | go | goroutine 기반 동시성 |
| 빠른 프로토타이핑, MVP, 풀스택 JS | nodejs-typescript | 빠른 반복, npm 생태계 |
| ML/AI 통합, 데이터 파이프라인 | python-fastapi | Python ML 생태계, 비동기 |
| 관리자 패널, 콘텐츠 중심, 빠른 CRUD | python-django | 내장 어드민, ORM |
| 엔터프라이즈, JVM 선호 | spring-boot-java | 성숙한 생태계 |
| 명확한 신호 없음 | 도메인 defaultStack.backend | 도메인 기본값 |

**Frontend 의사결정**:

| 서비스 특성 | 추천 | 이유 |
|------------|------|------|
| SEO 중요, 사용자 대면 웹 | nextjs | SSR/SSG |
| 대시보드, 관리자 SPA | react-vite | 빠른 빌드, SPA 최적화 |
| 정적 사이트, 블로그, 문서 | astro | 최소 JS |
| Vue 생태계 선호 | vue-nuxt 또는 vue | Nuxt=SSR, Vue=SPA |
| API 전용, 웹 UI 불필요 | none | 불필요 |
| 명확한 신호 없음 | 도메인 defaultStack.frontend | 도메인 기본값 |

**Database 의사결정**:

| 서비스 특성 | 추천 | 이유 |
|------------|------|------|
| 복잡한 관계, ACID 트랜잭션 | postgresql | 고급 기능, 확장성 |
| 읽기 중심, 단순 관계 | mysql | 성능, 단순성 |
| 스키마 유연, 문서 지향 | mongodb | 유연한 스키마 |
| 임베디드, 로컬 프로토타입 | sqlite | 제로 설정 |
| 명확한 신호 없음 | 도메인 defaultStack.database | 도메인 기본값 |

**Cache 의사결정**:

| 서비스 특성 | 추천 | 이유 |
|------------|------|------|
| 세션 관리, pub/sub, 다양한 자료구조 | redis | 범용, 고성능 |
| 단순 key-value 캐시만 | memcached | 단순, 빠름 |
| 저트래픽, MVP | none | 조기 최적화 불필요 |
| 명확한 신호 없음 | 도메인 defaultStack.cache | 도메인 기본값 |

**Message Queue 의사결정**:

| 서비스 특성 | 추천 | 이유 |
|------------|------|------|
| 이벤트 스트리밍, 높은 처리량 | kafka | 스트림 처리 |
| 태스크 큐, 안정적 전달 | rabbitmq | 유연한 라우팅 |
| AWS 생태계 | sqs | 관리형, 간편 |
| 단순 서비스, 비동기 불필요 | none | 불필요 |
| 명확한 신호 없음 | 도메인 defaultStack.messageQueue | 도메인 기본값 |

**Infrastructure 의사결정**:

| 서비스 특성 | 추천 | 이유 |
|------------|------|------|
| 일반적인 개발 환경 | docker-compose | 표준 |
| 대규모 클러스터, 프로덕션급 인프라 | kubernetes | 오케스트레이션 |
| 명확한 신호 없음 | docker-compose | 기본값 |

3. **출력**: 추천 결과를 아래 형식으로 표시

```
📊 서비스 분석 결과

설명: "{description}"

도메인: {icon} {name}
  {compliance 목록 (있으면)}

추천 기술 스택:
  Backend       : {choice} — {reason}
  Frontend      : {choice} — {reason}
  Database      : {choice} — {reason}
  Cache         : {choice} — {reason}
  Message Queue : {choice} — {reason}
  Infrastructure: {choice} — {reason}
```

4. **확인**: AskUserQuestion 1회

```
A. 이대로 진행
B. 일부 수정
C. 직접 선택 (수동 — 기존 방식)
```

**분기 처리**:
- **A (이대로 진행)**: 추천된 도메인 + 스택을 확정. Step 3, Step 4 건너뛰고 Step 5로.
- **B (일부 수정)**: AskUserQuestion으로 수정할 항목 번호 선택:
  ```
  수정할 항목을 선택하세요 (쉼표 구분):
  1. 도메인 ({현재값})
  2. Backend ({현재값})
  3. Frontend ({현재값})
  4. Database ({현재값})
  5. Cache ({현재값})
  6. Message Queue ({현재값})
  7. Infrastructure ({현재값})
  ```
  선택된 항목만 개별 AskUserQuestion (Step 4와 동일한 선택지 제공). 수정 후 최종 확인(Y/N) 1회. Step 3, Step 4 건너뛰고 Step 5로.
- **C (직접 선택)**: Step 2.5 결과 무시. 기존 Step 3 → Step 4 순서대로 진행 (기존 플로우 동일).

### Step 3: 도메인 선택 (Step 2.5에서 확정 시 건너뜀)

**조건**: Step 2.5에서 A(수락) 또는 B(수정 완료) → 이 단계 건너뜀. C(수동) 또는 Step 2.5 스킵 시에만 실행.

`domains/_registry.json` 로드 → AskUserQuestion으로 도메인 선택

### Step 4: 기술 스택 선택 (Step 2.5에서 확정 시 건너뜀)

**조건**: Step 2.5에서 A(수락) 또는 B(수정 완료) → 이 단계 건너뜀. C(수동) 또는 Step 2.5 스킵 시에만 실행.

도메인별 defaultStack 기본값 제안 → AskUserQuestion: 백엔드, 프론트엔드, DB, 캐시, 인프라

**백엔드 선택지**: spring-boot-kotlin, spring-boot-java, nodejs-typescript, python-fastapi, python-django, go, **none** (프론트엔드 전용)

**Python 스택 선택 가이드**:
- `python-fastapi`: 비동기 REST API, 마이크로서비스, ML 모델 서빙 → Pydantic + SQLAlchemy + Alembic
- `python-django`: 관리자 패널 포함 풀스택, ORM 중심, 빠른 프로토타이핑 → DRF + Django ORM
**프론트엔드 선택지**: nextjs, react-vite, vue-nuxt, vue, astro, **none** (백엔드 전용)
**DB 선택지**: mysql, postgresql, mongodb, sqlite, **none** (BaaS 사용 시)

백엔드와 프론트엔드 모두 `none`은 불가 (최소 하나 선택)

### Step 5: 에이전트 팀 구성
스택에 따라 필수 에이전트를 자동 결정한 뒤, 추가 에이전트를 AskUserQuestion으로 선택.

**필수 에이전트 (스택 기반 자동)**:

| 스택 구성 | 필수 에이전트 |
|-----------|-------------|
| 백엔드만 (프론트엔드=none) | pm, backend, code-reviewer |
| 프론트엔드만 (백엔드=none) | pm, frontend, code-reviewer |
| 풀스택 (백엔드+프론트엔드) | pm, backend, frontend, code-reviewer |

**선택 에이전트** (AskUserQuestion multi-select):
planner, db-designer, qa, docs

### Step 5.5: 워크플로우 프로필 선택
AskUserQuestion: Standard (권장, 전체 체이닝) / Fast (리뷰 생략, 프로토타입용)

### Step 5.6: 스킬 프로파일 선택
AskUserQuestion: 스킬 프로파일을 선택하세요:
1. **Full** (전체, 권장) — 모든 스킬 노출
2. **Developer** — 개발 핵심만 (status, backlog, feature, plan, impl, review-pr, merge-pr, hotfix, retro)
3. **Docs-only** — 문서 전용 (status, docs, create)
4. **Custom** — 직접 선택

Custom 선택 시: 전체 스킬 목록에서 multi-select (AskUserQuestion) → `conventions.customSkills` 배열에 저장

--quick 모드: `"full"` 기본값 자동 적용 (질문 없음)

### Step 6: 파일 생성

1. **project.json**: name, description, domain, techStack, agents, conventions (taskPrefix, branchStrategy:git-flow, commitFormat:conventional, prLineLimit:500, testCoverage:80, workflowProfile, skillProfile), createdAt, kitVersion (VERSION 값), kitSource (KIT_SOURCE_URL 또는 기본 repo URL). skillProfile이 "custom"이면 `conventions.customSkills` 배열도 포함
2. **backlog.json**: metadata (lastTaskNumber:0, version:1), summary (전체 0), phases:{}, tasks:{}
3. **CLAUDE.md**: `.claude/templates/CLAUDE.md.tmpl` 마커 치환 (skillProfile 기반 스킬 목록 필터링)
4. **VERSION**: `echo "0.1.0" > VERSION`
5. **README.md**: `.claude/templates/README.md.tmpl` 마커 치환 (기존 README 교체)
6. **docs/api-specs/**: `mkdir -p`
7. **.gitignore** 업데이트 (필요 시)
8. **Git 초기 커밋** (선택): `git add` → `git commit` → `git checkout -b develop`

**Python 스택 선택 시 추가 생성**:
- `python-fastapi`: `pyproject.toml` (FastAPI+uvicorn+SQLAlchemy+pytest+ruff), `app/__init__.py`, `app/main.py`, `app/config.py`, `tests/conftest.py`
- `python-django`: `pyproject.toml` (Django+DRF+pytest+ruff), `manage.py`, `config/settings/base.py`, `config/urls.py`
- 공통: `.python-version`, `alembic.ini` (FastAPI) 또는 초기 migration (Django)
- 컨벤션 참조: `python-project-structure.md`, `python-testing.md`, `python-dependency.md`, `python-patterns.md`

### Step 7: 완료 안내
필수 포함: 생성된 파일 목록, 프로젝트 정보 (이름, 도메인, 기술 스택), 활성 에이전트, Git 원격 저장소 설정 안내, 다음 단계 (/skill-feature, /skill-backlog, /skill-docs)
마지막 줄: "💡 처음이시면 docs/getting-started.md의 '첫 기능 만들기'를 따라해보세요."

## Layered Override 적용
설정 우선순위: 사용자 입력 > domains/{domain}/domain.json > domains/_base/ > 하드코딩 기본값

## 주의사항
- 기존 설정 덮어쓰기 전 확인 필수
- Git 저장소 없으면 생성 권유
- 도메인 변경은 `/skill-domain switch` 사용
