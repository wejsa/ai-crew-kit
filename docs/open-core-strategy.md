# 오픈소스 전략 계획서

## 1. 개요

ai-crew-kit **전체를 MIT 오픈소스로 공개**하고, 커뮤니티 성장과 개인 브랜딩을 통해 간접 수익화를 추구하는 전략.

### 왜 Full Open Source인가?

- 프로젝트의 본질이 **마크다운 + JSON 설정 파일** → 유료화해도 복사 방지 불가
- 기능을 나눠서 제한하면 사용자 경험만 나빠지고 채택률 하락
- 시장이 아직 작음 → 지금은 사용자 확보가 수익보다 중요
- 오픈소스 레퍼런스 프로젝트로서의 브랜드 가치가 더 큼

---

## 2. 공개 범위

**전체 공개 (MIT License)**

| 카테고리 | 항목 | 수량 |
|----------|------|------|
| **도메인** | `_base`, `general`, `fintech`, `ecommerce` | 4개 |
| **스킬** | init, status, plan, impl, review-pr, merge-pr, feature, backlog, review, create, onboard, validate, fix, docs, estimate, retro, hotfix, rollback, release, upgrade, health-check, report, domain | 23개 |
| **에이전트** | pm, backend, frontend, planner, qa, docs, code-reviewer, devops, pr-reviewer(3종), docs-impact-analyzer, db-designer | 13개 |
| **워크플로우** | full-feature, quick-fix, review-only, hotfix, migration, docs-only, spike | 7개 |
| **예제** | fintech-gateway, ecommerce-shop | 2개 |
| **문서** | 전체 | 12개 |

---

## 3. 수익화 전략

코드 자체가 아닌, **코드 위에 올리는 서비스**로 수익화.

### 3.1 수익 채널

| 채널 | 설명 | 예상 단가 | 시작 시점 |
|------|------|----------|----------|
| **컨설팅** | 팀별 도메인 커스터마이징, 에이전트 최적화, 온보딩 지원 | $100~200/시간 | Phase 2 이후 |
| **커스텀 도메인 개발** | 의료, 물류, 교육 등 새 도메인 구축 대행 | $2,000~5,000/도메인 | Phase 2 이후 |
| **워크숍/교육** | "AI 에이전트 팀으로 개발하기" 온라인/오프라인 | $50~100/인 | Phase 3 이후 |
| **GitHub Sponsors** | 자발적 후원 | $5~50/월 | Phase 1과 동시 |
| **기업 지원 계약** | 우선 이슈 대응, SLA 기반 기술 지원 | $500~2,000/월 | 사용자 100+ 이후 |

### 3.2 가치 제안 정리

```
무료로 주는 것:  코드 전체, 문서 전체, 업데이트 전체
돈을 받는 것:   시간, 전문성, 맞춤 서비스
```

---

## 4. 실행 절차

### Phase 1: 오픈소스 저장소 정비 (1~2주)

저장소를 "외부 기여자가 참여하고 싶은" 상태로 만드는 단계.

#### Step 1.1 — 커뮤니티 필수 파일 추가

- [ ] `CONTRIBUTING.md` — 기여 가이드 (이슈 등록, PR 규칙, 코드 스타일)
- [ ] `CODE_OF_CONDUCT.md` — 행동 강령 (Contributor Covenant 기반)
- [ ] `.github/ISSUE_TEMPLATE/bug_report.md` — 버그 리포트 템플릿
- [ ] `.github/ISSUE_TEMPLATE/feature_request.md` — 기능 제안 템플릿
- [ ] `.github/PULL_REQUEST_TEMPLATE.md` — PR 템플릿

#### Step 1.2 — README 개선

- [ ] 영문 README 추가 또는 이중 언어 지원 (글로벌 사용자 확보)
- [ ] 데모 GIF/영상 추가 (5분 온보딩 과정)
- [ ] "Why ai-crew-kit?" 섹션 추가 (차별점 명확화)
- [ ] Badges 업데이트 (CI status, contributors, Discord 등)

#### Step 1.3 — CI/CD 추가

- [ ] GitHub Actions: 스키마 검증, 링크 체크, SKILL.md 포맷 검증
- [ ] Release automation: 태그 푸시 → CHANGELOG 자동 생성

#### Step 1.4 — GitHub 기능 활성화

- [ ] Discussions 활성화 (Q&A, Ideas, Show and Tell 카테고리)
- [ ] GitHub Sponsors 프로필 설정
- [ ] Topics/Tags 설정 (claude-code, ai-agent, developer-tools 등)

