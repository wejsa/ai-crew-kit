# Phase 4: 4-Layer Override + Constraint Rules

> **우선순위**: P1 | **의존성**: Phase 0 + Phase 2 | **난이도**: M

## 목표

기존 2층 Layered Override를 **4층으로 확장**하고, 도메인x언어 교차 **제약 규칙(Constraint Rules)** MVP 3개를 구현한다.

## 범위 경계

| 이것만 한다 | 이것은 하지 않는다 |
|------------|-------------------|
| 4층 구조: `_base → {domain} → {domain}/{language} → project.json` | 언어 튜토리얼 rules (Python type hints 쓰세요 등) |
| MVP 교차 체크리스트 3개 | 12개 언어 전체 rules |
| domain-first 우선순위 기본값 | lint 도구 자동 연동 |
| project.json에 overridePriority 필드 | rules 자동 강제 (리뷰 참조용만) |
| `.claude/rules/` 디렉토리 스캐폴딩 | ECC rules 복사/이식 |

### 교차 체크리스트 MVP 3개 (TFT 합의)

1. `healthcare/python/phi-logging-guard.md` — PHI 로깅 탐지
2. `fintech/kotlin/bigdecimal-money.md` — Double 금전 계산 금지
3. `saas/typescript/tenant-isolation.md` — 쿼리 tenant_id 누락

## TFT 분석 가이드

### Architect 분석 항목
1. **4층 로드 순서 구현**: 현재 skill-health-check가 `_base → {domain}` 2층으로 health/_category.json을 병합하는 로직(`SKILL.md:34-39`) 확인 → 이것을 4층으로 일반화하는 방법
2. **conventions 디렉토리 구조**: `_base/conventions/` vs `rules/` 공존 방식
   - conventions = 기존 권장사항 (24개 md)
   - rules = 새로운 제약사항 (domain x language 교차)
   - 두 디렉토리의 역할 분리 명확화

### Domain Lead 분석 항목
1. **domain-first 우선순위의 구체적 충돌 시나리오**
   - healthcare가 "모든 로깅 허용"이고 python rules가 "PHI 로깅 금지"면?
   - → domain이 이기므로 PHI 로깅 금지가 적용됨 (domain = 상위 제약)
2. **기존 python-*.md 4개와 새 rules의 관계**: 중복 방지 전략
3. **교차 체크리스트 3개의 상세 내용 설계**: 각각 어떤 패턴을 감지/권고할지

### Security Lead 분석 항목
1. **rules가 보안 검사(Phase 5)와 겹치지 않도록** 경계 설정
   - rules = 도메인 비즈니스 제약 (BigDecimal 필수 등)
   - Phase 5 = 범용 보안 (secrets, injection 등)

### Product Lead 분석 항목
1. **rules 파일이 "Claude가 이미 아는 것을 가르치는" 결과가 되지 않는지** 최종 검증
   - 각 rule의 내용이 "기술 교육"이 아닌 "도메인 제약"인지 확인

## 구현 작업 목록

### Task 4-1: rules 디렉토리 구조 생성
- 디렉토리: `.claude/rules/` (신규)
  ```
  .claude/rules/
  ├── README.md              # rules vs conventions 구분 설명
  ├── healthcare/
  │   └── python/
  │       └── phi-logging-guard.md
  ├── fintech/
  │   └── kotlin/
  │       └── bigdecimal-money.md
  └── saas/
      └── typescript/
          └── tenant-isolation.md
  ```

### Task 4-2: 교차 체크리스트 MVP 3개 작성
- **phi-logging-guard.md**: PHI 18개 식별자 로깅 탐지 패턴, 안전한 로깅 예시
- **bigdecimal-money.md**: Double/Float 금전 계산 감지 패턴, BigDecimal 전환 예시
- **tenant-isolation.md**: SQL 쿼리에서 tenant_id 누락 감지 패턴

### Task 4-3: project.schema.json overridePriority 활성화
- 파일: `.claude/schemas/project.schema.json`
- 변경: Phase 0에서 예약한 `overridePriority` 필드 상세화
  ```json
  "overridePriority": {
    "enum": ["domain-first", "merge"],
    "default": "domain-first",
    "description": "domain-first: 도메인 규칙이 언어 규칙을 덮어씀. merge: 양쪽 모두 적용 (가장 엄격)"
  }
  ```

### Task 4-4: skill-review-pr에 rules 참조 로직 추가
- 파일: `.claude/skills/skill-review-pr/SKILL.md`
- 변경: PR 리뷰 시 `.claude/rules/{domain}/{language}/` 하위 파일을 자동 참조
  - project.json의 domain + techStack.backend에서 language 추출
  - 해당 rules가 없으면 스킵 (기존 동작 유지)

### Task 4-5: docs/concepts.md Layered Override 문서 업데이트
- 파일: `docs/concepts.md`
- 변경: 2층 → 4층 다이어그램 + 충돌 해결 규칙 추가

### Task 4-6: rules/README.md 작성
- 내용: "rules는 도메인 제약이다. 언어 튜토리얼이 아니다" 원칙 명시
- 새 rule 작성 가이드라인 (MUST/MUST NOT 형식, 코드 예시 필수)

## 수정/생성 파일

| 파일 | 작업 |
|------|------|
| `.claude/rules/` (디렉토리) | **신규** |
| `.claude/rules/README.md` | **신규** |
| `.claude/rules/healthcare/python/phi-logging-guard.md` | **신규** |
| `.claude/rules/fintech/kotlin/bigdecimal-money.md` | **신규** |
| `.claude/rules/saas/typescript/tenant-isolation.md` | **신규** |
| `.claude/schemas/project.schema.json` | 수정 |
| `.claude/skills/skill-review-pr/SKILL.md` | 수정 |
| `docs/concepts.md` | 수정 |

## 성공 기준

- [ ] `.claude/rules/` 디렉토리에 3개 교차 체크리스트 존재
- [ ] 각 rule 파일이 "제약(Constraint)" 형식 — 코드 예시(좋음/나쁨) 포함
- [ ] skill-review-pr이 healthcare+python-fastapi 프로젝트에서 phi-logging-guard.md 자동 참조
- [ ] `overridePriority: "domain-first"` 기본값이 적용됨
- [ ] 기존 conventions/ 24개 파일이 변경 없이 유지됨

## 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| rules가 conventions과 중복되어 혼란 | 중 | 중 | rules/README.md에 명확한 경계 정의 |
| 4층 로드 시 성능 저하 (파일 읽기 증가) | 낮 | 낮 | 해당 디렉토리 없으면 스킵 |
| 교차 체크리스트 내용이 "교육적"으로 흐를 수 있음 | 중 | 중 | Product Lead가 최종 검토 |
