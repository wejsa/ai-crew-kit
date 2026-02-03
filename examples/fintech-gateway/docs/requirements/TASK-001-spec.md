# TASK-001: JWT 토큰 인증

## 개요

JWT(JSON Web Token) 기반 인증 시스템을 구현합니다.
Access Token과 Refresh Token을 사용한 인증 플로우를 지원합니다.

## 기능 요구사항

### FR-001: 로그인
- 이메일/비밀번호로 로그인
- 성공 시 Access Token + Refresh Token 발급
- 실패 시 적절한 에러 코드 반환

### FR-002: Token 발급
- Access Token: 1시간 만료
- Refresh Token: 7일 만료
- Token Family 기반 세션 관리

### FR-003: Token Rotation
- Refresh Token 사용 시 새로운 Token Pair 발급
- 기존 Refresh Token 무효화

### FR-004: Token Reuse Detection
- 이미 사용된 Refresh Token 재사용 감지
- 감지 시 해당 Token Family 전체 무효화
- 보안 이벤트 로깅

### FR-005: 로그아웃
- Access Token 블랙리스트 등록
- 해당 Token Family 전체 무효화

## 비기능 요구사항

### NFR-001: 보안
- 비밀키: 256bit 이상 (HS256)
- 토큰 평문 로깅 금지
- 민감정보 마스킹

### NFR-002: 성능
- 토큰 검증: < 10ms
- 로그인 처리: < 100ms

### NFR-003: 확장성
- 추후 Redis 분산 캐시 전환 고려
- 인터페이스 기반 설계

## API 명세

### POST /api/v1/auth/login
```json
// Request
{
  "email": "user@example.com",
  "password": "password123"
}

// Response (200 OK)
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
  "tokenType": "Bearer",
  "expiresIn": 3600
}

// Error Response (401 Unauthorized)
{
  "code": "PG-GW-012",
  "message": "Invalid credentials"
}
```

### POST /api/v1/auth/refresh
```json
// Request
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
}

// Response (200 OK)
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
  "tokenType": "Bearer",
  "expiresIn": 3600
}

// Error Response (401 Unauthorized) - Token Reuse Detection
{
  "code": "PG-GW-003",
  "message": "Token has been revoked"
}
```

### POST /api/v1/auth/logout
```json
// Request
Authorization: Bearer {accessToken}

// Response (200 OK)
{
  "message": "Successfully logged out"
}
```

## 도메인 참고자료

- `.claude/domains/fintech/docs/token-auth.md`
- `.claude/domains/fintech/docs/security-compliance.md`

## 수용 기준

- [ ] 로그인/로그아웃 정상 동작
- [ ] Token Rotation 동작 확인
- [ ] Token Reuse Detection 동작 확인
- [ ] 단위 테스트 커버리지 80% 이상
- [ ] PCI-DSS 컴플라이언스 체크 통과
- [ ] 토큰 로깅 보안 확인

## 스텝 분리 계획

### Step 1: JWT 서비스 인터페이스 및 모델 (~200 라인)
- `JwtToken.kt` (도메인 모델)
- `JwtService.kt` (서비스 인터페이스)
- `JwtProperties.kt` (설정)
- `TokenFamily.kt` (토큰 패밀리 모델)

### Step 2: JWT 서비스 구현 (~300 라인)
- `JwtServiceImpl.kt` (구현체)
- `JwtTokenProvider.kt` (토큰 생성/검증)
- `InMemoryTokenFamilyRepository.kt` (토큰 패밀리 저장소)

### Step 3: JWT 인증 필터 및 설정 (~250 라인)
- `JwtAuthenticationFilter.kt`
- `SecurityConfig.kt`
- `AuthController.kt`
- `AuthService.kt`
