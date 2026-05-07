---
name: skill-init
description: 프로젝트 초기화 - 요구사항 입력 → 도메인/스택 추천 → 백로그 자동 생성. /skill-init으로 호출합니다.
disable-model-invocation: true
allowed-tools: Bash(git:*), Read, Write, Glob, AskUserQuestion
argument-hint: "[--quick] [--reset]"
complexity-hint: light
---

# skill-init: 프로젝트 초기화

빈 디렉토리에서 새 프로젝트를 시작할 때 사용. **이미 코드가 있는 프로젝트는 `/skill-onboard`를 사용하세요** (자동 스캔 기반).

## 실행 조건
- 사용자가 `/skill-init` 또는 "프로젝트 시작해줘" 요청 시

## 옵션
```
/skill-init           # 새 프로젝트 초기화 (요구사항 우선 대화형)
/skill-init --quick   # 제로 결정 빠른 초기화 (자동 감지 + 기본값)
/skill-init --reset   # 기존 설정 초기화 (재설정)
/skill-init --quick --reset
```

## --quick vs 일반 모드

| 단계 | 일반 모드 (요구사항 우선) | --quick 모드 |
|------|-------------------------|-------------|
| Step 1 환경 검증 | 그대로 + 기존 코드 감지 시 onboard 권장 | 그대로 |
| Step 2 요구사항 입력 | 자유 서술 (한 줄~여러 문단) | 디렉토리명만 사용 (입력 없음) |
| Step 3 정보 보강 | lean 입력일 때만 후속 최대 3질문, rich이면 skip | skip |
| Step 4 프로젝트 메타 | 자동 추출 (요구사항/디렉토리명) → 정정 시에만 입력 | 디렉토리명 자동 |
| Step 5 도메인/스택 추천 | LLM 추론 (registry/매핑 표 1차 근거) → 수락/수정/수동 | 디렉토리명 키워드 매칭 (무음) |
| Step 6 에이전트 팀 | AskUserQuestion multi-select | 자동 |
| Step 7 워크플로우 프로필 | AskUserQuestion 1회 | standard 기본값 |
| Step 8 스킬 프로파일 | AskUserQuestion 1회 | full 기본값 |
| Step 9 백로그 자동 분해 | **opt-in** — Y/N 사전 확인 | skip (빈 백로그) |
| Step 10 파일 생성 | 그대로 | 그대로 |
| Step 11 완료 안내 | 그대로 + 백로그 시작 가이드 | + "/skill-init --reset" 안내 |

### 케이스별 흐름 요약 (일반 모드)

입력 횟수는 **AskUserQuestion / 자유 입력 / Enter 확인**을 모두 포함한 사용자 상호작용 횟수입니다.

| Case | 입력 충실도 | 흐름 | 사용자 입력 횟수 |
|------|-----------|------|----------------|
| 1. rich + 추천 수락 + 백로그 Y(A) | 50자↑ + 키워드 ≥ 2 | 2(요구사항) → 4(이름 Enter) → 5(A) → 6(에이전트) → 7(워크플로우) → 8(스킬) → 9 사전(Y) → 9 결과(A) → 10 | **6-7회** |
| 2. lean + 추천 수락 + 백로그 Y(A) | 50자↓ | 2 → 3(3질문) → 4(이름 Enter) → 5(A) → 6 → 7 → 8 → 9(Y) → 9(A) → 10 | **9-10회** |
| 3. 추천 일부 수정 (B) | rich/lean 무관 | 5(B) → 수정 항목 multi-select → 항목별 1회씩 | Case 1·2 + 2~5회 |
| 4. 직접 선택 (escape hatch C) | rich/lean 무관 | 5(C) → 도메인 → backend → frontend → DB → cache → infra | Case 1·2 + 6회 |
| 5. 백로그 분해 거절 (9 N) | rich/lean 무관 | 9 사전(N) → 9 결과 단계 skip | Case 1·2 - 1회 |
| 6. 백로그 수정 후 진행 (9 B→A) | rich/lean 무관 | 9 결과(B) → 피드백 자유 서술 → 재확인(A) | Case 1·2 + 2회 (최대 4회: B 2회 한도) |
| 7. --quick (파일 감지) | 기존 프로젝트 | 자동 | **0회** |
| 8. --quick (디렉토리명 매칭) | 빈 디렉토리 | 디렉토리명 → 도메인 | **0회** |
| 9. --quick 폴백 | 빈 디렉토리 + 매칭 실패 | 백엔드 1회 질문 | **1회** |

