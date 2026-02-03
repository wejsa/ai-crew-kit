# AI Crew Kit 예제 프로젝트

이 디렉토리는 AI Crew Kit의 사용 예시를 제공합니다.

## 예제 목록

### 1. fintech-gateway

핀테크 도메인의 API Gateway 프로젝트 예제입니다.

```
fintech-gateway/
├── .claude/state/
│   ├── project.json      # 프로젝트 설정 (fintech 도메인)
│   └── backlog.json      # 백로그 예시
├── docs/requirements/
│   └── TASK-001-spec.md  # 요구사항 문서 예시
├── CLAUDE.md             # 생성된 CLAUDE.md 예시
└── README.md             # 프로젝트 설명
```

**특징:**
- fintech 도메인 설정
- Spring Boot + Kotlin 기술 스택
- JWT 인증 기능 예제
- PM, backend, code-reviewer, qa 에이전트 활성화

### 2. pg-gateway-backlog.json (레거시)

PG Gateway 마이그레이션 프로젝트의 실제 백로그 예시입니다.
45개의 상세한 Task가 포함된 대규모 백로그 구조를 참고할 수 있습니다.

---

## 예제 사용법

### 예제 프로젝트 복사

```bash
# fintech-gateway 예제를 새 프로젝트로 복사
cp -r examples/fintech-gateway my-new-project
cd my-new-project

# 프로젝트 설정 수정
vi .claude/state/project.json
```

### 처음부터 시작

```bash
# 새 디렉토리 생성
mkdir my-project && cd my-project

# AI Crew Kit 초기화
/skill-init

# 도메인: fintech
# 스택: spring-boot-kotlin
# 에이전트: pm, backend, code-reviewer, qa
```

---

## 예제 워크플로우

### Full-Feature 워크플로우 예시

```bash
# 1. 기능 기획
/skill-feature "JWT 토큰 인증"

# 2. 설계 및 계획
/skill-plan

# 3. 구현 (스텝별)
/skill-impl

# 4. 리뷰
/skill-review-pr 1

# 5. 머지
/skill-merge-pr 1

# 6. 다음 스텝
/skill-impl --next
```

### Quick-Fix 워크플로우 예시

```bash
# 버그 수정 요청
"토큰 만료 버그 고쳐줘"

# PM이 자동으로 quick-fix 워크플로우 실행
# 1. 버그 분석
# 2. 수정 및 PR 생성
# 3. 코드 리뷰
# 4. 머지
```
