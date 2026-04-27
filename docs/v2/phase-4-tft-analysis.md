# Phase 4: TFT 분석 — 4-Layer Override + Constraint Rules

> **Step**: 0 (설계문서, PR 없음)
> **상위 계획**: [phase-4-rules.md](./phase-4-rules.md)
> **상세 계획**: [phase-4-plan.md](./phase-4-plan.md)
> **분석 일자**: 2026-04-27

---

## 1. 4-Layer Override 의미 재정의 (선행 확정)

상위 문서의 "4층"은 **개념적 우선순위 모델**이며, 각 영역(conventions/checklists/health/rules)이 모두 4층을 사용한다는 뜻이 아니다. Phase 4는 다음과 같이 한정한다.

### 1.1 4층 우선순위 모델 (개념)

```
1. project.json (사용자 설정)              ← 최우선 (가장 좁은 범위)
2. .claude/rules/{domain}/{language}/      ← 도메인 × 언어 교차 (Phase 4 신설)
3. .claude/domains/{domain}/               ← 도메인 (기존)
4. .claude/domains/_base/                  ← 공통 기본 (기존)
```

### 1.2 영역별 실제 적용 범위 (D1 — 결정)

| 영역 | 현재 적용 층수 | Phase 4 변경 | 근거 |
|------|--------------|-------------|------|
| `conventions/` | 1층 (`_base`만) | **변경 없음** | conventions = 도메인 무관 권장. 4층 일반화는 범위 초과 |
| `checklists/` | 2층 (`_base` + `{domain}`) | **변경 없음** | 도메인 체크리스트는 현 구조로 충분. 언어 분기 필요 시 rules로 처리 |
| `health/_category.json` | 2층 (`_base` + `{domain}` 가중치 병합) | **변경 없음** | Phase 1에서 이미 정착, 가중치 정합성 위험 |
| `rules/` (신규) | **4층 중 3번째 층 신설** | **추가** | 도메인 × 언어 교차에서만 의미. `_base/rules`/`{domain}/rules`는 만들지 않음 |

> **핵심**: Phase 4의 "4층 도입"은 **rules 영역 신설** + **개념 모델 명문화**이며, 기존 영역 구조는 보존한다. README/concepts 다이어그램의 4층 표기는 우선순위 모델을 의미하고, 실제 디렉토리 추가는 rules에 한정한다.

### 1.3 H001 (Phase 4 ↛ Phase 2 의존) 재확인

상위 문서 §39 "H001: Phase 2 의존 근거 불명확 → 제거" 그대로. rules 로드는 skillProfile/workflowProfile과 독립이며 skill-review-pr 단계에서 project.json의 domain + techStack만 사용한다.

---

## 2. conventions vs rules 경계 (H002 — 선행 확정)

상위 문서 TFT Architect 항목 §31. 다음 매트릭스로 SSOT 확정.

### 2.1 정의 매트릭스

| 축 | conventions | rules |
|----|------------|-------|
| 강제도 | SHOULD (권장) | MUST / MUST NOT (제약) |
| 적용 범위 | 도메인 무관 또는 언어 단독 | **도메인 × 언어 교차에서만** |
| 위반 시 | 리뷰에서 권고 | 리뷰에서 **CRITICAL/MAJOR 지적** |
| 예시 | "Pydantic 스키마 분리" | "PHI 변수를 logger 인자로 전달 금지" |
| 형식 | prose md | **frontmatter 필수** + prose + 좋은/나쁜 코드 예시 |
| 위치 | `_base/conventions/` (1곳) | `.claude/rules/{domain}/{language}/` (교차점) |

### 2.2 기존 conventions 24개 감사 결과

기존 24개 파일을 검토한 결과, **rules로 승격해야 할 항목은 없다**. 근거:

| 파일군 | 도메인 종속? | rules 승격? | 사유 |
|-------|-----------|-----------|------|
| python-dependency, python-patterns, python-project-structure, python-testing | ❌ | ❌ | 언어 단독 권장. 모든 도메인 동일 적용 |
| frontend-component, frontend-state, frontend-styling, frontend-testing | ❌ | ❌ | 프론트엔드 일반 권장 |
| api-design, cache, database, deployment, error-handling, git-workflow, logging, message-queue, monitoring, naming, project-structure, security, testing | ❌ | ❌ | 범용 SHOULD 수준 |

