# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
