---
name: skill-review-pr
description: PR 리뷰 - GitHub PR에 대한 5관점 통합 리뷰 수행. 사용자가 "PR 리뷰해줘" 또는 /skill-review-pr을 요청할 때 사용합니다.
disable-model-invocation: false
allowed-tools: Bash(git:*), Bash(gh:*), Read, Write, Glob, Grep, Task, AskUserQuestion
argument-hint: "{PR번호} [--auto-fix] [--mode standard|full] | config [--mode standard|full] [--agents domain,security,test] [--reset]"
complexity-hint: heavy
---

# skill-review-pr: PR 리뷰

## 실행 조건
- 사용자가 `/skill-review-pr {번호}` 또는 "PR {번호} 리뷰해줘" 요청 시
- `--auto-fix`: CRITICAL 이슈 자동 수정 후 재리뷰
- `--mode standard|full`: 이번 PR만 지정 모드로 리뷰 (일회성)
- `/skill-review-pr config`: 리뷰 모드 설정 관리

## 리뷰 모드 설정 (config 서브커맨드)

`/skill-review-pr config` 로 진입. 일반 리뷰 플로우와 분기된다.

### 명령어
| 명령어 | 동작 |
|--------|------|
| `config` | 현재 설정 표시 |
| `config --mode standard` | 프리셋 변경 (standard: domain+security) |
| `config --mode full` | 프리셋 변경 (full: 전체 3 에이전트) |
| `config --agents domain,security` | 커스텀 에이전트 조합 설정 |
| `config --agents domain,test` | 커스텀 에이전트 조합 설정 |
| `config --reset` | `review` 섹션 삭제 (자동 Tier 분류 활성화) |

### 실행 로직
1. `project.json` 읽기
2. 인자 파싱:
   - 인자 없음 → 현재 설정 표시 후 종료
   - `--mode` → `project.json`의 `review.mode` 업데이트, `review.agents` 삭제
   - `--agents` → 쉼표 구분 파싱, domain 필수 검증, `project.json`의 `review.agents` 업데이트, `review.mode` 삭제
   - `--reset` → `project.json`에서 `review` 섹션 전체 삭제
3. `project.json` 저장 (metadata.updatedAt 갱신)
4. 변경 결과 표시

### 설정 저장 형식 (project.json)
```json
{
  "review": {
    "mode": "standard"
  }
}
```
또는 커스텀:
```json
{
  "review": {
    "agents": ["domain", "security"]
  }
}
```

### 유효성 검증
- 유효 에이전트: `domain`, `security`, `test`
- **domain은 필수** — 누락 시 자동 추가 + "⚠️ domain은 필수 에이전트입니다. 자동 추가됨" 경고
- `--mode`와 `--agents` 동시 사용 불가 → 에러
- 잘못된 에이전트명 → 에러 + 유효 목록 안내

### 현재 설정 표시 형식

`project.json`에 `review` 섹션 유무에 따라 분기 출력.

**(A) review 미설정** — 자동 Tier 분류 적용:
```
📋 리뷰 모드 설정
─────────────────
모드: 자동 Tier 분류 (디폴트) — PR 특성에 따라 T0/T1a/T1b/T2/T3 자동 결정
에이전트: PR마다 0~3개 가변 (Tier 표 참조)

명시 변경: /skill-review-pr config --mode standard
커스텀:    /skill-review-pr config --agents domain,test
```

**(B) review.mode 또는 review.agents 명시** — 자동 분류 OFF:
```
📋 리뷰 모드 설정
─────────────────
모드: standard (명시)
에이전트: domain, security

자동 분류 복원: /skill-review-pr config --reset
변경:          /skill-review-pr config --mode full
커스텀:        /skill-review-pr config --agents domain,test,security
```

### config 서브커맨드 감지 후 STOP — 아래 리뷰 플로우 진행 금지.

---

## 리뷰 모드 해석 (에이전트 결정)

리뷰 실행 시 에이전트 목록을 다음 우선순위로 결정:
1. `--mode` CLI 옵션 (PR 단위 오버라이드)
2. `project.json`의 `review.agents` (커스텀)
3. `project.json`의 `review.mode` (프리셋)
4. **자동 Tier 분류** (아래 "자동 Tier 분류" 섹션 참조)

