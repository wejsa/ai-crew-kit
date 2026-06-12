<!-- PARITY: 이 문서는 merge-gate-explained.md(영문)와 페어 — 한쪽 수정 시 반드시 동시 갱신 -->

# 머지 게이트 해설 (Merge Gate Explained)

> [← README로 돌아가기](../README.ko.md) · [English](./merge-gate-explained.md) · 직접 체험: [examples/merge-gate-demo](../examples/merge-gate-demo/README.ko.md)

**요약** — AI Crew Kit은 마지막 리뷰가 미해결 CRITICAL을 게시한 PR의 `gh pr merge`를
차단합니다. 이 차단은 프롬프트도, 컨벤션도, 모델에게 따르라고 부탁하는 지시문도
아닙니다 — **명령이 실행되기 전에 exit 2를 내는 bash PreToolUse 훅**입니다. Claude는
말로 통과할 수 없고, 세션 안에서 우회할 수도 없습니다.

---

## 1. 문제: prose는 강제가 아니다

모든 AI 코딩 워크플로우에는 이런 규칙이 있습니다:

> *"리뷰에서 CRITICAL 이슈가 발견되면 PR을 머지하지 마라."*

대부분의 프레임워크에서 이 규칙은 프롬프트 안에 삽니다. 모델이 읽고, 대개는 따르지만 —
가끔은 따르지 않습니다. 긴 지시 파일, 압축된 컨텍스트 윈도, 애매한 리뷰 요약, 그리고
분기 하나를 잘못 타면, 알려진 CRITICAL 결함이 있는 PR이 자동 머지됩니다. 누구도 그걸
선택하지 않았는데, prose가 버텨주지 못한 것뿐입니다.

AI Crew Kit은 이 규칙을 prose에 맡기기엔 너무 중요하다고 봅니다. 머지 결정은 Claude
Code 세션에서 완전히 결정적인 단 하나의 레이어 — **훅**에 위임됩니다.

```
Claude가 실행하려는 명령:  gh pr merge 42 --squash
        │
        ▼
PreToolUse 훅 (bash) ── .claude/state/backlog.json을 읽음
        │                GitHub reviewDecision을 읽음 (best-effort)
        │
        ├── 미해결 CRITICAL?  ──► exit 2  ──► 명령은 결코 실행되지 않음
        │                                      Claude는 거부 사유를 전달받음
        └── 그 외             ──► exit 0  ──► 명령 정상 진행
```

훅은 `.claude/hooks/pre-tool-use.sh`(~180줄의 평범한 bash)입니다. `Bash` 도구 매처에
등록되어 `gh pr merge` 외의 모든 명령은 무시하며, LLM을 호출하지 않습니다.

이 훅이 kit의 훅 분류 체계(bookkeeping vs gate, bookkeeping 훅이 절대 차단하면 안 되는
이유)에서 차지하는 위치는 [`.claude/hooks/README.md`](../.claude/hooks/README.md)의
SSOT 표를 참조하세요 — 여기에 복제하지 않습니다.

---

## 2. 판정 방식: 세 개의 신호

### 신호 A — 워크플로우 상태 (오프라인, 결정적)

kit의 리뷰 스킬은 판정을 `backlog.json`에 기록합니다. 게이트는 머지하려는 PR을
*소유한* Task를 찾아 그 판정을 읽습니다:

```jq
.tasks[]?
| select(
    (.workflowState.prNumber // -1) == $n          # 리뷰 워크플로우가 기록
    or any((.steps // [])[]?; (.prNumber // -1) == $n)   # PR 생성 시점에 기록 (SSOT)
  )
| .workflowState.lastReviewDecision
```

소유 Task의 `lastReviewDecision`이 정확히 `"REQUEST_CHANGES"`이면 머지가 차단됩니다.
중요한 디테일 둘:

- **join이 이중 키입니다.** PR 번호는 PR 생성 시(`steps[].prNumber`)와 리뷰
  워크플로우(`workflowState.prNumber`) 두 곳에 기록되며, 게이트는 둘 중 어느 쪽이든
  매칭합니다.
- **타입이 엄격합니다.** `prNumber`는 JSON 정수여야 합니다. 스키마가 `"42"`(문자열)를
  거부하고, 게이트의 `jq --argjson` 비교도 매칭하지 않습니다. `backlog.schema.json`이
  CI에서 강제합니다.

신호 A는 **네트워크도, GitHub 계정도, 실제 PR도 필요 없습니다.** 그래서
[5분 데모](../examples/merge-gate-demo/README.ko.md)가 가능합니다: fixture 파일
하나면 게이트를 발동시킬 수 있습니다.

### 신호 A2 — transient 리뷰 결정 (오프라인, 결정적; v4.8.0)

