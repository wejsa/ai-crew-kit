---
name: aick-release
description: 릴리스 - 빌드 검증 + API spec 스냅샷 + 버전 범프 + CHANGELOG + main 머지 + 태그 생성. /aick-release로 호출합니다.
disable-model-invocation: true
allowed-tools: Bash(git:*), Bash(gh:*), Bash(cat:*), Bash(./gradlew:*), Bash(npm:*), Bash(yarn:*), Bash(go:*), Bash(swag:*), Read, Write, Edit, Glob, AskUserQuestion, Skill
argument-hint: "{버전타입: patch|minor|major}"
complexity-hint: light
---

# aick-release: 릴리스 자동화

## 실행 조건
- 사용자가 `/aick-release {버전타입}` 요청 시 (develop 브랜치에서만)

## 버전 타입
| 타입 | 설명 | 예시 |
|------|------|------|
| patch | 버그 수정 | 1.1.0 → 1.1.1 |
| minor | 기능 추가 | 1.1.0 → 1.2.0 |
| major | Breaking 변경 | 1.1.0 → 2.0.0 |

## 사전 조건 (MUST-EXECUTE-FIRST — 하나라도 실패 시 STOP)
1. project.json 존재
2. backlog.json 존재 + 유효 JSON
3. Worktree 환경 차단 (`git-dir != git-common-dir` → STOP, 메인 레포에서 실행 안내)
4. develop 브랜치 확인
5. Clean 상태 (uncommitted changes 없음)
6. `git fetch origin`
7. Health Gate (선택): project.json에 healthCheck 설정이 있으면
   /aick-health-check --quick 실행. CRITICAL 0건이어야 진행.
   healthCheck 설정이 없거나 실패 시에도 AskUserQuestion으로 계속 여부 확인.
   (릴리스를 차단하지 않음 — 사용자 판단에 맡김)

## 실행 플로우

### 1. 현재 버전 읽기
`cat VERSION`

### 2. 새 버전 계산
MAJOR.MINOR.PATCH 파싱 → 타입에 따라 범프

### 2.5 멱등 검사 (중간 실패 재개·스테일 중복 — v4.8.0)
**태그 존재 = 릴리스 완료 판정의 SSOT.** ⚠️ 재개 감지는 반드시 **범프 전 `CURRENT_VERSION` 기준** — Step 9 커밋 이후 실패하면 VERSION이 이미 전진해 있어 NEW 기준 검사는 영구 불발(자체 리뷰 finding G1: 데드 브랜치)이다.

1. `git fetch --tags origin` (사전 조건 6의 fetch에 태그 보강)
2. **미완 릴리스 재개 감지 (CURRENT + 원격 태그 기준)**: **원격 태그 부재**(`git ls-remote --tags origin "v$CURRENT_VERSION"` 출력 비어 있음 — ⚠️ 로컬 태그 기준 금지: Step 11이 로컬 태그를 만든 뒤 Step 12 push가 실패하면 로컬 기준 검사는 불발) **+** CHANGELOG에 `## [$CURRENT_VERSION]` 섹션 **존재** → 직전 릴리스가 파일 업데이트 후 중단된 상태. `ls-remote` 자체가 실패(네트워크 불가)하면 **STOP**: "릴리스는 push까지가 완료 — 네트워크 복구 후 재실행하세요." AskUserQuestion 1회: "직전 릴리스 v$CURRENT_VERSION이 미완(원격 태그 없음)입니다. 완성을 재개할까요? [재개 / 새 버전 진행]"
   - **재개** → `NEW_VERSION = $CURRENT_VERSION`으로 재설정(Step 2 범프 결과 폐기), Step 3(빌드) 통과 후 Step 4~8 스킵. 재개 지점은 결정적으로:
     - 로컬 태그 `v$CURRENT_VERSION` 존재(rev-parse 성공) → **Step 12(push)부터** (커밋·태그 완료, push만 실패한 상태)
     - 로컬 태그 부재 + develop 최신 커밋 제목 == `chore: release v$CURRENT_VERSION` → **Step 10(main 머지)부터**
     - 둘 다 아님 → **Step 9(develop 커밋)부터**
     - 출력에 명시: "⟳ v$CURRENT_VERSION 재개 — Step {N}부터"
   - **새 버전 진행** → 케이스 3으로
