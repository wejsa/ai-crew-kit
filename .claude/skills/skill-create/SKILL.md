---
name: skill-create
description: 커스텀 스킬 생성 - SKILL.md 스캐폴딩 + CLAUDE.md 자동 등록
disable-model-invocation: false
allowed-tools: Bash(mkdir:*), Bash(ls:*), Read, Write, Edit, Glob, Grep, AskUserQuestion
argument-hint: "<name> [description]"
---

# skill-create: 커스텀 스킬 생성

## 실행 조건
- 사용자가 `/skill-create {name} "{description}"` 또는 "커스텀 스킬 만들어줘: {name}" 요청 시

## 사전 조건 검증 (MUST-EXECUTE-FIRST)

실패 시 즉시 중단 + 사용자 보고.

```bash
# [REQUIRED] 1. project.json 존재
if [ ! -f ".claude/state/project.json" ]; then
  echo "project.json이 없습니다. /skill-init을 먼저 실행하세요."
  exit 1
fi

# [REQUIRED] 2. CLAUDE.md 존재
if [ ! -f "CLAUDE.md" ]; then
  echo "CLAUDE.md가 없습니다. /skill-init을 먼저 실행하세요."
  exit 1
fi

# [REQUIRED] 3. 스킬명 인수 존재
if [ -z "$1" ]; then
  echo "스킬명을 지정해주세요. 예: /skill-create my-lint \"프로젝트 전용 린트\""
  exit 1
fi
```

## 인수 파싱

```
/skill-create <name> [description]

- name: 스킬 이름 (영문 소문자 + 하이픈, skill- 접두사 자동 추가)
- description: 스킬 설명 (따옴표로 감싸기, 생략 시 대화형으로 수집)
```

**이름 정규화:**
- 입력이 `skill-`로 시작하면 그대로 사용
- 아니면 `skill-` 접두사 자동 추가
- 예: `my-lint` → `skill-my-lint`
- 유효한 문자: `[a-z0-9-]`

## 실행 플로우

### Step 1: 중복 검사

```bash
# 동일 이름 스킬 존재 여부 확인
SKILL_DIR=".claude/skills/custom/skill-{name}"
if [ -d "$SKILL_DIR" ]; then
  echo "이미 존재하는 커스텀 스킬입니다: $SKILL_DIR"
  # 사용자에게 덮어쓰기 여부 확인
fi

# 빌트인 스킬과 이름 충돌 확인
BUILTIN_DIR=".claude/skills/skill-{name}"
if [ -d "$BUILTIN_DIR" ]; then
  echo "빌트인 스킬과 이름이 충돌합니다: skill-{name}"
  echo "다른 이름을 사용해주세요."
  exit 1
fi
```

### Step 2: 스킬 정보 수집

description이 인수로 제공되지 않은 경우 AskUserQuestion으로 수집:

```
커스텀 스킬 정보를 입력해주세요.

### 스킬 설명
이 스킬이 하는 일을 한 줄로 설명해주세요.
예: "프로젝트 전용 린트 규칙 실행"
```

추가 수집 항목 (AskUserQuestion):

```
### 도구 접근 권한
이 스킬에 필요한 도구를 선택해주세요.

- 읽기 전용 (Read, Glob, Grep)
- 읽기 + 쓰기 (Read, Write, Edit, Glob, Grep)
- 읽기 + 쓰기 + Bash (Read, Write, Edit, Glob, Grep, Bash)
- 전체 (Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion)
```

### Step 3: SKILL.md 생성

```bash
mkdir -p ".claude/skills/custom/skill-{name}"
```

`.claude/skills/custom/skill-{name}/SKILL.md` 파일 생성:

```markdown
---
name: skill-{name}
description: {description}
disable-model-invocation: false
allowed-tools: {선택된 도구 목록}
argument-hint: ""
---

# skill-{name}: {description}

## 실행 조건
- 사용자가 `/skill-{name}` 요청 시

## 실행 플로우

### Step 1: TODO
(여기에 스킬 로직을 구현하세요)

## 출력 포맷

```
## skill-{name} 실행 결과
{결과 내용}
```

## 자동 체이닝
- 없음 (독립 실행)

## 주의사항
- (필요한 주의사항을 추가하세요)
```

### Step 4: CLAUDE.md CUSTOM_SECTION에 스킬 등록

```bash
# 1. CLAUDE.md 읽기
# 2. <!-- CUSTOM_SECTION_START --> ~ <!-- CUSTOM_SECTION_END --> 블록 찾기
# 3. 블록 내에 커스텀 스킬 테이블 존재 여부 확인
```

**테이블이 없는 경우 (첫 커스텀 스킬):**

`<!-- CUSTOM_SECTION_START -->` 바로 다음에 삽입:

```markdown
### 커스텀 스킬

| 명령어 | 설명 |
|--------|------|
| `/skill-{name}` | {description} |
```

**테이블이 이미 있는 경우:**

테이블 마지막 행 다음에 새 행 추가:

```markdown
| `/skill-{name}` | {description} |
```

**구현 로직:**

```
1. CLAUDE.md 전체 읽기
2. CUSTOM_SECTION_START 마커 위치 찾기
3. CUSTOM_SECTION_END 마커 위치 찾기
4. 블록 내에 "### 커스텀 스킬" 헤더 존재 확인
5-A. 헤더 없음 → 헤더 + 테이블 헤더 + 행 삽입
5-B. 헤더 있음 → 테이블 마지막 행 뒤에 새 행 추가
6. Edit 도구로 CLAUDE.md 수정
```

### Step 5: 완료 리포트

```
## 커스텀 스킬 생성 완료

### 생성된 파일
- `.claude/skills/custom/skill-{name}/SKILL.md`

### CLAUDE.md 등록
- 커스텀 스킬 섹션에 `/skill-{name}` 등록됨

### 다음 단계
1. SKILL.md를 편집하여 스킬 로직을 구현하세요:
   `.claude/skills/custom/skill-{name}/SKILL.md`
2. 완성 후 `/skill-{name}`으로 실행하세요
3. `/skill-validate`로 스킬 구조를 검증할 수 있습니다
```

## 자동 체이닝
- 없음 (독립 실행)

## 주의사항
- 빌트인 스킬과 이름 충돌 방지 (빌트인 목록은 `.claude/skills/` 하위 디렉토리 기준)
- CLAUDE.md CUSTOM_SECTION 마커가 없으면 에러 메시지 출력 후 종료
- 기존 커스텀 스킬 덮어쓰기 시 사용자 확인 필수
- SKILL.md 프론트매터의 `allowed-tools`는 사용자 선택에 따라 설정