어떤 PR은 정당하게 backlog Task가 없습니다 — 긴급 핫픽스(`/aick-hotfix`)나, kit이
계획한 적 없는 PR에 대한 ad-hoc "PR 123 리뷰해줘" 같은 경우입니다. 이런 PR의 판정은
리뷰하는 스킬이 `.claude/state/review-decisions.json`에 기록합니다(키 = PR 번호;
형식은 [`review-decisions.schema.json`](../.claude/schemas/review-decisions.schema.json)이
고정):

```json
{ "42": { "decision": "REQUEST_CHANGES", "source": "aick-hotfix", "updatedAt": "…" } }
```

머지하려는 PR의 엔트리가 `REQUEST_CHANGES`면 차단됩니다 — 신호 A와 동일한 오프라인·
결정적 의미론입니다. 엔트리는 머지 성공 시 삭제되고, 재리뷰가 덮어씁니다. A2를
정직하게 유지하는 스코프 규칙 둘:

- **A2는 backlog Task가 소유하지 않은 PR에서만 평가됩니다.** Task가 소유하는 순간
  backlog(신호 A)가 단일 진실 소스입니다 — 과거 ad-hoc 리뷰의 stale transient 엔트리가
  더 새로운 backlog 결정을 이길 수 없습니다.
- 이 파일은 **로컬 전용**(gitignore)입니다: 판정은 리뷰가 돌았던 머신을 보호하며,
  다른 클론에는 전파되지 않습니다 — §7 참조.

### 신호 B — GitHub 리뷰 결정 (best-effort, 네트워크)

두 상태 신호가 모두 차단하지 않으면 게이트는 GitHub에 묻습니다:

```bash
timeout 8 gh pr view <N> --json reviewDecision
```

GitHub가 `CHANGES_REQUESTED`를 보고하면 — 예컨대 로컬 backlog 상태가 없는 동료의
PR에 사람 리뷰어가 변경을 요청한 경우 — 역시 차단됩니다. 여기서의 모든 실패(gh 부재,
네트워크, 인증, 타임아웃)는 조용히 무시됩니다: 신호 B는 추가 안전망이지 의존성이
아닙니다. `CCK_GATE_NO_GH=1`로 전면 스킵할 수 있습니다(에어갭 환경, 테스트 결정성).

신호는 A → A2 → B 순으로 평가되고, 첫 차단이 이깁니다 — 이후 신호는 조회되지
않습니다. allow 판정이 차단을 덮지 못합니다: 게이트는 차단들의 OR입니다.

---

## 3. Fail-open 설계 철학

게이트의 일은 하나입니다: *신호가 명확히 "차단"을 가리킬 때 머지를 막는 것.* 두 번째
일 — 게이트 자신이 고장 났을 때 당신의 워크플로우를 망가뜨리는 것 — 은 거부합니다.
모든 인프라 실패는 **allow**로 귀결됩니다:

| # | 조건 | 동작 |
|---|------|------|
| 1 | `CCK_MERGE_GATE=off` (`false`/`0`/`no` 포함) | 게이트 비활성 — allow |
| 2 | 프로젝트 디렉토리 접근 불가 | allow |
| 3 | 하네스로부터 stdin 입력 없음 | allow |
| 4 | `timeout` 바이너리 부재 (stdin 읽기에 사용) | allow |
| 5 | `jq` 미설치 | allow |
| 6 | 도구 입력에 명령 문자열 없음 | allow |
| 7 | 명령이 `gh pr merge`가 아님 | allow (관심 밖) |
| 8 | `CCK_GATE_BYPASS=1` | allow — **로그 + 배너** |
| 9 | PR 번호 추출 불가 (예: 번호 없는 current-branch 머지) | allow — 로그 |
| 10 | `backlog.json` 부재 | 신호 A 스킵 |
| 11 | `backlog.json` 파싱 불가 | 신호 A 스킵 |
| 12 | 이 PR을 소유한 Task 없음 / 결정이 `APPROVED`·`COMMENT`·null | 차단 없음 |
| 13 | `review-decisions.json` 부재, 파싱 불가, 또는 이 PR의 엔트리 없음 | 신호 A2 스킵 |
| 14 | 신호 B: gh 부재, 네트워크/인증 실패, 8초 타임아웃, `CCK_GATE_NO_GH=1` | 신호 B 스킵 |

왜 fail-closed가 아닌가? `jq`가 없다고 머지를 막는 게이트는 자기 의존성의 대가를
사용자에게 물리는 것이고, 사람들이 끄는 법부터 배우는 게이트는 게이트가 없는 것보다
나쁘기 때문입니다. 트레이드오프는 명시적입니다: **성능이 저하된 게이트는 조용합니다.**
데모에서 "아무 일도 안 일어나면" 위 표를 순서대로 점검하세요 — 데모의
[트러블슈팅 섹션](../examples/merge-gate-demo/README.ko.md)이 정확히 그걸 합니다.

