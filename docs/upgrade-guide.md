# 프레임워크 업그레이드

> [← README로 돌아가기](../README.md)

AI Crew Kit이 업데이트되면, 기존 프로젝트에서 프레임워크 파일만 선택적으로 업그레이드할 수 있습니다.
프로젝트 코드, 상태 파일(backlog, project.json, lessons-learned), 커스텀 설정은 보존됩니다.

## 업그레이드 실행

> ⚠️ **v3.x 시드에서 v4.0.0으로 처음 올리는 경우** 아래 `/crew-upgrade` 명령이 아직 프로젝트에 없습니다(구 `/skill-upgrade`만 존재). 먼저 [v3.x → v4.0.0 마이그레이션](#v3x--v400-마이그레이션-스킬-프리픽스-skill---crew-) 섹션을 따라 한 번 올린 뒤, 이후부터 아래 명령을 사용하세요.

```bash
# 변경 사항 미리보기 (실제 변경 없음 — 권장 첫 단계)
/crew-upgrade --dry-run

# 최신 버전으로 업그레이드
/crew-upgrade

# 특정 버전으로 업그레이드 (예: v2.0.0 GA)
/crew-upgrade --version v2.0.0

# 소스 지정 (기본값은 project.json의 kitSource)
/crew-upgrade --source https://github.com/wejsa/ai-crew-kit.git
```

## v1.x → v2.0 마이그레이션

v1.x 사용자는 `/crew-upgrade --version v2.0.0` 한 번이면 충분합니다 — `migrations.json` v2.0.0의 4 add_field(`hooks` / `conventions.skillProfile` / `conventions.overridePriority` / `tokenHints`)가 자동 적용됩니다.

| 항목 | 자동 처리 |
|------|----------|
| `project.json` 스키마 확장 | ✅ 4 add_field 자동 마이그레이션 |
| `CLAUDE.md` Override 템플릿 갱신 | ✅ 결정적 치환 + `CUSTOM_SECTION` 보존 |
| `.claude/state/lessons-learned.json` 회귀 보호 | ✅ 기존 데이터 100% 보존, schema 검증 활성 |
| 가중치 재배분 (Phase 1 hook-safety + Phase 5) | ✅ 자동 — 사용자 점수 영향 ≤1점 |

**점수 영향 ≤1점, 수동 작업 0건.** 상세 변경 사항·FAQ·롤백 매뉴얼은 [v1.x → v2.0.0 마이그레이션 가이드](./v2/migration-guide.md)를 참조하세요.

## v3.x → v4.0.0 마이그레이션 (스킬 프리픽스 skill-* → crew-*)

v4.0.0에서 22개 빌트인 스킬의 호출 명령어가 `/skill-*` → `/crew-*`로 바뀌었습니다 (예: `/skill-impl` → `/crew-impl`). **기존 v3.x 시드 프로젝트에는 아직 구 `skill-upgrade` 스킬만 있으므로, 첫 업그레이드는 본인 프로젝트에 있는 구 명령으로 실행합니다:**

```bash
# 1. 기존 프로젝트에 있는 구 명령으로 v4.0.0 업그레이드 (이 명령이 스스로를 crew-upgrade로 교체)
/skill-upgrade --version v4.0.0

# 2. 이후부터는 새 명령 사용
/crew-upgrade
```

업그레이드가 자동 처리하는 것:

| 항목 | 자동 처리 |
|------|----------|
| 빌트인 스킬 디렉토리 교체 | ✅ `.claude/skills/` 통째 교체 — 구 `skill-*` 22개 디렉토리(구 `skill-upgrade` 포함) 자연 제거, 새 `crew-*` 설치 |
| 커스텀 스킬 보존 | ✅ `.claude/skills/custom/`은 별도 백업·복원 (이름 변경 없음 — skill- 접두사 커스텀 스킬도 그대로 유지) |
| CLAUDE.md 스킬 레지스트리 | ✅ 결정적 재생성으로 `/crew-*` 반영 + `CUSTOM_SECTION` 보존 |
| customSkills 검증 | ✅ 스키마가 `crew-`/`skill-` 둘 다 허용 — 기존 커스텀 스킬 검증 실패 없음 |

> ⚠️ **수동 정리 필요**: 본인이 작성한 스크립트·alias·문서·`CLAUDE.md`의 `CUSTOM_SECTION` 안에 `/skill-impl` 같은 구 명령이 박혀 있으면 `/crew-*`로 직접 바꿔야 합니다 (프레임워크는 사용자 콘텐츠를 건드리지 않습니다).

> ℹ️ **v3→v4 1회성 거친 모서리(정상)**: 이 한 번의 업그레이드는 **구 `skill-upgrade`가 실행**하는데, 그 마지막 검증 단계가 리네임된 `skill-validate`(현 `crew-validate`)를 호출하므로 "스킬 없음" 경고가 뜨거나 건너뛸 수 있습니다. 업그레이드 자체(스킬 교체·CLAUDE.md 재생성)는 정상 완료되며, **업그레이드 후 `/crew-validate`를 한 번 직접 실행**해 검증을 마치면 됩니다. CLAUDE.md 재생성 검증에서 드물게 거짓 경고가 보여도 레지스트리는 `/crew-*`로 올바르게 재생성됩니다(`git diff CLAUDE.md`로 확인). v4 이후 업그레이드부터는 이 모서리가 사라집니다(`crew-upgrade`가 `crew-validate`를 호출).

## 최초 업그레이드 (crew-upgrade도 skill-upgrade도 없는 프로젝트)

v1.6.0 이전에 초기화된 프로젝트에는 crew-upgrade 스킬이 없습니다.
아래 명령으로 1회성 부트스트랩 후 사용하세요:

```bash
# 1. ai-crew-kit 최신 버전 클론
git clone --depth 1 https://github.com/wejsa/ai-crew-kit.git /tmp/ai-crew-kit-latest

# 2. crew-upgrade 스킬만 복사
cp -r /tmp/ai-crew-kit-latest/.claude/skills/crew-upgrade .claude/skills/

# 3. 임시 파일 정리
rm -rf /tmp/ai-crew-kit-latest

# 4. 이후 crew-upgrade 사용 가능
/crew-upgrade
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
/crew-upgrade --rollback

# 특정 백업 지정 — 실제 timestamp는 `ls .claude/temp/`로 확인 후 치환
/crew-upgrade --rollback .claude/temp/upgrade-backup-<YYYYMMDD-HHmmss>/
```

> **v2.0.0 사용자 안내** — `--rollback`은 R6 1차 자동 방어선([test_rollback.py](../tests/upgrade/test_rollback.py))으로 라운드트립·비-trivial 멱등성·사용자 보존이 회귀 보호됩니다. 매뉴얼 사전·사후 검증 체크리스트는 [migration-guide.md §4](./v2/migration-guide.md)를 참조하세요.
