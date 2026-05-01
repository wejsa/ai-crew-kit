"""Shared fixtures and helpers for lessons-learned regression tests.

Phase 7 Step 2 — docs/v2/phase-7-plan.md
v1.23.0에 이미 구현된 lessons-learned 메커니즘의 회귀 보호 갭 메우기.

PR #44 리뷰 반영:
- C1 (CRITICAL): schema_errors가 (path, validator_keyword) 튜플 반환 →
  jsonschema 메시지 문자열 의존 제거. validator 속성은 안정적 공개 API.
- 심화 5-(a): valid_document/valid_lesson을 sample-valid.json에서 로드 →
  Step 1 fixture와 SSOT 통합 (이전엔 conftest 인라인 dict로 분기).
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

    하이픈 파일명이라 importlib 동적 로드. sys.modules 캐싱은 다른 테스트가
    동일 모듈을 재로드 시 충돌 회피용. 후속 부채 D11(모듈 추출)로 정리 예정.
    """
    spec = importlib.util.spec_from_file_location(
        "validate_lessons_learned",
        REPO_ROOT / "scripts" / "validate-lessons-learned.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["validate_lessons_learned"] = mod
    spec.loader.exec_module(mod)
    return mod.threshold_recommended


@pytest.fixture(scope="session")
def valid_document() -> dict:
    """Step 1 sample-valid.json을 SSOT로 사용 — PR #44 리뷰 심화 5-(a)."""
    return _load("tests/lessons/fixtures/sample-valid.json")


@pytest.fixture
def valid_lesson(valid_document: dict) -> dict:
    """Mutable single-lesson copy derived from valid_document SSOT."""
    return deepcopy(valid_document["lessons"][0])


def schema_errors(doc: dict, schema_obj: dict) -> list[tuple[str, str]]:
    """Return list of (path, validator_keyword) tuples for each violation.

    `validator` 필드는 jsonschema의 안정적 공개 API. 메시지 문자열 매칭
    대비 향후 jsonschema 버전 업에 면역. (PR #44 리뷰 CRITICAL #1)
    """
    from jsonschema import Draft7Validator

    return [
        (
            "/".join(str(p) for p in err.absolute_path) or "<root>",
            err.validator,
        )
        for err in sorted(Draft7Validator(schema_obj).iter_errors(doc), key=lambda e: list(e.path))
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
