# Phase 1: TFT 분석 — 훅 스펙 조사 + 설계 보정

> **Step**: 0 (설계문서, PR 없음)
> **상위 계획**: [phase-1-plan.md](./phase-1-plan.md)
> **조사 일자**: 2026-04-17

---

## 1. Claude Code 네이티브 훅 스펙 (공식 문서 기준)

`claude-code-guide` 에이전트 조사 결과:

| 항목 | 스펙 | 영향 |
|------|------|------|
| 필드명 | `hooks` | 계획과 일치 |
| 이벤트 | SessionStart, PreToolUse, PostToolUse, Stop 포함 21개 | 계획과 일치 |
| 매처 구조 | 이벤트 하위에 `matcher`/`hooks` 배열 | **계획 수정 필요** — 2층 구조 |
| Tool 필터 | `"matcher": "Edit|Write"` (정규식) | OK |
| 파일 경로 필터 | **네이티브 미지원** (v2.1.85+ `if` 필드로 권한 규칙 문법 사용 가능) | **R1 — 재설계** |
| Shell | bash/sh, 프로필 소싱됨 | OK |
| 환경변수 | `$CLAUDE_PROJECT_DIR`, session_id, cwd | OK |
| Stdin | JSON 이벤트 (`tool_input.file_path` 등 포함) | 스크립트에서 파싱 필요 |
| Exit code | 0=허용, 2=블록, 기타=비블로킹 에러 | **R4 — exit 2 금지** |
| PostToolUse 재귀 방지 | **네이티브 없음** | **R2 — 스크립트 방어 필수** |
| Stop 훅 발동 시점 | "Claude 응답 완료 시마다" (턴 종료) | **R3 — 계획 재정의** |
| Stop 훅 무한 루프 방어 | `stop_hook_active` JSON 필드 제공 | 공식 메커니즘 활용 |
| 워크트리 동시성 | 문서 명시 없음 | **R5 — 실증 필요** |

---

## 2. 주요 리스크 정확 분석 (총 6건)

### R1 (HIGH) — 파일 경로 필터 네이티브 미지원

**문제**: 계획서의 `excludePaths: [".claude/state/", ".claude/temp/"]`는 **Claude Code가 무시한다**. settings.json 스키마에 커스텀 키 추가해도 훅 매처는 사용하지 않음.

**영향**: PostToolUse 훅이 상태 파일 Write에도 발동 → 무한 루프 재귀 위험 증가.

**대응**:
- **A안 (권장)**: 스크립트 최상단에서 stdin JSON을 `jq`로 파싱하여 `tool_input.file_path` 추출 → 제외 경로면 즉시 `exit 0`
- **B안 (Claude Code v2.1.85+ 한정)**: settings.json matcher에 `"if": "Write(.claude/state/**)"` 권한 규칙 문법으로 필터. 단, 이 방식은 **반대 의미**(매칭 시 실행)라서 "제외"하려면 반대 논리 표현 필요 — 복잡도 증가
- **결정**: **A안**. 단, settings.json hooks 정의에 `"description"`으로 "스크립트가 내부적으로 .claude/state/, .claude/temp/ 제외"를 명시하여 감사 추적 확보

**구현 변경**:
```bash
# .claude/hooks/post-tool-use.sh 최상단
INPUT=$(cat)  # stdin JSON 수신
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
case "$FILE_PATH" in
  .claude/state/*|.claude/temp/*|*/.claude/state/*|*/.claude/temp/*)
    exit 0  # 1단계 경로 제외
    ;;
esac
```

### R2 (HIGH) — PostToolUse 재귀 네이티브 방지 없음

**문제**: Claude Code는 PostToolUse 훅이 Write를 호출해도 재귀를 막지 않음. R1이 방어를 뚫리면 훅 → Write → 훅 → Write 무한 루프.

**대응 (계획서 3단계 폴백 유지 + 강화)**:
1. **1단계 (R1 대응 후 스크립트 경로 제외)**: 위 스크립트
2. **2단계 (재진입 방지)**: 환경변수 전파의 한계 — Claude Code는 훅을 fresh shell로 실행할 수 있어 `export` 불안정. 대신 **파일 기반 뮤텍스**로 전환:
   ```bash
   LOCK=/tmp/ack-hook-$$-$(echo "$INPUT" | jq -r '.session_id // "nosession"').lock
   [ -e "$LOCK" ] && exit 0
   trap "rm -f $LOCK" EXIT
   touch "$LOCK"
   ```
3. **3단계 (자동 비활성화)**: `.claude/state/hook-trigger-count` 카운터 파일. 10초 이내 3회 트리거 감지 시 `.claude/state/hook-disabled.flag` 생성 + stderr 경고. 이후 훅 스크립트 첫 줄에서 `[ -f .claude/state/hook-disabled.flag ] && exit 0`.

