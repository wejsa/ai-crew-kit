---
name: skill-release
description: 릴리스 - 빌드 검증 + API spec 스냅샷 + 버전 범프 + CHANGELOG + main 머지 + 태그 생성
disable-model-invocation: true
allowed-tools: Bash(git:*), Bash(gh:*), Bash(cat:*), Bash(./gradlew:*), Bash(npm:*), Bash(yarn:*), Bash(go:*), Bash(swag:*), Read, Write, Edit, Glob, AskUserQuestion
argument-hint: "{버전타입: patch|minor|major}"
---

# skill-release: 릴리스 자동화

## 실행 조건
- 사용자가 `/skill-release {버전타입}` 요청 시
- develop 브랜치에서만 실행 가능

## 버전 타입
| 타입 | 설명 | 예시 |
|------|------|------|
| `patch` | 버그 수정 | 1.1.0 → 1.1.1 |
| `minor` | 기능 추가 | 1.1.0 → 1.2.0 |
| `major` | Breaking 변경 | 1.1.0 → 2.0.0 |

## 사전 조건 검증

### 필수 조건
1. **develop 브랜치**: 현재 브랜치가 develop
2. **Clean 상태**: 커밋되지 않은 변경사항 없음
3. **원격 동기화**: origin/develop과 동기화됨

```bash
# 브랜치 확인
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "develop" ]; then
  echo "Error: develop 브랜치에서만 실행 가능합니다."
  exit 1
fi

# Clean 상태 확인
if [ -n "$(git status --porcelain)" ]; then
  echo "Error: 커밋되지 않은 변경사항이 있습니다."
  exit 1
fi

# 원격 동기화
git fetch origin
```

## 실행 플로우

### 1. 현재 버전 읽기
```bash
CURRENT_VERSION=$(cat VERSION)
echo "현재 버전: $CURRENT_VERSION"
```

### 2. 새 버전 계산
```bash
# 버전 파싱 (MAJOR.MINOR.PATCH)
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

case "$VERSION_TYPE" in
  major)
    NEW_VERSION="$((MAJOR + 1)).0.0"
    ;;
  minor)
    NEW_VERSION="$MAJOR.$((MINOR + 1)).0"
    ;;
  patch)
    NEW_VERSION="$MAJOR.$MINOR.$((PATCH + 1))"
    ;;
esac

echo "새 버전: $NEW_VERSION"
```

### 3. 빌드 & 테스트 검증

`.claude/state/project.json`의 `techStack.backend` 참조 (skill-impl 패턴 재사용).

| 스택 | 빌드 | 테스트 |
|------|------|--------|
| spring-boot-kotlin | `./gradlew build` | `./gradlew test` |
| spring-boot-java | `./gradlew build` | `./gradlew test` |
| nodejs-typescript | `npm run build` | `npm test` |
| go | `go build ./...` | `go test ./...` |

**project.json 미존재 시**: 스킵 + `"ℹ️ project.json 없음 — 빌드/테스트 스킵"`
**실패 시**: 즉시 중단 (파일 변경 전이므로 롤백 불필요)

### 4. 변경사항 수집

#### 4.1 마지막 태그 이후 커밋 자동 수집
```bash
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LAST_TAG" ]; then
  GIT_LOG=$(git log ${LAST_TAG}..HEAD --oneline --no-merges)
else
  GIT_LOG=$(git log --oneline --no-merges -50)
fi
```

#### 4.2 conventional commit prefix 기반 분류
- `feat:` → Added
- `fix:` → Fixed
- `refactor:`, `perf:` → Changed
- `docs:`, `chore:`, `test:` → 제외

#### 4.3 사용자 확인
AskUserQuestion으로 초안 제시 → "그대로 사용" 또는 직접 수정

### 5. VERSION 파일 업데이트
```bash
echo "$NEW_VERSION" > VERSION
```

