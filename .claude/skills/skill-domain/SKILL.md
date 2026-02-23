---
name: skill-domain
description: 도메인 관리 - 조회, 전환, 커스터마이징, 워크플로우 정의. /skill-domain으로 호출합니다.
disable-model-invocation: true
allowed-tools: Bash(git:*), Read, Write, Glob, AskUserQuestion
argument-hint: "[list|switch|add-doc|add-checklist|add-workflow|export] [options]"
---

# skill-domain: 도메인 관리

## 실행 조건
- 사용자가 `/skill-domain` 또는 "도메인 정보 보여줘" 요청 시

## 명령어

```
/skill-domain                      # 현재 도메인 정보
/skill-domain list                 # 사용 가능한 도메인 목록
/skill-domain switch {domain}      # 도메인 전환
/skill-domain add-doc {path}       # 참고자료 추가
/skill-domain add-checklist {path} # 체크리스트 추가
/skill-domain add-workflow {name}   # 커스텀 워크플로우 정의
/skill-domain export {name}        # 커스텀 도메인으로 내보내기
```

---

## 실행 플로우

### 기본: 현재 도메인 정보

```bash
# project.json에서 도메인 확인
cat .claude/state/project.json | jq '.domain'

# 도메인 설정 로드
cat .claude/domains/{domain}/domain.json
```

**출력 예시:**
```
## 현재 도메인: fintech 🏦

### 설명
결제/정산/금융 서비스를 위한 도메인

### 적용 체크리스트
- ✅ common.md (공통)
- ✅ security-basic.md (공통)
- ✅ compliance.md (도메인)
- ✅ domain-logic.md (도메인)
- ✅ security.md (도메인)

### 참고자료
- payment-flow.md — 결제 플로우
- settlement.md — 정산 프로세스
- refund-cancel.md — 취소/환불 정책
- security-compliance.md — PCI-DSS, 전금법
- api-design.md — API 설계 가이드
- error-handling.md — 에러 처리

### 키워드 매핑
- 결제, 승인, 인증 → payment-flow.md
- 정산, 수수료 → settlement.md
- 취소, 환불 → refund-cancel.md
```

---

### list: 사용 가능한 도메인 목록

```bash
# 레지스트리 로드
cat .claude/domains/_registry.json
```

**출력 예시:**
```
## 사용 가능한 도메인

| 도메인 | 아이콘 | 설명 | 상태 |
|--------|--------|------|------|
| fintech | 🏦 | 결제/정산/금융 서비스 | stable |
| ecommerce | 🛒 | 이커머스/마켓플레이스 | stable |
| healthcare | 🏥 | 의료/헬스케어 | beta |
| saas | ☁️ | SaaS/B2B 플랫폼 | beta |
| general | 🔧 | 범용 (도메인 특화 없음) | stable |

### 현재 선택: fintech 🏦

도메인 전환: `/skill-domain switch {도메인명}`
```

---

### switch: 도메인 전환

**Step 1: 현재 상태 확인**
```bash
cat .claude/state/project.json | jq '{domain, name}'
```

**Step 2: 대상 도메인 유효성 검증**
```bash
# 도메인 존재 확인
ls .claude/domains/{target}/domain.json
```

**Step 3: 전환 영향 분석**

```
## 도메인 전환: fintech → ecommerce

### 변경 사항

#### 제거되는 체크리스트
- compliance.md (PCI-DSS, 전금법)
- domain-logic.md (결제 도메인 로직)
- security.md (토큰 보안)

#### 추가되는 체크리스트
- compliance.md (전자상거래법)
- domain-logic.md (주문 도메인 로직)
- performance.md (대용량 트래픽)

#### 제거되는 참고자료
- payment-flow.md, settlement.md, ...

#### 추가되는 참고자료
- order-flow.md, inventory.md, shipping.md, ...

계속하시겠습니까?
```

**Step 4: 전환 실행**

```bash
# 1. 기존 CLAUDE.md에서 커스텀 섹션 추출
#    <!-- CUSTOM_SECTION_START --> 와 <!-- CUSTOM_SECTION_END --> 사이 내용 저장
CUSTOM_CONTENT=$(sed -n '/<!-- CUSTOM_SECTION_START -->/,/<!-- CUSTOM_SECTION_END -->/p' CLAUDE.md | sed '1d;$d')

# 2. project.json 업데이트
#    domain 필드 변경
#    conventions.taskPrefix 도메인 기본값으로 업데이트

# 3. CLAUDE.md 재생성
#    템플릿 로드 → 마커 치환 → 새 CLAUDE.md 생성
cat .claude/templates/CLAUDE.md.tmpl
# 마커 치환 후 저장

# 4. 커스텀 섹션 복원
#    새 CLAUDE.md의 커스텀 섹션 마커 사이에 기존 내용 삽입
```

