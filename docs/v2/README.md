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
