# AI Crew Kit v2.0.0 개발 계획서

> **브랜치**: `v2-develop` (develop에서 분기)
> **목표**: ECC 기능 차용 기반 차세대 프로세스 프레임워크
> **원칙**: ACK 미니멀리즘("Claude가 이미 아는 것은 가르치지 않는다") 유지

---

## 버전 전략

| 태그 | 포함 Phase | 성격 |
|------|-----------|------|
| `v2.0.0-alpha.1~N` | Phase 0~3 (P0 Quick Win) | 구조 변경 |
| `v2.0.0-beta.1~N` | Phase 4~6 (P1 Big Bet) | 콘텐츠 확장 |
| `v2.0.0-rc.1~N` | Phase 7~8 (P2 Fill-in + Release) | 안정화 |
| `v2.0.0` | 전체 | 정식 릴리즈 |

## 브랜치 전략

```
main ──────────────────────────────────────→ (안정)
  │
  └── develop ──┬── v1.45.x hotfix (유지보수)
                │
                └── v2-develop ──┬── feature/phase-0-foundation
                                 ├── feature/phase-1-hooks
                                 ├── feature/phase-2-profiles
                                 ├── ...
                                 └── v2.0.0 → main merge + tag
```

- `develop`: v1.x 핫픽스 전용. 신규 기능 금지.
- `v2-develop`: v2 기능 개발. feature 브랜치에서 머지.
- `develop → v2-develop`: 주기적 머지 (v1.x 수정 반영)
- 보안 패치: v1.x + v2 양방향 백포트

---

## Phase 의존성 맵

```
Phase 0 (Foundation)
  ├── Phase 1 (Hooks) ─────────────┐
  ├── Phase 2 (Profiles) ──────────┤
  └── Phase 3 (Token) ─────────────┤
                                    ▼
                              Phase 4 (Rules) ← Phase 0
                              Phase 5 (Security) ← Phase 0 + 1
                              Phase 6 (Compliance) ← Phase 5
                                    │
                                    ▼
                              Phase 7 (Context) ← Phase 1 + 4
                              Phase 8 (Release) ← 전체
```

- Phase 1, 2, 3은 **병렬 가능** (Phase 0 완료 후)
- Phase 4는 Phase 0 의존 (H001: Phase 2 의존 근거 불명확 → 제거. rules 로드는 프로파일과 독립)
- Phase 5는 Phase 0 + 1 의존 (훅이 보안 스캔 트리거)
- Phase 6은 Phase 5 의존 (보안 데이터 기반 리포트)
- Phase 7은 Phase 1 + 4 의존
- Phase 8은 전체 의존

---

## Phase 목록

| Phase | 이름 | 문서 | 우선순위 |
|-------|------|------|---------|
| 0 | Foundation | [phase-0-foundation.md](./phase-0-foundation.md) | P0 |
| 1 | Native Hooks | [phase-1-hooks.md](./phase-1-hooks.md) | P0 |
| 2 | Skill Profiles | [phase-2-profiles.md](./phase-2-profiles.md) | P0 |
| 3 | Token Optimization | [phase-3-token.md](./phase-3-token.md) | P0 |
| 4 | 4-Layer Override + Rules | [phase-4-rules.md](./phase-4-rules.md) | P1 |
| 5 | AgentShield-lite | [phase-5-security.md](./phase-5-security.md) | P1 |
| 6 | Compliance Report | [phase-6-compliance.md](./phase-6-compliance.md) | P1 |
| 7 | Context & Learning | [phase-7-context.md](./phase-7-context.md) | P2 |
| 8 | Migration & Release | [phase-8-release.md](./phase-8-release.md) | P2 |

---

## 📍 진행 상황 (Single GA Strategy, 2026-04-30~)

> **전략 변경 (2026-04-30 합의)**: alpha.N 태그는 **외부 릴리스가 아닌 인터널 마일스톤**. 사용자는 v2.0.0 GA만 install하므로 모든 Phase 산출물이 alpha.1 ↔ GA 누적 회귀 보존되어야 한다. 따라서 각 Phase fixture는 작성자 로컬에 머무르지 않고 **CI로 자동화**되어야 GA 안전성이 확보된다. alpha.4 등 인터널 태그는 생성하지 않는다.

