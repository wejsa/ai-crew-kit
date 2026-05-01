# Phase 7 Lean Closure (옵션 A) — 구현 계획서

> **상위**: [phase-7-context.md](./phase-7-context.md) (v2.1+ 보류 항목 포함)
> **채택안**: **옵션 A — Lean Closure** (2026-05-01 합의). v1.23.0 이미 구현된 lessons-learned 메커니즘의 회귀 보호 갭만 메운다.
> **브랜치**: `feature/phase-7-step-*` (v2-develop 분기)
> **버전 영향**: 없음 (alpha.4 인터널 + 단일 GA 전략)

---

## 🔄 진행 상황 (다른 세션에서 재개 시 확인)

| Step | 상태 | 비고 |
|------|------|------|
| 0 — 옵션 결정 (재진입 시 본 문서) | ✅ 완료 | 옵션 A 채택 — Phase 6 D-MIN/D-NEED 학습 적용 |
| 1 — schema + validator + workflow job + fixtures + plan + phase-7-context 보류 헤더 | ⏳ 진행 중 | feature/phase-7-step-1 (PR #43 — 리뷰 반영 후 secrets 필터 Step 2로 이관, fixtures 추가) |
| 2 — skill-retro §5.3 **secrets 필터 통합** + impact 임계값 정량 출력 + tests/lessons/ pytest fixture (~12건) | ⏳ | Step 1 머지 후. Step 1에서 이관된 secrets 필터 책임 포함 |

---

## 진단 (옵션 결정 근거)

### ✅ 이미 구현됨 (v1.23.0, 2026-03-05)
- `.claude/state/lessons-learned.json` — skill-retro §5.3에서 저장/누적
- skill-retro `--lessons` (list/search/top) 관리 명령
- skill-plan §"과거 학습 반영" — impact=high 우선 + 최대 5건 자동 참조
- lesson 구조: `{id, taskId, category, title, description, impact, tags, appliedCount, createdAt, updatedAt}`

### 🔧 갭 (회귀 보호 미흡 — GA 안전성 영향)
1. **schema 부재** — 사용자 수동 편집 / skill-retro 수정 PR 시 회귀 검출 불가
2. **secrets 필터링 부재** — `description` 필드에 코드 스니펫 박힐 때 secrets 누출 위험
3. **impact 임계값 SSOT 부재** — high/medium/low 기준이 prose에만 존재
4. **cross-ref 검증 부재** — taskId가 completed.json 실재 검증 없음

### ⏸ v2.1+ 보류 (D-NEED 미충족)
- contextSnapshot (Task 7-1/7-2) — v1.x 사용자 요청 사례 부재. v1.32 SKILL.md 토큰 효율화로 대부분 해결
- skill-create `--from-history` (Task 7-6) — v1.x 요청 사례 부재
- 도메인별 lessons-learned 파일 분리 — 단일 파일 + tags로 충분

---

## 🔒 핵심 결정

| ID | 결정 | 영향 |
|----|------|------|
| **D1** | `lessons-learned.schema.json` (Draft 7) — v1.23 entry 구조 그대로 정의. id `^L-\d{3,}$`, category enum, impact enum, appliedCount minimum 1 | Step 1 |
| **D2** (개정) | ~~validator + skill-retro 양쪽 적용~~ → **Step 2에서만 적용** (skill-retro §5.3 통합). 근거: SEC-S01~S05 모두 `excludeContexts: ["comment"]` 보유하므로 lesson description(코멘트성 텍스트)에 정적 정규식 매칭 시 false positive 다발 (PR #43 리뷰 MAJOR). Step 2에서 skill-retro AskUserQuestion으로 사용자 판단 위임 | Step 2 |
| **D3** | impact 임계값은 schema description으로 SSOT 명시 (`>=5 → high / >=3 → medium / <3 → low`). validator는 WARN only(사용자 override 허용) | Step 1, 2 |
| **D4** (개정) | cross-ref 검증은 completed.json + backlog.json(`tasks` + `archived`) 양쪽 ID 합집합. **양쪽 모두 부재 시 SKIP / 한쪽만 부재 시 WARN(부분 검증)** (PR #43 리뷰 MINOR #1). 양쪽 존재 시에만 CRITICAL FAIL | Step 1 |
| **D5** | CI workflow 신규 X — 기존 `secrets-tests.yml`에 `validate-lessons-learned` job 추가. secrets-patterns 데이터 재사용 + 토큰 효율 | Step 1 |
| **D6** | workflowState / contextSnapshot / --from-history 등 v2.1+ 보류 — phase-7-context.md 상단에 명시 보존 | Step 1 |
| **D7** | `.claude/state/lessons-learned.json` 부재 시 validator graceful skip(exit 0) — 메타 레포 / 신규 프로젝트 호환 | Step 1 |
| **D8** (신규) | CI에서 validator 동작 증명용 **fixture 3건**(`tests/lessons/fixtures/`) — positive 1, negative 2(bad id, additionalProperties). validator `--fixture <path>` 옵션 추가. 메타 레포에서 실제 데이터 부재로 SKIP되는 상황의 회귀 보호 갭 해소 (PR #43 리뷰 CRITICAL #1) | Step 1 |
| **D9** (신규 — 후속 부채) | schema multi-version 분기는 v2.1+ contextSnapshot/`--from-history` 부활 시 한번에 도입. 현재 `metadata.schemaVersion`은 optional + validator 미사용 — SSOT 명시만 있고 메커니즘 부재. forward-compat 부채로 인지(PR #43 리뷰 MINOR #2) | v2.1+ |

---

## 보안/하위호환 영향

| 항목 | 영향 |
|------|------|
| 기존 lessons-learned.json 사용자 데이터 | 변경 없음 — schema는 기존 v1.23 구조 그대로 정의 |
| skill-retro `--lessons` 동작 | 변경 없음 (Step 1) → Step 2에서 출력에 임계값 정량 표시만 추가 |
| skill-plan 참조 동작 | 변경 없음 — impact=high 필터 그대로 |
| CI 시간 | secrets-tests.yml에 ~5초 job 추가 |
| 로컬 dev 영향 | 없음 (CI에서만 schema/secrets 검증, 런타임 거부는 Step 2 skill-retro 수정 후) |

---

## 스텝 분리 (2 PR + 회귀 자동화 D0 동시)

| Step | 제목 | 예상 라인 | 주요 파일 | 의존 |
|------|------|----------|---------|------|
| 1 | schema + validator + workflow job + plan + 보류 헤더 | ~280 | `.claude/schemas/lessons-learned.schema.json`, `scripts/validate-lessons-learned.py`, `.github/workflows/secrets-tests.yml`, `docs/v2/phase-7-plan.md`, `docs/v2/phase-7-context.md` | — |
| 2 | skill-retro §5.3 secrets 필터 통합 + impact 임계값 정량 출력 + tests/lessons/ pytest fixture (~12건) | ~270 | `.claude/skills/skill-retro/SKILL.md`, `tests/lessons/`, `docs/v2/context-migration.md` | Step 1 |

라인 한도 500 — 모든 스텝 안전.

---

## 스텝별 상세

### Step 1: schema + validator + workflow + fixtures + plan (PR 1)

**파일**:

- `.claude/schemas/lessons-learned.schema.json` (신규, 105줄):
  - `metadata`(version, updatedAt, schemaVersion?) + `lessons` array
  - lessonEntry: id `^L-\d{3,}$`, taskId, category enum(quality|performance|architecture|process|security), title 1-200자, description 0-2000자, impact enum, tags array uniqueItems, appliedCount integer ≥ 1, createdAt/updatedAt date-time, domain (선택)
  - `additionalProperties: false`로 신규 필드 통제

- `scripts/validate-lessons-learned.py` (신규, ~165줄):
  - `--fixture <path>` 옵션 (CI에서 validator 동작 증명용)
  - 기본 모드: `.claude/state/lessons-learned.json` 검증, 부재 시 graceful skip
  - jsonschema Draft 7 검증
  - taskId cross-ref: 양쪽 부재→SKIP / 양쪽 존재→CRITICAL FAIL / 한쪽만→WARN
  - impact 임계값 sanity (WARN only)
  - **secrets 필터링은 Step 2로 이관** (D2 개정)

- `tests/lessons/fixtures/` (신규):
  - `sample-valid.json` — positive (must pass)
  - `sample-invalid-id.json` — negative (id `BAD-ID` schema fail)
  - `sample-extra-property.json` — negative (additionalProperties false 위반)

- `.github/workflows/secrets-tests.yml`:
  - `validate-lessons-learned` job 추가 (5단계 검증):
    1. real lessons-learned (메타 레포 graceful skip)
    2. positive fixture (must pass)
    3. negative fixture: bad id (must fail)
    4. negative fixture: extra property (must fail)
  - `paths` 트리거에 `.claude/schemas/lessons-learned.schema.json`, `.claude/state/lessons-learned.json`, `scripts/validate-lessons-learned.py`, `tests/lessons/**` 추가

- `docs/v2/phase-7-plan.md` (본 문서)
- `docs/v2/phase-7-context.md` 상단에 v2.1+ 보류 헤더 + 옵션 A 결정 명시

**검증 (Step 1 로컬 실행)**:
- 기본 모드(메타 레포): graceful skip exit 0 ✅
- positive fixture: schema OK exit 0 ✅
- negative bad id: schema FAIL exit 1 ✅
- negative extra property: additionalProperties FAIL exit 1 ✅
- missing fixture path: clear error exit 1 ✅

### Step 2: skill-retro 통합 + secrets 필터 + 임계값 정량 출력 + pytest fixture (PR 2)

**파일**:
- `.claude/skills/skill-retro/SKILL.md`:
  - §5.3 저장 직전 `description` SEC-S01~S05 매칭 시 AskUserQuestion으로 사용자에게 알리고 거부 또는 마스킹 후 저장 옵션 제공 (D2 개정 — Step 1에서 이관)
  - --lessons list/top 출력에 `appliedCount X (권장: Y)` 정량 표시
- `tests/lessons/conftest.py` — fixture loader (schema + secrets-patterns)
- `tests/lessons/test_schema.py` — 정상/negative 5건(id 형식 / category 비-enum / impact 비-enum / appliedCount 0 / required 누락)
- `tests/lessons/test_secrets_filter.py` — SEC-S01~S05 각 1건 + clean 1건. excludeContexts 처리(comment/type_declaration) 정상 동작 검증
- `tests/lessons/test_threshold.py` — 임계값 경계 (appliedCount 2/3/4/5/6)
- `docs/v2/context-migration.md` (신규) — Phase 7 Lean Closure 사용자 가이드

**검증**:
- 12+ pytest 케이스 PASS
- 회귀 (schema 변경/임계값 변경/excludeContexts 변경) 시 FAIL 발생 확인

---

## 위험 및 대응

| ID | 리스크 | 확률 | 영향 | 대응 | 감지 스텝 |
|----|--------|------|------|------|-----------|
| **R1** | 기존 사용자 lessons-learned.json이 새 schema 위배 | 낮 | 중 | Step 1 머지 전 사용자 환경 검증 안내. v1.23 구조 그대로 정의해 깨질 가능성 매우 낮음 | Step 1 |
| **R2** (개정) | ~~secrets 필터 false positive~~ → **해소됨** — D2 개정으로 secrets 필터를 Step 2로 이관, excludeContexts 처리 + AskUserQuestion 사용자 판단 | (해소) |
| **R3** (개정) | cross-ref 검증이 archived Task 누락 시 false positive | 중 | 중 | completed.json + backlog.json `archived` 양쪽 검색. **양쪽 부재 시 SKIP / 한쪽만 부재 시 WARN(부분 검증)** (D4 개정) | Step 1 |
| **R4** | impact 임계값 변경 요구 발생 | 낮 | 낮 | schema description 한 곳만 수정. WARN only이라 동작 비파괴 | Step 2 |
| **R5** | contextSnapshot 보류 결정에 사용자 반대 | 낮 | 낮 | phase-7-context.md 상단에 v2.1+ 재진입 옵션 명시 — Phase 6 패턴 일관 | Step 1 |
| **R6** (신규) | 메타 레포 CI에서 validator가 항상 graceful skip → 회귀 보호 무용 | 중→해소 | 중 | D8 신규 — fixture 3건(`tests/lessons/fixtures/`) + `--fixture` 옵션으로 CI 동작 증명 (PR #43 리뷰 CRITICAL #1) | Step 1 |

---

## 진행 방식 권장

1. Step 1 머지 → schema + CI 보호 즉시 활성화
2. Step 2 머지 → 런타임 secrets 필터 + 임계값 정량 출력 + fixture 회귀 보호
3. Phase 7 완료 → Phase 8 (Migration & Release / GA) 진입

---

## 참고

- 상위 plan: [phase-7-context.md](./phase-7-context.md) (v2.1+ 보류 항목 포함)
- skill-retro §5.3 SSOT: [`.claude/skills/skill-retro/SKILL.md`](../../.claude/skills/skill-retro/SKILL.md)
- skill-plan 학습 참조: [`.claude/skills/skill-plan/SKILL.md`](../../.claude/skills/skill-plan/SKILL.md) §"과거 학습 반영"
- secrets-patterns 재사용: [`_base/health/secrets-patterns.json`](../../.claude/domains/_base/health/secrets-patterns.json)
- Phase 5 후속 트랙 A 패턴 참조: [phase-5-tests-plan.md](./phase-5-tests-plan.md)
- Phase 6 보류 학습 (D-MIN / D-NEED 적용 근거): [phase-6-compliance.md](./phase-6-compliance.md)
