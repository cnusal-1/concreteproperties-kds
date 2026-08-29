# KDS 24 — 한계상태설계법 (교량)

`concreteproperties_kds.kds24` 는 **KDS 24 14 21 콘크리트교 설계기준
(한계상태설계법)** 을 구현한 서브패키지다. 교량 설계에 필요한 하중(KDS 24 12 11,
24 12 21)까지 함께 다룬다.

KDS 14 와의 차이를 먼저 잡고 들어가는 편이 빠르다 —
[KDS 14 와 KDS 24 의 비교](comparison.md) 를 먼저 읽기를 권한다.

## 서브패키지 구성

| 모듈 | 대상 기준 | 무엇을 구하는가 | 문서 |
|---|---|---|---|
| `kds24.materials` | 24 14 21 1.4, 3.1 | 재료계수, 설계 재료강도, 포물선-직선 곡선, 등가블록 계수 | 이 문서 |
| `kds24.design_code` | 24 14 21 4.1.1 | `KDS24` 클래스 — 설계휨강도 $M_{Rd}$, P-M 상관도, 2축 휨, 최소편심 | 이 문서 |
| `kds24.loads` | 24 12 11 4.1 | 13개 하중조합, 하중수정계수 $\eta$, 교량 등급 | [하중조합과 설계하중](kds24_loads.md) |
| `kds24.live_load` | 24 12 21 4.3, 4.4 | KL-510 표준트럭·표준차로하중, 다차로 재하계수, 충격 | [하중조합과 설계하중](kds24_loads.md) |
| `kds24.shear` | 24 14 21 4.1.2 | 변각 트러스 모델 전단 | [전단](kds24_shear.md) |
| `kds24.serviceability` | 24 14 21 4.2, 4.3 | 응력 한계, 균열폭, 처짐, 피로 | [사용성과 피로](kds24_serviceability.md) |

## 핵심 — 재료계수

KDS 24 는 단면에 곱하는 강도감소계수가 **없다.** 대신 재료마다 재료계수를 곱해
설계 재료강도를 만든다 (표 1.4-1).

| 한계상태 | 콘크리트 $\phi_c$ | 강재 $\phi_s$ |
|---|---|---|
| 극한 | 0.65 | 0.90 |
| 극단상황 | 0.65 | 0.90 |
| 사용 | 1.00 | 1.00 |
| 피로 | 1.00 | 1.00 |

$$
f_{cd} = \phi_c \cdot \alpha \cdot f_{ck}
\quad (\alpha = 0.85, \ \text{식 (3.1-47)})
\qquad
f_{yd} = \phi_s f_y
$$

```python
from concreteproperties_kds.kds24 import (
    design_compressive_strength, design_yield_strength, material_factors,
)

material_factors("극한")                        # (0.65, 0.90)
design_compressive_strength(fck=40)             # 22.10 MPa
design_yield_strength(fy=400)                   # 360.0 MPa

# 사용한계상태에서는 재료계수가 1.0 이라 기준값이 그대로 나온다
design_compressive_strength(fck=40, phi_c=1.0)  # 34.00 MPa
```

**설계의 의도.** 강도설계법의 $\phi$ 하나는 "이 단면이 얼마나 못 미더운가"를 뭉뚱그린
값이라, 콘크리트가 지배하는 파괴와 철근이 지배하는 파괴를 구분하지 못한다.
한계상태설계법은 재료마다 불확실성이 다르다는 사실 — 공장에서 만드는 철근은
현장에서 치는 콘크리트보다 훨씬 예측이 잘 된다 — 을 계수에 그대로 담는다.
$\phi_s$ = 0.90 이 $\phi_c$ = 0.65 보다 훨씬 큰 이유가 그것이다.

## 응력-변형률 관계

곡선의 **형상은 KDS 14 표 4.1-1 과 같고, 최대값만 다르다.** 두 기준이 같은 실험
자료를 쓰기 때문이다.