| Phase / 트랙 | 상태 | 머지 SHA | 비고 |
|-------------|------|---------|------|
| 0 — Foundation | ✅ | alpha.1 (VERSION 파일만) | schema 확장 |
| 1 — Native Hooks | ✅ | alpha.2 packed | 5 hooks + atomic-write + HI-01~04 + CI `hook-tests` |
| 2 — Skill Profiles | ✅ | alpha.2 backfill | 추가 작업 없음 |
| 3 — Token Optimization | ✅ | alpha.2 backfill | 추가 작업 없음 |
| 4 — Layered Override + Rules | ✅ | alpha.3 packed | 메커니즘 + 0개 콘텐츠 (옵션 A) |
| 5 — AgentShield-lite | ✅ | alpha.4 packed (`6cf43c9`) | secrets-patterns + SEC-05/06/07 + 도메인 패턴 + migration |
| **트랙 A — 회귀 자동화** | ✅ | `8b1b628` | secrets-patterns schema + fixture pytest 89 + 14 메타 + cross-ref + `_category` 가중치 + SSOT drift 메타 + 5 jobs CI ([phase-5-tests-plan.md](./phase-5-tests-plan.md)) |
| **6 — Compliance Report** | ⏳ **다음** | — | skill-compliance-report 신규 + fintech 우선 (PCI-DSS / 전자금융감독규정) |
| 7 — Context & Learning | ⏳ | — | Phase 1+4 의존 |
| 8 — Migration & Release (GA) | ⏳ | — | **GA 검증 게이트** — 통합 회귀 매트릭스 + skill-upgrade v1→v2 시뮬레이션 + E2E |