→ **conventions는 그대로 유지**. rules는 **신규 디렉토리**에서만 생성한다.

### 2.3 중복 회피 규칙 (rules/README.md에 명시)

1. **rules는 도메인 + 언어 교차에서만 존재**한다. `_base/rules/`와 `{domain}/rules/`는 만들지 않는다.
2. **conventions에 있는 내용을 rules에 중복 기술하지 않는다**. 단, 도메인 맥락에서 강제 수준이 달라질 때(SHOULD → MUST)만 rules로 작성한다.
3. **rules는 "Claude가 이미 아는 기술 사용법"이 아니라 "도메인 비즈니스 제약"이다**. 예: "Pydantic 사용법" ✗, "환자 식별자를 로그에 기록 금지" ✓.

---

## 3. domain-first vs merge 정책 (실제 적용 방식)

### 3.1 정책 의미 명문화

| 정책 | 동작 | 적용 시점 |
|------|------|---------|
| `domain-first` (default) | 도메인 제약이 언어 룰을 덮어씀 (도메인이 강함) | rules 충돌 시 도메인 메시지 우선 |
| `merge` | 양쪽 모두 적용 (가장 엄격한 합집합) | 모든 rules 동시 적용 |

### 3.2 실제 충돌 시나리오 분석

상위 문서 Domain Lead §38: "healthcare가 모든 로깅 허용 vs python rules가 PHI 로깅 금지" 시나리오 검토.

- **MVP 단계 결론**: rules는 **도메인 × 언어 단일 디렉토리**(`{domain}/{language}/`)에 위치하므로, 동일 위치에 동일 주제 충돌은 구조적으로 발생하지 않는다.
- **잠재 충돌**: 향후 `{domain}` 단독 룰(예: healthcare 일반)과 `{language}` 단독 룰(예: python 일반)이 도입될 때 발생 가능. 그러나 §1.2 결정으로 두 단독 층은 **만들지 않는다** → MVP에서 충돌 자체가 없음.
- **실용 의미**: `overridePriority` 필드는 **향후 확장용 예약**. MVP에서는 두 값 모두 동일 동작이며 정책 분기 로직을 구현하지 않는다.

### 3.3 결정 (D2)

- `overridePriority` 필드는 schema에 enum + default `domain-first`로 활성화한다.
- **MVP 동작**: 단일 디렉토리 로드. 분기 로직 미구현(향후 Phase로 이관).
- **문서화**: rules/README.md와 docs/concepts.md에 "현재 MVP에서는 충돌 없음. 정책은 향후 확장 시 활성화" 명시.

---

## 4. language 매핑 (D3 — 신설 SSOT)

### 4.1 techStack.backend → language 매핑 테이블

| `techStack.backend` (project.json) | `language` (rules 디렉토리명) |
|-----------------------------------|----------------------------|
| `spring-boot-kotlin` | `kotlin` |
| `spring-boot-java` | `java` |
| `nodejs-typescript` | `typescript` |
| `python-fastapi` | `python` |
| `python-django` | `python` |
| `go` | `go` |
| `none` | (매핑 없음 → rules 로드 스킵) |

### 4.2 매핑 SSOT 위치

- **위치**: `.claude/rules/README.md`에 표 형태로 정의 + skill-review-pr이 직접 참조.
- **이유**: schema enum이나 별도 JSON으로 두면 `none` 케이스/공백 케이스 처리 분산. README가 사람·LLM 모두에게 가독성 우위.
- **검증**: skill-validate가 `.claude/rules/{domain}/{language}/` 디렉토리의 language 부분이 위 매핑 우측 값에 속하는지 확인.

### 4.3 frontend 매핑은 MVP 제외

- 이유: frontend rules가 MVP 3개 중 0개. tenant-isolation은 backend(typescript=Node) 가정.
- 향후: `techStack.frontend` enum(nextjs/react/vue)을 별도 매핑 또는 `typescript`/`javascript`로 통합 — Phase 7+로 이관.

