# `_base/health/` — Health Check 카테고리 + 시크릿 패턴 라이브러리

> Phase 1 (alpha.2) — `_category.json` 도입 (카테고리 가중치 SSOT)
> Phase 5 (alpha.4+) — `secrets-patterns.json` 도입 (민감정보 패턴 SSOT)

본 디렉토리는 **모든 도메인이 공통으로 적용받는** 헬스체크 정의를 담는다. 도메인별 오버라이드는 `domains/{domain}/health/` 하위에 같은 이름 파일로 정의한다.

## 파일 구성

| 파일 | 역할 |
|------|------|
| `_category.json` | 카테고리 정의 + 가중치 + failCap (Phase 1) |
| `secrets-patterns.json` | 도메인 무관 시크릿/민감정보 정규식 패턴 (Phase 5) |

## `secrets-patterns.json` 개요

`skill-health-check`이 SEC-01 / SEC-05 검사 시 자동 로드하는 **공통 패턴 라이브러리**. 도메인 무관 시크릿(API 키, AWS 자격, 클라우드 토큰 등)과 민감정보 로깅 패턴을 정의한다.

### 검사 항목 매핑

| 검사 항목 | 로드하는 섹션 | 위반 시 |
|----------|--------------|---------|
| **SEC-01** (민감정보 로깅) | `common.runtime` | CRITICAL FAIL |
| **SEC-05** (하드코딩 시크릿) | `common.hardcoded` | CRITICAL FAIL |
| **SEC-07** (도메인별 민감 데이터) | `{domain}/health/secrets-patterns.json` `domain.patterns` | CRITICAL FAIL |

### 스키마 표준

```json
{
  "version": "1.0.0",
  "common": {
    "hardcoded": [ /* SEC-05 매칭 — 도메인 무관 시크릿 정적 노출 */ ],
    "runtime": [ /* SEC-01 매칭 — 도메인 무관 로깅 누설 */ ]
  }
}
```

도메인별 파일은 `domain.patterns` 섹션만 두고 `common`은 두지 않는다 (D3).

### 패턴 entry 필드

| 필드 | 필수 | 타입 | 설명 |
|------|:---:|------|------|
| `id` | ✅ | string | `SEC-S{nn}` 형식. 외부 패턴 ID. SKILL.md SEC-01/05/07이 매칭 시 출처 표기에 사용 |
| `name` | ✅ | string | 사람이 읽는 패턴 이름 |
| `pattern` | ✅ | string | JavaScript 호환 정규식. JSON 이스케이프 (`\\\\` → `\\`). Python `re` 모듈도 호환 권장 |
| `severity` | ✅ | enum | `CRITICAL` / `MAJOR` / `MINOR` |
| `confidence` | ✅ | enum | `high` / `medium` / `low` — **v2.0 MVP는 `high`만 포함** |
| `description` | ✅ | string | 위반 시 사용자에게 표시할 한글 설명 |
| `excludeFiles` | 권장 | string[] | 글롭 패턴. 매칭 파일 검사 제외 |
| `excludeContexts` | 권장 | enum[] | `env_var_reference` / `type_declaration` / `comment` — `skill-health-check` SKILL.md에 처리 절차 정의 |

## confidence 등급 가이드

각 패턴은 false positive 위험에 따라 `confidence`를 부여한다.

| 등급 | 정의 | v2.0 채택 | 예시 |
|------|------|:--------:|------|
| `high` | 정규식이 false positive 거의 없음. 형식이 명확하거나 체크섬 검증 가능. | ✅ | AWS Access Key (`AKIA + 16자`), GitHub PAT (`ghp_ + 36자`), SSN (`\d{3}-\d{2}-\d{4}`), PAN Luhn 검증 |
| `medium` | 부분 매칭. 검사기 휴리스틱으로 한정적 신뢰. | ❌ (v2.1+) | CVV (3~4자리만으론 false positive), MRN (기관별 형식 다양) |
| `low` | 변수명 키워드 단독 매칭. 사용자 컨텍스트 의존. | ❌ (v2.1+) | 변수에 "passcode" 포함 등 |

