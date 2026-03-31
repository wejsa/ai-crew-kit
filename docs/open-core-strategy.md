# Open Core 전략 계획서

## 1. 개요

ai-crew-kit을 **Open Core** 모델로 전환하여, 핵심 기능은 오픈소스(MIT)로 공개하고 고부가가치 도메인/기능은 프리미엄으로 제공하는 전략.

---

## 2. 공개/비공개 경계 설계

### 2.1 오픈소스 (Community Edition - MIT)

| 카테고리 | 포함 항목 |
|----------|----------|
| **도메인** | `_base`, `general` |
| **스킬 (14개)** | skill-init, skill-status, skill-plan, skill-impl, skill-review-pr, skill-merge-pr, skill-feature, skill-backlog, skill-review, skill-create, skill-onboard, skill-validate, skill-fix, skill-docs |
| **에이전트 (8개)** | agent-pm, agent-backend, agent-frontend, agent-planner, agent-qa, agent-docs, agent-code-reviewer, agent-devops |
| **워크플로우 (3개)** | full-feature, quick-fix, review-only |
| **스키마** | project.schema.json, backlog.schema.json |
| **템플릿** | CLAUDE.md.tmpl, README.md.tmpl, pr-body.md.tmpl |
| **문서** | getting-started, concepts, skill-reference, workflow-guide, upgrade-guide |
| **예제** | 없음 (별도 제공) |

### 2.2 프리미엄 (Pro Edition)

| 카테고리 | 포함 항목 | 가치 |
|----------|----------|------|
| **도메인: fintech** | 체크리스트(security, compliance, domain-logic), 템플릿(audit-log, idempotent-handler, state-machine, error-code), 참고문서 7개, glossary, error-codes | PCI-DSS/전자금융감독규정 자동 검증 |
| **도메인: ecommerce** | 체크리스트(compliance, performance, domain-logic), 템플릿(order-state-machine, price-calculator, inventory-handler), 참고문서 7개, glossary | 전자상거래법 자동 검증 |
| **스킬 (8개)** | skill-estimate, skill-retro, skill-hotfix, skill-rollback, skill-release, skill-upgrade, skill-health-check, skill-report | 운영/분석 고급 기능 |
| **에이전트 (5개)** | pr-reviewer-test, pr-reviewer-security, pr-reviewer-domain, docs-impact-analyzer, agent-db-designer | 전문 리뷰/분석 |
| **워크플로우 (4개)** | hotfix, migration, docs-only, spike | 고급 워크플로우 |
| **스키마** | health-history.schema.json, migrations.json | 운영 이력 관리 |
| **예제** | fintech-gateway, ecommerce-shop | 실전 레퍼런스 |
| **문서** | customization, harness-phase1/2, regression-testing | 고급 운영 가이드 |

---

## 3. 실행 절차 (Phase별)

### Phase 1: 저장소 분리 준비 (1~2주)

#### Step 1.1 — 디렉토리 구조 재설계

```
ai-crew-kit/                    ← 오픈소스 (public repo)
├── .claude/
│   ├── skills/                 ← Community 스킬만
│   ├── agents/                 ← Community 에이전트만
│   ├── domains/
│   │   ├── _base/
│   │   ├── _registry.json      ← general만 등록
│   │   └── general/
│   ├── workflows/              ← 기본 워크플로우만
│   ├── schemas/                ← 기본 스키마만
│   └── templates/
├── docs/
├── LICENSE                     ← MIT
├── README.md
└── CHANGELOG.md

ai-crew-kit-pro/                ← 프리미엄 (private repo)
├── domains/
│   ├── fintech/
│   └── ecommerce/
├── skills/
│   ├── skill-estimate/
│   ├── skill-retro/
│   ├── skill-hotfix/
│   ├── skill-rollback/
│   ├── skill-release/
│   ├── skill-upgrade/
│   ├── skill-health-check/
│   └── skill-report/
├── agents/
│   ├── pr-reviewer-test.md
│   ├── pr-reviewer-security.md
│   ├── pr-reviewer-domain.md
│   ├── docs-impact-analyzer.md
│   └── agent-db-designer.md
├── workflows/
│   ├── hotfix.yaml
│   ├── migration.yaml
│   ├── docs-only.yaml
│   └── spike.yaml
├── examples/
│   ├── fintech-gateway/
│   └── ecommerce-shop/
├── docs/
├── install.sh                  ← 설치 스크립트
├── LICENSE                     ← Commercial License
└── README.md
```

#### Step 1.2 — 프리미엄 설치 메커니즘 설계

프리미엄 사용자가 Community 위에 Pro를 얹는 방식:

```bash
# 1. Community Edition 설치
git clone https://github.com/wejsa/ai-crew-kit.git my-project
cd my-project

# 2. Pro Edition 추가 (라이선스 키 필요)
npx ai-crew-kit-pro install --key=LICENSE_KEY
# 또는
curl -sL https://pro.ai-crew-kit.dev/install.sh | bash -s -- --key=LICENSE_KEY
```

설치 스크립트가 하는 일:
- 라이선스 키 검증
- `.claude/domains/fintech/`, `.claude/domains/ecommerce/` 복사
- `.claude/skills/` 에 프리미엄 스킬 추가
- `.claude/agents/` 에 프리미엄 에이전트 추가
- `_registry.json` 업데이트 (프리미엄 도메인 등록)
- `.gitignore` 에 프리미엄 경로 추가 (재배포 방지)

#### Step 1.3 — Layered Override 호환성 확인

현재의 `_base → {domain} → project.json` 구조가 Pro 도메인 추가 시에도 정상 동작하는지 검증. `_registry.json`에 도메인을 동적으로 등록/해제하는 구조 확인.

---

