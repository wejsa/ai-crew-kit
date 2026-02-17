---
name: skill-upgrade
description: 프레임워크 업그레이드 - ai-crew-kit 최신 버전으로 프레임워크 파일 업데이트
disable-model-invocation: true
allowed-tools: Bash(git:*), Bash(cp:*), Bash(rm:*), Bash(tar:*), Bash(diff:*), Bash(mktemp:*), Bash(mkdir:*), Bash(cat:*), Bash(ls:*), Bash(date:*), Bash(wc:*), Bash(df:*), Bash(jq:*), Bash(echo:*), Read, Write, Edit, Glob, Grep, AskUserQuestion
argument-hint: "[--dry-run] [--source <git-url|local-path>] [--version <tag>] [--rollback <backup-path>]"
---

# skill-upgrade: 프레임워크 업그레이드

## 실행 조건
- 사용자가 `/skill-upgrade` 또는 "프레임워크 업그레이드해줘" 요청 시

## 옵션
```
/skill-upgrade                              # 최신 버전으로 업그레이드
/skill-upgrade --dry-run                    # 변경 사항 미리보기 (실제 변경 없음)
/skill-upgrade --source <git-url|local-path> # 소스 지정
/skill-upgrade --version <tag>               # 특정 버전으로 업그레이드
/skill-upgrade --rollback                    # 가장 최근 백업에서 롤백
/skill-upgrade --rollback <backup-path>      # 지정 백업에서 롤백
```

## 롤백 모드

`--rollback` 옵션 감지 시, 아래 플로우만 실행하고 종료:

1. 백업 경로 결정:
   - `--rollback <path>` → 해당 경로 사용
   - `--rollback` (경로 없음) → `.claude/temp/upgrade-backup-*/` 중 최신 디렉토리
2. 백업 디렉토리 존재 및 무결성 확인
3. 사용자 확인: "다음 백업에서 롤백합니다: {경로}. 진행하시겠습니까?"
4. 백업 내 `backup.tar.gz` 해제 → 프레임워크 파일 복원
5. `project.json`의 `kitVersion`을 백업 시점 값으로 되돌림
6. 롤백 완료 리포트 출력

## 실행 플로우

### Step 1: 환경 검증

```bash
# 필수 파일 확인
ls .claude/state/project.json

# Git clean 상태 확인
git status --porcelain

# 잠금 파일 확인
ls .claude/temp/.upgrade.lock

# 디스크 공간 확인
df -h .
```

**검증 항목:**
| 항목 | 조건 | 처리 |
|------|------|------|
| project.json | 없음 | "프로젝트가 초기화되지 않았습니다. `/skill-init`을 먼저 실행하세요." 안내 후 종료 |
| Git 상태 | uncommitted changes 있음 | "커밋되지 않은 변경사항이 있습니다. 커밋 후 다시 실행하세요." 경고 + 진행 여부 질문 |
| 잠금 파일 | `.upgrade.lock` 존재 | "이전 업그레이드가 중단된 것 같습니다." 경고 + 롤백 안내 + 진행 여부 질문 |
| 디스크 공간 | 부족 | 경고 후 종료 |

### Step 2: 소스 확보

**소스 결정 우선순위:**
1. `--source` 옵션으로 지정된 값
2. `project.json`의 `kitSource` 필드
3. 기본값: `https://github.com/wejsa/ai-crew-kit.git`

```bash
# project.json에서 kitSource 읽기
cat .claude/state/project.json | grep kitSource

# 소스가 로컬 경로인지 Git URL인지 판별
# Git URL인 경우:
UPGRADE_TMP=$(mktemp -d)
git clone --depth 1 [--branch <tag>] <source-url> "$UPGRADE_TMP"

# 로컬 경로인 경우:
UPGRADE_TMP=<local-path>
```

- `--version` 옵션이 있으면 `--branch <tag>`로 특정 버전 클론

### Step 3: 소스 구조 검증

새 소스에 필수 디렉토리/파일이 존재하는지 확인:

```bash
ls "$UPGRADE_TMP/.claude/skills/"
ls "$UPGRADE_TMP/.claude/domains/"
ls "$UPGRADE_TMP/.claude/templates/"
ls "$UPGRADE_TMP/.claude/schemas/"
ls "$UPGRADE_TMP/VERSION"
```

**하나라도 없으면:**
> "유효한 AI Crew Kit 소스가 아닙니다. 필수 디렉토리가 누락되었습니다: {목록}"
> 종료

### Step 4: 버전 비교

