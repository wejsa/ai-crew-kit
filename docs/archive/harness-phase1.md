# ai-crew-kit v1.34.0 구현 계획서

> **목표**: SKILL.md 기반 코드베이스 건강 검진 시스템 (Garbage Collection Phase 1)
> **버전**: v1.33.1 → v1.34.0
> **예상 작업량**: 반나절
> **설계 원칙**: JSON 규칙 엔진 없이 SKILL.md 단일 형식. 기존 체크리스트/skill-validate와 두벌 관리 금지.

---

## 설계 결정 기록

### 왜 JSON 규칙 엔진을 도입하지 않는가

ai-crew-kit은 별도 런타임이 없는 프롬프트 기반 시스템이다. JSON 규칙 파일을 만들어도 Claude가 SKILL.md를 읽고 JSON을 해석하여 실행하는 구조이므로, **SKILL.md 자체가 이 프레임워크의 선언적 엔진**이다.

| 버린 것 | 이유 |
|---------|------|
| `*.rules.json` 27개 규칙 파일 | 체크리스트(.md)와 의미적 중복. 두벌 관리 |
| `health-rule.schema.json` | 규칙 파일이 없으므로 불필요 |
| verification 타입 8종 JSON 형식화 | SKILL.md에 자연어로 기술하면 Claude가 맥락적으로 판단. techStack 분기도 자동 |
| skill-validate와 중복되는 5개 규칙 | 이미 구현됨 (레지스트리 정합성, JSON 유효성, 워크플로우 참조 등) |

| 유지하는 것 | 이유 |
|------------|------|
| 점수 체계 (0-100) + 등급 | 기존 어디에도 없는 정량적 평가 |
| health-history.json 이력 추적 | 추세 파악 → 조기 경고 |
| Post-merge drift gate | 머지 후 자동 검증 |
| 도메인별 카테고리 가중치 (`_category.json`) | Layered Override 패턴 활용 |
| 코드↔문서 교차 검증 | skill-validate가 커버하지 않는 영역 |

### 기존 도구와의 역할 분리

```
Tier 1: /skill-status --health     → 운영 준비 확인 (5초, 매일)
         "JSON 깨진 거 없나? orphan intent 있나?"

Tier 2: /skill-health-check        → 코드베이스 심층 검진 (30초~, 주 1회 또는 릴리스 전)
         "코드와 문서가 동기화돼 있나? 상태 파일 정합성은?"

Tier 3: /skill-validate            → 프레임워크 구조 무결성 (업그레이드 후 자동)
         "SKILL.md 프론트매터 맞나? 스키마 호환되나?"

별도축: /skill-report              → 프로세스 메트릭 (프로젝트 건강도 ≠ 코드 건강도)
         "블록 Task 있나? Stale 워크플로우 있나?"
```

체크리스트(`.md`)는 PR 리뷰 시 AI 리뷰어가 참조하는 **설계 원칙/가이드라인**으로 유지.
skill-health-check는 체크리스트 중 **자동 탐지 가능한 항목만** 코드 스캔으로 사전 검증.
같은 내용을 JSON으로 다시 정의하지 않는다.

---

## 릴리스 범위

| 포함 | 미포함 (v1.35.0+) |
|------|-------------------|
| `/skill-health-check` SKILL.md 기반 검진 | `agent-gc` 자동 정리 에이전트 |
| 4개 _base 카테고리 + fintech compliance 확장 | cron 기반 주기적 자동 실행 |
| 점수(0-100) + 등급 + health-history.json | ecommerce 도메인 검사 항목 |
| `/skill-merge-pr` drift gate | 자동 정리 PR 생성 |
| 검증 도구 선택 가이드 + 에스컬레이션 체인 | |

---

## 사전 조건

- ai-crew-kit v1.33.1 (현재 develop 브랜치)
- Claude Code CLI 설치 완료

---

## 전체 구현 순서 (6 스텝)

```
Step 1: 카테고리 가중치 파일 생성 (_category.json)
Step 2: health-history.schema.json + project.schema.json 확장
Step 3: skill-health-check SKILL.md 작성 (핵심)
Step 4: skill-merge-pr drift gate 추가
Step 5: 기존 스킬 연동 (skill-status 에스컬레이션, skill-release 게이트)
Step 6: 문서 업데이트 (README, skill-reference, CHANGELOG, VERSION)
```

---

## 신규/수정 파일 목록

### 신규 (4개)

| # | 파일 | 설명 |
|---|------|------|
| 1 | `.claude/domains/_base/health/_category.json` | 기본 4개 카테고리 + 점수 설정 |
| 2 | `.claude/domains/fintech/health/_category.json` | compliance 추가 + 가중치 재조정 |
| 3 | `.claude/schemas/health-history.schema.json` | 검사 이력 스키마 |
| 4 | `.claude/skills/skill-health-check/SKILL.md` | 엔진 동작 명세 (핵심) |