### Phase 2: 오픈소스 저장소 정비 (1~2주)

#### Step 2.1 — Community Edition 저장소 정리

- [ ] 프리미엄 콘텐츠를 별도 브랜치/저장소로 이동
- [ ] `_registry.json`에서 fintech, ecommerce 제거
- [ ] README.md에 Community vs Pro 비교표 추가
- [ ] CONTRIBUTING.md 작성 (기여 가이드)
- [ ] CODE_OF_CONDUCT.md 추가
- [ ] Issue/PR 템플릿 생성 (.github/ISSUE_TEMPLATE/, .github/PULL_REQUEST_TEMPLATE.md)
- [ ] GitHub Actions CI 추가 (스키마 검증, 링크 체크 등)

#### Step 2.2 — 프리미엄 업그레이드 안내 통합

Community 스킬에서 프리미엄 기능 호출 시 자연스러운 안내:

```
# skill-status에서 health-check 미설치 시:
💡 코드베이스 건강 검진은 Pro Edition에서 제공됩니다.
   자세히: https://ai-crew-kit.dev/pro
```

도메인 선택 시 fintech/ecommerce가 없으면:
```
📋 사용 가능한 도메인: general
💡 fintech, ecommerce 도메인은 Pro Edition에서 제공됩니다.
```

#### Step 2.3 — 라이선스 정리

| 대상 | 라이선스 |
|------|---------|
| Community Edition | MIT (현행 유지) |
| Pro Edition | Commercial (EULA) |
| 사용자 생성 코드 | 사용자 소유 (제한 없음) |

---

### Phase 3: 프리미엄 배포 인프라 (2~3주)

#### Step 3.1 — 라이선스 관리 시스템

| 요소 | 선택지 | 추천 |
|------|--------|------|
| 라이선스 키 발급 | Gumroad, LemonSqueezy, Stripe | **LemonSqueezy** (한국 정산 지원) |
| 키 검증 | 온라인 검증 API | 오프라인 JWT 토큰 (개발자 경험 우선) |
| 배포 | Private npm, GitHub Packages, 직접 다운로드 | **GitHub Packages** (Private repo 연동) |

#### Step 3.2 — 가격 모델

| 플랜 | 가격 (제안) | 포함 |
|------|------------|------|
| **Community** | 무료 (MIT) | general 도메인, 기본 스킬 14개 |
| **Pro Individual** | $29/월 또는 $249/년 | 전체 도메인 + 전체 스킬 + 예제 |
| **Pro Team** | $19/인/월 (5인~) | Pro + 팀 공유 설정 + 우선 지원 |
| **Enterprise** | 문의 | Pro Team + 커스텀 도메인 개발 + SLA |

#### Step 3.3 — 랜딩 페이지 / 문서 사이트

- `ai-crew-kit.dev` 또는 유사 도메인 확보
- 오픈소스 문서: GitHub Pages 또는 Docusaurus
- Pro 소개 페이지: 비교표, 데모 영상, 사용 사례

---

### Phase 4: 커뮤니티 구축 (지속)

#### Step 4.1 — 초기 커뮤니티 채널

| 채널 | 용도 |
|------|------|
| GitHub Discussions | Q&A, 기능 제안, 사용 사례 공유 |
| Discord 서버 | 실시간 소통, 온보딩 지원 |
| X/Twitter | 업데이트 공지, 사용 사례 홍보 |

#### Step 4.2 — 기여 유도 전략

- `good first issue` 라벨로 진입장벽 낮추기
- 새 도메인 기여 가이드 (customization.md 기반)
- 커스텀 스킬 갤러리 (커뮤니티 제작 스킬 모음)
- 기여자 인정: README Contributors 섹션, 릴리스 노트 멘션

#### Step 4.3 — 콘텐츠 마케팅

- "ai-crew-kit으로 5분 만에 에이전트 팀 구성하기" 블로그/영상
- Claude Code 커뮤니티에서 활동
- 도메인별 사용 사례 시리즈 (일반, 핀테크, 이커머스)

---

## 4. 우선순위 로드맵

```
[Phase 1] 저장소 분리 준비          ██████░░░░░░░░░░  1~2주
[Phase 2] 오픈소스 저장소 정비       ░░░░░░██████░░░░  1~2주
[Phase 3] 프리미엄 배포 인프라       ░░░░░░░░░░██████  2~3주
[Phase 4] 커뮤니티 구축             ░░░░░░░░░░░░████→ 지속
```

**즉시 시작 가능한 작업:**
1. CONTRIBUTING.md, CODE_OF_CONDUCT.md 작성
2. GitHub Issue/PR 템플릿 추가
3. README.md에 Community vs Pro 비교표 추가
4. 프리미엄 콘텐츠를 별도 private repo로 분리

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| Community가 Pro를 포크하여 무료 배포 | 수익 감소 | 지속적 업데이트로 가치 유지, 브랜드/지원 차별화 |
| Community 기능이 너무 빈약하면 채택 저조 | 성장 저하 | Community만으로도 실용적인 가치 제공 (general 도메인 완전 동작) |
| Pro 경계가 모호하면 사용자 혼란 | UX 저하 | 명확한 비교표 + 프리미엄 기능 호출 시 자연스러운 안내 |
| 1인 유지보수 부담 | 번아웃 | 커뮤니티 기여 활성화, Phase 4에 집중 |

---

## 6. 성공 지표

| 지표 | 목표 (6개월) | 목표 (12개월) |
|------|-------------|--------------|
| GitHub Stars | 500+ | 2,000+ |
| Community 사용자 | 200+ | 1,000+ |
| Pro 유료 구독자 | 20+ | 100+ |
| 외부 기여자 | 10+ | 30+ |
| MRR (Monthly Recurring Revenue) | $500+ | $3,000+ |
