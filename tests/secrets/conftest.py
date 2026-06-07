"""Shared fixtures and helpers for secrets-patterns regression tests.

Phase 5 후속 트랙 A Step 2 — docs/v2/phase-5-tests-plan.md
PR #37 / #38 / #39 작성자 로컬 fixture를 CI 자동화로 마이그레이션.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def base_patterns() -> dict:
    return _load(".claude/domains/_base/health/secrets-patterns.json")


@pytest.fixture(scope="session")
def skill_md_text() -> str:
    """skill-health-check/SKILL.md 본문 — SSOT drift 검증용 (M001 후속)."""
    return (REPO_ROOT / ".claude/skills/skill-health-check/SKILL.md").read_text(encoding="utf-8")


def get_pattern(data: dict, section: str, pattern_id: str) -> dict:
    """Find pattern entry by dotted section path and id.

    Examples: section='common.runtime', 'common.hardcoded', 'domain.patterns'
    """
    cur = data
    for part in section.split("."):
        cur = cur[part]
    for entry in cur:
        if entry["id"] == pattern_id:
            return entry
    raise KeyError(f"{pattern_id} not found in {section}")


# excludeContexts SSOT — skill-health-check/SKILL.md security 카테고리 헤더 일관
EXCLUDE_CTX = {
    "env_var_reference": [
        re.compile(r"process\.env\.\w+"),
        re.compile(r"os\.environ\["),
        re.compile(r"os\.getenv\("),
        re.compile(r"System\.getenv\("),
        re.compile(r"os\.Getenv\("),
        re.compile(r"os\.LookupEnv\("),
    ],
    "type_declaration": [re.compile(r"\b(?:class|interface|type)\s+\w+")],
    "comment": [re.compile(r"^\s*(?://|#|\*|/\*)")],
}


def excluded_by(line: str, ctx_list: Iterable[str]) -> str | None:
    for ctx in ctx_list:
        for rgx in EXCLUDE_CTX[ctx]:
            if rgx.search(line):
                return ctx
    return None


def matches(entry: dict, line: str) -> bool:
    """True if line matches entry's pattern AND not excluded by entry's excludeContexts."""
    if not re.search(entry["pattern"], line):
        return False
    return excluded_by(line, entry.get("excludeContexts", [])) is None
