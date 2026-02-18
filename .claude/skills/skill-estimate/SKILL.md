---
name: skill-estimate
description: 작업 복잡도 추정 - 5팩터 분석 + 과거 데이터 보정
disable-model-invocation: false
allowed-tools: Bash(git:*), Bash(gh:*), Bash(wc:*), Read, Glob, Grep
argument-hint: "<TASK-ID|--phase N|--sprint>"
---

# skill-estimate: 작업 복잡도 추정

## 실행 조건
- 사용자가 `/skill-estimate {TASK-ID}` 또는 "이 작업 얼마나 걸려?" 요청 시
- 사용자가 `/skill-estimate --phase {N}` 또는 "페이즈 N 분석해줘" 요청 시
- 사용자가 `/skill-estimate --sprint` 또는 "스프린트 플래닝 해줘" 요청 시

## 실행 모드

| 모드 | 트리거 | 대상 |
|------|--------|------|
| 단일 Task | `/skill-estimate TASK-001` | 지정 Task 복잡도 추정 |
| 페이즈 | `/skill-estimate --phase 1` | 해당 Phase의 모든 Task 요약 |
| 스프린트 | `/skill-estimate --sprint` | TODO 상태 Task 우선순위 + 추정 |

## 사전 조건 검증 (MUST-EXECUTE-FIRST)

실패 시 즉시 중단 + 사용자 보고.

```bash
# [REQUIRED] 1. project.json 존재
if [ ! -f ".claude/state/project.json" ]; then
  echo "project.json이 없습니다. /skill-init을 먼저 실행하세요."
  exit 1
fi

# [REQUIRED] 2. backlog.json 존재 + 유효 JSON
if [ ! -f ".claude/state/backlog.json" ]; then
  echo "backlog.json이 없습니다."
  exit 1
fi
```

## 5팩터 복잡도 분석

각 Task를 다음 5가지 축으로 분석하여 복잡도 점수를 산출:

### Factor 1: 코드 변경 규모 (Code Scope)

요구사항/스펙에서 예상 변경 범위를 분석:

| 점수 | 기준 |
|------|------|
| 1 | 단일 파일 수정, 10줄 미만 |
| 2 | 2~3개 파일, 50줄 미만 |
| 3 | 4~8개 파일, 200줄 미만 |
| 5 | 9~15개 파일, 500줄 미만 |
| 8 | 15개 이상 파일, 500줄 이상 |

**데이터 소스:**
- `docs/requirements/{TASK-ID}-spec.md` (존재 시)
- `backlog.json` Task description
- 유사 과거 Task의 실제 변경량 (completed.json + git log)

### Factor 2: 아키텍처 영향 (Architecture Impact)

| 점수 | 기준 |
|------|------|
| 1 | 기존 패턴 내 구현, 새 모듈 없음 |
| 2 | 기존 모듈에 새 기능 추가 |
| 3 | 새 모듈/서비스 1개 생성 |
| 5 | 복수 모듈 간 상호작용 변경 |
| 8 | 아키텍처 패턴 변경, DB 스키마 대규모 수정 |

### Factor 3: 의존성 위험 (Dependency Risk)

| 점수 | 기준 |
|------|------|
| 1 | 외부 의존성 없음 |
| 2 | 안정적 라이브러리 사용 |
| 3 | 새 외부 서비스 연동 1개 |
| 5 | 복수 외부 서비스 연동 또는 버전 업그레이드 |
| 8 | 핵심 인프라 변경 (DB 교체, 프레임워크 마이그레이션 등) |

### Factor 4: 테스트 복잡도 (Test Complexity)

| 점수 | 기준 |
|------|------|
| 1 | 단위 테스트만 필요 |
| 2 | 단위 + 통합 테스트 |
| 3 | 외부 서비스 모킹 필요 |
| 5 | E2E 테스트 또는 성능 테스트 필요 |
| 8 | 보안 테스트, 장애 시나리오 테스트 필요 |

### Factor 5: 도메인 복잡도 (Domain Complexity)

| 점수 | 기준 |
|------|------|
| 1 | 단순 CRUD |
| 2 | 비즈니스 규칙 1~2개 |
| 3 | 상태 머신 또는 복잡한 검증 로직 |
| 5 | 트랜잭션/보상 로직, 동시성 처리 |
| 8 | 컴플라이언스 요구사항, 멱등성 보장 |

## 복잡도 점수 산출

```
총점 = Factor1 + Factor2 + Factor3 + Factor4 + Factor5
최소: 5, 최대: 40
```

| 총점 범위 | 복잡도 등급 | 예상 스텝 수 |
|-----------|-----------|-------------|
| 5~10 | LOW | 1~2 스텝 |
| 11~18 | MEDIUM | 2~4 스텝 |
| 19~28 | HIGH | 4~6 스텝 |
| 29~40 | CRITICAL | 6~10 스텝 (Task 분할 권장) |

## 과거 데이터 보정

### completed.json 기반 학습

과거 완료 Task에서 실제 소요 시간을 추출하여 추정치를 보정:

```bash
# completed.json에서 타임스탬프 기반 소요 시간 산출
if [ -f ".claude/state/completed.json" ]; then
  python3 -c "
import json
from datetime import datetime

data = json.load(open('.claude/state/completed.json'))
for task_id, task in data.items():
    created = task.get('createdAt', '')
    completed = task.get('completedAt', '')
    if created and completed:
        try:
            t1 = datetime.fromisoformat(created.replace('Z', '+00:00'))
            t2 = datetime.fromisoformat(completed.replace('Z', '+00:00'))
            duration = (t2 - t1).total_seconds() / 3600  # hours
            steps = len(task.get('steps', []))
            print(f'{task_id}: {duration:.1f}h, {steps} steps')
        except:
            pass
"
fi
```

**보정 로직:**
1. 유사 규모(스텝 수 유사) 과거 Task 검색
2. 실제 소요 시간 평균 산출
3. 추정 스텝 수 × (과거 평균 스텝당 시간) = 보정된 추정

**과거 데이터 없는 경우:**
- 기본 추정값 사용 (스텝당 1시간 기준)
- "과거 데이터 부족으로 기본 추정치입니다" 안내

### git log 기반 코드 변경 규모

```bash
# 과거 Task 관련 커밋의 변경 규모
git log --all --oneline --grep="$TASK_PREFIX" --format="%H" | head -20 | while read hash; do
  git diff --stat "$hash~1" "$hash" 2>/dev/null | tail -1
done
```

### execution-log.json (선택적)

```bash
# 존재 시에만 활용
if [ -f ".claude/state/execution-log.json" ]; then
  # 스킬 실행 이력에서 패턴 분석
  # 예: review-pr에서 REQUEST_CHANGES 빈도 → 품질 위험도
fi
```

## 출력 포맷

### 단일 Task 모드

```
## 복잡도 추정: {TASK-ID}

### Task 정보
- **제목**: {title}
- **Phase**: {phase}
- **우선순위**: {priority}

### 5팩터 분석

| 팩터 | 점수 | 근거 |
|------|------|------|
| 코드 변경 규모 | {N}/8 | {근거} |
| 아키텍처 영향 | {N}/8 | {근거} |
| 의존성 위험 | {N}/8 | {근거} |
| 테스트 복잡도 | {N}/8 | {근거} |
| 도메인 복잡도 | {N}/8 | {근거} |

### 결과
- **총점**: {total}/40
- **복잡도**: {LOW|MEDIUM|HIGH|CRITICAL}
- **예상 스텝 수**: {N}개
- **예상 소요 시간**: ~{N}시간

### 과거 데이터 보정
{보정 내용 또는 "과거 데이터 부족 (기본 추정치)"}

### 권장 사항
- {스텝 분리 전략}
- {위험 완화 방안}
```

### 페이즈 모드 (`--phase N`)

```
## Phase {N} 복잡도 분석

### 요약
| 지표 | 값 |
|------|-----|
| Task 수 | {N}개 |
| 평균 복잡도 | {avg}/40 |
| 총 예상 스텝 | {N}개 |
| 총 예상 시간 | ~{N}시간 |

### Task별 추정

| Task | 제목 | 복잡도 | 예상 스텝 | 예상 시간 |
|------|------|--------|----------|----------|
| TASK-001 | {title} | MEDIUM (15) | 3 | ~3h |
| TASK-002 | {title} | HIGH (22) | 5 | ~5h |

### 위험 요소
- {HIGH/CRITICAL Task 목록}
- {의존성 충돌 가능성}
```

### 스프린트 모드 (`--sprint`)

```
## 스프린트 플래닝

### 사용 가능한 Task (TODO 상태)

| 우선순위 | Task | 제목 | 복잡도 | 예상 스텝 | 예상 시간 |
|---------|------|------|--------|----------|----------|
| 1 | TASK-003 | {title} | LOW (8) | 2 | ~2h |
| 2 | TASK-001 | {title} | MEDIUM (15) | 3 | ~3h |
| 3 | TASK-005 | {title} | HIGH (24) | 5 | ~5h |

### 스프린트 권장 구성
총 예상: {N}시간, {N}스텝

#### 필수 포함 (높은 우선순위)
- TASK-003: {title}
- TASK-001: {title}

#### 선택 포함 (여유 있을 경우)
- TASK-005: {title}

### 의존 관계
- TASK-001 → TASK-005 (선행 필요)
```

## 데이터 소스 우선순위

1. **completed.json** — 핵심 (타임스탬프 기반 소요 시간 산출)
2. **backlog.json** — 현재 Task 메타데이터
3. **git log / gh pr view** — 코드 변경 규모, PR 메트릭
4. **execution-log.json** — 선택적 (존재 시에만)

## 자동 체이닝
- 없음 (독립 실행)

## 주의사항
- 추정은 참고용이며 실제 소요 시간과 다를 수 있음
- 과거 데이터가 충분할수록 보정 정확도 향상
- CRITICAL 등급 Task는 Task 분할을 강력 권장
- 상태 파일은 읽기 전용 (수정하지 않음)
- completed.json의 effort/duration 전용 필드 없이 createdAt/completedAt 타임스탬프로 계산
