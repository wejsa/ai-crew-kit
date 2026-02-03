# 주문 플로우

## 개요

이커머스 주문의 전체 라이프사이클을 설명합니다.

## 주문 상태 머신

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  CART → CHECKOUT → PAYMENT_PENDING → PAID → PREPARING       │
│          │              │            │          │           │
│          ▼              ▼            ▼          ▼           │
│       CANCELLED     CANCELLED   CANCELLED   SHIPPING        │
│                                               │              │
│                                               ▼              │
│                                           DELIVERED          │
│                                               │              │
│                                               ▼              │
│                                     COMPLETED / RETURN       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 상태 정의

| 상태 | 설명 | 다음 상태 |
|------|------|----------|
| CART | 장바구니 | CHECKOUT |
| CHECKOUT | 주문서 작성 | PAYMENT_PENDING, CANCELLED |
| PAYMENT_PENDING | 결제 대기 | PAID, CANCELLED |
| PAID | 결제 완료 | PREPARING, CANCELLED |
| PREPARING | 상품 준비 | SHIPPING, CANCELLED |
| SHIPPING | 배송 중 | DELIVERED |
| DELIVERED | 배송 완료 | COMPLETED, RETURN |
| COMPLETED | 주문 완료 | - |
| CANCELLED | 주문 취소 | - |
| RETURN | 반품/교환 | COMPLETED, REFUNDED |

## 주문 생성 플로우

### 1. 장바구니 → 주문서

```kotlin
@Transactional
suspend fun createOrder(cartId: String, userId: String): Order {
    // 1. 장바구니 조회
    val cart = cartService.getCart(cartId)

    // 2. 재고 확인 및 예약
    val reservations = cart.items.map { item ->
        inventoryService.reserve(item.productId, item.quantity)
    }

    // 3. 주문 생성
    val order = Order(
        userId = userId,
        items = cart.items.map { it.toOrderItem() },
        status = OrderStatus.CHECKOUT,
        reservations = reservations
    )

    // 4. 가격 계산 (할인 적용)
    val pricing = pricingService.calculate(order)

    return orderRepository.save(order.copy(pricing = pricing))
}
```

### 2. 결제 처리

```kotlin
@Transactional
suspend fun processPayment(orderId: String, paymentInfo: PaymentInfo): Order {
    val order = orderRepository.findById(orderId)
        ?: throw OrderNotFoundException()

    // 1. 결제 요청
    val paymentResult = paymentService.process(
        orderId = orderId,
        amount = order.pricing.finalAmount,
        paymentInfo = paymentInfo
    )

    // 2. 결제 성공 시 상태 변경
    if (paymentResult.success) {
        order.status = OrderStatus.PAID
        // 재고 예약 → 확정
        inventoryService.confirm(order.reservations)
    } else {
        order.status = OrderStatus.CANCELLED
        // 재고 예약 해제
        inventoryService.release(order.reservations)
    }

    return orderRepository.save(order)
}
```

## 주문 취소

### 취소 가능 조건

| 상태 | 취소 가능 | 처리 |
|------|----------|------|
| CHECKOUT | ✅ | 예약 해제 |
| PAYMENT_PENDING | ✅ | 예약 해제 |
| PAID | ✅ | 결제 취소 + 재고 복원 |
| PREPARING | ⚠️ | 출고 전까지 가능 |
| SHIPPING | ❌ | 반품으로 처리 |
| DELIVERED | ❌ | 반품으로 처리 |

### 취소 처리

```kotlin
@Transactional
suspend fun cancelOrder(orderId: String, reason: String): Order {
    val order = orderRepository.findById(orderId)
        ?: throw OrderNotFoundException()

    require(order.canCancel()) { "취소할 수 없는 주문 상태입니다" }

    // 1. 결제 취소 (결제 완료 상태인 경우)
    if (order.status == OrderStatus.PAID) {
        paymentService.cancel(order.paymentId)
    }

    // 2. 재고 복원
    inventoryService.restore(order.items)

    // 3. 상태 변경
    order.status = OrderStatus.CANCELLED
    order.cancelledAt = Instant.now()
    order.cancelReason = reason

    return orderRepository.save(order)
}
```

## 주문 항목 구조

```kotlin
data class Order(
    val id: String,
    val userId: String,
    val items: List<OrderItem>,
    val shippingAddress: Address,
    val pricing: OrderPricing,
    var status: OrderStatus,
    val createdAt: Instant,
    var paidAt: Instant? = null,
    var shippedAt: Instant? = null,
    var deliveredAt: Instant? = null
)

data class OrderItem(
    val productId: String,
    val productName: String,
    val optionId: String?,
    val quantity: Int,
    val unitPrice: BigDecimal,
    val totalPrice: BigDecimal
)

data class OrderPricing(
    val itemsTotal: BigDecimal,
    val shippingFee: BigDecimal,
    val discountAmount: BigDecimal,
    val couponDiscount: BigDecimal,
    val finalAmount: BigDecimal
)
```

## 이벤트 발행

주문 상태 변경 시 이벤트 발행:

```kotlin
sealed class OrderEvent {
    data class Created(val order: Order) : OrderEvent()
    data class Paid(val orderId: String, val paidAt: Instant) : OrderEvent()
    data class Shipped(val orderId: String, val trackingNumber: String) : OrderEvent()
    data class Delivered(val orderId: String) : OrderEvent()
    data class Cancelled(val orderId: String, val reason: String) : OrderEvent()
}
```

## 참고사항

- 재고 예약 → 확정 2단계 처리로 동시성 이슈 방지
- 결제 실패 시 반드시 예약 해제
- 주문 취소 시 결제 취소 먼저 처리
- 모든 상태 변경에 이력 기록