**계획서 수정 필요**: "환경변수 `ACK_HOOK_RUNNING=1`" → **"파일 락 `/tmp/ack-hook-$SESSION-$$.lock`"**.

### R3 (MEDIUM) — Stop 훅은 "세션 종료"가 아니라 "턴 종료마다" 발동

**문제**: 계획서는 "세션 종료 시 continuation-plan 생성"을 Stop 훅에 위임했지만, 실제로는 **매 응답 완료마다** 발동. 매번 continuation-plan을 덮어쓰면 I/O 낭비 + 불필요한 파일 변경.

**대응**:
- **차별화 트리거**: Stop 훅 스크립트에서 다음 조건 판별:
  - `stop_hook_active: true` → **이미 Stop 훅 내부에서 발동된 재귀** → 즉시 exit 0
  - backlog.json의 `currentTask.workflowState`가 "idle" 또는 없음 → 활성 작업 없음 → continuation-plan 생성 스킵
  - 위 둘 아니면 → continuation-plan 갱신 (원자적 temp write + rename)
- **잠금 해제는 매 턴 수행 OK**: 만료 잠금 정리는 자주 해도 무해
- **continuation-plan은 디바운스**: 마지막 갱신으로부터 60초 이내면 스킵

**계획서 수정 필요**: Stop 훅 설명을 "세션 종료 시" → "응답 완료 시마다 (디바운스 + 조건부)"로 수정.

### R4 (MEDIUM) — 훅 실패 시 세션 중단 위험 (exit code 오용)

**문제**: 계획서 성공 기준 "훅 실행 실패(exit ≠ 0) 시 에러 로그 + 세션 정상 계속"을 보장하려면 **절대 exit 2를 쓰면 안 됨**. Claude Code는 exit 2를 "블록"으로 해석하여 세션 흐름 차단.

**대응**:
- **스크립트 작성 규칙**: `set -e` 금지, 대신 명시적 `|| true` 후 `exit 0`
- **에러 로깅**: `>&2` 및 `.claude/state/hook-errors.log`에 append (디버깅용)
- **단, 의도적 차단**: PreToolUse는 향후 Phase에서 도입 시 exit 2 활용 가능. Phase 1 범위는 전부 비블로킹.

**Hook Integrity Audit (HI-04) 신설 제안**: 훅 스크립트 정적 검사에서 `exit 2` 또는 `set -e` 검출 → MAJOR 경고.

### R5 (MEDIUM) — 워크트리 동시 훅 race condition (문서 부재)

**문제**: 두 worktree에서 동시에 PostToolUse 훅이 발동 → 둘 다 `backlog.json`에 `lockedAt` 갱신 Write → 락 없이 덮어쓰기 → 데이터 손실.

**대응**:
- **flock 기반 원자적 쓰기**: `flock -x .claude/state/backlog.lock -c "jq ... backlog.json > backlog.json.tmp && mv backlog.json.tmp backlog.json"`
- flock 미지원 시스템(macOS 일부) 대비: `mkdir .claude/state/.backlog-lock` 기반 뮤텍스 폴백
- Step 2/3 구현에서 helper 함수로 추출: `.claude/hooks/lib/atomic-write.sh`

### R6 (LOW) — `if` 필드는 Claude Code v2.1.85+에서만 동작

**문제**: 계획 B안(권한 규칙 문법)을 썼다가 구 버전 사용자에게 훅이 동작 안 할 위험.

**대응**: A안(스크립트 내 필터) 채택으로 회피. 버전 의존성 제거. 단 Phase 1 릴리스 노트에 "Claude Code v2.x 권장"으로 표시.

---

## 3. TFT 5인 분석 결과

### Architect
- **결론**: 계획서 근간 유효. 단 2가지 구조 변경:
  - settings.json hooks 구조: `{"PostToolUse": [{"matcher": "Edit|Write", "hooks": [{"command": "..."}]}]}` (2층 배열)
  - `excludePaths` 커스텀 필드 제거 → 스크립트 내 필터로 이관
- **기술 부채**: flock 폴백, jq 의존성 — Step 2에서 `.claude/hooks/lib/`로 공용 유틸 분리

### Security Lead
- **화이트리스트 확정**: `git`, `cat`, `echo`, `jq`, `date`, `test`, `[`, `mv`, `mkdir`, `flock`, `trap`
- **차단 패턴 확정** (HI-01 정규식):
  - `\brm\s+-[rf]` (rm -rf)
  - `\bsudo\b`, `\bcurl\b`, `\bwget\b`
  - `git\s+reset\s+--hard`, `git\s+push\s+--force`
  - `\|\s*(curl|wget|nc|bash|sh)` (외부 전송 파이프 한정)
