"""add_gitignore_entry 마이그레이션 실행 검증 (v4.8.0 — closeout B2).

aick-upgrade Step 12-4가 prose로 실행하는 add_gitignore_entry의 **필요조건**을
참조 구현으로 시뮬레이션한다. prose-실행 본체(LLM)는 직접 테스트 불가하므로,
여기서는 (a) migrations.json 데이터 계약 (b) 적용 의미론(append-if-absent)의
멱등성을 회귀 보호한다 — v1.45.1(worktrees)·v4.8.0(review-decisions) 엔트리가
실제 실행 검증 0건이던 갭(2026-06 완결 감사) 해소.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MIGRATIONS_PATH = REPO_ROOT / ".claude" / "schemas" / "migrations.json"


def _gitignore_entries() -> list[dict]:
    with MIGRATIONS_PATH.open(encoding="utf-8") as f:
        migrations = json.load(f)["migrations"]
    return [
        change
        for mig in migrations
        for change in mig.get("changes", [])
        if change.get("type") == "add_gitignore_entry"
    ]


def apply_add_gitignore_entry(gitignore_text: str, entry: str) -> str:
    """참조 구현 — aick-upgrade Step 12-4 의미론: 엔트리가 이미 줄 단위로
    존재하면 무변경, 없으면 말미에 추가."""
    lines = gitignore_text.splitlines()
    if entry in (line.strip() for line in lines):
        return gitignore_text
    if gitignore_text and not gitignore_text.endswith("\n"):
        gitignore_text += "\n"
    return gitignore_text + entry + "\n"


def test_entries_exist():
    """add_gitignore_entry 엔트리가 최소 2건(worktrees, review-decisions)."""
    entries = _gitignore_entries()
    values = [e["entry"] for e in entries]
    assert ".claude/worktrees/" in values
    assert ".claude/state/review-decisions.json*" in values


def test_data_contract():
    """entry 값 계약: 비어있지 않고, 개행·선행 공백 없음 (한 줄 엔트리)."""
    for change in _gitignore_entries():
        entry = change["entry"]
        assert entry, "entry must be non-empty"
        assert "\n" not in entry, f"entry must be single-line: {entry!r}"
        assert entry == entry.strip(), f"entry must have no surrounding whitespace: {entry!r}"
        # 추적 중 파일 경고 안내는 필수 (사용자 가이드 계약)
        assert change.get("trackedWarning"), f"trackedWarning required: {entry}"


def test_apply_to_empty_gitignore():
    """빈 .gitignore에 적용 → 엔트리 존재."""
    for change in _gitignore_entries():
        result = apply_add_gitignore_entry("", change["entry"])
        assert change["entry"] in result.splitlines()


def test_apply_idempotent():
    """재적용 → 중복 0 (멱등). 업그레이드 재실행 시나리오."""
    text = "# user rules\nnode_modules/\n"
    for change in _gitignore_entries():
        once = apply_add_gitignore_entry(text, change["entry"])
        twice = apply_add_gitignore_entry(once, change["entry"])
        assert once == twice, f"not idempotent: {change['entry']}"
        assert once.splitlines().count(change["entry"]) == 1


def test_apply_preserves_existing():
    """기존 사용자 규칙 보존 + 이미 존재하는 엔트리는 무변경."""
    for change in _gitignore_entries():
        existing = f"# mine\n{change['entry']}\nbuild/\n"
        result = apply_add_gitignore_entry(existing, change["entry"])
        assert result == existing


def test_kit_gitignore_has_all_entries():
    """kit 자체 .gitignore가 모든 마이그레이션 엔트리를 이미 포함 (시드↔kit 동기)."""
    kit_gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    kit_lines = {line.strip() for line in kit_gitignore.splitlines()}
    for change in _gitignore_entries():
        assert change["entry"] in kit_lines, (
            f"kit .gitignore missing migration entry: {change['entry']}"
        )
