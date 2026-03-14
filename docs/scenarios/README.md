# BDD 시나리오 문서

## 개요

프레임워크 검증 시나리오를 BDD(Behavior-Driven Development) YAML 형식으로 구조화합니다.
Given/When/Then 패턴으로 기대 동작을 명세하며, 추후 자동화 변환이 가능합니다.

## 파일 구조

```
docs/scenarios/
  ├── README.md              # 이 파일
  ├── full-feature.yaml      # 전체 기능 개발 워크플로우
  └── {workflow-name}.yaml   # 워크플로우별 시나리오
```

## YAML 형식

```yaml
scenario:
  name: "시나리오 이름"
  description: "시나리오 설명"
  workflow: "full-feature | quick-fix | hotfix | ..."

steps:
  - name: "단계 이름"
    skill: "skill-name"
    given:
      - "사전 조건 1"
      - "사전 조건 2"
    when:
      - "실행 동작"
    then:
      - "기대 결과 1"
      - "기대 결과 2"
    files_changed:
      - path: "변경되는 파일 경로"
        action: "create | update | delete"
    on_failure:
      - "실패 시 동작"
```

## 활용

- **skill-validate**: 시나리오 YAML 구조 검증 (필수 필드 확인)
- **skill-retro**: 실행 로그와 시나리오 대조하여 이탈 분석
- **skill-qa**: 테스트 케이스 생성 시 시나리오 참조