### --quick 자동 감지

**디렉토리명 도메인 매칭** (파일 감지 전 실행):
1. 디렉토리명을 `-`, `_`, 공백으로 분리하여 토큰화
2. `_registry.json`의 각 도메인 keywords와 토큰 매칭
3. 2개 이상 토큰 매칭 시 해당 도메인의 defaultStack 적용 (무음)
4. 매칭 실패 → 파일 기반 감지

예: `patient-appointment` → healthcare / `tenant-billing-app` → saas

**파일 기반 감지 (백엔드)**:
- `build.gradle.kts` → spring-boot-kotlin / `build.gradle` → spring-boot-java / `pom.xml` → spring-boot-java
- `go.mod` → go / `pyproject.toml`/`requirements.txt` → python (FastAPI/Django 자동 판별)
- `package.json` + express/fastify/nestjs → nodejs-typescript

**프론트엔드**: `next.config.*` → nextjs / `vite.config.*` + react → react-vite / `nuxt.config.*` → vue-nuxt / `astro.config.*` → astro / `vue.config.*` → vue

**감지 실패 (빈 디렉토리)**: 백엔드 1회 질문 → 도메인 기본 DB/캐시/인프라 적용

---

## 일반 모드 실행 플로우

### Step 1: 환경 검증

#### 평가 순서 (반드시 다음 순서로)

1. **Git 저장소 확인** — 없으면 `git init -b main`
2. **ai-crew-kit clone 자동 정리** (아래 "표준 진입 플로우" 절) — 검출 + 가드 통과 시 즉시 실행. 통과 후에는 디렉토리가 깨끗해지므로 이후 가드는 자연스럽게 통과.
3. **기존 코드 감지 가드** (자동 정리가 SKIP되거나 비대상일 때만 의미 있음) — 아래 "기존 코드 감지 안내" 절
4. **`project.json` 존재 확인** — 있으면 재초기화 경고 (`--reset` 없으면 진행 여부 확인). `--reset` 모드면 Step 10에서 자동 백업.

| 항목 | 조건 | 처리 |
|------|------|------|
| Git 저장소 | 없음 | `git init -b main` |
| Git remote origin | ai-crew-kit 가리킴 + fingerprint 일치 | 자동 정리 (M1+M2 통과 시) |
| Git remote origin | 사용자 저장소 | 유지 |
| **기존 코드 파일** (자동 정리 후 또는 비대상) | `src/`, `app/`, `lib/`, 빌드 파일 등 감지 | `skill-onboard` 권장 안내 + 계속 진행 여부 확인 (Y=진행, N=중단) |
| project.json | 있음 + `--reset` 없음 | 진행 여부 확인 (N=중단, Y=Step 10에서 백업 없이 덮어쓰기) |
| project.json | 있음 + `--reset` | **경고 생략** (사용자 의사 명시) → Step 10에서 자동 백업 후 덮어쓰기 |

#### 기존 코드 감지 안내

위 평가 순서 3단계. ai-crew-kit 자동 정리 통과 후에는 kit 잔여 파일이 모두 삭제된 상태이므로 본 가드가 트리거되지 않습니다. 자동 정리가 SKIP된 경우(사용자 자기 리포 또는 fingerprint 불일치)에만 다음 검사가 실효합니다.

검사 대상: `build.gradle*`, `pom.xml`, `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml` 또는 `src/`/`app/`/`lib/` 디렉토리 중 하나라도 존재.