**프리셋 → 에이전트 매핑**:
| 모드 | 에이전트 |
|------|---------|
| `full` | domain, security, test |
| `standard` | domain, security |

> 4단계 자동 Tier 분류는 사용자가 `project.json`에 `review` 섹션을 명시하지 않은 경우에만 적용된다. `review.mode` 또는 `review.agents`가 설정되어 있으면 자동 분류는 비활성화된다 (사용자 의도 우선).

## 사전 조건 (MUST-EXECUTE-FIRST — 하나라도 실패 시 STOP)
1. project.json 존재
2. backlog.json 존재 + 유효 JSON
3. PR 번호 지정됨
4. PR 존재 + OPEN 상태 (`gh pr view --json state`)
5. Draft 아님

## 경량 점검
CLAUDE.md "경량 점검 프로토콜" 3단계 실행: ①PR-backlog 일치 ②Stale 감지 ③Intent 복구

## 워크플로우 진행 표시
CLAUDE.md 진행 표시 프로토콜. 현재 단계: "코드 리뷰 중 ({Tier 라벨 또는 모드 이름} — {N} 에이전트)"

## 워크플로우 상태 추적
CLAUDE.md 상태 추적 패턴. currentSkill="skill-review-pr"

## 리뷰 전 컨벤션 로딩
1. PR 변경 파일 확인 (`gh pr view {N} --json files`)
2. CLAUDE.md 트리거 테이블로 매칭 컨벤션 식별
3. 도메인 체크리스트 Read: `_base/checklists/common.md`(필수) + `{domain}/checklists/`

## 자동 Tier 분류 (sub-agent 수 자동 결정)

PR 정보 수집(Step 1) 후 PR 특성을 기반으로 sub-agent 호출 수를 자동 조정한다. **`project.json`에 `review` 섹션(`review.mode` 또는 `review.agents`)이 명시되어 있으면 본 분류는 비활성화되고 "리뷰 모드 해석"이 우선한다.**

### Tier 판정 (위에서 아래로 첫 매치 적용)

| Tier | 조건 | sub-agent | 라벨 |
|------|------|-----------|------|
| **T1a** | 변경 파일 1건 이상 · 100% 테스트 파일 변경 · ≤200줄 · 보안 키워드 0 | 1 (`pr-reviewer-test`) | Test-only |
| **T1b** | 변경 파일 1건 이상 · 100% 의존성 매니페스트 변경 · src/ 변경 0건 · 보안 키워드 0 | 1 (`pr-reviewer-security`) | Deps-only |
| **T0** | 변경 파일 1건 이상 · ≤50줄 · src/ 변경 0건 · 보안 키워드 0 | 0 (직접 리뷰) | Trivial |
| **T3** | >200줄 **OR** 보안 키워드 hit **OR** criticalPaths 매치 | 3 (domain+security+test) | Full |
| **T2** | 그 외 (catch-all 기본값) | 2 (domain+security) | Standard |

> **순서 의도**: 작은 특수 케이스(T1a/T1b)를 T0보다 먼저 평가해야 30줄 test/deps PR이 0-agent로 흡수되지 않음. T3가 T2 위인 이유는 T3가 양성 조건(OR), T2는 음성 catch-all이라서. 변경 파일 0건(rebase-only, mode-change-only 등) PR은 T1a/T1b/T0 모두 "1건 이상" 조건으로 자연 탈락 → T3 미매치 → T2 catch-all에서 사람 검토 흐름으로 진입.

### 패턴 정의

**테스트 파일** (T1a):
- 디렉토리: `tests/**`, `test/**`, `__tests__/**`, `src/test/**` (Maven/Gradle)
- 파일명: `**/*.{test,spec}.{js,ts,jsx,tsx,mjs,cjs}`, `**/*_test.{py,go}`, `**/test_*.py`, `**/*Test.{java,kt}`, `**/*Spec.{java,kt,groovy}`

