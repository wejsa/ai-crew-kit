# 프레임워크 업그레이드

> [← README로 돌아가기](../README.md)

AI Crew Kit이 업데이트되면, 기존 프로젝트에서 프레임워크 파일만 선택적으로 업그레이드할 수 있습니다.
프로젝트 코드, 상태 파일(backlog, project.json), 커스텀 설정은 보존됩니다.

## 업그레이드 실행

```bash
# 변경 사항 미리보기 (실제 변경 없음)
/skill-upgrade --dry-run

# 최신 버전으로 업그레이드
/skill-upgrade

# 특정 버전으로 업그레이드
/skill-upgrade --version v1.7.0

# 소스 지정 (기본값은 project.json의 kitSource)
/skill-upgrade --source https://github.com/wejsa/ai-crew-kit.git
```

## 최초 업그레이드 (skill-upgrade가 없는 프로젝트)

v1.6.0 이전에 초기화된 프로젝트에는 skill-upgrade 스킬이 없습니다.
아래 명령으로 1회성 부트스트랩 후 사용하세요:

```bash
# 1. ai-crew-kit 최신 버전 클론
git clone --depth 1 https://github.com/wejsa/ai-crew-kit.git /tmp/ai-crew-kit-latest

# 2. skill-upgrade 스킬만 복사
cp -r /tmp/ai-crew-kit-latest/.claude/skills/skill-upgrade .claude/skills/

# 3. 임시 파일 정리
rm -rf /tmp/ai-crew-kit-latest

# 4. 이후 skill-upgrade 사용 가능
/skill-upgrade
```

## 업그레이드 시 보존되는 항목

| 구분 | 항목 | 보존 방식 |
|------|------|----------|
| **프로젝트 상태** | project.json, backlog.json | 완전 보존 |
| **프로젝트 코드** | src/, docs/, VERSION 등 | 완전 보존 |
| **CLAUDE.md 커스텀 규칙** | `CUSTOM_SECTION` 마커 사이 내용 | 추출 → 재생성 → 복원 |
| **도메인 커스텀 파일** | add-doc, add-checklist로 추가한 파일 | 자동 감지 → 복원 |
| **도구 권한 설정** | settings.json 커스텀 권한 | 머지 (기존 보존 + 새 항목 추가) |

## 롤백

문제 발생 시 즉시 이전 상태로 복원할 수 있습니다:

```bash
# 가장 최근 백업에서 롤백
/skill-upgrade --rollback

# 특정 백업 지정
/skill-upgrade --rollback .claude/temp/upgrade-backup-20260208-143052/
```
