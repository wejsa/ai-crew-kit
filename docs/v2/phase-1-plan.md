# Phase 1: Native Hooks Framework — 구현 계획서

> **상위 문서**: [phase-1-hooks.md](./phase-1-hooks.md)
> **버전**: `v2.0.0-alpha.2` (Phase 0 alpha.1 이후)
> **브랜치**: `feature/phase-1-hooks-step-*` (v2-develop 분기, Step별 별도 브랜치)
> **예상 작업량**: 7~9시간 (TFT 설계 2h + 구현 5h + 검증 2h)
> **우선순위**: P0 | **의존성**: Phase 0 (완료) | **난이도**: M

---

## 🔄 현재 진행 상황 (다른 세션에서 재개 시 확인)

| Step | 상태 | 비고 |
|------|------|------|
| 0 — TFT 설계 | ✅ 완료 | [phase-1-tft-analysis.md](./phase-1-tft-analysis.md) |
| 1 — hooks 스키마 + settings.json 구조 예약 | ✅ 완료 | PR #23 머지 |
| 2 — SessionStart + Stop 훅 | ✅ 완료 | PR #25 머지 (a0c01d7) — 리뷰 피드백 7건 반영, `.claude/hooks/tests/` 회귀 테스트 6건, hook-tests CI job 신설 |
| 3 — PostToolUse + 3단계 무한 루프 방어 | ✅ 완료 | PR #26 머지 (b63004a) — 리뷰 피드백 6건 반영(H001 matcher 확장, H004 경로 정규화, H005 nosession 격리, H006 카운터 상한, H008/H010 경계/롤오버 테스트), hook-tests 10/10 통과 |
| 4 — CLAUDE.md.tmpl 세션 시작 섹션 재작성 | ✅ 완료 | PR #27 머지 (1d96475) — 훅 자동 안내 + `<details>` 폴백 블록 3트리거 명시, 리뷰 H001 반영(continuation-plan.md 경로 state/ 교정 2건) |
| 5 — Hook Integrity Audit (HI-01~04) | ⏳ 대기 | Step 1 머지 후 병렬 가능 |
| 6 — CHANGELOG + VERSION bump → alpha.2 | ⏳ 대기 | Step 1~5 전부 머지 후 |

**재개 프롬프트 예시**:
> `docs/v2/phase-1-plan.md` 읽고 Step {N} 착수해줘. 직전 완료는 PR #{PR번호}.

---

## 요구사항 요약

Claude Code 네이티브 훅으로 **세션 시작 자동화**, **스킬 전환 비용 제거**, **세션 종료 정리**를 구현하되, 다음 3가지 안전 제약을 강제한다:

1. **PostToolUse 무한 루프 방어** (C001 — CRITICAL) — 3단계 폴백 필수
2. **훅 명령어 인젝션 방어** (H009) — 화이트리스트 + 차단 패턴 + Hook Integrity Audit
3. **훅 비활성화 시 v1.x 동작 100% 유지** (하위호환)

세부 범위/TFT 분석 항목/성공 기준은 `docs/v2/phase-1-hooks.md` 참조.

---

## 🔒 스키마 소유권 계약 (H003 대응)

본 Phase에서 다루는 두 스키마는 **관리 주체가 다름** — 혼동 방지 위해 경계를 명문화한다.

| 파일 | 관리 주체 | 검증 대상 | 강제 수단 |
|------|---------|---------|---------|
| `.claude/schemas/project.schema.json` | ai-crew-kit (본 레포) | `examples/*/.claude/state/project.json` 등 ai-crew-kit 내부 구성 | `scripts/validate-schema.sh` + `.github/workflows/schema-validation.yml` |
| `.claude/settings.json` | **Claude Code 공식 스키마** (외부) | 실제 훅 실행 대상 | Claude Code 런타임 + 본 레포 JSON 구문 체크 |

**핵심 원칙**:
- `project.schema.json`의 `hooks` 정의는 **참고용 계약**이며 `.claude/settings.json`에 자동 적용되지 않는다.
- `.claude/settings.json`은 Claude Code 공식 스키마(`https://json.schemastore.org/claude-code-settings.json`)에 맞춰야 한다. 특히 `hooks[].hooks[].type: "command"`가 필수.
- 두 스키마의 `hookMatcher` 구조 동기화는 **Step 5 HI-03(health-check) 과제**로 런타임에서 양쪽 대조 검사.
- Phase 4 Layered Override 도입 시 `hooks.schema.json`으로 definition 분리 검토.