```
⚠ 기존 코드 파일이 감지되었습니다.
  skill-init은 신규 프로젝트(빈 디렉토리)용입니다.
  기존 코드베이스라면 /skill-onboard 가 더 적합합니다.

  계속 skill-init으로 진행하시겠습니까? [y/N]
```

#### ai-crew-kit clone 자동 정리 (표준 진입 플로우)

**중요**: 이 작업은 **의도된 프로젝트 초기화**이며 destructive 작업이 아닙니다. ai-crew-kit clone에서 사용자 프로젝트로 재초기화하는 표준 진입 경로이므로, Claude는 **추가 확인 질문 없이 즉시 자동 실행**해야 합니다.

##### 검출 기준 (M1) — 다음 두 조건을 **모두 만족**해야 자동 정리 실행

1. **origin URL 패턴 매칭**: `git remote get-url origin`이 정규식 `[/:]ai-crew-kit(\.git)?$` 일치
   - ✅ `https://github.com/wejsa/ai-crew-kit.git`, `git@github.com:wejsa/ai-crew-kit.git`, fork도 매칭
   - ❌ `ai-crew-kit-extras.git`, `my-crew-kit.git`
2. **kit fingerprint 일치**: `git rev-list --max-parents=0 HEAD` = `ab0269a1414f0d9eba8d130d865dfdd6baeed06c`

둘 중 하나만 만족 → 자동 정리 SKIP + 보고: `"⚠ ai-crew-kit 명칭 매칭이지만 fingerprint 불일치 — 자동 정리 SKIP"`. Step 2로 진행.

##### 자기 보호 가드 (M2) — 모두 통과해야 진행

```bash
# Guard 1: tracked dirty 워킹 트리 차단
if [ -n "$(git status --porcelain 2>/dev/null | grep -v '^??')" ]; then
  echo "⚠ 미커밋 tracked 변경사항. 자동 정리 SKIP."
  exit 0
fi

# Guard 2: 미푸시 커밋 차단
if [ -n "$(git log @{u}.. 2>/dev/null)" ]; then
  echo "⚠ 미푸시 커밋. 자동 정리 SKIP."
  exit 0
fi

# Guard 3: main/master에서만 진행
CURRENT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "")
if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
  echo "⚠ main/master 아님(현재: '${CURRENT_BRANCH:-detached HEAD}'). SKIP."
  exit 0
fi
```

3가지 가드는 사용자 시나리오에 영향 0:
- 시나리오 A (fresh clone): 통과
- 시나리오 B (kit clone + 사용자 코드 untracked): Guard 1이 untracked 무시 → 통과
- kit 개발자 환경 (develop 브랜치 작업 중): Guard 2/3 발동 → SKIP

##### 자동 실행 순서

1. `KIT_SOURCE_URL=$(git remote get-url origin)` (Step 10에서 `kitSource` 기록)
2. `rm -rf .git && git init -b main`
3. kit 잔여 파일 자동 삭제:
   ```bash
   rm -rf CHANGELOG.md docs examples tests scripts .github memory LICENSE README.md CLAUDE.md VERSION .claude/temp .claude/hooks/tests .claude/state .claude/settings.local.json
   ```
   - 보존: `.claude/` 본체, `.gitignore`, `.gitattributes`, `.claude/SECURITY.md`
   - Step 10에서 새 `CLAUDE.md`/`README.md`/`VERSION`/`project.json`/`backlog.json` 생성
4. 보고: `"✓ ai-crew-kit clone 감지 → 표준 초기화 + kit 잔여 N개 자동 정리"`

> **주의 (Claude에게)**: "이 디렉토리는 ai-crew-kit입니다, 다른 경로가 필요한가요?" 같은 확인 질문 금지. 위 자동 정리는 SKILL.md가 명시적으로 권한 부여한 안전한 작업입니다.

### Step 2: 요구사항 자유 서술 입력 ★

