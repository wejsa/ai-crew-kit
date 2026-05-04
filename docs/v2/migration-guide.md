# v1.x → v2.0.0 마이그레이션 가이드

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

### 1.2 Breaking Changes

- **`project.json` 스키마 확장** — 5개 신규 top-level 필드(`hooks`, `tokenHints`, `customDomain`, `healthCheck`, `orchestrator`) + `conventions` 2개 신규 키. 자동 마이그레이션 4건은 `migrations.json` SSOT 적용. 누락 3건(`customDomain`/`healthCheck`/`orchestrator`)은 schema default 통과 (Step 3 OQ-02에서 확정 예정).
- **`CLAUDE.md.tmpl` 구조 변경** — Phase 4 4층 Override 도입으로 마커 갱신. **`CUSTOM_SECTION_START`/`CUSTOM_SECTION_END` 마커 사이 콘텐츠는 자동 보존**.
- **`skill-health-check` 가중치 재배분** — Phase 5에서 hook-safety 부채 해소 + 도메인 `_category.json` 명시. 사용자 점수 영향 ≤1점 ([security-migration.md §5](./security-migration.md) 참조).

### 1.3 사용자 점수 영향

신규 위반 발견 시 외에는 **≤1점**. SEC-01 회귀 보존 + 신규 SEC-05/06/07 추가는 점수 영향 0이며, alpha.2 hook-safety 부채 해소만 healthcare phi-protection에서 -0.91% ≈ ~1.0점 (의도적 floor). 상세는 [security-migration.md §1](./security-migration.md).

> **CHANGELOG 정합 알림** — `CHANGELOG.md [2.0.0]`은 Phase 8 Step 4(미진행)에서 완성된다. 본 §1.2는 `migrations.json` SSOT + Phase 4·5 Added 섹션 기반이며, Step 4 머지 시 정합 fixup이 동시 commit될 수 있다 (D7 — migrations.json 우선).

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

v2.0.0 GA 시점 `examples/` 디렉토리는 **`fintech-gateway` / `ecommerce-shop`** 두 도메인만 제공한다. **`saas` / `healthcare` 도메인은 `tests/upgrade/fixtures/` 단위 fixture 검증만 완료** (Phase 8 Step 3 진행). 실제 example project는 v2.1+ 후속 범위.

---

## 4. 롤백 매뉴얼 절차

> ⚠️ **R6 1차 방어선** — `--rollback` 자동 동작은 구현되어 있으나 v1.x 시기 실사용 사례가 미상이다. 본 §은 *사용자가 매뉴얼로 검증 가능한 체크리스트*만 책임진다. 자동 시뮬레이션 검증은 Phase 8 Step 3 `tests/upgrade/test_rollback.py`에서 추가될 예정.

