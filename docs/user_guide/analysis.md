# 해석

이 문서는 해석 수행 방법을 정리한다. 결과를 꺼내 보는 방법은
[결과](results.md) 를 참고한다.

해석은 재료 특성이 부여된 `CompoundGeometry` 로부터 `ConcreteSection` 객체를
만드는 것으로 시작한다.

```python
from concreteproperties import ConcreteSection

conc_sec = ConcreteSection(geom)
```

프리스트레스트 단면은 `PrestressedSection` 을 대신 사용한다
([프리스트레스트 해석](prestressed_analysis.md) 참고). 단면에 `SteelStrand` 재료가
있는데 `ConcreteSection` 을 만들려 하면 `ValueError` 가 발생한다.

KDS 설계기준을 적용하려면 단면을 설계기준 객체에 할당한다.

```python
from concreteproperties_kds import KDS

kds = KDS(column_type="tie")
kds.assign_concrete_section(conc_sec)
```

할당 시점에 다음이 수행된다.

- 요소망이 생성되는 철근(`Steel`)이 있으면 `ValueError`
- 단위계가 지정되지 않았으면 SI (N, mm) 로 설정
- 단면 내 철근의 최대 항복강도로부터 $\varepsilon_y$, $\varepsilon_{t,tl}$ 결정
- 순수압축 하중 $P_o$ 와 순수인장 하중 $P_{nt}$ 계산

## 단면 도시

```python
conc_sec.plot_section()
```

## 총단면 제원

`ConcreteSection` 객체를 만들면 총단면 제원이 자동으로 계산된다.

```python
gross = kds.get_gross_properties()
gross.print_results()

# 콘크리트 탄성계수 기준 환산단면
transformed = kds.get_transformed_gross_properties(elastic_modulus=conc.elastic_modulus)
transformed.print_results()
```

## 균열단면 제원

```python
cracked = kds.calculate_cracked_properties(theta=0)
cracked.calculate_transformed_properties(elastic_modulus=conc.elastic_modulus)

print(cracked.m_cr)       # 균열모멘트
print(cracked.d_nc)       # 중립축 깊이
print(cracked.ixx_c_cr)   # 균열단면 2차모멘트
```

균열모멘트는 콘크리트의 응력이 `flexural_tensile_strength`(KDS 의 파괴계수
$f_r = 0.63\lambda\sqrt{f_{ck}}$)에 도달할 때 균열이 발생하는 것으로 보고 계산한다.
균열단면 제원은 콘크리트가 선형탄성이고 압축만 저항한다는 가정으로 구한다.

## 모멘트-곡률 해석

```python
mk_res = kds.moment_curvature_analysis(theta=0, kappa_inc=1e-7)
```

이 해석은 **사용** 응력-변형률 관계를 사용한다. 변위 제어 방식이며 곡률 증분은
`kappa_inc`, `kappa_mult`, `kappa_inc_max`, `delta_m_min`, `delta_m_max` 로 제어한다.

> 모멘트-곡률 해석에는 강도감소계수가 적용되지 않는다. 실제 거동을 보는 해석이기
> 때문이다.

## 극한 휨강도

```python
f_res, u_res, phi = kds.ultimate_bending_capacity(theta=0, n_design=0)
```

**극한** 응력-변형률 관계를 사용한다. 압축연단 변형률을 $\varepsilon_{cu}$ 로 두고
축력 평형을 만족하는 중립축을 찾는다.

KDS 모듈은 여기에 더해, 최외단 인장철근의 순인장변형률로부터 강도감소계수를
결정하고 이를 적용한 설계강도를 함께 반환한다. $\phi$ 가 $\varepsilon_t$ 에
의존하고 $\varepsilon_t$ 는 다시 공칭 축력 $N_d/\phi$ 에 의존하므로 $\phi$ 는
비선형 반복으로 구한다. 자세한 내용은
[KDS 설계기준 문서](design_codes/kds.md#강도감소계수의-비선형-반복) 를 참고한다.

반환값은 다음 세 가지이다.

| 값 | 의미 |
|---|---|
| `f_res` | 설계강도 ($\phi M_n$, $\phi P_n$) |
| `u_res` | 공칭강도 ($M_n$, $P_n$), 중립축 깊이 `d_n`, `k_u` |
| `phi` | 적용된 강도감소계수 |

## P-M 상관도

```python
f_mi, mi, phis = kds.moment_interaction_diagram(theta=0, n_points=24)
```

중립축을 `limits` 사이에서 이동시키며 상관도를 만든다. 기본 `limits` 는
`[("D", 1.0), ("N", 0.0)]` — 압축연단 변형률이 압축측 끝까지 도달한 점부터
순수휨점까지 — 이고, 기본 `control_points` 는 균형점 `[("fy", 1.0)]` 이다.

사용할 수 있는 제어점은 다음과 같다.

| 종류 | 의미 |
|---|---|
| `"D"` | 중립축 깊이 / 단면 깊이 의 비 |
| `"d_n"` | 중립축 깊이 |
| `"fy"` | 최외단 인장철근의 항복비 |
| `"N"` | 공칭 축력 |
| `"kappa0"` | 곡률이 0 인 압축 상태 |

KDS 모듈은 상관도 앞에 최대 공칭 축강도 $0.80 P_o$(나선철근 $0.85 P_o$) 를 무모멘트
점으로 추가하고, 상관도가 이 값을 넘어서면 교점을 구해 수평으로 절단한다. 뒤에는
순수인장점 $P_{nt}$ 를 추가한다.

## 2축 휨 상관도

```python
f_bb, phis = kds.biaxial_bending_diagram(n_design=1200e3, n_points=48)
```

주어진 계수 축력에 대해 $\theta$ 를 $-\pi$ 에서 $\pi$ 까지 돌리며 각 방향의 설계
휨강도를 계산한다.

> **주의** — 현재 구현은 사용자가 **중립축 각도**를 지정하는 방식이다. 비대칭
> 단면에서 중립축 각도가 0 이 아니면 2축 휨모멘트가 발생하고, `m_x` 와 `m_y` 의
> 비가 축력 수준에 따라 달라진다. 설계곡선 가까이에서 작업할 때는 P-M 상관도만으로
> 판단하지 말고 2축 휨 상관도를 함께 확인해야 한다.

## 응력 해석

| 메서드 | 상태 |
|---|---|
| `calculate_uncracked_stress(m_x=..., m_y=..., n=...)` | 비균열 |
| `calculate_cracked_stress(cracked_results=..., m=...)` | 균열 |
| `calculate_service_stress(moment_curvature_results=..., m=...)` | 사용 |
| `calculate_ultimate_stress(ultimate_results=...)` | 극한 |

```python
stress = kds.calculate_ultimate_stress(ultimate_results=u_res)
stress.plot_stress()
```
