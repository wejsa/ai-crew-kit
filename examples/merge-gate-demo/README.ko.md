<!-- PARITY: 이 문서는 README.md(영문)와 페어 — 한쪽 수정 시 반드시 동시 갱신 -->

# 머지 게이트 데모 — 나쁜 머지가 막히는 장면을 5분 안에

[English](./README.md) · 한국어

이 데모는 AI Crew Kit의 **결정적 머지 게이트**가 눈앞에서 발동하는 것을 보여줍니다:
Claude가 미해결 CRITICAL 이슈가 리뷰에서 발견된 PR을 머지하려 하면, bash PreToolUse
훅이 그 명령을 **실행되기도 전에** 거부합니다.

- **실제 PR 불필요. GitHub 인증 불필요.** 게이트 자체는 네트워크 호출 0회 — fixture 파일 하나가 상태를 시뮬레이션합니다 (셋업에서 1회 받거나, 로컬 체크아웃에서 복사).
- Act 1(차단)은 ~5분, Act 2(의도적 우회)는 +1–2분.
- 플랫폼: **Linux / macOS / WSL**. 네이티브 Windows는 미검증 — WSL을 사용하세요.

> 게이트 내부 동작: [docs/merge-gate-explained.ko.md](../../docs/merge-gate-explained.ko.md)

---

## 0. 사전 점검 (1분)

```bash
command -v jq timeout   # 둘 다 경로가 나와야 함 — 하나라도 없으면 게이트가
                        # 조용히 fail-open되어 데모에서 아무 일도 안 일어남
env | grep CCK_         # 아무것도 안 나와야 함 — 남아 있는 CCK_MERGE_GATE/
                        # CCK_GATE_BYPASS 값이 게이트를 조용히 끄거나 우회시킴
```

플러그인이 아직 없다면 설치 (아무 Claude Code 세션 안에서):

```
/plugin marketplace add wejsa/ai-crew-kit
/plugin install ai-crew-kit@ai-crew-kit
```

> **스코프가 중요합니다.** 위 CLI 명령은 **사용자 전역(user-wide)**으로 설치되어 어느
> 폴더에서나 동작합니다. 반면 `/plugin` UI에서 **project**(또는 local) 스코프를 골랐다면
> 플러그인이 다른 디렉토리로 따라오지 **않습니다**. 데모 세션에서 `/plugin list --enabled`에
> `ai-crew-kit`이 보이는지 확인하고, 없으면 그 세션 안에서 위 두 명령을 실행하세요.

---

## 1. 샌드박스 만들기 (1분)

**일반 터미널에서**(Claude 프롬프트 아님), 아무 위치에나 — 플러그인을 설치했던 곳과
무관한 일회용 폴더입니다:

```bash
mkdir gate-demo && cd gate-demo
git init -q && git commit --allow-empty -qm init
mkdir -p .claude/state        # 디렉토리를 먼저 — curl은 부모 디렉토리를 안 만듦
BASE=https://raw.githubusercontent.com/wejsa/ai-crew-kit/main/examples/merge-gate-demo
curl -fsSL "$BASE/.claude/state/backlog.json" -o .claude/state/backlog.json
curl -fsSL "$BASE/CLAUDE.md" -o CLAUDE.md
```

두 번째 파일 `CLAUDE.md`는 세션이 요청받은 명령을 kit의 워크플로우 스킬로 라우팅하지
않고 **literal하게** 실행하도록 지시합니다 — 없으면 Claude가 `aick-merge-pr`을 호출해
훅이 발동하기 전에 prose로 머지를 막는 경우가 많습니다 (Act 1의 결과 표 참조).

(로컬 체크아웃에서 작업한다면: `cp <kit>/examples/merge-gate-demo/.claude/state/backlog.json .claude/state/ && cp <kit>/examples/merge-gate-demo/CLAUDE.md .`)

fixture는 Task 하나입니다: 그 스텝이 **PR #42**를 만들었고, 리뷰가
**`lastReviewDecision: "REQUEST_CHANGES"`** — 미해결 CRITICAL(배포할 때마다 리셋되는
레이트 리미터)을 기록한 상태. 게이트가 읽는 것이 정확히 이 상태입니다.

