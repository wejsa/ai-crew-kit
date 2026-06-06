# 커스터마이징 가이드

> [← README로 돌아가기](../README.md)

## Layered Override

설정은 다음 3층 순서로 적용되며, 상위가 하위를 오버라이드합니다.

```
CLAUDE.md — CUSTOM_SECTION                ← 최우선 (프로젝트 고유 규칙)
    ↑
project.json (사용자 설정)                ← 스택·컨벤션 설정값
    ↑
domains/_base/                            ← 공통 기본값 (conventions·checklists)
```

**체크리스트 로딩:**
1. `_base/checklists/` — 모든 프로젝트 공통 체크리스트
2. `/skill-review-pr` 실행 시 자동 적용

**conventions 로딩:**
- `_base/conventions/*.md` — API 설계, DB, 에러 처리, 보안, 테스트 등 공통 컨벤션
- `project.json`의 `conventions` 필드로 일부 동작 오버라이드 가능
- CUSTOM_SECTION에 추가 규칙 작성 시 최우선 적용

---

## 디렉토리 구조

```
.claude/
├── domains/
│   ├── _base/
│   │   ├── conventions/        # 공통 컨벤션
│   │   │   ├── api-design.md
│   │   │   ├── database.md
│   │   │   ├── error-handling.md
│   │   │   ├── security.md
│   │   │   ├── testing.md
│   │   │   └── ...
│   │   ├── checklists/         # 공통 리뷰 체크리스트
│   │   ├── health/             # 헬스체크 정의
│   │   └── templates/          # 공통 템플릿
│   └── general/                # 범용 기본 문서 (getting-started 등)
└── skills/
    ├── skill-*/                # 내장 스킬
    └── custom/                 # 커스텀 스킬 (skill-create로 생성)
```

---

## 공통 컨벤션 및 체크리스트 커스터마이징

### 방법 1: CUSTOM_SECTION에 추가 (권장)

`CLAUDE.md`의 `<!-- CUSTOM_SECTION_START -->` ~ `<!-- CUSTOM_SECTION_END -->` 사이에 작성합니다. 프레임워크 업그레이드 시에도 이 영역은 자동 보존됩니다.

```markdown
<!-- CLAUDE.md 내부 -->
<!-- CUSTOM_SECTION_START -->
## 팀 코딩 규칙

- 모든 API 응답은 `ApiResponse<T>` 래퍼 사용
- 예외는 `@ControllerAdvice`에서 일괄 처리
- 로그는 구조화 로깅 (JSON 포맷)
<!-- CUSTOM_SECTION_END -->
```

### 방법 2: 별도 컨벤션 파일 추가

공통 컨벤션을 보완하는 파일을 `_base/conventions/`에 신규 생성할 수 있습니다. 업그레이드 시 내장 파일(`skill-upgrade` 업데이트 대상)과 충돌하지 않도록 파일명을 구분하세요.

```bash
# 예: 팀 전용 컨벤션 파일 추가
.claude/domains/_base/conventions/team-standards.md
```

`CLAUDE.md`에서 참조 링크를 추가하면 에이전트가 자동으로 참조합니다.

### 방법 3: 체크리스트 파일 추가

`_base/checklists/`에 마크다운 테이블 형식으로 체크리스트 파일을 추가합니다. `/skill-review-pr` 실행 시 자동 적용됩니다.

#### 체크리스트 형식

심각도에 따라 리뷰 결과가 달라집니다:

- **CRITICAL** — 반드시 수정 필요 (리뷰 거절)
- **MAJOR** — 수정 권장 (조건부 승인)
- **MINOR** — 개선 제안

```markdown
# 주문 처리 체크리스트

## 상태 관리

| 항목 | 설명 | 심각도 |
|------|------|--------|
| 상태 머신 정합성 | 정의된 전이만 허용, 무효 전이 차단 | CRITICAL |
| 낙관적 락 | 동시성 처리에 @Version 사용 | CRITICAL |
| 멱등성 보장 | 결제 요청에 멱등키 적용 | MAJOR |

## 보안

| 항목 | 설명 | 심각도 |
|------|------|--------|
| 개인정보 암호화 | AES-256 암호화 저장 | CRITICAL |
| SQL Injection | 파라미터 바인딩 사용 확인 | CRITICAL |
| 인증 미들웨어 | 보호 경로에 인증 적용 | MAJOR |
```

---

## DB 및 마이그레이션 도구 변경

`_base/conventions/database.md`의 정책(네이밍·필수 컬럼·Soft Delete·낙관적 잠금·무중단 마이그레이션)은 DB·도구 무관하게 적용됩니다. 기본값을 다른 DB나 마이그레이션 도구로 바꾸려면 `project.json`만 변경하면 됩니다.

### 기본값

| 항목 | 기본값 |
|------|--------|
| DB | MySQL 8.0+ |
| 마이그레이션 도구 | Flyway (`V{N}__{description}.sql`) |

