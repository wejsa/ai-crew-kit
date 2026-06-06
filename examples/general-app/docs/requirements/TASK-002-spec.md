# TASK-002 — 리소스 CRUD API

## 목적
핵심 리소스에 대한 생성/조회/수정/삭제 API를 제공한다. (TASK-001 인증 완료 후 진행)

## 요구사항
- `POST /resources` — 리소스 생성 (인증 필요)
- `GET /resources` — 목록 조회 (페이지네이션: page, size)
- `GET /resources/{id}` — 단건 조회
- `PATCH /resources/{id}` — 부분 수정 (소유자 또는 권한자만)
- `DELETE /resources/{id}` — 삭제 (소프트 삭제)

## 수용 기준
- 존재하지 않는 id는 404, 권한 없는 수정/삭제는 403, 검증 실패는 400
- 목록은 기본 size=20, 최대 100
- CRUD 단위·통합 테스트 커버리지 ≥ 80%

## 비고
범용 예제용 명세입니다. 실제 프로젝트에서는 `/skill-plan`이 스텝별 설계로 확장합니다.
