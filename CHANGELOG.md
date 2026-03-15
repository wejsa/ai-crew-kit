# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
