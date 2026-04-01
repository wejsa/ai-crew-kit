# Phase 1-2: 프론트엔드 생태계 강화 상세 요구사항

> 작성일: 2026-04-01
> 테마: "백엔드 중심에서 풀스택으로"
> 상위 문서: [개선 로드맵](../roadmap-universal-access.md) §4.2

---

## 1. 개요

| 항목 | 내용 |
|------|------|
| **문제** | 도메인 3개 모두 Spring Boot 중심. 프론트엔드 컨벤션 0개, 패키지 매니저 npm만 지원 |
| **해결** | A. 패키지 매니저 확장, B. 프론트엔드 컨벤션 4개, C. 리뷰 에이전트 프론트엔드 인식 |
| **변경 파일** | skill-impl, skill-init, skill-onboard, pr-reviewer-domain, _base/conventions/ |
| **스키마 변경** | 없음 |

---

## 2. A. 패키지 매니저 다양성

### 2.1 현재 상태

skill-impl Step 5 빌드 명령어:

| 스택 | 빌드 | 테스트 | 린트 |
|------|------|--------|------|
| spring-boot-kotlin | `./gradlew build` | `./gradlew test` | `./gradlew ktlintCheck` |
| nodejs-typescript | `npm run build` | `npm test` | `npm run lint` |
| go | `go build ./...` | `go test ./...` | `golangci-lint run` |

### 2.2 추가할 패키지 매니저

| Lock 파일 | 매니저 | 빌드 | 테스트 | 린트 |
|-----------|--------|------|--------|------|
| `yarn.lock` | yarn | `yarn build` | `yarn test` | `yarn lint` |
| `pnpm-lock.yaml` | pnpm | `pnpm build` | `pnpm test` | `pnpm lint` |
| `bun.lockb` | bun | `bun run build` | `bun test` | `bun run lint` |

### 2.3 감지 우선순위

project.json `buildCommands` > Lock 파일 자동 감지 > techStack 기반 폴백

Lock 파일 감지 로직 (프로젝트 루트에서 순서대로):
1. `bun.lockb` → bun
2. `pnpm-lock.yaml` → pnpm
3. `yarn.lock` → yarn
4. `package-lock.json` → npm (기존)

복수 존재 시 위 우선순위 적용.

### 2.4 변경 파일

| 파일 | 변경 |
|------|------|
| skill-impl/SKILL.md | Step 5 빌드 테이블에 yarn/pnpm/bun 행 추가 |
| skill-init/SKILL.md | Step 4 기술 스택에서 패키지 매니저 자동 감지 안내 |
| skill-onboard/SKILL.md | Step 1 스캔 대상에 yarn.lock/pnpm-lock.yaml/bun.lockb 추가 |

---

## 3. B. 프론트엔드 컨벤션

### 3.1 기존 컨벤션 (13개, 전부 백엔드/범용)

```
api-design.md, cache.md, database.md, deployment.md,
error-handling.md, git-workflow.md, logging.md, message-queue.md,
monitoring.md, naming.md, project-structure.md, security.md, testing.md
```

### 3.2 추가할 컨벤션 (4개)

위치: `.claude/domains/_base/conventions/`

#### frontend-component.md

| 섹션 | 내용 |
|------|------|
| 컴포넌트 구조 | 파일 1개 = 컴포넌트 1개, barrel export 패턴 |
| 네이밍 | PascalCase 컴포넌트, camelCase hooks, kebab-case 파일 |
| Props | interface Props 타입 정의 필수, 기본값 destructuring |
| 합성 패턴 | children/render props/compound 사용 기준 |
| 크기 제한 | 단일 파일 200줄 경고, 300줄 분리 권장 |

#### frontend-testing.md

| 섹션 | 내용 |
|------|------|
| 테스트 피라미드 | Unit(컴포넌트) → Integration(페이지) → E2E(사용자 흐름) |
| React Testing Library | render + screen + userEvent 패턴, getBy/queryBy/findBy 구분 |
| 스토리북 | *.stories.tsx 컴포넌트 문서화, args/play 패턴 |
| E2E | Playwright 권장, 페이지 객체 패턴 |
| 커버리지 | 컴포넌트 80%+, 유틸 함수 90%+ |

#### frontend-styling.md

| 섹션 | 내용 |
|------|------|
| 방식 선택 | CSS Modules (격리 필요) vs Tailwind (유틸리티 우선) |
| 디자인 토큰 | 색상/간격/타이포 변수화, 하드코딩 금지 |
| 반응형 | Mobile-first, breakpoint 3단계 (sm/md/lg) |
| 다크 모드 | CSS 변수 + prefers-color-scheme |
| 금지 패턴 | !important, 인라인 style (동적 제외), 매직넘버 |

#### frontend-state.md