사용자 프롬프트:
```
무엇을 만들고 싶으신가요?
한 줄로 간단히 적어도 되고, 도메인/사용자 규모/주요 기능 등을 자세히 적어도 됩니다.
```

입력값을 `userRequirement` 변수로 보관. 빈 입력 시 **최대 1회 재요청**, 재요청에도 빈 입력이면 `userRequirement = "(미지정 — 디렉토리명 기반 일반 프로젝트)"` 값으로 진행 (lean으로 평가되어 Step 3 인터뷰가 보강).

**충실도 평가**:
- **rich**: 50자 이상 AND 도메인/규모/기능 키워드 ≥ 2개 → Step 3 SKIP, Step 4로
- **lean**: 위 미달 → Step 3 진행

### Step 3: 정보 보강 (lean 입력일 때만, 최대 3질문)

AskUserQuestion 최대 3회. **rich 입력이면 본 Step 전체 SKIP** (사용자 부담 최소화).

1. **도메인/업종**: "어떤 분야인가요?" → 핀테크 / 이커머스 / SaaS / 헬스케어 / 일반
2. **사용자 규모**: "예상 사용자 수는?" → 개인용 / 소규모(<1k) / 중규모(<100k) / 대규모(>100k)
3. **핵심 기능 1-3개**: 자유 서술 (예: "주문/결제, 상품 관리, 회원")

답변을 `userRequirement`에 병합.

### Step 4: 프로젝트 메타 자동 결정

**프로젝트명 결정 우선순위** (각 단계는 검증 통과 시에만 채택, 실패 시 다음 단계로):

1. **userRequirement에서 명시적 추출**: `userRequirement`에 "X라는 …", "X 만들고 싶어", "이름은 X" 같이 **고유명사가 명시된 경우에만** LLM이 추출. 명시 없이 LLM이 임의로 작명하지 말 것 (hallucination 방지).
2. **현재 디렉토리 basename**: 1번 실패 시 `basename "$(pwd)"` 사용.
3. **basename 검증**: 다음 중 하나라도 해당하면 무효 처리하고 4번으로 폴백:
   - 무의미 토큰: `.`, `..`, `tmp`, `temp`, `test`, `untitled`, `new-project`, `my-project`
   - 빈 문자열 또는 공백만
   - 단일 글자 (예: `a`, `1`)
4. **사용자 입력 요청**: 1~3 모두 실패 시 AskUserQuestion으로 "프로젝트명을 입력하세요" 1회.
5. 위 결정값을 사용자에게 1줄로 제시 + Enter=수락 / 정정 시 입력.

```
프로젝트명: Tasky (요구사항에서 추출 / 디렉토리명 / 사용자 입력)
   [Enter] 수락 / 입력 시 정정
```

**taskPrefix 결정 알고리즘** (project.schema.json pattern: `^[A-Z][A-Z0-9-]*$` 만족):

1. 프로젝트명에서 영문 알파벳만 추출 (한글/특수문자/숫자 제거)
2. 추출 결과를 **대문자**로 변환
3. 길이 기반 처리:
   - **4-6자**: 그대로 사용 (예: `Tasky` → `TASKY`, `Shop` → `SHOP`)
   - **3자 이하**: 디폴트 `TASK` 사용 (의미 있는 prefix 형성 불가)
   - **7자 이상**: **첫 6자 절단** (예: 영문자만 추출 결과가 `SHOPHUB`(7자) → `SHOPHU`, `SHOPHUBMALL`(11자) → `SHOPHU`). 정보 보존을 위해 4자가 아닌 6자까지 유지.
4. 최종 결과가 schema pattern 위반(예: 영문 0자) → `TASK` 폴백
5. 한글 basename(예: `학생-앱`) → 1단계에서 영문 0자 → `TASK` 폴백, **이 케이스는 모호하므로 일반 모드에서 1회 정정 입력 받음** (`--quick`은 `TASK` 자동 확정)