### 수정 (7개)

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `.claude/schemas/project.schema.json` | healthCheck 설정 필드 추가 |
| 2 | `.claude/skills/skill-merge-pr/SKILL.md` | Post-Merge Health Gate 섹션 추가 |
| 3 | `.claude/skills/skill-status/SKILL.md` | 에스컬레이션 안내 1줄 추가 |
| 4 | `docs/skill-reference.md` | 명령어 추가 + 검증 도구 선택 가이드 |
| 5 | `README.md` | 버전 + 건강 검진 섹션 |
| 6 | `CHANGELOG.md` | v1.34.0 항목 추가 |
| 7 | `VERSION` | 1.33.1 → 1.34.0 |

**합계: 11개** (이전 계획 17개에서 35% 감소)

---

## Step 1: 카테고리 가중치 파일 생성

카테고리 가중치만 JSON으로 분리하는 이유: Layered Override 패턴 (`_base` → `{domain}`)을 활용하기 위해서다.
검증 규칙 자체는 SKILL.md에 기술한다.

### 1-1. _base 카테고리

#### 프롬프트

```
.claude/domains/_base/health/_category.json을 생성해줘.

{
  "description": "코드베이스 건강 검진 카테고리 정의 (_base)",
  "categories": [
    {
      "id": "doc-sync",
      "name": "문서 ↔ 코드 동기화",
      "description": "에이전트가 참조하는 문서와 실제 코드의 일치 여부",
      "weight": 35,
      "failCap": 50
    },
    {
      "id": "state-integrity",
      "name": "상태 파일 정합성",
      "description": "backlog.json 등 상태 파일과 Git 현실의 일치 여부",
      "weight": 25,
      "failCap": 50
    },
    {
      "id": "security",
      "name": "기본 보안",
      "description": "민감정보 노출, SQL Injection, CORS, 인증 등 기본 보안 검사",
      "weight": 25,
      "failCap": 40
    },
    {
      "id": "agent-config",
      "name": "에이전트 설정 유효성",
      "description": "에이전트 정의, 스킬 파일의 구성 유효성",
      "weight": 15,
      "failCap": 70
    }
  ],
  "scoring": {
    "gradeThresholds": {
      "HEALTHY": 90,
      "NEEDS_ATTENTION": 70,
      "AT_RISK": 50,
      "CRITICAL": 0
    },
    "severityWeights": { "CRITICAL": 3, "MAJOR": 2, "MINOR": 1 },
    "criticalFailCap": true
  }
}
```

### 1-2. fintech 카테고리 확장

#### 프롬프트

```
.claude/domains/fintech/health/_category.json을 생성해줘.

{
  "description": "fintech 도메인 카테고리 확장",
  "additionalCategories": [
    {
      "id": "compliance",
      "name": "컴플라이언스 준수",
      "description": "PCI-DSS, 전자금융감독규정 등 금융 규제 준수 여부",
      "weight": 40,
      "failCap": 30
    }
  ],
  "weightOverrides": {
    "doc-sync": 20,
    "state-integrity": 15,
    "security": 15,
    "agent-config": 10
  }
}

총합: compliance(40) + doc-sync(20) + state-integrity(15) + security(15) + agent-config(10) = 100
```

### 검증

```bash
python3 -m json.tool .claude/domains/_base/health/_category.json > /dev/null && echo "✅ base"
python3 -m json.tool .claude/domains/fintech/health/_category.json > /dev/null && echo "✅ fintech"
```

---

## Step 2: 스키마 정의

### 2-1. health-history.schema.json

#### 프롬프트

```
.claude/schemas/health-history.schema.json을 생성해줘.

{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Health Check History",
  "description": "skill-health-check 실행 이력 스키마",
  "type": "object",
  "required": ["version", "history"],
  "properties": {
    "version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
    "history": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["timestamp", "domain", "score", "grade", "categories", "mode"],
        "properties": {
          "timestamp": { "type": "string", "format": "date-time" },
          "domain": { "type": "string" },
          "score": { "type": "number", "minimum": 0, "maximum": 100 },
          "grade": { "type": "string", "enum": ["HEALTHY", "NEEDS_ATTENTION", "AT_RISK", "CRITICAL"] },
          "categories": {
            "type": "object",
            "additionalProperties": {
              "type": "object",
              "required": ["score", "pass", "fail", "skip"],
              "properties": {
                "score": { "type": "number" },
                "pass": { "type": "integer" },
                "fail": { "type": "integer" },
                "skip": { "type": "integer" },
                "error": { "type": "integer", "default": 0 }
              }
            }
          },
          "criticalFails": { "type": "array", "items": { "type": "string" } },
          "fixesApplied": { "type": "array", "items": { "type": "string" } },
          "mode": { "type": "string" }
        }
      }
    }
  }
}
```

