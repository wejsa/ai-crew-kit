---
name: skill-onboard
description: 기존 프로젝트 온보딩 - 코드베이스 스캔 + 자동 설정 생성
disable-model-invocation: false
allowed-tools: Bash(git:*), Bash(ls:*), Bash(cat:*), Bash(wc:*), Read, Write, Edit, Glob, Grep, AskUserQuestion
argument-hint: "[--scan-only]"
---

# skill-onboard: 기존 프로젝트 온보딩

## 실행 조건
- 사용자가 `/skill-onboard` 또는 "이 프로젝트에 적용해줘" 요청 시
- **기존 코드베이스가 이미 있는 프로젝트**에 AI Crew Kit을 적용할 때 사용
- `/skill-init`은 새 프로젝트, `/skill-onboard`는 기존 프로젝트

## 옵션
```
/skill-onboard              # 전체 온보딩 (스캔 + 설정 생성)
/skill-onboard --scan-only  # 스캔만 수행 (설정 생성 없음, 분석 결과만 출력)
```

## `/skill-init`과의 차이

| 항목 | skill-init | skill-onboard |
|------|-----------|---------------|
| 대상 | 새 프로젝트 | 기존 코드베이스 |
| 정보 수집 | 대화형 질문 | 코드베이스 자동 스캔 |
| techStack | 사용자 선택 | 자동 감지 (사용자 확인) |
| 도메인 | 사용자 선택 | 키워드 기반 추천 (사용자 확인) |
| 기존 파일 | 없음 | 백업 후 생성 |

## 사전 조건 검증 (MUST-EXECUTE-FIRST)

```bash
# [REQUIRED] 1. Git 저장소 확인
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Git 저장소가 아닙니다. git init을 먼저 실행하세요."
  exit 1
fi

# [WARNING] 2. 기존 AI Crew Kit 설정 확인
if [ -f ".claude/state/project.json" ]; then
  echo "이미 AI Crew Kit이 설정되어 있습니다."
  echo "기존 설정을 덮어쓰시겠습니까?"
  # AskUserQuestion으로 확인
fi
```

## 실행 플로우

### Step 1: 코드베이스 스캔

프로젝트 루트에서 아래 항목을 자동 감지:

#### 1.1 패키지 매니저 / 빌드 시스템 감지

```bash
# Node.js
if [ -f "package.json" ]; then
  DETECTED_BACKEND="nodejs-typescript"
  # package.json 분석으로 상세 감지
fi

# Gradle (Kotlin/Java)
if [ -f "build.gradle.kts" ]; then
  DETECTED_BACKEND="spring-boot-kotlin"
elif [ -f "build.gradle" ]; then
  DETECTED_BACKEND="spring-boot-java"
fi

# Maven
if [ -f "pom.xml" ]; then
  DETECTED_BACKEND="spring-boot-java"
fi

# Go
if [ -f "go.mod" ]; then
  DETECTED_BACKEND="go"
fi
```

#### 1.2 프론트엔드 감지

```bash
# package.json에서 프레임워크 감지
if [ -f "package.json" ]; then
  # next → nextjs
  # react → react
  # vue → vue
  # nuxt → vue
fi

# next.config.* 존재 → nextjs
# vue.config.* 존재 → vue
```

#### 1.3 데이터베이스 감지

```bash
# docker-compose.yml에서 DB 서비스 감지
if [ -f "docker-compose.yml" ] || [ -f "docker-compose.yaml" ]; then
  # postgres/postgresql → postgresql
  # mysql/mariadb → mysql
  # mongo/mongodb → mongodb
fi

# 의존성에서 감지
# pg, @prisma/client + postgresql → postgresql
# mysql2, sequelize + mysql → mysql
# mongoose, mongodb → mongodb
```

#### 1.4 캐시/메시지큐 감지

```bash
# docker-compose에서 감지
# redis → redis
# rabbitmq → rabbitmq
# kafka → kafka

# 의존성에서 감지
# ioredis, redis → redis
# amqplib → rabbitmq
```

