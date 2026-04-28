# Phase 5: TFT 분석 — AgentShield-lite (보안 스캐너)

> **Step**: 0 (설계문서, PR 없음)
> **상위 계획**: [phase-5-security.md](./phase-5-security.md)
> **분석 일자**: 2026-04-27

---

## 0. 사전 진단: Phase 1 마이그레이션 부채 발견 (선결 항목)

Phase 5 작업 전 다음 부채를 인지하고 해결해야 한다.

### 0.1 현황: hook-safety 가중치 정합성 미확보

Phase 1에서 `_base/health/_category.json`에 `hook-safety` (weight 10)을 추가했으나, **도메인별 `_category.json` 4개**가 모두 dictionary에 `hook-safety`를 명시하지 않음.

| 도메인 | 도메인 dictionary 합 | 자동 추가되는 _base hook-safety | 실제 합 | 정규화 발생 |
|--------|----------------|--------|---------|----------|
| fintech (형태 A) | doc-sync 20 + state-integrity 15 + security 15 + agent-config 10 + compliance 40 = **100** | 10 | **110** | ✓ |
| ecommerce (형태 B) | doc-sync 25 + state-integrity 20 + security 20 + agent-config 10 + inventory-consistency 25 = **100** | 10 | **110** | ✓ |
| saas (형태 B) | doc-sync 20 + state-integrity 15 + security 15 + agent-config 10 + tenant-isolation 40 = **100** | 10 | **110** | ✓ |
| healthcare (형태 B) | doc-sync 15 + state-integrity 15 + security 15 + agent-config 10 + phi-protection 45 = **100** | 10 | **110** | ✓ |

**결과**: skill-health-check Phase A §3은 합 ≠ 100 시 자동 정규화하므로 **모든 도메인 점수가 암묵적으로 ~9% 보정**되고 있음. 사용자가 인지하지 못한 채 점수가 변경됨 (alpha.2 이후).

### 0.2 영향

- 도메인 사용자가 `_category.json`을 보고 가중치를 이해하면 실제 점수와 불일치
- Phase 5에서 추가 카테고리/항목 도입 시 정규화 누적으로 의미 추적 불가
- `phase-1-plan.md` Step 5 가중치 표(`doc-sync 32/state-integrity 23/security 23/agent-config 12/hook-safety 10`)가 _base에만 적용되고 도메인 override는 명시 없음 → **alpha.2 릴리스의 잠재 결함**

### 0.3 해결 정책 (D0 — 선결 결정)

Phase 5 Step 1에서 **부채 해소를 함께 처리**한다.
- 4개 도메인 `_category.json`에 `hook-safety` 명시 추가
- 정규화로 보정되던 비율을 명시적으로 재배분 (도메인별 합 100 일관)
- security-migration.md에 "alpha.2 → Phase 5 적용 시점 점수 변화" 매핑 포함

---

## 1. 범위 경계 재확인

상위 phase-5-security.md §10~17 그대로 유지. 단 §0의 hook-safety 부채 해소를 **Step 1 범위에 추가**한다.

| 이것만 한다 | 이것은 하지 않는다 |
|------------|-------------------|
| skill-health-check secrets 서브카테고리 | 별도 AgentShield 스킬/CLI |
| 도메인별 민감정보 패턴 라이브러리 (도메인별 옵션 결정 필요) | AST 기반 분석 |
| regex 기반 SEC-01 외부화 + 확장 | CI 파이프라인 자동 통합 |
| **hook-safety 가중치 도메인별 명시 추가 (D0 해소)** | MCP 서버 리스크 프로파일링 |
| 기존 SEC-01~04와의 중복 정리 | 외부 도구(Snyk 등) 연동 |

---

## 2. SEC ID 체계 통합 (H003 — 선행 확정)

### 2.1 현재 분포

