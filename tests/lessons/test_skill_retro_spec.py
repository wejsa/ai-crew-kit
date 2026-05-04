"""skill-retro §5.3 secrets 필터 UX 레이어 회귀 가드 (Phase 7 Step 2).

PR #44 리뷰 MAJOR #1 대응:
D2 개정으로 secrets 필터의 핵심 동작은 SKILL.md spec(markdown)에 위치한다
(skill 자체가 markdown 기반이라 코드로 단언 불가). 누군가 §5.3에서 핵심
키워드를 지우면 회귀 보호가 무력화되므로 본 테스트가 키워드 존재를 가드한다.

정밀한 동작 검증은 아니지만 *spec 자체가 사라지는* 회귀를 잡는 1차 방어선.
실제 거부/마스킹/강행 동작 검증은 사용자 회고 시 인터랙티브 단계에 위임.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = REPO_ROOT / ".claude/skills/skill-retro/SKILL.md"


@pytest.fixture(scope="session")
def skill_md_text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


# §5.3 secrets 필터 spec — D2 개정 핵심 키워드
SECRETS_FILTER_KEYWORDS = [
    "Secrets 필터",                # 서브섹션 헤더
    "SEC-S01~S05",                  # 패턴 출처 (Step 1 SSOT)
    "AskUserQuestion",              # UX 메커니즘
    "default = 거부",               # 안전 기본값
    "마스킹 후 저장",               # 옵션 2
    "***MASKED-",                   # 마스킹 형식 토큰
    "강행 저장",                    # 옵션 3
    "비대화형",                     # fallback 트리거
    "자동 거부",                    # fallback 동작
    "execution-log",                # 감사 추적
    "lesson 단위",                  # 다중 매칭 옵션 적용 단위 (심화 1-d)
    "CI=true",                      # 비대화형 판별 기준 (심화 1-a)
]


@pytest.mark.parametrize("keyword", SECRETS_FILTER_KEYWORDS)
def test_secrets_filter_keyword_present(keyword, skill_md_text):
    assert keyword in skill_md_text, (
        f"skill-retro/SKILL.md에서 '{keyword}' 부재 — "
        "Phase 7 D2 개정 secrets 필터 spec이 침식됐는지 확인 필요."
    )


# 임계값 SSOT — schema description과 SKILL.md 양쪽에 박힘
THRESHOLD_TOKENS = [
    "appliedCount >= 5",
    "appliedCount >= 3",
    "appliedCount < 3",
]


@pytest.mark.parametrize("token", THRESHOLD_TOKENS)
def test_impact_threshold_present(token, skill_md_text):
    assert token in skill_md_text, f"impact 임계값 '{token}' 부재"


def test_lessons_quantitative_format(skill_md_text):
    """--lessons list/top 출력 정량 표기 회귀 가드."""
    assert "(권장: Y)" in skill_md_text, "정량 표기 형식 '(권장: Y)' 부재"
