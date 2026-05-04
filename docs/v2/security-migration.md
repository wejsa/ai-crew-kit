# v2.0.0-alpha.4 보안 마이그레이션 가이드

> **대상 사용자**: alpha.2 / alpha.3에서 v2.0.0-alpha.4로 업그레이드하는 프로젝트
> **상위 계획**: [phase-5-security.md](./phase-5-security.md) · TFT: [phase-5-tft-analysis.md](./phase-5-tft-analysis.md) · 구현: [phase-5-plan.md](./phase-5-plan.md)
> **선행**: PR #35 (D0 — alpha.2 hook-safety 부채 해소) · PR #36 (Step 1 — secrets 패턴 라이브러리) · PR #37 (Step 2 — SEC-01 외부화 + SEC-05/06/07) · PR #38 (Step 3 — 도메인 패턴)

본 문서는 Phase 5(AgentShield-lite) 적용 시 사용자가 알아야 할 보안 항목 변경, 점수 영향, 마이그레이션 절차, v2.1+ 후속 작업을 정리한다.

---

## 1. At a Glance

| 변경 | 사용자 영향 |
|------|-------------|
| **SEC-01 외부화** — 인라인 12 패턴 → `_base/health/secrets-patterns.json` `common.runtime` 로드 | 동작 회귀 보존 (키워드 1:1, 회귀 fixture 23건 PASS) |
| **SEC-05 신설** (CRITICAL) — 하드코딩 시크릿 (API 키 / secret / AWS / GitHub / Slack) | 신규 검사. 매칭 없으면 PASS, 위반 시 CRITICAL FAIL |
| **SEC-06 신설** (CRITICAL) — `.env` 노출 게이트 | dotenv 미사용 프로젝트는 SKIP |
| **SEC-07 신설** (CRITICAL) — 도메인별 민감 데이터 (PAN / SSN / 한국 주민·사업자) | `general` 도메인 또는 도메인 patterns 부재 시 SKIP |
| **alpha.2 hook-safety 가중치 부채 해소** (PR #35) — 도메인 `_category.json`에 명시 | **점수 영향 ≤1점** — 3 도메인(fintech/ecommerce/saas) Hamilton 라운딩으로 ≈0, healthcare phi-protection만 의도적 floor로 -0.91% ≈ ~1.0점 (§5 참조) |
| **PR #34 — 훅 스크립트 실행 권한 정정** (`6dcfdb3`) — alpha.2 PR #26 머지 시 누락된 `chmod +x`로 인해 `post-tool-use.sh` 등 5개 훅이 git index 모드 100644로 박힘 | alpha.2/alpha.3 PostToolUse 훅이 사실상 미동작(비블로킹 stderr라 사용자 가시 변화 없음)이었으나 alpha.4부터 의도 동작 활성화. 보안 감사 시 인지 필요 — lockedAt heartbeat / 3단계 무한 루프 방어 / hook-disabled.flag 카운터 모두 alpha.4에서 처음 작동 |
| **`python-fastapi` / `python-django` 검사 대상 추가** | 기존 누락 결함 동시 해소 |

**총 사용자 점수 영향**: 신규 위반 발견 시 외에는 ≤1점. SEC-01 회귀 보존 + 신규 SEC-* 추가는 점수 영향 0이며, alpha.2 hook-safety 부채 해소만 healthcare phi-protection에서 -0.91% ≈ ~1.0점 (의도적 floor — PR #35 §점수 영향 분석). 다른 3 도메인은 Hamilton 라운딩으로 ≈0.

---

## 2. SEC-01 외부화 — 회귀 보존 정책

### 변경 사실

`skill-health-check`의 SEC-01(민감정보 로깅 금지)은 alpha.3까지 SKILL.md 본문에 12 패턴이 인라인이었다. alpha.4부터 `_base/health/secrets-patterns.json`의 `common.runtime` 섹션(SEC-S06~S17)에서 동적 로드한다.

### 1:1 매핑 보존

| 평문 키워드 (alpha.3 인라인) | 외부 패턴 ID (alpha.4 JSON) |
|------------------------------|------------------------------|
| `log.*password` | SEC-S06 |
| `log.*cardNumber` | SEC-S07 |
| `log.*creditCard` | SEC-S08 |
| `log.*cvv` | SEC-S09 |
| `log.*ssn` | SEC-S10 |
| `log.*주민등록` | SEC-S11 |
| `logger.*secret` | SEC-S12 |
| `println.*password` | SEC-S13 |
| `log.*apiKey` | SEC-S14 |
| `log.*token` | SEC-S15 |
| `log.*bearer` | SEC-S16 |
| `log.*authorization` | SEC-S17 |

키워드는 1:1 동일하며 정규식은 단어 경계(`\b`) + `log/logger/println` 변형 흡수로 정밀화. **PR #37 H001 보정**으로 `confidence: medium`(예외 — v1.x 회귀 보존 한정) 채택.

### medium confidence 안내

`common.runtime` SEC-S06~S17 FAIL 시 다음 안내가 첨부된다:

> ℹ️ medium confidence — 정보성 로그 메시지(예: `logger.info("Password validation failed")`) false positive 가능. 변수 보간이 아닌 단순 키워드 등장이면 무시 가능. 정밀화는 v2.1+ 검토.

신규 추가 패턴(`common.hardcoded` SEC-S01~S05, 도메인 `domain.patterns`)은 모두 `high`이며 별도 안내 없이 FAIL 처리.

### 회귀 검증 결과

PR #37 머지 시 회귀 fixture **23건 전건 PASS** (양성 17 + excludeContexts 음성 6). alpha.3 ↔ alpha.4 매칭 결과 동일성 확인.

---

## 3. 신규 항목 SEC-05 / SEC-06 / SEC-07

### SEC-05 — 하드코딩 시크릿 (CRITICAL)

**대상 패턴** (`common.hardcoded` SEC-S01~S05, 모두 high confidence):
- API 키 / secret·private_key 변수에 16자 이상 리터럴
- AWS Access Key (`AKIA|AGPA|AROA|AIDA|ANPA` + 16자)
- GitHub Token (`ghp|gho|ghu|ghs|ghr` + 36자)
- Slack Bot/User Token (`xox[bp]-...`)

**대응**: 환경변수 또는 시크릿 매니저로 분리.

### SEC-06 — `.env` 노출 게이트 (CRITICAL)

**검사**: 다음 두 게이트 중 하나라도 위반 시 FAIL.
1. `.gitignore`에 `.env*` 또는 `.env` 또는 정확한 파일명 매칭 라인 존재
2. 검사 대상 dotenv 파일에 AWS/GitHub/Slack 명시 prefix(`AKIA…`, `ghp_…`, `xoxb-…`) 미매칭. placeholder(`<...>`, `xxx`, `your-...` 등)는 통과 처리

**SKIP 조건**: dotenv 파일 부재 시 (정상). `.env.example` / `.env.template` / `.env.sample`은 placeholder 가정으로 검사 제외.

**대응**: `.gitignore`에 `.env*` 추가 + 이미 commit된 경우 `git rm --cached` + 노출 시크릿 외부 콘솔에서 즉시 회수.

### SEC-07 — 도메인별 민감 데이터 (CRITICAL)

**대상 패턴** (`{domain}/health/secrets-patterns.json` `domain.patterns`, 모두 high):
| 도메인 | 패턴 | 정규식 | 체크섬 |
|--------|------|--------|--------|
| fintech | PAN 16자리 | `\b[3-6]\d{15}\b` (IIN 제한) | Luhn |
| healthcare | 미국 SSN | SSA invalid 그룹 lookahead 제외 | — |
| ecommerce | 한국 주민등록 | YYMMDD + 성별 [1-8] 검증 | 가중치 [2,3,4,5,6,7,8,9,2,3,4,5] |
| ecommerce | 한국 사업자 | 세무서 코드 [1-9] 시작 | 가중치 [1,3,7,1,3,7,1,3,5] |

**SKIP 조건**: `domain == general` 또는 도메인 `secrets-patterns.json` 부재.

**대응**: 컴플라이언스 표준(PCI-DSS / HIPAA Privacy Rule §164.514 / 한국 개인정보보호법 §24)에 따라 마스킹·암호화·분리 보관·환경변수 분리.

---

## 4. alpha.2 hook-safety 정규화 부채 해소

### 잠재 결함 (alpha.2 ~ alpha.3)

`_base/health/_category.json`에 hook-safety(weight 10)가 추가됐으나 도메인 4개(fintech / ecommerce / saas / healthcare)의 `_category.json`이 dictionary에 hook-safety를 명시하지 않아, 합 110이 자동 정규화되어 **모든 도메인 점수가 ~9% 보정**되고 있었다. 사용자가 인지하지 못한 채 점수가 변경됨.

### 해소 (PR #35, d0715de)

도메인 4개의 `_category.json`에 hook-safety weight 9 명시 + 정규화로 보정되던 비율을 명시화 (예: fintech doc-sync 20 → 18, compliance 40 → 35 등).

### 점수 영향

**≤1점** — 정규화로 이미 적용 중이던 비율을 명시화. fintech/ecommerce/saas 3 도메인은 Hamilton 라운딩으로 ≈0, healthcare phi-protection만 의도적 floor(40)로 -0.91% ≈ ~1.0점. 도메인별 라운딩 정책 차이는 PR #35 §점수 영향 분석 표 참조 — 모든 도메인 ±1점 이내라 등급 변동은 발생하지 않는다.

---

## 5. 점수 영향 분석

Phase 5는 **별도 카테고리 추가 없이 security 카테고리 내부 항목 확장**으로 처리됨. 따라서 카테고리 가중치 외부 재배분 불필요.

| 항목 | alpha.3 | alpha.4 | 영향 |
|------|---------|---------|------|
| security 카테고리 내부 항목 수 | SEC-01~04 (4개) | SEC-01~07 (7개) | 신규 위반 발견 시에만 FAIL 증가 |
| security 카테고리 weight | 23 (`_base`) | 23 (변경 없음) | 0 |
| failCap 40 적용 | CRITICAL FAIL 시 | 동일 | 0 |
| 도메인 가중치 합 | 100 (정규화 후) | 100 (명시) | 도메인별 라운딩 정책 차이로 fintech/ecommerce/saas ≈0, healthcare phi-protection -0.91% ≈ ~1.0점 (PR #35 §점수 영향 분석) |

**라운딩 정책 차이**: PR #35는 fintech/ecommerce/saas에 Hamilton 라운딩(잔여 0.36%/0.27%/0.36%를 base 카테고리에 분배)을 적용해 점수 영향을 ≈0으로 흡수했다. healthcare는 phi-protection을 floor(40)로 의도적으로 내림(40.91% → 40)하여 차이 0.91%를 base 카테고리(doc/state/security 14)에 +0.36 분배 — 결과적으로 healthcare phi-protection 점수만 가시적인 -0.91% 차이가 발생한다. 등급 변동은 발생하지 않는 범위이며, 모든 도메인이 ±1점 이내로 통제된다.

---

## 6. excludeFiles / excludeContexts 사용자 가이드

### 패턴 정의 위치

| 파일 | 역할 |
|------|------|
| `.claude/domains/_base/health/secrets-patterns.json` | 공통 패턴 (`common.hardcoded` + `common.runtime`) |
| `.claude/domains/{domain}/health/secrets-patterns.json` | 도메인 특화 패턴 (`domain.patterns`) |
| `.claude/domains/_base/health/README.md` | 스키마 / confidence 가이드 / excludeContexts enum 정의 (SSOT) |
| `.claude/skills/skill-health-check/SKILL.md` §security 카테고리 헤더 | excludeContexts 정규식 SSOT 구현 + 처리 절차 |

### 새 파일 패턴 제외 추가

특정 디렉토리(예: `**/seed/**`, `**/fixtures/**`)를 검사 제외하려면 해당 패턴 entry의 `excludeFiles` 배열에 글롭 추가 후 PR.

### excludeContexts enum

| enum | 차단 대상 |
|------|-----------|
| `env_var_reference` | `process.env.X` / `os.environ[X]` / `os.getenv(...)` / `System.getenv(...)` / `os.Getenv(...)` / `os.LookupEnv(...)` |
| `type_declaration` | `class\|interface\|type` 키워드 직후 단어 (예: `class Password`) |
| `comment` | 라인 시작 `//`, `#`, `/*`, ` * ` |

> **type_declaration 한계**: 라인 단위 제외이므로 `class PasswordValidator { val secret = "abc1234567890123" }` 같은 single-line 정의는 false negative. 시크릿 리터럴은 별도 라인/`const`로 분리 권장. v2.1+에서 토큰-단위 처리로 정밀화 검토.

---

## 7. autoFix 정책

**모든 SEC-* 항목 `autoFix: 불가`** (D5). 보안 관련은 수동 수정 + (필요 시) 자격 회수 절차 필수. `--fix` 모드 진입 시에도 SEC-* 항목은 사용자 안내만 표시하고 자동 수정 시도하지 않는다.

---

## 8. Phase 4 rules와의 다층 방어

SEC-07(헬스체크 시점, 정규식 자동 검사)과 Phase 4 `.claude/rules/{domain}/{language}/`(PR 리뷰 시점, LLM 의미 판단)는 다른 검사 시점·방식이다. 동일 코드 라인이 양쪽에서 보고될 수 있으며 이는 다층 방어로 정상이다.

| 축 | Phase 4 rules | Phase 5 SEC-07 |
|----|--------------|----------------|
| 검사 시점 | PR 리뷰 (`skill-review-pr`) | 헬스체크 (`skill-health-check`) |
| 검사 방식 | LLM 의미 판단 | 정규식 + 체크섬 |
| 출처 표기 | `rules/{domain}/{language}/{rule-id}.md` | `{domain}/SEC-S{nn}` |

출처 표기로 분별 가능하므로 사용자 혼란을 통제한다.

---

## 9. v2.1+ 후속 작업 (보류 항목)

옵션 B(high confidence only) 정책 일관 유지를 위해 다음 항목은 v2.0에서 보류, v2.1+에서 재검토.

| 항목 | 보류 사유 | 재검토 트리거 |
|------|-----------|---------------|
| **한국 오픈뱅킹 토큰** (H001) | `fintech/docs/open-banking.md` 점검 결과 access_token base64url(prefix 부재) + `fintech_use_num`/`bank_tran_id` 형식 명시 없음 → 정규식 추측 시 R4 위험 | 금융결제원 표준 형식 정리 후. 토큰 *로깅*은 `_base` SEC-01 SEC-S15(token)/SEC-S17(authorization) 커버 |
| **fintech CVV** | 3~4자리 정규식만으로 false positive 과다 (TFT §7.2) | 변수명·타입 컨텍스트 검출 메커니즘 도입 시. CVV *로깅*은 SEC-01 SEC-S09 커버 |
| **healthcare DEA Number** | 형식은 명확(`[A-Z]{2}\d{7}` + 체크섬)하나 v2.0 범위에서 SSN 우선 | 미국 healthcare 사용자 실증 발생 시 |
| **healthcare MRN** | 기관별 형식 다양 → low confidence | 표준화된 패턴 합의 형성 시 |
| **saas 도메인** | 확정 패턴 부재 (테넌트 API 키는 형식 다양) | 광범위한 SaaS 사용자 데이터 수집 후 |
| **medium / low confidence 패턴 일반** | 옵션 B 정책 — 신규는 high만 | 실 사용 데이터 + 사용자 피드백 후 |
| **`secrets-patterns.schema.json`** (D7) | MVP 범위 외 — SKILL.md/README 형식 명세로 대체 | skill-validate 확장 트랙 |
| **`type_declaration` 토큰-단위 처리** | M003 한계 — 라인 단위 제외로 single-line FN | 사용자 케이스 누적 후 |
| ~~**회귀 fixture 자동화** (Step 3 리뷰 O1)~~ ✅ **GA 전 격상 + 완료** | v2.0 단일 GA 전략(2026-04-30 합의)으로 GA 전 트랙 A로 격상 | 트랙 A Step 1~3 완료(PR #40/#41/#42): `tests/secrets/` 89 parametrize + 14 메타 + cross-ref + `_category` 가중치 검증 + SSOT drift 메타. `secrets-tests.yml` 워크플로우. 자세한 내용은 [phase-5-tests-plan.md](./phase-5-tests-plan.md) 참조 |

---

## 10. 문제 해결 (Troubleshooting)

### Q1. SEC-01 결과가 alpha.3과 다르게 나온다

A. 회귀 보존이 원칙. fixture 23건은 전건 PASS로 검증됨. 차이가 발견되면:
1. `_base/health/secrets-patterns.json` 파일 존재 + JSON 유효성 확인
2. 정규식 컴파일 오류 시 해당 패턴만 SKIP되며 WARN 출력 — 다른 패턴은 정상
3. 문제 지속 시 GitHub Issue로 fixture 케이스 + alpha.3/alpha.4 결과 첨부

### Q2. SEC-05/06/07이 false positive를 보고한다

A. 패턴 entry의 `excludeFiles` / `excludeContexts`로 통제 가능.
- `excludeFiles`에 해당 디렉토리 글롭 추가
- 변수가 환경변수 참조라면 `env_var_reference`가 자동 처리. Go/Python 함수형도 alpha.4부터 커버됨
- 도메인 SEC-07 false positive는 체크섬 단계에서 자동 폐기 (PAN Luhn / 한국 주민·사업자 가중치)

### Q3. SEC-07이 `general` 도메인에서 SKIP된다

A. 정상 동작. `general`은 도메인 특화 패턴 없음. fintech/healthcare/ecommerce로 도메인 전환 시 자동 활성화.

---

## 11. 참고

- 상위 설계: [phase-5-security.md](./phase-5-security.md)
- TFT 분석: [phase-5-tft-analysis.md](./phase-5-tft-analysis.md)
- 구현 계획: [phase-5-plan.md](./phase-5-plan.md)
- Phase 1 선행: [phase-1-plan.md](./phase-1-plan.md) (`_category.json` 도입)
- 패턴 라이브러리 SSOT: [`_base/health/README.md`](../../.claude/domains/_base/health/README.md)
- 검사 절차 SSOT: [`skill-health-check/SKILL.md`](../../.claude/skills/skill-health-check/SKILL.md) §security 카테고리