---

### Phase 2: 커뮤니티 구축 (2~4주)

사용자를 모으고, 피드백을 받고, 기여자를 만드는 단계.

#### Step 2.1 — 커뮤니티 채널 개설

| 채널 | 용도 | 우선순위 |
|------|------|---------|
| GitHub Discussions | Q&A, 기능 제안, 사용 사례 | 필수 |
| Discord 서버 | 실시간 소통, 온보딩 지원 | 높음 |
| X/Twitter | 업데이트 공지, 사용 사례 공유 | 높음 |

#### Step 2.2 — 초기 사용자 확보

- [ ] Claude Code 공식 커뮤니티에 프로젝트 소개
- [ ] 한국 개발자 커뮤니티 (GeekNews, disquiet 등)에 공유
- [ ] "ai-crew-kit으로 5분 만에 에이전트 팀 구성하기" 블로그 포스트
- [ ] Product Hunt 런칭

#### Step 2.3 — 기여 유도

- [ ] `good first issue` 라벨로 10개 이상 이슈 등록
- [ ] 새 도메인 기여 가이드 정비 (customization.md 보완)
- [ ] 커스텀 스킬 갤러리 (커뮤니티 제작 스킬 공유 공간)
- [ ] 기여자 인정: README Contributors 섹션, 릴리스 노트 멘션

---

### Phase 3: 콘텐츠 & 브랜딩 (4주~)

프로젝트와 메인테이너의 전문성을 알리는 단계.

#### Step 3.1 — 콘텐츠 제작

| 콘텐츠 | 형태 | 목적 |
|--------|------|------|
| 퀵스타트 영상 (5분) | YouTube/X | 첫 사용자 온보딩 |
| 도메인별 튜토리얼 | 블로그 시리즈 | 심화 사용 사례 |
| "AI 에이전트 팀 아키텍처" | 기술 블로그 | 전문성 어필 |
| 라이브 코딩 세션 | YouTube/Twitch | 커뮤니티 참여 |

#### Step 3.2 — 컨설팅 서비스 페이지

- [ ] 랜딩 페이지 또는 GitHub README에 서비스 안내 섹션
- [ ] 문의 채널 (이메일, Cal.com 등 예약 링크)
- [ ] 서비스 메뉴: 팀 온보딩, 커스텀 도메인 개발, 워크숍

---

## 5. 우선순위 로드맵

```
[Phase 1] 저장소 정비        ██████░░░░░░░░░░  1~2주
[Phase 2] 커뮤니티 구축      ░░░░██████░░░░░░  2~4주
[Phase 3] 콘텐츠 & 브랜딩    ░░░░░░░░██████░░  4주~
[수익화]  컨설팅/교육 시작    ░░░░░░░░░░░░████→ 지속
```

**즉시 시작 가능한 작업:**
1. CONTRIBUTING.md, CODE_OF_CONDUCT.md 작성
2. GitHub Issue/PR 템플릿 추가
3. GitHub Discussions, Sponsors 활성화
4. README 영문화

---

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| 사용자가 안 모임 | 수익화 불가 | 콘텐츠 마케팅 강화, 커뮤니티 채널 다변화 |
| 경쟁 프로젝트 등장 | 사용자 분산 | 선점 효과 + 지속 업데이트 + 도메인 특화 |
| 1인 유지보수 부담 | 번아웃 | 커뮤니티 기여 활성화, 코어 기여자 육성 |
| 컨설팅 수요 없음 | 수익 0 | GitHub Sponsors 병행, 콘텐츠로 간접 수익 |
| Claude Code 생태계 변화 | 프로젝트 무력화 | 에이전트 오케스트레이션 패턴 자체의 범용성 유지 |

---

## 7. 성공 지표

| 지표 | 목표 (3개월) | 목표 (6개월) | 목표 (12개월) |
|------|-------------|-------------|--------------|
| GitHub Stars | 100+ | 500+ | 2,000+ |
| 활성 사용자 | 30+ | 200+ | 1,000+ |
| 외부 기여자 | 3+ | 10+ | 30+ |
| 커뮤니티 도메인 | 1+ | 3+ | 5+ |
| Discord 멤버 | 30+ | 100+ | 500+ |
| 컨설팅 건수 | - | 2+ | 10+ |
| GitHub Sponsors | 5+ | 20+ | 50+ |