---

## 🛡️ 보안 리뷰 필수 변경점 (H006 대응)

다음 파일 변경 PR은 **security-lead(또는 security 에이전트) 리뷰 필수**:

| 파일 | 이유 | 체크포인트 |
|------|------|---------|
| `.claude/settings.json` (`hooks` 필드) | clone 시 모든 contributor 세션에서 자동 실행 | 위험 패턴, 외부 스크립트 참조, 경로 prefix |
| `.claude/hooks/**` | 훅 스크립트 본체 | 비블로킹 규칙, 차단 패턴, stdin 프롬프트 유발 명령 |
| `.claude/schemas/project.schema.json` (hooks, `definitions.hookMatcher`) | 다른 훅 정의의 계약 | description 필수화, timeout 상한, `command` pattern |

운영 규칙:
1. 위 파일이 diff에 포함되면 PR label에 `security-review` 자동 부여 (후속 Phase)
2. `.github/CODEOWNERS`에 상기 경로 등록 (본 PR에서 도입)
3. `.claude/hooks/README.md`에 "자동 실행 경고" 섹션 필수

---

## 현재 상태 점검

| 항목 | 상태 |
|------|------|
| VERSION | `2.0.0-alpha.1` (Phase 0 완료) |
| `project.schema.json` hooks 필드 | 예약 상태 (`type: object, default: {}`) — Phase 1에서 상세화 필요 |
| `.claude/settings.json` hooks | 미정의 |
| `.claude/hooks/` 디렉토리 | 부재 — 신규 생성 |
| `CLAUDE.md.tmpl` 세션 시작 섹션 | 수동 git sync 스크립트 (L51-75) |
| `skill-health-check` hook-safety 카테고리 | 부재 |

---

## 설계 개요

### 컴포넌트 구조

```
.claude/
├── settings.json                       [수정] hooks 필드 추가
├── hooks/                              [신규]
│   ├── session-start.sh                세션 시작: git sync + 상태 로드
│   ├── post-tool-use.sh                Write/Edit 후: lockedAt 리프레시 (+ 무한 루프 방어)
│   └── stop.sh                         세션 종료: 잠금 해제 + continuation-plan 생성
├── schemas/
│   └── project.schema.json             [수정] hooks 상세 스키마
├── templates/
│   └── CLAUDE.md.tmpl                  [수정] 세션 시작 섹션 재작성
├── skills/
│   └── skill-health-check/SKILL.md     [수정] hook-safety 카테고리 (HI-01~03) 추가
└── domains/_base/health/
    └── _category.json                  [수정] 가중치 재배분 (hook-safety 10~15%)
```

### 시퀀스 (SessionStart 훅 흐름 예시)

```
Claude Code 세션 시작
  → settings.json hooks.SessionStart 감지
    → .claude/hooks/session-start.sh 실행
       1. git rev-parse --git-dir / --git-common-dir 비교 → 워크트리 감지
       2. 워크트리면 fetch+merge origin/v2-develop, 아니면 pull
       3. .claude/state/continuation-plan.md 존재 시 출력
       4. backlog.json의 in_progress Task 안내
    → 훅 완료 (exit 0) → Claude 세션 진입
  → 훅 실패 (exit != 0) → 에러 로그 출력 + 세션 정상 계속
```

### 데이터 모델 — `project.schema.json` hooks 상세화

> **[TFT 보정 — R1]** Claude Code 공식 훅 구조는 `{event: [{matcher, hooks: [{command}]}]}` 2층 배열. 파일 경로 필터는 **네이티브 미지원** → `excludePaths` 커스텀 키는 무시되므로 제거하고, 스크립트 내 stdin JSON 파싱으로 필터링.