### 2-2. project.schema.json에 healthCheck 필드 추가

#### 프롬프트

```
기존 .claude/schemas/project.schema.json의 properties에 healthCheck 필드를 추가해줘.
기존 필드는 절대 수정하지 마라. additionalProperties: false가 최상위에 있으므로
properties에 추가해야 한다.

"healthCheck": {
  "type": "object",
  "description": "건강 검진 설정 (/skill-health-check)",
  "properties": {
    "exclude": {
      "type": "array",
      "items": { "type": "string" },
      "description": "비활성화할 검사 항목 ID 목록"
    },
    "thresholds": {
      "type": "object",
      "properties": {
        "criticalMinScore": { "type": "integer", "default": 70 },
        "autoBacklogSeverity": { "type": "string", "enum": ["CRITICAL", "MAJOR"], "default": "CRITICAL" }
      },
      "additionalProperties": false
    },
    "schedule": {
      "type": "object",
      "properties": {
        "recommendedFrequency": { "type": "string", "default": "weekly" },
        "autoRunOnMerge": { "type": "boolean", "default": true }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

### 검증

```bash
python3 -m json.tool .claude/schemas/health-history.schema.json > /dev/null && echo "✅"
python3 -m json.tool .claude/schemas/project.schema.json > /dev/null && echo "✅"
python3 -c "import json; d=json.load(open('.claude/schemas/project.schema.json')); print('healthCheck' in d['properties'])"
```

---

## Step 3: skill-health-check SKILL.md 작성 (핵심)

### 프롬프트

```
.claude/skills/skill-health-check/SKILL.md를 생성해줘.

이 파일이 /skill-health-check 커맨드의 전체 동작 명세다.
별도 JSON 규칙 파일 없이, 이 SKILL.md 하나가 엔진이다.

---
name: skill-health-check
description: 코드베이스 건강 검진 - 문서↔코드 동기화, 상태 정합성, 기본 보안, 에이전트 설정, 도메인 컴플라이언스 검증. 사용자가 "건강 검진해줘", "헬스체크해줘" 또는 /skill-health-check를 요청할 때 사용합니다.
disable-model-invocation: false
allowed-tools: Bash(git:*), Bash(grep:*), Bash(find:*), Bash(python3:*), Read, Glob, Grep, Write
argument-hint: "[--quick|--scope <category>|--fix]"
---

# skill-health-check: 코드베이스 건강 검진

## 실행 조건
- /skill-health-check 또는 "건강 검진해줘", "전체 검진해줘", "헬스체크 돌려줘"

## 기존 도구와의 관계
- /skill-status --health: 운영 준비 경량 점검 (JSON 유효성, orphan intent). 매일 사용.
- /skill-health-check (이 스킬): 코드↔문서 동기화, 상태 정합성 심층 검진. 주 1회 또는 릴리스 전.
- /skill-validate: 프레임워크 구조 무결성. 업그레이드 후 자동 호출.
- 이 스킬은 skill-validate와 중복 검사하지 않는다. 각자 고유 영역만 담당.

## 명령어 옵션
| 모드 | 명령어 | 설명 |
|------|--------|------|
| 전체 검사 | /skill-health-check | 전체 실행 |
| 빠른 검사 | /skill-health-check --quick | CRITICAL 항목만 |
| 영역 지정 | /skill-health-check --scope doc-sync | 특정 카테고리만 |
| 자동 수정 | /skill-health-check --fix | autoFix 가능 항목 즉시 반영 |

## 실행 절차

### Phase A: 설정 로딩
1. .claude/state/project.json에서 현재 도메인과 techStack 확인
   - project.json이 없으면 도메인 "general", techStack 미설정으로 간주
2. .claude/domains/_base/health/_category.json 로딩
3. .claude/domains/{domain}/health/_category.json 로딩 (있으면 병합)
   - additionalCategories → 추가
   - weightOverrides → 기존 카테고리 가중치 조정
   - 최종 가중치 합 100으로 정규화
4. project.json의 healthCheck.exclude에 있는 항목 ID 제외
5. --scope 옵션이 있으면 해당 카테고리만 필터
6. --quick 옵션이 있으면 severity: CRITICAL만 필터

### Phase B: 검사 실행
아래 "검사 항목" 섹션의 각 항목에 대해:
1. 사전 조건 확인 → 미충족 시 SKIP
2. 검사 실행
3. 결과: PASS | FAIL | SKIP | ERROR
4. FAIL인 항목에 대해:
   - backlog 등록 대상이면 backlog.json에 Task 등록
   - --fix 모드이고 autoFix 가능하면 자동 수정 실행 (confirm 필요 시 AskUserQuestion)

