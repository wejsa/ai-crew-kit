# TASK-001: JWT 토큰 인증

## 개요

JWT(JSON Web Token) 기반 인증 시스템을 구현합니다.
Access Token과 Refresh Token을 사용한 인증 플로우를 지원합니다.

## 의존성

### Spring Cloud BOM (WebFlux 기반)
```kotlin
// build.gradle.kts
plugins {
    kotlin("jvm") version "2.0.21"
    kotlin("plugin.spring") version "2.0.21"
    id("org.springframework.boot") version "3.3.5"
    id("io.spring.dependency-management") version "1.1.6"
}

dependencyManagement {
    imports {
        mavenBom("org.springframework.cloud:spring-cloud-dependencies:2024.0.0")
    }
}

dependencies {
    // Gateway (WebFlux 기반)
    implementation("org.springframework.cloud:spring-cloud-starter-gateway")
    implementation("org.springframework.boot:spring-boot-starter-webflux")

    // Security
    implementation("org.springframework.boot:spring-boot-starter-security")

    // JWT
    implementation("io.jsonwebtoken:jjwt-api:0.12.6")
    runtimeOnly("io.jsonwebtoken:jjwt-impl:0.12.6")
    runtimeOnly("io.jsonwebtoken:jjwt-jackson:0.12.6")

    // Test
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testImplementation("io.projectreactor:reactor-test")
    testImplementation("io.mockk:mockk:1.13.13")
    testImplementation("org.springframework.security:spring-security-test")
}
```

> **주의**: Spring Cloud Gateway 4.1.x는 **WebFlux 기반**입니다. 서블릿 코드(`@Controller`, `MockMvc`, `HttpServletRequest`) 혼입을 금지합니다. `WebFilter`, `SecurityWebFilterChain`, `WebTestClient`를 사용하세요.

## 기능 요구사항

### FR-001: 로그인
- 이메일/비밀번호로 로그인
- `InMemoryUserRepository`에서 사용자 조회
- `PasswordEncoder`(bcrypt, cost 12)로 비밀번호 검증
- 성공 시 Access Token + Refresh Token 발급
- 실패 시 적절한 에러 코드 반환

### FR-002: Token 발급
- Access Token: 1시간 만료
- Refresh Token: 7일 만료
- Token Family 기반 세션 관리

### FR-003: Token Rotation
- Refresh Token 사용 시 새로운 Token Pair 발급
- 기존 Refresh Token 무효화
- `ConcurrentHashMap.compute()`로 원자적 버전 갱신 (Race Condition 방어)

### FR-004: Token Reuse Detection
- 이미 사용된 Refresh Token 재사용 감지
- 감지 시 해당 Token Family 전체 무효화
- 보안 이벤트 로깅

