# AI Crew Kit 예제 프로젝트

이 디렉토리는 AI Crew Kit의 사용 예시를 제공합니다. AI Crew Kit은 도메인 무관 범용 프레임워크이므로, 예제는 특정 비즈니스 도메인이 아니라 **워크플로우와 설정 구조**를 보여주는 데 초점을 둡니다.

## 예제 목록

### general-app — 범용 최소 예제

기술 스택에 중립적인 범용 프로젝트 설정 예제입니다.

```
general-app/
├── .claude/state/
│   ├── project.json      # 프로젝트 설정 (범용)
│   └── backlog.json      # 백로그 예시
├── docs/requirements/
│   └── TASK-001-spec.md  # 요구사항 문서 예시
├── CLAUDE.md             # 생성된 CLAUDE.md 예시
└── README.md             # 프로젝트 설명
```

**특징:**
- 도메인 무관 범용 설정
- 기술 스택 자동 감지 + 빌드/테스트 게이트
- code-reviewer, qa 에이전트 활성화 (오케스트레이션·구현은 메인 세션 — v4.8.0)
- plan → impl → review → merge 오케스트레이션 예시

---

## 예제 사용법

### 기존 프로젝트에 적용

```bash
# AI Crew Kit 스킬을 기존 프로젝트에 복사
cp -r ai-crew-kit/.claude my-existing-project/
cd my-existing-project

# 온보딩 실행 (코드베이스 자동 스캔 → 설정 생성)
/aick-onboard

# 적용 전 스캔 결과만 먼저 확인하려면:
/aick-onboard --scan-only
```

### 처음부터 시작

```bash
# 새 디렉토리 생성
mkdir my-project && cd my-project

# AI Crew Kit 초기화 (요구사항 자유 서술 → 스택 LLM 추천 → 에이전트 팀 선택)
/aick-init
```

---

## 예제 워크플로우

### Full-Feature 워크플로우 예시

```bash
# 1. 기능 기획
/aick-feature "JWT 토큰 인증"

# 2. 설계 및 계획
/aick-plan

# 3. 구현 (스텝별)
/aick-impl

# 4. 리뷰
/aick-review-pr 1

# 5. 머지
/aick-merge-pr 1

# 6. 다음 스텝
/aick-impl --next
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
