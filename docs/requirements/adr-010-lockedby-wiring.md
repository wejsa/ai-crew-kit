# ADR-010: lockedBy/lockedAt 잠금 서브시스템 배선 (file-membership 하트비트)

> 상태: 채택 (Accepted) — v4.5.0
> 작성일: 2026-06-07
> 결정자: 프레임워크 운영자

---

## 1. 맥락

v2.2.0에서 도입한 lockedBy/lockedAt 잠금 하트비트 서브시스템이 **처음부터 무동작**이었음이 v4.4.1 자체 정합성 분석에서 드러났다.

- **PostToolUse 훅** 하트비트: `select(.status=="in_progress" and (.lockedBy // "") == $sid)` — `$sid`는 훅이 stdin에서 읽는 Claude Code `session_id`(UUID).
- **Stop 훅** 만료: `lockedAt`이 10분(600초) 초과 시 `lockedBy`/`lockedAt`을 null.
- **producer**(crew-plan 조기 잠금): `assignee`/`assignedAt`/`lockTTL`/`lockedFiles`만 설정, **`lockedBy` 미설정**.

→ 어떤 producer도 `lockedBy`를 채우지 않아 훅의 join이 영구 무매칭 → `lockedAt` 미갱신 → 만료 경로도 무동작. 실동작 잠금은 별도 경로(`assignedAt`+`lockTTL`, crew-impl이 `assignedAt`를 활동마다 변이 — schema의 "assignedAt 불변"과 모순)가 담당해 왔다.

## 2. 핵심 제약 (Claude Code, 확인됨)

`session_id`는 SessionStart/PostToolUse/Stop **3개 훅 stdin 모두**에 있고 세션 수명 내내 안정적이나(`/clear`·`/compact`·resume 유지, `/branch`만 새 id), **스킬(모델)이 자신의 session_id를 얻는 문서화된 경로가 없다**(`CLAUDE_SESSION_ID` 등 env 미존재, Bash엔 `CLAUDECODE=1`만).

→ producer 스킬이 `lockedBy=session_id`를 쓸 수 없다. 순진하게 `lockedBy=assignee`를 채우면 훅의 `lockedBy==session_id`는 포맷 불일치로 여전히 무매칭 → `lockedAt`만 set돼 stop.sh가 **10분마다 거짓 만료**(활성 작업 중 lock 해제)를 전 프로젝트에 배포 → harmful.

## 3. 결정

**session_id 매칭을 폐기하고 file-membership 하트비트로 배선한다.**

| 필드 | 역할 (v4.5.0) |
|------|---------------|
| `assignee`+`assignedAt` | **불변** 할당 기록 (crew-impl의 assignedAt 변이 중단 → schema 정합) |
| `lockedBy` | 잠금 보유자 = `assignee` 값 (정보용, session_id 아님) |
| `lockedAt` | **활동 하트비트** — PostToolUse가 **편집 파일 ∈ task.lockedFiles**일 때 갱신 (session_id 불요) |
| `lockTTL` | 만료 윈도우 (≥3600) |

- **하트비트(PostToolUse)**: `편집 파일 ∈ lockedFiles`인 in_progress task의 `lockedAt`을 갱신. `lockedFiles`는 task 전용이라 사실상 소유 세션만 그 파일을 편집 → session 스코핑을 대체.
- **만료 판정(reclaim·Stop 통일)**: `(lockedAt // assignedAt) + lockTTL < now`. `lockedAt` 우선, 없으면 `assignedAt` 폴백(in-flight task 하위호환).
- **producer**: crew-plan 조기 잠금이 `assignedAt`/`lockedBy`(=assignee)/`lockedAt`(=now)을 함께 설정. crew-impl 스텝 시작 시 `lockedFiles` 채우며 `lockedBy`/`lockedAt` 설정. 이후 하트비트는 훅이 자동 수행 → crew-impl의 수동 `assignedAt` 변이 불필요(순효과 단순화).
- **Stop 훅**: 고정 600초 폐기(긴 빌드/사고 중 거짓 만료 위험). 만료 시 `lockedBy`/`lockedAt`만 null(비파괴 — status는 스킬 reclaim이 전체 회수).

## 4. 대안 (기각)

- **SessionStart가 session_id를 파일에 영속화 → 스킬이 read**: 동시 세션이 단일 파일을 덮어써 다른 세션의 id를 읽는 race → 거짓 lockedBy → 거짓 만료. 기각.
- **System 2 제거(assignedAt+lockTTL 단일화)**: 단순하나 v2.2.0이 의도한 활동-하트비트 기반 정확한 liveness 상실. 운영자가 "배선" 선택.

## 5. 영향

- 런타임 잠금 동작 변경 = minor(v4.5.0). 기존 시드는 crew-upgrade/`/plugin update`로 전파. in-flight task(lockedAt=null)는 `// assignedAt` 폴백으로 기존과 동일 동작 → 데이터 마이그레이션 불필요.
- 변경: `backlog.schema.json`(필드 description), `post-tool-use.sh`/`stop.sh`, `crew-plan`/`crew-impl`/`crew-backlog`/`crew-health-check`(SI-03), 4개 hook 테스트 재작성(session_id→file-membership, 600s→lockTTL).

## 6. 후속 (선택)

- ~~`garbage-not-iso` lockedAt이 `fromdateiso8601` 실패 시 0 폴백 → 즉시 만료(M002). 현 동작 유지·문서화.~~ **v4.8.0에서 해소**: 파싱 불가 타임스탬프는 만료로 취급하지 않음(거짓 만료=동시 편집 위험이 미만료=수동 교정 대기보다 위험하다고 재판단) — stop.sh·diagnose.sh 술어 변경, 교정은 `/aick-validate --fix`, 가시화는 diagnose.
- file-membership은 lockedFiles 경로 포맷(프로젝트 상대) 일치에 의존. 훅은 FILE_PATH_NORM(정규화 상대)로 비교. 워크트리/심볼릭 경로 엣지는 graceful degrade(미스 시 미갱신 → assignedAt 폴백이 보호).
