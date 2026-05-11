"""Schema compliance regression for skill-init outputs.

Issue #62 — PR #61 (skill-init 재설계) 자체 정적 검증 13 케이스 영속화.
SKILL.md L590~620 task/phase 객체 사양 + 회귀 차단 케이스.

각 테스트는 한 가지 사양만 검증해 실패 원인이 명확하도록 분리되어 있음.
"""
from __future__ import annotations

import json
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
