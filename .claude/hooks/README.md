# .claude/hooks/ — Native Lifecycle Hooks

> **상위 계획**: [docs/v2/phase-1-plan.md](../../docs/v2/phase-1-plan.md)
> **TFT 분석**: [docs/v2/phase-1-tft-analysis.md](../../docs/v2/phase-1-tft-analysis.md)
> **도입 버전**: v2.0.0-alpha.2 (Phase 1 Step 2~)

Claude Code 네이티브 훅으로 ai-crew-kit 워크플로우 자동화를 구현합니다. 훅이 비활성화되어도 v1.x 동작은 100% 유지됩니다.

---

## 디렉토리 구조

```
.claude/hooks/
├── README.md                     이 파일
├── lib/
│   └── atomic-write.sh           flock/mkdir 기반 원자적 쓰기 helper (R5)
├── session-start.sh              SessionStart: git sync + 상태 로드
├── stop.sh                       Stop: 만료 잠금 해제 + continuation-plan 갱신
└── post-tool-use.sh              [Step 3] PostToolUse: lockedAt 갱신 + 무한 루프 방어
```

---

## 비블로킹 작성 규칙 (중요)

훅 스크립트는 **Claude 세션을 절대 차단하지 않아야** 합니다. 다음 규칙을 지키세요.

| 금지 | 이유 | 대안 |
|------|------|------|
| `exit 2` | Claude Code는 exit 2를 "tool 호출 블록" 시그널로 해석 — 세션 흐름 차단 | 모든 에러 경로 `exit 0` + stderr 로그 |
| `set -e` (단독) | 중간 명령어 실패가 세션 차단으로 전파 | `... \|\| true` 또는 개별 체크 + `exit 0` |
| `set -u` / `set -o pipefail` | 미정의 변수/파이프 실패가 비의도적 차단 유발 | 명시적 조건 체크 |

**HI-04** (Phase 1 Step 5) 정적 검사로 위 규칙 위반을 자동 탐지합니다.

---

## 현재 등록된 훅

### SessionStart (`session-start.sh`)

**발동 시점**: Claude Code 세션 시작 시 1회
**timeout**: 30초
**동작**:
1. git sync (워크트리면 `git fetch + merge --ff-only`, 일반 클론이면 `git pull --ff-only`)
2. `.claude/state/continuation-plan.md` 존재 시 stdout 출력
3. `.claude/state/backlog.json`의 `in_progress` Task 목록 안내

**graceful skip 시나리오**: git 미설치, jq 미설치, 비-git 디렉토리 → 경고 로그 후 계속.

### Stop (`stop.sh`)

**발동 시점**: Claude 응답 완료 시마다 (세션 종료 아님 — R3)
**timeout**: 15초
**동작**:
1. `stop_hook_active=true` 수신 시 즉시 exit 0 (공식 재귀 방지)
2. backlog.json의 만료(10분 초과) 잠금 해제 (원자적 쓰기)
3. continuation-plan 조건부 갱신:
   - 60초 이내 갱신됐으면 스킵 (디바운스)
   - `workflowState=idle` 또는 `in_progress` Task 0건이면 스킵
   - 그 외: atomic temp write + rename

**stderr 출력 자제**: 매 턴 발동이라 노이즈 방지.

### PostToolUse

Step 3에서 등록 예정 (`post-tool-use.sh` + 3단계 무한 루프 방어).

---

## 디버깅

### 로그 위치

- **hook-errors.log**: `.claude/state/hook-errors.log` — 훅 실패 append (비블로킹 에러 포함)
- **continuation-plan.md**: `.claude/state/continuation-plan.md` — Stop 훅이 주기 갱신 (디바운스 60s)

### 수동 실행

```bash
# SessionStart 시뮬레이션
echo '{}' | bash .claude/hooks/session-start.sh

# Stop 재귀 방지 확인
echo '{"stop_hook_active": true}' | bash .claude/hooks/stop.sh
# → 즉시 exit 0, 출력 없음

# Stop 정상 발동
echo '{"stop_hook_active": false}' | bash .claude/hooks/stop.sh
```

### 훅 일괄 비활성화

긴급 상황에서 훅을 멈춰야 할 때:

```bash
# 1. 자동 비활성화 플래그 (PostToolUse만, Step 3 도입 후)
touch .claude/state/hook-disabled.flag

# 2. 전체 비활성화 (Claude Code 전역)
# settings.json에 "disableAllHooks": true 추가
```

---

## 동시성 — 워크트리 race 대응 (R5)

두 워크트리에서 동시에 `.claude/state/*.json`을 갱신하는 시나리오:

- **권장**: `atomic_write` helper (`lib/atomic-write.sh`) 사용. flock 가용 환경은 배타 잠금, 미지원 환경은 `mkdir` 뮤텍스 폴백.
- **사용법**:
  ```bash
  source "$(dirname "$0")/lib/atomic-write.sh"
  atomic_write .claude/state/backlog.json \
    jq '.currentTask.lockedAt = "..."' .claude/state/backlog.json
  ```

---

## 참고

- [Claude Code 공식 훅 문서](https://docs.anthropic.com/claude-code) — 이벤트 종류, stdin JSON 스키마, exit code 의미
- `docs/v2/phase-1-tft-analysis.md` §1 — 네이티브 스펙 조사 결과
- `docs/v2/phase-1-hooks.md` — Phase 1 상위 계획
