# Git 워크플로우 컨벤션

모든 프로젝트에 적용되는 기본 Git 워크플로우 규칙입니다.

## 브랜치 전략

### 기본 브랜치

| 브랜치 | 용도 | 보호 |
|--------|------|------|
| `main` | 운영 배포 버전 | Protected |
| `develop` | 개발 통합 브랜치 | Protected |

### 작업 브랜치

| 유형 | 패턴 | 예시 |
|------|------|------|
| 기능 개발 | `feature/{taskId}-{설명}` | `feature/TASK-001-user-auth` |
| 버그 수정 | `bugfix/{taskId}-{설명}` | `bugfix/TASK-002-login-error` |
| 긴급 수정 | `hotfix/HOT-{NNN}-{설명}` | `hotfix/HOT-001-security-patch` |
| 롤백 | `revert/{대상}` | `revert/v1.2.3`, `revert/-123` |
| 스텝 개발 | `feature/{taskId}-step{N}` | `feature/TASK-001-step1` |

### 브랜치 생성 규칙

```bash
# develop에서 분기 (일반 개발)
git checkout develop
git pull origin develop
git checkout -b feature/{taskId}-step{N}
```

### 긴급 수정 (Hotfix) 플로우

**hotfix는 main에서 직접 분기하는 유일한 예외 케이스:**

```bash
# 1. main에서 분기
git checkout main
git pull origin main
git checkout -b hotfix/HOT-{NNN}-{설명}

# 2. 수정 + 테스트
# 3. PR 생성 (--base main)
gh pr create --base main --title "hotfix: HOT-{NNN} - {설명}"

# 4. 보안 리뷰 → 머지 → 패치 버전 범프 → 태그
# 5. develop 백머지
git checkout develop && git merge main
```

### 롤백 (Revert) 플로우

```bash
# 1. main에서 분기
git checkout main
git pull origin main
git checkout -b revert/{대상}

# 2. git revert (히스토리 보존)
git revert {SHA} --mainline 1 --no-edit  # merge commit인 경우

# 3. PR 생성 (--base main)
gh pr create --base main --title "revert: {대상} 롤백"

# 4. 머지 → 패치 버전 범프 → 태그
# 5. develop 백머지
git checkout develop && git merge main
```

### Worktree 모드 (Claude Squad 등)

git worktree 환경에서는 develop checkout이 불가하므로, 현재 브랜치(CS 브랜치)를 feature 브랜치로 직접 사용한다.

| 일반 모드 | Worktree 모드 |
|----------|--------------|
| `git checkout develop && git pull` | `git fetch origin develop && git merge origin/develop` |
| `git checkout -b feature/X` | 브랜치 생성 없음 (현재 브랜치 사용) |
| `gh pr merge --squash --delete-branch` | `gh pr merge --squash` (브랜치 유지) |
| 머지 후 `git checkout develop` | 머지 후 `git merge origin/develop` |
| `git push origin develop` (상태) | `git push origin HEAD` |

감지: `git rev-parse --git-dir` ≠ `--git-common-dir` → worktree

### 브랜치 병합

- PR은 항상 `develop` 브랜치로 생성
- Squash 머지 사용 (커밋 히스토리 정리)
- 머지 후 작업 브랜치 삭제

## 커밋 메시지

### 형식

```
<type>: <description>

[optional body]

[optional footer]
```

### 타입

| Type | 설명 | 예시 |
|------|------|------|
| `feat` | 새 기능 | `feat: 사용자 로그인 API 추가` |
| `fix` | 버그 수정 | `fix: 토큰 만료 오류 수정` |
| `refactor` | 리팩토링 | `refactor: 인증 서비스 구조 개선` |
| `docs` | 문서 | `docs: API 문서 업데이트` |
| `test` | 테스트 | `test: 로그인 단위 테스트 추가` |
| `chore` | 빌드/설정 | `chore: 의존성 버전 업데이트` |
| `style` | 포맷팅 | `style: 코드 포맷 적용` |
| `perf` | 성능 | `perf: 쿼리 최적화` |

### 규칙

1. **제목**
   - 50자 이내
   - 마침표 없음
   - 명령형 사용 ("추가", "수정", "개선")

2. **본문** (선택)
   - 72자 줄바꿈
   - "무엇을", "왜" 설명

3. **Task ID 포함**
   ```
   feat: TASK-001 Step 1 - JWT 서비스 구현
   ```

### 예시

```
feat: TASK-001 Step 1 - JWT 토큰 서비스 구현

- JWT 토큰 발급/검증 서비스 추가
- Access Token / Refresh Token 분리
- Token Rotation 로직 구현

Co-Authored-By: Claude <noreply@anthropic.com>
```

## PR (Pull Request) 규칙

### PR 제목

```
feat: {Task ID} Step {N} - {스텝 제목}
```

### PR 본문

```markdown
## Summary
- 변경 사항 요약 (1-3 bullet points)

## Test plan
- [ ] 단위 테스트 통과
- [ ] 통합 테스트 통과
- [ ] 수동 테스트 완료

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### PR 규칙

| 항목 | 규칙 |
|------|------|
| 라인 수 | 500라인 미만 권장 |
| 리뷰어 | 최소 1명 승인 필요 |
| CI | 빌드/테스트 통과 필수 |
| 충돌 | 충돌 해결 후 머지 |

## 태그 규칙

### 버전 태그

```
v{major}.{minor}.{patch}
```

| 유형 | 변경 시점 | 예시 |
|------|----------|------|
| major | 호환성 깨지는 변경 | v2.0.0 |
| minor | 기능 추가 | v1.1.0 |
| patch | 버그 수정 | v1.0.1 |

### 릴리스 태그 생성

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## .gitignore 필수 항목

```gitignore
# IDE
.idea/
.vscode/
*.iml

# Build
build/
target/
dist/
node_modules/

# Logs
*.log
logs/

# Environment
.env
.env.local

# OS
.DS_Store
Thumbs.db

# Temp
.claude/temp/
```

## 충돌 해결

### 해결 순서

1. 최신 develop 가져오기
   ```bash
   git fetch origin develop
   ```

2. rebase 또는 merge
   ```bash
   git rebase origin/develop
   # 또는
   git merge origin/develop
   ```

3. 충돌 해결 후 계속
   ```bash
   git add .
   git rebase --continue
   ```

4. 강제 푸시 (rebase 시)
   ```bash
   git push --force-with-lease
   ```

## 금지 사항

| 금지 항목 | 이유 |
|----------|------|
| `main` 직접 푸시 | 코드 리뷰 우회 (hotfix/rollback PR은 `--base main` 예외) |
| `--force` 푸시 (공유 브랜치) | 다른 작업 손실 |
| 큰 바이너리 파일 커밋 | 저장소 크기 증가 |
| 민감정보 커밋 | 보안 위험 |