3. **스테일 중복 감지 (NEW 기준)**: 태그 `v$NEW_VERSION` 이미 존재 → **STOP**: "v$NEW_VERSION은 이미 릴리스됨 — 로컬 checkout이 stale합니다. `git pull` 후 재실행하세요."
4. 둘 다 아님 → 정상 진행 (Step 3으로).

### 3. 빌드 & 테스트 검증
빌드 명령어: `buildCommands` 우선 → `techStack` 폴백.
스택별 명령 표 SSOT: `${CLAUDE_PLUGIN_ROOT}/.claude/templates/protocols/build-commands.md` (clone/seed면 `.claude/templates/protocols/build-commands.md`)를 Read 후 적용 — 본 스킬에 표 복제 금지.

project.json 미존재 시 스킵. 실패 시 즉시 중단 (파일 변경 전이므로 롤백 불필요).

### 4. 변경사항 수집
- 마지막 태그 이후 커밋 자동 수집 (태그 없으면 최근 50개)
- conventional commit prefix 분류: feat→Added, fix→Fixed, refactor/perf→Changed, docs/chore/test→제외
- AskUserQuestion으로 초안 확인 ("그대로 사용" 또는 수정)

### 5-7. 파일 업데이트
- VERSION 파일: `echo "$NEW_VERSION" > VERSION`
- CHANGELOG.md: `## [X.Y.Z] - YYYY-MM-DD` 섹션 삽입 ([Unreleased] 아래)
- README.md: project.json name 기반 동적 패턴으로 제목 버전 교체

### 8. API spec 스냅샷

| 스택 | 감지 방법 | 생성 명령 |
|------|----------|----------|
| spring-boot | build.gradle에 openapi-gradle-plugin | `./gradlew generateOpenApiDocs` |
| nodejs | package.json에 generate:api-docs | `npm run generate:api-docs` |
| go | swag 명령 존재 | `swag init -o docs/api-specs` |

**플러그인 미감지 시 자동 설치**:
- Spring Boot: springdoc-openapi 플러그인 + 의존성 + openApi 설정 블록 추가
- Node.js: swagger-jsdoc 패키지 설치 + scripts 추가 + generate 스크립트 생성
- Go: `go install github.com/swaggo/swag/cmd/swag@latest`

생성 성공: info.version을 NEW_VERSION으로 업데이트
실패: AskUserQuestion "계속 진행?" (릴리스 차단 아님)

### 9. develop 커밋
```bash
git add VERSION CHANGELOG.md README.md
# API spec + 빌드 파일 변경 포함
git commit -m "chore: release v$NEW_VERSION

- VERSION: $CURRENT_VERSION → $NEW_VERSION
- CHANGELOG.md 업데이트
- README.md 버전 업데이트

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### 10. develop → main 머지
```bash
git checkout main && git pull origin main
git merge develop -m "Merge branch 'develop' for release v$NEW_VERSION"
```

### 11. 태그 생성
`git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"`

### 12. 원격 푸시
`git push origin develop && git push origin main && git push origin "v$NEW_VERSION"` → `git checkout develop`

## 출력 포맷
필수 포함: 이전/새 버전, 태그, 브랜치 머지 상태, 빌드/테스트 결과, API spec 결과, 변경사항 요약 (Added/Changed/Fixed), GitHub 확인 링크

## 롤백

| 실패 지점 | 롤백 |
|----------|------|
| Step 3 빌드/테스트 | 불필요 (파일 변경 전) |
| Step 8 API spec | 사용자 확인 후 스킵 가능 |
| Step 9 커밋 | `git reset --hard HEAD~1` |
| Step 10+ | 태그 삭제 + main/develop reset + force push |

## 주의사항
- develop 브랜치에서만 실행, main 직접 실행 금지
- Clean 상태 필수, 충돌 발생 시 수동 해결 후 재시도
- **재실행은 안전(멱등)** — Step 2.5가 **CURRENT 기준** 태그(완료 SSOT)·CHANGELOG로 미완 릴리스를 감지해 재개/정상을 결정적으로 분기(범프 후 NEW 기준 검사는 데드 브랜치 — 금지). 롤백 표의 Step 10+ 롤백 후 재실행도 동일 분기가 재개 처리. 완주 후 재실행은 정상적으로 다음 버전을 진행한다
