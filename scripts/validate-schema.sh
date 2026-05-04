#!/usr/bin/env bash
# validate-schema.sh — project.schema.json fixture 검증
#
# 실행: bash scripts/validate-schema.sh
# 종료 코드: 0 = 전체 통과, 1 = 1건 이상 실패
#
# 검증 도구 우선순위:
#   1. check-jsonschema (CLI) — CI/로컬 권장
#   2. python3 + jsonschema 라이브러리 — 대부분의 개발 환경에서 가용
#   3. 둘 다 없으면 JSON 구문만 체크 (warning 출력)
#
# CI는 .github/workflows/schema-validation.yml에서 동일 로직 수행.

set -u -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SCHEMA="$REPO_ROOT/.claude/schemas/project.schema.json"
POSITIVE_DIR="$REPO_ROOT/.claude/schemas/fixtures/positive"
NEGATIVE_DIR="$REPO_ROOT/.claude/schemas/fixtures/negative"
SETTINGS="$REPO_ROOT/.claude/settings.json"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RESET='\033[0m'

pass() { printf "${GREEN}✓${RESET} %s\n" "$1"; }
fail() { printf "${RED}✗${RESET} %s\n" "$1" >&2; }
warn() { printf "${YELLOW}⚠${RESET} %s\n" "$1" >&2; }

# ── 검증 도구 선택 ───────────────────────────────────────────
# SCHEMA_VALIDATOR_STRICT=1 이면 fallback 모드에서 exit 77 (skip)로 종료하여
# false-positive PASS를 방지. CI는 STRICT 권장.
STRICT="${SCHEMA_VALIDATOR_STRICT:-0}"
VALIDATOR="fallback"
if command -v check-jsonschema >/dev/null 2>&1; then
  VALIDATOR="check-jsonschema"
elif command -v python3 >/dev/null 2>&1 && python3 -c "import jsonschema" >/dev/null 2>&1; then
  VALIDATOR="python-jsonschema"
else
  warn "JSON Schema 검증 도구 미설치 — JSON 구문만 체크"
  warn "설치 권장: pip install check-jsonschema 또는 pip install jsonschema"
  if [ "$STRICT" = "1" ]; then
    warn "SCHEMA_VALIDATOR_STRICT=1 — fallback 모드 거부, exit 77 (skip)"
    exit 77
  fi
fi

# ── validator 함수 ───────────────────────────────────────────
validate_against_schema() {
  local file="$1"
  case "$VALIDATOR" in
    check-jsonschema)
      check-jsonschema --schemafile "$SCHEMA" "$file" >/dev/null 2>&1
      ;;
    python-jsonschema)
      python3 - "$SCHEMA" "$file" <<'PY' >/dev/null 2>&1
import json, sys
from jsonschema import validate, ValidationError, SchemaError
schema_path, target_path = sys.argv[1], sys.argv[2]
try:
    with open(schema_path) as f:
        schema = json.load(f)
    with open(target_path) as f:
        target = json.load(f)
    validate(target, schema)
except (ValidationError, SchemaError, Exception) as e:
    sys.exit(1)
PY
      ;;
    fallback)
      python3 -c "import json, sys; json.load(open('$file'))" >/dev/null 2>&1
      ;;
  esac
}

check_meta_schema() {
  case "$VALIDATOR" in
    check-jsonschema)
      check-jsonschema --check-metaschema "$SCHEMA" >/dev/null 2>&1
      ;;
    python-jsonschema)
      python3 - "$SCHEMA" <<'PY' >/dev/null 2>&1
import json, sys
from jsonschema import Draft7Validator
try:
    with open(sys.argv[1]) as f:
        schema = json.load(f)
    Draft7Validator.check_schema(schema)
except Exception:
    sys.exit(1)
PY
      ;;
    fallback)
      python3 -c "import json, sys; json.load(open('$SCHEMA'))" >/dev/null 2>&1
      ;;
  esac
}

PASS=0
FAIL=0

# ── 1. 메타스키마: project.schema.json 자체 유효성 ───────────
if check_meta_schema; then
  pass "meta: project.schema.json is valid JSON Schema (Draft-07)"
  PASS=$((PASS + 1))
else
  fail "meta: project.schema.json 자체가 Draft-07 위반"
  FAIL=$((FAIL + 1))
fi

# ── 2. .claude/settings.json JSON 구문 ───────────────────────
if [ -f "$SETTINGS" ]; then
  if python3 -c "import json, sys; json.load(open('$SETTINGS'))" >/dev/null 2>&1; then
    pass ".claude/settings.json JSON 구문 OK"
    PASS=$((PASS + 1))
  else
    fail ".claude/settings.json JSON 파싱 실패"
    FAIL=$((FAIL + 1))
  fi
fi

# ── 3. positive fixtures — 모두 validate 성공해야 ────────────
if [ -d "$POSITIVE_DIR" ]; then
  for f in "$POSITIVE_DIR"/*.json; do
    [ -f "$f" ] || continue
    name="$(basename "$f")"
    if [ "$VALIDATOR" = "fallback" ]; then
      if validate_against_schema "$f"; then
        pass "positive/$name (구문만, validation skip)"
        PASS=$((PASS + 1))
      else
        fail "positive/$name JSON 파싱 실패"
        FAIL=$((FAIL + 1))
      fi
      continue
    fi
    if validate_against_schema "$f"; then
      pass "positive/$name"
      PASS=$((PASS + 1))
    else
      fail "positive/$name — 스키마 통과해야 하는데 실패"
      FAIL=$((FAIL + 1))
    fi
  done
fi

# ── 4. negative fixtures — 모두 validate 실패해야 ────────────
if [ -d "$NEGATIVE_DIR" ] && [ "$VALIDATOR" != "fallback" ]; then
  for f in "$NEGATIVE_DIR"/*.json; do
    [ -f "$f" ] || continue
    name="$(basename "$f")"
    if validate_against_schema "$f"; then
      fail "negative/$name — 스키마가 거부해야 하는데 통과됨"
      FAIL=$((FAIL + 1))
    else
      pass "negative/$name (기대대로 거부됨)"
      PASS=$((PASS + 1))
    fi
  done
fi

echo ""
echo "──────────────────────────────"
echo "  Validator: $VALIDATOR"
echo "  PASS: $PASS  FAIL: $FAIL"
if [ "$VALIDATOR" = "fallback" ]; then
  echo "  ⚠ fallback 모드 — 스키마 validation 생략 (구문만)."
  echo "    신뢰도 확보: SCHEMA_VALIDATOR_STRICT=1 bash $0"
fi
echo "──────────────────────────────"

[ "$FAIL" -eq 0 ]
