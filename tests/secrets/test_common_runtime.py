"""SEC-S06~S17 — common.runtime patterns (v1.x SEC-01 회귀 보존, medium 예외).

Phase 5 PR #37 회귀 fixture 23건의 자동화 마이그레이션.
키워드는 alpha.3 인라인 12 패턴과 1:1 매핑되어야 한다.
"""
import pytest

from .conftest import get_pattern, matches


# (pattern_id, line, expected_match) — alpha.3 인라인 12 패턴 키워드 양성
RUNTIME_POSITIVE_CASES = [
    ("SEC-S06", 'logger.info("login: " + password)'),
    ("SEC-S07", "log.debug(cardNumber)"),
    ("SEC-S08", "logger.error(creditCard.toString())"),
    ("SEC-S09", 'log.info("cvv=" + cvv)'),
    ("SEC-S10", "logger.warn(ssn)"),
    ("SEC-S11", 'log.info("주민등록번호 처리")'),
    ("SEC-S12", 'logger.debug("secret loaded: " + secret)'),
    ("SEC-S13", 'println("PASSWORD=" + password)'),
    ("SEC-S14", "logger.info(apiKey)"),
    ("SEC-S15", 'log.error("jwt token: " + token)'),
    ("SEC-S16", 'logger.warn("bearer " + bearerToken)'),
    ("SEC-S17", 'log.info("authorization " + authorization)'),
]


@pytest.mark.parametrize("pattern_id,line", RUNTIME_POSITIVE_CASES)
def test_runtime_positive(base_patterns, pattern_id, line):
    """alpha.3 인라인 12 패턴 키워드가 외부화 후에도 동일하게 매칭됨 (회귀 보존)."""
    entry = get_pattern(base_patterns, "common.runtime", pattern_id)
    assert matches(entry, line) is True, f"{pattern_id} should match: {line!r}"


# excludeContexts 음성 — type_declaration / comment
RUNTIME_NEGATIVE_CASES = [
    ("SEC-S06", 'class Password { val value: String = "" }', "type_declaration"),
    ("SEC-S06", "// log.info(password) — comment", "comment"),
    ("SEC-S06", "# logger.info(password)", "comment"),
    ("SEC-S06", "/* log.info(password) */", "comment"),
    ("SEC-S06", " * log.info(password)", "comment"),
    ("SEC-S12", "interface SecretManager { }", "type_declaration"),
]


@pytest.mark.parametrize("pattern_id,line,reason", RUNTIME_NEGATIVE_CASES)
def test_runtime_excludes(base_patterns, pattern_id, line, reason):
    """excludeContexts SSOT가 false positive 차단."""
    entry = get_pattern(base_patterns, "common.runtime", pattern_id)
    assert matches(entry, line) is False, f"{pattern_id} should be excluded by {reason}: {line!r}"


def test_runtime_count(base_patterns):
    """v1.x SEC-01의 12 패턴이 1:1로 보존되어야 함."""
    assert len(base_patterns["common"]["runtime"]) == 12


def test_runtime_all_medium(base_patterns):
    """common.runtime은 v1.x 회귀 보존 한정 medium confidence 예외."""
    for entry in base_patterns["common"]["runtime"]:
        assert entry["confidence"] == "medium", f"{entry['id']} confidence should be medium"
        assert entry["severity"] == "CRITICAL", f"{entry['id']} severity should be CRITICAL"


def test_runtime_id_range(base_patterns):
    """SEC-S06~S17 12개 ID 범위 검증."""
    ids = sorted(p["id"] for p in base_patterns["common"]["runtime"])
    assert ids == [f"SEC-S{n:02d}" for n in range(6, 18)]