#### 1.5 인프라 감지

```bash
# docker-compose.yml 존재 → docker-compose
# k8s/, kubernetes/ 디렉토리 존재 → kubernetes
# Dockerfile만 존재 → docker-compose (기본)
```

#### 1.6 빌드 명령어 감지

감지된 빌드 시스템을 기반으로 `buildCommands`를 자동 설정:

```bash
# 감지된 백엔드 스택 기반 빌드 명령어 결정
case "$DETECTED_BACKEND" in
  *spring*|*kotlin*)
    DETECTED_BUILD="./gradlew build"
    DETECTED_TEST="./gradlew test"
    DETECTED_LINT="./gradlew ktlintCheck"
    ;;
  *java*)
    DETECTED_BUILD="./gradlew build"
    DETECTED_TEST="./gradlew test"
    DETECTED_LINT="./gradlew checkstyleMain"
    ;;
  *node*|*typescript*)
    DETECTED_BUILD="npm run build"
    DETECTED_TEST="npm test"
    DETECTED_LINT="npm run lint"
    # package.json scripts에서 실제 명령어 확인
    if [ -f "package.json" ]; then
      # build 스크립트가 없으면 빈 값
      HAS_BUILD=$(python3 -c "import json; s=json.load(open('package.json')).get('scripts',{}); print(s.get('build',''))")
      [ -z "$HAS_BUILD" ] && DETECTED_BUILD=""
    fi
    ;;
  *go*)
    DETECTED_BUILD="go build ./..."
    DETECTED_TEST="go test ./..."
    DETECTED_LINT="golangci-lint run"
    ;;
esac
```

**Maven 프로젝트 추가 감지:**
```bash
if [ -f "pom.xml" ]; then
  DETECTED_BUILD="mvn package"
  DETECTED_TEST="mvn test"
  DETECTED_LINT=""
fi
```

#### 1.7 도메인 추천

도메인 레지스트리의 `keywords`와 프로젝트 파일명/디렉토리명/README 내용을 매칭:

```bash
# .claude/domains/_registry.json 읽기
# 각 도메인의 keywords와 프로젝트 파일 매칭

# 매칭 소스:
# 1. 디렉토리명 (src/payment/ → fintech)
# 2. 파일명 (order.ts → ecommerce)
# 3. README.md 내용 (결제, 상품 등)
# 4. package.json name/description
```

**매칭 점수:**
- 디렉토리명 매칭: 3점
- 파일명 매칭: 2점
- README/설명 매칭: 1점
- 최고 점수 도메인을 추천, 동점이면 general

#### 1.8 기존 구조 분석

```bash
# 소스 코드 규모
find src/ -type f | wc -l 2>/dev/null

# 테스트 존재 여부
ls -d test/ tests/ __tests__/ spec/ 2>/dev/null

# 기존 문서
ls docs/ 2>/dev/null
ls README.md 2>/dev/null
```

### Step 2: 스캔 결과 출력 + 사용자 확인

```
## 코드베이스 스캔 결과

### 감지된 기술 스택
| 항목 | 감지 결과 | 신뢰도 |
|------|----------|--------|
| 백엔드 | nodejs-typescript | HIGH (package.json) |
| 프론트엔드 | nextjs | HIGH (next.config.js) |
| 데이터베이스 | postgresql | MEDIUM (docker-compose) |
| 캐시 | redis | MEDIUM (docker-compose) |
| 인프라 | docker-compose | HIGH (docker-compose.yml) |

### 감지된 빌드 명령어
| 항목 | 명령어 | 감지 근거 |
|------|--------|----------|
| 빌드 | {DETECTED_BUILD} | {감지 근거} |
| 테스트 | {DETECTED_TEST} | {감지 근거} |
| 린트 | {DETECTED_LINT} | {감지 근거} |

### 도메인 추천
| 도메인 | 매칭 점수 | 매칭 키워드 |
|--------|----------|------------|
| ecommerce | 8점 | 주문, 상품, 장바구니 |
| fintech | 2점 | 결제 |
| general | 0점 | - |

→ 추천: ecommerce (이커머스)

### 프로젝트 규모
- 소스 파일: {N}개
- 테스트: {있음/없음}
- 기존 문서: {있음/없음}
```