- **HI-02**: `.claude/hooks/` 외부 경로 또는 `http://`/`https://` 참조 → CRITICAL
- **HI-04 신설 (위 R4)**: 훅 스크립트에 `exit 2`, `set -e` 감지 → MAJOR

### DX Lead
- **사용자 메시지 형식**:
  - SessionStart: `🪝 [hook] git sync…` → `✓ 동기화 완료 (+3 commits)`
  - Stop: stderr 출력 금지 (매 턴 발동이라 노이즈). 조용히 잠금 정리만
  - PostToolUse: stderr 출력 금지 (매 Write마다 발동)
  - 3단계 자동 비활성화 발동 시에만 눈에 띄게 stderr: `⚠️ PostToolUse 훅이 3회 연속 재귀 트리거되어 자동 비활성화됨. .claude/state/hook-disabled.flag 삭제 시 복원.`
- **CLAUDE.md.tmpl 폴백**: 훅 미설정 감지 로직 추가 권장 — skill-init이 settings.json 생성할 때 hooks 없으면 `<details>` 블록 펼침

### Product Lead
- **범위 준수 확인**: PreToolUse 차단 제외, Instinct 학습 제외, 외부 스크립트 금지 — 유지
- **스코프 추가 제안**: HI-04 신설은 동일 카테고리 내 1항목 추가라 범위 초과 아님. 승인.
- **하위호환**: hooks 필드가 `{}` 또는 부재 시 settings.json validate 통과 확인 필요 (Step 1 테스트)

### Domain Lead
- 도메인별 훅 프로파일은 Phase 4 (Layered Override)로 이관 — 계획서와 동일
- fintech의 감사 로그 훅은 Phase 4 설계 시 `.claude/domains/fintech/hooks/` 후보

---

## 4. 실패/경계값 시나리오 (H012~H016 대응)

| # | 시나리오 | 기대 동작 |
|---|---------|---------|
| 1 | `jq` 미설치 환경 | 스크립트 첫 줄에서 `command -v jq >/dev/null || exit 0` + stderr 경고 |
| 2 | backlog.json 깨진 JSON | `jq` 실패 → `exit 0` (훅이 세션을 망가뜨리지 않음) |
| 3 | flock 미지원 (Windows WSL 등) | mkdir 폴백 뮤텍스로 degrade, 경고 로그 |
| 4 | PostToolUse 재귀 10회 이상 | 3회 시점에 이미 hook-disabled.flag로 차단됨 (테스트로 증명) |
| 5 | Stop 훅이 `stop_hook_active: true` 수신 | 즉시 exit 0 (공식 메커니즘 준수) |
| 6 | 워크트리 2개 동시 Write | flock으로 직렬화, `lockedAt` 최신 값 보존 |
| 7 | Claude Code 구버전 (hooks 필드 미지원) | settings.json의 hooks 필드 무시됨 + v1.x 동작 유지 |
| 8 | 훅 스크립트에 실행 권한 없음 | Claude Code가 실행 실패 → 에러 로그 + 세션 계속 (Step 2 검증) |

---

## 5. 계획서 수정 요약

다음 항목을 [phase-1-plan.md](./phase-1-plan.md)에 반영 필요:

1. **"데이터 모델" 섹션**: hooks 스키마를 2층 구조(matcher/hooks)로 수정, `excludePaths` 커스텀 필드 제거
2. **"무한 루프 방어 3단계"**: 2단계를 환경변수 → **파일 락**으로 교체
3. **Step 3 상세**: 스크립트 첫 줄에서 stdin JSON 파싱하여 경로 필터링, flock 기반 원자적 쓰기
4. **Step 2 상세**: Stop 훅이 `stop_hook_active` 체크 + 60초 디바운스 + 조건부 continuation-plan 생성
5. **Step 5 (Hook Integrity Audit)**: HI-04 신설 — `exit 2`/`set -e` 정적 검사 (MAJOR)
6. **리스크 표**: R1~R6 재분류, `exit code 오용`과 `워크트리 race` 명시적 추가

---

## 6. Step 1 착수 Go/No-Go 체크

- [x] Claude Code 훅 스펙 공식 문서 확인 완료
- [x] 6개 주요 리스크 식별 + 대응 방안 확정
- [x] 5인 TFT 분석 완료
- [x] 실패 시나리오 8개 도출
- [x] 계획서 수정 항목 리스트업
- [ ] 계획서 반영 (본 문서 작성 후 즉시 수행)
- [ ] 사용자 최종 승인 (Step 1 PR 생성 전)

**결론**: Step 1 착수 준비 완료. 단 계획서 먼저 패치.
