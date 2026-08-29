# 사용자 가이드

이 문서는 `concreteproperties` 의 작업 흐름을 단계별로 정리하고, 해석에 사용된
가정을 밝힌다.

## 목차

```{toctree}
:maxdepth: 1

user_guide/materials
user_guide/geometry
user_guide/analysis
user_guide/prestressed_analysis
user_guide/results
user_guide/design_codes
user_guide/assumptions
```

KDS 모듈별 상세 문서는 [설계기준](user_guide/design_codes.md) 에서 찾을 수 있다.
강도설계법(KDS 14 20)과 한계상태설계법(KDS 24)의 두 갈래로 나뉘어 있고, 둘의
차이를 견준 문서는 [KDS 14 와 KDS 24 의 비교](user_guide/design_codes/comparison.md)
에 있다.

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

### KDS 모듈이 추가로 제공하는 검토

- ☑ 하중조합과 소요강도 (KDS 14 20 10 4.2.2)
- ☑ 전단 설계 — $V_c$, $V_s$, 최소 전단철근량, 스터럽 간격 (KDS 14 20 22)
- ☑ 비틀림 설계 — $T_{cr}$, $T_n$, 종방향 철근, 단면 크기 (KDS 14 20 22)
- ☑ 처짐 — 유효단면2차모멘트, 장기처짐, 최소 두께, 허용처짐 (KDS 14 20 30)
- ☑ 균열 제어 — 휨철근 간격 제한 (KDS 14 20 30)
- ☑ 수축·온도철근 (KDS 14 20 30)
- ☑ 내구성 — 노출등급 16종의 최소 설계기준압축강도 (KDS 14 20 40)
- ☑ 최소 피복두께와 철근 간격 (KDS 14 20 50)
- ☑ 정착길이·표준갈고리·겹침이음 (KDS 14 20 52)
- ☑ 세장 기둥의 모멘트확대계수법 (KDS 14 20 20 4.4)
- ☑ 프리스트레스 손실과 허용응력 (KDS 14 20 60)
- ☑ 2축 휨 간략식 (Bresler) 과 엄밀해 비교
- ☐ 2방향 슬래브, 스트럿-타이, 뚫림전단, 내진상세