```json
{
  "hooks": {
    "type": "object",
    "properties": {
      "SessionStart": { "type": "array", "items": { "$ref": "#/definitions/hookMatcher" } },
      "PostToolUse": { "type": "array", "items": { "$ref": "#/definitions/hookMatcher" } },
      "Stop": { "type": "array", "items": { "$ref": "#/definitions/hookMatcher" } }
    },
    "additionalProperties": false
  },
  "definitions": {
    "hookMatcher": {
      "type": "object",
      "required": ["hooks"],
      "properties": {
        "matcher": { "type": "string", "description": "Tool 이름 정규식 (예: Edit|Write)" },
        "hooks": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["command"],
            "properties": {
              "command": { "type": "string", "minLength": 1 },
              "description": { "type": "string" },
              "timeout": { "type": "integer", "default": 30 }
            }
          }
        }
      }
    }
  }
}
```

### 무한 루프 방어 (3단계 폴백) — TFT 보정 반영

| 단계 | 메커니즘 | 구현 위치 | 보정 근거 |
|------|---------|---------|---------|
| 1. 경로 제외 (스크립트 레벨) | stdin JSON에서 `tool_input.file_path` 추출 → `.claude/state/`, `.claude/temp/` 경로면 즉시 exit 0 | `.claude/hooks/post-tool-use.sh` 상단 | **R1** — 네이티브 경로 필터 부재로 스크립트 이관 |
| 2. 파일 락 (재진입 방지) | `/tmp/ack-hook-${session_id}.lock` 존재 시 즉시 exit 0, 없으면 생성 + `trap "rm -f $LOCK" EXIT` | `.claude/hooks/post-tool-use.sh` | **R2** — 환경변수는 fresh shell 환경에서 불안정 → 파일 락으로 변경 |
| 3. 자동 비활성화 | 10초 윈도우 내 3회 트리거 감지 시 `.claude/state/hook-disabled.flag` 생성 + stderr 경고 | `.claude/state/hook-trigger-count` 카운터 | 계획대로 유지 |

> **훅 스크립트 작성 규칙 (R4)**: `exit 2` 금지 (블록 시그널), `set -e` 금지 (의도치 않은 세션 차단 위험). 비블로킹 원칙 — 모든 에러 경로 `exit 0`.

---

## 스텝 분리 (6 PR + 1 설계문서)

| Step | 제목 | 예상 라인 | 주요 파일 | 의존 |
|------|------|----------|---------|------|
| 0 | TFT 설계 + 훅 스펙 조사 (설계문서 커밋) | — | `.claude/temp/phase-1-tft-analysis.md` | — |
| 1 | hooks 스키마 상세화 + settings.json 구조 예약 | ~200 | `project.schema.json`, `settings.json` | Step 0 |
| 2 | SessionStart + Stop 훅 스크립트 + 등록 | ~300 | `.claude/hooks/session-start.sh`, `stop.sh`, `settings.json` | Step 1 |
| 3 | PostToolUse 훅 + 3단계 무한 루프 방어 | ~250 | `.claude/hooks/post-tool-use.sh`, `settings.json` | Step 2 |
| 4 | CLAUDE.md.tmpl 세션 시작 섹션 재작성 | ~80 | `.claude/templates/CLAUDE.md.tmpl` | Step 2 |
| 5 | Hook Integrity Audit — health-check 확장 | ~200 | `skill-health-check/SKILL.md`, `_base/health/_category.json` | Step 1 |
| 6 | CHANGELOG + VERSION bump + 통합 검증 | ~50 | `CHANGELOG.md`, `VERSION`, `README.md` | Step 1~5 |

> **라인 제한**: Step 1~5는 개별 PR, Step 6은 릴리스 PR. prLineLimit 전역 500 적용.

---

## 스텝별 상세

### Step 0: TFT 설계 + 훅 스펙 조사 (설계문서, PR 없음)

**산출물**: `.claude/temp/phase-1-tft-analysis.md`

- **Architect**
  - Claude Code 공식 문서/`claude-code-guide` 에이전트로 settings.json hooks 네이티브 스펙 확인
  - 훅이 shell command인지 skill 호출인지 (스펙에 따라 Step 2~3 구조 변경)
  - 워크트리 동시 훅 race condition: `flock` 또는 원자적 쓰기로 방어 가능 여부