```bash
# 현재 버전
CURRENT_VERSION=$(cat .claude/state/project.json | jq -r '.kitVersion // "unknown"')

# 새 버전
NEW_VERSION=$(cat "$UPGRADE_TMP/VERSION")
```

| 비교 결과 | 동작 |
|-----------|------|
| 새 버전 > 현재 | 정상 진행 |
| 새 버전 = 현재 | "이미 최신 버전입니다 (v{version})." + 진행 여부 질문 |
| 새 버전 < 현재 | "다운그레이드입니다 (v{current} → v{new}). 계속하시겠습니까?" 경고 |
| 현재 = unknown | 최초 업그레이드 (부트스트랩 모드) — 정상 진행 |

### Step 5: 스키마 마이그레이션 체크

```bash
# 새 소스의 migrations.json 확인
cat "$UPGRADE_TMP/.claude/schemas/migrations.json"
```

- `migrations.json`이 있으면: 현재 kitVersion에 해당하는 마이그레이션 항목 확인
- 없으면: 스키마 diff로 폴백 (project.schema.json 비교)
- 마이그레이션 계획을 Step 7에서 미리보기에 포함

### Step 6: 커스터마이징 감지

**6-1. 도메인 커스텀 파일 감지**
```bash
# 현재 도메인 디렉토리의 파일 목록
find .claude/domains/ -type f | sort > /tmp/current_domain_files.txt

# 새 소스의 도메인 디렉토리 파일 목록
find "$UPGRADE_TMP/.claude/domains/" -type f | sort > /tmp/new_domain_files.txt

# 현재에만 존재하는 파일 = 사용자가 추가한 커스텀 파일
comm -23 /tmp/current_domain_files.txt /tmp/new_domain_files.txt > /tmp/custom_files.txt
```

**6-2. domain.json 커스텀 항목 감지**
- 각 도메인의 `domain.json`을 새 소스와 비교
- 사용자가 추가한 `keywords`, `checklists` 항목 추출

**6-3. settings.json 커스텀 권한 감지**
```bash
# 현재 settings.json의 permissions
cat .claude/settings.json | jq '.permissions'

# 새 소스의 settings.json permissions
cat "$UPGRADE_TMP/.claude/settings.json" | jq '.permissions'
```
- 현재에만 있는 `allow[]` 항목 = 커스텀 권한

### Step 7: 변경 미리보기 (diff)

프레임워크 디렉토리별 변경사항 표시:

```
## 업그레이드 미리보기: v{current} → v{new}

### 변경되는 프레임워크 디렉토리
| 디렉토리 | 추가 | 수정 | 삭제 |
|---------|------|------|------|
| .claude/agents/ | N | N | N |
| .claude/skills/ | N | N | N |
| .claude/domains/ | N | N | N |
| .claude/templates/ | N | N | N |
| .claude/schemas/ | N | N | N |
| .claude/workflows/ | N | N | N |
| .claude/docs/ | N | N | N |

### 보존되는 커스터마이징
- 도메인 커스텀 파일: {N}개
- domain.json 커스텀 항목: {N}개
- settings.json 커스텀 권한: {N}개
- CLAUDE.md 커스텀 섹션: {있음/없음}
- README.md 커스텀 섹션: {있음/없음}

### 스키마 마이그레이션
- {마이그레이션 항목 목록}
```

### Step 8: 사용자 확인

변경 사항 표시 후 진행 여부 질문.

- `--dry-run` 모드인 경우: 미리보기 결과만 출력하고 **여기서 종료**
- 일반 모드: AskUserQuestion으로 진행 여부 확인

```
업그레이드를 진행하시겠습니까?
- 예, 진행합니다
- 아니오, 취소합니다
```

### Step 9: 백업 생성

```bash
# 백업 디렉토리 생성
BACKUP_DIR=".claude/temp/upgrade-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 프레임워크 파일 + CLAUDE.md + README.md 백업
tar czf "$BACKUP_DIR/backup.tar.gz" \
  .claude/agents/ \
  .claude/skills/ \
  .claude/domains/ \
  .claude/templates/ \
  .claude/schemas/ \
  .claude/workflows/ \
  .claude/docs/ \
  .claude/settings.json \
  CLAUDE.md \
  README.md \
  2>/dev/null

# 백업 무결성 검증
tar tzf "$BACKUP_DIR/backup.tar.gz" > /dev/null

# 현재 kitVersion 기록 (롤백 시 참조)
echo "$CURRENT_VERSION" > "$BACKUP_DIR/kitVersion.txt"
```

