# v1.x → v2.0.0 마이그레이션 가이드

> ⚠️ **명령어 변경 안내(역사 문서)**: 이 문서의 `/skill-*` 명령(예: `/skill-upgrade`)은 **v2 시기 표기**입니다. 이후 스킬 프리픽스가 두 번 바뀌었습니다 — v4.0.0 `/skill-*` → `/crew-*`, v4.6.0 `/crew-*` → `/aick-*`(현재). 현재 명령·옵션은 [docs/upgrade-guide.md](../upgrade-guide.md)를 SSOT로 따르세요. 본 문서는 v1→v2 변경 컨텍스트의 역사 기록으로 보존됩니다.

> **대상 사용자**: v1.x ai-crew-kit으로 초기화된 기존 프로젝트를 v2.0.0 GA로 업그레이드하는 사용자
> **상위 계획**: [phase-8-plan.md](./phase-8-plan.md) — 옵션 A Lean Closure (Step 1~6)
> **선행 머지**: PR #45 (Phase 8 Step 1 — plan + skill-upgrade SKILL.md 갭 fix)
> **명령 SSOT**: [docs/upgrade-guide.md](../upgrade-guide.md) — `/skill-upgrade` 옵션·보존 항목 표 단일 진실
> **본 문서 범위**: v1→v2 *변경 컨텍스트*·*매뉴얼 검증*·*FAQ*. 명령 블록은 `upgrade-guide.md`를 인용한다.

---

## 1. 변경 사항 요약

### 1.1 At a Glance

| 변경 | 출처 | 사용자 영향 |
|------|------|-------------|
| `project.json hooks` 추가 (default `{}`) | `migrations.json` v2.0.0 | 자동 — Phase 1 훅 미사용 시 빈 객체 유지 |
| `project.json conventions.skillProfile` 추가 (default `"default"`) | `migrations.json` v2.0.0 | 자동 — `default`는 전체(full)와 동일. `developer` / `docs-only` / `custom` 선택 가능 |
| `project.json conventions.overridePriority` 추가 (default `"domain-first"`) | `migrations.json` v2.0.0 | 자동 — Phase 4 4층 Override 기본 정책 |
| `project.json tokenHints` 추가 (default `{}`) | `migrations.json` v2.0.0 | 자동 — 프로젝트별 complexity-hint 오버라이드는 선택 |
| `.claude/rules/` 디렉토리 (도메인×언어 제약 메커니즘, 0-content 출시) | Phase 4 | 메커니즘만 추가. 콘텐츠는 사용자 실수요 발생 시 직접 추가([rules/README.md](../../.claude/rules/README.md) 참조) |
| `secrets-patterns` + skill-health-check SEC-05/06/07 | Phase 5 | 신규 검사. 위반 시 CRITICAL FAIL — 상세는 [security-migration.md](./security-migration.md) |
| `lessons-learned.json` 회귀 보호 (schema + validator + pytest fixture) | Phase 7 | 자동 — `.claude/state/*` 디렉토리 전체 보존 (skill-upgrade 보존 대상 표 명시) |
| ~~`skill-compliance-report`~~ | (보류) | Phase 6 옵션 D 채택(2026-05-01). v2.1+ 재진입 시 검토 |

### 1.2 주요 변경 사항 (대부분 자동 적용)

- **`project.json` 스키마 확장** — 5개 신규 top-level 필드(`hooks`, `tokenHints`, `customDomain`, `healthCheck`, `orchestrator`) + `conventions` 2개 신규 키. 자동 마이그레이션 4건은 `migrations.json` SSOT 적용. 누락 3건(`customDomain`/`healthCheck`/`orchestrator`)은 schema optional이라 부재 통과 (Phase 8 Step 3 fixture 검증 결과 — `migrations.json` 추가 보강 불요).
- **`CLAUDE.md.tmpl` 구조 변경** — Phase 4 4층 Override 도입으로 템플릿 본문 갱신. `CUSTOM_SECTION_START`/`CUSTOM_SECTION_END` 마커는 v1.x와 동일하며, **마커 사이 콘텐츠는 자동 보존**된다.
- **`skill-health-check` 가중치 재배분** — Phase 5에서 hook-safety 부채 해소 + 도메인 `_category.json` 명시. 사용자 점수 영향 ≤1점 ([security-migration.md §5](./security-migration.md) 참조).
- **마이그레이션 비용** — semver major bump(v1→v2)이지만 사용자 *수동 작업이 필요한 변경*은 거의 없다 (모두 자동 마이그레이션 또는 default 통과).

