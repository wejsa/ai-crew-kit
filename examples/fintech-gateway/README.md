# Fintech Gateway 예제 프로젝트

AI Crew Kit을 사용한 핀테크 도메인 API Gateway 프로젝트 예제입니다.

## 프로젝트 개요

| 항목 | 값 |
|------|-----|
| **도메인** | fintech |
| **기술 스택** | Spring Boot 3 + Kotlin |
| **데이터베이스** | MySQL 8.0 |
| **캐시** | Redis |
| **인프라** | Docker Compose |

## 디렉토리 구조

```
fintech-gateway/
├── .claude/state/
│   ├── project.json      # 프로젝트 설정
│   └── backlog.json      # 백로그
├── docs/requirements/
│   └── TASK-001-spec.md  # JWT 인증 요구사항
├── CLAUDE.md             # AI 에이전트 지시문
└── README.md             # 이 파일
```

## 활성화된 에이전트

| 에이전트 | 역할 |
|---------|------|
| agent-pm | 워크플로우 오케스트레이션 |
| agent-backend | 백엔드 개발 |
| agent-code-reviewer | 5관점 코드 리뷰 |
| agent-qa | 테스트 설계 및 검증 |

## 예제 Task

### TASK-001: JWT 토큰 인증

JWT 기반 인증 시스템 구현 예제입니다.

**요구사항:**
- Access Token / Refresh Token 발급
- Token Rotation 지원
- Token Reuse Detection

**스텝 분리:**
1. JWT 서비스 인터페이스 및 모델 (~200 라인)
2. JWT 서비스 구현 (~300 라인)
3. JWT 인증 필터 및 설정 (~250 라인)

## 사용법

```bash
# 프로젝트 디렉토리로 이동
cd examples/fintech-gateway

# 상태 확인
/skill-status

# 백로그 확인
/skill-backlog

# Task 개발 시작
/skill-plan
```

## 도메인 특화 설정

이 예제는 fintech 도메인으로 설정되어 있어 다음 기능이 자동 적용됩니다:

### 자동 참조 참고자료
- 결제 플로우 (`payment-flow.md`)
- 토큰 인증 (`token-auth.md`)
- 보안 컴플라이언스 (`security-compliance.md`)

### 리뷰 체크리스트
- PCI-DSS 컴플라이언스 체크
- 상태머신 검증
- JWT 보안 검증

### 에러 코드 체계
- `PG-GW-001` ~ `PG-GW-099` 범위 사용
