---
name: skill-init
description: 프로젝트 초기화 - 도메인 선택 + 자동 셋업
disable-model-invocation: true
allowed-tools: Bash(git:*), Read, Write, Glob, AskUserQuestion
argument-hint: "[--reset]"
---

# skill-init: 프로젝트 초기화

## 실행 조건
- 사용자가 `/skill-init` 또는 "프로젝트 시작해줘" 요청 시

## 옵션
```
/skill-init           # 새 프로젝트 초기화
/skill-init --reset   # 기존 설정 초기화 (재설정)
```

## 실행 플로우

### Step 1: 환경 검증

```bash
# Git 저장소 확인
git status

# 기존 설정 파일 확인
ls .claude/state/project.json
ls CLAUDE.md
```

**검증 항목:**
| 항목 | 조건 | 처리 |
|------|------|------|
| Git 저장소 | 없음 | 생성 여부 확인 |
| project.json | 있음 | 재초기화 경고 (--reset 없으면) |
| CLAUDE.md | 있음 | 백업 여부 확인 |

**기존 설정 발견 시:**
```
## ⚠️ 기존 설정 발견

현재 디렉토리에 이미 프로젝트 설정이 있습니다:
- `.claude/state/project.json`
- `CLAUDE.md`

초기화하면 기존 설정이 덮어쓰기됩니다.
계속하시겠습니까?
```

### Step 2: 프로젝트 정보 수집

**AskUserQuestion 사용:**

```
## 프로젝트 기본 정보

### 프로젝트 이름
예: my-project, payment-service

### 프로젝트 설명
예: 사용자 인증 및 권한 관리 서비스
```

### Step 3: 도메인 선택

**도메인 목록 로드:**
```bash
# domains/_registry.json에서 로드
cat .claude/domains/_registry.json
```

**AskUserQuestion 사용:**

```
## 도메인 선택

프로젝트에 맞는 도메인을 선택해주세요:

1. 🏦 fintech    — 결제/정산/금융 서비스
2. 🛒 ecommerce  — 이커머스/마켓플레이스
3. 🏥 healthcare — 의료/헬스케어 (beta)
4. ☁️ saas       — SaaS/B2B 플랫폼 (beta)
5. 🔧 general    — 범용 (도메인 특화 없음)

각 도메인은 맞춤형 참고자료, 체크리스트, 템플릿을 제공합니다.
```

### Step 4: 기술 스택 선택

**도메인별 기본값 제안:**
```json
// 도메인별 defaultStack 참조
{
  "fintech": {
    "backend": "spring-boot-kotlin",
    "database": "mysql",
    "cache": "redis"
  },
  "ecommerce": {
    "backend": "spring-boot-kotlin",
    "frontend": "nextjs",
    "database": "mysql"
  }
}
```

**AskUserQuestion 사용:**

```
## 기술 스택 선택

### 백엔드
- Spring Boot 3 (Kotlin) ← fintech 기본값
- Spring Boot 3 (Java)
- Node.js (TypeScript)
- Go

### 프론트엔드
- Next.js
- React
- Vue
- None

### 데이터베이스
- MySQL
- PostgreSQL
- MongoDB

### 캐시
- Redis
- None

### 인프라
- Docker + Compose
- Kubernetes
- None
```

### Step 5: 에이전트 팀 구성

**AskUserQuestion 사용:**

```
## 에이전트 팀 구성

### 기본 활성화 (필수)
✅ 🎯 agent-pm — 프로젝트 총괄, 태스크 분배, 진행 관리
✅ ⚙️ agent-backend — API 설계, 비즈니스 로직, 서버 개발
✅ 👀 agent-code-reviewer — 코드 품질 검토, 보안 점검, 개선 제안

### 선택 에이전트 (다중 선택 가능)

**📋 기획/설계**
☐ 📝 agent-planner — 요구사항 분석, 기능 명세, 유저 스토리 작성
☐ 🗄️ agent-db-designer — ERD 설계, 테이블 정규화, 인덱스 전략

**💻 개발**
☐ 🎨 agent-frontend — UI/UX 구현, 컴포넌트 개발, 상태 관리
   (프론트엔드 스택 선택 시 자동 활성화)

**🔍 품질/문서**
☐ 🧪 agent-qa — 테스트 케이스 작성, E2E 테스트, 품질 검증
☐ 📚 agent-docs — API 문서, README, 기술 문서 작성
```

