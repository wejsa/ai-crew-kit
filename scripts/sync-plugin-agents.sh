#!/usr/bin/env bash
# sync-plugin-agents.sh
#
# 플러그인 노출용 루트 `agents/` 미러를 `.claude/agents/` 로부터 재생성한다.
#
# 배경:
#   Claude Code/Cowork 플러그인은 플러그인 루트의 `agents/` 디렉토리만
#   서브에이전트로 자동탐색한다. `.claude/agents/` 를 manifest의 `agents`
#   파일배열로 지정하면 `claude plugin validate` 는 통과하지만 런타임에는
#   로드되지 않는다(Agents 0). 디렉토리 문자열 형식은 manifest가 거부된다.
#   따라서 루트 `agents/` 미러가 필요하다.
#
# SSOT:
#   `.claude/agents/` 가 단일 진실 공급원(SSOT)이다. clone/프로젝트 모드에서
#   Claude Code가 프로젝트 `.claude/agents/` 를 자동탐색한다. 에이전트를
#   추가/수정한 뒤 반드시 이 스크립트를 실행해 `agents/` 미러를 동기화하고
#   함께 커밋한다. (`agents/` 는 GitHub 마켓플레이스 clone이 서빙하므로 커밋 필수)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/.claude/agents"
DST="$ROOT/agents"

[ -d "$SRC" ] || { echo "error: $SRC 없음" >&2; exit 1; }
rm -rf "$DST"
mkdir -p "$DST"
cp "$SRC"/*.md "$DST"/
echo "synced $(ls "$DST"/*.md | wc -l | tr -d ' ') agents → agents/"
