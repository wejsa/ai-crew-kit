---
name: skill-status
description: 프로젝트 상태 확인 - 현재 작업 진행상황, 백로그 요약, Git 상태 확인
disable-model-invocation: true
allowed-tools: Bash(git:*), Read, Glob
argument-hint: ""
---

# skill-status: 프로젝트 상태 확인

## 실행 조건
- 사용자가 `/skill-status` 또는 "상태 확인해줘" 요청 시

## 실행 플로우

### 1. Git 상태 확인
```bash
git branch --show-current
git status --short
git log --oneline -5
```

### 2. 프로젝트 설정 확인
`.claude/state/project.json` 파일에서:
- **도메인**: 현재 프로젝트 도메인 (fintech, ecommerce, general 등)
- **기술 스택**: 백엔드, 프론트엔드, DB 등
- **활성 에이전트**: 사용 가능한 에이전트 목록
- **Kit 버전**: kitVersion 필드 (미기록 시 "미설정" 표시)

### 3. 백로그 상태 요약
`.claude/state/backlog.json` 파일에서:
- **todo**: 대기 중인 Task 수
- **in_progress**: 진행 중인 Task (Task ID, 제목, 현재 스텝)
- **done**: 완료된 Task 수

### 4. 계획 파일 확인
`.claude/temp/` 디렉토리에서 진행 중인 계획 파일 확인

### 5. 출력 포맷

```
## 📊 프로젝트 상태

### 프로젝트 설정
- **도메인**: {도메인명} ({도메인ID})
- **기술 스택**: {백엔드} / {프론트엔드} / {DB}
- **활성 에이전트**: {에이전트 목록}
- **Task 접두사**: {taskPrefix}
- **Kit 버전**: v{kitVersion} (kitVersion 미기록 시 "미설정" 표시)

### Git 상태
- **현재 브랜치**: {브랜치명}
- **최근 커밋**: {커밋 메시지}
- **변경 파일**: {수}개

### 백로그 요약
| 상태 | 수량 |
|------|------|
| 📋 대기 (todo) | {N}개 |
| 🔄 진행 중 (in_progress) | {N}개 |
| ✅ 완료 (done) | {N}개 |

### 진행 중인 작업
- **{Task ID}**: {제목}
  - 현재 스텝: Step {N}/{Total}
  - 브랜치: feature/{Task ID}-step{N}

### 다음 단계 추천
- `/skill-plan`: 새 작업 시작
- `/skill-impl`: 현재 스텝 개발 진행
- `/skill-impl --next`: 다음 스텝 진행
```

### 병렬 작업 현황 (--locks 옵션)

`/skill-status --locks` 실행 시 추가 출력:

```
### 현재 진행 중인 Task

| Task ID | 제목 | 담당자 | 스텝 | 잠금 파일 | 상태 |
|---------|------|--------|------|----------|------|
| TASK-001 | JWT 서비스 | dev@PC1-... | 2/3 | 3개 | 🔄 정상 |
| TASK-003 | Rate Limiter | qa@PC2-... | 1/2 | 2개 | ⚠️ 만료임박 |
| TASK-005 | 캐시 설정 | dev@PC3-... | 1/1 | 1개 | 🔴 만료 (1h 초과) |

### 잠금 상세

**TASK-001** (dev@DESKTOP-ABC-20260203-143052)
- 할당: 2026-02-03 14:30 (1시간 23분 전)
- 잠금 파일:
  - src/domain/jwt/JwtService.kt
  - src/domain/jwt/TokenValidator.kt
  - src/infrastructure/security/JwtFilter.kt

**TASK-005** 🔴 만료
- 할당: 2026-02-03 10:15 (5시간 38분 전)
- ⚠️ lockTTL(1시간) 초과 - 인계 가능
- 잠금 파일:
  - src/config/CacheConfig.kt
```

### 만료 표시 기준

| 상태 | 조건 | 아이콘 |
|------|------|--------|
| 정상 | 남은시간 > 30분 | 🔄 |
| 만료임박 | 남은시간 <= 30분 | ⚠️ |
| 만료 | lockTTL 초과 | 🔴 |

## 주의사항
- 읽기 전용 작업만 수행
- 상태 파일이 없으면 초기 상태로 간주
