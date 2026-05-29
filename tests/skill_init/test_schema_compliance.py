"""Schema compliance regression for skill-init outputs.

Issue #62 — PR #61 (skill-init 재설계) 자체 정적 검증 13 케이스 영속화.
SKILL.md L590~620 task/phase 객체 사양 + 회귀 차단 케이스.

각 테스트는 한 가지 사양만 검증해 실패 원인이 명확하도록 분리되어 있음.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from .conftest import (
    BACKLOG_FIXTURES,
    REPO_ROOT,
    mutate,
    schema_errors,
)


# ── Test 1: SKILL.md Step 9 task 템플릿 (6 필드 omit) ───────────────
def test_task_template_omits_six_dynamic_fields(base_task: dict, task_schema: dict) -> None:
    """Step 9 task는 skill-impl이 동적 산정할 6 필드를 omit해야 함.

    init이 lockTTL=3600 박으면 skill-impl 동적 산정(≤3→3600, 4~8→7200, ≥9→10800)이
    무력화되어 대형 task 동시성 사고 위험 (CRITICAL-C002).
    """
    forbidden_at_init = {
        "assignee",
        "assignedAt",
        "lockTTL",
        "lockedFiles",
        "steps",
        "workflowState",
        "currentStep",
        "specFile",
    }
    assert forbidden_at_init.isdisjoint(base_task.keys()), (
        f"Step 9 template should omit dynamic fields: "
        f"{forbidden_at_init & set(base_task.keys())}"
    )
    assert schema_errors(base_task, task_schema) == []


# ── Test 2: 빈 백로그 (Step 9 N/C 결과) ────────────────────────────────
def test_empty_backlog_passes_schema(now: str, backlog_schema: dict) -> None:
    empty = {
        "metadata": {
            "lastTaskNumber": 0,
            "version": 1,
            "projectPrefix": "TASK",
            "createdAt": now,
            "updatedAt": now,
        },
        "summary": {"total": 0, "done": 0, "inProgress": 0, "review": 0, "todo": 0},
        "phases": {},
        "tasks": {},
    }
    assert schema_errors(empty, backlog_schema) == []


# ── Test 3: 풀 백로그 (Step 9 Y/A 결과, task.phase ↔ phases 키 매핑 정합) ──
def test_full_backlog_passes_schema(base_task: dict, backlog_schema: dict, now: str) -> None:
    full = {
        "metadata": {
            "lastTaskNumber": 3,
            "version": 1,
            "projectPrefix": "TASK",
            "createdAt": now,
            "updatedAt": now,
        },
        "summary": {"total": 3, "done": 0, "inProgress": 0, "review": 0, "todo": 3},
        "phases": {
            "1": {"name": "기반/인프라", "description": "인증/스키마/공통", "status": "todo"},
            "2": {"name": "핵심 도메인", "description": "보드/카드", "status": "todo"},
        },
        "tasks": {
            "TASK-001": {**base_task},
            "TASK-002": {**base_task, "id": "TASK-002", "title": "DB 스키마"},
            "TASK-003": {**base_task, "id": "TASK-003", "title": "보드 CRUD", "phase": 2},
        },
    }
    assert schema_errors(full, backlog_schema) == []


# ── Test 4: currentStep:0 회귀 차단 (schema minimum:1) ─────────────────
def test_current_step_zero_is_rejected(base_task: dict, task_schema: dict) -> None:
    violating = mutate(base_task, currentStep=0)
    errors = schema_errors(violating, task_schema)
    assert any(path == "currentStep" and v == "minimum" for path, v in errors), (
        f"currentStep:0 must violate minimum constraint, got: {errors}"
    )


# ── Test 5: specFile:null 회귀 차단 (schema type:string, nullable 아님) ──
def test_spec_file_null_is_rejected(base_task: dict, task_schema: dict) -> None:
    violating = mutate(base_task, specFile=None)
    errors = schema_errors(violating, task_schema)
    assert any(path == "specFile" and v == "type" for path, v in errors)


# ── Test 6: project.json (saas + 풀스택 + v2.0 GA 필드 4종) ──────────────
def test_project_json_with_v2_ga_fields(project_schema: dict, now: str) -> None:
    project = {
        "version": "1.0.0",
        "kitVersion": "2.1.0",
        "metadata": {"version": 1, "createdAt": now, "updatedAt": now},
        "hooks": {},
        "tokenHints": {},
        "name": "Tasky",
        "description": "B2B SaaS 칸반 보드",
        "createdAt": now,
        "domain": "saas",
        "techStack": {
            "backend": "spring-boot-kotlin",
            "frontend": "nextjs",
            "database": "postgresql",
            "cache": "redis",
            "messageQueue": "none",
            "infrastructure": "docker-compose",
        },
        "agents": {
            "enabled": ["pm", "backend", "frontend", "code-reviewer", "qa"],
            "disabled": ["planner", "db-designer", "docs"],
        },
        "conventions": {
            "taskPrefix": "TASK",
            "branchStrategy": "git-flow",
            "commitFormat": "conventional",
            "prLineLimit": 500,
            "testCoverage": 80,
            "workflowProfile": "standard",
            "skillProfile": "full",
            "overridePriority": "domain-first",
        },
        "kitSource": "https://github.com/wejsa/ai-crew-kit",
    }
    assert schema_errors(project, project_schema) == []


# ── Test 7: taskPrefix 알고리즘 10 케이스 ──────────────────────────────
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Tasky", "TASKY"),
        ("Shop", "SHOP"),
        ("ShopHub", "SHOPHU"),
        ("ShopHubMall", "SHOPHU"),
        ("학생-앱", "TASK"),
        ("a", "TASK"),
        ("", "TASK"),
        ("123", "TASK"),
        ("App2024-Mall", "APP202"),
        ("---", "TASK"),
    ],
)
def test_task_prefix_algorithm(raw: str, expected: str) -> None:
    from .conftest import PREFIX_PATTERN, derive_prefix

    result = derive_prefix(raw)
    assert result == expected, f"derive_prefix({raw!r}) = {result!r}, expected {expected!r}"
    assert PREFIX_PATTERN.match(result), f"{result!r} fails schema pattern"


# ── Test 8: phase 객체 schema 통과 (name + status required) ─────────────
def test_phase_object_valid(phase_schema: dict) -> None:
    phase = {"name": "기반/인프라", "status": "todo", "description": "..."}
    assert schema_errors(phase, phase_schema) == []


# ── Test 9~12: enum 회귀 차단 ─────────────────────────────────────────
@pytest.mark.parametrize(
    "field,value,expected_path",
    [
        # Test 9 — phase status 'blocked' 차단 (enum: todo/in_progress/done 3종)
        # phase_schema는 별도라 아래에서 phase 케이스만 분리
        ("type", "refactor", "type"),  # Test 10
        ("priority", "urgent", "priority"),  # Test 11
        ("id", "task-001", "id"),  # Test 12
    ],
)
def test_task_enum_pattern_regressions(
    base_task: dict, task_schema: dict, field: str, value: str, expected_path: str
) -> None:
    violating = mutate(base_task, **{field: value})
    errors = schema_errors(violating, task_schema)
    assert any(path == expected_path for path, _ in errors), (
        f"{field}={value!r} should violate; errors: {errors}"
    )


def test_phase_status_blocked_rejected(phase_schema: dict) -> None:
    violating = {"name": "x", "status": "blocked"}
    errors = schema_errors(violating, phase_schema)
    assert any(path == "status" and v == "enum" for path, v in errors)


# ── Test 13: task.phase=5 orphan — schema는 통과(cross-field 검증 없음) ──
def test_phase_orphan_passes_schema_init_must_enforce(
    base_task: dict, backlog_schema: dict, now: str
) -> None:
    """schema는 task.phase ↔ phases 키 cross-field 검증을 하지 않음.

    init 측이 SKILL.md Step 9 매핑 규칙(L447~454)으로 강제해야 함.
    본 케이스는 schema 통과 자체를 회귀 보호 — Hard limits 측 검증은
    test_hard_limits.py가 담당.
    """
    backlog = {
        "metadata": {
            "lastTaskNumber": 1,
            "version": 1,
            "projectPrefix": "TASK",
            "createdAt": now,
            "updatedAt": now,
        },
        "summary": {"total": 1, "done": 0, "inProgress": 0, "review": 0, "todo": 1},
        "phases": {"1": {"name": "기반/인프라", "status": "todo"}},
        "tasks": {"TASK-001": {**base_task, "phase": 5}},  # phases엔 "5" 없음
    }
    assert schema_errors(backlog, backlog_schema) == []


# ── Fixture round-trip: positive/negative 디렉토리 일관성 ────────────────
@pytest.mark.parametrize(
    "fixture_path",
    sorted((BACKLOG_FIXTURES / "positive").glob("*.json")),
    ids=lambda p: p.name,
)
def test_backlog_positive_fixtures_pass(fixture_path: Path, backlog_schema: dict) -> None:
    doc = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert schema_errors(doc, backlog_schema) == [], (
        f"positive/{fixture_path.name} should pass schema"
    )


@pytest.mark.parametrize(
    "fixture_path",
    sorted((BACKLOG_FIXTURES / "negative").glob("*.json")),
    ids=lambda p: p.name,
)
def test_backlog_negative_fixtures_fail(fixture_path: Path, backlog_schema: dict) -> None:
    doc = json.loads(fixture_path.read_text(encoding="utf-8"))
    errors = schema_errors(doc, backlog_schema)
    assert errors, f"negative/{fixture_path.name} should violate schema but passed"


# ── PreToolUse 머지 게이트 신호 A 회귀 박제 (v2.4.1) ────────────────────
# v2.4.0 게이트(pre-tool-use.sh)는 workflowState.lastReviewDecision를 읽고
# step/workflowState.prNumber로 PR을 join한다. 이 필드들이 populated 상태로
# schema를 통과함을 보증해 additionalProperties:false sleeper(v2.1.1/v2.3.0/
# v2.4.0 클래스)를 차단하고, 게이트의 --argjson 숫자 join이 매치하는 정수
# 타입 계약을 박제한다. (기존 positive fixture는 모두 workflowState=null이라
# 이 경로를 검증하지 못했음.)
GATE_FIXTURE = "task-with-workflowstate-and-lock.json"


def test_workflowstate_gate_fields_pass_and_typed(backlog_schema: dict) -> None:
    """게이트가 읽는 populated workflowState/step/lock 필드가 schema 통과 + 올바른 타입."""
    doc = json.loads((BACKLOG_FIXTURES / "positive" / GATE_FIXTURE).read_text("utf-8"))
    assert schema_errors(doc, backlog_schema) == [], "게이트 fixture가 schema를 통과해야 함"

    ws = doc["tasks"]["TASK-001"]["workflowState"]
    # 신호 A의 결정적 트리거 — 존재 + enum 값
    assert ws["lastReviewDecision"] == "REQUEST_CHANGES"
    # 게이트 jq join은 --argjson(숫자)과 비교 → 반드시 정수여야 매치 (P0-②)
    assert isinstance(ws["prNumber"], int) and not isinstance(ws["prNumber"], bool)
    assert isinstance(ws["fixLoopCount"], int)
    # step.prNumber(SSOT — skill-impl Step 8)도 정수
    assert isinstance(doc["tasks"]["TASK-001"]["steps"][0]["prNumber"], int)
    # 가변 잠금 필드(v2.2.0)도 populated 상태로 통과
    assert doc["tasks"]["TASK-001"]["lockedBy"]
    assert doc["tasks"]["TASK-001"]["lockedAt"]


def test_workflowstate_string_prnumber_rejected(backlog_schema: dict) -> None:
    """문자열 prNumber는 schema 거부 — CLAUDE.md.tmpl이 문자열 placeholder를
    쓰면 검증 실패 + 게이트 join 미스(P0-②)가 발생하던 sleeper의 회귀 차단."""
    doc = json.loads((BACKLOG_FIXTURES / "positive" / GATE_FIXTURE).read_text("utf-8"))
    doc["tasks"]["TASK-001"]["workflowState"]["prNumber"] = "42"  # 문자열 = 위반
    errors = schema_errors(doc, backlog_schema)
    # workflowState는 oneOf:[$ref, null]이므로 내부 type 위반이 workflowState 경로의
    # oneOf 실패로 표면화된다(정수|null 계약 위반 = 거부됨).
    assert any(path.endswith("workflowState") and v == "oneOf" for path, v in errors), (
        f"문자열 prNumber는 workflowState oneOf 위반으로 거부되어야 함; errors: {errors}"
    )


# ── 머지 게이트 템플릿 emission 회귀 박제 (v2.4.1 fix-up) ───────────────
# 위 fixture/schema 테스트는 "schema가 올바른 shape를 받아들임"만 검증한다.
# 그러나 원래 sleeper는 schema가 아니라 **LLM이 따르는 템플릿**에 살았다
# (prNumber를 문자열 placeholder로, lastReviewDecision 누락). 따라서 게이트의
# 결정적 신호가 시드되는 두 권위 템플릿을 직접 파싱해 전제조건을 무장한다.
# 이 테스트가 없으면 누군가 템플릿을 string placeholder로 되돌려도 pytest는 green.
WORKFLOWSTATE_TEMPLATE_FILES = [
    REPO_ROOT / ".claude/templates/CLAUDE.md.tmpl",
    REPO_ROOT / ".claude/skills/skill-backlog/SKILL.md",
]


def _extract_workflowstate_block(text: str) -> str:
    """첫 `"workflowState": { ... }` 블록을 중괄호 균형으로 추출."""
    start = text.index('"workflowState"')
    brace = text.index("{", start)
    depth = 0
    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[brace : i + 1]
    raise AssertionError("workflowState 블록의 닫힘 괄호를 찾지 못함")


@pytest.mark.parametrize(
    "tmpl_path", WORKFLOWSTATE_TEMPLATE_FILES, ids=lambda p: p.name
)
def test_workflowstate_template_emits_gate_fields(tmpl_path: Path) -> None:
    """LLM이 시드받는 workflowState 템플릿이 게이트 전제조건을 충족하는지 직접 검증."""
    block = _extract_workflowstate_block(tmpl_path.read_text("utf-8"))
    # 결정적 신호 필드 존재 — 누락 시 게이트 신호 A가 읽을 필드가 없어 silent no-op
    assert '"lastReviewDecision"' in block, (
        f"{tmpl_path.name} workflowState 템플릿에 lastReviewDecision 누락 — "
        f"PreToolUse 머지 게이트 신호 A가 silent no-op됨"
    )
    # prNumber/fixLoopCount는 정수|null — 문자열 값으로 모델링하면 schema 거부 +
    # 게이트의 --argjson 숫자 join 미스(원래 sleeper). `"field": "..."` 형태 금지.
    for field in ("prNumber", "fixLoopCount"):
        assert not re.search(rf'"{field}"\s*:\s*"', block), (
            f"{tmpl_path.name}: {field}가 문자열로 모델링됨 — 정수 또는 null이어야 함"
            f"(따옴표 시 schema 거부 + 게이트 숫자 join 미스)"
        )
