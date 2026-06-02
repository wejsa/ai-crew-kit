# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.5.1] - 2026-06-02

> **skill-upgrade hooks 전파 부채 해소** — 기존 skill-upgrade가 `.claude/hooks/`를 업데이트 대상에서 누락하고 settings.json은 권한(`allow`/`deny`)만 머지해, **v2.4.0 PreToolUse 머지 게이트(스크립트 `pre-tool-use.sh` + settings.json 등록)가 기존 시드 프로젝트에 전파되지 않던** 부채를 수정. v2.0 이후 모든 hook 변경(v2.1.3 threshold·v2.2.0 init-flag·v2.3.3 worktree claim 등)이 init 시점에 고정되던 문제도 함께 해소.

### Fixed

- **`skill-upgrade` hook 스크립트 전파**: `.claude/hooks/`를 업데이트 대상 디렉토리 표 + Step 6-0 SHA256 해시 비교 목록 + Step 9 백업에 추가. 훅은 clone/세션 시 자동 실행되는 **보안 민감** 파일이므로 해시 불일치를 미리보기에서 가시화→승인 후 교체하고, 교체 후 `skill-health-check`의 `hook-safety` 카테고리가 위험 패턴을 재검한다. (누락돼 있던 `rules`도 해시 비교 목록에 함께 보정.)
- **`skill-upgrade` settings.json `hooks` 필드 동기화 (Step 12-3)**: 이전엔 `permissions.allow`/`deny`만 머지하여 신규 hook 등록(v2.4.0 `PreToolUse`)이 전파되지 않았음. 이제 이벤트별로 프레임워크 훅 항목을 추가/갱신한다. 프레임워크 훅 식별은 **경로 접두 무관 + 스크립트 basename 기준**(상대경로·`$CLAUDE_PROJECT_DIR` 절대경로 모두 인식)이라 구버전 상대경로 등록을 새 형식으로 교체해 **중복 등록을 방지**한다. 사용자 커스텀 훅(`.claude/hooks/` 미참조)은 보존.
- **`skill-upgrade` Step 11 "현재 유지" 존중**: 디렉토리 단위 복사가 사용자의 "현재 유지" 선택을 덮어쓰던 honor gap 수정 — 복사 후 백업본으로 되돌려 보존(특히 하드닝한 hook). "수동 머지"는 소스+현재 병치.

### Added (회귀 박제)

- **`tests/upgrade/test_hooks_propagation.py`** (5 정적 가드): skill-upgrade는 prose-executed라 실행 단위 테스트가 없으므로, 전파의 필요조건(업데이트 표·해시 비교 목록에 hooks 존재, settings.json hooks 동기화 문서화, Step 11 복원 절, 접두 무관 매칭)을 정적으로 회귀 가드. 부채가 재발하면 fail.

## [2.5.0] - 2026-06-02

> **스킬·에이전트별 모델 라우팅** — 토큰 비용을 작업 성격에 맞게 배분한다. 무거운 구현·빈번한 조언성 백그라운드 분석은 `sonnet`으로, 품질 판단(PR 리뷰 종합·계획·리뷰 탐지 서브에이전트)은 `opus`로 고정. 품질 안전망(버그 탐지=opus 고정, 머지 차단=결정론적 PreToolUse hook, 빌드/테스트/린트/헬스체크 게이트=모델 무관)을 유지한 채 최대 토큰 소비처인 구현 단계를 절감한다.

### Changed

- **`skill-impl` / `skill-merge-pr` → `model: sonnet`**: 구현(최대 토큰 소비처)과 머지(기계적 — 실제 차단은 PreToolUse hook이 수행)를 sonnet으로. 구현 품질의 잔여 위험은 opus 리뷰 + 결정론 게이트(빌드/테스트/린트/헬스체크)가 흡수한다.
- **`skill-review-pr` → `model: opus`**: PR 리뷰 종합·confidence×severity 매트릭스·REQUEST_CHANGES 결정은 머지 품질 게이트의 신호원이므로 opus 유지.
- **`pr-reviewer-{domain,security,test}` → `model: opus`**: 버그·보안·테스트갭 탐지를 서브에이전트 frontmatter로 **결정론적 opus 고정**. 체인 호출 시 발생할 수 있는 턴 모델 오버라이드 불확실성과 무관하게 탐지 품질을 보장 — 가장 중요한 "버그 누락 0"을 모델 라우팅 메커니즘에 의존시키지 않는다.
- **`agent-qa` / `docs-impact-analyzer` → `model: sonnet`**: 조언용·비차단 백그라운드 분석(테스트 품질·문서 영향도)은 sonnet으로. 어떤 게이트도 막지 않으므로 품질 영향 없음.

### Notes

- **`skill-plan`은 model 필드 미설정** — 디폴트(세션 모델)를 따른다. 자기 턴 직접 호출이라 사용자 디폴트 모델로 실행된다.
- **confidence 채점 Task**(skill-review-pr Step 4)는 기존대로 parent 모델 상속(self-bias 회피 설계상 강제 지정 안 함) — 본 변경과 무관. 핀은 탐지 서브에이전트(Step 3)에만 적용.
- 본 변경은 **시드되는 사용자 프로젝트의 모델 기본값**을 바꾼다. 기존 시드 프로젝트에는 `skill-upgrade`가 agents/skills 교체 시 전파된다. kit 개발 리포 자체는 skill-impl/review/merge를 실행하지 않으므로 효과는 다운스트림 프로젝트에서 발현.

## [2.4.1] - 2026-05-30

> **v2.4.0 머지 게이트 신뢰성 패치** — v2.4.0 직후 전체 프로젝트 분석에서, 방금 도입한 PreToolUse 머지 게이트의 **결정적 신호(신호 A)가 프로덕션에서 silent no-op**일 수 있음을 발견. 게이트는 `workflowState.lastReviewDecision == REQUEST_CHANGES`를 읽고 `prNumber`(정수)로 PR을 join하는데, LLM이 따르는 표준 템플릿(`CLAUDE.md.tmpl`)이 ① `lastReviewDecision`를 아예 누락하고 ② `prNumber`/`fixLoopCount`를 **문자열 placeholder**로 모델링하고 있었음 — 문자열은 schema 거부(`integer|null`) + 게이트의 숫자 join 미스. 결과적으로 자기 PR(kit 주 사용 케이스) 리뷰에서 게이트가 안 켜질 수 있던, v2.4.0이 막겠다던 바로 그 구멍의 재현. 프레임워크가 반복적으로 맞는 `additionalProperties:false` sleeper 버그 클래스(v2.1.1/v2.3.0/v2.4.0)와 동일.

### Fixed

- **`CLAUDE.md.tmpl` workflowState 템플릿** — 게이트 전제조건 복구: ① `lastReviewDecision: null` 필드 추가(skill-review-pr Step 6.5 소유 명시), ② `prNumber`/`fixLoopCount`를 문자열 placeholder → **정수/`null` 리터럴**로 교체 + 타입·소유권 주의 블록 신설(따옴표 금지 사유 = schema 거부 + 게이트 join 미스, SSOT=schema 포인터 명시), ③ "완료/부분 갱신 시 `lastReviewDecision`/`prNumber` 드롭 금지 — workflowState는 항상 전체 객체로 다시 쓴다" 경고 추가(미해결 CRITICAL PR 머지 방지).
- **`skill-backlog/SKILL.md` workflowState 예시** — 동일 누락 수정(자체 리뷰 fix-up): backlog 쓰기 프로토콜의 권위 예시(skill-impl Step 8이 "준수" 지시)도 `lastReviewDecision`/`fixLoopCount`를 누락하고 있었음 → 게이트가 이 경로로도 silent no-op 가능하던 두 번째 구멍 차단.

### Added (회귀 박제)

- **`fixtures/backlog/positive/task-with-workflowstate-and-lock.json`** — populated workflowState(`lastReviewDecision=REQUEST_CHANGES`, `prNumber`/`fixLoopCount` 정수) + `lockedBy`/`lockedAt` + `step.prNumber` 정수를 실제 shape로 검증. 기존 positive fixture는 모두 `workflowState=null`이라 이 경로를 검증 못 했음.
- **`test_schema_compliance.py` 3 케이스** — (1) 게이트가 읽는 필드 존재 + 정수 타입(schema 수용), (2) 문자열 `prNumber` schema 거부(타입 계약), (3) **템플릿 emission 검증** — `CLAUDE.md.tmpl`·`skill-backlog/SKILL.md`의 workflowState 블록을 직접 파싱해 `lastReviewDecision` 존재 + `prNumber`/`fixLoopCount` 비-문자열을 단언(템플릿이 string placeholder로 회귀하면 fail — 원래 sleeper가 살던 정확한 위치를 무장).
- **`test-pre-tool-use-merge-gate.sh` §10 (4 assertion)** — 신호 B(GitHub `reviewDecision`)를 live hook 위에서 stub `gh`로 검증: `CHANGES_REQUESTED`→block / `APPROVED`→allow / gh 실패→fail-open / 신호 A 우선. 기존엔 `CCK_GATE_NO_GH=1`로 전면 스킵되던 경로.

> **커버리지 경계**: pytest = schema 수용성 + 템플릿 emission(정적), bash §10 = live hook 동작(신호 B). 게이트의 `--argjson` 숫자 join 자체는 §2/§6/§8(신호 A) + §10(신호 B)이 실 hook 실행으로 커버.

## [2.4.0] - 2026-05-29

> **PreToolUse 머지 품질 게이트 (1순위 하네스 개선)** — 하네스 엔지니어링 리뷰에서 식별된 단일 최대 구조적 미스매치 해소: "CRITICAL은 머지 차단"이 그동안 prose 지시(skill-merge-pr/CLAUDE.md/skill-review-pr 519줄)였을 뿐 **결정적 강제가 없었다**. LLM이 review 분기를 한 번만 잘못 따라도 미해결 CRITICAL PR이 auto-merge되는 구멍. 신뢰 가능한 레이어(hook)는 bookkeeping(heartbeat/lock)만 하고, 신뢰 불가 레이어(prose+LLM)가 정작 핵심 게이트를 맡던 역전 구조를, **`gh pr merge`를 PreToolUse hook이 직접 deny**하는 것으로 바로잡음.

### Added

