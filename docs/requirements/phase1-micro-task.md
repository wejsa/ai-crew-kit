# Phase 1-1: 경량 경로 (Micro Task) 상세 요구사항

> 작성일: 2026-04-01
> 테마: "버튼 하나 고치는데 풀 사이클은 과잉"
> 상위 문서: [개선 로드맵](../roadmap-universal-access.md) §4.1

---

## 1. 개요

| 항목 | 내용 |
|------|------|
| **문제** | 파일 1~3개, ~100줄 수정에 feature → plan → impl 풀 사이클 강제 |
| **해결** | 규모별 자동 분기 + `--micro` 옵션으로 plan 생략 경로 |
| **변경 파일** | skill-impl/SKILL.md, skill-backlog/SKILL.md, CLAUDE.md.tmpl |
| **스키마 변경** | 없음 (task.type은 Phase 0에서 추가 완료) |

---

## 2. 규모 분류 기준

| 규모 | 파일 수 | 예상 라인 | 경로 |
|------|---------|----------|------|
| **Micro** | ≤ 3개 | ~100줄 | impl → PR → Trivial 리뷰 |
| **Standard** | 4~10개 | 100~1000줄 | feature → plan → impl → review → merge (현재) |
| **Large** | 10개+ | 1000줄+ | Phase 분리 + 멀티 Task (현재) |

---

## 3. Micro 경로 상세

### 3.1 진입 방식

**A. 명시적**: `/skill-impl --micro "버그 설명 또는 작업 내용"`

**B. 자연어 자동 판단**:
- "OO 고쳐줘" / "OO 버그 수정해줘" → 규모 추정 → Micro 판단 시 자동 전환
- "OO 추가해줘" + 명백히 소규모 → Micro 제안
- 판단 기준: 사용자 설명에서 영향 파일/범위 추정, 확신 못 하면 Standard

**C. skill-feature에서 분기**:
- `/skill-feature "버그명"` 실행 시, AI가 규모를 추정
- Micro로 판단되면: "이 작업은 소규모(~N줄)로 보입니다. Micro 경로로 진행할까요?"
- 사용자 확인 후 Micro 경로 전환

### 3.2 Micro 경로 워크플로우

```
/skill-impl --micro "설명"
  │
  ├── 1. backlog에 간소화 Task 자동 등록
  │     - type: AI 추론 (bug/chore/feature)
  │     - priority: AI 추론
  │     - steps: [{number: 1, title: "Micro 구현", status: "pending"}]
  │     - status: in_progress, assignee 설정
  │
  ├── 2. plan 생략 — 계획 파일 미생성
  │     - 사전 조건에서 "계획 파일 존재" 체크 면제
  │
  ├── 3. 코드 구현 (현재 skill-impl Step 3과 동일)
  │
  ├── 4. 라인 수 검증 — Micro 전용 제한
  │     - ≤ 150줄: 정상 진행
  │     - 150~300줄: 경고 "Micro 범위를 초과합니다. Standard로 전환할까요?"
  │     - > 300줄: 차단 "Standard 경로가 필요합니다. /skill-plan 실행"
  │
  ├── 5. 빌드 & 테스트 (현재와 동일)
  │
  ├── 6. 커밋 & PR 생성
  │     - 커밋: `fix: {taskId} - {설명}` (type은 AI 추론)
  │     - PR: `--base develop`
  │
  └── 7. Trivial 리뷰 자동 적용
        - 리뷰 경로: skill-review-pr Trivial Fast Path 조건 매칭 시 경량 리뷰
        - 조건 미매칭 시 (src/ 변경 등): 일반 리뷰로 폴백
```

### 3.3 Micro에서 생략되는 것

| 항목 | Standard | Micro |
|------|----------|-------|
| skill-feature (요구사항 문서) | 필수 | 생략 |
| skill-plan (설계 + 스텝 분리) | 필수 | 생략 |
| 계획 파일 (.claude/temp/) | 생성 | 미생성 |
| backlog 등록 | 필수 | 자동 (간소화) |
| 빌드/테스트 | 필수 | 필수 (동일) |
| PR 생성 | 필수 | 필수 (동일) |
| 코드 리뷰 | 일반 | Trivial 우선, 폴백 가능 |

### 3.4 Micro Task의 backlog 레코드

```json
{
  "id": "TASK-005",
  "title": "검색 결과 빈 페이지 수정",
  "type": "bug",
  "status": "in_progress",
  "priority": "medium",
  "phase": 1,
  "steps": [{"number": 1, "title": "Micro 구현", "status": "pending", "files": []}],
  "currentStep": 1,
  "micro": true,
  "createdAt": "...", "updatedAt": "..."
}
```

`micro: true` 필드로 Micro Task 식별. skill-report에서 Micro 비율 집계.

---

## 4. skill-impl 변경사항

### 4.1 사전 조건 분기

```
--micro 옵션 시:
  ✅ 1. project.json 존재
  ✅ 2. backlog.json 존재 + 유효 JSON
  ⬜ 3. in_progress Task 존재 → Micro가 자동 생성
  ⬜ 4. 계획 파일 존재 → 면제
  ✅ 5. origin/develop 동기화
```

### 4.2 argument-hint 갱신

```
argument-hint: "[--next|--all|--retry|--skip|--micro \"설명\"]"
```

---

## 5. CLAUDE.md.tmpl 자연어 매핑 추가

| 자연어 | 스킬 | 동작 |
|--------|------|------|
| "OO 고쳐줘" | `/skill-impl --micro "OO"` | 규모 자동 판단 → Micro/Standard |
| "OO 버그 수정해줘" | `/skill-impl --micro "OO"` | bug type으로 Micro |
| "간단하게 OO 추가해줘" | `/skill-impl --micro "OO"` | Micro 경로 |

---

## 6. Out of Scope

| 항목 | 사유 |
|------|------|
| Micro Task 전용 리뷰 스킬 | 기존 Trivial Fast Path로 충분 |
| Large 경로 자동화 | Phase 분리는 수동 판단 필요 (Phase 2) |
| Micro에서 멀티 파일 잠금 | ≤3 파일이므로 충돌 가능성 낮음 |

---

## 7. 검증 기준

- [ ] `--micro "설명"` 시 plan 없이 구현 → PR 생성
- [ ] backlog에 간소화 Task 자동 등록 (type AI 추론)
- [ ] 150줄 초과 시 Standard 전환 경고
- [ ] 300줄 초과 시 차단 + /skill-plan 안내
- [ ] Trivial 리뷰 조건 매칭 시 경량 리뷰 적용
- [ ] Trivial 미매칭 시 일반 리뷰 폴백
- [ ] 기존 --next/--all/--retry/--skip 동작 유지
- [ ] skill-report에서 Micro Task 비율 집계 가능
- [ ] 자연어 "OO 고쳐줘" → Micro 판단 동작
