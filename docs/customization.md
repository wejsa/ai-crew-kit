# 도메인 확장 및 커스터마이징

> [← README로 돌아가기](../README.md)

## Layered Override

설정은 다음 순서로 적용되며, 상위가 하위를 오버라이드합니다 (v2.0.0-alpha.3 / Phase 4부터 4층):

```
project.json (사용자 설정)                ← 최우선
    ↑
.claude/rules/{domain}/{language}/        ← 도메인 × 언어 교차 (Phase 4 신설)
    ↑
domains/{domain}/domain.json              ← 도메인 설정
    ↑
domains/_base/                            ← 공통 기본값
    ↑
하드코딩 기본값                            ← 최하위
```

**예시:** fintech 도메인의 기본 테스트 커버리지는 80%이지만, `project.json`에 `testCoverage: 90`을 설정하면 90%가 적용됩니다.

**체크리스트 로딩 (2층 유지):**
1. `_base/checklists/` — 모든 도메인 공통 체크리스트
2. `{domain}/checklists/` — 도메인 특화 체크리스트 (공통에 추가)
3. `/skill-review-pr` 실행 시 두 레이어가 병합되어 적용

**Rules 로딩 (4층 중 2번째 — PR 리뷰 컨텍스트 한정, Phase 4):**
1. `project.json`의 `domain` + `techStack.backend` 읽기
2. language 매핑 → `.claude/rules/{domain}/{language}/*.md` 글롭
3. 매칭 파일을 `pr-reviewer-domain` 에이전트에 전달
4. 디렉토리 부재 또는 매칭 0개 → SKIP (기존 동작 유지)