$$
f_c = f_{cd} \left[ 1 - \left( 1 - \frac{\varepsilon_c}{\varepsilon_{co}}
\right)^n \right] \quad (0 \le \varepsilon_c \le \varepsilon_{co}),
\qquad
f_c = f_{cd} \quad (\varepsilon_{co} < \varepsilon_c \le \varepsilon_{cu})
$$

표 3.1-3 의 계수:

| $f_{ck}$ (MPa) | $\le 40$ | 50 | 60 | 70 | 80 | 90 |
|---|---|---|---|---|---|---|
| $n$ | 2.00 | 1.92 | 1.50 | 1.29 | 1.22 | 1.20 |
| $\varepsilon_{co}$ | 0.0020 | 0.0021 | 0.0022 | 0.0023 | 0.0024 | 0.0025 |
| $\varepsilon_{cu}$ | 0.0033 | 0.0032 | 0.0031 | 0.0030 | 0.0029 | 0.0028 |

```python
from concreteproperties_kds.kds24 import curve_parameters, design_stress, equivalent_block

curve_parameters(fck=40)              # (2.0, 0.0020, 0.0033)
design_stress(fck=40, eps_c=0.0015)   # 20.72 MPa
equivalent_block(fck=40)              # (0.798, 0.412) — 수치적분으로 구한 등가블록 계수
```

`equivalent_block()` 은 포물선-직선을 수치적분해 등가직사각형 블록의 계수
$(\alpha_{eq}, \beta_{eq})$ 를 돌려준다. KDS 는 반올림해 0.80 / 0.40 으로 싣지만,
$\beta$ 는 실제로 0.412 라 표의 반올림 폭이 조금 크다.

## 재료 상수

| 함수 | 반환 | 근거 |
|---|---|---|
| `mean_compressive_strength(fck)` | $f_{cm} = f_{ck} + \Delta f$ | 식 (3.1-1) |
| `mean_tensile_strength(fck)` | $f_{ctm} = 0.30 f_{cm}^{2/3}$ | 3.1.2.3 |
| `characteristic_tensile_strength(fck)` | $f_{ctk} = 0.70 f_{ctm}$ | 3.1.2.3 |
| `design_tensile_strength(fck, phi_c)` | $f_{ctd} = \phi_c f_{ctk}$ | 식 (3.1-48) |
| `elastic_modulus(fck, m_c)` | $E_c = 0.077 m_c^{1.5} \sqrt[3]{f_{cm}}$ | 3.1.2.2(1) |

```{note}
KDS 24 는 탄성계수의 일반식만 두는데, 보통중량 콘크리트($m_c$ = 2,300 kg/m³)를
넣으면 $0.077 \times 2300^{1.5}$ = 8,493 이 나온다. KDS 14 20 10 이 8,500 으로
반올림해 식 (4.3-2) 를 따로 둔 것과 0.08 % 차이라, 사실상 같은 식이다.
```

## `KDS24` 설계기준 클래스

```python
from concreteproperties import ConcreteSection
from sectionproperties.pre.library import concrete_rectangular_section

from concreteproperties_kds.kds24 import KDS24

code = KDS24()                        # 극한한계상태의 재료계수 (0.65, 0.90)
conc = code.create_concrete_material(compressive_strength=40)
steel = code.create_steel_material(yield_strength=400)

geom = concrete_rectangular_section(
    d=600, b=400,
    dia_top=22, area_top=387.1, n_top=0, c_top=50,
    dia_bot=22, area_bot=387.1, n_bot=4, c_bot=50,
    n_circle=16, conc_mat=conc, steel_mat=steel,
)
code.assign_concrete_section(ConcreteSection(geom))

result = code.design_bending_capacity()
print(f"M_Rd = {result.m_x / 1e6:.1f} kN.m")   # M_Rd = 282.3 kN.m
```

`create_concrete_material()` 이 만든 재료에는 **재료계수가 이미 들어 있다.**
그래서 단면을 풀면 나오는 값이 곧 설계강도이고, 메서드 이름도
`ultimate_...` 가 아니라 `design_bending_capacity()` 다.

### 메서드