---

## 4. 우회와 제어

환경변수 셋, 의도도 셋:

| 변수 | 의도 | 범위 |
|------|------|------|
| `CCK_GATE_BYPASS=1` | *"이해했고, 그래도 머지한다."* 의도적 1회 우회. 감사 로그에 기록되고 🔓 배너로 알림. | 전체 우회 |
| `CCK_MERGE_GATE=off` | *"이 게이트를 아예 돌리지 마라."* | 전면 비활성 |
| `CCK_GATE_NO_GH=1` | *"네트워크를 절대 부르지 마라."* 신호 A·A2는 여전히 강제. | 부분 — 신호 B만 비활성 |

알아둘 가치가 있는 속성: **우회는 세션 안에서 발동시킬 수 없습니다.** 훅은 *자기*
프로세스 환경 — Claude Code가 시작될 때의 환경 — 을 읽습니다. 명령 문자열 접두
(`CCK_GATE_BYPASS=1 gh pr merge 42`)나 이전 Bash 호출의 `export`는 훅 프로세스에
도달하지 않으므로 머지는 여전히 차단됩니다. 실제로 우회하려면 사람이 직접
`CCK_GATE_BYPASS=1 claude`로 CLI를 재시작하거나 `settings.json` `env`에 넣어야 합니다.
다시 말해: *Claude는 자기 머지 게이트를 우회할 수 없습니다 — 오직 당신만 할 수 있습니다.*

---

## 5. 감사 로그

게이트의 의미 있는 이벤트는 전부 `.claude/state/hook-errors.log`에 누적됩니다:

```
[2026-06-11T09:14:02Z] [pre-tool-use] merge blocked: PR #42 — backlog: last review decision is REQUEST_CHANGES (unresolved CRITICAL posted)
[2026-06-11T09:16:40Z] [pre-tool-use] merge gate bypassed (CCK_GATE_BYPASS) — cmd: gh pr merge 42 --squash
```

차단과 우회가 모두 기록되므로 "누가 언제 게이트를 넘었나"를 사후에 답할 수 있습니다.
(PR 번호 추출 실패도 기록됩니다 — fail-open이기 때문입니다.)

---

## 6. Standalone으로 직접 실행해 보기 (Claude 세션 불필요)

훅은 stdin으로 JSON을 읽는 평범한 bash라, 이 리포 체크아웃에서 직접 돌려볼 수
있습니다:

```bash
# ai-crew-kit 리포 루트에서
D=$(mktemp -d) && mkdir -p "$D/.claude/state"
cp examples/merge-gate-demo/.claude/state/backlog.json "$D/.claude/state/"

# 차단: fixture의 PR 42에는 미해결 CRITICAL이 있음
echo '{"tool_input":{"command":"gh pr merge 42 --squash"}}' \
  | CLAUDE_PROJECT_DIR="$D" CCK_GATE_NO_GH=1 bash .claude/hooks/pre-tool-use.sh; echo "exit=$?"   # → 2

# 허용: PR 99는 누구의 것도 아님
echo '{"tool_input":{"command":"gh pr merge 99"}}' \
  | CLAUDE_PROJECT_DIR="$D" CCK_GATE_NO_GH=1 bash .claude/hooks/pre-tool-use.sh; echo "exit=$?"   # → 0
```

fixture(아래는 스냅샷 — 정본은
[`examples/merge-gate-demo/.claude/state/backlog.json`](../examples/merge-gate-demo/.claude/state/backlog.json))는
스텝이 PR #42를 만들고 리뷰가 `REQUEST_CHANGES`를 기록한 Task 하나입니다:

```json
{
  "steps": [{ "number": 1, "title": "Rate limiter middleware", "status": "pr_created", "prNumber": 42 }],
  "workflowState": { "prNumber": 42, "lastReviewDecision": "REQUEST_CHANGES" }
}
```

게이트의 동작은 회귀 스위트로 고정되어 있습니다 —
[`.claude/hooks/tests/test-pre-tool-use-merge-gate.sh`](../.claude/hooks/tests/test-pre-tool-use-merge-gate.sh)가
차단·허용·우회·fail-open 경로, transient 결정(신호 A2 — 소유 스코프 포함), PR 번호 추출 엣지 케이스(URL, 플래그, 임베드 숫자,
선행 0)를 커버하며 CI에서 실행됩니다.

---

## 7. 게이트가 하지 않는 것 (정직한 한계)

결정적 게이트는 그것이 놓인 경계만큼만 좋습니다. 가장자리를 아세요:

- **결정을 강제하지, 신호를 강제하지 않습니다.** 신호 A·A2는 리뷰 워크플로우가
  *기록한* 상태를 읽습니다. 리뷰가 아예 돌지 않았거나 결정을 기록하지 않았다면 상태
  신호에는 강제할 것이 없고 신호 B로 폴백합니다. 게이트는 "기록된 CRITICAL에도
  불구하고 머지"를 불가능하게 만들 뿐, 일어나지 않은 리뷰를 만들어내지는 않습니다.
  (v4.8.0부터 SessionStart 훅이 게이트를 무력화하는 데이터 결함 — 문자열 `prNumber`,
  결정 미기록 리뷰 — 을 경고하므로, 조용한 fail-open이 최소한 보이게는 됩니다.)
- **Claude의 Bash 도구를 지키지, 당신의 터미널을 지키지 않습니다.** Claude Code 밖의
  셸에서 직접 치는 `gh pr merge 42`는 개입 대상이 아닙니다 — 이건 Claude Code 훅이지
  서버 측 규칙이 아닙니다. 팀 전체의 강한 강제가 필요하면 GitHub branch protection과
  결합하세요. 게이트는 세션 내 레이어입니다.
- **신호 A2는 로컬 전용입니다.** 핫픽스·ad-hoc 리뷰 판정(v4.8.0 — 이 경로들은 이전엔
  게이트를 완전히 우회했습니다)은 gitignore된 파일에 살며, 리뷰가 돌았던 머신만
  보호합니다 — 다른 클론이나 동료의 세션은 보호하지 않습니다. 머신 간 강제는 여전히
  신호 B + branch protection의 몫입니다.
- **롤백(`/aick-rollback`)은 설계상 게이트 밖에 남습니다**: 리뷰 단계 자체가 없습니다 —
  이미 리뷰된 코드의 감사 추적되는 `git revert`이며, 빌드/테스트로 게이트됩니다.
- **우회는 기능입니다.** `CCK_GATE_BYPASS=1`은 의도적으로 존재하고, 사람 전용이며(§4),
  기록됩니다. 의도적 출구가 없는 게이트는 사람들에게 게이트를 영구히 끄는 법을
  가르칩니다.

---

## 8. FAQ

**데모에서 아무 일도 안 일어났어요 — 머지가 그냥 통과됐는데요?**
fail-open 표(§3)를 순서대로 점검하세요: ① `command -v jq timeout` — 둘 다 있어야 합니다.
② `env | grep CCK_` — 남아 있는 `CCK_MERGE_GATE=off`나 `CCK_GATE_BYPASS=1`이 조용히
allow시킵니다. ③ Claude 세션을 **`.claude/state/backlog.json`이 있는 디렉토리 안에서**
시작해야 합니다 — 훅은 세션의 프로젝트 루트(`CLAUDE_PROJECT_DIR`)에서 상태를 읽으므로,
세션 도중 데모 폴더로 `cd`하는 것은 소용없습니다. ④ `.claude/state/hook-errors.log`에서
추출 실패 항목을 확인하세요.

**차단에 네트워크가 필요한가요?**
아니요. 신호 A는 순수 로컬 파일 읽기입니다 — 데모는 네트워크 호출 0회로 ~50ms에
차단합니다. 신호 B만 네트워크를 쓰고, best-effort이며, `CCK_GATE_NO_GH=1`로 스킵
가능합니다.

**Claude가 `CCK_GATE_BYPASS=1`을 설정하고 머지할 수 있나요?**
아니요. 인라인 접두와 세션 내 `export`는 훅의 프로세스 환경에 도달하지 않습니다(§4).
유일하게 유효한 경로 — 변수와 함께 CLI를 재시작 — 는 사람의 행동입니다.

**왜 권한 프롬프트가 아니라 `exit 2`인가요?**
PreToolUse 훅의 `exit 2`는 Claude Code의 deny 계약입니다: 도구 호출이 거부되고 stderr가
사유로 Claude에 전달됩니다. 모델은 *왜* 막혔는지 보고, 제안된 다음 단계(수정 후 재리뷰,
또는 우회 요청)에 따라 행동할 수 있습니다.

**프레임워크 전체가 이만큼 결정적인가요?**
아니요, 그렇게 포장하지도 않을 겁니다. 머지 게이트, lock 하트비트/만료, 스키마 검증,
훅 안전성 정적 검사는 결정적이고, 대부분의 워크플로우 스텝은 여전히 LLM이 따르는
지시문입니다. kit의 설계 원칙은 *가장 위험한* 결정부터 결정론 레이어로 옮기는 것이고 —
머지 게이트가 그 접근의 기함입니다.

---

*함께 보기: [examples/merge-gate-demo](../examples/merge-gate-demo/README.ko.md) (5분 실습) ·
[`.claude/hooks/README.md`](../.claude/hooks/README.md) (훅 분류 SSOT) ·
[워크플로우 가이드](./workflow-guide.md) (리뷰 판정이 만들어지는 곳).*
