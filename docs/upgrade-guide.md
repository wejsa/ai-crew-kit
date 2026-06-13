# 프레임워크 업그레이드

> [← README로 돌아가기](../README.md)

AI Crew Kit이 업데이트되면, 기존 프로젝트에서 프레임워크 파일만 선택적으로 업그레이드할 수 있습니다.
프로젝트 코드, 상태 파일(backlog, project.json, lessons-learned), 커스텀 설정은 보존됩니다.

## 설치 방식별 차이 (v4.8.0+)

`/aick-upgrade`는 설치 모드를 자동 판별해 다르게 동작합니다:

| 모드 | 프레임워크 파일 (skills·agents·hooks·templates) | 프로젝트-로컬 (gitignore·kitVersion·CLAUDE.md) |
|------|------|------|
| **클론/시드** | 본 스킬이 교체 (아래 본문 전체 적용) | 본 스킬이 적용 |
| **플러그인** | `/plugin marketplace update`가 교체 (본 스킬 무관여) | **본 스킬이 적용** — 마이그레이션·kitVersion·CLAUDE.md 재생성만 수행, 로컬 프레임워크 디렉토리는 생성하지 않음 |

플러그인 사용자: 아래 본문의 파일 교체·settings 머지·커스터마이징 복원 단계는 해당되지 않습니다. 권장 절차 = `/plugin marketplace update` → 프로젝트에서 `/aick-upgrade` 1회.

## 업그레이드 실행

> ⚠️ **구버전 시드에서 처음 올리는 경우** 아래 `/aick-upgrade` 명령이 아직 프로젝트에 없을 수 있습니다 (v4.0~4.5 시드는 `/crew-upgrade`, v3.x 시드는 `/skill-upgrade`만 존재). 본인 프로젝트에 있는 구 업그레이드 명령으로 아래 **프리픽스 마이그레이션** 섹션을 따라 한 번 올린 뒤, 이후부터 아래 명령을 사용하세요.

```bash
# 변경 사항 미리보기 (실제 변경 없음 — 권장 첫 단계)
/aick-upgrade --dry-run

# 최신 버전으로 업그레이드
/aick-upgrade

# 특정 버전으로 업그레이드 (예: v2.0.0 GA)
/aick-upgrade --version v2.0.0

# 소스 지정 (기본값은 project.json의 kitSource)
/aick-upgrade --source https://github.com/wejsa/ai-crew-kit.git
```

## v4.7.x → v4.8.0 마이그레이션 (에이전트 7종 재편 + 게이트 신호 A2)

수동 작업 0건 — 업그레이드가 자동 처리합니다.

- **에이전트 12종 → 7종**: 미배선 장식 에이전트 5종(pm·planner·backend·frontend·docs)이 제거됩니다. **동작 변화 없음**(어떤 스킬도 호출하지 않던 에이전트). `.claude/agents/` 통째 교체로 자동 전파되며, 기존 `project.json`의 `agents.enabled`에 구 이름이 남아 있어도 검증은 통과하고(`schema` legacy 수용) `/aick-health-check`(SI-05)가 MINOR로 정리를 안내합니다.
- **머지 게이트 신호 A2**: 핫픽스·ad-hoc 리뷰 PR도 게이트가 차단합니다. `.gitignore`에 `.claude/state/review-decisions.json*` 엔트리가 자동 추가됩니다(글롭 — atomic-write tmp 잔재 포함. `migrations.json` `add_gitignore_entry` — 로컬 전용 transient 상태).
- **플러그인 사용자도 1회 실행 필요**: 위 gitignore 엔트리 등 프로젝트-로컬 마이그레이션은 `/plugin update`로 도달하지 않습니다 — 플러그인 갱신 후 프로젝트에서 `/aick-upgrade`를 1회 실행하세요(플러그인 모드 자동 감지, 파일 교체 없음).

## v1.x → v2.0 마이그레이션

v1.x 사용자는 `/aick-upgrade --version v2.0.0` 한 번이면 충분합니다 — `migrations.json` v2.0.0의 4 add_field(`hooks` / `conventions.skillProfile` / `conventions.overridePriority` / `tokenHints`)가 자동 적용됩니다.

| 항목 | 자동 처리 |
|------|----------|
| `project.json` 스키마 확장 | ✅ 4 add_field 자동 마이그레이션 |
| `CLAUDE.md` Override 템플릿 갱신 | ✅ 결정적 치환 + `CUSTOM_SECTION` 보존 |
| `.claude/state/lessons-learned.json` 회귀 보호 | ✅ 기존 데이터 100% 보존, schema 검증 활성 |
| 가중치 재배분 (Phase 1 hook-safety + Phase 5) | ✅ 자동 — 사용자 점수 영향 ≤1점 |

