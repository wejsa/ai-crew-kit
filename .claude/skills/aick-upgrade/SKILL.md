---
name: aick-upgrade
description: 프레임워크 업그레이드 - 클론/시드는 프레임워크 파일 교체, 플러그인 모드는 프로젝트-로컬 마이그레이션(gitignore·kitVersion·CLAUDE.md 재생성). /aick-upgrade로 호출합니다.
disable-model-invocation: true
allowed-tools: Bash(git:*), Bash(cp:*), Bash(rm:*), Bash(tar:*), Bash(diff:*), Bash(mktemp:*), Bash(mkdir:*), Bash(cat:*), Bash(ls:*), Bash(date:*), Bash(wc:*), Bash(df:*), Bash(jq:*), Bash(echo:*), Read, Write, Edit, Glob, Grep, AskUserQuestion
argument-hint: "[--dry-run] [--source <git-url|local-path>] [--version <tag>] [--rollback <backup-path>]"
complexity-hint: light
---

# aick-upgrade: 프레임워크 업그레이드

## 실행 조건
- 사용자가 `/aick-upgrade` 또는 "프레임워크 업그레이드해줘" 요청 시

## 옵션
```
/aick-upgrade                              # 최신 버전으로 업그레이드
/aick-upgrade --dry-run                    # 변경 사항 미리보기 (실제 변경 없음)
/aick-upgrade --source <git-url|local-path> # 소스 지정
/aick-upgrade --version <tag>               # 특정 버전으로 업그레이드
/aick-upgrade --rollback                    # 가장 최근 백업에서 롤백
/aick-upgrade --rollback <backup-path>      # 지정 백업에서 롤백
```

## 롤백 모드

`--rollback` 옵션 감지 시, 아래 플로우만 실행하고 종료:

1. 백업 경로 결정: `--rollback <path>` → 해당 경로, 경로 없음 → `.claude/temp/upgrade-backup-*/` 중 최신
2. 백업 디렉토리 존재 및 무결성 확인. 백업 내용물에 프레임워크 디렉토리가 포함되어 있는데 현재 설치가 플러그인 모드(= Step 0.5 D1 앵커가 절대경로로 치환되어 있음 — 롤백은 Step 0.5를 실행하지 않으므로 앵커 관찰로 직접 판정)이면 경고 1줄: "클론 시절 백업 — 복원 시 로컬 시드가 재생성됩니다"
3. 사용자 확인: "다음 백업에서 롤백합니다: {경로}. 진행하시겠습니까?"
4. `backup.tar.gz` 해제 → 백업 내용물 복원 (모드별 상이 — 클론 백업: 프레임워크 디렉토리·CLAUDE.md 등 / 플러그인 P4 백업: 프로젝트-로컬 4파일. **플러그인 백업의 project.json은 통째 스냅샷 복원** — 업그레이드 이후의 변이도 함께 되돌아감)
5. `project.json`의 `kitVersion`을 백업 시점 값으로 되돌림
6. 롤백 완료 리포트 출력

## 실행 플로우

### Step 0.5: 설치 모드 판별 (v4.8.0)

**`${CLAUDE_PLUGIN_ROOT}`는 env 변수가 아니라 스킬 로드 시점의 텍스트 치환이다** (CLAUDE.md "경로 해석 규칙" 판정 규칙과 동일). Bash로 env를 검사하지 말 것.

- **D1 (로드 출처)**: 아래 **앵커 라인**의 경로 표기만 보고 판정한다(설명 문장 자체의 `${...}`도 플러그인 모드에선 치환되므로, 판정은 오직 앵커 라인 기준). 앵커가 절대경로로 치환되어 있으면 **플러그인 로드**, 리터럴 `${CLAUDE_PLUGIN_ROOT}/...` 형태 그대로면 **클론/시드 로드**.
  - 앵커: `${CLAUDE_PLUGIN_ROOT}/.claude/templates/CLAUDE.md.tmpl`
  - 플러그인 로드면 치환된 절대경로에서 plugin root를 얻고 `<root>/VERSION` 존재 확인 (부재 → "플러그인 설치 손상 — `/plugin` 재설치 후 재시도" STOP)
- **D2 (로컬 시드 존재)**: Glob `.claude/skills/aick-*/SKILL.md` 결과가 비어있지 않음 = 빌트인 시드 존재. `.claude/skills/custom/`은 판별에서 제외(플러그인 모드에도 존재 가능). `.claude/templates/` 존재 여부도 판별자가 **아님**(부분 시드 오판 위험).
- **라우팅**:

