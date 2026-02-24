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

이미 코드베이스가 있는 프로젝트에 AI Crew Kit을 적용하려면:

```bash
/skill-onboard
```

코드베이스를 자동 스캔하여 기술 스택, 도메인을 감지하고 설정 파일을 생성합니다.

| 항목 | skill-init | skill-onboard |
|------|-----------|---------------|
| 대상 | 새 프로젝트 | 기존 코드베이스 |
| 정보 수집 | 대화형 질문 | 코드베이스 자동 스캔 |
| 기존 파일 | 없음 | 백업 후 생성 |