### Step 6: 파일 생성

**생성 항목:**

1. **project.json 생성**
```json
{
  "name": "{프로젝트명}",
  "description": "{설명}",
  "domain": "{선택된 도메인}",
  "techStack": {
    "backend": "{백엔드}",
    "frontend": "{프론트엔드}",
    "database": "{DB}",
    "cache": "{캐시}",
    "infrastructure": "{인프라}"
  },
  "agents": {
    "enabled": ["pm", "backend", "code-reviewer", ...],
    "disabled": [...]
  },
  "conventions": {
    "taskPrefix": "{도메인별 기본값}",
    "branchStrategy": "git-flow",
    "commitFormat": "conventional",
    "prLineLimit": 500,
    "testCoverage": 80
  },
  "createdAt": "{timestamp}"
}
```

2. **backlog.json 초기화**
```json
{
  "metadata": {
    "lastTaskNumber": 0,
    "createdAt": "{timestamp}",
    "updatedAt": "{timestamp}"
  },
  "summary": {
    "total": 0,
    "done": 0,
    "inProgress": 0,
    "review": 0,
    "todo": 0
  },
  "phases": {},
  "tasks": {}
}
```

3. **CLAUDE.md 생성**
```bash
# 템플릿 로드
cat .claude/templates/CLAUDE.md.tmpl

# 마커 치환 (project.json + domain 설정 기반)
# {{PROJECT_NAME}} → 프로젝트명
# {{DOMAIN_SECTION}} → 도메인별 설정
# 등...
```

4. **.gitignore 업데이트** (필요 시)

5. **Git 초기 커밋** (선택)
```bash
git add .claude/state/ CLAUDE.md
git commit -m "chore: 프로젝트 초기화 (AI Crew Kit)"
```

### Step 7: 완료 안내

```
## ✅ 프로젝트 초기화 완료

### 생성된 파일
- `.claude/state/project.json` — 프로젝트 설정
- `.claude/state/backlog.json` — 백로그 (빈 상태)
- `CLAUDE.md` — AI 지시문

### 프로젝트 정보
- **이름**: {프로젝트명}
- **도메인**: {도메인} ({도메인 아이콘})
- **기술 스택**: {백엔드} + {프론트} + {DB}

### 활성화된 에이전트
- 🎯 agent-pm
- ⚙️ agent-backend
- 👀 agent-code-reviewer
- {추가 에이전트...}

### 다음 단계
1. 새 기능 기획: `/skill-feature "기능명"` 또는 "새 기능 기획해줘"
2. 백로그 확인: `/skill-backlog` 또는 "백로그 보여줘"
3. 참고자료 조회: `/skill-docs` 또는 "참고자료 보여줘"
```

## 출력 포맷

### 초기화 성공
```
## ✅ 프로젝트 초기화 완료

### 프로젝트 정보
- **이름**: {name}
- **도메인**: {domain}
- **스택**: {techStack}

### 생성된 파일
{파일 목록}

### 다음 단계
{안내}
```

### 초기화 실패
```
## ❌ 초기화 실패

### 원인
{에러 내용}

### 해결 방법
{해결 방법}
```

## Layered Override 적용

초기화 시 설정 우선순위:

```
1. 사용자 입력 (최우선)
2. domains/{domain}/domain.json
3. domains/_base/ 기본값
4. 하드코딩 기본값 (최하위)
```

## 주의사항
- 기존 설정 덮어쓰기 전 확인 필수
- Git 저장소 없으면 생성 권유
- 도메인 변경은 `/skill-domain switch` 사용