| 출처 | ID | 검사 방식 |
|------|-----|---------|
| skill-health-check SKILL.md (SEC-01~04) | SEC-01 (민감정보 로깅), SEC-02 (SQL Injection), SEC-03 (CORS), SEC-04 (API 인증) | 인라인 정규식 (Grep) |
| Phase 5 신규 항목 | SEC-05 (하드코딩 시크릿), SEC-06 (.env 노출), SEC-07 (도메인별 민감 데이터 로깅) | 인라인 정규식 + 외부 패턴 |
| secrets-patterns.json | SEC-S01~S03 (common: api-key, secret/private-key, password) | 외부 JSON → 동적 로드 |

### 2.2 결정 (D1)

세 네임스페이스를 통합한다.

```
SEC-01 ─ 민감정보 로깅 (CRITICAL)            ← 기존 인라인 12패턴을 secrets-patterns.json common.runtime으로 외부화
SEC-02 ─ SQL Injection (CRITICAL)            ← 기존 유지
SEC-03 ─ CORS (MAJOR)                        ← 기존 유지
SEC-04 ─ API 인증 (MAJOR)                    ← 기존 유지
SEC-05 ─ 하드코딩 시크릿 (CRITICAL)           ← secrets-patterns.json common.hardcoded 로드
SEC-06 ─ 환경변수 파일 노출 (CRITICAL)        ← .env 게이트(gitignore 검사 + .env 평문 secret)
SEC-07 ─ 도메인별 민감 데이터 (CRITICAL)      ← secrets-patterns.json 도메인별 파일 로드 (도메인 콘텐츠 보유 시만 실행)
```

**SEC-S{nn}는 외부 패턴 ID로만 사용** — 검사 항목 ID가 아니다. SEC-01/05/07이 패턴 파일을 로드하여 매칭하면 리포트에 `SEC-01 (SEC-S04 매칭)` 형식으로 출처 표기.

### 2.3 SEC-01 ↔ SEC-05 분리 근거

- **SEC-01 (런타임 노출)**: `logger.info(password)` — 코드 실행 시 로그로 새는 패턴
- **SEC-05 (정적 노출)**: `const API_KEY = "abc123..."` — 소스에 박힌 시크릿
- 양자 모두 secrets-patterns.json에서 로드하지만 **검사 대상 코드 위치가 다름** (logger 호출 vs 변수 할당)

---

## 3. Phase 4 rules와의 경계 재확인 (H004)

### 3.1 핵심 분리

| 축 | Phase 4 rules | Phase 5 secrets |
|----|--------------|----------------|
| 검사 시점 | **PR 리뷰** (skill-review-pr Step 2.5) | **헬스체크** (skill-health-check, 주기적) |
| 검사 주체 | LLM (pr-reviewer-domain) | Grep + 정규식 (자동) |
| 검사 방식 | 의미 판단 (코드 의도 해석) | 패턴 매칭 (syntactic) |
| 강제도 | MUST/MUST NOT (도메인 비즈니스) | CRITICAL/MAJOR (보안 정합성) |
| 콘텐츠 | 도메인 비즈니스 제약 (예: PHI 변수를 logger 인자에 전달 금지) | 정형 패턴 (예: PAN 16자리 정규식) |
| 출력 | PR 인라인 코멘트 | 헬스체크 리포트 + backlog 자동 등록 |

### 3.2 겹침 영역 — PHI 식별자

healthcare 도메인에서 양쪽이 모두 PHI를 다룰 수 있다. 정책:

- **Phase 4 rules**: 도메인 *의미*를 LLM이 판단 (예: 변수명이 일반적이지만 healthcare 컨텍스트에서 PHI일 수 있음 → LLM 추론)
- **Phase 5 secrets**: 정규식으로 *정형 패턴* 검사 (예: `\d{3}-\d{2}-\d{4}` SSN 형식 하드코딩)

→ **겹침 OK**. 양쪽이 다른 시점/방식으로 같은 데이터를 검사하는 것은 다층 방어로 자연스럽다. **중복 보고 회피**는 LLM 출력 자체에 위임 (Phase 4 rules 위반은 Phase 5에서 동일 라인 SEC-07로 또 보고되더라도 두 출처 모두 표시되면 사용자가 인지 가능).