### Phase C: 점수 계산
1. 카테고리별 점수 = (PASS 수 / (PASS + FAIL + ERROR 수)) × 100
   - SKIP은 분모에서 제외
   - 해당 카테고리에 CRITICAL FAIL이 하나라도 있으면 점수 상한 = failCap
2. 전체 점수 = Σ(카테고리 점수 × 가중치) / Σ(가중치)
3. 등급 판정: _category.json의 gradeThresholds 참조

### Phase D: 리포트 생성
1. 콘솔 출력 (아래 형식 참조)
2. .claude/state/health-history.json에 결과 누적
   - 파일이 없으면 초기 구조 자동 생성: {"version": "1.0.0", "history": []}
   - .claude/state/ 디렉토리가 없으면 mkdir -p로 생성
   - 이전 기록 대비 변화량 표시
   - 3회 연속 FAIL인 항목은 severity 자동 상향 제안
3. health-history.json 기록은 항상 마지막에 수행 (중간 실패해도 기존 이력 보존)

### 콘솔 출력 형식

╔════════════════════════════════════════╗
║        🏥 Health Check Report          ║
║        {timestamp}                     ║
╠════════════════════════════════════════╣
║  Overall Score: {score}/100  {grade}   ║
║                                        ║
║  {category1}  {bar}  {percent}%        ║
║  {category2}  {bar}  {percent}%        ║
║  ...                                   ║
╠════════════════════════════════════════╣
║  CRITICAL: {n}건  MAJOR: {n}건         ║
╠════════════════════════════════════════╣
║  🔴 {항목ID} {항목명}                  ║
║     {상세 설명}                        ║
║  ...                                   ║
╚════════════════════════════════════════╝

이전 기록 대비:
  📈 Score: {이전}점 → {현재}점 (+{차이})
  ✅ 해결: {해결된 항목 목록}
  🆕 신규: {새로 발견된 항목 목록}

---

## 검사 항목

### 카테고리: doc-sync (문서 ↔ 코드 동기화)

#### DS-01. 빌드 명령어 실행 (CRITICAL)
- 사전 조건: CLAUDE.md 존재
- 검사: CLAUDE.md의 Build/빌드 섹션에서 코드 블록 추출 → 실행 → exit code 확인
- timeout: 120초. 초과 시 ERROR.
- FAIL 시: backlog 자동 등록 (CRITICAL bugfix)
- autoFix: 불가

#### DS-02. 테스트 명령어 실행 (CRITICAL)
- 사전 조건: CLAUDE.md 존재
- 검사: CLAUDE.md의 Test/테스트 섹션에서 코드 블록 추출 → 실행 → exit code 확인
- timeout: 180초
- FAIL 시: backlog 자동 등록
- autoFix: 불가

#### DS-03. 기술 스택 정합성 (MAJOR)
- 사전 조건: .claude/state/project.json 존재
- 검사: project.json의 techStack vs 실제 의존성 파일 대조
  - 탐지 대상: build.gradle.kts, build.gradle, pom.xml, package.json, requirements.txt, go.mod
  - techStack에 "spring-boot-kotlin"이지만 build.gradle이 없으면 FAIL
  - 반대로 package.json이 있는데 techStack이 "nodejs"가 아니면 FAIL
- autoFix: project.json 업데이트 가능 (confirm: true)

#### DS-04. 환경변수 동기화 (MAJOR)
- 사전 조건: CLAUDE.md 존재
- 검사: 코드 내 환경변수 참조 패턴 vs CLAUDE.md 환경변수 섹션
  - 패턴: @Value("${...}"), process.env.XXX, os.environ["XXX"], os.Getenv("XXX")
  - 코드에만 있고 문서에 없는 환경변수 → FAIL
  - spring.*, server.* 프레임워크 기본값은 무시
  - techStack에 따라 적절한 패턴 사용 (Claude가 맥락 판단)
- autoFix: 불가 (수동 문서 업데이트 필요)

#### DS-05. 패키지 구조 동기화 (MAJOR)
- 사전 조건: CLAUDE.md 존재 + src/ 디렉토리 존재
- 검사: CLAUDE.md 패키지 구조 섹션 vs 실제 파일시스템
  - phantom path (문서에만 존재) → MAJOR
  - undocumented path (코드에만 존재, 주요 디렉토리) → MINOR
- autoFix: CLAUDE.md 구조 섹션 재생성 가능 (confirm: true)

#### DS-06. CLAUDE.md 신선도 (MINOR)
- 사전 조건: CLAUDE.md 존재
- 검사: CLAUDE.md 마지막 수정일 이후 src/ 변경 커밋 수 카운트
  - 30건 이상이면 "문서가 오래됨" 판정 → FAIL
- autoFix: 불가 (CLAUDE.md 재생성 안내만)