> **v2.0 MVP는 `high` confidence만 포함한다 (옵션 B 채택, TFT §11).**
> medium/low는 실 사용 데이터 + 사용자 피드백 후 v2.1+에서 검토.

## `excludeFiles` 기본 권장

새 패턴 작성 시 다음 디렉토리/파일은 기본적으로 제외하라.

| 패턴 | 사유 |
|------|------|
| `**/test/**`, `**/*.test.*`, `**/*.spec.*`, `**/__tests__/**` | 테스트 더미 자격 빈번 |
| `docs/**`, `**/*.md` | 문서 예시 코드 |
| `**/migrations/**`, `**/seed/**` | 시드 / 마이그레이션 더미 데이터 |

## `excludeContexts` enum 정의

`skill-health-check` SKILL.md에서 다음 정규식으로 처리한다 (SSOT).

| enum | 정규식 | 매칭 시 검사 제외 |
|------|--------|-----|
| `env_var_reference` | `process\.env\.\w+`, `os\.environ\[`, `System\.getenv\(` | 환경변수 참조 (실제 시크릿 아님) |
| `type_declaration` | `class\|interface\|type` 키워드 직후 단어 | 타입/클래스 선언 (예: `class Password`) |
| `comment` | 라인 시작 `//`, `#`, `/*`, ` * ` | 주석 라인 |

## 새 공통 패턴 추가 절차

1. **high confidence 검증**: 정규식이 false positive를 충분히 통제하는지 확인. 불확실하면 `medium`/`low`로 분류하고 v2.1+로 이관
2. **정규식 작성**: JavaScript + Python `re` 양쪽 호환. `\b` 단어 경계 적극 활용
3. **JSON 이스케이프**: `\\b` → `\\\\b` (JSON 문자열 내 백슬래시는 두 번)
4. **테스트 fixture 작성** (Step 2 이후): 매칭 케이스 + 비매칭 케이스(excludeContexts 적용)
5. **SEC-S{nn} ID 부여**: 마지막 ID + 1
6. **PR로 v2-develop 머지**

## 새 도메인 패턴 추가 절차 (`{domain}/health/secrets-patterns.json`)

1. 디렉토리 생성: `.claude/domains/{domain}/health/`
2. `secrets-patterns.json` 작성. **`domain.patterns` 섹션만** 정의
3. `common.hardcoded` / `common.runtime`은 도메인 파일에 작성하지 않음 (`_base`만 보유)
4. high confidence 패턴만 포함 (옵션 B)

도메인 패턴 예시 (Step 3 이후 작성 예정):
- `fintech`: PAN Luhn 검증 + 한국 오픈뱅킹 토큰
- `healthcare`: 미국 SSN
- `ecommerce`: 한국 주민등록번호 / 사업자번호 (체크섬 검증)

## 금지 항목

- ❌ `medium` / `low` confidence 패턴 (v2.0 범위 외)
- ❌ autoFix 활성화 (보안은 수동 수정 필수 — D5)
- ❌ 도메인 무관 패턴을 `domain.patterns`에 작성 (`common`에 작성)
- ❌ 도메인 특화 패턴을 `_base`에 작성 (`{domain}/health/`에 작성)
- ❌ `confidence` 필드 누락
- ❌ 기존 SEC-01의 12 패턴을 인라인으로 SKILL.md에 재정의 (Step 2 이후 외부화 완료)

## 참고

- 상위 설계: [docs/v2/phase-5-security.md](../../../../docs/v2/phase-5-security.md)
- TFT 분석: [docs/v2/phase-5-tft-analysis.md](../../../../docs/v2/phase-5-tft-analysis.md)
- 구현 계획: [docs/v2/phase-5-plan.md](../../../../docs/v2/phase-5-plan.md)
- 검사 절차: [skill-health-check SKILL.md](../../../skills/skill-health-check/SKILL.md) `secrets` 카테고리 (Step 2 이후)
- Phase 4 도메인 × 언어 rules와의 경계: [docs/v2/phase-5-tft-analysis.md §3](../../../../docs/v2/phase-5-tft-analysis.md)