- **Security Lead**
  - 화이트리스트 확정: `git`, `cat`, `echo`, `jq`, `date`, `test`, `[`
  - 차단 패턴 확정: `rm`, `sudo`, `curl`, `wget`, `git reset --hard`, `git push --force`, `|` (외부 전송 용도)
  - Hook Integrity Audit 검사 알고리즘 (정규식 목록) 초안
- **DX Lead**
  - 훅 실행 중 사용자에게 보이는 메시지 형식 (예: `🪝 SessionStart: git sync 중...`)
  - CLAUDE.md.tmpl 변경 사양: 훅 미설정 폴백 절차 유지
- **Product Lead**: 범위 검증 — hooks 필드 부재 시 v1.x 동작 100% 유지 확인
- **Domain Lead**: 도메인별 훅 프로파일은 Phase 4 (Layered Override)로 이관 확정

**실패 시나리오 최소 2개** (H012~H016 대응):
1. Claude Code가 네이티브 훅을 미지원 → Step 2~3 중단, 대안 설계 필요
2. 워크트리 동시 훅 충돌 재현 → `flock` 기반 파일 잠금 검증

### Step 1: hooks 스키마 상세화 + settings.json 구조 예약 (PR 1)

**파일**:
- `.claude/schemas/project.schema.json` (수정, ~150줄)
  - `hooks` 객체를 위 "데이터 모델" 섹션대로 확장
  - `additionalProperties: true` → `false`로 전환 (v2 한정, skill-upgrade가 v1 호환 보정)
- `.claude/settings.json` (수정, ~30줄)
  - `hooks` 객체 빈 구조 추가: `{"SessionStart": [], "PostToolUse": [], "Stop": []}`
  - 실제 훅 등록은 Step 2~3에서 순차 추가

**검증**:
- 기존 v1 project.json 예시가 새 스키마 validate 통과
- `jq '.hooks' .claude/settings.json` 출력 유효

### Step 2: SessionStart + Stop 훅 스크립트 + 등록 (PR 2)

> **[TFT 보정 — R3]** Stop 훅은 "세션 종료"가 아니라 **"Claude 응답 완료 시마다"** 발동. continuation-plan을 매 턴 덮어쓰면 비효율 → 조건부 + 디바운스로 재설계.

**파일**:
- `.claude/hooks/lib/atomic-write.sh` (신규, ~30줄) — flock 기반 원자적 쓰기 helper (**R5 대응**). flock 미지원 환경은 `mkdir` 뮤텍스 폴백.
- `.claude/hooks/session-start.sh` (신규, ~80줄)
  - `command -v jq >/dev/null || exit 0` (jq 미설치 graceful skip)
  - 워크트리 감지 후 fetch+merge or pull (`origin/v2-develop`)
  - `.claude/state/continuation-plan.md` 존재 시 stdout 출력 (사용자 가시)
  - backlog.json에서 `status: in_progress` Task 목록 추출 + 출력
  - 모든 실패 경로: `>&2` 경고 + **`exit 0`** (비블로킹)
- `.claude/hooks/stop.sh` (신규, ~80줄)
  - stdin JSON에서 `stop_hook_active` 확인 → true면 즉시 exit 0 (**공식 재귀 방지**)
  - 만료 잠금 스캔 → atomic-write로 해제 (매 턴 수행 OK)
  - continuation-plan 디바운스: `.claude/state/continuation-plan.md` mtime이 60초 이내면 갱신 스킵
  - 활성 Task 없으면(workflowState=idle) continuation-plan 생성 스킵
  - 그 외: 원자적 temp write + rename
- `.claude/settings.json` (수정, ~20줄)
  - `SessionStart: [{"hooks": [{"command": "$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.sh", "timeout": 30}]}]`
  - `Stop: [{"hooks": [{"command": "$CLAUDE_PROJECT_DIR/.claude/hooks/stop.sh", "timeout": 15}]}]`
- `.claude/hooks/README.md` (신규, ~40줄) — 훅 설계 원칙, 비블로킹 규칙(`exit 2`/`set -e` 금지), 디버깅 로그 위치 (`.claude/state/hook-errors.log`)

