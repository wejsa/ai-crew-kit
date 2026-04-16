# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - TBD

### Added
- v2.0.0 스키마 확장: `hooks`, `skillProfile`, `overridePriority`, `tokenHints` 필드 예약
- `kitVersion` SemVer 프리릴리즈 패턴 지원 (`2.0.0-alpha.1` 등)
- 스킬 프로파일 시스템 (developer/full/docs-only/custom) — CLAUDE.md 스킬 노출 제어
- `skill-profiles.json` 프로파일 정의 파일
- `project.schema.json`에 `customSkills` 배열 필드 추가 (custom 프로파일용)
- `skill-init`에 스킬 프로파일 선택 단계 (Step 5.6) 추가
- TEMPLATE-ENGINE에 `SKILL_LIST_SECTION`, `NATURAL_LANGUAGE_COMMANDS` 블록 마커 추가

### Changed
- CLAUDE.md.tmpl: 하드코딩 스킬 목록/자연어 매핑을 프로파일 기반 블록 마커로 교체

### Breaking Changes
- `project.schema.json` 스키마 확장 — v1.x skill이 v2 project.json의 신규 필드를 인식하지 못할 수 있음 (skill-upgrade로 해결)

## [1.45.1] - 2026-04-14

### Added
- **Claude Code v2.1.49+ 네이티브 git worktree 지원** — `claude --worktree <name>` (`-w`) 호환
  - `.gitignore`: `.claude/worktrees/` 추적 제외 (상태 파일 경합 방지)
  - `CLAUDE.md.tmpl`: Git 워크트리 프로토콜에 오케스트레이터 비교 테이블 추가
  - `git-workflow.md`: Worktree 모드 섹션을 Claude Code 네이티브 / Claude Squad / 수동 worktree로 일반화
  - README 요구사항: Claude Code v2.1.49+ 권장 명시
  - `skill-upgrade`: `add_gitignore_entry` 마이그레이션 타입 추가 — 기존 프로젝트 업그레이드 시 `.gitignore`에 `.claude/worktrees/` 자동 추가 (이미 추적 중이면 제거 명령 안내)

### Changed
- `project.schema.json`: `orchestrator.type` enum에서 `claude-code-native` 값 제거 — 감지는 git 메타데이터(`git rev-parse --git-dir != --git-common-dir`)로 자동 수행되므로 enum 값이 분기 로직에 사용되지 않는 선언적 no-op였음. 오케스트레이터 종류(네이티브/Squad/수동)는 모두 동일 경로로 처리됨.

