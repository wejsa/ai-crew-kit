"""fintech/SEC-S01 — PAN 16자리 IIN [3-6] 제한 + Luhn 체크섬.

Phase 5 PR #38 fixture 모태. M001(IIN 제한) 반영.
"""
import re

import pytest

from .conftest import get_pattern, luhn_ok, matches


# (line, raw_match_expected, luhn_pass_expected)
PAN_CASES = [
    # 양성 — IIN 3-6 + Luhn pass (실제 카드 발급사 테스트 번호)
    ('val pan = "4111111111111111"', True, True),    # Visa test
    ('val pan = "5555555555554444"', True, True),    # Mastercard test
    ('val pan = "6011000990139424"', True, True),    # Discover test
    ('val pan = "3530111333300000"', True, True),    # JCB test (35xx)
    # raw 매칭하나 Luhn 실패 → 폐기 (false positive 차단)
    ('val pan = "4111111111111112"', True, False),
    ('val pan = "5555555555554443"', True, False),
    ('val pan = "6011000990139425"', True, False),
    # 음성 — IIN 0/1/2/7/8/9 거부 (M001 IIN 제한)
    ('order_id = "0123456789012345"', False, None),
    ('txn = "1234567890123456"', False, None),
    ('id = "2345678901234567"', False, None),
    ('id = "7777777777777777"', False, None),
    ('id = "8888888888888888"', False, None),
    ('id = "9999999999999999"', False, None),
    # 음성 — 길이
    ('pan = "411111111111111"', False, None),    # 15자 (Amex 길이 — IIN 4지만 16자 아님)
    ('pan = "41111111111111111"', False, None),  # 17자
    # 음성 — 단어 경계 \b
    ('id = "abc4111111111111111def"', False, None),
    # 음성 — 하이픈/공백 분리 (정규식은 인접 16자만)
    ('pan = "4111-1111-1111-1111"', False, None),
    ('pan = "4111 1111 1111 1111"', False, None),
]


@pytest.mark.parametrize("line,raw_expected,luhn_expected", PAN_CASES)
def test_pan(fintech_patterns, line, raw_expected, luhn_expected):
    entry = get_pattern(fintech_patterns, "domain.patterns", "SEC-S01")
    raw = matches(entry, line)
    assert raw is raw_expected, f"raw mismatch ({line!r}): expected {raw_expected}, got {raw}"
    if raw and luhn_expected is not None:
        m = re.search(r"\b[3-6]\d{15}\b", line)
        assert m, f"raw matched but no 16-digit found in {line!r}"
        assert luhn_ok(m.group(0)) is luhn_expected, f"Luhn mismatch: {line!r}"


def test_pan_high_confidence(fintech_patterns):
    entry = get_pattern(fintech_patterns, "domain.patterns", "SEC-S01")
    assert entry["confidence"] == "high"
    assert entry["severity"] == "CRITICAL"


def test_fintech_count(fintech_patterns):
    """fintech 도메인은 SEC-S01 PAN 1개 (오픈뱅킹 토큰 H001 보류, CVV M002 보류)."""
    assert len(fintech_patterns["domain"]["patterns"]) == 1
    assert fintech_patterns["domain"]["patterns"][0]["id"] == "SEC-S01"
