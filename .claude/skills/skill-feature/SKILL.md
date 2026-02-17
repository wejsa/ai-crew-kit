---
name: skill-feature
description: 기능 기획 - 요구사항 정의 + 백로그 Task 등록
disable-model-invocation: true
allowed-tools: Bash(git:*), Read, Write, Glob, Grep
argument-hint: "[기능명]"
---

# skill-feature: 기능 기획

## 실행 조건
- 사용자가 `/skill-feature {기능명}` 또는 "새 기능 기획해줘: {기능명}" 요청 시
- 기능명 없이 호출 시 기능 추천

## 실행 플로우

### 1. 기능 분석
- 요청된 기능의 범위와 목적 파악
- 기존 코드베이스 분석 (관련 파일, 패턴)
- 기술적 실현 가능성 검토
- **도메인 참고자료 확인**:
  - `.claude/state/project.json`에서 현재 도메인 확인
  - `.claude/domains/{domain}/domain.json`의 keywords 매핑으로 관련 문서 자동 탐색
  - `.claude/domains/_base/conventions/`에서 관련 컨벤션 확인
  - 관련 참고자료를 요구사항 문서에 반영

### 2. 중복 확인
`.claude/state/backlog.json`에서 유사 Task 확인:
- 동일/유사 기능이 있으면 사용자에게 알림
- 병합 또는 별도 생성 여부 확인

### 3. 요구사항 문서 생성
`docs/requirements/{taskId}-spec.md` 생성:

```markdown
# {Task ID}: {기능명}

## 개요
{기능 설명}

## 목적
- {목적 1}
- {목적 2}

## 기능 요구사항

### FR-001: {요구사항 제목}
- **설명**: {상세 설명}
- **우선순위**: Must/Should/Could/Won't
- **수용 기준**:
  - [ ] {기준 1}
  - [ ] {기준 2}

## 비기능 요구사항
- **성능**: {성능 요구사항}
- **보안**: {보안 요구사항}
- **확장성**: {확장성 요구사항}

## 기술 스펙
- **영향 범위**: {영향받는 모듈/파일}
- **의존성**: {필요한 라이브러리/서비스}
- **API 변경**: {있음/없음}

## 테스트 계획
- 단위 테스트: {범위}
- 통합 테스트: {범위}
- E2E 테스트: {범위}

## 참고자료
- {관련 문서 링크}
```

### 4. 사용자 검토/승인 요청
- 생성된 요구사항 문서 제시
- 수정 사항 확인
- **승인 받을 때까지 진행하지 않음**

### 5. 백로그 등록
승인 후 `.claude/state/backlog.json`에 Task 추가:
```json
{
  "id": "{taskId}",
  "title": "{기능명}",
  "description": "{간단 설명}",
  "status": "todo",
  "priority": "{우선순위}",
  "phase": {phase},
  "specFile": "docs/requirements/{taskId}-spec.md",
  "dependencies": [],
  "steps": [],
  "currentStep": 0,
  "createdAt": "{timestamp}",
  "updatedAt": "{timestamp}"
}
```

### 6. 커밋 & 푸시
```bash
git add docs/requirements/{taskId}-spec.md .claude/state/backlog.json
git commit -m "feat: {taskId} 요구사항 정의 - {기능명}"
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
GIT_COMMON_DIR=$(git rev-parse --git-common-dir 2>/dev/null)
if [ "$GIT_DIR" != "$GIT_COMMON_DIR" ]; then
  git push -u origin HEAD
else
  git push origin develop
fi
```

### 7. skill-plan 자동 호출

**"Y" 승인 시 반드시 수행:**
```
Skill tool 사용: skill="skill-plan", args="{taskId}"
```

**중요:**
- 백로그 등록 후 skill-plan 호출
- skill-plan 호출 없이 직접 설계 진행 **금지**
- 반드시 Skill tool을 사용하여 skill-plan 스킬 실행

**출력 예시:**
```
✅ 백로그 등록 완료
🔄 설계 단계로 자동 진행합니다...
```

## Task ID 생성 규칙
- 형식: `{PREFIX}-{번호}`
- PREFIX: `project.json`의 `conventions.taskPrefix` 사용 (기본: TASK)
- 번호: `backlog.json`의 `metadata.lastTaskNumber + 1` (3자리 패딩)
- 예: `TASK-001`, `PG-GW-002`

## 기능 추천 (기능명 없이 호출 시)
프로젝트 분석 후 추천:
1. 현재 코드베이스 분석
2. 누락된 기능 식별
3. 개선 가능 영역 제안
4. 우선순위와 함께 3-5개 추천

## 출력 포맷

```
## 🎯 새 기능 기획: {기능명}

### 요구사항 문서
📄 `docs/requirements/{taskId}-spec.md` 생성 완료

### 요약
- **Task ID**: {taskId}
- **기능명**: {기능명}
- **Phase**: {phase}
- **우선순위**: {priority}
- **예상 스텝**: {N}개

### 다음 단계
요구사항 문서를 검토해주세요.
승인하시면 백로그에 등록합니다.

승인하시겠습니까? (Y/N)

> Y: 백로그 등록 후 `/skill-plan` 자동 실행
> N: 요구사항 수정
```

## 주의사항
- 요구사항 문서는 반드시 사용자 승인 후 백로그 등록
- 중복 Task 생성 방지
- Phase는 프로젝트 현황에 맞게 자동 추천 (사용자 변경 가능)