#### DS-07. 요구사항 문서 존재 (MINOR)
- 사전 조건: .claude/state/completed.json 존재
- 검사: 완료된 feature Task에 대응하는 docs/requirements/ 파일 존재 확인
  - 파일명에 Task ID가 포함되어야 함
- autoFix: 불가

### 카테고리: state-integrity (상태 파일 정합성)

#### SI-01. 고아 브랜치 탐지 (MAJOR)
- 사전 조건: .claude/state/backlog.json 존재
- 검사: feature/* 또는 {taskPrefix}-* 브랜치 중 backlog.json에 없는 것
- autoFix: 사용자 확인 후 고아 브랜치 삭제 (confirm: true)

#### SI-02. 고아 Task 탐지 (MAJOR)
- 사전 조건: .claude/state/backlog.json 존재
- 검사: in_progress 상태 Task 중 대응 브랜치가 없는 것
  - 주의: skill-status --health의 orphan intent 점검과는 다른 대상
- autoFix: status를 'ready'로 리셋 (confirm: true)

#### SI-03. 잠금 만료 탐지 (MINOR)
- 사전 조건: .claude/state/backlog.json 존재
- 검사: lockedBy 필드가 있는 Task 중 lockedAt이 1시간 이상 경과한 것
- autoFix: 자동 잠금 해제 (confirm: false — TTL 초과는 명백한 비정상)

#### SI-04. backlog 내부 논리 검증 (MAJOR)
- 사전 조건: .claude/state/backlog.json 존재
- 검사:
  - 중복 Task ID 존재 여부
  - 의존성(dependsOn) 참조가 실제 존재하는 Task ID인지
  - 순환 의존성 여부
  - status 값이 허용된 enum인지 (todo, in_progress, done, blocked)
- FAIL 시: backlog 자동 등록
- autoFix: 불가 (수동 수정 안내)

#### SI-05. 에이전트 파일 정합성 (CRITICAL)
- 사전 조건: .claude/state/project.json 존재
- 검사: project.json의 agents.enabled 목록 vs .claude/agents/agent-*.md 파일 존재 대조
  - 주의: 필드명은 agents.enabled (agents.active 아님)
  - enabled에 있으나 파일 없음 → CRITICAL
  - 파일 있으나 enabled에 없음 → MINOR (정보 제공)
- FAIL 시: backlog 자동 등록
- autoFix: 불가

### 카테고리: agent-config (에이전트 설정 유효성)

#### AC-01. 활성 도메인 유효성 (CRITICAL)
- 사전 조건: .claude/state/project.json 존재
- 검사: project.json의 domain 값이 _registry.json에 등록되어 있는지
  - 주의: 이 항목은 skill-validate Cat 1-3에서도 유사하게 점검됨.
    skill-validate는 "구조적 존재"를, 이 항목은 "런타임 설정 유효성"을 확인.
    skill-validate를 최근 실행했다면 SKIP 가능.
- FAIL 시: backlog 자동 등록
- autoFix: 불가

#### AC-02. 스킬 SKILL.md 본문 완전성 (MINOR)
- 사전 조건: 없음 (항상 실행)
- 검사: .claude/skills/*/SKILL.md에 필수 섹션 존재 확인
  - 필수: "실행 조건" 또는 "트리거", "실행 플로우" 또는 "워크플로우" 또는 "절차"
  - 주의: skill-validate는 YAML 프론트매터만 검증. 이 항목은 본문 구조를 검증.
- autoFix: 불가

### 카테고리: security (기본 보안 — 전체 도메인 공통)

아래 항목들은 모든 도메인에서 실행된다.
검사 대상 파일 패턴은 techStack에 따라 Claude가 맥락적으로 결정한다:
- spring-boot-kotlin/java: src/**/*.{kt,java}
- nodejs-typescript: src/**/*.{ts,js}
- go: **/*.go
- 해당 패턴에 매칭되는 파일이 0건이면 SKIP

#### SEC-01. 민감정보 로깅 금지 (CRITICAL)
- 검사: 로그 출력문에서 민감정보 패턴 탐지 (하나라도 매칭되면 FAIL)
  - 패턴: log.*password, log.*cardNumber, log.*creditCard, log.*cvv,
    log.*ssn, log.*주민등록, logger.*secret, println.*password
  - FAIL 시 매칭 위치를 리포트에 포함
- 참조: _base/checklists/security-basic.md "로깅 금지"
- FAIL 시: backlog 자동 등록
- autoFix: 불가 (보안 관련은 수동 수정 필수)

#### SEC-02. SQL Injection 위험 (CRITICAL)
- 검사: MyBatis XML에서 안전하지 않은 파라미터 바인딩 탐지
  - 사전 조건: src/**/*.xml 파일 존재 (MyBatis 사용 프로젝트)
  - 패턴: ${...} 중 #{...}가 아닌 것
  - tableName, columnName, orderBy 관련은 제외 (동적 바인딩 허용)
  - 매칭 위치 리포트 포함
