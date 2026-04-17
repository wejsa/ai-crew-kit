# ai-crew-kit v1.35.0 구현 계획서 — GC의 손

> **목표**: 기존 skill-health-check에 추세 경보 + "정리해줘" 진입점 추가 (Garbage Collection Phase 2)
> **버전**: v1.34.0 → v1.35.0
> **예상 작업량**: 2시간
> **설계 원칙**: 새 스킬/에이전트를 만들지 않는다. 기존 스킬을 최소 확장한다.

---

## 설계 결정 기록

### 왜 skill-gc를 만들지 않는가

에이전트 팀 3회 토의(아키텍트, PM, QA, 테크니컬 라이터, 실사용자, 프레임워크 설계자, 토큰 경제학자)를 거쳐 **만장일치로 skill-gc 신설을 기각**했다.

| 기각 사유 | 근거 |
|-----------|------|
| **고유 기능 0개** | "GC의 손" 9개 기능이 전부 기존 --fix에 구현됨 |
| **시스템 프롬프트 비용** | 스킬 1개 추가 = 매 대화 턴 +60토큰 = **월 ~66,000토큰 영구 비용** |
| **사용자 혼란** | "정리해줘" vs "헬스체크 --fix"의 차이를 구분할 수 없음 |
| **아키텍처 패턴 이탈** | 기존 패턴: 대상(noun) 기반 분류. GC는 동작(verb) 기반 → 이질적 |
| **YAGNI** | 향후 확장(cron, retro 연동)도 기존 스킬 확장으로 가능 |
| **v1.32.0 압축 원칙** | 74% 압축 직후 새 진입점 추가는 역행 |

### "GC의 손"의 진짜 정체

"GC의 눈"(v1.34.0)을 만들 때 이미 `--fix` 옵션으로 "손"의 70%를 함께 구현했다.
나머지 30%는 **추세 경보**(기존 어디에도 없음)와 **검진 주기 안내**뿐이다.
이 2가지는 기존 스킬에 **16줄 추가**로 완성된다.

### 기존 --fix 현황 (이미 구현됨)

| 스킬 | 수정 대상 | 항목 수 |
|------|----------|--------|
| skill-health-check --fix | 잠금 해제, 고아 브랜치/Task, techStack, CLAUDE.md 구조 | 5개 |
| skill-status --health --fix | orphan intent 정리, completed.json 보충 | 1개 범주 |
| skill-validate --fix | 레지스트리 정리, metadata 보정 | 2개 |

사용자가 "전부 정리"를 원하면 3개를 순서대로 실행하면 된다.
이 빈도는 별도 스킬을 정당화할 만큼 높지 않다.

---

## 릴리스 범위

| 포함 | 미포함 (v1.36.0+) |
|------|-------------------|
| 추세 경보 (3회 연속 FAIL, 점수 하락) | ecommerce 도메인 검사 항목 |
| "정리해줘" → --fix 자연어 매핑 | skill-retro 학습 연동 |
| 검진 주기 안내 (7일/14일 경과) | cron 기반 자동 실행 |
| | 자동 정리 PR 생성 |

---

## 전체 구현 순서 (2 스텝)

```
Step 1: skill-health-check 확장 (추세 경보 + "정리해줘" 트리거)
Step 2: skill-status 검진 주기 안내 + 문서 업데이트
```

---

## 파일 변경 목록

### 수정 (4개, 신규 0개)

| # | 파일 | 변경 내용 | 추가 줄 수 |
|---|------|----------|-----------|
| 1 | `.claude/skills/skill-health-check/SKILL.md` | 추세 경보 + "정리해줘" 트리거 | +13줄 |
| 2 | `.claude/skills/skill-status/SKILL.md` | 검진 주기 안내 | +3줄 |
| 3 | `docs/skill-reference.md` | 자연어 매핑 + 가이드 업데이트 | +3줄 |
| 4 | `CHANGELOG.md` + `VERSION` + `README.md` | v1.35.0 | +10줄 |

**합계: +29줄, 신규 파일 0개, 스킬 수 23개 유지**

---

## Step 1: skill-health-check 확장

### 1-1. "정리해줘" 트리거 추가

#### 프롬프트

```
.claude/skills/skill-health-check/SKILL.md의 실행 조건을 수정해줘.

현재:
  ## 실행 조건
  - /skill-health-check 또는 "헬스체크 해줘" 또는 /skill-health-check를 요청할 때 사용합니다.

변경:
  ## 실행 조건
  - /skill-health-check 또는 "헬스체크 해줘"
  - "정리해줘", "cleanup" → --fix 모드로 자동 전환
```

### 1-2. 추세 경보 추가

#### 프롬프트

```
.claude/skills/skill-health-check/SKILL.md의 Phase D(리포트 생성) 섹션에
추세 경보를 추가해줘.

현재 Phase D의 항목 3 다음에 추가:

4. 추세 경보 (health-history.json에 3회 이상 기록이 있을 때):
   - 동일 항목 3회 연속 FAIL → "⚠️ {항목ID}가 3회 연속 실패 중. severity 상향을 고려하세요."
   - 전체 점수 3회 연속 하락 → "⚠️ Health score 지속 하락: {N1}점 → {N2}점 → {N3}점"
   - 특정 카테고리 failCap 이하 3회 연속 → "⚠️ {카테고리} 집중 점검 필요"
   - history가 3회 미만이면 추세 분석을 스킵한다.
   - --fix 모드 실행 기록(mode에 "fix" 포함)은 추세 비교에서 별도 취급한다
     (fix 직후 점수 급등을 "자연 개선"과 구분하기 위해).

기존 내용은 수정하지 마라.
```

