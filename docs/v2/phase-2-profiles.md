# Phase 2: Skill Profiles & Selective Loading

> **우선순위**: P0 | **의존성**: Phase 0 | **난이도**: S

## 목표

프로젝트/사용자 상황에 맞는 **스킬 프로파일**을 정의하여 불필요한 스킬 로드를 제거하고 토큰 예산을 절약한다.

## 범위 경계

| 이것만 한다 | 이것은 하지 않는다 |
|------------|-------------------|
| skill-profiles.json 스키마 정의 | 스킬 코드 자체 변경 |
| 기본 프로파일 3종 (developer, full, docs-only) 정의 | ECC의 `--with/--without` CLI 플래그 구현 |
| project.json의 skillProfile 필드 연동 | 런타임 프로파일 전환 (세션 중 변경) |
| CLAUDE.md.tmpl에 활성 스킬 목록 반영 | 에이전트 프로파일 (에이전트는 기존 agents.enabled 사용) |

## TFT 분석 가이드

### Architect 분석 항목
1. **스킬 간 의존성 매핑**: 23개 스킬 중 상호 호출 관계 파악
   - 예: skill-impl → skill-review-pr 호출. skill-impl만 있고 skill-review-pr이 없으면?
   - 프로파일에서 제외된 스킬을 다른 스킬이 호출 시 에러 처리 방식
2. **프로파일 로드 시점**: Claude Code가 SKILL.md를 로드하는 메커니즘 확인
   - 프로파일이 "로드하지 않는다"를 실현할 수 있는지 (SKILL.md 파일 존재 but 무시)

### DX Lead 분석 항목
1. **기본 프로파일 3종의 스킬 배분** 확정
   - `developer`: 일상 개발에 필요한 최소 세트
   - `full`: 전체 23개 스킬
   - `docs-only`: 문서 작업 전용
2. **skill-init에서 프로파일 선택 UX**: 초기화 시 프로파일 질문 추가 여부

### Product Lead 분석 항목
1. **프로파일 정의가 "언급만 하고 사용 안 하는" 형태가 되지 않도록** 실효성 검증
   - 실제 토큰 절감 효과 추정

## 구현 작업 목록

### Task 2-1: skill-profiles.json 생성
- 파일: `.claude/skill-profiles.json` (신규)
- 내용:
  ```json
  {
    "profiles": {
      "developer": {
        "description": "일상 개발 (계획 → 구현 → 리뷰 → 머지)",
        "skills": ["skill-status", "skill-backlog", "skill-plan", "skill-impl",
                   "skill-review-pr", "skill-merge-pr", "skill-hotfix", "skill-retro"]
      },
      "full": {
        "description": "전체 스킬",
        "skills": "*"
      },
      "docs-only": {
        "description": "문서 작업 전용",
        "skills": ["skill-status", "skill-docs", "skill-create"]
      }
    },
    "default": "full"
  }
  ```

### Task 2-2: project.schema.json 필드 활성화
- 파일: `.claude/schemas/project.schema.json`
- 변경: Phase 0에서 예약한 `skillProfile` 필드에 enum 값 추가
  - `["developer", "full", "docs-only", "custom"]`

### Task 2-3: CLAUDE.md.tmpl 스킬 목록 조건부 출력
- 파일: `.claude/templates/CLAUDE.md.tmpl`
- 변경: 주요 스킬 섹션에 프로파일 기반 필터링 주석 추가
  - `{{#if skillProfile == "developer"}}` ... `{{/if}}` 형태의 조건부 렌더링

### Task 2-4: skill-init에 프로파일 선택 단계 추가
- 파일: `.claude/skills/skill-init/SKILL.md`
- 변경: 기존 에이전트 선택 후 프로파일 선택 질문 추가
  - "--quick 모드: 기본값 `full` 자동 적용"

## 수정/생성 파일

| 파일 | 작업 |
|------|------|
| `.claude/skill-profiles.json` | **신규** |
| `.claude/schemas/project.schema.json` | 수정 |
| `.claude/templates/CLAUDE.md.tmpl` | 수정 |
| `.claude/skills/skill-init/SKILL.md` | 수정 |

## 성공 기준

- [ ] `skill-profiles.json` 파일이 3개 프로파일을 정의
- [ ] `project.json`에 `skillProfile: "developer"` 설정 시, CLAUDE.md에 해당 스킬만 노출
- [ ] `skillProfile` 미설정 시 `"full"` 기본값 적용 (하위호환)
- [ ] 프로파일에서 제외된 스킬의 자연어 매핑이 CLAUDE.md에서 미노출

## 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| 스킬 간 의존성으로 프로파일 제외가 무의미 | 중 | 중 | TFT에서 의존성 맵 작성, 최소 세트 검증 |
| Claude Code가 SKILL.md 선택 로드를 지원하지 않을 수 있음 | 중 | 높음 | CLAUDE.md 수준 필터링으로 폴백 |