### Step 10: 커스텀 콘텐츠 추출

**10-1. CLAUDE.md 커스텀 섹션 추출**
```bash
# CUSTOM_SECTION_START ~ CUSTOM_SECTION_END 사이 내용 추출
# 마커가 없으면 빈 문자열
```

**10-2. README.md 커스텀 섹션 추출**
```bash
# CUSTOM_SECTION_START ~ CUSTOM_SECTION_END 사이 내용 추출
# 마커가 없으면 (구버전) 빈 문자열 — 첫 업그레이드 시 마커 자동 추가
```

**10-3. 도메인 커스텀 파일 추출**
- Step 6에서 감지한 커스텀 파일 목록을 임시 디렉토리에 복사

**10-4. domain.json 커스텀 항목 추출**
- Step 6에서 감지한 커스텀 keywords, checklists 항목을 JSON으로 저장

**10-5. settings.json 커스텀 권한 추출**
- Step 6에서 감지한 커스텀 allow/deny 항목을 저장

### Step 11: 프레임워크 파일 교체

```bash
# 잠금 파일 생성
echo '{"startedAt":"'$(date -Iseconds)'","backupDir":"'$BACKUP_DIR'"}' > .claude/temp/.upgrade.lock

# 진행 상태 파일 생성
echo '{"step":11,"backupDir":"'$BACKUP_DIR'","timestamp":"'$(date -Iseconds)'"}' > .claude/temp/upgrade-state.json
```

**교체 대상 디렉토리:**
```bash
# 삭제 → 복사 (디렉토리 단위)
FRAMEWORK_DIRS=(".claude/agents" ".claude/skills" ".claude/domains" ".claude/templates" ".claude/schemas" ".claude/workflows" ".claude/docs")

for dir in "${FRAMEWORK_DIRS[@]}"; do
  # 새 소스에 해당 디렉토리가 있는 경우만
  if [ -d "$UPGRADE_TMP/$dir" ]; then
    rm -rf "$dir"
    cp -r "$UPGRADE_TMP/$dir" "$dir"
  fi
done
```

**실패 시 자동 롤백:**
- 위 작업 중 오류 발생 시 → 즉시 백업에서 복원
- `tar xzf "$BACKUP_DIR/backup.tar.gz"` 실행
- 잠금 파일 삭제

### Step 12: 커스터마이징 복원 + project.json 마이그레이션

**12-1. 도메인 커스텀 파일 복원**
```bash
# Step 10에서 추출한 커스텀 파일을 원래 위치에 복사
```

**12-2. domain.json 커스텀 항목 머지**
```bash
# 새 domain.json에 사용자 커스텀 keywords/checklists 항목 머지
# 중복 키는 사용자 값 우선
```

**12-3. settings.json 머지**
```bash
# 기존 커스텀 권한 추출
CURRENT_ALLOWS=$(jq '.permissions.allow // []' .claude/settings.json)
NEW_ALLOWS=$(jq '.permissions.allow // []' "$UPGRADE_TMP/.claude/settings.json")

# 합집합 (중복 제거)
MERGED_ALLOWS=$(jq -s '.[0] + .[1] | unique' <(echo "$CURRENT_ALLOWS") <(echo "$NEW_ALLOWS"))

# 기존 deny 보존
CURRENT_DENIES=$(jq '.permissions.deny // []' .claude/settings.json)

# 머지된 settings.json 생성
# 새 settings.json 기반 + merged allow + 기존 deny
```

**12-4. project.json 마이그레이션**
```bash
# kitVersion 업데이트
jq '.kitVersion = "'$NEW_VERSION'"' .claude/state/project.json > /tmp/project_tmp.json

# kitSource 설정 (없으면 추가)
jq '.kitSource = "'$KIT_SOURCE'"' /tmp/project_tmp.json > .claude/state/project.json

# migrations.json에 정의된 추가 마이그레이션 적용
```

### Step 13: CLAUDE.md/README.md 재생성

**13-1. CLAUDE.md 재생성**
```bash
# 새 CLAUDE.md.tmpl 로드
cat .claude/templates/CLAUDE.md.tmpl

# project.json 기반 마커 치환 (skill-init Step 6과 동일 로직)
# {{PROJECT_NAME}}, {{DOMAIN_SECTION}} 등

# CUSTOM_SECTION 마커 내에 Step 10에서 추출한 커스텀 내용 삽입
```

