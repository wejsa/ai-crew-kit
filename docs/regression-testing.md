# 회귀 테스트 전략

> [<- README로 돌아가기](../README.md)

## Golden State

프레임워크 변경 후 기존 기능이 깨지지 않았는지 검증하기 위해 **Golden State** 예제 프로젝트를 지정합니다.

### 지정된 Golden State

| 예제 | 도메인 | 역할 |
|------|--------|------|
| `examples/fintech-gateway/` | fintech | **Primary Golden State** — 모든 프레임워크 변경 후 검증 필수 |
| `examples/ecommerce-shop/` | ecommerce | Secondary — 도메인 관련 변경 시 추가 검증 |

### fintech-gateway가 Golden State인 이유
- 가장 복잡한 도메인 규칙 (PCI-DSS, 에러코드 체계, 외부/내부 분리)
- TASK-001 명세가 가장 상세 (테스트 12건, 수용 기준 8항목)
- 래퍼 타입, CAS 패턴 등 고급 패턴 포함
- 다른 예제에서 발생 가능한 이슈를 대부분 커버

## 검증 절차

### 프레임워크 변경 시 필수

```
1. 변경 완료
2. /skill-validate 실행 → 전체 PASS 확인
3. fintech-gateway Golden State 검증:
   a. .claude/state/backlog.json 유효성
   b. .claude/state/project.json 유효성
   c. domain.json keywords.docs[] 참조 정합성
   d. _registry.json ↔ domain.json 교차 정합성
   e. CLAUDE.md 에러코드 ↔ error-handling.md SSOT 일치
4. ecommerce-shop 기본 검증 (변경 범위에 따라)
```

### 검증 자동화

`/skill-validate`가 Category 1~12를 자동 검증합니다.
Golden State 특화 검증은 아래 항목을 수동 확인합니다:

| 항목 | 검증 방법 | 기준 |
|------|----------|------|
| 스키마 준수 | Category 11 (스키마-데이터 정합성) | ERROR 0건 |
| 참조 정합성 | Category 10 (키워드 참조) | ERROR 0건 |
| 교차 정합성 | Category 12 (레지스트리-도메인) | WARN 0건 |
| SSOT 일관성 | 수동 — CLAUDE.md ↔ domain docs 비교 | 불일치 0건 |

## 회귀 발생 시 대응

1. 즉시 `/skill-validate --fix`로 자동 수정 가능 항목 처리
2. 자동 수정 불가 항목은 수동 수정
3. 수정 후 `/skill-validate` 재실행으로 전체 PASS 확인
4. 필요 시 `/skill-rollback`으로 변경 철회