`{prefix}` 결과를 사용자에게 1줄 제시. 일반 모드에서 다음 케이스만 정정 입력 받음: ① 한글/영문0자 폴백 ② 다른 프로젝트와 prefix 충돌 ③ 사용자가 명시적으로 정정. 그 외에는 자동 확정.

**설명**: `userRequirement` 첫 문장 자동 사용. 빈 입력이거나 추출 실패 시 빈 문자열 (schema에서 description은 optional).

> 결과: 일반적으로 추가 입력 0회. 무의미한 디렉토리명/한글 케이스에서만 1회 정정.

### Step 5: 도메인 + 스택 추천 ★

`userRequirement`를 LLM이 분석하여 도메인 + 스택을 추천. 결과 변동을 줄이기 위해 아래 **결정 규칙 표**를 1차 근거로 사용 (재현성 정책).

#### 재현성 결정 규칙 (LLM이 우선 적용)

| 항목 | 결정 근거 (우선순위 순) |
|---|---|
| 도메인 | `_registry.json.keywords` 매칭 → 동률 시 `keywordPolicy` → 모호 시 LLM 추론 |
| Backend | 도메인 `defaultStack.backend` → 요구사항 키워드 override (실시간/채팅/스트리밍 → `nodejs-typescript`, ML/데이터/AI → `python-fastapi`, 고성능/마이크로서비스 → `go`, 엔터프라이즈/금융/트랜잭션 → `spring-boot-kotlin`, 관리자 패널/CRUD → `python-django`) |
| Frontend | 도메인 `defaultStack.frontend` → SEO/사용자 대면 → `nextjs`, 대시보드 SPA → `react-vite`, API 전용 → `none` |
| Database | 도메인 `defaultStack.database` → 트랜잭션 → `postgresql`, 단순 관계 → `mysql`, 문서지향 → `mongodb`, 로컬/MVP → `sqlite` |
| Cache | 도메인 `defaultStack.cache` → 세션/pub-sub → `redis`, 단순 KV → `memcached`, 저트래픽 → `none` |
| Message Queue | 도메인 `defaultStack.messageQueue` → 스트리밍 → `kafka`, 태스크 큐 → `rabbitmq`, AWS → `sqs`, 비동기 불필요 → `none` |
| Infrastructure | `docker-compose` 기본, 대규모 클러스터 → `kubernetes` |

LLM 프롬프트 끝에 1줄 명시: **"Be deterministic. Prefer registry mappings over creative inference."**

#### 출력 형식

```
📊 요구사항 분석

요구사항 요약: "{한 줄 요약}"

도메인: {icon} {name} ({근거 1줄})
  컴플라이언스: {목록 — 있으면}

추천 기술 스택:
  Backend       : {choice} — {근거}
  Frontend      : {choice} — {근거}
  Database      : {choice} — {근거}
  Cache         : {choice} — {근거}
  Message Queue : {choice} — {근거}
  Infrastructure: {choice} — {근거}
```

#### 사용자 확인 (AskUserQuestion 1회)

```
A. 이대로 진행
B. 일부 수정
C. 직접 선택 (수동 — escape hatch)
```

- **A**: 추천 확정. Step 6으로.
- **B**: 수정할 항목 multi-select → 항목별 AskUserQuestion → 최종 확인 → Step 6으로.
- **C (escape hatch)**: 추천 무시, 도메인 수동 선택 → 도메인별 defaultStack 기본값 → Backend/Frontend/DB/Cache/Infrastructure 개별 선택. 기존 수동 흐름과 동일.

**스택 선택지 (escape hatch C에서 사용)**:
- Backend: spring-boot-kotlin, spring-boot-java, nodejs-typescript, python-fastapi, python-django, go, **none**
- Frontend: nextjs, react-vite, vue-nuxt, vue, astro, **none**
- Database: mysql, postgresql, mongodb, sqlite, **none**
- Backend와 Frontend 모두 `none`은 불가 (최소 하나)
- **Python 가이드**: `python-fastapi`(비동기 API/ML 서빙) vs `python-django`(관리자 패널/풀스택)