- 참조: _base/checklists/security-basic.md "SQL Injection"
- FAIL 시: backlog 자동 등록

#### SEC-03. CORS 설정 (MAJOR)
- 검사: CORS에서 allowedOrigins("*") 사용 금지
  - 패턴: allowedOrigins("*"), Access-Control-Allow-Origin: *
  - 매칭 위치 리포트 포함
- 참조: _base/checklists/security-basic.md "입력 검증" + 해당 도메인 security 체크리스트

#### SEC-04. API 인증 (MAJOR)
- 검사: Controller에 인증 관련 어노테이션 존재 확인
  - Kotlin/Java: @PreAuthorize, @Secured, @RolesAllowed, @AuthenticationPrincipal
  - TypeScript: @UseGuards, @Auth, authMiddleware
  - Go: middleware.Auth, authRequired
  - 예외: *Health*Controller, *Public*Controller (헬스체크, 공개 API)
  - 대상 파일 각각에 존재해야 PASS (each scope)
- 참조: _base/checklists/security-basic.md "인증 필수"

### 카테고리: compliance (도메인 조건부 — fintech만 해당)

아래 항목들은 project.json의 domain이 "fintech"일 때만 실행된다.
파일 패턴 규칙은 security 카테고리와 동일 (techStack 맥락 판단, 0건이면 SKIP).

#### FIN-01. 감사 로그 존재 (CRITICAL)
- 검사: 코드에서 감사 로그 어노테이션/서비스 패턴 탐지
  - Kotlin/Java: @AuditLog, @Audited, AuditEvent, auditService
  - TypeScript: @AuditLog, auditLogger, audit.log
  - 하나라도 있으면 PASS (any scope)
- 참조: fintech/checklists/compliance.md "감사 추적" 항목의 자동화 사전 검증
- FAIL 시: backlog 자동 등록

#### FIN-02. 멱등성 키 (MAJOR)
- 검사: 결제 관련 Controller에 멱등성 키 파라미터 존재 확인
  - 대상 파일: *Payment*Controller*, *Order*Controller* 등 (techStack 맥락 판단)
  - 패턴: idempotencyKey, idempotency-key, Idempotent, X-Idempotency-Key
  - 대상 파일이 없으면 SKIP
  - 대상 파일 각각에 패턴이 존재해야 PASS (each scope)
- 참조: fintech/checklists/domain-logic.md "멱등성 키 필수"

#### FIN-03. 금액 정밀도 (MAJOR)
- 검사: 금액 관련 변수에 Double/Float 사용 금지
  - 패턴: Double.*amount, Float.*amount, double.*price, float.*price
  - domain 모델 파일 대상 (techStack 맥락 판단)
  - 하나라도 매칭되면 FAIL, 매칭 위치 리포트 포함
- 참조: fintech/checklists/domain-logic.md "BigDecimal 필수"

#### FIN-04. 트랜잭션 관리 (MAJOR)
- 검사: 결제 서비스에 트랜잭션 관리 존재 확인
  - Kotlin/Java: @Transactional, transactionTemplate, TransactionStatus
  - TypeScript: transaction, beginTransaction, prisma.$transaction
  - 대상: *Payment*Service* 등 (techStack 맥락 판단)
  - 대상 파일이 없으면 SKIP

## 중요 규칙

- command_run(DS-01, DS-02)에서 프로덕션 DB에 접속하는 명령어는 실행하지 마라.
- autoFix에서 confirm: true인 항목은 반드시 AskUserQuestion으로 사용자 승인을 받아라.
- security/compliance 항목의 grep 대상 파일 패턴은 techStack에 따라 Claude가 판단한다.
  SKILL.md에 모든 언어 패턴을 열거하지 않는다. Claude가 project.json의 techStack을 보고 적절한 파일 확장자와 패턴을 선택한다.
- security 카테고리(SEC-*)는 모든 도메인에서 실행된다. compliance 카테고리(FIN-*)는 fintech에서만 실행된다.
- 이 스킬은 체크리스트(.md)를 대체하지 않는다. 체크리스트는 PR 리뷰용 설계 원칙이고,
  이 스킬은 코드 패턴의 자동 사전 탐지다. "참조" 필드로 관련 체크리스트 항목을 연결한다.

## 실행 로그
execution-log.json에 기록:
- action: "health_check_started" | "health_check_completed"
- details: { mode, score, grade, criticalCount, fixCount }
```

### 검증

```bash
wc -l .claude/skills/skill-health-check/SKILL.md
head -20 .claude/skills/skill-health-check/SKILL.md
```

---

## Step 4: skill-merge-pr drift gate 추가

### 프롬프트

```
기존 .claude/skills/skill-merge-pr/SKILL.md를 수정해줘.