### 1.3 사용자 점수 영향

신규 위반 발견 시 외에는 **≤1점**. SEC-01 회귀 보존 + 신규 SEC-05/06/07 추가는 점수 영향 0이며, alpha.2 hook-safety 부채 해소만 healthcare phi-protection에서 -0.91% ≈ ~1.0점 (의도적 floor). 상세는 [security-migration.md §1](./security-migration.md).

> **CHANGELOG 정합** — `CHANGELOG.md [2.0.0]` Breaking Changes 섹션이 본 §1.2와 동일 SSOT(`migrations.json` v2.0.0). Phase 8 Step 4 머지로 정합 완료.

---

## 2. 자동 마이그레이션 절차

명령은 [docs/upgrade-guide.md](../upgrade-guide.md)에서 단일 진실로 관리된다. v2.0.0 한정 권장 흐름:

```bash
/skill-upgrade --dry-run                       # 1) 변경 미리보기 (필수)
/skill-upgrade --version v2.0.0                # 2) 본 업그레이드
```

`/skill-upgrade --version v2.0.0` 실행 시 사용자 관점 4단계:

1. **백업 생성** — `.claude/temp/upgrade-backup-{YYYYMMDD-HHmmss}/backup.tar.gz` (`tar tzf` 무결성 검증 자동)
2. **프레임워크 파일 교체** — `.claude/agents/`, `skills/`, `domains/`, `rules/`(신규), `templates/`, `schemas/`, `workflows/`, `docs/` 디렉토리 단위 갱신. 커스텀 스킬(`skills/custom/`) 자동 분리 보존
3. **`project.json` 자동 마이그레이션** — `migrations.json` v2.0.0의 4 add_field 적용 + `kitVersion` v2.0.0 갱신
4. **`CLAUDE.md`/`README.md` 재생성** — 새 템플릿에 결정적 치환 + `CUSTOM_SECTION_START` 마커 사이 콘텐츠 복원

실행 후 다음 출력을 확인한다:

- `🆕 신규 기능 안내` 블록 (`migrations.json features` v2.0.0 — skillProfile / complexity-hint, **§3에서 권장 설정**)
- `✅ 검증 통과` (`skill-validate` 자동 호출)
- `백업 위치: .claude/temp/upgrade-backup-{ts}/` + `롤백 명령: /skill-upgrade --rollback`

### `--dry-run` 출력 체크포인트

`/skill-upgrade --dry-run` 결과에서 다음 4항을 확인한다 (사용자 결정 근거):

- **버전 전환**: `v{current} → v{new}` 라인이 의도한 대상 버전인가
- **보존 커스터마이징 요약**: 도메인 커스텀 파일·`domain.json` 커스텀 항목·settings.json 권한 모두 감지됐는가
- **해시 불일치 파일 목록**: 사용자가 직접 수정한 프레임워크 파일이 빠짐없이 표시되는가 (덮어쓰기 / 유지 / 수동 머지 결정 필요)
- **스키마 마이그레이션 항목**: `migrations.json` v2.0.0의 4 add_field가 적용 대상으로 표시되는가

부분 실패(특정 파일 충돌·해시 불일치 다수) 발견 시 **dry-run 단계에서 중단**하고 §5 FAQ Q1·Q2 절차로 사전 해결한 후 본 업그레이드를 실행한다.

문제 발생 시 §4 롤백 매뉴얼 절차 참조.

---

## 3. 수동 확인 사항

업그레이드 직후 다음 5항목을 점검한다 (모두 선택 — 기본값 유지 시 동작 회귀 0).