명령은 [docs/upgrade-guide.md §롤백](../upgrade-guide.md#롤백) 인용:

```bash
/skill-upgrade --rollback                # 가장 최근 백업 복원
/skill-upgrade --rollback <backup-path>  # 지정 백업 복원
```

### 사전 검증 체크리스트

- [ ] 백업 디렉토리 존재 — `ls .claude/temp/upgrade-backup-*/`
- [ ] 백업 tar 무결성 — `tar tzf .claude/temp/upgrade-backup-{ts}/backup.tar.gz | head` (오류 없이 목록 출력)
- [ ] 중요 상태 파일 별도 보관 권장 — `cp .claude/state/backlog.json /tmp/backlog-pre-rollback.json`

### 사후 검증 체크리스트

- [ ] 복원된 `project.json kitVersion`이 백업 시점 버전과 일치 (`grep kitVersion .claude/state/project.json`)
- [ ] `CLAUDE.md`의 `CUSTOM_SECTION_START` 사이 내용이 사전 보관본과 동일
- [ ] `backlog.json metadata.version` 회귀 — Task 상태(in_progress/completed) 변경 없음

### 백업 보존 정책

- 백업은 `.claude/temp/upgrade-backup-*/` 누적 보관 (자동 정리 없음)
- 디스크 부담 시 사용자가 수동 삭제 — 마이그레이션 7일 이상 안정 동작 확인 후 권장
- `--rollback` 실행 직후 백업은 보존 (재롤백 시도 가능)

---

## 5. FAQ

### Q1. 업그레이드 후 `project.json` 검증 실패가 발생합니다.

`migrations.json` v2.0.0의 4 add_field는 자동 적용되지만, **누락된 v2 신규 필드**(`customDomain` / `healthCheck` / `orchestrator`)는 schema default로 통과하지 않을 수 있다 (Phase 8 Step 3 OQ-02에서 보강 검토). 임시 수동 보강:

```jsonc
{ "customDomain": null, "healthCheck": {}, "orchestrator": {} }
```

문제 지속 시 `--rollback` 후 [GitHub Issues](https://github.com/wejsa/ai-crew-kit/issues)에 `project.json` 첨부 (시크릿 마스킹 후).

### Q2. `CLAUDE.md`의 커스텀 규칙이 사라졌습니다.

`CUSTOM_SECTION_START`/`CUSTOM_SECTION_END` **마커가 누락된 v1.x 초기 프로젝트**일 가능성이 높다. skill-upgrade는 마커 부재 시 (1) 전체 파일 백업 + (2) 템플릿 diff로 커스텀 추출을 시도하지만 실패할 수 있다.

복구 절차: §4 사전 체크리스트로 백업 무결성 확인 → `tar xzf .claude/temp/upgrade-backup-{ts}/backup.tar.gz CLAUDE.md` → 마커 사이로 콘텐츠 이동 → 재실행. 재발 방지를 위해 마커를 명시 배치한다.

### Q3. Phase 1 훅이 작동하지 않습니다.

가장 흔한 원인은 **스크립트 실행 권한 누락**이다 (PR #34 사례 — alpha.2~alpha.3에서 5개 훅이 git index 모드 100644로 박혔다, [security-migration.md §1](./security-migration.md)). 점검:

```bash
ls -l .claude/hooks/*.sh                      # 모두 -rwxr-xr-x 인지 확인
chmod +x .claude/hooks/*.sh                   # 누락 시 일괄 부여
grep -A2 hooks .claude/settings.json          # settings.json hooks 등록 확인
```

훅 비활성화 자동 플래그(`.claude/state/hook-disabled.flag`) 존재 시 무한 루프 방어 작동 중일 수 있다 — 플래그 파일 점검 후 삭제.

### Q4. `skillProfile` 변경 후 `CLAUDE.md`가 갱신되지 않습니다.

`skillProfile`은 `project.json` 변경만으로 `CLAUDE.md`가 자동 재생성되지 않는다. 강제 재생성:

```bash
/skill-upgrade --dry-run                      # 차이 확인
/skill-upgrade --version v2.0.0               # 동일 버전 재실행 시에도 13단계로 재생성
```

대안: `/skill-init` 재실행 (CUSTOM_SECTION 보존 동일).

### Q5. v1.x 핫픽스(서브에이전트 worktree 격리 등)와 v2가 충돌합니다.

v2.0.0 GA 후 `develop` 브랜치는 **v1.x 핫픽스 라인으로 동결**된다 (phase-8-plan.md D2). v2 신규 작업은 `v2-develop`에서 분기. 양방향 머지(main↔develop 핫픽스)는 유지된다. 충돌 흡수 방식은 phase-8-plan.md OQ-06 결정 후 Step 6 진입 시점에 Notion 릴리스 노트(메모리 §외부 참조)에 게시된다.

---

## 6. 참고 링크

- [docs/v2/phase-8-plan.md](./phase-8-plan.md) — Phase 8 결정 SSOT (9 D + 7 OQ + 6 R)
- [docs/v2/security-migration.md](./security-migration.md) — Phase 5 보안 마이그레이션 (SEC-05/06/07 상세)
- [docs/upgrade-guide.md](../upgrade-guide.md) — `/skill-upgrade` 명령·옵션·보존 항목 SSOT
- [.claude/schemas/migrations.json](../../.claude/schemas/migrations.json) — 마이그레이션 SSOT (D7 — phase-8-release.md doc과 불일치 시 본 파일 우선)
- [.claude/skills/skill-upgrade/SKILL.md](../../.claude/skills/skill-upgrade/SKILL.md) — skill 동작 SSOT
- `CHANGELOG.md [2.0.0]` — Step 4 완성 후 정합
- ~~[docs/v2/phase-6-compliance.md](./phase-6-compliance.md)~~ — v2.1+ 보류 (ADJ-01)