### Step 6: 에이전트 팀 구성

스택 기반 자동 + multi-select.

| 스택 구성 | 필수 에이전트 |
|-----------|-------------|
| 백엔드만 (frontend=none) | pm, backend, code-reviewer |
| 프론트엔드만 (backend=none) | pm, frontend, code-reviewer |
| 풀스택 | pm, backend, frontend, code-reviewer |

**선택 (multi-select)**: planner, db-designer, qa, docs

### Step 7: 워크플로우 프로필 선택
AskUserQuestion: Standard (권장, 전체 체이닝) / Fast (리뷰 생략, 프로토타입용)

### Step 8: 스킬 프로파일 선택

1. **Full** (전체, 권장)
2. **Developer** (status, backlog, feature, plan, impl, review-pr, merge-pr, hotfix, retro)
3. **Docs-only** (status, docs, create)
4. **Custom** — multi-select → `conventions.customSkills` 배열 저장

--quick: `"full"` 자동.

### Step 9: 백로그 자동 분해 (opt-in) ★

#### 사전 확인 (필수)

```
요구사항을 백로그(Phase + Task)로 자동 분해할까요?
[Y] 진행 (LLM이 phase/task 후보 생성 → 사용자 확인 후 backlog.json 채움)
[N] skip (빈 백로그로 종료)
```

`N` 선택 시 본 Step 전체 SKIP → Step 10에서 빈 backlog.json 생성. **(런타임 토큰 절감용 기본 옵션)**

#### Y 분기: LLM 분해 규칙

**입력**: `userRequirement` (Step 2+3 병합), 결정된 도메인/스택

**Phase 고정 4-카테고리 템플릿** (해당 없으면 skip, 순서 강제):
1. **PHASE-1: 기반/인프라** (인증, DB 스키마, 멀티테넌시, 공통 모듈)
2. **PHASE-2: 핵심 도메인** (제품 정체성을 이루는 entity/use case)
3. **PHASE-3: 부가 기능** (검색/필터/알림/통계 등)
4. **PHASE-4: 운영/품질** (감사 로그, 모니터링, 관리자 도구, 회귀 테스트)

**Task 분해 규칙**:
- 각 phase에 task 3-7개 (LLM이 더 만들면 통합 지시)
- 전체 task 10-25개로 수렴
- task `description` **1-2줄 강제** (한 줄 요약 + 핵심 산출물). 길어지면 LLM에 재요청.
- task ID: phase 순서 → task 생성 순서로 `{PREFIX}-001`부터

**Priority 결정 규칙** (강제):
- PHASE-1 / PHASE-2 task = `high`
- PHASE-3 task = `medium`
- PHASE-4 task = `low`
- 도메인 컴플라이언스(GDPR/HIPAA/PCI-DSS) 관련 = `critical`로 격상

**LLM 프롬프트 끝**: **"Be deterministic. Same requirements must yield same phase structure and similar task count."**

**각 task 필드** (backlog.schema.json 준수 — required: `id`, `title`, `status`, `priority`, `createdAt`):
```json
{
  "id": "{PREFIX}-{NNN}",
  "title": "...",
  "description": "1-2줄 요약 + 핵심 산출물",
  "status": "todo",
  "type": "feature",
  "priority": "critical|high|medium|low",
  "phase": <int>,
  "dependencies": [],
  "createdAt": "<ISO8601>",
  "assignee": null,
  "assignedAt": null,
  "lockTTL": 3600,
  "lockedFiles": [],
  "steps": [],
  "workflowState": null
}
```

> **의도적 부재 필드**:
> - `currentStep`: schema `minimum: 1`이므로 0은 위반. `skill-plan`이 task를 픽업할 때 1로 설정 (필드 부재 = 미시작)
> - `specFile`: schema `type: "string"`이라 null 불가, init 시점엔 spec 파일이 없으므로 필드 자체를 omit (`skill-feature`/`skill-plan`이 필요 시 채움)

