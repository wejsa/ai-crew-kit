# SHOP-002: 주문 처리 시스템

## 개요

주문 생성부터 완료까지의 전체 라이프사이클을 관리하는 시스템.
주문 상태 머신, 재고 예약/차감, 가격 계산, 전자상거래법 준수를 포함합니다.

### 의존성

- SHOP-001 (상품 카탈로그 API) — 상품 조회, 가격, 재고 데이터 참조

### 기술 스택

```json
{
  "runtime": "Node.js 20 LTS",
  "language": "TypeScript 5.x",
  "framework": "Express 또는 Fastify",
  "database": "PostgreSQL 16",
  "orm": "Prisma 5.x",
  "test": "Vitest + Supertest",
  "validation": "Zod"
}
```

---

## 기능 요구사항

### FR-001: 주문 생성

- 장바구니 상품을 주문으로 전환
- 주문 시점 가격 스냅샷 저장 (가격 변동 대응)
- 재고 예약 (2단계 패턴: RESERVE → CONFIRM/RELEASE)
- 배송지 정보 입력

### FR-002: 주문 상태 머신

11가지 상태와 허용된 전이만 가능:

```
CART → CHECKOUT → PAYMENT_PENDING → PAID → PREPARING → SHIPPING → DELIVERED → COMPLETED
                                     ↓                      ↓
                                  CANCELLED        RETURN → REFUNDED
```

| 상태 | 설명 | 허용 전이 |
|------|------|----------|
| CART | 장바구니 | CHECKOUT |
| CHECKOUT | 주문서 작성 | PAYMENT_PENDING, CANCELLED |
| PAYMENT_PENDING | 결제 대기 | PAID, CANCELLED |
| PAID | 결제 완료 | PREPARING, CANCELLED |
| PREPARING | 상품 준비 | SHIPPING, CANCELLED |
| SHIPPING | 배송 중 | DELIVERED |
| DELIVERED | 배송 완료 | COMPLETED, RETURN |
| COMPLETED | 주문 완료 | — |
| CANCELLED | 주문 취소 | — |
| RETURN | 반품/교환 | COMPLETED, REFUNDED |
| REFUNDED | 환불 완료 | — |

무효 전이 시도 시: `EC-041 INVALID_ORDER_TRANSITION` 에러 반환.

### FR-003: 재고 관리

- **예약**: 주문 생성 시 가용 재고에서 차감
- **확정**: 결제 완료 시 예약 → 출고 대기
- **해제**: 주문 취소 시 가용 재고 복원
- **음수 방지**: 재고 < 0 불가 (DB CHECK 제약)
- **동시성**: 낙관적 락 (`version` 필드) + 재시도 3회

```typescript
// 재고 예약 — 낙관적 락
async function reserveStock(productId: string, quantity: number): Promise<void> {
  const inventory = await prisma.inventory.findUnique({ where: { productId } })
  if (inventory.availableStock < quantity) throw new InsufficientStockError()

  const updated = await prisma.inventory.updateMany({
    where: { productId, version: inventory.version },
    data: {
      reservedStock: { increment: quantity },
      version: { increment: 1 }
    }
  })
  if (updated.count === 0) throw new OptimisticLockError()
}
```

### FR-004: 가격 계산

- 상품 단가 × 수량 = 항목 소계
- 쿠폰/프로모션 할인 적용
- 배송비 계산 (무료배송 조건 확인)
- 최종 결제 금액 = 항목 합계 - 할인 + 배송비

```typescript
interface OrderPricing {
  itemsTotal: number      // 상품 합계 (정수, 원 단위)
  shippingFee: number     // 배송비
  discountAmount: number  // 할인 금액
  couponDiscount: number  // 쿠폰 할인
  finalAmount: number     // 최종 결제 금액 (0원 미만 불가)
}

// Zod 검증 스키마 — 모든 금액 필드에 정수 강제
const orderPricingSchema = z.object({
  itemsTotal: z.number().int().nonnegative(),
  shippingFee: z.number().int().nonnegative(),
  discountAmount: z.number().int().nonnegative(),
  couponDiscount: z.number().int().nonnegative(),
  finalAmount: z.number().int().nonnegative(),
})
```

> **주의**: 금액 계산은 정수(원 단위)로 처리. 소수점 절사. DB 컬럼은 `DECIMAL(12,0)`.
> TypeScript `number`는 부동소수점이므로, **Zod `z.number().int()` 검증 필수**.
> 최종 금액: `Math.max(0, itemsTotal - discountAmount - couponDiscount + shippingFee)`

### FR-005: 주문 취소

