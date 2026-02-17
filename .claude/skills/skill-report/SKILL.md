---
name: skill-report
description: 프로젝트 메트릭 리포트 - throughput, quality, code, health 4축 분석
disable-model-invocation: false
allowed-tools: Bash(git:*), Bash(gh:*), Bash(python3:*), Read, Write, Glob, Grep
argument-hint: "[--full]"
---

# skill-report: 프로젝트 메트릭 리포트

## 실행 조건
- 사용자가 `/skill-report` 또는 "리포트 생성해줘" 요청 시
- 사용자가 `/skill-report --full` 또는 "전체 리포트 생성해줘" 요청 시

## 실행 모드

| 모드 | 트리거 | 범위 |
|------|--------|------|
| 기본 | `/skill-report` | 최근 7일 또는 마지막 리포트 이후 |
| 전체 | `/skill-report --full` | 프로젝트 전체 히스토리 |

## 사전 조건 검증 (MUST-EXECUTE-FIRST)

실패 시 즉시 중단 + 사용자 보고. 절대 다음 단계 진행 금지.

```bash
# [REQUIRED] 1. project.json 존재
if [ ! -f ".claude/state/project.json" ]; then
  echo "❌ project.json이 없습니다. /skill-init을 먼저 실행하세요."
  exit 1
fi

# [REQUIRED] 2. backlog.json 존재 + 유효 JSON
if [ ! -f ".claude/state/backlog.json" ]; then
  echo "❌ backlog.json이 없습니다. /skill-init을 먼저 실행하세요."
  exit 1
fi
cat .claude/state/backlog.json | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null || {
  echo "❌ backlog.json이 유효한 JSON이 아닙니다."
  exit 1
}
```

## 실행 플로우

### 1. 데이터 수집 (read-only)

모든 수집은 읽기 전용. 상태 파일 수정 없음.

#### 1.1 백로그 데이터
```bash
cat .claude/state/backlog.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
tasks = data.get('tasks', {})
summary = {
    'total': len(tasks),
    'todo': sum(1 for t in tasks.values() if t['status'] == 'todo'),
    'in_progress': sum(1 for t in tasks.values() if t['status'] == 'in_progress'),
    'done': sum(1 for t in tasks.values() if t['status'] == 'done'),
    'blocked': sum(1 for t in tasks.values() if t['status'] == 'blocked'),
    'critical': sum(1 for t in tasks.values() if t.get('priority') == 'critical'),
}
print(json.dumps(summary, indent=2))
"
```

#### 1.2 완료 이력
```bash
if [ -f ".claude/state/completed.json" ]; then
  cat .claude/state/completed.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'완료 Task 수: {len(data)}')
for task_id, task in data.items():
    print(f'  {task_id}: {task.get(\"title\", \"\")} (완료: {task.get(\"completedAt\", \"N/A\")})')
"
fi
```

#### 1.3 실행 로그
```bash
if [ -f ".claude/state/execution-log.json" ]; then
  cat .claude/state/execution-log.json | python3 -c "
import json, sys
logs = json.load(sys.stdin)
# 최근 7일 또는 전체 필터링
print(f'실행 로그 항목 수: {len(logs)}')
"
fi
```

#### 1.4 PR 데이터
```bash
# 머지된 PR 목록
gh pr list --state merged --json number,title,additions,deletions,createdAt,mergedAt,reviews --limit 50

# 열린 PR 목록
gh pr list --state open --json number,title,additions,deletions,createdAt,reviewDecision --limit 20
```

#### 1.5 Git 커밋 데이터
```bash
# 커밋 빈도
git log --format="%ai" --since="7 days ago" | wc -l

# 커밋 타입 분포
git log --oneline --since="7 days ago" | head -50
```

### 2. 메트릭 분석 (4축)

#### 2.1 Throughput (처리량)
| 지표 | 계산 방법 |
|------|----------|
| 완료 Task 수 | completed.json 항목 수 (기간 내) |
| 평균 리드타임 | 첫 커밋 ~ 마지막 PR 머지 평균 |
| 스텝 완료율 | 완료 스텝 / 전체 스텝 |
| Task 처리 속도 | 완료 Task 수 / 기간(일) |

#### 2.2 Quality (품질)
| 지표 | 계산 방법 |
|------|----------|
| CRITICAL 비율 | CRITICAL 이슈 수 / 전체 리뷰 수 |
| 수정 라운드 평균 | fix 횟수 / PR 수 |
| 첫 리뷰 통과율 | 첫 리뷰에서 APPROVED / 전체 PR |
| 리뷰 코멘트 밀도 | 코멘트 수 / PR 수 |