| 메서드 | 반환 |
|---|---|
| `create_concrete_material(compressive_strength, m_c=2300, colour=...)` | `Concrete` |
| `create_steel_material(yield_strength=400, fracture_strain=0.05, colour=...)` | `SteelBar` |
| `assign_concrete_section(concrete_section)` | — |
| `design_bending_capacity(theta=0, n_design=0)` | 설계강도 결과 ($\phi$ 는 없다) |
| `moment_interaction_diagram(theta=0, **kwargs)` | 설계 상관도 **하나** |
| `biaxial_bending_diagram(n_design=0, **kwargs)` | 설계 2축 휨 상관도 |
| `squash_tensile_load()` | $(N_{Rd,\max},\ N_{Rd,\min})$ |
| `net_tensile_strain(theta=0, d_n=0)` | 순인장변형률 |
| `minimum_moment(n_design, h)` | 최소편심에 의한 최소 설계휨모멘트 |

`moment_interaction_diagram()` 이 곡선을 **하나만** 돌려주는 것이 KDS 14 와 가장
눈에 띄는 차이다. KDS 14 는 공칭·설계 두 곡선을 돌려주고 그 간격이 점마다
달라지지만, KDS 24 는 재료계수가 재료에 들어 있어 나올 곡선이 하나뿐이다.

### 최소편심

KDS 24 에는 KDS 14 의 최대 축강도 저감계수 $\alpha_{max}$ (0.80 / 0.85)가 없다.
대신 최소편심을 직접 요구한다.

$$
e_{min} = \max \left( \frac{h}{30},\ 20\ \text{mm} \right)
\qquad \text{(4.1.1.2(5))}
$$

```python
from concreteproperties_kds.kds24 import minimum_eccentricity

minimum_eccentricity(h=600)    # 20.0 mm
minimum_eccentricity(h=1500)   # 50.0 mm
```

같은 목적("완전한 중심축하중은 없다")을 계수로 처리하느냐, 편심으로 처리하느냐의
차이다. 실제 사용 가능한 축력으로 견주면 두 기준의 차이는 크지 않다 —
{ref}`비교 문서 3절 <축력-비교>` 을 참고한다.

### 2축 휨

$$
\left( \frac{M_{Edx}}{M_{Rdx}} \right)^{a}
+ \left( \frac{M_{Edy}}{M_{Rdy}} \right)^{a} \le 1.0
\qquad \text{(식 (4.1-4))}
$$

지수 $a$ 는 원형·타원형 단면에서 2.0 이고, 직사각형 단면에서는 축력비
$N_{Ed}/N_{Rd}$ 에 따라 1.0 ~ 2.0 사이를 보간한다.

```python
from concreteproperties_kds.kds24 import biaxial_exponent

biaxial_exponent(n_ed=50, n_rd=1000)                  # 1.0
biaxial_exponent(n_ed=700, n_rd=1000)                 # 1.5
biaxial_exponent(n_ed=0, n_rd=1000, shape="원형")     # 2.0
```

## 기준 값 출처

KDS 24 14 21 원문(HWP)의 표와 식을 직접 대조하였다.

| 확인한 것 | 조문 |
|---|---|
| 재료계수 0.65 / 0.90 | 표 1.4-1 |
| $n$, $\varepsilon_{co}$, $\varepsilon_{cu}$ | 표 3.1-3 |
| $\Delta f$ (4 / 보간 / 6 MPa) | 식 (3.1-1) |
| $f_{cd}$, $f_{ctd}$ | 식 (3.1-47), (3.1-48) |
| 최소편심 | 4.1.1.2(5) |
| 2축 휨 지수 | 4.1.1.3(3) 식 (4.1-4) |
| 전단 $V_{cd}$, $V_{sd}$, $V_{d,max}$ | 식 (4.1-7) ~ (4.1-23) |
| 사용한계상태 등급·균열폭 | 표 4.2-1, 표 4.2-2 |

시험(`tests/test_kds24_*.py`)이 표 3.1-3 재현, KDS 14 곡선 형상과의 일치, 손계산
대조를 고정하고 있다.