**검증**:
- 로컬에서 `echo '{}' | bash .claude/hooks/session-start.sh` 직접 실행 → exit 0
- Stop 훅 재귀 시뮬: `echo '{"stop_hook_active":true}' | bash .claude/hooks/stop.sh` → 즉시 exit 0
- 실제 세션 시작 시 git sync 자동 수행 확인
- `jq` 언인스톨 환경에서 훅 실행 → 세션 정상 시작 (R2 시나리오)

### Step 3: PostToolUse 훅 + 3단계 무한 루프 방어 (PR 3)

> **[TFT 보정 — R1, R2]** 파일 경로 필터는 네이티브 미지원이라 **스크립트 최상단에서** stdin JSON 파싱으로 처리. 재진입 방지는 환경변수 대신 **파일 락**.

**파일**:
- `.claude/hooks/post-tool-use.sh` (신규, ~150줄) — 실행 순서:
  ```bash
  #!/usr/bin/env bash
  # set -e 금지, exit 2 금지 (R4)

  # 0단계: 자동 비활성화 플래그 확인
  [ -f .claude/state/hook-disabled.flag ] && exit 0

  # jq 의존성
  command -v jq >/dev/null || exit 0

  # stdin JSON 수신
  INPUT=$(cat)
  FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
  SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "nosession"' 2>/dev/null)

  # 1단계: 경로 제외 (R1)
  case "$FILE_PATH" in
    .claude/state/*|.claude/temp/*|*/.claude/state/*|*/.claude/temp/*) exit 0 ;;
  esac

  # 2단계: 파일 락 재진입 방지 (R2)
  LOCK="/tmp/ack-hook-${SESSION_ID}.lock"
  [ -e "$LOCK" ] && exit 0
  trap 'rm -f "$LOCK"' EXIT
  touch "$LOCK"

  # 3단계: 트리거 카운터 (10초 윈도우)
  # .claude/state/hook-trigger-count 증가 → 3회 초과 시 hook-disabled.flag 생성 + stderr 경고

  # 핵심 동작: backlog.json lockedAt 갱신 (atomic-write.sh 활용 — R5)
  source .claude/hooks/lib/atomic-write.sh
  atomic_jq_update .claude/state/backlog.json '...'

  exit 0
  ```
- `.claude/settings.json` (수정, ~15줄)
  - `PostToolUse: [{"matcher": "Edit|Write|MultiEdit|NotebookEdit", "hooks": [{"command": "$CLAUDE_PROJECT_DIR/.claude/hooks/post-tool-use.sh", "timeout": 10}]}]`
- `.claude/state/.gitignore` 업데이트 (수정, ~3줄) — `hook-trigger-count`, `hook-disabled.flag`, `hook-errors.log` 제외
- `/tmp/` 락 파일은 gitignore 불필요 (레포 외부)

**테스트 시나리오** (실패/경계값 포함):
1. 정상 Write (src/Foo.kt) → lockedAt 갱신, 카운터 0
2. `.claude/state/backlog.json` Write → 1단계 경로 제외로 즉시 exit 0
3. 중첩 Write 시뮬 (락 존재 상태에서 재호출) → 즉시 exit 0
4. 10초 내 3회 연속 재귀 강제 → `hook-disabled.flag` 생성 + 경고 stderr
5. `jq` 언인스톨 → exit 0 (세션 정상)
6. backlog.json 깨진 JSON → jq 실패 → exit 0
7. 워크트리 2개 동시 Write → flock으로 직렬화, 최종 `lockedAt` 하나 보존 (R5)

### Step 4: CLAUDE.md.tmpl 세션 시작 섹션 재작성 (PR 4)

**파일**:
- `.claude/templates/CLAUDE.md.tmpl` (수정, ~50줄)
  - L51-75 "세션 시작 시 필수" 섹션 교체:
    - 기본 안내: "SessionStart 훅이 자동 실행합니다. 수동 조작 불필요."
    - 폴백 블록 `<details>`로 숨김: 훅 미설정/실패 시 수동 절차
  - 기존 `/skill-status`, `/skill-plan` 호출 예시는 유지

**검증**:
- skill-init으로 새 프로젝트 생성 시 CLAUDE.md 렌더링 정상
- 훅 비활성 프로젝트에서 폴백 절차가 명확히 표시

### Step 5: Hook Integrity Audit — health-check 확장 (PR 5)