### FR-005: 로그아웃
- Access Token 블랙리스트 등록 (`ConcurrentHashMap.newKeySet()` 기반, 스레드 안전)
- 해당 Token Family 전체 무효화
- 블랙리스트 TTL: 데모에서는 미적용 (Production Readiness Gaps #9 참조)

## 비기능 요구사항

### NFR-001: 보안
- 비밀키: 256bit 이상 (HS256), `${JWT_SECRET}` 환경변수 (기본값 없이)
- 토큰 평문 로깅 금지 — Logback eyJ 패턴 마스킹 필터 적용
- 민감정보 마스킹 — 래퍼 타입으로 컴파일 타임 보안

### NFR-002: 성능
- 토큰 검증: < 10ms
- 로그인 처리: < 100ms

### NFR-003: 확장성
- 추후 Redis 분산 캐시 전환 고려
- 인터페이스 기반 설계

### NFR-004: 에러 응답 보안
- 외부 응답은 3단계로 통합: TOKEN_MISSING / TOKEN_EXPIRED / TOKEN_INVALID
- 내부 로그에만 세분화된 에러코드 사용 (정보 유출 방지)

## 구성 요소

### 도메인 모델 (래퍼 타입)
```kotlin
@JvmInline
value class AccessToken(val value: String) {
    override fun toString() = "[MASKED]"
}

@JvmInline
value class RefreshToken(val value: String) {
    override fun toString() = "[MASKED]"
}

data class TokenPair(val accessToken: AccessToken, val refreshToken: RefreshToken)
```

### 사용자 저장소 (인터페이스 + 구현)
```kotlin
// 인터페이스 (NFR-003 확장성: 추후 RDB 전환 시 구현체만 교체)
interface UserRepository {
    suspend fun findByEmail(email: String): User?
    suspend fun findById(id: String): User?
}

@Repository
class InMemoryUserRepository : UserRepository {
    private val users = ConcurrentHashMap<String, User>()

    init {
        // 데모 사용자 (프로덕션에서는 DB 전환)
        users["admin@example.com"] = User(
            id = "user-001",
            email = "admin@example.com",
            passwordHash = passwordEncoder.encode("admin1234"),
            roles = listOf("MERCHANT_ADMIN"),
            merchantId = "MID001"
        )
    }

    override suspend fun findByEmail(email: String): User? = users[email]
    override suspend fun findById(id: String): User? = users.values.find { it.id == id }
}
```

### 비밀번호 검증
```kotlin
@Bean
fun passwordEncoder(): PasswordEncoder = BCryptPasswordEncoder(12)
```

### 글로벌 예외 처리 (WebFlux)
```kotlin
@RestControllerAdvice
class GlobalExceptionHandler {
    @ExceptionHandler(TokenException::class)
    fun handleTokenException(ex: TokenException): ResponseEntity<ErrorResponse> {
        // 외부 에러 매핑 (내부 코드 노출 금지)
        val externalCode = when (ex) {
            is TokenException.Missing -> "TOKEN_MISSING"
            is TokenException.Expired -> "TOKEN_EXPIRED"
            is TokenException.InvalidCredentials -> "INVALID_CREDENTIALS"
            else -> "TOKEN_INVALID"  // FORMAT, SIGNATURE, REUSED 등 통합
        }
        return ResponseEntity.status(ex.httpStatus).body(ErrorResponse(externalCode, ex.message))
    }
}
```

### Logback 토큰 마스킹 필터
```xml
<!-- logback-spring.xml -->
<configuration>
    <conversionRule conversionWord="maskedMsg"
        converterClass="com.example.gateway.logging.TokenMaskingConverter" />
    <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %maskedMsg%n</pattern>
        </encoder>
    </appender>
</configuration>
```
```kotlin
// eyJ 패턴(JWT 토큰 시작) 마스킹
class TokenMaskingConverter : ClassicConverter() {
    private val tokenPattern = Regex("eyJ[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+")
    override fun convert(event: ILoggingEvent): String =
        tokenPattern.replace(event.formattedMessage, "[JWT_MASKED]")
}
```

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
  "code": "INVALID_CREDENTIALS",
  "message": "Invalid credentials"
}
// 내부 로그에만 PG-GW-012 기록 (외부 노출 금지)
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
  "code": "TOKEN_INVALID",
  "message": "Token has been revoked"
}
// 내부 로그에만 PG-GW-016 기록 (외부 노출 금지)
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

## 도메인 참고자료 (SSOT)

> **SSOT 원칙**: 아래 도메인 문서가 JWT 사양/에러코드의 진실점(Single Source of Truth)입니다.
> 본 스펙 문서의 API 명세/에러코드는 구현 가이드용 요약이며, 불일치 시 도메인 문서를 우선합니다.

- `.claude/domains/fintech/docs/token-auth.md` — JWT 토큰 구조, Token Rotation, 보안 규칙
- `.claude/domains/fintech/docs/error-handling.md` — 에러 코드 전체 정의 (SSOT)
- `.claude/domains/fintech/docs/security-compliance.md` — PCI-DSS, 암호화 규칙

## 수용 기준

- [ ] 로그인/로그아웃 정상 동작
- [ ] Token Rotation 동작 확인
- [ ] Token Reuse Detection 동작 확인
- [ ] **브랜치 커버리지** 80% 이상 (Jacoco 리포트)
- [ ] PCI-DSS 컴플라이언스 체크 통과
- [ ] 토큰 로깅 보안 확인 (eyJ 마스킹)
- [ ] 래퍼 타입 toString() → "[MASKED]" 확인
- [ ] 외부 에러 응답 3단계 통합 확인

## 테스트 명세 (12건 이상)

