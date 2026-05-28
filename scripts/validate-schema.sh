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
# review-thresholds-ordering-violation.json은 JSON Schema cross-field 비교 한계로
# schema는 통과하나, 별도 Python ordering 검증으로 거부 처리(아래 5번 블록).
ORDERING_FIXTURE="review-thresholds-ordering-violation.json"
if [ -d "$NEGATIVE_DIR" ] && [ "$VALIDATOR" != "fallback" ]; then
  for f in "$NEGATIVE_DIR"/*.json; do
    [ -f "$f" ] || continue
    name="$(basename "$f")"
    # ordering violation은 schema 우회 → 별도 검증 블록에서 처리, 본 루프 SKIP
    if [ "$name" = "$ORDERING_FIXTURE" ]; then
      continue
    fi
    if validate_against_schema "$f"; then
      fail "negative/$name — 스키마가 거부해야 하는데 통과됨"
      FAIL=$((FAIL + 1))
    else
      pass "negative/$name (기대대로 거부됨)"
      PASS=$((PASS + 1))
    fi
  done
fi

# ── 5. ordering 검증 (review.thresholds critical ≥ major ≥ minor) ────────
# JSON Schema Draft-07이 cross-field 숫자 비교 불가하므로 별도 Python 검증.
# - 모든 positive fixture에서 ordering 위반 시 FAIL
# - ordering-violation negative fixture는 위반이 감지되어야 PASS
if command -v python3 >/dev/null 2>&1 && [ -d "$POSITIVE_DIR" ]; then
  ORDERING_CHECK=$(python3 - <<'PY'
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve()  # never resolves to a real file — use cwd-relative
# Better: rely on positional args
PY
)
  # 단순 inline 검증
  python3 - "$POSITIVE_DIR" "$NEGATIVE_DIR/$ORDERING_FIXTURE" <<'PY'
import json
import sys
from pathlib import Path

positive_dir = Path(sys.argv[1])
ordering_neg = Path(sys.argv[2])
pass_count = 0
fail_count = 0

def check_ordering(data):
    """Returns None if no thresholds, else (critical, major, minor) tuple."""
    t = data.get("review", {}).get("thresholds")
    if not t:
        return None
    c = t.get("critical", 80)
    m = t.get("major", 60)
    n = t.get("minor", 50)
    return (c, m, n) if (c >= m >= n) else False

for p in sorted(positive_dir.glob("*.json")):
    data = json.loads(p.read_text())
    result = check_ordering(data)
    if result is False:
        print(f"FAIL_ORDERING: positive/{p.name} — critical/major/minor 순서 위반")
        fail_count += 1
    else:
        pass_count += 1

# Negative ordering fixture는 위반이어야 함
if ordering_neg.exists():
    data = json.loads(ordering_neg.read_text())
    result = check_ordering(data)
    if result is False:
        print(f"PASS_ORDERING: negative/{ordering_neg.name} (기대대로 ordering 위반 감지)")
        pass_count += 1
    else:
        print(f"FAIL_ORDERING: negative/{ordering_neg.name} — 위반이어야 하나 통과")
        fail_count += 1

sys.exit(0 if fail_count == 0 else 1)
PY
  ORDERING_EXIT=$?
  if [ $ORDERING_EXIT -eq 0 ]; then
    pass "review.thresholds ordering (positive + negative ordering fixture)"
    PASS=$((PASS + 1))
  else
    fail "review.thresholds ordering 검증 실패"
    FAIL=$((FAIL + 1))
  fi
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