### 3.3 Phase 4 옵션 A 결정과의 정합성

- Phase 4 옵션 A로 콘텐츠 0개 → 현재 healthcare/python/phi-logging-guard.md 등 미작성
- Phase 5에서 healthcare/health/secrets-patterns.json에 PHI 식별자 정규식을 두는 것은 **다른 메커니즘** (정규식 자동 검사) → 원칙 위배 아님
- Phase 4 옵션 A는 "*Claude가 이미 아는 도메인 의미*를 LLM에 다시 가르치지 않는다"는 결정. Phase 5 정규식은 *자동화 도구가 매번 정규식을 새로 만들지 않도록* 하는 SSOT 가치 — 다른 차원

---

## 4. regex 오탐 관리 전략 (R1 — 핵심 리스크)

### 4.1 오탐 발생 케이스 매트릭스

| 케이스 | 예시 | 대응 |
|--------|------|------|
| 타입 선언 | `class Password { ... }` | `class\|interface\|type\s+\w*Password` 제외 (SEC-01 기존 적용) |
| 주석 | `// password: example` | `^\s*(//\|#\|\*)` 라인 제외 |
| 변수 선언만 (할당 없음) | `let password: string` | 정규식에 `=\s*['"]` 강제 — 할당 + 리터럴 시만 매칭 |
| 환경변수 참조 | `process.env.API_KEY`, `os.environ['SECRET']` | `\$\{?process\.env\|os\.environ\|System\.getenv` 제외 |
| 테스트 파일 | `__tests__/`, `*.spec.ts`, `*test*.py` | 파일 경로 패턴 자체 제외 |
| 도큐먼트 예시 | `docs/`, `*.md` 코드 블록 | 검사 대상에서 `docs/`, `*.md` 제외 |
| 마이그레이션 더미 | `migrations/seed.sql` 데모 데이터 | `migrations/`, `seed/` 제외 |
| 도메인 단어 (false syntax) | "passcode", "pasta" 같은 부분 매칭 | `\b` 단어 경계 강제 |

### 4.2 secrets-patterns.json 패턴별 메타데이터

각 패턴에 `excludeFiles`, `excludeContexts` 필드를 두어 SSOT로 관리.

```json
{
  "common": {
    "hardcoded": [
      {
        "id": "SEC-S01",
        "pattern": "(?i)(api[_-]?key|apikey)\\s*[:=]\\s*['\"][^'\"]{16,}['\"]",
        "severity": "CRITICAL",
        "description": "API 키 하드코딩",
        "excludeFiles": ["**/test/**", "**/*.test.*", "**/*.spec.*", "**/__tests__/**", "docs/**", "**/*.md"],
        "excludeContexts": ["env_var_reference", "type_declaration", "comment"]
      }
    ]
  }
}
```

`excludeContexts` 처리는 SKILL.md에서 정의 (모든 패턴 공통):
- `env_var_reference`: `process.env.\w+`, `os.environ\[`, `System.getenv\(`
- `type_declaration`: `class|interface|type` 키워드 직후 단어
- `comment`: 라인 시작 `//`, `#`, `/*`, ` * `

### 4.3 도메인별 패턴 정확도 등급

각 도메인 패턴에 `confidence` 필드 추가:
- `high` — 명확한 정규식 (예: PAN 16자리는 Luhn 체크섬 검증 가능)
- `medium` — 부분 매칭 (예: MRN은 형식이 기관마다 다름)
- `low` — 키워드 휴리스틱 (예: 변수명에 "patient_ssn" 포함)

→ 옵션 결정 시 `high`만 우선 포함, `medium/low`는 v2.1+로 이관하는 안 가능.

---

## 5. 가중치 재배분 정책 (H006 + D0)

### 5.1 alpha.3 → alpha.4 가중치 전이

**선결 (D0 해소)**: 도메인 _category.json 4개에 hook-safety 명시.

**Phase 5 신규**: secrets는 별도 카테고리가 아닌 **security 내부 항목 확장**으로 처리 (상위 계획 §75~85 §3 권장안).

