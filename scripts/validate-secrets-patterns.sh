#!/usr/bin/env bash
# Validate secrets-patterns.json files: JSON Schema + Python re.compile
# Used by: .github/workflows/secrets-tests.yml
# Phase 5 후속 트랙 A Step 1 — docs/v2/phase-5-tests-plan.md

set -euo pipefail

SCHEMA=".claude/schemas/secrets-patterns.schema.json"

if [[ ! -f "$SCHEMA" ]]; then
  echo "✗ Schema not found: $SCHEMA"
  exit 1
fi

# Auto-discover all secrets-patterns.json under .claude/domains/ (M002 — 새 도메인 추가 시 작성자 부담 0)
mapfile -t TARGETS < <(find .claude/domains -type f -name 'secrets-patterns.json' | sort)
if [[ ${#TARGETS[@]} -eq 0 ]]; then
  echo "✗ No secrets-patterns.json files found under .claude/domains/"
  exit 1
fi

# _base는 항상 존재해야 함 — common.hardcoded + common.runtime SSOT (drift 방지)
if [[ ! -f ".claude/domains/_base/health/secrets-patterns.json" ]]; then
  echo "✗ .claude/domains/_base/health/secrets-patterns.json — required file missing"
  exit 1
fi

fail=0
for target in "${TARGETS[@]}"; do
  if [[ ! -f "$target" ]]; then
    echo "✗ $target — file not found"
    fail=1
    continue
  fi
  python3 - "$SCHEMA" "$target" <<'PY' || fail=1
import json, re, sys
import jsonschema

schema_path, target = sys.argv[1], sys.argv[2]
schema = json.load(open(schema_path))
data = json.load(open(target))

try:
    jsonschema.validate(data, schema)
except jsonschema.ValidationError as e:
    path = "/".join(str(p) for p in e.absolute_path)
    print(f"✗ {target} — schema validation failed at /{path}: {e.message}")
    sys.exit(1)

def check_section(entries, label):
    for p in entries:
        try:
            re.compile(p["pattern"])
        except re.error as e:
            print(f"✗ {target} [{label} {p['id']}] — regex compile failed: {e}")
            sys.exit(1)

# id 중복 검증 (M003 — schema 표현 한계 보강)
all_ids = []
if "common" in data:
    check_section(data["common"].get("hardcoded", []), "common.hardcoded")
    check_section(data["common"].get("runtime", []), "common.runtime")
    all_ids += [p["id"] for p in data["common"].get("hardcoded", [])]
    all_ids += [p["id"] for p in data["common"].get("runtime", [])]
if "domain" in data:
    check_section(data["domain"].get("patterns", []), "domain.patterns")
    all_ids += [p["id"] for p in data["domain"].get("patterns", [])]

dupes = sorted({i for i in all_ids if all_ids.count(i) > 1})
if dupes:
    print(f"✗ {target} — duplicate IDs in same file: {dupes}")
    sys.exit(1)

print(f"✓ {target}")
PY
done

if [[ $fail -ne 0 ]]; then
  echo ""
  echo "secrets-patterns validation FAILED"
  exit 1
fi

echo ""
echo "All ${#TARGETS[@]} secrets-patterns files passed schema + regex compile."
