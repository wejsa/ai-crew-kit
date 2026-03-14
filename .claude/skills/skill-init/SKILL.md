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
| Step 3: 도메인 선택 | AskUserQuestion 1회 | 자동 감지 → fallback: general |
| Step 4: 기술 스택 | AskUserQuestion 5+회 | `_registry.json`의 domain.defaultStack |
| Step 5: 에이전트 팀 | AskUserQuestion multi-select | 기본 3개: pm, backend, code-reviewer |
| Step 5.5: 워크플로우 프로필 | AskUserQuestion 1회 | standard 기본값 |
| Step 6-7 | 그대로 | + "설정 변경: /skill-init --reset" 안내 |

### --quick 자동 감지
- package.json → nodejs-typescript
- build.gradle.kts → spring-boot-kotlin / build.gradle → spring-boot-java
- go.mod → go
- 감지 실패 → general 도메인 + defaultStack

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

### Step 3: 도메인 선택
`domains/_registry.json` 로드 → AskUserQuestion으로 도메인 선택

### Step 4: 기술 스택 선택
도메인별 defaultStack 기본값 제안 → AskUserQuestion: 백엔드, 프론트엔드, DB, 캐시, 인프라

### Step 5: 에이전트 팀 구성
AskUserQuestion multi-select:
- 필수: pm, backend, code-reviewer
- 선택: planner, db-designer, frontend (프론트엔드 스택 선택 시 자동), qa, docs

### Step 5.5: 워크플로우 프로필 선택
AskUserQuestion: Standard (권장, 전체 체이닝) / Fast (리뷰 생략, 프로토타입용)

### Step 6: 파일 생성

1. **project.json**: name, description, domain, techStack, agents, conventions (taskPrefix, branchStrategy:git-flow, commitFormat:conventional, prLineLimit:500, testCoverage:80, workflowProfile), createdAt, kitVersion (VERSION 값), kitSource (KIT_SOURCE_URL 또는 기본 repo URL)
2. **backlog.json**: metadata (lastTaskNumber:0, version:1), summary (전체 0), phases:{}, tasks:{}
3. **CLAUDE.md**: `.claude/templates/CLAUDE.md.tmpl` 마커 치환
4. **VERSION**: `echo "0.1.0" > VERSION`
5. **README.md**: `.claude/templates/README.md.tmpl` 마커 치환 (기존 README 교체)
6. **docs/api-specs/**: `mkdir -p`
7. **.gitignore** 업데이트 (필요 시)
8. **Git 초기 커밋** (선택): `git add` → `git commit` → `git checkout -b develop`

### Step 7: 완료 안내
필수 포함: 생성된 파일 목록, 프로젝트 정보 (이름, 도메인, 기술 스택), 활성 에이전트, Git 원격 저장소 설정 안내, 다음 단계 (/skill-feature, /skill-backlog, /skill-docs)

## Layered Override 적용
설정 우선순위: 사용자 입력 > domains/{domain}/domain.json > domains/_base/ > 하드코딩 기본값

## 주의사항
- 기존 설정 덮어쓰기 전 확인 필수
- Git 저장소 없으면 생성 권유
- 도메인 변경은 `/skill-domain switch` 사용
