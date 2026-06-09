# Cowork / Claude Code 플러그인으로 설치하기

AI Crew Kit는 리포 clone 방식 외에 **Claude Code · Cowork 플러그인**으로도 설치할 수 있습니다.
이 리포 자체가 곧 마켓플레이스이자 단일 플러그인입니다 (`.claude-plugin/marketplace.json` + `.claude-plugin/plugin.json`).

플러그인으로 설치하면 clone 없이도 22개 스킬(`/aick-status`, `/aick-impl` 등)과 12개 서브에이전트, 품질 게이트 훅이 현재 작업 중인 프로젝트에서 바로 사용 가능해집니다.

---

## 1. 설치

### Cowork (데스크톱 앱)

1. Cowork 설정 → **Capabilities / Plugins** 에서 마켓플레이스 추가
2. 마켓플레이스 소스로 이 리포를 지정: `wejsa/ai-crew-kit`
3. 목록에서 **ai-crew-kit** 플러그인을 설치(enable)

### Claude Code (CLI)

```bash
# 1) 마켓플레이스 등록 (GitHub 리포를 마켓플레이스로 추가)
/plugin marketplace add wejsa/ai-crew-kit

# 2) 플러그인 설치
/plugin install ai-crew-kit@ai-crew-kit

# 변경 반영 / 업데이트
/plugin marketplace update ai-crew-kit
```

> 로컬에서 먼저 검증하려면 clone 후 로컬 경로로 추가합니다:
> `/plugin marketplace add ./ai-crew-kit` → `/plugin install ai-crew-kit@ai-crew-kit`
> 매니페스트 검증: `claude plugin validate ./ai-crew-kit --strict`

---

## 2. 매니페스트 구조

| 컴포넌트 | 로드 경로 | 동작 |
|----------|----------|------|
| 스킬 (22) | `skills` 필드 → `./.claude/skills/` (디렉토리 문자열) | 기본 `skills/`에 **추가** — `<name>/SKILL.md` 자동탐색 |
| 에이전트 (12) | 루트 `agents/` 디렉토리 (자동탐색, **manifest 필드 없음**) | 플러그인 루트 `agents/*.md`를 서브에이전트로 자동탐색 |
| 훅 (4) | `hooks` 필드 (plugin.json 인라인) | SessionStart / PreToolUse / PostToolUse / Stop |

스킬은 `.claude/skills/`를 그대로 재사용하지만, **에이전트는 루트 `agents/` 미러가 필요**합니다(아래 주의 참조).

### ⚠️ 에이전트는 루트 `agents/` 미러로 노출 (validate ≠ runtime 함정)

Claude Code 플러그인은 **플러그인 루트의 `agents/` 디렉토리만** 서브에이전트로 자동탐색합니다. 실측으로 확인된 함정:

| manifest `agents` 형식 | `claude plugin validate` | 실제 런타임 로드 |
|------------------------|:------------------------:|:----------------:|
| `"./.claude/agents/*.md"` 파일 배열 | ✅ 통과 | ❌ **로드 안 됨 (Agents 0)** |
| `"./.claude/agents"` 디렉토리 문자열 | ❌ 거부 | — |
| **필드 없음 + 루트 `agents/` 디렉토리** | ✅ 통과 | ✅ **Agents 12 로드** |

즉 `validate`가 통과해도 `.claude/agents/` 파일배열은 런타임에 로드되지 않습니다. 그래서 매니페스트에서 `agents` 필드를 빼고, **루트 `agents/`에 미러**를 둡니다.

- **SSOT는 `.claude/agents/`** 입니다 (clone/프로젝트 모드에서 Claude Code가 프로젝트 `.claude/agents/`를 자동탐색).
- 루트 `agents/`는 그 **미러**이며 `scripts/sync-plugin-agents.sh`(또는 `.ps1`)로 재생성합니다.
- `agents/`는 GitHub 마켓플레이스 clone이 서빙하므로 **반드시 커밋**합니다.
- 에이전트를 추가/수정하면 sync 스크립트를 다시 실행해 미러를 갱신하고 함께 커밋하세요.

```bash
# 에이전트 변경 후 미러 동기화 (macOS/Linux/git-bash)
bash scripts/sync-plugin-agents.sh
# Windows PowerShell
# powershell -ExecutionPolicy Bypass -File scripts\sync-plugin-agents.ps1
git add agents/ .claude/agents/
git commit -m "chore: sync plugin agents mirror"
```

덕분에 같은 리포가 **(A) clone해서 쓰는 kit** 이면서 동시에 **(B) 설치형 플러그인** 으로 동작합니다.
검증·실측 결과: `claude plugin validate ./ --strict` 통과 + `claude plugin details ai-crew-kit` 에서 **Skills(22) · Agents(12) · Hooks(4)** 로드 확인.

---

## 3. ⚠️ 훅(hooks) 관련 기술 제약

훅은 bash 스크립트(`.claude/hooks/*.sh`) 기반이라 환경에 따라 주의가 필요합니다.
**스킬·에이전트는 순수 마크다운이라 OS·플랫폼과 무관하게 항상 동작합니다.** 아래 제약은 훅에만 해당됩니다.

### SessionStart의 `${CLAUDE_PLUGIN_ROOT}` 미해결 버그

Claude Code에는 **SessionStart 이벤트에서 `${CLAUDE_PLUGIN_ROOT}`가 빈 값으로 풀리는 알려진 버그**가 있습니다(CLI 포함). 즉 `bash "${CLAUDE_PLUGIN_ROOT}/.claude/hooks/session-start.sh"` 로 두면 경로가 깨집니다. PreToolUse / PostToolUse / Stop 에서는 정상 동작합니다.

**우회 방법(이미 적용됨):** SessionStart만 절대경로 우회로 `${CLAUDE_PROJECT_DIR}` 를 사용합니다.

```jsonc
// plugin.json
"SessionStart": [{ "hooks": [{
  "command": "bash \"${CLAUDE_PROJECT_DIR}/.claude/hooks/session-start.sh\""  // PLUGIN_ROOT 대신 PROJECT_DIR
}]}],
"PostToolUse": [{ "hooks": [{
  "command": "bash \"${CLAUDE_PLUGIN_ROOT}/.claude/hooks/post-tool-use.sh\""  // 정상 동작
}]}]
```

- **clone / `/aick-onboard` 로 `.claude/` 가 프로젝트에 존재하는 경우** → SessionStart 훅(git sync, continuation-plan 로드)이 정상 동작합니다. (이것이 AI Crew Kit의 표준 사용 방식)
- **`.claude/` 없이 순수 플러그인만 설치한 프로젝트** → SessionStart 스크립트는 파일이 없어 조용히 no-op 합니다. 모든 훅은 비블로킹(exit 0) 설계라 세션을 막지 않습니다. git sync가 필요하면 `/aick-onboard` 로 `.claude/` 를 프로젝트에 배치하세요.