| D1 | D2 | 플로우 |
|----|----|--------|
| 클론/시드 로드 | — | 아래 Step 1~15.5 (클론 플로우) |
| 플러그인 로드 | 시드 없음 | **"플러그인 모드 플로우" 섹션 (P1~P6)**. 로컬 `.claude/templates/*.tmpl`만 잔존하면 안내 1줄("로컬 템플릿 감지 — 번들 템플릿이 SSOT, 로컬본 미사용") 후 진행 |
| 플러그인 로드 | 시드 존재 | 클론 플로우 + 안내 1줄: "플러그인과 로컬 시드 동시 감지 — 로컬 시드 기준 업그레이드. 플러그인-only 전환은 eject-guide §플러그인-only 전환 참조" |

- `--rollback`은 모드 무관 (위 롤백 모드 섹션).

### Step 1: 환경 검증

| 항목 | 조건 | 처리 |
|------|------|------|
| project.json | 없음 | "/aick-init 먼저 실행" 안내 후 종료 |
| Git 상태 | uncommitted changes | 경고 + 진행 여부 질문 |
| 잠금 파일 | `.upgrade.lock` 존재 | "이전 업그레이드 중단됨" 경고 + 롤백 안내 |
| 디스크 공간 | 부족 | 경고 후 종료 |

확인 대상: `project.json`, `git status --porcelain`, `.claude/temp/.upgrade.lock`, `df -h .`

### Step 2: 소스 확보

소스 결정 우선순위: `--source` 옵션 → `project.json`의 `kitSource` → 기본값 `https://github.com/wejsa/ai-crew-kit.git`

- Git URL → `git clone --depth 1 [--branch <tag>]` 임시 디렉토리에
- 로컬 경로 → 직접 사용
- `--version` 옵션 → `--branch <tag>`로 특정 버전 클론

### Step 3: 소스 구조 검증

필수 디렉토리/파일 확인: `skills/`, `domains/`, `templates/`, `schemas/`, `VERSION`
하나라도 없으면 "유효한 AI Crew Kit 소스가 아닙니다" 안내 후 종료.

### Step 4: 버전 비교

| 비교 결과 | 동작 |
|-----------|------|
| 새 버전 > 현재 | 정상 진행 |
| 새 버전 = 현재 | "이미 최신 버전" + 진행 여부 질문 |
| 새 버전 < 현재 | "다운그레이드" 경고 |
| 현재 = unknown | 부트스트랩 모드 — 정상 진행 |

### Step 5: 스키마 마이그레이션 체크

`migrations.json` 확인 → 있으면 현재 kitVersion 해당 마이그레이션 항목 확인, 없으면 스키마 diff 폴백.

### Step 6: 커스터마이징 감지

**6-0. SHA256 해시 비교 (전체 프레임워크 파일)**

전체 프레임워크 디렉토리(`agents`, `skills`, `domains`, `templates`, `schemas`, `workflows`, `docs`, `hooks`)의 모든 파일에 대해 SHA256 해시 비교:
- 동일 경로에 존재하나 해시 불일치 → 사용자 수정 파일로 감지
- 감지된 파일은 미리보기에 포함 (파일명, 현재 해시 앞 8자, 소스 해시 앞 8자)
- 덮어쓰기 전 사용자에게 확인 (AskUserQuestion): "소스로 덮어쓰기" / "현재 유지" / "수동 머지"
- ⚠️ **`hooks/` 스크립트는 clone/세션 시 자동 실행되는 보안 민감 파일**이다. 해시 불일치 hook은 미리보기에서 반드시 가시화하고, 교체 후 `aick-health-check`의 `hook-safety` 카테고리가 위험 패턴을 재검한다. 사용자가 직접 하드닝한 hook을 보존하려면 "현재 유지"를 선택한다(Step 11이 해당 파일 교체에서 제외).

**6-1. 커스텀 파일 감지**: `.claude/domains/_base/`·`.claude/domains/general/` 아래에서 현재에만 존재하는 파일 = 사용자 추가 커스텀 체크리스트/컨벤션 파일
**6-2. settings.json 커스텀 권한 감지**: 현재에만 있는 `allow[]` 항목 = 커스텀 권한

