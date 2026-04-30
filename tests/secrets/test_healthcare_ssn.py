"""healthcare/SEC-S01 — 미국 SSN with SSA invalid lookahead.

Phase 5 PR #38 fixture 모태. M001(SSA invalid 그룹 거부) 반영.
"""
import pytest

from .conftest import get_pattern, matches


SSN_CASES = [
    # 양성 — 유효 형식 (area != 000/666/9XX, group != 00, serial != 0000)
    ('ssn = "123-45-6789"', True),
    ('val s = "555-12-3456"', True),
    ('s = "098-76-5432"', True),
    ('ssn = "001-01-0001"', True),  # boundary — area 001 + group 01 + serial 0001
    # 음성 — area=000 / 666 / 9XX (SSA invalid 그룹)
    ('ssn = "000-12-3456"', False),
    ('ssn = "666-12-3456"', False),
    ('ssn = "900-12-3456"', False),
    ('ssn = "999-12-3456"', False),
    ('ssn = "987-12-3456"', False),  # 9XX 전체 invalid
    # 음성 — group=00
    ('ssn = "123-00-4567"', False),
    # 음성 — serial=0000
    ('ssn = "123-45-0000"', False),
    # 음성 — 형식
    ('ssn = "123 45 6789"', False),     # 공백
    ('ssn = "123456789"', False),       # 하이픈 없음
    ('ssn = "12-345-6789"', False),     # 잘못된 분리
]


@pytest.mark.parametrize("line,expected", SSN_CASES)
def test_ssn(healthcare_patterns, line, expected):
    entry = get_pattern(healthcare_patterns, "domain.patterns", "SEC-S01")
    assert matches(entry, line) is expected, f"{line!r} expected {expected}"


def test_ssn_high_confidence(healthcare_patterns):
    entry = get_pattern(healthcare_patterns, "domain.patterns", "SEC-S01")
    assert entry["confidence"] == "high"
    assert entry["severity"] == "CRITICAL"


def test_healthcare_count(healthcare_patterns):
    """healthcare 도메인은 SEC-S01 SSN 1개 (DEA M003 / MRN low 보류)."""
    assert len(healthcare_patterns["domain"]["patterns"]) == 1
    assert healthcare_patterns["domain"]["patterns"][0]["id"] == "SEC-S01"
