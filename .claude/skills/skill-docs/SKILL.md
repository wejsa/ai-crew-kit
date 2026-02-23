---
name: skill-docs
description: 프로젝트 참고자료 - 개발 시 자동 참조되는 도메인별 문서. 사용자가 "문서 찾아줘", "참고자료" 또는 /skill-docs를 요청할 때 사용합니다.
disable-model-invocation: false
allowed-tools: Read, Glob
argument-hint: "[keyword]"
---

# skill-docs: 프로젝트 참고자료

## 개요
프로젝트 도메인별 참고자료를 제공합니다.
개발 중 관련 키워드 감지 시 자동으로 참조됩니다.

## 사용 방법

### 명시적 호출
```
/skill-docs                    # 전체 문서 목록
/skill-docs payment            # 결제 관련 문서
/skill-docs api                # API 설계 문서
```

### 자동 참조 (disable-model-invocation: false)
개발 중 관련 키워드 감지 시 Claude가 자동으로 참조:
- 결제, 승인, 인증 → payment 문서
- API 설계, 엔드포인트 → api-design 문서
- 에러, 예외, 재시도 → error-handling 문서

## 문서 구조 (도메인 시스템)

문서 위치는 `.claude/state/project.json`의 도메인 설정에 따라 결정됩니다:

```
.claude/domains/
├── _base/
│   ├── conventions/            # 공통 개발 컨벤션
│   │   ├── naming.md
│   │   ├── git-workflow.md
│   │   ├── api-design.md
│   │   ├── testing.md
│   │   ├── logging.md
│   │   ├── database.md
│   │   ├── error-handling.md
│   │   ├── security.md
│   │   └── project-structure.md
│   └── templates/              # 공통 템플릿
│       ├── api-spec.yaml
│       ├── test-scenario.md
│       └── requirement-spec.md
├── {domain}/                   # 현재 도메인 (fintech, ecommerce, general 등)
│   ├── docs/                   # 도메인별 참고자료
│   │   ├── README.md           # 문서 목록 및 키워드 매핑
│   │   └── {topic}.md          # 주제별 문서
│   ├── checklists/             # 도메인별 체크리스트
│   └── domain.json             # 도메인 설정 + 키워드 매핑
```

**문서 로딩 우선순위**:
1. `.claude/domains/{domain}/docs/` (도메인별 참고자료)
2. `.claude/domains/_base/conventions/` (공통 개발 컨벤션)
3. `.claude/domains/_base/templates/` (공통 템플릿)

## 키워드 매핑

키워드 매핑은 `.claude/domains/{domain}/domain.json`의 `keywords` 필드에서 로드됩니다:

```json
{
  "keywords": {
    "payment": {
      "triggers": ["결제", "승인", "인증", "카드"],
      "docs": ["payment-flow.md", "token-auth.md"]
    },
    "settlement": {
      "triggers": ["정산", "수수료", "D+N"],
      "docs": ["settlement.md"]
    }
  }
}
```

## 공통 컨벤션 키워드 매핑

도메인과 무관하게 모든 프로젝트에 적용되는 개발 컨벤션입니다.
`.claude/domains/_base/conventions/` 경로에서 로드됩니다.

| 키워드 | 문서 |
|--------|------|
| API, REST, 엔드포인트, 상태코드 | api-design.md |
| 테스트, 커버리지, 단위테스트, TDD | testing.md |
| 로그, 로깅, 추적, traceId | logging.md |
| 테이블, 스키마, 마이그레이션, DB, 인덱스 | database.md |
| 에러, 예외, 재시도, 서킷브레이커 | error-handling.md |
| 보안, 인증, 암호화, XSS, CORS | security.md |
| 패키지, 구조, 레이어, 아키텍처 | project-structure.md |
| 네이밍, 변수명, 클래스명 | naming.md |
| 브랜치, 커밋, PR, Git | git-workflow.md |
| 캐시, Redis, TTL, 무효화 | cache.md |
| 메시지큐, RabbitMQ, Kafka, 이벤트, 비동기 | message-queue.md |
| 배포, Docker, CI/CD, K8s, 환경변수 | deployment.md |
| 모니터링, 메트릭, 알림, 헬스체크 | monitoring.md |

