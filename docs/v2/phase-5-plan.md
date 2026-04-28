# Phase 5: AgentShield-lite — 구현 계획서

> **상위 문서**: [phase-5-security.md](./phase-5-security.md)
> **TFT 분석**: [phase-5-tft-analysis.md](./phase-5-tft-analysis.md)
> **버전 목표**: `v2.0.0-alpha.4` (Phase 5 단독)
> **브랜치**: `feature/phase-5-security-step-*` (v2-develop 분기)
> **예상 작업량**: 6~8시간 (TFT 1.5h 완료 + 구현 4h + 검증 2h)
> **우선순위**: P1 | **의존성**: Phase 0 + Phase 1 (완료) | **난이도**: M
> **채택안**: **옵션 B (메커니즘 + common + 도메인별 high confidence)** + **B-2 (D0 부채는 선분리 PR)**. SEC-01 외부화 12 패턴(`common.runtime` SEC-S06~S17)은 v1.x 회귀 보존을 위해 `medium` 허용 (PR #36 H001 보정).

---

## 🔄 현재 진행 상황 (다른 세션에서 재개 시 확인)

| Step | 상태 | 비고 |
|------|------|------|
| 0 — TFT 설계 + 옵션 결정 | ✅ 완료 | [phase-5-tft-analysis.md](./phase-5-tft-analysis.md) — 옵션 B + B-2 채택 |
| **선** — D0 hook-safety 가중치 부채 해소 | ✅ 완료 | PR #35 머지 (d0715de) — 4개 도메인 _category.json에 hook-safety 명시 + Hamilton 일관 회복 (M001 반영) |
| 1 — secrets-patterns.json 스키마 + common high confidence 패턴 + 작성 가이드 | 🔄 진행 중 | 본 PR |
| 2 — skill-health-check SKILL.md SEC-01 외부화 + SEC-05/06/07 추가 | ⏳ 대기 | Step 1 의존 |
| 3 — 도메인별 high confidence 패턴 (fintech/healthcare/ecommerce) | ⏳ 대기 | Step 1, 2 의존 |
| 4 — security-migration.md + CHANGELOG + VERSION → alpha.4 | ⏳ 대기 | Step 1~3 |

**재개 프롬프트 예시**:
> `docs/v2/phase-5-plan.md` 읽고 Step {N} 착수해줘. 직전 완료는 PR #{PR번호}.

---

## 요구사항 요약 (옵션 B + B-2)

skill-health-check에 **민감정보 탐지(Secrets Scanner)**와 **보안 항목 강화**를 추가하여 ECC AgentShield의 핵심 기능을 ACK에 내재화한다. 단:

1. **D0 부채 (Phase 1 마이그레이션 결함)**는 Step 1 시작 전 별도 PR(#35)로 선해소 ✅ 완료.
2. 콘텐츠는 **신규 패턴은 high confidence만** 포함 (false positive 통제). 단 `common.runtime`(SEC-S06~S17)은 v1.x SEC-01 12 패턴 외부화로 회귀 보존을 위해 `medium` 허용. low는 v2.1+로 이관.
3. 도메인 콘텐츠는 fintech/healthcare/ecommerce만. saas는 확정 패턴 부재로 보류.

세부 분석/리스크/결정 근거: [`phase-5-tft-analysis.md`](./phase-5-tft-analysis.md).

---

## 🔒 핵심 결정 사항 (TFT 결과)

| ID | 결정 | 영향 |
|----|------|------|
| **D0** | hook-safety 가중치 부채 선분리 PR | ✅ PR #35 완료 |
| **D1** | SEC ID 통합 — SEC-01~04(기존) + SEC-05~07(신규) + SEC-S{nn}(외부 패턴 ID, 출처 표기용) | Step 1, 2 |
| **D2** | 명시 가중치 = 정규화 후 비율 → 점수 영향 ≤ 1점 | ✅ PR #35 완료 |
| **D3** | secrets-patterns.json 스키마 — `common.hardcoded` / `common.runtime` / `domain.patterns` 3섹션. SSOT는 _base + 도메인별 분산 | Step 1, 3 |
| **D4** | 옵션 B: 신규는 high confidence만. `common.runtime`(v1.x SEC-01 회귀 보존) 한정 medium 허용. low는 v2.1+ | Step 1, 3 |
| **D5** | autoFix 전 항목 금지 (보안 정책 유지) | Step 2 |
| **D6** | Phase 4 rules와 다층 방어 — 검사 시점/방식 다름, 중복 보고 OK | Step 2 |
| **D7** | secrets-patterns.schema.json은 향후 Phase로 이관 (SKILL.md 형식 명세만) | Step 1 |

---

## 🛡️ 보안/하위호환 영향

| 항목 | 영향 | 대응 |
|------|------|------|
| `.claude/settings.json` / `.claude/hooks/` | 변경 없음 | — |
| 기존 SEC-01~04 결과 | Step 2에서 SEC-01 외부화 시 회귀 위험 | 12 패턴 평문 ↔ JSON 1:1 검증 + 회귀 테스트 (Step 2 검증) |
| 도메인 점수 | D0 해소(PR #35)로 정규화 ±1점 → 명시화. Phase 5 자체는 카테고리 가중치 미변경 (security 내부 항목 확장만) | release notes 명시 |
| `general` 도메인 | common 패턴만 적용. 도메인별 패턴 부재 시 SEC-07 SKIP | SKILL.md 절차에 명문화 |
| `none` techStack | 기존 SEC-* 정책과 일관 — 파일 패턴 부재로 전 SEC SKIP | 변경 없음 |

---

## 현재 상태 점검

| 항목 | 상태 |
|------|------|
| VERSION | `2.0.0-alpha.3` (Phase 4 완료) |
| `.claude/domains/_base/health/secrets-patterns.json` | **부재 — Step 1 신규** |
| `.claude/domains/_base/health/README.md` | 부재 — Step 1 신규 (작성 가이드) |
| skill-health-check `secrets` 항목 | 부재 — Step 2 |
| 도메인별 secrets-patterns.json | 부재 — Step 3 |
| `docs/v2/security-migration.md` | 부재 — Step 4 |
| 도메인 _category.json hook-safety 명시 | ✅ PR #35 완료 |

---

## 설계 개요

### 컴포넌트 구조

```
.claude/
├── domains/
│   ├── _base/
│   │   └── health/
│   │       ├── _category.json              [기존]
│   │       ├── secrets-patterns.json       [Step 1 신규]  common.hardcoded + common.runtime
│   │       └── README.md                   [Step 1 신규]  작성 가이드 (rules/README.md 패턴)
│   ├── fintech/health/
│   │   └── secrets-patterns.json           [Step 3 신규]  domain.patterns (PAN Luhn / 오픈뱅킹 토큰)
│   ├── healthcare/health/
│   │   └── secrets-patterns.json           [Step 3 신규]  domain.patterns (SSN)
│   └── ecommerce/health/
│       └── secrets-patterns.json           [Step 3 신규]  domain.patterns (한국 주민/사업자)
├── skills/skill-health-check/
│   └── SKILL.md                            [Step 2 수정]  SEC-01 외부화 + SEC-05/06/07 추가
docs/v2/
├── phase-5-tft-analysis.md                 [Step 0 산출물 → Step 1 PR에 commit]
├── phase-5-plan.md                         [Step 1 신규 — 본 문서]
└── security-migration.md                   [Step 4 신규]  alpha.2 정규화 부채 → 명시화 안내
VERSION                                     [Step 4 → alpha.4]
README.md                                   [Step 4 — 뱃지 갱신]
CHANGELOG.md                                [Step 4 — Phase 5 항목 추가]
```

### 시퀀스 (skill-health-check secrets 검사 흐름 — Step 2 도입 후)

```
skill-health-check 실행
  → Phase A: 설정 로딩 (기존)
  → Phase B: 검사 실행
       ├─ doc-sync (기존)
       ├─ state-integrity (기존)
       ├─ security
       │   ├─ SEC-01 (외부화): _base/health/secrets-patterns.json common.runtime 로드 + 12 패턴 매칭
       │   ├─ SEC-02 (기존): SQL Injection
       │   ├─ SEC-03 (기존): CORS
       │   ├─ SEC-04 (기존): API 인증
       │   ├─ SEC-05 (신규): _base + common.hardcoded 로드 + 시크릿 매칭
       │   ├─ SEC-06 (신규): .env 파일 + .gitignore 게이트
       │   └─ SEC-07 (신규): {domain}/health/secrets-patterns.json domain.patterns 로드 (부재 시 SKIP)
       ├─ agent-config (기존)
       └─ hook-safety (Phase 1)
  → Phase C, D (기존)
```

### 데이터 모델 (Step 1)

#### `_base/health/secrets-patterns.json` 스키마

```json
{
  "version": "1.0.0",
  "common": {
    "hardcoded": [
      {
        "id": "SEC-S01",
        "name": "API 키 하드코딩",
        "pattern": "(?i)(api[_-]?key|apikey)\\s*[:=]\\s*['\"][A-Za-z0-9_\\-]{16,}['\"]",
        "severity": "CRITICAL",
        "confidence": "high",
        "description": "API 키 변수에 16자 이상 하드코딩된 문자열",
        "excludeFiles": ["**/test/**", "**/*.test.*", "**/*.spec.*", "**/__tests__/**", "docs/**", "**/*.md"],
        "excludeContexts": ["env_var_reference", "type_declaration", "comment"]
      }
    ],
    "runtime": [
      {
        "id": "SEC-S04",
        "name": "비밀번호 로깅",
        "pattern": "(?i)log(?:ger)?\\.\\w+\\([^)]*\\bpassword\\b",
        "severity": "CRITICAL",
        "confidence": "high",
        "description": "logger 호출에 password 변수 직접 전달",
        "excludeFiles": ["**/test/**", "**/*.test.*", "**/*.spec.*", "**/__tests__/**"],
        "excludeContexts": ["type_declaration", "comment"]
      }
    ]
  }
}
```

#### 필드 정의

| 필드 | 필수 | 설명 |
|------|:---:|------|
| `id` | ✅ | `SEC-S{nn}` 형식. 외부 패턴 ID. SKILL.md SEC-01/05/07이 매칭 시 출처 표기에 사용 |
| `name` | ✅ | 사람이 읽는 패턴 이름 |
| `pattern` | ✅ | JavaScript 호환 정규식 (Grep / Python `re` 양쪽 호환 권장) |
| `severity` | ✅ | `CRITICAL` / `MAJOR` / `MINOR` |
| `confidence` | ✅ | `high` / `medium` / `low` — 옵션 B: 신규는 high, `common.runtime`(SEC-S06~S17)은 medium 허용 |
| `description` | ✅ | 위반 시 사용자에게 표시할 설명 |
| `excludeFiles` | 권장 | 글롭 패턴 배열. 매칭 시 검사 제외 |
| `excludeContexts` | 권장 | enum 배열: `env_var_reference` / `type_declaration` / `comment` |

#### `excludeContexts` 처리 정책 (SKILL.md에 정의 예정 — Step 2)

- `env_var_reference`: `process\.env\.\w+`, `os\.environ\[`, `System\.getenv\(`
- `type_declaration`: `class|interface|type` 키워드 직후 단어
- `comment`: 라인 시작 `//`, `#`, `/*`, ` * `

---

## 스텝 분리 (4 PR + 1 설계문서 + 선PR 완료)

| Step | 제목 | 예상 라인 | 주요 파일 | 의존 |
|------|------|----------|---------|------|
| 0 | TFT 설계 (설계문서) | — | `docs/v2/phase-5-tft-analysis.md` | — |
| 선 | D0 hook-safety 가중치 부채 해소 | ✅ 완료 | PR #35 (d0715de) | — |
| 1 | secrets-patterns.json 스키마 + common high confidence + plan.md + 작성 가이드 | ~280 | `_base/health/secrets-patterns.json`, `_base/health/README.md`, `docs/v2/phase-5-plan.md`, TFT 산출물 commit | 선 |
| 2 | skill-health-check SEC-01 외부화 + SEC-05/06/07 추가 | ~250 | `skill-health-check/SKILL.md` | Step 1 |
| 3 | 도메인별 high confidence 패턴 (fintech PAN/오픈뱅킹, healthcare SSN, ecommerce 한국 주민/사업자) | ~200 | `{fintech,healthcare,ecommerce}/health/secrets-patterns.json` | Step 1, 2 |
| 4 | security-migration.md + CHANGELOG + VERSION → alpha.4 | ~150 | `docs/v2/security-migration.md`, `CHANGELOG.md`, `VERSION`, `README.md` | Step 1~3 |

> **라인 제한**: Step 1~3는 개별 PR, Step 4는 릴리스 PR. prLineLimit 전역 500 적용.

---

## 스텝별 상세

### Step 0: TFT 설계 (설계문서) — ✅ 완료

**산출물**: [`docs/v2/phase-5-tft-analysis.md`](./phase-5-tft-analysis.md)

본 PR(Step 1)에서 git에 commit 추가 (untracked → tracked).

### 선: D0 hook-safety 가중치 부채 해소 — ✅ 완료 (PR #35, d0715de)

4개 도메인 `_category.json`에 hook-safety weight 9 명시. Hamilton 일관 라운딩으로 보정 (healthcare phi=41 보정 — M001 반영).

### Step 1: secrets-patterns.json 스키마 + common 패턴 + 작성 가이드 (PR 1)

**파일**:

- `.claude/domains/_base/health/secrets-patterns.json` (신규, ~150줄):
  - `common.hardcoded`: 5 high confidence 패턴
    - SEC-S01: API 키 하드코딩 (`api_key`, `apikey` 등)
    - SEC-S02: 시크릿/비공개 키 (`secret`, `private_key`)
    - SEC-S03: AWS Access Key 5 prefix (`(?:AKIA|AGPA|AROA|AIDA|ANPA)[0-9A-Z]{16}`. ASIA STS 임시 토큰은 코드 하드코딩 가능성 낮아 제외)
    - SEC-S04: GitHub Token 5 prefix (`(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}` — PAT/OAuth/User App/Server App/Refresh)
    - SEC-S05: Slack Bot Token (`xox[bp]-[\w-]+`)
  - `common.runtime`: SEC-01 12 패턴 외부화 — **medium confidence** (v1.x 회귀 보존 한정, 정보성 로그 메시지 false positive 가능성 인지). Step 2에서 SKILL.md가 이를 로드
    - SEC-S06~S17: log.*password, log.*cardNumber, log.*creditCard, log.*cvv, log.*ssn, log.*주민등록, logger.*secret, println.*password, log.*apiKey, log.*token, log.*bearer, log.*authorization
    - 각 패턴에 `excludeContexts: ["type_declaration", "comment"]` 명시 (기존 SEC-01의 `class.*Password` 제외 정책 보존)

- `.claude/domains/_base/health/README.md` (신규, ~120줄):
  - 섹션 구성:
    1. **개요**: secrets-patterns.json은 health-check가 자동으로 로드하는 패턴 라이브러리
    2. **secrets-patterns.json 스키마** (위 §데이터 모델 표 그대로)
    3. **common vs domain 분리 원칙**:
       - `common`: 도메인 무관 (API 키, 시크릿, 클라우드 자격) — `_base/`만
       - `domain.patterns`: 도메인 특화 (PAN, SSN 등) — `{domain}/health/`만
    4. **confidence 등급 가이드**:
       - high: 정규식이 false positive 거의 없음 (Luhn, 형식 명확)
       - medium: 부분 매칭 (현재 v2.0 미포함)
       - low: 휴리스틱 (현재 v2.0 미포함)
    5. **excludeFiles 기본 권장**: test/spec/__tests__/docs/markdown
    6. **excludeContexts enum 정의**:
       - `env_var_reference`, `type_declaration`, `comment`
    7. **새 패턴 추가 절차**:
       - high confidence 검증 → 정규식 작성 → 테스트 fixture 작성 (Step 2 이후) → PR
    8. **금지 항목**:
       - 신규 medium/low confidence 패턴 (v2.0 범위 외 — `common.runtime` SEC-01 회귀 보존 medium 예외)
       - autoFix 활성화 (보안 정책)
       - 도메인 무관 패턴을 `domain.patterns`에 작성

- `docs/v2/phase-5-plan.md` (본 문서, 신규, ~250줄)

- `docs/v2/phase-5-tft-analysis.md` (Step 0 untracked 산출물 → commit)

**Step 1에서 만들지 않는 것**:
- 도메인별 secrets-patterns.json 디렉토리 (Step 3)
- skill-health-check SKILL.md 변경 (Step 2)
- security-migration.md (Step 4)
- secrets-patterns.schema.json (D7 — 차후 Phase로 이관)

**검증**:
- `python3 -c "import json; json.load(open('.claude/domains/_base/health/secrets-patterns.json'))"` → JSON 유효
- 공통 패턴 5개 + 12 runtime 패턴 = 17개 entries 확인
- 모든 entry에 필수 필드(`id`/`name`/`pattern`/`severity`/`confidence`/`description`) 존재
- `confidence`: hardcoded 5개 `high`, runtime 12개 `medium` (회귀 보존). 신규 추가는 `high`만
- 정규식 컴파일 가능성 (Python `re.compile`로 17개 모두 검증)
- README.md markdown 렌더링 정상

### Step 2: skill-health-check SEC-01 외부화 + SEC-05/06/07 추가 (PR 2)

**파일**:
- `.claude/skills/skill-health-check/SKILL.md` (수정, ~250줄)
  - SEC-01 본문 교체:
    - 인라인 12 패턴 정의 → `_base/health/secrets-patterns.json` `common.runtime` 로드로 교체
    - excludeContexts 처리 절차 정의
  - 신규 항목 추가:
    - **SEC-05** (CRITICAL): 하드코딩 시크릿 — `common.hardcoded` 로드
    - **SEC-06** (CRITICAL): 환경변수 파일 노출 — `.env` 존재 + `.gitignore` 미등록 + 평문 secret 검사
    - **SEC-07** (CRITICAL): 도메인별 민감 데이터 — `{domain}/health/secrets-patterns.json` `domain.patterns` 로드 (부재 시 SKIP)
  - excludeContexts 처리 SSOT:
    - `env_var_reference`: `process\.env\.\w+`, `os\.environ\[`, `System\.getenv\(`
    - `type_declaration`: `class|interface|type` 키워드 직후 단어
    - `comment`: 라인 시작 `//`, `#`, `/*`, ` * `

**검증** (옵션 B 회귀):
- 기존 SEC-01 12 패턴 매칭 결과 동일 (alpha.3 ↔ alpha.4 회귀 fixture 비교)
- SEC-05: AWS Access Key 박힌 fixture → CRITICAL FAIL
- SEC-06: `.env` 평문 + `.gitignore` 미등록 → CRITICAL FAIL
- SEC-07: 도메인 콘텐츠 부재 시 SKIP, 부재한 도메인(general) → SKIP
- excludeContexts 동작: `class Password { }` 미매칭, `process.env.API_KEY` 미매칭

### Step 3: 도메인별 high confidence 패턴 (PR 3)

**파일**:
- `.claude/domains/fintech/health/secrets-patterns.json` (신규, ~80줄)
  - **PAN (카드번호)**: 16자리 숫자 + Luhn 알고리즘 검증 — `confidence: high`
    - 정규식만으론 false positive 위험. Luhn 검증을 SKILL.md 또는 별도 알고리즘 단계에 위임 (Step 2 SKILL.md 절차에 Luhn 처리 포함)
  - **오픈뱅킹 토큰**: 한국 오픈뱅킹 표준 — 명확한 prefix가 있으면 high
- `.claude/domains/healthcare/health/secrets-patterns.json` (신규, ~50줄)
  - **SSN (미국)**: `\d{3}-\d{2}-\d{4}` 형식 — high (형식 명확)
- `.claude/domains/ecommerce/health/secrets-patterns.json` (신규, ~60줄)
  - **한국 주민등록번호**: `\d{6}-\d{7}` + 체크섬 (Luhn 비슷)
  - **한국 사업자번호**: `\d{3}-\d{2}-\d{5}` + 체크섬

**검증**:
- 각 파일 `domain.patterns` entry 1~2개, 모두 `confidence: high`
- fintech PAN fixture: Luhn 통과 16자리 → CRITICAL FAIL, Luhn 미통과 → 매칭 후 SKIP (Luhn 검증으로 false positive 차단)
- healthcare SSN fixture: 형식 일치 → FAIL
- ecommerce 주민/사업자 fixture: 체크섬 통과 → FAIL

### Step 4: security-migration.md + CHANGELOG + VERSION → alpha.4 (PR 4)

**파일**:
- `docs/v2/security-migration.md` (신규, ~150줄):
  - **alpha.2 정규화 부채 해소 시점**: PR #35 (d0715de) 기록
  - **alpha.3 → alpha.4 가중치 변화 표** (사용자 점수 영향 ±1점 이내, 정규화 후 비율 명시화)
  - **신규 SEC-* 항목 매핑**: SEC-01 외부화 결과 동일성, SEC-05~07 신규 검사 안내
  - **autoFix 정책**: 모든 SEC-* 수동 수정 필수
  - **excludeFiles/excludeContexts 사용자 가이드**
- `VERSION`: `2.0.0-alpha.3` → `2.0.0-alpha.4`
- `README.md`: 제목 + 뱃지 갱신
- `CHANGELOG.md`: `[2.0.0]` 섹션에 Phase 5 Added/Changed/Breaking 서브섹션 추가

---

## 파일 충돌 검사

현재 v2-develop에 다른 in_progress Phase 작업 없음. v1.x 핫픽스 가능성:
- `.claude/skills/skill-health-check/SKILL.md` (Step 2) — 동일 영역 변경 시 충돌. **Step 2 시작 전 `git fetch origin develop && git merge origin/develop` 권장**.

---

## 성공 기준

- [ ] `_base/health/secrets-patterns.json`에 common.hardcoded 5 + common.runtime 12 = 17개 high confidence 패턴
- [ ] `_base/health/README.md` 작성 가이드 + confidence 등급 정의 + 새 패턴 추가 절차
- [ ] skill-health-check `secrets` 항목 (SEC-05/06/07) 동작 — high confidence 매칭
- [ ] SEC-01 외부화 후 결과가 alpha.3 동일 (회귀 검증)
- [ ] 도메인별 패턴 (fintech PAN+오픈뱅킹, healthcare SSN, ecommerce 한국 주민/사업자) 동작
- [ ] saas/general 도메인은 SEC-07 SKIP (도메인 패턴 부재)
- [ ] `excludeFiles`/`excludeContexts` 동작 — false positive 통제
- [ ] autoFix 모든 SEC-* 거부
- [ ] CHANGELOG/VERSION/README alpha.4 일관
- [ ] security-migration.md에 alpha.2 정규화 부채 → 명시화 사실 기록
- [ ] **신규 medium/low confidence 패턴 0개** — `common.runtime`(SEC-S06~S17, v1.x SEC-01 회귀 보존) medium만 허용 (옵션 B + PR #36 H001 보정)

---

## 리스크 및 대응

> 상세 근거는 [phase-5-tft-analysis.md](./phase-5-tft-analysis.md) §10 참조.

| ID | 리스크 | 확률 | 영향 | 대응 | 감지 스텝 |
|----|--------|------|------|------|----------|
| **R1** | regex 오탐 → 사용자 신뢰도 손상 | 중 | 높음 | high confidence만 (옵션 B), excludeFiles + excludeContexts SSOT | Step 1, 3 |
| **R2** | hook-safety 가중치 정정으로 점수 변화 | ✅ 해소 | — | PR #35 완료. Phase 5 자체는 카테고리 가중치 미변경 | — |
| **R3** | SEC-01 외부화 시 동작 회귀 | 중 | 중 | 12 패턴 평문 ↔ JSON 1:1 검증 + 회귀 fixture | Step 2 |
| **R4** | 도메인별 패턴 정확도 부족 | 높→중 | 중 | high confidence만 (옵션 B). PAN Luhn 검증, SSN 형식 명확 | Step 3 |
| **R5** | secrets-patterns.json 스키마 부재 → 잘못된 작성 | 중 | 낮 | README.md 형식 명세 + 검증 가이드 | Step 1 |
| **R6** | Phase 4 rules와 중복 보고 | 낮 | 낮 | 다층 방어 OK 정책. 출처 표기로 분별 | Step 2 |
| **R7** | autoFix 시도로 보안 wound | 낮 | 높음 | 모든 SEC-* autoFix 명시 금지 | Step 2 |
| **R8** | --quick 모드 검사 시간 증가 | 낮 | 낮 | high confidence ~17개 + Grep 단일 호출 | Step 2 |
| **R9** | docs/, *.md false positive | 중 | 낮 | excludeFiles 기본값에 docs/, *.md 포함 | Step 1 |

---

## 진행 방식 권장

1. **Step 0 (설계)**: ✅ 완료
2. **선 (D0)**: ✅ 완료 (PR #35)
3. **Step 1~3**: 각 PR 생성 시 `feature/phase-5-security-step-N` 브랜치 → `v2-develop`으로 머지
4. **Step 4**: 모든 스텝 머지 확인 후 릴리스 PR (v2-develop, 태그 `v2.0.0-alpha.4`)
5. 각 PR 머지 전 `/skill-review-pr` 실행 권장 (특히 Step 2 — skill-health-check 본체 변경)

---

## 참고 문서

- [phase-5-security.md](./phase-5-security.md) — 상위 계획
- [phase-5-tft-analysis.md](./phase-5-tft-analysis.md) — TFT 분석 + 옵션 B 결정
- [phase-4-plan.md](./phase-4-plan.md) — 직전 Phase 진행 패턴 참고
- [README.md](./README.md) — 전체 Phase 로드맵