| 섹션 | 내용 |
|------|------|
| 상태 분류 | 서버 상태 (React Query/SWR) vs 클라이언트 상태 (Zustand/Context) |
| 원칙 | 서버 상태는 캐시로 관리, 클라이언트 상태 최소화 |
| 금지 패턴 | 전역 상태에 폼 데이터, prop drilling 3단계 이상 |
| 패턴 | 커스텀 훅으로 상태 로직 추출, selector 패턴 |

### 3.3 컨벤션 트리거

CLAUDE.md.tmpl의 컨벤션 트리거 테이블에 추가:

| 트리거 | 컨벤션 파일 |
|--------|------------|
| `*.tsx`, `*.jsx`, `*.vue` 파일 수정 | `frontend-component.md` |
| `*.test.tsx`, `*.spec.tsx`, `*.stories.tsx` | `frontend-testing.md` |
| `*.css`, `*.scss`, `tailwind.config.*` | `frontend-styling.md` |
| `*Store*`, `*Context*`, `use*.ts` hooks | `frontend-state.md` |

---

## 4. C. 리뷰 에이전트 프론트엔드 인식

### 4.1 pr-reviewer-domain 확장

변경 파일에 프론트엔드 파일(`.tsx`, `.jsx`, `.vue`, `.svelte`)이 포함되면 추가 체크:

| 체크 항목 | 기준 | 심각도 |
|----------|------|--------|
| 컴포넌트 크기 | 단일 파일 300줄 초과 | MINOR |
| Prop drilling | 동일 prop이 3단계+ 전달 | MINOR |
| a11y 기본 | `<img>` alt 누락, `<button>` 내 텍스트 없음, role 미지정 | MAJOR |
| 테스트 존재 | `*.tsx` → `*.test.tsx` 또는 `*.stories.tsx` 존재 | MINOR |
| 인라인 스타일 | 동적 계산 외 style={{}} 사용 | MINOR |

### 4.2 변경 파일

| 파일 | 변경 |
|------|------|
| `.claude/agents/pr-reviewer-domain.md` | 프론트엔드 체크 항목 5개 추가 |

### 4.3 실행 조건

- PR 변경 파일에 `.tsx`/`.jsx`/`.vue`/`.svelte` 확장자가 1개 이상 포함된 경우에만 활성화
- 백엔드 전용 PR에서는 프론트엔드 체크 스킵 (불필요한 검사 방지)

---

## 5. 구현 순서

```
Step 1: 프론트엔드 컨벤션 4개 파일 생성
  └── _base/conventions/frontend-{component,testing,styling,state}.md

Step 2: 패키지 매니저 확장
  ├── skill-impl 빌드 테이블 + Lock 파일 감지 로직
  ├── skill-init 패키지 매니저 감지 안내
  └── skill-onboard 스캔 대상 확장

Step 3: 리뷰 에이전트 프론트엔드 인식
  └── pr-reviewer-domain.md 체크 항목 추가

Step 4: CLAUDE.md.tmpl 컨벤션 트리거 테이블 갱신
```

---

## 6. Out of Scope

| 항목 | 사유 |
|------|------|
| 프론트엔드 전용 도메인 | 기존 _base 컨벤션 확장으로 충분. 별도 도메인은 Phase 2+ |
| SSR/SSG 빌드 최적화 | 프레임워크별 차이가 너무 큼, buildCommands로 대응 |
| Storybook 자동 실행 | CI 영역 (ciDelegation으로 처리) |
| CSS-in-JS (styled-components) | Tailwind/CSS Modules 우선, 요청 시 추가 |

---

## 7. 검증 기준

### 패키지 매니저
- [ ] `yarn.lock` 존재 시 `yarn build/test/lint` 실행
- [ ] `pnpm-lock.yaml` 존재 시 `pnpm build/test/lint` 실행
- [ ] `bun.lockb` 존재 시 `bun run build/test/lint` 실행
- [ ] Lock 파일 복수 존재 시 우선순위(bun > pnpm > yarn > npm) 적용
- [ ] `buildCommands` 설정이 자동 감지보다 우선

### 컨벤션
- [ ] `frontend-component.md` 존재 + *.tsx 수정 시 로드
- [ ] `frontend-testing.md` 존재 + *.test.tsx 수정 시 로드
- [ ] `frontend-styling.md` 존재 + *.css/tailwind.config.* 수정 시 로드
- [ ] `frontend-state.md` 존재 + *Store*/use*.ts 수정 시 로드
- [ ] 기존 13개 컨벤션 동작 유지

### 리뷰 에이전트
- [ ] .tsx 파일 포함 PR에서 a11y 체크 동작
- [ ] .tsx 파일에 대응 .test.tsx 없으면 MINOR 이슈
- [ ] 백엔드 전용 PR에서 프론트엔드 체크 미실행
- [ ] 컴포넌트 300줄 초과 시 MINOR 이슈
