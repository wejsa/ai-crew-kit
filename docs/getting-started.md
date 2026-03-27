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
/skill-init

# 빠른 시작 (제로 결정 — 자동 감지 + 기본값)
/skill-init --quick
```

## 초기화 흐름

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

> **--quick 모드**: 2~5단계를 자동 감지/기본값으로 건너뛰어 즉시 시작합니다. 나중에 `/skill-init --reset`으로 재설정할 수 있습니다.

## 기존 프로젝트 온보딩

이미 코드베이스가 있는 프로젝트에 AI Crew Kit을 적용하려면 `/skill-onboard`를 사용합니다.

### 준비

```bash
# 1. AI Crew Kit 스킬 복사
git clone https://github.com/wejsa/ai-crew-kit.git
cp -r ai-crew-kit/.claude my-existing-project/

# 2. 프로젝트에서 Claude Code 실행
cd my-existing-project
claude

# 3. 온보딩 실행
/skill-onboard
```

### 온보딩 흐름

```
/skill-onboard 실행
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
/skill-onboard              # 전체 온보딩 (스캔 + 설정 생성)
/skill-onboard --scan-only  # 스캔만 수행 (설정 생성 없음, 분석 결과만 확인)
```

> `--scan-only`는 적용 전에 감지 결과를 미리 확인하고 싶을 때 유용합니다.

### 온보딩 후 다음 단계

```bash
# 1. 기존 기능을 Task로 등록
/skill-feature "기능명"

# 2. 백로그 확인
/skill-backlog

# 3. 작업 시작
/skill-plan
```

### skill-init과의 차이

| 항목 | skill-init | skill-onboard |
|------|-----------|---------------|
| 대상 | 새 프로젝트 | 기존 코드베이스 |
| 정보 수집 | 대화형 질문 | 코드베이스 자동 스캔 |
| 기존 파일 | 없음 | 백업 후 생성 |
