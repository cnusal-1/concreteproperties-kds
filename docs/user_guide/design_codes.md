# 설계기준

설계기준 모듈은 `concreteproperties` 를 각국의 철근콘크리트 설계기준 맥락에서
바로 쓸 수 있게 해 준다. 재료 상수를 기준에 맞게 만들어 주고, 공칭강도에
강도감소계수(또는 재료계수)를 적용한 설계강도를 계산한다.

## 지원 기준

| 기준 | 클래스 | 비고 |
|---|---|---|
| **KDS 14 20 (대한민국)** | `concreteproperties_kds.KDS` | [상세 문서](design_codes/kds.md) — 이 저장소에서 추가 |
| AS 3600:2018 (호주) | `concreteproperties.design_codes.AS3600` | 원 패키지 |
| NZS 3101:2006 (뉴질랜드) | `concreteproperties.design_codes.NZS3101` | 원 패키지 |
| NZSEE C5 평가지침 | `concreteproperties.design_codes.NZS3101` | 원 패키지 |
| AS 5100 (호주, 교량) | — | 미구현 |

## KDS 14 20 모듈 구성

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

전체 설계 흐름을 하나로 엮은 예제는
[`examples/17_종합설계.py`](../../examples/17_종합설계.py) 를 참고한다.

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

design_codes/kds
design_codes/kds_loads
design_codes/kds_shear
design_codes/kds_serviceability
design_codes/kds_durability
design_codes/kds_detailing
design_codes/kds_slender
design_codes/kds_psc
design_codes/kds_biaxial
design_codes/equations
```