**현재 v2-develop HEAD**: `8b1b628` (PR #42 트랙 A Step 3)
**현재 VERSION**: `2.0.0-alpha.4` (인터널)
**현재 활성 CI**: `hook-tests` / `schema-validation` / `secrets-tests` (4 jobs) — 총 6 CI checks

### 🔄 다른 세션에서 재개 시 프롬프트

새 세션 진입 시 다음 프롬프트로 시작:

```
docs/v2/README.md §진행 상황과 docs/v2/phase-6-compliance.md 읽고
Phase 6 (Compliance Report) 착수해줘.

전제 조건:
- v2.0 단일 GA 전략(2026-04-30 합의)이라 alpha 태그 외부 릴리스 없음
- Phase 5 + 트랙 A 회귀 자동화 완료 (v2-develop HEAD 8b1b628)
- 인터널 VERSION은 alpha.4지만 태그 미생성, 인터널 마일스톤만

권장 진행 방식:
1. TFT 5인 분석 (Phase 5 패턴 참조)
2. D0급 결정으로 "각 산출물 회귀 테스트 자동화는 산출물 PR과 동시 또는 즉시 후속"
   사전 확정 (트랙 A 패턴 일반화)
3. 옵션 A/B/C 비교 후 사용자 합의
4. plan.md 작성 → 4 스텝 PR 진행
```

### Phase 6 진입 시 권장 D0급 결정 (사전 확정)

| ID | 결정 사항 | 근거 |
|----|-----------|------|
| D0 | 산출물 회귀 테스트 자동화는 PR과 동시 또는 즉시 후속 | 트랙 A 사후 마이그레이션 비용 ↑, 단일 GA 안전성 |
| H004 (선결) | 데이터 수집 방식: 역추적(git log + PR 메타) vs 실시간 수집 | phase-6-compliance.md §Security Lead 분석 |
| MVP 도메인 | fintech 우선 (PCI-DSS / 전자금융감독규정) | phase-6-compliance.md §범위 경계 |
| 출력 형식 | JSON (PDF는 v2.1+) | phase-6-compliance.md §범위 경계 |

### 핵심 컨텍스트 파일 (다른 세션 진입 시 우선 읽기)

| 파일 | 역할 |
|------|------|
| `docs/v2/README.md` (본 문서) | Phase 목록 + 진행 상황 SSOT + 재개 프롬프트 |
| `docs/v2/phase-6-compliance.md` | Phase 6 상위 계획 (TFT 분석 가이드 포함) |
| `docs/v2/phase-5-tests-plan.md` | 트랙 A 3 스텝 패턴 — Phase 6 회귀 자동화 D0 참고 |
| `docs/v2/security-migration.md` | Phase 5 사용자 가이드 (Phase 6 마이그레이션 패턴 참조) |
| `.github/workflows/secrets-tests.yml` | 트랙 A CI workflow 패턴 (4 jobs 분리) |
| `.claude/state/project.json` | (메타 레포라 부재) — 일반 프로젝트는 도메인/techStack SSOT |

### 작업 체이닝 패턴 (Phase 5 패턴 일관)

각 Phase는 일반적으로 다음 흐름:
1. Step 0 — TFT 분석 + 옵션 결정 (설계 문서, PR 없음)
2. Step 1 — 핵심 메커니즘 + plan.md
3. Step 2 — 통합/확장
4. Step 3 — 콘텐츠 (도메인별)
5. Step 4 — migration/CHANGELOG/VERSION (인터널 — 외부 릴리스 X)
6. (선택) 트랙 X — 회귀 자동화 (각 Phase 산출물별)

각 PR 머지 후:
- 별도 chore commit으로 plan.md 진행 상황 테이블 갱신
- README.md (본 문서) §진행 상황 표 갱신 (Phase 완료 시)

---

## 절대 금지 항목 (TFT 만장일치)

| 기능 | 금지 사유 |
|------|----------|
| 멀티 하네스 (Cursor/Codex/OpenCode) | SSOT 훼손, 설정 동기화 비용 > 이득 |
| `/plugin install` 배포 | 버전 파편화, monolithic 정체성 훼손 |
| Rust control-plane | 불필요한 런타임 스택 추가 |
| GUI Dashboard (Tkinter) | CLI 우선, `/skill-backlog dashboard`로 충분 |
| 언어 튜토리얼성 rules | "Claude가 이미 아는 것" 원칙 위배 |
| Instinct v2 풀버전 | 세션 간 모델 튜닝 = 철학 충돌 |

---

## 구현 프로세스 (모든 Phase 공통)

각 Phase의 "구현해줘" 요청 시, 다음 3단계를 **반드시 순서대로** 실행한다:

### Step 1: TFT 분석/설계 (구현 전)

Phase별 계획서에 명시된 **TFT 분석 가이드**에 따라 5인 TFT를 소집한다:

| 역할 | 분석 범위 |
|------|----------|
| **Architect** | 구조적 정합성, Layered Override 영향, 기술 부채 |
| **Security Lead** | 보안 영향, 훅 인젝션 표면, 컴플라이언스 연동 |
| **DX Lead** | 사용자 흐름 변경, 온보딩 영향, CLI UX |
| **Product Lead** | 범위 통제, 미니멀리즘 원칙 준수 여부, 우선순위 조정 |
| **Domain Lead** | 도메인 구조 영향, 컨벤션 로드 순서, 교차 체크리스트 |

TFT 분석 결과물:
- 세부 요구사항 명세 (입력/출력/제약)
- 수정 파일별 변경 사양
- 엣지 케이스 목록
- 마이그레이션 영향도

**필수 절차 (H012~H016 대응)**:
- 각 Phase에서 **실패/에러 시나리오 최소 2개**를 TFT가 도출할 것
- 성공 기준에 happy path뿐 아니라 **실패 시 복구 동작**을 1개 이상 포함할 것
- 미결 결정 사항에는 **권장안 + 불일치 시 영향도**를 반드시 명시할 것

### Step 2: 설계 확정

TFT 분석 결과를 기반으로:
- 파일별 변경 diff 초안 확정
- 테스트 시나리오 정의 (정상 + **실패/경계값** 시나리오 필수 포함)
- 하위호환 검증 계획

### Step 3: 구현

확정된 설계에 따라 코드 작성 → 커밋 → 푸시.

> **원칙**: Step 1~2 없이 Step 3으로 직행하지 않는다.
> **원칙**: TFT가 "범위 초과"로 판단한 항목은 해당 Phase에서 제외하고 후속 Phase로 이관한다.

---

## Breaking Changes 요약 (v1.x → v2.0.0)

| 변경 | 영향 | 마이그레이션 |
|------|------|------------|
| `project.schema.json` 새 필드 추가 | `additionalProperties: false`로 인해 구버전 스킬이 신버전 project.json 거부 | skill-upgrade v2 |
| 4층 Layered Override | conventions 로드 순서 변경 | 기존 2층은 기본값으로 호환 |
| health-check 가중치 재배분 | 기존 점수와 차이 발생 | 마이그레이션 가이드에 매핑표 |
| CLAUDE.md.tmpl 구조 변경 | 세션 시작 프로토콜 변경 | skill-upgrade가 CLAUDE.md 재생성 |
| settings.json hooks 필드 | 구조 확장 | 없으면 기존 동작 유지 (graceful) |
