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

| 명령어 | 예시 |
|--------|------|
| 조회 | `/skill-backlog`, `list`, `list --status=todo`, `list --phase=2` |
| 추가 | `/skill-backlog add "제목" --phase=2 --priority=high` |
| 수정 | `/skill-backlog update {taskId} --status=in_progress` |
| 우선순위 | `/skill-backlog priority {taskId} high` |
| 잠금 해제 | `/skill-backlog unlock {taskId} --force` |

## backlog.json 쓰기 프로토콜

모든 backlog.json 쓰기 시 반드시 아래 순서를 따른다:

1. **읽기**: 현재 `metadata.version` 값 기록
2. **쓰기**: 변경 적용 + `metadata.version` 1 증가 + `metadata.updatedAt` 갱신
3. **검증**: 쓰기 직후 JSON 유효성 검증 → 실패 시 `git checkout -- .claude/state/backlog.json` 롤백
4. **충돌 감지**: Git push 실패 시 `metadata.version` 비교로 충돌 감지
   - 로컬 version ≠ 원격 version → 아래 충돌 해소 규칙 적용
   - 동일 → 네트워크 오류, 재시도

### JSON 충돌 해소 규칙 (pull --rebase 후)

| 상황 | 해소 방법 |
|------|----------|
| 서로 **다른 Task** 수정 | 두 변경 모두 유지 |
| 같은 Task의 **다른 필드** 수정 | 두 필드 모두 유지 |
| 같은 Task의 **같은 필드** 수정 | 최신 `updatedAt` 타임스탬프 우선 |
| `metadata.version` 충돌 | `max(local, remote) + 1` |
| `metadata.updatedAt` | 현재 시각으로 갱신 |

해소 후 JSON 유효성 재검증 필수. 실패 시 `git rebase --abort` + 사용자 안내.

**completed.json 동일 프로토콜 적용**: completed.json에도 `metadata.version`/`updatedAt`을 관리하며, 위와 동일한 충돌 해소 규칙을 따른다.

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
      "lockedFiles": ["src/auth/JwtService.kt"],
      "specFile": "docs/requirements/TASK-001-spec.md",
      "dependencies": [],
      "steps": [
        {"number": 1, "title": "Step 제목", "status": "in_progress", "files": ["JwtService.kt"]}
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

## 상태 값 / 우선순위

상태: `todo` | `in_progress` | `done` | `blocked`
우선순위: `critical`(긴급) | `high` | `medium` | `low`

## 출력

필수 포함: Phase별 Task 테이블(ID/제목/상태/우선순위/의존성), 요약(전체/대기/진행/완료 수)

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

**산정 시점**: Task를 `in_progress`로 전환할 때 `lockTTL` 계산하여 저장.
`lockTTL` 필드가 없는 기존 Task는 기본값 3600(1시간) 적용.

**만료 판정**: `assignedAt` + `lockTTL`초 < 현재 시각 → 만료
- `/skill-status`에서 경고 표시, 다른 세션에서 인계 가능

### assignee 생성 규칙
`{user}@{hostname}-{YYYYMMDD-HHmmss}` — user: $USER/$USERNAME/git user.name/"anonymous", hostname: $HOSTNAME/$COMPUTERNAME/"unknown"

## 긴급 잠금 해제

`/skill-backlog unlock {taskId} --force`

**사용 조건**: assignee가 현재 세션과 다름 + `--force` 필수 + "I understand the risks" 입력

**해제 후**: assignee/assignedAt 제거, lockedFiles 초기화, status→`todo`, 커밋 & 푸시, 감사 로그 기록

## 주의사항
- 변경 시 자동으로 `updatedAt` 갱신
- 상태 변경 시 Git 커밋 & 푸시 수행
