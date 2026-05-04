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

**자주 발생할 위반 사례 + 수정**:

| 위반 | 예 | 수정 |
|------|----|------|
| `id` 자릿수 부족 | `"id": "L-1"` | `"id": "L-001"` (3자리 이상) |
| `category` enum 위반 | `"category": "bug"` | quality / performance / architecture / process / security 중 선택 |
| `impact` enum 위반 | `"impact": "ultra"` | high / medium / low 중 선택 |
| `appliedCount` 0 이하 | `"appliedCount": 0` | `1` 이상 (최초 추출 시 1) |
| 임의 필드 추가 | `"customField": "..."` | schema 미정의 필드 제거 또는 v2.1+ schema 갱신 동반 |

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

**옵션은 lesson 단위로 적용** (다중 패턴 매칭 시 모두 표시 후 단일 옵션 선택 — 개별 패턴 선택 불가).

**마스킹 결과 예시**:
```
원본:    결제 시 api_key=AbCd1234567890xyz 노출 위험
마스킹:  결제 시 api_key=***MASKED-SEC-S01*** 노출 위험
```

**거부 영속성**: 거부된 lesson은 `execution-log.json`에 `lesson_rejected_secrets` 이벤트로 기록되며, dedup key(`title+category`)로 다음 회고 시 동일 lesson 재출현하면 자동 재거부 — 매번 묻지 않음.

**강행 저장은 CI도 통과**: 사용자가 [강행]을 선택한 lesson은 `lessons-learned.json`에 그대로 저장되고 `validate-lessons-learned` CI도 통과. Step 1 D2 개정으로 secrets 검사 책임이 skill-retro 레이어로 일원화돼 *의도된 인용*과 *실수 누출*을 사용자가 단일 시점에 판단.

⚠️ **비대화형 환경 사용자 주의**: `CI=true` 또는 stdout 비-TTY 환경(예: CI가 자동으로 `/skill-retro` 호출)에서는 AskUserQuestion 불가 → **자동 거부** + `execution-log`에 `lesson_rejected_secrets_noninteractive` 기록. 학습 손실 가능성 있음 — 정기 검토 권장.

**기존 lessons에 박힌 secrets 처리**: 본 필터는 *신규 lesson 저장 시점*에만 작동. v1.23+ 사용자가 이미 누적한 lessons에 secrets가 박혀 있어도 자동 마스킹/거부되지 않는다. 필요 시 수동 grep + 수정:

```bash
grep -nE '(api[_-]?key|secret|AKIA|ghp_|xox[bp]-)' .claude/state/lessons-learned.json
```

전수 일괄 처리 도구는 v2.1+ Backfill 후보로 보류 (실수요 발생 시 도입).

> **왜 정적 차단이 아닌가**: SEC-S01~S05가 모두 `excludeContexts: ["comment"]` 보유 — lesson description은 본질적으로 코멘트성 텍스트라 안티패턴 *예시 코드*에서 false positive 다발 가능. 사용자가 이를 의도적 인용으로 판단할 수 있어야 한다 (옵션 A D2 개정).

### 3. impact 임계값 정량 표시 — `--lessons list/top`

기존 `impact` 단순 출력에서 권장값 정량 비교가 추가된다. **권장과 일치 시 `(권장: Y)` 표기 생략** — 표 가독성 우선, 변화는 *override가 발생한 행*에만 표시.

권장 임계값(SSOT는 `lessons-learned.schema.json` description):
- `appliedCount >= 5` → **high** 권장
- `appliedCount >= 3` → **medium** 권장
- `appliedCount < 3` → **low** 권장

표기 예 (권장과 다른 행만 변화):

```
| ID    | 제목                | 영향도            | 적용 횟수 |
| ----- | ------------------- | ----------------- | --------- |
| L-001 | 결제 nullable 누락  | high              | 7         |
| L-002 | 캐시 TTL 부주의     | low (권장: high)  | 6         |   ← override 발생
```

사용자가 의도적으로 override 가능 — 강제 변경 X. impact를 권장과 맞추고 싶으면 `--lessons` 명령으로 직접 편집.

### 4. 메타 레포 / 신규 프로젝트 graceful

`.claude/state/lessons-learned.json` 부재 시 `validate-lessons-learned.py`는 **graceful skip(exit 0)**. 신규 프로젝트가 첫 회고 전까지 CI 영향 없음.

---

## v1.23+ 사용자 행동 항목

대부분의 경우 **추가 작업 없음**. 다음 항목만 확인 권장:

1. **schema 위반 사전 점검**: `python3 scripts/validate-lessons-learned.py` 한 번 실행. 위반 시 위 §1 표 따라 수정.
2. **수동 편집한 lesson 검토**: title/description 등에 우연히 secrets 패턴 박혀있으면 다음 회고 저장 시 AskUserQuestion 발생.
3. **CI 게이트 인지**: PR 머지 전 `validate-lessons-learned` + `lessons-fixture-tests` job 통과 확인.

### CI 실패 시 로컬 재현

```bash
# schema + cross-ref 검증 (메타 레포는 graceful skip)
python3 scripts/validate-lessons-learned.py

# fixture 단건 검증 (CI 4단계 중 하나)
python3 scripts/validate-lessons-learned.py --fixture tests/lessons/fixtures/sample-valid.json

# pytest 회귀 (Step 2 머지 후)
pytest tests/lessons -v
```

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
