# Cowork / Claude Code 플러그인으로 설치하기

AI Crew Kit는 리포 clone 방식 외에 **Claude Code · Cowork 플러그인**으로도 설치할 수 있습니다.
이 리포 자체가 곧 마켓플레이스이자 단일 플러그인입니다 (`.claude-plugin/marketplace.json` + `.claude-plugin/plugin.json`).

플러그인으로 설치하면 clone 없이도 23개 스킬(`/skill-status`, `/skill-impl` 등)과 12개 서브에이전트, 품질 게이트 훅이 현재 작업 중인 프로젝트에서 바로 사용 가능해집니다.

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

플러그인은 기존 `.claude/` 디렉토리를 **그대로 재사용**합니다 (파일 중복 없음).

| 매니페스트 필드 | 가리키는 경로 | 동작 |
|----------------|--------------|------|
| `skills` | `./.claude/skills/` (디렉토리 문자열) | 기본 `skills/`에 **추가** — `<name>/SKILL.md` 23개 스킬 로드 |
| `agents` | `.claude/agents/*.md` 파일 12개 배열 | 기본 `agents/`를 **대체** — 12개 서브에이전트 로드 |
| `hooks` | (plugin.json 인라인) | SessionStart / PreToolUse / PostToolUse / Stop |

> **주의:** `agents` 필드는 디렉토리 문자열이 아니라 **개별 `.md` 파일 경로 배열**을 요구합니다(`claude plugin validate --strict` 기준). 에이전트를 추가/삭제하면 `plugin.json` 의 `agents` 배열도 함께 갱신해야 합니다. 반면 `skills` 는 디렉토리 문자열을 허용하므로 스킬 추가 시 매니페스트 수정이 필요 없습니다.

덕분에 같은 리포가 **(A) clone해서 쓰는 kit** 이면서 동시에 **(B) 설치형 플러그인** 으로 동작합니다.
매니페스트는 `claude plugin validate ./ --strict` 로 검증을 통과합니다.

---

## 3. ⚠️ 훅(hooks) 관련 기술 제약 2가지

훅은 bash 스크립트(`.claude/hooks/*.sh`) 기반이라 환경에 따라 주의가 필요합니다.
**스킬·에이전트는 순수 마크다운이라 OS·플랫폼과 무관하게 항상 동작합니다.** 아래 제약은 훅에만 해당됩니다.

### 3-1. SessionStart의 `${CLAUDE_PLUGIN_ROOT}` 미해결 버그

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

- **clone / `/skill-onboard` 로 `.claude/` 가 프로젝트에 존재하는 경우** → SessionStart 훅(git sync, continuation-plan 로드)이 정상 동작합니다. (이것이 AI Crew Kit의 표준 사용 방식)
- **`.claude/` 없이 순수 플러그인만 설치한 프로젝트** → SessionStart 스크립트는 파일이 없어 조용히 no-op 합니다. 모든 훅은 비블로킹(exit 0) 설계라 세션을 막지 않습니다. git sync가 필요하면 `/skill-onboard` 로 `.claude/` 를 프로젝트에 배치하세요.

### 3-2. Windows CLI 셸은 cmd.exe — bash 래퍼 필요

훅이 전부 `.sh`(bash) 스크립트인데 **Windows의 Claude Code CLI는 기본 셸이 cmd.exe** 라 스크립트를 그대로 실행할 수 없습니다.

**대응(이미 적용됨):** 모든 훅 커맨드를 `bash "..."` 로 감쌌습니다. 이러면 cmd.exe가 `bash` 를 호출하므로 **git-bash 또는 WSL의 bash가 PATH에 있으면** 동작합니다.

| 실행 환경 | 훅 동작 |
|-----------|---------|
| **Cowork (Linux 샌드박스)** | `.sh` 네이티브 실행 — 제약 없음 ✅ |
| macOS / Linux CLI | 네이티브 bash — 제약 없음 ✅ |
| **Windows CLI** | `bash` 가 PATH에 있어야 함 (Git for Windows 설치 시 git-bash 포함). 경로 변환(`C:\` ↔ `/c/`) 이슈가 있으면 git-bash/WSL 터미널에서 `claude` 를 실행 권장 ⚠️ |

> Windows에서 훅을 쓰지 않으려면 `/plugin` 에서 플러그인을 enable 하되, 훅이 부담되면 프로젝트 `.claude/settings.json` 의 hooks 블록을 비우거나, 스킬·에이전트만 쓰고 훅은 생략해도 됩니다. 스킬·에이전트만으로도 워크플로우 명령은 모두 사용 가능합니다.

---

## 4. 설치 후 첫 사용

플러그인을 설치한 뒤, 작업할 프로젝트에서:

```bash
/skill-onboard      # 기존 코드베이스 스캔 → 도메인·스택 감지 → .claude/ 스캐폴딩 생성
# 또는 새