→ **카테고리 가중치 외부 재배분 불필요**. 내부적으로 SEC-01~07을 security가 흡수.

### 5.2 _base 가중치 (변경 없음)

```json
{
  "doc-sync": 32,
  "state-integrity": 23,
  "security": 23,
  "agent-config": 12,
  "hook-safety": 10
}
```

이것이 alpha.3 현 상태. Phase 5에서 _base 가중치는 변경하지 않는다. 도메인은 §5.3.

### 5.3 도메인별 가중치 (Phase 5에서 정정 + 명시)

각 도메인의 도메인 특화 카테고리(compliance/inventory-consistency/tenant-isolation/phi-protection)는 유지하되, hook-safety 10을 명시 추가하고 다른 카테고리에서 -10 흡수.

| 도메인 | 변경 전 dictionary 합 (정규화 후 실제) | 변경 후 명시 합 (실제 = 100) |
|--------|--------------|-----------|
| fintech | doc-sync 20, state-integrity 15, security 15, agent-config 10, compliance 40 + (auto)hook-safety 10 = 110 → ~9.1% 정규화 | **명시 합 100**: doc-sync 18, state-integrity 14, security 14, agent-config 9, compliance 35, hook-safety 10 |
| ecommerce | doc-sync 25, state-integrity 20, security 20, agent-config 10, inventory-consistency 25 → 110 정규화 | **명시 합 100**: doc-sync 23, state-integrity 18, security 18, agent-config 9, inventory-consistency 22, hook-safety 10 |
| saas | doc-sync 20, state-integrity 15, security 15, agent-config 10, tenant-isolation 40 → 110 정규화 | **명시 합 100**: doc-sync 18, state-integrity 14, security 14, agent-config 9, tenant-isolation 35, hook-safety 10 |
| healthcare | doc-sync 15, state-integrity 15, security 15, agent-config 10, phi-protection 45 → 110 정규화 | **명시 합 100**: doc-sync 14, state-integrity 14, security 14, agent-config 9, phi-protection 39, hook-safety 10 |

**비례 감소 식**: 각 카테고리 × (100 / 110) → 정규화 후 정수 반올림. 합 100 일관 검증.

> **D2 결정**: 이 표는 정규화로 보정되던 실제 비율을 명시화한 것이라 **사용자 점수 영향 0** (이미 적용 중인 비율을 가시화). 부채 해소 정정 + 사용자 점수 안정성 동시 달성.

### 5.4 security-migration.md 매핑표 핵심 내용

- alpha.2 ~ alpha.3: 도메인 점수가 정규화로 ~9% 보정되고 있었음 (잠재 결함)
- alpha.4 (Phase 5): 명시 가중치로 동일 비율 유지 → 사용자 점수 영향 0
- alpha.4 신규: SEC-05~07 추가 → security 카테고리 내부 항목 늘어남. CRITICAL FAIL 발생 시 failCap 40 적용은 동일.

---

## 6. secrets-patterns.json 스키마 표준 (D3)

```json
{
  "$schema": "../../../schemas/secrets-patterns.schema.json",
  "version": "1.0.0",
  "common": {
    "hardcoded": [ /* SEC-S01~S03: 도메인 무관 시크릿 */ ],
    "runtime": [ /* SEC-S04~Sn: 로깅 노출 (기존 SEC-01 12패턴 외부화) */ ]
  },
  "domain": {
    "patterns": [ /* SEC-S{xx}: 도메인 특화 (PAN, PHI 등) */ ]
  }
}
```

- `common`은 모든 도메인에 적용
- `domain`은 해당 도메인 디렉토리(`{domain}/health/secrets-patterns.json`)에서만 정의
- `common.hardcoded` ↔ SEC-05, `common.runtime` ↔ SEC-01 (외부화), `domain.patterns` ↔ SEC-07

> 스키마 파일(`secrets-patterns.schema.json`) 작성은 향후 skill-validate 확장으로 이관. Phase 5 MVP에서는 SKILL.md에 형식만 정의.

