#!/usr/bin/env python3
"""Validate cross-references in secrets-patterns.json descriptions.

Phase 5 후속 트랙 A Step 3 — docs/v2/phase-5-tests-plan.md
description 자연어에서 'domains/{domain}/{docs|checklists}/...md' 경로를 추출하여
실제 파일 존재 여부 검증. 도메인 docs drift 시 자동 검출.

Used by: .github/workflows/secrets-tests.yml
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(r"domains/[a-z_]+/(?:docs|checklists)/[a-z_-]+\.md")


def extract_refs(data: dict) -> list[tuple[str, str]]:
    """Return list of (pattern_id, ref_path) tuples found in entry descriptions."""
    refs: list[tuple[str, str]] = []
    sections = []
    if "common" in data:
        sections.extend(data["common"].get("hardcoded", []))
        sections.extend(data["common"].get("runtime", []))
    if "domain" in data:
        sections.extend(data["domain"].get("patterns", []))
    for entry in sections:
        for match in PATTERN.findall(entry.get("description", "")):
            refs.append((entry["id"], match))
    return refs


def main() -> int:
    targets = sorted((REPO_ROOT / ".claude/domains").glob("*/health/secrets-patterns.json"))
    if not targets:
        print("✗ No secrets-patterns.json files found")
        return 1

    fail = 0
    total_refs = 0
    for target in targets:
        rel = target.relative_to(REPO_ROOT)
        data = json.loads(target.read_text(encoding="utf-8"))
        refs = extract_refs(data)
        if not refs:
            print(f"⚠ {rel} — no cross-references found in descriptions")
            continue
        for pid, ref in refs:
            total_refs += 1
            ref_path = REPO_ROOT / ".claude" / ref
            if ref_path.exists():
                print(f"✓ {rel} [{pid}] → {ref}")
            else:
                print(f"✗ {rel} [{pid}] → {ref} (not found at {ref_path.relative_to(REPO_ROOT)})")
                fail += 1

    print(f"\nTotal {total_refs} cross-references checked, {fail} broken.")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