| 항목 | 위치 | 권장 |
|------|------|------|
| `conventions.skillProfile` | `project.json` | `default`(=full) 유지가 안전. 토큰 절감이 필요하면 `developer` / `docs-only` / `custom` 중 선택 |
| `conventions.overridePriority` | `project.json` | `domain-first` 기본 (Phase 4 4층 Override). 단독 베이스 우선이 필요하면 `base-first` |
| `hooks` 활성화 | `.claude/settings.json` `hooks` | Phase 1 훅 미사용 시 빈 객체 유지. 활성화 시 [phase-1-hooks.md](./phase-1-hooks.md) 참조 + **§FAQ Q3**(스크립트 실행 권한) |
| `tokenHints` 오버라이드 | `project.json` `tokenHints` | 선택 — 프로젝트별 complexity-hint 조정. 기본값 유지 권장 |
| `.claude/rules/{domain}/{language}/` 콘텐츠 | rules dir | **기본 0개**. 도메인×언어 제약 발생 시 [rules/README.md](../../.claude/rules/README.md) 가이드라인 따라 추가 |

### 도메인 examples 안내

v2.0.0 GA 시점 `examples/` 디렉토리는 **`fintech-gateway` / `ecommerce-shop`** 두 도메인만 제공한다. **`saas` / `healthcare` 도메인은 `tests/upgrade/fixtures/` 단위 fixture 검증만 완료** (Phase 8 Step 3에서 진행 예정). 실제 example project는 v2.1+ 후속 범위.

---

## 4. 롤백 매뉴얼 절차

> ⚠️ **R6 1차 방어선** — `--rollback` 자동 동작은 구현되어 있으나 v1.x 시기 실사용 사례가 미상이다. 본 §은 *사용자가 매뉴얼로 검증 가능한 체크리스트*만 책임진다. 자동 시뮬레이션 검증은 Phase 8 Step 3 `tests/upgrade/test_rollback.py`에서 추가될 예정.

