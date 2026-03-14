---
name: skill-onboard
description: 기존 프로젝트 온보딩 - 코드베이스 스캔 + 자동 설정 생성. 사용자가 "프로젝트 온보딩" 또는 /skill-onboard를 요청할 때 사용합니다.
disable-model-invocation: false
allowed-tools: Bash(git:*), Bash(ls:*), Bash(cat:*), Bash(wc:*), Read, Write, Edit, Glob, Grep, AskUserQuestion
argument-hint: "[--scan-only]"
---

# skill-onboard: 기존 프로젝트 온보딩

## 실행 조건
- 사용자가 `/skill-onboard` 또는 "이 프로젝트에 적용해줘" 요청 시
- **기존 코드베이스** 대상 (새 프로젝트는 `/skill-init`)

## 옵션
```
/skill-onboard              # 전체 온보딩 (스캔 + 설정 생성)
/skill-onboard --scan-only  # 스캔만 (분석 결과 출력 후 종료)
```

## skill-init과의 차이

| 항목 | skill-init | skill-onboard |
|------|-----------|---------------|
| 대상 | 새 프로젝트 | 기존 코드베이스 |
| 정보 수집 | 대화형 질문 | 코드베이스 자동 스캔 |
| 기존 파일 | 없음 | 백업 후 생성 |

## 사전 조건 (MUST-EXECUTE-FIRST — 하나라도 실패 시 STOP)
1. Git 저장소 확인 → 없으면 "git init 먼저 실행" 안내
2. 기존 AI Crew Kit 설정 (project.json) → AskUserQuestion으로 덮어쓰기 확인

## 실행 플로우

### Step 1: 코드베이스 스캔

**백엔드**: package.json → nodejs-typescript / build.gradle.kts → spring-boot-kotlin / build.gradle → spring-boot-java / pom.xml → spring-boot-java / go.mod → go
**프론트엔드**: package.json 의존성 (next/react/vue/nuxt) + next.config.*/vue.config.* 감지
**데이터베이스**: docker-compose + 의존성 (postgres/mysql/mongodb)
**캐시/메시지큐**: docker-compose + 의존성 (redis/rabbitmq/kafka)
**인프라**: docker-compose.yml → docker-compose / k8s/ → kubernetes / Dockerfile만 → docker-compose

**빌드 명령어 감지** (techStack 기반):
- spring/kotlin → ./gradlew build/test/ktlintCheck
- java → ./gradlew build/test/checkstyleMain
- node/typescript → npm run build/test/lint (package.json scripts 확인)
- go → go build/test + golangci-lint
- Maven → mvn package/test

**도메인 추천**: `_registry.json` keywords와 매칭 (디렉토리명 3점, 파일명 2점, README/설명 1점 → 최고점 추천, 동점이면 general)

**기존 구조 분석**: 소스 파일 수, 테스트 존재 여부, 기존 문서

### Step 2: 스캔 결과 출력 + 확인
감지된 기술 스택 (항목, 결과, 신뢰도), 빌드 명령어, 도메인 추천, 프로젝트 규모 출력
AskUserQuestion: "결과 정확" / "기술 스택 수정" / "도메인 변경"
`--scan-only` 모드: 여기서 종료

### Step 3: 추가 정보 수집
AskUserQuestion: 프로젝트 이름 (디렉토리명 기본값), 설명, 에이전트 구성 (skill-init Step 5 동일), Task 접두사

### Step 4: 기존 파일 백업
README.md → README.md.bak / CLAUDE.md → CLAUDE.md.bak (존재 시)

### Step 5: 설정 파일 생성
skill-init Step 6 동일: project.json (buildCommands 포함), backlog.json, CLAUDE.md, README.md, VERSION (기존 있으면 유지)
커스텀 스킬: `.claude/skills/custom/` 존재 시 스캔 → CLAUDE.md CUSTOM_SECTION에 삽입

### Step 6: Git 설정
- develop 브랜치 생성 (없는 경우)
- .gitignore에 `.claude/temp/` 추가 (없는 경우)

### Step 7: 완료 리포트
필수 포함: 프로젝트 정보, 생성된 파일, 백업된 파일, 다음 단계 (/skill-feature, /skill-backlog, /skill-plan)

## 주의사항
- 기존 코드/파일은 절대 수정하지 않음 (AI Crew Kit 설정만 추가)
- README.md.bak 백업은 온보딩 시에만 생성
- 스캔 결과 100% 정확하지 않을 수 있으므로 사용자 확인 필수
- 감지 실패 시 사용자에게 직접 입력 요청
- ports는 docker-compose 포트 매핑 있으면 포함, 없으면 생략
