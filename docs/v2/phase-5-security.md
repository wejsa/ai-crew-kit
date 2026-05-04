# Phase 5: AgentShield-lite (보안 스캐너)

> **우선순위**: P1 | **의존성**: Phase 0 + Phase 1 | **난이도**: M

## 목표

skill-health-check에 **도메인별 민감정보 탐지(Secrets Scanner)**와 **훅 안전성 검증**을 추가하여 ECC AgentShield의 핵심 기능을 ACK에 내재화한다.

## 범위 경계

| 이것만 한다 | 이것은 하지 않는다 |
|------------|-------------------|
| skill-health-check에 secrets 서브카테고리 추가 | 별도 AgentShield 스킬/CLI 도구 개발 |
| 도메인별 민감정보 패턴 라이브러리 (fintech/healthcare) | AST 기반 분석 (v2.1+ 검토) |
| regex 기반 로거 탐지 확장 (기존 SEC-01 강화) | CI 파이프라인 통합 |
| health-check 가중치 재배분 | MCP 서버 리스크 프로파일링 (복잡도 과다) |
| 기존 SEC-01~04와의 중복 제거 | 외부 도구(Snyk, Dependabot) 연동 |

## TFT 분석 가이드

### Security Lead 분석 항목
1. **도메인별 민감정보 패턴 정의**:
   - fintech: PAN(카드번호 16자리), CVV(3~4자리), 오픈뱅킹 토큰, API 키
   - healthcare: MRN(진료번호), NPI, PHI 18개 식별자 패턴
   - ecommerce: PII(주민번호, 사업자번호)
   - saas: 테넌트 API 키, 관리자 토큰
2. **기존 SEC-01과의 관계**: SEC-01은 `log.*password` 등 12패턴 → 이것을 확장할지 별도 항목으로 분리할지
3. **오탐(false positive) 관리**: 타입 선언, 주석, 변수명에서의 오탐 필터링 전략

### Architect 분석 항목
1. **SEC ID 체계 통합 (H003)**: 기존 SEC-01~04(health-check 내장)와 신규 SEC-05~07 + secrets-patterns.json의 SEC-S01~S03이 **3개 네임스페이스로 분산**됨. 통합 ID 체계 확정 필요:
   - 권장안: `SEC-01~04`(기존 유지) + `SEC-05~07`(신규 health-check 항목) + `SEC-S{nn}`(secrets-patterns.json, 도메인별 동적)
   - SEC-01(민감정보 로깅)과 SEC-S01~S03(하드코딩 탐지)의 **검사 대상 겹침 여부** 확인 → 겹치면 SEC-01을 SEC-S로 흡수하거나 참조 관계 정의
2. **가중치 재배분 설계 + 중간 상태 정의 (H006)**: 현재 4개 카테고리 (doc-sync 35%, state-integrity 25%, security 25%, agent-config 15%)
   - Phase 1에서 hook-safety 추가됨 → Phase 5에서 secrets 추가
   - **중간 상태 정의 필수**: Phase 1 완료 ~ Phase 5 완료 사이에 가중치가 어떻게 전이되는지 명시
   - 권장안: Phase 1 완료 시 `hook-safety: 10%` 추가하고 나머지 4개를 비례 감소. Phase 5에서 최종 재배분.

### DX Lead 분석 항목
1. **FAIL 시 사용자 경험**: secrets 탐지 FAIL의 리포트 형식
   - 파일:라인:패턴을 명확히 표시
   - autoFix 불가 (보안은 수동 수정 필수)

### Domain Lead 분석 항목
1. **도메인별 패턴 파일 위치**: `_base/health/` vs `{domain}/health/` vs 별도 파일
2. **도메인이 없는(general) 프로젝트의 기본 패턴**: 공통 secrets만 검사

## 구현 작업 목록

