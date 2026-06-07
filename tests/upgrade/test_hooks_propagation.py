"""crew-upgrade가 .claude/hooks/ + settings.json hooks 필드 전파를 문서화하는지 정적 검증.

배경(게이트 전파 부채, 2026-06): crew-upgrade는 `.claude/hooks/` 스크립트를
업데이트 대상에서 누락하고 settings.json은 권한만 머지해, v2.4.0 PreToolUse 머지
게이트(스크립트 + 등록)가 기존 시드 프로젝트에 전파되지 않았다.

crew-upgrade는 prose-executed(LLM이 본문 지침을 직접 수행)라 실행 단위 테스트가
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
    / "crew-upgrade"
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
    """Step 11이 '현재 유지' 선택을 복사 후 복원해 존중해야 함 (하드닝한 hook 보존).

    '현재 유지'·'보존'은 6-0/12-3에도 등장하므로, Step 11 복원 절에 고유한
    '되돌려' 문구로 가드한다(절이 삭제되면 fail)."""
    assert "되돌려" in text, (
        "Step 11이 '현재 유지' 파일을 백업본으로 되돌리는 복원 절을 명시하지 않음 "
        "— 디렉토리 단위 복사가 사용자 hook 커스터마이징을 덮어쓸 위험"
    )


def test_framework_hook_match_is_prefix_agnostic(text: str) -> None:
    """settings.json hooks 동기화의 프레임워크 훅 식별이 경로 접두 무관이어야 함.

    `$CLAUDE_PROJECT_DIR/` 접두로만 매칭하면 상대경로로 등록된 구버전 프로젝트가
    중복 등록됨 → 'basename' 또는 '접두 무관' 기준 명시를 가드."""
    assert "basename" in text or "접두 무관" in text, (
        "프레임워크 훅 식별이 접두 무관/basename 기준임을 명시하지 않음 "
        "— 상대경로 등록 프로젝트에서 hooks 중복 등록 위험"
    )
