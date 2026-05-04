# Phase 3: Token Optimization Hints

> **우선순위**: P0 | **의존성**: Phase 0 | **난이도**: S

## 목표

스킬별 **모델 권장 사양**과 **토큰 예산 가이드**를 SKILL.md frontmatter에 명시하여 비용 효율을 높인다.

## 범위 경계

| 이것만 한다 | 이것은 하지 않는다 |
|------------|-------------------|
| SKILL.md frontmatter에 `model-hint` 필드 추가 | 모델 자동 전환 로직 구현 |
| 스킬별 권장 모델/thinking 설정 문서화 | Claude Code settings에서 모델 강제 지정 |
| 토큰 최적화 가이드 문서 작성 | 토큰 사용량 추적/대시보드 |
| project.schema.json에 tokenHints 필드 활성화 | 비용 청구 연동 |

## TFT 분석 가이드

### Architect 분석 항목
1. **SKILL.md frontmatter 확장 스펙**: Claude Code가 커스텀 frontmatter 필드를 어떻게 처리하는지
   - `model-hint`가 실제 모델 전환을 트리거하는지, 아니면 안내용인지
2. **23개 스킬의 복잡도 분류**: 어느 스킬이 heavy(opus), medium(sonnet), light(haiku)인지

### Product Lead 분석 항목
1. **비용 절감 추정**: sonnet vs opus 비용 차이 × 스킬 호출 빈도
2. **사용자 혼란 방지**: "이 스킬은 haiku를 권장합니다"가 품질 우려를 만들지 않는지

## 구현 작업 목록

### Task 3-1: SKILL.md frontmatter 확장
- 대상: 23개 SKILL.md 전체
- 추가 필드:
  ```yaml
  model-hint: sonnet          # opus | sonnet | haiku
  thinking-hint: false        # true | false
  max-thinking-tokens: 0      # 0 = 비활성
  context-weight: medium      # heavy | medium | light (토큰 소비 예상)
  ```
- 분류 기준:
  - **heavy** (opus 권장): skill-review-pr, skill-plan, skill-health-check
  - **medium** (sonnet 권장): skill-impl, skill-feature, skill-retro, skill-report
  - **light** (haiku 가능): skill-status, skill-backlog, skill-docs

### Task 3-2: project.schema.json tokenHints 활성화
- 파일: `.claude/schemas/project.schema.json`
- 변경: Phase 0에서 예약한 `tokenHints` 필드에 상세 스키마 추가
  ```json
  "tokenHints": {
    "defaultModel": "sonnet",
    "compactionThreshold": 50,
    "maxMcpServers": 10
  }
  ```

### Task 3-3: 토큰 최적화 가이드 문서
- 파일: `docs/token-optimization.md` (신규)
- 내용:
  - 스킬별 권장 모델 테이블
  - CLAUDE_AUTOCOMPACT_PCT_OVERRIDE 설정 안내
  - MCP 서버 수 제한 권장 (10개 이하)
  - 프로파일별 토큰 예산 비교

## 수정/생성 파일

| 파일 | 작업 |
|------|------|
| `.claude/skills/*/SKILL.md` (23개) | 수정 (frontmatter 4줄 추가) |
| `.claude/schemas/project.schema.json` | 수정 (tokenHints 상세화) |
| `docs/token-optimization.md` | **신규** |

## 성공 기준

- [ ] 23개 SKILL.md에 `model-hint`, `context-weight` 필드 존재
- [ ] heavy/medium/light 분류가 TFT 합의 결과와 일치
- [ ] 토큰 최적화 가이드 문서가 3개 이상의 실용적 설정을 안내
- [ ] project.json에 tokenHints 미설정 시 기본값 적용 (하위호환)

## 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| model-hint가 실제 동작하지 않고 문서용에 그칠 수 있음 | 높 | 낮 | 안내용이라도 가치 있음 (사용자 판단 보조) |
| 스킬 복잡도가 프로젝트마다 달라 일률 분류 어려움 | 중 | 낮 | project.json tokenHints로 오버라이드 허용 |
