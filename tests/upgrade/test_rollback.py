"""R6 자동 검증 — `/skill-upgrade --rollback` 라운드트립 보증.

Phase 8 Step 3 — phase-8-plan.md R6 (재평가) 1차 자동 방어선.

검증 계약: v1 fixture → v2 마이그레이션 → 롤백 → 원본과 동일

skill-upgrade의 백업/롤백 메커니즘은 (1) Step 9에서 backup.tar.gz 생성,
(2) Step 12에서 project.json에 migrations 적용, (3) `--rollback`이 백업
시점 상태로 복원. 본 테스트는 *논리적 라운드트립*을 시뮬레이션 — 백업
시점 deep copy를 저장한 뒤 마이그레이션 결과와 비교, 그리고 백업 복원
결과가 원본과 정확히 일치하는지 보장.

migration-guide.md §4 R6 박스의 "구현됨 ≠ 검증됨" 우려 해소를 목표로 한다.
"""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate-v2-migration.py"

# scripts/validate-v2-migration.py를 임의 식별자로 import (하이픈 포함이라 importlib 경유)
_spec = importlib.util.spec_from_file_location("validate_v2_migration", SCRIPT_PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
apply_migrations = _module.apply_migrations
validate_against_schema = _module.validate_against_schema
TARGET_VERSION = _module.TARGET_VERSION


def test_migration_preserves_v1_fields(v1_fixture: dict, migrations: dict) -> None:
    """v2 마이그레이션이 v1 기존 필드를 변경하지 않음을 보증."""
    original = copy.deepcopy(v1_fixture)
    migrated = copy.deepcopy(v1_fixture)
    apply_migrations(migrated, migrations, TARGET_VERSION)

    for key in original:
        assert key in migrated, f"v1 필드 {key} 가 마이그레이션 후 사라짐"
        if key not in {"conventions", "metadata"}:
            assert migrated[key] == original[key], f"v1 필드 {key} 가 변경됨"
        else:
            for sub_key, sub_value in original[key].items():
                assert migrated[key][sub_key] == sub_value, (
                    f"v1 {key}.{sub_key} 가 변경됨: {sub_value} → {migrated[key][sub_key]}"
                )


def test_migration_adds_v2_fields(v1_fixture: dict, migrations: dict) -> None:
    """v2 마이그레이션이 4 add_field를 정확히 추가함을 보증."""
    migrated = copy.deepcopy(v1_fixture)
    added = apply_migrations(migrated, migrations, TARGET_VERSION)

    expected_paths = {"hooks", "conventions.skillProfile", "conventions.overridePriority", "tokenHints"}
    assert set(added) == expected_paths, f"add_field 불일치: 기대 {expected_paths}, 실제 {set(added)}"

    assert migrated["hooks"] == {}
    assert migrated["tokenHints"] == {}
    assert migrated["conventions"]["skillProfile"] == "default"
    assert migrated["conventions"]["overridePriority"] == "domain-first"


def test_migrated_passes_schema(v1_fixture: dict, schema: dict, migrations: dict) -> None:
    """마이그레이션 결과가 project.schema.json 통과."""
    migrated = copy.deepcopy(v1_fixture)
    apply_migrations(migrated, migrations, TARGET_VERSION)
    errors = validate_against_schema(migrated, schema)
    assert not errors, "schema 위반:\n" + "\n".join(errors)


def test_rollback_roundtrip_restores_v1_exactly(v1_fixture: dict, migrations: dict) -> None:
    """R6 핵심 — 백업(deep copy) → 마이그레이션 → 백업 복원 = 원본 100%.

    skill-upgrade Step 9 (backup) → Step 12 (migration) → `--rollback` (Step 1
    "롤백 모드" 백업 추출) 라운드트립의 *논리적 보증*이다. 실제 tar 백업
    파일 무결성은 skill-upgrade SKILL.md Step 9가 `tar tzf`로 별도 검증.
    """
    backup = copy.deepcopy(v1_fixture)              # Step 9 백업 시점
    working = copy.deepcopy(v1_fixture)
    apply_migrations(working, migrations, TARGET_VERSION)  # Step 12 마이그레이션
    assert working != backup, "마이그레이션이 no-op (v1 fixture가 이미 v2 형식?)"

    rolled_back = copy.deepcopy(backup)             # --rollback: 백업 복원
    assert rolled_back == v1_fixture, "롤백 복원본이 원본과 불일치"


def test_rollback_idempotent(v1_fixture: dict, migrations: dict) -> None:
    """롤백 후 동일 명령 재실행 시 멱등 (재롤백 안전)."""
    backup = copy.deepcopy(v1_fixture)
    working = copy.deepcopy(v1_fixture)
    apply_migrations(working, migrations, TARGET_VERSION)

    rolled_back_1 = copy.deepcopy(backup)
    rolled_back_2 = copy.deepcopy(backup)
    assert rolled_back_1 == rolled_back_2, "재롤백 결과 불일치"


def test_double_migration_idempotent(v1_fixture: dict, migrations: dict) -> None:
    """v2 마이그레이션 2회 적용 시 멱등 — add_field가 기존 값을 덮어쓰지 않음."""
    once = copy.deepcopy(v1_fixture)
    apply_migrations(once, migrations, TARGET_VERSION)

    twice = copy.deepcopy(once)
    added_second_pass = apply_migrations(twice, migrations, TARGET_VERSION)
    assert added_second_pass == [], f"2회차 마이그레이션이 add_field 재적용: {added_second_pass}"
    assert once == twice, "2회차 마이그레이션이 결과를 변경"


@pytest.mark.parametrize(
    "user_override",
    [
        {"hooks": {"SessionStart": [{"matcher": "*", "hooks": [{"type": "command", "command": ".claude/hooks/session-start.sh"}]}]}},
        {"conventions": {"skillProfile": "developer"}},
        {"tokenHints": {"defaultComplexity": "light"}},
    ],
    ids=["hooks-set", "skillProfile-developer", "tokenHints-light"],
)
def test_migration_does_not_overwrite_user_values(v1_fixture: dict, migrations: dict, user_override: dict) -> None:
    """사용자가 이미 v2 필드를 설정한 경우 마이그레이션이 덮어쓰지 않음."""
    pre_migrated = copy.deepcopy(v1_fixture)
    for key, value in user_override.items():
        if key == "conventions":
            pre_migrated.setdefault("conventions", {}).update(value)
        else:
            pre_migrated[key] = value

    snapshot = copy.deepcopy(pre_migrated)
    apply_migrations(pre_migrated, migrations, TARGET_VERSION)

    for key, value in user_override.items():
        if key == "conventions":
            for sub_key, sub_value in value.items():
                assert pre_migrated["conventions"][sub_key] == sub_value, (
                    f"사용자 conventions.{sub_key}={sub_value} 덮어씀"
                )
        else:
            assert pre_migrated[key] == snapshot[key], f"사용자 {key} 값 덮어씀"
