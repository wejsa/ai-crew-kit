# ADR-011: Claude Code 신기능 채택 평가 (2026-06 사이클)

> 상태: 채택 (Accepted) — v4.8.0 예정분
> 작성일: 2026-06-13
> 결정자: 프레임워크 운영자

---

## 1. 맥락

2026-06 프레임워크 재분석(§4)에서 Claude Code 신기능 채택 후보가 도출됐다. 후보 전수를 **공식 문서(code.claude.com/docs — subagents·skills·plugins-reference·commands)로 실재·의미론 검증** 후, "기존 구조 무변경 + 실질 가치 + 낮은 리스크" 기준으로 선별했다. 본 ADR은 채택분과 함께 **보류분의 근거를 박제**해 다음 평가 사이클에서 재논의 비용을 줄인다.

## 2. 채택

### 2.1 자문 에이전트 3종 `maxTurns: 15` (agent-qa · docs-impact-analyzer · agent-db-designer)

- 셋 다 **읽기 전용**(Read/Glob/Grep)·**비차단 자문**(aick-impl Step 10 / aick-plan 3.0 백그라운드 디스패치) — 출력이 늦거나 잘려도 메인 플로우는 fallback으로 진행.
- 기존 보호는 prose timeout(60초)뿐 — LLM이 지시를 어기면 무한 탐색으로 토큰 폭주 가능. `maxTurns`는 하네스 레벨의 **결정적 백스톱**.
- 15턴 근거: 분석 작업 = diff/spec 읽기 수 회 + 요약 1회. 통상 10턴 미만, 15는 여유분.

### 2.2 파괴적 플로우 스킬 `disallowed-tools` (aick-rollback · aick-hotfix)

`allowed-tools`는 **자동 승인 목록**일 뿐 가용 도구를 제한하지 않는다(공식 의미론). `disallowed-tools`가 실제 제거를 수행 — 파괴적 플로우(main 직접 변경·revert)에서 플로우 밖 도구를 차단:

| 스킬 | 차단 | 근거 |
|------|------|------|
| aick-rollback | `Task, WebFetch, WebSearch, NotebookEdit` | 롤백 플로우는 메인 세션 단독(서브에이전트 디스패치 없음). 웹 섭취는 인젝션 표면 |
| aick-hotfix | `WebFetch, WebSearch, NotebookEdit` | **`Task`는 유지** — Step 7 보안 리뷰가 pr-reviewer-security를 Task로 디스패치 |

## 3. 보류 (근거 박제 — 재평가 트리거 명시)

| 기능 | 보류 근거 | 재평가 트리거 |
|------|----------|--------------|
| subagent `background: true` | 호출 측(aick-impl·plan의 `run_in_background: true`)이 이미 SSOT — frontmatter 이중 명세는 드리프트 표면만 추가 | 호출 경로가 3곳 이상으로 늘면 frontmatter로 이전 |
| pr-reviewer 3종 `maxTurns` | 하드 캡이 대형 PR의 정당한 심층 리뷰를 **조용히 절단**할 수 있음 — 잘린 출력은 review-pr 실패 처리(2개+ 실패 중단)에 안 잡혀 게이트 측 false-negative 위험 | 캡 도달을 실패로 감지하는 신호가 생기면 |
| subagent `memory` (리뷰 패턴 학습) | kit의 학습은 **검사·전파 가능한 상태 파일**(lessons-learned.json — 현재 aick-retro가 쓰고 aick-plan이 설계에 반영)로 일원화하는 설계 — 에이전트별 사일로 메모리는 검사 불가·시드 전파 불가·두 기억 체계 드리프트를 만들어 원칙과 충돌 | 리뷰 관점 학습 수요가 실측으로 확인되면 — 그때도 lessons-learned 확장이 1순위, agent memory는 차선 |
| 신규 훅 이벤트 (UserPromptSubmit·PreCompact·SubagentStop 등 27종 중 미사용분) | 훅 1개 추가 = 스크립트+plugin.json+settings 전파(aick-upgrade hooks 표)+테스트+HI-04 — 현 4훅이 강제하는 불변식 대비 추가 가치 미달. PreCompact continuation-plan 백업은 Stop 디바운스가 실질 커버 | 결정적으로 강제해야 할 새 불변식이 생기면 (게이트 클래스) |
| skill `paths` / `when_to_use` / `arguments` / `context: fork` | 워크플로우 스킬은 경로 스코프 아님. WHEN 트리거는 v1.18.1부터 description에 내장. fork는 상태 파일 쓰기 스킬과 충돌 위험 | 경로 스코프형 커스텀 스킬 수요 발생 시 |
| skill/agent `effort` | 모델 라우팅과 별개 레버 — 실측 없이 핀하면 비용·품질 영향 불투명 | `/usage` 실측 데이터 확보 후 |
| plugin `defaultEnabled` / `dependencies` / LSP / monitors / themes | 해당 없음 (단일 플러그인·의존성 없음·런타임 없음) | 플러그인 분할 시 |

## 4. 영향

- 시드 전파: skills/·agents/는 업그레이드 대상 — `aick-upgrade`/`plugin update`로 자동 전파.
- `agents/` 루트 미러 동기화(sync-plugin-agents.sh) + CI `validate-plugin.yml` 검증 대상.
- 미지 frontmatter 필드는 Claude Code가 무시하므로 구버전 호환(필드 추가는 non-breaking) — kit 자체가 비공식 커스텀 필드 `complexity-hint`를 22개 스킬 전체에 수 버전째 배포해 온 실증이 근거. 단, `maxTurns`/`disallowed-tools`의 **강제력**은 해당 필드를 지원하는 Claude Code 버전에서만 발휘(미지원 버전에선 조용히 무시 = 기존과 동일 동작, 보호만 없음).
