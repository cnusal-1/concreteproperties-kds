# 2축 휨 간략식

`KDS.biaxial_bending_diagram()` 은 2축 휨 상관면을 **엄밀하게** 계산한다.
`concreteproperties_kds.biaxial` 은 실무에서 널리 쓰이는 간략식을 제공하여
엄밀해와 비교할 수 있게 한다.

> 간략식은 KDS 14 20 의 조문이 아니라 문헌에서 널리 인정되는 근사법이다.
> 설계에 사용할 때는 엄밀해와 대조하기를 권한다.

## 등하중선법 (load contour method)

$$\left(\frac{M_{ux}}{\phi M_{nx}}\right)^\alpha
+ \left(\frac{M_{uy}}{\phi M_{ny}}\right)^\alpha \le 1.0$$

$\phi M_{nx}$, $\phi M_{ny}$ 는 **같은 계수 축력**에서의 1축 설계 휨강도이다.
$\alpha = 1.0$ 은 직선 상관(보수측), $\alpha = 2.0$ 은 원형 상관에 가깝다.

```python
import numpy as np
from concreteproperties_kds.biaxial import check_load_contour

f_x, _, _ = kds.ultimate_bending_capacity(theta=0, n_design=1200e3)
f_y, _, _ = kds.ultimate_bending_capacity(theta=-np.pi / 2, n_design=1200e3)

res = check_load_contour(
    m_ux=200e6, m_uy=120e6,
    phi_m_nx=abs(f_x.m_x), phi_m_ny=abs(f_y.m_y),
    alpha=1.0,
)
res.print_results()
```

## Bresler 역하중법 (reciprocal load method)

$$\frac{1}{P_n} = \frac{1}{P_{nx}} + \frac{1}{P_{ny}} - \frac{1}{P_o}$$

- $P_{nx}$ : 편심 $e_x = M_{ux}/P_u$ 만 작용할 때의 축강도
- $P_{ny}$ : 편심 $e_y = M_{uy}/P_u$ 만 작용할 때의 축강도
- $P_o$ : 순수압축 강도

적용 범위는 $P_u \ge 0.1 f_{ck} A_g$ 이다. `fck` 와 `a_g` 를 주면 범위를 벗어날 때
경고 문구를 결과의 `note` 에 담는다.

```python
from concreteproperties_kds.biaxial import check_bresler_reciprocal

res = check_bresler_reciprocal(
    p_u=1200e3,
    phi_p_nx=1963e3,
    phi_p_ny=2758e3,
    phi_p_o=3591e3,
    fck=27,
    a_g=500 * 500,
)
res.print_results()
```

## 엄밀해와의 비교

500 × 500 기둥(8-D22, fck 27, SD400), $N_d = 1200$ kN,
$M_{ux} = 200$, $M_{uy} = 120$ kN·m 일 때 (`examples/15_2축휨간략식.py`):

| 방법 | 소요/강도 |
|---|---:|
| **엄밀 2축 휨 상관면** | **0.7536** |
| 등하중선법 $\alpha = 1.00$ | 0.8285 |
| 등하중선법 $\alpha = 1.25$ | 0.6712 |
| 등하중선법 $\alpha = 1.50$ | 0.5458 |
| 등하중선법 $\alpha = 2.00$ | 0.3647 |
| Bresler 역하중법 | 0.7122 |

$\alpha = 1.0$ 만 엄밀해보다 보수적이고, $\alpha \ge 1.25$ 는 위험측이 된다.
$\alpha$ 를 임의로 키우지 말고, 이 저장소의 엄밀해로 확인하는 편이 낫다.

```python
from concreteproperties_kds.biaxial import compare_with_exact

for alpha, value, conservative in compare_with_exact(
    m_ux=200e6, m_uy=120e6,
    phi_m_nx=386.23e6, phi_m_ny=386.23e6,
    exact_ratio=0.7536,
):
    print(f"alpha={alpha:.2f}  {value:.4f}  {'보수적' if conservative else '위험측'}")
```

## 엄밀해 사용법

```python
f_bb, phis = kds.biaxial_bending_diagram(n_design=1200e3, n_points=48)
f_bb.plot_diagram()

# 설계 단면력이 상관면 안에 있는지
print(f_bb.point_in_diagram(m_x=200e6, m_y=120e6))
```

강도감소계수도 방향에 따라 달라진다. 위 예의 기둥에서는 0.688 ~ 0.828 로
변한다 — 같은 축력이라도 중립축 방향에 따라 순인장변형률이 달라지기 때문이다.
간략식은 이 효과를 직접 반영하지 못한다.

## API

| 함수 | 내용 |
|---|---|
| `load_contour(m_ux, m_uy, m_nx, m_ny, alpha)` | 등하중선법 상관식 좌변 |
| `check_load_contour(...)` | 등하중선법 검토 → `BiaxialCheck` |
| `bresler_reciprocal(p_nx, p_ny, p_o)` | 역하중법 축강도 |
| `check_bresler_reciprocal(...)` | 역하중법 검토 → `BiaxialCheck` |
| `compare_with_exact(...)` | 여러 $\alpha$ 를 엄밀해와 비교 |
