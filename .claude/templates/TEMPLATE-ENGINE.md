# CLAUDE.md 템플릿 엔진 설계

## 개요

AI Crew Kit의 CLAUDE.md 자동 생성 엔진입니다.
프로젝트 설정(project.json)과 도메인 설정(domain.json)을 기반으로 CLAUDE.md를 동적 생성합니다.

## 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                      Input Sources                          │
├─────────────────┬─────────────────┬─────────────────────────┤
│ project.json    │ domain.json     │ _base/conventions       │
│ (사용자 설정)    │ (도메인 기본값)  │ (공통 규약)             │
└────────┬────────┴────────┬────────┴────────────┬────────────┘
         │                 │                     │
         ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Layered Override Resolver                      │
│   우선순위: project.json > domain.json > _base              │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Template Processor                        │
│   CLAUDE.md.tmpl + Resolved Values → CLAUDE.md              │
└─────────────────────────────────────────────────────────────┘
```

## 마커 정의

### 단순 치환 마커

단일 값으로 치환되는 마커입니다.

| 마커 | 출처 | 기본값 | 설명 |
|------|------|--------|------|
| `{{PROJECT_NAME}}` | project.json → name | "My Project" | 프로젝트명 |
| `{{PROJECT_DESCRIPTION}}` | project.json → description | "" | 프로젝트 설명 |
| `{{DOMAIN_ID}}` | project.json → domain | "general" | 도메인 ID |
| `{{DOMAIN_NAME}}` | domain.json → name | "범용" | 도메인 표시명 |
| `{{DOMAIN_ICON}}` | domain.json → icon | "🔧" | 도메인 아이콘 |
| `{{TASK_PREFIX}}` | project.json → conventions.taskPrefix | domain.defaultTaskPrefix | Task ID 접두사 |
| `{{PR_LINE_LIMIT}}` | project.json → conventions.prLineLimit | 500 | PR 라인 제한 |
| `{{TEST_COVERAGE}}` | project.json → conventions.testCoverage | 80 | 테스트 커버리지 목표 |

### 블록 마커

조건부 또는 반복 처리되는 마커입니다.

| 마커 | 생성 로직 | 설명 |
|------|----------|------|
| `{{TECH_STACK_SECTION}}` | techStack 기반 | 기술 스택 목록 |
| `{{AGENTS_SECTION}}` | agents.enabled 기반 | 활성화된 에이전트 목록 |
| `{{CONVENTIONS_SECTION}}` | conventions + domain 기반 | 코딩 컨벤션 |
| `{{DOMAIN_DOCS_MAPPING}}` | domain.keywordMapping 기반 | skill-docs 키워드 매핑 |
| `{{DOMAIN_ERROR_CODES}}` | error-codes.json 기반 | 에러 코드 테이블 |
| `{{DOMAIN_COMPLIANCE}}` | domain.compliance 기반 | 컴플라이언스 목록 |
| `{{CUSTOM_SECTION}}` | project.json → customSections | 사용자 정의 섹션 |

---

## 치환 로직

### 1. 값 해석 (Layered Override)

```python
def resolve_value(key: str) -> any:
    """
    우선순위:
    1. project.json (최우선)
    2. domain.json
    3. _base conventions
    4. 하드코딩 기본값
    """
    # Step 1: project.json 확인
    value = project_json.get(key)
    if value is not None:
        return value

    # Step 2: domain.json 확인
    domain_id = project_json.get("domain", "general")
    domain_config = load_domain_json(domain_id)
    value = domain_config.get(key)
    if value is not None:
        return value

    # Step 3: _base conventions 확인
    base_conventions = load_base_conventions()
    value = base_conventions.get(key)
    if value is not None:
        return value

    # Step 4: 기본값 반환
    return DEFAULTS.get(key, "")
```

### 2. 단순 마커 치환

```python
def substitute_simple_markers(template: str, values: dict) -> str:
    """
    {{MARKER_NAME}} 형태의 마커를 값으로 치환
    """
    result = template
    for marker, value in values.items():
        result = result.replace(f"{{{{{marker}}}}}", str(value))
    return result
