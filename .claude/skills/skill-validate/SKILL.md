---
name: skill-validate
description: 프레임워크 검증 - 업그레이드 후 구조 무결성 자체 검증
disable-model-invocation: true
allowed-tools: Bash(cat:*), Bash(ls:*), Bash(python3:*), Read, Glob, Grep
argument-hint: "[--fix]"
---

# skill-validate: 프레임워크 검증

## 실행 조건
- `skill-upgrade` Step 14 완료 후 자동 호출
- 또는 사용자가 `/skill-validate` 직접 호출

## 옵션
```
/skill-validate          # 검증만 수행 (읽기 전용)
/skill-validate --fix    # 자동 수정 가능한 항목 수정
```

## 검증 항목

### 1. [REQUIRED] SKILL.md YAML 프론트매터 파싱 검증

모든 `.claude/skills/*/SKILL.md` 파일의 YAML 프론트매터 유효성 확인:

```bash
# 모든 SKILL.md 파일 순회
for skill_file in .claude/skills/*/SKILL.md; do
  # YAML 프론트매터 추출 (--- ~ --- 사이)
  # 필수 필드 확인: name, description
  # allowed-tools 형식 검증
done
```

**검증 항목:**
- `---` 시작/종료 마커 존재
- `name` 필드 존재 + 비어있지 않음
- `description` 필드 존재 + 비어있지 않음
- YAML 파싱 가능 (문법 오류 없음)

### 2. [REQUIRED] 모든 JSON 파일 유효성 검증

`.claude/` 하위 모든 `.json` 파일 파싱 검증:

```bash
for json_file in $(find .claude/ -name "*.json" -type f); do
  python3 -c "import sys,json; json.load(open('$json_file'))" 2>/dev/null || {
    echo "❌ 유효하지 않은 JSON: $json_file"
  }
done
```

**대상 파일:**
- `.claude/schemas/*.json`
- `.claude/domains/**/domain.json`
- `.claude/domains/_registry.json`
- `.claude/schemas/migrations.json`
- `.claude/state/*.json` (존재 시)

### 3. [REQUIRED] 도메인 레지스트리 정합성

`.claude/domains/_registry.json`과 실제 디렉토리 일치 확인:

```bash
# 레지스트리에 등록된 도메인 ID 목록
REGISTERED=$(cat .claude/domains/_registry.json | python3 -c "
import sys,json
data = json.load(sys.stdin)
for d in data['domains']:
    print(d['id'])
")

# 실제 도메인 디렉토리 목록 (_base 제외)
ACTUAL=$(ls -d .claude/domains/*/ | grep -v _base | xargs -I{} basename {})
```

**검증 항목:**
- 레지스트리에 있으나 디렉토리 없음 → ERROR
- 디렉토리 있으나 레지스트리에 없음 → WARNING
- 각 도메인 디렉토리에 `domain.json` 존재 확인

### 4. [REQUIRED] 템플릿 마커 완결성 검사

`.claude/templates/*.tmpl` 파일의 마커가 TEMPLATE-ENGINE.md에 정의되어 있는지 확인:

```bash
# 템플릿에서 사용된 마커 추출
grep -oP '\{\{[A-Z_]+\}\}' .claude/templates/*.tmpl | sort -u

# TEMPLATE-ENGINE.md에 정의된 마커 추출
grep -oP '\{\{[A-Z_]+\}\}' .claude/templates/TEMPLATE-ENGINE.md | sort -u
```

**검증 항목:**
- 템플릿에 사용됐으나 정의되지 않은 마커 → WARNING
- 정의됐으나 사용되지 않는 마커 → INFO

### 5. [IMPORTANT] 스킬 간 교차 참조 정합성

스킬에서 참조하는 다른 스킬/에이전트 파일이 존재하는지 확인:

```bash
# SKILL.md에서 참조하는 스킬명 추출
grep -oP 'skill="skill-[a-z-]+"' .claude/skills/*/SKILL.md

# 참조된 스킬의 SKILL.md 존재 확인
# 참조된 에이전트의 .md 파일 존재 확인
```

### 6. [IMPORTANT] 스키마 파일 검증

`.claude/schemas/` 디렉토리의 스키마 파일 검증:

- `project.schema.json`: JSON Schema Draft-07 호환 확인
- `backlog.schema.json`: JSON Schema Draft-07 호환 확인
- `migrations.json`: 유효 JSON + 필수 구조 확인

### 7. [OPTIONAL] 워크플로우 YAML 검증

`.claude/workflows/*.yaml` 파일 구조 검증:

- 필수 필드: `name`, `steps`
- 각 step에 `name`, `skill` 필드 존재
- 참조된 스킬 존재 확인

## 출력 포맷

```
## 🔍 프레임워크 검증 결과

### 요약
| 카테고리 | PASS | WARN | FAIL |
|---------|------|------|------|
| SKILL.md 프론트매터 | 15 | 0 | 0 |
| JSON 유효성 | 8 | 0 | 0 |
| 도메인 레지스트리 | 3 | 0 | 0 |
| 템플릿 마커 | 12 | 1 | 0 |
| 교차 참조 | 20 | 0 | 0 |
| 스키마 | 3 | 0 | 0 |
| 워크플로우 | 6 | 0 | 0 |

### 전체 결과: ✅ PASS (67 통과, 1 경고, 0 실패)

### 경고 상세
- ⚠️ [템플릿] 미사용 마커: {{CUSTOM_MARKER}} (TEMPLATE-ENGINE.md에 정의됨)

### 실패 상세
(없음)
```

### 실패 시 출력
```
### 전체 결과: ❌ FAIL (65 통과, 1 경고, 2 실패)

### 실패 상세
1. ❌ [JSON] .claude/domains/fintech/domain.json — 파싱 실패 (line 15: trailing comma)
2. ❌ [레지스트리] healthcare 도메인 등록됨 — 디렉토리 없음

### 수정 방법
1. `domain.json` 수동 수정 필요
2. `/skill-validate --fix` 실행 시 자동 수정 가능 항목 처리
```

## --fix 모드

자동 수정 가능 항목:
- 레지스트리에 있으나 디렉토리 없는 도메인 → 레지스트리에서 제거
- `metadata.version` 필드 누락 → 기본값 1 추가

자동 수정 불가 항목 (수동 필요):
- JSON 문법 오류
- YAML 프론트매터 오류
- 누락된 스킬/에이전트 파일

## 주의사항
- 기본 모드는 읽기 전용 (파일 수정 없음)
- `--fix`는 안전한 항목만 수정
- 검증 실패가 프레임워크 동작을 차단하지는 않음 (경고 성격)
