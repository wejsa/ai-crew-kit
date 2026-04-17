# 토큰 최적화 가이드

> [← README로 돌아가기](../README.md)

AI Crew Kit v2.0.0에서는 각 스킬에 **복잡도 힌트(`complexity-hint`)**를 명시하여 사용자가 토큰 예산을 가시적으로 관리할 수 있도록 합니다.

> **원칙**: ACK는 모델을 **자동 전환하지 않습니다**. `complexity-hint`는 **안내용**이며, 실제 모델 선택은 Claude Code 설정 또는 사용자 판단에 맡깁니다.

---

## 1. 스킬별 복잡도 분류

모든 SKILL.md에는 `complexity-hint: heavy | medium | light` 필드가 명시되어 있습니다.

### 🔴 Heavy (3개 — Opus 권장)

전략적 판단, 다관점 통합, 심층 분석이 필요한 스킬.

| 스킬 | 역할 |
|---|---|
| `skill-review-pr` | 5관점 통합 PR 리뷰 |
| `skill-plan` | Task 선택 + 설계 분석 + 스텝 분리 |
| `skill-health-check` | 다중 카테고리 코드베이스 검진 |

### 🟡 Medium (9개 — Sonnet 권장)

정해진 프로세스를 따르되 판단이 필요한 스킬.

| 스킬 | 역할 |
|---|---|
| `skill-impl` | 스텝 개발 + PR 생성 |
| `skill-feature` | 요구사항 정의 + 백로그 등록 |
| `skill-retro` | 완료 Task 회고 + 학습 반영 |
| `skill-report` | 프로젝트 메트릭 4축 분석 |
| `skill-estimate` | 작업 복잡도 5팩터 추정 |
| `skill-fix` | CRITICAL 이슈 자동 수정 |
| `skill-onboard` | 기존 프로젝트 스캔 + 온보딩 |
| `skill-review` | 경로 기반 5관점 코드 리뷰 |
| `skill-hotfix` | main 긴급 수정 + 보안 리뷰 |

### 🟢 Light (11개 — Haiku 가능)

상태 조회, 템플릿 기반, 정형화된 작업.

| 스킬 | 역할 |
|---|---|
| `skill-status` | 프로젝트 상태 확인 |
| `skill-backlog` | Task CRUD |
| `skill-docs` | 키워드 기반 문서 검색 |
| `skill-create` | 스킬 스캐폴딩 |
| `skill-domain` | 도메인 조회/전환 |
| `skill-release` | 빌드 + 머지 + 태그 생성 |
| `skill-upgrade` | 프레임워크 업그레이드 |
| `skill-validate` | 구조 무결성 검증 |
| `skill-init` | 프로젝트 초기화 |
| `skill-merge-pr` | PR Squash 머지 |
| `skill-rollback` | git revert 기반 롤백 |

---

## 2. 복잡도 → 권장 모델 매핑

`complexity-hint`는 모델명을 하드코딩하지 않고 **복잡도 레벨**로 표현합니다 (모델 세대 변경에 독립적).

| complexity-hint | 권장 모델 | 특징 |
|---|---|---|
| **heavy** | Opus 4.x | 심층 추론, 다관점 통합, extended thinking 유리 |
| **medium** | Sonnet 4.x | 균형 잡힌 속도·품질, 일반 개발 작업 |
| **light** | Haiku 4.x | 빠른 응답, 정형화된 작업 |

> 모델 이름은 세대별로 바뀝니다(Opus 4.7 → 4.8 → ...). 복잡도 분류는 변경되지 않습니다.

---

## 3. project.json의 `tokenHints`로 오버라이드

프로젝트 특성에 따라 스킬별 복잡도를 조정할 수 있습니다.

```json
{
  "tokenHints": {
    "defaultComplexity": "medium",
    "skillOverrides": {
      "skill-impl": "light",
      "skill-review-pr": "heavy"
    },
    "maxMcpServers": 10,
    "compactionThreshold": 50
  }
}
```

