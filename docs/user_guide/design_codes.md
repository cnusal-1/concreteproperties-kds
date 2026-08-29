# 설계기준

설계기준 모듈은 `concreteproperties` 를 각국의 철근콘크리트 설계기준 맥락에서
바로 쓸 수 있게 해 준다. 재료 상수를 기준에 맞게 만들어 주고, 공칭강도에
강도감소계수(또는 재료계수)를 적용한 설계강도를 계산한다.

## 지원 기준

| 기준 | 클래스 | 비고 |
|---|---|---|
| **KDS 14 20 (대한민국, 강도설계법)** | `concreteproperties_kds.KDS` | [상세 문서](design_codes/kds.md) — 이 저장소에서 추가 |
| **KDS 24 (대한민국, 한계상태설계법·교량)** | `concreteproperties_kds.kds24.KDS24` | [상세 문서](design_codes/kds24.md) — 이 저장소에서 추가 |
| AS 3600:2018 (호주) | `concreteproperties.design_codes.AS3600` | 원 패키지 |
| NZS 3101:2006 (뉴질랜드) | `concreteproperties.design_codes.NZS3101` | 원 패키지 |
| NZSEE C5 평가지침 | `concreteproperties.design_codes.NZS3101` | 원 패키지 |
| AS 5100 (호주, 교량) | — | 미구현 |

## 두 갈래 — KDS 14 와 KDS 24

이 저장소는 대한민국의 두 설계 체계를 모두 다룬다.

| | KDS 14 20 | KDS 24 |
|---|---|---|
| 이름 | 콘크리트구조 설계기준 (**강도설계법**) | 교량 설계기준 (**한계상태설계법**) |
| 대상 | 건축물·일반 콘크리트구조 | 교량 |
| 안전율 | 단면 강도감소계수 $\phi$ | 재료계수 $\phi_c$, $\phi_s$ |
| 패키지 | `concreteproperties_kds` 최상위 | `concreteproperties_kds.kds24` |
| 진입점 | `KDS` | `KDS24` |

둘의 차이를 숫자와 그림으로 견준 문서가 따로 있다 —
**[KDS 14 와 KDS 24 의 비교](design_codes/comparison.md)**. 어느 쪽을 쓸지
고민 중이거나, 같은 단면의 두 결과가 왜 다른지 알고 싶다면 여기부터 읽는다.

```{warning}
두 기준을 섞어 쓰면 안 된다. 하중계수와 재료계수·강도감소계수는 한 벌로 보정된
값이라, KDS 24 의 하중조합에 KDS 14 의 $\phi$ 를 쓰면 안전율이 무너진다.
```

## KDS 14 20 모듈 구성 (강도설계법)

KDS 는 단면 해석뿐 아니라 하중조합·전단·사용성·내구성·상세까지 함께 제공한다.
`kds` 모듈이 단면 해석의 중심이고, 나머지는 단면 요소망과 무관한 순수 함수
모듈이다.

| 모듈 | 대상 기준 | 무엇을 구하는가 | 문서 |
|---|---|---|---|
| `kds` | 14 20 10, 14 20 20 | 재료, 설계 휨강도 $\phi M_n$, 강도감소계수 $\phi$, P-M 상관도, 최대 축강도, 연성·최소철근량 | [휨 및 압축](design_codes/kds.md) |
| `loads` | 14 20 10 4.2.2 | 하중조합 12개를 모두 평가해 소요강도 $U$ 와 지배 조합 | [하중조합](design_codes/kds_loads.md) |
| `shear` | 14 20 22 | $V_c$, $V_s$, 최소 전단철근량, 스터럽 간격, 비틀림 $T_n$ | [전단 및 비틀림](design_codes/kds_shear.md) |
| `serviceability` | 14 20 30 | 유효단면2차모멘트, 장기처짐, 최소 두께, 허용처짐, 균열 제어 철근 간격 | [사용성](design_codes/kds_serviceability.md) |
| `durability` | 14 20 40 | 노출등급별 최소 설계기준압축강도와 피복두께 | [내구성](design_codes/kds_durability.md) |
| `detailing` | 14 20 50, 52 | 최소 피복·순간격, 정착길이, 표준갈고리, 겹침이음 | [철근상세·정착·이음](design_codes/kds_detailing.md) |
| `slender` | 14 20 20 4.4 | 세장비, 임계좌굴하중 $P_c$, 모멘트확대계수 $\delta_{ns}$ | [세장 기둥](design_codes/kds_slender.md) |
| `psc` | 14 20 60 | 긴장재 허용응력, 프리스트레스 손실, $f_{ps}$, PSC 단면의 $\phi M_n$ | [프리스트레스트](design_codes/kds_psc.md) |
| `biaxial` | (문헌) | 등하중선법·Bresler 역하중법으로 2축 휨 약산 | [2축 휨 간략식](design_codes/kds_biaxial.md) |