### Step 7: 변경 미리보기 (diff)

필수 포함: 버전 전환(v{current} → v{new}), 디렉토리별 추가/수정/삭제 수, 보존 커스터마이징 요약, 해시 불일치 파일 목록, 스키마 마이그레이션 항목

### Step 8: 사용자 확인

- `--dry-run`: 미리보기만 출력 후 **종료**
- 일반: AskUserQuestion으로 진행 여부 확인

### Step 9: 백업 생성

백업 디렉토리: `.claude/temp/upgrade-backup-{YYYYMMDD-HHmmss}/`
- 프레임워크 디렉토리(**업데이트 대상 표 전체 — `.claude/hooks/` 포함**, Step 11이 삭제하므로 롤백 위해 필수) + settings.json + CLAUDE.md + README.md → `backup.tar.gz`
- **v3.0.0+ — 잔여 도메인 자산도 백업에 포함**: Step 11.5에서 opt-in 삭제 가능한 `.claude/domains/{fintech,ecommerce,saas,healthcare}/`, `.claude/rules/`, `.claude/domains/_registry.json` 중 현재 존재하는 항목을 `backup.tar.gz`에 함께 담는다(삭제 선택 시 롤백 보장).
- `tar tzf`로 무결성 검증
- 현재 kitVersion을 `kitVersion.txt`에 기록

### Step 10: 커스텀 콘텐츠 추출

**10-0. CUSTOM_SECTION 마커 안전장치**
- CLAUDE.md/README.md에서 `CUSTOM_SECTION_START` 마커 존재 확인
- 마커 없으면: 전체 파일 백업 + 템플릿 diff로 커스텀 내용 추출 + 경고 출력

**10-1~10-4**: CLAUDE.md/README.md 커스텀 섹션, `_base`/`general` 커스텀 파일, settings.json 커스텀 권한 — 각각 임시 저장

### Step 11: 프레임워크 파일 교체

- 잠금 파일 + 진행 상태 파일 생성
- 커스텀 스킬 디렉토리(`.claude/skills/custom`) 별도 백업
- 프레임워크 디렉토리 삭제 → 새 소스에서 복사 (디렉토리 단위). **대상은 "업데이트 대상" 표의 모든 디렉토리 — `.claude/hooks/` 포함**(hook 스크립트 전파).
- **Step 6-0에서 "현재 유지"로 결정된 파일은 복사 후 백업본으로 되돌려 보존**(디렉토리 단위 복사가 사용자 선택을 덮어쓰지 않도록 — 특히 하드닝한 hook). "수동 머지" 선택 파일은 소스+현재를 나란히 남겨 사용자 머지 안내.
- 커스텀 스킬 복원
- **실패 시 자동 롤백**: `tar xzf "$BACKUP_DIR/backup.tar.gz"` + 잠금 파일 삭제

> **v3.0.0 — 도메인 디렉토리 단위 복사 주의**: `.claude/domains/` 교체는 **디렉토리 통째 삭제 후 복사**가 아니라 `_base`·`general` 등 신규 소스에 존재하는 항목만 동기화한다. 신규 소스에는 `fintech`/`ecommerce`/`saas`/`healthcare` 도메인 디렉토리가 없으므로 **이들은 자연히 미복사**되며, 기존 시드의 잔여 도메인 디렉토리는 **강제로 삭제하지 않고 그대로 둔다**(아래 Step 11.5에서 opt-in 정리). 이 "미삭제" 예외는 **`.claude/domains/`에만** 적용된다 — 사용자 추가 체크리스트·컨벤션이 `_base`/`general`에 in-place로 섞여 살기 때문이다.

> **v4.0.0 — `.claude/skills/`는 통째 교체(중요, 위 도메인 예외와 다름)**: `.claude/skills/`는 **`custom/`을 먼저 별도 백업**(line 116) → **디렉토리 통째 삭제 → 새 소스에서 복사** → **`custom/` 복원** 순으로 교체한다. 따라서 상류에서 **이름이 바뀌거나 제거된 빌트인 스킬**(프리픽스 리네임 — v4.0.0 `skill-*`→`crew-*`, v4.6.0 `crew-*`→`aick-*` 22개; v3.0.0의 `skill-domain` 제거)은 통째 삭제 단계에서 자연 제거되어 **orphan(`crew-impl`과 `aick-impl` 동시 존재)으로 남지 않는다**. 도메인의 "미삭제" 예외를 `.claude/skills/`에 **일반화하지 말 것** — 빌트인 스킬은 in-place 사용자 자산이 아니므로 통째 교체가 맞다. 사용자 커스텀 스킬(`.claude/skills/custom/`)은 별도 백업·복원으로 보존되며, 이름은 변경하지 않는다(skill-/crew- 접두사 커스텀 스킬도 그대로 유지 — customSkills 스키마가 aick-/crew-/skill- 셋 다 허용).

