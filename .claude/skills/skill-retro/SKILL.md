---
name: skill-retro
description: 완료 Task 회고 - 분석 리포트 생성 + 체크리스트/컨벤션 학습 반영
disable-model-invocation: false
allowed-tools: Bash(git:*), Bash(gh:*), Read, Write, Edit, Glob, Grep, AskUserQuestion
argument-hint: "[TASK-ID|--summary]"
---

# skill-retro: 완료 Task 회고

## 실행 조건
- 사용자가 `/skill-retro` 또는 "회고 해줘" 요청 시
- 사용자가 `/skill-retro {TASK-ID}` 또는 "TASK-001 회고해줘" 요청 시
- 사용자가 `/skill-retro --summary` 또는 "전체 회고 요약해줘" 요청 시

## 실행 모드

| 모드 | 트리거 | 대상 |
|------|--------|------|
| 기본 | `/skill-retro` | 최근 완료 1개 Task |
| 특정 | `/skill-retro TASK-001` | 지정 Task |
| 전체 요약 | `/skill-retro --summary` | completed.json 전체 |

## 사전 조건 검증 (MUST-EXECUTE-FIRST)

실패 시 즉시 중단 + 사용자 보고. 절대 다음 단계 진행 금지.

```bash
# [REQUIRED] 1. project.json 존재
if [ ! -f ".claude/state/project.json" ]; then
  echo "❌ project.json이 없습니다. /skill-init을 먼저 실행하세요."
  exit 1
fi

# [REQUIRED] 2. completed.json 존재 + 유효 JSON
if [ ! -f ".claude/state/completed.json" ]; then
  echo "❌ completed.json이 없습니다. 완료된 Task가 없습니다."
  exit 1
fi
cat .claude/state/completed.json | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null || {
  echo "❌ completed.json이 유효한 JSON이 아닙니다."
  exit 1
}

# [REQUIRED] 3. 완료된 Task 존재 확인
TASK_COUNT=$(python3 -c "import json; print(len(json.load(open('.claude/state/completed.json'))))")
if [ "$TASK_COUNT" == "0" ]; then
  echo "❌ 완료된 Task가 없습니다."
  exit 1
fi
```

## 실행 플로우

### 1. 대상 Task 식별

**기본 모드** (인수 없음):
```bash
# completed.json에서 가장 최근 완료된 Task
python3 -c "
import json
data = json.load(open('.claude/state/completed.json'))
latest = max(data.values(), key=lambda x: x.get('completedAt', ''))
print(latest['id'])
"
```

**특정 Task 모드**:
```bash
# 인수로 받은 TASK-ID가 completed.json에 존재하는지 확인
python3 -c "
import json, sys
data = json.load(open('.claude/state/completed.json'))
task_id = sys.argv[1]
if task_id not in data:
    print(f'❌ {task_id}가 완료 목록에 없습니다.')
    sys.exit(1)
print(task_id)
" "$TASK_ID"
```

**전체 요약 모드** (`--summary`):
- completed.json의 모든 Task를 대상으로 통합 분석
- 개별 회고 대신 전체 패턴 요약 리포트 생성

### 2. 데이터 수집 (read-only)

모든 수집은 읽기 전용. 상태 파일 수정 없음.

#### 2.1 완료 이력
```bash
# completed.json에서 Task 정보
cat .claude/state/completed.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
task_id = sys.argv[1]
task = data[task_id]
print(json.dumps(task, indent=2, ensure_ascii=False))
" "$TASK_ID"
```

#### 2.2 실행 로그
```bash
# execution-log.json에서 해당 Task 이벤트
if [ -f ".claude/state/execution-log.json" ]; then
  cat .claude/state/execution-log.json | python3 -c "
import json, sys
logs = json.load(sys.stdin)
task_id = sys.argv[1]
events = [l for l in logs if l.get('taskId') == task_id]
print(json.dumps(events, indent=2, ensure_ascii=False))
" "$TASK_ID"
fi
```

#### 2.3 PR 이력
```bash
# Task에 연결된 PR들의 리뷰/코멘트 수집
gh pr list --state merged --search "$TASK_ID" --json number,title,additions,deletions,reviews,comments,createdAt,mergedAt --limit 20
```

#### 2.4 Git 커밋 이력
```bash
# Task 관련 커밋
git log --all --oneline --grep="$TASK_ID" --format="%H %ai %s"
```

#### 2.5 요구사항 스펙 (존재 시)
```bash
# docs/requirements/{TASK_ID}-spec.md
if [ -f "docs/requirements/${TASK_ID}-spec.md" ]; then
  cat "docs/requirements/${TASK_ID}-spec.md"
fi
```

### 3. 분석 (5축)

수집된 데이터를 기반으로 5가지 축에서 분석:

#### 3.1 Speed (속도)
- 총 소요 시간: 첫 커밋 ~ 마지막 PR 머지
- 스텝별 소요 시간
- PR 리뷰 대기 시간
- 병목 구간 식별

#### 3.2 Quality (품질)
- CRITICAL 이슈 발생 횟수
- 수정 라운드 수 (fix 횟수)
- 첫 리뷰 통과율 (APPROVED without fix)
- PR 코멘트 수

#### 3.3 Patterns (패턴)
- 반복 등장한 이슈 유형
- 자주 수정된 파일/영역
- 리뷰에서 반복 지적된 항목
- 스킬 실행 순서 패턴

#### 3.4 Decisions (의사결정)
- 설계 결정 사항 요약
- 트레이드오프 기록
- 기술 부채 생성 여부

#### 3.5 Lessons (교훈)
- 잘된 점 (Keep)
- 개선할 점 (Improve)
- 새로 배운 것 (Learn)
- 다음에 시도할 것 (Try)

