# 도메인 확장 및 커스터마이징

> [← README로 돌아가기](../README.md)

## 참고자료 추가

```bash
# 로컬 파일 추가
/skill-domain add-doc docs/my-guide.md

# URL에서 추가
/skill-domain add-doc "https://example.com/api-guide.md"
```

## 체크리스트 추가

```bash
/skill-domain add-checklist docs/my-checklist.md
```

**체크리스트 형식:**
```markdown
| 항목 | 설명 | 심각도 |
|------|------|--------|
| 항목1 | 설명1 | CRITICAL |
| 항목2 | 설명2 | MAJOR |
```

## 새 도메인 생성

**방법 1: 기존 도메인 복제 (권장)**
```bash
/skill-domain export my-custom-domain
```

**방법 2: 수동 생성**
```bash
# 1. 디렉토리 생성
mkdir -p .claude/domains/my-domain/{docs,checklists,templates}

# 2. domain.json 작성
# 3. _registry.json에 등록
```

## 도메인 전환

```bash
# 현재 도메인 확인
/skill-domain

# 도메인 목록 조회
/skill-domain list

# 도메인 전환
/skill-domain switch ecommerce
```

## 커스텀 스킬 생성

```bash
# 스킬 스캐폴딩 생성
/skill-create

# .claude/skills/custom/ 디렉토리에 생성됨
# CLAUDE.md CUSTOM_SECTION에 자동 등록
```

## Layered Override

설정은 다음 순서로 오버라이드됩니다:

```
1. project.json (사용자 설정)      ← 최우선
2. domains/{domain}/domain.json   ← 도메인 설정
3. domains/_base/                 ← 공통 기본값
4. 하드코딩 기본값                  ← 최하위
```

예: `project.json`에 `testCoverage: 90`을 설정하면 도메인 기본값(80)을 오버라이드합니다.
