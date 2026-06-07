#!/usr/bin/env python3
"""v1 project.json fixture에 migrations.json을 cumulative 적용한 결과가 project.schema.json을 통과하는지 검증.

Phase 8 Step 3 — examples 마이그레이션 검증 + 회귀 fixture (Task 8-3).

사용법:
    python3 scripts/validate-v2-migration.py                            # 4 fixtures 전체
    python3 scripts/validate-v2-migration.py --fixture <path>           # 단일 fixture
    python3 scripts/validate-v2-migration.py --diagnostic               # OQ-02 진단 모드 (누락 필드 보고)

검증 범위 (한계):
    - migrations.json의 `add_field` 타입 변경만 시뮬레이션. `add_gitignore_entry`
      등 다른 type은 project.json 외부 파일/리소스 영향이라 본 스크립트가 처리하지 않음
      (crew-upgrade SKILL.md Step 12-5에서 별도 메커니즘으로 처리).
    - cumulative 적용 — 0.0.0 ~ target 사이의 모든 add_field를 to 버전 오름차순 적용.
      project.schema.json의 top-level properties에 속하지 않는 path(예: backlog.* —
      backlog.json 영역)는 자동 스킵하여 schema `additionalProperties: false` 충돌 방지.

OQ-02 진단: migrations.json v2.0.0이 추가하지 않는 v2 schema 필드
(customDomain / healthCheck / orchestrator) 부재 상태에서 schema 통과 여부 확인.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft7Validator
except ImportError:
    print("FATAL: jsonschema 미설치. 'pip install jsonschema==4.21.1' 후 재실행.", file=sys.stderr)
    sys.exit(2)

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / ".claude" / "schemas" / "project.schema.json"
MIGRATIONS_PATH = REPO_ROOT / ".claude" / "schemas" / "migrations.json"
FIXTURES_DIR = REPO_ROOT / "tests" / "upgrade" / "fixtures"
TARGET_VERSION = "2.0.0"

# OQ-02: v2 schema에 정의되어 있으나 migrations.json이 add_field로 추가하지 않는 필드
OQ_02_FIELDS = ["customDomain", "healthCheck", "orchestrator"]

# migrations.json의 default 값에 등장하는 placeholder — crew-upgrade가 런타임 치환
# (예: kitVersion="${KIT_VERSION}" → 실제 업그레이드 대상 버전). 본 시뮬레이션은
# target 버전 + 공식 저장소 URL로 치환한다 (시뮬레이션 일관성 + schema pattern 통과).
DEFAULT_KIT_SOURCE = "https://github.com/wejsa/ai-crew-kit.git"


def make_placeholders(target: str, kit_source: str = DEFAULT_KIT_SOURCE) -> dict[str, str]:
    """crew-upgrade Step 12-4 환경 변수 시뮬레이션용 placeholder 매핑."""
    return {"${KIT_VERSION}": target, "${KIT_SOURCE}": kit_source}


def substitute_placeholders(value, placeholders: dict[str, str]):
    """default 값이 placeholder 문자열이면 치환. 그 외 deep 구조는 미변경."""
    if isinstance(value, str) and value in placeholders:
        return placeholders[value]
    return value


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def parse_version(v: str) -> tuple[int, ...]:
    """SemVer 비교용 — prerelease 부분 무시 (cumulative 정렬 목적)."""
    base = v.split("-")[0]
    return tuple(int(p) for p in base.split("."))


def apply_add_field(project: dict, change: dict, placeholders: dict[str, str] | None = None) -> tuple[bool, str]:
    """migrations.json의 add_field 1건 적용. 이미 존재하면 no-op.

    Raises:
        ValueError: 부모 경로가 dict가 아닐 때 (사용자 데이터 손상 감지 — silent overwrite 방지).

    Returns:
        (added, path) — added=True면 신규 추가, False면 이미 존재.
    """
    path = change["path"]
    default = substitute_placeholders(change.get("default"), placeholders or {})
    parts = path.split(".")
    cursor = project
    for idx, key in enumerate(parts[:-1]):
        if key not in cursor:
            cursor[key] = {}
        elif not isinstance(cursor[key], dict):
            parent = ".".join(parts[: idx + 1])
            raise ValueError(
                f"부모 경로 '{parent}'가 dict가 아님 ({type(cursor[key]).__name__}) — silent overwrite 방지를 위해 중단. "
                f"입력 project.json을 점검하거나 --rollback으로 복원 권장."
            )
        cursor = cursor[key]
    leaf = parts[-1]
    if leaf in cursor:
        return False, path
    cursor[leaf] = copy.deepcopy(default)
    return True, path


def apply_migrations(
    project: dict,
    migrations: dict,
    target: str,
    schema_top_keys: set[str] | None = None,
    placeholders: dict[str, str] | None = None,
) -> list[str]:
    """target 버전 *이하*의 모든 add_field cumulative 적용 (실제 crew-upgrade 동작 시뮬레이션).

    Args:
        project: 입력 project.json (in-place 변경).
        migrations: migrations.json 로드 결과.
        target: 마이그레이션 대상 버전 (예: "2.0.0").
        schema_top_keys: 이 set에 속하지 않는 top-level path key를 가진 add_field는 스킵
            (예: backlog.* — backlog.json 영역이라 project schema와 충돌). None이면 필터링 없음.
        placeholders: default 값 치환 매핑 (예: ${KIT_VERSION} → target). None이면 자동 생성.

    Returns:
        실제 추가된 path 목록 (이미 존재하던 leaf는 제외).
    """
    if placeholders is None:
        placeholders = make_placeholders(target)
    target_tuple = parse_version(target)
    relevant = sorted(
        (m for m in migrations.get("migrations", []) if parse_version(m["to"]) <= target_tuple),
        key=lambda m: parse_version(m["to"]),
    )
    added_fields: list[str] = []
    for migration in relevant:
        for change in migration.get("changes", []):
            if change["type"] != "add_field":
                continue
            top_key = change["path"].split(".")[0]
            if schema_top_keys is not None and top_key not in schema_top_keys:
                continue  # 다른 파일 영역 (예: backlog.json)
            was_added, path = apply_add_field(project, change, placeholders)
            if was_added:
                added_fields.append(path)
    return added_fields


def schema_top_level_keys(schema: dict) -> set[str]:
    """project.schema.json의 top-level properties 키 집합 — apply_migrations 필터용."""
    return set(schema.get("properties", {}).keys())


def validate_against_schema(project: dict, schema: dict) -> list[str]:
    """schema 위반 메시지 목록. 빈 리스트면 통과."""
    validator = Draft7Validator(schema)
    return [
        f"{'/'.join(str(p) for p in err.absolute_path) or '(root)'}: {err.message}"
        for err in sorted(validator.iter_errors(project), key=lambda e: e.path)
    ]


def diagnose_oq02(project: dict) -> list[str]:
    """OQ-02 진단: migrations.json이 추가하지 않는 v2 필드의 부재 보고."""
    missing: list[str] = []
    for field in OQ_02_FIELDS:
        if field not in project:
            missing.append(field)
    return missing


def validate_fixture(fixture_path: Path, schema: dict, migrations: dict, diagnostic: bool) -> bool:
    """단일 fixture 검증. 통과면 True."""
    fixture_path = fixture_path.resolve()
    try:
        rel = fixture_path.relative_to(REPO_ROOT)
    except ValueError:
        rel = fixture_path
    print(f"\n━━━ {rel} ━━━")
    fixture = load_json(fixture_path)
    print(f"  v1 kitVersion: {fixture.get('kitVersion', '(unset)')}")

    migrated = copy.deepcopy(fixture)
    added = apply_migrations(migrated, migrations, TARGET_VERSION, schema_top_level_keys(schema))
    if added:
        print(f"  적용된 add_field ({len(added)}건):")
        for path in added:
            print(f"    + {path}")
    else:
        print("  적용된 add_field: 0건 (이미 v2 형식이거나 마이그레이션 대상 없음)")

    errors = validate_against_schema(migrated, schema)
    if errors:
        print(f"  ✗ schema 위반 ({len(errors)}건):")
        for err in errors:
            print(f"    {err}")
        return False
    print("  ✓ project.schema.json 통과")

    if diagnostic:
        missing = diagnose_oq02(migrated)
        if missing:
            print(f"  ℹ OQ-02 진단: 부재 v2 필드 {missing} → schema 통과(optional 필드)")
        else:
            print("  ℹ OQ-02 진단: customDomain/healthCheck/orchestrator 모두 존재")

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fixture", type=Path, help="단일 fixture 경로 (미지정 시 tests/upgrade/fixtures/v1-*.json 전체)")
    parser.add_argument("--diagnostic", action="store_true", help="OQ-02 진단 모드 (누락 v2 필드 보고)")
    args = parser.parse_args()

    if not SCHEMA_PATH.exists():
        print(f"FATAL: {SCHEMA_PATH} 부재", file=sys.stderr)
        return 2
    if not MIGRATIONS_PATH.exists():
        print(f"FATAL: {MIGRATIONS_PATH} 부재", file=sys.stderr)
        return 2

    schema = load_json(SCHEMA_PATH)
    migrations = load_json(MIGRATIONS_PATH)

    if args.fixture:
        fixtures = [args.fixture]
    else:
        fixtures = sorted(FIXTURES_DIR.glob("v1-*-project.json"))
        if not fixtures:
            print(f"FATAL: {FIXTURES_DIR}/v1-*-project.json 매칭 0건", file=sys.stderr)
            return 2

    print(f"검증 대상: {len(fixtures)}건, 타겟 버전: v{TARGET_VERSION}")
    results = [validate_fixture(f, schema, migrations, args.diagnostic) for f in fixtures]
    passed = sum(results)
    total = len(results)
    print(f"\n━━━ 결과 ━━━")
    print(f"  통과: {passed}/{total}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
