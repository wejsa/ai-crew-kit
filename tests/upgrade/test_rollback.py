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
apply_add_field = _module.apply_add_field
validate_against_schema = _module.validate_against_schema
schema_top_level_keys = _module.schema_top_level_keys
TARGET_VERSION = _module.TARGET_VERSION


def _migrate(project: dict, migrations: dict, schema: dict) -> list[str]:
    """schema-aware cumulative migration apply. project를 in-place 변경하고 추가된 path 반환."""
    return apply_migrations(project, migrations, TARGET_VERSION, schema_top_level_keys(schema))


def test_migration_preserves_v1_fields(v1_fixture: dict, migrations: dict, schema: dict) -> None:
    """v2 마이그레이션이 v1 기존 필드를 변경하지 않음을 보증."""
    original = copy.deepcopy(v1_fixture)
    migrated = copy.deepcopy(v1_fixture)
    _migrate(migrated, migrations, schema)

    for key in original:
        assert key in migrated, f"v1 필드 {key} 가 마이그레이션 후 사라짐"
        if key not in {"conventions", "metadata"}:
            assert migrated[key] == original[key], f"v1 필드 {key} 가 변경됨"
        else:
            for sub_key, sub_value in original[key].items():
                assert migrated[key][sub_key] == sub_value, (
                    f"v1 {key}.{sub_key} 가 변경됨: {sub_value} → {migrated[key][sub_key]}"
                )


def test_migration_adds_v2_fields(v1_fixture: dict, migrations: dict, schema: dict) -> None:
    """v2 마이그레이션이 4 add_field를 정확히 추가함을 보증."""
    migrated = copy.deepcopy(v1_fixture)
    added = _migrate(migrated, migrations, schema)

    expected_paths = {"hooks", "conventions.skillProfile", "conventions.overridePriority", "tokenHints"}
    assert set(added) == expected_paths, f"add_field 불일치: 기대 {expected_paths}, 실제 {set(added)}"

    assert migrated["hooks"] == {}
    assert migrated["tokenHints"] == {}
    assert migrated["conventions"]["skillProfile"] == "default"
    assert migrated["conventions"]["overridePriority"] == "domain-first"


def test_migrated_passes_schema(v1_fixture: dict, schema: dict, migrations: dict) -> None:
    """마이그레이션 결과가 project.schema.json 통과."""
    migrated = copy.deepcopy(v1_fixture)
    _migrate(migrated, migrations, schema)
    errors = validate_against_schema(migrated, schema)
    assert not errors, "schema 위반:\n" + "\n".join(errors)


def test_rollback_roundtrip_restores_v1_exactly(v1_fixture: dict, migrations: dict, schema: dict) -> None:
    """R6 핵심 — 백업 → 마이그레이션된 working → 백업 복원 = 원본 100%.

    skill-upgrade Step 9 (backup tar.gz) → Step 12 (migration applied to working
    project.json) → `--rollback` (working 폐기 + tar 추출 복원) 라운드트립의 *논리적
    보증*. 실제 tar 무결성은 skill-upgrade SKILL.md Step 9의 `tar tzf` 검증과 본 PR
    migration-guide.md §4 사전 체크리스트가 책임.

    핵심: working에 마이그레이션 *적용 후*, working을 백업으로 *덮어써서* 라운드트립
    검증. (이전 버전은 working을 사용하지 않아 vacuous truth였음 — 외부 리뷰 #1 fix)
    """
    backup = copy.deepcopy(v1_fixture)              # Step 9 백업 시점
    working = copy.deepcopy(v1_fixture)
    _migrate(working, migrations, schema)           # Step 12 마이그레이션
    assert working != backup, "마이그레이션이 no-op (v1 fixture가 이미 v2 형식?)"
    assert "hooks" in working and "hooks" not in backup, "마이그레이션이 hooks 필드를 추가하지 않음"

    # --rollback 시뮬레이션: working을 backup 내용으로 완전 교체
    working.clear()
    working.update(copy.deepcopy(backup))

    assert working == v1_fixture, "라운드트립 후 working이 원본 v1과 불일치"
    assert "hooks" not in working, "롤백이 v2 필드를 제거하지 못함"