### Task 5-1: 도메인별 민감정보 패턴 파일 생성
- 파일: `.claude/domains/_base/health/secrets-patterns.json` (신규)
  ```json
  {
    "common": [
      {"id": "SEC-S01", "pattern": "(?i)(api[_-]?key|apikey)\\s*[:=]\\s*['\"][^'\"]{8,}", "severity": "CRITICAL", "description": "API 키 하드코딩"},
      {"id": "SEC-S02", "pattern": "(?i)(secret|private[_-]?key)\\s*[:=]\\s*['\"][^'\"]{8,}", "severity": "CRITICAL", "description": "시크릿 키 하드코딩"},
      {"id": "SEC-S03", "pattern": "(?i)(password|passwd|pwd)\\s*[:=]\\s*['\"][^'\"]{4,}", "severity": "CRITICAL", "description": "비밀번호 하드코딩"}
    ]
  }
  ```
- 파일: `.claude/domains/fintech/health/secrets-patterns.json` (신규)
  - fintech 전용: PAN, CVV, 오픈뱅킹 토큰 패턴
- 파일: `.claude/domains/healthcare/health/secrets-patterns.json` (신규)
  - healthcare 전용: MRN, NPI, PHI 식별자 패턴

### Task 5-2: skill-health-check 확장
- 파일: `.claude/skills/skill-health-check/SKILL.md`
- 변경:
  - SEC-01 강화: 기존 12패턴 → secrets-patterns.json 기반 동적 로드
  - 신규 항목 추가:
    - SEC-05: 하드코딩된 시크릿 탐지 (CRITICAL)
    - SEC-06: 환경변수 파일(.env) 내 민감정보 + .gitignore 확인 (CRITICAL)
    - SEC-07: 도메인별 민감 데이터 로깅 탐지 (CRITICAL, 도메인별 패턴 적용)

### Task 5-3: 가중치 재배분
- 파일: `.claude/domains/_base/health/_category.json`
- 변경: 5+1 카테고리 가중치 재배분
  ```
  doc-sync: 30% (기존 35%)
  state-integrity: 20% (기존 25%)
  security: 25% (유지, 내부 항목 확장)
  agent-config: 10% (기존 15%)
  hook-safety: 15% (Phase 1에서 추가)
  ```
  - security 내부에서 SEC-01~04(기존) + SEC-05~07(신규) 통합

### Task 5-4: 마이그레이션 매핑표
- 파일: `docs/v2/security-migration.md` (신규)
- 내용: v1.x 점수 → v2 점수 변환 가이드 (가중치 변경으로 인한 점수 차이 설명)

## 수정/생성 파일

| 파일 | 작업 |
|------|------|
| `.claude/domains/_base/health/secrets-patterns.json` | **신규** |
| `.claude/domains/fintech/health/secrets-patterns.json` | **신규** |
| `.claude/domains/healthcare/health/secrets-patterns.json` | **신규** |
| `.claude/skills/skill-health-check/SKILL.md` | 수정 |
| `.claude/domains/_base/health/_category.json` | 수정 |
| `docs/v2/security-migration.md` | **신규** |

## 성공 기준

- [ ] fintech 프로젝트에서 PAN 패턴 하드코딩 시 SEC-05 CRITICAL FAIL
- [ ] healthcare 프로젝트에서 PHI 로깅 시 SEC-07 CRITICAL FAIL
- [ ] general 프로젝트에서 common 패턴만 적용 (도메인 전용 패턴 미적용)
- [ ] 기존 SEC-01~04 결과가 동일하게 유지 (회귀 없음)
- [ ] 가중치 변경 후 기존 100점 프로젝트가 급격한 점수 하락 없음 (±5점 이내)

## 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| regex 오탐율 > 10% | 중 | 높음 | 타입 선언/주석 필터링 + 도메인별 예외 패턴 |
| 가중치 변경으로 기존 건강 점수 급변 | 중 | 중 | security-migration.md 매핑표 + 경과 기간 안내 |
| 도메인별 패턴이 과다해져 검사 시간 증가 | 낮 | 낮 | --quick 모드에서 CRITICAL만 실행 |
