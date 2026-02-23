---
name: skill-backlog
description: 백로그 관리 - Task 목록 조회, 추가, 수정, 우선순위 변경. /skill-backlog로 호출합니다.
disable-model-invocation: true
allowed-tools: Bash(git:*), Read, Write, Glob
argument-hint: "[list|add|update|priority] [options]"
---

# skill-backlog: 백로그 관리

## 실행 조건
- 사용자가 `/skill-backlog` 또는 "백로그 보여줘" 요청 시

## 명령어 옵션

### 조회 (기본)
```
/skill-backlog
/skill-backlog list
/skill-backlog list --status=todo
/skill-backlog list --phase=2
```

### 추가
```
/skill-backlog add "Task 제목" --phase=2 --priority=high
```

### 수정
```
/skill-backlog update {taskId} --status=in_progress
/skill-backlog update {taskId} --priority=critical
```

### 우선순위 변경
```
/skill-backlog priority {taskId} high|medium|low|critical
```

## backlog.json 쓰기 프로토콜

모든 backlog.json 쓰기 시 반드시 아래 순서를 따른다:

1. **읽기**: 현재 `metadata.version` 값 기록
2. **쓰기**: 변경 적용 + `metadata.version` 1 증가 + `metadata.updatedAt` 갱신
3. **검증**: 쓰기 직후 JSON 유효성 검증
   ```bash
   cat .claude/state/backlog.json | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null || {
     echo "❌ backlog.json 쓰기 후 JSON 유효성 검증 실패. 롤백 필요."
     # Git에서 복원
     git checkout -- .claude/state/backlog.json
     exit 1
   }
   ```
4. **충돌 감지**: Git push 실패 시 `metadata.version` 비교로 충돌 감지
   - 로컬 version과 원격 version이 다르면 → 수동 머지 필요
   - 동일하면 → 네트워크 오류, 재시도

## 백로그 데이터 구조

**스키마 정의**: `.claude/schemas/backlog.schema.json` (단일 권위 문서)

`.claude/state/backlog.json`:
```json
{
  "metadata": {
    "lastTaskNumber": 1,
    "projectPrefix": "TASK",
    "version": 1,
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z"
  },
  "tasks": {
    "TASK-001": {
      "id": "TASK-001",
      "title": "Task 제목",
      "description": "상세 설명",
      "status": "in_progress",
      "priority": "high",
      "phase": 1,
      "assignee": "dev@DESKTOP-ABC-20260203-143052",
      "assignedAt": "2026-02-03T14:30:52Z",
      "lockedFiles": [
        "src/auth/JwtService.kt",
        "src/auth/TokenValidator.kt"
      ],
      "specFile": "docs/requirements/TASK-001-spec.md",
      "dependencies": [],
      "steps": [
        {
          "number": 1,
          "title": "Step 제목",
          "status": "in_progress",
          "files": ["JwtService.kt"]
        },
        {
          "number": 2,
          "title": "Step 2 제목",
          "status": "pending",
          "files": ["TokenValidator.kt"]
        }
      ],
      "currentStep": 1,
      "workflowState": {
        "currentSkill": "skill-impl",
        "lastCompletedSkill": "skill-plan",
        "prNumber": null,
        "autoChainArgs": "",
        "updatedAt": "2026-02-03T14:30:52Z"
      },
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:00:00Z"
    }
  }
}
```

## 출력 포맷

### 목록 조회 시
```
## 📋 백로그 목록

### Phase 1: 초기화
| ID | 제목 | 상태 | 우선순위 | 의존성 |
|----|------|------|---------|--------|
| TASK-001 | 프로젝트 설정 | ✅ done | high | - |

### Phase 2: 핵심 기능
| ID | 제목 | 상태 | 우선순위 | 의존성 |
|----|------|------|---------|--------|
| TASK-002 | 인증 서비스 | 🔄 in_progress | high | TASK-001 |
| TASK-003 | 캐시 서비스 | 📋 todo | medium | TASK-002 |

---
**요약**: 전체 {N}개 | 대기 {N}개 | 진행 {N}개 | 완료 {N}개
```

## 상태 값
- `todo`: 대기 중
- `in_progress`: 진행 중
- `done`: 완료
- `blocked`: 차단됨 (의존성 미충족)

## 우선순위
- `critical`: 긴급 (즉시 처리)
- `high`: 높음
- `medium`: 보통
- `low`: 낮음

## 주의사항
- 변경 시 자동으로 `updatedAt` 갱신
- 상태 변경 시 Git 커밋 & 푸시 수행

## 병렬 작업 지원

### 다중 in_progress 허용 조건
- 의존성 없는 Task는 다중 `in_progress` 허용
- `assignee` 필드로 작업자/세션 구분
- `lockedFiles`로 파일 잠금 관리
- 동일 파일 수정 Task는 순차 처리 권장

### 잠금 만료 (동적 TTL)

`lockTTL`은 스텝 복잡도에 따라 동적으로 산정:

| 조건 | TTL | 근거 |
|------|-----|------|
| lockedFiles ≤ 3개 | 1시간 | 단순 스텝 |
| lockedFiles 4~8개 | 2시간 | 중간 복잡도 |
| lockedFiles 9개 이상 | 3시간 | 복잡한 스텝 |
| `--extend-lock` 사용 | +1시간 | 수동 연장 (최대 4시간) |

**산정 시점**: Task를 `in_progress`로 전환할 때 `lockTTL` 필드를 계산하여 저장.
```json
{
  "assignedAt": "2026-02-03T14:30:52Z",
  "lockTTL": 7200,
  "lockedFiles": ["A.kt", "B.kt", "C.kt", "D.kt"]
}
```

`lockTTL` 필드가 없는 기존 Task는 기본값 3600(1시간) 적용.

**만료 판정**: `assignedAt` + `lockTTL`초 < 현재 시각 → 만료
- 만료된 잠금은 `/skill-status`에서 경고 표시
- 다른 세션에서 만료된 Task 인계 가능

### assignee 생성 규칙
```
{user}@{hostname}-{YYYYMMDD-HHmmss}

생성 순서:
1. user: $USER || $USERNAME || git config user.name || "anonymous"
2. hostname: $HOSTNAME || $COMPUTERNAME || "unknown"
3. timestamp: 현재 시각 (YYYYMMDD-HHmmss)

예: dev@DESKTOP-ABC-20260203-143052
```

## 긴급 잠금 해제

### 명령어
```
/skill-backlog unlock {taskId} --force
```

### 사용 케이스
- 세션 비정상 종료 + 긴급 수정 필요
- TTL 만료 대기 불가 상황

### 실행 조건
1. 해당 Task의 assignee가 현재 세션과 다름
2. `--force` 플래그 필수
3. "I understand the risks" 입력 요구
4. 감사 로그 기록

### 출력 형식
```
⚠️ 강제 잠금 해제

Task: {taskId}
원래 담당자: {assignee}
할당 시각: {assignedAt} ({경과 시간} 전)

경고:
- 원래 담당자가 작업 중일 수 있습니다
- 코드 충돌이 발생할 수 있습니다
- 데이터 손실 위험이 있습니다

계속하려면 "I understand the risks"를 입력하세요:
```

### 해제 후 처리
1. 기존 assignee, assignedAt 제거
2. lockedFiles 초기화
3. status를 `todo`로 변경
4. Git 커밋 & 푸시
5. 감사 로그에 강제 해제 기록