def test_rollback_idempotent_after_migration(v1_fixture: dict, migrations: dict, schema: dict) -> None:
    """진짜 멱등성 — 1차 롤백 후 사용자 dirty 변경이 발생해도 2차 롤백이 정확히 v1로 복원.

    3차 외부 리뷰 보강: 같은 backup으로 단순히 두 번 clear+update하면 deterministic
    operation이라 trivial 통과. 진짜 비-trivial 멱등성은 *1차 롤백 → 사용자 실수
    dirty 변경 → 2차 롤백이 dirty를 무시하고 정확히 복원* 시나리오로 검증해야 한다.
    """
    backup = copy.deepcopy(v1_fixture)
    working = copy.deepcopy(v1_fixture)
    _migrate(working, migrations, schema)
    assert working != v1_fixture

    # 1차 롤백
    working.clear()
    working.update(copy.deepcopy(backup))
    assert working == v1_fixture, "1차 롤백 후 v1과 불일치"

    # 사용자 실수로 dirty 변경 발생 (예: 수동 편집, 다른 도구의 부분 쓰기)
    working["spurious"] = "user accident"
    working.setdefault("conventions", {})["accidental"] = True

    # 2차 롤백 — dirty 변경을 무시하고 v1으로 정확히 복원해야 진짜 멱등
    working.clear()
    working.update(copy.deepcopy(backup))
    assert working == v1_fixture, "재롤백 후 v1과 불일치 (멱등 위반)"
    assert "spurious" not in working, "재롤백이 dirty 키를 제거하지 못함"
    assert "accidental" not in working["conventions"], "재롤백이 dirty 중첩 키를 제거하지 못함"


def test_double_migration_idempotent(v1_fixture: dict, migrations: dict, schema: dict) -> None:
    """v2 마이그레이션 2회 적용 시 멱등 — add_field가 기존 값을 덮어쓰지 않음."""
    once = copy.deepcopy(v1_fixture)
    _migrate(once, migrations, schema)

    twice = copy.deepcopy(once)
    added_second_pass = _migrate(twice, migrations, schema)
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
def test_migration_does_not_overwrite_user_values(v1_fixture: dict, migrations: dict, schema: dict, user_override: dict) -> None:
    """사용자가 이미 v2 필드를 설정한 경우 마이그레이션이 덮어쓰지 않음."""
    pre_migrated = copy.deepcopy(v1_fixture)
    for key, value in user_override.items():
        if key == "conventions":
            pre_migrated.setdefault("conventions", {}).update(value)
        else:
            pre_migrated[key] = value

    snapshot = copy.deepcopy(pre_migrated)
    _migrate(pre_migrated, migrations, schema)

    for key, value in user_override.items():
        if key == "conventions":
            for sub_key, sub_value in value.items():
                assert pre_migrated["conventions"][sub_key] == sub_value, (
                    f"사용자 conventions.{sub_key}={sub_value} 덮어씀"
                )
        else:
            assert pre_migrated[key] == snapshot[key], f"사용자 {key} 값 덮어씀"


def test_apply_add_field_fails_fast_on_non_dict_parent() -> None:
    """apply_add_field가 부모 경로가 dict 아닐 때 silent overwrite 대신 ValueError로 즉시 중단.

    외부 리뷰 #3 — migration tool 안전성: 손상된 입력에 대해 명시적 오류 vs 조용한 데이터
    손실. v1.x 시기 사용자 project.json 직접 편집 → 타입 손상 가능.
    """
    broken = {"conventions": "not-a-dict"}
    change = {"path": "conventions.skillProfile", "default": "default"}

    with pytest.raises(ValueError, match="dict가 아님"):
        apply_add_field(broken, change)

    # 입력 보존 — silent overwrite 안 됨
    assert broken == {"conventions": "not-a-dict"}, "ValueError 발생 후에도 입력이 보존되지 않음"


def test_cumulative_apply_skips_non_project_paths(schema: dict, migrations: dict) -> None:
    """cumulative 적용 시 project schema에 없는 top-level path(예: backlog.*)는 스킵.

    외부 리뷰 #2 — migrations.json v1.39.0의 `backlog.step.prLineLimit`은 project.json
    영역이 아님(`additionalProperties: false`와 충돌). schema-aware 필터로 안전 우회.
    """
    minimal = {"name": "x", "version": "1.0.0"}
    apply_migrations(minimal, migrations, TARGET_VERSION, schema_top_level_keys(schema))

    assert "backlog" not in minimal, "backlog.* 필드가 project.json에 누락 적용됨 (schema 위반 위험)"
    errors = validate_against_schema(minimal, schema)
    assert not errors, f"cumulative 적용 결과 schema 위반: {errors}"
