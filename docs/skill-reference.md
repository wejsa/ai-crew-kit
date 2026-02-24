# 스킬 레퍼런스

> [← README로 돌아가기](../README.md)

## 자주 사용하는 명령어

| 명령어 | 설명 | 자연어 예시 |
|--------|------|------------|
| `/skill-status` | 프로젝트 상태 확인 | "상태 확인해줘" |
| `/skill-feature` | 새 기능 기획 | "새 기능 기획해줘" |
| `/skill-plan` | 설계 및 스텝 계획 | "다음 작업 가져와줘" |
| `/skill-impl` | 코드 구현 + PR 생성 | "개발 진행해줘" |
| `/skill-review-pr` | PR 리뷰 | "PR 123 리뷰해줘" |
| `/skill-merge-pr` | PR 머지 | "PR 123 머지해줘" |
| `/skill-retro` | 완료 Task 회고 | "회고 해줘" |
| `/skill-hotfix` | main 긴급 수정 | "긴급 수정해줘" |
| `/skill-rollback` | 릴리스 롤백 | "v1.2.3 롤백해줘" |
| `/skill-report` | 프로젝트 메트릭 리포트 | "리포트 생성해줘" |

## 전체 명령어 목록

### 프로젝트 관리

| 명령어 | 설명 |
|--------|------|
| `/skill-init` | 프로젝트 초기화 |
| `/skill-init --quick` | 제로 결정 빠른 초기화 |
| `/skill-init --reset` | 기존 설정 초기화 (재설정) |
| `/skill-status` | 현재 상태 확인 |
| `/skill-status --health` | 시스템 건강 점검 |
| `/skill-status --health --fix` | 건강 점검 + Orphan 자동 복구 |
| `/skill-backlog` | 백로그 조회/관리 |
| `/skill-onboard` | 기존 프로젝트에 AI Crew Kit 적용 |
| `/skill-onboard --scan-only` | 스캔만 수행 (설정 생성 없음) |

### 개발 워크플로우

| 명령어 | 설명 |
|--------|------|
| `/skill-feature` | 새 기능 기획 |
| `/skill-plan` | 설계 + 스텝 계획 수립 |
| `/skill-impl` | 코드 구현 (스텝별) |
| `/skill-impl --next` | 다음 스텝 진행 |
| `/skill-review` | 코드 리뷰 |
| `/skill-review-pr {번호}` | PR 리뷰 |
| `/skill-review-pr {번호} --auto-fix` | PR 리뷰 + CRITICAL 이슈 자동 수정 |
| `/skill-fix {번호}` | CRITICAL 이슈 수정 |
| `/skill-merge-pr {번호}` | PR 머지 |

### 운영/인프라

| 명령어 | 설명 |
|--------|------|
| `/skill-hotfix "{설명}"` | main 긴급 수정 |
| `/skill-rollback {태그\|PR번호}` | 릴리스/PR 롤백 |
| `/skill-release` | 버전 릴리스 |

### 분석/문서

| 명령어 | 설명 |
|--------|------|
| `/skill-docs` | 참고자료 조회 |
| `/skill-retro` | 완료 Task 회고 |
| `/skill-retro {TASK-ID}` | 특정 Task 회고 |
| `/skill-retro --summary` | 전체 회고 요약 |
| `/skill-report` | 프로젝트 메트릭 리포트 |
| `/skill-report --full` | 전체 히스토리 리포트 |
| `/skill-estimate` | 작업 복잡도 추정 |

### 설정/확장

| 명령어 | 설명 |
|--------|------|
| `/skill-domain` | 도메인 관리 |
| `/skill-domain list` | 도메인 목록 조회 |
| `/skill-domain switch {도메인}` | 도메인 전환 |
| `/skill-domain add-doc {경로}` | 참고자료 추가 |
| `/skill-domain add-checklist {경로}` | 체크리스트 추가 |
| `/skill-create` | 커스텀 스킬 생성 |
| `/skill-upgrade` | 프레임워크 업그레이드 |
| `/skill-upgrade --dry-run` | 변경 사항 미리보기 |
| `/skill-validate` | 업그레이드 후 검증 |

## 자연어 매핑

명령어를 모르더라도 자연어로 요청할 수 있습니다:

| 자연어 | 매핑되는 스킬 |
|--------|-------------|
| "새 기능 기획해줘" | `/skill-feature` |
| "다음 작업 가져와줘" | `/skill-plan` |
| "개발 진행해줘" | `/skill-impl` |
| "PR 123 리뷰해줘" | `/skill-review-pr 123` |
| "PR 123 머지해줘" | `/skill-merge-pr 123` |
| "상태 확인해줘" | `/skill-status` |
| "회고 해줘" | `/skill-retro` |
| "리포트 생성해줘" | `/skill-report` |
| "작업량 추정해줘" | `/skill-estimate` |
| "긴급 수정해줘" | `/skill-hotfix` |
| "v1.2.3 롤백해줘" | `/skill-rollback v1.2.3` |
| "참고자료 보여줘" | `/skill-docs` |
| "스킬 만들어줘" | `/skill-create` |
| "프로젝트 온보딩해줘" | `/skill-onboard` |
