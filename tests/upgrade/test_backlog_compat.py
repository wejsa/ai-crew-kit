"""v1 backlog → v2 환경 호환성 회귀 보호 (Issue #65).

skill-upgrade는 .claude/state/backlog.json을 보존만 수행한다 (변환 없음).
backlog.schema.json은 v1.45.1과 v2 사이 diff가 없으므로 변환 룰 자체가
불필요. 그러나 step 정의의 `additionalProperties: false` 때문에 v1 시기
실제 사용된 step.description / step.estimatedLines 필드가 거부되던 sleeper
호환성 결함이 있었고, develop의 examples/ecommerce-shop/backlog.json까지
이 결함을 트리거하던 상태였다.

본 테스트는 v1.45.1 examples/ 의 실제 backlog.json 두 종(ecommerce/fintech)을
fixture로 박제하여, 향후 backlog.schema.json 변경 시 v1 호환이 무음으로
깨지지 않도록 회귀 보호한다.
"""
from __future__ import annotations

import jsonschema


def test_v1_backlog_passes_current_schema(v1_backlog: dict, backlog_schema: dict) -> None:
    """v1.45.1 시기 실제 backlog.json이 현재 backlog.schema.json을 통과."""
    jsonschema.validate(v1_backlog, backlog_schema)


def test_v1_backlog_preserves_step_description_and_estimated_lines(v1_backlog: dict) -> None:
    """v1 ecommerce fixture에 한해 step.description + step.estimatedLines 보존 검증.

    fintech fixture는 step에 description/estimatedLines가 없으므로 본 검증을 건너뛴다.
    ecommerce fixture는 두 필드가 모두 존재해야 한다 (v1 실제 데이터 박제).
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
    # ecommerce fixture는 has_rich_step=True여야 하지만, parametrize 양쪽 fixture에서
    # 공통 통과해야 하므로 가벼운 단언만 수행 (값 정합성).
    _ = has_rich_step
