# SHOP-001: 상품 카탈로그 API

## 개요
상품 정보를 관리하는 RESTful API. 상품 등록, 조회, 수정, 삭제 및 검색/필터링 기능 제공.

## 기능 요구사항

### 1. 상품 CRUD
- **등록**: 상품명, 가격, 설명, 카테고리, 재고 수량, 이미지 URL
- **조회**: 단건 조회 (ID), 목록 조회 (페이지네이션)
- **수정**: 부분 수정 (PATCH) 지원
- **삭제**: Soft delete (deletedAt)

### 2. 카테고리
- 1depth 카테고리 (추후 계층 구조 확장 예정)
- 카테고리별 상품 목록 필터링

### 3. 검색
- 상품명 키워드 검색 (LIKE)
- 가격 범위 필터
- 정렬: 가격순, 최신순, 인기순

### 4. 페이지네이션
- 커서 기반 페이지네이션
- 기본 페이지 크기: 20

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | /api/v1/products | 상품 목록 |
| GET | /api/v1/products/:id | 상품 상세 |
| POST | /api/v1/products | 상품 등록 |
| PATCH | /api/v1/products/:id | 상품 수정 |
| DELETE | /api/v1/products/:id | 상품 삭제 |
| GET | /api/v1/categories | 카테고리 목록 |

## 데이터 모델

### Product
| 필드 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| name | VARCHAR(200) | 상품명 |
| description | TEXT | 상품 설명 |
| price | DECIMAL(12,2) | 판매가 |
| categoryId | UUID | FK → Category |
| stockQuantity | INT | 재고 수량 |
| imageUrl | VARCHAR(500) | 대표 이미지 |
| status | ENUM | ACTIVE, INACTIVE, SOLD_OUT |
| createdAt | TIMESTAMP | 생성일 |
| updatedAt | TIMESTAMP | 수정일 |
| deletedAt | TIMESTAMP | 삭제일 (soft delete) |

## 비기능 요구사항
- 응답 시간: 200ms 이내 (P95)
- 테스트 커버리지: 80% 이상
