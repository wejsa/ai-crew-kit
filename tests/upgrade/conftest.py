"""Shared fixtures for tests/upgrade/.

Phase 8 Step 3 — examples 마이그레이션 검증 + R6 자동 검증.
validate-v2-migration.py의 apply_migrations 로직을 재사용하기 위해
scripts/ 디렉토리를 sys.path에 추가한다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
SCHEMAS_DIR = REPO_ROOT / ".claude" / "schemas"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture(scope="session")
def schema() -> dict:
    """project.schema.json 로드."""
    with (SCHEMAS_DIR / "project.schema.json").open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def migrations() -> dict:
    """migrations.json 로드."""
    with (SCHEMAS_DIR / "migrations.json").open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(params=sorted(FIXTURES_DIR.glob("v1-*-project.json")), ids=lambda p: p.stem)
def v1_fixture_path(request) -> Path:
    """v1-*-project.json fixture 경로 (parametrize)."""
    return request.param


@pytest.fixture
def v1_fixture(v1_fixture_path: Path) -> dict:
    """v1 fixture를 dict로 로드."""
    with v1_fixture_path.open(encoding="utf-8") as f:
        return json.load(f)