| 현재 상태 | 취소 가능 | 처리 |
|----------|----------|------|
| CHECKOUT | ✅ | 재고 예약 해제 |
| PAYMENT_PENDING | ✅ | 재고 예약 해제 |
| PAID | ✅ | 결제 취소 요청 + 재고 복원 |
| PREPARING | ⚠️ 조건부 | 출고 전까지만 가능 |
| SHIPPING 이후 | ❌ | 반품으로 처리 |

---

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | /api/v1/orders | 주문 생성 |
| GET | /api/v1/orders/:id | 주문 상세 |
| GET | /api/v1/orders | 내 주문 목록 |
| PATCH | /api/v1/orders/:id/status | 상태 변경 |
| POST | /api/v1/orders/:id/cancel | 주문 취소 |

### 주문 생성 요청

```json
{
  "items": [
    { "productId": "uuid", "quantity": 2 }
  ],
  "shippingAddress": {
    "zipCode": "06100",
    "address1": "서울시 강남구",
    "address2": "101호",
    "receiverName": "홍길동",
    "receiverPhone": "010-1234-5678"
  },
  "couponCode": "WELCOME10"
}
```

### 주문 생성 응답

```json
{
  "id": "order-uuid",
  "status": "PAYMENT_PENDING",
  "items": [...],
  "pricing": {
    "itemsTotal": 50000,
    "shippingFee": 3000,
    "discountAmount": 0,
    "couponDiscount": 5000,
    "finalAmount": 48000
  },
  "createdAt": "2026-03-10T12:00:00Z"
}
```

### 에러 응답

```json
{
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "일부 상품의 재고가 부족합니다.",
    "timestamp": "2026-03-10T12:00:00Z"
  }
}
```

> **보안**: 외부 응답에 실제 재고 수량을 노출하지 않음 (재고 정보 수집 공격 방지). 내부 로그에만 상세 기록.

> 내부 로그에만 상세 에러 코드(EC-0XX) 기록. 외부 응답은 범용 코드 사용.

---

## 데이터 모델

### Order

| 필드 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| userId | UUID | 주문자 |
| status | ENUM | 주문 상태 (11가지) |
| shippingAddress | JSONB | 배송지 정보 |
| pricing | JSONB | 가격 정보 (OrderPricing) |
| couponCode | VARCHAR(50) | 적용된 쿠폰 |
| cancelReason | TEXT | 취소 사유 |
| version | INT | 낙관적 락 |
| createdAt | TIMESTAMP | 주문 생성일 |
| updatedAt | TIMESTAMP | 최종 수정일 |

### OrderItem

| 필드 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| orderId | UUID | FK → Order |
| productId | UUID | FK → Product |
| productName | VARCHAR(200) | 주문 시점 상품명 (스냅샷) |
| unitPrice | DECIMAL(12,0) | 주문 시점 단가 (스냅샷) |
| quantity | INT | 수량 |
| totalPrice | DECIMAL(12,0) | 소계 |

---

## 비기능 요구사항

### NFR-001: 동시성

- 재고 예약: 낙관적 락 + 3회 재시도 (OptimisticLockError 시)
- 주문 상태 변경: 낙관적 락 (version 필드)
- 동시 주문 시 재고 부족 → 후순위 주문에 `INSUFFICIENT_STOCK` 반환

### NFR-002: 성능

- 주문 생성: 500ms 이내 (P95)
- 주문 조회: 200ms 이내 (P95)
- 주문 목록: 커서 기반 페이지네이션 (SHOP-001과 동일 패턴)

### NFR-003: 컴플라이언스

- **전자상거래법**: 주문 내역 표시, 청약철회 7일 보장
- **소비자보호법**: 취소/환불 규정 준수
- **개인정보보호법**: 배송지 정보 암호화 저장

### NFR-004: 에러 코드

> 아래 에러 코드는 이 명세에서 최초 정의합니다.
> 주문 상태 머신 상세는 `.claude/domains/ecommerce/docs/order-flow.md` 참조.

| 외부 코드 | HTTP | 내부 코드 | 설명 |
|----------|------|----------|------|
| INSUFFICIENT_STOCK | 409 | EC-031 | 재고 부족 |
| INVALID_ORDER_TRANSITION | 422 | EC-041 | 무효 상태 전이 |
| ORDER_NOT_FOUND | 404 | EC-042 | 주문 미존재 |
| ORDER_NOT_CANCELLABLE | 422 | EC-043 | 취소 불가 상태 |
| INVALID_COUPON | 422 | EC-051 | 쿠폰 유효성 실패 |

---

## 스텝 분리 계획

### Step 1: 주문 CRUD + 상태 머신 (~400줄)

**구현 범위:**
- Order, OrderItem 엔티티 + Prisma 스키마
- 주문 상태 머신 (전이 검증 로직)
- 주문 생성 API (재고 예약 포함)
- 주문 조회/목록 API
- 주문 취소 API

