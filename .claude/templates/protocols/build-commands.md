# 빌드/테스트/린트 명령 표 (SSOT)

> **단일 진실 소스** — 스택별 빌드·테스트·린트 명령과 패키지 매니저 감지 규칙의 정본.
> 소비 스킬: `aick-impl`(Step 5) · `aick-release`(Step 3) · `aick-fix`(Step 4/5) · `aick-hotfix`(Step 4) · `aick-rollback`(Step 4) · `aick-onboard`(빌드 명령 감지). **각 스킬에 표를 복제하지 말 것** — v4.8.0에서 발산(impl 12스택 vs release 3스택) 해소를 위해 추출됨.
>
> 경로의 `${CLAUDE_PLUGIN_ROOT}`는 플러그인 설치 시 절대경로로 치환된다. clone/seed 설치라 리터럴로 남아 있으면 접두를 제거하고 프로젝트 로컬 `.claude/templates/protocols/build-commands.md`로 읽는다.

## 적용 규칙

1. `project.json`의 `buildCommands`(build/test/lint) **우선** — 설정된 키만 사용, 미설정 키는 아래 폴백.
2. 미설정 시 `techStack` 기반 폴백 (아래 스택 표).
3. JS/TS 계열은 **패키지 매니저 자동 감지** 표가 스택 표의 npm 표기를 덮어쓴다 (Lock 파일 기준).
4. 표에 없는 스택: 빌드 게이트를 스킵하지 말고 사용자에게 명령을 1회 질문 → `buildCommands`에 기록 제안.

## 스택 표

| 스택 | 빌드 | 테스트 | 린트 |
|------|------|--------|------|
| spring-boot-kotlin | `./gradlew build` | `./gradlew test` | `./gradlew ktlintCheck` |
| spring-boot-java (Gradle) | `./gradlew build` | `./gradlew test` | `./gradlew checkstyleMain` |
| spring-boot-java (Maven) | `mvn package` | `mvn test` | `mvn checkstyle:check` |
| nodejs-typescript | `npm run build` | `npm test` | `npm run lint` |
| python-fastapi | - | `pytest` | `ruff check .` |
| python-django | `python manage.py check` | `pytest` | `ruff check .` |
| go | `go build ./...` | `go test ./...` | `golangci-lint run` |
| nextjs | `next build` | `vitest` 또는 `jest` | `next lint` |
| react-vite | `vite build` | `vitest` | `eslint .` |
| vue-nuxt | `nuxt build` | `vitest` | `eslint .` |
| vue | `vite build` | `vitest` | `eslint .` |
| astro | `astro build` | `vitest` | `eslint .` |

## 패키지 매니저 자동 감지 (Lock 파일 기준, `buildCommands` 미설정 시)

| Lock 파일 | 매니저 | 빌드 | 테스트 | 린트 |
|-----------|--------|------|--------|------|
| `bun.lockb` | bun | `bun run build` | `bun test` | `bun run lint` |
| `pnpm-lock.yaml` | pnpm | `pnpm build` | `pnpm test` | `pnpm lint` |
| `yarn.lock` | yarn | `yarn build` | `yarn test` | `yarn lint` |
| `package-lock.json` | npm | `npm run build` | `npm test` | `npm run lint` |

복수 Lock 파일 존재 시 위 우선순위(bun > pnpm > yarn > npm) 적용.