**의존성 매니페스트** (T1b):
- JS/TS: `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `bun.lockb`
- Python: `requirements*.txt`, `pyproject.toml`, `poetry.lock`, `Pipfile`, `Pipfile.lock`
- JVM: `pom.xml`, `build.gradle`, `build.gradle.kts`, `gradle.lockfile`
- Go/Rust: `go.mod`, `go.sum`, `Cargo.toml`, `Cargo.lock`
- 기타: `composer.json`, `composer.lock`, `Gemfile`, `Gemfile.lock`

**보안 키워드** (대소문자 무관, **변경 파일 경로 부분문자열 매치만**): `password`, `secret`, `token`, `auth`, `cors`, `sql`, `inject`
- diff 본문은 매치 대상 아님 (false-positive 폭발 방지 — `// @author` 주석, SQL 마이그레이션 키워드, DI `@Inject` 등이 자동 T3 격상되지 않도록)
- 매치 예: `src/auth/`, `oauth-routes.ts`, `token-bucket.ts`, `migrations/202xx-add-sql-index.sql`은 hit. `src/profile.ts` 내부에 `"password"` 문자열만 있는 경우는 hit 아님
- 코드 본문 secret 누출 검출은 별도 secret-scanning 책임 영역 (본 분류기 범위 밖)

**criticalPaths** (옵셔널):
- `.claude/domains/{domain}/domain.json`에 `criticalPaths: ["src/payment/**", ...]` 배열이 있으면 변경 파일과 글롭 매치 검사
- 도메인 메타에 미정의면 본 트리거는 자연 SKIP (schema 변경 별도)

### Tier별 플로우
- **T0**: Step 1 → 2(체크리스트) → 4~7 (Step 2.5 + sub-agent 스킵, 직접 diff 확인 후 결정)
- **T1a / T1b**: Step 1 → 2 → 2.5 → 3(단일 sub-agent) → 4~7
- **T2 / T3**: Step 1 → 2 → 2.5 → 3(다중 sub-agent) → 4~7

> PR 코멘트 최상단 출력 형식은 "출력 → 분류 헤더" 섹션 참조 (SSOT).

---

## 실행 플로우

### 1. PR 정보 수집
`gh pr view {N} --json title,body,author,state,baseRefName,headRefName,files,additions,deletions`
`gh pr diff {N} > /tmp/pr-{N}-diff.txt`, `gh pr checks {N}`
diff는 임시 파일에 저장하여 에이전트가 Read로 참조하도록 한다 (프롬프트 포함 금지).

**diff 파일 생명주기**:
- 생성: Step 1에서 `gh pr diff` 결과 저장
- 공유: Step 3에서 3개 에이전트가 동일 파일 Read (재fetch 없음)
- 갱신: auto-fix 후 재리뷰 시에만 `gh pr diff`로 덮어쓰기 (코드가 변경되었으므로)
- 유지: 리뷰 프로세스 중 파일 삭제 금지 — 반복 작업 시 재활용
- 정리: PR 머지 완료 시 `rm /tmp/pr-{N}-diff.txt`

### 2. 체크리스트 검증
| 항목 | 검증 방법 | 필수 |
|------|----------|------|
| 빌드 성공 | CI 결과 | ✅ |
| 테스트 통과 | CI 결과 | ✅ |
| 린트 통과 | CI 결과 | ⚠️ |
| 라인 수 제한 | diff 분석 | ⚠️ |
| 충돌 없음 | mergeable | ✅ |

### 2.5. 도메인 × 언어 Rules 로드 (Phase 4)

`.claude/rules/{domain}/{language}/`에 도메인 비즈니스 제약 파일이 있으면 자동 참조.

**T0(Trivial) 시 SKIP** (서브에이전트 미호출이므로 전달 불필요). T1a/T1b도 도메인 에이전트가 호출되지 않으므로 `rules_paths` 전달 불필요(자연 SKIP).

