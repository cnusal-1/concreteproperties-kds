# 결과

해석을 수행하면 해석 종류에 맞는 결과 객체가 반환된다. 각 객체는 결과를 출력하거나
도시하는 메서드를 갖는다.

## 총단면 제원

`get_gross_properties()` 는 `GrossProperties` 객체를 반환한다.

```python
gross = kds.get_gross_properties()
gross.print_results()
```

주요 속성은 다음과 같다.

| 속성 | 의미 |
|---|---|
| `total_area`, `concrete_area`, `reinf_lumped_area` | 전체·콘크리트·철근 면적 |
| `e_a` | 축강성 $\sum E A$ |
| `mass`, `perimeter` | 단면 질량, 둘레 |
| `cx`, `cy` | 탄성 도심 |
| `e_ixx_g`, `e_iyy_g`, `e_ixy_g` | 전체좌표계 휨강성 |
| `e_ixx_c`, `e_iyy_c`, `e_ixy_c` | 도심축 휨강성 |
| `phi` | 주축 회전각 |
| `e_i11`, `e_i22` | 주축 휨강성 |
| `conc_ultimate_strain` | 콘크리트 극한변형률 |

> `GrossProperties` 에 저장되는 단면2차모멘트는 탄성계수가 곱해진 **휨강성**
> ($EI$) 이다. 순수한 $I$ 값이 필요하면
> `get_transformed_gross_properties(elastic_modulus=Ec)` 로 환산단면 제원을 얻는다.

```python
transformed = kds.get_transformed_gross_properties(elastic_modulus=conc.elastic_modulus)
transformed.print_results()
print(transformed.ixx_c)   # 콘크리트 기준 환산 도심축 단면2차모멘트
```

## 균열단면 제원

`calculate_cracked_properties()` 는 `CrackedResults` 객체를 반환한다.

| 속성 | 의미 |
|---|---|
| `m_cr` | 균열모멘트 |
| `d_nc` | 균열단면의 중립축 깊이 |
| `theta` | 해석한 중립축 각 |
| `e_ixx_c_cr` 등 | 균열단면 휨강성 |
| `ixx_c_cr` 등 | `calculate_transformed_properties()` 호출 후 생기는 환산 균열단면 제원 |

```python
cracked = kds.calculate_cracked_properties(theta=0)
cracked.calculate_transformed_properties(elastic_modulus=conc.elastic_modulus)
cracked.print_results()
```

`PrestressedSection` 은 `m_cr` 로 (정모멘트 균열모멘트, 부모멘트 균열모멘트) 의
튜플을 반환한다.

## 모멘트-곡률

`MomentCurvatureResults` 객체를 반환한다.

| 속성/메서드 | 의미 |
|---|---|
| `kappa`, `m_x`, `m_y`, `m_xy` | 곡률과 모멘트 이력 |
| `plot_results()` | 모멘트-곡률 곡선 도시 |
| `plot_multiple_results()` | 여러 곡선 비교 |
| `plot_failure_geometry()` | 파괴 시점의 형상 도시 |
| `get_curvature(moment)` | 주어진 모멘트에 대응하는 곡률 |

## 극한 휨강도

`UltimateBendingResults` 객체이다.

| 속성 | 의미 |
|---|---|
| `theta` | 중립축 각 |
| `d_n` | 중립축 깊이 |
| `k_u` | 최외단 인장철근 기준 중립축 깊이비 $c/d$ |
| `n` | 축력 |
| `m_x`, `m_y`, `m_xy` | 휨모멘트 |
| `print_results()` | 결과 출력 |

KDS 모듈의 `ultimate_bending_capacity()` 는 `(설계강도, 공칭강도, phi)` 를 반환한다.

```python
f_res, u_res, phi = kds.ultimate_bending_capacity(n_design=1200e3)

eps_t = kds.net_tensile_strain(theta=0, d_n=u_res.d_n)
print(kds.section_classification(eps_t=eps_t))   # 변화구간단면
print(f"phi = {phi:.3f}")
print(f"phiMn = {f_res.m_x / 1e6:.1f} kN.m")
```

## P-M 상관도

`MomentInteractionResults` 객체이다.

| 메서드 | 의미 |
|---|---|
| `plot_diagram()` | 상관도 도시 |
| `plot_multiple_diagrams()` | 여러 상관도 비교 (공칭 vs 설계) |
| `point_in_diagram(n, m)` | 주어진 (N, M) 이 상관도 내부에 있는지 판정 |
| `get_results_lists(moment)` | 축력·모멘트 목록 반환 |

```python
from concreteproperties.results import MomentInteractionResults

f_mi, mi, phis = kds.moment_interaction_diagram(n_points=24)

MomentInteractionResults.plot_multiple_diagrams(
    [mi, f_mi], ["공칭강도", "설계강도"], fmt="-",
)

# 설계 단면력 (N* = 1500 kN, M* = 300 kN.m) 의 안전 여부
print(f_mi.point_in_diagram(n=1500e3, m=300e6))
```

## 2축 휨 상관도

`BiaxialBendingResults` 객체이다.

| 메서드 | 의미 |
|---|---|
| `plot_diagram()` | $M_x$-$M_y$ 곡선 도시 |
| `plot_multiple_diagrams_2d()` | 여러 축력에 대한 곡선 비교 |
| `plot_multiple_diagrams_3d()` | 3차원 상관면 도시 |
| `point_in_diagram(m_x, m_y)` | 주어진 ($M_x$, $M_y$) 의 안전 여부 |
| `get_results_lists()` | 모멘트 목록 반환 |

## 응력 해석

`StressResult` 객체이다.

| 속성/메서드 | 의미 |
|---|---|
| `concrete_analysis_sections`, `concrete_stresses`, `concrete_forces` | 콘크리트 요소별 응력·힘 |
| `lumped_reinforcement_geometries`, `lumped_reinforcement_stresses`, `lumped_reinforcement_forces` | 철근별 응력·힘 |
| `plot_stress()` | 응력 분포 도시 |
| `sum_forces()`, `sum_moments()` | 단면력 합 |

```python
stress = kds.calculate_ultimate_stress(ultimate_results=u_res)
stress.plot_stress()

conc_stresses = [float(s) for arr in stress.concrete_stresses for s in arr]
steel_stresses = [float(s) for s in stress.lumped_reinforcement_stresses]
print(f"콘크리트 최대 압축응력 = {max(conc_stresses):.2f} MPa")
print(f"철근 최대 인장응력     = {min(steel_stresses):.2f} MPa")
```

## 단위

`concreteproperties` 는 결과 출력 시 단위를 붙여 준다. KDS 모듈은
`assign_concrete_section()` 에서 단위계가 지정되지 않았으면 SI (N, mm) 를 기본값으로
설정한다. 따라서 입력은 N, mm, MPa 로 하고, 출력의 모멘트는 N·mm 이므로 kN·m 로
보려면 $10^6$ 으로 나눈다.

```python
from concreteproperties.post import si_kn_m, si_n_mm

conc_sec.default_units = si_kn_m   # kN, m 로 출력
```
