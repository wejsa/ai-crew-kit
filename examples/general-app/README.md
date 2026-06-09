# general-app — 범용 예제 프로젝트

AI Crew Kit(v3.0.0+, 도메인 무관 범용 프레임워크)의 기본 설정 구조를 보여주는 최소 예제입니다.

## 구성

| 파일 | 설명 |
|------|------|
| `.claude/state/project.json` | 프로젝트 설정 (스택·에이전트·컨벤션, 도메인 없음) |
| `.claude/state/backlog.json` | 2개 Task 백로그 예시 |
| `docs/requirements/TASK-001-spec.md` | 요구사항 문서 예시 |
| `CLAUDE.md` | 생성된 CLAUDE.md 예시 |

## 워크플로우

```bash
/aick-plan          # TASK-001 선택 + 스텝별 설계
/aick-impl          # 스텝 구현 + PR
/aick-review-pr 1   # 다관점 리뷰
/aick-merge-pr 1    # 머지
/aick-impl --next   # 다음 스텝
```

## 특징
- 도메인 무관 범용 설정 (`project.json`에 `domain` 없음)
- 기술 스택 기반 빌드/테스트 게이트
- PM·backend·code-reviewer·qa 에이전트 활성화
- plan → impl → review → merge 오케스트레이션