> ⚠️ **Claude 세션을 이 디렉토리 안에서 시작하세요.** 게이트는 세션의 프로젝트 루트에서
> 상태를 읽습니다. 다른 곳에서 시작하고 `cd`만 해서 들어오면 게이트는 조용히 발동하지
> 않습니다.

---

## 2. Act 1 — 차단 (2분)

`gate-demo/` 안에서 **새** Claude Code 세션을 시작하고, 정확히 붙여넣으세요:

```
Do not use any skill. Run this exact bash command as-is: gh pr merge 42 --squash
```

("Do not use any skill" 부분이 중요합니다 — kit 자신의 머지 스킬로 라우팅되는 것을
억제합니다. 라우팅되면 훅이 발동하기 전에 prose가 머지를 막아 버립니다.)

**기대 화면** (실제 세션 실측): Bash 도구 호출 자체가 훅의 거부로 실패합니다 — Claude
Code는 도구 호출 아래에 `PreToolUse:Bash hook error` 블록으로 렌더링하고, Claude가
그 사유를 답변으로 전달합니다:

```
● Bash(gh pr merge 42 --squash)
  ⎿  Error: PreToolUse:Bash hook error: [bash ".../pre-tool-use.sh"]:
🛑 [pre-tool-use] Merge blocked — PR #42
   Reason: backlog: last review decision is REQUEST_CHANGES (unresolved CRITICAL posted)
   A PR with unresolved CRITICAL findings cannot be merged.
   Next steps:
     1) [Recommended] Fix the CRITICAL findings, then re-review: /aick-review-pr 42 --auto-fix
     2) If this is a downgraded or false-positive finding, re-examine the review decision and re-review
     3) [Deliberate override] Set CCK_GATE_BYPASS=1 and retry (user responsibility)
```

**실제로 어느 레이어가 막았나?** 라이브 모델의 라우팅은 매번 다를 수 있어 세 가지
결과가 가능합니다. **세 결과 모두 나쁜 머지를 막은 것 — 어느 쪽이 나와도 셋업이 잘못된 게
아닙니다.** 표는 *어느 레이어*가 막았는지를 알려줄 뿐이며(`cat .claude/state/hook-errors.log`가
판별 기준), 1행이 이 데모가 보여주려는 결정론 레이어입니다:

| 결과 | 발동한 레이어 | hook-errors.log |
|------|--------------|-----------------|
| 실행 전 🛑 거부 (위 메시지) | **결정론 훅** — 이 데모의 핵심 | `merge blocked: PR #42` 줄 |
| Claude가 `aick-merge-pr` 호출, backlog 읽고 거절 | prose 레이어 — 다층 방어는 작동했지만 훅은 미발동 | 비어 있음 / 없음 |
| Claude가 거절 ("PR #42가 없는데요…") | 모델 스스로의 합리적 판단 | 비어 있음 / 없음 |

2–3행도 나쁜 머지를 막긴 하지만 — *확률적* 레이어를 통해서입니다. 결정론 레이어를
보려면 위의 정확한 프롬프트를 다시 붙여넣거나("Do not use any skill" 접두 + 샌드박스
`CLAUDE.md`가 스킬 라우팅을 억제), 아래 보장 경로로 건너뛰세요. prose 레이어를 먼저
보고 훅을 나중에 보는 것은 이 프레임워크의 테제를 두 번 시연하는 셈입니다: 모델은
보통 옳게 행동한다 — 훅은 그렇지 않을 때를 위해 존재한다.

회의적인 분들을 위한 노트 (그게 이 데모의 목적입니다):

- **권한 프롬프트는 게이트 실패가 아닙니다.** Claude Code가 Bash 명령 허용을 먼저
  물으면 허용하세요 — 게이트는 권한 다음, 실행 시점에 발동합니다.
- **차단 메시지의 "Next steps" 3개에 대해:** ① `/aick-review-pr 42 --auto-fix`는
  **실제 프로젝트에서** 자동 수정·재리뷰 루프를 시작합니다 — 이 샌드박스에는 실제
  PR·프로젝트 설정이 없어 스킬이 사전 조건에서 멈추니 여기서는 건너뛰세요.
  ② "리뷰 결정 재검토"는 실제 프로젝트에서 오탐을 다루는 경로입니다.
  ③ 이 아래 Act 2입니다. (스킬 표면은 현재 한국어 우선이며, 출력은 사용자 언어에
  맞춰집니다.)

