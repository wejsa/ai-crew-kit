#!/usr/bin/env python3
"""Validate _category.json weight sums equal 100 across _base + 4 domains.

Phase 5 후속 트랙 A Step 3 — docs/v2/phase-5-tests-plan.md
PR #35(D0 alpha.2 hook-safety 부채 해소) 명시화 결과 검증. 도메인 _category.json
drift 시 정규화 폴백에 가려져 점수가 암묵적으로 보정되는 패턴 재발 방지.

3가지 형식 모두 인식:
  1. _base 배열 형식: {"categories": [{...weight}, ...]}
  2. 형태 A (legacy fintech): {"additionalCategories": [...], "weightOverrides": {...}}
  3. 형태 B (dictionary):     {"categories": {id: {weight: N, ...}, ...}}

Used by: .github/workflows/secrets-tests.yml
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SUM = 100


def category_sum(data: dict) -> int | None:
    """Compute total weight across a _category.json. Returns None if format unknown."""
    if "additionalCategories" in data:
        # 형태 A: legacy fintech (additionalCategories + weightOverrides)
        s = sum(c.get("weight", 0) for c in data.get("additionalCategories", []))
        s += sum(data.get("weightOverrides", {}).values())
        return s

    cats = data.get("categories")
    if isinstance(cats, list):
        # _base 배열 형식
        return sum(c.get("weight", 0) for c in cats)
    if isinstance(cats, dict):
        # 형태 B: ecommerce/healthcare/saas
        return sum(v.get("weight", 0) for v in cats.values() if isinstance(v, dict))
    return None


def main() -> int:
    targets = sorted((REPO_ROOT / ".claude/domains").glob("*/health/_category.json"))
    if not targets:
        print("✗ No _category.json files found")
        return 1
    if not (REPO_ROOT / ".claude/domains/_base/health/_category.json").exists():
        print("✗ _base/health/_category.json — required file missing")
        return 1

    fail = 0
    for target in targets:
        rel = target.relative_to(REPO_ROOT)
        data = json.loads(target.read_text(encoding="utf-8"))
        total = category_sum(data)
        if total is None:
            print(f"✗ {rel} — unknown format (no categories/additionalCategories key)")
            fail += 1
            continue
        if total != EXPECTED_SUM:
            print(f"✗ {rel} — weight sum {total} != {EXPECTED_SUM} (정규화 폴백 의존 — PR #35 명시화 필요)")
            fail += 1
        else:
            print(f"✓ {rel} — sum = {total}")

    print(f"\nChecked {len(targets)} _category.json files, {fail} failed.")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