> **[TFT 보정 — R4]** 훅 스크립트 정적 검사에 `exit 2`, `set -e` 탐지 항목 추가 (HI-04).

**파일**:
- `.claude/skills/skill-health-check/SKILL.md` (수정, ~180줄)
  - 새 카테고리 `hook-safety` 추가:
    - **HI-01** (CRITICAL): settings.json hooks 및 `.claude/hooks/*.sh` 명령어에 차단 패턴 탐지
      - 정규식: `\brm\s+-[rf]`, `\bsudo\b`, `\bcurl\b`, `\bwget\b`, `git\s+reset\s+--hard`, `git\s+push\s+--force`, `\|\s*(curl|wget|nc|bash|sh)`
    - **HI-02** (CRITICAL): 외부 스크립트 참조 탐지 — `.claude/hooks/` 외부 경로 또는 `http://`, `https://` 참조 시 FAIL
    - **HI-03** (MINOR): hooks 필드 JSON 구조 유효성 (project.schema.json validate)
    - **HI-04** (MAJOR, 신설): 훅 스크립트 비블로킹 규칙 위반 탐지 — `.claude/hooks/*.sh`에 `exit 2` 또는 `set -e`(단독, `|| true` 동반 없음) 검출 시 FAIL
  - autoFix: 불가 (보안 관련 수동 수정 필수)
- `.claude/domains/_base/health/_category.json` (수정, ~15줄)
  - `hook-safety` 카테고리 추가, `weight: 10`
  - 가중치 재배분: doc-sync 35→32, state-integrity 25→23, security 25→23, agent-config 15→12, hook-safety 10 (합 100)
  - `failCap: 40` (CRITICAL 비중 높음)

**검증**:
- 위험 패턴(`rm -rf`, `curl | bash`) 주입된 settings.json → HI-01 CRITICAL FAIL
- 외부 URL 참조 → HI-02 CRITICAL FAIL
- 스키마 위반 hooks 구조 → HI-03 MINOR FAIL
- `exit 2` 포함 훅 스크립트 → HI-04 MAJOR FAIL
- 가중치 합 100 유지, health-history 이전 기록 대비 변화 안내

### Step 6: CHANGELOG + VERSION + 릴리스 검증 (PR 6)

**파일**:
- `/VERSION`: `2.0.0-alpha.1` → `2.0.0-alpha.2`
- `/CHANGELOG.md`: `[2.0.0]` 섹션에 Phase 1 항목 추가
  - Added: Native Hooks Framework (SessionStart/PostToolUse/Stop), Hook Integrity Audit
  - Changed: CLAUDE.md.tmpl 세션 시작 섹션, health-check 가중치 재배분
  - Breaking: 없음 (훅 부재 시 v1.x 동작 유지)
- `/README.md`: 버전 뱃지 `v2.0.0-alpha.2`
- 통합 검증: 실제 세션에서 SessionStart → 개발 → Stop 전 흐름 수동 시연

---

## 파일 충돌 검사

현재 다른 in_progress 작업 없음. 본 저장소는 메타 개발이라 backlog 추적 부재. 단, v1.x 핫픽스가 develop에서 발생 시 `.claude/settings.json` 충돌 가능성 → **Step 2 시작 전 `git fetch origin develop && git merge origin/develop` 선제 동기화 권장**.

---

## 성공 기준 (상위 문서 기준 + TFT 보정)

- [ ] `settings.json`에 hooks 필드가 2층 구조(matcher/hooks)로 정의되고 Claude Code가 인식
- [ ] SessionStart 훅: git sync + 상태 로드 자동 수행
- [ ] Stop 훅: `stop_hook_active` 체크로 재귀 방지, 60초 디바운스 동작, idle 시 continuation-plan 생성 스킵
- [ ] hooks 필드 부재 시 v1.x 동작 100% 유지 (폴백)
- [ ] PostToolUse 훅: `.claude/state/` Write 시 **스크립트 레벨에서** 즉시 exit (R1)
- [ ] PostToolUse: 파일 락 기반 재진입 방지 동작 (R2)
- [ ] PostToolUse: 10초 내 3회 연속 트리거 시 `hook-disabled.flag` 생성 + 경고
- [ ] 워크트리 2개 동시 Write 시 flock으로 직렬화, 데이터 손실 없음 (R5)
- [ ] skill-health-check `hook-safety` 카테고리 동작 (HI-01~04)
- [ ] 위험 패턴 (`rm -rf`, `sudo`, `curl | bash`) → HI-01 CRITICAL FAIL
- [ ] 외부 스크립트/URL 참조 → HI-02 CRITICAL FAIL
- [ ] 훅 스크립트에 `exit 2`/`set -e` → HI-04 MAJOR FAIL (R4)
- [ ] 훅 실행 실패(exit != 0, exit 2 제외) → 에러 로그 + 세션 정상 계속
- [ ] `jq` 미설치 환경에서 훅이 graceful skip (세션 정상 동작)
- [ ] `.claude/hooks/README.md`로 훅 디버깅 절차 + 비블로킹 규칙 문서화

