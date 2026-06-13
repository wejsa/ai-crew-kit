# ADR-009: agent-devops 제거

> 상태: 제안 (Proposed)
> 작성일: 2026-04-03
> 결정자: 프레임워크 운영자
> 상위 로드맵: [roadmap-ecosystem-expansion.md](../roadmap-ecosystem-expansion.md)

---

## 1. 맥락

agent-devops는 CI/CD 파이프라인, Docker 설정, Kubernetes 매니페스트, 모니터링 구성 등
인프라 관련 코드를 생성하는 전문 에이전트로 정의되어 있다.

그러나 프레임워크 사용 현황 분석 결과, 실질적 사용이 전무한 상태다.

---

## 2. 현황 분석

### 2.1 사용률

| 항목 | 결과 |
|------|------|
| 스킬 연동 | **0건** — 22개 스킬 중 어떤 것도 agent-devops를 호출하지 않음 |
| 워크플로우 참조 | **0건** — agent-pm이 어떤 워크플로우에서도 agent-devops를 호출하지 않음 |
| 예제 프로젝트 | **2/2 비활성** — fintech, ecommerce 모두 agents.disabled에 포함 |

### 2.2 파일 분석

**위치**: `.claude/agents/agent-devops.md`
**크기**: 520줄
**내용**:
- CI/CD 파이프라인 구성 (GitHub Actions 템플릿)
- Docker 설정 (멀티스테이지 빌드, docker-compose)
- Kubernetes 배포 매니페스트 (Deployment, Service, Ingress)
- 모니터링 (Prometheus, Grafana, ELK)
- 보안 (시크릿 관리, 네트워크 정책)

### 2.3 참조 위치

| 파일 | 참조 유형 | 영향 |
|------|----------|------|
| `.claude/agents/agent-devops.md` | 정의 | 삭제 대상 |
| `.claude/domains/fintech/CLAUDE-example.md` | 에이전트 테이블 | agent-devops 행 제거 |
| `docs/concepts.md` | 에이전트 목록 | "선택적" 에이전트에서 제거 |
| `examples/ecommerce-shop/CLAUDE.md` | disabled 목록 | 참조 제거 (이미 비활성) |
| `examples/fintech-gateway/CLAUDE.md` | disabled 목록 | 참조 제거 (이미 비활성) |

---

## 3. 결정

### agent-devops를 제거한다.

**삭제**:
- `.claude/agents/agent-devops.md`

**수정** (참조 제거):
- `.claude/domains/fintech/CLAUDE-example.md` — 에이전트 테이블에서 행 제거
- `docs/concepts.md` — 에이전트 목록에서 제거
- `examples/ecommerce-shop/CLAUDE.md` — disabled 목록에서 제거
- `examples/fintech-gateway/CLAUDE.md` — disabled 목록에서 제거

**유지** (독립 문서):
- `.claude/domains/_base/conventions/deployment.md` — 배포 모범 사례 참조 문서. agent-devops와 무관하게 독립적으로 존재하며, Docker/CI-CD 가이드로서 가치 있음.

---

## 4. 근거

### 4.1 제거 찬성 근거

1. **제로 통합**: 어떤 스킬도, 어떤 워크플로우도 이 에이전트를 호출하지 않는다
2. **양쪽 예제 모두 비활성**: 프레임워크 제작자 스스로가 불필요하다고 판단한 상태
3. **유지보수 비용**: 520줄의 한국어 문서를 업데이트하는 비용이 발생하지만 사용자 가치는 0
4. **프레임워크 범위 재정의**: ADR-010에서 인프라 코드를 명시적으로 범위 밖으로 선언. agent-devops의 존재가 범위 정의와 모순
5. **에이전트 로드 부담 제거**: 에이전트 정의 파일이 존재하면 CLAUDE.md 생성 시 참조 대상에 포함되어 불필요한 토큰 소모

### 4.2 제거 반대 논점과 반박

| 반대 논점 | 반박 |
|----------|------|
| "나중에 쓸 수 있다" | Git 히스토리에서 복원 가능. 필요 시 재추가 비용 < 유지보수 비용 |
| "Dockerfile 생성은 유용하다" | deployment.md 컨벤션으로 가이드 충분. agent-backend가 Dockerfile 생성 가능 |
| "DevOps 도메인을 추가할 수 있다" | ADR-010에서 인프라 코드 제외 결정. 추가 시 새로운 에이전트 정의가 더 적합 |

---

## 5. 영향도

### 5.1 영향 있는 사용자

**없음.**
- 현재 agent-devops를 활성화하여 사용하는 프로젝트가 존재하지 않음
- 기존 프로젝트의 agents.disabled에서 제거해도 기능 변화 없음

### 5.2 마이그레이션

기존 프로젝트의 CLAUDE.md에 agent-devops 참조가 있는 경우:
- skill-upgrade 시 자동 제거 (CLAUDE.md 재생성)
- 수동 대응: agents 섹션에서 agent-devops 관련 줄 삭제

### 5.3 대안 경로

Dockerfile, docker-compose.yml 작성이 필요한 사용자:
1. `_base/conventions/deployment.md` 참조 (Docker 모범 사례 포함)
2. agent-backend에게 직접 요청 ("Dockerfile 만들어줘")
3. 필요 시 CLAUDE.md CUSTOM_SECTION에 배포 관련 지시 추가

---

## 6. 실행 계획

### 6.1 타이밍

Phase 3 (v1.40.0) 릴리스와 함께 진행. 별도 Phase 불필요.

### 6.2 체크리스트

- [ ] `.claude/agents/agent-devops.md` 삭제
- [ ] `.claude/domains/fintech/CLAUDE-example.md` 수정
- [ ] `docs/concepts.md` 수정
- [ ] `examples/ecommerce-shop/CLAUDE.md` 수정
- [ ] `examples/fintech-gateway/CLAUDE.md` 수정
- [ ] CHANGELOG [Unreleased]에 기록: "Removed: agent-devops (ADR-009)"
- [ ] skill-upgrade migrations.json에 제거 안내 추가

---

## 7. 참고

- deployment.md (96줄): Docker 모범 사례, CI/CD 표준, 배포 전략 가이드. 독립 문서로서 계속 유지.
- agent-devops 원본은 Git 히스토리에 보존되므로, 미래에 인프라 도메인을 추가하더라도 참고 가능.