**커스텀 섹션 보존 규칙:**
- `<!-- CUSTOM_SECTION_START -->` 와 `<!-- CUSTOM_SECTION_END -->` 사이 내용 유지
- 도메인 전환 시 자동 복원
- 상세 로직: `.claude/templates/TEMPLATE-ENGINE.md` 참조

**Step 5: 전환 완료 안내**

```
## ✅ 도메인 전환 완료

### 변경된 설정
- **도메인**: fintech → ecommerce
- **Task 접두사**: PG → EC
- **체크리스트**: 5개 → 4개

### 보존된 설정
- ✅ 커스텀 섹션 (프로젝트 특화 규칙)

### 주의사항
- 기존 Task ID는 변경되지 않습니다
- 새 Task부터 새 접두사가 적용됩니다
- 코드 리뷰 시 새 도메인 체크리스트가 적용됩니다
- **커스텀 규칙은 그대로 유지됩니다**

### 다음 단계
- `/skill-docs` — 새 도메인 참고자료 확인
- `/skill-status` — 현재 상태 확인
```

---

### add-doc: 참고자료 추가

**사용법:**
```
/skill-domain add-doc docs/my-custom-guide.md
/skill-domain add-doc "https://example.com/guide.md"
```

**Step 1: 파일 확인**
```bash
# 로컬 파일인 경우
cat {path}

# URL인 경우 (WebFetch 사용)
```

**Step 2: 키워드 설정**

```
## 참고자료 추가

### 파일 정보
- **파일명**: my-custom-guide.md
- **크기**: 5.2KB
- **라인 수**: 150

### 키워드 매핑
이 참고자료를 자동 참조할 키워드를 입력해주세요:

예: 인증, OAuth, 로그인

(쉼표로 구분)
```

**Step 3: 파일 복사 및 등록**
```bash
# 도메인 docs 디렉토리로 복사
cp {source} .claude/domains/{domain}/docs/{filename}

# domain.json의 keywordMapping 업데이트
```

**Step 4: 완료 안내**
```
## ✅ 참고자료 추가 완료

- **파일**: my-custom-guide.md
- **위치**: .claude/domains/fintech/docs/
- **키워드**: 인증, OAuth, 로그인

코드에서 위 키워드 사용 시 자동으로 참조됩니다.
```

---

### add-checklist: 체크리스트 추가

**사용법:**
```
/skill-domain add-checklist docs/my-checklist.md
```

**Step 1: 파일 확인 및 형식 검증**
```bash
cat {path}
```

**체크리스트 형식 검증:**
- 마크다운 테이블 형식 확인
- 필수 컬럼: 항목, 설명, 심각도
- 심각도 값: CRITICAL, MAJOR, MINOR

**Step 2: 적용 시점 설정**

```
## 체크리스트 추가

### 파일 정보
- **파일명**: my-checklist.md
- **항목 수**: 15개

### 적용 시점 선택
이 체크리스트를 언제 적용할까요?

1. 코드 리뷰 시 (review)
2. PR 리뷰 시 (pr-review)
3. 둘 다 (both)
```

**Step 3: 파일 복사 및 등록**
```bash
# 도메인 checklists 디렉토리로 복사
cp {source} .claude/domains/{domain}/checklists/{filename}

# domain.json의 checklists 배열에 추가
```

**Step 4: 완료 안내**
```
## ✅ 체크리스트 추가 완료

- **파일**: my-checklist.md
- **위치**: .claude/domains/fintech/checklists/
- **적용 시점**: 코드 리뷰, PR 리뷰

코드 리뷰 시 이 체크리스트가 자동으로 적용됩니다.
```

---

### add-workflow: 커스텀 워크플로우 정의

**사용법:**
```
/skill-domain add-workflow my-workflow
```

사전 정의된 6개 워크플로우 외에 프로젝트 고유 워크플로우를 생성합니다.

**Step 1: 워크플로우 정보 수집**

AskUserQuestion으로 수집:
```
## 커스텀 워크플로우 생성

### 워크플로우 이름
예: hotfix, data-migration, api-integration

### 설명
이 워크플로우의 목적을 설명해주세요.

### 스텝 정의
각 스텝에 사용할 스킬을 선택하세요:

1. 스텝명 → 스킬 (예: "분석 → skill-plan")
2. 스텝명 → 스킬
3. ...

### 게이트 조건 (선택)
스텝 간 진행 조건이 있으면 지정:
- user_approval: 사용자 승인 필요
- build_success: 빌드 성공 필수
- test_pass: 테스트 통과 필수
```

**Step 2: YAML 생성**

`.claude/workflows/{name}.yaml` 생성:

```yaml
name: {워크플로우명}
description: {설명}
created: {timestamp}
custom: true

steps:
  - name: {스텝명}
    skill: {스킬명}
    gate: {게이트 조건}
  - name: {스텝명}
    skill: {스킬명}

error_handling:
  on_failure: pause
  on_timeout: notify
```

