# Phase 1: Native Hooks Framework

> **우선순위**: P0 | **의존성**: Phase 0 | **난이도**: M

## 목표

Claude Code 네이티브 훅 시스템을 도입하여 **세션 시작 자동화**, **스킬 전환 비용 제거**, **세션 종료 정리**를 구현한다.

## 범위 경계

| 이것만 한다 | 이것은 하지 않는다 |
|------------|-------------------|
| settings.json에 hooks 필드 정의 | 훅으로 코드 품질 검사 실행 (Phase 5 영역) |
| SessionStart 훅: git sync + 상태 로드 | 훅으로 린트/빌드 자동 실행 |
| PostToolUse 훅: backlog 동기화 (Write/Edit 후) | 훅 체이닝 (훅이 다른 훅 트리거) |
| Stop 훅: 잠금 해제 + continuation-plan 생성 | ECC의 Instinct 학습 (Phase 7 영역) |
| Hook Integrity Audit (health-check 확장) | 외부 스크립트 실행 |
| CLAUDE.md.tmpl "세션 시작" 섹션 훅 연동 | PreToolUse 차단 로직 (v2.1+ 검토) |

## TFT 분석 가이드

### Architect 분석 항목
1. **훅 실행 모델**: Claude Code의 hooks 이벤트 수신 방식 확인
   - `settings.json`의 hooks 필드 구조 (Claude Code 공식 스펙 확인)
   - 훅 명령어가 shell command인지 skill 호출인지
2. **PostToolUse 무한 루프 방어 (C001 — CRITICAL)**: PostToolUse(Write) 훅이 backlog.json을 Write하면 무한 재귀 발생 가능. 반드시 다음 **3단계 폴백 전략**을 검증하고 확정할 것:
   - **1단계 (경로 제외)**: 훅 트리거에서 `.claude/state/`, `.claude/temp/` 경로의 Write를 제외 → 훅이 상태 파일 수정 시 재트리거하지 않음
   - **2단계 (재진입 방지)**: 훅 실행 중 플래그(환경변수 `ACK_HOOK_RUNNING=1` 등)를 설정하여 동일 훅의 재진입 차단
   - **3단계 (기능 축소)**: 위 방어가 모두 실패할 경우, 3회 연속 트리거 감지 시 해당 세션의 PostToolUse 훅을 자동 비활성화하고 경고 출력
   - TFT는 Claude Code가 위 메커니즘 중 어떤 것을 네이티브 지원하는지 확인하고, 지원하지 않는 경우 shell script 래퍼로 구현 가능 여부를 판단할 것
3. **워크트리 환경 호환**: 여러 세션의 동시 훅 실행 시 race condition

### Security Lead 분석 항목
1. **Hook Integrity Audit 설계**: skill-health-check에 추가할 검사 항목
   - settings.json hooks 내 명령어 화이트리스트 검증
   - 외부 스크립트 참조 탐지 — **심각도 CRITICAL** (H010: 외부 스크립트는 서명 검증 불가 → 인젝션 벡터)
2. **훅 명령어 인젝션 방어 (H009 — 선행 확정 필수)**:
   - **화이트리스트 방식**: 허용 명령어를 명시적으로 정의 (`git`, `cat`, `echo`, `jq` 등)
   - **차단 패턴**: `rm`, `sudo`, `curl`, `wget`, `git reset --hard`, `git push --force`, 파이프(`|`)를 통한 외부 전송
   - **정책**: 화이트리스트에 없는 명령어는 HI-01 CRITICAL FAIL
   - TFT는 이 화이트리스트 초안을 확정하고, 도메인별 예외가 필요한지 판단할 것

### DX Lead 분석 항목
1. **CLAUDE.md.tmpl 세션 시작 섹션** 변경 사양
   - 현재: `CLAUDE.md.tmpl:51-75` 수동 git sync + `/skill-status`
   - 변경: SessionStart 훅으로 자동화, 수동 섹션을 "자동 실행됨" 안내로 교체
2. **사용자 피드백**: 훅 실행 중 사용자에게 보이는 메시지 형식

### Product Lead 분석 항목
1. **훅 비활성화 시 기존 동작 100% 유지** 확인
   - hooks 필드가 없으면 v1.x 동작과 동일해야 함

### Domain Lead 분석 항목
1. **도메인별 훅 프로파일 필요 여부**
   - fintech: merge 전 감사 로그 훅 필요?
   - 결론에 따라 Phase 4 (Layered Override)와 연동 설계

## 구현 작업 목록