> Rules는 도메인 비즈니스 제약(MUST/MUST NOT)을 언어별로 표현합니다. SHOULD 수준 권장은 conventions에 작성하세요. 자세한 사용법은 [도메인 × 언어 Rules](#도메인--언어-rules) 섹션과 [.claude/rules/README.md](../.claude/rules/README.md) 참조.

---

## domain.json 구조

각 도메인은 `.claude/domains/{domain-id}/domain.json`에 설정을 정의합니다.

```json
{
  "id": "ecommerce",
  "name": "이커머스",
  "icon": "🛒",
  "version": "1.0.0",
  "description": "상품, 주문, 재고, 배송, 프로모션 등 이커머스 서비스 도메인",

  "defaultStack": {
    "backend": "spring-boot-kotlin",
    "frontend": "nextjs",
    "database": "mysql",
    "cache": "redis",
    "messageQueue": "rabbitmq",
    "infrastructure": "docker-compose"
  },

  "compliance": ["전자상거래법", "소비자보호법", "개인정보보호법"],
  "errorCodePrefix": "EC",

  "conventions": {
    "taskPrefix": "EC",
    "branchStrategy": "git-flow",
    "commitFormat": "conventional"
  },

  "checklists": ["domain-logic.md", "compliance.md", "performance.md"],

  "keywords": {
    "order": {
      "triggers": ["주문", "결제", "구매", "체크아웃", "장바구니"],
      "docs": ["order-flow.md", "payment-integration.md"]
    },
    "inventory": {
      "triggers": ["재고", "품절", "입고", "출고"],
      "docs": ["inventory.md"]
    }
  }
}
```

### 주요 필드 설명

| 필드 | 용도 | 영향 범위 |
|------|------|----------|
| `defaultStack` | `/skill-init` 시 기본 기술 스택 | 프로젝트 초기화 |
| `compliance` | 리뷰 시 컴플라이언스 체크 항목 | `/skill-review-pr` |
| `errorCodePrefix` | 에러 코드 접두사 (예: EC-001) | 코드 생성, 문서 |
| `conventions` | Task ID/브랜치/커밋 형식 | `/skill-plan`, `/skill-impl` |
| `checklists` | 도메인 체크리스트 파일 목록 | `/skill-review`, `/skill-review-pr` |
| `keywords` | 키워드 → 참고자료 자동 매핑 | 개발 중 자동 참조 |

### keywords 동작 방식

사용자가 "주문 API 구현해줘"라고 요청하면:

1. "주문" 키워드가 `keywords.order.triggers`에 매칭
2. `order-flow.md`, `payment-integration.md`가 자동 참조
3. 해당 문서의 규칙을 반영하여 코드 생성

---

## 디렉토리 구조

```
.claude/
├── domains/
│   ├── _registry.json          # 도메인 목록 (모든 도메인 인덱스)
│   ├── _base/
│   │   ├── conventions/        # 공통 컨벤션 (24개)
│   │   │   ├── api-design.md
│   │   │   ├── database.md
│   │   │   ├── error-handling.md
│   │   │   ├── security.md
│   │   │   ├── testing.md
│   │   │   └── ...
│   │   └── checklists/         # 공통 체크리스트
│   ├── fintech/
│   │   ├── domain.json         # 도메인 설정
│   │   ├── docs/               # 참고자료 (9개)
│   │   │   ├── payment-flow.md
│   │   │   ├── token-auth.md
│   │   │   └── ...
│   │   └── checklists/         # 리뷰 체크리스트 (3개)
│   │       ├── compliance.md
│   │       ├── domain-logic.md
│   │       └── security.md
│   ├── ecommerce/
│   │   ├── domain.json
│   │   ├── docs/
│   │   └── checklists/
│   └── general/
│       ├── domain.json
│       └── docs/
└── rules/                       # Phase 4 신설 — 도메인 × 언어 교차 제약
    ├── README.md                # rules vs conventions 경계, language 매핑 SSOT
    └── _example/_example/       # 학습용 템플릿 (실제 리뷰 미적용)
        └── sample-rule.md
    # 사용자가 필요 시 다음 형태로 추가:
    #   {domain}/{language}/{rule-id}.md
    #   예: healthcare/python/phi-logging-guard.md
```

---

## 참고자료 추가

도메인에 참고자료를 추가하면 `keywords` 매핑을 통해 개발 시 자동 참조됩니다.

```bash
# 로컬 파일 추가
/skill-domain add-doc docs/my-guide.md

# URL에서 추가
/skill-domain add-doc "https://example.com/api-guide.md"
```

추가된 문서는 `{domain}/docs/`에 저장되고, `domain.json`의 `keywords`에 등록됩니다.

---

## 체크리스트 추가

```bash
/skill-domain add-checklist docs/my-checklist.md
```

### 체크리스트 형식

체크리스트는 마크다운 테이블로 작성합니다. `심각도`에 따라 리뷰 결과가 달라집니다:

- **CRITICAL** — 반드시 수정 필요 (리뷰 거절)
- **MAJOR** — 수정 권장 (조건부 승인)
- **MINOR** — 개선 제안

```markdown
# 주문 처리 체크리스트

## 상태 관리

| 항목 | 설명 | 심각도 |
|------|------|--------|
| 상태 머신 정합성 | 정의된 전이만 허용, 무효 전이 차단 | CRITICAL |
| 낙관적 락 | 재고 동시성 처리에 @Version 사용 | CRITICAL |
| 멱등성 보장 | 결제 요청에 멱등키 적용 | MAJOR |

## 보안

| 항목 | 설명 | 심각도 |
|------|------|--------|
| 배송지 암호화 | 개인정보 AES-256 암호화 저장 | CRITICAL |
| SQL Injection | 파라미터 바인딩 사용 확인 | CRITICAL |
| 인증 미들웨어 | 보호 경로에 인증 적용 | MAJOR |
```

추가된 체크리스트는 `{domain}/checklists/`에 저장되고, `/skill-review-pr` 실행 시 자동 적용됩니다.

---

## 도메인 × 언어 Rules

> v2.0.0-alpha.3 / Phase 4부터 도입. 메커니즘만 제공되며 콘텐츠는 사용자가 필요 시 직접 추가합니다.

도메인의 비즈니스 제약을 **언어별로** 명시할 때 사용합니다. PR 리뷰 시 `pr-reviewer-domain` 에이전트가 자동 참조합니다.

### rules vs conventions 비교

| 축 | conventions | rules |
|----|------------|-------|
| 강제도 | SHOULD (권장) | **MUST / MUST NOT** (제약) |
| 적용 범위 | 도메인 무관 또는 언어 단독 | **도메인 × 언어 교차** |
| 위반 시 | 리뷰에서 권고 | 리뷰에서 **CRITICAL/MAJOR 지적** |
| 예시 | "Pydantic 스키마 분리" | "PHI 변수를 logger 인자로 전달 금지" |
| 위치 | `domains/_base/conventions/` | `.claude/rules/{domain}/{language}/` |

### language 매핑

`project.json`의 `techStack.backend` 값을 다음 매핑으로 디렉토리명으로 변환합니다.

| `techStack.backend` | rules 디렉토리 |
|--------------------|---------------|
| `spring-boot-kotlin` | `kotlin` |
| `spring-boot-java` | `java` |
| `nodejs-typescript` | `typescript` |
| `python-fastapi` | `python` |
| `python-django` | `python` |
| `go` | `go` |
| `none` | (스킵) |

> 매핑 SSOT는 [.claude/rules/README.md](../.claude/rules/README.md). 표에 새 backend 추가 시 그 파일을 갱신하세요.

### 새 rule 추가 절차

1. `.claude/rules/{domain}/{language}/` 디렉토리 생성
2. `{rule-id}.md` 파일을 frontmatter 표준에 맞춰 작성:
   - `id`, `domain`, `language`, `severity` (CRITICAL/MAJOR/MINOR)
   - `triggers` (정규식 힌트, false positive 허용)
   - `related` (도메인 docs 링크)
3. 본문에 **MUST / MUST NOT 제약** + **좋은 예 / 나쁜 예 코드** 작성
4. PR로 머지 → 다음 리뷰부터 자동 적용

상세 작성 가이드는 [.claude/rules/README.md](../.claude/rules/README.md), 학습용 템플릿은 `.claude/rules/_example/_example/sample-rule.md` 참조.

### 작성 시 주의사항

- ❌ "Claude가 이미 아는 기술 사용법" (라이브러리 API, 언어 문법, 일반 보안)
- ✅ **도메인 비즈니스 제약** (HIPAA PHI 보호, 멀티테넌시 격리, 금전 정확성 등)
- ❌ 도메인 무관 권장사항 → conventions에 작성하세요
- ❌ `_base/rules/`, `{domain}/rules/` 단독 층 신규 생성 금지

### 현재 정책 (v2.0 MVP)

- **콘텐츠 0개**: alpha.3은 메커니즘만 제공. 사용자가 필요 시 직접 추가
- **`overridePriority` 분기 미구현**: 단일 디렉토리(도메인 × 언어 교차)라 충돌이 구조적으로 발생하지 않음. 향후 단독 도메인/언어 룰 도입 시 활성화

---

## 새 도메인 생성

### 방법 1: 기존 도메인 복제 (권장)

```bash
/skill-domain create my-domain --ref ecommerce
```

기존 도메인의 구조를 복제하고, 새 도메인에 맞게 수정할 수 있습니다.

### 방법 2: 수동 생성

```bash
# 1. 디렉토리 생성
mkdir -p .claude/domains/my-domain/{docs,checklists}

# 2. domain.json 작성 (위 구조 참고)

# 3. _registry.json에 등록
```

`_registry.json`에 추가할 항목:

```json
{
  "id": "my-domain",
  "name": "내 도메인",
  "icon": "🎯",
  "description": "커스텀 도메인 설명",
  "defaultStack": { "backend": "spring-boot-kotlin", "database": "postgresql" },
  "compliance": [],
  "keywords": ["관련", "키워드"],
  "maturity": "beta"
}
```

### 방법 3: 도메인 내보내기

다른 프로젝트에서 재사용할 수 있도록 도메인을 내보냅니다.

```bash
/skill-domain export my-domain
```

---

## 도메인 전환

```bash
# 도메인 목록 조회
/skill-domain list

# 도메인 전환
/skill-domain switch ecommerce
```

전환 시 `project.json`의 도메인이 변경되고, 해당 도메인의 체크리스트/참고자료/컨벤션이 적용됩니다.

---

## 커스텀 스킬 생성

```bash
# 스킬 스캐폴딩 생성
/skill-create
```

`.claude/skills/custom/` 디렉토리에 생성되며, `CLAUDE.md`의 `CUSTOM_SECTION`에 자동 등록됩니다. 프레임워크 업그레이드 시에도 커스텀 스킬은 보존됩니다.

---

## CUSTOM_SECTION 활용 예시

`CLAUDE.md`의 `<!-- CUSTOM_SECTION_START -->` ~ `<!-- CUSTOM_SECTION_END -->` 사이에 프로젝트 고유 규칙을 추가할 수 있습니다. 도메인 전환이나 프레임워크 업그레이드 시에도 이 영역은 자동 보존됩니다.

### 예시: 컨텍스트 압축 시 사용자 알림

기본 동작은 compact 발생 시 상태 파일을 재읽기하고 작업을 계속 진행합니다. 압축 발생을 알림 받고 싶다면 CUSTOM_SECTION에 추가하세요:

```markdown
<!-- CUSTOM_SECTION_START -->
## 컨텍스트 압축 알림 (프로젝트 규칙)

compact 감지 시 다음을 수행한다:
1. 상태 파일 재읽기 (backlog.json, plan 파일)
2. 사용자에게 알림: "⚠️ 컨텍스트 압축 발생 — 상태 복구 완료. 이전 대화 세부 맥락이 축약되었을 수 있습니다."
3. 사용자가 "계속" 또는 "중단" 선택
<!-- CUSTOM_SECTION_END -->
```

### 예시: 프로젝트 고유 코딩 규칙

```markdown
<!-- CUSTOM_SECTION_START -->
## 프로젝트 코딩 규칙

- 모든 API 응답은 `ApiResponse<T>` 래퍼 사용
- 예외는 `@ControllerAdvice`에서 일괄 처리
- 로그는 구조화 로깅 (JSON 포맷)
<!-- CUSTOM_SECTION_END -->
```
