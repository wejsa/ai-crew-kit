# TASK-001 — 사용자 인증 API

## 목적
JWT 기반 사용자 인증(로그인/로그아웃/토큰 갱신)을 제공한다.

## 요구사항
- `POST /auth/login` — 자격증명 검증 → access/refresh 토큰 발급
- `POST /auth/refresh` — refresh 토큰으로 access 토큰 재발급
- `POST /auth/logout` — refresh 토큰 무효화
- 비밀번호는 단방향 해시(bcrypt 등)로 저장, 평문 로깅 금지

## 수용 기준
- 잘못된 자격증명은 401, 만료 토큰은 401, 형식 오류는 400
- access 토큰 만료 15분 / refresh 토큰 만료 14일
- 인증 관련 단위·통합 테스트 커버리지 ≥ 80%

## 비고
범용 예제용 명세입니다. 실제 프로젝트에서는 `/crew-plan`이 스텝별 설계로 확장합니다.