**phase 객체 생성** (backlog.json `phases` 필드, schema는 `name`/`status` required, key는 정수 문자열):
```json
"phases": {
  "1": { "name": "기반/인프라", "description": "...", "status": "todo" },
  "2": { "name": "핵심 도메인", "description": "...", "status": "todo" },
  "3": { "name": "부가 기능", "description": "...", "status": "todo" },
  "4": { "name": "운영/품질", "description": "...", "status": "todo" }
}
```
- 키는 phase 번호의 정수 문자열 (`"1"`~`"4"`)
- task에 매칭되지 않는 phase는 생략 (LLM이 분해 결과에 phase 번호를 사용한 것만 채움)
- `name`은 4-카테고리 고정 명칭 (기반/인프라, 핵심 도메인, 부가 기능, 운영/품질)
- `description`은 LLM이 해당 프로젝트 맥락에 맞춰 1줄 작성 (예: PHASE-2의 "주문/결제/배송 핵심 흐름"). 채울 내용 없으면 생략 가능 (schema에서 optional).
- `status`는 모두 `"todo"`로 초기화 (schema enum: `todo`/`in_progress`/`done` 3종만)

#### 사용자 확인 (분해 결과 출력 후)

```
📋 백로그 분해 결과 (총 {N}개 task / {M}개 phase)

PHASE-1: 기반/인프라
  TASK-001 [high] 인증/JWT 발급
  TASK-002 [high] 사용자 스키마 + 회원가입
  ...

PHASE-2: 핵심 도메인
  TASK-005 [high] ...

[A] 이대로 진행
[B] 수정 요청 (자유 서술)
[C] 빈 백로그로 진행
```

- **A**: 그대로 backlog.json에 채워 Step 10으로.
- **B**: 사용자 피드백을 LLM에 전달하여 재생성 → 재확인. **최대 2회까지만 재시도** (1차/2차 재생성). 3회차 재확인부터는 [B] 옵션 비활성화 → [A] 진행 또는 [C] 빈 백로그 중 선택만 허용. 무한 루프 및 토큰 폭증 방지.
- **C**: 본 분해 결과 폐기, 빈 backlog.json으로 Step 10으로.

### Step 10: 파일 생성

#### 사전 처리 (--reset 모드일 때만)

`--reset` 옵션으로 진입한 경우, 기존 설정을 안전하게 백업한 뒤 새로 생성합니다.

1. 타임스탬프 백업 디렉토리 생성: `.claude/temp/reset-backup-$(date +%Y%m%d-%H%M%S)/`
2. 다음 파일이 존재하면 백업 디렉토리로 이동:
   - `project.json` → 백업
   - `.claude/state/backlog.json` → 백업 (특히 진행 중 task가 있으면 새 분해 결과와 충돌 위험 차단)
   - `CLAUDE.md`, `README.md`, `VERSION` → 백업
3. 백업 완료 후 사용자에게 1줄 보고: `"✓ 기존 설정을 .claude/temp/reset-backup-{timestamp}/ 에 백업했습니다."`
4. 이후 1~8 단계로 진행 (덮어쓰기가 아닌 새로 쓰기 형태가 됨)

> 일반 모드(--reset 없음)에서 기존 `project.json`이 발견되면 Step 1 환경 검증에서 이미 경고하고 사용자가 진행을 선택했을 것입니다. Step 10에서는 추가 백업 없이 덮어씁니다 (사용자 의사 확정).

#### 파일 생성 절차

1. **project.json**: name, description, domain, techStack, agents, conventions (taskPrefix, branchStrategy:git-flow, commitFormat:conventional, prLineLimit:500, testCoverage:80, workflowProfile, skillProfile), createdAt, kitVersion, kitSource. skillProfile=`custom`이면 `conventions.customSkills` 포함
   - **`kitSource` 결정 규칙**:
     - Step 1 ai-crew-kit 자동 정리를 거친 경우: `KIT_SOURCE_URL` 값 사용
     - 자동 정리 미발동(사용자 자기 리포로 시작 또는 git remote 미설정)인 경우: `"https://github.com/wejsa/ai-crew-kit"` 기본값 (kit 시드 출처 문서화 목적)