"3. 로컬 동기화"와 "4. 상태 업데이트" 사이에 다음 섹션을 추가:

### 3.5 Post-Merge Health Gate

project.json의 healthCheck.autoRunOnMerge로 제어 (기본값: true. false 시 스킵).
project.json이 없으면 스킵.

1. /skill-health-check --quick 자동 실행
2. 결과 확인:
   - 모든 CRITICAL PASS → 정상 진행
   - CRITICAL FAIL → WARNING 출력:
     "⚠️ 머지 후 health check에서 CRITICAL 이슈 발견: {이슈 목록}"
     "즉시 수정 필요. /skill-health-check로 상세 확인하세요."
   - WARNING은 머지를 롤백하지 않음 (이미 완료). 알림만 제공.
3. 점수 추세 확인 (health-history.json이 있고 이전 기록이 있으면):
   - 10점 이상 하락 → "📉 Health score가 {이전}점 → {현재}점으로 하락했습니다."

기존 내용은 수정하지 말고 추가만 해줘.
```

### 검증

```bash
grep -n "Health Gate\|health-check\|drift" .claude/skills/skill-merge-pr/SKILL.md
```

---

## Step 5: 기존 스킬 연동

### 5-1. skill-status 에스컬레이션 안내

#### 프롬프트

```
.claude/skills/skill-status/SKILL.md의 "5.5 시스템 건강 점검 (--health)" 섹션 끝에
다음을 추가해줘:

#### 에스컬레이션 안내
점검 결과에서 3개 이상 경고가 발견되면 출력 하단에 안내:
"💡 심층 검진이 필요할 수 있습니다: /skill-health-check"

기존 내용은 수정하지 마라.
```

### 5-2. skill-release 게이트 (선택)

#### 프롬프트

```
.claude/skills/skill-release/SKILL.md의 사전 조건 목록 끝에 다음을 추가해줘:

8. Health Gate (선택): project.json에 healthCheck 설정이 있으면
   /skill-health-check --quick 실행. CRITICAL 0건이어야 진행.
   healthCheck 설정이 없거나 실패 시에도 AskUserQuestion으로 계속 여부 확인.
   (릴리스를 차단하지 않음 — 사용자 판단에 맡김)

기존 내용은 수정하지 마라.
```

### 검증

```bash
grep -n "에스컬레이션\|health-check\|Health Gate" .claude/skills/skill-status/SKILL.md .claude/skills/skill-release/SKILL.md
```

---

## Step 6: 문서 업데이트 및 버전 태깅

### 6-1. docs/skill-reference.md

#### 프롬프트

```
docs/skill-reference.md를 수정해줘.

1. "자주 사용하는 명령어" 테이블에 추가:
| `/skill-health-check` | 코드베이스 건강 검진 | "건강 검진해줘" |

2. "프로젝트 관리" 섹션 테이블에 추가 (/skill-status 행 아래):
| `/skill-health-check` | 코드베이스 건강 검진 (점수 + 등급) |
| `/skill-health-check --quick` | CRITICAL 항목만 빠른 검사 |
| `/skill-health-check --scope {카테고리}` | 특정 카테고리만 검사 |
| `/skill-health-check --fix` | 자동 수정 포함 검사 |

3. 파일 끝에 새 섹션 추가:

### 어떤 검증 도구를 사용해야 하나요?

| 상황 | 명령어 | 소요 시간 |
|------|--------|----------|
| 매일 세션 시작할 때 | `/skill-status --health` | ~5초 |
| "뭔가 이상한데?" 싶을 때 | `/skill-health-check --quick` | ~15초 |
| 릴리스 전 전수 점검 | `/skill-health-check` | ~30초 |
| 프레임워크 업그레이드 후 | `/skill-validate` (자동 실행됨) | ~10초 |
| 주간 팀 리포트 | `/skill-report` | ~30초 |

기존 내용은 수정하지 마라.
```

### 6-2. README.md

#### 프롬프트

```
README.md를 수정해줘.

1. 버전 배지: v1.33.1 → v1.34.0

2. "주요 명령어" 테이블에 추가:
| `/skill-health-check` | 코드베이스 건강 검진 | "건강 검진해줘" |

3. "전체 22개 명령어" → "전체 23개 명령어"

4. "핵심 원칙" 섹션 바로 위에 새 섹션:

## 🏥 건강 검진 (Health Check)

에이전트가 생성한 코드와 문서 간 드리프트를 탐지하고, 엔트로피 축적을 조기에 발견합니다.