---

## 5. MVP 3개 Rules 상세 설계

### 5.1 `healthcare/python/phi-logging-guard.md`

**제약 (MUST NOT)**: HIPAA Safe Harbor 18개 식별자를 logger 호출 인자에 직접 전달 금지.

**탐지 패턴 (예시 정규식)**:
- `logger\.(info|warn|error|debug)\([^)]*\b(patient|ssn|dob|mrn|email|phone|address|name)\b`
- `print\([^)]*\b(patient|ssn|dob|mrn)\b`
- f-string에 직접 변수 삽입: `f["].*\{patient\.\w+\}.*["]`

**좋은 예**:
```python
logger.info("patient_record_accessed", extra={"patient_id_hash": hash_phi(pid)})
```

**나쁜 예**:
```python
logger.info(f"Patient {patient.name} accessed record {record_id}")
```

**근거**: HIPAA Privacy Rule §164.514(b) Safe Harbor + healthcare/glossary.md "PHI 18개 식별자".

### 5.2 `fintech/kotlin/bigdecimal-money.md`

**제약 (MUST NOT)**: 금전 표현 변수에 `Double`/`Float` 사용 금지. **MUST**: `BigDecimal` + 명시적 `RoundingMode`.

**탐지 패턴**:
- `\b(Double|Float)\s+\w*(amount|price|balance|fee|cost|payment|charge|refund)\b`
- `:\s*(Double|Float)\s*=\s*[\d.]+\s*//.*?(원|won|krw|usd|eur)` (주석 단서)
- 산술 후 `.toDouble()` 캐스팅

**좋은 예**:
```kotlin
val amount: BigDecimal = BigDecimal("100.50")
val total: BigDecimal = amount.multiply(rate).setScale(2, RoundingMode.HALF_EVEN)
```

**나쁜 예**:
```kotlin
val amount: Double = 100.50
val total = amount * rate  // 부동소수점 오차 발생
```

**근거**: fintech/checklists/domain-logic.md "BigDecimal 필수" + fintech/docs/payment-flow.md.

### 5.3 `saas/typescript/tenant-isolation.md`

**제약 (MUST)**: 멀티테넌트 비즈니스 테이블 쿼리에 `tenant_id` 조건 필수 누락 금지.

