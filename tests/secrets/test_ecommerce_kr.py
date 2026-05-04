"""ecommerce/SEC-S01 RRN + SEC-S02 BRN — 한국 형식 + 체크섬.

Phase 5 PR #38 fixture 모태. M002(RRN YYMMDD+성별) + M003(BRN 세무서 코드) 반영.
"""
import re

import pytest

from .conftest import biz_ok, get_pattern, matches, rrn_ok


# RRN — (line, raw_match_expected, checksum_expected)
RRN_CASES = [
    # 양성 — 형식 + 체크섬 통과
    ('rrn = "900101-1000006"', True, True),    # 1990-01-01, 성별 1
    # raw 매칭하나 체크섬 실패 → 폐기
    ('rrn = "900101-1000007"', True, False),
    # raw 매칭 + 체크섬은 별도 (2000년대 + 외국인 등 cover)
    ('rrn = "001231-3234561"', True, None),    # 2000-12-31, 성별 3 (2000s 남)
    ('rrn = "950115-5234561"', True, None),    # 외국인 (성별 5 — 1900s 외남)
    # 음성 — 월 검증 (M002)
    ('rrn = "999999-1234567"', False, None),   # 월 99
    ('rrn = "991320-9876543"', False, None),   # 월 13
    ('rrn = "900001-1234567"', False, None),   # 월 00
    # 음성 — 일 검증 (M002)
    ('rrn = "900132-1234567"', False, None),   # 일 32
    ('rrn = "900100-1234567"', False, None),   # 일 00
    # 음성 — 성별 코드 (M002 — 1-8만 허용)
    ('rrn = "900101-0234567"', False, None),   # 성별 0
    ('rrn = "900101-9234567"', False, None),   # 성별 9 (1899 이전, 사실상 사망)
]


@pytest.mark.parametrize("line,raw_expected,chk_expected", RRN_CASES)
def test_rrn(ecommerce_patterns, line, raw_expected, chk_expected):
    entry = get_pattern(ecommerce_patterns, "domain.patterns", "SEC-S01")
    raw = matches(entry, line)
    assert raw is raw_expected, f"raw mismatch ({line!r}): expected {raw_expected}, got {raw}"
    if raw and chk_expected is not None:
        m = re.search(r"\b\d{6}-\d{7}\b", line)
        assert m, f"raw matched but no RRN found in {line!r}"
        assert rrn_ok(m.group(0)) is chk_expected, f"RRN checksum mismatch: {line!r}"


# BRN — (line, raw_match_expected, checksum_expected)
BRN_CASES = [
    # 양성 — 형식 + 체크섬 통과
    ('biz = "100-00-00009"', True, True),
    # raw 매칭 + 체크섬 실패
    ('biz = "100-00-00001"', True, False),
    # 음성 — 첫 자리 0 (M003 — 세무서 코드 100-999만 사용)
    ('biz = "000-12-34567"', False, None),
    ('biz = "099-12-34567"', False, None),
    # 음성 — 형식 (자릿수 / 분리 위치)
    ('biz = "1234-56-7890"', False, None),
    ('biz = "10-000-00009"', False, None),
    ('biz = "1000000009"', False, None),
]


@pytest.mark.parametrize("line,raw_expected,chk_expected", BRN_CASES)
def test_brn(ecommerce_patterns, line, raw_expected, chk_expected):
    entry = get_pattern(ecommerce_patterns, "domain.patterns", "SEC-S02")
    raw = matches(entry, line)
    assert raw is raw_expected, f"raw mismatch ({line!r}): expected {raw_expected}, got {raw}"
    if raw and chk_expected is not None:
        m = re.search(r"\b[1-9]\d{2}-\d{2}-\d{5}\b", line)
        assert m, f"raw matched but no BRN found in {line!r}"
        assert biz_ok(m.group(0)) is chk_expected, f"BRN checksum mismatch: {line!r}"


def test_ecommerce_high_confidence(ecommerce_patterns):
    """ecommerce 도메인은 모두 high confidence + CRITICAL."""
    for entry in ecommerce_patterns["domain"]["patterns"]:
        assert entry["confidence"] == "high"
        assert entry["severity"] == "CRITICAL"


def test_ecommerce_count(ecommerce_patterns):
    """ecommerce 도메인은 SEC-S01 RRN + SEC-S02 BRN 2개."""
    ids = sorted(p["id"] for p in ecommerce_patterns["domain"]["patterns"])
    assert ids == ["SEC-S01", "SEC-S02"]
