"""Shared fixtures for aick-init regression tests.

Issue #62 — v2.1.0 PR #61 (aick-init 재설계) 후속 영속화.
PR #61이 사용하던 휘발성 `/tmp/validate_skill_init.py`(13 케이스)를 정착시키고
Hard limits cross-field 강제 / Step 4 sanitization 정규식까지 확장 커버.
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKLOG_FIXTURES = REPO_ROOT / ".claude/schemas/fixtures/backlog"


def _load(rel: str) -> Any:
    return json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def project_schema() -> dict:
    return _load(".claude/schemas/project.schema.json")


@pytest.fixture(scope="session")
def backlog_schema() -> dict:
    return _load(".claude/schemas/backlog.schema.json")


@pytest.fixture(scope="session")
def task_schema(backlog_schema: dict) -> dict:
    return backlog_schema["definitions"]["task"]


@pytest.fixture(scope="session")
def phase_schema(backlog_schema: dict) -> dict:
    """phase 객체 스키마 — additionalProperties 패턴으로 정의됨."""
    return backlog_schema["properties"]["phases"]["additionalProperties"]


@pytest.fixture(scope="session")
def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture
def base_task(now: str) -> dict:
    """SKILL.md Step 9 task 템플릿 (6 필드 omit 정합).

    init 시점에 채우는 필드만 포함:
    - id, title, description, status, type, priority, phase, dependencies, createdAt

    init이 채우지 않는 필드 (aick-plan/impl이 동적 산정):
    - assignee, assignedAt, lockTTL, lockedFiles, steps, workflowState
    - currentStep (minimum:1 — init 시점엔 부재)
    - specFile (type:string — null 불가, init 시점엔 spec 없음)
    """
    return {
        "id": "TASK-001",
        "title": "사용자 인증/JWT 발급",
        "description": "JWT 기반 인증 미들웨어 + 회원가입/로그인 API",
        "status": "todo",
        "type": "feature",
        "priority": "high",
        "phase": 1,
        "dependencies": [],
        "createdAt": now,
    }


def schema_errors(doc: dict, schema_obj: dict) -> list[tuple[str, str]]:
    """jsonschema 위반 결과를 (path, validator_keyword) 튜플 리스트로.

    validator 속성은 jsonschema의 안정적 공개 API.
    메시지 문자열 매칭보다 jsonschema 버전 변경에 면역.
    """
    return [
        (
            "/".join(str(p) for p in err.absolute_path) or "<root>",
            err.validator,
        )
        for err in sorted(
            Draft7Validator(schema_obj).iter_errors(doc),
            key=lambda e: list(e.path),
        )
    ]


def mutate(base: dict, **overrides: Any) -> dict:
    out = deepcopy(base)
    out.update(overrides)
    return out


# ── Step 4 taskPrefix 알고리즘 (SKILL.md L248~262 영속화) ──
# 한 곳에 알고리즘을 캡슐화 — SKILL.md 변경 시 본 함수와 동기 갱신 필수.

PREFIX_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]*$")


def derive_prefix(name: str) -> str:
    """SKILL.md Step 4 taskPrefix 알고리즘 영속 구현.

    1. 알파벳/숫자만 추출 (한글/공백/특수문자 제거)
    2. 첫 글자가 비-알파벳이면 strip (숫자로 시작 케이스)
    3. 대문자 변환
    4. 길이 분기: 4-6자 그대로 / 3↓ TASK / 7+ 첫 6자
    5. schema pattern 위반 시 TASK 폴백
    """
    extracted = re.sub(r"[^A-Za-z0-9]", "", name)
    extracted = re.sub(r"^[^A-Za-z]+", "", extracted)
    extracted = extracted.upper()

    if len(extracted) >= 7:
        result = extracted[:6]
    elif len(extracted) >= 4:
        result = extracted
    else:
        return "TASK"

    return result if PREFIX_PATTERN.match(result) else "TASK"


# ── Step 4 프로젝트명 sanitization (SKILL.md L236~243 영속화) ──

# 화이트리스트: [A-Za-z0-9가-힣\s_-]
NAME_PATTERN = re.compile(r"^[A-Za-z0-9가-힣][A-Za-z0-9가-힣\s_-]{0,49}$")

# 셸 메타문자: $ ` ; & | > < \ \n (sanitization 차단 대상)
SHELL_META = re.compile(r"[$`;&|><\\\n]")

# 비가시 문자 (zero-width chars + ZWJ)
ZERO_WIDTH = re.compile(r"[​-‍﻿]")


def sanitize_project_name(raw: str) -> str | None:
    """SKILL.md Step 4 sanitization 강제 룰 구현.

    반환:
        - 통과: sanitize된 이름 (whitespace 정규화, ZW strip)
        - 거부: None (폴백 단계로 이동 신호)

    검사 순서:
    1. 비가시 문자 strip
    2. 셸 메타 포함 시 즉시 거부
    3. 화이트리스트 외 문자 strip
    4. 길이 50자 truncate
    5. 정규식 매칭 검증
    """
    if raw is None:
        return None

    s = ZERO_WIDTH.sub("", raw).strip()
    if not s:
        return None
    if SHELL_META.search(s):
        return None

    # 화이트리스트 외 문자 strip
    s = re.sub(r"[^A-Za-z0-9가-힣\s_-]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return None

    if len(s) > 50:
        s = s[:50].rstrip()

    return s if NAME_PATTERN.match(s) else None


# ── Step 9 Hard limits cross-field 강제 (SKILL.md L395~410 영속화) ──

ALLOWED_PHASES = {1, 2, 3, 4}
MAX_TASKS_PER_PHASE = 10
MAX_TOTAL_TASKS = 30
MAX_DESCRIPTION_LEN = 200


def enforce_hard_limits(tasks: list[dict]) -> dict:
    """Step 9 LLM 분해 결과에 Hard limits 적용 후 결과 + 절단 리포트 반환.

    절단 우선순위 (D-N4 critical 보호):
    - critical task는 일반 priority보다 후순위로 절단
    - 단 cap 자체는 critical 포함 절대 상한 (5차 scope down 후 CRITICAL-A2 해결)
    """
    result: list[dict] = []
    dropped: list[dict] = []

    # 1. phase 외 값 drop
    for t in tasks:
        if t.get("phase") not in ALLOWED_PHASES:
            dropped.append({**t, "reason": "phase out of {1,2,3,4}"})
        else:
            result.append(t)

    # 2. description truncate
    for t in result:
        desc = t.get("description", "")
        if len(desc) > MAX_DESCRIPTION_LEN:
            t["description"] = desc[: MAX_DESCRIPTION_LEN - 3] + "..."

    # 3. phase당 ≤10 절단 (priority 후순위 분리: critical 후순위 절단)
    by_phase: dict[int, list[dict]] = {}
    for t in result:
        by_phase.setdefault(t["phase"], []).append(t)
    surviving = []
    for phase_no, phase_tasks in by_phase.items():
        if len(phase_tasks) <= MAX_TASKS_PER_PHASE:
            surviving.extend(phase_tasks)
            continue
        # 분리: critical vs 나머지
        non_critical = [t for t in phase_tasks if t.get("priority") != "critical"]
        critical = [t for t in phase_tasks if t.get("priority") == "critical"]
        kept: list[dict] = []
        kept.extend(non_critical[:MAX_TASKS_PER_PHASE])
        # critical은 남은 슬롯에 보충 (critical 우선 보존)
        remaining_slots = MAX_TASKS_PER_PHASE - len(kept)
        kept.extend(critical[:remaining_slots])
        # critical만으로 슬롯 초과 시: critical 우선 채움
        if not non_critical and len(critical) > MAX_TASKS_PER_PHASE:
            kept = critical[:MAX_TASKS_PER_PHASE]
        # 절단된 task 기록
        kept_ids = {t["id"] for t in kept}
        for t in phase_tasks:
            if t["id"] not in kept_ids:
                dropped.append({**t, "reason": f"phase {phase_no} cap (max {MAX_TASKS_PER_PHASE})"})
        surviving.extend(kept)

    # 4. 전체 ≤30 절단 (동일 critical 후순위 룰)
    if len(surviving) > MAX_TOTAL_TASKS:
        non_critical = [t for t in surviving if t.get("priority") != "critical"]
        critical = [t for t in surviving if t.get("priority") == "critical"]
        kept = non_critical[:MAX_TOTAL_TASKS]
        remaining = MAX_TOTAL_TASKS - len(kept)
        kept.extend(critical[:remaining])
        if not non_critical and len(critical) > MAX_TOTAL_TASKS:
            kept = critical[:MAX_TOTAL_TASKS]
        kept_ids = {t["id"] for t in kept}
        for t in surviving:
            if t["id"] not in kept_ids:
                dropped.append({**t, "reason": f"total cap (max {MAX_TOTAL_TASKS})"})
        surviving = kept

    return {"tasks": surviving, "dropped": dropped}