```

### 3. 블록 마커 생성

각 블록 마커는 전용 생성 함수를 사용합니다.

---

## 블록 생성기

### TECH_STACK_SECTION

```python
def generate_tech_stack_section(tech_stack: dict) -> str:
    """
    기술 스택 섹션 생성
    """
    lines = []

    mapping = {
        "backend": "백엔드",
        "frontend": "프론트엔드",
        "database": "데이터베이스",
        "cache": "캐시",
        "infrastructure": "인프라"
    }

    for key, label in mapping.items():
        value = tech_stack.get(key)
        if value:
            lines.append(f"- **{label}**: {value}")

    return "\n".join(lines)
```

**출력 예시:**
```markdown
- **백엔드**: Spring Boot 3 (Kotlin)
- **프론트엔드**: Next.js
- **데이터베이스**: MySQL
- **캐시**: Redis
```

### AGENTS_SECTION

```python
def generate_agents_section(agents: dict) -> str:
    """
    활성화된 에이전트 섹션 생성
    """
    enabled = agents.get("enabled", [])

    agent_info = {
        "pm": {"icon": "🎯", "name": "agent-pm", "role": "총괄 오케스트레이터"},
        "backend": {"icon": "⚙️", "name": "agent-backend", "role": "백엔드 개발"},
        "frontend": {"icon": "🎨", "name": "agent-frontend", "role": "프론트엔드 개발"},
        "code-reviewer": {"icon": "👀", "name": "agent-code-reviewer", "role": "코드 리뷰"},
        "qa": {"icon": "🧪", "name": "agent-qa", "role": "테스트/품질 검증"},
        "docs": {"icon": "📚", "name": "agent-docs", "role": "문서화"},
        "db-designer": {"icon": "🗃️", "name": "agent-db-designer", "role": "DB 설계"},
        "planner": {"icon": "📋", "name": "agent-planner", "role": "기획/요구사항 정의"}
    }

    lines = ["### 활성화된 에이전트", "", "| 에이전트 | 역할 |", "|----------|------|"]

    for agent_id in enabled:
        info = agent_info.get(agent_id, {})
        icon = info.get("icon", "")
        name = info.get("name", agent_id)
        role = info.get("role", "")
        lines.append(f"| {icon} `{name}` | {role} |")

    return "\n".join(lines)
```

**출력 예시:**
```markdown
### 활성화된 에이전트

| 에이전트 | 역할 |
|----------|------|
| 🎯 `agent-pm` | 총괄 오케스트레이터 |
| ⚙️ `agent-backend` | 백엔드 개발 |
| 👀 `agent-code-reviewer` | 코드 리뷰 |
```

### DOMAIN_DOCS_MAPPING

```python
def generate_docs_mapping(domain_config: dict) -> str:
    """
    도메인 참고자료 키워드 매핑 테이블 생성
    """
    keyword_mapping = domain_config.get("keywordMapping", {})

    if not keyword_mapping:
        return ""

    lines = [
        "---",
        "",
        "## 참고자료 자동 참조",
        "",
        "다음 키워드 사용 시 관련 참고자료가 자동 참조됩니다:",
        "",
        "| 키워드 | 참조 문서 |",
        "|--------|----------|"
    ]

    for doc, keywords in keyword_mapping.items():
        keyword_str = ", ".join(keywords)
        lines.append(f"| {keyword_str} | `{doc}` |")

    return "\n".join(lines)
```

**출력 예시:**
```markdown
---

## 참고자료 자동 참조

다음 키워드 사용 시 관련 참고자료가 자동 참조됩니다:

| 키워드 | 참조 문서 |
|--------|----------|
| 결제, 승인, 인증 | `payment-flow.md` |
| 정산, 수수료, D+N | `settlement.md` |
| 취소, 환불 | `refund-cancel.md` |
```

### CONVENTIONS_SECTION

```python
def generate_conventions_section(project: dict, domain: dict) -> str:
    """
    코딩 컨벤션 섹션 생성
    기술 스택에 따라 적절한 컨벤션 로드
    """
    tech_stack = project.get("techStack", {})
    backend = tech_stack.get("backend", "")

    # 백엔드 스택별 컨벤션 파일 선택
    if "kotlin" in backend.lower():
        return load_convention_template("kotlin")
    elif "java" in backend.lower():
        return load_convention_template("java")
    elif "node" in backend.lower() or "typescript" in backend.lower():
        return load_convention_template("typescript")
    elif "go" in backend.lower():
        return load_convention_template("go")
    else:
        return load_convention_template("default")
