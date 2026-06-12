# 아카이브 — 미배선 에이전트 5종 (v4.8.0에서 플러그인 표면 제거)

`agent-pm` · `agent-planner` · `agent-backend` · `agent-frontend` · `agent-docs`

v3.0.0 범용 피벗 이후 어떤 스킬도 이 에이전트들을 호출하지 않았다(2026-06 honest-review
실측: 스킬 참조 0건). 구현·기획·문서화는 메인 세션(스킬 체이닝)의 몫이고, 서브에이전트는
품질 분석 전담(pr-reviewer ×3, agent-qa, agent-db-designer, docs-impact-analyzer +
리뷰 가이드 agent-code-reviewer)이라는 실제 구조에 맞춰 v4.8.0에서 플러그인 표면에서
제거했다 — "12 agents" 표기는 실동작 **7종**으로 정정.

- 기존 시드의 `project.json` `agents.enabled`에 남은 구 이름은 schema가 legacy로 계속
  수용하며(검증 통과), `/aick-health-check`(SI-05)가 MINOR로 정리를 안내한다.
- 복원이 필요하면 이 디렉토리의 파일 또는 git 히스토리(`git log --follow`)를 참조.
