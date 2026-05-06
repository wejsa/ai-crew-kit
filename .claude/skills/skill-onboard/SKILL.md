---
name: skill-onboard
description: 기존 프로젝트 온보딩 - 코드베이스 스캔 + 자동 설정 생성. 사용자가 "프로젝트 온보딩" 또는 /skill-onboard를 요청할 때 사용합니다.
disable-model-invocation: false
allowed-tools: Bash(git:*), Bash(ls:*), Bash(cat:*), Bash(wc:*), Read, Write, Edit, Glob, Grep, AskUserQuestion
argument-hint: "[--scan-only]"
complexity-hint: medium
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
2. **ai-crew-kit clone 자동 정리** (표준 진입 플로우):
   - **추가 확인 질문 없이 즉시 실행** — 의도된 초기화이며 destructive 작업이 아님
   - **검출 기준** (둘 다 만족 시 실행):
     1. `git remote get-url origin`이 정규식 `[/:]ai-crew-kit(\.git)?$` 일치
     2. `git rev-list --max-parents=0 HEAD`가 `ab0269a1414f0d9eba8d130d865dfdd6baeed06c` (ai-crew-kit initial commit)와 일치
     - 둘 중 하나라도 불일치 → 자동 스킵 + Step 1 코드베이스 스캔으로 일반 진행
   - **자기 보호 가드** (3가지 모두 통과해야 정리 진행):
     1. **tracked dirty** 워킹 트리(`git status --porcelain | grep -v '^??'` 출력 있음) → SKIP
        - **untracked 파일은 통과**: 시나리오 B에서 사용자가 src/, app/, lib/ 등에 자기 코드를 *복사만* 한 상태(`git add` 미실행)는 untracked → 통과하여 정리 진행. 사용자 코드 보존 + kit 잡티 제거.
        - tracked 수정/추가/삭제만 차단(kit 개발자 미커밋 작업 보호).
     2. 미푸시 커밋(`git log @{u}..` 출력 있음) → SKIP
     3. main/master 브랜치만 진행. 비-main, detached HEAD(빈 문자열), 빈 값 모두 SKIP (kit dev 환경은 보통 develop/feature/* 또는 tag checkout)
     - 가드 미통과 시 보고 후 Step 1로 일반 진행 (정리 없이)
   - **실행 순서** (검출+가드 통과 시):
     1. `KIT_SOURCE_URL=$(git remote get-url origin)` 저장 (Step 5에서 `kitSource`로 기록)
     2. `rm -rf .git && git init -b main`
     3. kit 잔여 파일 자동 삭제 (한 줄):
        ```bash
        rm -rf CHANGELOG.md docs examples tests scripts .github memory LICENSE README.md CLAUDE.md VERSION .claude/temp .claude/hooks/tests .claude/state .claude/settings.local.json
        ```
        보존: `.claude/` (프레임워크 본체, 단 `hooks/tests/`/`state/`/`settings.local.json` 제외), `.gitignore`, `.gitattributes`, `.claude/SECURITY.md`. 삭제된 `CLAUDE.md`/`README.md`/`VERSION`은 Step 5에서 사용자 프로젝트용으로 새로 생성됨 (`README.md.bak` 백업 불필요 — kit clone 케이스이므로).
     4. 보고: `"✓ ai-crew-kit clone 감지 → 표준 초기화 + kit 잔여 N개 자동 정리"`
   - **시나리오 B 주의** (사용자 코드가 이미 함께 있는 경우): 사용자 코드가 보통 `src/`/`app/`/`lib/` 등 비충돌 경로면 안전. 단, 사용자가 자기 `docs/`/`tests/`/`scripts/`/`.github/workflows/`를 동일 경로에 미리 복사한 경우 함께 삭제됨. 의심 시 사용자에게 사전 백업(`tar czf .pre-onboard-backup-$(date +%s).tar.gz docs tests scripts .github`) 권장.
   - 검출 자동 스킵된 경우(시나리오 C): 기존 동작 유지, 영향 없음.
   - Claude는 "다른 경로가 필요한가요?" 같은 확인 질문을 하지 말 것
3. 기존 AI Crew Kit 설정 (project.json) → AskUserQuestion으로 덮어쓰기 확인

## 실행 플로우

### Step 1: 코드베이스 스캔

**백엔드**: build.gradle.kts → spring-boot-kotlin / build.gradle → spring-boot-java / pom.xml → spring-boot-java / go.mod → go / pyproject.toml/requirements.txt → python (FastAPI/Django 판별) / package.json + express/fastify/nestjs → nodejs-typescript

**Python FastAPI vs Django 자동 판별**:
- `manage.py` 존재 OR `django` in dependencies → `python-django`
- `fastapi` in dependencies OR `uvicorn` in dependencies → `python-fastapi`
- 둘 다 없으면 `app/main.py` 존재 → `python-fastapi` / `config/settings/` 존재 → `python-django`
- 판별 불가 → AskUserQuestion으로 직접 선택
**프론트엔드**: next.config.* → nextjs / vite.config.* + react → react-vite / nuxt.config.* → vue-nuxt / astro.config.* → astro / vue.config.*/vue 의존성 → vue
**패키지 매니저**: bun.lockb → bun / pnpm-lock.yaml → pnpm / yarn.lock → yarn / package-lock.json → npm (복수 시 bun>pnpm>yarn>npm)
**Python 패키지**: poetry.lock → poetry / Pipfile.lock → pipenv / requirements.txt → pip
**데이터베이스**: docker-compose + 의존성 (postgres/mysql/mongodb)
**캐시/메시지큐**: docker-compose + 의존성 (redis/rabbitmq/kafka)
**인프라**: docker-compose.yml → docker-compose / k8s/ → kubernetes / Dockerfile만 → docker-compose

**빌드 명령어 감지** (techStack 기반):
- spring/kotlin → ./gradlew build/test/ktlintCheck
- java → ./gradlew build/test/checkstyleMain (Maven: mvn package/test)
- node/typescript → npm run build/test/lint (package.json scripts 확인)
- go → go build/test + golangci-lint
- python-fastapi → pytest / ruff check .
- python-django → python manage.py check / pytest / ruff check .
- nextjs → next build / vitest 또는 jest / next lint
- react-vite → vite build / vitest / eslint .
- vue-nuxt → nuxt build / vitest / eslint .
- vue → vite build / vitest / eslint .
- astro → astro build / vitest / eslint .

**도메인 추천**: `_registry.json` keywords와 매칭 (디렉토리명 3점, 파일명 2점, README/설명 1점 → 최고점 추천, 동점이면 general)

**기존 구조 분석**: 소스 파일 수, 테스트 존재 여부, 기존 문서

### Step 2: 스캔 결과 출력 + 확인
감지된 기술 스택 (항목, 결과, 신뢰도), 빌드 명령어, 도메인 추천, 프로젝트 규모 출력
AskUserQuestion: "결과 정확" / "기술 스택 수정" / "도메인 변경"
`--scan-only` 모드: 여기서 종료

### Step 3: 추가 정보 수집
AskUserQuestion: 프로젝트 이름 (디렉토리명 기본값), 설명, 에이전트 구성 (skill-init Step 5 동일 — 스택 기반 필수 자동 결정 + 선택 추가), Task 접두사

### Step 4: 기존 파일 백업
README.md → README.md.bak / CLAUDE.md → CLAUDE.md.bak (존재 시)

> **kit clone 케이스 예외**: 사전 조건 2번에서 자동 정리로 README.md/CLAUDE.md/VERSION이 이미 삭제되었으므로 본 단계에서 백업 대상 없음. 자연스럽게 스킵됨.

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