### Step 11.5: 잔여 도메인 디렉토리 opt-in 정리 (v3.0.0+)

v3.0.0은 도메인 콘텐츠(`fintech`/`ecommerce`/`saas`/`healthcare`)와 `.claude/rules/`, `_registry.json`을 제거했다. 신규 소스에 없어 자연 미복사되지만, **기존 시드에 남은 잔여 디렉토리는 자동 삭제하지 않는다**.

- 잔여 감지: `.claude/domains/{fintech,ecommerce,saas,healthcare}/`, `.claude/rules/`, `.claude/domains/_registry.json` 중 현재 존재하는 항목 목록화 (`_base`·`general`은 **대상 아님 — 절대 삭제 금지**).
- 잔여가 있으면 AskUserQuestion으로 **opt-in** 제안: "지금 정리(백업 후 삭제)" / "그대로 유지".
  - "정리" 선택 시에만: Step 9 백업(`backup.tar.gz`)에 이미 포함되어 있음을 확인 → 해당 항목 삭제 → 삭제 목록 리포트.
  - "유지" 선택(기본 안전값) 시: 그대로 둔다. 도메인 health-check도 함께 제거되므로 "삭제→health-check CRITICAL" 지뢰는 발생하지 않는다.
- **강제 삭제 금지**: 사용자가 명시적으로 "정리"를 선택하지 않는 한 어떤 잔여 항목도 삭제하지 않는다. `_base`·`general`은 어떤 경우에도 삭제 대상에 포함하지 않는다.

### Step 12: 커스터마이징 복원 + project.json 마이그레이션

- 12-1. `_base`/`general` 커스텀 파일 원위치 복원
- 12-2. settings.json 머지:
  - **권한**: `permissions.allow` 합집합(중복 제거) + 기존 `permissions.deny` 보존
  - **`hooks` 필드 동기화**: 새 소스의 hooks 등록을 기준으로, 이벤트별(`PreToolUse`/`PostToolUse`/`SessionStart`/`Stop`)로 **프레임워크 훅 항목**을 누락 시 추가 + 변경(command/timeout/matcher) 시 갱신. **프레임워크 훅 식별은 경로 접두 무관 + 스크립트 basename 기준**: command가 `.claude/hooks/{session-start,post-tool-use,stop,pre-tool-use,diagnose}.sh`를 참조하면(상대경로 `.claude/hooks/...`·절대경로 `$CLAUDE_PROJECT_DIR/.claude/hooks/...` 모두) 동일 프레임워크 훅으로 간주해 **소스 항목으로 교체**(구버전 상대경로 등록을 제거하고 새 형식으로 대체 — 중복 등록 방지). `.claude/hooks/`를 참조하지 **않는** 사용자 커스텀 훅 항목은 보존. → v2.4.0 `PreToolUse` 머지 게이트 등록이 기존 시드 프로젝트에 도달하는 경로(이전엔 권한만 머지해 hooks 미전파). `settings.local.json`은 미변경.
- 12-3. project.json: kitVersion 업데이트, kitSource 설정, migrations 적용
- 12-4. 프로젝트 파일 마이그레이션 (migrations.json의 `add_gitignore_entry` 타입):
  - 대상 entry가 `.gitignore`에 없으면 주석(`comment`)과 함께 추가
  - `git ls-files --error-unmatch <entry>` 검사 → 이미 추적 중인 파일 감지 시 `trackedWarning` 메시지 출력 (자동 제거하지 않고 사용자 안내만)
  - 이미 존재하면 no-op

### Step 13: CLAUDE.md/README.md 재생성

> ⚠️ **서브 에이전트 위임 금지** — 메인 에이전트가 직접 수행한다. 서브 에이전트는 템플릿 변경 맥락이 없어 구 버전을 복사할 위험이 있다.