#### 2.3 Code (코드)
| 지표 | 계산 방법 |
|------|----------|
| PR 평균 크기 | (additions + deletions) / PR 수 |
| 커밋 빈도 | 커밋 수 / 기간(일) |
| PR 크기 분포 | S(<100) / M(100~300) / L(300~500) / XL(500+) |
| 커밋 타입 분포 | feat / fix / refactor / docs / test / chore |

#### 2.4 Health (건강도)
| 지표 | 계산 방법 |
|------|----------|
| 오픈 Task 수 | backlog의 todo + in_progress |
| 블록된 Task 수 | backlog의 blocked |
| Stale 워크플로우 | workflowState.updatedAt 30분+ 경과 |
| 오래된 PR | 열린 PR 중 3일+ 미머지 |

### 3. 리포트 생성

#### 3.1 디렉토리 생성
```bash
mkdir -p docs/reports
```

#### 3.2 리포트 작성

`docs/reports/report-YYYY-MM-DD.md` 파일 생성:

```markdown
# 프로젝트 메트릭 리포트

- **생성일**: {YYYY-MM-DD}
- **기간**: {시작일} ~ {종료일}
- **모드**: {기본|전체}

---

## Throughput (처리량)

| 지표 | 값 | 추세 |
|------|-----|------|
| 완료 Task | {N}개 | {↑↓→} |
| 평균 리드타임 | {N}시간 | {↑↓→} |
| 스텝 완료율 | {N}% | {↑↓→} |
| 일일 처리량 | {N} Task/일 | {↑↓→} |

## Quality (품질)

| 지표 | 값 | 추세 |
|------|-----|------|
| CRITICAL 비율 | {N}% | {↑↓→} |
| 수정 라운드 평균 | {N}회 | {↑↓→} |
| 첫 리뷰 통과율 | {N}% | {↑↓→} |
| 리뷰 코멘트 밀도 | {N}개/PR | {↑↓→} |

## Code (코드)

| 지표 | 값 |
|------|-----|
| PR 평균 크기 | {N}줄 |
| 커밋 빈도 | {N}커밋/일 |
| PR 크기 분포 | S:{N} M:{N} L:{N} XL:{N} |

### 커밋 타입 분포
| 타입 | 수 | 비율 |
|------|-----|------|
| feat | {N} | {N}% |
| fix | {N} | {N}% |
| refactor | {N} | {N}% |
| docs | {N} | {N}% |
| test | {N} | {N}% |
| chore | {N} | {N}% |

## Health (건강도)

| 지표 | 값 | 상태 |
|------|-----|------|
| 오픈 Task | {N}개 | {🟢🟡🔴} |
| 블록된 Task | {N}개 | {🟢🟡🔴} |
| Stale 워크플로우 | {N}개 | {🟢🟡🔴} |
| 오래된 PR | {N}개 | {🟢🟡🔴} |

### 건강도 기준
| 상태 | 조건 |
|------|------|
| 🟢 양호 | 블록 0, Stale 0, 오래된 PR 0 |
| 🟡 주의 | 블록 1~2 또는 Stale 1~2 |
| 🔴 경고 | 블록 3+ 또는 Stale 3+ |

---

## 종합 분석

{AI 분석 결과: 전체 프로젝트 상태 요약, 주요 이슈, 개선 제안}

## 권장 조치

- [ ] {구체적 개선 사항 1}
- [ ] {구체적 개선 사항 2}
- [ ] {구체적 개선 사항 3}
```

### 4. 추세 비교 (이전 리포트 존재 시)

```bash
# 이전 리포트 존재 확인
ls docs/reports/report-*.md 2>/dev/null | sort | tail -2
```

이전 리포트가 있으면 주요 지표의 추세(↑↓→)를 표시.

## 출력 포맷

### 리포트 완료
```
## 📊 프로젝트 메트릭 리포트

### 핵심 지표
| 축 | 핵심 지표 | 값 |
|-----|----------|-----|
| Throughput | 완료 Task | {N}개 |
| Quality | 첫 리뷰 통과율 | {N}% |
| Code | PR 평균 크기 | {N}줄 |
| Health | 전체 건강도 | {🟢🟡🔴} |

### 리포트
📄 `docs/reports/report-YYYY-MM-DD.md`

### 주요 발견
- {발견 1}
- {발견 2}

### 권장 조치
- {조치 1}
- {조치 2}
```

## 실행 로그 기록
- 없음 (순수 진단 스킬)

## 자동 체이닝
- 없음 (독립 실행)

## 주의사항
- 순수 읽기 전용 (상태 파일 수정 없음)
- execution-log에도 기록하지 않음
- 리포트 파일만 생성 (`docs/reports/`)
- 이전 리포트와 비교하여 추세 표시
- `--full` 모드는 전체 히스토리를 분석하므로 시간이 오래 걸릴 수 있음
