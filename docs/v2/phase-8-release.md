# Phase 8: Migration & Release

> **우선순위**: P2 | **의존성**: Phase 0~7 전체 | **난이도**: L

## 목표

v1.x → v2.0.0 **마이그레이션 경로**를 확보하고, 정식 릴리즈를 완료한다.

## 범위 경계

| 이것만 한다 | 이것은 하지 않는다 |
|------------|-------------------|
| skill-upgrade v2 마이그레이션 로직 | v1.x 코드 변경 (별도 핫픽스로) |
| 마이그레이션 가이드 문서 작성 | 자동 마이그레이션 롤백 테스트 자동화 |
| examples/ 프로젝트 v2 마이그레이션 검증 | 새로운 예제 프로젝트 추가 |
| CHANGELOG v2.0.0 확정 | v2.1.0 계획 수립 |
| README.md 정식 버전 업데이트 | 마케팅 문서 |
| v2.0.0 태그 + main 머지 | GitHub Release 노트 (수동) |

## TFT 분석 가이드

### Architect 분석 항목
1. **skill-upgrade v2 마이그레이션 시퀀스**:
   - v1.x project.json → v2 project.json 변환 로직
   - 새 필드(`hooks`, `skillProfile`, `overridePriority`, `tokenHints`) 기본값 주입
   - `kitVersion` 업데이트
   - CLAUDE.md 재생성 (CUSTOM_SECTION 보존)
2. **하위호환 검증 체크리스트**:
   - v1.x skill-upgrade가 v2 소스를 처리할 수 있는지
   - v2 skill이 v1 project.json을 읽을 수 있는지

### DX Lead 분석 항목
1. **마이그레이션 가이드 구조**: 사용자가 10분 안에 v2 전환 가능하도록
   - Step 1: `skill-upgrade --version v2.0.0`
   - Step 2: 변경 사항 확인
   - Step 3: 프로파일 선택 (선택사항)
2. **롤백 경로**: 문제 발생 시 v1.x로 복원하는 절차

### Product Lead 분석 항목
1. **릴리즈 체크리스트**: 모든 Phase의 성공 기준 달성 여부 검증
2. **CHANGELOG 작성**: Breaking Changes 섹션 강조

### Security Lead 분석 항목
1. **보안 패치 백포트 절차**: v2.0.0 릴리즈 후 v1.x에도 보안 패치를 적용하는 프로세스

## 구현 작업 목록

### Task 8-1: skill-upgrade v2 마이그레이션 로직
- 파일: `.claude/skills/skill-upgrade/SKILL.md`
- 변경:
  - v1→v2 마이그레이션 감지 (소스 VERSION ≥ 2.0.0 && 현재 kitVersion < 2.0.0)
  - project.json 변환:
    ```
    1. conventions.skillProfile 기본값 "full" 추가
    2. conventions.overridePriority 기본값 "domain-first" 추가
    3. hooks: {} 빈 객체 추가
    4. tokenHints: {} 빈 객체 추가
    5. kitVersion 업데이트
    ```
  - settings.json 머지: 기존 permissions 보존 + hooks 빈 객체 추가
  - CLAUDE.md 재생성: CUSTOM_SECTION 추출 → v2 tmpl로 재생성 → 복원
  - `.claude/rules/` 디렉토리 복사 (없으면 생성)

### Task 8-2: 마이그레이션 가이드 문서
- 파일: `docs/v2/migration-guide.md` (신규)
- 내용:
  - v1 → v2 변경 사항 요약
  - 자동 마이그레이션 절차 (`skill-upgrade --version v2.0.0`)
  - 수동 확인 사항 (프로파일 선택, 훅 설정)
  - 롤백 절차 (`skill-upgrade --rollback`)
  - FAQ

### Task 8-3: examples/ 마이그레이션 검증
- 대상: `examples/fintech-gateway/`, `examples/ecommerce-shop/`
- 절차:
  1. 각 예제의 project.json을 v2 스키마로 변환
  2. skill-health-check 실행 → 신규 카테고리(hook-safety, secrets) 동작 확인
  3. skill-compliance-report 실행 (fintech만) → 리포트 생성 확인

### Task 8-4: CHANGELOG 확정
- 파일: `CHANGELOG.md`
- 변경: `[2.0.0] - {릴리즈 날짜}` 섹션 완성
  - Added: 훅, 프로파일, 토큰 힌트, rules, secrets 스캐너, compliance report, lessons
  - Changed: 4층 Layered Override, health-check 가중치
  - Breaking Changes: 스키마 확장, CLAUDE.md.tmpl 구조, 가중치 재배분

### Task 8-5: VERSION + README 정식 업데이트
- `VERSION`: `2.0.0`
- `README.md`: 버전 뱃지, 새 기능 소개 섹션

### Task 8-6: docs/upgrade-guide.md 업데이트
- 파일: `docs/upgrade-guide.md`
- 변경: v2.0.0 마이그레이션 섹션 추가 (migration-guide.md 참조 링크)

### Task 8-7: 릴리즈
- `v2-develop` → `develop` 머지
- `develop` → `main` 머지
- `v2.0.0` 태그 생성

## 수정/생성 파일

| 파일 | 작업 |
|------|------|
| `.claude/skills/skill-upgrade/SKILL.md` | 수정 |
| `docs/v2/migration-guide.md` | **신규** |
| `examples/fintech-gateway/.claude/state/project.json` | 수정 |
| `examples/ecommerce-shop/.claude/state/project.json` | 수정 |
| `CHANGELOG.md` | 수정 |
| `VERSION` | 수정 |
| `README.md` | 수정 |
| `docs/upgrade-guide.md` | 수정 |

## 성공 기준

- [ ] `skill-upgrade --version v2.0.0` 실행 시 v1 프로젝트가 v2로 정상 변환
- [ ] 변환 후 project.json이 v2 스키마 검증 통과
- [ ] CLAUDE.md CUSTOM_SECTION이 마이그레이션 후 보존됨
- [ ] `skill-upgrade --rollback`으로 v1.x 복원 가능
- [ ] examples/ 2개 프로젝트 모두 v2 마이그레이션 + health-check 통과
- [ ] CHANGELOG에 Breaking Changes 섹션 존재

## 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| v1 프로젝트의 커스텀 설정이 마이그레이션에서 손실 | 중 | 높음 | 백업 자동 생성 (기존 skill-upgrade 로직) |
| v2-develop과 develop 머지 시 충돌 | 중 | 중 | 주기적 머지로 최소화 |
| 릴리즈 후 critical 버그 발견 | 낮 | 높음 | v2.0.1 핫픽스 경로 사전 정의 |