| 카테고리 | 설명 | 기본 가중치 |
|----------|------|------------|
| doc-sync | 문서 ↔ 코드 동기화 | 35% |
| state-integrity | 상태 파일 정합성 | 25% |
| security | 기본 보안 검사 | 25% |
| agent-config | 에이전트 설정 유효성 | 15% |
| compliance | 컴플라이언스 준수 (fintech) | 도메인 선택 시 자동 추가 |

`/skill-health-check --fix`로 자동 수정 가능한 항목을 즉시 반영할 수 있습니다.

기존 내용은 수정하지 마라.
```

### 6-3. CHANGELOG.md

#### 프롬프트

```
CHANGELOG.md의 [Unreleased] 아래에 추가:

## [1.34.0] - 2026-03-27

### Added
- `/skill-health-check` 코드베이스 건강 검진 (19개 검사 항목, 점수 + 등급 + 이력 추적)
- 기본 보안 검사 4개 항목 (민감정보, SQL Injection, CORS, API 인증 — 전체 도메인)
- fintech 도메인 컴플라이언스 검사 4개 항목 (감사 로그, 멱등성, 금액 정밀도, 트랜잭션)
- `health-history.schema.json` 검사 이력 스키마
- `/skill-merge-pr` Post-Merge Health Gate (CRITICAL 자동 감지)
- `/skill-release` 사전 Health Gate (선택적)
- `/skill-status --health` → `/skill-health-check` 에스컬레이션 안내
- `docs/skill-reference.md` 검증 도구 선택 가이드

### Changed
- `project.schema.json`에 `healthCheck` 설정 필드 추가

기존 내용은 수정하지 마라.
```

### 6-4. VERSION

```
VERSION 파일을 1.34.0으로 업데이트해줘.
```

### 최종 검증

```bash
# 신규 파일 확인
echo "=== New files ==="
ls -la .claude/domains/_base/health/_category.json
ls -la .claude/domains/fintech/health/_category.json
ls -la .claude/schemas/health-history.schema.json
ls -la .claude/skills/skill-health-check/SKILL.md

# JSON 검증
echo -e "\n=== JSON validation ==="
for f in .claude/domains/*/health/_category.json .claude/schemas/health-history.schema.json .claude/schemas/project.schema.json; do
  python3 -m json.tool "$f" > /dev/null 2>&1 && echo "✅ $f" || echo "❌ $f"
done

# 버전 확인
echo -e "\n=== Version check ==="
grep "v1.34.0\|1.34.0" README.md VERSION CHANGELOG.md

# 검사 항목 수 확인 (SKILL.md에서)
echo -e "\n=== Check item count ==="
grep -c "^####" .claude/skills/skill-health-check/SKILL.md
```

### Git 태깅

```bash
git add -A
git commit -m "feat: add skill-health-check with SKILL.md-based engine (v1.34.0)

- Add /skill-health-check: 19 check items (doc-sync 7, state-integrity 5, security 4, agent-config 2, compliance 4)
- Add scoring system (0-100) with grades and health-history.json tracking
- Add Post-Merge Health Gate in /skill-merge-pr
- Add escalation path from /skill-status --health
- Extend project.schema.json with healthCheck settings
- No JSON rule engine — SKILL.md is the declarative engine"

git tag -a v1.34.0 -m "v1.34.0: Health Check System"
```

---

## 이전 계획 대비 변경 요약

| 항목 | 이전 (v2) | 현재 (v3) |
|------|----------|----------|
| 아키텍처 | JSON 규칙 엔진 + 8종 verification 타입 | **SKILL.md 단일 엔진** |
| 규칙 정의 | *.rules.json 27개 파일 | **SKILL.md 내 마크다운 테이블** |
| 신규 파일 | 11개 | **4개** (65% 감소) |
| 총 파일 변경 | 17개 | **11개** (35% 감소) |
| 체크리스트 관계 | 의미적 중복 (같은 내용 두벌) | **"참조" 필드로 연결 (한벌 관리)** |
| skill-validate 관계 | 5개 규칙 완전 중복 | **역할 분리 (중복 0)** |
| techStack 대응 | JSON에 분기 로직 하드코딩 | **Claude 맥락 판단 (유연)** |
| skill-upgrade 영향 | Step 6/11/12 수정 필요 | **변경 없음** |
| 검사 항목 | 27개 (중복 5개 포함) | **19개 (중복 0, security 4개 전체 도메인 적용)** |
| 추가 연동 | 없음 | **skill-release 게이트 + 에스컬레이션 + 도구 선택 가이드** |

## 구현 완료 후 테스트

```
# 전체 검진 (프레임워크 자체에서는 대부분 SKIP 예상)
/skill-health-check

# CRITICAL만
/skill-health-check --quick

# 특정 카테고리
/skill-health-check --scope agent-config

# examples/fintech-gateway/ 에서는 fintech compliance 항목도 실행
```
