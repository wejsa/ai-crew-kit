# DB 설계 컨벤션

모든 프로젝트에 적용되는 데이터베이스 설계 규칙입니다.
도메인별 데이터 모델(결제 테이블, 상품 테이블 등)은 해당 도메인 문서를 참조하세요.

## 테이블 네이밍

| 규칙 | 예시 |
|------|------|
| snake_case | `user_accounts`, `payment_transactions` |
| 복수형 | `users`, `orders`, `payments` |
| 접두사 금지 | ~~`tbl_users`~~ → `users` |
| 연결 테이블 | `{table1}_{table2}` (알파벳순) | `order_products` |

## 컬럼 네이밍

| 규칙 | 예시 |
|------|------|
| snake_case | `user_name`, `created_at` |
| PK | `id` |
| FK | `{참조테이블_단수형}_id` | `user_id`, `order_id` |
| Boolean | `is_` 접두사 | `is_active`, `is_deleted` |
| 날짜/시간 | `_at` 접미사 | `created_at`, `updated_at` |
| 금액 | 명확한 의미 표현 | `total_amount`, `discount_amount` |

## 필수 컬럼

모든 테이블에 포함되어야 하는 컬럼:

```sql
CREATE TABLE users (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    -- ... 비즈니스 컬럼 ...
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL      -- Soft Delete 사용 시
);
```

| 컬럼 | 타입 | 필수 | 설명 |
|------|------|------|------|
| id | BIGINT AUTO_INCREMENT | ✅ | 서로게이트 PK |
| created_at | TIMESTAMP | ✅ | 생성 시각 |
| updated_at | TIMESTAMP | ✅ | 수정 시각 |
| deleted_at | TIMESTAMP NULL | ❌ | Soft Delete 시 삭제 시각 |

## 데이터 타입 표준

| 용도 | 타입 | 비고 |
|------|------|------|
| 금액 | `DECIMAL(15,2)` | 부동소수점 사용 금지 |
| 시간 | `TIMESTAMP` (MySQL) / `TIMESTAMPTZ` (PostgreSQL) | UTC 저장 |
| UUID | `CHAR(36)` 또는 `BINARY(16)` | 외부 노출 식별자 |
| 상태값 | `VARCHAR(20)` | ENUM 타입 대신 문자열 권장 |
| 긴 텍스트 | `TEXT` | 4KB 초과 시 |
| JSON | `JSON` (MySQL) / `JSONB` (PostgreSQL) | 구조화되지 않은 데이터 |
| Boolean | `TINYINT(1)` (MySQL) / `BOOLEAN` (PostgreSQL) | |

## 제약조건 네이밍

| 유형 | 패턴 | 예시 |
|------|------|------|
| Primary Key | `pk_{table}` | `pk_users` |
| Unique | `uk_{table}_{col}` | `uk_users_email` |
| Foreign Key | `fk_{table}_{col}` | `fk_orders_user_id` |
| Index | `idx_{table}_{col}` | `idx_users_created_at` |
| Check | `ck_{table}_{col}` | `ck_payments_amount` |

## 인덱스 설계 원칙

| 원칙 | 설명 |
|------|------|
| 카디널리티 | 고유값이 많은 컬럼 우선 인덱싱 |
| 쿼리 패턴 | WHERE/JOIN/ORDER BY에 사용되는 컬럼 |
| 복합 인덱스 | 왼쪽 우선 원칙 (가장 선택적인 컬럼 먼저) |
| 커버링 인덱스 | SELECT 대상까지 포함하면 테이블 접근 불필요 |
| 과도한 인덱스 금지 | 쓰기 성능 저하 — 테이블당 5개 이내 권장 |

```sql
-- 복합 인덱스: 왼쪽 우선 원칙
CREATE INDEX idx_orders_user_status ON orders (user_id, status);
-- user_id 단독 조회: ✅ 사용됨
-- status 단독 조회: ❌ 사용 안 됨
-- user_id + status 조회: ✅ 사용됨

-- 커버링 인덱스
CREATE INDEX idx_orders_covering ON orders (user_id, status, created_at, total_amount);
-- SELECT status, total_amount FROM orders WHERE user_id = ? → 테이블 접근 불필요
```

## 마이그레이션 전략

Flyway 기반 버전 관리:

| 항목 | 규칙 |
|------|------|
| 파일명 | `V{N}__{description}.sql` |
| 번호 | 순차 증가 (`V1`, `V2`, ...) |
| 설명 | snake_case (`create_users_table`) |
| 실행 | 순서대로 한 번만 실행 |

```
db/migration/
├── V1__create_users_table.sql
├── V2__create_orders_table.sql
├── V3__add_users_phone_column.sql
└── V4__create_payments_table.sql
```

## 무중단 마이그레이션 원칙

서비스 중단 없이 스키마를 변경하기 위한 원칙:

| 변경 유형 | 전략 |
|----------|------|
| 컬럼 추가 | NULL 허용으로 추가 → 데이터 채움 → NOT NULL 변경 |
| 컬럼 삭제 | 코드에서 참조 제거 → 다음 배포에서 컬럼 삭제 |
| 컬럼 타입 변경 | 새 컬럼 추가 → 데이터 마이그레이션 → 기존 컬럼 삭제 |
| 테이블 이름 변경 | 새 테이블 생성 → 동기화 → 기존 테이블 삭제 |
| 인덱스 추가 | `CREATE INDEX CONCURRENTLY` (PostgreSQL) |

```sql
-- 예시: NOT NULL 컬럼 안전 추가
-- Step 1: NULL 허용으로 추가
ALTER TABLE users ADD COLUMN phone VARCHAR(20) NULL;

-- Step 2: 데이터 채움 (배치)
UPDATE users SET phone = '000-0000-0000' WHERE phone IS NULL;

-- Step 3: NOT NULL 변경
ALTER TABLE users MODIFY COLUMN phone VARCHAR(20) NOT NULL;
```

## Soft Delete 패턴

```sql
-- deleted_at NULL = 활성, NOT NULL = 삭제됨
SELECT * FROM users WHERE deleted_at IS NULL;

-- 인덱스 (MySQL)
CREATE INDEX idx_users_active ON users (deleted_at, created_at);

-- 부분 인덱스 (PostgreSQL)
CREATE INDEX idx_users_active ON users (created_at) WHERE deleted_at IS NULL;
```

## 낙관적 잠금

동시 수정 충돌 방지를 위한 `version` 컬럼 사용:

```sql
ALTER TABLE orders ADD COLUMN version INT NOT NULL DEFAULT 0;

-- 업데이트 시 버전 체크
UPDATE orders
SET status = 'COMPLETED', version = version + 1
WHERE id = ? AND version = ?;
-- affected rows = 0 이면 충돌 발생 → 재시도 또는 예외
```