#### 절차
1. `project.json`에서 `domain`, `techStack.backend` 읽기. 둘 중 하나라도 부재 시 SKIP.
2. **language 매핑**: `.claude/rules/README.md`의 "language 매핑 (SSOT)" 표를 Read로 로드 후 `techStack.backend` 값을 매칭하여 디렉토리명 도출. 표에 없는 값(`none` 포함)은 SKIP. 본 SKILL.md에 매핑 표를 복제하지 않음 — README가 단일 진실 소스(drift 방지).
3. `.claude/rules/{domain}/{language}/*.md` 글롭 (예: `find .claude/rules/healthcare/python -name '*.md' -type f`).
4. 매칭 파일 경로를 `rules_paths` 리스트에 수집.
5. **부재 시 SKIP** — 디렉토리 자체가 없거나 매칭 0개면 기존 동작 유지(에이전트에 빈 목록 전달 X).
6. `_example/_example/` 경로는 매핑 표에 없으므로 자연 SKIP.

#### 출력
`rules_paths`가 비어있지 않을 때만 PR 코멘트 헤더에 표시:
```
📋 적용 Rules: {domain}/{language} ({N}개) — {파일명1}, {파일명2}
```

#### 적용 대상 에이전트
- **pr-reviewer-domain**: `rules_paths` 전달 → 도메인 비즈니스 제약 검토에 활용
- **pr-reviewer-security**: 미전달 (보안 영역은 Phase 5 범용 보안과 분리)
- **pr-reviewer-test**: 미전달

### 3. N관점 병렬 리뷰 (모드 기반 sub-agent 선택)

**에이전트 결정**: "리뷰 모드 해석" 섹션의 우선순위로 실행할 에이전트 목록 결정.
결정된 에이전트만 **하나의 메시지에서 동시 호출**:

| sub-agent | 파일 | 관점 | 호출 조건 (모드 / Tier) |
|-----------|------|------|------|
| pr-reviewer-domain | `.claude/agents/pr-reviewer-domain.md` | 도메인 + 아키텍처 | 모드: full, standard / Tier: T2, T3 |
| pr-reviewer-security | `.claude/agents/pr-reviewer-security.md` | 보안 + 컴플라이언스 | 모드: full, standard / Tier: T1b, T2, T3 |
| pr-reviewer-test | `.claude/agents/pr-reviewer-test.md` | 테스트 품질 | 모드: full / Tier: T1a, T3 |

각 Task: Read로 agent 파일 로드 후 지침에 따라 리뷰.
**토큰 절감**: PR diff를 프롬프트에 직접 포함하지 않는다. 대신 에이전트에게 다음을 전달:
- 변경 파일 목록 (파일명 + additions/deletions 수)
- diff 파일 경로: `/tmp/pr-{N}-diff.txt`
- **rules 파일 경로 목록 (`rules_paths`) — pr-reviewer-domain 에이전트에만 전달** (Step 2.5에서 수집). 비어있으면 미전달.
- 에이전트는 해당 파일을 Read로 자유롭게 참조한다 (시야 제한 없음).

| 항목 | 값 |
|------|-----|
| timeout | 60초 |
| retry | 0회 (--auto-fix 시 자동 1회 재시도 후 스킵) |
| fallback | "⚠️ {에이전트명} 분석 불가 — 수동 확인 필요" |

**오류 처리**:
- 1개 실패: AskUserQuestion (재시도/스킵/중단). --auto-fix 시 자동 재시도→실패시 스킵
- 2개+ 실패: 즉시 중단

### 4. 결과 병합
이슈 ID 재채번: CRITICAL→C001~, MAJOR→H001~, MINOR→M001~
위반 항목 통합 테이블 (체크리스트, 항목, 심각도, 파일:라인)
CRITICAL 1개 이상 → 전체 REQUEST_CHANGES

### 5. PR 코멘트 작성
- 코멘트 본문 최상단에 **분류 헤더**(명시 `review` 설정 시 "리뷰 모드 헤더", 자동 분류 시 "Tier 헤더") + (rules_paths 비어있지 않을 때만) "적용 Rules 헤더" 삽입 — Claude의 응답 출력만이 아니라 실제 PR 코멘트 본문에도 반드시 포함. T0(Trivial)은 분류 헤더만, 적용 Rules 헤더 미출력.
`gh pr comment` — 전체 요약 (관점별 상태/이슈 수, 체크리스트 결과, 주요 피드백)
`gh api repos/.../pulls/{N}/comments` — 이슈별 인라인 코멘트 (심각도, 설명, 권장 수정 코드)

