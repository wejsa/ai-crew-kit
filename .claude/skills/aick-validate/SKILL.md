---
name: aick-validate
description: 프레임워크 검증 - 업그레이드 후 구조 무결성 자체 검증. aick-upgrade에서 자동 호출되거나 /aick-validate로 호출합니다.
disable-model-invocation: true
allowed-tools: Bash(cat:*), Bash(ls:*), Bash(python3:*), Read, Glob, Grep
argument-hint: "[--fix]"
complexity-hint: light
---

# aick-validate: 프레임워크 검증

## 실행 조건
- `aick-upgrade` 완료 후 자동 호출
- 또는 사용자가 `/aick-validate` 직접 호출

## 옵션
```
/aick-validate          # 검증만 수행 (읽기 전용)
/aick-validate --fix    # 자동 수정 가능한 항목 수정
```

## 검증 항목

### Category 1: [REQUIRED] 구조 검증

**1. SKILL.md YAML 프론트매터**
모든 `.claude/skills/*/SKILL.md` 순회:
- `---` 시작/종료 마커, `name`/`description` 필드 존재, YAML 파싱 가능
- `complexity-hint` 필드가 존재하면 값이 `heavy|medium|light` 중 하나인지 검증 (optional 필드, 없어도 통과). 잘못된 값 → WARNING

**2. 모든 JSON 파일 유효성**
`.claude/` 하위 모든 `.json` 파싱 검증:
- schemas, migrations.json, state/*.json
- **인스턴스 스키마 검증 (권장, v4.4.0)**: `check-jsonschema`/python `jsonschema` 설치 시 `state/backlog.json`을 `schemas/backlog.schema.json`으로, `state/project.json`을 `project.schema.json`으로 직접 검증한다. 파싱 통과만으로는 `additionalProperties:false`·enum·숫자범위 위반을 못 잡으므로(런타임 sleeper 클래스), validator가 있으면 인스턴스 검증까지 수행. 미설치 시 파싱 검증으로 폴백하고 그 사실을 INFO로 안내. 상세 항목별 진단은 `/aick-health-check` SI-04 참조.

**3. 템플릿 마커 완결성**
`${CLAUDE_PLUGIN_ROOT}/.claude/templates/*.tmpl` (clone/seed면 `.claude/templates/*.tmpl`) 마커가 TEMPLATE-ENGINE.md에 정의돼 있는지:
- 사용됐으나 미정의 → WARNING, 정의됐으나 미사용 → INFO

### Category 2: [IMPORTANT] 참조 검증

**4. 스킬 간 교차 참조**
SKILL.md에서 참조하는 스킬/에이전트 파일 존재 확인

**5. 스키마 파일**
project.schema.json, backlog.schema.json → JSON Schema Draft-07 호환.
migrations.json → 유효 JSON + 필수 구조.

**5.5 상태 타임스탬프 형식 (v4.8.0)**
`state/backlog.json` 모든 Task의 시각 필드(`assignedAt`·`lockedAt`·`planApprovedAt`·`createdAt`·`updatedAt`·`completedAt`·`pausedAt`·`mergedAt`)를 jq `fromdateiso8601` 파싱 시뮬레이션으로 검사 — null이 아닌데 파싱 불가(예: 시간 없는 `"2026-06-12"`)면 WARNING + Task ID·필드·현재 값 출력. 만료 판정(stop.sh·aick-plan 0.5·aick-impl 잠금 정리)은 파싱 불가 타임스탬프를 **만료로 취급하지 않으므로**(v4.8.0, M002 — 거짓 만료 방지), 교정 전까지 해당 잠금은 자동 만료되지 않는다 → `--fix` 안내.

### Category 3: [OPTIONAL] 확장 검증

**6. 워크플로우 YAML**
필수 필드 `name`/`steps`, 각 step에 `name`/`skill`, 참조 스킬 존재

**7. 커스텀 스킬 매니페스트**
`.claude/skills/custom/*/SKILL.md` 존재 + 프론트매터 유효성 + CLAUDE.md 등록 여부(WARNING) + 빌트인 이름 충돌(ERROR). 접두사 무관 검사 — 신규 `aick-` + 구 `crew-`(v4.0~4.5)·`skill-`(v4.0 이전) 접두사 커스텀 스킬 모두 커버(customSkills 스키마가 둘 다 허용하므로 검증 누락 방지).

## 출력

필수 포함: 카테고리별 PASS/WARN/FAIL 수 요약 테이블, 전체 결과(PASS/FAIL + 총 통과/경고/실패 수), 경고·실패 상세, 수정 방법 안내

## --fix 모드

자동 수정 가능: metadata.version 누락 → 기본값 1
타임스탬프 형식 오류 (v4.8.0, 검증 5.5 — 잠금 만료에 관여하는 필드만):
- `lockedAt` 파싱 불가 → 현재 시각(ISO 8601) — 가변 하트비트라 안전
- `assignedAt` 파싱 불가 → 현재 시각 + 경고 — 원칙적으로 불변 필드이나 손상 값은 복원 불가, TTL은 교정 시점부터 재기산됨을 명시
- `planApprovedAt` 파싱 불가 → `null` — 승인 기록 손상은 보수적으로 무효화(aick-plan 재승인 강제)
- 그 외 이력 필드(`createdAt`·`completedAt` 등) 파싱 불가 → 자동 수정 불가, 경고만(원본 값 추정 불가·만료 판정 무관)
- 수정 시 `metadata.version` 1 증가 + `aick-backlog` 쓰기 프로토콜 준수
자동 수정 불가 (수동): JSON 문법 오류, YAML 프론트매터 오류, 누락 파일

## 주의사항
- 기본 모드는 읽기 전용 (파일 수정 없음)
- `--fix`는 안전한 항목만 수정
- 검증 실패가 프레임워크 동작을 차단하지는 않음 (경고 성격)
