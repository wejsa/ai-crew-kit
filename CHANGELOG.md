# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
