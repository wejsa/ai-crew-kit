---
name: skill-plan
description: 계획 수립 - Task 선택 + 설계 분석 + 스텝 분리 계획
disable-model-invocation: true
allowed-tools: Bash(git:*), Read, Write, Glob, Grep
argument-hint: "[taskId]"
---

# skill-plan: 계획 수립

## 실행 조건
- 사용자가 `/skill-plan` 또는 "다음 작업 가져와" 요청 시
- 특정 Task 지정: `/skill-plan {taskId}`

## 실행 플로우

### 1. Task 선택

**자동 선택 기준** (taskId 미지정 시):
1. `status: todo` 인 Task 중
2. `dependencies` 모두 충족된 Task 중
3. `lockedFiles` 충돌 없는 Task 중
4. `priority` 높은 순서대로
5. 같은 우선순위면 `phase` 낮은 순서

**선택 불가 조건**:
- 의존성 미충족 Task는 `blocked` 표시
- 같은 파일을 수정하는 `in_progress` Task 존재 시 경고

**병렬 작업 가능 조건**:
- 의존성 체인에 없는 Task
- 다른 `in_progress` Task의 `lockedFiles`와 겹치지 않음

### 2. 요구사항 확인
선택된 Task의 `specFile` 읽기:
```
docs/requirements/{taskId}-spec.md
```

### 3. 설계 분석
요구사항 기반으로 분석:

**도메인 템플릿 참조**:
- `.claude/state/project.json`에서 현재 도메인 확인
- `.claude/domains/{domain}/templates/` 디렉토리에서 관련 템플릿 활용
- `.claude/domains/_base/templates/`의 공통 템플릿 참조

#### 3.1 컴포넌트 설계
- 생성/수정할 파일 목록
- 각 파일의 역할과 책임
- 패키지/모듈 구조

#### 3.2 시퀀스 다이어그램
- 주요 플로우 시각화
- 컴포넌트 간 상호작용

#### 3.3 API 설계 (해당 시)
- 엔드포인트 정의
- 요청/응답 스키마
- 에러 코드

#### 3.4 데이터 모델
- 엔티티/DTO 정의
- 관계 설계

### 4. 스텝 분리 계획
**분리 기준**:
- 각 스텝 **500라인 미만**
- 논리적 단위로 분리
- 각 스텝은 독립적으로 빌드/테스트 가능

**스텝 구조**:
```
Step 1: {제목}
- 파일: {파일 목록}
- 예상 라인: {N}
- 내용: {상세 설명}

Step 2: {제목}
- 파일: {파일 목록}
- 예상 라인: {N}
- 내용: {상세 설명}
- 의존: Step 1
```

### 4.5 파일 충돌 검사

계획 수립 완료 후, 다른 `in_progress` Task와 파일 충돌 검사:

1. 스텝별 수정 예정 파일 목록 추출
2. backlog.json의 다른 `in_progress` Task `lockedFiles` 조회
3. 교집합 검사

**충돌 없음**: 정상 진행

**충돌 발생 시**:
```
⚠️ 파일 충돌 경고

다음 파일이 다른 Task에서 수정 중입니다:
- src/auth/JwtService.kt
  └── TASK-002 (dev@OTHER-PC-20260203-100000) Step 2 진행 중

옵션:
1. 순차 처리 - 해당 Task 완료 대기 (권장)
2. 강제 진행 ⚠️
   - 머지 시 수동 충돌 해결 필요
   - 같은 파일 동시 수정으로 코드 손실 가능
   - 정말 진행하시겠습니까? ("yes" 입력)
```

**강제 진행 시**: 계획 파일에 충돌 경고 명시

---

### 5. 계획 파일 생성
`.claude/temp/{taskId}-plan.md` 생성:

```markdown
# {Task ID}: {제목} - 개발 계획

## 요구사항 요약
{요구사항 핵심 내용}

## 설계

### 컴포넌트 구조
```
{패키지/파일 구조}
```

### 시퀀스 다이어그램
```mermaid
sequenceDiagram
{다이어그램}
```

### API 설계
{API 정의}

### 데이터 모델
{모델 정의}

## 스텝별 계획

### Step 1: {제목}
- **파일**: {파일 목록}
- **예상 라인**: {N}
- **내용**:
  - {작업 1}
  - {작업 2}
- **테스트**:
  - {테스트 항목}

### Step 2: {제목}
...

## 예상 일정
- 전체 스텝: {N}개
- 예상 PR: {N}개

## 리스크 & 고려사항
- {리스크 1}
- {리스크 2}
```

### 6. 사용자 검토/승인 요청
- 설계와 스텝 계획 제시
- 수정 의견 수렴
- **승인 받을 때까지 개발 진행하지 않음**

### 7. 상태 업데이트 (승인 후)

`backlog.json` 업데이트:
```json
{
  "status": "in_progress",
  "assignee": "dev@DESKTOP-ABC-20260203-143052",
  "assignedAt": "2026-02-03T14:30:52Z",
  "lockedFiles": ["src/auth/JwtService.kt", "src/auth/TokenValidator.kt"],
  "steps": [
    {"number": 1, "title": "...", "status": "pending", "files": ["JwtService.kt"]},
    {"number": 2, "title": "...", "status": "pending", "files": ["TokenValidator.kt"]}
  ],
  "currentStep": 1,
  "updatedAt": "{timestamp}"
}
```

### 8. skill-impl 자동 호출

**"Y" 승인 시 반드시 수행:**
```
Skill tool 사용: skill="skill-impl"
```

**중요:**
- backlog.json 업데이트 후 skill-impl 호출
- skill-impl 호출 없이 직접 개발 진행 **금지**
- 반드시 Skill tool을 사용하여 skill-impl 스킬 실행

**출력 예시:**
```
✅ 계획 승인 완료
🔄 Step 1 개발을 자동 시작합니다...
```

## 출력 포맷

```
## 📋 계획 수립: {Task ID}

### 선택된 Task
- **ID**: {taskId}
- **제목**: {제목}
- **Phase**: {phase}
- **우선순위**: {priority}

### 설계 요약
{설계 핵심 내용}

### 스텝 계획
| Step | 제목 | 예상 라인 | 주요 파일 |
|------|------|----------|----------|
| 1 | {제목} | {N} | {파일} |
| 2 | {제목} | {N} | {파일} |

### 계획 파일
📄 `.claude/temp/{taskId}-plan.md` 생성 완료

---
설계와 스텝 계획을 검토해주세요.
승인하시면 개발을 시작합니다.

승인하시겠습니까? (Y/N)

> Y: 상태 업데이트 후 `/skill-impl` 자동 실행 (Step 1 시작)
> N: 계획 수정
```

## 라인 수 가이드라인
| 예상 라인 | 상태 | 조치 |
|----------|------|------|
| < 300 | ✅ 양호 | 진행 |
| 300~500 | ⚠️ 주의 | 가능하면 분리 권장 |
| > 500 | ❌ 초과 | 반드시 분리 |

## Git 동기화 프로토콜

상태 업데이트 시:
```bash
# 1. 최신 상태 동기화
git pull origin develop --rebase

# 2. backlog.json 수정 (자동 처리)

# 3. 커밋 & 푸시
git add .claude/state/backlog.json
git commit -m "chore: start TASK-001"
git push origin develop

# 4. 푸시 실패 시 (충돌)
git pull --rebase
# JSON 충돌: 두 Task 변경 모두 유지 (수동 해결)
git push origin develop
```

## 주의사항
- 계획 파일은 Git에서 제외됨 (`.claude/temp/`)
- 계획 승인 전 코드 작성 금지
- 의존성 있는 스텝은 순서 명시
- 각 스텝은 PR 생성 단위
- 병렬 작업 시 `lockedFiles` 충돌 주의