**13-0. CUSTOM_SECTION 확인**: Step 10에서 임시 저장한 CUSTOM_SECTION 내용을 사용한다 (이 시점에서 기존 CLAUDE.md를 다시 읽지 않는다)

**13-1. 결정적 치환 (CLAUDE.md)**:
1. **새 템플릿**(`templates/CLAUDE.md.tmpl`) 전체를 Read로 로드
2. 마커(`{{...}}`)를 Layered Override 값으로 문자열 치환
3. `{{CUSTOM_SECTION}}`에 13-0에서 추출한 내용 삽입
4. 치환 완료된 전체 내용을 Write로 CLAUDE.md에 기록
5. ❌ **이전 CLAUDE.md를 참조하지 않는다** — CUSTOM_SECTION 외의 내용은 오직 템플릿에서만 생성

**13-2. 결정적 치환 (README.md)**: 동일 패턴

**13-3. 재생성 검증**:
1. 새 템플릿에서 비-마커 고유 문장 3개를 샘플 추출
2. 재생성된 CLAUDE.md에서 해당 문장 존재 확인 (Grep)
3. 구 템플릿에만 있던 삭제 대상 키워드가 잔존하는지 네거티브 체크 (`CUSTOM_SECTION` 내부 제외)
   - ⚠️ 네거티브 키워드는 **구체적 명령 토큰**(예: `/skill-impl`, `/skill-plan`)으로 한정한다. **bare `skill-`을 키워드로 쓰지 말 것** — 보존 대상인 `skill-profiles.json` 파일명·일반 명사 "skill"/"스킬"·`skillProfile`/`customSkills` 필드명에 오탐해 재생성을 무한 재시도/중단시킨다.
4. 불일치 시 → 13-1부터 재시도 (최대 1회)

### Step 14: 완료 처리

잠금 파일 삭제, 진행 상태 파일 삭제, 임시 클론 디렉토리 정리

### Step 15: 프레임워크 검증

`Skill tool: skill="aick-validate"` 자동 호출.
- 통과 → "✅ 검증 통과", 실패 → 경고 + `--fix` 안내 (롤백하지 않음)

### Step 15.5: 신규 기능 안내

`migrations.json`의 `features` 배열에서 **이전 버전 < feature.version ≤ 새 버전** 범위의 항목을 필터링하여 안내:

