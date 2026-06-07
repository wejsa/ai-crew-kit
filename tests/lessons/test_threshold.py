"""Impact threshold regression tests (Phase 7 Step 2).

SSOT: lessons-learned.schema.json description + crew-retro SKILL.md.
권장: appliedCount >= 5 → high / >= 3 → medium / < 3 → low.

threshold_recommended() 함수가 변경되면 fixture 임계값과 어긋나
fail이 발생하므로 회귀 보호 작동.
"""
from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "applied_count, expected",
    [
        (1, "low"),
        (2, "low"),
        (3, "medium"),
        (4, "medium"),
        (5, "high"),
        (6, "high"),
        (10, "high"),
    ],
)
def test_threshold_boundaries(applied_count, expected, threshold_recommended):
    assert threshold_recommended(applied_count) == expected


def test_low_medium_boundary(threshold_recommended):
    assert threshold_recommended(2) != threshold_recommended(3)


def test_medium_high_boundary(threshold_recommended):
    assert threshold_recommended(4) != threshold_recommended(5)