```

### DOMAIN_ERROR_CODES

```python
def generate_error_codes_section(domain_id: str) -> str:
    """
    도메인 에러 코드 테이블 생성
    """
    error_codes_path = f".claude/domains/{domain_id}/error-codes/error-codes.json"

    if not os.path.exists(error_codes_path):
        return ""

    error_codes = load_json(error_codes_path)

    lines = [
        "## 에러 코드 체계",
        "",
        "| 코드 | HTTP | 설명 |",
        "|------|------|------|"
    ]

    for code, info in error_codes.items():
        http_status = info.get("httpStatus", 500)
        description = info.get("description", "")
        lines.append(f"| {code} | {http_status} | {description} |")

    return "\n".join(lines)
```

### DOMAIN_COMPLIANCE

```python
def generate_compliance_section(domain_config: dict) -> str:
    """
    도메인 컴플라이언스 목록 생성
    """
    compliance = domain_config.get("compliance", [])

    if not compliance:
        return "해당 없음"

    return ", ".join(compliance)
```

---

## 커스텀 섹션 보존

도메인 전환 시 사용자가 추가한 커스텀 규칙을 보존합니다.

### 커스텀 섹션 마커

CLAUDE.md 템플릿에서 커스텀 섹션은 다음 마커로 구분됩니다:

```markdown
<!-- CUSTOM_SECTION_START -->
(사용자 커스텀 규칙)
<!-- CUSTOM_SECTION_END -->
```

### 커스텀 섹션 추출

```python
def extract_custom_section(existing_claude_md: str) -> str:
    """
    기존 CLAUDE.md에서 커스텀 섹션 추출

    Returns:
        커스텀 섹션 내용 (마커 제외), 없으면 빈 문자열
    """
    START_MARKER = "<!-- CUSTOM_SECTION_START -->"
    END_MARKER = "<!-- CUSTOM_SECTION_END -->"

    start_idx = existing_claude_md.find(START_MARKER)
    end_idx = existing_claude_md.find(END_MARKER)

    if start_idx == -1 or end_idx == -1:
        return ""

    # 마커 사이의 내용 추출 (마커 자체는 제외)
    content_start = start_idx + len(START_MARKER)
    custom_content = existing_claude_md[content_start:end_idx].strip()

    return custom_content