---

## 리스크 및 대응 (TFT 분석 R1~R6 반영)

> 상세 근거는 [phase-1-tft-analysis.md](./phase-1-tft-analysis.md) §2 참조. (동일 디렉토리)

| ID | 리스크 | 확률 | 영향 | 대응 | 감지 스텝 |
|----|--------|------|------|------|----------|
| **R1** | 파일 경로 필터 네이티브 미지원 — `excludePaths` 커스텀 키 무시됨 | **확정** | 높음 | 스크립트 최상단에서 stdin JSON의 `tool_input.file_path` 파싱 → 경로 제외 처리 | Step 3 |
| **R2** | PostToolUse 재귀 네이티브 방지 없음 | **확정** | 높음 | 환경변수 대신 **파일 락**(`/tmp/ack-hook-${session}.lock`) + 10초 윈도우 3회 카운터 자동 비활성화 | Step 3 |
| **R3** | Stop 훅은 "세션 종료"가 아니라 "응답 완료 시마다" 발동 | **확정** | 중 | `stop_hook_active` 체크 + 60초 디바운스 + idle 상태 시 스킵 | Step 2 |
| **R4** | 훅 스크립트가 `exit 2`/`set -e` 사용 시 세션 차단 | 낮 | 높음 | 작성 규칙 강제 + HI-04 정적 검사 | Step 2/3, Step 5 |
| **R5** | 워크트리 동시 Write race condition (공식 문서 부재) | 중 | 중 | `flock` 기반 원자적 쓰기 helper(`.claude/hooks/lib/atomic-write.sh`), 미지원 시 mkdir 폴백 | Step 2 |
| **R6** | Claude Code 구버전에서 hooks 필드 미지원 | 낮 | 낮 | hooks 부재 시 v1.x 동작 유지 (하위호환) + 릴리스 노트에 "Claude Code v2.x 권장" 명시 | Step 1, 6 |
| R7 | `jq` 미설치 환경 | 낮 | 중 | 훅 첫 줄 `command -v jq \|\| exit 0` graceful skip | Step 2/3 |
| R8 | CLAUDE.md.tmpl 변경이 skill-upgrade 영향 | 낮 | 중 | Phase 8에서 skill-upgrade 마이그레이션 검증 | Step 4 |
| R9 | 가중치 재배분으로 기존 health 점수 급변 | 중 | 낮 | Phase 8 마이그레이션 가이드에 매핑표 | Step 5 |

---

## 진행 방식 권장

1. **Step 0 (설계)**: `.claude/temp/phase-1-tft-analysis.md`를 먼저 작성하고 사용자 리뷰 → 승인 후 Step 1 착수
2. **Step 1~5**: 각 PR 생성 시 `feature/phase-1-hooks-step-N` 브랜치 → `v2-develop`으로 머지
3. **Step 6**: 모든 스텝 머지 확인 후 릴리스 PR (v2-develop → v2-develop tag `v2.0.0-alpha.2`)
4. 각 PR 머지 전 `/skill-review-pr` 실행 권장 (특히 Step 3, 5)

---

## 참고 문서

- [phase-1-hooks.md](./phase-1-hooks.md) — 상위 계획
- [phase-0-foundation.md](./phase-0-foundation.md) — 완료된 기반
- [README.md](./README.md) — 전체 Phase 로드맵
- [../harness-phase2.md](../harness-phase2.md) — 이전 릴리스 계획서 포맷 참고