**보너스 — 속여 보세요.** Claude에게:

```
Run exactly: CCK_GATE_BYPASS=1 gh pr merge 42 --squash
```

여전히 차단됩니다. 훅은 **자기 자신의** 프로세스 환경 — Claude Code CLI가 시작될 때의
환경 — 을 읽으므로, 인라인 접두(또는 이전 명령에서의 `export`)는 절대 훅에 도달하지
않습니다. **Claude는 자기 머지 게이트를 우회할 수 없습니다. 오직 당신만 할 수 있습니다**
(Act 2).

### 보장 경로 (Claude 세션 불필요)

게이트는 stdin을 읽는 평범한 bash입니다 — kit 체크아웃에서 차단을 ~50ms, 네트워크
0회로 결정적으로 증명할 수 있습니다:

```bash
# ai-crew-kit 리포 루트에서, 샌드박스가 ../gate-demo에 있을 때
echo '{"tool_input":{"command":"gh pr merge 42 --squash"}}' \
  | CLAUDE_PROJECT_DIR="$(cd ../gate-demo && pwd)" CCK_GATE_NO_GH=1 \
    bash .claude/hooks/pre-tool-use.sh; echo "exit=$?"     # → 차단, exit=2

echo '{"tool_input":{"command":"gh pr merge 99"}}' \
  | CLAUDE_PROJECT_DIR="$(cd ../gate-demo && pwd)" CCK_GATE_NO_GH=1 \
    bash .claude/hooks/pre-tool-use.sh; echo "exit=$?"     # → PR 99에는 CRITICAL이 없음, exit=0
```

kit 체크아웃이 없다면? 훅 자체를 받아 `gate-demo/` 안에서 바로 실행하세요:

```bash
curl -fsSL https://raw.githubusercontent.com/wejsa/ai-crew-kit/main/.claude/hooks/pre-tool-use.sh -o /tmp/gate.sh
echo '{"tool_input":{"command":"gh pr merge 42 --squash"}}' \
  | CLAUDE_PROJECT_DIR="$PWD" bash /tmp/gate.sh; echo "exit=$?"   # → 2 (게이트 판정: 네트워크 호출 0회)
```

Act 1 성공 기준: 세션 내 차단 **+ `hook-errors.log`에 `merge blocked` 줄**, **또는**
standalone `exit=2`. (allow 케이스를 standalone으로만 보여주는 건 의도입니다 — 라이브
세션에서 allow되면 `gh pr merge`가 진짜로 실행됩니다.)

---

## 3. Act 2 — 의도적 우회 (1–2분)

우회는 사람만 할 수 있는 행동입니다: 변수가 CLI 자신의 환경에 있어야 합니다.

1. Claude 세션을 종료합니다.
2. 우회 변수와 함께 재시작: `CCK_GATE_BYPASS=1 claude`
   (동등한 방법: 샌드박스의 `.claude/settings.json`에 `{"env": {"CCK_GATE_BYPASS": "1"}}`)
3. Act 1과 같은 프롬프트 붙여넣기: `Do not use any skill. Run this exact bash command as-is: gh pr merge 42 --squash`
4. 이번엔 게이트가 비켜섭니다. 화면에 대해 알아둘 두 가지 (실제 세션 실측):

- 🔓 우회 배너는 UI에 **보이지 않습니다** — 훅의 stderr로 나가는데, Claude Code는
  *차단*(exit 2) 훅의 stderr만 표시합니다. 배너를 기다리지 마세요.