```

### 커스텀 섹션 보존하며 재생성

```python
def generate_claude_md_with_preservation(
    project_json_path: str,
    existing_claude_md_path: str = "CLAUDE.md"
) -> str:
    """
    커스텀 섹션을 보존하며 CLAUDE.md 재생성

    Args:
        project_json_path: project.json 경로
        existing_claude_md_path: 기존 CLAUDE.md 경로 (커스텀 섹션 추출용)

    Returns:
        생성된 CLAUDE.md 내용
    """
    # 1. 기존 CLAUDE.md에서 커스텀 섹션 추출
    custom_section = ""
    if os.path.exists(existing_claude_md_path):
        with open(existing_claude_md_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        custom_section = extract_custom_section(existing_content)

    # 2. 새 CLAUDE.md 생성 (기존 로직)
    new_content = generate_claude_md(project_json_path)

    # 3. 커스텀 섹션 복원
    if custom_section:
        # {{CUSTOM_SECTION}} 또는 빈 커스텀 섹션을 기존 내용으로 교체
        START_MARKER = "<!-- CUSTOM_SECTION_START -->"
        END_MARKER = "<!-- CUSTOM_SECTION_END -->"

        # 마커 사이 내용을 커스텀 섹션으로 교체
        start_idx = new_content.find(START_MARKER)
        end_idx = new_content.find(END_MARKER)

        if start_idx != -1 and end_idx != -1:
            before = new_content[:start_idx + len(START_MARKER)]
            after = new_content[end_idx:]
            new_content = f"{before}\n{custom_section}\n{after}"

    return new_content
```

---

## 전체 처리 플로우

```python
def generate_claude_md(project_json_path: str) -> str:
    """
    CLAUDE.md 생성 메인 함수
    """
    # 1. 입력 파일 로드
    project = load_json(project_json_path)
    domain_id = project.get("domain", "general")
    domain = load_domain_json(domain_id)

    # 2. 템플릿 로드
    template = load_template(".claude/templates/CLAUDE.md.tmpl")

    # 3. 단순 마커 값 준비
    simple_values = {
        "PROJECT_NAME": project.get("name", "My Project"),
        "PROJECT_DESCRIPTION": project.get("description", ""),
        "DOMAIN_ID": domain_id,
        "DOMAIN_NAME": domain.get("name", "범용"),
        "DOMAIN_ICON": domain.get("icon", "🔧"),
        "TASK_PREFIX": resolve_task_prefix(project, domain),
        "PR_LINE_LIMIT": resolve_pr_line_limit(project, domain),
        "TEST_COVERAGE": resolve_test_coverage(project, domain),
    }

    # 4. 블록 마커 값 준비
    block_values = {
        "TECH_STACK_SECTION": generate_tech_stack_section(project.get("techStack", {})),
        "AGENTS_SECTION": generate_agents_section(project.get("agents", {})),
        "CONVENTIONS_SECTION": generate_conventions_section(project, domain),
        "DOMAIN_DOCS_MAPPING": generate_docs_mapping(domain),
        "DOMAIN_ERROR_CODES": generate_error_codes_section(domain_id),
        "DOMAIN_COMPLIANCE": generate_compliance_section(domain),
        "CUSTOM_SECTION": "",  # 초기 생성 시 빈 값, 보존 시 extract_custom_section()으로 대체
    }

    # 5. 마커 치환
    result = template
    for marker, value in {**simple_values, **block_values}.items():
        result = result.replace(f"{{{{{marker}}}}}", str(value))

    return result
```

---

## 사용 시점

### 1. 프로젝트 초기화 (skill-init)

```
/skill-init
  ↓
대화형 설정 수집
  ↓
project.json 생성
  ↓
generate_claude_md() 호출
  ↓
CLAUDE.md 생성
```

### 2. 도메인 전환 (skill-domain switch)

```
/skill-domain switch ecommerce
  ↓
기존 CLAUDE.md에서 커스텀 섹션 추출
  ↓
project.json의 domain 필드 업데이트
  ↓
generate_claude_md() 호출
  ↓
CLAUDE.md 재생성 (커스텀 섹션 복원)
```

### 3. 설정 변경

```
project.json 수동 편집
  ↓
/skill-status (변경 감지)
  ↓
CLAUDE.md 재생성 제안
```

---

## 확장 포인트

### 커스텀 마커 추가

1. `TEMPLATE-ENGINE.md`에 마커 정의 추가
2. `CLAUDE.md.tmpl`에 마커 사용
3. 생성 함수 구현

### 도메인별 템플릿 오버라이드

```
.claude/domains/fintech/templates/CLAUDE.md.tmpl  # 도메인 전용 템플릿
.claude/templates/CLAUDE.md.tmpl                  # 기본 템플릿
```

도메인 템플릿이 있으면 우선 사용합니다.

### 코드 템플릿 스택 기반 자동 선택

코드 템플릿(`.tmpl`)은 백엔드 스택에 따라 자동 선택됩니다.

**파일 확장자 규칙:**
| 스택 | 확장자 | 예시 |
|------|--------|------|
| spring-boot-kotlin | `.kt.tmpl` | `state-machine.kt.tmpl` |
| spring-boot-java | `.java.tmpl` | `state-machine.java.tmpl` |
| nodejs-typescript | `.ts.tmpl` | `state-machine.ts.tmpl` |
| go | `.go.tmpl` | `state-machine.go.tmpl` |

**선택 로직:**
```python
def select_template(template_name: str, tech_stack: dict, domain: str) -> str:
    """
    스택 기반 템플릿 파일 선택

    1. project.json의 techStack.backend 확인
    2. 해당 확장자의 템플릿 파일 검색
    3. 없으면 .kt.tmpl 폴백 (기본)
    """
    backend = tech_stack.get("backend", "spring-boot-kotlin")

    ext_map = {
        "spring-boot-kotlin": ".kt.tmpl",
        "spring-boot-java": ".java.tmpl",
        "nodejs-typescript": ".ts.tmpl",
        "go": ".go.tmpl",
    }

    ext = ext_map.get(backend, ".kt.tmpl")
    template_path = f".claude/domains/{domain}/templates/{template_name}{ext}"

    if os.path.exists(template_path):
        return template_path

    # 폴백: Kotlin 템플릿
    fallback = f".claude/domains/{domain}/templates/{template_name}.kt.tmpl"
    return fallback if os.path.exists(fallback) else None
```

**사용 시점:**
- `skill-plan` — 설계 분석 시 관련 템플릿 참조
- `skill-impl` — 코드 생성 시 템플릿 기반 스캐폴딩

**현재 지원 현황:**
| 도메인 | `.kt.tmpl` | `.ts.tmpl` | `.java.tmpl` | `.go.tmpl` |
|--------|-----------|-----------|-------------|-----------|
| fintech | 5개 | 4개 | - | - |
| ecommerce | 3개 | 3개 | - | - |

### PR Body 템플릿

PR 생성 시 사용되는 body 템플릿입니다.

#### 파일 위치
```
.claude/templates/pr-body.md.tmpl                    # 기본 템플릿
.claude/domains/{domain}/templates/pr-body.md.tmpl   # 도메인 오버라이드
```

#### 마커 정의

| 마커 | 출처 | 기본값 | 설명 |
|------|------|--------|------|
| `{{TASK_TITLE}}` | 런타임 | "" | Task 제목 |
| `{{STEP_NUMBER}}` | 런타임 | "1" | 현재 스텝 번호 |
| `{{STEP_TOTAL}}` | 런타임 | "1" | 전체 스텝 수 |
| `{{CHANGES_LIST}}` | 런타임 (git diff) | "" | 변경 사항 목록 |

#### 사용 시점
- `skill-impl` → PR 생성 시 자동 로드

### 조건부 섹션

```markdown
{{#if HAS_FRONTEND}}
## 프론트엔드 가이드
...
{{/if}}
```

조건부 블록은 `{{#if CONDITION}}...{{/if}}` 형식으로 지원 예정입니다.

---

## 기본값 정의

```json
{
  "DEFAULTS": {
    "PROJECT_NAME": "My Project",
    "PROJECT_DESCRIPTION": "",
    "DOMAIN_ID": "general",
    "DOMAIN_NAME": "범용",
    "DOMAIN_ICON": "🔧",
    "TASK_PREFIX": "TASK",
    "PR_LINE_LIMIT": 500,
    "TEST_COVERAGE": 80,
    "BRANCH_STRATEGY": "git-flow",
    "COMMIT_FORMAT": "conventional"
  }
}
```

---

## 검증 규칙

### 필수 마커 검증

템플릿 처리 후 치환되지 않은 마커가 있으면 경고:

```
⚠️ 미치환 마커 발견: {{CUSTOM_MARKER}}
project.json 또는 domain.json에 해당 값을 추가하세요.
```

### 출력 검증

생성된 CLAUDE.md의 유효성 검증:

1. 마크다운 문법 검증
2. 코드 블록 닫힘 확인
3. 테이블 형식 확인
4. 빈 섹션 경고

---

## 관련 파일

| 파일 | 설명 |
|------|------|
| `.claude/templates/CLAUDE.md.tmpl` | 메인 템플릿 |
| `.claude/schemas/project.json` | project.json 스키마 |
| `.claude/domains/{domain}/domain.json` | 도메인 설정 |
| `.claude/domains/_base/conventions/` | 공통 컨벤션 |