### DB 변경

```jsonc
// project.json
{
  "techStack": {
    // schema enum: mysql / postgresql / mongodb / none
    "database": "postgresql"
  }
}
```

SQL DB 간 구문 차이는 Claude가 컨텍스트에 맞춰 적용합니다(자주 쓰이는 매핑 예시):

| MySQL | PostgreSQL |
|-------|-----------|
| `TINYINT(1)` | `BOOLEAN` |
| `AUTO_INCREMENT` | `IDENTITY` / `SERIAL` |
| `JSON` | `JSONB` |

> **MongoDB는 치환 대상이 아닙니다.** conventions의 정책(필수 컬럼 의미·Soft Delete·낙관적 잠금)만 차용하고 스키마/쿼리는 도큐먼트 모델에 맞게 별도 작성하세요.

### 마이그레이션 도구 변경

도구 자체는 schema에서 강제하지 않으며, 사용자는 도구의 표준 식별자 체계를 그대로 따르면 됩니다.

| 도구 | 표준 식별자 예 |
|------|----------------|
| Flyway (기본) | `V1__create_users_table.sql` |
| Alembic | `2024_01_create_users_table.py` (revision id) |
| Liquibase | `001-create-users-table.xml` (changelog ID) |
| Prisma migrate | `20240101000000_create_users_table/migration.sql` |
| golang-migrate | `000001_create_users_table.up.sql` |

### 팀 표준 강제 (CUSTOM_SECTION)

> **보존 범위 안내**: `skill-upgrade`의 CUSTOM_SECTION 자동 보존 메커니즘은 `CLAUDE.md`와 `README.md` 두 파일에만 적용됩니다. `_base/conventions/database.md` 같은 conventions 파일에 직접 마커를 다는 방식은 업그레이드 시 자동 보존이 보장되지 않으므로, 다음 두 가지 대안을 권장합니다.
>
> - **(권장)** 팀 DB 표준은 `CLAUDE.md`의 CUSTOM_SECTION에 추가 — 자동 보존됨, agent-db-designer도 CLAUDE.md를 참조
> - **(대안)** 별도 파일(예: `domains/_base/conventions/database-team.md`) 신규 생성 — 업그레이드 시 보존되며 `CLAUDE.md`에서 참조 링크 추가

```markdown
<!-- CLAUDE.md 내부 -->
<!-- CUSTOM_SECTION_START -->
## 팀 DB 표준 (PostgreSQL)

- 시계열 데이터: TimescaleDB 하이퍼테이블 사용
- JSONB 인덱스: GIN 인덱스 + 부분 표현식 인덱스 우선
- 파티셔닝: 월 단위 RANGE 파티션 (1년 보관 후 아카이브)
- 통계 갱신: ANALYZE를 마이그레이션 마지막 단계에 포함
<!-- CUSTOM_SECTION_END -->
```

`agent-db-designer`는 `CLAUDE.md`를 자동 참조하여 팀 표준에 맞춘 설계 초안을 제시합니다.

---

## 커스텀 스킬 생성

```bash
# 스킬 스캐폴딩 생성
/skill-create
```

`.claude/skills/custom/` 디렉토리에 생성되며, `CLAUDE.md`의 `CUSTOM_SECTION`에 자동 등록됩니다. 프레임워크 업그레이드 시에도 커스텀 스킬은 보존됩니다.

---

## CUSTOM_SECTION 활용 예시

`CLAUDE.md`의 `<!-- CUSTOM_SECTION_START -->` ~ `<!-- CUSTOM_SECTION_END -->` 사이에 프로젝트 고유 규칙을 추가할 수 있습니다. 프레임워크 업그레이드 시에도 이 영역은 자동 보존됩니다.

### 예시: 컨텍스트 압축 시 사용자 알림

기본 동작은 compact 발생 시 상태 파일을 재읽기하고 작업을 계속 진행합니다. 압축 발생을 알림 받고 싶다면 CUSTOM_SECTION에 추가하세요:

```markdown
<!-- CUSTOM_SECTION_START -->
## 컨텍스트 압축 알림 (프로젝트 규칙)

compact 감지 시 다음을 수행한다:
1. 상태 파일 재읽기 (backlog.json, plan 파일)
2. 사용자에게 알림: "컨텍스트 압축 발생 — 상태 복구 완료. 이전 대화 세부 맥락이 축약되었을 수 있습니다."
3. 사용자가 "계속" 또는 "중단" 선택
<!-- CUSTOM_SECTION_END -->
```

### 예시: 프로젝트 고유 코딩 규칙

```markdown
<!-- CUSTOM_SECTION_START -->
## 프로젝트 코딩 규칙

- 모든 API 응답은 `ApiResponse<T>` 래퍼 사용
- 예외는 `@ControllerAdvice`에서 일괄 처리
- 로그는 구조화 로깅 (JSON 포맷)
<!-- CUSTOM_SECTION_END -->
```