```
━━━ 🆕 신규 기능 안내 ━━━━━━━━━━━━━━━━
v{version}: {title}
  {description}
  👉 {detail}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

각 feature의 `action` 필드에 따라 안내 방식 분기:
- `none`: "별도 설정 불필요" — 정보성 안내만
- `recommend`: "권장 설정" — 설정 방법 안내 (선택)
- `required`: "필수 설정" — 설정하지 않으면 기능 제한
- `optional`: "선택 설정" — 설정 방법 안내 (선택, recommend와 동일 톤·비강제)
- 그 외 미지정 값: `recommend`와 동일하게 정보성+설정 안내로 처리(분기 누락으로 안내가 누락되지 않도록 폴백)

해당 버전 범위에 features가 없으면 이 단계를 스킵한다.

## 플러그인 모드 플로우 (P1~P6) — v4.8.0

플러그인 파일(skills·agents·hooks·templates)은 `/plugin marketplace update`의 소유다. 본 플로우는 **프로젝트-로컬 파일만** 다룬다: `.gitignore`·`.claude/state/project.json`·`CLAUDE.md`·`README.md`. 파일 교체 계열 단계(Step 2·3·6-0~6-2·9·11·11.5·12-1·12-2)는 전부 생략하며, **어떤 P-스텝도 로컬 프레임워크 디렉토리를 생성하지 않는다** (시드 전환 금지 — `.claude/skills/`·`.claude/templates/` 등).

### P1. 환경 검증
- project.json 부재 → "/aick-init 먼저 실행" 안내 후 종료
- `<plugin root>/VERSION` 부재 → STOP (Step 0.5 백스톱)
- Git uncommitted changes → 경고 + 진행 여부 질문 (Step 1과 동일)
- `.claude/temp/.upgrade.lock` 존재 → **차단** + "`--rollback` 또는 잠금 수동 삭제 후 재시도" 안내 (클론 Step 1은 경고만 — 플러그인 분기는 P3.5~P6 동시 실행을 차단)

### P2. 버전 비교
current = `project.json.kitVersion`, target = `<plugin root>/VERSION`.
- current 부재·`unknown`·semver 패턴 불일치(`v4.7.0`·`0.1.0` 오기입 등) → **부트스트랩**: current를 `0.0.0`으로 간주
- target == current → "이미 최신" + 진행 여부 질문 (재적용은 수렴 의미론으로 안전 — 아래 불변식)
- target < current → "플러그인이 프로젝트 기록보다 구버전 — `/plugin marketplace update` 먼저 실행 권장" + 진행 여부 질문
- `--source`/`--version` 지정 시 → "플러그인 모드의 타깃은 설치된 플러그인 버전입니다. 다른 버전은 `/plugin marketplace update` 또는 클론 모드를 사용하세요" 안내 후 **종료**

### P3. 미리보기 + 확인
적용 예정 마이그레이션 목록(**필터: current < to ≤ target** — migrations.json `from` 필드는 문서화 용도, 필터에 미사용) + 재생성 대상(CLAUDE.md, README는 마커 존재 시) + kitVersion 전환 출력. `--dry-run`이면 여기서 **종료**. 일반: AskUserQuestion 1회.

### P3.5. 잠금
`.claude/temp/.upgrade.lock` + `upgrade-state.json` 생성 — P3.5~P6 구간 보호 (클론 Step 11 첫 줄과 동일 패턴).

### P4. 경량 백업
`.claude/temp/upgrade-backup-{YYYYMMDD-HHmmss}/backup.tar.gz` — `CLAUDE.md`·`README.md`·`.gitignore`·`.claude/state/project.json` 중 **존재하는 파일만** 포함(부재 파일은 `absent.txt` 매니페스트에 기록 — 롤백 시 생성하지 않음). `tar tzf` 무결성 검증 + 현재 kitVersion을 `kitVersion.txt`에 기록 (Step 9와 동일 형식 — `--rollback` 호환).

### P5. 적용 (순서 고정 — kitVersion 기록은 마지막)
1. **마이그레이션**: Step 12-4 `add_gitignore_entry`(no-op 멱등·trackedWarning 동일) + Step 12-3 `add_field` — 단 **path 루트가 project.json 스키마 top-level 속성인 항목만** 적용, 그 외(`backlog.*` 등)는 스킵+로그(부트스트랩에서 비-project.json 마이그레이션이 project.json을 오염하지 않도록 — `scripts/validate-v2-migration.py`의 schema-top-key 필터와 동일 대상 규칙. 단 그 스크립트는 `to ≤ target` 누적 적용이고 하한 `current`는 없다 — 적용 가능한 change type이 모두 멱등이라 종료 상태 동일). `kitSource` add_field는 플러그인 모드 스킵(클론 캡처 변수 — 기존 값 보존, 부재 시 미기록).
2. **CLAUDE.md 재생성**: Step 13 재사용 (13-0 CUSTOM_SECTION 안전장치, 13-1 결정적 치환 — 템플릿 = `<plugin root>/.claude/templates/CLAUDE.md.tmpl`, 13-3 검증+재시도 1회, 서브 에이전트 위임 금지)
3. **README.md 재생성 — 조건부**: CUSTOM_SECTION 마커 있으면 13-2 재사용(번들 템플릿), 마커 없으면 **스킵** + 안내 "README는 사용자 소유로 보임 — 재생성을 원하면 CUSTOM_SECTION 마커 복원 후 재실행" (CLAUDE.md는 프레임워크 소유라 무조건 재생성 — 10-0 안전장치 적용)
4. **kitVersion = target 기록** + `metadata.version` 1 증가 — **2~3 검증 통과 후에만** (중간 실패 시 SI-06 드리프트 신호가 살아남아 재실행을 유도)

**실패 시 자동 복원**: P5 중 오류 → P4 `backup.tar.gz` **자동 해제**(`tar xzf` — 클론 Step 11 자동 롤백과 동일 패턴, 안내가 아니라 자동) + 잠금 삭제 + 실패 보고.

### P6. 마무리
잠금·진행 상태 파일 삭제 → `Skill tool: skill="aick-validate"` 자동 호출 (출력에 1줄 명시: "플러그인 모드 — 검증 범위는 state·custom 스킬 중심") → 신규 기능 안내 (Step 15.5 동일 필터 — 부트스트랩은 전체 features) → 출력: 버전 전환, 적용 마이그레이션, 재생성 결과(README 스킵 여부 포함), 백업 위치, 롤백 명령.

### 불변식 (P-플로우)
- **수렴 의미론**: 입력(project.json·CUSTOM_SECTION·플러그인 버전) 불변 시 재실행 = no-op 동등. 입력 변경 시 현재 값으로 수렴(안전).
- state 중 `project.json` **제외** 무변경(backlog.json·completed.json 등). custom 스킬·settings.json 무변경.
- 플러그인 모드 적용 가능 마이그레이션 대상은 **P4 백업 4파일로 한정** — migrations.json에 새 change type 추가 시 P4 백업 목록 동시 확장 의무.

## 출력

필수 포함: 버전 전환(v{old}→v{new}), 변경 요약(업데이트 디렉토리/추가/수정/삭제 수), 복원 커스터마이징 목록, 스키마 마이그레이션 결과, **신규 기능 안내** (있을 때만), 백업 위치, 롤백 명령어, CHANGELOG 발췌

## 업데이트 대상 (프레임워크 파일)

| 디렉토리 | 설명 |
|---------|------|
| `.claude/agents/` | 에이전트 정의 |
| `.claude/skills/` | 스킬 구현 |
| `.claude/domains/` | `_base`(컨벤션·체크리스트·헬스·템플릿)·`general` 자산 (커스텀 파일은 감지→복원) |
| `.claude/templates/` | CLAUDE.md.tmpl, README.md.tmpl 등 |
| `.claude/schemas/` | project.schema.json, migrations.json, secrets-patterns.schema.json, lessons-learned.schema.json |
| `.claude/workflows/` | 워크플로우 YAML |
| `.claude/docs/` | 프레임워크 문서 |
| `.claude/hooks/` | 훅 스크립트 (clone/세션 자동 실행 — **보안 민감**: 해시 비교+승인 후 교체, 교체 후 hook-safety 재검) |

**머지 방식**: `.claude/settings.json` — `permissions.allow` 추가 머지(기존 커스텀 권한 보존) + `hooks` 필드 프레임워크 훅 동기화(Step 12-2, 사용자 커스텀 훅 보존). `settings.local.json`은 보존(미변경).

## 보존 대상 (프로젝트 파일)

- `.claude/state/*` — **디렉토리 전체 보존** (사용자 누적 데이터). 주요 파일: `backlog.json`, `completed.json`, `lessons-learned.json` (Phase 7), `health-history.json`, `continuation-plan.md` 등
  - **v1 → v2 backlog 호환**: `backlog.schema.json`은 v1.x ↔ v2 사이 차이가 없어 변환 룰 불필요. `migrations.json`은 `project.json`만 다루며 `backlog.json`은 그대로 보존된다. v1 시기 `step.description` / `step.estimatedLines` 같은 옵셔널 필드도 현 schema에 옵셔널로 포함되어 검증 통과 (Issue #65, 회귀 보호: `tests/upgrade/test_backlog_compat.py`).
- `.claude/settings.local.json` — 로컬 권한 override
- `.claude/temp/` — 진행 중 plan 파일, 백업 디렉토리
- `.claude/plans/` — 사용자 plan 산출물
- `CLAUDE.md` — 재생성 + `CUSTOM_SECTION` 보존
- `README.md` — 재생성 + `CUSTOM_SECTION` 보존
- `VERSION`, `CHANGELOG.md`, `docs/`, `src/` 등 프로젝트 자산

## 안전장치

| 장치 | 설명 |
|------|------|
| 잠금 파일 | `.claude/temp/.upgrade.lock` — Step 11~14 구간 보호 |
| 진행 상태 | `.claude/temp/upgrade-state.json` — 중단 시 복구 참조 |
| 디스크 검증 | Step 1 `df -h` |
| 백업 무결성 | Step 9 `tar tzf` 검증 |
| 자동 롤백 | Step 11 교체 중 오류 → 즉시 백업 복원 |
| SHA256 해시 | Step 6-0 전체 프레임워크 파일 해시 비교 → 사용자 수정 파일 감지 |
| CUSTOM_SECTION 마커 | Step 10-0 사전 확인 + Step 13-0 누락 시 자동 삽입 |

## 주의사항
- Git 상태가 clean한 상태에서 실행 권장
- 업그레이드 후 `git diff`로 변경사항 확인 권장
- 문제 발생 시 `--rollback`으로 즉시 복원 가능
