# 프리스트레스트 해석

프리스트레스트 콘크리트 단면은 `ConcreteSection` 대신 `PrestressedSection` 객체로
해석한다.

```python
from concreteproperties import PrestressedSection

ps_sec = PrestressedSection(geom)
```

강연선에 의한 축력과 휨모멘트는 모든 해석에 자동으로 포함된다.

## 강연선 재료

```python
import concreteproperties.stress_strain_profile as ssp
from concreteproperties import SteelStrand

strand = SteelStrand(
    name="SWPC 7B 15.2mm",
    density=7.85e-6,
    stress_strain_profile=ssp.StrandHardening(
        yield_strength=1600,
        elastic_modulus=195e3,
        fracture_strain=0.035,
        breaking_strength=1860,
    ),
    colour="slategrey",
    prestress_stress=1200,   # 유효 프리스트레스
)
```

KDS 14 20 62(프리스트레스트 콘크리트 구조)의 강연선 규격은 KS D 7002 를 따른다.
대표적으로 SWPC 7B 는 $f_{pu} = 1860$ MPa, $f_{py} \ge 0.85 f_{pu}$ 이다.

> **주의** — 이 저장소의 KDS 설계기준 모듈은 **철근콘크리트 단면**을 대상으로 한다.
> `KDS.assign_concrete_section()` 은 `ConcreteSection` 을 전제로 하며,
> `PrestressedSection` 에 대한 강도감소계수 규정(KDS 14 20 62)은 구현되어 있지 않다.
> PSC 단면은 `PrestressedSection` 의 메서드를 직접 사용하고, 강도감소계수는
> 사용자가 적용한다.

## 단면 도시

```python
ps_sec.plot_section()
```

## 총단면 제원

`PrestressedSection` 객체를 만들면 총단면 제원이 자동으로 계산된다.

## 균열단면 제원

일반 철근콘크리트 단면과 달리, PSC 단면의 균열단면 제원은 자중 등 외부 하중에
민감하다. 따라서 `m_ext` 와 `n_ext` 로 외부 단면력을 함께 준다.

```python
cracked = ps_sec.calculate_cracked_properties(m_ext=500e6, n_ext=0)
```

> `m_ext` 와 `n_ext` 를 프리스트레스와 조합한 결과가 콘크리트에 인장을 발생시켜야
> 한다. 단면 전체가 압축이면 균열해석을 할 수 없고 `ValueError` 가 발생한다.
> 콘크리트의 휨인장강도를 0 으로 두고 정·부 균열모멘트를 확인해 보면 쉽게 알 수 있다.

## 모멘트-곡률 해석

```python
mk_res = ps_sec.moment_curvature_analysis(kappa_inc=1e-7)
```

## 극한 휨강도

```python
u_res = ps_sec.ultimate_bending_capacity()
```

## 상관도

P-M 상관도와 2축 휨 상관도는 프리스트레스트 단면에 대해 **아직 구현되어 있지 않다**.

## 응력 해석

| 메서드 | 상태 |
|---|---|
| `calculate_uncracked_stress()` | 비균열 |
| `calculate_cracked_stress(cracked_results=...)` | 균열 |
| `calculate_service_stress(moment_curvature_results=...)` | 사용 |
| `calculate_ultimate_stress(ultimate_results=...)` | 극한 |

균열 응력을 계산하려면 먼저 `calculate_cracked_properties()` 로 균열단면 제원을
구하고 그 결과를 넘겨야 한다.
