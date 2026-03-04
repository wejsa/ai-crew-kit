# AI Crew Kit v1.21.0

> 도메인 선택 → 자동 셋업 → 에이전트 팀 즉시 가동

AI 에이전트 팀 기반 소프트웨어 개발 키트입니다. 도메인을 선택하면 해당 분야에 특화된 에이전트 팀과 체크리스트, 참고자료가 자동으로 구성됩니다.

---

## 빠른 시작

```bash
# 1. 저장소 클론
git clone https://github.com/wejsa/ai-crew-kit.git my-project
cd my-project

# 2. Claude Code 실행
claude

# 3. 프로젝트 초기화
/skill-init --quick    # 5분 체험 (제로 결정, 자동 감지)
/skill-init            # 대화형 (모든 설정을 직접 선택)

# 4. 첫 기능 기획
/skill-feature "사용자 인증"
```

초기화 과정에서 **도메인**, **기술 스택**, **에이전트 팀**을 선택하고, 프로젝트 전용 `README.md`와 `VERSION`(0.1.0)이 자동 생성됩니다.

---

## 요구사항

| 구분 | 요구사항 |
|------|---------|
| **필수** | [Claude Code](https://claude.ai/download) CLI |
| **권장** | Git 2.30+ |

> Node.js, Python 등 외부 런타임은 불필요합니다. Claude Code가 모든 것을 처리합니다.

---

## 지원 도메인

| 도메인 | 설명 | 기본 스택 | 컴플라이언스 |
|--------|------|----------|-------------|
| 🏦 **fintech** | 결제, 정산, 금융 서비스 | Spring Boot + MySQL + Redis | PCI-DSS, 전자금융감독규정 |
| 🛒 **ecommerce** | 이커머스, 마켓플레이스 | Spring Boot + MySQL + Redis | 전자상거래법, 소비자보호법 |
| 🔧 **general** | 범용 프로젝트 | Spring Boot + MySQL | - |

---

## 주요 명령어

| 명령어 | 설명 | 자연어 예시 |
|--------|------|------------|
| `/skill-status` | 프로젝트 상태 확인 | "상태 확인해줘" |
| `/skill-feature` | 새 기능 기획 | "새 기능 기획해줘" |
| `/skill-plan` | 설계 및 스텝 계획 | "다음 작업 가져와줘" |
| `/skill-impl` | 코드 구현 + PR 생성 | "개발 진행해줘" |
| `/skill-review-pr` | PR 리뷰 | "PR 123 리뷰해줘" |
| `/skill-merge-pr` | PR 머지 | "PR 123 머지해줘" |
| `/skill-retro` | 완료 Task 회고 | "회고 해줘" |
| `/skill-hotfix` | main 긴급 수정 | "긴급 수정해줘" |
| `/skill-rollback` | 릴리스 롤백 | "v1.2.3 롤백해줘" |
| `/skill-report` | 프로젝트 메트릭 리포트 | "리포트 생성해줘" |

전체 22개 명령어와 자연어 매핑은 [스킬 레퍼런스](./docs/skill-reference.md)를 참조하세요.

---

## 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **Domain-Driven Kit** | 도메인 선택이 전체 키트 동작 결정 |
| **Layered Override** | `_base` → `{domain}` → `project.json` 순서로 설정 적용 |
| **Agent Orchestration** | PM이 워크플로우에 따라 에이전트 자동 분배 |
| **Zero-Config Start** | `/skill-init` 한 번으로 즉시 가동 |

---

## 상세 문서

| 문서 | 내용 |
|------|------|
| [설치 및 시작하기](./docs/getting-started.md) | 설치 상세, 초기화 흐름, 온보딩 |
| [핵심 개념](./docs/concepts.md) | 도메인, 에이전트 팀, 디렉토리 구조, 실행 모델 |
| [스킬 레퍼런스](./docs/skill-reference.md) | 22개 스킬 전체 목록, 자연어 매핑 |
| [워크플로우 가이드](./docs/workflow-guide.md) | 자동 체이닝, 7가지 워크플로우, 품질 게이트, Git 전략 |
| [도메인 확장](./docs/customization.md) | 참고자료/체크리스트 추가, 새 도메인 생성, Layered Override |
| [프레임워크 업그레이드](./docs/upgrade-guide.md) | 업그레이드, 보존 항목, 롤백 |

---

## 변경 로그

자세한 변경 이력은 [CHANGELOG.md](./CHANGELOG.md)를 참조하세요.

---

## 라이선스

MIT License

---

## 관련 링크

- [상세 문서](./docs/)
- [이슈 리포트](https://github.com/wejsa/ai-crew-kit/issues)
