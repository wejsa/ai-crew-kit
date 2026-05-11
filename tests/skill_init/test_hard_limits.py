"""Hard limits enforcement for Step 9 backlog decomposition.

Issue #62 — SKILL.md Step 9 L395~410 cross-field 강제 룰 영속화.

본 모듈은 SKILL.md L395~410 Hard limits 자연어 사양을 알고리즘으로 구현하고
회귀 fixture로 검증한다. 검증 대상:
- phase ∈ {1,2,3,4} 외 값 drop
- phase당 task ≤ 10 절단 (critical 후순위 보존)
- 전체 task ≤ 30 절단 (critical 후순위 보존)
- description ≤ 200자 truncate
- critical만으로 cap 초과 시에도 cap 적용 (5차 scope down 후 CRITICAL-A2 해결 검증)
"""
from __future__ import annotations

import pytest

from .conftest import (
    MAX_DESCRIPTION_LEN,
    MAX_TASKS_PER_PHASE,
    MAX_TOTAL_TASKS,
    enforce_hard_limits,
)


def _make_task(idx: int, phase: int = 1, priority: str = "high", description: str = "x") -> dict:
    return {
        "id": f"TASK-{idx:03d}",
        "title": f"task {idx}",
        "description": description,
        "status": "todo",
        "type": "feature",
        "priority": priority,
        "phase": phase,
        "dependencies": [],
        "createdAt": "2026-05-11T00:00:00+00:00",
    }


# ── phase ∈ {1,2,3,4} 외 값 drop ───────────────────────────────────────
@pytest.mark.parametrize("invalid_phase", [0, 5, 6, -1, 100])
def test_phase_out_of_range_is_dropped(invalid_phase: int) -> None:
    tasks = [_make_task(1, phase=invalid_phase), _make_task(2, phase=1)]
    result = enforce_hard_limits(tasks)
    assert len(result["tasks"]) == 1
    assert result["tasks"][0]["id"] == "TASK-002"
    assert any("phase out of" in d["reason"] for d in result["dropped"])


def test_all_allowed_phases_pass() -> None:
    tasks = [_make_task(i, phase=p) for i, p in enumerate([1, 2, 3, 4], start=1)]
    result = enforce_hard_limits(tasks)
    assert len(result["tasks"]) == 4
    assert result["dropped"] == []


# ── phase당 ≤ 10 절단 + critical 우선 보존 ──────────────────────────────
def test_phase_cap_truncates_to_ten() -> None:
    tasks = [_make_task(i, phase=1, priority="high") for i in range(1, 16)]  # 15 > 10
    result = enforce_hard_limits(tasks)
    survivors = [t for t in result["tasks"] if t["phase"] == 1]
    assert len(survivors) == MAX_TASKS_PER_PHASE
    assert len(result["dropped"]) == 5


def test_phase_cap_preserves_critical_first() -> None:
    """phase당 cap 초과 시 critical은 후순위로 절단되어야 함.

    구성: high 8개 + critical 5개 = 13개 (phase 1)
    기대: high 8개 모두 유지 + critical 2개만 남고 3개 절단 (총 10개)
    """
    tasks = [_make_task(i, phase=1, priority="high") for i in range(1, 9)]
    tasks += [_make_task(i, phase=1, priority="critical") for i in range(100, 105)]
    result = enforce_hard_limits(tasks)
    survivors = result["tasks"]
    assert len(survivors) == MAX_TASKS_PER_PHASE
    # critical 절단 보고 + critical 일부만 보존
    dropped_critical = [d for d in result["dropped"] if d.get("priority") == "critical"]
    assert len(dropped_critical) == 3, (
        f"critical 후순위 절단 동작 검증. dropped: {result['dropped']}"
    )


def test_phase_cap_critical_only_still_enforced() -> None:
    """critical만으로 cap 초과 시에도 ceiling 적용 (CRITICAL-A2 5차 해결 검증).

    5차 scope down 이전엔 'critical 보호 [Y] cap 무시' 옵션이 있어
    사용자 입력으로 hard limit이 무력화 가능했음. 6차에서 ceiling 제거 후
    Hard limits 자체가 critical 포함 절대 상한이 됨.
    """
    tasks = [_make_task(i, phase=1, priority="critical") for i in range(1, 13)]  # 12 > 10
    result = enforce_hard_limits(tasks)
    survivors = result["tasks"]
    assert len(survivors) == MAX_TASKS_PER_PHASE, (
        "critical 단독 cap 초과 시에도 hard limit 적용 (사용자 우회 불가)"
    )


# ── 전체 ≤ 30 절단 ───────────────────────────────────────────────────
def test_total_cap_enforced_across_phases() -> None:
    """phase 4개 × 10개씩 = 40개 → 30개로 절단."""
    tasks: list[dict] = []
    idx = 1
    for phase in [1, 2, 3, 4]:
        for _ in range(10):
            tasks.append(_make_task(idx, phase=phase, priority="high"))
            idx += 1
    result = enforce_hard_limits(tasks)
    assert len(result["tasks"]) == MAX_TOTAL_TASKS


# ── description ≤ 200자 truncate ─────────────────────────────────────
def test_description_truncated_at_200_chars() -> None:
    long_desc = "가" * 300
    tasks = [_make_task(1, description=long_desc)]
    result = enforce_hard_limits(tasks)
    survivor = result["tasks"][0]
    assert len(survivor["description"]) == MAX_DESCRIPTION_LEN
    assert survivor["description"].endswith("...")


def test_description_under_limit_unchanged() -> None:
    tasks = [_make_task(1, description="짧은 설명")]
    result = enforce_hard_limits(tasks)
    assert result["tasks"][0]["description"] == "짧은 설명"


# ── 절단 보고 형식 — task ID/제목/priority 노출 (SKILL.md L403 정합) ──
def test_dropped_report_includes_task_metadata() -> None:
    tasks = [_make_task(i, phase=1, priority="high") for i in range(1, 12)]  # 11 > 10
    result = enforce_hard_limits(tasks)
    assert result["dropped"], "절단 발생 시 보고 비어있지 않아야"
    dropped = result["dropped"][0]
    for field in ("id", "title", "priority", "reason"):
        assert field in dropped, f"절단 보고에 {field} 누락 (컴플라이언스 가시성)"
