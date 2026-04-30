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


def category_sum(data: dict, base_data: dict | None = None) -> tuple[int | None, list[str]]:
    """Compute total weight across a _category.json.

    Returns (sum, warnings). sum is None if format unknown. warnings는 형태 A 도메인이
    _base 카테고리 일부를 weightOverrides에 누락하여 _base default가 자동 적용되는 경우
    효과적 sum과 명시적 sum 불일치를 알리는 advisory 메시지(M001 후속).
    """
    warnings: list[str] = []

    if "additionalCategories" in data:
        # 형태 A: legacy fintech (additionalCategories + weightOverrides)
        s = sum(c.get("weight", 0) for c in data.get("additionalCategories", []))
        s += sum(data.get("weightOverrides", {}).values())
        if base_data and isinstance(base_data.get("categories"), list):
            base_ids = {c["id"] for c in base_data["categories"] if isinstance(c, dict) and "id" in c}
            override_ids = set(data.get("weightOverrides", {}).keys())
            missing = base_ids - override_ids
            if missing:
                warnings.append(
                    f"weightOverrides 미커버 _base 카테고리: {sorted(missing)} "
                    "(_base default 자동 적용 — 효과적 sum과 명시 sum 불일치 가능. "
                    "도메인에 모든 _base 카테고리 명시 권장)"
                )
        return s, warnings

    cats = data.get("categories")
    if isinstance(cats, list):
        # _base 배열 형식
        return sum(c.get("weight", 0) for c in cats), warnings
    if isinstance(cats, dict):
        # 형태 B: ecommerce/healthcare/saas
        return sum(v.get("weight", 0) for v in cats.values() if isinstance(v, dict)), warnings
    return None, warnings


def main() -> int:
    targets = sorted((REPO_ROOT / ".claude/domains").glob("*/health/_category.json"))
    if not targets:
        print("✗ No _category.json files found")
        return 1

    base_path = REPO_ROOT / ".claude/domains/_base/health/_category.json"
    if not base_path.exists():
        print("✗ _base/health/_category.json — required file missing")
        return 1
    base_data = json.loads(base_path.read_text(encoding="utf-8"))

    fail = 0
    for target in targets:
        rel = target.relative_to(REPO_ROOT)
        data = json.loads(target.read_text(encoding="utf-8"))
        # _base 자체 검증에는 base_data 비교 불필요
        total, warnings = category_sum(data, None if target == base_path else base_data)
        for w in warnings:
            print(f"  ⚠ {rel} — {w}")
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
