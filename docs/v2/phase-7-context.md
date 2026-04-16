# Phase 7: Context & Learning

> **우선순위**: P2 | **의존성**: Phase 1 + Phase 4 | **난이도**: M

## 목표

스킬 간 **컨텍스트 전달 효율**을 높이고, skill-retro의 **학습 반영율**을 개선한다.

## 범위 경계

| 이것만 한다 | 이것은 하지 않는다 |
|------------|-------------------|
| workflowState에 contextSnapshot 필드 병합 | 별도 skill-context.json 파일 생성 |
| skill-retro에 confidence score 산출 추가 | 자동 적용 (opt-in 제안만) |
| lessons-learned.json 도메인별 분리 | Instinct v2 풀버전 (모델 튜닝) |
| skill-plan에서 lessons 자동 참조 | 크로스 도메인 lessons 전이 |
| Skill Creator git 히스토리 분석 옵션 | git log 전체 분석 |

## TFT 분석 가이드

### Architect 분석 항목
1. **contextSnapshot 필드 설계**: workflowState에 어떤 필드를 추가할지
   - 후보: `domain`, `checklistPaths`, `loadedConventions`, `prNumber`, `lockedFiles`
   - TTL: 30분 (넘으면 무효화)
2. **lessons-learned.json 위치**: `.claude/state/lessons-learned.json` vs `.claude/state/{domain}/lessons-learned.json`

### DX Lead 분석 항목
1. **confidence score 산출 로직**: 반복 횟수, 도메인 매칭도, 영향 범위
   - 임계값: high ≥ 0.8, medium ≥ 0.5, low < 0.5
2. **skill-plan에서의 lessons 참조 UX**: "이전 학습: {제목}" 형태로 계획에 자동 삽입
3. **승인 피로 vs 자동화**: 현재 skill-retro는 100% 수동 승인 → high confidence는 opt-in 제안

### Product Lead 분석 항목
1. **"팀 경험 메타데이터 누적"과 "모델 학습"의 경계** 재확인
   - 허용: 반복 패턴 기록, 소요 시간 통계, 빈출 이슈 목록
   - 금지: Claude의 행동 자체를 변경하는 프롬프트 주입
2. **Skill Creator --from-history 범위**: git log 최근 N개 커밋만 분석

### Security Lead 분석 항목
1. **lessons-learned.json에 민감 정보 유입 방지**: 코드 스니펫 저장 시 secrets 필터링

## 구현 작업 목록

### Task 7-1: contextSnapshot 필드 추가
- 파일: `.claude/schemas/project.schema.json` 또는 backlog.schema.json
- 변경: workflowState 내 contextSnapshot 객체 정의
  ```json
  "contextSnapshot": {
    "domain": "fintech",
    "checklistPaths": [".claude/domains/fintech/checklists/"],
    "activeRules": [".claude/rules/fintech/kotlin/bigdecimal-money.md"],
    "prNumber": 42,
    "ttl": 1800,
    "createdAt": "2026-04-16T10:30:00Z"
  }
  ```

### Task 7-2: skill-impl/skill-review-pr 컨텍스트 전달 연동
- 파일: `.claude/skills/skill-impl/SKILL.md`
- 변경: 스킬 완료 시 contextSnapshot 자동 기록
- 파일: `.claude/skills/skill-review-pr/SKILL.md`
- 변경: 사전 조건 단계에서 contextSnapshot 존재 시 바로 사용 (재로드 스킵)

### Task 7-3: lessons-learned.json 스키마 정의
- 파일: `.claude/schemas/lessons-learned.schema.json` (신규)
  ```json
  {
    "domain": "fintech",
    "lessons": [
      {
        "id": "L-001",
        "taskId": "TASK-45",
        "category": "quality",
        "title": "결제 API nullable field 검증 누락",
        "confidence": 0.85,
        "occurrences": 3,
        "lastSeen": "2026-04-16",
        "suggestedAction": "컨벤션에 nullable 검증 체크리스트 추가"
      }
    ]
  }
  ```

### Task 7-4: skill-retro confidence score 추가
- 파일: `.claude/skills/skill-retro/SKILL.md`
- 변경: 회고 결과에 confidence score 산출 로직 추가
  - `confidence = min(1.0, occurrences / 5)` (5회 반복이면 1.0)
  - high confidence 항목: "다음 /skill-plan에서 자동 참조됩니다" 안내
  - 자동 적용은 하지 않음 (TFT 합의: opt-in only)

### Task 7-5: skill-plan lessons 참조
- 파일: `.claude/skills/skill-plan/SKILL.md`
- 변경: 계획 수립 시 lessons-learned.json에서 관련 항목 자동 로드
  - 현재 도메인 + 현재 techStack과 매칭되는 lessons만
  - 계획 파일에 "참고: 이전 학습" 섹션 자동 삽입

### Task 7-6: skill-create --from-history 옵션
- 파일: `.claude/skills/skill-create/SKILL.md`
- 변경: `--from-history` 옵션 추가
  - git log 최근 50개 커밋에서 반복 패턴 추출
  - 추출된 패턴으로 SKILL.md 초안 생성 제안

## 수정/생성 파일

| 파일 | 작업 |
|------|------|
| `.claude/schemas/lessons-learned.schema.json` | **신규** |
| `.claude/skills/skill-retro/SKILL.md` | 수정 |
| `.claude/skills/skill-plan/SKILL.md` | 수정 |
| `.claude/skills/skill-impl/SKILL.md` | 수정 |
| `.claude/skills/skill-review-pr/SKILL.md` | 수정 |
| `.claude/skills/skill-create/SKILL.md` | 수정 |
| `.claude/schemas/project.schema.json` (또는 backlog) | 수정 |

## 성공 기준

- [ ] skill-impl 완료 후 contextSnapshot이 workflowState에 기록됨
- [ ] skill-review-pr이 contextSnapshot 존재 시 사전 조건 중복 검사 스킵
- [ ] skill-retro 실행 시 각 학습 항목에 confidence score 표시
- [ ] skill-plan이 lessons-learned.json의 high confidence 항목을 자동 참조
- [ ] lessons-learned.json에 코드 스니펫이 포함되지 않음 (메타데이터만)
- [ ] contextSnapshot TTL(30분) 초과 시 자동 무효화

## 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| confidence score 부정확 (잘못된 패턴에 높은 점수) | 중 | 중 | 5회 미만은 자동 참조 제외, 수동 curation 안내 |
| lessons가 도메인 변경 시 오염 | 낮 | 중 | 도메인별 파일 분리로 격리 |
| contextSnapshot이 stale 데이터로 오도 | 낮 | 중 | TTL 30분 + 무효화 로직 |