**13-2. README.md 재생성**
```bash
# 새 README.md.tmpl 로드
cat .claude/templates/README.md.tmpl

# project.json 기반 마커 치환
# {{PROJECT_NAME}}, {{PROJECT_DESCRIPTION}} 등

# CUSTOM_SECTION 마커 내에 Step 10에서 추출한 커스텀 내용 삽입
```

### Step 14: 완료 리포트

```bash
# 잠금 파일 삭제
rm -f .claude/temp/.upgrade.lock
rm -f .claude/temp/upgrade-state.json

# Git clone 임시 디렉토리 정리 (로컬 소스가 아닌 경우)
rm -rf "$UPGRADE_TMP"
```

### Step 15: 프레임워크 검증 (skill-validate 자동 호출)

업그레이드 완료 후 구조 무결성 자동 검증:

```
Skill tool 사용: skill="skill-validate"
```

- 검증 통과 시: 완료 리포트에 "✅ 검증 통과" 포함
- 검증 실패 시: 경고 표시 + `--fix` 옵션 안내
- 검증 실패가 업그레이드를 롤백하지는 않음

**출력:**
```
## 업그레이드 완료: v{old} → v{new}

### 변경 요약
- 업데이트된 디렉토리: {목록}
- 추가된 파일: {N}개
- 수정된 파일: {N}개
- 삭제된 파일: {N}개

### 복원된 커스터마이징
- 도메인 커스텀 파일: {목록}
- domain.json 커스텀 항목: {목록}
- settings.json 커스텀 권한: {목록}
- CLAUDE.md 커스텀 섹션: 복원됨
- README.md 커스텀 섹션: 복원됨

### 스키마 마이그레이션
- {적용된 마이그레이션 목록}

### 백업 위치
`{BACKUP_DIR}/`

### 롤백 방법
문제 발생 시:
\`\`\`bash
/skill-upgrade --rollback {BACKUP_DIR}
\`\`\`

### CHANGELOG 발췌 (v{old} → v{new})
{새 소스의 CHANGELOG.md에서 관련 버전 항목 발췌}
```

---

## 업데이트 대상 (프레임워크 파일)

| 디렉토리 | 설명 |
|---------|------|
| `.claude/agents/` | 에이전트 정의 |
| `.claude/skills/` | 스킬 구현 |
| `.claude/domains/` | 도메인 설정 (커스텀 파일/항목은 감지→복원) |
| `.claude/templates/` | CLAUDE.md.tmpl, README.md.tmpl 등 |
| `.claude/schemas/` | project.schema.json, migrations.json |
| `.claude/workflows/` | 워크플로우 YAML |
| `.claude/docs/` | 프레임워크 문서 |

**머지 방식으로 처리:**
| 파일 | 머지 전략 |
|------|----------|
| `.claude/settings.json` | 새 권한만 추가 머지 (기존 커스텀 권한 보존) |

## 보존 대상 (프로젝트 파일)

| 경로 | 설명 |
|------|------|
| `.claude/state/*` | project.json, backlog.json, completed.json |
| `.claude/settings.local.json` | 로컬 설정 |
| `.claude/temp/` | 임시 파일 |
| `.claude/plans/` | 계획 파일 |
| `CLAUDE.md` | 재생성 (커스텀 섹션 보존) |
| `README.md` | 재생성 (커스텀 섹션 보존) |
| `VERSION` | 프로젝트 버전 (변경 안 함) |
| `CHANGELOG.md` | 프로젝트 변경이력 |
| `docs/` | 프로젝트 문서 |
| `src/` 등 | 소스 코드 |

## 안전장치

### 잠금 파일
- **경로:** `.claude/temp/.upgrade.lock`
- Step 1에서 존재 확인 → 있으면 "이전 업그레이드가 중단됨" 경고 + 롤백 안내
- Step 11 시작 시 생성, Step 14 완료 시 삭제

### 진행 상태 파일
- **경로:** `.claude/temp/upgrade-state.json`
- 현재 단계, 백업 경로, 타임스탬프 기록
- 중단 시 복구 참조용

### 디스크 공간 검증
- Step 1에서 `df -h` 확인

### 백업 무결성
- Step 9에서 `tar tzf`로 아카이브 검증

### 자동 롤백
- Step 11 파일 교체 중 오류 발생 시 → 즉시 백업에서 복원

## 주의사항
- Git 상태가 clean한 상태에서 실행 권장
- 업그레이드 후 `git diff`로 변경사항 확인 권장
- 문제 발생 시 `--rollback`으로 즉시 복원 가능
