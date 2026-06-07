#!/usr/bin/env python3
"""Validate .claude/state/lessons-learned.json (Phase 7 Step 1).

Phase 7 Lean Closure (옵션 A) — docs/v2/phase-7-plan.md
이미 v1.23.0에 구현된 lessons-learned 메커니즘의 회귀 보호 갭을 메운다.

검증 항목 (Step 1 책임):
1. JSON Schema (lessons-learned.schema.json) 준수
2. taskId cross-ref — completed.json + backlog.json(archived 포함) 실재 검증
   - 양쪽 모두 부재 시 SKIP (메타 레포 / 신규 프로젝트)
   - 한쪽만 부재 시 WARN (PR #43 리뷰 MINOR #1)
3. impact 임계값 sanity (WARN only — 사용자 override 허용)
   권장: appliedCount>=5 → high / >=3 → medium / <3 → low

> secrets 필터링(SEC-S01~S05)은 Step 2(crew-retro §5.3 통합)에서 도입.
> SEC-S01~S05 모두 `excludeContexts: ["comment"]` 보유 → lesson description은
> 코멘트성 텍스트라 정적 검증 시 false positive 다발 (PR #43 리뷰 MAJOR).
> Step 2에서 crew-retro AskUserQuestion으로 사용자 판단 위임.

모드:
- 기본: `.claude/state/lessons-learned.json` 검증. 부재 시 graceful skip(exit 0)
- `--fixture <path>`: 지정 파일 검증. cross-ref는 known_ids 부재로 자연 SKIP.
  CI에서 validator 동작 증명용 (PR #43 리뷰 CRITICAL #1).

Used by: .github/workflows/secrets-tests.yml
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LESSONS_PATH = REPO_ROOT / ".claude/state/lessons-learned.json"
SCHEMA_PATH = REPO_ROOT / ".claude/schemas/lessons-learned.schema.json"
COMPLETED_PATH = REPO_ROOT / ".claude/state/completed.json"
BACKLOG_PATH = REPO_ROOT / ".claude/state/backlog.json"


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_known_task_ids() -> tuple[set[str], bool, bool]:
    """Return (ids, completed_seen, backlog_seen)."""
    ids: set[str] = set()
    completed_seen = COMPLETED_PATH.exists()
    backlog_seen = BACKLOG_PATH.exists()
    if completed_seen:
        try:
            data = load_json(COMPLETED_PATH)
            if isinstance(data, dict):
                for entry in data.get("tasks", []):
                    if "id" in entry:
                        ids.add(entry["id"])
            elif isinstance(data, list):
                for entry in data:
                    if isinstance(entry, dict) and "id" in entry:
                        ids.add(entry["id"])
        except (json.JSONDecodeError, OSError):
            pass
    if backlog_seen:
        try:
            data = load_json(BACKLOG_PATH)
            if isinstance(data, dict):
                for entry in data.get("tasks", []):
                    if "id" in entry:
                        ids.add(entry["id"])
                for entry in data.get("archived", []):
                    if isinstance(entry, dict) and "id" in entry:
                        ids.add(entry["id"])
        except (json.JSONDecodeError, OSError):
            pass
    return ids, completed_seen, backlog_seen


def threshold_recommended(applied: int) -> str:
    if applied >= 5:
        return "high"
    if applied >= 3:
        return "medium"
    return "low"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--fixture",
        type=Path,
        default=None,
        help="검증 대상 파일 경로 지정 (CI에서 validator 동작 증명용)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target = args.fixture if args.fixture is not None else DEFAULT_LESSONS_PATH
    is_fixture = args.fixture is not None
    label = target.relative_to(REPO_ROOT) if target.is_absolute() else target

    if not target.exists():
        if is_fixture:
            print(f"✗ fixture not found: {label}")
            return 1
        print(f"⊘ {label} not present — SKIP (graceful)")
        return 0

    if not SCHEMA_PATH.exists():
        print(f"✗ schema not found at {SCHEMA_PATH.relative_to(REPO_ROOT)}")
        return 1

    try:
        from jsonschema import Draft7Validator
    except ImportError:
        print("✗ jsonschema not installed (pip install jsonschema)")
        return 1

    schema = load_json(SCHEMA_PATH)
    try:
        data = load_json(target)
    except json.JSONDecodeError as exc:
        print(f"✗ {label} invalid JSON: {exc}")
        return 1

    validator = Draft7Validator(schema)
    schema_errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if schema_errors:
        for err in schema_errors:
            loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
            print(f"✗ schema {loc}: {err.message}")
        return 1
    print(f"✓ {label} schema OK ({len(data.get('lessons', []))} lessons)")

    fail = 0
    warn = 0
    known_ids, completed_seen, backlog_seen = collect_known_task_ids()

    if not completed_seen and not backlog_seen:
        cross_ref_mode = "skip"
    elif completed_seen and backlog_seen:
        cross_ref_mode = "strict"
    else:
        cross_ref_mode = "partial"

    for lesson in data.get("lessons", []):
        lid = lesson["id"]

        if cross_ref_mode == "strict":
            if lesson["taskId"] not in known_ids:
                print(f"✗ cross-ref {lid}: taskId '{lesson['taskId']}' not in completed.json/backlog.json")
                fail += 1
        elif cross_ref_mode == "partial":
            if lesson["taskId"] not in known_ids:
                missing = "backlog.json" if completed_seen else "completed.json"
                print(
                    f"⚠ cross-ref {lid}: taskId '{lesson['taskId']}' not found "
                    f"(WARN — {missing} absent, partial check)"
                )
                warn += 1

        recommended = threshold_recommended(lesson["appliedCount"])
        if recommended != lesson["impact"]:
            print(
                f"⚠ impact {lid}: appliedCount={lesson['appliedCount']} "
                f"recommends '{recommended}' but is '{lesson['impact']}' (override OK)"
            )
            warn += 1

    print(
        f"\n{len(data.get('lessons', []))} lessons checked, "
        f"{fail} CRITICAL fail, {warn} warnings."
    )
    if cross_ref_mode == "skip":
        print("⊘ completed.json/backlog.json absent — cross-ref SKIPPED")
    elif cross_ref_mode == "partial":
        missing = "backlog.json" if completed_seen else "completed.json"
        print(f"⚠ {missing} absent — cross-ref partial (WARN-level only)")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
