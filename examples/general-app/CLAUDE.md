# general-app

> AI Crew Kit이 생성하는 CLAUDE.md 예시입니다. 실제로는 `/crew-init`이 템플릿에서 자동 생성합니다.

## 프로젝트 개요

| 항목 | 값 |
|------|-----|
| **기술 스택** | Spring Boot (Kotlin) + PostgreSQL + Redis |
| **인프라** | docker-compose |

## 에이전트 팀
- **PM** — 워크플로우 오케스트레이션
- **backend** — 구현
- **code-reviewer** — 리뷰
- **qa** — 테스트 품질

## 워크플로우
plan → impl → review → merge. 자세한 스킬은 GitHub 리포 문서를 참조하세요.

<!-- CUSTOM_SECTION:START -->
<!-- 프로젝트별 커스텀 컨벤션을 이 영역에 추가하세요. crew-upgrade가 이 영역을 보존합니다. -->
<!-- CUSTOM_SECTION:END -->
