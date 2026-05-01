#!/usr/bin/env python3
"""Validate .claude/state/lessons-learned.json (Phase 7 Step 1).

Phase 7 Lean Closure (옵션 A) — docs/v2/phase-7-plan.md
이미 v1.23.0에 구현된 lessons-learned 메커니즘의 회귀 보호 갭을 메운다.

검증 항목:
1. JSON Schema (lessons-learned.schema.json) 준수
2. taskId cross-ref — completed.json + backlog.json(archived 포함) 실재 검증
3. description 필드 secrets 필터 — _base/health/secrets-patterns.json
   common.hardcoded(SEC-S01~S05) 정규식 매칭 시 CRITICAL FAIL
4. impact 임계값 sanity (WARN only — 사용자 override 허용)
   권장: appliedCount>=5 → high / >=3 → medium / <3 → low

파일 부재 시: SKIP + exit 0 (메타 레포 / 신규 프로젝트 graceful)

Used by: .github/workflows/secrets-tests.yml
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LESSONS_PATH = REPO_ROOT / ".claude/state/lessons-learned.json"
SCHEMA_PATH = REPO_ROOT / ".claude/schemas/lessons-learned.schema.json"
SECRETS_PATTERNS_PATH = REPO_ROOT / ".claude/domains/_base/health/secrets-patterns.json"
COMPLETED_PATH = REPO_ROOT / ".claude/state/completed.json"
BACKLOG_PATH = REPO_ROOT / ".claude/state/backlog.json"


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_known_task_ids() -> set[str]:
    ids: set[str] = set()
    if COMPLETED_PATH.exists():
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
    if BACKLOG_PATH.exists():
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
    return ids


def load_secret_patterns() -> list[tuple[str, re.Pattern[str]]]:
    if not SECRETS_PATTERNS_PATH.exists():
        return []
    data = load_json(SECRETS_PATTERNS_PATH)
    out: list[tuple[str, re.Pattern[str]]] = []
    for entry in data.get("common", {}).get("hardcoded", []):
        try:
            out.append((entry["id"], re.compile(entry["pattern"])))
        except re.error as exc:
            print(f"⚠ secrets-patterns {entry.get('id')} compile failed: {exc}")
    return out


def threshold_recommended(applied: int) -> str:
    if applied >= 5:
        return "high"
    if applied >= 3:
        return "medium"
    return "low"


def main() -> int:
    if not LESSONS_PATH.exists():
        print(f"⊘ {LESSONS_PATH.relative_to(REPO_ROOT)} not present — SKIP (graceful)")
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
        data = load_json(LESSONS_PATH)
    except json.JSONDecodeError as exc:
        print(f"✗ {LESSONS_PATH.relative_to(REPO_ROOT)} invalid JSON: {exc}")
        return 1

    validator = Draft7Validator(schema)
    schema_errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if schema_errors:
        for err in schema_errors:
            loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
            print(f"✗ schema {loc}: {err.message}")
        return 1
    print(f"✓ {LESSONS_PATH.relative_to(REPO_ROOT)} schema OK ({len(data.get('lessons', []))} lessons)")

    fail = 0
    warn = 0
    known_ids = collect_known_task_ids()
    secret_patterns = load_secret_patterns()
    if not secret_patterns:
        print("⚠ secrets-patterns common.hardcoded not loaded — secrets filter SKIPPED")

    for lesson in data.get("lessons", []):
        lid = lesson["id"]

        if known_ids and lesson["taskId"] not in known_ids:
            print(f"✗ cross-ref {lid}: taskId '{lesson['taskId']}' not in completed.json/backlog.json")
            fail += 1

        for pid, pat in secret_patterns:
            if pat.search(lesson["description"]):
                print(f"✗ secrets {lid}: description matches {pid}")
                fail += 1

        recommended = threshold_recommended(lesson["appliedCount"])
        if recommended != lesson["impact"]:
            print(
                f"⚠ impact {lid}: appliedCount={lesson['appliedCount']} "
                f"recommends '{recommended}' but is '{lesson['impact']}' (override OK)"
            )
            warn += 1

    print(
        f"\n{len(data.get('lessons', []))} lessons checked, "
        f"{fail} CRITICAL fail, {warn} impact threshold warnings."
    )
    if not known_ids:
        print("⊘ completed.json/backlog.json absent — cross-ref SKIPPED (meta-repo)")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
