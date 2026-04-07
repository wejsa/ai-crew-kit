# 프레임워크 제거 가이드 (Eject)

> [← README로 돌아가기](../README.md)

AI Crew Kit을 사용하다가 프레임워크 없이 진행하려는 경우를 위한 가이드입니다.

## 프레임워크가 관리하는 파일

| 디렉토리/파일 | 역할 | 제거 안전성 |
|-------------|------|-----------|
| `.claude/skills/` | 스킬 정의 (SKILL.md) | 안전하게 삭제 가능 |
| `.claude/domains/` | 도메인 컨벤션, 체크리스트 | 안전하게 삭제 가능 |
| `.claude/templates/` | CLAUDE.md 생성 템플릿 | 안전하게 삭제 가능 |
| `.claude/agents/` | 에이전트 정의 | 안전하게 삭제 가능 |
| `.claude/schemas/` | JSON 스키마 | 안전하게 삭제 가능 |
| `.claude/workflows/` | 워크플로우 정의 | 안전하게 삭제 가능 |
| `.claude/docs/` | 프레임워크 내부 문서 | 안전하게 삭제 가능 |
| `.claude/state/project.json` | 프로젝트 설정 | 참고용 보관 권장 |
| `.claude/state/backlog.json` | 백로그 + Task 이력 | 참고용 보관 권장 |
| `.claude/state/completed.json` | 완료 이력 | 참고용 보관 권장 |
| `.claude/temp/` | 임시 파일 | 안전하게 삭제 가능 |
| `CLAUDE.md` | 생성된 프로젝트 지침 | 프로젝트 문서로 보관 가능 |
| `docs/requirements/` | 요구사항 문서 | 삭제 금지 (프로젝트 산출물) |
| `docs/retro/` | 회고 리포트 | 삭제 금지 (프로젝트 산출물) |
| `docs/reports/` | 메트릭 리포트 | 삭제 금지 (프로젝트 산출물) |

## 제거 절차

### 1. 현재 작업 완료

모든 in_progress Task를 done 또는 todo로 변경하고, 열린 PR을 머지 또는 닫습니다.

```bash
/skill-status  # 진행 중인 작업 확인
```

### 2. 상태 파일 백업 (선택)

```bash
mkdir -p .archive/ai-crew-kit
cp .claude/state/*.json .archive/ai-crew-kit/
cp CLAUDE.md .archive/ai-crew-kit/
```

### 3. 프레임워크 파일 삭제

```bash
rm -rf .claude/skills .claude/domains .claude/templates
rm -rf .claude/agents .claude/schemas .claude/workflows
rm -rf .claude/docs .claude/temp
```

### 4. 선택적 정리

```bash
# 상태 파일도 삭제하는 경우
rm -rf .claude/state

# CLAUDE.md 삭제하는 경우
rm CLAUDE.md

# 빈 .claude 디렉토리 삭제
rmdir .claude 2>/dev/null
```

### 5. 제거 후 수동 관리 체크리스트

프레임워크가 자동화하던 것을 직접 관리해야 합니다:

- [ ] **코드 리뷰**: GitHub/GitLab 자체 리뷰 기능으로 대체
- [ ] **빌드/테스트 게이트**: CI/CD 파이프라인에 직접 설정
- [ ] **코딩 컨벤션**: ESLint/Prettier/ktlint 등 린트 설정으로 대체
- [ ] **백로그 관리**: Jira/Linear/GitHub Issues 등 외부 도구로 이전
- [ ] **PR 크기 제한**: GitHub Actions 등으로 라인 수 체크 설정
- [ ] **보안 체크**: SonarQube/Snyk 등 보안 도구 도입

## 부분 제거

프레임워크의 일부만 유지하고 싶다면:

| 유지할 기능 | 필요 파일 |
|-----------|----------|
| Claude Code 기본 지침 | `CLAUDE.md`만 유지 |
| 도메인 참고자료 | `.claude/domains/{선택한 도메인}/` 유지 |
| 코딩 컨벤션 | `.claude/domains/_base/conventions/` 유지 |