- **`.claude/hooks/pre-tool-use.sh` (PreToolUse / Bash 매처) — 머지 품질 게이트**: `gh pr merge` 직전 미해결 CRITICAL PR을 결정적으로 차단(`exit 2`). 차단 신호 — **A(state, 오프라인 결정적)**: PR N 소유 Task(`step.prNumber==N` 또는 `workflowState.prNumber==N`)의 `workflowState.lastReviewDecision=="REQUEST_CHANGES"`. PR 번호 SSOT는 `step.prNumber`(skill-impl Step 8)라 거기서도 join해야 발동(자체 리뷰 finding #1로 초안의 `workflowState.prNumber` 단독 join이 프로덕션 no-op임을 잡아 수정). PR 번호 추출은 토큰 기반 순수-숫자 매칭(URL `/pull/N`·플래그·선행0 정규화 — finding #2). **B(GitHub, best-effort)**: `reviewDecision==CHANGES_REQUESTED`. 둘 중 하나라도 차단이면 deny + stderr 복구 안내. **인프라 실패(jq/git/gh 부재·파싱 불가·backlog 부재·네트워크)는 fail-open(exit 0)** — 게이트 자체 장애가 정상 머지를 막지 않음. 제어 env: `CCK_MERGE_GATE=off`(전면 비활성)·`CCK_GATE_BYPASS=1`(1회 의도적 우회)·`CCK_GATE_NO_GH=1`(신호 B 스킵, 오프라인).
- **`.claude/hooks/tests/test-pre-tool-use-merge-gate.sh`** (run-all.sh 등록): **실제 backlog shape**(step.prNumber + workflowState.lastReviewDecision)로 fixture 구성해 join을 진짜로 검증. 비대상 통과 / 차단+사유 / APPROVED·COMMENT 통과 / 우회·비활성 / fail-open(backlog 부재·번호 없음·미매칭) / 추출 견고성(URL·플래그·선행0·greedy 우회) / SHA 임베드 숫자 비추출 / workflowState.prNumber 경로 / 공백 정규화. 19 assertion.
- **`backlog.schema.json` `workflowState.lastReviewDecision`** 정식 등록 (enum APPROVED/COMMENT/REQUEST_CHANGES/null): skill-review-pr Step 6.5와 skill-fix가 이미 참조했으나 schema 미등록(`additionalProperties:false`)으로 거부되던 **sleeper 해소** — 게이트 신호 A의 전제조건이자 skill-fix 모드 판정 복구.

### Changed

- **`scripts/check-hook-blocking.sh` (HI-04)**: ① **정규식 허점 메움** — 구 패턴은 `exit` 앞에 다른 내용이 있어야만 매치하여 단독 `  exit 2`를 놓쳤음(awk 기반 주석 제외 검출로 교체, 단독·복합 형태 모두 포착). ② **Gate 훅 opt-in 예외** — 파일 상단 `# hi04-exempt: gate-hook` 마커 선언 시 exit-2 검사 면제(`set -e` 검사는 유지 — fail-open 보장). Bookkeeping(비블로킹) vs Gate(설계상 블로킹) 훅 카테고리 구분을 정적 검사에 반영.
- **`.claude/settings.json`**: `PreToolUse`(matcher `Bash`, timeout 10) 훅 등록.
- **`.claude/hooks/README.md`**: "훅의 두 카테고리: Bookkeeping vs Gate" 섹션 신설(차단 정책 정반대 + fail-open 원칙 SSOT), PreToolUse 게이트 동작·env·한계 문서화.

### Notes

- **기존 사용자 업그레이드**: `settings.json` 병합으로 PreToolUse 등록을 전파하는 skill-upgrade 로직은 후속 과제. kit 개발 리포 자체는 backlog state가 없어 신호 A는 no-op(실효는 사용자 프로젝트에서 발현).
- **후속(MVP 범위 외)**: `gh pr create`(빌드 미통과 차단)·`gh pr review --approve`(자기 PR+강등 차단) 게이트는 동일 패턴 복제로 별도 PR. confidence 채점 외부 도구 위임(RFC #77)은 본 게이트가 안전망을 제공해 압박이 완화됨.

## [2.3.3] - 2026-05-29

> **SessionStart 훅 — develop 미반영 워크트리 claim 감지 (다중 워크트리 동시 선택 안전장치)** — 다중 워크트리 환경에서 한 워크트리가 Task를 claim하면 그 변경이 `worktree-<name>` 브랜치에 먼저 박힌 뒤 별도 단계로 develop SSOT에 전파된다(CLAUDE.md 워크트리 프로토콜 "상태 파일 반영" 행). 그 전파 지연 윈도우 동안 develop tip만 보는 다른 세션은 in-flight claim을 보지 못해 같은 Task를 동시 선택할 수 있었음 — `session-start.sh`가 "✓ 최신 상태 (develop)"라고 안내해 거짓 안심을 주던 사각지대. skill-plan §1.5 조기 잠금과 §0.5 TTL 자동 해제는 claim이 **develop까지 전파된 뒤**에만 유효하므로 이 윈도우를 못 막았음. 근본 차단(develop SSOT 직접 claim)이 아닌 **가시화 보완**으로, hook이 `origin/worktree-*` 브랜치를 직접 스캔해 경고한다.

### Added

- **`.claude/hooks/session-start.sh` 4단계 — develop 미반영 워크트리 claim 감지**: git sync(1단계) 직후 `origin/worktree-*` 원격 추적 ref만 타깃 fetch 후, 각 브랜치 backlog.json에서 `in_progress`이지만 현재 backlog에는 `todo`로 남은 Task를 경고. 복수 워크트리가 같은 Task를 claim하면 🔴(동시 claim), 단일이면 🔶 + assignee 표시. **현재 세션 자기 브랜치는 제외**, develop에서 이미 `in_progress`(정상 전파됨)거나 `done`/`merged`(머지 후 잔존 브랜치의 stale claim)면 미경고. R4 비블로킹 준수(모든 실패 경로 `|| true`, exit 0).
- **`.claude/hooks/tests/test-session-start-claims.sh`** (run-all.sh 등록): 베어 원격 + develop/worktree-a/b/c 브랜치로 실제 시나리오 구성. 이중 claim 감지 / 자기 브랜치 제외 / `develop=done` stale 무시 / 워크트리 브랜치 부재 graceful / dict·array backlog 양 형태 / 깨진 JSON·파일 없는 브랜치 견고성 검증. 12 assertion.

### Notes

- **한계**: `worktree-<name>` 네이티브 브랜치 명명만 감지(임의 브랜치명 수동 worktree 미지원). claim이 develop까지 전파된 뒤의 충돌은 skill-plan §1.5 claim-time 검사 영역 — hook은 todo 전파 지연 윈도우만 보완한다(근본 차단 아님).
- **사용자 영향**: 마이그레이션 불필요. SessionStart 출력에 경고 1블록이 조건부로 추가될 뿐 schema·런타임 state·자동화 로직 무변경. backlog.json 부재 또는 `origin/worktree-*` 브랜치 부재 시 완전 no-op(네트워크 호출 없음).

## [2.3.2] - 2026-05-29

> **인라인 코멘트 라벨 형식 SSOT 신설 (patch)** — v2.3.1 release notes가 "후속 (별도)"로 박제한 **P1 #2**(PR #76 자체 리뷰 사이클 2 finding #2) 해소. 인라인 코멘트 라벨 형식에 단일 진실 소스가 없어 **3곳이 단절**되어 있었음: sub-agent(`pr-reviewer-domain/security/test`)는 markdown 표 셀 텍스트(`CRITICAL`/`MAJOR`/`MINOR`)만 emit, `skill-review-pr` Step 5는 "심각도(필터 후 카테고리)"라고만 명시하고 **라벨 형식 미명세**, `skill-fix` Step 2는 `🔴 **CRITICAL**` / `[CRITICAL]` 정규식을 기대. LLM 출력 가변으로 일부 세션이 다른 형식을 emit하면 `skill-fix`가 강등/CRITICAL을 **silent 누락**할 위험이 있었음 — v2.3.1이 막은 강등 silent-isolation과 동일 버그 클래스. **옵션 A(단일 컨트롤 포인트)**: `skill-review-pr` Step 5에 라벨 형식 SSOT를 신설하고 skill-fix·sub-agent가 이를 참조하도록 정렬. **자체 /code-review 1 사이클** 결과 클린(findings 0건) — 최고 리스크인 강등 마커 `·`(U+00B7) 코드포인트가 두 파일 간 일관함을 검증. 자동화 로직(모드 분기·강등 매트릭스·fix loop 진입 조건) 무변경 — 라벨 형식 명세만 정렬. 5 files +32/-6.

### Added

- **`.claude/skills/skill-review-pr/SKILL.md` Step 5 — "인라인 코멘트 라벨 형식 (SSOT — skill-fix 파싱 계약)"** (PR #79, `89de100`): 최종 게시 라벨 형식의 단일 진실 소스 표 신설. 정상 게시 `🔴 **CRITICAL**` / `🟠 **MAJOR**` / `🟡 **MINOR**`, 강등 `🟠 **MAJOR** [원래 CRITICAL · 강등]`. confidence는 본문 끝 병기(`confidence: 85`), 이모지는 시각 보조(파싱은 `**CRITICAL**` 볼드 토큰 + `[원래 CRITICAL · 강등]` 마커 기준 — 이모지 누락 견고).

### Fixed

- **`.claude/skills/skill-fix/SKILL.md` Step 2 — 파싱 정규식 명문화 + SSOT 출처 명시**: 정상 게시 CRITICAL `\*\*CRITICAL\*\*`(이모지 무관) + `[CRITICAL]` 레거시, 강등 `\[원래 CRITICAL\s*·\s*강등\]` 마커로만 식별(라벨은 MAJOR로 렌더되므로). 단일 진실 소스가 skill-review-pr Step 5임을 명시.
- **`.claude/agents/pr-reviewer-{domain,security,test}.md` 출력 형식 — SSOT 위임 명시**: "본 에이전트는 markdown 표만 emit, 최종 인라인 코멘트 라벨은 skill-review-pr Step 5 SSOT가 결정, confidence 강등/드롭/채번 미수행" 1줄 추가.

### Notes

- **사용자 영향 (v2.3.1 → v2.3.2)**: 마이그레이션 불필요. 라벨 형식 명세 정렬만으로 schema·런타임 state·자동화 로직 무변경.
- **자체 리뷰 메타**: 7개 finder 관점(line-by-line / removed-behavior / cross-file / reuse / simplification / efficiency / altitude)을 doc SSOT 정합성 기준으로 적용. 강등 마커 `·` 코드포인트 drift(이 PR이 막으려는 버그 클래스 자체)를 byte-level 검증 → 두 파일 U+00B7 일관. findings 0건으로 fix-up 없이 머지.

## [2.3.1] - 2026-05-28

> **skill-fix 강등 CRITICAL 인지 (patch)** — v2.3.0 PR #76이 도입한 confidence 매트릭스에서 강등된 CRITICAL이 MAJOR 라벨로 게시되어 `skill-fix`가 사전조건 `🔴 CRITICAL 존재` 체크에 매치 못해 silent 격리되던 결함 해소. 사용자가 강등 경고 헤더(`⚠️ 강등된 CRITICAL N개`)를 보고 `/skill-fix {N}` 수동 호출 시 강등 항목도 fix 후보로 인정. 호출 모드별 분기: **auto-fix 모드**(`workflowState.fixLoopCount` ≥ 1 **AND** `lastReviewDecision="REQUEST_CHANGES"`)는 정상 게시 CRITICAL만(SSOT — false-positive 진동 차단). **수동 호출 모드**(그 외)는 정상 + 강등 둘 다. **자체 /code-review 1 사이클**에서 fixLoopCount 단독 판정의 silent-isolation 재발 시나리오(직전 auto-fix 잔재 → manual 호출 오분류) 발견 → `lastReviewDecision`을 AND 조건으로 묶어 엄격 정의. `workflowState.lastReviewDecision`은 skill-review-pr Step 6.5에서 매 리뷰마다 갱신(APPROVED/COMMENT/REQUEST_CHANGES). 부수로 커밋 메시지 ID 표기 SSOT 단일화(정상=`[C{NNN}]`, 강등=`[H{NNN}(원래 CRITICAL · 강등)]`).

### Fixed

- **`.claude/skills/skill-fix/SKILL.md` — 강등 CRITICAL 인지 모드별 분기** (PR #78, 9cd060b):
  - 사전조건 #5: "fix 후보 이슈 존재"로 일반화 + 모드별 정의(auto-fix는 `fixLoopCount ≥ 1 AND lastReviewDecision="REQUEST_CHANGES"`, 수동은 그 외)
  - Step 2 파싱: `[원래 CRITICAL · 강등]` 접두로 강등 항목 매치. 이슈에 `isDemoted` 마커 부여
  - Step 6 커밋 메시지 ID 표기 SSOT 단일화
  - Step 7 수동 호출 + 강등 fix 시나리오 흐름 명시(자동 재호출 X)
  - 주의사항에 v2.3+ 강등 매트릭스 인지 + 자기 PR chain 차단 흐름 명시
- **`.claude/skills/skill-review-pr/SKILL.md` Step 6.5 — `workflowState.lastReviewDecision` 갱신**: skill-fix가 auto-fix vs 수동 모드를 fixLoopCount 단독이 아닌 lastReviewDecision과 함께 정확히 분기하도록 매 리뷰마다 결정값(`APPROVED`/`COMMENT`/`REQUEST_CHANGES`) 저장. 직전 auto-fix 루프가 APPROVE로 끝난 뒤 사용자가 강등 항목을 수동 fix 시도하는 silent-isolation 재발 시나리오 차단.

### Notes

- **사용자 영향 (v2.3.0 → v2.3.1)**: 마이그레이션 불필요. `workflowState.lastReviewDecision` 필드 신설은 in-session state라 schema 변경 X — 다음 skill-review-pr 호출이 자동 갱신.
- **자체 리뷰 메타**: PR #78 첫 push가 본 PR이 차단하려던 silent-isolation 시나리오를 fixLoopCount 잔재로 그대로 재발시킬 수 있음을 자체 1 사이클에서 발견 → fix-up commit `6fc89ce`로 lastReviewDecision AND 조건 도입. fix-up 후 머지. 본 패치 자체가 "fix-up 사이클이 안전성 필수" 메타 학습의 실증.
- **후속 (별도 issue)**: P1 #2 — skill-review-pr/sub-agent 인라인 코멘트 라벨 형식 SSOT 부재(`🔴 **CRITICAL**` / `[CRITICAL]` 정규식이 sub-agent 출력 형식 가변에 약함). 별도 PR로 sub-agent 출력 형식 SSOT 추가 필요.
- **참고 (v2.3.1 정정 commit)**: 본 PR이 해소한 항목은 v2.3.0 PR #76 자체 리뷰 **finding #14**(사이클 1 분류 번호) — GitHub Issue #14가 아님(GitHub Issue #14는 무관한 v1.44.0 기술 스택 추천 작업으로 이미 closed). PR #78 commit/release notes에 박제된 `Closes #14` 키워드는 해당 issue에 영향 없음(이미 closed). 본 항목으로 정정 명시.

## [2.3.0] - 2026-05-28

> **skill-review-pr 헤비함 감소 2단계 (minor)** — PR 리뷰가 매번 3-agent 병렬 호출 + sub-agent 도출 이슈 전부 게시 정책으로 사용자 토큰 폭주·노이즈 부담이 컸음을 진단(체감 컨텍스트 1.7K~1.9K 줄 × 3 병렬 + 모델 미지정 → 부모 상속 = 사실상 Opus 3개). 두 PR로 분리 해소: **PR #75 1단계** = PR 특성 기반 자동 Tier 분류(T0 Trivial / T1a Test-only / T1b Deps-only / T2 Standard / T3 Full)로 흔한 작은 PR이 가벼운 경로로 자동 라우팅. **PR #76 2단계** = sub-agent 도출 이슈를 독립 채점 단계(Step 3.5)로 confidence 0-100 부여 후 severity × confidence 매트릭스(CRITICAL conf<critical은 MAJOR 강등 게시·드롭 X로 누락 위험 차단)로 게시·결정 자동 필터링 + `review.thresholds` 외부화. 부수로 `project.schema.json`에 `review` 섹션(mode/agents/thresholds) 정식 등록 — v1.36.0~v2.2.0까지 `/skill-review-pr config`가 추가하던 `review.*` 값이 top-level `additionalProperties: false`에 silent 위반하던 sleeper 해소. **자체 /code-review → fix-up → 재리뷰 사이클**로 두 PR 각각 P0 안전 회귀 5~6건씩 발견·해소(silent ship, 머지 차단 escalation, 매트릭스 모순). 2단계 사이클 2에서 본질적 design trade-off 발견(confidence 정수 + 단일 임계치 게이트의 한계) → α 옵션(현 iteration 머지 + v2.4 재설계 RFC 분리) 적용. 두 PR 합산 19 files +850/-90.

### Added

- **`skill-review-pr` 자동 Tier 분류 (PR #75, `3f2bad4`)**: `project.json`에 `review.mode`/`review.agents` 미설정 시 PR 특성(변경 줄 수·테스트/의존성 파일 비율·`src/` 변경 여부·보안 키워드·`criticalPaths` 매치) 기반으로 T0~T3 5단계 자동 분류. 매트릭스 표 순서가 곧 첫 매치 우선순위(T1a → T1b → T0 → T3 → T2) — 작은 test/deps PR이 T0에 흡수되지 않음. `review` 명시 설정은 자동 분류 비활성화(사용자 의도 우선). 분류 결과 헤더 PR 코멘트 본문에 노출(`🎯 자동 분류: T2 Standard (2 에이전트) — domain, security`).
- **`skill-review-pr` Confidence 채점 + 결정 매트릭스 (PR #76, `0eaa0d4`)**: Step 3 sub-agent 결과를 Step 3.5 독립 채점(self-bias 회피 + 채점 Task에 CLAUDE.md/매칭 컨벤션/`rules_paths`(domain 이슈) 전달) → severity × confidence 매트릭스(CRITICAL conf<critical → MAJOR 강등 게시·드롭 X / MAJOR conf<major → 드롭 / MINOR conf<minor → 드롭) → 자기 PR + 강등 CRITICAL ≥1이면 자동 chain 차단(skill-merge-pr/skill-fix 미호출, sticky 경고). T0(Trivial)은 채점·매트릭스 우회(legacy `CRITICAL ≥1 → REQUEST_CHANGES` 보존). 동시 채점 Task ≤10(chunk), 총 ≤30(절대 상한, 초과 시 상위 채번·나머지 fallback). 채점 실패(파싱/timeout) 시 1회 재시도 → confidence=critical 임계치 값 fallback + `scoring-failure-fallback` 로그 마커.
- **`project.schema.json` `review` 섹션 정식 등록**: `review.mode`(enum: full/standard), `review.agents`(items enum: domain/security/test + `contains: {const: domain}` 강제 — 수동 편집 우회 차단), `review.thresholds`(critical/major/minor — critical `minimum: 50`로 false-positive 게이트 무력화 차단, 각 키 디폴트 80/60/50 독립 fallback). `not: {required: [mode, agents]}`로 mode/agents 상호 배타 강제. critical ≥ major ≥ minor ordering은 JSON Schema cross-field 비교 한계로 schema 표면 강제 X — Step 4 sanity check + `validate-schema.sh` ordering 블록 + ordering-violation fixture 3중 방어선.
- **CI fixture 신규 9종** (`schemas/fixtures/`):
  - Positive 4: `v2-review-mode-full.json` / `v2-review-agents-custom.json` / `v2-review-thresholds-full.json` / `v2-review-thresholds-partial.json` (독립 fallback 검증)
  - Negative 5: `review-mode-and-agents-both.json` (not 제약) / `review-critical-below-minimum.json` (≥50 강제) / `review-agents-unknown.json` (enum) / `review-agents-missing-domain.json` (contains) / `review-thresholds-ordering-violation.json` (별도 ordering 블록에서 감지)
  - 검증: `validate-schema.sh` 21/21 PASS (positive 8 + negative 11 + ordering 1 + 기존 1).
- **`pr-reviewer-test` T1a "테스트 자체 품질 모드" 분기**: 소스 변경 0 + 테스트 100% 변경 시 소스↔테스트 매핑 절차 건너뛰고 신규 테스트의 assert 유효성/경계값/스멜/도메인 체크리스트 커버를 우선 평가. T1a에서 false-negative 누락 차단.

### Changed

- **`skill-review-pr` 결정 분기 — 자기 PR + 강등 가드 신설**: 기존 `CRITICAL 0개 + 자기 PR → COMMENT` 단일 분기 → 5행 표 (CRITICAL ≥1 우선, 강등 ≥1 + 자기 PR → chain 차단, 강등 ≥1 + 타인 PR → APPROVE chain 진행 throughput 보존, 강등 0 정상 분기). REQUEST_CHANGES 우선이라 자기 PR + CRITICAL + 강등 동시 케이스는 REQUEST_CHANGES로 흡수.
- **Step 7 다음 스킬 → Step 6 매트릭스 SSOT 참조 재구성**: chain 차단 분기 중복 제거. 모드별 동작은 Step 4 매트릭스의 chain 컬럼만 따른다 — 분기 정의 단일화.
- **`skill-review-pr config --reset` 의미 갱신**: 기존 "디폴트(full) 복원" 거짓 안내 → "`review` 섹션 삭제 (자동 Tier 분류 활성화)". 현재 설정 표시도 (A) 자동 분류 / (B) 명시 설정 분기로 갱신해 디폴트 동작과 사용자 멘탈 모델 정렬.
- **보안 키워드 매치 채널 — diff 본문 제외**: 기존 "변경 파일 경로 또는 diff 본문 매치"로 false-positive 폭발(`// @author` 주석·SQL 마이그레이션·DI `@Inject` 등이 모두 T3 격상) → "변경 파일 경로 부분문자열 매치만". 코드 본문 secret 누출 검출은 secret-scanning 책임 영역으로 분리 명시.
- **`scripts/validate-schema.sh` — ordering 검증 블록 신설**: positive fixture 전체 + ordering-violation negative fixture를 Python heredoc으로 cross-field 검증. JSON Schema 한계 보완.

### Notes

- **사용자 영향 (v2.2.0 → v2.3.0)**: 마이그레이션 불필요. `review` 섹션 미설정 사용자(=다수)는 디폴트 동작이 "full 3-agent"에서 "자동 Tier 분류(대부분 T2 2-agent, T3는 보안 키워드 hit / 200줄 초과 / criticalPaths 매치 시 강제)"로 변경. **흔한 작은 PR은 헤비 경로 자동 우회 + 보안/대규모 변경은 여전히 풀 리뷰**. 강제 변경: `/skill-review-pr config --mode full`. `review.thresholds` 옵셔널 신규 — 디폴트 80/60/50 적용.
- **알려진 한계 (v2.4 재설계 — RFC #77)**: 1) confidence 정수 + 단일 임계치 게이트의 본질적 trade-off(fallback 80은 MAJOR/MINOR 임계 모두 통과 / Rubric 75↔임계 80 갭으로 컨벤션 미명시 진성 CRITICAL 자동 강등), 2) 강등 H{NNN} ID 채번 재리뷰 시 shift, 3) 강등 개념 7가지 용어 혼용, 4) Step 4 매트릭스 ↔ Step 6 5분기 매핑 부재, 5) H/M prefix 통념 반대 매핑. 본 release는 "confidence 기반 false-positive 필터의 **첫 iteration**" — RFC에 방향 A(band-gap) / B(multi-criteria) / C(외부 도구 위임) / D(단순화) 4안 박제.
- **후속 PR**: PR #76 자체 리뷰 **finding #14**(skill-fix가 강등 CRITICAL 미감지 — PR #76 직접 후속, v2.3.1에서 해소), #77 RFC 답변 + 실 PR 200건 채점 시뮬레이션 데이터 수집. (※ "#14"는 본 release 자체 리뷰의 finding 분류 번호로 GitHub Issue #14가 아님)
- **메타 학습**: 두 PR 자체 /code-review 사이클에서 각각 P0 5~6건 발견 — fix-up 후 재리뷰 1 사이클이 안정성 필수. mini-Ralph 자동 진행 모드(사용자가 결정 옵션 매번 확인 부담 해소)는 단순 fix-up엔 효과적이나 본질적 design trade-off는 인터셉트 필요.

## [2.2.0] - 2026-05-24

> **lock 의미 schema 정렬 + 초기 셋업 트리거 보호 (minor)** — v2.1.4 PR-A의 후속 의미 정렬 PR-B. `backlog.schema.json`이 `assignee`/`assignedAt`(불변 할당)만 정의해 두고 hook과 진단·헬스체크가 사실상 `lockedBy`/`lockedAt`(가변 잠금 heartbeat)을 별개로 사용해온 어휘 불일치를 정식 schema 필드로 박제(옵션 A — hook 코드 무변경, schema에 신규 필드 추가). 부가로 v2.1.4 PR-A 작업 도중 라이브 시연된 B5(skill-init 작업 자체가 10초/3회 임계를 발동시켜 자동 비활성화) false-positive를 `.claude/state/init-in-progress.flag` 마커로 카운터 진입 자체 차단. skill-init Step 0/11 + skill-onboard Step 0/7에 마커 생성/제거 절차 + 1시간 TTL stale 자동 회수로 SKILL 비정상 종료 대비. hooks/README/skill-health-check 가이드 어휘가 모두 schema 정합 명시. v2.1.4가 미처 손대지 못한 `test-post-tool-use-auto-disable.sh` array fixture도 dict로 마이그레이션하여 schema 정합 100% 달성. 14/14 PASS (PR-A 13 + 신규 1). minor 의미: schema 확장(옵셔널 필드 추가, backward-compatible)이지만 의미 모델이 정식 정의되므로 patch 대신 minor.

### Added

- **`.claude/schemas/backlog.schema.json` — `lockedBy`/`lockedAt` 필드 추가**: `task` 정의에 옵셔널 필드 2종 추가 (둘 다 `["string", "null"]` / `["string", "null"] format date-time`). `assignee`/`assignedAt`(불변 할당)와 의미 분리 명시 — `lockedBy`는 현재 잠금 보유 세션(가변), `lockedAt`은 PostToolUse heartbeat 시각(가변, Stop 10분 TTL 만료 시 null). 기존 `assignee`/`assignedAt` description에도 "불변" 의미 보강. 마이그레이션 영향 0(옵셔널 필드 추가, 기존 backlog.json은 그대로 통과).
- **`.claude/hooks/post-tool-use.sh` — 0-A단계 init-in-progress.flag 체크 (v2.2.0)**: STATE_DIR 변수군에 `INIT_FLAG` + `INIT_FLAG_TTL_SECONDS=3600` 신설. 0단계(hook-disabled.flag) 직후, jq 의존성 체크 전에 마커 존재 시 즉시 exit 0(카운터 진입 자체 차단). 마커 mtime이 TTL 초과면 자동 회수 + log_err 기록(stale 마커 안전장치). stat -c %Y(Linux) / -f %m(macOS) fallback 패턴.
- **`.claude/skills/skill-init/SKILL.md` Step 0/11 — 트리거 보호 마커 절차**: Step 1 직전 `Step 0: 트리거 보호 마커 생성` 신설(`mkdir -p .claude/state && touch init-in-progress.flag`), Step 11 끝에 `트리거 보호 마커 제거` 절차 명시(`rm -f init-in-progress.flag`). 실패 경로(`|| true`) graceful + 1시간 TTL 안전장치 양면 방어.
- **`.claude/skills/skill-onboard/SKILL.md` Step 0/7 — 동일 패턴**: 사전 조건 직후 Step 0 마커 생성, Step 7 완료 리포트 직후 마커 제거. abort 경로(빈 디렉토리 N 선택 등)에서도 가능한 한 제거 명시.
- **`.claude/hooks/tests/test-init-flag-bypass.sh` (신규)**: 5 assertion × 3 시나리오 — (1) 마커 존재 + 5회 호출 → flag/counter 둘 다 미생성(카운터 진입 자체 차단), (2) 마커 부재 + 4회 → 정상 비활성화(회귀 보호), (3) stale 마커(1h+1s 후퇴) + 4회 → 자동 회수 + 정상 비활성화. `touch -d "$past_iso"` / `touch -t "YYYYMMDDHHMM"` 양쪽 fallback.

### Changed

- **`.claude/hooks/README.md` — 3단계 표 → 0-A 단계 포함 + schema 정합 명시**: PostToolUse 동작 표에 `0-A | init-in-progress.flag 존재 (mtime ≤ 1h) | 즉시 exit 0` 행 추가. "lockedBy/lockedAt은 v2.2.0부터 backlog.schema.json 정식 필드(가변 잠금 의미, assignee/assignedAt(불변 할당)와 구분)" 명시. 단계 표 헤더 "3단계 무한 루프 방어 + init 보호 마커" 갱신.
- **`.claude/skills/skill-health-check/SKILL.md` SI-03 — schema cross-ref**: "lockedBy 필드가 있는 Task" 검사 설명에 "둘 다 v2.2.0+ backlog.schema.json 정식 필드 — 가변 잠금 의미, assignee/assignedAt(불변 할당)와 구분" 명시. autoFix 설명에 "lockedBy/lockedAt을 null로" 명시. stop.sh 10분 TTL 대비 본 검사 1시간 TTL이 보수적인 이유 추가.
- **`.claude/hooks/tests/test-post-tool-use-auto-disable.sh` fixture 마이그레이션 (v2.1.4 잔재)**: v1 array `[{...}]` → schema 정합 dict `{"T1": {...}}`. v2.1.4 PR-A 시점에 `.tasks[0]` 인덱싱이 우연히 동작(heartbeat 경로 미진입)해 마이그레이션 누락. 본 PR로 schema↔fixture 정합 100% 달성.
- **`.claude/hooks/tests/run-all.sh`**: 신규 `test-init-flag-bypass.sh` 등록. 13 → 14 케이스.

### Notes

- **사용자 영향 (v2.1.4 → v2.2.0)**: 마이그레이션/액션 불필요. schema 신규 필드는 옵셔널이라 기존 backlog.json 그대로 호환. hook 동작은 마커 마련 외 변화 없음(0단계가 0-A로 한 칸 분기 추가만).
- **루트 backlog.json/project.json 수동 이동 안내**: PR-A에서 분리한 후속 작업. 기존에 잘못 루트에 생성한 프로젝트는 다음 명령으로 이동 권장. `git mv backlog.json .claude/state/ && git mv project.json .claude/state/ && git commit -m "fix: move backlog/project state to v2 SSOT path"`. v2.0+ hook이 `.claude/state/` SSOT에서만 작동하므로 이동 전에는 hook 무동작(corruption은 PR-A로 차단됨).
- **변경 범위**: 9 파일 (schema 1 + hook 1 + skill 2 + 테스트 신규 1 + 테스트 마이그레이션 1 + run-all 1 + 가이드 2) + 버전 메타 3. 검증: `bash -n` PASS, `run-all.sh` 14/14 PASS, `validate-schema.sh` 12/12 PASS.
- **PR-A 메타 사건 종결**: v2.1.4 작업 중 본 리포에서 발생한 PostToolUse 자동 비활성화 false-positive를 본 PR의 init-in-progress.flag 마커가 근본 차단. 향후 skill-init/onboard 사용 중 동일 사건 재발 없음.

## [2.1.4] - 2026-05-24

> **backlog.json corruption 차단 + 경로 SSOT 정합 (patch)** — schema 정합성 검토 중 발견된 데이터 손실 가능 결함 2건 + SSOT 모순 1건 일괄 차단. `backlog.schema.json:73-79`은 `tasks: type=object`(key=Task ID dict)로 정의되어 있으나 `post-tool-use.sh:163` / `stop.sh:83`이 `.tasks |= map(...)` 사용 — jq `map(f)`는 array 변환 연산자라 dict 적용 시 `{"TASK-001":...,"TASK-002":...}` → `[{...},{...}]`로 평탄화되어 **key가 영구 손실**되는 corruption. 현재까지는 `lockedBy` 필드 불일치(schema는 `assignee`)로 `HAS_OWNED=false`가 우연히 corruption 분기를 막아왔으나, 이후 의미 정렬 PR에서 `lockedBy`를 첫 정렬할 때 즉시 활성화되는 sleeper. `with_entries(.value |= ...)`로 dict 의미 유지하며 동일 결과 산출. 부수적으로 `skill-init/SKILL.md` Step 10 `project.json`/`backlog.json` 생성 절차에서 경로 미명시로 인해 LLM이 프로젝트 루트에 작성하던 결함과, line 486 주석 "프로젝트 루트. `.claude/state/`가 아님"의 `CLAUDE.md.tmpl:308/310` SSOT 정면 모순을 함께 해소. 회귀 보호 신규 테스트 `test-tasks-dict-shape.sh`(11 assertion, dict type/key 보존 + heartbeat + 만료 해제 + 빈 dict 코너) 추가, 기존 4개 array fixture를 schema 정합 dict로 마이그레이션. 13/13 PASS.

### Fixed

- **`.claude/hooks/post-tool-use.sh:163-167` corruption 차단**: `.tasks |= map(...)` → `.tasks |= with_entries(.value |= (...))` 전환. jq `map(f) = [.[] | f]`로 array 변환되어 schema-정합 dict가 array로 평탄화 + key 영구 손실되던 sleeper bug 차단. 현재 `lockedBy`/`assignee` 필드 불일치(B3, PR-B 대상)로 분기 미진입 상태이나, 의미 정렬 직후 활성화될 위험을 선제 차단. 동작 변화 0(B3 미해결 상태 그대로면 무동작 유지).
- **`.claude/hooks/stop.sh:80-89` corruption 차단**: 만료 lock 해제 블록도 동일 패턴(`with_entries(.value |= ...)`) 적용. backlog.schema.json:73-79 정합. dict 키 보존하면서 만료된 task의 `lockedAt`/`lockedBy`만 null로 초기화.
- **`.claude/skills/skill-init/SKILL.md:486` SSOT 모순 정정**: "프로젝트 루트. `.claude/state/`가 아님 — v2.0.3 cleanup 대상이며 사용자 프로젝트엔 부재" 주석 삭제 — `CLAUDE.md.tmpl:308`(backlog.json은 `.claude/state/backlog.json`), `:310`(project.json), hook의 `STATE_DIR=".claude/state"` 하드코딩과 정면 모순이었음. v2.0.3 cleanup은 kit clone에서 init할 때만 적용되는 일회성 정리이지 사용자 프로젝트 부재 근거가 아님. 정정 후: `.claude/state/{project,backlog}.json` 경로 그대로 백업 + 루트 폴백 감지(v1 잔재용).
- **`.claude/skills/skill-init/SKILL.md` Step 10 경로 명시**: 파일 생성 절차 1·2번 헤더에 `(경로: .claude/state/project.json)` / `(경로: .claude/state/backlog.json)` 명시. 상단에 "상태 파일 경로 SSOT (v2.0+)" 박스 추가 — `mkdir -p .claude/state` 선행 의무, 루트 작성 시 hook/SSOT 어긋남 명시. LLM이 절차 텍스트만 보고 루트에 작성하던 결함 차단.

### Added

- **`.claude/hooks/tests/test-tasks-dict-shape.sh` (신규)**: schema-정합 dict fixture 회귀 보호. 11 assertion 3 시나리오 — (1) PostToolUse heartbeat 후 `.tasks` 타입 `object` 유지 + 키 3개 보존 + 소유 Task만 lockedAt 갱신 + 미소유/완료 Task 미변경, (2) Stop 만료 해제 후 동일 보존 + 만료 Task만 `lockedAt`/`lockedBy` null, (3) 빈 dict (`tasks: {}`) 호출 후에도 type=object 유지. 향후 `map(f)` 재발 즉시 fail.

### Changed

- **`.claude/hooks/tests/{test-lock-expiry,test-post-tool-use-path-exclude,test-post-tool-use-lock-reentry,test-post-tool-use-heartbeat}.sh` fixture 마이그레이션**: v1 array `.tasks: [{...}, {...}]` → schema 정합 dict `.tasks: {"T1": {...}, "T2": {...}}`로 통일. assertion도 `.tasks[0].lockedAt` → `.tasks["T1"].lockedAt` 인덱싱 변경. hook의 `with_entries` 전환으로 array fixture가 호출 후 `{"0":...}` 객체로 변환되어 깨지던 회귀 차단. 본 PR 정신(schema↔fixture 정합) 자기 적용.
- **`.claude/hooks/tests/run-all.sh`**: 신규 `test-tasks-dict-shape.sh` 등록. 12 → 13 케이스.

### Notes

- **사용자 영향 (v2.1.3 → v2.1.4)**: 마이그레이션/액션 불필요. hook 동작 변화 0(현재 분기 미진입이므로). 신규 init 프로젝트는 `.claude/state/` 경로 자동 적용. **기존에 잘못 루트에 `backlog.json`/`project.json`을 생성한 프로젝트**는 `git mv backlog.json .claude/state/ && git mv project.json .claude/state/`로 수동 이동 권장(자동 마이그레이션은 PR-B 후속에서 skill-health-check 감지 항목으로 도입 예정).
- **lockedBy/lockedAt vs assignee/assignedAt 의미 정렬**(B3/B4): 본 PR 범위 외. PR-B(v2.2.0)에서 `backlog.schema.json`에 `lockedBy`/`lockedAt` 필드 추가 + diagnose.sh/health-check 가이드 정렬 + B5(트리거 카운터 init/onboard 중 일시 무시 마커) 동시 처리. 본 PR은 corruption 차단 + 경로 SSOT만 다룸(긴급도 분리).
- **변경 범위**: 9 파일 (hook 2 + skill-init SKILL.md 1 + 신규 테스트 1 + 마이그레이션 테스트 4 + run-all.sh 1) + 버전 메타 3. 검증: `bash -n` PASS, `run-all.sh` 13/13 PASS.

## [2.1.3] - 2026-05-17

> **hook 진단 도구 + threshold 외부화 (patch)** — PostToolUse 자동 비활성화 발동 후 "지금 어떻게 할 건가" 결정에 필요한 진단·영향 평가·복구 가이드가 README 산문 곳곳에 흩어져 있어 LLM이 사용자 질문을 받았을 때 transcript 의존적 추측으로 끝나던 UX 결함 해소. **read-only** `diagnose.sh` 신설로 flag/counter/lock/log/settings를 한 번에 점검하고 영향 결론(🟢/🟡)을 단정. `post-tool-use.sh` 임계값(`TRIGGER_MAX=3`)·윈도우(`TRIGGER_WINDOW_SECONDS=10`)를 `CCK_HOOK_THRESHOLD`/`CCK_HOOK_WINDOW_SEC` 환경변수로 외부화 — 멀티파일 Edit이 잦은 단독 작업자가 기본값(3)이 너무 빡빡할 때 자체 완화 가능. **회귀 0**: env 미설정 시 동작 100% 동일, TFT R1/R2 권장값 그대로. 비숫자/0 값은 무시되고 기본값 fallback. README "자동 비활성화 진단 가이드" 섹션 신설(원인 TOP 3, hook-trigger-count 포맷 해석, 복구 결정 트리, "Stop 부재 ≠ 미동작" 명시, 임계값 권장값 표). 회귀 테스트 2건 추가로 12/12 PASS.

### Added

- **`.claude/hooks/diagnose.sh` (신규)**: read-only hook 진단 도구. 4개 섹션 출력 — `[등록 상태]`(settings.json + 스크립트 존재), `[PostToolUse]`(flag/counter/trigger-count 해석 + 추정 원인 + env override 가시화), `[Stop]`(continuation-plan + 만료 lock 후보 카운트), `[영향 평가]`(in_progress + lockedBy 기반 🟢/🟡 결론), `[행동 옵션]`(복구/임계값 완화/방치 선택지). `backlog.json`/`flag`/`counter`/`continuation-plan.md` 어느 것도 mutate하지 않음(SHA256 회귀 테스트로 검증). jq/git 미설치, settings.json/backlog.json 부재 시 가용 항목만 출력하고 exit 0 graceful skip.
- **`.claude/hooks/README.md` 진단 가이드 섹션 신설**: "흔한 원인 TOP 3", "`hook-trigger-count` 포맷 해석", "복구 결정 트리", "Stop 부재 ≠ 미동작", "임계값 권장값 표"(단독/팀/자동화 패턴별). 진단 도구 사용 예시 출력 첨부.
- **회귀 테스트 2건**: `test-threshold-env-override.sh`(4 시나리오: THRESHOLD=5/비숫자/0/미설정), `test-diagnose.sh`(6 시나리오: clean/flag+no-lock/flag+lock/no-backlog/no-settings/read-only SHA256 검증). `run-all.sh` 등록.

### Changed

- **`.claude/hooks/post-tool-use.sh` 임계값 외부화**: 하드코딩 `TRIGGER_WINDOW_SECONDS=10` / `TRIGGER_MAX=3` → `CCK_HOOK_WINDOW_SEC`/`CCK_HOOK_THRESHOLD` env override. 미설정·비숫자·0 이하 값은 기본값(10/3) fallback. **회귀 0** — 기존 `test-post-tool-use-auto-disable.sh` 4회째 발동 시나리오 100% 유지.

### Notes

- **사용자 영향 (v2.1.2 → v2.1.3)**: 마이그레이션/액션 불필요. 기본 동작 100% 동일. 멀티파일 Edit 작업이 잦아 자동 비활성화가 자주 발동했다면 `export CCK_HOOK_THRESHOLD=8`로 완화 가능.
- **권장 사용 흐름**: 자동 비활성화 발동 시 `bash .claude/hooks/diagnose.sh` 1회 실행으로 영향 평가 + 행동 옵션 확인. transcript 추적 불필요한 상황 다수 (lockedBy 0건이면 영향 없음으로 즉시 단정).
- **변경 범위**: 6 파일 영역(post-tool-use.sh, diagnose.sh 신규, hooks/README.md, tests 2 신규, run-all.sh, README/VERSION/CHANGELOG 버전 메타). 검증: `bash -n` PASS, `run-all.sh` 12/12 PASS.
- **PR #72 자체 리뷰 반영 (1차)**: CI shellcheck SC2034 (diagnose.sh 미사용 `have_git` 제거), M001 (diagnose.sh "추정 원인" 메시지가 effective `CCK_HOOK_THRESHOLD`/`CCK_HOOK_WINDOW_SEC` 반영하도록 — env override 의도와 일관), H001 (테스트 fail 카운터 미연결 패턴 → if/else 분기로 false PASS 차단), H002 (`WINDOW_SEC=1` 시나리오 신설 — 2초 sleep 후 카운터 리셋 검증), H003 (`break` 후 후속 assertion `early_fail` 가드), H004 (`THRESHOLD=5` 시나리오 `WINDOW=3600` 고정 — CI 부하 무관 결정론). M005 방어적 일관성으로 diagnose.sh의 counter 파일 비숫자 sanitize 패턴도 동기화.

## [2.1.2] - 2026-05-12

> **머지 결정 일관성 — MAJOR 라벨을 정책에 맞춤 (patch)** — PR 리뷰 결과 보고가 어떤 때는 "CRITICAL만 수정", 어떤 때는 "MAJOR도 수정 후 재리뷰"로 흔들리던 비일관성 해소. 자동화 결정 게이트(`skill-review-pr` Step 4/6/7은 CRITICAL만 차단)와 agent 라벨("MAJOR = 머지 전 수정 권장")의 SSOT 충돌이 원인이었음. 자동화 로직과 `skill-fix` 파싱은 **전혀 건드리지 않고** 4개 agent의 MAJOR 헤더와 1개 매핑 표 행만 정책에 맞춰 정렬했으며, `skill-review-pr/SKILL.md` 주의사항에 "심각도별 머지 정책" SSOT 블록을 추가하여 LLM이 결과 보고할 때 본 규칙을 우선하도록 명문화. 토큰 비용 변화 0 (auto-fix 루프는 CRITICAL에만 적용된다는 사실도 함께 명문화). 본 PR(#71) 자체 리뷰가 새 정책의 첫 적용 사례로, MINOR 1건을 "수정 후 재리뷰 권장"이 아닌 "정보 제공"으로 보고하여 정책이 의도대로 작동함을 확인.

### Fixed

- **agent 라벨 4건 통일 (#71)**: `pr-reviewer-domain.md`, `pr-reviewer-security.md`, `pr-reviewer-test.md`, `agent-db-designer.md`의 `### MAJOR (머지 전 수정 권장)` 헤더를 `### MAJOR (개선 권고 — 머지 차단 없음)`로 정렬. `agent-qa.md` P2→MAJOR 매핑 행도 "개선 권고, 머지 차단 없음"으로 정렬. 자동화 결정 게이트(`skill-review-pr` Step 4/6/7)는 이미 CRITICAL만 차단으로 동작 중이었으나 agent 라벨이 "MAJOR=머지 전 수정 권장"으로 표기되어 LLM에게 "재리뷰 권하라"는 상충 시그널을 주던 결함 해소.
- **`skill-review-pr/SKILL.md` SSOT 블록 신설 (#71)**: 주의사항 섹션에 "심각도별 머지 정책" 블록 추가 — CRITICAL=차단·수정 후 재리뷰 / MAJOR=권고·머지 가능(다음 PR/별도 Task로 처리) / MINOR=참고. LLM이 이전 회차의 표현보다 본 규칙을 우선하도록 명시. auto-fix 루프는 CRITICAL에만 적용된다는 사실을 명문화하여 토큰 비용 통제 의도를 SSOT에 박제. 기존 "CRITICAL 이슈는 반드시 수정 필요" 한 줄은 본 블록에 흡수.

### Notes

- **사용자 영향 (v2.1.1 → v2.1.2)**: 마이그레이션/액션 불필요. 자동화 로직 변경 없음 — `skill-review-pr` 결정 로직, `skill-fix` 파싱, `fixLoopCount` 루프 가드 모두 그대로. 다음 PR 리뷰부터 결과 보고 표현이 일관(CRITICAL=수정 필수, MAJOR=정보 제공)되게만 바뀜.
- **토큰 비용**: 변화 0. 대안으로 검토된 "MAJOR까지 차단+auto-fix" 방향은 루프 길어져 토큰 폭증 위험으로 거부.
- **변경 범위**: 6 파일, +12/-6. Trivial PR 경량 리뷰 단일 라운드로 완료(자기 PR → COMMENT).

## [2.1.1] - 2026-05-11

> **schema 정합성 sleeper bug 2건 일괄 수정 (patch)** — v2.1.0 PR #61 6차 자체 리뷰 후속 이슈 2건(#66 escape hatch enum mismatch / #65 v1 backlog 호환)을 함께 해소. (#66) `skill-init` Step 5 escape hatch C + `--quick` 파일 감지가 이미 `react-vite`/`vue-nuxt`/`astro`/`sqlite`를 사용 중이었으나 `project.schema.json` enum에 누락되어 생성 결과가 검증 실패하던 결함 수정. (#65) v1.x 시기 실제 backlog가 사용하던 `step.description` / `step.estimatedLines`가 `additionalProperties:false`에 막혀 거부되던 sleeper bug 해소 — `examples/ecommerce-shop/backlog.json`도 동일 결함으로 silent 위반 중이었음. 본문에서 가정된 "v1→v2 task 자동 마이그레이션"은 실제 `backlog.schema.json` diff가 0이라 변환 룰 자체가 불필요했고, 진짜 결함은 step 옵셔널 필드 부재였음. 회귀 보호 fixture/pytest + CI 가드 추가로 동일 패턴 재발 방지. 마이그레이션 영향 0 (기존 enum/필드 유지, 옵셔널 확장만).

### Fixed

- **`.claude/schemas/project.schema.json` — frontend/database enum 확장 (#66)**: `skill-init` Step 5 escape hatch C 흐름과 `--quick` 모드 파일 기반 감지가 사용하는 스택 값이 schema enum에서 누락되어 생성된 `project.json`이 검증 실패하던 결함 수정. `techStack.frontend`에 `react-vite`, `vue-nuxt`, `astro` 추가, `techStack.database`에 `sqlite` 추가. 기존 enum 값은 그대로 유지하여 마이그레이션 영향 0. SKILL.md/skill-onboard/skill-impl이 이미 이 값들로 동작 중이었음.
- **`.claude/schemas/backlog.schema.json` — v1 backlog 호환 + 현존 example 정합 (#65)**: step 정의에 옵셔널 `description` / `estimatedLines` 필드 추가. v1.x 시기 실제 backlog가 사용하던 두 필드가 `additionalProperties:false`에 막혀 거부되던 sleeper bug 해소. 동일 결함이 `examples/ecommerce-shop/.claude/state/backlog.json`에도 잠재해 schema 검증을 silently 위반하던 상태였음. CI 가드 추가(`.github/workflows/schema-validation.yml`)로 examples backlog도 schema 검증되며, v1.45.1 examples 박제 fixture(`tests/upgrade/fixtures/v1-{ecommerce,fintech}-backlog.json`) + pytest(`test_backlog_compat.py`)로 회귀 보호. `backlog.schema.json`은 v1↔v2 schema diff 0 — 변환 룰 자체가 불필요하므로 `migrations.json` 추가 없음. `skill-upgrade`는 기존대로 `.claude/state/*` 보존만 수행하며 SKILL.md에 v1 호환 정책 명문화.

### Notes

- **사용자 영향 (v2.1.0 → v2.1.1)**: 마이그레이션/액션 불필요. schema 옵셔널 확장만이라 기존 `project.json`/`backlog.json` 호환.
- **CI 가드 추가**: `Schema Validation` 잡에 `examples/*/.claude/state/backlog.json` 검증 단계 추가. 자기 fork에서 examples를 수정 중이라면 schema 위반 시 즉시 fail.
- **v1.x 사용자**: 이전에 `skill-upgrade` 후 `step.description`/`step.estimatedLines` 필드 때문에 schema 위반이 보고됐다면 본 패치로 해소. 별도 작업 없음.
- 후속 Open Issue: #64 (v2.1.0 통합 추적 메타 이슈, 5/11 릴리스로 본질 종결).

## [2.1.0] - 2026-05-11

> **skill-init 요구사항 우선 플로우 재설계 + 백로그 자동 분해 opt-in (minor)** — 기존 "도메인 → 스택 → (백로그 별도)" 순서를 "요구사항 자유 서술 → 도메인/스택 LLM 추천 → 백로그 자동 분해(opt-in)" 흐름으로 뒤집어 실제 제품 개발 사고 흐름과 일치시킴. 사용자가 한 줄 또는 여러 문단의 요구사항을 입력하면 Phase 4-카테고리 백로그(10-25 task)가 즉시 준비되어 `/skill-plan`/`/skill-impl` 체인으로 바로 진입 가능. 6 라운드 자체 리뷰 + 수정으로 입력 신뢰 경계(prompt injection 방어), sanitization(셸/path traversal 차단), Hard limits 강제, 컴플라이언스 priority 강제 격상, 절단 가시성 확보 등 안전장치 충실. 정적 검증 13/13 PASS.

### Added

- **`.claude/skills/skill-init/SKILL.md` — 요구사항 우선 플로우 (Step 2~9 신설)**:
  - **입력 신뢰 경계 섹션 (신규)**: Step 2/3/4/9 사용자 입력이 Step 1 destructive 분기 / Step 9 컴플라이언스 격상 / Step 10 백업/덮어쓰기 결정을 변경할 권한 없음 명시. "ignore previous instructions" 등 메타 지시 무시. 비가시 문자(zero-width chars U+200B/200C/200D/FEFF, ZWJ) sanitization strip.
  - **Step 2 요구사항 자유 서술 입력**: 한 줄~여러 문단. 빈 입력 시 최대 1회 재요청 후 placeholder 진입. **입력 상한** 5000자/50줄 + project.json description 200자.
  - **Step 3 정보 보강** (lean 입력일 때만 최대 3질문). rich 입력이면 SKIP.
  - **Step 4 프로젝트 메타 자동 결정**: 프로젝트명 5단계 폴백 + **sanitization 강제** (화이트리스트 + 길이 1-50 + 셸 메타 차단). taskPrefix 알고리즘.
  - **Step 5 LLM 추론 추천**: 도메인 + 스택 단일 추천 + 차순위 옵션 부기. 재현성 결정 규칙 표.
  - **Step 9 백로그 자동 분해 (opt-in, 신규)**: Phase 4-카테고리 고정 템플릿. **Hard limits 강제** (phase당 ≤10, 전체 ≤30, critical 포함 절대 상한 — 사용자 우회 불가). **Priority 강제 + 컴플라이언스 격상** (강제 그룹 / 심사 그룹 분리). **절단 보고 형식**으로 critical 누락 가시성 확보.
  - **task.phase ↔ phases 키 매핑 규칙** + orphan phase drop 강제.
  - **Step 10 사전 처리 (`--reset`)**: PID suffix 백업 디렉토리 + `MANIFEST.txt` + `MANIFEST.sha256`. `--reset` + 진행 중 task ≥ 1 시 1회 confirm.
  - **Step 11**: 백로그 시작 가이드 / 빈 백로그 안내 / **v1 데이터 복원 안내**.
- **재현성 정책 표**: 결정적 항목 vs 경험적 관측 정직 분리. LLM sampling 한계 명시.
- **`.claude/skills/skill-onboard/SKILL.md`**: 빈 디렉토리 시 `/skill-init` 권장 안내 + 차이점 표 보강.

### Changed

- **Step 1 평가 순서**: 자동 정리 실행 시 코드 감지 가드 SKIP / 진행 중 task 분기 세분화.
- **Step 1 보존/삭제 14종 표 형태** (정밀도 보존).
- **--quick 케이스 흐름 표**: 9 케이스로 확장. 입력 횟수 명시.

### Fixed

- **6 라운드 자체 리뷰 + 수정 (CRITICAL 13 + MAJOR 60 + MINOR 30 누적)**:
  - 1차→2차: schema 위반 11건 (currentStep:0, specFile:null, phase 객체, --reset 처리 등)
  - 3차 5관점: phase 매핑 룰, task 템플릿 빈값 omit (skill-impl 동적 lockTTL 보호), 재현성 SLA 다운그레이드, 프로젝트명 sanitization, 입력 신뢰 경계
  - 4차: v1 detector 정정, project.json v2 GA 필드, Hard limits critical 보호, 컴플라이언스 키워드 확장, MANIFEST 무결성
  - **5차 scope down**: v1→v2 위임 분기 제거 (skill-upgrade v1 task 변환 미수행 확인 — 거짓 약속 차단). v1 자동 변환은 #65로 분리
  - 6차: Hard ceiling 수치 모순 정정, 컴플라이언스 절단 가시성, 재현성 정책 강제/심사 분리, v1 데이터 복원 안내

### Notes

- **사용자 영향 (v2.0.x → v2.1.0)**:
  - `/skill-init` 흐름 변경 (요구사항 우선). `--quick` 모드는 기존 동작 유지.
  - 신규 기능: 백로그 자동 분해 (opt-in). N이면 기존과 동일 빈 백로그.
  - `--reset`: 백업 디렉토리 명세 강화. v1 사용자는 백업 후 새 v2 빈 백로그 (수동 복원).
  - schema/backlog 형식 변경 없음. 기존 v2 프로젝트 호환.
- **후속 Issue**: #62 test 영속화 / #63 cleanup protocol / #65 v1→v2 자동 마이그레이션 (v2.1+) / #66 escape hatch enum mismatch
- 자체 정적 검증 13/13 PASS.

## [2.0.3] - 2026-05-06

> **kit clone cleanup 4종 추가 (patch)** — v2.0.2의 ai-crew-kit clone 자동 정리에 누락된 항목 보강. cleanup 10종 → 14종. `README.md`/`CLAUDE.md`/`VERSION`(Step 6 새로 생성과 일관성), `.claude/state/`(kit dev runtime state), `.claude/settings.local.json`(kit 개발자 로컬 권한 설정 — 사용자 무관) 추가. Step 1 표의 `CLAUDE.md` 행을 사용자 저장소/kit clone 케이스로 분리하여 모순 해소.

### Changed

- **`.claude/skills/skill-init/SKILL.md`** — Step 1 cleanup 대상에 4종 추가: `README.md`, `CLAUDE.md`, `VERSION` (Step 6에서 사용자 프로젝트용으로 어차피 덮어씀이지만 정리 단계에서 명시 삭제로 일관성 확보), `.claude/state/` (kit dev runtime state — `hook-trigger-count` 등), `.claude/settings.local.json` (kit 개발자 로컬 권한 설정 — 사용자 프로젝트에 무관). 총 cleanup 항목 10종 → 14종. Step 1 표 `CLAUDE.md | 있음 | 백업 여부 확인` 행을 사용자 저장소 케이스로 한정하고 ai-crew-kit clone 케이스는 별도 행("자동 삭제")으로 분리하여 모순 해소. 보존 목록에 `.claude/SECURITY.md` 명시(사용자도 자기 hook 추가 시 보안 원칙 적용 가치).
- **`.claude/skills/skill-onboard/SKILL.md`** — 동일 cleanup 14종으로 동기화. Step 4 백업 단계에 "kit clone 케이스 예외" 명시(자동 정리에서 이미 삭제되었으므로 백업 대상 없음 — 자연스럽게 스킵).
- **`README.md`, `docs/getting-started.md`, `docs/skill-reference.md`, `docs/concepts.md`** — cleanup 14종 목록과 README.md/CLAUDE.md/VERSION이 Step 6에서 새로 생성됨을 명시하도록 갱신.

### Notes

- 사용자 영향: kit clone에서 init 시 사용자 프로젝트가 더 깨끗하게 시작됨. `.claude/settings.local.json`(kit 개발자 권한 설정 노출)과 `.claude/state/`(kit runtime state) 잡티 제거. README.md/CLAUDE.md/VERSION은 어차피 Step 6에서 덮어쓰던 동작을 Step 1에서 명시 삭제로 변경하여 init 진행 중 kit metadata 잠시 노출되던 UX 거슬림 해소.
- v2.0.2 → v2.0.3 사용자 영향 없음. 자동 마이그레이션 불필요.
- 보존 결정: `.claude/SECURITY.md`(사용자 hook 추가 시 동일 보안 원칙 적용), `.gitignore`/`.gitattributes`(사용자에게도 유효).

## [2.0.2] - 2026-05-05

> **skill-init/onboard에서 ai-crew-kit clone 자동 정리 (patch)** — 사용자가 ai-crew-kit clone에서 신규/기존 프로젝트로 진입할 때 Claude가 보수적으로 멈추거나 kit 잔여 파일(CHANGELOG.md, docs/, examples/ 등) 처리를 수동으로 묻던 UX 결함 해결. skill-init Step 1, skill-onboard 사전 조건에 "표준 진입 플로우 — 추가 확인 없이 자동 실행" 명시. 검출 기준(origin URL 정규식 + initial commit fingerprint) + 자기 보호 가드 3종(tracked dirty / 미푸시 / 비-main·detached) 통과 시 kit 잔여 10개 항목(`CHANGELOG.md`, `docs/`, `examples/`, `tests/`, `scripts/`, `.github/`, `memory/`, `LICENSE`, `.claude/temp/`, `.claude/hooks/tests/`) 자동 삭제. 외부 리뷰 2라운드 모두 반영(M1 검출 기준 / M2 dev 가드 / M3 Guard 1 untracked 우회로 시나리오 B UX 보존 / m1·m4·m5·m6).

### Changed

- **`.claude/skills/skill-init/SKILL.md`** — Step 1에 "ai-crew-kit clone 자동 정리" 표준 진입 플로우 명시. 검출 기준(origin URL 정규식 `[/:]ai-crew-kit(\.git)?$` + initial commit fingerprint `ab0269a14...` 둘 다 매칭) + 자기 보호 가드 3가지(더티 워킹 트리/미푸시 커밋/비-main 브랜치 차단) 모두 통과 시 `rm -rf .git && git init -b main` 후 kit 잔여 10개 항목(CHANGELOG.md, docs/, examples/, tests/, scripts/, .github/, memory/, LICENSE, .claude/temp/, .claude/hooks/tests/)을 **추가 확인 질문 없이** 자동 삭제. Claude가 이전에 보수적으로 멈추던 케이스 해결. Step 7 마지막 줄 `docs/getting-started.md` 참조를 GitHub URL로 변경.
- **`.claude/skills/skill-onboard/SKILL.md`** — 사전 조건 2번에 동일 검출+가드+자동 정리 로직 추가 (skill-init과 일치). 시나리오 A(`.claude/`만 복사)는 검출 자동 스킵, 시나리오 B(kit clone+사용자 코드)는 사전 정리 후 온보딩, 시나리오 C(kit clone 아님)는 자동 스킵으로 영향 없음. 시나리오 B 동일 경로 충돌(사용자가 자기 docs/tests를 동일 경로에 둔 경우) 1줄 주의 추가.
- **`README.md`** — 빠른 시작 섹션에 자동 정리 5단계 결과 + 검출 기준/가드 설명 추가. 버전 배지 v2.0.0 → v2.0.1 정정. 기존 프로젝트 온보딩 경로를 시나리오 A(권장) 중심으로 정리하고 시나리오 B 동일 경로 충돌 주의 추가.
- **`docs/getting-started.md`** — 초기화 흐름 다이어그램에 "1단계 환경 검증 + ai-crew-kit clone 자동 정리" 명시. 검출 기준/가드 박스, kit dev 잡티 10종 명시. 기존 프로젝트 온보딩에 시나리오 A(`.claude/`만 복사)와 시나리오 B(kit clone+사용자 코드) 분기 + 사전 백업 권장. 온보딩 흐름 다이어그램에 "0. 사전 조건" 단계 추가.
- **`docs/skill-reference.md`** — `/skill-init`, `/skill-onboard` 행에 "ai-crew-kit clone 감지 시 자동 정리" 한 줄 + 표 하단에 검출/가드/잔여파일 요약 박스.
- **`docs/concepts.md`** — 프로젝트 루트 자동 생성 섹션에 "ai-crew-kit clone에서 시작 시 kit dev 잡티 10종 자동 삭제" 1줄 주석.
- **`.claude/rules/README.md`, `.claude/domains/_base/health/README.md`, `.claude/hooks/README.md`** — 사용자 프로젝트에서 `docs/` 자동 정리 시 깨질 dead link 11개를 GitHub 절대 URL로 보정. `blob/main` 버전 표류 주의 1줄(시드 시점 보존이 필요하면 `blob/{kitVersion 태그}`로 변경) 추가.
- **`CHANGELOG.md`** — 본 변경 기록.

### Notes

- 사용자 영향: skill-init/skill-onboard 진입 시 멈춤 없이 자연스럽게 진행. 사용자 프로젝트가 더 깨끗하게 시작됨(kit 잡티 0).
- 프로덕션 훅 3종(SessionStart/PostToolUse/Stop) 영향 0 — `CLAUDE_PROJECT_DIR` 만 참조하여 self-contained.
- LICENSE는 Y/n 질문 없이 자동 삭제(사용자가 자기 라이선스 결정). KIT_SOURCE_URL은 보존되어 skill-upgrade가 kit 가이드 문서 fetch 가능.
- 외부 리뷰 1라운드(직전 CRITICAL 1건은 재평가에서 MINOR로 강등, MAJOR 2건 M1·M2 본 PR에서 반영, MINOR 4건 중 m1·m4 반영, m2·m3 INFO로 분류).
- M2 가드는 사용자 시나리오에 영향 0이며 ai-crew-kit 본인 dev 환경에서 `/skill-init` 실수 실행 시의 폭탄을 방지합니다.
- **외부 리뷰 2라운드 반영** — Guard 1(더티 워킹 트리)이 시나리오 B(사용자 코드 untracked) 흐름을 차단하던 M3 결함 수정: `grep -v '^??'`로 tracked dirty만 차단. m5 Guard 3 detached HEAD 빈 문자열 우회 차단(`[ -n ]` 조건 제거, positive 로직). m6 skill-init Step 7 마지막 줄 GitHub URL을 `blob/v{kitVersion}` 동적 치환 + main 보조 안내로 변경. fingerprint `ab0269a14...` 실제 main root commit 일치 검증 완료.

## [2.0.1] - 2026-05-05

> **DB 컨벤션 정책 중심 정리 (patch)** — v1.41.0 "프레임워크는 특정 기술 패턴을 가르치지 않음" 철학 정렬. `_base/conventions/database.md`와 `agent-db-designer.md`에서 Claude 기본 지식 영역(DB별 구문/타입표/인덱스 설계 원칙)을 제거하고, 팀 정책(네이밍·필수 컬럼·Soft Delete·낙관적 잠금·무중단 마이그레이션)만 유지. 기본값(MySQL+Flyway) 외 사용 시 `project.json`의 `techStack.database`만 변경하면 Claude가 컨텍스트에 맞춰 구문 적용. 사용자 진입점은 `docs/customization.md`로 단일화.

### Changed

- **`_base/conventions/database.md`** (#53) — 정책-only 슬림화, 159 → 70줄(~56% 감소). 상단 박스에 "기본값 + 커스터마이징 경로" 명시(`project.json` SSOT 참조), `↔` → `→` 단방향 표기, NoSQL은 정책 차용만 명시, 도구별 표준 식별자 체계 그대로 따르기, non-blocking 인덱스 옵션 각주.
- **`.claude/agents/agent-db-designer.md`** (#54) — DB별 특성표/MySQL·PostgreSQL 특화/인덱스 설계 원칙 제거. 의사결정 프레임워크/도메인별 특수설계/심각도/출력 형식은 유지. 240 → 185줄(~23% 감소). healthcare PHI 패턴 정정(append-only `phi_access_log` 별도 테이블 + 분리 저장 원칙, `audit-trail.md` 정합), saas 도메인 특수 설계 신규 추가(`tenant_id` 격리·격리 전략 3종·PostgreSQL RLS·시계열 과금), GDPR Art.17 vs 의료법 보존 의무 충돌 케이스 명시.
- **`docs/customization.md`** (#55) — 신규 섹션 "DB 및 마이그레이션 도구 변경"(+70줄). schema 정합(enum `mysql/postgresql/mongodb/none` + `additionalProperties: false` 약속 준수), SQL 구문 매핑 표 + NoSQL 별도 단락 분리, 도구 4종 명명 규칙(Flyway/Alembic/Liquibase/Prisma/golang-migrate). CUSTOM_SECTION 보존 범위 정직 표기(v2.0은 CLAUDE.md/README.md만, conventions 파일은 v2.1+ 도입 예정) + 권장 대안 2종 안내.

### Notes

- v2.0.0 → v2.0.1 사용자 영향 없음. 자동 마이그레이션 불필요.
- 외부 리뷰 1라운드(CRITICAL 1건 + MAJOR 7건 + MINOR 6건) 모두 반영.
- v2.1+ 로드맵: schema enum 확장(CockroachDB/SQLite/DynamoDB), `techStack.migration` 신규 필드, conventions 파일 단위 CUSTOM_SECTION 자동 보존.

## [2.0.0] - 2026-05-04

> **GA 릴리스 — Migration Surface 요약**: v1.x 사용자는 `/skill-upgrade --version v2.0.0` 자동 마이그레이션으로 충분. 자동 적용 4 add_field(`hooks`/`conventions.skillProfile`/`conventions.overridePriority`/`tokenHints`), 수동 작업 *거의 없음*, 점수 영향 ≤1점. 상세는 [docs/v2/migration-guide.md](./docs/v2/migration-guide.md).
>
> **Phase 6 (`skill-compliance-report`) 보류** — 2026-05-01 옵션 D 채택. ACK 미니멀리즘 위배 + 실수요 미검증 + 위반 탐지 Phase 4/5 중복. v2.1+ 재진입 시 검토.

### Added

#### Phase 8 — Migration & Release / GA (v2.0.0)
- **`docs/v2/migration-guide.md`** (Step 2) — v1.x → v2.0.0 마이그레이션 사용자 가이드 5섹션(변경 사항 / 자동 절차 / 수동 확인 / 롤백 매뉴얼 / FAQ 5건) + R6 1차 방어선
- **examples v2 형식 마이그레이션** (Step 3) — `examples/{fintech-gateway,ecommerce-shop}/.claude/state/project.json`에 `kitVersion 2.0.0` + `kitSource` + `conventions.skillProfile`/`overridePriority` + `hooks {}` + `tokenHints {}` 명시
- **`tests/upgrade/fixtures/v1-{fintech,ecommerce,saas,healthcare}-project.json`** (Step 3) — 4 도메인 v1 형식 fixture (saas/healthcare는 OQ-04 fixture-only 검증, 실제 examples 디렉토리는 v2.1+ 후속)
- **`scripts/validate-v2-migration.py`** (Step 3) — cumulative add_field 적용(target ≤ 버전 오름차순) + schema-aware 필터(`backlog.*` 등 다른 파일 영역 자동 스킵) + ${KIT_VERSION}/${KIT_SOURCE} placeholder 치환 + 비-dict 부모 fail-fast(silent overwrite 방지) + OQ-02 진단 모드
- **`tests/upgrade/test_rollback.py`** (Step 3) — R6 1차 자동 방어선. 9 tests × 4 fixtures parametrize (외부 리뷰 #1/#2 보강 반영): v1 보존 / v2 add_field / schema 통과 / *진짜 라운드트립*(v1 → migrated → 백업 복원 = v1) / *비-trivial 멱등성*(1차 롤백 → dirty 변경 → 2차 롤백 = v1) / 더블 마이그레이션 멱등 / 사용자 보존(3 parametrize) / fail-fast on non-dict parent / cumulative+schema-aware filter
- **CI 워크플로우 2 jobs 신설** (`.github/workflows/secrets-tests.yml`) — `validate-v2-migration`(4 fixtures + 2 examples 검증) + `upgrade-fixture-tests`(pytest tests/upgrade -v R6)
- **`skill-upgrade` SKILL.md 갭 fix** (Step 1) — 업데이트 대상 표에 `.claude/rules/`(Phase 4 도입) 추가 + 보존 대상 표에 `lessons-learned.json`(Phase 7 도입) 명시
- **`docs/v2/phase-8-plan.md`** (Step 1) — 옵션 A Lean Closure 결정 SSOT (9 D + 7 OQ + 6 R + Step 1~6 분리)
- **`docs/v2/phase-8-release.md` SSOT 이관 헤더** (Step 1) — phase-8-plan.md를 결정 SSOT로 명시 (PR #45 리뷰 MAJOR #1)

#### Phase 7 — Context & Learning (v2.0.0)
- **`.claude/schemas/lessons-learned.schema.json`** (Step 1) — v1.23 lessons-learned 회귀 보호 schema. id/category/severity/impact 필드 + `additionalProperties: false`
- **`scripts/validate-lessons-learned.py`** (Step 1) — 4단계 검증(schema validation + cross-ref + impact 정량 + required field 누락). `--fixture` 단일 검증 모드
- **`tests/lessons/` pytest 33 cases (5 files)** (Step 2) — schema validation / secrets 필터 / threshold 적용 / skill-retro 명세 / fixtures(positive/invalid-id/extra-property)
- **`skill-retro` §5.3 secrets 필터** (Step 2) — lessons-learned 작성 시 토큰/이메일 패턴 자동 redact + impact 정량(상/중/하 → 점수 매핑)
- **CI 워크플로우 2 jobs 신설** (`.github/workflows/secrets-tests.yml`) — `validate-lessons-learned`(positive PASS + 2 negative MUST FAIL) + `lessons-fixture-tests`(pytest tests/lessons)
- **`docs/v2/phase-7-{plan,context}.md` + `context-migration.md`** — 옵션 A Lean Closure 결정 + 사용자 마이그레이션 안내

#### Phase 5 — AgentShield-lite (v2.0.0-alpha.4)
- **`secrets-patterns.json` 스키마** — 3 섹션 표준(`common.hardcoded` / `common.runtime` / `domain.patterns`) + entry 필드(`id`/`name`/`pattern`/`severity`/`confidence`/`description`/`excludeFiles`/`excludeContexts`)
- **`_base/health/secrets-patterns.json`** — 공통 패턴 17개
  - `common.hardcoded` SEC-S01~S05 (high) — API 키, secret/private_key, AWS Access Key 5 prefix(`AKIA|AGPA|AROA|AIDA|ANPA`), GitHub Token 5 prefix(`ghp|gho|ghu|ghs|ghr`), Slack Bot/User Token
  - `common.runtime` SEC-S06~S17 (medium 예외 — v1.x SEC-01 회귀 보존) — log/logger/println에 password/cardNumber/creditCard/cvv/ssn/주민등록/secret/apiKey/token/bearer/authorization 등 직접 전달
- **`_base/health/README.md`** — 스키마/confidence 등급 가이드/`excludeFiles` 기본 권장/`excludeContexts` enum SSOT 정의/새 공통·도메인 패턴 추가 절차/금지 항목/도메인 ID 네임스페이스 정책(`{domain}/SEC-S01`부터)/v2.0 채택·보류 명시
- **`skill-health-check` 신규 검사** (모두 CRITICAL, autoFix 불가)
  - **SEC-05** — 하드코딩 시크릿. `_base/common.hardcoded` 로드 + 매칭
  - **SEC-06** — `.env` 노출 게이트. gitignore 등록 + 평문 시크릿(AWS/GitHub/Slack 명시 prefix) 두 단계, `.env.example`/`.env.template`/`.env.sample`은 placeholder 가정 제외
  - **SEC-07** — 도메인별 민감 데이터. `{domain}/health/secrets-patterns.json` `domain.patterns` 로드 + 체크섬 검증(PAN Luhn / 한국 주민·사업자 가중치). `general` 도메인 또는 도메인 patterns 부재 시 SKIP
- **`skill-health-check` 카테고리 헤더 SSOT** — 외부 패턴 로드 절차(부재/JSON 파싱/정규식 컴파일 실패 3-tier 폴백) + `excludeContexts` 처리 정규식(JS/Python dict+getenv/Java/Go Getenv+LookupEnv 커버) + 출처 표기 형식(`{domain}/SEC-S{nn}`) + `medium` confidence 안내 문구
- **도메인별 `secrets-patterns.json`**
  - **`fintech/health/secrets-patterns.json`** — SEC-S01 PAN 16자리 IIN 제한(`\b[3-6]\d{15}\b`) + Luhn 위임. CVV 형식 매칭은 v2.0 보류(SEC-01 SEC-S09 커버)
  - **`healthcare/health/secrets-patterns.json`** — SEC-S01 미국 SSN, SSA invalid 그룹(area=000/666/9XX, group=00, serial=0000) lookahead 제외. DEA Number/MRN 보류
  - **`ecommerce/health/secrets-patterns.json`** — SEC-S01 한국 주민등록(YYMMDD + 성별 1-8 형식 검증 + 가중치 [2,3,4,5,6,7,8,9,2,3,4,5] 체크섬), SEC-S02 한국 사업자(세무서 코드 [1-9] 시작 + 가중치 [1,3,7,1,3,7,1,3,5] 체크섬)
- **`docs/v2/security-migration.md`** — alpha.3 → alpha.4 마이그레이션 가이드. SEC-01 회귀 보존 1:1 매핑표, 신규 SEC-* 가이드, alpha.2 hook-safety 부채 해소 사실, 점수 영향 0 분석, excludeFiles/excludeContexts 사용자 가이드, autoFix 정책, Phase 4 rules 다층 방어, v2.1+ 보류 항목 9건, Troubleshooting Q1~Q3
- **TFT 설계 문서** — `docs/v2/phase-5-tft-analysis.md` (5인 분석 + D0~D7 결정 + 옵션 A/B/C 비교 + 9 리스크 + 옵션 B 채택), `docs/v2/phase-5-plan.md` (Step 1~4 구현 계획 + 진행 상황 SSOT 테이블)
- **`python-fastapi` / `python-django` 검사 대상 파일 패턴** — security 카테고리 헤더에 추가 (alpha.2 이후 누락 결함 동시 해소)

#### Phase 4 — 4-Layer Override + Constraint Rules (v2.0.0-alpha.3)
- **`.claude/rules/` 디렉토리** — 도메인 × 언어 교차 제약 규칙 메커니즘 신설 (4층 Layered Override의 2번째 층, PR 리뷰 컨텍스트 한정 적용)
- **`.claude/rules/README.md`** — rules vs conventions 경계 매트릭스, language 매핑 SSOT 표(7개 backend), frontmatter 표준(id/domain/language/severity/triggers/related), 새 rule 작성 가이드라인, 금지 항목 (`_base/rules/`, `{domain}/rules/` 단독 층 신규 생성 금지), skill-review-pr 통합 절차
- **`.claude/rules/_example/_example/sample-rule.md`** — 학습용 예시 템플릿. `_example` 경로는 language 매핑 표에 없어 실제 PR 리뷰에 적용되지 않음 (자연 SKIP)
- **`skill-review-pr` Step 2.5 (Rules 로드)** — PR 리뷰 시 `project.json`의 `domain` + `techStack.backend` 읽고 language 매핑 → `.claude/rules/{domain}/{language}/*.md` 글롭 → `pr-reviewer-domain` 에이전트에 `rules_paths` 전달. 부재 시 / Trivial PR / `_example` 시 SKIP (4단 자연 SKIP 체인)
- **`pr-reviewer-domain` 에이전트** — 신설 "Rules 처리 (Phase 4)" 섹션. Read 로드 → frontmatter 파악 → MUST/MUST NOT 본문과 PR diff 대조 → 위반 시 frontmatter `severity` 기반 보고 → 출처 경로 (`rules/{domain}/{language}/{rule-id}.md`) 명시. `triggers` 정규식은 자동 차단이 아닌 LLM 컨텍스트 힌트
- **`skill-review-pr` 출력 헤더** — `📋 적용 Rules: {domain}/{language} (N개) — {파일들}` (rules_paths 비어있거나 Trivial 시 미출력으로 노이즈 방지)
- **`docs/concepts.md`** — 핵심 원칙 표 + Layered Override 다이어그램 4층 갱신 (project.json → rules → domains → _base + 하드코딩 baseline)
- **`docs/customization.md`** — 4층 다이어그램, 디렉토리 구조 트리에 `.claude/rules/` 추가, 신규 섹션 "## 도메인 × 언어 Rules" (rules vs conventions 비교, language 매핑 표, 새 rule 추가 절차, 작성 시 주의사항, 현재 정책)
- **TFT 설계 문서** — `docs/v2/phase-4-tft-analysis.md` (5인 분석 + 8개 리스크 + 옵션 A 결정), `docs/v2/phase-4-plan.md` (Step 1~4 구현 계획)

> **본 릴리스는 메커니즘만 포함.** 도메인 × 언어 룰 콘텐츠는 0개로 출시되며, 사용자가 실 사용 케이스 발생 시 직접 추가합니다 (옵션 A 채택 — "Claude가 이미 아는 것은 가르치지 않는다" 원칙 준수).

#### Phase 1 — Native Hooks Framework (v2.0.0-alpha.2)
- **SessionStart 훅** (`.claude/hooks/session-start.sh`) — 세션 진입 시 git sync(워크트리/비워크트리 자동 구분) + 이전 세션 `continuation-plan.md` 자동 출력
- **PostToolUse 훅** (`.claude/hooks/post-tool-use.sh`) — `Edit|Write|MultiEdit|NotebookEdit` 후 `lockedAt` heartbeat 갱신 + **3단계 무한 루프 방어**
  - 0단계: `hook-disabled.flag` 존재 시 즉시 종료
  - 1단계: `file_path`가 `.claude/state/*` / `.claude/temp/*`면 즉시 종료 (R1 — 네이티브 path 필터 부재 보완)
  - 2단계: 세션별 파일 락 재진입 방지 (R2)
  - 3단계: 10초 윈도우 내 3회 초과 시 `hook-disabled.flag` 자동 생성 + stderr 경고
- **Stop 훅** (`.claude/hooks/stop.sh`) — 응답 완료 시 `stop_hook_active` 체크 + 60초 디바운스 + idle 시 `continuation-plan.md` 생성 스킵, TTL 만료 락 자동 해제 (R3)
- **atomic-write 헬퍼** (`.claude/hooks/lib/atomic-write.sh`) — `flock` 기반 원자적 JSON 쓰기, 워크트리 동시 Write race 방어 (R5), `flock` 미지원 시 mkdir 폴백
- **Hook Integrity Audit** — `skill-health-check`의 신규 `hook-safety` 카테고리 (weight 10, failCap 40)
  - **HI-01** (CRITICAL) — 차단 패턴 정적 검사: `rm -rf`, `sudo`, `curl`/`wget`, `git reset --hard`, `git push --force`(`--force-with-lease` 제외, `-f` 단축형 포함), 파이프 실행(`| curl|wget|nc|bash|sh`)
  - **HI-02** (CRITICAL) — 외부 스크립트 참조 탐지: 실행 키워드(`source|bash|sh|exec|eval|.|#!`) 직후 경로 + allowlist(`/bin/true`, `/bin/false`, `/dev/*`, `/tmp`, `$TMPDIR`, 내부 hooks, 표준 인터프리터) 적용으로 환경변수 할당 오탐 방지
  - **HI-03** (MINOR) — hooks 필드 JSON 구조/스키마 유효성 + timeout 60초 상한 (SessionStart 기본 30초 × 2배 여유)
  - **HI-04** (MAJOR) — 훅 비블로킹 규칙 위반 (R4): `exit 2` 금지, `set -e` 단독(`|| true` 미동반) 금지. Grep 기반 인라인 + CI `scripts/check-hook-blocking.sh` 등가 실행
- **`_base/health/_category.json`**: `hook-safety` 카테고리 추가 (weight 10)
- **도메인 `_category.json` 병합 규칙 명문화** — `skill-health-check` Phase A §3에 두 형태 정의
  - 형태 A (legacy): `additionalCategories` + `weightOverrides` (fintech)
  - 형태 B (dictionary): `categories: { id: {weight?, failCap?, description?} }` (ecommerce/healthcare/saas)
  - 합 ≠ 100 시 자동 정규화
- **훅 디버깅 가이드** (`.claude/hooks/README.md`) — 자동 실행 경고, 3단계 방어 동작표, 수동 복구 절차
- **훅 회귀 테스트 10건** (`.claude/hooks/tests/`) — atomic-write parallel, stop recursion, lock expiry, session-start git graceful skip, continuation-plan debounce, HI-04 checker, post-tool-use path-exclude/lock-reentry/auto-disable(+10초 롤오버)/heartbeat
- **CI `hook-tests` job** (`.github/workflows/hook-tests.yml`) — shellcheck + `bash -n` + HI-04 자가 검사 + `run-all.sh` (Ubuntu)
- **`scripts/check-hook-blocking.sh`** — HI-04 자가 검사 스크립트 (주석 라인 제외, `tests/` fixture 제외)
- **`project.schema.json` `definitions.hookMatcher`** 상세화 — SessionStart/PostToolUse/Stop 이벤트 배열, `type: "command"` 강제, `timeout` 상한
- **CODEOWNERS 운영 원칙** — `.claude/settings.json`(hooks), `.claude/hooks/**`, schema hooks 변경 시 security-review 필수 (phase-1-plan.md §보안 리뷰 필수 변경점)

#### Phase 2 — Skill Profiles (v2.0.0-alpha.2 — alpha.1 이후 backfill, PR #20 commit 037c2fc)
- 스킬 프로파일 시스템 (`default` ≡ `full` / `developer` / `docs-only` / `custom`, 5종) — CLAUDE.md 스킬 노출 제어
- `skill-profiles.json` 프로파일 정의 파일
- `project.schema.json`에 `customSkills` 배열 필드 추가 (custom 프로파일용)
- `skill-init`에 스킬 프로파일 선택 단계 (Step 5.6) 추가
- TEMPLATE-ENGINE에 `SKILL_LIST_SECTION`, `NATURAL_LANGUAGE_COMMANDS` 블록 마커 추가

#### Phase 3 — Token Optimization (v2.0.0-alpha.2 — alpha.1 이후 backfill, PR #21 commit 39592ee)
- 스킬 복잡도 힌트 — 23개 SKILL.md에 `complexity-hint` frontmatter 필드 추가 (heavy 3 / medium 9 / light 11)
- `project.schema.json`의 `tokenHints` 상세 스키마: `defaultComplexity`, `skillOverrides`, `maxMcpServers`, `compactionThreshold`
- `docs/token-optimization.md` 신규 — 복잡도 매핑, 환경변수 안내, 프로파일×복잡도 조합

#### Phase 0 Foundation (v2.0.0-alpha.1, VERSION 파일만 존재 — 태그 미생성)
- v2.0.0 스키마 확장: `hooks`, `skillProfile`, `overridePriority`, `tokenHints` 필드 예약
- `kitVersion` SemVer 프리릴리즈 패턴 지원 (`2.0.0-alpha.1` 등)

### Changed

#### Phase 5 (v2.0.0-alpha.4)
- **SEC-01 외부화** — `skill-health-check/SKILL.md` 인라인 12 패턴 → `_base/health/secrets-patterns.json` `common.runtime` 로드. 키워드 1:1 동일(회귀 보존), 정규식은 단어 경계 + `log/logger/println` 변형 흡수로 정밀화. 회귀 fixture 23건 PASS
- **alpha.2 hook-safety 정규화 부채 해소** (PR #35, d0715de) — 도메인 4개(fintech/ecommerce/saas/healthcare) `_category.json`의 dictionary에 hook-safety weight 9 명시 + 기존 카테고리 비례 감소(예: fintech doc-sync 20 → 18, compliance 40 → 35)로 합 100 일관. 정규화로 보정되던 비율을 명시화 — **사용자 점수 영향 ≤1점** (fintech/ecommerce/saas는 Hamilton 라운딩으로 ≈0, healthcare phi-protection만 의도적 floor로 -0.91% ≈ ~1.0점, PR #35 §점수 영향 분석 참조)
- **`_base/health/README.md` `excludeContexts` `env_var_reference` enum** — Go(`os.Getenv` / `os.LookupEnv`) + Python 함수형(`os.getenv`) 추가 (PR #37 리뷰 M001 후속). `skill-health-check/SKILL.md` SSOT 동기화
- **`skill-health-check/SKILL.md` `type_declaration` 처리 한계 명시** — single-line 정의 + 시크릿 리터럴 동일 라인은 라인 단위 제외 때문에 false negative. 워크어라운드(시크릿 별도 라인 분리) + v2.1+ 토큰-단위 정밀화 메모 (PR #37 리뷰 M003 후속)

#### Phase 4 (v2.0.0-alpha.3)
- **`project.schema.json` `overridePriority` description 보강** — Phase 0에서 예약된 enum/default 유지하고 description만 명료화: `domain-first` / `merge` 의미 + "v2.0 MVP는 분기 로직 미구현 (단일 디렉토리 구조라 충돌 구조적으로 발생하지 않음). 향후 단독 도메인/언어 룰 도입 시 활성화" + rules/README.md 참조
- **`docs/concepts.md` & `docs/customization.md` Layered Override** 3층 → 4층 다이어그램 (rules 포함, 하드코딩 기본값은 baseline으로 카운트 외)

#### Phase 1 (v2.0.0-alpha.2)
- **`CLAUDE.md.tmpl` 세션 시작 섹션** — 훅 자동 실행을 기본 흐름으로 기술, 수동 절차는 `<details>` 폴백 블록(구버전 Claude Code / `hook-disabled.flag` 존재 / 훅 부재 3가지 트리거)으로 이동. 기존 스크립트 100% 보존
- **`_base/health/_category.json` 가중치 재배분** (합 100 유지)
  - doc-sync 35 → 32
  - state-integrity 25 → 23
  - security 25 → 23
  - agent-config 15 → 12
  - hook-safety +10 (신규)

#### Phase 2 (v2.0.0-alpha.2 — alpha.1 이후 backfill)
- CLAUDE.md.tmpl: 하드코딩 스킬 목록/자연어 매핑을 프로파일 기반 블록 마커로 교체

### Fixed

#### Phase 1 사후 결함 해소 (v2.0.0-alpha.4)
- **훅 스크립트 실행 권한 정정** (PR #34, 6dcfdb3) — alpha.2 PR #26 머지 시 누락된 `chmod +x`로 인해 `post-tool-use.sh`를 비롯한 5개 훅이 git index 모드 100644로 박혀 PostToolUse 이벤트마다 "Permission denied" 실패. 비블로킹 정책(R4)으로 세션은 정상 진행됐으나 lockedAt heartbeat 갱신 / 3단계 무한 루프 방어 / hook-disabled.flag 카운터가 사실상 alpha.2/alpha.3 동안 미동작. alpha.4부터 의도 동작 활성화 (콘텐츠 변경 0, 권한 비트만 조정)

### Breaking Changes

> **요약**: 모든 Breaking Change에 대해 `/skill-upgrade --version v2.0.0`이 자동 마이그레이션을 수행한다. 사용자 수동 작업이 필요한 변경은 *없다*. 점수 영향 ≤1점, 동작 회귀 0.

- **`project.json` 스키마 확장** — 5개 신규 top-level 필드(`hooks` / `tokenHints` / `customDomain` / `healthCheck` / `orchestrator`) + `conventions` 2개 신규 키(`skillProfile` / `overridePriority`). v1.x skill이 신규 필드를 인식하지 못할 수 있음. **자동 해결**: `migrations.json` v2.0.0이 4 add_field(`hooks {}` / `conventions.skillProfile "default"` / `conventions.overridePriority "domain-first"` / `tokenHints {}`)를 적용. 누락 3개(`customDomain`/`healthCheck`/`orchestrator`)는 schema optional이라 부재 통과 (Phase 8 Step 3 fixture 검증 결과)
- **`CLAUDE.md.tmpl` 구조 변경** — Phase 4 4층 Override 도입으로 템플릿 본문 갱신. `CUSTOM_SECTION_START`/`CUSTOM_SECTION_END` 마커는 v1.x와 동일하며, **마커 사이 콘텐츠는 자동 보존**된다 (skill-upgrade Step 13 결정적 치환). Phase 2(skillProfile 기반 스킬 목록 필터링) + Phase 1(훅 자동 실행을 기본 흐름으로 기술, 수동 절차는 `<details>` 폴백)도 동일 마커 보존 정책 적용
- **`skill-health-check` 가중치 재배분** — Phase 1 hook-safety +10 신규(doc-sync 35→32, state-integrity 25→23, security 25→23, agent-config 15→12) + Phase 5 alpha.2 hook-safety 정규화 부채 해소(도메인 4개 `_category.json` 명시). **사용자 점수 영향 ≤1점** — 3 도메인은 Hamilton 라운딩으로 ≈0, healthcare phi-protection만 의도적 floor로 -0.91% ≈ ~1.0점 (security-migration.md §5 참조)
- **Phase 1 훅: 없음** — `.claude/settings.json`에 `hooks` 필드가 부재하거나 `.claude/hooks/` 디렉토리가 없으면 v1.x 동작이 100% 유지됨 (하위호환 보장)
- **Phase 4 rules: 없음** — `.claude/rules/` 디렉토리가 부재하거나 `{domain}/{language}/` 매칭이 0개면 alpha.2 동작이 100% 유지됨. 메커니즘만 추가되고 콘텐츠 0개 출시이므로 모든 PR 리뷰에서 자연 SKIP
- **Phase 5 secrets: 없음** — `_base/health/secrets-patterns.json` 부재 시 SEC-01/SEC-05 SKIP + WARN, 도메인 patterns 부재 시 SEC-07 SKIP, dotenv 미사용 프로젝트는 SEC-06 SKIP. SEC-01 외부화는 키워드 1:1 매핑 보존(회귀 fixture 23건 PASS)으로 alpha.3 동작 유지
- **Phase 7 lessons-learned: 없음** — `.claude/state/*` 디렉토리 전체 보존 (skill-upgrade 보존 대상 표 명시). 신규 schema는 회귀 보호 메커니즘이라 사용자 데이터 영향 0
- **Phase 8 마이그레이션: 없음** — 본 절이 정의하는 자동 마이그레이션이 모든 변경을 흡수. 매뉴얼 작업 0건. 롤백은 [migration-guide.md §4](./docs/v2/migration-guide.md) R6 1차 자동 방어선 + 매뉴얼 체크리스트 6건으로 보장

### Deferred (v2.1+ 후속)

- **Phase 6 — `skill-compliance-report`** (옵션 D 채택, 2026-05-01) — 위반 탐지 Phase 4/5 중복 + ACK 미니멀리즘 위배 + v1.x 시기 실수요 미검증으로 보류. 재진입 조건 + 부활 옵션은 [docs/v2/phase-6-compliance.md](./docs/v2/phase-6-compliance.md) §보류 결정 참조 (ADJ-01)

## [1.45.1] - 2026-04-14

### Added
- **Claude Code v2.1.49+ 네이티브 git worktree 지원** — `claude --worktree <name>` (`-w`) 호환
  - `.gitignore`: `.claude/worktrees/` 추적 제외 (상태 파일 경합 방지)
  - `CLAUDE.md.tmpl`: Git 워크트리 프로토콜에 오케스트레이터 비교 테이블 추가
  - `git-workflow.md`: Worktree 모드 섹션을 Claude Code 네이티브 / Claude Squad / 수동 worktree로 일반화
  - README 요구사항: Claude Code v2.1.49+ 권장 명시
  - `skill-upgrade`: `add_gitignore_entry` 마이그레이션 타입 추가 — 기존 프로젝트 업그레이드 시 `.gitignore`에 `.claude/worktrees/` 자동 추가 (이미 추적 중이면 제거 명령 안내)

### Changed
- `project.schema.json`: `orchestrator.type` enum에서 `claude-code-native` 값 제거 — 감지는 git 메타데이터(`git rev-parse --git-dir != --git-common-dir`)로 자동 수행되므로 enum 값이 분기 로직에 사용되지 않는 선언적 no-op였음. 오케스트레이터 종류(네이티브/Squad/수동)는 모두 동일 경로로 처리됨.

### Reverted
- **서브에이전트 worktree 격리 (PR #16)** — 100회 시뮬레이션(5 에이전트 × 20 시나리오) 결과 전면 되돌림.
  - 근거: 대상 6개 agent는 `tools: Read, Glob, Grep`만 사용 → 물리적으로 쓰기 불가이므로 "메인 워크트리 오염 방지"는 존재하지 않는 문제를 해결
  - 보안 이득 주장(exfiltration/injection/silent failure)은 worktree 경계 밖(`/tmp`, `~`, 부모 컨텍스트 반환)에서 발생 → 격리로 해결 불가
  - Task 파라미터 `isolation: "worktree"`의 런타임 실재 미확인, Claude Code v2.1.48 이하 CI에서 호출 실패 가능성
  - 향후 쓰기 가능한 분석 에이전트 도입 시 런타임 계약 검증 후 재설계

> 기존 worktree 분기 로직(`git rev-parse --git-dir != --git-common-dir`)이 네이티브 worktree도 자동 감지하므로 스킬 본문 변경 없이 호환됨.

## [1.45.0] - 2026-04-07

### Added
- **UX 마찰 10건 일괄 해소** — TFT 대규모 분석 기반 개선
  - CLAUDE.md 30초 요약 (Quick Reference) 섹션 추가 — 온보딩 시간 단축
  - 에러 정보 SSOT 통합 — troubleshooting.md 중앙화, workflow-guide는 참조 링크
  - Trivial Fix 경로 (--micro) 문서화 — workflow-guide에 플로우차트 + 기준표
  - 워크플로우 프로필 비교 테이블 — standard vs fast 비교 명시
  - skill-impl `--dry-run` 옵션 — 빌드/테스트만 검증, PR 미생성
  - Eject 가이드 (`docs/eject-guide.md`) — 프레임워크 제거 절차 + 체크리스트
  - 스킬 티어 분류 — 일상(Daily) 6개 / 주간(Weekly) 5개 / 설정(Setup) 8개
  - Task 일시정지 (`paused` 상태) — `--pause`/`--resume` + `pauseReason`/`pausedAt` 필드
  - Lock 자동정리 — skill-plan/impl 진입 시 TTL 만료 Task 자동 해제

### Fixed
- README.md 버전 뱃지 불일치 (v1.43.0 → v1.45.0)

## [1.44.0] - 2026-04-07

### Added
- **서비스 설명 기반 기술 스택 추천** (Issue #14) — skill-init에 Step 2.5 추가
  - 자연어 서비스 설명 입력 → 도메인 + 풀 스택 자동 추천 (키워드 점수제 매칭)
  - 6개 컴포넌트 의사결정 테이블 (Backend, Frontend, Database, Cache, MQ, Infrastructure)
  - 3가지 분기: 수락(A) / 일부 수정(B) / 직접 선택(C) — 경력자 기존 플로우 100% 보존
  - 초심자 질문 횟수 8+회 → 4회로 감소
  - --quick 모드: 디렉토리명 키워드 매칭 추가 (추가 질문 없음)
  - 케이스별 흐름 요약 테이블 문서화 (7개 시나리오)

## [1.43.4] - 2026-04-05

### Added
- **주석 처리된 코드 금지 컨벤션** — 테스트 파일에서 assertion/검증 코드 주석 처리 금지 (빌드 게이트 우회 방지)
  - `testing.md`: 규칙 + 근거 추가
  - `common.md`: 체크리스트 항목 추가 (MAJOR)

## [1.43.3] - 2026-04-05

### Fixed
- **Python 스택 스키마 누락** — `project.schema.json` backend enum에 `python-fastapi`, `python-django` 추가 (기존 5개 → 7개)
- **--quick 모드 스택 강제 지정 제거** — 빈 디렉토리에서 `defaultStack`(Spring Boot) 강제 적용 → 백엔드 프레임워크 직접 선택 폴백으로 변경

## [1.43.2] - 2026-04-05

### Added
- **에러 코드 체계** — ecommerce(29코드), saas(25코드), healthcare(26코드) error-codes.json 신규
- **헬스체크 카테고리** — ecommerce(inventory-consistency), saas(tenant-isolation), healthcare(phi-protection) health/_category.json 신규
- **키워드 충돌 해소** — _registry.json에 keywordPolicy 추가 (결제/정산/구독 3건 충돌 문서화)

### Fixed
- **도메인 시뮬레이션 B등급 이슈 수정** — 상태 머신 엣지 케이스, 컴플라이언스, 크로스도메인 개선
  - **ecommerce**: 셀러 terminated 서브오더 처리 정책, 서브오더 created→cancelled/paid→cancel_requested 전이 추가, 정산 disputed 이체 배치 제외 규칙, 구독 적용 범위 명시, fintech 결제 매핑 참조
  - **fintech**: FDS 심각도 MAJOR→CRITICAL, 제3자 제공 심각도 CRITICAL 통일, 마이데이터 토큰 로깅 금지 항목 추가
  - **saas**: 구독 canceled→active 복구 전이 추가, 인보이스 전이 검증, progressive backoff 용어 수정, 제3자 제공 CRITICAL 통일, 구독 적용 범위 명시
  - **healthcare**: 예약 이중 예약 방지 제약 조건 추가

## [1.43.1] - 2026-04-05

### Fixed
- **도메인 시뮬레이션 A등급 이슈 수정** — 5개 도메인 상태 머신/문서 정합성 45건 해결
  - **fintech**: 정산 상태 전이 테이블 신규 작성, 환불 상태 머신 SSOT 통일(refund-cancel.md), 결제 전이 domain-logic.md↔payment-flow.md 동기화, 마이데이터 retrying→failed 다이어그램 수정, README에 open-banking/mydata 문서 추가
  - **ecommerce**: 주문 상태 머신 11→13개 통일(문서↔템플릿), 주문↔결제 상태 매핑 테이블 추가, 재고 예약 TTL KT 15→30분 통일, TS 가격 계산 BigDecimal 대안 안내, README 참고 문서 5건 추가, domain-logic.md 전이 테이블 동기화
  - **saas**: 인보이스 허용 전이 테이블 추가, 구독↔테넌트 상태 연동 규칙 정의, glossary.md 17개 용어 추가
  - **healthcare**: glossary.md 23개 의료 용어 추가
  - **cross-domain**: 4개 도메인 domain.json에 `_base` 체크리스트(common, security-basic, architecture) 참조 추가

## [1.43.0] - 2026-04-04

### Added
- **Healthcare 신규 도메인** — PHI 보호, 진료기록, 처방, 환자 동의, 보험 청구 전용 도메인
  - `domain.json`: 10 keyword 그룹 (64 트리거), compliance 5개 (HIPAA, 의료법, 개인정보보호법, 생명윤리법, 진료기록보존규정), PostgreSQL 기본 스택
  - docs/ 7개:
    - `phi-data-handling.md`: PHI 18개 식별자, 비식별화(Safe Harbor/Expert Determination), 저장/전송/로깅 규칙, 보존/폐기 기간
    - `access-control.md`: 역할 계층(System Admin→의사→간호사→약사→접수→환자), 접근 제어 매트릭스, 환자-의료진 관계 접근, Break-the-Glass(4시간 자동 만료), HL7 FHIR 리소스 매핑
    - `audit-trail.md`: HIPAA Security Rule 감사, 필수 기록 이벤트 10종, 감사 로그 12 필드, 불변성(append-only), 보존 10년
    - `consent-management.md`: 동의 상태머신(6 states, +denied), 동의 유형 4종, 철회 처리, 응급 예외, 미성년자 동의
    - `prescription-flow.md`: 처방 상태머신(8 states, +expired), DUR 검증 7항목, 용량 검증, 마약류 특별 규정
    - `appointment-flow.md`: 예약 상태머신(6 states), 접수/수납 플로우, No-show 처리
    - `billing-claims.md`: 청구 상태머신(7 states, +rejected/appealed), 급여/비급여, 심사/삭감 대응
  - checklists/ 3개:
    - `security.md`: PHI 암호화, 로깅 금지, 접근 통제, Break-the-Glass, 전송 보안 (12 CRITICAL)
    - `compliance.md`: HIPAA Privacy/Security Rule, 의료법, 개인정보보호법(민감정보 제23조), 생명윤리법, 진료기록 보존 (10 CRITICAL)
    - `domain-logic.md`: 처방/예약/동의 상태 전이, DUR 약물 상호작용, 진료기록 무결성, 환자 식별 (8 CRITICAL)
- `pr-reviewer-domain.md`: healthcare 중점 검토 항목 8개 (PHI 접근, 처방 전이, 동의 검증, 진료기록 무결성, 감사 로그)
- `pr-reviewer-security.md`: healthcare 보안 검토 항목 8개 (PHI 평문 저장, 로그 출력, 비암호화 전송, 동의 없는 제공)
- `project.schema.json`: domain enum에 "healthcare" 추가

## [1.42.0] - 2026-04-04

### Added
- **SaaS 신규 도메인** — 멀티테넌시, 구독 결제, 사용량 과금 등 SaaS 플랫폼 전용 도메인
  - `domain.json`: 8 keyword 그룹 (52 트리거), compliance 4개 (GDPR, 개인정보보호법, SOC2, 정보통신망법), PostgreSQL 기본 스택
  - docs/ 6개:
    - `tenant-isolation.md`: 테넌트 격리 전략(DB/스키마/RLS), 테넌트 상태머신(4 states), RBAC 역할 계층, API 키 관리, 리전 데이터 레지던시
    - `subscription-billing.md`: 구독 상태머신(7 states), 과금 모델 5종(flat/seat/usage/tiered/hybrid), 프로레이션, 인보이스
    - `onboarding-provisioning.md`: 가입/프로비저닝 플로우, 트라이얼 관리, 셀프서비스 설정
    - `data-lifecycle.md`: 데이터 분류, GDPR 삭제권/이동권, 테넌트 오프보딩(90일 보존), 감사 로그 스키마
    - `usage-metering.md`: 사용량 미터링, 쿼터(소프트/하드), 초과 과금, 피처 게이팅
    - `webhook-integration.md`: 테넌트 웹훅 설정, at-least-once 배달, HMAC-SHA256 서명 검증
  - checklists/ 3개:
    - `tenant-security.md`: 테넌트 격리 14 CRITICAL, 크로스테넌트 방지, 세션 격리
    - `compliance.md`: GDPR/PIPA/SOC2/정보통신망법, 감사 로그 필수 필드, 데이터 보존/폐기
    - `domain-logic.md`: 구독 상태 전이, 과금 BigDecimal, 프로레이션, 미터링, 피처 게이팅, Noisy Neighbor 방지

## [1.41.3] - 2026-04-04

### Fixed
- ecommerce 도메인 리뷰 수정 (ERROR 6건, WARN 8건)
  - `marketplace.md`: 셀러 상태머신 다이어그램 수정 (active→terminated, rejected 노드 누락), 서브오더 허용 전이 테이블 추가, 수수료 공식에 PG 수수료 추가
  - `seller-settlement.md`: adjusted 상태 탈출 경로 추가 (adjusted→confirmed), 허용 전이 테이블 추가, 프로모션 분담금 규칙 명확화
  - `subscription-commerce.md`: 상태머신 다이어그램 전면 재작성, paused→canceled(90일 초과) 전이 추가, created→canceled(최초 결제 실패) 전이 추가, 재시도 횟수 명확화 (3회 재시도=총 4회 시도)
  - `domain-logic.md`: adjusted 재확정 체크리스트 항목 CRITICAL 추가, 일시정지 기한 MINOR→MAJOR 상향
  - `compliance.md`: 분쟁 해결 MAJOR→CRITICAL 상향, 판매자 신원 확인 정부 등록부 대조 추가, 통신판매중개업법→전자상거래법(통신판매중개의무) 명칭 수정
  - `domain.json`: compliance 명칭 수정, marketplace에 정산 트리거 추가, subscription에 일시정지/재개/프로레이션/일할계산 트리거 추가
- fintech 도메인 리뷰 수정 (ERROR 5건, WARN 7건)
  - `open-banking.md`: canceled 상태 테이블 정의 추가, 종료 상태 명시, 에러 코드 A0400~A0899 예약 대역 추가, 이체 API(출금/입금) SLA 5초 추가, 수취인→예금주 용어 통일
  - `mydata.md`: 동의 철회 규칙 명확화 (즉시 전송 중단 + 5영업일 이내 삭제)
  - `compliance.md`: 동의 철회 "즉시"→"즉시 전송 중단 + 5영업일 이내 삭제" 수정, 타임아웃 SLA 상세화, 동의 이력 5년 보존 항목 추가
  - `domain-logic.md`: 전송 실패 후 expired→failed 상태 수정 (expired는 동의 유효기간 만료 전용), 재동의 검증 항목 추가
  - `domain.json`: open-banking 트리거에 이체 추가

### Changed
- README.md: 도메인 테이블에 오픈뱅킹/마이데이터/마켓플레이스/구독 커머스 반영, 컴플라이언스 확장 표시

## [1.41.2] - 2026-04-04

### Added
- fintech 도메인 오픈뱅킹/마이데이터 확장
  - `open-banking.md`: 이용기관 등록, 사용자 인증(OAuth 2.0), 토큰 관리, 계좌 조회/이체 플로우, 이체 상태머신(8 states), 에러 코드 대역
  - `mydata.md`: 전송요구 상태머신(8 states), 데이터 수집 범위, 동의 관리, 데이터 보관/폐기 규칙, API 규격
- fintech 체크리스트 확장
  - `compliance.md`: 오픈뱅킹 규정(CRITICAL 4건), 마이데이터 규정(CRITICAL 3건)
  - `domain-logic.md`: 오픈뱅킹 연동(CRITICAL 3건), 마이데이터 연동(CRITICAL 2건)
- fintech `domain.json` keywords 2개 추가 (open-banking, mydata), compliance에 오픈뱅킹규정·신용정보법 추가

## [1.41.1] - 2026-04-04

### Added
- ecommerce 도메인 마켓플레이스 확장
  - `marketplace.md`: 셀러 상태머신(6 states), 멀티셀러 주문 분리, 서브오더 상태머신, 커미션 모델, 셀러 등급 체계
  - `seller-settlement.md`: 정산 상태머신(8 states), 정산 주기(D+N), 정산 계산 구조, 반품/환불 처리, 정산 리포트
  - `subscription-commerce.md`: 구독 상태머신(6 states), 결제 주기, 결제 실패 재시도(3회), 프로레이션 계산
- ecommerce 체크리스트 확장
  - `domain-logic.md`: 마켓플레이스 섹션(CRITICAL 4건), 구독 커머스 섹션(CRITICAL 1건)
  - `compliance.md`: 통신판매중개업자 의무 섹션(CRITICAL 3건)
- ecommerce `domain.json` keywords 2개 추가 (marketplace, subscription), compliance에 통신판매중개업법 추가

## [1.41.0] - 2026-04-04

### Added
- 프레임워크 정체성 명시: "프로세스 관리 프레임워크"로서의 역할 경계 문서화
  - CLAUDE.md.tmpl: `프레임워크 역할 경계` 섹션 — 프레임워크(워크플로우·품질게이트·컨벤션) vs Claude(코드작성·기술판단) 분리 명시
  - README.md: 프레임워크 철학 한 문단 추가
  - docs/concepts.md: `설계 철학: 프레임워크와 AI의 역할 분리` 섹션 — 분리 이유 3가지, 프레임워크가 하지 않는 것 목록
- `security.md` 비-REST 프로토콜 보안 가이드: WebSocket(`wss://`, Origin 검증, 핸드셰이크 인증), SSE, gRPC 보안 요구사항
- `skill-feature` Step 2.5 통신 방식 확인: 실시간 요구사항 감지 시 프로토콜(REST/WebSocket/SSE/gRPC) 선택 유도, spec에 통신방식 항목 반영

### Fixed
- TEMPLATE-ENGINE.md `ext_map` 버그: `backend:"none"` (프론트엔드 전용) 시 `.kt.tmpl` 폴백 → `None` 반환으로 수정
- TEMPLATE-ENGINE.md `ext_map` Python 누락: `python-fastapi`, `python-django` → `.py.tmpl` 매핑 추가

## [1.40.0] - 2026-04-03

### Added
- Python 퍼스트클래스 생태계: FastAPI/Django를 Spring Boot와 동등 수준으로 지원
  - `python-project-structure.md`: FastAPI/Django 프로젝트 구조 컨벤션
  - `python-testing.md`: pytest 중심 테스팅 가이드 (fixture, 피라미드, 커버리지)
  - `python-dependency.md`: pyproject.toml, poetry/pip, Alembic 마이그레이션
  - `python-patterns.md`: Pydantic DI, async, SQLAlchemy, 예외 처리 패턴
- Python 코드 리뷰 규칙: 아키텍처(5건), 보안(3건), 테스트(4건) 항목 추가
- Sub-agent Python 리뷰: pr-reviewer-security/domain/test에 Python 탐지 패턴 및 검증 테이블
- 체크리스트 Python 항목: security-basic(5건), architecture(9건), common(4건) 추가
- `skill-init` Python 초기화: 스택 선택 가이드 + 스캐폴딩 상세 (pyproject.toml, app/ 구조)
- `skill-onboard` Python 자동 감지: FastAPI vs Django 판별 휴리스틱 4단계

### Removed
- `agent-devops` 제거 (ADR-009): 사용률 0%, 스킬 연동 0건, 예제 2/2 비활성
  - 삭제: `.claude/agents/agent-devops.md` (520줄)
  - 참조 제거: CLAUDE-example, concepts.md, 예제 2개
  - 유지: `deployment.md` 컨벤션 (독립 참조 문서)

### Changed
- `agent-backend.md`: Python 빌드/테스트 명령, 패키지 구조, 코딩 가이드 추가
- `project-structure.md`: Python (FastAPI/Django) 구조 추가 + 상세 컨벤션 참조
- `docs/concepts.md`: 지원 기술 스택 섹션 신설 (6개 백엔드 + 5개 프론트엔드)
- `docs/getting-started.md`: Python 프로젝트 시작 가이드 추가

## [1.39.0] - 2026-04-02

### Added
- 스텝별 `prLineLimit` 오버라이드: skill-plan이 스텝 특성에 따라 자동 설정 (50~1000)
  - 폴백 체인: step.prLineLimit > conventions.prLineLimit > 500
  - 프로필별 동적 기준: standard limit×0.6/limit/limit×1.4, fast limit/limit×2
- `skill-upgrade` 신규 기능 안내 (Step 15.5): 업그레이드 시 새 기능을 action별로 안내
  - `migrations.json`에 `features` 배열 추가 (action: none/recommend/required)

### Changed
- `backlog.schema.json`: step 정의에 `prLineLimit` 필드 추가 (optional, minimum 50)
- `skill-plan` §4: 스텝 분리 시 prLineLimit 자동 설정 가이드라인 (마이그레이션→100~200, 서비스→500~800, 테스트→700~1000)
- `skill-impl` §4: 라인 검증 동적화 (고정 테이블 → 폴백 체인 + 비율 기반 산정)
- `CLAUDE.md.tmpl`: 라인 제한 섹션 동적 테이블로 교체 + 자동 조정 안내

## [1.38.1] - 2026-04-01

### Added
- 스택 인식 확장: Python(FastAPI/Django), React Vite, Vue, Vue-Nuxt, Astro, Next.js 분리 (4종→11종)
- `--quick` 빈 디렉토리 폴백: 감지 실패 시 프로젝트 유형 1회 질문 (5개 선택지)
- Step 4 선택지에 `none` 옵션: 백엔드 전용/프론트엔드 전용 프로젝트 지원
- DB 선택지 확장: postgresql, mongodb, sqlite, none
- Maven 빌드 지원: `pom.xml` 감지, `mvn package/test/checkstyle:check` 빌드 테이블
- `skill-impl` allowed-tools: go, golangci-lint, mvn, mvnw, python, pytest, ruff, poetry, pip, npx 추가

### Changed
- 에이전트 팀 구성: "backend 항상 필수" → 스택 기반 자동 결정 (백엔드만/프론트엔드만/풀스택)
- `skill-onboard` 빌드 명령어 감지: Python, Next.js, React Vite, Vue, Nuxt, Astro 전체 추가
- `skill-onboard` 스캔 대상: Python 패키지 매니저(poetry/pipenv/pip) 추가

## [1.38.0] - 2026-04-01

### Added
- `skill-impl --micro "설명"`: 소규모 작업 경량 경로 (plan 생략, 바로 구현→PR)
- Micro 전용 라인 제한: ≤150줄 정상, 150~300줄 경고, >300줄 차단→Standard 전환
- 프론트엔드 컨벤션 4개: `frontend-component.md`, `frontend-testing.md`, `frontend-styling.md`, `frontend-state.md`
- 패키지 매니저 자동 감지: yarn.lock, pnpm-lock.yaml, bun.lockb (우선순위: bun>pnpm>yarn>npm)
- pr-reviewer-domain 프론트엔드 검증: a11y(MAJOR), 컴포넌트 크기, prop drilling, 테스트 존재, 인라인 스타일
- `backlog.schema.json`: task.micro boolean 필드 (Micro Task 식별)
- 자연어 매핑 3개: "OO 고쳐줘", "OO 버그 수정해줘", "간단하게 OO 추가해줘" → --micro
- TEMPLATE-ENGINE.md 컨벤션 트리거 테이블에 프론트엔드 4개 항목 등록

### Changed
- `skill-impl` 빌드 테이블: yarn/pnpm/bun 명령어 + Lock 파일 감지 로직 추가
- `skill-impl` allowed-tools: `Bash(pnpm:*)`, `Bash(bun:*)` 추가
- `skill-onboard` 스캔 대상: 패키지 매니저 Lock 파일 3종 추가
- `skill-report` Throughput: Micro Task 비율 메트릭 추가

## [1.37.0] - 2026-04-01

### Added
- 에러 복구 프로토콜: CLAUDE.md.tmpl에 10가지 에러 유형별 표준 복구 가이드 인라인
- `skill-impl --retry`: 실패한 스텝 재시작 (PR close + 브랜치 정리 + 재실행)
- `skill-impl --skip`: 빌드 실패 스텝 건너뛰기 (step.status="skipped")
- `/skill-backlog dashboard`: Phase별 진행률 + in_progress + blocked + 다음 착수 가능 Task
- `/skill-backlog archive`: Task soft delete (status="archived", list 기본 제외)
- `/skill-backlog batch`: 다중 Task 일괄 변경 (dry-run + 확인 + 원자적 실행)
- `/skill-backlog deps`: 의존성 텍스트 트리 + `--reverse` 영향도 분석
- `task.type` 필드: feature | bug | chore | spike (add 시 AI 추론)
- `docs/getting-started.md` "첫 기능 만들기" 5단계 워크스루
- 자연어 매핑 13개 추가 (--retry, --skip, dashboard, deps, archive, batch 등)

### Changed
- `skill-backlog update` 옵션 확장: --title, --description, --phase, --type, --reason
- `skill-backlog list` 필터 확장: --type, --assignee=me, --stale
- `skill-impl --next/--all`: skipped 스텝 호환 (이전 스텝이 skipped면 다음 진행 허용)
- `backlog.schema.json`: task.status에 "archived", step.status에 "skipped" 추가
- `skill-health-check`: archived Task 건강 검진 제외, archived/skipped/type enum 인식
- `skill-status`: archived 카운트 별도 표시
- `skill-report`: Task type별 분포 + 스킵 비율 메트릭 추가
- 5개 핵심 스킬에 에러 복구 프로토콜 참조 + fallback 추가

## [1.36.0] - 2026-03-31

### Added
- `/skill-review-pr config` 서브커맨드: 리뷰 모드 설정 관리 (조회/변경/초기화)
- 리뷰 모드 2단계: `full` (domain+security+test, 디폴트) / `standard` (domain+security)
- 커스텀 에이전트 조합: `--agents domain,test` 형태로 자유 구성 (domain 필수)
- PR 단위 모드 오버라이드: `--mode standard|full` 옵션
- 리뷰 결과 헤더에 실행/미실행 에이전트 목록 표시

### Changed
- Trivial PR Fast Path 기준 완화: 30줄 → 50줄 (경량 리뷰 대상 확대)
- Step 3 리뷰 엔진: 고정 3-agent → 모드 기반 N-agent 선택적 실행

## [1.35.2] - 2026-03-30

### Changed
- 6개 에이전트 `model: opus` 제거 → 부모 모델 자동 상속 (Pro→sonnet, Max→opus 자동 적용)
- PR diff 배달 방식 변경: 프롬프트 3회 포함 → `/tmp/` 파일 저장 + 경로 전달 (부모 컨텍스트 토큰 ~67% 절감)
- diff 파일 생명주기 관리: 생성→공유→갱신(auto-fix시)→유지→정리(머지시)
- skill-plan/skill-impl 에이전트 프롬프트 경량화 (경로/목록만 전달, 에이전트 자체 Read)

### Removed
- pr-reviewer-test의 domain-logic.md 중복 로드 (pr-reviewer-domain이 담당)

## [1.35.1] - 2026-03-29

### Added
- `/skill-health-check` CRITICAL/MAJOR FAIL 시 backlog.json에 Task 자동 등록 (MINOR은 리포트만)
- `/skill-review-pr` 경량 리뷰 판정 (Trivial PR Fast Path): additions+deletions ≤ 30 && src/ 변경 0건 && 보안 키워드 미포함 시 3-agent 리뷰 스킵

## [1.35.0] - 2026-03-29

### Added
- 추세 경보: 3회 연속 FAIL 항목 감지, 점수 하락 추세, 카테고리 failCap 경고
- "정리해줘" 자연어 매핑 → `/skill-health-check --fix` 자동 전환 (dry-run 확인 포함)
- `/skill-status` 검진 주기 안내 (7일/14일 경과 시, suppressReminder 설정 가능)
- history 50건 초과 시 자동 정리 (oldest 삭제)
- streak 판정 규칙 명확화 (SKIP 미중단, ERROR=FAIL, fix 제외, PASS 리셋)

### Fixed
- Phase C 점수 계산: 전 항목 SKIP 카테고리 제로 분모 방지 (가중치 재분배)
- Phase B autoFix: 실패/거절 시 FAIL 기록, fixesApplied에 성공 항목만 포함
- SEC-01 패턴 확장: apiKey, token, bearer, authorization 추가 + 타입 선언 제외
- SEC-02 범위 확장: JPA @Query, JDBC string concatenation 탐지 대상 추가
- Post-Merge Health Gate: 이력 없을 때 추세 비교 스킵
- health-history.schema.json: mode 필드 enum 제한 (full/quick/scope/fix/quick-fix)

## [1.34.0] - 2026-03-27

### Added
- `/skill-health-check` 코드베이스 건강 검진 (22개 검사 항목, 점수 + 등급 + 이력 추적)
- 기본 보안 검사 4개 항목 (민감정보, SQL Injection, CORS, API 인증 — 전체 도메인)
- fintech 도메인 컴플라이언스 검사 4개 항목 (감사 로그, 멱등성, 금액 정밀도, 트랜잭션)
- `health-history.schema.json` 검사 이력 스키마
- `/skill-merge-pr` Post-Merge Health Gate (CRITICAL 자동 감지)
- `/skill-release` 사전 Health Gate (선택적)
- `/skill-status --health` → `/skill-health-check` 에스컬레이션 안내
- `docs/skill-reference.md` 검증 도구 선택 가이드

### Changed
- `project.schema.json`에 `healthCheck` 설정 필드 추가

## [1.33.1] - 2026-03-16

### Fixed
- skill-upgrade Step 13: CLAUDE.md 재생성 시 서브 에이전트 위임 금지 + 결정적 치환 원칙 적용 (구 버전 복사 방지)
- TEMPLATE-ENGINE.md: 결정적 치환 원칙 명시 (기존 CLAUDE.md는 CUSTOM_SECTION 추출에만 사용)

### Added
- skill-upgrade Step 13-3: 재생성 검증 게이트 (포지티브/네거티브 체크 + 재시도)
- TEMPLATE-ENGINE.md: 재생성 정합성 검증 규칙 (upgrade 시 템플릿 반영 확인)

## [1.33.0] - 2026-03-15

### Changed
- 컨텍스트 한계 관리: 70% 강제 중단 → compact 허용 + 상태 파일 조건부 복구 + 작업 계속 진행 (76줄 → 12줄)
- compact 후 복구: 3파일 무조건 읽기 → 조건부 읽기 (backlog만 항상, plan/project는 필요 시)

### Added
- customization.md: CUSTOM_SECTION 활용 예시 2건 (compact 알림 절충안, 프로젝트 코딩 규칙)

## [1.32.1] - 2026-03-15

### Fixed
- skill-plan/feature: allowed-tools에 AskUserQuestion 누락 복구 (v1.29.0 merge 충돌 해소 시 유실)
- 컨텍스트 한계 관리: 모델별 총 컨텍스트 크기 확인 절차 추가 (Opus 1M을 200k로 오인하여 조기 중단 방지)

### Removed
- 고아 파일 shared-protocols.md 삭제 (v1.32.0 압축으로 미참조 상태)

## [1.32.0] - 2026-03-15

### Changed
- CLAUDE.md 템플릿: Git 워크트리 프로토콜 결정 테이블 + 워크플로우 상태 추적 프로토콜 추가 (SSOT 강화)
- 22개 SKILL.md 선언적 압축 (8,361줄 → 2,165줄, 74% 절감)
  - bash 코드 블록 → 선언적 요구사항 전환
  - CLAUDE.md 프로토콜 반복 제거 → 참조 + 단계명 힌트 2줄로 통일
  - 출력 포맷 템플릿 → 필수 필드 목록으로 축소
  - 워크플로우 체인당 토큰 ~54,500 → ~11,300 (79% 절감)
- 모든 스킬의 기능 로직, 결정 트리, Tier S 명령(squash merge 플래그, Intent 스키마 등) 100% 보존

## [1.31.1] - 2026-03-12

### Fixed
- `examples/README.md`: ecommerce-shop 예제 목록 누락 수정 (v1.28.0에서 추가되었으나 목록 미갱신)

## [1.31.0] - 2026-03-11

### Added
- `docs/customization.md` 확장 (79→249줄) — domain.json 전체 구조 워크스루, 체크리스트 형식 가이드, Layered Override 상세 설명
  - domain.json 주요 필드 설명 테이블 + keywords 동작 방식 워크스루
  - 체크리스트 심각도(CRITICAL/MAJOR/MINOR) 설명 + 실전 예시
  - 디렉토리 구조 트리, _registry.json 등록 예시, 도메인 생성 3가지 방법

### Fixed
- domain.json 문서 예시를 실제 `ecommerce/domain.json`과 일치시킴 (conventions, defaultStack 필드 정합성)

## [1.30.0] - 2026-03-11

### Added
- README.md "빠른 시작": 기존 프로젝트용 `/skill-onboard` 진입점 추가 (신규 사용자 발견성 개선)
- `docs/getting-started.md`: 온보딩 섹션 확장 — 준비 단계, 실행 흐름 다이어그램, `--scan-only` 옵션, 온보딩 후 다음 단계
- `examples/README.md`: "기존 프로젝트에 적용" 섹션 추가 (`/skill-onboard` + `--scan-only` 안내)

## [1.29.0] - 2026-03-11

### Added
- `shared-protocols.md`: 9개 공통 프로토콜 SSOT 문서 신규 생성 — Protocol A(project+backlog 검증), B(completed 검증), C(운영환경 검증), D(origin/develop 동기화), E(Worktree 감지), F(빌드 명령어 결정), G(에러 3줄 표준), H(AskUserQuestion 승인), I(진행 표시)
- 독립 스킬 5개(retro, report, estimate, create, onboard)에 간소화 진행 표시 추가 (Protocol I)

### Changed
- 14개 스킬의 MUST-EXECUTE-FIRST 중복 검증(~20줄씩) → Protocol 참조로 교체 (순 -197줄 감소)
- 에러 메시지 전체 3줄 표준화: ❌ 에러 / 원인 / 해결 (Protocol G)
- 승인 프롬프트 Y/N → AskUserQuestion 통일 (Protocol H)
- skill-feature, skill-plan: allowed-tools에 `AskUserQuestion` 추가 (Protocol H 정합성)

## [1.28.0] - 2026-03-11

### Added
- ecommerce-shop: `SHOP-002-spec.md` 주문 처리 시스템 설계 명세 — 상태 머신 11가지, 재고 동시성(낙관적 락), 가격 계산(Zod 정수 강제), 에러 코드 5종, 테스트 15건, Production Readiness Gaps 11항목
- ecommerce-shop: `CLAUDE.md` 프로젝트 지시문 — fintech-gateway와 대칭 구조 (에이전트 5종, 키워드 매핑 6종, 체크리스트 5관점, 에러 코드 체계)
- ecommerce-shop: `backlog.json` SHOP-002에 steps 2개 추가 (주문 CRUD+상태머신 ~400줄, 가격계산+테스트 ~350줄)

### Fixed
- README.md: 버전 배지 `v1.25.0` → `v1.27.0` 정합성 수정
- SHOP-002-spec.md: 에러 응답에서 재고 수량 노출 제거 (보안)
- SHOP-002-spec.md: 금액 정수 강제 Zod `z.number().int()` 스키마 + `Math.max(0)` 음수 방지 추가
- SHOP-002-spec.md: 테스트 10건 → 15건 확충 (상태전이 전수, 가격 스냅샷, 경계값, 쿠폰 동시성, 음수 방지)
- SHOP-002-spec.md: Production Readiness Gaps 7건 → 11건 확충 (인증 상세, 멱등성, 암호화, 동의, 에스크로)
- order-flow.md: REFUNDED 상태 누락 → 추가 (SSOT 정합성)

## [1.27.0] - 2026-03-10

### Added
- skill-validate: Category 10 도메인 키워드 참조 정합성 — `keywords.*.docs[]` ↔ 실제 파일 ERROR 레벨 검증, `_base:` 접두사 경로 해석 지원
- skill-validate: Category 11 스키마-데이터 정합성 — project.json/backlog.json이 스키마 required 필드를 준수하는지 검증
- skill-validate: Category 12 레지스트리-도메인 교차 검증 — `_registry.json` ↔ `domain.json` 간 name/icon/description/keywords 일치 확인
- domain.json: 3개 도메인(fintech/ecommerce/general)에 `icon` 필드 추가 — Category 9 검증 통과
- ecommerce: `member.md` 신규 — 회원가입/로그인/마이페이지/탈퇴/법적 보관 의무
- ecommerce: `product.md` 신규 — 상품 구조/상태 전이/카테고리/가격 정책
- ecommerce: `member` keyword 추가 ("회원", "회원가입", "로그인", "마이페이지", "탈퇴")
- general: keyword docs를 `_base:conventions/` 접두사 참조로 전환 — 중복 문서 방지, `_base/conventions/` 재활용
- BDD 시나리오 구조화: `docs/scenarios/` — Given/When/Then YAML 형식 + full-feature.yaml 예시
- workflow-guide: 판단 분기점 테이블 5건 + Troubleshooting 7건 추가
- SSOT 원칙 적용: CLAUDE.md/TASK-001-spec.md에 도메인 docs 진실점 포인터 추가
- 회귀 테스트 전략: `docs/regression-testing.md` — fintech-gateway Golden State 지정 + 검증 절차

### Fixed
- TASK-001-spec.md: refresh 에러 응답 내부코드(PG-GW-016) → 외부코드(TOKEN_INVALID) 변경
- error-handling.md: SSOT에 PG-GW-012 (INVALID_CREDENTIALS) 누락 → 추가
- _registry.json: lastUpdated 갱신 + description/compliance/keywords 동기화
- ecommerce domain.json: "장바구니" trigger 추가 (registry-domain 불일치 해소)
- fintech domain.json: "토큰/PG/VAN/가맹점" trigger 추가 (registry-domain 불일치 해소)

### Changed
- workflow-guide: 설계 스텝 표시 "Step 1,2,3" → "Step 1,2" 조정

## [1.26.0] - 2026-03-10

### Added
- TASK-001-spec: 의존성 GAV 고정 — Spring Cloud BOM 2024.0.0, jjwt 0.12.6, Kotlin 2.0.21, Spring Boot 3.3.5, MockK 1.13.13
- TASK-001-spec: WebFlux 주의사항 — 서블릿 코드(`@Controller`, `MockMvc`, `HttpServletRequest`) 혼입 금지 명시
- TASK-001-spec: 구성 요소 상세화 — 래퍼 타입(AccessToken/RefreshToken), InMemoryUserRepository, BCryptPasswordEncoder(cost 12), GlobalExceptionHandler, Logback eyJ 마스킹 필터
- TASK-001-spec: UserRepository 인터페이스 분리 — NFR-003 확장성(추후 RDB 전환) 준수
- TASK-001-spec: 테스트 명세 12건 추가 — 단위 9건, 동시성 1건, 보안 1건, E2E 1건 (WebTestClient 필수)
- TASK-001-spec: 수용 기준 8항목 추가 — 브랜치 커버리지 80%, PCI-DSS, eyJ 마스킹, 래퍼 타입 등
- TASK-001-spec: Production Readiness Gaps 9항목 — InMemory→Redis, HS256→RS256, JSON body→Cookie 등
- TASK-001-spec: 블랙리스트 동시성 전략 — `ConcurrentHashMap.newKeySet()` 명시
- CLAUDE.md: 에러 코드 외부 매핑에 `INVALID_CREDENTIALS` 추가 (PG-GW-012 내부 전용)
- CLAUDE.md: 브랜치 커버리지 80%+ 목표, WebTestClient 필수 (MockMvc 금지) 명시

### Changed
- TASK-001-spec: 스텝 분리 3→2 합침 (Step 1: 스캐폴딩+모델+구현 ~450줄, Step 2: 필터+컨트롤러+테스트 ~300줄)
- TASK-001-spec: 로그인 에러 외부코드 `PG-GW-012` → `INVALID_CREDENTIALS`로 변경 (내부코드 노출 방지)
- project.json: infrastructure `docker-compose` → `none` 변경

## [1.25.1] - 2026-03-10

### Fixed
- backlog.json 스키마 정합성: `metadata.version` 필드 추가 (동시성 제어 필수), task `id` 필드 추가, `phase` 타입 integer로 수정, `specFile` 필드명 통일
- project.json 스키마 정합성: `version` (required) 필드 추가, `metadata.version` 동시성 제어 필드 추가
- backlog.schema.json: phases에 `required: ["name", "status"]` + `additionalProperties: false` 보강
- 에러 코드 확정: Token Reuse Detection → PG-GW-016 (TOKEN_REUSED)으로 통일 (TASK-001-spec.md, token-auth.md, CLAUDE.md, error-handling.md)
- Refresh Token 전달 방식 확정: 데모=JSON body 채택, 프로덕션=HttpOnly Cookie 권장사항 문서화 + XSS 보안 제약 경고 추가
- 양쪽 예제(fintech-gateway, ecommerce-shop) 동일 적용

## [1.25.0] - 2026-03-09

### Added
- skill-impl: push 전 develop 동기화 — 다른 세션의 backlog.json 변경 반영, push 실패 시 충돌 해소 + 재시도
- skill-impl: branch 중복 방지 — 기존 branch/PR 상태 확인 후 생성/이어서 작업/스킵 분기
- skill-impl: 워크트리 merge 후 step 상태 재검증 — 이미 완료된 step 스킵, 충돌 경고
- skill-impl: step 완료 시 `assignedAt` 자동 갱신 — lock heartbeat 효과
- skill-merge-pr: completed.json version 관리 — `metadata.version`/`updatedAt` 동시성 제어 도입
- skill-merge-pr: push 전 develop 동기화 — state 파일 충돌 방지
- skill-merge-pr: 워크트리 → develop 명시적 동기화 (섹션 5.7) — state 파일 메인 리포 반영
- skill-backlog: JSON 충돌 해소 규칙 명시 — 다른 Task는 모두 유지, 같은 필드는 최신 우선, version = max + 1
- skill-status: execution-log.json 동시 쓰기 안전 규칙 — append-only + push 충돌 시 재추가
- skill-plan: 섹션 7 lockedFiles push 성공 확인 필수 + 충돌 시 교집합 검사
- project.schema.json: `metadata.version`/`updatedAt` 동시성 제어 필드 추가

## [1.24.0] - 2026-03-08

### Added
- skill-plan: Task 조기 잠금(섹션 1.5) — 선택 즉시 `in_progress` + git push로 동시 세션 중복 선택 방지
- skill-plan: 계획 거절 시 롤백 — `todo`로 복원 + git push로 잠금 해제
- skill-status: `--locks`에 🟡 계획 중 상태 표시 (`lockedFiles` 비어있는 `in_progress` Task 구분)
- README.md: 리디자인 — 중앙 정렬 헤더, shields.io 배지 4개, 이모지 섹션 헤더, GitHub Alert 블록, blockquote 원칙, 중앙 푸터
- LICENSE: MIT 라이선스 파일 신규 생성

### Changed
- skill-plan: 섹션 7(승인 후) 축소 — status/assignee는 조기 잠금에서 설정, 승인 후는 lockedFiles/steps만 갱신
- skill-plan: Git 동기화 프로토콜 충돌 해소 로직 보강 — 같은 Task 중복 claim 시 재선택
- README.md: 제목에서 버전 번호 제거 → 배지로 이동 (릴리스 시 제목 수정 불필요)
- README.md: 요구사항 섹션 하단 이동, 정보 우선순위 재배치

## [1.23.0] - 2026-03-05

### Added
- skill-domain: `create` 명령어 추가 — `--ref` 참조 도메인 기반 새 도메인 생성 + AI 초기 문서 자동 생성
- skill-domain: `disable-model-invocation: false`로 변경 (AI 문서 생성 지원)
- skill-validate: 검증 항목 #9 도메인 완전성 검증 추가 (domain.json 필수 필드, docs/ 최소 파일)
- skill-retro: `lessons-learned.json` 구조 설계 + 회고 시 학습 항목 자동 추출/저장 (Step 5.5)
- skill-retro: `--lessons` 명령어 추가 (list/search/top 하위 명령)
- skill-plan: "과거 학습 반영" 절차 추가 — lessons-learned.json에서 관련 항목 로드 후 설계 참고

### Changed
- skill-domain: allowed-tools에 `Edit` 추가
- skill-domain: argument-hint에 `create` 추가

## [1.22.0] - 2026-03-04

### Added
- 워크플로우 프로필 (standard/fast): project.schema.json에 `workflowProfile` 필드 추가
- CLAUDE.md.tmpl: `{{WORKFLOW_PROFILE}}`, `{{WORKFLOW_CHAINING_RULES}}` 마커 기반 프로필별 체이닝 규칙 동적 생성
- TEMPLATE-ENGINE.md: `generate_workflow_chaining_rules()` 블록 생성기 추가
- skill-init: Step 5.5 워크플로우 프로필 선택 질문 추가 (--quick 시 standard 자동)
- skill-impl: 프로필별 라인 수 제한 (standard: 700줄, fast: 1000줄)
- skill-impl: 프로필별 다음 스킬 분기 (standard: review-pr, fast: merge-pr 직행)

### Changed
- CLAUDE.md.tmpl: 자동 체이닝 규칙 테이블을 `{{WORKFLOW_CHAINING_RULES}}` 블록 마커로 교체
- CLAUDE.md.tmpl: 중단 조건 "라인 수 700 초과" → "라인 수 제한 초과 (프로필별 상이)"
- CLAUDE.md.tmpl: 워크플로우 진행 표시에서 review-pr/fix 단계에 "(standard에서만 실행)" 주석 추가
- skill-init: project.json conventions 템플릿에 `workflowProfile` 필드 추가

## [1.21.0] - 2026-03-04

### Added
- 워크플로우 진행 표시 프로토콜: 체이닝 스킬 진입 시 표준 진행바 출력 (✅/🔄/⬜ 아이콘 + 단계별 설명)
- 자동 체이닝 전환/중단 출력 포맷: 6가지 전환 사유 + 3가지 중단 사유 표준 메시지 템플릿
- 스킬 진입 시 경량 점검 프로토콜: PR-backlog 상태 자동 보정, Stale workflow 감지(30분), Intent 파일 복구
- 6개 스킬(plan, impl, review-pr, fix, merge-pr, feature)에 워크플로우 진행 표시 섹션 추가
- 4개 스킬(plan, impl, review-pr, merge-pr)에 경량 점검 절차 추가
- skill-impl: 컨벤션 로딩 절차 — 계획 파일의 참조 컨벤션 또는 트리거 테이블 기반 자동 로드
- skill-plan: 스텝 설계 시 "참조 컨벤션" 필드 추가 (skill-impl이 활용)
- skill-review-pr: 리뷰 전 컨벤션 + 체크리스트 로딩 절차 추가
- backlog.schema.json: workflowState.fixLoopCount 필드 추가 (루프 가드)

### Changed
- 컨벤션 레이지 로딩: CONVENTIONS_SECTION 마커가 인라인 컨벤션 → 트리거 테이블로 변경 (토큰 ~60% 절감)
- 에러 코드 레이지 로딩: DOMAIN_ERROR_CODES 마커가 전체 테이블 → 파일 경로 참조로 변경
- TEMPLATE-ENGINE.md: generate_conventions_section(), generate_error_codes_section() 레이지 로딩 방식으로 재설계
- 자동 체이닝 규칙 테이블 3행 추가 (feature→plan, review-pr→fix, fix→review-pr)

## [1.20.0] - 2026-02-24

### Changed
- README.md 구조 개편: 599줄 → 110줄 축소, 상세 내용을 docs/ 6개 파일로 분리
  - `docs/getting-started.md`: 설치 상세 + 초기화 흐름 + 온보딩 안내
  - `docs/concepts.md`: 도메인, 에이전트 팀, 디렉토리 구조, 실행 모델, 핵심 원칙
  - `docs/skill-reference.md`: 22개 스킬 전체 레퍼런스 + 자연어 매핑
  - `docs/workflow-guide.md`: 자동 체이닝, 7가지 워크플로우, 품질 게이트, Git 전략
  - `docs/customization.md`: 도메인 확장, 새 도메인 생성/전환, Layered Override
  - `docs/upgrade-guide.md`: 프레임워크 업그레이드, 보존 항목, 롤백

### Added
- skill-init: `--quick` 모드 — 제로 결정 온보딩 (자동 감지 + 기본값, AskUserQuestion 0회)
  - 디렉토리명 → 프로젝트명, 빌드 파일 기반 도메인/스택 자동 감지
  - 감지 실패 시 general 도메인 defaultStack 사용
  - 기본 에이전트 3개 (pm, backend, code-reviewer)
  - `--quick --reset` 조합 지원

## [1.19.0] - 2026-02-23

### Changed
- skill-status: 정적 "다음 단계 추천"을 컨텍스트 기반 추천으로 교체 (workflowState/PR 상태/백로그 기반 8단계 우선순위)
- skill-review-pr: 서브에이전트 실패 시 사용자 선택 제공 (재시도/스킵/중단), 재시도 1회 허용
- skill-review-pr: 서브에이전트 실패를 execution-log.json에 기록 (subagent_failed 액션)
- 에러 메시지 표준화: skill-estimate, skill-onboard, skill-retro, skill-report, skill-create의 MUST-EXECUTE-FIRST 에러를 ❌/원인/해결 3줄 형식으로 통일

### Added
- skill-status: `--health --fix` 옵션 — Orphan Intent 자동 복구 + 정리 (30분 경과 기준, skill-validate --fix 패턴)

## [1.18.1] - 2026-02-23

### Changed
- 22개 SKILL.md description에 WHEN(사용 시점/트리거 조건) 추가
  - P0: 13개 자동 트리거 스킬 — 자연어 매칭 정확도 개선 (plan, impl, review-pr, fix, merge-pr, report, retro, estimate, create, onboard, hotfix, rollback, docs)
  - P1: 9개 내부 전용 스킬 — 문서화 일관성 확보 (init, feature, review, domain, backlog, status, release, validate, upgrade)
- Anthropic 스킬 가이드 기준 description 필드의 WHAT + WHEN 구조 적용

## [1.18.0] - 2026-02-22

### Added
- 공통 컨벤션 4개 추가 (`_base/conventions/`):
  - cache.md: 캐시 컨벤션 (키 네이밍, TTL 전략, Cache-Aside/Write-Through/Write-Behind, 무효화, Thundering Herd 방지)
  - message-queue.md: 메시지 큐 컨벤션 (CloudEvents 포맷, 전달 보증, 멱등성, DLQ, 재시도, 이벤트 버전 관리)
  - deployment.md: 배포 컨벤션 (환경 구분, Docker, CI/CD 파이프라인, 배포 전략, 헬스 체크, 롤백)
  - monitoring.md: 모니터링 컨벤션 (RED/USE 메서드, 메트릭 네이밍, 알림 규칙, 로그-메트릭-트레이스 연계)
- skill-upgrade: Step 6-0 SHA256 해시 비교 커스터마이징 감지 추가 (전체 프레임워크 파일 대상)
- skill-upgrade: Step 10-0 CUSTOM_SECTION 마커 존재 사전 확인 + 전체 백업 안전장치 추가
- skill-upgrade: Step 13-0 마커 자동 삽입 + 백업 커스텀 내용 복원 안전장치 추가

### Changed
- skill-upgrade: 해시 불일치 파일에 대해 덮어쓰기 전 사용자 확인 (소스 덮어쓰기/현재 유지/수동 머지)
- skill-upgrade: Step 7 미리보기에 사용자 수정 프레임워크 파일 목록 추가
- skill-docs: 공통 컨벤션 키워드 매핑에 4개 항목 추가 (캐시, 메시지큐, 배포, 모니터링)

## [1.17.0] - 2026-02-19

### Added
- project.schema.json: `buildCommands` 프로퍼티 추가 (build/test/lint 명령어 외부 설정)
- skill-onboard: 빌드 명령어 자동 감지 로직 (Step 1.6) + project.json 저장
- CLAUDE.md.tmpl: 루프 가드 규칙 추가 (skill-fix→skill-review-pr 최대 2회)

### Changed
- skill-hotfix: 워크트리 에러 메시지에 이유/대안 추가 (📌 이유 + 💡 대안)
- skill-rollback: 워크트리 에러 메시지에 이유/대안 추가 (📌 이유 + 💡 대안)
- skill-release: 워크트리 에러 메시지에 이유/대안 추가 + 실패 출력 포맷 표준화
- skill-plan: 승인 메시지를 "Y/N" → "Y/수정사항 입력"으로 변경 (부분 수정 지원)
- skill-plan: DB 설계 서브에이전트 호출 프로토콜 표준화 (timeout 60초, fallback, retry 0)
- skill-review-pr: 3종 리뷰 서브에이전트 호출 프로토콜 표준화 (timeout 60초, fallback, retry 0)
- skill-impl: docs/QA 서브에이전트 호출 프로토콜 표준화 (timeout 60초, fallback, retry 0)
- skill-impl: 빌드 명령어를 buildCommands 우선 참조 → techStack 폴백으로 변경
- skill-hotfix: 빌드 명령어를 buildCommands 우선 참조 → techStack 폴백으로 변경
- skill-rollback: 빌드 명령어를 buildCommands 우선 참조 → techStack 폴백으로 변경
- skill-release: 빌드 명령어를 buildCommands 우선 참조 → techStack 폴백으로 변경
- skill-fix: 빌드/테스트 명령어를 buildCommands 우선 참조 → techStack 폴백으로 변경
- skill-fix: 루프 가드 적용 (fix 횟수 기반 --auto-fix 재호출 제어)
- skill-onboard: 실패 출력 포맷 표준화 (❌ 실패 / 단계 / 에러 / 복구 방법)

## [1.16.0] - 2026-02-19

### Added
- skill-merge-pr: Intent 기반 원자적 다중 파일 업데이트 프로토콜 (세션 중단 복구)
- skill-backlog: 동적 lockTTL (lockedFiles 수 기반 1~3시간 자동 산정)
- backlog.schema.json: lockTTL 필드 추가 (3600~14400초)
- skill-status: 실행 로그 아카이브 로테이션 절차 구체화 (500건 초과 시 자동 정리, 30일 보관)

### Changed
- skill-merge-pr: Task 완료 처리에 intent 파일 기반 복구 메커니즘 추가 (5.0~5.7단계)
- skill-plan: 상태 업데이트에 lockTTL 산정 로직 추가 + Intent 복구 사전 점검 추가
- skill-impl: assignedAt 연장 시 lockTTL 동적 재산정 + Intent 복구 사전 점검 추가
- skill-status: lockTTL 표시를 동적 TTL로 변경 + --health에 orphan intent 감지 추가
- 서브에이전트 5개 지시문 대폭 확충 (317→855줄): 심각도 판정, 도메인별 검증, 설계 프레임워크
- agent-db-designer: CRITICAL/MAJOR/MINOR/INFO 심각도 판정 기준 + 출력 심각도 컬럼 추가
- agent-qa: P1/P2/P3 → CRITICAL/MAJOR/MINOR 심각도 매핑 테이블 추가 (pr-reviewer-test 연동)
- pr-reviewer-test: 심각도-우선순위 역방향 매핑 추가 (agent-qa 연동)
- pr-reviewer-security: general 도메인 보안 검토 항목 추가 (6항목)
- pr-reviewer-domain: general 도메인 중점 검토 항목 보강 (6항목)
- agent-pm: 컨텍스트 전달 프로토콜 표준화 (파일 명명 규칙, 생산자-소비자 매핑, 충돌 해소)
- docs-impact-analyzer, agent-qa, pr-reviewer-test: 에이전트 간 상호참조 관계 명시

## [1.15.0] - 2026-02-18

### Added
- skill-onboard: 기존 프로젝트 온보딩 (코드베이스 스캔 → 기술 스택 자동 감지 → 도메인 추천 → 설정 생성)
- skill-create: 커스텀 스킬 스캐폴딩 (SKILL.md 생성 + CLAUDE.md CUSTOM_SECTION 자동 등록)
- skill-estimate: 작업 복잡도 추정 (5팩터 분석 + completed.json 타임스탬프 기반 과거 데이터 보정)
- .claude/skills/custom/: 커스텀 스킬 디렉토리 (.gitkeep 포함)
- skill-validate: Category 8 커스텀 스킬 매니페스트 검증 추가

### Changed
- CLAUDE.md.tmpl: 신규 스킬 3개 등록 (명령어, 자연어 매핑 4건, 자동 체이닝 3건)
- skill-upgrade: Step 11에 커스텀 스킬 보존 로직 추가 (custom/ 백업 → 프레임워크 교체 → custom/ 복원)

## [1.14.1] - 2026-02-18

### Added
- skill-plan: MUST-EXECUTE-FIRST 블록 추가 (project.json/backlog.json 검증 + origin/develop 동기화)
- skill-status: --health에 backlog-completed 정합성 검증 추가
- backlog.schema.json: phases에 status 필드 추가 (todo/in_progress/done 자동 갱신)

### Changed
- skill-impl: MUST-EXECUTE-FIRST에 origin/develop 동기화 검증 추가 (5커밋 초과 차단, 1~4 자동 머지)
- skill-merge-pr: MUST-EXECUTE-FIRST에 origin/develop 동기화 검증 추가
- skill-merge-pr: Task 완료 처리 순서 변경 (completed.json 먼저 → backlog.json → 교차 검증 → Phase 갱신 → 단일 커밋)
- skill-merge-pr: backlog-completed 교차 검증 + 누락 자동 복구 로직 추가
- skill-merge-pr: Phase 상태 자동 갱신 로직 추가 (소속 Task 기준)

## [1.14.0] - 2026-02-18

### Added
- skill-retro: 완료 Task 회고 분석 + 체크리스트/컨벤션 학습 반영
- skill-hotfix: main 긴급 수정 + 보안 리뷰 + 패치 릴리스 + develop 백머지
- skill-rollback: git revert 기반 릴리스/PR 롤백 + 리버트 PR 감사 추적
- skill-report: 프로젝트 메트릭 리포트 (throughput, quality, code, health)
- hotfix.yaml: 긴급 핫픽스 워크플로우 정의

### Changed
- skill-merge-pr: Task 완료 시 회고 실행 안내 추가
- skill-status: 실행 로그 프로토콜에 신규 3개 스킬 항목 추가
- CLAUDE.md.tmpl: 신규 4개 스킬 명령어/자연어/워크플로우 매핑 추가
- backlog.schema.json: workflowState.currentSkill enum 확장
- git-workflow.md: 핫픽스/롤백 브랜치 절차 상세 추가

## [1.13.2] - 2026-02-17

### Fixed
- .gitignore에 `memory/` 디렉토리 추가

## [1.13.1] - 2026-02-17

### Fixed
- v1.12.0에서 누락된 `_base/conventions/` 공통 컨벤션 문서 7개 파일 커밋 추가

## [1.13.0] - 2026-02-17

### Added
- agent-db-designer: YAML frontmatter 기반 네이티브 subagent 전환 (분석 전용, Read/Glob/Grep)
- agent-qa: YAML frontmatter 기반 네이티브 subagent 전환 (분석 전용, Read/Glob/Grep)
- skill-plan: DB 설계 분석 병렬 Task 호출 (agents.enabled 조건부)
- skill-impl: QA 테스트 품질 분석 백그라운드 Task 호출 (agents.enabled 조건부)
- 워크플로우 상태 영속화: `workflowState` 필드로 크래시 후 재개 지원 (skill-impl, skill-review-pr, skill-fix, skill-merge-pr)
- backlog.json 동시 쓰기 보호: `metadata.version` 낙관적 동시성 제어 + JSON 유효성 검증 프로토콜
- 스킬 사전 조건 검증 표준화: `MUST-EXECUTE-FIRST` 블록 전 스킬 적용 (skill-impl, skill-review-pr, skill-fix, skill-release)
- 중앙화된 스킬 실행 로그: `.claude/state/execution-log.json` append-only 감사 추적
- skill-validate: 업그레이드 후 자체 검증 스킬 신규 생성 (7개 검증 카테고리)
- backlog.schema.json: backlog.json 데이터 모델 JSON Schema 정의
- General 도메인 보강: keywords 6개 + checklists 3개 + common-patterns.md 추가
- 멀티 스택 코드 템플릿: TypeScript 템플릿 7개 추가 (fintech 4개, ecommerce 3개) + 스택 기반 자동 선택
- skill-status 진단 강화: `--health` 옵션, 활성 PR 상태, 워크플로우 진행 상태, 시스템 건강 점검
- 의존성 취약점 검사: skill-impl 빌드 후 `npm audit` / `dependencyCheckAnalyze` / `govulncheck` 선택적 실행
- 트러블슈팅 가이드: `.claude/docs/troubleshooting.md` 8개 장애 시나리오별 진단/해결
- E-commerce 예제 프로젝트: `examples/ecommerce-shop/` (project.json, backlog.json, 요구사항 스펙)
- 커스텀 워크플로우 정의: `skill-domain add-workflow` 명령 추가

### Changed
- docs-impact-analyzer: 문서 영향도 분석 + 초안 제안까지 확장 (agent-docs 핵심 기능 통합)
- skill-plan: allowed-tools에 Task 추가
- agent-code-reviewer: YAML frontmatter 추가 (참조 문서로 명시), agent-qa 연동 정보 추가
- agent-db-designer: 상세 가이드(434줄) → 분석 핵심+출력 형식(76줄)으로 축약
- agent-qa: 상세 가이드(412줄) → 분석 핵심+출력 형식(71줄)으로 축약
- skill-upgrade: Step 15에서 skill-validate 자동 호출
- pr-reviewer-security: 의존성 취약점 리뷰 섹션 추가

### Removed
- project.schema.json, skill-init: 미구현 healthcare/saas 도메인 선택지 제거

## [1.12.0] - 2026-02-15

### Added
- 공통 개발 컨벤션 문서 7개 추가 (`_base/conventions/`):
  - api-design.md: API 설계 컨벤션 (URL 구조, 상태코드, 페이지네이션, 멱등성, Rate Limiting)
  - testing.md: 테스팅 컨벤션 (테스트 피라미드, 커버리지 목표, Mock 전략, 격리 원칙)
  - logging.md: 로깅 컨벤션 (구조화 로그, 레벨 기준, 민감정보 마스킹, 성능 로깅)
  - database.md: DB 설계 컨벤션 (네이밍, 인덱스, 마이그레이션, 무중단 변경, 낙관적 잠금)
  - error-handling.md: 에러 처리 컨벤션 (예외 계층, 재시도 전략, 서킷 브레이커)
  - security.md: 보안 개발 컨벤션 (JWT 인증, 입력 검증, CORS, Secret 관리)
  - project-structure.md: 프로젝트 구조 컨벤션 (레이어 아키텍처, 스택별 패키지 구조)
- skill-docs: 공통 컨벤션 키워드 매핑 섹션 추가 (도메인 무관 자동 참조)
- skill-docs: 문서 로딩 우선순위에 `_base/conventions/` 경로 추가
- skill-docs: 출력 포맷에 공통 컨벤션 섹션 추가

### Changed
- skill-feature: 기능 분석 시 공통 컨벤션 참조 경로 추가
- skill-impl: 참고자료 로드 순서에 공통 컨벤션 경로 추가
## [1.11.0] - 2026-02-12

### Added
- Claude Squad (git worktree) 옵셔널 통합: 모든 스킬에서 worktree 환경 자동 감지 및 대응
- project.schema.json: `orchestrator` 프로퍼티 추가 (`auto`/`claude-squad`/`none`)
- git-workflow.md: Worktree 모드 비교 테이블 문서 추가

### Changed
- CLAUDE.md.tmpl: 세션 시작 git 동기화에 worktree 분기 추가
- skill-impl: 환경 준비/커밋/푸시에 worktree 분기 추가 (CS 브랜치 직접 사용)
- skill-merge-pr: 머지 실행(`--delete-branch` 제거)/로컬 동기화/완료 푸시/충돌 안내에 worktree 대응 추가
- skill-plan: Git 동기화 프로토콜에 worktree 분기 추가
- skill-feature: 커밋/푸시에 worktree 분기 추가
- skill-release: worktree 환경 실행 차단 + 메인 레포 경로 안내

## [1.10.0] - 2026-02-12

### Changed
- PR body 템플릿 간소화: 자동화 프로세스와 중복되는 테스트/관련 문서/체크리스트 섹션 제거
- fintech PR 템플릿: 컴플라이언스 섹션만 유지, 나머지 중복 섹션 제거
- skill-impl: PR body 마커 6개→4개 축소 (TASK_ID, TEST_COVERAGE 제거)

## [1.9.0] - 2026-02-11

### Added
- 서브에이전트 frontmatter에 icon 필드 추가 (🔐 보안, 🏛️ 도메인, 🧪 테스트, 📝 문서분석)

### Changed
- skill-review-pr: Task 호출에 아이콘 description 추가, 결과 병합 테이블 아이콘 반영
- skill-impl: docs-impact-analyzer Task에 아이콘 description 추가

## [1.8.0] - 2026-02-11

### Changed
- skill-release Step 8: API 문서 도구 미감지 시 "스킵" → "자동 설치 후 재시도"로 변경 (Spring Boot/Node.js/Go 지원)
- skill-release Step 9: 자동 설치된 빌드 파일 변경분을 릴리스 커밋에 포함
- skill-init Step 7: API 문서 도구 수동 설정 안내 제거, 릴리스 시 자동 처리 안내로 교체

## [1.7.1] - 2026-02-08

### Changed
- skill-upgrade: kitSource 미설정 시 AskUserQuestion 대신 기본값(`https://github.com/wejsa/ai-crew-kit.git`) 사용
- skill-init: kitSource fallback을 사용자 질문에서 기본 URL로 변경

## [1.7.0] - 2026-02-08

### Added
- skill-upgrade: 프레임워크 업그레이드 스킬 신규 생성 (14단계 실행 플로우)
  - file-sync 기반 프레임워크 파일 선택적 업데이트
  - 도메인 커스텀 파일/항목 3단계 보존 (감지→추출→복원)
  - settings.json 커스텀 권한 머지 (합집합 + deny 보존)
  - CLAUDE.md/README.md 커스텀 섹션 보존 재생성
  - --dry-run, --rollback, --source, --version 옵션 지원
  - 잠금 파일, 진행 상태 파일, 자동 롤백 안전장치
- migrations.json: project.json 스키마 마이그레이션 매니페스트 추가
- project.schema.json: `kitVersion`, `kitSource` optional 필드 추가
- README.md.tmpl: CUSTOM_SECTION 마커 추가 (CLAUDE.md.tmpl과 동일 패턴)
- README.md: 프레임워크 업그레이드 섹션 추가 (부트스트랩 가이드 포함)

### Changed
- skill-init: Step 1에서 히스토리 리셋 전 ai-crew-kit origin URL 조건부 캡처
- skill-init: Step 6에서 project.json에 `kitVersion`, `kitSource` 필드 기록
- skill-status: 프로젝트 설정에 Kit 버전 표시 추가

## [1.6.0] - 2026-02-08

### Added
- skill-release: 빌드 & 테스트 검증 단계 추가 (Step 3, project.json 스택 기반)
- skill-release: API spec 스냅샷 단계 추가 (Step 8, springdoc/swagger-jsdoc/swag 자동 감지)
- skill-release: CHANGELOG 자동 수집 (git log + conventional commit 분류 + 사용자 확인)
- skill-init: 필수 의존성 설정 섹션 추가 (백엔드 스택별 API 문서 도구 안내)
- skill-init: docs/api-specs/ 디렉토리 초기 생성

### Changed
- skill-release: 실행 플로우 10단계 → 12단계 확장
- skill-release: Co-Authored-By "Opus 4.5" → "Opus 4.6" 업데이트
- skill-release: allowed-tools에 빌드 도구(./gradlew, npm, yarn, go, swag) 및 Glob 추가
- skill-release: 롤백 섹션에 부분 실패 대응 테이블 추가
- skill-init: Git 초기 커밋에 docs/ 디렉토리 포함

## [1.5.0] - 2026-02-07

### Added
- 3개 전용 리뷰 subagent 신규 생성 (YAML frontmatter 기반 네이티브 subagent)
  - pr-reviewer-security: 보안 + 컴플라이언스 (Read/Glob/Grep only)
  - pr-reviewer-domain: 도메인 + 아키텍처 (Read/Glob/Grep only)
  - pr-reviewer-test: 테스트 품질 (Read/Glob/Grep only)
- skill-review-pr: Task 실패 시 부분 결과 처리 및 오류 대응 규칙
- skill-impl: PR 생성 후 docs-impact-analyzer 백그라운드 Task 자동 실행
- docs-impact-analyzer subagent 신규 생성 (문서 영향도 분석 전용)

### Changed
- skill-review-pr: 순차 5관점 검토 → 3개 네이티브 subagent 병렬 호출로 변경
- skill-review-pr: 에이전트 활용 섹션 플레이스홀더 → 실제 subagent 연동으로 교체
- skill-impl: allowed-tools에 Task 추가
- agent-code-reviewer: mermaid 다이어그램 순차→병렬 흐름 반영

### Fixed
- Task subagent_type: 커스텀 에이전트명 → general-purpose + Read 로드 방식으로 수정
  - Task tool은 빌트인 타입(Bash, general-purpose, Explore 등)만 지원
  - 프롬프트에서 에이전트 파일을 Read로 로드하여 지침 적용하는 패턴으로 변경

## [1.4.0] - 2026-02-07

### Added
- PR body 템플릿 시스템 (pr-body.md.tmpl) + Layered Override 도메인 오버라이드
- fintech 도메인 PR 템플릿 (컴플라이언스 체크리스트 포함)
- skill-review-pr: 도메인 체크리스트 명시적 로딩 및 검토 결과 PR 코멘트 포함

### Changed
- skill-impl: PR body 하드코딩 → 템플릿 기반 동적 생성으로 변경
- skill-review-pr: 5관점 검토에 체크리스트 파일 대조 절차 구체화

## [1.3.0] - 2026-02-07

### Fixed
- skill-init: `git clone ai-crew-kit` 후 origin이 원본 저장소를 가리키는 문제 수정
  - Step 1 환경 검증에서 `git remote -v`로 origin 확인
  - ai-crew-kit origin 감지 시 `rm -rf .git && git init -b main`으로 히스토리 초기화

### Added
- skill-init: Git 초기 커밋 후 `develop` 브랜치 자동 생성
- skill-init: 완료 안내에 Git 원격 저장소 설정 가이드 추가

## [1.2.0] - 2026-02-07

### Added
- CLAUDE.md 템플릿: 세션 시작 시 continuation-plan.md 확인 단계 추가 (3단계→4단계)
- CLAUDE.md 템플릿: 컨텍스트 한계 관리 섹션 신규 추가 (70% 트리거, 연속 계획 파일, 복구 절차)

### Changed
- CLAUDE.md 템플릿: 스킬 자동 체이닝 규칙을 자동 연속 실행 규칙으로 교체 (테이블 형식 + 금지사항, 위치 이동)

## [1.1.3] - 2026-02-07

### Fixed
- skill-impl: `--all` 옵션 플로우에서 스텝 간 자동 진행이 중단되던 문제 수정
- skill-impl: `--all` 플로우 다이어그램의 "사용자 확인", "수동" 표현을 자동 체이닝으로 변경

### Added
- CLAUDE.md 템플릿: 스킬 자동 체이닝 규칙 섹션 추가 (자동 진행 원칙, 중단 조건)

## [1.1.2] - 2026-02-07

### Added
- skill-init: README.md 템플릿 기반 자동 생성 (프로젝트 전용 README)
- skill-init: VERSION 파일 초기화 (0.1.0) 자동 생성
- README.md.tmpl 템플릿 추가

### Changed
- skill-release: README.md 버전 업데이트 패턴을 project.json 기반 동적 처리로 변경
- skill-init: Git 초기 커밋 대상에 README.md, VERSION 포함

## [1.1.1] - 2026-02-05

### Changed
- README.md: 하드코딩된 버전 참조 제거 (제목만 버전 유지)
- CHANGELOG.md: [Unreleased] 섹션 추가로 skill-release 자동화 지원

## [1.1.0] - 2026-02-04

### Added
- skill-fix: CRITICAL 이슈 자동 수정 스킬 추가
- skill-release: 버전 관리 및 릴리스 자동화 스킬 추가
- 버전 관리 시스템 도입 (VERSION 파일 + CHANGELOG.md)

### Changed
- skill-review-pr: self-PR 감지 및 comment 기반 리뷰 로직 강화
- skill-merge-pr: self-PR 승인 조건 스킵 및 검증 로직 추가
- skill-impl/skill-plan: 워크플로우 체이닝 설정 정리
- .gitignore: auto-generated CLAUDE.md 제외 규칙 추가

### Fixed
- README 마크다운 취소선 렌더링 오류 수정 (`~` → `-`)

## [1.0.0] - 2026-02-03

### Added
- 초기 릴리스
- 12개 스킬: skill-feature, skill-plan, skill-impl, skill-review-pr, skill-fix, skill-merge-pr, skill-init, skill-docs, skill-hotfix, skill-rollback, skill-monitor, skill-report
- 6개 에이전트: backend, frontend, db-designer, devops, qa, docs
- 4개 도메인: general, ecommerce, fintech, _base
- 워크플로우 자동 연결 시스템