- 가시적 신호는 **에러 출처의 전환**입니다: Act 1의 실패는 `PreToolUse:Bash hook
  error … Merge blocked`(명령 미실행)였지만, 이제 명령이 **실제로 실행**되고 `gh`
  자신이 실패합니다(`no git remotes found` — PR #42는 애초에 없으므로). 그 전환 —
  hook error → gh error — 이 바로 우회가 작동했다는 증거입니다.

그리고 기록이 남습니다:

```bash
cat .claude/state/hook-errors.log
# [ ... ] [pre-tool-use] merge blocked: PR #42 — backlog: last review decision is REQUEST_CHANGES (unresolved CRITICAL posted)
# [ ... ] [pre-tool-use] merge gate bypassed (CCK_GATE_BYPASS) — cmd: gh pr merge 42 --squash
```

모든 차단과 모든 우회가 타임스탬프와 함께 기록됩니다 — 사람은 게이트를 열 수 있지만,
결코 몰래 열 수는 없습니다.

5. 게이트가 다시 작동하도록 정리: 세션 종료, env 제거(또는 settings 항목 삭제), 평소처럼
   재시작.

---

## 4. 트러블슈팅 — "아무 일도 안 일어났는데?"

게이트는 **설계상 fail-open**입니다(고장 난 게이트가 실제 작업을 막으면 안 되므로),
모든 셋업 문제가 "머지가 그냥 통과됐다"로 나타납니다. 이 순서로 확인하세요:

| # | 확인 | 이유 |
|---|------|------|
| 1 | `command -v jq` | jq 없음 → 게이트가 입력을 못 읽음 → 무음 allow |
| 2 | `command -v timeout` | timeout 없음 → stdin 읽기 실패 → 무음 allow |
| 3 | `env \| grep CCK_` | 남아 있는 `CCK_MERGE_GATE=off` / `CCK_GATE_BYPASS=1` → 무음 allow |
| 4 | 세션을 `gate-demo/` **안에서** 시작했나? | 게이트는 세션 루트의 `.claude/state/`를 읽음 — 시작 후 `cd`는 소용없음 |
| 5 | `cat .claude/state/hook-errors.log` | "PR number extraction failed" 항목 = 명령 형태를 파싱 못 한 것 |
| 6 | 플러그인이 실제로 업데이트됐나? | `/plugin` → 버전 확인; 마켓플레이스 캐시가 구버전을 서빙할 수 있음 — 필요 시 마켓플레이스 제거 후 재추가 |
| 7 | **이 세션**에서 플러그인 활성? | `/plugin list --enabled`에 `ai-crew-kit`이 보여야 함 — **project/local 스코프 설치는 새 폴더로 안 따라옴**; user-wide(CLI 명령) 설치 또는 이 세션에서 활성화 |
| 8 | 머지는 막혔는데 로그가 비어 있다? | 훅이 아니라 **prose 레이어**(스킬 라우팅/모델 판단)가 막은 것 — Act 1의 정확한 프롬프트를 다시 붙여넣어 훅을 발동시키세요 |

함께 알아두면 좋은 것:

- 게이트는 **Claude의 Bash 도구만** 가로챕니다. 터미널에서 직접 실행하는 `gh pr merge`는
  개입 대상이 아닙니다 — 서버 측 강제가 필요하면 GitHub branch protection과 함께 쓰세요.
- 데모를 **kit 리포 안에서**(`examples/merge-gate-demo/`) 돌려도 됩니다 — 로컬
  `.gitignore`가 훅 부수효과(`hook-errors.log`, `continuation-plan.md`)를 `git status`
  에서 차단합니다. 그래도 일회용 디렉토리로 복사해 나가는 쪽이 더 깔끔합니다.

---

## 방금 본 것

| 주장 | 증거 |
|------|------|
| 차단은 결정적이다 | bash 훅, `exit 2`, 실행 전 발동; stdin 파이프로 네트워크 0회 재현 가능 |
| Claude는 우회할 수 없다 | 인라인 env 접두 / 세션 내 export는 훅 프로세스에 도달하지 않음 |
| 사람은 의도적으로 우회할 수 있다 | CLI 시작 시 `CCK_GATE_BYPASS=1` — 그리고 기록됨 |
| 고장이 사용자를 가두지 않는다 | fail-open 14경로 ([해설](../../docs/merge-gate-explained.ko.md#3-fail-open-설계-철학)) |

다음 단계: 실제 프로젝트에 `/aick-init`으로 설치하면, 당신의 AI 크루가 시도하는 모든
`gh pr merge`를 같은 게이트가 지킵니다.