명령은 [docs/upgrade-guide.md §롤백](../upgrade-guide.md#롤백) 인용:

```bash
/skill-upgrade --rollback                # 가장 최근 백업 복원
/skill-upgrade --rollback <backup-path>  # 지정 백업 복원
```

### 사전 검증 체크리스트

- [ ] 백업 디렉토리 존재 — `ls .claude/temp/upgrade-backup-*/` (`{ts}`는 `YYYYMMDD-HHmmss` 형식 자리)
- [ ] 백업 tar 무결성 — `tar tzf .claude/temp/upgrade-backup-*/backup.tar.gz >/dev/null && echo OK` (종료 코드 0 + `OK` 출력 확인. `tar tzf`는 *목록 출력*이라 별도 종료 코드 검사 필요)
- [ ] 백업 무결성 해시 별도 보관 — `sha256sum .claude/temp/upgrade-backup-*/backup.tar.gz > /tmp/backup-sha.txt` (사후 변조 검증용)
- [ ] 중요 상태 파일 별도 보관 권장 — `cp .claude/state/backlog.json /tmp/backlog-pre-rollback.json`

### 사후 검증 체크리스트

- [ ] 복원된 `project.json kitVersion`이 백업 시점 버전과 일치 — `grep kitVersion .claude/state/project.json`
- [ ] `CLAUDE.md`의 `CUSTOM_SECTION_START` 사이 내용이 사전 보관본과 동일 — `diff <(sed -n '/CUSTOM_SECTION_START/,/CUSTOM_SECTION_END/p' /tmp/CLAUDE.md.bak) <(sed -n '/CUSTOM_SECTION_START/,/CUSTOM_SECTION_END/p' CLAUDE.md)`
- [ ] `backlog.json` Task 상태 회귀 — `diff <(jq .tasks /tmp/backlog-pre-rollback.json) <(jq .tasks .claude/state/backlog.json)` (출력 없으면 동일)

### 백업 보존 정책

- 백업은 `.claude/temp/upgrade-backup-*/` 누적 보관 (자동 정리 없음)
- 멀티유저 환경: `chmod 700 .claude/temp/` 권장 (다른 OS 사용자에게 평문 백업 노출 방지)
- `.gitignore`에 `.claude/temp/` 포함 여부 확인 — v1.6.0+는 자동 포함되나 사용자 커스텀 시 누락 가능 (커밋 사고 방지)
- 디스크 부담 시 사용자가 수동 삭제 — 마이그레이션 7일 이상 안정 동작 확인 후 권장
- `--rollback` 실행 직후 백업은 보존 (재롤백 시도 가능)

---

## 5. FAQ

### Q1. 업그레이드 후 `project.json` 검증 실패가 발생합니다.

`migrations.json` v2.0.0의 4 add_field는 자동 적용되지만, **누락된 v2 신규 필드**(`customDomain` / `healthCheck` / `orchestrator`)는 schema default로 통과하지 않을 수 있다 (Phase 8 Step 3 OQ-02에서 보강 검토).

> ⚠️ **임시 우회 주의** — 아래 보강은 OQ-02 확정 전까지의 *우회*다. 다음 패치 릴리스에서 default 값이 확정되면 본 보강은 자동 마이그레이션 대상으로 흡수된다. 빈 객체 보강 시 향후 schema가 required 키를 추가할 경우 silent behavior change 가능. **commit 메시지에 `migration-guide Q1 workaround` 표기 권장** (추후 추적용).

```jsonc
// OQ-02 확정 전 임시 보강
{ "customDomain": null, "healthCheck": {}, "orchestrator": {} }
```

보강 후 `/skill-validate`(또는 `/skill-health-check`)로 통과 재확인. 통과하지 않을 때 즉시 `--rollback` 실행 금지 — §4 R6 박스의 *"자동 동작 검증 미상"* 경고 적용. 안전 절차:

1. **§4 사전 검증 체크리스트 완료** (백업 무결성 + sha256 + 상태 파일 보관)
2. `/skill-upgrade --rollback` 실행
3. **§4 사후 검증 체크리스트로 복원 정합 확인** (`kitVersion` / `CUSTOM_SECTION` / backlog Task)
4. 그래도 실패 시 [GitHub Issues](https://github.com/wejsa/ai-crew-kit/issues)에 `project.json` 첨부 (외부 공유 전 토큰·이메일·외부 시스템 ID 마스킹)

### Q2. `CLAUDE.md`의 커스텀 규칙이 사라졌습니다.

`CUSTOM_SECTION_START`/`CUSTOM_SECTION_END` **마커가 누락된 v1.x 초기 프로젝트**일 가능성이 높다. skill-upgrade는 마커 부재 시 (1) 전체 파일 백업 + (2) 템플릿 diff로 커스텀 추출을 시도하지만 실패할 수 있다.

복구 절차: §4 사전 체크리스트로 백업 무결성 확인 → `tar xzf .claude/temp/upgrade-backup-*/backup.tar.gz CLAUDE.md` → 마커 사이로 콘텐츠 이동 → 재실행. **추출된 CLAUDE.md를 외부 채널로 공유하기 전 토큰·이메일·외부 시스템 ID 마스킹 필수** (Q1과 동일 정책). 재발 방지를 위해 마커를 명시 배치한다.

### Q3. Phase 1 훅이 작동하지 않습니다.

가장 흔한 원인은 **스크립트 실행 권한 누락**이다 (PR #34 사례 — alpha.2~alpha.3에서 `post-tool-use.sh` 런타임 훅이 git index 모드 100644로 박혔다, [security-migration.md §1](./security-migration.md)). 점검·권한 부여:

```bash
# 1) 미실행 훅 식별 (디렉토리 내 untrusted/임시 .sh 부재 사전 확인)
ls -l .claude/hooks/                                                          # 의도하지 않은 .sh 부재 확인
find .claude/hooks -maxdepth 1 -name "*.sh" ! -perm -u+x                      # 실행 권한 없는 훅 목록

# 2) v2.0.0 Claude Code 런타임 훅 3건 명시 부여 (PR #34 회귀 케이스 해소)
chmod +x .claude/hooks/{post-tool-use,session-start,stop}.sh

# 3) settings.json 등록 확인 (PostToolUse / SessionStart / Stop 매핑)
grep -A3 hooks .claude/settings.json
```

> Claude Code 훅 3건(`post-tool-use.sh` / `session-start.sh` / `stop.sh`)은 `.claude/hooks/`에, git hooks(`pre-commit` 등)는 `.git/hooks/`에 별도 존재한다. `lib/`(유틸)·`tests/`는 직접 실행 대상 아님. 와일드카드(`chmod +x .claude/hooks/*.sh`)는 third-party·임시 백업본까지 실행 가능 상태로 만들어 supply-chain 관점에서 **위 명시 부여 패턴 권장**.

훅 비활성화 자동 플래그가 존재할 수 있다 — 위치 무관 탐색: `find .claude -name 'hook-disabled*'`. 플래그가 발견되면 (1) `.claude/state/hook-error.log`로 무한 루프 원인 확인 → (2) 원인(예: post-commit이 새 commit 트리거) 해결 → (3) `rm <플래그-경로>`. **원인 미해결 상태 삭제 금지** — 재발 시 시스템 부하 / lock contention 위험.

### Q4. `skillProfile` 변경 후 `CLAUDE.md`가 갱신되지 않습니다.

`skillProfile`은 `project.json` 변경만으로 `CLAUDE.md`가 자동 재생성되지 않는다. 강제 재생성:

```bash
/skill-upgrade --dry-run                      # 차이 확인
/skill-upgrade --version v2.0.0               # 동일 버전 재실행 시에도 CLAUDE.md/README.md 재생성 단계 진입
```

skill-upgrade가 동일 버전 재실행 시에도 결정적 치환 단계를 거치므로 `skillProfile` 반영이 강제된다 (skill-upgrade SKILL.md `Step 13 — CLAUDE.md/README.md 재생성` 참조).

### Q5. v1.x 핫픽스(서브에이전트 worktree 격리 등)와 v2가 충돌합니다.

v2.0.0 GA 후 `develop` 브랜치는 **v1.x 핫픽스 라인으로 동결**된다 (phase-8-plan.md D2). v2 신규 작업은 `v2-develop`에서 분기. 양방향 머지(main↔develop 핫픽스)는 유지된다. 충돌 흡수 방식은 [phase-8-plan.md OQ-06](./phase-8-plan.md#open-questions-step-26-진행-시-답해야-함)의 결정에 따라 **Step 6 머지 PR 본문**(공개 1차 채널)에 명시되며, 내부 Notion 릴리스 노트(메모리 §외부 참조)는 보조 채널로 동기화된다.

---

## 6. 참고 링크

- [docs/v2/phase-8-plan.md](./phase-8-plan.md) — Phase 8 결정 SSOT (9 D + 7 OQ + 6 R)
- [docs/v2/security-migration.md](./security-migration.md) — Phase 5 보안 마이그레이션 (SEC-05/06/07 상세)
- [docs/upgrade-guide.md](../upgrade-guide.md) — `/skill-upgrade` 명령·옵션·보존 항목 SSOT (본 PR 머지 시점 v1.7.0 예제 인용. **Phase 8 Step 5에서 v2.0.0 갱신 예정** — Step 5 머지 전까지 v1↔v2 명령 형식 호환이라 사용에는 문제 없음)
- [.claude/schemas/migrations.json](../../.claude/schemas/migrations.json) — 마이그레이션 SSOT (D7 — phase-8-release.md doc과 불일치 시 본 파일 우선)
- [.claude/skills/skill-upgrade/SKILL.md](../../.claude/skills/skill-upgrade/SKILL.md) — skill 동작 SSOT
- `CHANGELOG.md [2.0.0]` — Step 4 완성 후 정합
- ~~[docs/v2/phase-6-compliance.md](./phase-6-compliance.md)~~ — v2.1+ 보류 (ADJ-01)