### 단위 테스트 (WebTestClient 사용)
| # | 테스트 | 설명 |
|---|--------|------|
| 1 | 로그인 성공 | 유효한 이메일/비밀번호 → AT + RT 발급 |
| 2 | 로그인 실패 — 잘못된 비밀번호 | PG-GW-012 에러 |
| 3 | 로그인 실패 — 미존재 사용자 | PG-GW-012 에러 (동일 응답, 열거 공격 방지) |
| 4 | AT 검증 성공 | 유효한 AT로 보호된 엔드포인트 접근 |
| 5 | AT 검증 실패 — 만료 | PG-GW-003 에러 |
| 6 | AT 검증 실패 — 잘못된 서명 | PG-GW-004 에러 |
| 7 | Token Rotation 성공 | RT로 새 AT + RT 발급, 기존 RT 무효화 |
| 8 | Token Reuse Detection | 이미 사용된 RT 재사용 → Family 전체 무효화 |
| 9 | 로그아웃 | AT 블랙리스트 등록 → 이후 사용 불가 |

### 동시성 테스트
| # | 테스트 | 설명 |
|---|--------|------|
| 10 | 동시 Token Rotation | 2 스레드 동시 rotation → 하나만 성공, 다른 하나 Reuse Detection |

### 보안 테스트
| # | 테스트 | 설명 |
|---|--------|------|
| 11 | 토큰 미로깅 검증 | 로그 출력에 eyJ 패턴이 없는지 확인 |

### 통합 테스트 (E2E)
| # | 테스트 | 설명 |
|---|--------|------|
| 12 | 로그인 → 갱신 → 로그아웃 | 전체 인증 플로우 E2E 검증 |

## 스텝 분리 계획

### Step 1: 스캐폴딩 + JWT 서비스 인터페이스/모델/구현 (~450 라인)
- `build.gradle.kts` (프로젝트 스캐폴딩 + 의존성)
- `application.yml` (설정)
- `JwtToken.kt` (도메인 모델, 래퍼 타입)
- `JwtService.kt` (서비스 인터페이스)
- `JwtProperties.kt` (설정)
- `TokenFamily.kt` (토큰 패밀리 모델)
- `JwtServiceImpl.kt` (구현체)
- `JwtTokenProvider.kt` (토큰 생성/검증)
- `InMemoryTokenFamilyRepository.kt` (토큰 패밀리 저장소, CAS 패턴)
- `UserRepository.kt` (사용자 저장소 인터페이스)
- `InMemoryUserRepository.kt` (사용자 저장소 구현체)

### Step 2: JWT 인증 필터, 컨트롤러, 설정 (~300 라인)
- `JwtAuthenticationFilter.kt` (WebFlux WebFilter)
- `SecurityConfig.kt` (SecurityWebFilterChain)
- `AuthController.kt`
- `AuthService.kt`
- `GlobalExceptionHandler.kt` (외부 3단계 에러 매핑)
- `TokenMaskingConverter.kt` (Logback eyJ 마스킹)
- `logback-spring.xml`
- `PasswordEncoderConfig.kt` (BCrypt cost 12)
- 테스트 12건

## Production Readiness Gaps

> 이 데모 구현은 프레임워크 효용 증명이 목적입니다. 프로덕션 배포 시 아래 항목을 반드시 해결하세요.

| # | 항목 | 데모 | 프로덕션 요구사항 |
|---|------|------|----------------|
| 1 | 토큰 저장소 | InMemory (`ConcurrentHashMap`) | Redis Cluster (TTL 기반 자동 정리) |
| 2 | 사용자 저장소 | InMemory (하드코딩) | RDB + Spring Data (암호화 저장) |
| 3 | JWT 알고리즘 | HS256 (대칭키) | RS256/ES256 (비대칭키, 키 로테이션) |
| 4 | 비밀키 관리 | 환경변수 | Vault / AWS KMS / Azure Key Vault |
| 5 | HTTPS | 미적용 | TLS 1.3 필수 (Let's Encrypt / ALB) |
| 6 | Refresh Token 전달 | JSON body | HttpOnly + Secure + SameSite Cookie |
| 7 | Rate Limiting | 미구현 | Token Bucket / Redis 기반 |
| 8 | 감사 로그 | 콘솔 로그 | 구조화 로그 + ELK/CloudWatch |
| 9 | 블랙리스트 TTL | 미적용 (메모리 누수) | AT 만료 시간 기준 자동 정리 |
