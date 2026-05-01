"""Secrets filter regression tests for skill-retro §5.3 (Phase 7 Step 2).

skill-retro stores lesson description after matching against
_base/health/secrets-patterns.json common.hardcoded (SEC-S01~S05).
Match → AskUserQuestion (거부 / 마스킹 / 강행). Tests cover the regex layer
only — UX layer is verified via skill-retro SKILL.md spec, not pytest.

These tests pin the regex contract: positive samples must match,
clean text must not. Excludeable contexts (comment/type_declaration)
are handled at the AskUserQuestion layer in skill-retro, not here.
"""
from __future__ import annotations

import pytest

from .conftest import find_pattern


CLEAN_DESCRIPTIONS = [
    "결제 API에서 nullable 검증 누락 사례 발견",
    "트랜잭션 격리 수준 변경 후 동시성 이슈 해소",
    "리뷰 시 도메인 컨벤션 자동 참조 도입 권장",
]


@pytest.mark.parametrize("text", CLEAN_DESCRIPTIONS)
def test_clean_description_no_match(text, hardcoded_patterns):
    """PR #44 리뷰 MINOR — find_pattern 재호출 제거, 직접 컴파일."""
    import re as _re
    for entry in hardcoded_patterns:
        pat = _re.compile(entry["pattern"])
        assert not pat.search(text), f"{entry['id']} false positive on {text!r}"


@pytest.mark.parametrize(
    "pattern_id, sample",
    [
        ("SEC-S01", 'api_key = "sk-1234567890ABCDEFG_xyz"'),
        ("SEC-S01", "apiKey: 'AbCdEf0123456789xyz'"),
        ("SEC-S02", 'secret = "abcdefghijklmnopqrstuvwxyz"'),
        ("SEC-S02", 'private_key: "-----BEGINabcdefghijklmnopqrst"'),
        ("SEC-S03", "AKIAIOSFODNN7EXAMPLE"),
        ("SEC-S04", "ghp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"),
        ("SEC-S05", "xoxb-12345-67890-abcdefg"),
    ],
)
def test_secret_pattern_matches(pattern_id, sample, hardcoded_patterns):
    pat = find_pattern(hardcoded_patterns, pattern_id)
    assert pat.search(sample), f"{pattern_id} failed to match {sample!r}"


def test_all_hardcoded_have_comment_excludecontext(hardcoded_patterns):
    """SEC-S01~S05 모두 excludeContexts에 'comment' 포함 — skill-retro가
    description(코멘트성 텍스트)에 대해 AskUserQuestion으로 사용자 판단을
    위임하는 결정(D2 개정)의 근거. 이 invariant이 깨지면 정적 매칭 정책
    재검토 필요."""
    for entry in hardcoded_patterns:
        excludes = entry.get("excludeContexts", [])
        assert "comment" in excludes, (
            f"{entry['id']}({entry['name']}) has no 'comment' in excludeContexts. "
            "If this is intentional, revisit Phase 7 D2 (secrets filter design)."
        )


def test_hardcoded_pattern_count(hardcoded_patterns):
    """SEC-S01~S05 5건 — Phase 5 PR #36/#37 결과 + Phase 7 회귀 보호."""
    ids = sorted(entry["id"] for entry in hardcoded_patterns)
    assert ids == ["SEC-S01", "SEC-S02", "SEC-S03", "SEC-S04", "SEC-S05"]