### Reverted
- **서브에이전트 worktree 격리 (PR #16)** — 100회 시뮬레이션(5 에이전트 × 20 시나리오) 결과 전면 되돌림.
  - 근거: 대상 6개 agent는 `tools: Read, Glob, Grep`만 사용 → 물리적으로 쓰기 불가이므로 "메인 워크트리 오염 방지"는 존재하지 않는 문제를 해결
  - 보안 이득 주장(exfiltration/injection/silent failure)은 worktree 경계 밖(`/tmp`, `~`, 부모 컨텍스트 반환)에서 발생 → 격리로 해결 불가
  - Task 파라미터 `isolation: "worktree"`의 런타임 실재 미확인, Claude Code v2.1.48 이하 CI에서 호출 실패 가능성
  - 향후 쓰기 가능한 분석 에이전트 도입 시 런타임 계약 검증 후 재설계

> 기존 worktree 분기 로직(`git rev-parse --git-dir != --git-common-dir`)이 네이티브 worktree도 자동 감지하므로 스킬 본문 변경 없이 호환됨.

## [1.45.0] - 2026-04-07

### Added
- **UX 마찰 10건 일괄 해소** — TFT 대규모 분석 기반 개선
  - CLAUDE.md 30초 요약 (Quick Reference) 섹션 추가 — 온보딩 시간 단축
  - 에러 정보 SSOT 통합 — troubleshooting.md 중앙화, workflow-guide는 참조 링크
  - Trivial Fix 경로 (--micro) 문서화 — workflow-guide에 플로우차트 + 기준표
  - 워크플로우 프로필 비교 테이블 — standard vs fast 비교 명시
  - skill-impl `--dry-run` 옵션 — 빌드/테스트만 검증, PR 미생성
  - Eject 가이드 (`docs/eject-guide.md`) — 프레임워크 제거 절차 + 체크리스트
  - 스킬 티어 분류 — 일상(Daily) 6개 / 주간(Weekly) 5개 / 설정(Setup) 8개
  - Task 일시정지 (`paused` 상태) — `--pause`/`--resume` + `pauseReason`/`pausedAt` 필드
  - Lock 자동정리 — skill-plan/impl 진입 시 TTL 만료 Task 자동 해제

### Fixed
- README.md 버전 뱃지 불일치 (v1.43.0 → v1.45.0)

## [1.44.0] - 2026-04-07

### Added
- **서비스 설명 기반 기술 스택 추천** (Issue #14) — skill-init에 Step 2.5 추가
  - 자연어 서비스 설명 입력 → 도메인 + 풀 스택 자동 추천 (키워드 점수제 매칭)
  - 6개 컴포넌트 의사결정 테이블 (Backend, Frontend, Database, Cache, MQ, Infrastructure)
  - 3가지 분기: 수락(A) / 일부 수정(B) / 직접 선택(C) — 경력자 기존 플로우 100% 보존
  - 초심자 질문 횟수 8+회 → 4회로 감소
  - --quick 모드: 디렉토리명 키워드 매칭 추가 (추가 질문 없음)
  - 케이스별 흐름 요약 테이블 문서화 (7개 시나리오)

## [1.43.4] - 2026-04-05

### Added
- **주석 처리된 코드 금지 컨벤션** — 테스트 파일에서 assertion/검증 코드 주석 처리 금지 (빌드 게이트 우회 방지)
  - `testing.md`: 규칙 + 근거 추가
  - `common.md`: 체크리스트 항목 추가 (MAJOR)

## [1.43.3] - 2026-04-05

### Fixed
- **Python 스택 스키마 누락** — `project.schema.json` backend enum에 `python-fastapi`, `python-django` 추가 (기존 5개 → 7개)
- **--quick 모드 스택 강제 지정 제거** — 빈 디렉토리에서 `defaultStack`(Spring Boot) 강제 적용 → 백엔드 프레임워크 직접 선택 폴백으로 변경

## [1.43.2] - 2026-04-05

### Added
- **에러 코드 체계** — ecommerce(29코드), saas(25코드), healthcare(26코드) error-codes.json 신규
- **헬스체크 카테고리** — ecommerce(inventory-consistency), saas(tenant-isolation), healthcare(phi-protection) health/_category.json 신규
- **키워드 충돌 해소** — _registry.json에 keywordPolicy 추가 (결제/정산/구독 3건 충돌 문서화)

### Fixed
- **도메인 시뮬레이션 B등급 이슈 수정** — 상태 머신 엣지 케이스, 컴플라이언스, 크로스도메인 개선
  - **ecommerce**: 셀러 terminated 서브오더 처리 정책, 서브오더 created→cancelled/paid→cancel_requested 전이 추가, 정산 disputed 이체 배치 제외 규칙, 구독 적용 범위 명시, fintech 결제 매핑 참조
  - **fintech**: FDS 심각도 MAJOR→CRITICAL, 제3자 제공 심각도 CRITICAL 통일, 마이데이터 토큰 로깅 금지 항목 추가
  - **saas**: 구독 canceled→active 복구 전이 추가, 인보이스 전이 검증, progressive backoff 용어 수정, 제3자 제공 CRITICAL 통일, 구독 적용 범위 명시
  - **healthcare**: 예약 이중 예약 방지 제약 조건 추가

## [1.43.1] - 2026-04-05

### Fixed
- **도메인 시뮬레이션 A등급 이슈 수정** — 5개 도메인 상태 머신/문서 정합성 45건 해결
  - **fintech**: 정산 상태 전이 테이블 신규 작성, 환불 상태 머신 SSOT 통일(refund-cancel.md), 결제 전이 domain-logic.md↔payment-flow.md 동기화, 마이데이터 retrying→failed 다이어그램 수정, README에 open-banking/mydata 문서 추가
  - **ecommerce**: 주문 상태 머신 11→13개 통일(문서↔템플릿), 주문↔결제 상태 매핑 테이블 추가, 재고 예약 TTL KT 15→30분 통일, TS 가격 계산 BigDecimal 대안 안내, README 참고 문서 5건 추가, domain-logic.md 전이 테이블 동기화
  - **saas**: 인보이스 허용 전이 테이블 추가, 구독↔테넌트 상태 연동 규칙 정의, glossary.md 17개 용어 추가
  - **healthcare**: glossary.md 23개 의료 용어 추가
  - **cross-domain**: 4개 도메인 domain.json에 `_base` 체크리스트(common, security-basic, architecture) 참조 추가

## [1.43.0] - 2026-04-04

### Added
- **Healthcare 신규 도메인** — PHI 보호, 진료기록, 처방, 환자 동의, 보험 청구 전용 도메인
  - `domain.json`: 10 keyword 그룹 (64 트리거), compliance 5개 (HIPAA, 의료법, 개인정보보호법, 생명윤리법, 진료기록보존규정), PostgreSQL 기본 스택
  - docs/ 7개:
    - `phi-data-handling.md`: PHI 18개 식별자, 비식별화(Safe Harbor/Expert Determination), 저장/전송/로깅 규칙, 보존/폐기 기간
    - `access-control.md`: 역할 계층(System Admin→의사→간호사→약사→접수→환자), 접근 제어 매트릭스, 환자-의료진 관계 접근, Break-the-Glass(4시간 자동 만료), HL7 FHIR 리소스 매핑
    - `audit-trail.md`: HIPAA Security Rule 감사, 필수 기록 이벤트 10종, 감사 로그 12 필드, 불변성(append-only), 보존 10년
    - `consent-management.md`: 동의 상태머신(6 states, +denied), 동의 유형 4종, 철회 처리, 응급 예외, 미성년자 동의
    - `prescription-flow.md`: 처방 상태머신(8 states, +expired), DUR 검증 7항목, 용량 검증, 마약류 특별 규정
    - `appointment-flow.md`: 예약 상태머신(6 states), 접수/수납 플로우, No-show 처리
    - `billing-claims.md`: 청구 상태머신(7 states, +rejected/appealed), 급여/비급여, 심사/삭감 대응
  - checklists/ 3개:
    - `security.md`: PHI 암호화, 로깅 금지, 접근 통제, Break-the-Glass, 전송 보안 (12 CRITICAL)
    - `compliance.md`: HIPAA Privacy/Security Rule, 의료법, 개인정보보호법(민감정보 제23조), 생명윤리법, 진료기록 보존 (10 CRITICAL)
    - `domain-logic.md`: 처방/예약/동의 상태 전이, DUR 약물 상호작용, 진료기록 무결성, 환자 식별 (8 CRITICAL)
- `pr-reviewer-domain.md`: healthcare 중점 검토 항목 8개 (PHI 접근, 처방 전이, 동의 검증, 진료기록 무결성, 감사 로그)
- `pr-reviewer-security.md`: healthcare 보안 검토 항목 8개 (PHI 평문 저장, 로그 출력, 비암호화 전송, 동의 없는 제공)
- `project.schema.json`: domain enum에 "healthcare" 추가

## [1.42.0] - 2026-04-04

### Added
- **SaaS 신규 도메인** — 멀티테넌시, 구독 결제, 사용량 과금 등 SaaS 플랫폼 전용 도메인
  - `domain.json`: 8 keyword 그룹 (52 트리거), compliance 4개 (GDPR, 개인정보보호법, SOC2, 정보통신망법), PostgreSQL 기본 스택
  - docs/ 6개:
    - `tenant-isolation.md`: 테넌트 격리 전략(DB/스키마/RLS), 테넌트 상태머신(4 states), RBAC 역할 계층, API 키 관리, 리전 데이터 레지던시
    - `subscription-billing.md`: 구독 상태머신(7 states), 과금 모델 5종(flat/seat/usage/tiered/hybrid), 프로레이션, 인보이스
    - `onboarding-provisioning.md`: 가입/프로비저닝 플로우, 트라이얼 관리, 셀프서비스 설정
    - `data-lifecycle.md`: 데이터 분류, GDPR 삭제권/이동권, 테넌트 오프보딩(90일 보존), 감사 로그 스키마
    - `usage-metering.md`: 사용량 미터링, 쿼터(소프트/하드), 초과 과금, 피처 게이팅
    - `webhook-integration.md`: 테넌트 웹훅 설정, at-least-once 배달, HMAC-SHA256 서명 검증
  - checklists/ 3개:
    - `tenant-security.md`: 테넌트 격리 14 CRITICAL, 크로스테넌트 방지, 세션 격리
    - `compliance.md`: GDPR/PIPA/SOC2/정보통신망법, 감사 로그 필수 필드, 데이터 보존/폐기
    - `domain-logic.md`: 구독 상태 전이, 과금 BigDecimal, 프로레이션, 미터링, 피처 게이팅, Noisy Neighbor 방지

## [1.41.3] - 2026-04-04

### Fixed
- ecommerce 도메인 리뷰 수정 (ERROR 6건, WARN 8건)
  - `marketplace.md`: 셀러 상태머신 다이어그램 수정 (active→terminated, rejected 노드 누락), 서브오더 허용 전이 테이블 추가, 수수료 공식에 PG 수수료 추가
  - `seller-settlement.md`: adjusted 상태 탈출 경로 추가 (adjusted→confirmed), 허용 전이 테이블 추가, 프로모션 분담금 규칙 명확화
  - `subscription-commerce.md`: 상태머신 다이어그램 전면 재작성, paused→canceled(90일 초과) 전이 추가, created→canceled(최초 결제 실패) 전이 추가, 재시도 횟수 명확화 (3회 재시도=총 4회 시도)
  - `domain-logic.md`: adjusted 재확정 체크리스트 항목 CRITICAL 추가, 일시정지 기한 MINOR→MAJOR 상향
  - `compliance.md`: 분쟁 해결 MAJOR→CRITICAL 상향, 판매자 신원 확인 정부 등록부 대조 추가, 통신판매중개업법→전자상거래법(통신판매중개의무) 명칭 수정
  - `domain.json`: compliance 명칭 수정, marketplace에 정산 트리거 추가, subscription에 일시정지/재개/프로레이션/일할계산 트리거 추가
- fintech 도메인 리뷰 수정 (ERROR 5건, WARN 7건)
  - `open-banking.md`: canceled 상태 테이블 정의 추가, 종료 상태 명시, 에러 코드 A0400~A0899 예약 대역 추가, 이체 API(출금/입금) SLA 5초 추가, 수취인→예금주 용어 통일
  - `mydata.md`: 동의 철회 규칙 명확화 (즉시 전송 중단 + 5영업일 이내 삭제)
  - `compliance.md`: 동의 철회 "즉시"→"즉시 전송 중단 + 5영업일 이내 삭제" 수정, 타임아웃 SLA 상세화, 동의 이력 5년 보존 항목 추가
  - `domain-logic.md`: 전송 실패 후 expired→failed 상태 수정 (expired는 동의 유효기간 만료 전용), 재동의 검증 항목 추가
  - `domain.json`: open-banking 트리거에 이체 추가

### Changed
- README.md: 도메인 테이블에 오픈뱅킹/마이데이터/마켓플레이스/구독 커머스 반영, 컴플라이언스 확장 표시

## [1.41.2] - 2026-04-04

### Added
- fintech 도메인 오픈뱅킹/마이데이터 확장
  - `open-banking.md`: 이용기관 등록, 사용자 인증(OAuth 2.0), 토큰 관리, 계좌 조회/이체 플로우, 이체 상태머신(8 states), 에러 코드 대역
  - `mydata.md`: 전송요구 상태머신(8 states), 데이터 수집 범위, 동의 관리, 데이터 보관/폐기 규칙, API 규격
- fintech 체크리스트 확장
  - `compliance.md`: 오픈뱅킹 규정(CRITICAL 4건), 마이데이터 규정(CRITICAL 3건)
  - `domain-logic.md`: 오픈뱅킹 연동(CRITICAL 3건), 마이데이터 연동(CRITICAL 2건)
- fintech `domain.json` keywords 2개 추가 (open-banking, mydata), compliance에 오픈뱅킹규정·신용정보법 추가

## [1.41.1] - 2026-04-04

### Added
- ecommerce 도메인 마켓플레이스 확장
  - `marketplace.md`: 셀러 상태머신(6 states), 멀티셀러 주문 분리, 서브오더 상태머신, 커미션 모델, 셀러 등급 체계
  - `seller-settlement.md`: 정산 상태머신(8 states), 정산 주기(D+N), 정산 계산 구조, 반품/환불 처리, 정산 리포트
  - `subscription-commerce.md`: 구독 상태머신(6 states), 결제 주기, 결제 실패 재시도(3회), 프로레이션 계산
- ecommerce 체크리스트 확장
  - `domain-logic.md`: 마켓플레이스 섹션(CRITICAL 4건), 구독 커머스 섹션(CRITICAL 1건)
  - `compliance.md`: 통신판매중개업자 의무 섹션(CRITICAL 3건)
- ecommerce `domain.json` keywords 2개 추가 (marketplace, subscription), compliance에 통신판매중개업법 추가

## [1.41.0] - 2026-04-04

### Added
- 프레임워크 정체성 명시: "프로세스 관리 프레임워크"로서의 역할 경계 문서화
  - CLAUDE.md.tmpl: `프레임워크 역할 경계` 섹션 — 프레임워크(워크플로우·품질게이트·컨벤션) vs Claude(코드작성·기술판단) 분리 명시
  - README.md: 프레임워크 철학 한 문단 추가
  - docs/concepts.md: `설계 철학: 프레임워크와 AI의 역할 분리` 섹션 — 분리 이유 3가지, 프레임워크가 하지 않는 것 목록
- `security.md` 비-REST 프로토콜 보안 가이드: WebSocket(`wss://`, Origin 검증, 핸드셰이크 인증), SSE, gRPC 보안 요구사항
- `skill-feature` Step 2.5 통신 방식 확인: 실시간 요구사항 감지 시 프로토콜(REST/WebSocket/SSE/gRPC) 선택 유도, spec에 통신방식 항목 반영

### Fixed
- TEMPLATE-ENGINE.md `ext_map` 버그: `backend:"none"` (프론트엔드 전용) 시 `.kt.tmpl` 폴백 → `None` 반환으로 수정
- TEMPLATE-ENGINE.md `ext_map` Python 누락: `python-fastapi`, `python-django` → `.py.tmpl` 매핑 추가

## [1.40.0] - 2026-04-03

### Added
- Python 퍼스트클래스 생태계: FastAPI/Django를 Spring Boot와 동등 수준으로 지원
  - `python-project-structure.md`: FastAPI/Django 프로젝트 구조 컨벤션
  - `python-testing.md`: pytest 중심 테스팅 가이드 (fixture, 피라미드, 커버리지)
  - `python-dependency.md`: pyproject.toml, poetry/pip, Alembic 마이그레이션
  - `python-patterns.md`: Pydantic DI, async, SQLAlchemy, 예외 처리 패턴
- Python 코드 리뷰 규칙: 아키텍처(5건), 보안(3건), 테스트(4건) 항목 추가
- Sub-agent Python 리뷰: pr-reviewer-security/domain/test에 Python 탐지 패턴 및 검증 테이블
- 체크리스트 Python 항목: security-basic(5건), architecture(9건), common(4건) 추가
- `skill-init` Python 초기화: 스택 선택 가이드 + 스캐폴딩 상세 (pyproject.toml, app/ 구조)
- `skill-onboard` Python 자동 감지: FastAPI vs Django 판별 휴리스틱 4단계

### Removed
- `agent-devops` 제거 (ADR-009): 사용률 0%, 스킬 연동 0건, 예제 2/2 비활성
  - 삭제: `.claude/agents/agent-devops.md` (520줄)
  - 참조 제거: CLAUDE-example, concepts.md, 예제 2개
  - 유지: `deployment.md` 컨벤션 (독립 참조 문서)

### Changed
- `agent-backend.md`: Python 빌드/테스트 명령, 패키지 구조, 코딩 가이드 추가
- `project-structure.md`: Python (FastAPI/Django) 구조 추가 + 상세 컨벤션 참조
- `docs/concepts.md`: 지원 기술 스택 섹션 신설 (6개 백엔드 + 5개 프론트엔드)
- `docs/getting-started.md`: Python 프로젝트 시작 가이드 추가

## [1.39.0] - 2026-04-02

### Added
- 스텝별 `prLineLimit` 오버라이드: skill-plan이 스텝 특성에 따라 자동 설정 (50~1000)
  - 폴백 체인: step.prLineLimit > conventions.prLineLimit > 500
  - 프로필별 동적 기준: standard limit×0.6/limit/limit×1.4, fast limit/limit×2
- `skill-upgrade` 신규 기능 안내 (Step 15.5): 업그레이드 시 새 기능을 action별로 안내
  - `migrations.json`에 `features` 배열 추가 (action: none/recommend/required)

### Changed
- `backlog.schema.json`: step 정의에 `prLineLimit` 필드 추가 (optional, minimum 50)
- `skill-plan` §4: 스텝 분리 시 prLineLimit 자동 설정 가이드라인 (마이그레이션→100~200, 서비스→500~800, 테스트→700~1000)
- `skill-impl` §4: 라인 검증 동적화 (고정 테이블 → 폴백 체인 + 비율 기반 산정)
- `CLAUDE.md.tmpl`: 라인 제한 섹션 동적 테이블로 교체 + 자동 조정 안내

## [1.38.1] - 2026-04-01

### Added
- 스택 인식 확장: Python(FastAPI/Django), React Vite, Vue, Vue-Nuxt, Astro, Next.js 분리 (4종→11종)
- `--quick` 빈 디렉토리 폴백: 감지 실패 시 프로젝트 유형 1회 질문 (5개 선택지)
- Step 4 선택지에 `none` 옵션: 백엔드 전용/프론트엔드 전용 프로젝트 지원
- DB 선택지 확장: postgresql, mongodb, sqlite, none
- Maven 빌드 지원: `pom.xml` 감지, `mvn package/test/checkstyle:check` 빌드 테이블
- `skill-impl` allowed-tools: go, golangci-lint, mvn, mvnw, python, pytest, ruff, poetry, pip, npx 추가

### Changed
- 에이전트 팀 구성: "backend 항상 필수" → 스택 기반 자동 결정 (백엔드만/프론트엔드만/풀스택)
- `skill-onboard` 빌드 명령어 감지: Python, Next.js, React Vite, Vue, Nuxt, Astro 전체 추가
- `skill-onboard` 스캔 대상: Python 패키지 매니저(poetry/pipenv/pip) 추가

## [1.38.0] - 2026-04-01

### Added
- `skill-impl --micro "설명"`: 소규모 작업 경량 경로 (plan 생략, 바로 구현→PR)
- Micro 전용 라인 제한: ≤150줄 정상, 150~300줄 경고, >300줄 차단→Standard 전환
- 프론트엔드 컨벤션 4개: `frontend-component.md`, `frontend-testing.md`, `frontend-styling.md`, `frontend-state.md`
- 패키지 매니저 자동 감지: yarn.lock, pnpm-lock.yaml, bun.lockb (우선순위: bun>pnpm>yarn>npm)
- pr-reviewer-domain 프론트엔드 검증: a11y(MAJOR), 컴포넌트 크기, prop drilling, 테스트 존재, 인라인 스타일
- `backlog.schema.json`: task.micro boolean 필드 (Micro Task 식별)
- 자연어 매핑 3개: "OO 고쳐줘", "OO 버그 수정해줘", "간단하게 OO 추가해줘" → --micro
- TEMPLATE-ENGINE.md 컨벤션 트리거 테이블에 프론트엔드 4개 항목 등록

### Changed
- `skill-impl` 빌드 테이블: yarn/pnpm/bun 명령어 + Lock 파일 감지 로직 추가
- `skill-impl` allowed-tools: `Bash(pnpm:*)`, `Bash(bun:*)` 추가
- `skill-onboard` 스캔 대상: 패키지 매니저 Lock 파일 3종 추가
- `skill-report` Throughput: Micro Task 비율 메트릭 추가

## [1.37.0] - 2026-04-01

### Added
- 에러 복구 프로토콜: CLAUDE.md.tmpl에 10가지 에러 유형별 표준 복구 가이드 인라인
- `skill-impl --retry`: 실패한 스텝 재시작 (PR close + 브랜치 정리 + 재실행)
- `skill-impl --skip`: 빌드 실패 스텝 건너뛰기 (step.status="skipped")
- `/skill-backlog dashboard`: Phase별 진행률 + in_progress + blocked + 다음 착수 가능 Task
- `/skill-backlog archive`: Task soft delete (status="archived", list 기본 제외)
- `/skill-backlog batch`: 다중 Task 일괄 변경 (dry-run + 확인 + 원자적 실행)
- `/skill-backlog deps`: 의존성 텍스트 트리 + `--reverse` 영향도 분석
- `task.type` 필드: feature | bug | chore | spike (add 시 AI 추론)
- `docs/getting-started.md` "첫 기능 만들기" 5단계 워크스루
- 자연어 매핑 13개 추가 (--retry, --skip, dashboard, deps, archive, batch 등)

### Changed
- `skill-backlog update` 옵션 확장: --title, --description, --phase, --type, --reason
- `skill-backlog list` 필터 확장: --type, --assignee=me, --stale
- `skill-impl --next/--all`: skipped 스텝 호환 (이전 스텝이 skipped면 다음 진행 허용)
- `backlog.schema.json`: task.status에 "archived", step.status에 "skipped" 추가
- `skill-health-check`: archived Task 건강 검진 제외, archived/skipped/type enum 인식
- `skill-status`: archived 카운트 별도 표시
- `skill-report`: Task type별 분포 + 스킵 비율 메트릭 추가
- 5개 핵심 스킬에 에러 복구 프로토콜 참조 + fallback 추가

## [1.36.0] - 2026-03-31

### Added
- `/skill-review-pr config` 서브커맨드: 리뷰 모드 설정 관리 (조회/변경/초기화)
- 리뷰 모드 2단계: `full` (domain+security+test, 디폴트) / `standard` (domain+security)
- 커스텀 에이전트 조합: `--agents domain,test` 형태로 자유 구성 (domain 필수)
- PR 단위 모드 오버라이드: `--mode standard|full` 옵션
- 리뷰 결과 헤더에 실행/미실행 에이전트 목록 표시

### Changed
- Trivial PR Fast Path 기준 완화: 30줄 → 50줄 (경량 리뷰 대상 확대)
- Step 3 리뷰 엔진: 고정 3-agent → 모드 기반 N-agent 선택적 실행

## [1.35.2] - 2026-03-30

### Changed
- 6개 에이전트 `model: opus` 제거 → 부모 모델 자동 상속 (Pro→sonnet, Max→opus 자동 적용)
- PR diff 배달 방식 변경: 프롬프트 3회 포함 → `/tmp/` 파일 저장 + 경로 전달 (부모 컨텍스트 토큰 ~67% 절감)
- diff 파일 생명주기 관리: 생성→공유→갱신(auto-fix시)→유지→정리(머지시)
- skill-plan/skill-impl 에이전트 프롬프트 경량화 (경로/목록만 전달, 에이전트 자체 Read)

### Removed
- pr-reviewer-test의 domain-logic.md 중복 로드 (pr-reviewer-domain이 담당)

## [1.35.1] - 2026-03-29

### Added
- `/skill-health-check` CRITICAL/MAJOR FAIL 시 backlog.json에 Task 자동 등록 (MINOR은 리포트만)
- `/skill-review-pr` 경량 리뷰 판정 (Trivial PR Fast Path): additions+deletions ≤ 30 && src/ 변경 0건 && 보안 키워드 미포함 시 3-agent 리뷰 스킵

## [1.35.0] - 2026-03-29

### Added
- 추세 경보: 3회 연속 FAIL 항목 감지, 점수 하락 추세, 카테고리 failCap 경고
- "정리해줘" 자연어 매핑 → `/skill-health-check --fix` 자동 전환 (dry-run 확인 포함)
- `/skill-status` 검진 주기 안내 (7일/14일 경과 시, suppressReminder 설정 가능)
- history 50건 초과 시 자동 정리 (oldest 삭제)
- streak 판정 규칙 명확화 (SKIP 미중단, ERROR=FAIL, fix 제외, PASS 리셋)

### Fixed
- Phase C 점수 계산: 전 항목 SKIP 카테고리 제로 분모 방지 (가중치 재분배)
- Phase B autoFix: 실패/거절 시 FAIL 기록, fixesApplied에 성공 항목만 포함
- SEC-01 패턴 확장: apiKey, token, bearer, authorization 추가 + 타입 선언 제외
- SEC-02 범위 확장: JPA @Query, JDBC string concatenation 탐지 대상 추가
- Post-Merge Health Gate: 이력 없을 때 추세 비교 스킵
- health-history.schema.json: mode 필드 enum 제한 (full/quick/scope/fix/quick-fix)

## [1.34.0] - 2026-03-27

### Added
- `/skill-health-check` 코드베이스 건강 검진 (22개 검사 항목, 점수 + 등급 + 이력 추적)
- 기본 보안 검사 4개 항목 (민감정보, SQL Injection, CORS, API 인증 — 전체 도메인)
- fintech 도메인 컴플라이언스 검사 4개 항목 (감사 로그, 멱등성, 금액 정밀도, 트랜잭션)
- `health-history.schema.json` 검사 이력 스키마
- `/skill-merge-pr` Post-Merge Health Gate (CRITICAL 자동 감지)
- `/skill-release` 사전 Health Gate (선택적)
- `/skill-status --health` → `/skill-health-check` 에스컬레이션 안내
- `docs/skill-reference.md` 검증 도구 선택 가이드

### Changed
- `project.schema.json`에 `healthCheck` 설정 필드 추가

## [1.33.1] - 2026-03-16

### Fixed
- skill-upgrade Step 13: CLAUDE.md 재생성 시 서브 에이전트 위임 금지 + 결정적 치환 원칙 적용 (구 버전 복사 방지)
- TEMPLATE-ENGINE.md: 결정적 치환 원칙 명시 (기존 CLAUDE.md는 CUSTOM_SECTION 추출에만 사용)

### Added
- skill-upgrade Step 13-3: 재생성 검증 게이트 (포지티브/네거티브 체크 + 재시도)
- TEMPLATE-ENGINE.md: 재생성 정합성 검증 규칙 (upgrade 시 템플릿 반영 확인)

## [1.33.0] - 2026-03-15

### Changed
- 컨텍스트 한계 관리: 70% 강제 중단 → compact 허용 + 상태 파일 조건부 복구 + 작업 계속 진행 (76줄 → 12줄)
- compact 후 복구: 3파일 무조건 읽기 → 조건부 읽기 (backlog만 항상, plan/project는 필요 시)

### Added
- customization.md: CUSTOM_SECTION 활용 예시 2건 (compact 알림 절충안, 프로젝트 코딩 규칙)

## [1.32.1] - 2026-03-15

### Fixed
- skill-plan/feature: allowed-tools에 AskUserQuestion 누락 복구 (v1.29.0 merge 충돌 해소 시 유실)
- 컨텍스트 한계 관리: 모델별 총 컨텍스트 크기 확인 절차 추가 (Opus 1M을 200k로 오인하여 조기 중단 방지)

### Removed
- 고아 파일 shared-protocols.md 삭제 (v1.32.0 압축으로 미참조 상태)

## [1.32.0] - 2026-03-15

### Changed
- CLAUDE.md 템플릿: Git 워크트리 프로토콜 결정 테이블 + 워크플로우 상태 추적 프로토콜 추가 (SSOT 강화)
- 22개 SKILL.md 선언적 압축 (8,361줄 → 2,165줄, 74% 절감)
  - bash 코드 블록 → 선언적 요구사항 전환
  - CLAUDE.md 프로토콜 반복 제거 → 참조 + 단계명 힌트 2줄로 통일
  - 출력 포맷 템플릿 → 필수 필드 목록으로 축소
  - 워크플로우 체인당 토큰 ~54,500 → ~11,300 (79% 절감)
- 모든 스킬의 기능 로직, 결정 트리, Tier S 명령(squash merge 플래그, Intent 스키마 등) 100% 보존

## [1.31.1] - 2026-03-12

### Fixed
- `examples/README.md`: ecommerce-shop 예제 목록 누락 수정 (v1.28.0에서 추가되었으나 목록 미갱신)

## [1.31.0] - 2026-03-11

### Added
- `docs/customization.md` 확장 (79→249줄) — domain.json 전체 구조 워크스루, 체크리스트 형식 가이드, Layered Override 상세 설명
  - domain.json 주요 필드 설명 테이블 + keywords 동작 방식 워크스루
  - 체크리스트 심각도(CRITICAL/MAJOR/MINOR) 설명 + 실전 예시
  - 디렉토리 구조 트리, _registry.json 등록 예시, 도메인 생성 3가지 방법

### Fixed
- domain.json 문서 예시를 실제 `ecommerce/domain.json`과 일치시킴 (conventions, defaultStack 필드 정합성)

## [1.30.0] - 2026-03-11

### Added
- README.md "빠른 시작": 기존 프로젝트용 `/skill-onboard` 진입점 추가 (신규 사용자 발견성 개선)
- `docs/getting-started.md`: 온보딩 섹션 확장 — 준비 단계, 실행 흐름 다이어그램, `--scan-only` 옵션, 온보딩 후 다음 단계
- `examples/README.md`: "기존 프로젝트에 적용" 섹션 추가 (`/skill-onboard` + `--scan-only` 안내)

## [1.29.0] - 2026-03-11

### Added
- `shared-protocols.md`: 9개 공통 프로토콜 SSOT 문서 신규 생성 — Protocol A(project+backlog 검증), B(completed 검증), C(운영환경 검증), D(origin/develop 동기화), E(Worktree 감지), F(빌드 명령어 결정), G(에러 3줄 표준), H(AskUserQuestion 승인), I(진행 표시)
- 독립 스킬 5개(retro, report, estimate, create, onboard)에 간소화 진행 표시 추가 (Protocol I)

### Changed
- 14개 스킬의 MUST-EXECUTE-FIRST 중복 검증(~20줄씩) → Protocol 참조로 교체 (순 -197줄 감소)
- 에러 메시지 전체 3줄 표준화: ❌ 에러 / 원인 / 해결 (Protocol G)
- 승인 프롬프트 Y/N → AskUserQuestion 통일 (Protocol H)
- skill-feature, skill-plan: allowed-tools에 `AskUserQuestion` 추가 (Protocol H 정합성)

## [1.28.0] - 2026-03-11

### Added
- ecommerce-shop: `SHOP-002-spec.md` 주문 처리 시스템 설계 명세 — 상태 머신 11가지, 재고 동시성(낙관적 락), 가격 계산(Zod 정수 강제), 에러 코드 5종, 테스트 15건, Production Readiness Gaps 11항목
- ecommerce-shop: `CLAUDE.md` 프로젝트 지시문 — fintech-gateway와 대칭 구조 (에이전트 5종, 키워드 매핑 6종, 체크리스트 5관점, 에러 코드 체계)
- ecommerce-shop: `backlog.json` SHOP-002에 steps 2개 추가 (주문 CRUD+상태머신 ~400줄, 가격계산+테스트 ~350줄)

### Fixed
- README.md: 버전 배지 `v1.25.0` → `v1.27.0` 정합성 수정
- SHOP-002-spec.md: 에러 응답에서 재고 수량 노출 제거 (보안)
- SHOP-002-spec.md: 금액 정수 강제 Zod `z.number().int()` 스키마 + `Math.max(0)` 음수 방지 추가
- SHOP-002-spec.md: 테스트 10건 → 15건 확충 (상태전이 전수, 가격 스냅샷, 경계값, 쿠폰 동시성, 음수 방지)
- SHOP-002-spec.md: Production Readiness Gaps 7건 → 11건 확충 (인증 상세, 멱등성, 암호화, 동의, 에스크로)
- order-flow.md: REFUNDED 상태 누락 → 추가 (SSOT 정합성)

## [1.27.0] - 2026-03-10

### Added
- skill-validate: Category 10 도메인 키워드 참조 정합성 — `keywords.*.docs[]` ↔ 실제 파일 ERROR 레벨 검증, `_base:` 접두사 경로 해석 지원
- skill-validate: Category 11 스키마-데이터 정합성 — project.json/backlog.json이 스키마 required 필드를 준수하는지 검증
- skill-validate: Category 12 레지스트리-도메인 교차 검증 — `_registry.json` ↔ `domain.json` 간 name/icon/description/keywords 일치 확인
- domain.json: 3개 도메인(fintech/ecommerce/general)에 `icon` 필드 추가 — Category 9 검증 통과
- ecommerce: `member.md` 신규 — 회원가입/로그인/마이페이지/탈퇴/법적 보관 의무
- ecommerce: `product.md` 신규 — 상품 구조/상태 전이/카테고리/가격 정책
- ecommerce: `member` keyword 추가 ("회원", "회원가입", "로그인", "마이페이지", "탈퇴")
- general: keyword docs를 `_base:conventions/` 접두사 참조로 전환 — 중복 문서 방지, `_base/conventions/` 재활용
- BDD 시나리오 구조화: `docs/scenarios/` — Given/When/Then YAML 형식 + full-feature.yaml 예시
- workflow-guide: 판단 분기점 테이블 5건 + Troubleshooting 7건 추가
- SSOT 원칙 적용: CLAUDE.md/TASK-001-spec.md에 도메인 docs 진실점 포인터 추가
- 회귀 테스트 전략: `docs/regression-testing.md` — fintech-gateway Golden State 지정 + 검증 절차

### Fixed
- TASK-001-spec.md: refresh 에러 응답 내부코드(PG-GW-016) → 외부코드(TOKEN_INVALID) 변경
- error-handling.md: SSOT에 PG-GW-012 (INVALID_CREDENTIALS) 누락 → 추가
- _registry.json: lastUpdated 갱신 + description/compliance/keywords 동기화
- ecommerce domain.json: "장바구니" trigger 추가 (registry-domain 불일치 해소)
- fintech domain.json: "토큰/PG/VAN/가맹점" trigger 추가 (registry-domain 불일치 해소)

### Changed
- workflow-guide: 설계 스텝 표시 "Step 1,2,3" → "Step 1,2" 조정

## [1.26.0] - 2026-03-10

### Added
- TASK-001-spec: 의존성 GAV 고정 — Spring Cloud BOM 2024.0.0, jjwt 0.12.6, Kotlin 2.0.21, Spring Boot 3.3.5, MockK 1.13.13
- TASK-001-spec: WebFlux 주의사항 — 서블릿 코드(`@Controller`, `MockMvc`, `HttpServletRequest`) 혼입 금지 명시
- TASK-001-spec: 구성 요소 상세화 — 래퍼 타입(AccessToken/RefreshToken), InMemoryUserRepository, BCryptPasswordEncoder(cost 12), GlobalExceptionHandler, Logback eyJ 마스킹 필터
- TASK-001-spec: UserRepository 인터페이스 분리 — NFR-003 확장성(추후 RDB 전환) 준수
- TASK-001-spec: 테스트 명세 12건 추가 — 단위 9건, 동시성 1건, 보안 1건, E2E 1건 (WebTestClient 필수)
- TASK-001-spec: 수용 기준 8항목 추가 — 브랜치 커버리지 80%, PCI-DSS, eyJ 마스킹, 래퍼 타입 등
- TASK-001-spec: Production Readiness Gaps 9항목 — InMemory→Redis, HS256→RS256, JSON body→Cookie 등
- TASK-001-spec: 블랙리스트 동시성 전략 — `ConcurrentHashMap.newKeySet()` 명시
- CLAUDE.md: 에러 코드 외부 매핑에 `INVALID_CREDENTIALS` 추가 (PG-GW-012 내부 전용)
- CLAUDE.md: 브랜치 커버리지 80%+ 목표, WebTestClient 필수 (MockMvc 금지) 명시

### Changed
- TASK-001-spec: 스텝 분리 3→2 합침 (Step 1: 스캐폴딩+모델+구현 ~450줄, Step 2: 필터+컨트롤러+테스트 ~300줄)
- TASK-001-spec: 로그인 에러 외부코드 `PG-GW-012` → `INVALID_CREDENTIALS`로 변경 (내부코드 노출 방지)
- project.json: infrastructure `docker-compose` → `none` 변경

## [1.25.1] - 2026-03-10

### Fixed
- backlog.json 스키마 정합성: `metadata.version` 필드 추가 (동시성 제어 필수), task `id` 필드 추가, `phase` 타입 integer로 수정, `specFile` 필드명 통일
- project.json 스키마 정합성: `version` (required) 필드 추가, `metadata.version` 동시성 제어 필드 추가
- backlog.schema.json: phases에 `required: ["name", "status"]` + `additionalProperties: false` 보강
- 에러 코드 확정: Token Reuse Detection → PG-GW-016 (TOKEN_REUSED)으로 통일 (TASK-001-spec.md, token-auth.md, CLAUDE.md, error-handling.md)
- Refresh Token 전달 방식 확정: 데모=JSON body 채택, 프로덕션=HttpOnly Cookie 권장사항 문서화 + XSS 보안 제약 경고 추가
- 양쪽 예제(fintech-gateway, ecommerce-shop) 동일 적용

## [1.25.0] - 2026-03-09

### Added
- skill-impl: push 전 develop 동기화 — 다른 세션의 backlog.json 변경 반영, push 실패 시 충돌 해소 + 재시도
- skill-impl: branch 중복 방지 — 기존 branch/PR 상태 확인 후 생성/이어서 작업/스킵 분기
- skill-impl: 워크트리 merge 후 step 상태 재검증 — 이미 완료된 step 스킵, 충돌 경고
- skill-impl: step 완료 시 `assignedAt` 자동 갱신 — lock heartbeat 효과
- skill-merge-pr: completed.json version 관리 — `metadata.version`/`updatedAt` 동시성 제어 도입
- skill-merge-pr: push 전 develop 동기화 — state 파일 충돌 방지
- skill-merge-pr: 워크트리 → develop 명시적 동기화 (섹션 5.7) — state 파일 메인 리포 반영
- skill-backlog: JSON 충돌 해소 규칙 명시 — 다른 Task는 모두 유지, 같은 필드는 최신 우선, version = max + 1
- skill-status: execution-log.json 동시 쓰기 안전 규칙 — append-only + push 충돌 시 재추가
- skill-plan: 섹션 7 lockedFiles push 성공 확인 필수 + 충돌 시 교집합 검사
- project.schema.json: `metadata.version`/`updatedAt` 동시성 제어 필드 추가

## [1.24.0] - 2026-03-08

### Added
- skill-plan: Task 조기 잠금(섹션 1.5) — 선택 즉시 `in_progress` + git push로 동시 세션 중복 선택 방지
- skill-plan: 계획 거절 시 롤백 — `todo`로 복원 + git push로 잠금 해제
- skill-status: `--locks`에 🟡 계획 중 상태 표시 (`lockedFiles` 비어있는 `in_progress` Task 구분)
- README.md: 리디자인 — 중앙 정렬 헤더, shields.io 배지 4개, 이모지 섹션 헤더, GitHub Alert 블록, blockquote 원칙, 중앙 푸터
- LICENSE: MIT 라이선스 파일 신규 생성

### Changed
- skill-plan: 섹션 7(승인 후) 축소 — status/assignee는 조기 잠금에서 설정, 승인 후는 lockedFiles/steps만 갱신
- skill-plan: Git 동기화 프로토콜 충돌 해소 로직 보강 — 같은 Task 중복 claim 시 재선택
- README.md: 제목에서 버전 번호 제거 → 배지로 이동 (릴리스 시 제목 수정 불필요)
- README.md: 요구사항 섹션 하단 이동, 정보 우선순위 재배치

## [1.23.0] - 2026-03-05

### Added
- skill-domain: `create` 명령어 추가 — `--ref` 참조 도메인 기반 새 도메인 생성 + AI 초기 문서 자동 생성
- skill-domain: `disable-model-invocation: false`로 변경 (AI 문서 생성 지원)
- skill-validate: 검증 항목 #9 도메인 완전성 검증 추가 (domain.json 필수 필드, docs/ 최소 파일)
- skill-retro: `lessons-learned.json` 구조 설계 + 회고 시 학습 항목 자동 추출/저장 (Step 5.5)
- skill-retro: `--lessons` 명령어 추가 (list/search/top 하위 명령)
- skill-plan: "과거 학습 반영" 절차 추가 — lessons-learned.json에서 관련 항목 로드 후 설계 참고

### Changed
- skill-domain: allowed-tools에 `Edit` 추가
- skill-domain: argument-hint에 `create` 추가

## [1.22.0] - 2026-03-04

### Added
- 워크플로우 프로필 (standard/fast): project.schema.json에 `workflowProfile` 필드 추가
- CLAUDE.md.tmpl: `{{WORKFLOW_PROFILE}}`, `{{WORKFLOW_CHAINING_RULES}}` 마커 기반 프로필별 체이닝 규칙 동적 생성
- TEMPLATE-ENGINE.md: `generate_workflow_chaining_rules()` 블록 생성기 추가
- skill-init: Step 5.5 워크플로우 프로필 선택 질문 추가 (--quick 시 standard 자동)
- skill-impl: 프로필별 라인 수 제한 (standard: 700줄, fast: 1000줄)
- skill-impl: 프로필별 다음 스킬 분기 (standard: review-pr, fast: merge-pr 직행)

### Changed
- CLAUDE.md.tmpl: 자동 체이닝 규칙 테이블을 `{{WORKFLOW_CHAINING_RULES}}` 블록 마커로 교체
- CLAUDE.md.tmpl: 중단 조건 "라인 수 700 초과" → "라인 수 제한 초과 (프로필별 상이)"
- CLAUDE.md.tmpl: 워크플로우 진행 표시에서 review-pr/fix 단계에 "(standard에서만 실행)" 주석 추가
- skill-init: project.json conventions 템플릿에 `workflowProfile` 필드 추가

## [1.21.0] - 2026-03-04

### Added
- 워크플로우 진행 표시 프로토콜: 체이닝 스킬 진입 시 표준 진행바 출력 (✅/🔄/⬜ 아이콘 + 단계별 설명)
- 자동 체이닝 전환/중단 출력 포맷: 6가지 전환 사유 + 3가지 중단 사유 표준 메시지 템플릿
- 스킬 진입 시 경량 점검 프로토콜: PR-backlog 상태 자동 보정, Stale workflow 감지(30분), Intent 파일 복구
- 6개 스킬(plan, impl, review-pr, fix, merge-pr, feature)에 워크플로우 진행 표시 섹션 추가
- 4개 스킬(plan, impl, review-pr, merge-pr)에 경량 점검 절차 추가
- skill-impl: 컨벤션 로딩 절차 — 계획 파일의 참조 컨벤션 또는 트리거 테이블 기반 자동 로드
- skill-plan: 스텝 설계 시 "참조 컨벤션" 필드 추가 (skill-impl이 활용)
- skill-review-pr: 리뷰 전 컨벤션 + 체크리스트 로딩 절차 추가
- backlog.schema.json: workflowState.fixLoopCount 필드 추가 (루프 가드)

### Changed
- 컨벤션 레이지 로딩: CONVENTIONS_SECTION 마커가 인라인 컨벤션 → 트리거 테이블로 변경 (토큰 ~60% 절감)
- 에러 코드 레이지 로딩: DOMAIN_ERROR_CODES 마커가 전체 테이블 → 파일 경로 참조로 변경
- TEMPLATE-ENGINE.md: generate_conventions_section(), generate_error_codes_section() 레이지 로딩 방식으로 재설계
- 자동 체이닝 규칙 테이블 3행 추가 (feature→plan, review-pr→fix, fix→review-pr)

## [1.20.0] - 2026-02-24

### Changed
- README.md 구조 개편: 599줄 → 110줄 축소, 상세 내용을 docs/ 6개 파일로 분리
  - `docs/getting-started.md`: 설치 상세 + 초기화 흐름 + 온보딩 안내
  - `docs/concepts.md`: 도메인, 에이전트 팀, 디렉토리 구조, 실행 모델, 핵심 원칙
  - `docs/skill-reference.md`: 22개 스킬 전체 레퍼런스 + 자연어 매핑
  - `docs/workflow-guide.md`: 자동 체이닝, 7가지 워크플로우, 품질 게이트, Git 전략
  - `docs/customization.md`: 도메인 확장, 새 도메인 생성/전환, Layered Override
  - `docs/upgrade-guide.md`: 프레임워크 업그레이드, 보존 항목, 롤백

### Added
- skill-init: `--quick` 모드 — 제로 결정 온보딩 (자동 감지 + 기본값, AskUserQuestion 0회)
  - 디렉토리명 → 프로젝트명, 빌드 파일 기반 도메인/스택 자동 감지
  - 감지 실패 시 general 도메인 defaultStack 사용
  - 기본 에이전트 3개 (pm, backend, code-reviewer)
  - `--quick --reset` 조합 지원

## [1.19.0] - 2026-02-23

### Changed
- skill-status: 정적 "다음 단계 추천"을 컨텍스트 기반 추천으로 교체 (workflowState/PR 상태/백로그 기반 8단계 우선순위)
- skill-review-pr: 서브에이전트 실패 시 사용자 선택 제공 (재시도/스킵/중단), 재시도 1회 허용
- skill-review-pr: 서브에이전트 실패를 execution-log.json에 기록 (subagent_failed 액션)
- 에러 메시지 표준화: skill-estimate, skill-onboard, skill-retro, skill-report, skill-create의 MUST-EXECUTE-FIRST 에러를 ❌/원인/해결 3줄 형식으로 통일

### Added
- skill-status: `--health --fix` 옵션 — Orphan Intent 자동 복구 + 정리 (30분 경과 기준, skill-validate --fix 패턴)

## [1.18.1] - 2026-02-23

### Changed
- 22개 SKILL.md description에 WHEN(사용 시점/트리거 조건) 추가
  - P0: 13개 자동 트리거 스킬 — 자연어 매칭 정확도 개선 (plan, impl, review-pr, fix, merge-pr, report, retro, estimate, create, onboard, hotfix, rollback, docs)
  - P1: 9개 내부 전용 스킬 — 문서화 일관성 확보 (init, feature, review, domain, backlog, status, release, validate, upgrade)
- Anthropic 스킬 가이드 기준 description 필드의 WHAT + WHEN 구조 적용

## [1.18.0] - 2026-02-22

### Added
- 공통 컨벤션 4개 추가 (`_base/conventions/`):
  - cache.md: 캐시 컨벤션 (키 네이밍, TTL 전략, Cache-Aside/Write-Through/Write-Behind, 무효화, Thundering Herd 방지)
  - message-queue.md: 메시지 큐 컨벤션 (CloudEvents 포맷, 전달 보증, 멱등성, DLQ, 재시도, 이벤트 버전 관리)
  - deployment.md: 배포 컨벤션 (환경 구분, Docker, CI/CD 파이프라인, 배포 전략, 헬스 체크, 롤백)
  - monitoring.md: 모니터링 컨벤션 (RED/USE 메서드, 메트릭 네이밍, 알림 규칙, 로그-메트릭-트레이스 연계)
- skill-upgrade: Step 6-0 SHA256 해시 비교 커스터마이징 감지 추가 (전체 프레임워크 파일 대상)
- skill-upgrade: Step 10-0 CUSTOM_SECTION 마커 존재 사전 확인 + 전체 백업 안전장치 추가
- skill-upgrade: Step 13-0 마커 자동 삽입 + 백업 커스텀 내용 복원 안전장치 추가

### Changed
- skill-upgrade: 해시 불일치 파일에 대해 덮어쓰기 전 사용자 확인 (소스 덮어쓰기/현재 유지/수동 머지)
- skill-upgrade: Step 7 미리보기에 사용자 수정 프레임워크 파일 목록 추가
- skill-docs: 공통 컨벤션 키워드 매핑에 4개 항목 추가 (캐시, 메시지큐, 배포, 모니터링)

## [1.17.0] - 2026-02-19

### Added
- project.schema.json: `buildCommands` 프로퍼티 추가 (build/test/lint 명령어 외부 설정)
- skill-onboard: 빌드 명령어 자동 감지 로직 (Step 1.6) + project.json 저장
- CLAUDE.md.tmpl: 루프 가드 규칙 추가 (skill-fix→skill-review-pr 최대 2회)

### Changed
- skill-hotfix: 워크트리 에러 메시지에 이유/대안 추가 (📌 이유 + 💡 대안)
- skill-rollback: 워크트리 에러 메시지에 이유/대안 추가 (📌 이유 + 💡 대안)
- skill-release: 워크트리 에러 메시지에 이유/대안 추가 + 실패 출력 포맷 표준화
- skill-plan: 승인 메시지를 "Y/N" → "Y/수정사항 입력"으로 변경 (부분 수정 지원)
- skill-plan: DB 설계 서브에이전트 호출 프로토콜 표준화 (timeout 60초, fallback, retry 0)
- skill-review-pr: 3종 리뷰 서브에이전트 호출 프로토콜 표준화 (timeout 60초, fallback, retry 0)
- skill-impl: docs/QA 서브에이전트 호출 프로토콜 표준화 (timeout 60초, fallback, retry 0)
- skill-impl: 빌드 명령어를 buildCommands 우선 참조 → techStack 폴백으로 변경
- skill-hotfix: 빌드 명령어를 buildCommands 우선 참조 → techStack 폴백으로 변경
- skill-rollback: 빌드 명령어를 buildCommands 우선 참조 → techStack 폴백으로 변경
- skill-release: 빌드 명령어를 buildCommands 우선 참조 → techStack 폴백으로 변경
- skill-fix: 빌드/테스트 명령어를 buildCommands 우선 참조 → techStack 폴백으로 변경
- skill-fix: 루프 가드 적용 (fix 횟수 기반 --auto-fix 재호출 제어)
- skill-onboard: 실패 출력 포맷 표준화 (❌ 실패 / 단계 / 에러 / 복구 방법)

## [1.16.0] - 2026-02-19

### Added
- skill-merge-pr: Intent 기반 원자적 다중 파일 업데이트 프로토콜 (세션 중단 복구)
- skill-backlog: 동적 lockTTL (lockedFiles 수 기반 1~3시간 자동 산정)
- backlog.schema.json: lockTTL 필드 추가 (3600~14400초)
- skill-status: 실행 로그 아카이브 로테이션 절차 구체화 (500건 초과 시 자동 정리, 30일 보관)

### Changed
- skill-merge-pr: Task 완료 처리에 intent 파일 기반 복구 메커니즘 추가 (5.0~5.7단계)
- skill-plan: 상태 업데이트에 lockTTL 산정 로직 추가 + Intent 복구 사전 점검 추가
- skill-impl: assignedAt 연장 시 lockTTL 동적 재산정 + Intent 복구 사전 점검 추가
- skill-status: lockTTL 표시를 동적 TTL로 변경 + --health에 orphan intent 감지 추가
- 서브에이전트 5개 지시문 대폭 확충 (317→855줄): 심각도 판정, 도메인별 검증, 설계 프레임워크
- agent-db-designer: CRITICAL/MAJOR/MINOR/INFO 심각도 판정 기준 + 출력 심각도 컬럼 추가
- agent-qa: P1/P2/P3 → CRITICAL/MAJOR/MINOR 심각도 매핑 테이블 추가 (pr-reviewer-test 연동)
- pr-reviewer-test: 심각도-우선순위 역방향 매핑 추가 (agent-qa 연동)
- pr-reviewer-security: general 도메인 보안 검토 항목 추가 (6항목)
- pr-reviewer-domain: general 도메인 중점 검토 항목 보강 (6항목)
- agent-pm: 컨텍스트 전달 프로토콜 표준화 (파일 명명 규칙, 생산자-소비자 매핑, 충돌 해소)
- docs-impact-analyzer, agent-qa, pr-reviewer-test: 에이전트 간 상호참조 관계 명시

## [1.15.0] - 2026-02-18

### Added
- skill-onboard: 기존 프로젝트 온보딩 (코드베이스 스캔 → 기술 스택 자동 감지 → 도메인 추천 → 설정 생성)
- skill-create: 커스텀 스킬 스캐폴딩 (SKILL.md 생성 + CLAUDE.md CUSTOM_SECTION 자동 등록)
- skill-estimate: 작업 복잡도 추정 (5팩터 분석 + completed.json 타임스탬프 기반 과거 데이터 보정)
- .claude/skills/custom/: 커스텀 스킬 디렉토리 (.gitkeep 포함)
- skill-validate: Category 8 커스텀 스킬 매니페스트 검증 추가

### Changed
- CLAUDE.md.tmpl: 신규 스킬 3개 등록 (명령어, 자연어 매핑 4건, 자동 체이닝 3건)
- skill-upgrade: Step 11에 커스텀 스킬 보존 로직 추가 (custom/ 백업 → 프레임워크 교체 → custom/ 복원)

## [1.14.1] - 2026-02-18

### Added
- skill-plan: MUST-EXECUTE-FIRST 블록 추가 (project.json/backlog.json 검증 + origin/develop 동기화)
- skill-status: --health에 backlog-completed 정합성 검증 추가
- backlog.schema.json: phases에 status 필드 추가 (todo/in_progress/done 자동 갱신)

### Changed
- skill-impl: MUST-EXECUTE-FIRST에 origin/develop 동기화 검증 추가 (5커밋 초과 차단, 1~4 자동 머지)
- skill-merge-pr: MUST-EXECUTE-FIRST에 origin/develop 동기화 검증 추가
- skill-merge-pr: Task 완료 처리 순서 변경 (completed.json 먼저 → backlog.json → 교차 검증 → Phase 갱신 → 단일 커밋)
- skill-merge-pr: backlog-completed 교차 검증 + 누락 자동 복구 로직 추가
- skill-merge-pr: Phase 상태 자동 갱신 로직 추가 (소속 Task 기준)

## [1.14.0] - 2026-02-18

### Added
- skill-retro: 완료 Task 회고 분석 + 체크리스트/컨벤션 학습 반영
- skill-hotfix: main 긴급 수정 + 보안 리뷰 + 패치 릴리스 + develop 백머지
- skill-rollback: git revert 기반 릴리스/PR 롤백 + 리버트 PR 감사 추적
- skill-report: 프로젝트 메트릭 리포트 (throughput, quality, code, health)
- hotfix.yaml: 긴급 핫픽스 워크플로우 정의

### Changed
- skill-merge-pr: Task 완료 시 회고 실행 안내 추가
- skill-status: 실행 로그 프로토콜에 신규 3개 스킬 항목 추가
- CLAUDE.md.tmpl: 신규 4개 스킬 명령어/자연어/워크플로우 매핑 추가
- backlog.schema.json: workflowState.currentSkill enum 확장
- git-workflow.md: 핫픽스/롤백 브랜치 절차 상세 추가

## [1.13.2] - 2026-02-17

### Fixed
- .gitignore에 `memory/` 디렉토리 추가

## [1.13.1] - 2026-02-17

### Fixed
- v1.12.0에서 누락된 `_base/conventions/` 공통 컨벤션 문서 7개 파일 커밋 추가

## [1.13.0] - 2026-02-17

### Added
- agent-db-designer: YAML frontmatter 기반 네이티브 subagent 전환 (분석 전용, Read/Glob/Grep)
- agent-qa: YAML frontmatter 기반 네이티브 subagent 전환 (분석 전용, Read/Glob/Grep)
- skill-plan: DB 설계 분석 병렬 Task 호출 (agents.enabled 조건부)
- skill-impl: QA 테스트 품질 분석 백그라운드 Task 호출 (agents.enabled 조건부)
- 워크플로우 상태 영속화: `workflowState` 필드로 크래시 후 재개 지원 (skill-impl, skill-review-pr, skill-fix, skill-merge-pr)
- backlog.json 동시 쓰기 보호: `metadata.version` 낙관적 동시성 제어 + JSON 유효성 검증 프로토콜
- 스킬 사전 조건 검증 표준화: `MUST-EXECUTE-FIRST` 블록 전 스킬 적용 (skill-impl, skill-review-pr, skill-fix, skill-release)
- 중앙화된 스킬 실행 로그: `.claude/state/execution-log.json` append-only 감사 추적
- skill-validate: 업그레이드 후 자체 검증 스킬 신규 생성 (7개 검증 카테고리)
- backlog.schema.json: backlog.json 데이터 모델 JSON Schema 정의
- General 도메인 보강: keywords 6개 + checklists 3개 + common-patterns.md 추가
- 멀티 스택 코드 템플릿: TypeScript 템플릿 7개 추가 (fintech 4개, ecommerce 3개) + 스택 기반 자동 선택
- skill-status 진단 강화: `--health` 옵션, 활성 PR 상태, 워크플로우 진행 상태, 시스템 건강 점검
- 의존성 취약점 검사: skill-impl 빌드 후 `npm audit` / `dependencyCheckAnalyze` / `govulncheck` 선택적 실행
- 트러블슈팅 가이드: `.claude/docs/troubleshooting.md` 8개 장애 시나리오별 진단/해결
- E-commerce 예제 프로젝트: `examples/ecommerce-shop/` (project.json, backlog.json, 요구사항 스펙)
- 커스텀 워크플로우 정의: `skill-domain add-workflow` 명령 추가

### Changed
- docs-impact-analyzer: 문서 영향도 분석 + 초안 제안까지 확장 (agent-docs 핵심 기능 통합)
- skill-plan: allowed-tools에 Task 추가
- agent-code-reviewer: YAML frontmatter 추가 (참조 문서로 명시), agent-qa 연동 정보 추가
- agent-db-designer: 상세 가이드(434줄) → 분석 핵심+출력 형식(76줄)으로 축약
- agent-qa: 상세 가이드(412줄) → 분석 핵심+출력 형식(71줄)으로 축약
- skill-upgrade: Step 15에서 skill-validate 자동 호출
- pr-reviewer-security: 의존성 취약점 리뷰 섹션 추가

### Removed
- project.schema.json, skill-init: 미구현 healthcare/saas 도메인 선택지 제거

## [1.12.0] - 2026-02-15

### Added
- 공통 개발 컨벤션 문서 7개 추가 (`_base/conventions/`):
  - api-design.md: API 설계 컨벤션 (URL 구조, 상태코드, 페이지네이션, 멱등성, Rate Limiting)
  - testing.md: 테스팅 컨벤션 (테스트 피라미드, 커버리지 목표, Mock 전략, 격리 원칙)
  - logging.md: 로깅 컨벤션 (구조화 로그, 레벨 기준, 민감정보 마스킹, 성능 로깅)
  - database.md: DB 설계 컨벤션 (네이밍, 인덱스, 마이그레이션, 무중단 변경, 낙관적 잠금)
  - error-handling.md: 에러 처리 컨벤션 (예외 계층, 재시도 전략, 서킷 브레이커)
  - security.md: 보안 개발 컨벤션 (JWT 인증, 입력 검증, CORS, Secret 관리)
  - project-structure.md: 프로젝트 구조 컨벤션 (레이어 아키텍처, 스택별 패키지 구조)
- skill-docs: 공통 컨벤션 키워드 매핑 섹션 추가 (도메인 무관 자동 참조)
- skill-docs: 문서 로딩 우선순위에 `_base/conventions/` 경로 추가
- skill-docs: 출력 포맷에 공통 컨벤션 섹션 추가

### Changed
- skill-feature: 기능 분석 시 공통 컨벤션 참조 경로 추가
- skill-impl: 참고자료 로드 순서에 공통 컨벤션 경로 추가
## [1.11.0] - 2026-02-12

### Added
- Claude Squad (git worktree) 옵셔널 통합: 모든 스킬에서 worktree 환경 자동 감지 및 대응
- project.schema.json: `orchestrator` 프로퍼티 추가 (`auto`/`claude-squad`/`none`)
- git-workflow.md: Worktree 모드 비교 테이블 문서 추가

### Changed
- CLAUDE.md.tmpl: 세션 시작 git 동기화에 worktree 분기 추가
- skill-impl: 환경 준비/커밋/푸시에 worktree 분기 추가 (CS 브랜치 직접 사용)
- skill-merge-pr: 머지 실행(`--delete-branch` 제거)/로컬 동기화/완료 푸시/충돌 안내에 worktree 대응 추가
- skill-plan: Git 동기화 프로토콜에 worktree 분기 추가
- skill-feature: 커밋/푸시에 worktree 분기 추가
- skill-release: worktree 환경 실행 차단 + 메인 레포 경로 안내

## [1.10.0] - 2026-02-12

### Changed
- PR body 템플릿 간소화: 자동화 프로세스와 중복되는 테스트/관련 문서/체크리스트 섹션 제거
- fintech PR 템플릿: 컴플라이언스 섹션만 유지, 나머지 중복 섹션 제거
- skill-impl: PR body 마커 6개→4개 축소 (TASK_ID, TEST_COVERAGE 제거)

## [1.9.0] - 2026-02-11

### Added
- 서브에이전트 frontmatter에 icon 필드 추가 (🔐 보안, 🏛️ 도메인, 🧪 테스트, 📝 문서분석)

### Changed
- skill-review-pr: Task 호출에 아이콘 description 추가, 결과 병합 테이블 아이콘 반영
- skill-impl: docs-impact-analyzer Task에 아이콘 description 추가

## [1.8.0] - 2026-02-11

### Changed
- skill-release Step 8: API 문서 도구 미감지 시 "스킵" → "자동 설치 후 재시도"로 변경 (Spring Boot/Node.js/Go 지원)
- skill-release Step 9: 자동 설치된 빌드 파일 변경분을 릴리스 커밋에 포함
- skill-init Step 7: API 문서 도구 수동 설정 안내 제거, 릴리스 시 자동 처리 안내로 교체

## [1.7.1] - 2026-02-08

### Changed
- skill-upgrade: kitSource 미설정 시 AskUserQuestion 대신 기본값(`https://github.com/wejsa/ai-crew-kit.git`) 사용
- skill-init: kitSource fallback을 사용자 질문에서 기본 URL로 변경

## [1.7.0] - 2026-02-08

### Added
- skill-upgrade: 프레임워크 업그레이드 스킬 신규 생성 (14단계 실행 플로우)
  - file-sync 기반 프레임워크 파일 선택적 업데이트
  - 도메인 커스텀 파일/항목 3단계 보존 (감지→추출→복원)
  - settings.json 커스텀 권한 머지 (합집합 + deny 보존)
  - CLAUDE.md/README.md 커스텀 섹션 보존 재생성
  - --dry-run, --rollback, --source, --version 옵션 지원
  - 잠금 파일, 진행 상태 파일, 자동 롤백 안전장치
- migrations.json: project.json 스키마 마이그레이션 매니페스트 추가
- project.schema.json: `kitVersion`, `kitSource` optional 필드 추가
- README.md.tmpl: CUSTOM_SECTION 마커 추가 (CLAUDE.md.tmpl과 동일 패턴)
- README.md: 프레임워크 업그레이드 섹션 추가 (부트스트랩 가이드 포함)

### Changed
- skill-init: Step 1에서 히스토리 리셋 전 ai-crew-kit origin URL 조건부 캡처
- skill-init: Step 6에서 project.json에 `kitVersion`, `kitSource` 필드 기록
- skill-status: 프로젝트 설정에 Kit 버전 표시 추가

## [1.6.0] - 2026-02-08

### Added
- skill-release: 빌드 & 테스트 검증 단계 추가 (Step 3, project.json 스택 기반)
- skill-release: API spec 스냅샷 단계 추가 (Step 8, springdoc/swagger-jsdoc/swag 자동 감지)
- skill-release: CHANGELOG 자동 수집 (git log + conventional commit 분류 + 사용자 확인)
- skill-init: 필수 의존성 설정 섹션 추가 (백엔드 스택별 API 문서 도구 안내)
- skill-init: docs/api-specs/ 디렉토리 초기 생성

### Changed
- skill-release: 실행 플로우 10단계 → 12단계 확장
- skill-release: Co-Authored-By "Opus 4.5" → "Opus 4.6" 업데이트
- skill-release: allowed-tools에 빌드 도구(./gradlew, npm, yarn, go, swag) 및 Glob 추가
- skill-release: 롤백 섹션에 부분 실패 대응 테이블 추가
- skill-init: Git 초기 커밋에 docs/ 디렉토리 포함

## [1.5.0] - 2026-02-07

### Added
- 3개 전용 리뷰 subagent 신규 생성 (YAML frontmatter 기반 네이티브 subagent)
  - pr-reviewer-security: 보안 + 컴플라이언스 (Read/Glob/Grep only)
  - pr-reviewer-domain: 도메인 + 아키텍처 (Read/Glob/Grep only)
  - pr-reviewer-test: 테스트 품질 (Read/Glob/Grep only)
- skill-review-pr: Task 실패 시 부분 결과 처리 및 오류 대응 규칙
- skill-impl: PR 생성 후 docs-impact-analyzer 백그라운드 Task 자동 실행
- docs-impact-analyzer subagent 신규 생성 (문서 영향도 분석 전용)

### Changed
- skill-review-pr: 순차 5관점 검토 → 3개 네이티브 subagent 병렬 호출로 변경
- skill-review-pr: 에이전트 활용 섹션 플레이스홀더 → 실제 subagent 연동으로 교체
- skill-impl: allowed-tools에 Task 추가
- agent-code-reviewer: mermaid 다이어그램 순차→병렬 흐름 반영

### Fixed
- Task subagent_type: 커스텀 에이전트명 → general-purpose + Read 로드 방식으로 수정
  - Task tool은 빌트인 타입(Bash, general-purpose, Explore 등)만 지원
  - 프롬프트에서 에이전트 파일을 Read로 로드하여 지침 적용하는 패턴으로 변경

## [1.4.0] - 2026-02-07

### Added
- PR body 템플릿 시스템 (pr-body.md.tmpl) + Layered Override 도메인 오버라이드
- fintech 도메인 PR 템플릿 (컴플라이언스 체크리스트 포함)
- skill-review-pr: 도메인 체크리스트 명시적 로딩 및 검토 결과 PR 코멘트 포함

### Changed
- skill-impl: PR body 하드코딩 → 템플릿 기반 동적 생성으로 변경
- skill-review-pr: 5관점 검토에 체크리스트 파일 대조 절차 구체화

## [1.3.0] - 2026-02-07

### Fixed
- skill-init: `git clone ai-crew-kit` 후 origin이 원본 저장소를 가리키는 문제 수정
  - Step 1 환경 검증에서 `git remote -v`로 origin 확인
  - ai-crew-kit origin 감지 시 `rm -rf .git && git init -b main`으로 히스토리 초기화

### Added
- skill-init: Git 초기 커밋 후 `develop` 브랜치 자동 생성
- skill-init: 완료 안내에 Git 원격 저장소 설정 가이드 추가

## [1.2.0] - 2026-02-07

### Added
- CLAUDE.md 템플릿: 세션 시작 시 continuation-plan.md 확인 단계 추가 (3단계→4단계)
- CLAUDE.md 템플릿: 컨텍스트 한계 관리 섹션 신규 추가 (70% 트리거, 연속 계획 파일, 복구 절차)

### Changed
- CLAUDE.md 템플릿: 스킬 자동 체이닝 규칙을 자동 연속 실행 규칙으로 교체 (테이블 형식 + 금지사항, 위치 이동)

## [1.1.3] - 2026-02-07

### Fixed
- skill-impl: `--all` 옵션 플로우에서 스텝 간 자동 진행이 중단되던 문제 수정
- skill-impl: `--all` 플로우 다이어그램의 "사용자 확인", "수동" 표현을 자동 체이닝으로 변경

### Added
- CLAUDE.md 템플릿: 스킬 자동 체이닝 규칙 섹션 추가 (자동 진행 원칙, 중단 조건)

## [1.1.2] - 2026-02-07

### Added
- skill-init: README.md 템플릿 기반 자동 생성 (프로젝트 전용 README)
- skill-init: VERSION 파일 초기화 (0.1.0) 자동 생성
- README.md.tmpl 템플릿 추가

### Changed
- skill-release: README.md 버전 업데이트 패턴을 project.json 기반 동적 처리로 변경
- skill-init: Git 초기 커밋 대상에 README.md, VERSION 포함

## [1.1.1] - 2026-02-05

### Changed
- README.md: 하드코딩된 버전 참조 제거 (제목만 버전 유지)
- CHANGELOG.md: [Unreleased] 섹션 추가로 skill-release 자동화 지원

## [1.1.0] - 2026-02-04

### Added
- skill-fix: CRITICAL 이슈 자동 수정 스킬 추가
- skill-release: 버전 관리 및 릴리스 자동화 스킬 추가
- 버전 관리 시스템 도입 (VERSION 파일 + CHANGELOG.md)

### Changed
- skill-review-pr: self-PR 감지 및 comment 기반 리뷰 로직 강화
- skill-merge-pr: self-PR 승인 조건 스킵 및 검증 로직 추가
- skill-impl/skill-plan: 워크플로우 체이닝 설정 정리
- .gitignore: auto-generated CLAUDE.md 제외 규칙 추가

### Fixed
- README 마크다운 취소선 렌더링 오류 수정 (`~` → `-`)

## [1.0.0] - 2026-02-03

### Added
- 초기 릴리스
- 12개 스킬: skill-feature, skill-plan, skill-impl, skill-review-pr, skill-fix, skill-merge-pr, skill-init, skill-docs, skill-hotfix, skill-rollback, skill-monitor, skill-report
- 6개 에이전트: backend, frontend, db-designer, devops, qa, docs
- 4개 도메인: general, ecommerce, fintech, _base
- 워크플로우 자동 연결 시스템
