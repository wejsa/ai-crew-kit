# 기본 베이스라인

ai-crew-kit은 v3.0.0부터 도메인 특화 없는 **범용 프레임워크**입니다. 이 디렉토리는 모든 프로젝트에 적용되는 기본 베이스라인(공통 문서·기본 스택 메타)을 제공합니다.

## 개요

| 항목 | 내용 |
|------|------|
| **적합한 프로젝트** | 모든 일반 소프트웨어 프로젝트 |
| **적용 규칙** | `_base/` 공통 체크리스트·컨벤션 (기본 보안 포함) |
| **기본 스택** | 프로젝트 요구사항 기반 추천 (skill-init Step 5) |

## 적용 체크리스트

### 공통 (`_base/`)
- `checklists/common.md` — 코드 품질, 테스트 기본
- `checklists/security-basic.md` — 기본 보안 체크리스트
- `checklists/architecture.md` — 아키텍처 일관성
- `conventions/` — 언어·스택 무관 공통 컨벤션

## 사용 방법

### 1. 프로젝트 초기화
```bash
/skill-init
```

### 2. 기능 개발
```bash
/skill-plan
/skill-impl
```

## 참고 문서

| 문서 | 설명 |
|------|------|
| [getting-started.md](docs/getting-started.md) | 시작 가이드 |
| [common-patterns.md](docs/common-patterns.md) | 공통 패턴 |

## 커스터마이징

프로젝트별 컨벤션·체크리스트는 `_base/conventions/`, `_base/checklists/`에 추가하거나
CLAUDE.md의 CUSTOM_SECTION에 직접 기술합니다. 자세한 내용은 GitHub 리포의
`docs/customization.md`를 참조하세요.
