# DB 설계 컨벤션

> **기본값**: MySQL 8.0+ · Flyway 마이그레이션. 다른 DB(PostgreSQL/MongoDB 등)나 도구(Liquibase/Alembic/Prisma migrate 등) 사용 시 `domain.json`의 `database` 필드만 변경하세요. Claude가 구문을 자동 치환합니다(예: `TINYINT(1)` ↔ `BOOLEAN`, `AUTO_INCREMENT` ↔ `IDENTITY`, `JSON` ↔ `JSONB`).
>
> **본 컨벤션의 정책은 DB·도구 무관 적용됩니다.** 팀 표준을 추가로 강제하려면 `CUSTOM_SECTION` 마커로 본 파일에 추가하세요 (→ `docs/customization.md`).

도메인별 데이터 모델(결제 테이블, 상품 테이블 등)은 해당 도메인 문서를 참조하세요.

## 테이블 네이밍

| 규칙 | 예시 |
|------|------|
| snake_case | `user_accounts`, `payment_transactions` |
| 복수형 | `users`, `orders`, `payments` |
| 접두사 금지 | ~~`tbl_users`~~ → `users` |
| 연결 테이블 | `{table1}_{table2}` (알파벳순) — `order_products` |

## 컬럼 네이밍

| 규칙 | 예시 |
|------|------|
| snake_case | `user_name`, `created_at` |
| PK | `id` |
| FK | `{참조테이블_단수형}_id` — `user_id`, `order_id` |
| Boolean | `is_` 접두사 — `is_active`, `is_deleted` |
| 날짜/시간 | `_at` 접미사 — `created_at`, `updated_at` |
| 금액 | 명확한 의미 표현 — `total_amount`, `discount_amount` |

## 필수 컬럼

| 컬럼 | 필수 | 용도 |
|------|:---:|------|
| `id` | ✅ | Primary Key (서로게이트) |
| `created_at` | ✅ | 생성 시각 (UTC) |
| `updated_at` | ✅ | 수정 시각 (UTC) |
| `deleted_at` | ❌ | Soft Delete 사용 시 |

> 시간은 UTC 저장. 금액은 부동소수점 금지(고정소수 정밀 타입 사용).

## 제약조건 네이밍

| 유형 | 패턴 | 예시 |
|------|------|------|
| Primary Key | `pk_{table}` | `pk_users` |
| Unique | `uk_{table}_{col}` | `uk_users_email` |
| Foreign Key | `fk_{table}_{col}` | `fk_orders_user_id` |
| Index | `idx_{table}_{col}` | `idx_users_created_at` |
| Check | `ck_{table}_{col}` | `ck_payments_amount` |

## 기본 정책

- **Soft Delete**: 감사 추적이 필요한 도메인(fintech/healthcare 등)은 `deleted_at` 사용. 모든 활성 조회에 `deleted_at IS NULL` 조건 필수.
- **낙관적 잠금**: 동시 수정 가능한 엔티티는 `version` 컬럼 + `WHERE version = ?` 패턴. affected rows = 0 시 충돌 → 재시도 또는 예외.
- **마이그레이션**: Flyway 표준 — 파일명 `V{N}__{snake_case_description}.sql`, 순차 증가, 한 번만 실행. 다른 도구 사용 시 동등 명명 규칙 유지.

## 무중단 마이그레이션 원칙

| 변경 유형 | 전략 |
|----------|------|
| 컬럼 추가 | NULL 허용 추가 → 데이터 채움 → NOT NULL 변경 |
| 컬럼 삭제 | 코드에서 참조 제거 → 다음 배포에서 컬럼 삭제 |
| 컬럼 타입 변경 | 새 컬럼 추가 → 데이터 마이그레이션 → 기존 컬럼 삭제 |
| 테이블 이름 변경 | 새 테이블 생성 → 동기화 → 기존 테이블 삭제 |
| 인덱스 추가 | DB가 지원하는 동시(non-blocking) 옵션 사용 |

> 위험한 DDL(대용량 테이블 ALTER, DROP, RENAME, FK 추가)은 영향 분석 + 롤백 계획 필수.
