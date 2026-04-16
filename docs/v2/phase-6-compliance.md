# Phase 6: Compliance Traceability Report

> **우선순위**: P1 | **의존성**: Phase 5 | **난이도**: L

## 목표

규제 요구사항에서 코드 구현까지의 **추적성 리포트**를 자동 생성하는 `skill-compliance-report` 스킬을 신규 개발한다.

## 범위 경계

| 이것만 한다 | 이것은 하지 않는다 |
|------------|-------------------|
| skill-compliance-report 신규 스킬 개발 | 외부 감사 도구 연동 |
| fintech 도메인 우선 구현 (PCI-DSS, 전자금융감독규정) | 전체 5개 도메인 동시 구현 |
| 규제 → 체크리스트 → 코드 위치 → PR 매핑 | PDF 출력 (v2.1+ 검토) |
| JSON 형식 리포트 생성 | 실시간 대시보드 |
| health-check 결과 + PR 리뷰 기록 통합 | 외부 DB 저장 |

## TFT 분석 가이드

### Security Lead 분석 항목
1. **규제-코드 매핑 구조 설계**: 어떤 정보를 어떻게 연결할지
   - 입력: 규제 프레임워크(PCI-DSS 항목), 체크리스트 ID, 코드 경로, PR 번호, 머지 일자
   - 출력: 항목별 준수/미준수 상태 + 증거 링크
2. **기존 체크리스트와의 연결**: `.claude/domains/fintech/checklists/compliance.md`의 각 항목에 ID를 부여해야 하는지

### Domain Lead 분석 항목
1. **fintech 규제 매핑 구조**: PCI-DSS 3.2.1 항목 → ACK 체크리스트 항목 → 코드 증거
2. **healthcare 확장 계획**: fintech 완료 후 healthcare(HIPAA) 적용 순서

### Product Lead 분석 항목
1. **리포트 소비자 정의**: 누가 이 리포트를 읽는가? (개발자? 감사팀? CISO?)
2. **기존 skill-report와의 차이**: skill-report = 프로젝트 메트릭, skill-compliance-report = 규제 준수 증거

### DX Lead 분석 항목
1. **CLI 인터페이스 설계**: `/skill-compliance-report --domain fintech --framework pci-dss`

## 구현 작업 목록

### Task 6-1: 규제-코드 매핑 스키마 정의
- 파일: `.claude/schemas/compliance-mapping.schema.json` (신규)
  ```json
  {
    "framework": "PCI-DSS",
    "version": "3.2.1",
    "requirements": [
      {
        "id": "3.2.1",
        "title": "PAN 암호화 저장",
        "checklistRef": "fintech/checklists/compliance.md#SEC-PAN",
        "codeEvidence": [
          {"path": "src/payment/CardEncryption.kt", "type": "implementation"},
          {"path": "tests/payment/CardEncryptionTest.kt", "type": "test"}
        ],
        "prRefs": [42, 56],
        "status": "COMPLIANT",
        "lastAuditDate": "2026-04-15"
      }
    ]
  }
  ```

### Task 6-2: skill-compliance-report 스킬 개발
- 파일: `.claude/skills/skill-compliance-report/SKILL.md` (신규)
- 옵션:
  ```
  /skill-compliance-report                              # 현재 도메인 전체
  /skill-compliance-report --framework pci-dss          # 특정 프레임워크만
  /skill-compliance-report --format json                # JSON 출력
  ```
- 실행 흐름:
  1. project.json에서 domain 확인
  2. `{domain}/compliance/mapping.json` 로드 (없으면 자동 생성 제안)
  3. health-check 결과(`health-history.json`)에서 보안 항목 상태 추출
  4. 코드 증거 경로 유효성 확인 (파일 존재 여부)
  5. 리포트 생성 → `docs/reports/compliance-{date}.json`

### Task 6-3: fintech 매핑 파일 생성
- 파일: `.claude/domains/fintech/compliance/mapping.json` (신규)
- 내용: PCI-DSS + 전자금융감독규정의 주요 항목 → 체크리스트 매핑

### Task 6-4: CLAUDE.md.tmpl 스킬 목록에 추가
- 파일: `.claude/templates/CLAUDE.md.tmpl`
- 변경: 스킬 목록에 `/skill-compliance-report` 추가

## 수정/생성 파일

| 파일 | 작업 |
|------|------|
| `.claude/skills/skill-compliance-report/SKILL.md` | **신규** |
| `.claude/schemas/compliance-mapping.schema.json` | **신규** |
| `.claude/domains/fintech/compliance/mapping.json` | **신규** |
| `.claude/templates/CLAUDE.md.tmpl` | 수정 |
| `docs/skill-reference.md` | 수정 (스킬 목록에 추가) |

## 성공 기준

- [ ] `/skill-compliance-report` 실행 시 fintech 프로젝트에서 PCI-DSS 매핑 리포트 생성
- [ ] 리포트에 규제 항목 → 체크리스트 → 코드 경로 → PR 번호 체인이 포함
- [ ] 코드 증거 경로가 실제 존재하지 않으면 "EVIDENCE_MISSING" 상태 표시
- [ ] general 도메인에서 실행 시 "컴플라이언스 매핑 없음" 안내 후 정상 종료
- [ ] 리포트 JSON이 compliance-mapping.schema.json 스키마 유효

## 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| 매핑 유지보수 비용 (규제 변경 시) | 높 | 중 | 매핑 파일을 사용자 편집 가능하게 설계 |
| 코드 증거가 리팩토링으로 경로 변경 시 매핑 무효화 | 중 | 중 | skill-health-check에서 매핑 유효성 검사 추가 |
| fintech 외 도메인 확장 지연 | 중 | 낮 | fintech 구조를 템플릿화하여 확장 용이하게 |