### 검증

```bash
grep -n "정리해줘\|추세 경보\|3회 연속" .claude/skills/skill-health-check/SKILL.md
```

---

## Step 2: skill-status 검진 주기 안내 + 문서 업데이트

### 2-1. skill-status 검진 주기 안내

#### 프롬프트

```
.claude/skills/skill-status/SKILL.md의 "검진 주기 안내" 또는
"에스컬레이션 안내" 섹션 아래에 다음을 추가해줘:

#### 검진 주기 안내
health-history.json이 존재하면 마지막 전체 검진(mode에 "fix" 미포함) 날짜를 확인한다.
- 7일 이상 경과: "📅 마지막 건강 검진이 {N}일 전입니다. /skill-health-check 권장"
- 14일 이상 경과: "⏰ 건강 검진이 {N}일간 미실행. /skill-health-check --fix 권장"
- health-history.json이 없거나 기록이 없으면: 안내하지 않음

기존 내용은 수정하지 마라.
```

### 2-2. docs/skill-reference.md 업데이트

#### 프롬프트

```
docs/skill-reference.md를 수정해줘.

1. 자연어 매핑 테이블에 추가:
| "정리해줘" | `/skill-health-check --fix` |

2. "어떤 검증 도구를 사용해야 하나요?" 테이블에 행 추가:
| 문제를 수정할 때 | `/skill-health-check --fix` | ~30초 |

기존 내용은 수정하지 마라.
```

### 2-3. README.md + CHANGELOG.md + VERSION

#### 프롬프트

```
1. README.md 버전 배지: v1.34.0 → v1.35.0

2. CHANGELOG.md의 [Unreleased] 아래에 추가:

## [1.35.0] - 2026-03-27

### Added
- 추세 경보: 3회 연속 FAIL 항목 감지, 점수 하락 추세, 카테고리 failCap 경고
- "정리해줘" 자연어 매핑 → `/skill-health-check --fix` 자동 전환
- `/skill-status` 검진 주기 안내 (7일/14일 경과 시)

3. VERSION: 1.35.0
```

### 최종 검증

```bash
# 변경 확인
grep -n "정리해줘\|추세 경보\|검진 주기" \
  .claude/skills/skill-health-check/SKILL.md \
  .claude/skills/skill-status/SKILL.md \
  docs/skill-reference.md

# 버전 확인
grep "v1.35.0\|1.35.0" README.md VERSION CHANGELOG.md

# health-check SKILL.md 비대화 확인 (310줄 이하 목표)
wc -l .claude/skills/skill-health-check/SKILL.md
```

### Git 태깅

```bash
git add -A
git commit -m "feat: add trend alerts and cleanup trigger to health-check (v1.35.0)

- Add trend alerts: 3-consecutive FAIL detection, score decline warning
- Add '정리해줘' natural language trigger → --fix auto-switch
- Add check interval notification in skill-status (7d/14d)
- No new skills or agents — minimal extension of existing tools"

git tag -a v1.35.0 -m "v1.35.0: GC의 손 — 추세 경보 + 정리 트리거"
```

---

## 이전 계획 대비 변경 요약

| 항목 | v4 (이전) | v5 (최종) |
|------|----------|----------|
| 아키텍처 | agent-gc + skill-gc 신설 | **기존 스킬 16줄 확장** |
| 파일 수 | 신규 2 + 수정 4 = 6 | **수정 4개, 신규 0** |
| 추가 줄 수 | ~200줄 | **+29줄** |
| 스킬 수 | 23 → 24 | **23 유지** |
| 시스템 프롬프트 비용 | +월 66,000토큰 | **0** |
| 추세 경보 | skill-gc 내부 | **health-check Phase D** |
| "정리해줘" | /skill-gc | **health-check --fix 자연어 매핑** |
| 검진 주기 안내 | skill-status 확장 | **동일** |
| 오케스트레이션 | 3개 --fix 연쇄 호출 | **제거** (사용 빈도 낮음) |
| 재검증 | skill-gc 내부 | **제거** (기존 --fix에서 처리) |
| ecommerce | 동시 릴리스 | **v1.36.0 분리** |

## 비대화 방지 가드레일

향후 health-check SKILL.md가 비대해질 경우의 분리 기준:

| 조건 | 조치 |
|------|------|
| SKILL.md 400줄 초과 | 카테고리별 검사 로직을 도메인 파일로 분리 검토 |
| autoFix에 빌드+테스트+커밋 필요 | skill-fix 패턴으로 별도 스킬 분리 |
| 검사 항목 40개 초과 | 카테고리 단위 서브 스킬 분리 |
| "전체 정리" 수요가 주 3회 이상 | 그때 skill-gc 오케스트레이터 신설 |

---

## 구현 완료 후 테스트

```
# 추세 경보 확인 (3회 이상 실행 이력 필요)
/skill-health-check
# → Phase D 리포트에 추세 경보 섹션 확인

# "정리해줘" 트리거 확인
"정리해줘"
# → /skill-health-check --fix로 자동 전환되는지 확인

# 검진 주기 안내 확인 (7일 미실행 상태에서)
/skill-status
# → "마지막 건강 검진이 N일 전" 안내 확인

# --fix 실행
/skill-health-check --fix
# → 기존 5개 autoFix 항목 수정 + 추세 경보 출력
```