---

## 7. TFT 5인 분석

### 7.1 Architect

- **결론**: §0~6 결정 모두 안전. 단 가중치 정정(§5)이 release notes에서 가시되어야 사용자가 의도된 변경임을 인지 가능.
- **결정**: secrets는 별도 카테고리 분리하지 않고 security 내부 항목 확장 (상위 계획 일치). 카테고리 폭증 회피.
- **기술 부채**: secrets-patterns.schema.json은 차후 Phase로 이관. MVP에서는 SKILL.md 형식 명세만.

### 7.2 Security Lead

- **공통 패턴 우선순위 (high confidence만)**:
  - `api-key`/`apikey` 할당 + 16자 이상 (SEC-S01)
  - `secret`/`private-key` 할당 + 16자 이상 (SEC-S02)
  - AWS Access Key (`AKIA[0-9A-Z]{16}`) (SEC-S03)
  - GitHub PAT (`ghp_[A-Za-z0-9]{36}`) (SEC-S04)
  - Slack Bot Token (`xox[bp]-[\w-]+`) (SEC-S05)
- **password 관련**: SEC-S06으로 분리. 4자 이상 + 따옴표 필수. **medium confidence**(테스트 자격 등 오탐 빈번) — 옵션 B/C 시만 포함.
- **fintech 패턴**: PAN(Luhn 검증 가능 16자리), CVV(3~4자리만으로는 false positive 과다 → 보류 권장), 오픈뱅킹 토큰
- **healthcare 패턴**: SSN (`\d{3}-\d{2}-\d{4}`), MRN(기관별 형식 다양 → low confidence), DEA Number
- **ecommerce 패턴**: 한국 주민등록번호(`\d{6}-\d{7}`), 사업자번호(`\d{3}-\d{2}-\d{5}`)
- **saas 패턴**: 보류 (테넌트 API 키는 형식이 다양 → 낮은 정확도)

### 7.3 DX Lead

- **FAIL 메시지**: `SEC-05: 하드코딩 시크릿 ({파일경로}:{라인}) — 패턴 SEC-S01 (api-key) — 환경변수 또는 시크릿 매니저 사용 권장`
- **autoFix 불가**: 보안은 수동 수정 필수 (상위 계획 일치)
- **--quick 모드 동작**: CRITICAL만 — SEC-05/SEC-06/SEC-07 모두 CRITICAL이라 모두 실행. SEC-03/04는 MAJOR라 SKIP.

### 7.4 Product Lead

- **범위 검증**: AST 분석/MCP 리스크/외부 도구 연동 모두 제외 — 유지
- **옵션 결정 위임**: 도메인별 패턴 콘텐츠 범위는 사용자 결정. §10 옵션 A/B/C 비교 제공
- **마이그레이션 부채 해소**: D0 해결로 alpha.2의 잠재 결함이 alpha.4에서 가시화됨 → release notes에 명시 필수

### 7.5 Domain Lead

- **도메인별 패턴 파일 위치**: `{domain}/health/secrets-patterns.json` (상위 계획 일치)
- **general 도메인**: common만 적용. 도메인별 secrets-patterns.json 부재로 SEC-07은 SKIP
- **도메인 추가 시 절차**: 새 도메인 디렉토리 생성 시 secrets-patterns.json 부재해도 동작 (옵션). 작성 가이드는 SKILL.md / domains/_base/health/README.md 참조

---

## 8. 옵션 비교 (사용자 결정)

### 옵션 A — 메커니즘 + common 패턴 (5개 high confidence)

