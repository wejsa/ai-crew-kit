# Phase 7 Lean Closure — 사용자 마이그레이션 가이드

> **상위 계획**: [phase-7-context.md](./phase-7-context.md) — 옵션 A 진행 결정
> **상세 계획**: [phase-7-plan.md](./phase-7-plan.md) — D1~D9 결정 + Step 1/2

## 무엇이 바뀌나

Phase 7은 v1.23.0(2026-03-05)에 이미 구현된 `lessons-learned` 메커니즘의 **회귀 보호 갭**만 메운다. 신규 콘텐츠 0개. v1.23+ 사용자가 v2.0 GA로 업그레이드해도 **기존 동작은 변경되지 않으며**, 다음 4가지가 추가된다.

### 1. schema 자동 검증 — `.claude/schemas/lessons-learned.schema.json`

`lessons-learned.json` 구조가 JSON Schema Draft 7로 명문화. CI(`validate-lessons-learned`)가 변경 시마다 검증.

| 항목 | 강제도 | 비고 |
|------|-------|------|
| `id` 패턴 `^L-\d{3,}$` | 필수 | v1.23 형식 그대로 |
| `category` enum | 필수 | quality / performance / architecture / process / security |
| `impact` enum | 필수 | high / medium / low |
| `appliedCount` ≥ 1 | 필수 | v1.23은 1부터 시작 (생성 시 1) |
| `additionalProperties` | 금지 | v2.1+ 신규 필드는 schema 갱신 동반 |
| `metadata.schemaVersion` | 선택 | 미설정 시 1.0.0 가정 (v2.1+ 멀티 버전 분기 후속) |

기존 `lessons-learned.json`은 v1.23 구조 그대로 정의되어 **호환성 손상 0**. 단, 사용자가 수동 편집한 변형 구조가 있으면 schema 위반으로 CI FAIL 발생 가능 — 이 경우 [`scripts/validate-lessons-learned.py`](../../scripts/validate-lessons-learned.py)를 로컬에서 실행해 진단.

### 2. 저장 시 secrets 필터 — skill-retro §5.3

회고에서 추출된 lesson `description`이 SEC-S01~S05(API 키 / 시크릿 / AWS / GitHub PAT / Slack 토큰) 정규식과 매칭되면 **skill-retro가 AskUserQuestion으로 사용자에게 결정을 묻는다**.

```
⚠ lesson L-042 description에 SEC-S01(API 키 하드코딩) 매칭됨:
  "...api_key='AbCd1234...' 패턴 위험..."

선택:
  [거부]      이 lesson을 저장하지 않음 (default)
  [마스킹]    매칭 부분을 ***MASKED-SEC-S01***으로 치환 후 저장
  [강행]      안티패턴 예시 등 의도된 인용. 그대로 저장 (사용자 책임)
```

비대화형 환경(AskUserQuestion 불가)은 **자동 거부** + execution-log에 경고 기록.

> **왜 정적 차단이 아닌가**: SEC-S01~S05가 모두 `excludeContexts: ["comment"]` 보유 — lesson description은 본질적으로 코멘트성 텍스트라 안티패턴 *예시 코드*에서 false positive 다발 가능. 사용자가 이를 의도적 인용으로 판단할 수 있어야 한다 (옵션 A D2 개정).

### 3. impact 임계값 정량 표시 — `--lessons list/top`

기존 `impact` 단순 출력에서 권장값 정량 비교가 추가된다.

```diff
  | ID    | 제목                 | 영향도          | 적용 횟수 |
  | ----- | -------------------- | --------------- | --------- |
- | L-001 | 결제 nullable 누락   | high            | 7         |
+ | L-001 | 결제 nullable 누락   | high            | 7         |
- | L-002 | 캐시 TTL 부주의      | low             | 6         |
+ | L-002 | 캐시 TTL 부주의      | low (권장: high)| 6         |
```

권장 임계값(SSOT는 `lessons-learned.schema.json` description):
- `appliedCount >= 5` → **high** 권장
- `>= 3` → **medium** 권장
- `< 3` → **low** 권장

현재 impact가 권장과 다른 경우만 `(권장: Y)` 표기. 사용자가 의도적으로 override 가능 — 강제 변경 X.

### 4. 메타 레포 / 신규 프로젝트 graceful

`.claude/state/lessons-learned.json` 부재 시 `validate-lessons-learned.py`는 **graceful skip(exit 0)**. 신규 프로젝트가 첫 회고 전까지 CI 영향 없음.

---

## v1.23+ 사용자 행동 항목

대부분의 경우 **추가 작업 없음**. 다음 항목만 확인 권장:

1. **schema 위반 사전 점검**: `python3 scripts/validate-lessons-learned.py` 한 번 실행. 위반 시 안내 따라 수정.
2. **수동 편집한 lesson 검토**: title/description 등에 우연히 secrets 패턴 박혀있으면 다음 회고 저장 시 AskUserQuestion 발생.
3. **CI 게이트 인지**: PR 머지 전 `validate-lessons-learned` job 통과 확인.

---

## v2.1+ 보류 항목 (재진입 조건 도래 시 부활)

| 보류 항목 | 재진입 조건 |
|----------|-----------|
| **contextSnapshot** (workflowState 컨텍스트 캐싱) | 토큰 비용 메트릭 측정 후 절감 잠재성 정량 검증 |
| **skill-create `--from-history`** (git log 패턴 추출) | 사용자 요구 발생 |
| **lessons 도메인별 파일 분리** | 도메인 변경 시 lessons 오염 사례 1건 이상 발생 |
| **schema multi-version 분기** (`schemaVersion` 활용) | contextSnapshot/from-history 부활 시 한번에 도입 (D9) |

---

## 참고

- skill-retro SSOT: [`.claude/skills/skill-retro/SKILL.md`](../../.claude/skills/skill-retro/SKILL.md)
- skill-plan 학습 참조: [`.claude/skills/skill-plan/SKILL.md`](../../.claude/skills/skill-plan/SKILL.md) §"과거 학습 반영"
- secrets-patterns SSOT: [`_base/health/secrets-patterns.json`](../../.claude/domains/_base/health/secrets-patterns.json)
- v1.23.0 릴리스 노트: 단일 파일 + `tags` 도메인 구분 + `appliedCount` 누적 도입 시점