### 4. 리포트 생성

#### 4.1 디렉토리 생성
```bash
mkdir -p docs/retro
```

#### 4.2 리포트 작성
`docs/retro/{TASK-ID}-retro.md` 파일 생성:

```markdown
# 회고: {TASK-ID} - {제목}

## 기본 정보
| 항목 | 값 |
|------|-----|
| Task ID | {TASK-ID} |
| 제목 | {제목} |
| 시작일 | {시작일} |
| 완료일 | {완료일} |
| 총 소요 시간 | {소요 시간} |
| 스텝 수 | {N}개 |
| PR 수 | {N}개 |

## Speed (속도)
{속도 분석 결과}

## Quality (품질)
| 지표 | 값 |
|------|-----|
| CRITICAL 이슈 | {N}건 |
| 수정 라운드 | {N}회 |
| 첫 리뷰 통과율 | {N}% |

## Patterns (패턴)
{반복 패턴 분석}

## Decisions (의사결정)
{주요 결정 사항}

## Lessons (교훈)
### Keep (유지)
- {잘된 점}

### Improve (개선)
- {개선할 점}

### Learn (배운 것)
- {새로운 학습}

### Try (시도)
- {다음에 시도할 것}

## Action Items
- [ ] {구체적 개선 사항}
```

#### 전체 요약 모드 리포트 (`--summary`)
`docs/retro/summary-YYYY-MM-DD.md` 파일 생성:

```markdown
# 전체 회고 요약 - {날짜}

## 통계
| 지표 | 값 |
|------|-----|
| 완료 Task 수 | {N}개 |
| 평균 소요 시간 | {N}시간 |
| 평균 스텝 수 | {N}개 |
| CRITICAL 발생률 | {N}% |

## 공통 패턴
{반복 등장 패턴}

## 주요 교훈
{통합 교훈}

## 권장 개선 사항
- [ ] {개선 사항}
```

### 5. 학습 반영 (체크리스트/컨벤션)

분석에서 **반복 패턴**이 발견되면 체크리스트 또는 컨벤션 파일에 추가를 **제안**한다.

#### 5.1 반복 패턴 감지 기준
- 동일 유형 이슈가 2회 이상 발생
- 리뷰에서 동일 항목이 2회 이상 지적
- 동일 실수가 다른 Task에서도 반복

#### 5.2 대상 파일 식별
```bash
# 체크리스트 파일 목록
ls .claude/domains/_base/checklists/*.md
ls .claude/domains/*/checklists/*.md 2>/dev/null

# 컨벤션 파일 목록
ls .claude/domains/_base/conventions/*.md
```

#### 5.3 사용자 승인 절차

**반드시 AskUserQuestion으로 승인 받은 후에만 파일 수정.**

```
발견된 반복 패턴을 체크리스트/컨벤션에 추가할까요?

### 제안 항목

1. **체크리스트 추가** → `_base/checklists/code-review.md`
   - 항목: "{반복 패턴 설명}"
   - 심각도: MAJOR

2. **컨벤션 추가** → `_base/conventions/error-handling.md`
   - 규칙: "{반복 패턴에서 도출된 규칙}"

승인 여부를 선택해주세요.
```

AskUserQuestion 옵션:
- "전체 승인" → 모든 제안 항목 반영
- "선택적 승인" → 개별 항목별 승인/거부
- "반영 안 함" → 리포트만 유지, 파일 수정 없음

#### 5.4 파일 수정 (승인 시에만)

```bash
# Edit 도구로 체크리스트/컨벤션 파일에 항목 추가
# 기존 테이블 형식에 맞춰 행 추가
```

**중요**: CLAUDE.md는 절대 수정하지 않음. 체크리스트/컨벤션 파일만 수정.

### 6. 실행 로그 기록

`.claude/state/execution-log.json`에 추가:

```json
{
  "timestamp": "{현재 시각}",
  "taskId": "{TASK-ID}",
  "skill": "skill-retro",
  "action": "retro_completed",
  "details": {"reportFile": "docs/retro/{TASK-ID}-retro.md"}
}
```

체크리스트/컨벤션 수정 시 추가 로그:
```json
{
  "timestamp": "{현재 시각}",
  "taskId": "{TASK-ID}",
  "skill": "skill-retro",
  "action": "checklist_updated",
  "details": {"files": ["{수정된 파일 경로}"]}
}
```

## 출력 포맷

### 개별 회고 완료
```
## 📝 회고 완료: {TASK-ID}

### 요약
- **Task**: {TASK-ID} - {제목}
- **소요 시간**: {소요 시간}
- **품질 점수**: CRITICAL {N}건 / 수정 {N}라운드

### 주요 교훈
- {교훈 1}
- {교훈 2}

### 리포트
📄 `docs/retro/{TASK-ID}-retro.md`

### 학습 반영
{반영 결과 또는 "제안 없음"}
```

### 전체 요약 완료
```
## 📊 전체 회고 요약

### 통계
- **완료 Task**: {N}개
- **평균 소요 시간**: {N}시간
- **CRITICAL 발생률**: {N}%

### 리포트
📄 `docs/retro/summary-YYYY-MM-DD.md`
```

## 자동 체이닝
- 없음 (독립 실행)
- skill-merge-pr 완료 시 안내 메시지만 표시됨

## 주의사항
- 데이터 수집은 읽기 전용 (backlog.json, completed.json 수정 없음)
- 체크리스트/컨벤션 수정은 반드시 사용자 승인 후에만
- CLAUDE.md 수정 금지 (체크리스트/컨벤션 파일만 대상)
- execution-log 쓰기 시 파일 미존재 시 `[]`로 생성
- 500건 초과 시 오래된 항목 아카이브