**산출물:**
- `src/orders/order.model.ts` — 엔티티, 상태 ENUM
- `src/orders/order-state-machine.ts` — 상태 전이 검증
- `src/orders/order.service.ts` — 비즈니스 로직
- `src/orders/order.controller.ts` — API 라우트
- `prisma/migrations/` — Order, OrderItem 테이블

### Step 2: 가격 계산 + 테스트 (~350줄)

**구현 범위:**
- 가격 계산 로직 (할인, 배송비, 쿠폰)
- 쿠폰 유효성 검증
- 테스트 15건
- 에러 핸들링 미들웨어

**산출물:**
- `src/orders/pricing.service.ts` — 가격 계산
- `src/orders/coupon.service.ts` — 쿠폰 검증
- `src/middleware/error-handler.ts` — 에러 핸들링
- `tests/orders/` — 테스트 파일

---

## 테스트 명세 (15건)

| # | 테스트 | 유형 |
|---|--------|------|
| 1 | 주문 생성 성공 (재고 예약 확인) | 기본 |
| 2 | 주문 생성 실패 — 재고 부족 | 네거티브 |
| 3 | 상태 전이 성공 (PAYMENT_PENDING → PAID) | 기본 |
| 4 | 상태 전이 실패 — 무효 전이 (SHIPPING → CHECKOUT) | 네거티브 |
| 5 | **상태 전이 매트릭스 전수 검증** (파라미터화 테스트) | 핵심 |
| 6 | 주문 취소 — 결제 전 (재고 복원 확인) | 핵심 |
| 7 | 주문 취소 — 결제 후 (환불 트리거 확인) | 핵심 |
| 8 | 주문 취소 실패 — 배송 중 | 네거티브 |
| 9 | 가격 계산 — 쿠폰 적용 | 기본 |
| 10 | **가격 스냅샷 불변** — 주문 후 상품 가격 변경 시 주문 금액 불변 | 핵심 |
| 11 | **경계값** — 수량 0/음수, 빈 장바구니, 재고 정확 소진 | 경계값 |
| 12 | **동시 주문 — 2 요청 동시 재고 예약** | 동시성 |
| 13 | **동시 쿠폰 사용 — 2 요청 동시 적용 시 1건만 성공** | 동시성 |
| 14 | **최종 금액 음수 방지** — 할인 > 상품가 시 finalAmount == 0 | 경계값 |
| 15 | **E2E — 주문 생성 → 결제 → 배송 → 완료** | 통합 |

### 수용 기준

- [ ] 주문 상태 머신 11가지 상태 전이 정상 동작
- [ ] 재고 예약/확정/해제 정합성 검증
- [ ] 동시 주문 시 재고 초과 판매 방지
- [ ] 가격 스냅샷 — 주문 후 상품 가격 변경 시 주문 금액 불변
- [ ] 전자상거래법 — 청약철회 7일 보장
- [ ] 테스트 커버리지 80% 이상

---

## 도메인 참고자료 (SSOT)

| 문서 | 내용 |
|------|------|
| `.claude/domains/ecommerce/docs/order-flow.md` | 주문 상태 머신, 이벤트 발행 |
| `.claude/domains/ecommerce/docs/inventory.md` | 재고 유형, 2단계 예약 패턴, 동시성 |
| `.claude/domains/ecommerce/docs/promotion.md` | 쿠폰 구조, 할인 계산, 중복 적용 규칙 |
| `.claude/domains/ecommerce/docs/payment-integration.md` | 결제 연동 (Step 2 참조) |

---

## Production Readiness Gaps

이 데모는 단일 인스턴스 기반입니다. 프로덕션 전환 시 다음 항목 보강 필요:

| # | 항목 | 데모 | 프로덕션 |
|---|------|------|----------|
| 1 | 세션/인증 | `X-User-Id` 헤더 주입 | JWT 인증 + 소유자 검증 |
| 2 | 결제 연동 | Mock 처리 | PG사 실제 연동 + 금액 검증 |
| 3 | 결제 멱등성 | 미구현 | idempotency key 기반 이중 결제 방지 |
| 4 | 이벤트 발행 | 동기 호출 | RabbitMQ/Kafka |
| 5 | 배송 연동 | Mock 처리 | 택배사 API |
| 6 | 동시성 | 낙관적 락 | 분산 락 (Redis) |
| 7 | 배송지 암호화 | 평문 JSONB | AES-256-GCM 암호화 저장 |
| 8 | 개인정보 동의 | 미구현 | 수집·이용 동의 + 제3자 제공 동의 |
| 9 | 에스크로 | 미구현 | 10만원+ 거래 시 에스크로 선택권 |
| 10 | 모니터링 | 콘솔 로그 | ELK/Datadog |
| 11 | 배송비 | 고정 3,000원 | 택배사별 실시간 계산 |