또는 `docs/README.md`에 키워드 매핑 정의:

```markdown
| 키워드 | 문서 |
|--------|------|
| 결제, 승인, 인증 | payment-flow.md |
| 정산, 수수료 | settlement.md |
| 취소, 환불 | refund-cancel.md |
| API, 엔드포인트 | api-design.md |
| 에러, 예외, 재시도 | error-handling.md |
| 보안, 암호화 | security.md |
```

## 출력 포맷

### 문서 목록 조회
```
## 📚 참고자료 목록

### 도메인 참고자료 ({domain})
| 문서 | 설명 | 키워드 |
|------|------|--------|
| payment-flow.md | 결제 플로우 | 결제, 승인 |
| api-design.md | API 설계 가이드 | API, 엔드포인트 |
| error-handling.md | 에러 처리 | 에러, 예외 |

### 공통 컨벤션
| 문서 | 설명 | 키워드 |
|------|------|--------|
| api-design.md | API 설계 컨벤션 | API, REST |
| testing.md | 테스팅 컨벤션 | 테스트, 커버리지 |
| logging.md | 로깅 컨벤션 | 로그, 추적 |
| database.md | DB 설계 컨벤션 | 테이블, 스키마 |
| error-handling.md | 에러 처리 컨벤션 | 에러, 재시도 |
| security.md | 보안 개발 컨벤션 | 보안, 인증 |
| project-structure.md | 프로젝트 구조 컨벤션 | 패키지, 레이어 |
| naming.md | 네이밍 컨벤션 | 네이밍, 변수명 |
| git-workflow.md | Git 워크플로우 컨벤션 | 브랜치, 커밋 |
| cache.md | 캐시 컨벤션 | 캐시, Redis, TTL |
| message-queue.md | 메시지 큐 컨벤션 | 메시지큐, RabbitMQ, 이벤트 |
| deployment.md | 배포 컨벤션 | 배포, Docker, CI/CD |
| monitoring.md | 모니터링 컨벤션 | 모니터링, 메트릭, 알림 |

특정 문서 조회: `/skill-docs {키워드}`
```

### 특정 문서 조회
```
## 📄 참고자료: {문서명}

{문서 내용}

---
관련 문서: {관련 문서 목록}
```

## 템플릿 사용

### API 스펙 템플릿
```
/skill-docs template api-spec
```
→ `templates/api-spec.yaml` 내용 출력

### 테스트 시나리오 템플릿
```
/skill-docs template test-scenario
```
→ `templates/test-scenario.md` 내용 출력

### 요구사항 문서 템플릿
```
/skill-docs template requirement
```
→ `templates/requirement-spec.md` 내용 출력

## 커스터마이징 가이드

### 새 문서 추가
1. `docs/` 디렉토리에 마크다운 파일 추가
2. `docs/README.md`에 키워드 매핑 추가

### 예시: 쇼핑몰 프로젝트
```
docs/
├── README.md
├── order-flow.md         # 주문 플로우
├── inventory.md          # 재고 관리
├── shipping.md           # 배송
└── promotion.md          # 프로모션
```

### 예시: 금융 프로젝트
```
docs/
├── README.md
├── payment-flow.md       # 결제 플로우
├── settlement.md         # 정산
├── refund-cancel.md      # 환불/취소
├── security-compliance.md # 보안/컴플라이언스
└── api-design.md         # API 설계
```

## 자동 참조 동작

Claude가 코드 작성 중 다음과 같이 동작:

1. **키워드 감지**: 사용자 요청 또는 코드에서 키워드 발견
2. **문서 검색**: `docs/README.md`에서 매핑된 문서 찾기
3. **내용 참조**: 해당 문서 읽기
4. **코드 반영**: 참고자료 기반으로 구현
5. **출처 표기**: 참조한 문서 명시

```
## 구현 참고
- 참조 문서: `skill-docs/docs/payment-flow.md`
- 적용 내용: 결제 상태 머신 로직
```

## 주의사항
- 읽기 전용 작업만 수행
- 문서 수정은 직접 파일 편집 필요
- 자동 참조는 개발 컨텍스트에서만 동작
