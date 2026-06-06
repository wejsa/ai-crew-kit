"""v1 backlog → v2 환경 호환성 회귀 보호 (Issue #65).

skill-upgrade는 .claude/state/backlog.json을 보존만 수행한다 (변환 없음).
backlog.schema.json은 v1.45.1과 v2 사이 diff가 없으므로 변환 룰 자체가
불필요. 그러나 step 정의의 `additionalProperties: false` 때문에 v1 시기
실제 사용된 step.description / step.estimatedLines 필드가 거부되던 sleeper
호환성 결함이 있었다.

본 테스트는 v1.45.1 시기 형태의 backlog.json(rich step 포함)을 제너릭
fixture로 박제하여, 향후 backlog.schema.json 변경 시 v1 호환이 무음으로
깨지지 않도록 회귀 보호한다. (v3.0.0에서 도메인 예제 제거에 따라 fixture를
도메인 무관 generic으로 교체.)
"""
from __future__ import annotations

import jsonschema


def test_v1_backlog_passes_current_schema(v1_backlog: dict, backlog_schema: dict) -> None:
    """v1.45.1 시기 실제 backlog.json이 현재 backlog.schema.json을 통과."""
    jsonschema.validate(v1_backlog, backlog_schema)


def test_v1_backlog_preserves_step_description_and_estimated_lines(v1_backlog: dict) -> None:
    """rich step(step.description + step.estimatedLines)을 가진 v1 backlog가
    현재 schema에서 두 필드를 보존하는지 검증. 두 필드가 없는 fixture는 건너뛴다.
    """
    tasks = v1_backlog.get("tasks", {})
    has_rich_step = False
    for task in tasks.values():
        for step in task.get("steps", []):
            if "description" in step or "estimatedLines" in step:
                has_rich_step = True
                if "description" in step:
                    assert isinstance(step["description"], str)
                    assert step["description"], "step.description 값이 빈 문자열"
                if "estimatedLines" in step:
                    assert isinstance(step["estimatedLines"], int)
                    assert step["estimatedLines"] >= 1, "step.estimatedLines >= 1 위반"
    # 제너릭 fixture(v1-general-backlog)는 rich step(description+estimatedLines)을
    # 반드시 보유해야 회귀 보호가 유효하다. fixture가 step을 잃으면 실패.
    assert has_rich_step, "v1 backlog fixture에 rich step(description+estimatedLines)이 없음 — 회귀 보호 무력화"