- Step 1: 가중치 부채 해소 + secrets-patterns.json 스키마 + `_base/health/secrets-patterns.json` (common.hardcoded SEC-S01~S05) + common.runtime (SEC-01 외부화 12패턴)
- Step 2: skill-health-check SEC-05/SEC-06 추가 + SEC-01 외부화 (SEC-07은 도메인 콘텐츠 부재 시 SKIP)
- Step 3: security-migration.md (가중치 정정 + alpha.2 정규화 부채 설명)
- Step 4: CHANGELOG + VERSION → alpha.4
- **장점**: 모든 프로젝트에 즉시 가치 (시크릿 하드코딩 검사 보편적 효용). 도메인별 false positive 우려 회피
- **단점**: fintech/healthcare 사용자가 PAN/PHI 패턴 별도 작성 필요

### 옵션 B — 옵션 A + 도메인별 high confidence 패턴

- Step 1~3: 옵션 A와 동일
- Step 2 확장: fintech (PAN Luhn, 오픈뱅킹 토큰) + healthcare (SSN) + ecommerce (한국 주민/사업자) 추가
- saas 보류 (확정 패턴 부재)
- **장점**: 도메인 사용자에게 즉시 가치
- **단점**: 도메인 패턴 검증 부담, false positive 발생 시 신뢰도 손상

> **PR #36 H001 보정 (2026-04-28)**: SEC-01 외부화 12 패턴(`common.runtime` SEC-S06~S17)은 키워드 단독 매칭 + 정보성 로그 메시지 false positive 가능성 → v1.x SEC-01 회귀 보존을 위해 **`medium` confidence 허용**으로 옵션 B 재정의. 신규 추가 패턴(`common.hardcoded` SEC-S01~S05 + 도메인 패턴)은 `high`만 유지. README/JSON/plan.md 정합 갱신.

### 옵션 C — 전체 (상위 계획서 그대로)

- 옵션 B + medium/low confidence 패턴 + 도메인 4개 모두 포함
- **장점**: 계획 충실
- **단점**: false positive 위험 가장 큼. Phase 4와 동일한 "Claude가 이미 아는 것" 함정 가능 (예: medium 패턴은 LLM 판단이 더 정확할 수 있음)

### 권장

**옵션 B** (Phase 4와 다른 결론).

**근거**:
1. Phase 4 rules는 "도메인 의미"라 Claude 지식과 중복 → 옵션 A 합리
2. Phase 5 secrets는 "정규식 자동화"라 SSOT 가치 명확 → 콘텐츠 포함 합리
3. high confidence 패턴(PAN Luhn, SSN)은 false positive 거의 없음 — Phase 4 정규식 우려와 다른 차원
4. medium/low는 옵션 C로 미루어 안전마진 확보

---

## 9. 실패/경계값 시나리오

| # | 시나리오 | 기대 동작 |
|---|---------|---------|
| 1 | secrets-patterns.json 부재 (common 또는 도메인) | 해당 SEC-* 항목 SKIP, 카테고리 점수에 영향 없음 |
| 2 | secrets-patterns.json JSON 파싱 실패 | ERROR 보고, security 카테고리 부분 SKIP, 헬스체크 전체 중단 X |
| 3 | 정규식 컴파일 실패 (잘못된 패턴) | 해당 패턴만 SKIP + WARN, 다른 패턴 정상 실행 |
| 4 | excludeFiles 글롭 미적용 (구버전 도구) | 폴백: 단순 prefix 매칭 |
| 5 | techStack.backend = none | 파일 패턴 부재 → 전 SEC SKIP (기존 SEC-* 정책과 일관) |
| 6 | 도메인 _category.json에 hook-safety 없는 채 alpha.4 적용 | Step 1에서 일괄 정정. 미정정 도메인은 _base hook-safety 그대로 자동 추가됨 (현재 정규화 동작 유지) |
| 7 | 새 도메인 추가 시 secrets-patterns.json 누락 | SEC-07 SKIP. SKILL.md에 작성 가이드 안내 |
| 8 | autoFix 호출 (ban) | 자동 보안 수정 금지 — 사용자 안내만 |
| 9 | SEC-01의 12패턴 외부화 후 결과 회귀 (alpha.3 vs alpha.4 동일성) | 외부화는 동작 보존 — SEC-01 결과가 동일해야 함 (회귀 테스트 필수) |
| 10 | --quick 모드에서 secrets 검사 | CRITICAL만 → SEC-05/SEC-06/SEC-07 실행, 기존 SEC-01도 CRITICAL이라 실행 |