### 6. CHANGELOG.md 업데이트
새 버전 섹션을 CHANGELOG.md 상단에 추가 (## [Unreleased] 다음 위치)

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- {수집된 변경사항}

### Changed
- {수집된 변경사항}

### Fixed
- {수집된 변경사항}
```

### 7. README.md 버전 업데이트
```bash
# project.json에서 프로젝트명 읽기
PROJECT_NAME=$(grep '"name"' .claude/state/project.json | sed 's/.*: *"\(.*\)".*/\1/')

# 제목의 버전 업데이트 (프로젝트명 기반 동적 패턴)
sed -i "s/# $PROJECT_NAME v[0-9]*\.[0-9]*\.[0-9]*/# $PROJECT_NAME v$NEW_VERSION/" README.md
```
- `project.json`의 `name` 필드를 사용하여 동적으로 패턴 매칭
- ai-crew-kit 자체뿐 아니라 초기화된 모든 프로젝트에서 동작

### 8. API spec 스냅샷

버전 파일 업데이트 후, 커밋 전에 실행.

#### 스택별 생성

| 스택 | 감지 방법 | 생성 명령 | 출력 |
|------|----------|----------|------|
| spring-boot | build.gradle(.kts)에 `openapi-gradle-plugin` | `./gradlew generateOpenApiDocs` | docs/api-specs/openapi.json |
| nodejs | package.json에 `generate:api-docs` 스크립트 | `npm run generate:api-docs` | docs/api-specs/ |
| go | `swag` 명령 존재 | `swag init -o docs/api-specs` | docs/api-specs/ |

#### 플러그인/도구 미감지 시 — 자동 설치

`project.json`의 `techStack.backend` 기반으로 API 문서 도구를 자동 설치한다.

**Spring Boot (Kotlin/Java)** — build.gradle(.kts)에 springdoc-openapi 추가:

1. `build.gradle.kts` (또는 `build.gradle`) 파일을 Read로 읽기
2. plugins 블록에 아래 추가 (없는 경우):
   ```
   id("org.springdoc.openapi-gradle-plugin") version "1.9.0"
   ```
3. dependencies 블록에 아래 추가 (없는 경우):
   ```
   implementation("org.springdoc:springdoc-openapi-starter-webmvc-ui:2.8.6")
   ```
4. 파일 끝에 openApi 설정 블록 추가 (없는 경우):
   ```kotlin
   openApi {
       outputDir.set(file("docs/api-specs"))
       outputFileName.set("openapi.json")
   }
   ```
5. `./gradlew generateOpenApiDocs` 실행

**Node.js (TypeScript)** — swagger-jsdoc 패키지 설치:

1. 패키지 설치:
   ```bash
   npm install swagger-jsdoc swagger-ui-express
   npm install -D @types/swagger-jsdoc @types/swagger-ui-express
   ```
2. package.json의 scripts에 아래 추가 (없는 경우):
   ```json
   "generate:api-docs": "node scripts/generate-openapi.js"
   ```
3. `scripts/generate-openapi.js` 파일 생성 (없는 경우):
   - swagger-jsdoc로 프로젝트의 JSDoc 주석을 파싱하여 docs/api-specs/openapi.json 출력
4. `npm run generate:api-docs` 실행

**Go** — swag 설치:

1. swag CLI 설치:
   ```bash
   go install github.com/swaggo/swag/cmd/swag@latest
   ```
2. `swag init -o docs/api-specs` 실행

**자동 설치 후**:
- 설치에 사용된 변경사항을 릴리스 커밋에 포함 (Step 9의 git add에 빌드 파일 추가)
- `"✅ API 문서 도구 자동 설치 완료 — API spec 생성 성공"` 메시지 출력

**자동 설치 실패 시**:
- 기존 동작과 동일: AskUserQuestion으로 "API spec 생성 실패. 릴리스를 계속 진행할까요?" 확인
- 릴리스 차단 요소 아님

#### 생성 성공 시
- API spec의 `info.version`을 NEW_VERSION으로 업데이트 (Edit 도구)

#### 실패 시
- AskUserQuestion: "API spec 생성 실패. 릴리스를 계속 진행할까요?"
- 릴리스 차단 요소 아님

### 9. develop에 커밋
```bash
git add VERSION CHANGELOG.md README.md
# API spec 변경사항 포함
if [ -d "docs/api-specs" ] && [ -n "$(git status --porcelain docs/api-specs/)" ]; then
  git add docs/api-specs/
fi
# API 문서 도구 자동 설치에 의한 빌드 파일 변경 포함
git add -u build.gradle.kts build.gradle package.json package-lock.json 2>/dev/null || true

git commit -m "chore: release v$NEW_VERSION

- VERSION: $CURRENT_VERSION → $NEW_VERSION
- CHANGELOG.md 업데이트
- README.md 버전 업데이트
- API spec 업데이트 (해당 시)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### 10. develop → main 머지
```bash
git checkout main
git pull origin main
git merge develop -m "Merge branch 'develop' for release v$NEW_VERSION"
```

### 11. 태그 생성
```bash
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"
```

### 12. 원격 푸시
```bash
git push origin develop
git push origin main
git push origin "v$NEW_VERSION"
git checkout develop
```

## 출력 형식

```
## 릴리스 완료

- **이전 버전**: 1.1.0
- **새 버전**: 1.2.0
- **태그**: v1.2.0
- **브랜치**: develop → main 머지 완료
- **빌드/테스트**: 통과 (또는 스킵)
- **API spec**: 생성 완료 (또는 스킵)

### 변경사항 요약
- Added: {요약}
- Changed: {요약}
- Fixed: {요약}

### 확인
- [ ] GitHub에서 태그 확인: https://github.com/{owner}/{repo}/releases/tag/v1.2.0
- [ ] main 브랜치 확인
```

## 주의사항

### CRITICAL
- **develop 브랜치에서만 실행**: main에서 직접 실행 금지
- **Clean 상태 필수**: 커밋되지 않은 변경사항 있으면 중단
- **충돌 발생 시**: 수동 해결 후 재시도

### 롤백 방법

#### 부분 실패 대응

| 실패 지점 | 롤백 |
|----------|------|
| Step 3 빌드/테스트 | 불필요 (파일 변경 전) |
| Step 8 API spec | 사용자 확인 후 스킵 가능 |
| Step 9 커밋 | `git reset --hard HEAD~1` |
| Step 10~ | 기존 롤백 절차 동일 |

#### 전체 롤백
릴리스 실패 시:
```bash
# 태그 삭제
git tag -d v$NEW_VERSION
git push origin :refs/tags/v$NEW_VERSION

# main 브랜치 롤백
git checkout main
git reset --hard HEAD~1
git push origin main --force

# develop 브랜치 롤백
git checkout develop
git reset --hard HEAD~1
git push origin develop --force
```

## Edge Case

| 시나리오 | 처리 |
|---------|------|
| project.json 없음 | 빌드/테스트 + API spec 스킵 |
| 빌드 도구 미설치 | 즉시 중단 |
| API 문서 도구 미설정 | 자동 설치 후 재시도 (실패 시 스킵) |
| 첫 릴리스 (태그 없음) | 최근 50개 커밋에서 CHANGELOG 초안 |
