"""skill-upgrade가 .claude/hooks/ + settings.json hooks 필드 전파를 문서화하는지 정적 검증.

배경(게이트 전파 부채, 2026-06): skill-upgrade는 `.claude/hooks/` 스크립트를
업데이트 대상에서 누락하고 settings.json은 권한만 머지해, v2.4.0 PreToolUse 머지
게이트(스크립트 + 등록)가 기존 시드 프로젝트에 전파되지 않았다.

skill-upgrade는 prose-executed(LLM이 본문 지침을 직접 수행)라 실행 단위 테스트가
없다. 본 테스트는 전파의 **필요조건** — hooks가 업데이트 scope에 명시되어 있다 —
을 정적으로 회귀 가드한다. hooks가 다시 누락되면(원래 부채 재발) fail.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL_MD = (
    Path(__file__).resolve().parents[2]
    / ".claude"
    / "skills"
    / "skill-upgrade"
    / "SKILL.md"
)


@pytest.fixture(scope="module")
def text() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def test_hooks_in_update_target_table(text: str) -> None:
    """업데이트 대상 표에 .claude/hooks/ 행이 있어야 함 (hook 스크립트 전파)."""
    assert "`.claude/hooks/`" in text, (
        "업데이트 대상 표에 `.claude/hooks/` 누락 — hook 스크립트 미전파 부채 재발"
    )


def test_hooks_in_hash_compare_list(text: str) -> None:
    """Step 6-0 해시 비교 디렉토리 목록에 hooks 포함 (교체 전 가시화 + 승인)."""
    m = re.search(r"프레임워크 디렉토리\(([^)]*)\)", text)
    assert m, "Step 6-0 해시 비교 디렉토리 목록을 찾지 못함"
    dirs = m.group(1)
    assert "hooks" in dirs, f"Step 6-0 해시 비교 대상에 hooks 누락: {dirs}"


def test_settings_hooks_field_sync_documented(text: str) -> None:
    """Step 12-3가 settings.json hooks 필드 동기화를 문서화해야 함 (PreToolUse 등록 전파)."""
    assert "`hooks` 필드 동기화" in text, (
        "settings.json hooks 필드 동기화 미문서화 — PreToolUse 등록 미전파 부채 재발"
    )


def test_keep_choice_honored_in_replace(text: str) -> None:
    """Step 11이 '현재 유지' 선택을 존중해야 함 (하드닝한 hook 보존)."""
    assert "현재 유지" in text and "보존" in text, (
        "Step 11이 '현재 유지' 선택 보존을 명시하지 않음 — 사용자 hook 커스터마이징 손실 위험"
    )
