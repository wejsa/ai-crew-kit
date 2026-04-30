"""SSOT drift 방어 — conftest.py EXCLUDE_CTX ↔ SKILL.md 정규식 1:1 검증.

PR #41 리뷰 M001 후속. EXCLUDE_CTX SSOT가 3곳(_base/health/README.md / SKILL.md /
conftest.py)에 분산되어 drift 시 conftest.py가 자기-정합으로만 통과하는 위험을 차단.
SKILL.md를 SSOT 권위로 잡고, conftest.py 정규식이 모두 SKILL.md 본문에 표기되어
있는지 substring 매칭으로 검증.
"""
import pytest

from .conftest import EXCLUDE_CTX


def _normalize_md_table(text: str) -> str:
    """Markdown 표 escape(`\\|`)를 정규식 파이프(`|`)로 복원."""
    return text.replace("\\|", "|")


def test_exclude_ctx_regex_in_skill_md_ssot(skill_md_text):
    """EXCLUDE_CTX의 모든 정규식이 SKILL.md security 카테고리 SSOT에 표기되어 있어야 함.

    Drift 발생 시(예: SKILL.md에 새 enum 추가/제거, conftest.py만 변경) 테스트 FAIL.
    """
    normalized = _normalize_md_table(skill_md_text)
    missing = []
    for ctx_name, regexes in EXCLUDE_CTX.items():
        for rgx in regexes:
            if rgx.pattern not in normalized:
                missing.append((ctx_name, rgx.pattern))
    assert not missing, (
        f"EXCLUDE_CTX patterns missing in SKILL.md SSOT — drift 의심:\n"
        + "\n".join(f"  [{c}] {p}" for c, p in missing)
    )


def test_exclude_ctx_enum_keys_match_schema():
    """EXCLUDE_CTX 키가 secrets-patterns.schema.json `excludeContexts` enum과 일치."""
    import json
    from .conftest import REPO_ROOT

    schema = json.loads(
        (REPO_ROOT / ".claude/schemas/secrets-patterns.schema.json").read_text(encoding="utf-8")
    )
    enum_values = (
        schema["definitions"]["patternEntry"]["properties"]["excludeContexts"]["items"]["enum"]
    )
    assert set(EXCLUDE_CTX.keys()) == set(enum_values), (
        f"EXCLUDE_CTX keys {sorted(EXCLUDE_CTX.keys())} != schema enum {sorted(enum_values)}"
    )
