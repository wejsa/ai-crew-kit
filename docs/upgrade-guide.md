# 프레임워크 업그레이드

> [← README로 돌아가기](../README.md)

AI Crew Kit이 업데이트되면, 기존 프로젝트에서 프레임워크 파일만 선택적으로 업그레이드할 수 있습니다.
프로젝트 코드, 상태 파일(backlog, project.json, lessons-learned), 커스텀 설정은 보존됩니다.

## 업그레이드 실행

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

## 최초 업그레이드 (crew-upgrade가 없는 프로젝트)

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
