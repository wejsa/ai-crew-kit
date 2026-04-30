# Phase 5 후속 트랙 A: 테스트 자동화 구현 계획서

> **상위**: [phase-5-plan.md](./phase-5-plan.md) §v2.1+ 후속 작업 9번(회귀 fixture 자동화) + [security-migration.md](./security-migration.md) §9
> **채택 사유**: v2.0.0 단일 GA 전략에서 Phase 5 산출물의 회귀 보존 책임이 alpha.4 ↔ GA 누적이라 작성자 로컬 fixture(60+건)를 CI로 끌어올려야 GA 안전성 확보. v2.1+ 후속 → **GA 전 트랙 격상**.
> **브랜치**: `feature/phase-5-tests-step-*` (v2-develop 분기)
> **버전 영향**: 없음 (alpha.4 태그 미생성 + 단일 GA 전략 — 인터널 트랙)

---

## 🔄 진행 상황 (다른 세션에서 재개 시 확인)

| Step | 상태 | 비고 |
|------|------|------|
| 0 — 설계 (본 문서) | ✅ 완료 | |
| 1 — secrets-patterns 스키마 + workflow 골격 + plan | ⏳ 다음 | |
| 2 — fixture 테스트 60+건 (Python) | ⏳ 대기 | Step 1 의존 |
| 3 — cross-ref + `_category` 가중치 검증 + 보류 9번 → ✅ | ⏳ 대기 | Step 1, 2 의존 |

---

## 요구사항 요약

Phase 5에서 작성자 로컬에 머문 fixture를 CI로 끌어올린다.

