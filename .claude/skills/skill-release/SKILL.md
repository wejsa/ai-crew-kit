---
name: skill-release
description: 릴리스 - 버전 범프 + CHANGELOG 업데이트 + main 머지 + 태그 생성
disable-model-invocation: true
allowed-tools: Bash(git:*), Bash(gh:*), Bash(cat:*), Read, Write, Edit, AskUserQuestion
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

### 3. 변경사항 입력 받기
AskUserQuestion 도구를 사용하여 변경사항 카테고리별로 입력 받기:

**입력 항목**:
- **Added**: 새로운 기능
- **Changed**: 기존 기능 변경
- **Fixed**: 버그 수정
- **Removed**: 제거된 기능 (선택)
- **Deprecated**: 곧 제거될 기능 (선택)
- **Security**: 보안 관련 (선택)

### 4. VERSION 파일 업데이트
```bash
echo "$NEW_VERSION" > VERSION
```

### 5. CHANGELOG.md 업데이트
새 버전 섹션을 CHANGELOG.md 상단에 추가 (## [Unreleased] 다음 위치)

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- {사용자 입력}

### Changed
- {사용자 입력}

### Fixed
- {사용자 입력}
```

### 6. README.md 버전 업데이트
```bash
# project.json에서 프로젝트명 읽기
PROJECT_NAME=$(grep '"name"' .claude/state/project.json | sed 's/.*: *"\(.*\)".*/\1/')

# 제목의 버전 업데이트 (프로젝트명 기반 동적 패턴)
sed -i "s/# $PROJECT_NAME v[0-9]*\.[0-9]*\.[0-9]*/# $PROJECT_NAME v$NEW_VERSION/" README.md
```
- `project.json`의 `name` 필드를 사용하여 동적으로 패턴 매칭
- ai-crew-kit 자체뿐 아니라 초기화된 모든 프로젝트에서 동작

### 7. develop에 커밋
```bash
git add VERSION CHANGELOG.md README.md
git commit -m "chore: release v$NEW_VERSION

- VERSION: $CURRENT_VERSION → $NEW_VERSION
- CHANGELOG.md 업데이트
- README.md 버전 업데이트

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

### 8. develop → main 머지
```bash
git checkout main
git pull origin main
git merge develop -m "Merge branch 'develop' for release v$NEW_VERSION"
```

### 9. 태그 생성
```bash
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"
```

### 10. 원격 푸시
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