### 6. 리뷰 결정
**자기 PR 감지**: PR author == 현재 user → 승인 불가, COMMENT로 대체
- CRITICAL 0개 + 타인 PR → `gh pr review --approve`
- CRITICAL 0개 + 자기 PR → `gh pr review --comment` (승인 SKIP)
- CRITICAL 1개+ → `gh pr review --request-changes`

### 6.5 실행 로그
execution-log.json: APPROVED → action="approved", REQUEST_CHANGES → action="request_changes"

### 7. 다음 스킬

#### 기본 모드
- APPROVED → `Skill tool: skill="skill-merge-pr", args="{prNumber}"`
- REQUEST_CHANGES → 종료, "수정 후 재실행" 안내

#### --auto-fix 모드
- CRITICAL 0개 → 일반 승인 플로우
- CRITICAL 1개+ → workflowState.fixLoopCount 증가 후 `Skill tool: skill="skill-fix", args="{prNumber}"`
  - fixLoopCount 3회째 CRITICAL → skill-fix 호출 금지, REQUEST_CHANGES 즉시 중단 (루프 가드)
  - 직접 코드 수정 금지. skill-fix 없이 REQUEST_CHANGES 후 종료 금지.

## 출력
필수 포함: PR 번호/제목/작성자/브랜치, **분류 헤더(리뷰 모드 또는 Tier) + 실행 에이전트 목록**, **적용 Rules**(있을 때만), 체크리스트 결과, 관점별 리뷰 테이블(CRITICAL/MAJOR/MINOR 수), 주요 피드백 목록, 결정(APPROVED/REQUEST_CHANGES), 다음 자동 스킬

### 분류 헤더 (PR 코멘트 최상단, 둘 중 하나만 출력)

**(A) 리뷰 모드 헤더** — `project.json`에 `review` 설정이 명시된 경우:
```
🔍 리뷰 모드: standard (2/3 에이전트)
   실행: domain, security | 미실행: test
   설정 변경: /skill-review-pr config --mode full
```

**(B) Tier 헤더** — 자동 분류가 적용된 경우 (`review` 미설정):
```
🎯 자동 분류: T2 Standard (2 에이전트) — domain, security
   강제 변경: /skill-review-pr config --mode full
```

T0(Trivial)도 동일 형식으로 `T0 Trivial (0 에이전트) — 직접 리뷰`.

### 적용 Rules 헤더 (rules_paths가 비어있지 않을 때만, 분류 헤더 다음 줄)
```
📋 적용 Rules: healthcare/python (1개) — phi-logging-guard.md
```
- `rules_paths`가 비어있거나 T0(직접 리뷰)이면 본 헤더 자체를 출력하지 않는다 (노이즈 방지).

## 에러 복구
CLAUDE.md "에러 복구 프로토콜" 참조. 미존재 시 3회 재시도 후 사용자 보고.

## 주의사항
- Draft PR은 리뷰 불가
- 자기 PR은 GitHub 정책상 승인 불가 → COMMENT 후 머지 진행

### 심각도별 머지 정책 (일관 규칙 — LLM 보고 시 준수)
- **CRITICAL**: 머지 차단. 반드시 수정 후 재리뷰
- **MAJOR**: 머지 차단 **없음**. 개선 권고로 PR 코멘트에 남기되, 사용자에게 "수정 후 재리뷰"를 강요하지 않는다. 다음 PR/별도 개선 Task로 처리 가능
- **MINOR**: 참고 사항. 머지 영향 없음

> 결과 보고 시 MAJOR/MINOR를 "수정 후 재리뷰 권장"으로 표현하지 않는다. 이전 회차에서 본 표현이 있더라도 본 규칙을 우선한다. auto-fix 루프는 CRITICAL에만 적용된다 (토큰 비용 통제).