**점수 영향 ≤1점, 수동 작업 0건.** 상세 변경 사항·FAQ·롤백 매뉴얼은 [v1.x → v2.0.0 마이그레이션 가이드](./v2/migration-guide.md)를 참조하세요.

## v4.5.x → v4.6.0 마이그레이션 (스킬 프리픽스 crew-* → aick-*)

v4.6.0에서 22개 빌트인 스킬의 호출 명령어가 `/crew-*` → `/aick-*`로 바뀌었습니다 (예: `/crew-impl` → `/aick-impl`). **기존 v4.0~4.5 시드 프로젝트에는 아직 `/crew-upgrade` 스킬이 있으므로, 첫 업그레이드는 본인 프로젝트에 있는 구 명령으로 실행합니다:**

```bash
# 1. 기존 프로젝트의 구 명령으로 v4.6.0 업그레이드 (이 명령이 스스로를 aick-upgrade로 교체)
/crew-upgrade --version v4.6.0

# 2. 이후부터는 새 명령 사용
/aick-upgrade
```

업그레이드가 자동 처리하는 것:

| 항목 | 자동 처리 |
|------|----------|
| 빌트인 스킬 디렉토리 교체 | ✅ `.claude/skills/` 통째 교체 — 구 `crew-*` 22개 디렉토리(구 `crew-upgrade` 포함) 자연 제거, 새 `aick-*` 설치 |
| 커스텀 스킬 보존 | ✅ `.claude/skills/custom/`은 별도 백업·복원 (이름 변경 없음 — `crew-`/`skill-` 접두사 커스텀 스킬도 그대로 유지) |
| CLAUDE.md 스킬 레지스트리 | ✅ 결정적 재생성으로 `/aick-*` 반영 + `CUSTOM_SECTION` 보존 |
| customSkills 검증 | ✅ 스키마가 `aick-`/`crew-`/`skill-` 셋 다 허용 — 기존 커스텀 스킬 검증 실패 없음 |

> ⚠️ **수동 정리 필요**: 본인이 작성한 스크립트·alias·문서·`CLAUDE.md`의 `CUSTOM_SECTION` 안에 `/crew-impl` 같은 구 명령이 박혀 있으면 `/aick-*`로 직접 바꿔야 합니다 (프레임워크는 사용자 콘텐츠를 건드리지 않습니다).

> ℹ️ **1회성 거친 모서리(정상)**: 이 한 번의 업그레이드는 **구 `crew-upgrade`가 실행**하는데, 그 마지막 검증 단계가 리네임된 `aick-validate`를 호출하므로 "스킬 없음" 경고가 뜨거나 건너뛸 수 있습니다. 업그레이드 자체(스킬 교체·CLAUDE.md 재생성)는 정상 완료되며, **업그레이드 후 `/aick-validate`를 한 번 직접 실행**해 검증을 마치면 됩니다. v4.6 이후 업그레이드부터는 이 모서리가 사라집니다(`aick-upgrade`가 `aick-validate`를 호출).

## v3.x → v4.0.0 마이그레이션 (스킬 프리픽스 skill-* → crew-*, 역사)

v4.0.0에서 22개 빌트인 스킬의 호출 명령어가 `/skill-*` → `/crew-*`로 바뀌었습니다 (예: `/skill-impl` → `/crew-impl`). **기존 v3.x 시드 프로젝트에는 아직 구 `skill-upgrade` 스킬만 있으므로, 첫 업그레이드는 본인 프로젝트에 있는 구 명령으로 실행합니다:**

```bash
# 1. 기존 프로젝트에 있는 구 명령으로 v4.0.0 업그레이드 (이 명령이 스스로를 crew-upgrade로 교체)
/skill-upgrade --version v4.0.0

# 2. 이후 v4.6.0(aick-*)까지 마저 올림 — 위 'v4.5.x → v4.6.0' 섹션 참조
/crew-upgrade --version v4.6.0
```

업그레이드가 자동 처리하는 것:

| 항목 | 자동 처리 |
|------|----------|
| 빌트인 스킬 디렉토리 교체 | ✅ `.claude/skills/` 통째 교체 — 구 `skill-*` 22개 디렉토리(구 `skill-upgrade` 포함) 자연 제거, 새 `crew-*` 설치 |
| 커스텀 스킬 보존 | ✅ `.claude/skills/custom/`은 별도 백업·복원 (이름 변경 없음 — skill- 접두사 커스텀 스킬도 그대로 유지) |
| CLAUDE.md 스킬 레지스트리 | ✅ 결정적 재생성으로 `/crew-*` 반영 + `CUSTOM_SECTION` 보존 |
| customSkills 검증 | ✅ 스키마가 `crew-`/`skill-` 둘 다 허용 — 기존 커스텀 스킬 검증 실패 없음 |