| 영역 | 현재 | GA 전 목표 |
|------|------|------------|
| `secrets-patterns.json` 스키마 검증 | 없음 (Phase 5 D7 — 차후 Phase 이관) | **격상** — `secrets-patterns.schema.json` + CI |
| 정규식/체크섬 fixture | PR #37/#38/#39 작성자 로컬 60+건 | tests/secrets/ + CI |
| 도메인 cross-ref 무결성 | PR 리뷰 시 수동 검증 | scripts/validate-domain-crossref.py + CI |
| `_category.json` 가중치 합 100 | health-check 자체 정규화 (PR #35로 명시화) | scripts/validate-category-weights.py + CI |

---

## 🔒 핵심 결정

| ID | 결정 | 영향 |
|----|------|------|
| **D1** | `secrets-patterns.schema.json` 작성 (Phase 5 D7 차후 Phase 이관 → GA 전 격상) | Step 1 |
| **D2** | 검증 도구는 Python (jsonschema + re) — Phase 5 fixture가 Python 기반이라 일관 | Step 1, 2 |
| **D3** | CI workflow 분리 — `secrets-tests.yml` (hook-tests/schema-validation과 별도 동시 실행). 향후 트랙 B/C 추가 워크플로우 일관 | Step 1 |
| **D4** | fixture 카테고리 4분류 — 양성/음성/체크섬/excludeContexts | Step 2 |
| **D5** | cross-ref는 description 자연어에서 `domains/.../...` 정규식 추출 → 파일 존재 검증 (CRITICAL — drift 시 FAIL) | Step 3 |
| **D6** | `_category.json` 검증은 5 파일(_base + 4 도메인) 모두 명시 합 100 강제. 정규화 폴백은 health-check 자체에 두되 CI는 명시 합 강제 | Step 3 |
| **D7** | 라이센스/배포 영향 없음 — 인터널 검증 도구 | 모두 |

---

## 보안/하위호환 영향

| 항목 | 영향 |
|------|------|
| `_base/health/secrets-patterns.json` 콘텐츠 | 변경 없음 — 검증만 추가 |
| 기존 SEC-* 동작 | 변경 없음 — 회귀 보호 추가 |
| `skill-health-check` 자체 | 변경 없음 |
| CI 시간 | secrets-tests workflow ~30초 추가 (Phase 1 hook-tests ~1분과 비교 가능) |
| 로컬 dev 영향 | 없음 (CI에서만 실행) |

---

## 스텝 분리 (3 PR)

| Step | 제목 | 예상 라인 | 주요 파일 | 의존 |
|------|------|----------|---------|------|
| 1 | secrets-patterns 스키마 + workflow + plan | ~250 | `schemas/secrets-patterns.schema.json`, `scripts/validate-secrets-patterns.sh`, `.github/workflows/secrets-tests.yml`, `docs/v2/phase-5-tests-plan.md` | — |
| 2 | fixture 테스트 60+건 (Python) | ~300 | `tests/secrets/` | Step 1 |
| 3 | cross-ref + `_category` 가중치 + 보류 9번 → ✅ | ~100 | `scripts/validate-domain-crossref.py`, `scripts/validate-category-weights.py` + plan/migration 갱신 | Step 1, 2 |

라인 한도 500 — 모든 스텝 안전.

---

## 스텝별 상세

### Step 1: 스키마 + 워크플로우 골격 (PR 1)

**파일**:

- `.claude/schemas/secrets-patterns.schema.json` (신규, ~80줄):
  - JSON Schema Draft 7
  - top-level: `version` (string), `description` (string), `common`(`hardcoded` + `runtime` arrays) 또는 `domain`(`patterns` array)
  - entry: `id` (`^SEC-S\d{2}$`), `name`, `pattern`, `severity` enum(`CRITICAL|MAJOR|MINOR`), `confidence` enum(`high|medium|low`), `description`, `excludeFiles` array, `excludeContexts` enum array(`env_var_reference|type_declaration|comment`)
  - `_base`만 `common` 보유, 도메인은 `domain` 보유 (`oneOf`로 강제)

- `scripts/validate-secrets-patterns.sh` (신규, ~30줄):
  - 4 파일(`_base` + fintech/healthcare/ecommerce)에 대해 jsonschema 검증 (saas는 v2.0 패턴 부재로 자연 제외)
  - 정규식 컴파일 가능성 검증 (Python `re.compile`)
  - 실패 시 비-0 exit code

- `.github/workflows/secrets-tests.yml` (신규, ~40줄):
  - trigger: push to v2-develop / pull_request to v2-develop
  - jobs: `validate-secrets-patterns`
  - Ubuntu runner + Python 3.x + `pip install jsonschema`

- `docs/v2/phase-5-tests-plan.md` (본 문서, ~120줄)

**검증** (Step 1 로컬 실행 결과):
- 4 파일 모두 schema 통과 ✅
- 정규식 컴파일 4 파일 모두 성공 ✅
- Negative test 8건 모두 거부 확인 ✅: severity=BAD / id=INVALID / confidence=ultra / excludeContexts=bad_enum / common+domain 동시 / 필수 필드 누락 / version 비-semver / additional property

### Step 2: fixture 테스트 60+건 (PR 2)

**파일**:
- `tests/secrets/conftest.py` — 공통 fixture loader (3 도메인 + _base patterns)
- `tests/secrets/test_common_runtime.py` — SEC-S06~S17 12 키워드 ↔ JSON 매핑 검증 + alpha.3 회귀 fixture (Phase 5 PR #37의 23건 모태)
- `tests/secrets/test_common_hardcoded.py` — SEC-S01~S05 양성 + excludeContexts 음성
- `tests/secrets/test_fintech_pan.py` — IIN [3-6] + Luhn 통과/실패
- `tests/secrets/test_healthcare_ssn.py` — SSA invalid 그룹 lookahead
- `tests/secrets/test_ecommerce_kr.py` — 주민등록 + 사업자 체크섬 양성/음성
- workflow에 `tests/secrets/` pytest job 추가

**검증**:
- 60+ 케이스 PASS
- 의도적 회귀 (정규식 변경) 시 FAIL 발생 확인

### Step 3: cross-ref + `_category` + 보류 9번 갱신 (PR 3)

**파일**:
- `scripts/validate-domain-crossref.py` — description에서 `domains/[a-z_]+/[a-z_]+(/[a-z_-]+)*\.md` 정규식 추출 → `os.path.exists` 검증 (4 patterns 파일 대상)
- `scripts/validate-category-weights.py` — 5 `_category.json` 파일 (`_base` + 4 도메인) dictionary 합 100 강제 (additionalCategories 형태 A는 별도 처리)
- workflow에 추가 jobs
- `docs/v2/phase-5-plan.md` v2.1+ 보류 9번 → ✅ 갱신
- `docs/v2/security-migration.md` §9 보류 9번 → ✅ 갱신
- `.claude/domains/_base/health/README.md` 보류 9번 → ✅ 갱신

**검증**:
- 4 patterns의 cross-ref 경로 모두 실재
- 5 `_category.json` (`_base` + 4 도메인) 가중치 합 모두 100 (PR #35 명시화 결과 검증)
- 의도적 깨진 cross-ref 1건 → FAIL 확인 (테스트 시 일시 적용 후 폐기)

---

## 위험 및 대응

| ID | 리스크 | 확률 | 영향 | 대응 | 감지 스텝 |
|----|--------|------|------|------|-----------|
| **R1** | jsonschema 라이브러리 CI 환경 미설치 | 낮 | 중 | workflow에 `pip install jsonschema` 명시 | Step 1 |
| **R2** | Python re ↔ JS regex 호환 차이 | 중 | 낮 | Python re 우선 + JS 호환 케이스만 fixture에 추가 | Step 2 |
| **R3** | description 자연어 cross-ref 정규식 false negative | 중 | 낮 | 정규식 단순화 + WARN 보고로 운영 검토 (CRITICAL FAIL은 4 patterns 파일 description의 명시 경로만) | Step 3 |
| **R4** | `_category.json` 가중치 합 검증 ↔ 정규화 폴백 충돌 | 낮 | 낮 | PR #35 후 도메인 4개 모두 명시 합 100이라 충돌 없음. 검증은 명시 합 강제 | Step 3 |
| **R5** | Phase 6 진입 후 Step 2/3 지연 시 회귀 갭 | 중 | 중 | Step 1 머지로 schema 보호 즉시 적용. fixture는 후속이라도 schema가 1차 방어 | 모두 |
| **R6** | secrets-patterns.json 변경 PR이 본 트랙 머지 전 발생 | 낮 | 중 | 본 트랙 우선 머지 (Phase 6 착수 전) | Step 1 |

---

## 진행 방식 권장

1. Step 1 머지 → schema 보호 즉시 활성화
2. Step 2 머지 → fixture 회귀 보호
3. Step 3 머지 → 도메인 무결성 + 보류 9번 종료
4. 이후 Phase 6 착수 (Phase 6 plan에 "각 산출물 회귀 테스트 자동화"를 D0급 결정으로 사전 확정)

---

## 참고

- 상위 plan: [phase-5-plan.md](./phase-5-plan.md)
- 마이그레이션 가이드: [security-migration.md](./security-migration.md)
- 패턴 라이브러리 SSOT: [`_base/health/README.md`](../../.claude/domains/_base/health/README.md)
- v2 GA 전략 변경 (단일 GA): 사용자 합의 (2026-04-30)
