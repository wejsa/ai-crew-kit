# ecommerce-shop

## 프로젝트 개요

이커머스 온라인 쇼핑몰 서비스.
상품 카탈로그, 주문 처리, 재고 관리, 결제 연동 기능을 담당합니다.

### 기술 스택
- **Runtime**: Node.js 20 LTS
- **Language**: TypeScript 5.x
- **Frontend**: Next.js
- **Database**: PostgreSQL 16
- **ORM**: Prisma 5.x
- **Cache**: Redis
- **Test**: Vitest + Supertest

### 도메인
- **분류**: ecommerce (이커머스)
- **컴플라이언스**: 전자상거래법, 소비자보호법, 개인정보보호법

---

## 세션 시작 시 필수

```bash
# 1. 최신 상태 동기화
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
GIT_COMMON_DIR=$(git rev-parse --git-common-dir 2>/dev/null)
if [ "$GIT_DIR" != "$GIT_COMMON_DIR" ]; then
  # Worktree 모드 (Claude Squad 등)
  git fetch origin develop
  git merge origin/develop
else
  git checkout develop
  git pull origin develop
fi

# 2. 상태 요약 보기
/skill-status

# 3. 다음 작업 가져오기
/skill-plan
```

---

## 에이전트

### 활성화된 에이전트

| 에이전트 | 역할 | 트리거 |
|---------|------|--------|
| `@agent-pm` | 워크플로우 오케스트레이션 | 자연어 요청 자동 분석 |
| `@agent-backend` | 백엔드 API 개발 | "구현", "코드 작성" |
| `@agent-frontend` | UI/UX 구현 | "화면", "페이지" |
| `@agent-code-reviewer` | 5관점 코드 리뷰 | "리뷰해줘" |
| `@agent-qa` | 테스트 설계 및 검증 | "테스트", "검증" |

### 비활성화된 에이전트

- `agent-planner` (기획)
- `agent-docs` (문서화)
- `agent-db-designer` (DB 설계)
- `agent-devops` (인프라)

필요 시 `project.json`의 `agents.enabled`에 추가하여 활성화할 수 있습니다.

---

## 스킬

| 스킬 | 설명 | 자연어 |
|------|------|--------|
| `/skill-status` | 상태 확인 | "상태 확인해줘" |
| `/skill-backlog` | 백로그 조회 | "백로그 보여줘" |
| `/skill-feature` | 새 기능 기획 | "새 기능 기획해줘" |
| `/skill-plan` | 설계 + 스텝 계획 | "다음 작업 가져와줘" |
| `/skill-impl` | 구현 + PR 생성 | "개발 진행해줘" |
| `/skill-review-pr` | PR 리뷰 | "PR 리뷰해줘" |
| `/skill-merge-pr` | PR 머지 | "PR 머지해줘" |
| `/skill-docs` | 참고자료 | "주문 플로우 참고자료" |

---

## 개발 시 자동 참조 규칙

### 키워드 → 참고자료 매핑

| 키워드 | 참조 문서 |
|--------|----------|
| 주문, 결제, 구매, 장바구니 | `order-flow.md`, `payment-integration.md` |
| 재고, 품절, 입고, 출고 | `inventory.md` |
| 배송, 택배, 물류 | `shipping.md` |
| 쿠폰, 할인, 프로모션 | `promotion.md` |
| 상품, 카탈로그, 카테고리 | `product.md` |
| 회원, 로그인, 마이페이지 | `member.md` |

---

## 코드 리뷰 체크리스트

### 1. 컴플라이언스 (ecommerce 특화)
- [ ] 전자상거래법 준수 (사업자 정보, 청약철회)
- [ ] 소비자보호법 준수 (환불 규정)
- [ ] 개인정보보호법 준수 (배송지 암호화)

### 2. 도메인 로직
- [ ] 주문 상태 머신 전이 검증
- [ ] 재고 동시성 처리 (낙관적 락)
- [ ] 가격 계산 정수 처리 (원 단위)
- [ ] 멱등성 보장 (결제 요청)

### 3. 아키텍처
- [ ] 레이어 분리 (Controller → Service → Repository)
- [ ] 트랜잭션 범위 적정
- [ ] 에러 핸들링 미들웨어

### 4. 보안
- [ ] 배송지 정보 암호화
- [ ] SQL Injection 방지 (Prisma 파라미터 바인딩)
- [ ] 인증 미들웨어 적용

### 5. 테스트
- [ ] 커버리지 80% 이상
- [ ] 실패 케이스 테스트
- [ ] 동시성 테스트 (재고 경합)

---

## Git 브랜치 전략

```
main (운영)
  └── develop (개발 통합)
        └── feature/SHOP-XXX-stepN (스텝별 개발)
```

### 커밋 메시지 규칙
```
<type>: <description>

Types: feat, fix, refactor, docs, test, chore
예: feat: SHOP-001 Step 1 - 상품 CRUD API
```

---

## 에러 코드 체계

> 에러 코드는 `docs/requirements/SHOP-002-spec.md`에서 최초 정의.
> 주문 상태 머신 상세는 `.claude/domains/ecommerce/docs/order-flow.md` 참조.

### 외부 응답 (클라이언트에게 노출)

| 외부 코드 | HTTP | 설명 |
|----------|------|------|
| INSUFFICIENT_STOCK | 409 | 재고 부족 |
| INVALID_ORDER_TRANSITION | 422 | 무효 상태 전이 |
| ORDER_NOT_FOUND | 404 | 주문 미존재 |
| ORDER_NOT_CANCELLABLE | 422 | 취소 불가 상태 |
| INVALID_COUPON | 422 | 쿠폰 유효성 실패 |
| PRODUCT_NOT_FOUND | 404 | 상품 미존재 |

### 내부 에러 코드 (로그/모니터링용)

| 코드 | HTTP | 설명 |
|------|------|------|
| EC-031 | 409 | INSUFFICIENT_STOCK |
| EC-041 | 422 | INVALID_ORDER_TRANSITION |
| EC-042 | 404 | ORDER_NOT_FOUND |
| EC-043 | 422 | ORDER_NOT_CANCELLABLE |
| EC-051 | 422 | INVALID_COUPON |
| EC-061 | 404 | PRODUCT_NOT_FOUND |

---

## 테스트 규칙

### 커버리지 목표
- **라인 커버리지**: 80%+ (Vitest coverage 기준)
- 통합 테스트: 주요 플로우 100%
- **테스트 프레임워크**: Vitest + Supertest

### 필수 테스트 항목
- 상품 CRUD (성공 + 실패)
- 주문 상태 머신 전이 (정상 + 무효)
- 재고 예약/해제 정합성
- 동시 주문 재고 경합
- 가격 계산 + 쿠폰 적용
- E2E (주문 생성 → 결제 → 완료)