> ⚠️ **수동 정리 필요**: 본인이 작성한 스크립트·alias·문서·`CLAUDE.md`의 `CUSTOM_SECTION` 안에 `/skill-impl` 같은 구 명령이 박혀 있으면 `/crew-*`로 직접 바꿔야 합니다 (프레임워크는 사용자 콘텐츠를 건드리지 않습니다).

> 💡 **커스텀 스킬 권장**: 본인이 `skill-` 접두사로 만든 커스텀 스킬(`.claude/skills/custom/skill-*`)은 그대로 동작하고 검증도 통과하지만(하위호환 허용), v4 리네임의 목적인 이름 충돌 회피 관점에선 `skill-` 접두사가 미래 안전하지 않습니다(외부 도구의 `/skill-foo`와 충돌 여지). 가능하면 디렉토리·`name:`·`customSkills` 항목을 `crew-`로 직접 변경하는 것을 권장합니다.

> ℹ️ **v3→v4 1회성 거친 모서리(정상)**: 이 한 번의 업그레이드는 **구 `skill-upgrade`가 실행**하는데, 그 마지막 검증 단계가 리네임된 `skill-validate`(현 `aick-validate`)를 호출하므로 "스킬 없음" 경고가 뜨거나 건너뛸 수 있습니다. 업그레이드 자체(스킬 교체·CLAUDE.md 재생성)는 정상 완료되며, **업그레이드 후 `/aick-validate`를 한 번 직접 실행**해 검증을 마치면 됩니다. CLAUDE.md 재생성 검증에서 드물게 거짓 경고가 보여도 레지스트리는 `/crew-*`로 올바르게 재생성됩니다(`git diff CLAUDE.md`로 확인). v4 이후 업그레이드부터는 이 모서리가 사라집니다(`aick-upgrade`가 `aick-validate`를 호출).

## 최초 업그레이드 (aick-upgrade도 skill-upgrade도 없는 프로젝트)

v1.6.0 이전에 초기화된 프로젝트에는 aick-upgrade 스킬이 없습니다.
아래 명령으로 1회성 부트스트랩 후 사용하세요:

```bash
# 1. ai-crew-kit 최신 버전 클론
git clone --depth 1 https://github.com/wejsa/ai-crew-kit.git /tmp/ai-crew-kit-latest

# 2. aick-upgrade 스킬만 복사
cp -r /tmp/ai-crew-kit-latest/.claude/skills/aick-upgrade .claude/skills/

# 3. 임시 파일 정리
rm -rf /tmp/ai-crew-kit-latest

# 4. 이후 aick-upgrade 사용 가능
/aick-upgrade
```

## 업그레이드 시 보존되는 항목

| 구분 | 항목 | 보존 방식 |
|------|------|----------|
| **프로젝트 상태** | project.json, backlog.json | 완전 보존 |
| **누적 학습 데이터** | `.claude/state/` 디렉토리 전체 보존 (주요 파일: lessons-learned.json, completed.json, health-history.json) | 완전 보존 (Phase 7 회귀 보호 메커니즘) |
| **프로젝트 코드** | src/, docs/, VERSION 등 | 완전 보존 |
| **CLAUDE.md 커스텀 규칙** | `CUSTOM_SECTION` 마커 사이 내용 | 추출 → 재생성 → 복원 |
| **`_base`/`general` 커스텀 파일** | conventions·checklists에 추가한 사용자 파일 | 자동 감지 → 복원 |
| **도구 권한 설정** | settings.json 커스텀 권한 | 머지 (기존 보존 + 새 항목 추가) |

## 롤백

문제 발생 시 즉시 이전 상태로 복원할 수 있습니다:

```bash
# 가장 최근 백업에서 롤백
/aick-upgrade --rollback

# 특정 백업 지정 — 실제 timestamp는 `ls .claude/temp/`로 확인 후 치환
/aick-upgrade --rollback .claude/temp/upgrade-backup-<YYYYMMDD-HHmmss>/
```

> **v2.0.0 사용자 안내** — `--rollback`은 R6 1차 자동 방어선([test_rollback.py](../tests/upgrade/test_rollback.py))으로 라운드트립·비-trivial 멱등성·사용자 보존이 회귀 보호됩니다. 매뉴얼 사전·사후 검증 체크리스트는 [migration-guide.md §4](./v2/migration-guide.md)를 참조하세요.
