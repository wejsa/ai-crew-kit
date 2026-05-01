# Phase 6: Compliance Traceability Report

> **상태**: ⏸ **v2.1+ 보류** (2026-05-01 결정 — 옵션 D 채택)
> **우선순위**: ~~P1~~ → v2.1+ 재평가
> **의존성**: Phase 5 (충족) | **난이도**: L

## ⏸ 보류 결정 (2026-05-01)

본 Phase는 v2.0.0 GA 범위에서 제외하고 v2.1+에서 재평가한다.

### 보류 사유 (방향성 재점검 결과)

1. **방향성 위배 신호**: phase-6-compliance.md §Task 6-1의 `compliance-mapping.schema.json` 예시에서 `framework`, `id`, `title`(예: "PAN 암호화 저장")처럼 *컴플라이언스 지식*을 mapping.json에 박는 구조는 ACK 미니멀리즘 원칙("Claude가 이미 아는 것은 가르치지 않는다")과 Phase 4 옵션 A 결정과 모순된다. 추적성 메타(`checklistRef`, `codeEvidence`, `prRefs`)만 진짜 신규 가치이며, 지식 부분은 이미 `fintech/checklists/compliance.md` + Phase 5 secrets-patterns + Phase 4 rules 메커니즘이 SSOT로 처리한다.
2. **실수요 미검증**: v1.x 시기 컴플라이언스 리포트 사용자 요구 사례 부재. P1 우선순위 적정성 의심.
3. **위반 탐지 중복**: PR 리뷰 위반 탐지는 Phase 4 rules + Phase 5 SEC-01/05/07 + skill-review-pr이 이미 커버. 추적성 단독 가치만으로 v2.0 GA 포함 명분 약함.
4. **GA 임팩트 우선순위**: 단일 GA 전략에서 Phase 7(Context & Learning) / Phase 8(Migration & Release) 진입이 실제 GA 가치 큼.

### 재진입 조건 (v2.1+ 시점에 다음 중 1건 이상 만족 시 부활)

- 사용자(또는 v2.0 GA 도입 팀)에게서 컴플라이언스 추적성 리포트 요구 발생
- 감사 증빙 자동화에 대한 외부 컴플라이언스 표준 변화 (예: PCI-DSS v4.0 항목 추적 의무화)
- skill-health-check 카테고리 확장 시 `compliance-traceability` 카테고리가 자연스러운 확장 후보로 검토됨

### 부활 시 권장 옵션 (v2.1+ 진입 시 사전 후보)

| 옵션 | 핵심 |
|------|------|
| **옵션 A′ (Lean Mechanism)** | skill-compliance-report 신규 + schema는 추적성 메타만(title/description 등 지식 필드 제거) + mapping 콘텐츠 0개 + `_example` 샘플 1개. Phase 4 옵션 A 패턴 정확 일관 |
| **옵션 E (skill-health-check 통합)** | 신규 스킬 0개. 기존 `compliance.md` 항목에 ID 부여만 + health-check `compliance-traceability` 카테고리 추가로 PR 역추적. 강한 미니멀리즘 |

> 본 결정의 상세 분석(옵션 비교 표 + TFT 5인 분석 + 옵션 B 함정 검출)은 v2-develop 세션 로그(`8b1b628` 이후 2026-05-01 대화)에 보존. 부활 시 본 문서 상단 헤더 제거 + 옵션 A′ 또는 E 전환.

---

## (이하 원본 phase-6 계획 — v2.1+ 재진입 시 참고용 보존)

> **참고**: 아래 본문은 옵션 B(메커니즘 + fintech MVP 매핑)를 가정하고 작성되었다. v2.1+ 재진입 시 옵션 A′/E로 재구성 필요.


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
3. **compliance 데이터 수집 경로 명세 (H004 — 선행 확정 필수)**:
   - **누가**: skill-impl(PR 생성 시), skill-review-pr(리뷰 시), skill-merge-pr(머지 시)
   - **언제**: 각 스킬 실행 완료 시점에 매핑 데이터 자동 수집
   - **어떻게**: 각 스킬이 `compliance/mapping.json`에 증거를 append하는지, 아니면 skill-compliance-report 실행 시 git log/PR 기록을 역추적하는지
   - **권장안**: 역추적 방식 (각 스킬을 수정하지 않고, 리포트 생성 시점에 git log + PR 메타데이터를 분석)
   - **대안**: 실시간 수집 (각 스킬 수정 필요, 정확도 높지만 구현 비용 큼)
   - TFT는 권장안의 정확도가 충분한지 검증할 것

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