AskUserQuestion으로 확인:

```
위 스캔 결과를 검토해주세요. 수정이 필요한 항목이 있나요?

- 결과가 정확합니다, 진행해주세요
- 기술 스택 수정이 필요합니다
- 도메인 선택을 변경하고 싶습니다
```

**`--scan-only` 모드인 경우:** 스캔 결과 출력 후 여기서 종료.

### Step 3: 추가 정보 수집

스캔으로 자동 감지할 수 없는 항목을 AskUserQuestion으로 수집:

```
### 프로젝트 정보
- 프로젝트 이름: {디렉토리명 기본값}
- 프로젝트 설명: (입력 필요)

### 에이전트 구성
(skill-init Step 5와 동일한 에이전트 선택)

### Task 접두사
예: SHOP, API, APP (기본값: 도메인별 기본값)
```

### Step 4: 기존 파일 백업

```bash
# 기존 README.md 백업
if [ -f "README.md" ]; then
  cp README.md README.md.bak
fi

# 기존 CLAUDE.md 백업 (있는 경우)
if [ -f "CLAUDE.md" ]; then
  cp CLAUDE.md CLAUDE.md.bak
fi
```

### Step 5: 설정 파일 생성

skill-init Step 6과 동일한 파일 생성:

1. **project.json** — 스캔 결과 + 사용자 확인 기반 (감지된 `buildCommands` 포함)
2. **backlog.json** — 빈 상태로 초기화
3. **CLAUDE.md** — 템플릿 기반 생성
4. **README.md** — 템플릿 기반 생성
5. **VERSION** — `0.1.0` (기존 VERSION이 있으면 유지)

**커스텀 스킬 반영:**
```bash
# .claude/skills/custom/ 디렉토리가 있으면 스캔
if [ -d ".claude/skills/custom" ]; then
  # custom/skill-*/SKILL.md에서 name, description 추출
  # CLAUDE.md CUSTOM_SECTION에 커스텀 스킬 테이블 삽입
fi
```

### Step 6: Git 설정

```bash
# develop 브랜치 생성 (없는 경우)
if ! git rev-parse --verify develop > /dev/null 2>&1; then
  git checkout -b develop
fi

# .gitignore에 .claude/temp/ 추가 (없는 경우)
if ! grep -q ".claude/temp/" .gitignore 2>/dev/null; then
  echo ".claude/temp/" >> .gitignore
fi
```

### Step 7: 완료 리포트

```
## 온보딩 완료

### 프로젝트 정보
- **이름**: {name}
- **도메인**: {domain}
- **기술 스택**: {감지된 스택 요약}

### 생성된 파일
- `.claude/state/project.json`
- `.claude/state/backlog.json`
- `CLAUDE.md`
- `README.md`

### 백업된 파일
- `README.md` → `README.md.bak`

### 다음 단계
1. 기존 기능을 Task로 등록: `/skill-feature "기능명"`
2. 백로그 확인: `/skill-backlog`
3. 작업 시작: `/skill-plan`
```

### 실패
```
## ❌ 온보딩 실패

### 단계
{실패한 단계}

### 에러
{에러 메시지}

### 복구 방법
{복구 절차}
```

## 자동 체이닝
- 없음 (독립 실행)

## 주의사항
- 기존 코드/파일은 절대 수정하지 않음 (AI Crew Kit 설정만 추가)
- README.md.bak 백업은 온보딩 시에만 생성
- 스캔 결과는 100% 정확하지 않을 수 있으므로 사용자 확인 필수
- 감지 실패 시 (알 수 없는 스택 등) 사용자에게 직접 입력 요청
- ports 필드는 docker-compose에서 감지된 포트 매핑이 있으면 포함, 없으면 생략
