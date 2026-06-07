# 설치 및 시작하기

> [← README로 돌아가기](../README.md)

## 요구사항

| 구분 | 요구사항 |
|------|---------|
| **필수** | [Claude Code](https://claude.ai/download) CLI |
| **권장** | Git 2.30+ |

> **참고**: Claude Code가 파일을 읽고 직접 수행하므로 Node.js, Python 등 외부 런타임은 불필요합니다.

## 설치 단계

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
# 대화형 (모든 설정을 직접 선택)
/crew-init

# 빠른 시작 (제로 결정 — 자동 감지 + 기본값)
/crew-init --quick
```

## 초기화 흐름 (v2.1.0+, 요구사항 우선)

```
/crew-init 실행
    │
    ├── 1. 환경 검증 + ai-crew-kit clone 자동 정리 (해당 시)
    │       ├── kit 검출 (origin URL + initial commit fingerprint)
    │       ├── 자기 보호 가드 (더티/미푸시/비-main 차단)
    │       ├── kit 히스토리 제거 (rm -rf .git && git init -b main)
    │       └── kit 잔여 14종 자동 삭제
    │
    ├── 2. 요구사항 자유 서술 입력 ★ (한 줄 또는 여러 문단)
    │       예: "B2B SaaS로 팀 협업용 칸반 보드. 멀티테넌시 필수,
    │             50개 회사/회사당 100명, GDPR 대응."
    │       → 충실도 평가 (rich/lean)
    │
    ├── 3. 정보 보강 (lean 입력일 때만 최대 3질문)
    │       └── 도메인 / 사용자 규모 / 핵심 기능
    │
    ├── 4. 프로젝트 메타 자동 결정 (이름/taskPrefix/설명)
    │       └── 5단계 폴백 + sanitization
    │
    ├── 5. 도메인 + 스택 LLM 추천 ★
    │       ├── 재현성 결정 규칙 표 (registry/매핑 1차 근거)
    │       └── [A] 수락 / [B] 일부 수정 / [C] 직접 선택 (escape hatch)
    │
    ├── 6. 에이전트 팀 구성 (스택 기반 자동 + 선택)
    │
    ├── 7. 워크플로우 프로필 (standard / fast)
    │
    ├── 8. 스킬 프로파일 (full / developer / docs-only / custom)
    │
    ├── 9. 백로그 자동 분해 (opt-in) ★ — 사전 Y/N 확인
    │       └── Phase 4-카테고리 고정 템플릿
    │           ├── PHASE-1 기반/인프라
    │           ├── PHASE-2 핵심 도메인
    │           ├── PHASE-3 부가 기능
    │           └── PHASE-4 운영/품질
    │
    ├── 10. 파일 생성
    │       ├── .claude/state/project.json (kitSource = ai-crew-kit URL)
    │       ├── backlog.json (Step 9 결과 또는 빈 객체)
    │       ├── CLAUDE.md / README.md / VERSION
    │       └── --reset 시: .claude/temp/reset-backup-{ts}-{pid}/ + MANIFEST.txt
    │
    └── 11. 완료 안내 (백로그 시작 가이드 또는 빈 백로그 안내)
```

> **--quick 모드**: Step 2~9를 자동 감지/기본값으로 건너뛰어 즉시 시작합니다 (디렉토리명 기반 도메인 매칭 → 파일 감지 → 빈 백로그). 나중에 `/crew-init --reset`으로 재설정할 수 있습니다.
>
> **재현성**: 동일 요구사항으로 두 번 초기화하면 도메인/Backend/Database/Phase 4-카테고리 구조/priority 분포는 결정적으로 동일. Task 개수(±2)와 wording은 LLM sampling 한계로 경험적 관측 (SLA 아님).

> **1단계 자동 정리**: ai-crew-kit clone에서 시작한 경우 kit dev 잡티 14종(CHANGELOG, docs, examples, tests, scripts, .github, memory, LICENSE, README.md, CLAUDE.md, VERSION, .claude/temp, .claude/hooks/tests, .claude/state, .claude/settings.local.json)이 추가 확인 없이 자동 삭제되어 깨끗한 사용자 프로젝트로 시작합니다. README.md/CLAUDE.md/VERSION은 Step 6에서 사용자 프로젝트용으로 새로 생성됩니다. **검출 기준**: `git remote origin`이 `[/:]ai-crew-kit(\.git)?$` 매칭 + initial commit SHA가 `ab0269a14...` (kit fingerprint)와 일치. **가드**: 더티 워킹 트리/미푸시 커밋/비-main 브랜치 중 하나라도 해당하면 정리 SKIP하고 일반 진행 (kit 개발자 보호). kit 가이드 문서(getting-started, customization 등)는 GitHub 리포에서 항상 참조 가능 — `project.json.kitSource`로 기록됨.

### Python 프로젝트로 시작하기

```bash
# FastAPI 프로젝트 (비동기 REST API)
/crew-init
# → 도메인: general
# → 백엔드: python-fastapi
# → 자동 생성: pyproject.toml, app/ 구조, tests/conftest.py, alembic/

# Django 프로젝트 (관리자 패널 + REST API)
/crew-init
# → 도메인: general
# → 백엔드: python-django
# → 자동 생성: pyproject.toml, manage.py, config/, apps/
```

> Python 컨벤션 4개 (`python-project-structure`, `python-testing`, `python-dependency`, `python-patterns`)가 자동으로 적용됩니다.

## 기존 프로젝트 온보딩

이미 코드베이스가 있는 프로젝트에 AI Crew Kit을 적용하려면 `/crew-onboard`를 사용합니다.

### 준비

**권장 경로 (시나리오 A — `.claude/`만 복사, 가장 깨끗)**:

```bash
# 1. AI Crew Kit 스킬 복사
git clone https://github.com/wejsa/ai-crew-kit.git /tmp/ai-crew-kit
cp -r /tmp/ai-crew-kit/.claude my-existing-project/

# 2. 프로젝트에서 Claude Code 실행
cd my-existing-project
claude

# 3. 온보딩 실행
/crew-onboard
```

**대안 경로 (시나리오 B — kit clone에 사용자 코드 함께 두기)**:

```bash
# kit을 그대로 clone하고 그 안에서 작업
git clone https://github.com/wejsa/ai-crew-kit.git my-project
cd my-project
# 사용자 코드를 src/, app/, lib/ 등 비충돌 경로로 복사
# (docs/, tests/, scripts/, .github/는 자동 정리 대상이므로 충돌 주의)
claude
/crew-onboard
```

> 시나리오 B에서 `/crew-onboard`는 사전 조건 단계에서 ai-crew-kit clone을 자동 감지하여 `kit 잔여 파일 자동 정리`를 먼저 수행합니다 (crew-init과 동일). 사용자 코드가 `src/`/`app/`/`lib/` 등 비충돌 경로면 안전하나, 동일 경로(`docs/`, `tests/` 등)에 사용자 콘텐츠가 있으면 함께 삭제되므로 의심 시 `tar czf .pre-onboard-backup-$(date +%s).tar.gz docs tests scripts .github` 등으로 사전 백업하세요.

### 온보딩 흐름

```
/crew-onboard 실행
    │
    ├── 0. 사전 조건 (Git 저장소 + ai-crew-kit clone 자동 정리 — 해당 시)
    │       └── kit 검출+가드 통과 시 kit 잔여 자동 삭제 (crew-init과 동일)
    │
    ├── 1. 코드베이스 자동 스캔
    │       ├── 패키지 매니저 (package.json, build.gradle 등)
    │       ├── 프론트엔드 (Next.js, React, Vue 등)
    │       ├── 데이터베이스 (docker-compose, 의존성)
    │       ├── 캐시/메시지큐 (Redis, Kafka 등)
    │       ├── 빌드 명령어 (build, test, lint)
    │       └── 도메인 추천 (키워드 매칭 점수)
    │
    ├── 2. 스캔 결과 확인 (사용자 검토/수정)
    │
    ├── 3. 추가 정보 입력 (프로젝트 설명, 에이전트 선택)
    │
    ├── 4. 기존 파일 백업 (README.md → README.md.bak)
    │
    ├── 5. 설정 파일 생성
    │       ├── .claude/state/project.json
    │       ├── .claude/state/backlog.json
    │       ├── CLAUDE.md
    │       ├── README.md  (프로젝트 전용)
    │       └── VERSION    (0.1.0)
    │
    └── 6. 완료 → 다음 단계 안내
```

### 옵션

```bash
/crew-onboard              # 전체 온보딩 (스캔 + 설정 생성)
/crew-onboard --scan-only  # 스캔만 수행 (설정 생성 없음, 분석 결과만 확인)
```

> `--scan-only`는 적용 전에 감지 결과를 미리 확인하고 싶을 때 유용합니다.

### 온보딩 후 다음 단계

```bash
# 1. 기존 기능을 Task로 등록
/crew-feature "기능명"

# 2. 백로그 확인
/crew-backlog

# 3. 작업 시작
/crew-plan
```

### crew-init과의 차이

| 항목 | crew-init | crew-onboard |
|------|-----------|---------------|
| 대상 | 새 프로젝트 | 기존 코드베이스 |
| 정보 수집 | 대화형 질문 | 코드베이스 자동 스캔 |
| 기존 파일 | 없음 | 백업 후 생성 |

---

## 첫 기능 만들기

프로젝트 초기화가 끝났으면, 아래 5단계로 첫 기능을 만들어보세요.

### Step 1: 기능 기획
```
/crew-feature "사용자 인증"
```

**생성되는 것**: `docs/requirements/{TASK-ID}-spec.md` (요구사항 문서)
**다음 행동**: 요구사항 문서를 검토하고 승인하면 자동으로 Step 2로 진행

### Step 2: 설계 및 스텝 계획
```
/crew-plan
```

**생성되는 것**: `.claude/temp/{TASK-ID}-plan.md` (설계 + 스텝 분리)
**확인할 것**: 스텝별 파일 목록, 예상 라인 수, 의존성
**다음 행동**: 계획을 승인하면 자동으로 Step 3로 진행

### Step 3: 코드 구현
```
/crew-impl (자동 호출됨)
```

**생성되는 것**: feature 브랜치, 코드, PR
**확인할 것**: PR 링크가 출력됨 → GitHub에서 확인 가능
**다음 행동**: 자동으로 리뷰 진행

### Step 4: 코드 리뷰
```
/crew-review-pr {PR번호} (자동 호출됨)
```

**생성되는 것**: PR에 다관점 리뷰 코멘트
**CRITICAL 이슈 시**: 자동 수정 시도 (crew-fix)
**다음 행동**: 리뷰 통과 시 자동 머지

### Step 5: 머지 완료
```
/crew-merge-pr {PR번호} (자동 호출됨)
```

**결과**: Squash 머지, Task 상태 업데이트
**다음 스텝이 있으면**: 자동으로 Step 3부터 반복

### 막혔을 때
- **빌드 실패**: 에러 로그 확인 후 수정, "이어서 진행해줘" 또는 `/crew-impl --retry`
- **스텝 건너뛰기**: `/crew-impl --skip` (빌드 실패 시에만)
- **현재 상태 확인**: `/crew-status`
- **백로그 확인**: `/crew-backlog dashboard`
- **기타 에러**: CLAUDE.md "에러 복구 프로토콜"에 10가지 에러 유형별 복구 방법이 안내됩니다.