**Step 3: 검증**
- 참조된 스킬 존재 확인
- YAML 문법 유효성 확인
- 기존 워크플로우명 중복 확인

**Step 4: 완료 안내**
```
## ✅ 커스텀 워크플로우 생성 완료

- **이름**: {name}
- **위치**: .claude/workflows/{name}.yaml
- **스텝 수**: {N}개

### 사용 방법
agent-pm에게 이 워크플로우로 작업 요청:
"my-workflow 워크플로우로 진행해줘"

### 기존 워크플로우 목록
1. full-feature (기본)
2. quick-fix
3. spike
4. review-only
5. docs-only
6. migration
7. {name} ← 새로 추가됨
```

---

### export: 커스텀 도메인으로 내보내기

**사용법:**
```
/skill-domain export my-custom-domain
```

**Step 1: 현재 도메인 분석**
```bash
# 현재 도메인 설정 로드
cat .claude/domains/{current}/domain.json

# 추가된 커스텀 파일 확인
ls .claude/domains/{current}/docs/
ls .claude/domains/{current}/checklists/
```

**Step 2: 내보내기 확인**

```
## 도메인 내보내기

### 현재 도메인: fintech
### 새 도메인명: my-custom-domain

### 포함될 내용
- domain.json (설정)
- docs/ (8개 파일)
- checklists/ (3개 파일)
- glossary.md
- error-codes/

### 커스터마이징 항목
- ✅ my-custom-guide.md (추가됨)
- ✅ my-checklist.md (추가됨)

계속하시겠습니까?
```

**Step 3: 도메인 생성**
```bash
# 새 도메인 디렉토리 생성
mkdir -p .claude/domains/{new-domain}

# 현재 도메인 복사
cp -r .claude/domains/{current}/* .claude/domains/{new-domain}/

# domain.json 업데이트 (id, name 변경)

# _registry.json에 추가
```

**Step 4: 완료 안내**

```
## ✅ 도메인 내보내기 완료

### 생성된 도메인
- **ID**: my-custom-domain
- **위치**: .claude/domains/my-custom-domain/

### 구조
```
my-custom-domain/
├── domain.json
├── README.md
├── docs/
│   ├── payment-flow.md
│   ├── my-custom-guide.md (커스텀)
│   └── ...
├── checklists/
│   ├── compliance.md
│   ├── my-checklist.md (커스텀)
│   └── ...
├── glossary.md
└── error-codes/
```

### 다음 단계
1. 다른 프로젝트에서 사용:
   ```
   /skill-init
   # 도메인 선택: my-custom-domain
   ```

2. 팀과 공유:
   - `.claude/domains/my-custom-domain/` 디렉토리를 Git에 커밋
   - 또는 별도 저장소로 관리
```

---

## 에러 처리

### 도메인 없음
```
## ❌ 도메인을 찾을 수 없습니다

**요청한 도메인**: {domain}

### 사용 가능한 도메인
- fintech, ecommerce, healthcare, saas, general

### 해결 방법
1. 도메인명 확인: `/skill-domain list`
2. 올바른 도메인으로 재시도
```

### 프로젝트 미초기화
```
## ❌ 프로젝트가 초기화되지 않았습니다

`.claude/state/project.json` 파일이 없습니다.

### 해결 방법
먼저 프로젝트를 초기화하세요:
```
/skill-init
```
```

### 체크리스트 형식 오류
```
## ❌ 체크리스트 형식 오류

**파일**: {filename}
**오류**: 심각도 컬럼이 없습니다

### 올바른 형식
| 항목 | 설명 | 심각도 |
|------|------|--------|
| 항목1 | 설명1 | CRITICAL |
| 항목2 | 설명2 | MAJOR |

### 심각도 값
- CRITICAL: 필수 (위반 시 차단)
- MAJOR: 중요 (경고)
- MINOR: 권장 (정보)
```

---

## Layered Override 확인

도메인 정보 표시 시 적용 레이어 표시:

```
## 현재 설정 (Layered Override)

### 체크리스트 적용 순서
1. _base/checklists/common.md ← 공통
2. _base/checklists/security-basic.md ← 공통
3. fintech/checklists/compliance.md ← 도메인
4. fintech/checklists/domain-logic.md ← 도메인
5. fintech/checklists/security.md ← 도메인

### 설정 우선순위
| 설정 | 값 | 출처 |
|------|-----|------|
| taskPrefix | PG | project.json (사용자) |
| branchStrategy | git-flow | domain.json |
| commitFormat | conventional | _base |
| prLineLimit | 500 | _base |
```

---

## 주의사항

- 도메인 전환 시 기존 Task ID는 유지됨
- 새 Task부터 새 도메인의 taskPrefix 적용
- 커스텀 체크리스트는 도메인별로 관리됨
- export된 도메인은 _registry.json에 자동 등록됨