### Task 1-1: settings.json hooks 스키마 정의
- 파일: `.claude/settings.json`
- 변경: `hooks` 객체 추가
  ```json
  {
    "hooks": {
      "SessionStart": [{"command": "...", "description": "..."}],
      "PostToolUse": [{"tool": "Write", "command": "..."}],
      "Stop": [{"command": "..."}]
    }
  }
  ```
- Claude Code 공식 훅 스펙에 맞춰 구조 확정 (TFT 분석 시 확인)

### Task 1-2: SessionStart 훅 구현
- 역할: 세션 시작 시 자동 실행
- 동작:
  1. git fetch + merge (워크트리 감지 포함)
  2. `.claude/state/` 상태 파일 존재 확인
  3. continuation-plan.md 존재 시 내용 출력
  4. in_progress Task 자동 감지 + 안내

### Task 1-3: PostToolUse 훅 구현
- 역할: Write/Edit 도구 사용 후 자동 실행
- 동작: backlog.json의 현재 Task lockedAt 갱신 (TTL 리프레시)
- **무한 루프 방어 (필수)**:
  - `.claude/state/`, `.claude/temp/` 경로 Write는 훅 트리거에서 제외
  - 훅 스크립트 내부에 재진입 방지 로직 포함
  - 3회 연속 트리거 시 자동 비활성화 + 경고

### Task 1-4: Stop 훅 구현
- 역할: 세션 종료 시 자동 실행
- 동작:
  1. 만료 잠금 자동 해제
  2. continuation-plan.md 생성 (현재 workflowState 스냅샷)

### Task 1-5: CLAUDE.md.tmpl 수정
- 파일: `.claude/templates/CLAUDE.md.tmpl`
- 변경: "세션 시작 시 필수" 섹션을 훅 자동화 안내로 교체
  - 수동 스크립트 → "SessionStart 훅이 자동 실행합니다" 안내
  - 훅 미설정 시 폴백 수동 절차 유지

### Task 1-6: Hook Integrity Audit (health-check 확장)
- 파일: `.claude/skills/skill-health-check/SKILL.md`
- 변경: 새 카테고리 `hook-safety` 추가
  - HI-01: settings.json hooks 명령어에 위험 패턴 탐지 (CRITICAL)
  - HI-02: 외부 스크립트 참조 탐지 (CRITICAL — 인젝션 벡터)
  - HI-03: hooks 필드 JSON 구조 유효성 (MINOR)
- 가중치: 기존 4개 카테고리 + hook-safety 추가 → 재배분

## 수정/생성 파일

| 파일 | 작업 |
|------|------|
| `.claude/settings.json` | 수정 (hooks 필드 추가) |
| `.claude/templates/CLAUDE.md.tmpl` | 수정 (세션 시작 섹션) |
| `.claude/skills/skill-health-check/SKILL.md` | 수정 (hook-safety 카테고리) |
| `.claude/domains/_base/health/_category.json` | 수정 (가중치 재배분) |
| `.claude/schemas/project.schema.json` | 수정 (hooks 상세 스키마, Phase 0에서 예약한 것 확장) |

## 성공 기준

- [ ] `settings.json`에 hooks 필드가 정의되고 Claude Code가 인식
- [ ] SessionStart 훅 실행 시 git sync + 상태 로드 자동 수행
- [ ] Stop 훅 실행 시 continuation-plan.md 자동 생성
- [ ] hooks 필드가 없는 프로젝트에서 기존 동작 100% 유지 (하위호환)
- [ ] PostToolUse 훅이 `.claude/state/` Write 시 재트리거하지 않음 (무한 루프 방어)
- [ ] PostToolUse 3회 연속 트리거 시 자동 비활성화 + 경고 출력
- [ ] skill-health-check에 hook-safety 카테고리 검사 동작
- [ ] 위험 패턴 (`rm -rf`, `sudo`) 포함 훅 → HI-01 CRITICAL FAIL
- [ ] 외부 스크립트 참조 훅 → HI-02 CRITICAL FAIL
- [ ] 훅 실행 실패(exit code ≠ 0) 시 에러 로그 출력 + 세션 정상 계속 (훅 실패가 세션을 중단시키지 않음)

## 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| Claude Code 훅 스펙이 예상과 다를 수 있음 | 중 | 높음 | TFT 분석 단계에서 공식 문서/실제 테스트로 스펙 확인 |
| PostToolUse 무한 루프 | 낮 | 높음 | 3단계 폴백: 경로 제외 → 재진입 플래그 → 3회 자동 비활성화 |
| 워크트리 동시 훅 충돌 | 낮 | 중 | 파일 잠금 or 원자적 쓰기 |
