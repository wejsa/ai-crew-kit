#!/usr/bin/env bash
# Validate secrets-patterns.json files: JSON Schema + Python re.compile
# Used by: .github/workflows/secrets-tests.yml
# Phase 5 후속 트랙 A Step 1 — docs/v2/phase-5-tests-plan.md

set -euo pipefail

SCHEMA=".claude/schemas/secrets-patterns.schema.json"
TARGETS=(
  ".claude/domains/_base/health/secrets-patterns.json"
  ".claude/domains/fintech/health/secrets-patterns.json"
  ".claude/domains/healthcare/health/secrets-patterns.json"
  ".claude/domains/ecommerce/health/secrets-patterns.json"
)

if [[ ! -f "$SCHEMA" ]]; then
  echo "✗ Schema not found: $SCHEMA"
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

if "common" in data:
    check_section(data["common"].get("hardcoded", []), "common.hardcoded")
    check_section(data["common"].get("runtime", []), "common.runtime")
if "domain" in data:
    check_section(data["domain"].get("patterns", []), "domain.patterns")

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