2. **backlog.json**:
   - **공통**: `metadata`는 `{ "lastTaskNumber": <N>, "version": 1, "projectPrefix": "<PREFIX>", "createdAt": "<ISO8601>", "updatedAt": "<ISO8601>" }`
   - Step 9를 **N/C**로 종료한 경우: `lastTaskNumber: 0`, `summary: { total:0, done:0, inProgress:0, review:0, todo:0 }`, `phases: {}`, `tasks: {}`
   - Step 9를 **Y(A)**로 종료한 경우:
     - `lastTaskNumber` = 생성 task 수
     - `summary.todo` = 생성 task 수, `summary.total` = 생성 task 수, 나머지 0
     - `phases` = Step 9 분해 결과의 phase 객체 (위 Step 9의 phase JSON 형식 그대로)
     - `tasks` = task ID(`{PREFIX}-001` …)를 key로, Step 9 task 객체를 value로
3. **CLAUDE.md**: `.claude/templates/CLAUDE.md.tmpl` 마커 치환
4. **VERSION**: `echo "0.1.0" > VERSION`
5. **README.md**: `.claude/templates/README.md.tmpl` 마커 치환
6. **docs/api-specs/**: `mkdir -p`
7. **.gitignore** 업데이트
8. **Git 초기 커밋** (선택): `git add` → `git commit` → `git checkout -b develop`

**Python 스택 시 추가 생성**:
- `python-fastapi`: `pyproject.toml`, `app/__init__.py`, `app/main.py`, `app/config.py`, `tests/conftest.py`
- `python-django`: `pyproject.toml`, `manage.py`, `config/settings/base.py`, `config/urls.py`
- 공통: `.python-version`, `alembic.ini`(FastAPI) / 초기 migration(Django)

### Step 11: 완료 안내

필수 포함:
- 생성된 파일 목록
- 프로젝트 정보 (이름, 도메인, 기술 스택)
- 활성 에이전트
- Git 원격 저장소 설정 안내
- **백로그 시작 가이드** (Step 9를 Y로 진행한 경우):
  ```
  ✓ 백로그에 {N}개 task가 준비되었습니다.
    /skill-plan 으로 첫 번째 task부터 시작하세요.
  ```
- 다음 단계 (`/skill-feature`, `/skill-backlog`, `/skill-docs`)

마지막 줄 (kitVersion 동적 치환):
```
"💡 처음이시면 https://github.com/wejsa/ai-crew-kit/blob/v{kitVersion}/docs/getting-started.md 의 '첫 기능 만들기'를 따라해보세요."
```

> kit 가이드 문서는 사용자 프로젝트에 포함되지 않습니다. ai-crew-kit GitHub 리포의 `docs/`에서 참조. `kitVersion` 태그가 GitHub에 없을 경우 `blob/main` 안내.

## Layered Override 적용
설정 우선순위: 사용자 입력 > domains/{domain}/domain.json > domains/_base/ > 하드코딩 기본값

## 재현성(Determinism) 정책

동일 요구사항으로 두 번 초기화하면 핵심 구조는 동일해야 한다. Step 5 결정 규칙 표 + Step 9 phase 4-카테고리 템플릿 + priority 강제 규칙으로 안정화. LLM 프롬프트에 "Be deterministic" 명시.

**검증 기준**:
- ✅ 반드시 동일: 도메인, backend/database, phase 4-카테고리 구조, task 개수 ±2, priority 분포
- ⚠️ 변동 허용: task wording, cache/messageQueue 세부 값

## 주의사항
- 기존 설정 덮어쓰기 전 확인 필수
- Git 저장소 없으면 생성 권유
- 도메인 변경은 `/skill-domain switch` 사용
- 기존 코드 감지 시 `/skill-onboard` 권장
