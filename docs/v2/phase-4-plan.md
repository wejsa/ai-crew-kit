# Phase 4: 4-Layer Override + Constraint Rules — 구현 계획서

> **상위 문서**: [phase-4-rules.md](./phase-4-rules.md)
> **TFT 분석**: [phase-4-tft-analysis.md](./phase-4-tft-analysis.md)
> **버전 목표**: `v2.0.0-alpha.3` (Phase 4 단독)
> **브랜치**: `feature/phase-4-rules-step-*` (v2-develop 분기, Step별 별도 브랜치)
> **예상 작업량**: 3~4시간 (TFT 설계 1.5h 완료 + 구현 1.5h + 검증 1h)
> **우선순위**: P1 | **의존성**: Phase 0 (완료) | **난이도**: S
> **채택안**: **옵션 A — 메커니즘만 구현, MVP 3개 콘텐츠 보류** ([TFT §11](./phase-4-tft-analysis.md#11) 참조)

---

## 🔄 현재 진행 상황 (다른 세션에서 재개 시 확인)

| Step | 상태 | 비고 |
|------|------|------|
| 0 — TFT 설계 + 옵션 결정 | ✅ 완료 | [phase-4-tft-analysis.md](./phase-4-tft-analysis.md) — 옵션 A 채택 |
| 1 — rules 디렉토리 + README + schema description + 예시 템플릿 | ✅ 완료 | PR #30 머지 (73b2a92) — 리뷰 MINOR 3건 반영(M001 README 4-백틱 펜스 격상, M002 sample-rule 인라인 코드 통일, M003 skill-review-pr 통합 섹션 상태 안내) |
| 2 — skill-review-pr Step 2.5 통합 | ✅ 완료 | PR #31 머지 (ff1d2ac) — 리뷰 MINOR 2건 반영(M001 SSOT 이중화 제거 A안, M002 Step 5 출력 위치 명시) |
| 3 — concepts.md + customization.md 4층 다이어그램 | ⏳ 대기 | Step 1 의존 |
| 4 — CHANGELOG + VERSION bump → alpha.3 | ⏳ 대기 | Step 1~3 |

**재개 프롬프트 예시**:
> `docs/v2/phase-4-plan.md` 읽고 Step {N} 착수해줘. 직전 완료는 PR #{PR번호}.

---

## 요구사항 요약 (옵션 A)

도메인 × 언어 교차 **제약 규칙(Constraint Rules)** 메커니즘을 신설한다. 디렉토리 구조 + 작성 가이드 + skill-review-pr 자동 참조 통합. **MVP 3개 콘텐츠는 작성하지 않는다** — 실 사용 케이스 발생 시 사용자가 직접 작성하도록 토대만 제공.

세부 범위/TFT 분석 항목은 `docs/v2/phase-4-rules.md` 및 `phase-4-tft-analysis.md` 참조.

---

## 🔒 핵심 결정 사항 (TFT 결과 + 사용자 결정)

> 상세 근거는 [phase-4-tft-analysis.md](./phase-4-tft-analysis.md) §1~5, §11 참조.

| ID | 결정 | 영향 |
|----|------|------|
| **D1** | 4층 적용은 **rules 영역 신설**에만 한정. 기존 conventions/checklists/health 구조 보존 | Step 1, 3 |
| **D2** | `overridePriority`는 schema enum 활성화 + default `domain-first`. **MVP는 분기 로직 미구현** | Step 1 |
| **D3** | language 매핑 SSOT는 **rules/README.md**에 표 형태 (별도 JSON 만들지 않음) | Step 1, 2 |
| **D4** | rules는 **frontmatter 필수** (id/domain/language/severity/triggers/related). 검증은 향후 skill-validate로 이관 | Step 1 |
| **D5** | **`_base/rules/`, `{domain}/rules/`, frontend rules는 만들지 않음** (범위 초과) | 모든 Step |
| **D6** | skill-review-pr **Step 2.5 (Rules 로드)** 신설. pr-reviewer-domain만 rules 참조 | Step 2 |
| **D7** | **Trivial 경량 리뷰**(코드 변경 0건)는 rules 단계 SKIP — false positive 방지 | Step 2 |
| **D8** | **MVP 3개 콘텐츠 작성 보류** (옵션 A). README에 **예시 템플릿 1개**(가짜 도메인×언어)만 포함 | Step 1 |

---

## 🛡️ 보안/하위호환 영향

| 항목 | 영향 | 대응 |
|------|------|------|
| `.claude/settings.json` | 변경 없음 | — |
| `.claude/hooks/` | 변경 없음 | — |
| 기존 PR 리뷰 동작 | rules 디렉토리 부재 시 **기존 동작 100% 유지** | Step 2 검증 |
| `project.schema.json` overridePriority | Phase 0에서 enum 정의됨 — Step 1에서 description만 보강 | Step 1 |
| 기존 conventions 24개 | **변경 없음** | TFT §2.2 감사 완료 |
| 실제 도메인×언어 룰 콘텐츠 | **0개 (옵션 A)** — 사용자가 필요 시 추가 | — |

---

## 현재 상태 점검

| 항목 | 상태 |
|------|------|
| VERSION | `2.0.0-alpha.2` (Phase 1 완료) |
| `.claude/rules/` 디렉토리 | **부재 — Step 1에서 신규 생성** |
| `project.schema.json` `overridePriority` | enum 활성, description 일반화("Phase 4에서 상세 정의") — Step 1에서 구체화 |
| `skill-review-pr` rules 로드 단계 | **부재 — Step 2 신설** |
| `docs/concepts.md` Layered Override | 3층 — Step 3에서 4층 갱신 |
| `docs/customization.md` Layered Override | 3층 — Step 3 갱신 |

---

## 설계 개요

### 컴포넌트 구조 (옵션 A)

```
.claude/
├── rules/                                  [신규]
│   ├── README.md                          rules vs conventions, language 매핑 SSOT, 작성 가이드, 예시 템플릿
│   └── _example/                          예시 템플릿 (사용자 학습용, 실제 적용 X)
│       └── _example/
│           └── sample-rule.md             가짜 frontmatter + 좋은/나쁜 예시 패턴 시연
├── schemas/
│   └── project.schema.json                [수정] overridePriority description 보강
└── skills/
    └── skill-review-pr/
        └── SKILL.md                       [수정] Step 2.5 (Rules 로드) 신설
docs/
├── concepts.md                            [수정] 4층 Layered Override
└── customization.md                       [수정] 4층 다이어그램 + rules 가이드
```

> **참고**: `_example/_example/` 디렉토리 명명은 의도적. language 매핑 표에서 `_example`은 매핑 없음 → 실제 PR 리뷰에서 매칭되지 않음. 순수 학습용.

### 시퀀스 (skill-review-pr 흐름 변화)

```
PR 리뷰 시작
  → Step 1: PR 정보 수집
  → Step 2: 체크리스트 (기존)
  → Step 2.5 [신설]: Rules 로드
       1. project.json의 domain, techStack.backend 읽기
       2. language 매핑 (rules/README.md SSOT)
       3. .claude/rules/{domain}/{language}/*.md 글롭
       4. 매칭 파일 경로 수집 (없으면 SKIP — 옵션 A에서 일반적 동작)
  → Step 3: N관점 병렬 리뷰
       ↳ pr-reviewer-domain에 rules_paths 전달 (있을 때만)
  → 이후 단계 (기존)
```

### 데이터 모델

#### project.schema.json `overridePriority` 보강

```json
{
  "overridePriority": {
    "type": "string",
    "enum": ["domain-first", "merge"],
    "default": "domain-first",
    "description": "도메인 vs 언어 규칙 충돌 시 우선순위. domain-first: 도메인 룰이 언어 룰을 덮어씀(MVP 단일 디렉토리 구조에서는 충돌 없음). merge: 양쪽 모두 적용. v2.0 MVP는 분기 로직 미구현 — 향후 단독 도메인/언어 룰 도입 시 활성화."
  }
}
```

#### rules 파일 frontmatter 표준 (D4)

```yaml
---
id: <kebab-case>
domain: <healthcare|fintech|saas|ecommerce|general|_example>
language: <python|kotlin|typescript|java|go|_example>
severity: <CRITICAL|MAJOR|MINOR>
triggers:
  - "<regex>"
related:
  - "<상대 경로>"
---
```

#### language 매핑 (rules/README.md SSOT)

| `techStack.backend` | rules 디렉토리 |
|--------------------|---------------|
| `spring-boot-kotlin` | `kotlin` |
| `spring-boot-java` | `java` |
| `nodejs-typescript` | `typescript` |
| `python-fastapi` | `python` |
| `python-django` | `python` |
| `go` | `go` |
| `none` | (스킵) |

---

## 스텝 분리 (4 PR + 1 설계문서)

| Step | 제목 | 예상 라인 | 주요 파일 | 의존 |
|------|------|----------|---------|------|
| 0 | TFT 설계 (설계문서) | — | `docs/v2/phase-4-tft-analysis.md` | — |
| 1 | rules 디렉토리 + README + schema description + 예시 템플릿 | ~280 | `.claude/rules/README.md`, `.claude/rules/_example/_example/sample-rule.md`, `.claude/schemas/project.schema.json` | Step 0 |
| 2 | skill-review-pr Step 2.5 통합 | ~120 | `.claude/skills/skill-review-pr/SKILL.md` | Step 1 |
| 3 | docs/concepts.md + customization.md 갱신 | ~80 | `docs/concepts.md`, `docs/customization.md` | Step 1 |
| 4 | CHANGELOG + VERSION + 통합 검증 | ~50 | `CHANGELOG.md`, `VERSION`, `README.md` | Step 1~3 |

> **라인 제한**: Step 1~3는 개별 PR, Step 4는 릴리스 PR. prLineLimit 전역 500 적용.

---

## 스텝별 상세

### Step 0: TFT 설계 (설계문서, PR 없음)

**산출물**: [`docs/v2/phase-4-tft-analysis.md`](./phase-4-tft-analysis.md) — ✅ 완료

### Step 1: rules 디렉토리 + README + schema description + 예시 템플릿 (PR 1)

**파일**:
- `.claude/rules/README.md` (신규, ~180줄) — 섹션 구성:
  1. **개요**: rules는 도메인 × 언어 제약 규칙 (MUST/MUST NOT)
  2. **rules vs conventions** 비교표
  3. **language 매핑 테이블** (D3 SSOT)
  4. **frontmatter 표준** (D4)
  5. **새 rule 작성 가이드라인**:
     - "Claude가 이미 아는 기술" ✗ vs "도메인 비즈니스 제약" ✓
     - MUST / MUST NOT 형식 강제
     - 좋은/나쁜 코드 예시 필수
     - 탐지 패턴(정규식) 권장 — false positive 허용
  6. **예시 템플릿 안내**: `_example/_example/sample-rule.md` 참조
  7. **현재 정책**: MVP 단일 디렉토리, `overridePriority` 분기 미구현 (D2)
  8. **금지 항목**: `_base/rules/`, `{domain}/rules/` 단독 층 신규 생성 금지 (D5)
  9. **미작성 도메인×언어 추가 절차**: 디렉토리 생성 → frontmatter 표준 따라 작성 → PR

- `.claude/rules/_example/_example/sample-rule.md` (신규, ~80줄) — **학습용 예시 템플릿** (D8):
  ```markdown
  ---
  id: sample-rule
  domain: _example
  language: _example
  severity: MAJOR
  triggers:
    - "<여기에 정규식>"
  related:
    - "<관련 도메인 docs 경로>"
  ---

  # 예시 룰: <제목>

  > 본 파일은 **rules 작성 가이드용 템플릿**입니다.
  > `_example/_example/` 경로는 language 매핑 표에 없으므로 실제 리뷰에 적용되지 않습니다.

  ## 제약 (MUST / MUST NOT)
  - 도메인 비즈니스 의미를 담은 강제 사항을 작성합니다.
  - 예: "<도메인>에서 <언어>로 <X>를 직접 사용 금지"

  ## 좋은 예
  ```<language>
  // 모범 패턴
  ```

  ## 나쁜 예
  ```<language>
  // 안티패턴
  ```

  ## 안전한 대체 패턴
  - 안티패턴 대신 사용할 수 있는 안전한 방법 설명

  ## 근거
  - 컴플라이언스 표준 / 도메인 docs 링크
  ```

- `.claude/schemas/project.schema.json` (수정, ~3줄) — `overridePriority.description`을 위 §데이터 모델대로 교체

**Step 1에서 만들지 않는 것** (D8):
- 실제 도메인 디렉토리(`healthcare/`, `fintech/`, `saas/`)는 만들지 않음
- `.gitkeep`도 만들지 않음 — 사용자가 첫 rule을 추가할 때 자연스럽게 생성

**검증**:
- `find .claude/rules -type f` → README.md + _example/_example/sample-rule.md 2개
- `python3 -c "import json; json.load(open('.claude/schemas/project.schema.json'))"` → JSON 유효
- 기존 examples/ project.json들이 새 schema validate 통과
- `python3 -c "import yaml; yaml.safe_load(open('.claude/rules/_example/_example/sample-rule.md').read().split('---')[1])"` → frontmatter 파싱 성공

### Step 2: skill-review-pr Step 2.5 통합 (PR 2)

**파일**:
- `.claude/skills/skill-review-pr/SKILL.md` (수정, ~70줄)
  - **새 섹션 "Step 2.5: 도메인 × 언어 Rules 로드"** 추가 (Step 2와 Step 3 사이):
    ```markdown
    ### 2.5. 도메인 × 언어 Rules 로드

    1. project.json의 `domain`, `techStack.backend` 읽기
    2. language 매핑 (`.claude/rules/README.md` 표 참조):
       - spring-boot-kotlin → kotlin
       - spring-boot-java → java
       - nodejs-typescript → typescript
       - python-fastapi/django → python
       - go → go
       - none/매핑 없음 → SKIP
    3. `.claude/rules/{domain}/{language}/*.md` 글롭
    4. 매칭 파일 경로를 `rules_paths` 리스트에 수집
    5. **부재 시 SKIP** (기존 동작 유지)
    6. **Trivial 경량 리뷰 시 SKIP** (D7)
    7. `_example/_example/` 경로는 매핑 표에 없으므로 자연 SKIP

    ### 출력 헤더 (rules_paths 비어있지 않을 때만 표시)
    📋 적용 Rules: {domain}/{language} (N개) — {파일명1}, {파일명2}
    ```
  - **Step 3 (N관점 병렬 리뷰)** 수정: pr-reviewer-domain Task 프롬프트에 `rules_paths` 전달. Read는 에이전트가 수행.
  - **출력 섹션**: "리뷰 모드 헤더" 다음에 "적용 Rules 헤더" 조건부 추가

**검증** (옵션 A에서는 가짜 데이터 dry-run만 가능):
- 가짜 project.json (domain=healthcare, backend=python-fastapi) + 빈 rules 디렉토리 → `rules_paths = []` (SKIP)
- 사용자가 임시로 `.claude/rules/healthcare/python/test.md` 생성 후 dry-run → `rules_paths` 포함
- domain=general or rules 디렉토리 부재 → SKIP, 기존 출력 유지
- Trivial PR(50줄 이하 + src/ 변경 0건) → Rules 단계 SKIP

### Step 3: docs/concepts.md + customization.md 갱신 (PR 3)

**파일**:
- `docs/concepts.md` (수정, ~30줄)
  - L182 핵심 원칙 표의 "Layered Override" 설명 갱신: `_base → {domain} → {domain}/{language} → project.json`
  - L186~L195 다이어그램 4층으로 갱신:
    ```
    1. project.json (사용자 설정)              ← 최우선
    2. .claude/rules/{domain}/{language}/      ← 도메인 × 언어 (Phase 4)
    3. .claude/domains/{domain}/               ← 도메인 설정
    4. .claude/domains/_base/                  ← 공통 기본값
    5. 하드코딩 기본값                          ← 최하위
    ```
  - 주석 추가: "rules는 PR 리뷰 컨텍스트 한정 적용. conventions/checklists는 기존 구조 유지"
- `docs/customization.md` (수정, ~50줄)
  - L5~L24 다이어그램 4층 갱신
  - 새 섹션 **"## 도메인 × 언어 Rules"** 추가 (~30줄):
    - rules vs conventions 비교
    - language 매핑 표
    - 새 rule 작성 안내 (rules/README.md 링크)
    - "현재 콘텐츠 0개. 필요 시 직접 추가" 명시 (옵션 A)

**검증**:
- markdown 렌더링 정상
- 4층 표기 일관성 (concepts.md ↔ customization.md ↔ rules/README.md)

### Step 4: CHANGELOG + VERSION + 통합 검증 (PR 4)

**파일**:
- `/VERSION`: `2.0.0-alpha.2` → `2.0.0-alpha.3`
- `/CHANGELOG.md`: `[2.0.0]` 섹션에 Phase 4 항목 추가
  - **Added**:
    - `.claude/rules/` 디렉토리 (도메인 × 언어 교차 제약 규칙 **메커니즘**)
    - `.claude/rules/README.md` — rules vs conventions 경계, language 매핑 SSOT, 작성 가이드
    - `.claude/rules/_example/_example/sample-rule.md` — 학습용 예시 템플릿
    - skill-review-pr Step 2.5 (Rules 로드)
    - docs/concepts.md + customization.md 4층 Layered Override 다이어그램
  - **Changed**:
    - `project.schema.json` `overridePriority` description 보강
  - **Notes**:
    - 본 릴리스는 **메커니즘만** 포함. 도메인 × 언어 룰 콘텐츠는 사용자가 필요 시 직접 추가.
    - 기존 PR 리뷰 동작 100% 유지 (rules 부재 시 SKIP)
  - **Breaking**: 없음
- `/README.md`: 버전 뱃지 `v2.0.0-alpha.3`
- 통합 검증: dry-run으로 가짜 rules 1개 생성 후 skill-review-pr Step 2.5 동작 시연 → 검증 후 가짜 rules 제거

---

## 파일 충돌 검사

현재 v2-develop에 다른 in_progress Phase 작업 없음. v1.x 핫픽스가 develop에서 발생 시 다음 충돌 가능:
- `docs/concepts.md` (Step 3) — 동일 섹션 수정 시 충돌
- `.claude/skills/skill-review-pr/SKILL.md` (Step 2)
- `.claude/schemas/project.schema.json` (Step 1)

각 Step 시작 전 `git fetch origin develop && git merge origin/develop` 권장.

---

## 성공 기준 (옵션 A)

- [ ] `.claude/rules/README.md` 작성 완료 — rules vs conventions, language 매핑 SSOT, frontmatter 표준, 작성 가이드 포함
- [ ] `.claude/rules/_example/_example/sample-rule.md` 학습 템플릿 작성
- [ ] `project.schema.json` `overridePriority` description이 MVP 미구현 사실 명시
- [ ] skill-review-pr Step 2.5가 가짜 rules 1개로 dry-run 검증 통과
- [ ] rules 디렉토리 부재(또는 매칭 없음) 프로젝트에서 기존 리뷰 동작 100% 유지
- [ ] Trivial PR에서 Rules 단계 SKIP (D7)
- [ ] 기존 conventions/ 24개 파일 변경 없음
- [ ] docs/concepts.md + customization.md 4층 다이어그램 일관성
- [ ] CHANGELOG + VERSION → alpha.3, README 뱃지 갱신
- [ ] **MVP 3개 콘텐츠 작성 X** (옵션 A — 의도적 보류)

---

## 리스크 및 대응 (옵션 A 반영)

> 상세 근거는 [phase-4-tft-analysis.md](./phase-4-tft-analysis.md) §9 참조. R3, R5는 옵션 A 채택으로 영향 축소.

| ID | 리스크 | 확률 | 영향 | 대응 | 감지 스텝 |
|----|--------|------|------|------|----------|
| **R1** | language 매핑 enum 누락 시 rules 로드 실패 | 중 | 중 | rules/README.md SSOT + skill-validate 향후 검증 | Step 1, 3 |
| **R2** | "Claude가 이미 아는 것을 가르치는" 함정 (사용자가 추가 시) | 중 | 중 | rules/README.md "도메인 의미" 원칙 + 작성 가이드 | Step 1 |
| ~~R3~~ | ~~정규식 trigger의 false positive~~ | ~~높~~ | ~~낮~~ | **옵션 A로 MVP 콘텐츠 제거 → 위험 소멸** (사용자가 추가 시 책임) | — |
| **R4** | 기존 conventions와 rules 중복 (사용자 추가 시) | 중 | 중 | rules/README.md 명확한 경계 + TFT §2.2 감사 0건 | Step 1 |
| ~~R5~~ | ~~rules 파일 다수 시 토큰 폭증~~ | ~~낮~~ | ~~중~~ | **옵션 A로 콘텐츠 0개 → 위험 무효화** | — |
| **R6** | Step 2.5가 자기 PR/Trivial 리뷰와 충돌 | 낮 | 중 | Trivial은 rules SKIP (D7) | Step 2 |
| **R7** | overridePriority 분기 미구현 → 사용자 혼동 | 낮 | 낮 | concepts.md + schema description 명시 | Step 1, 3 |
| **R8** | 다이어그램 갱신이 v1 사용자 혼동 | 낮 | 낮 | "Phase 4 도입" 주석 + customization.md 안내 | Step 3 |
| **R9** | 옵션 A로 콘텐츠 0개 → 메커니즘이 죽은 코드처럼 보일 수 있음 | 중 | 낮 | _example 템플릿으로 사용 의도 시연 + README에 "필요 시 추가" 안내 | Step 1 |

---

## 진행 방식 권장

1. **Step 0 (설계)**: ✅ 완료
2. **Step 1~3**: 각 PR 생성 시 `feature/phase-4-rules-step-N` 브랜치 → `v2-develop`으로 머지
3. **Step 4**: 모든 스텝 머지 확인 후 릴리스 PR (v2-develop, 태그 `v2.0.0-alpha.3`)
4. 각 PR 머지 전 `/skill-review-pr` 실행 권장 (특히 Step 2 — skill-review-pr 자기 변경)

---

## 참고 문서

- [phase-4-rules.md](./phase-4-rules.md) — 상위 계획
- [phase-4-tft-analysis.md](./phase-4-tft-analysis.md) — TFT 분석 + 옵션 A 결정
- [phase-1-plan.md](./phase-1-plan.md) — 직전 Phase 진행 패턴 참고
- [README.md](./README.md) — 전체 Phase 로드맵
