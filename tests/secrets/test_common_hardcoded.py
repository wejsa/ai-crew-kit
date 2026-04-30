"""SEC-S01~S05 — common.hardcoded high-confidence patterns.

Phase 5 PR #36/#37 작성자 로컬 fixture의 자동화 마이그레이션.
"""
import pytest

from .conftest import get_pattern, matches


# 양성 — 16자/36자/특정 prefix 리터럴 매칭
HARDCODED_POSITIVE_CASES = [
    ("SEC-S01", 'val apiKey = "sk-1234567890abcdefABCDEFG"'),
    ("SEC-S01", 'const API_KEY = "abcdef0123456789xyz"'),
    ("SEC-S02", 'val secret = "abcdefghijklmnopqrstuvwxyz"'),
    ("SEC-S02", 'val privateKey = "-----BEGINabcdefghijklmnopqrst"'),
    # AWS Access Key 5 prefix (Phase 5 Step 1 H001/M001 보정)
    ("SEC-S03", 'val key = "AKIAIOSFODNN7EXAMPLE"'),
    ("SEC-S03", 'val arn = "AGPAEXAMPLE12345678X"'),
    ("SEC-S03", 'val role = "AROAEXAMPLE12345678X"'),
    ("SEC-S03", 'val user = "AIDAEXAMPLE12345678X"'),
    ("SEC-S03", 'val noaa = "ANPAEXAMPLE12345678X"'),
    # GitHub Token 5 prefix (PR #36 M002)
    ("SEC-S04", 'val pat = "ghp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"'),
    ("SEC-S04", 'val oauth = "gho_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"'),
    ("SEC-S04", 'val userapp = "ghu_cccccccccccccccccccccccccccccccccccc"'),
    ("SEC-S04", 'val server = "ghs_dddddddddddddddddddddddddddddddddddd"'),
    ("SEC-S04", 'val refresh = "ghr_eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"'),
    # Slack
    ("SEC-S05", 'val slackBot = "xoxb-12345-67890-abcdefg"'),
    ("SEC-S05", 'val slackUser = "xoxp-99999-88888-77777"'),
]


@pytest.mark.parametrize("pattern_id,line", HARDCODED_POSITIVE_CASES)
def test_hardcoded_positive(base_patterns, pattern_id, line):
    entry = get_pattern(base_patterns, "common.hardcoded", pattern_id)
    assert matches(entry, line) is True, f"{pattern_id} should match: {line!r}"


# 음성 — env_var_reference (Go/Python 함수형 포함, PR #37 M001 후속)
HARDCODED_ENV_VAR_CASES = [
    ("SEC-S01", "const apiKey = process.env.API_KEY"),
    ("SEC-S01", 'api_key = os.environ["API_KEY"]'),
    ("SEC-S01", 'val k = System.getenv("API_KEY")'),
    ("SEC-S01", 'apiKey, ok := os.LookupEnv("API_KEY")'),
    ("SEC-S01", 'api_key = os.getenv("API_KEY", "default")'),
]


@pytest.mark.parametrize("pattern_id,line", HARDCODED_ENV_VAR_CASES)
def test_hardcoded_env_var_excluded(base_patterns, pattern_id, line):
    """env_var_reference 정규식이 6 변형(JS/Python dict+getenv/Java/Go Getenv+LookupEnv) 모두 차단."""
    entry = get_pattern(base_patterns, "common.hardcoded", pattern_id)
    assert matches(entry, line) is False, f"{line!r} should be excluded by env_var_reference"


# 음성 — 의도적 제외 (ASIA prefix, Phase 5 Step 1 명시 결정)
def test_hardcoded_asia_prefix_excluded(base_patterns):
    """ASIA STS 임시 토큰은 의도적으로 SEC-S03 정규식에서 제외."""
    entry = get_pattern(base_patterns, "common.hardcoded", "SEC-S03")
    assert matches(entry, 'val tmp = "ASIAIOSFODNN7EXAMPLE"') is False


def test_hardcoded_count(base_patterns):
    assert len(base_patterns["common"]["hardcoded"]) == 5


def test_hardcoded_all_high(base_patterns):
    """common.hardcoded는 모두 high confidence + CRITICAL."""
    for entry in base_patterns["common"]["hardcoded"]:
        assert entry["confidence"] == "high", f"{entry['id']} confidence should be high"
        assert entry["severity"] == "CRITICAL", f"{entry['id']} severity should be CRITICAL"


def test_hardcoded_id_range(base_patterns):
    """SEC-S01~S05 5개 ID 범위 검증."""
    ids = sorted(p["id"] for p in base_patterns["common"]["hardcoded"])
    assert ids == [f"SEC-S{n:02d}" for n in range(1, 6)]