| 필드 | 기본값 | 설명 |
|---|---|---|
| `defaultComplexity` | `"medium"` | SKILL.md에 `complexity-hint`가 없을 때 적용 |
| `skillOverrides` | `{}` | 스킬별 복잡도 오버라이드 |
| `maxMcpServers` | `10` | 동시 활성화 MCP 서버 수 권장 상한 |
| `compactionThreshold` | `50` | `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` 권장값 (%) |

**우선순위**: `project.json.tokenHints.skillOverrides[skill]` > `SKILL.md.complexity-hint` > `tokenHints.defaultComplexity`

---

## 4. 환경변수 설정 안내

Claude Code 운영에서 적용할 수 있는 환경변수입니다. ACK가 강제하지 않으며, 프로젝트별 판단에 맡깁니다.

### `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`

컨텍스트 컴팩션이 트리거되는 임계값(%). 기본값은 Claude Code가 결정합니다.

```bash
# 컨텍스트 50% 시점에 컴팩션 (공격적, 긴 세션에 유리)
export CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50

# 컨텍스트 75% 시점에 컴팩션 (보수적, 컴팩션 손실 최소화)
export CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=75
```

**권장**: `tokenHints.compactionThreshold`를 프로젝트 전역 기본값으로 두고, 세션별로 환경변수로 오버라이드.

### `MAX_THINKING_TOKENS` (Extended Thinking 사용 시)

Extended Thinking 활성 상태에서 thinking 토큰 상한.

```bash
# 일반 프로젝트
export MAX_THINKING_TOKENS=10000

# 복잡한 아키텍처 분석이 많은 경우
export MAX_THINKING_TOKENS=32000
```

---

## 5. MCP 서버 수 관리

MCP 서버가 많을수록 초기 컨텍스트가 커지고 응답이 느려집니다. **10개 이하** 권장.

| MCP 서버 수 | 영향 |
|---|---|
| 1~5개 | 최적 |
| 6~10개 | 허용 범위 |
| 11~15개 | 응답 지연 체감 |
| 16개 이상 | 권장하지 않음 |

프로젝트 설정: `tokenHints.maxMcpServers`로 팀 가이드 명시.

---

## 6. 프로파일 × 복잡도 조합

Phase 2의 스킬 프로파일(`developer`/`full`/`docs-only`)과 Phase 3의 복잡도를 조합하면 프로젝트별 토큰 예산을 추정할 수 있습니다.

| 프로파일 | 노출 스킬 수 | Heavy | Medium | Light |
|---|---|---|---|---|
| `developer` | 9 | 2 | 4 | 3 |
| `full` | 21 (internal 제외) | 3 | 8 | 10 |
| `docs-only` | 3 | 0 | 0 | 3 |

`docs-only` 프로파일은 문서 전용 light 스킬만 사용 → 토큰 소비 최소.
`developer`는 heavy 2개(skill-plan, skill-review-pr)만 포함 → 나머지는 medium/light로 운영 가능.

---

## 7. 실패 시나리오와 대응

### Q. `complexity-hint` 필드가 Claude Code에서 무시되면?

ACK는 이 필드를 **문서 안내용**으로 사용합니다. Claude Code가 자동 모델 전환을 지원하지 않아도 가치는 유지됩니다:

1. 사용자가 스킬 호출 전 복잡도를 인지 → 수동으로 모델/thinking 설정
2. `/skill-health-check`가 SKILL.md 구조 검증 시 활용
3. 향후 Claude Code가 지원할 경우 자동 연동

### Q. 내 프로젝트에서 분류가 맞지 않으면?

`tokenHints.skillOverrides`로 프로젝트별 오버라이드:

```json
{
  "tokenHints": {
    "skillOverrides": {
      "skill-review-pr": "medium"  // 간단한 프로젝트에서는 medium으로 충분
    }
  }
}
```

---

## 관련 문서

- [스킬 레퍼런스](./skill-reference.md)
- [커스터마이징 가이드](./customization.md)
- [업그레이드 가이드](./upgrade-guide.md)