**탐지 패턴**:
- `db\.query\(["'`]SELECT\b(?![^)]*\btenant_id\b)` (SELECT에 tenant_id 부재)
- `\.from\(["'`](orders|users|invoices|subscriptions)["'`]\)` 후 `.where(...)` 누락
- ORM `findMany\(\{\s*\}\)` (빈 where)

**좋은 예**:
```typescript
const orders = await db.query(
  "SELECT * FROM orders WHERE tenant_id = $1 AND status = $2",
  [ctx.tenantId, status]
);
```

**나쁜 예**:
```typescript
const orders = await db.query("SELECT * FROM orders WHERE status = $1", [status]);
// → 다른 테넌트 데이터 노출
```

**근거**: saas/docs/tenant-isolation.md "tenant_id 필수 컬럼" + GDPR Art. 32 (데이터 격리).

### 5.4 공통 frontmatter 스키마

```yaml
---
id: <kebab-case>
domain: <healthcare|fintech|saas|...>
language: <python|kotlin|typescript|java|go>
severity: <CRITICAL|MAJOR|MINOR>
triggers:
  - "<정규식>"
related:
  - "<참조 문서 경로>"
---
```

skill-validate가 frontmatter 필드 존재 여부를 검증한다(향후 Phase). MVP에서는 README의 가이드라인만 명시.

---

## 6. skill-review-pr 통합 설계

### 6.1 로드 시점

PR 리뷰 Step 1(PR 정보 수집)과 Step 2(체크리스트) 사이에 **rules 로드 단계**를 신설한다.

```
1. PR 정보 수집 (gh pr view, diff)
2. [신설] Rules 로드:
   a. project.json의 domain, techStack.backend 읽기
   b. language 매핑 (§4.1)
   c. .claude/rules/{domain}/{language}/*.md 글롭
   d. 존재하면 파일 경로 목록 수집 (Read는 에이전트가 수행)
3. 체크리스트 검증 (기존)
4. N관점 병렬 리뷰
   ↳ pr-reviewer-domain 에이전트에게 rules 파일 경로를 컨텍스트로 전달
```

### 6.2 에이전트 전달 방식

- **방식**: 기존 diff 파일 경로 전달과 동일 패턴. 프롬프트에 rules 파일 경로 목록만 포함하고, 에이전트가 Read로 자유롭게 참조한다.
- **이유**: 프롬프트 토큰 폭증 방지. PR 리뷰 토큰 절감 정책(SKILL.md L165) 일관성.

### 6.3 부재 시 동작

- `.claude/rules/` 디렉토리 자체가 없으면 → 단계 전체 SKIP. 기존 동작 유지.
- 디렉토리는 있으나 해당 `{domain}/{language}/` 매칭 없으면 → 빈 목록으로 단계 통과.

### 6.4 적용 대상 에이전트

- **pr-reviewer-domain**: rules 참조 의무. 위반 시 CRITICAL/MAJOR로 보고.
- **pr-reviewer-security**: 보안 영역(Phase 5)과 분리. rules는 도메인 비즈니스 제약 — security 에이전트는 참조하지 않음.
- **pr-reviewer-test**: 영향 없음.

---

## 7. TFT 5인 분석 결과

### 7.1 Architect

- **결론**: rules 신규 디렉토리 + skill-review-pr Step 2.5 신설 안전. 기존 영역 보존.
- **결정**: `overridePriority`는 schema에 enum 활성화만 하고 분기 로직 미구현(MVP). 향후 Phase에서 단독 도메인/단독 언어 룰이 도입될 때 활성화.
- **기술 부채**: rules.schema.json(frontmatter 검증)은 Phase 4 범위 외 — 향후 skill-validate 확장 시.

### 7.2 Security Lead

- **결론**: rules가 보안(Phase 5)과 겹치지 않음 명문화 필요.
  - rules = **도메인 비즈니스 제약** (BigDecimal 필수, PHI 로깅 금지 등 *도메인 의미*가 들어가는 항목)
  - Phase 5 = **범용 보안** (secrets, SQL injection, CORS, auth — 도메인 무관)
- **경계 충돌 케이스**: PHI 로깅 금지는 보안과 도메인 모두 관련 → **rules에 둠**(도메인 의미가 본질). Phase 5에서는 일반 시크릿 패턴만 검사.

### 7.3 DX Lead

- **결론**: rules/README.md에 "rules vs conventions" 가시 비교표 필수. 신규 작성 가이드도 명시.
- **사용자 메시지**: skill-review-pr 출력에 `📋 적용 Rules: healthcare/python (1개)` 형태로 어떤 rules가 적용됐는지 표시 → 디버깅성 확보.

### 7.4 Product Lead

- **결론**: MVP 3개 모두 "도메인 제약"으로 검증됨. 기술 교육으로 흐르지 않음.
  - phi-logging-guard: HIPAA 의미 (도메인) ✓
  - bigdecimal-money: 금전 정확성 의미 (도메인) ✓
  - tenant-isolation: 멀티테넌시 의미 (도메인) ✓
- **범위 검증**: `_base/rules/`, `{domain}/rules/`, frontend rules, 4층 일반화 없음 — 모두 범위 초과로 후속 Phase 이관 확정.

### 7.5 Domain Lead

- **결론**: 기존 도메인 docs/checklists와 rules의 역할 차별화 명확.
  - docs(`{domain}/docs/`) = **흐름 설명** (예: payment-flow.md)
  - checklists(`{domain}/checklists/`) = **검토 항목** (도메인 단위)
  - rules(`{domain}/{language}/`) = **언어 차원의 코드 패턴 제약**
- **MVP 3개 패턴 검증**: 각 도메인 docs/glossary와 일관 — phi(healthcare), BigDecimal(fintech), tenant_id(saas) 모두 기존 docs와 정합.

---

## 8. 실패/경계값 시나리오 (H012~H016 대응)

| # | 시나리오 | 기대 동작 |
|---|---------|---------|
| 1 | `.claude/rules/` 디렉토리 부재 | skill-review-pr Step 2.5 SKIP, 기존 동작 |
| 2 | 해당 `{domain}/{language}/` 매칭 없음 | 빈 목록, 도메인 에이전트에 "rules 없음" 안내 |
| 3 | `techStack.backend = "none"` | language 매핑 부재 → rules 로드 SKIP |
| 4 | 알 수 없는 backend (스키마 enum 외) | 매핑 부재 → SKIP + skill-validate WARN |
| 5 | rules 파일이 frontmatter 깨짐 | 에이전트가 prose만 활용. Phase 4에서는 검증 없음(향후 skill-validate 확장) |
| 6 | rules 파일 다수(>10개) | MVP는 3개만 가정. 토큰 폭증 시 향후 lazy-load |
| 7 | rules 파일 내 정규식이 PR 코드와 false positive | 에이전트(LLM)가 컨텍스트로 판단. 자동 차단 아님 — 리뷰 보고만 |
| 8 | `overridePriority: "merge"` 설정 | MVP에서 동일 동작 (단일 디렉토리). 향후 분기 시 활성화 |
| 9 | project.json에 domain 부재(general) | `general/{language}/` 디렉토리도 가능 — MVP는 비움(향후 작성) |
| 10 | rules 디렉토리에 잘못된 language(예: ruby) | language 매핑에 없음 → 무시. skill-validate가 WARN |

---

## 9. 리스크 및 대응

| ID | 리스크 | 확률 | 영향 | 대응 | 감지 스텝 |
|----|--------|------|------|------|----------|
| **R1** | language 매핑 enum 누락 시 rules 로드 실패 | 중 | 중 | rules/README.md에 매핑 SSOT + skill-validate가 디렉토리 일치 검사 | Step 1, 4 |
| **R2** | "Claude가 이미 아는 것을 가르치는" 함정 | 중 | 중 | rules/README.md에 "도메인 의미" 원칙 + Product Lead 검토 게이트 | Step 2 |
| **R3** | 정규식 trigger의 false positive | 높 | 낮 | MVP는 LLM 컨텍스트 해석 — 자동 차단 아님 (보고만) | Step 2 |
| **R4** | 기존 conventions와 rules 중복 | 중 | 중 | rules/README.md에 명확한 경계 정의 + 24개 감사 완료 | Step 1 |
| **R5** | rules 파일 다수 시 토큰 폭증 | 낮 | 중 | MVP 3개. 향후 lazy-load(Phase 7+로 이관) | — |
| **R6** | skill-review-pr Step 2.5 추가가 자기 PR 리뷰/Trivial 경량 리뷰와 충돌 | 낮 | 중 | Trivial 경량 리뷰는 rules 단계 SKIP(코드 변경 0건이므로) | Step 3 |
| **R7** | overridePriority 분기 미구현 → 사용자 혼동 | 낮 | 낮 | concepts.md에 "MVP는 단일 디렉토리, 향후 확장" 명시 | Step 4 |
| **R8** | docs/concepts.md 다이어그램 갱신이 v1 사용자에 혼동 | 낮 | 낮 | "Phase 4 도입" 주석 + customization.md에 마이그레이션 안내 | Step 4 |

---

## 10. 계획서 보정 사항 (phase-4-rules.md → phase-4-plan.md 반영)

다음 항목을 [phase-4-plan.md](./phase-4-plan.md)에 반영한다.

1. **§1.2**: "4층 일반화"는 **rules 신설**에 한정. 기존 영역 변경 없음 — 상위 phase-4-rules.md의 "4층" 표현이 모든 영역으로 확장된다는 오해 방지.
2. **§4.1**: language 매핑 테이블을 plan에 명시 + rules/README.md SSOT.
3. **§5**: MVP 3개 rules의 frontmatter 스키마와 패턴 예시를 plan에 반영.
4. **§6**: skill-review-pr Step 2.5 (Rules 로드) 단계 신설.
5. **§3**: `overridePriority` MVP는 분기 미구현. enum 활성화만.
6. **§9**: R1~R8 리스크 표 plan에 복사.

---

## 11. 사용자 결정: 옵션 A 채택 (2026-04-27)

§5에서 설계한 MVP 3개 콘텐츠와 §1~4의 메커니즘을 분리 평가한 결과, 사용자와의 협의(2026-04-27)로 다음과 같이 확정한다.

### 11.1 결정 근거

| 항목 | 메커니즘 (디렉토리/README/skill-review-pr 통합) | MVP 3개 콘텐츠 |
|------|----------------------------------------------|--------------|
| 가치 | 사용자가 자기 도메인 제약을 명문화할 토대. Phase 7 의존성 충족 | 패턴 예시 |
| 부재 시 영향 | rules 부재 → SKIP. 안 쓰면 영향 0 | 빠지면 메커니즘만 가동 |
| 위험 | 낮음 | false positive + **"Claude가 이미 아는 것은 가르치지 않는다" 원칙과 긴장** |
| 검증 환경 | 본 레포에서 dry-run 가능 | 실제 healthcare/python 등 실 프로젝트 부재로 검증 불가 |

**핵심 긴장**: phi-logging-guard, bigdecimal-money, tenant-isolation은 모두 Claude가 이미 학습한 도메인 지식. `domain` 시그널만 명시되면 알아서 권고하므로 rules 파일 3개는 중복 위험.

### 11.2 채택안: 옵션 A — 메커니즘만 구현, MVP 3개 콘텐츠 보류

- **포함**: rules 디렉토리 구조, rules/README.md(작성 가이드 + language 매핑 SSOT), schema description 보강, skill-review-pr Step 2.5, docs 4층 다이어그램, CHANGELOG/VERSION
- **제외**: §5에서 설계한 MVP 3개 rules 파일(phi-logging-guard / bigdecimal-money / tenant-isolation) — 실 사용 케이스 발생 시 사용자가 직접 작성
- **추가 보강**: rules/README.md에 **예시 템플릿 1개** 포함 (가짜 도메인 × 가짜 언어로 frontmatter + 좋은/나쁜 예시 패턴 시연 — "이런 형식으로 쓰세요" 가이드용)

### 11.3 Step 분리 갱신

| 신Step | 내용 | 비고 |
|-------|------|------|
| 0 | TFT 설계 (본 문서) | 완료 |
| 1 | rules 디렉토리 + README + schema description 보강 + 예시 템플릿 1개 | (구 Step 1 + 기능 추가) |
| 2 | skill-review-pr Step 2.5 통합 | (구 Step 3 → 신 Step 2) |
| 3 | concepts.md + customization.md 4층 다이어그램 | (구 Step 4 → 신 Step 3) |
| 4 | CHANGELOG + VERSION → alpha.3 | (구 Step 5 → 신 Step 4) |
| ~~구 Step 2~~ | ~~MVP 3개 rules 작성~~ | **제거** |

작업량: 5~7h → **3~4h**

### 11.4 §5 (MVP 3개 상세 설계)의 위치

§5에서 설계한 phi-logging-guard / bigdecimal-money / tenant-isolation의 frontmatter·정규식·예시는 **참고 자료로 보존**한다(삭제 X). 향후 사용자가 실제로 해당 도메인×언어 룰을 작성할 때 참조 가능.

---

## 12. Step 1 착수 Go/No-Go 체크

- [x] 4층 적용 범위(rules 한정) 확정
- [x] conventions vs rules 경계 매트릭스 확정 (H002)
- [x] 기존 24개 conventions 감사 완료 (승격 항목 0)
- [x] domain-first vs merge MVP 동작 확정 (단일 디렉토리, 분기 미구현)
- [x] language 매핑 SSOT 확정
- [x] skill-review-pr Step 2.5 통합 설계 확정
- [x] 5인 TFT 분석 완료
- [x] 실패 시나리오 10개 도출
- [x] 리스크 8건 식별 + 대응 확정
- [x] 옵션 A 채택 (MVP 콘텐츠 보류, 메커니즘만)
- [x] phase-4-plan.md 작성 (옵션 A 반영)
- [x] 사용자 최종 승인 (옵션 A, 2026-04-27)

**결론**: Step 1 착수 준비 완료.
