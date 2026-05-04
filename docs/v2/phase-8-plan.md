# Phase 8 Lean Closure (옵션 A) — 구현 계획서

> **상위**: [phase-8-release.md](./phase-8-release.md) — Migration & Release / GA
> **채택안**: **옵션 A — Lean Closure** (2026-05-04 합의, [PR #44 코멘트](https://github.com/wejsa/ai-crew-kit/pull/44#issuecomment-4363971097)). phase-8 doc 원본 Task 8-1~8-7 그대로. 통합 회귀 매트릭스 / E2E는 v2.1+ 후속.
> **브랜치**: `feature/phase-8-step-*` (v2-develop 분기)
> **버전 영향**: 마지막 Step에서 alpha.4 → 2.0.0 GA 단일 commit 전환

---

## 🔄 진행 상황 (다른 세션에서 재개 시 확인)

| Step | 상태 | 비고 |
|------|------|------|
| 0 — 옵션 결정 (재진입 시 본 문서) | ✅ 완료 | Phase 7 패턴 일관 — 이미 구현된 메커니즘 + 갭 fix만 |
| 1 — plan.md + skill-upgrade SKILL.md 갭 fix + OQ 기록 | ⏳ 진행 중 | feature/phase-8-step-1 |
| 2 — migration-guide.md (Task 8-2) | ⏳ | |
| 3 — examples/ 마이그레이션 검증 + 회귀 fixture (Task 8-3, ADJ-01) | ⏳ | D0 적용점 |
| 4 — CHANGELOG v2.0.0 (Task 8-4) | ⏳ | |
| 5 — docs/upgrade-guide.md + README 본 페이지 (Task 8-5/8-6) | ⏳ | |
| 6 — VERSION 2.0.0 + branch flow + 태그 (Task 8-7, ADJ-04) | ⏳ | 최종 GA 게이트 |

---

## 진단 (옵션 A 결정 근거 — Phase 7 패턴 일관)

### ✅ 이미 구현된 v2 마이그레이션 메커니즘

Phase 0~5에서 *암묵적으로* 도입된 자산:

| 메커니즘 | 위치 | 동작 |
|---------|------|------|
| `migrations.json` `2.0.0` 엔트리 | `.claude/schemas/migrations.json` | 4개 `add_field` 변경 (`hooks`, `conventions.skillProfile` default `default`, `conventions.overridePriority` default `domain-first`, `tokenHints`) |
| v2.0.0 features 안내 | `migrations.json` `features` | skillProfile + complexity-hint 안내 (`recommend` / `optional`) |
| skill-upgrade Step 5 | `.claude/skills/skill-upgrade/SKILL.md` | `migrations.json` 자동 검출 + 적용 |
| skill-upgrade Step 12-4 | (위와 동일) | `project.json kitVersion 업데이트, kitSource 설정, migrations 적용` |
| skill-upgrade Step 13 | (위와 동일) | CLAUDE.md/README.md 재생성 (`CUSTOM_SECTION_START` 마커 + 결정적 치환) |
| skill-upgrade Step 15.5 | (위와 동일) | `features` 배열에서 v{prev}<v≤v{new} 범위 안내 |
| 백업 + 자동 롤백 | (Step 9~11) | `backup.tar.gz` + `tar tzf` 무결성 검증 + 실패 시 자동 복원 |
| `--rollback` 옵션 | (Step 1, "롤백 모드") | 백업 시점 `kitVersion` 복원 |

### 🔧 갭 (cosmetic doc 부정합)

- `skill-upgrade/SKILL.md` "업데이트 대상" 표에 `.claude/rules/` **누락** — Phase 4에서 디렉토리 추가됐으나 doc 표는 Phase 4 이전 상태
- "보존 대상" 표에 Phase 7 신규 state 파일(`lessons-learned.json`) 명시 없음 (`.claude/state/*` 일반 패턴으로 graceful 흡수되긴 함)

### ⏸ v2.1+ 보류 (D-NEED 미충족 — Phase 6/7 학습)

| 보류 항목 | 보류 사유 | 출처 |
|----------|----------|------|
| **통합 회귀 매트릭스** (별도 workflow) | 현재 `secrets-tests.yml`이 6 jobs 합동 실행 → 추가 가치 의심 | ADJ-02 → D14 |
| **E2E 흐름** (skill-init→plan→impl→review-pr→merge-pr) | v1.x 시기 요청 사례 부재 | ADJ-02 → D15 |
| **자동 롤백 테스트 자동화** | phase-8 doc §범위 경계에서 이미 제외 | doc 명시 |

---

## 🔒 핵심 결정

| ID | 결정 | 영향 |
|----|------|------|
| **D1** | 옵션 A — phase-8 doc Task 8-1~8-7 원본 + Phase 7 패턴 일관 (메커니즘 갭 fix만) | 모든 Step |
| **D2** | branch flow = `v2-develop → develop → main`. develop은 v2 GA 후 **v1.x 핫픽스 라인으로 동결** — v2 신규 작업 진입 차단(`v2-develop`이 후속 v2.x 작업 라인). main↔develop 핫픽스 양방향 머지는 유지 (PR #45 리뷰 MINOR 명확화) | Step 6 |
| **D3** | VERSION `2.0.0-alpha.4 → 2.0.0` 전환은 Step 6 **VERSION 파일 변경 한정 단일 commit** (메모리 §릴리스 프로세스 일관). branch flow 머지 PR 단위는 OQ-03 별도 결정 (PR #45 리뷰 MINOR 명확화) | Step 6 |
| **D4** | ADJ-01: phase-8 doc Task 8-3의 `skill-compliance-report` 실행 항목 무효화 (Phase 6 옵션 D 보류) | Step 3 |
| **D5** | ADJ-05: 각 Step 진입 시 D-MIN/D-NEED 사전 점검 (Phase 6/7 패턴) | 모든 Step |
| **D6** | 회귀 자동화는 Step 3(examples 검증)에서 자연 활성화. Step 1은 doc/spec 변경만 (회귀 대상 없음) | Step 1, 3 |
| **D7** | `migrations.json` SSOT 우선 — phase-8-release.md doc과 불일치 시 migrations.json 채택. doc 자체는 비편집 (plan.md가 결정 SSOT) | 모든 Step |
| **D14** (신규 — 후속 부채) | 통합 회귀 매트릭스 = v2.1+. `secrets-tests.yml` 합동 실행으로 현재 충분 | v2.1+ |
| **D15** (신규 — 후속 부채) | E2E 자동화 = v2.1+. v1.x 사용자 요구 발생 시 검토 | v2.1+ |

---

## ❓ Open Questions (Step 2~6 진행 시 답해야 함)

| ID | 질문 | 권장 답변 (잠정) | 확인 시점 |
|----|------|----------------|----------|
| **OQ-01** | `migrations.json` `skillProfile` 기본값 `"default"` vs phase-8 doc `"full"` 불일치 | **`"default"` 유지** (D7 적용 — migrations.json SSOT). features 안내가 *"기본값 'default'는 전체(full)와 동일"*이라 명시 — 의미상 동등 | Step 1 (본 PR 결정) |
| **OQ-02** | v2 신규 top-level 필드 5개 중 `migrations.json`에 누락된 3개 (`customDomain`, `healthCheck`, `orchestrator`) — 추가 보강 여부 + 기본값 | Step 3 examples 검증 시 v1 → v2 변환 결과가 v2 schema 통과하는지로 정합성 검증. 누락 시 migrations.json 추가 PR 필요 | Step 3 |
| **OQ-03** | branch flow 단계별 충돌 해소 PR 분리 vs 단일 PR (메모리 §주의사항: pull --rebase 권장) | v2-develop → develop은 *대규모 충돌 보장*이라 **별도 PR 권장**. develop → main은 fast-forward 가능 | Step 6 |
| **OQ-04** | `examples/` 디렉토리 `saas`, `healthcare` 도메인 부재 (현재 `fintech-gateway`, `ecommerce-shop`만). 신규 도메인 마이그레이션 검증 방식 | (옵션 A) examples 추가 = 범위 초과 위험 / **(옵션 B) 단위 fixture만 = 권장** — `tests/upgrade/fixtures/v1-{domain}-project.json` 형태로 4개 도메인 마이그레이션 검증 | Step 3 |
| **OQ-05** | v1 → v2 시뮬레이션 fixture 도입 시점 (Step 1 vs Step 3) | **Step 3** — Step 1은 plan/spec 갭만 처리. 시뮬레이션은 examples 검증과 함께 자연 흡수 | Step 1 결정 |
| **OQ-06** | `develop ↔ v2-develop` 머지 시 v1.45.x 핫픽스(서브에이전트 worktree 격리 PR #16/#18 등) 흡수 방식 | (옵션 A) v2 작업 중 주기적 develop 백머지로 흡수 / **(옵션 B) Step 6 진입 직전 일괄 백머지** — 옵션 B 권장 (충돌 영역 최소화) | Step 6 |
| **OQ-07** (신규) | Step 1에서 OQ-01만 잠정 결정하고 진행 — 추가 사용자 합의 필요 항목? | 없음 (cosmetic doc fix + plan만) | Step 1 |

> **불분명 항목 처리 원칙**: Step 1에 결정 영향 없는 OQ는 plan.md에 기록만. 진행 영향 있는 OQ는 권장 답으로 잠정 진행 후 다음 작업에서 사용자 확인.

---

## 보안/하위호환 영향

| 항목 | 영향 |
|------|------|
| 기존 v1.x 사용자 project.json | 호환성 손상 0 — `migrations.json`이 v2.0.0 자동 보강 |
| 기존 CLAUDE.md (CUSTOM_SECTION 보유) | skill-upgrade Step 13의 결정적 치환 + CUSTOM_SECTION 추출/복원으로 보존 |
| 자동 롤백 경로 | skill-upgrade `--rollback`으로 백업 시점 복원 가능 (이미 동작) |
| CI 시간 | Step 1은 doc만 → 변경 없음 |
| 로컬 dev 영향 | Step 1은 doc만 → 변경 없음 |

---

## 스텝 분리 (6 PR + 회귀 자동화 D0 — Step 3에서 활성화)

| Step | 제목 | 예상 라인 | 주요 파일 | 의존 |
|------|------|----------|---------|------|
| 1 | plan + skill-upgrade SKILL.md 갭 fix | ~280 (실제 1차 commit 214 → 리뷰 반영 후 ~270) | `docs/v2/phase-8-plan.md` (신규), `.claude/skills/skill-upgrade/SKILL.md` (갱신), `docs/v2/phase-8-release.md` (SSOT 이관 헤더) | — |
| 2 | migration-guide.md | ~200 | `docs/v2/migration-guide.md` (신규) | Step 1 |
| 3 | examples 마이그레이션 검증 + 회귀 fixture | ~400 | `examples/*/.claude/state/project.json` (수정), `tests/upgrade/fixtures/` (신규), `.github/workflows/secrets-tests.yml` (job 추가 가능) | Step 1, 2 |
| 4 | CHANGELOG v2.0.0 | ~150 | `CHANGELOG.md` | Step 3 |
| 5 | docs/upgrade-guide.md + README 본 페이지 | ~200 | `docs/upgrade-guide.md`, `README.md` | Step 4 |
| 6 | VERSION 2.0.0 + branch flow + 태그 | ~50 + 머지 commit | `VERSION`, branch ops | Step 5 |

라인 한도 500 — 모든 스텝 안전.

---

## 스텝별 상세

### Step 1: plan + skill-upgrade SKILL.md 갭 fix (PR 1, 본 PR)

**파일**:
- `docs/v2/phase-8-plan.md` (본 문서, ~270줄 — PR #45 리뷰 반영 포함)
- `.claude/skills/skill-upgrade/SKILL.md`:
  - "업데이트 대상 (프레임워크 파일)" 표에 `.claude/rules/` 행 추가 (Phase 4 도입)
  - "보존 대상 (프로젝트 파일)" 표에 `lessons-learned.json` 명시 (Phase 7 도입, `.claude/state/*` 디렉토리 전체 보존 명확화)
- `docs/v2/phase-8-release.md` (SSOT 이관 헤더 추가 — PR #45 리뷰 MAJOR #1)

**검증** (Step 1 doc만이라 회귀 자동화 없음):
- 표 갱신이 기존 동작 문장과 모순 없는지 시각 검토
- migrations.json + skill-upgrade 자동 처리는 Step 3에서 fixture로 회귀 보호

**Open Questions 기록 (위 §참조)**: OQ-01~07

### Step 2: migration-guide.md (PR 2)

**파일**:
- `docs/v2/migration-guide.md` (신규, ~200줄):
  - v1 → v2 변경 사항 요약 (CHANGELOG의 Breaking Changes 미러)
  - 자동 마이그레이션 절차 (`/skill-upgrade --version v2.0.0`)
  - 수동 확인 사항 (skillProfile 선택, 훅 활성화 여부)
  - 롤백 절차 (`/skill-upgrade --rollback`)
  - FAQ (자주 발생할 질문 5건 — schema 위반, CUSTOM_SECTION 손실, hook 작동 안함 등)

### Step 3: examples 마이그레이션 검증 + 회귀 fixture (PR 3)

**파일**:
- `examples/fintech-gateway/.claude/state/project.json` 수정 — v2 형식으로 마이그레이션 (kitVersion `2.0.0`, conventions에 `skillProfile` + `overridePriority` 추가, `hooks: {}`, `tokenHints: {}`)
- `examples/ecommerce-shop/.claude/state/project.json` 동일
- `tests/upgrade/fixtures/v1-fintech-project.json` (신규) + `v1-ecommerce-project.json`
  - **OQ-04 잠정 답**: `v1-saas-project.json` + `v1-healthcare-project.json`도 fixture로만 추가 (실제 examples 디렉토리는 미생성)
- `scripts/validate-v2-migration.py` (신규) — fixture 입력 → migrations.json 적용 → v2 schema 통과 검증
- **롤백 시뮬레이션** (R6 재평가 반영, PR #45 리뷰 MAJOR #2): `tests/upgrade/test_rollback.py` (또는 bash 스크립트) — *"v1 fixture → v2 마이그레이션 → --rollback → 원본 fixture와 일치"* 검증. ~30줄
- `.github/workflows/secrets-tests.yml`에 `validate-v2-migration` + `rollback-simulation` job 추가 (또는 별도 workflow)
- **ADJ-01 적용**: 본 Step 작업 목록에서 `skill-compliance-report` 실행 항목 무효화 (Phase 6 옵션 D 보류 사유 인용)

### Step 4: CHANGELOG v2.0.0 (PR 4)

**파일**:
- `CHANGELOG.md` `[Unreleased]` → `[2.0.0] - {릴리즈 날짜}` 섹션 완성:
  - Added: 훅, 프로파일, 토큰 힌트, rules, secrets 스캐너, ~~compliance report~~ (보류), lessons (회귀 보호 강화)
  - Changed: 4층 Layered Override, health-check 가중치
  - Breaking Changes: 스키마 확장, CLAUDE.md.tmpl 구조, 가중치 재배분

### Step 5: docs/upgrade-guide.md + README 본 페이지 (PR 5)

**파일**:
- `docs/upgrade-guide.md` v2.0.0 마이그레이션 섹션 추가 (migration-guide.md 참조 링크)
- `README.md` v2.0 신규 기능 소개 + Phase 7 lessons-learned 회귀 보호
- **OQ-04 GA UX 안내** (PR #45 리뷰 NICE): README / upgrade-guide에 *"v2.0 GA 시점 examples는 fintech-gateway / ecommerce-shop만. saas / healthcare 도메인은 fixture 단위 검증만 완료, example project는 v2.1+ 후속"* 명시

> **ADJ-04 적용**: VERSION은 본 Step에 포함하지 않음 — Step 6에서 단일 commit

### Step 6: VERSION 2.0.0 + branch flow + 태그 (PR 6 — 또는 단일 commit)

**파일/Operation**:
1. `VERSION` 파일 `2.0.0-alpha.4` → `2.0.0`
2. v2-develop → `release/v2.0.0` 브랜치 (선택) 또는 직접 develop 머지
3. develop → main 머지 (fast-forward 가능 시)
4. `v2.0.0` 태그 생성 + push
5. main 핫픽스 흡수 → develop 백머지 (메모리 §주의사항)
6. Notion 릴리스 노트 (메모리 §외부 참조 reference_notion.md 패턴)

**OQ-03 / OQ-06 결정 시점**: Step 6 진입 직전 사용자 합의 필수.

---

## 위험 및 대응

| ID | 리스크 | 확률 | 영향 | 대응 | 감지 스텝 |
|----|--------|------|------|------|-----------|
| **R1** | `migrations.json`에 v2 신규 필드 누락 (OQ-02) | 중 | 중 | Step 3 fixture 검증 시 schema 통과 못하면 즉시 보강 PR | Step 3 |
| **R2** | v2-develop ↔ develop 머지 시 대규모 충돌 (OQ-03) | 높 | 중 | OQ-03 권장: 별도 PR로 충돌 해소. v1.45.x 핫픽스를 Step 6 직전 일괄 백머지 (OQ-06) | Step 6 |
| **R3** | Phase 6 보류분이 doc 곳곳에 잔재 (compliance-report 언급) | 낮 | 낮 | Step 4 CHANGELOG / Step 5 README에서 명시 제거 (~~compliance report~~ 표기) | Step 4, 5 |
| **R4** | examples saas/healthcare 부재로 v2 마이그레이션 검증 부분적 (OQ-04) | 중 | 낮 | 권장: 단위 fixture만 (실제 examples 디렉토리 추가는 v2.1+ 후속) | Step 3 |
| **R5** | VERSION 변경 후 main 머지 실패 (CI/충돌) | 중 | 높 | Step 6를 마지막에 위치시키고 모든 Step 완료 + CI 그린 확인 후 진입 | Step 6 |
| **R6** (재평가, PR #45 리뷰 MAJOR #2) | skill-upgrade `--rollback` 동작 검증 부재 — 사용자 데이터 손실 + 평판 리스크 | 낮 | **높** (중→상향) | (i) Step 3 fixture에 **롤백 시뮬레이션 1건 추가** — *"v2 마이그레이션 → --rollback → 원본과 동일"* (~30줄). (ii) Step 2 migration-guide.md FAQ에 매뉴얼 테스트 절차 명시. *"구현됨 ≠ 검증됨"* — v1.x 시기 실사용 사례 미상 | Step 3 (필수) + Step 2 (보조) |

---

## 진행 방식 권장

1. Step 1 머지 → plan SSOT 활성화 + skill-upgrade doc 갭 해소
2. Step 2 머지 → 사용자 가이드 확보
3. Step 3 머지 → examples + fixture 회귀 보호 활성화 (D0 적용점)
4. Step 4 머지 → CHANGELOG GA 준비
5. Step 5 머지 → 외부 사용자 진입점 갱신
6. Step 6 진입 직전 OQ-03/OQ-06 사용자 합의 → VERSION + branch flow + 태그 단일 commit/PR
7. v2.0.0 GA 외부 공개 → develop은 v1.x 핫픽스 라인으로 동결

---

## 참고

- 상위 plan: [phase-8-release.md](./phase-8-release.md)
- 진입 합의: [PR #44 코멘트](https://github.com/wejsa/ai-crew-kit/pull/44#issuecomment-4363971097) — ADJ-01~06
- 메커니즘 SSOT: [`schemas/migrations.json`](../../.claude/schemas/migrations.json) (D7)
- 마이그레이션 흐름: [`skills/skill-upgrade/SKILL.md`](../../.claude/skills/skill-upgrade/SKILL.md)
- Phase 7 패턴 참조: [phase-7-plan.md](./phase-7-plan.md)
- 메모리 §릴리스 프로세스 / §주의사항 참조 (Co-Author 노트, pull --rebase)
