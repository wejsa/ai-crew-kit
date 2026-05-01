"""Shared fixtures and helpers for lessons-learned regression tests.

Phase 7 Step 2 — docs/v2/phase-7-plan.md
v1.23.0에 이미 구현된 lessons-learned 메커니즘의 회귀 보호 갭 메우기.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def schema() -> dict:
    return _load(".claude/schemas/lessons-learned.schema.json")


@pytest.fixture(scope="session")
def base_patterns() -> dict:
    return _load(".claude/domains/_base/health/secrets-patterns.json")


@pytest.fixture(scope="session")
def hardcoded_patterns(base_patterns: dict) -> list[dict]:
    """SEC-S01~S05 — common.hardcoded entries."""
    return base_patterns["common"]["hardcoded"]


@pytest.fixture(scope="session")
def threshold_recommended():
    """Load threshold_recommended() from validate-lessons-learned.py.

    Hyphenated filename requires importlib.
    """
    spec = importlib.util.spec_from_file_location(
        "validate_lessons_learned",
        REPO_ROOT / "scripts" / "validate-lessons-learned.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["validate_lessons_learned"] = mod
    spec.loader.exec_module(mod)
    return mod.threshold_recommended


@pytest.fixture
def valid_lesson() -> dict:
    """Minimal valid lesson — tests deepcopy this and mutate."""
    return {
        "id": "L-001",
        "taskId": "TEST-1",
        "category": "quality",
        "title": "Sample valid lesson",
        "description": "Plain description without secrets.",
        "impact": "high",
        "tags": ["sample"],
        "appliedCount": 5,
        "createdAt": "2026-04-01T00:00:00Z",
        "updatedAt": "2026-04-15T00:00:00Z",
    }


@pytest.fixture
def valid_document(valid_lesson: dict) -> dict:
    return {
        "metadata": {"version": 1, "updatedAt": "2026-05-01T00:00:00Z"},
        "lessons": [deepcopy(valid_lesson)],
    }


def schema_errors(doc: dict, schema_obj: dict) -> list[str]:
    """Return human-readable schema error messages (empty list if valid)."""
    from jsonschema import Draft7Validator

    validator = Draft7Validator(schema_obj)
    return [
        f"{'/'.join(str(p) for p in err.absolute_path) or '<root>'}: {err.message}"
        for err in sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    ]


def find_pattern(patterns: list[dict], pid: str) -> re.Pattern[str]:
    for entry in patterns:
        if entry["id"] == pid:
            return re.compile(entry["pattern"])
    raise KeyError(pid)


def mutate(base: dict, **overrides: Any) -> dict:
    """Return deep-copied base with top-level lesson[0] overrides applied."""
    out = deepcopy(base)
    out["lessons"][0].update(overrides)
    return out