---

## 10. 리스크 및 대응

| ID | 리스크 | 확률 | 영향 | 대응 | 감지 스텝 |
|----|--------|------|------|------|----------|
| **R1** | regex 오탐 → 사용자 신뢰도 손상 | 중 | 높음 | high confidence만 우선 (옵션 B), excludeFiles + excludeContexts 메타 + 검증 패턴 회귀 테스트 | Step 2 |
| **R2** | hook-safety 가중치 정정으로 점수 변화 | 낮 | 낮 | §5.3 명시 합 = 정규화 후 비율 유지 → 점수 영향 0. release notes 명시 | Step 1, Step 4 |
| **R3** | SEC-01 외부화 시 동작 회귀 | 중 | 중 | 12패턴 평문 ↔ JSON 1:1 검증 + 회귀 테스트 fixture | Step 2 |
| **R4** | 도메인별 패턴 정확도 부족 → false positive | 높 | 중 | high confidence만 채택 (옵션 B), `confidence` 필드로 분류 | Step 2 |
| **R5** | secrets-patterns.json 스키마 부재 → 사용자가 잘못 작성 | 중 | 낮 | SKILL.md 형식 명세 + 예시 1개 (도메인 부재 placeholder) | Step 1 |
| **R6** | Phase 4 rules와 중복 보고 | 낮 | 낮 | 다층 방어 OK 정책 (§3.2). 사용자 출처 표기로 분별 가능 | Step 2 |
| **R7** | autoFix 시도로 보안 wound | 낮 | 높음 | 모든 SEC-* autoFix 명시 금지 (기존 정책 유지) | Step 2 |
| **R8** | --quick 모드 검사 시간 증가 | 낮 | 낮 | secrets 패턴 수 제한 (high confidence ~10개) + Grep 단일 호출 패턴 | Step 2 |
| **R9** | docs/, *.md 내 코드 블록 false positive | 중 | 낮 | excludeFiles 기본값에 docs/, *.md 포함 | Step 1 |

---

## 11. Step 분리 안 (옵션 B 가정)

| Step | 제목 | 예상 라인 |
|------|------|----------|
| 0 | TFT 설계 (본 문서) | — |
| 1 | secrets-patterns.json 스키마 + common 패턴 + **hook-safety 가중치 부채 해소** (D0) | ~300 |
| 2 | skill-health-check 확장 (SEC-01 외부화 + SEC-05/06/07 추가) | ~250 |
| 3 | 도메인별 패턴 (fintech PAN/오픈뱅킹, healthcare SSN, ecommerce 한국 주민/사업자) — high confidence만 | ~250 |
| 4 | security-migration.md + CHANGELOG + VERSION → alpha.4 | ~150 |

옵션 A 시: Step 3 제거 → 4 → 3.
옵션 C 시: Step 3에 medium/low 패턴 추가 + saas 포함.

---

## 12. Step 1 착수 Go/No-Go 체크

- [x] hook-safety 가중치 부채 진단 + 해결 정책 확정 (D0)
- [x] SEC ID 체계 통합 (D1)
- [x] Phase 4 rules와 경계 매트릭스 (H004)
- [x] regex 오탐 관리 전략 + excludeContexts SSOT (R1)
- [x] 가중치 정정 표 (§5.3) — 점수 영향 0 검증
- [x] secrets-patterns.json 스키마 표준 (D3)
- [x] TFT 5인 분석 완료
- [x] 실패 시나리오 10건 + 리스크 9건
- [x] 옵션 A/B/C 비교 제공
- [ ] 사용자 옵션 결정 (A/B/C 중 택일)
- [ ] phase-5-plan.md 작성 (옵션 결정 후)
- [ ] 사용자 최종 승인

**결론**: 사용자 옵션 결정 단계로 진행. 권장은 옵션 B(메커니즘 + common + high confidence 도메인 패턴).
