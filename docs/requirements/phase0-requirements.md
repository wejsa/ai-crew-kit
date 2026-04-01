# Phase 0 (v1.37.0) 상세 요구사항

> 작성일: 2026-03-31 (v2 재작성)
> 테마: "막히는 지점을 없앤다"
> 대상: 개발자 (시니어~주니어) + 개발 지식이 있는 PM/테크리드
> 상위 문서: [개선 로드맵](../roadmap-universal-access.md)

---

## 목차

1. [REQ-1: 에러 복구 가이드](#1-req-1-에러-복구-가이드)
2. [REQ-2: 대화형 백로그 관리](#2-req-2-대화형-백로그-관리)
3. [REQ-3: getting-started 워크스루 보강](#3-req-3-getting-started-워크스루-보강)
4. [스키마 변경 요약](#4-스키마-변경-요약)
5. [구현 순서](#5-구현-순서)
6. [Out of Scope](#6-out-of-scope)
7. [검증 기준](#7-검증-기준)

---

## 1. REQ-1: 에러 복구 가이드

### 1.1 개요

| 항목 | 내용 |
|------|------|
| **배치 위치** | CLAUDE.md.tmpl에 "에러 복구 프로토콜" 섹션 인라인 (~25줄) |
| **대상 스킬** | skill-impl, skill-plan, skill-review-pr, skill-merge-pr, skill-backlog |
| **참조 방식** | 각 SKILL.md에 `CLAUDE.md "에러 복구 프로토콜" 참조` 1줄 + fallback |
| **신규 옵션** | `skill-impl --retry`, `skill-impl --skip` |
| **스키마 변경** | step.status enum에 `"skipped"` 추가 |

### 1.2 에러 출력 표준 형식

```
❌ [{에러 유형}]: {구체적 원인}

📋 현재 상태:
   - Task: {TASK-ID} Step {N}/{M}
   - 브랜치: {현재 브랜치}
   - 마지막 성공 지점: {단계명}

🔧 복구 방법:
   1. [권장] {가장 안전한 방법}
   2. {대안 방법}
   3. [최후수단] {리셋 방법}
```

### 1.3 에러 유형 → 복구 매핑 (10가지)

| # | 에러 유형 | 자동 복구 | 수동 복구 |
|---|----------|----------|----------|
| 1 | **빌드 실패 (1-2회)** | 자동 재시도 | - |
| 2 | **빌드 실패 (3회)** | - | [권장] 에러 로그 보고 수정 후 "이어서 진행해줘" / `--retry` / [최후수단] `--skip` |
| 3 | **JSON 파싱 에러** | `git checkout` 복원 시도 | [권장] 자동 복원 수락 / 에러 위치 안내 후 수동 수정 |
| 4 | **Git push 충돌** | `pull --rebase` 자동 시도 | [권장] 자동 rebase 수락 / 충돌 파일 수동 해결 |
| 5 | **PR 생성 실패** | 원인별 분기 | [권장] `gh auth status` 확인 / 네트워크 재시도 |
| 6 | **gh auth 만료** | `gh auth refresh` 안내 | [권장] `! gh auth refresh` 실행 |
| 7 | **워크플로우 중단 (세션 끊김)** | intent 기반 자동 복구 제안 | [권장] `/skill-status` 후 안내 따르기 / 수동 상태 초기화 |
| 8 | **lock TTL 만료** | 자동 연장 제안 | [권장] 연장 수락 / `--extend-lock` / [최후수단] `unlock --force` |
| 9 | **컨텍스트 압축 후 맥락 소실** | workflowState에서 현재 상태 복원 | [권장] `/skill-status` → 자동 맥락 복원 |
| 10 | **subagent 타임아웃** | 스킵하고 계속 진행 | [권장] 결과 없이 진행 수락 / 수동 재실행 |

### 1.4 --retry 옵션

```
/skill-impl --retry
```

**동작**:
1. 현재 스텝의 `step.status`를 `"pending"`으로 리셋
2. feature 브랜치 처리:
   - PR OPEN → close + 브랜치 삭제
   - PR MERGED → retry 거부 ("이미 머지된 스텝은 retry 불가")
   - PR 없음 → 브랜치 삭제
3. `workflowState.currentSkill` → `"skill-impl"` 리셋
4. `workflowState.fixLoopCount` → 0 리셋
5. skill-impl 정상 플로우 재실행

**제약**: skill-impl 실패 시에만 사용 가능

### 1.5 --skip 옵션

```
/skill-impl --skip
```

**동작**:
1. 경고: "Step {N}을 스킵합니다. 이후 스텝에서 빌드 실패가 발생할 수 있습니다."
2. 사용자 확인
3. `step.status` → `"skipped"`
4. `currentStep` +1
5. 다음 스텝 실행 또는 Task 완료 처리

**제약**:
- 빌드 실패 상태에서만 사용 가능 (정상 흐름에서는 불가)
- skill-report에서 "스킵된 스텝" 메트릭으로 집계

### 1.6 --skip 후 --next/--all 호환성

`--skip`으로 스텝을 건너뛴 후, 후속 스킬이 정상 동작해야 한다:

- **`--next` 사전 조건 확장**: 이전 스텝 status == `"merged"` **또는** `"skipped"` → 다음 스텝 진행 허용
- **`--all` 루프**: `skipped` 스텝은 건너뛰고 다음 스텝 자동 진행
- **skill-impl 환경 준비**: 이전 스텝이 `skipped`일 때 PR/브랜치가 없으므로 develop 기준으로 새 브랜치 생성

### 1.7 CLAUDE.md.tmpl 추가 내용

```markdown
## 에러 복구 프로토콜

스킬 실행 중 에러 발생 시, 반드시 아래 형식으로 안내한다:

1. **에러 유형**: 구체적 원인 한 줄
2. **현재 상태**: Task ID, Step, 브랜치, 마지막 성공 지점
3. **복구 방법**: 1~3가지, 첫 번째가 항상 [권장]

자동 복구 가능한 에러는 자동 시도 후 결과를 보고한다.
자동 복구 불가 시 복구 방법을 제시하고 사용자 선택을 대기한다.
```

### 1.8 각 SKILL.md 추가 (1줄)

```markdown
에러 복구: CLAUDE.md "에러 복구 프로토콜" 참조. 미존재 시 3회 재시도 후 사용자 보고.
```

---

## 2. REQ-2: 대화형 백로그 관리

### 2.1 개요

| 항목 | 내용 |
|------|------|
| **스킬명** | `/skill-backlog` (기존 확장) |
| **변경 파일** | skill-backlog/SKILL.md, CLAUDE.md.tmpl, backlog.schema.json |

### 2.2 최종 서브커맨드 체계

```
기존 유지:  list, add, update, priority, unlock
기존 확장:  update (옵션 추가), list (필터 추가)
신규 추가:  dashboard, archive, batch, deps
```

### 2.3 서브커맨드 상세

#### list (확장)

```
/skill-backlog list                     # 전체
/skill-backlog list --status=todo       # 상태 필터
/skill-backlog list --priority=high     # 우선순위 필터
/skill-backlog list --phase=2           # Phase 필터
/skill-backlog list --type=bug          # 타입 필터 (신규)
/skill-backlog list --assignee=me       # 내 작업만 (신규)
/skill-backlog list --stale=3d          # N일 이상 변경 없는 Task (신규)
```

자연어:
- "백로그 보여줘" → list
- "버그만 보여줘" → list --type=bug
- "내 작업 보여줘" → list --assignee=me
- "오래된 작업 보여줘" → list --stale=7d

빈 결과 처리: "해당 조건의 Task가 없습니다. 현재 todo 3개, in_progress 1개, done 2개입니다."

#### add (기존 + 확장)

```
/skill-backlog add "결제 알림 기능"                    # 제목만 (나머지 AI 추론)
/skill-backlog add "상품 검색 500 에러" --type=bug     # 버그 등록
/skill-backlog add "제목" --priority=high --phase=2    # 상세 지정
```

필수 입력: **제목만**. priority, phase, type은 AI가 추론 후 확인.

type별 기본 priority:
- feature: medium / bug: high / chore: low / spike: medium

**`/skill-feature`와의 차이**:
- `add`: 백로그 1줄 등록 (메모 수준, spec 미생성)
- `/skill-feature`: 요구사항 문서(spec.md) 생성 + 백로그 등록 + plan 체이닝

#### update (확장)

```
/skill-backlog update SHOP-001 --status=blocked --reason="API 스펙 미확정"
/skill-backlog update SHOP-001 --title="새 제목"
/skill-backlog update SHOP-001 --description="변경된 설명"
/skill-backlog update SHOP-001 --phase=2
/skill-backlog update SHOP-001 --type=bug
```

추가 옵션: `--title`, `--description`, `--phase`, `--type`, `--reason`

자연어:
- "SHOP-001 수정해줘" → update (대화형 필드 선택)
- "SHOP-001 Phase 2로 옮겨줘" → update --phase=2
- "SHOP-001 블로킹, API 미확정" → update --status=blocked --reason="API 미확정"

#### dashboard (신규)

```
/skill-backlog dashboard
```

출력:
```
📊 프로젝트 현황 — {프로젝트명}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase 1: 상품 기본 기능
  진행률: ██████████░░░░░ 3/5 (60%)
  ✅ SHOP-001 상품 카탈로그 API
  ✅ SHOP-002 Step 1/2 주문 CRUD
  🔄 SHOP-002 Step 2/2 가격 계산 — 2시간 경과
  ⬜ SHOP-003 결제 연동 — 대기 (SHOP-002 의존)
  🔴 SHOP-004 배송 추적 — blocked: 외부 API 미제공

⚠️ 주의:
  - SHOP-002 잠금 만료까지 1시간
  - SHOP-004 blocked 3일째

📌 다음 착수 가능:
  - SHOP-003 (SHOP-002 완료 후)
```

skill-status와의 차이: status는 Git/설정/워크플로우 기술 진단, dashboard는 Task 중심 진행률.
skill-report와의 차이: report는 기간 분석+파일 생성, dashboard는 현재 스냅샷+화면 출력만.

#### archive (신규)

```
/skill-backlog archive SHOP-005
```

동작:
1. `status` → `"archived"`
2. list에서 기본 제외 (`list --all` 또는 `list --archived`로 조회)
3. dependencies 참조 경고 + 확인
4. Git 커밋 & 푸시

제약:
- `in_progress` Task: archive 전 unlock 필수 (자동 안내)
- 자연어 "삭제해줘" → archive 안내 ("보관 처리합니다")

#### batch (신규)

```
/skill-backlog batch --phase=1 --priority=medium --set-phase=2
/skill-backlog batch --status=blocked --set-priority=critical
/skill-backlog batch SHOP-001,SHOP-003,SHOP-005 --set-status=todo
```

동작:
1. dry-run: 영향 Task 목록 표시
2. 사용자 확인
3. 일괄 변경 + `metadata.version` 1회 증가 (원자적)
4. Git 커밋 & 푸시

제약:
- `--set-status=in_progress` batch 불가 (잠금/assignee 개별 처리 필요)
- 최대 20개 Task (초과 시 분할 제안)

#### deps (신규)

```
/skill-backlog deps                    # 전체 의존성 트리
/skill-backlog deps SHOP-003           # SHOP-003의 의존 체인
/skill-backlog deps SHOP-001 --reverse # SHOP-001에 의존하는 Task (영향도)
```

출력 (텍스트 트리):
```
SHOP-003의 의존성:
  SHOP-001 (done) ✅
    └── SHOP-003 (todo) ← 착수 가능

SHOP-001의 영향도 (--reverse):
  SHOP-001 (done) ✅
    ├── SHOP-003 (todo) — 착수 가능
    └── SHOP-004 (blocked) — SHOP-003도 필요
```

제약: Task 15개 초과 시 의존성 있는 Task만 필터링.

### 2.4 CLAUDE.md.tmpl 자연어 매핑 추가

| 자연어 | 스킬 |
|--------|------|
| "백로그 보여줘" | `/skill-backlog list` |
| "버그만 보여줘" | `/skill-backlog list --type=bug` |
| "내 작업 보여줘" | `/skill-backlog list --assignee=me` |
| "Task 추가해줘: {제목}" | `/skill-backlog add "{제목}"` |
| "버그 등록해줘: {설명}" | `/skill-backlog add "{설명}" --type=bug` |
| "{ID} 수정해줘" | `/skill-backlog update {ID}` |
| "대시보드 보여줘" | `/skill-backlog dashboard` |
| "의존성 보여줘" | `/skill-backlog deps` |
| "{ID} 보관해줘" | `/skill-backlog archive {ID}` |
| "일괄 변경해줘" | `/skill-backlog batch` |

---

## 3. REQ-3: getting-started 워크스루 보강

### 3.1 개요

| 항목 | 내용 |
|------|------|
| **변경 파일** | docs/getting-started.md, skill-init/SKILL.md |
| **방식** | 별도 스킬 없이 문서로 해결 |

### 3.2 추가 섹션: "첫 기능 만들기"

기존 getting-started.md (설치 → 초기화 → 온보딩) 끝에 다음 섹션 추가:

```markdown
## 첫 기능 만들기

프로젝트 초기화가 끝났으면, 아래 5단계로 첫 기능을 만들어보세요.

### Step 1: 기능 기획
> /skill-feature "사용자 인증"

**생성되는 것**: docs/requirements/{TASK-ID}-spec.md (요구사항 문서)
**다음 행동**: 요구사항 문서를 검토하고 승인하면 자동으로 Step 2로 진행

### Step 2: 설계 및 스텝 계획
> /skill-plan

**생성되는 것**: .claude/temp/{TASK-ID}-plan.md (설계 + 스텝 분리)
**확인할 것**: 스텝별 파일 목록, 예상 라인 수, 의존성
**다음 행동**: 계획을 승인하면 자동으로 Step 3로 진행

### Step 3: 코드 구현
> /skill-impl (자동 호출됨)

**생성되는 것**: feature 브랜치, 코드, PR
**확인할 것**: PR 링크가 출력됨 → GitHub에서 확인 가능
**다음 행동**: 자동으로 리뷰 진행

### Step 4: 코드 리뷰
> /skill-review-pr {PR번호} (자동 호출됨)

**생성되는 것**: PR에 5관점 리뷰 코멘트
**CRITICAL 이슈 시**: 자동 수정 시도 (skill-fix)
**다음 행동**: 리뷰 통과 시 자동 머지

### Step 5: 머지 완료
> /skill-merge-pr {PR번호} (자동 호출됨)

**결과**: Squash 머지, Task 상태 업데이트
**다음 스텝이 있으면**: 자동으로 Step 3부터 반복

### 막혔을 때
- 빌드 실패: 에러 로그 확인 후 수정, "이어서 진행해줘"
- 스텝 재시작: /skill-impl --retry
- 현재 상태 확인: /skill-status
- 백로그 확인: /skill-backlog dashboard
```

### 3.3 skill-init 변경

Step 7 완료 안내 마지막에 1줄 추가:

```
💡 처음이시면 docs/getting-started.md의 "첫 기능 만들기"를 따라해보세요.
```

---

## 4. 스키마 변경 요약

### backlog.schema.json

```diff
  // task.status enum
- "enum": ["todo", "in_progress", "done", "blocked"]
+ "enum": ["todo", "in_progress", "done", "blocked", "archived"]

  // step.status enum
- "enum": ["pending", "in_progress", "pr_created", "merged", "done"]
+ "enum": ["pending", "in_progress", "pr_created", "merged", "done", "skipped"]

  // task 신규 optional 필드
+ "type": {
+   "type": "string",
+   "enum": ["feature", "bug", "chore", "spike"],
+   "default": "feature"
+ }
```

### 영향 범위

| 파일 | 변경 |
|------|------|
| backlog.schema.json | status/step.status enum 확장, type 필드 추가 |
| skill-impl | --retry, --skip 옵션 + --next/--all에서 skipped 스텝 호환 |
| skill-validate | archived/skipped 인식, type 필드 허용 |
| skill-health-check | archived Task 건강 검진 제외 |
| skill-status | archived 카운트 별도 표시 |
| skill-report | type별 메트릭, 스킵 비율 |
| CLAUDE.md.tmpl | 에러 복구 프로토콜 + 자연어 매핑 |

### 하위 호환성

- 기존 Task에 type 필드 없음 → `"feature"` 폴백
- skill-upgrade 시 자동 반영 (CLAUDE.md 재생성)
- 기존 기능 동작 변경 없음 (additive only)

---

## 5. 구현 순서

```
Task 1: 에러 복구 가이드 + 스키마 변경 통합
  ├── backlog.schema.json 전체 변경: step.status "skipped", task.status "archived", task.type 추가
  ├── CLAUDE.md.tmpl 에러 복구 프로토콜 섹션 추가 (~25줄)
  ├── 5개 스킬에 참조 + fallback 1줄 추가
  ├── skill-impl --retry 구현
  ├── skill-impl --skip 구현 + --next/--all skipped 호환
  └── skill-validate, skill-health-check, skill-status, skill-report 호환성

Task 2: 백로그 기존 확장
  ├── update 옵션 확장 (--title, --description, --phase, --type, --reason)
  ├── list 필터 확장 (--type, --assignee=me, --stale)
  └── add 시 type AI 추론 + 기본 priority

Task 3: 백로그 신규 서브커맨드
  ├── dashboard 구현
  ├── archive 구현
  ├── batch 구현
  ├── deps 구현
  └── CLAUDE.md.tmpl 자연어 매핑 추가

Task 4: getting-started 워크스루
  ├── docs/getting-started.md "첫 기능 만들기" 섹션 작성
  └── skill-init 완료 안내에 1줄 추가
```

> **Note**: Task 1에서 스키마 변경을 통합 처리한다. Task 2 이후는 스키마가 이미 확장된 상태에서 기능만 추가.

---

## 6. Out of Scope

Phase 0에서 하지 않는 항목.

| 항목 | 이관 | 사유 |
|------|------|------|
| skill-tutorial (별도 스킬) | 삭제 | 문서형 워크스루로 대체 (ADR-002) |
| 역할별 분기 (--role) | 삭제 | 개발 도구에 비개발 역할 분기 불필요 (ADR-001) |
| 에러 난이도 태그 | 삭제 | 개발자 전제이므로 불필요 |
| sprint 서브커맨드 | 삭제 | 스프린트 개념 부재, dashboard로 대체 (ADR-004) |
| edit/move/delete 서브커맨드 | 삭제 | update 확장 + archive로 대체 |
| assignee alias (팀원 이름) | Phase 1 | 스키마 설계 필요 |
| dueDate 필드 | Phase 1 | dashboard Phase 기반으로 우선 대응 |
| QA/PM 전용 워크플로우 | 삭제 | ADR-001, ADR-005 |

---

## 7. 검증 기준

### REQ-1 (에러 복구) 완료 조건

- [ ] CLAUDE.md.tmpl에 에러 복구 프로토콜 섹션 존재 (~25줄)
- [ ] 5개 스킬에 참조 + fallback 라인 존재
- [ ] 10가지 에러 유형 모두 표준 형식(에러→상태→복구)으로 안내
- [ ] 모든 복구 방법의 1번이 [권장]
- [ ] `--retry`: PR OPEN 시 close→브랜치 삭제→스텝 재시작 동작
- [ ] `--retry`: PR MERGED 시 거부 메시지 출력
- [ ] `--skip`: 확인 후 step.status="skipped", 다음 스텝 진행
- [ ] `--skip`: 정상 흐름에서 호출 시 거부
- [ ] `--next`: 이전 스텝이 `skipped`일 때 다음 스텝 진행 허용
- [ ] `--all`: `skipped` 스텝 건너뛰고 다음 스텝 자동 진행
- [ ] 기존 스킬 정상 동작 유지 (additive only)

### REQ-2 (대화형 백로그) 완료 조건

- [ ] 기존 5개 서브커맨드 동작 유지
- [ ] update: --title, --description, --phase, --type, --reason 동작
- [ ] list: --type, --assignee=me, --stale 필터 동작
- [ ] list 빈 결과 시 맥락 메시지 출력
- [ ] dashboard: Phase 진행률 + in_progress + blocked + 다음 후보 출력
- [ ] archive: status="archived" + dependencies 참조 경고
- [ ] batch: dry-run → 확인 → 원자적 변경 + version 1회 증가
- [ ] batch: --set-status=in_progress 거부
- [ ] deps: 텍스트 트리 + --reverse 동작
- [ ] task.type: add 시 AI 추론 + 확인
- [ ] CLAUDE.md.tmpl 자연어 매핑 10개 추가
- [ ] 기존 쓰기 프로토콜 (version, 충돌 해소) 준수

### REQ-3 (워크스루) 완료 조건

- [ ] getting-started.md에 "첫 기능 만들기" 섹션 존재 (5단계)
- [ ] 각 단계에 입력/출력/생성 파일/다음 행동 명시
- [ ] "막혔을 때" 섹션에 에러 복구 참조 포함
- [ ] skill-init 완료 안내에 워크스루 링크 1줄 존재