각 코드가 무엇을 정하는 기준인지는
[KDS 14 20 계열이란](../index.md#kds-14-20-계열이란) 을, 설계식과 조문의 1:1
대응은 [설계식 목록](design_codes/equations.md) 을 참고한다.

## KDS 24 서브패키지 구성 (한계상태설계법)

교량은 하중부터 다르다. 그래서 `kds24` 는 단면 해석뿐 아니라 하중조합과
차량활하중까지 함께 담는다.

| 모듈 | 대상 기준 | 무엇을 구하는가 | 문서 |
|---|---|---|---|
| `kds24.materials` | 24 14 21 1.4, 3.1 | 재료계수, 설계 재료강도, 포물선-직선 곡선 | [한계상태설계법](design_codes/kds24.md) |
| `kds24.design_code` | 24 14 21 4.1.1 | `KDS24` 클래스 — $M_{Rd}$, P-M 상관도, 최소편심 | [한계상태설계법](design_codes/kds24.md) |
| `kds24.loads` | 24 12 11 4.1 | 13개 하중조합, 하중수정계수 $\eta$, 교량 등급 | [하중조합과 설계하중](design_codes/kds24_loads.md) |
| `kds24.live_load` | 24 12 21 4.3, 4.4 | KL-510 표준트럭·표준차로하중, 충격 | [하중조합과 설계하중](design_codes/kds24_loads.md) |
| `kds24.shear` | 24 14 21 4.1.2 | 변각 트러스 모델 전단 | [전단](design_codes/kds24_shear.md) |
| `kds24.serviceability` | 24 14 21 4.2, 4.3 | 응력 한계, 균열폭, 처짐, 피로 | [사용성과 피로](design_codes/kds24_serviceability.md) |
| `kds24.deck` | 24 10 11 4.6.2, 24 14 21 4.6.5 | 교량 바닥판의 하중과 휨 설계 | [교량 바닥판](design_codes/kds24_deck.md) |
| `kds24.psc` | 24 14 21 1.5.7, 3.3 | 도입응력 한계, 즉시·장기 손실 | [프리스트레스와 PSC 거더](design_codes/kds24_psc.md) |
| `kds24.girder` | 24 14 21 4.1, 4.2 | PSC I형 거더 단면·합성·검토 | [프리스트레스와 PSC 거더](design_codes/kds24_psc.md) |

KDS 24 로 처음부터 끝까지 설계하는 예제는
[`examples/17_바닥판설계.py`](../../examples/17_바닥판설계.py) (교량 바닥판) 와
[`examples/18_PSC거더설계.py`](../../examples/18_PSC거더설계.py) (PSC I형 거더) 를
참고한다.

## 공통 사용법

모든 설계기준 클래스는 `DesignCode` 를 상속하며 같은 흐름으로 사용한다.

```python
code = <설계기준클래스>()                   # 1) 설계기준 객체
conc = code.create_concrete_material(...)   # 2) 재료 생성
steel = code.create_steel_material(...)
geom = ...                                  # 3) 형상 정의
code.assign_concrete_section(ConcreteSection(geom))   # 4) 단면 할당
f_res, u_res, phi = code.ultimate_bending_capacity()  # 5) 해석
```

`DesignCode` 로부터 상속되어 기준별 저감 없이 그대로 전달되는 메서드는 다음과 같다.

- `get_gross_properties()`
- `get_transformed_gross_properties()`
- `calculate_cracked_properties()`
- `moment_curvature_analysis()`
- `calculate_uncracked_stress()`
- `calculate_cracked_stress()`
- `calculate_service_stress()`
- `calculate_ultimate_stress()`

기준별로 재정의되어 강도감소계수가 적용되는 메서드는 다음과 같다.

- `ultimate_bending_capacity()` → `(설계강도, 공칭강도, phi)`
- `moment_interaction_diagram()` → `(설계 상관도, 공칭 상관도, phi 목록)`
- `biaxial_bending_diagram()` → `(설계 상관도, phi 목록)`

## 상관도 관련 주의

현재 `concreteproperties` 의 상관도는 사용자가 **중립축이 수평축과 이루는 각**을
지정하는 방식이다. 비대칭 단면에서 중립축 각도가 0 이 아니면 2축 휨모멘트가
발생하는데, 이때 `m_x` 와 `m_y` 의 비가 축력 수준에 따라 달라진다. 그 결과
2축 휨 상관도 없이 P-M 상관도만 보면 설계곡선 근처에서 안전율을 잘못 판단할 수 있다.

향후 버전에서는 중립축 각도 대신 **하중각**(`m_x` 대 `m_y` 의 비)을 일정하게
유지하는 방식이 도입될 예정이다.

```{toctree}
:hidden:
:maxdepth: 1

KDS 14 와 KDS 24 의 비교 <design_codes/comparison>
KDS 14 — 휨 및 압축 <design_codes/kds>
KDS 14 — 하중조합 <design_codes/kds_loads>
KDS 14 — 전단 및 비틀림 <design_codes/kds_shear>
KDS 14 — 사용성 <design_codes/kds_serviceability>
KDS 14 — 내구성 <design_codes/kds_durability>
KDS 14 — 철근상세·정착·이음 <design_codes/kds_detailing>
KDS 14 — 세장 기둥 <design_codes/kds_slender>
KDS 14 — 프리스트레스트 <design_codes/kds_psc>
KDS 14 — 2축 휨 간략식 <design_codes/kds_biaxial>
KDS 24 — 한계상태설계법 <design_codes/kds24>
KDS 24 — 하중조합과 설계하중 <design_codes/kds24_loads>
KDS 24 — 전단 <design_codes/kds24_shear>
KDS 24 — 사용성과 피로 <design_codes/kds24_serviceability>
KDS 24 — 교량 바닥판 <design_codes/kds24_deck>
KDS 24 — 프리스트레스와 PSC 거더 <design_codes/kds24_psc>
설계식 목록 <design_codes/equations>
```
