# 사용자 가이드

이 문서는 `concreteproperties` 의 작업 흐름을 단계별로 정리하고, 해석에 사용된
가정을 밝힌다.

## 목차

1. [재료](user_guide/materials.md) — 콘크리트·철근 재료와 응력-변형률 관계
2. [형상](user_guide/geometry.md) — 단면 형상 정의와 축 규약
3. [해석](user_guide/analysis.md) — 총단면·균열단면·극한단면 해석
4. [프리스트레스트 해석](user_guide/prestressed_analysis.md) — PSC 단면
5. [결과](user_guide/results.md) — 결과 객체와 후처리
6. [설계기준](user_guide/design_codes.md) — 설계기준 모듈
7. [가정](user_guide/assumptions.md) — 해석 가정과 부호 규약

## 작업 흐름

```
① 재료 정의            KDS.create_concrete_material() / create_steel_material()
        ↓
② 형상 정의            sectionproperties 의 단면 라이브러리 + add_bar_*()
        ↓
③ 단면 객체 생성       ConcreteSection(geom)  (PSC 는 PrestressedSection)
        ↓
④ 설계기준에 할당      KDS.assign_concrete_section(conc_sec)
        ↓
⑤ 해석                 ultimate_bending_capacity() / moment_interaction_diagram() ...
        ↓
⑥ 결과 후처리          print_results() / plot_diagram() / plot_stress()
```

설계기준 모듈을 쓰지 않고 `ConcreteSection` 을 직접 다루어도 되지만, 그 경우
강도감소계수는 사용자가 직접 적용해야 한다.

## 기능

### 해석 종류

- ☑ 철근콘크리트
- ☑ 강-콘크리트 합성
- ☑ 프리스트레스트 콘크리트

### 재료 특성

- ☑ 콘크리트 재료
  - ☑ 사용 응력-변형률 관계
    - ☑ 선형
    - ☑ 선형 (인장 무시)
    - ☑ Eurocode 비선형
    - ☑ Modified Mander 비선형 (구속·비구속 콘크리트)
  - ☑ 극한 응력-변형률 관계
    - ☑ 등가직사각형 응력블록
    - ☑ 이선형(bilinear)
    - ☑ Eurocode 포물선
  - ☑ 휨인장강도(파괴계수)
- ☑ 철근 재료
  - ☑ 완전탄소성
  - ☑ 변형경화 포함 탄소성
- ☑ 강연선 재료
  - ☑ 변형경화 포함 탄소성
  - ☑ PCI Journal (1992) 비선형

### 총단면 제원

- ☑ 단면적 (전체, 콘크리트, 철근, 강연선)
- ☑ 축강성
- ☑ 단면 질량
- ☑ 단면 둘레
- ☑ 단면1차모멘트
- ☑ 탄성 도심
- ☑ 전체좌표계 단면2차모멘트
- ☑ 도심축 단면2차모멘트
- ☑ 주축 회전각
- ☑ 주축 단면2차모멘트
- ☑ 도심축 단면계수
- ☑ 주축 단면계수
- ☑ 프리스트레스에 의한 단면력

### 사용성 해석

- ☑ 균열모멘트
- ☑ 균열단면 제원
- ☑ 모멘트-곡률 곡선

### 극한 해석

- ☑ 극한 휨강도
- ☑ 순수압축 하중
- ☑ 순수인장 하중
- ☑ 상관도
  - ☑ P-M 곡선
  - ☑ 2축 휨 곡선

### 응력 해석

- ☑ 비균열 응력
- ☑ 균열 응력
- ☑ 사용 응력
- ☑ 극한 응력

### 설계기준

- ☑ 설계기준 모듈
  - ☑ **KDS 14 20 (대한민국)** — 이 저장소에서 추가
  - ☑ AS 3600 (호주)
  - ☐ AS 5100 (호주, 교량)
  - ☑ NZS 3101 및 NZSEE C5 (뉴질랜드)
