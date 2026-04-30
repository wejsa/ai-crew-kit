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
def fintech_patterns() -> dict:
    return _load(".claude/domains/fintech/health/secrets-patterns.json")


@pytest.fixture(scope="session")
def healthcare_patterns() -> dict:
    return _load(".claude/domains/healthcare/health/secrets-patterns.json")


@pytest.fixture(scope="session")
def ecommerce_patterns() -> dict:
    return _load(".claude/domains/ecommerce/health/secrets-patterns.json")


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


# Checksum helpers — SKILL.md SEC-07 §체크섬 검증 1:1 구현
def luhn_ok(num: str) -> bool:
    """PAN Luhn — SKILL.md SEC-07 fintech 체크섬."""
    digits = [int(c) for c in num if c.isdigit()]
    if len(digits) != 16:
        return False
    s = 0
    for i, d in enumerate(reversed(digits)):
        s += d if i % 2 == 0 else (d * 2 if d * 2 < 10 else d * 2 - 9)
    return s % 10 == 0


def rrn_ok(num: str) -> bool:
    """한국 주민등록번호 (13자리) — 가중치 [2,3,4,5,6,7,8,9,2,3,4,5]."""
    n = [int(c) for c in num if c.isdigit()]
    if len(n) != 13:
        return False
    w = [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5]
    s = sum(n[i] * w[i] for i in range(12))
    return (11 - s % 11) % 10 == n[12]


def biz_ok(num: str) -> bool:
    """한국 사업자등록번호 (10자리) — 가중치 [1,3,7,1,3,7,1,3,5] + 8번째×5÷10 몫."""
    n = [int(c) for c in num if c.isdigit()]
    if len(n) != 10:
        return False
    w = [1, 3, 7, 1, 3, 7, 1, 3, 5]
    s = sum(n[i] * w[i] for i in range(9))
    s += (n[8] * 5) // 10
    return (10 - s % 10) % 10 == n[9]
