# Phase 0: Foundation (기반 준비)

> **우선순위**: P0 | **의존성**: 없음 | **난이도**: S

## 목표

v2.0.0 개발을 위한 **스키마 확장 기반**과 **버전 체계**를 준비한다.

## 범위 경계

| 이것만 한다 | 이것은 하지 않는다 |
|------------|-------------------|
| VERSION 파일을 2.0.0-alpha.1로 변경 | 실제 기능 구현 (훅, 프로파일 등) |
| project.schema.json에 v2 신규 필드 예약 | 기존 필드 삭제 또는 rename |
| CHANGELOG.md에 [2.0.0] 섹션 시작 | v1.x 변경사항 수정 |
| additionalProperties 전략 결정 | 새 디렉토리/파일 구조 실제 생성 |

## TFT 분석 가이드

이 Phase는 구조적 결정이 핵심이므로 **Architect + Product** 2인 중심으로 분석한다.

### 분석 항목

1. **`additionalProperties: false` 처리 전략** (Architect)
   - 현재: `project.schema.json:282`에 `additionalProperties: false`
   - 문제: 새 필드 추가 시 v1.x skill이 v2 project.json을 거부
   - 선택지:
     - A) `additionalProperties: true`로 전환 (유연, 검증 약화)
     - B) `false` 유지 + v2 전용 스키마 버전 분기
     - C) `false` 유지 + skill-upgrade가 스키마 함께 업데이트
   - 결정 기준: v1→v2 마이그레이션 안전성 vs 스키마 엄격성

2. **v2 project.json 신규 필드 목록 확정** (Product)
   - Phase 1~8에서 필요한 필드를 미리 예약 (구현은 각 Phase에서)
   - 예약 후보: `hooks`, `skillProfile`, `conventions.overridePriority`, `conventions.rulesSource`, `tokenHints`

3. **스키마 버전 관리 방식** (Architect)
   - 현재: `project.schema.json`의 `version` 필드 (예: "2.0.0")
   - v1 project.json과 v2 project.json을 skill-upgrade가 어떻게 구분할지

## 구현 작업 목록

### Task 0-1: VERSION 변경
- 파일: `/VERSION`
- 변경: `1.45.1` → `2.0.0-alpha.1`

### Task 0-2: CHANGELOG 준비
- 파일: `/CHANGELOG.md`
- 변경: `## [Unreleased]` 아래에 `## [2.0.0] - TBD` 섹션 추가
- 하위 구조: `### Added`, `### Changed`, `### Breaking Changes` 서브헤더

### Task 0-3: project.schema.json 확장
- 파일: `.claude/schemas/project.schema.json`
- 변경:
  - `conventions` 객체에 신규 필드 추가 (optional, default 포함):
    - `skillProfile`: `string`, default `"default"`
    - `overridePriority`: `enum ["domain-first", "merge"]`, default `"domain-first"`
  - `hooks` 객체 추가 (Phase 1에서 상세 정의, 여기선 빈 객체 예약)
  - `tokenHints` 객체 추가 (Phase 3에서 상세 정의)
  - `kitVersion` 패턴을 `^\\d+\\.\\d+\\.\\d+(-[a-zA-Z0-9.]+)?$`로 확장 (프리릴리즈 지원)
  - `additionalProperties` 전략 적용 (TFT 분석 결과에 따라)

### Task 0-4: README.md 버전 업데이트
- 파일: `/README.md`
- 변경: 버전 뱃지를 `v2.0.0-alpha.1`로 변경
- 제목: `AI Crew Kit v2.0.0-alpha.1`

### Task 0-5: migrations.json 마이그레이션 등록
- 파일: `.claude/schemas/migrations.json`
- 변경: v2.0.0 마이그레이션 엔트리 추가 (schema version bump)

## 수정/생성 파일

| 파일 | 작업 | 비고 |
|------|------|------|
| `VERSION` | 수정 | 2.0.0-alpha.1 |
| `CHANGELOG.md` | 수정 | v2.0.0 섹션 추가 |
| `README.md` | 수정 | 버전 뱃지 |
| `.claude/schemas/project.schema.json` | 수정 | 신규 필드 예약 |
| `.claude/schemas/migrations.json` | 수정 | 마이그레이션 엔트리 |

## 성공 기준

- [ ] `VERSION` 파일이 `2.0.0-alpha.1`
- [ ] `CHANGELOG.md`에 `[2.0.0]` 섹션 존재
- [ ] `project.schema.json`에 `hooks`, `skillProfile`, `overridePriority`, `tokenHints` 필드가 optional로 선언됨
- [ ] 기존 v1.x project.json 예시가 새 스키마에서 유효성 검증 통과 (하위호환)
- [ ] `kitVersion` 패턴이 `2.0.0-alpha.1` 형식 수용

## 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| additionalProperties 전략 오판 | 중 | 높음 | TFT에서 3가지 선택지 시뮬레이션 |
| 예약 필드가 실제 구현 시 구조 변경 필요 | 낮 | 중 | 필드를 최소한으로 예약, 상세는 각 Phase에서 |
