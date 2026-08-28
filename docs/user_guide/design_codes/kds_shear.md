# 전단 및 비틀림 (KDS 14 20 22)

`concreteproperties_kds.shear` 는 설계 전단강도·비틀림강도를 계산하고, 최소
전단철근량과 배치 간격 제한을 검토한다.

이 모듈의 함수는 단면 요소망과 무관한 **순수 함수**이다. 폭 $b_w$ 와 유효깊이
$d$ 는 사용자가 직접 준다.

> **주의** — KDS 14 20 22 는 2021년 개정에서 전단 규정이 상당히 바뀌었다. 이
> 모듈은 널리 쓰이는 형태의 규정을 구현한 것이므로, 사용 전에
> [검증 대조표](kds.md#기준-값-출처와-검증)를 확인한다.

## 강도감소계수

전단과 비틀림의 강도감소계수는 $\phi = 0.75$ 이다 (KDS 14 20 10 표 4.2-1).

## 콘크리트가 부담하는 전단강도

**간편식**

$$V_c = \frac{1}{6}\lambda\sqrt{f_{ck}}\, b_w d$$

**상세식** (`rho_w`, `v_u`, `m_u` 를 모두 주면 사용)

$$V_c = \left(0.16\lambda\sqrt{f_{ck}} + 17.6\,\rho_w \frac{V_u d}{M_u}\right) b_w d
\le 0.29\lambda\sqrt{f_{ck}}\, b_w d, \qquad \frac{V_u d}{M_u} \le 1.0$$

**축력의 영향** (`n_u`, `a_g` 지정)

$$\text{압축}\ (N_u > 0):\ \times\left(1 + \frac{N_u}{14 A_g}\right), \qquad
\text{인장}\ (N_u < 0):\ \times\left(1 + \frac{0.29 N_u}{A_g}\right)$$

인장이 커서 계수가 음수가 되면 $V_c = 0$ 으로 본다.

```python
from concreteproperties_kds.shear import concrete_shear_strength

v_c = concrete_shear_strength(fck=27, b_w=400, d=550)
print(f"{v_c / 1e3:.2f} kN")   # 190.53 kN
```

## 전단철근이 부담하는 전단강도

$$V_s = \frac{A_v f_{yt} d}{s} \quad (\text{수직스터럽}), \qquad
V_s = \frac{A_v f_{yt}(\sin\alpha + \cos\alpha) d}{s} \quad (\text{경사스터럽})$$

**상한**

$$V_s \le \frac{2}{3}\sqrt{f_{ck}}\, b_w d$$

이 상한을 넘으면 단면을 키워야 한다.

## 최소 전단철근량과 간격

$$A_{v,min} = \max\left(0.0625\sqrt{f_{ck}},\ 0.35\right)\frac{b_w s}{f_{yt}}$$

| 조건 | 최대 간격 |
|---|---|
| $V_s \le \frac{1}{3}\sqrt{f_{ck}} b_w d$ | $\min(d/2,\ 600\text{ mm})$ |
| $V_s > \frac{1}{3}\sqrt{f_{ck}} b_w d$ | $\min(d/4,\ 300\text{ mm})$ |

전단철근이 필요한 구간은 $V_u > \phi V_c / 2$ 이다.

## 전단 검토

```python
from concreteproperties_kds.shear import check_shear, required_stirrup_spacing

# 필요한 스터럽 간격
s = required_stirrup_spacing(v_u=320e3, fck=27, b_w=400, d=550, a_v=2 * 126.7, fyt=400)

res = check_shear(v_u=320e3, fck=27, b_w=400, d=550, a_v=2 * 126.7, s=250, fyt=400)
res.print_results()
print(res.ok)
```

`ShearCheck` 는 강도·최소철근량·간격·전단철근 상한·단면 크기를 각각 판정하고,
`ok` 로 종합 판정을 준다.

```
계수 전단력          Vu      =     320.00 kN
콘크리트 전단강도    Vc      =     190.53 kN
                 phi*Vc      =     142.89 kN
전단철근 전단강도    Vs      =     222.99 kN
                     Vs,max  =     762.10 kN
설계 전단강도    phi*Vn      =     310.14 kN
```

`required_stirrup_spacing` 은 강도 조건, 최소 전단철근량 조건, 간격 제한을 모두
만족하는 최대 간격을 반환한다. 전단철근으로도 부족하면 `ValueError` 를 낸다.

## 비틀림

**균열 비틀림모멘트**

$$T_{cr} = \frac{1}{3}\lambda\sqrt{f_{ck}}\,\frac{A_{cp}^2}{p_{cp}}$$

**비틀림을 무시할 수 있는 조건**

$$T_u < \phi\frac{1}{12}\lambda\sqrt{f_{ck}}\frac{A_{cp}^2}{p_{cp}} = \frac{\phi T_{cr}}{4}$$

**비틀림강도와 종방향 철근**

$$T_n = \frac{2 A_o A_t f_{yt}}{s}\cot\theta, \qquad A_o = 0.85 A_{oh}$$

$$A_l = \frac{A_t}{s} p_h \frac{f_{yt}}{f_y}\cot^2\theta$$

비프리스트레스트 부재는 $\theta = 45°$ 를 쓴다.

**단면 크기 검토**

$$\sqrt{\left(\frac{V_u}{b_w d}\right)^2 + \left(\frac{T_u p_h}{1.7 A_{oh}^2}\right)^2}
\le \phi\left(\frac{V_c}{b_w d} + \frac{2}{3}\sqrt{f_{ck}}\right)$$

```python
from concreteproperties_kds.shear import (
    check_torsion_section,
    cracking_torque,
    longitudinal_torsion_reinforcement,
    torsion_negligible,
    torsional_strength,
)

a_cp, p_cp = 400 * 600, 2 * (400 + 600)
a_oh, p_h = 320 * 520, 2 * (320 + 520)

t_cr = cracking_torque(fck=27, a_cp=a_cp, p_cp=p_cp)
if not torsion_negligible(t_u=30e6, fck=27, a_cp=a_cp, p_cp=p_cp):
    t_n = torsional_strength(a_t=126.7, s=250, a_oh=a_oh, fyt=400)
    a_l = longitudinal_torsion_reinforcement(
        a_t=126.7, s=250, p_h=p_h, fyt=400, fy=400
    )

demand, capacity, ok = check_torsion_section(
    v_u=320e3, t_u=30e6, fck=27, b_w=400, d=550, a_oh=a_oh, p_h=p_h
)
```

## API

| 함수 | 내용 |
|---|---|
| `concrete_shear_strength(...)` | $V_c$ (간편식/상세식/축력 효과) |
| `shear_reinforcement_strength(a_v, fyt, d, s, alpha)` | $V_s$ |
| `max_shear_reinforcement_strength(fck, b_w, d)` | $V_s$ 상한 |
| `minimum_shear_reinforcement(fck, b_w, s, fyt)` | $A_{v,min}$ |
| `max_stirrup_spacing(fck, b_w, d, v_s)` | 최대 간격 |
| `check_shear(...)` | 전단 종합 검토 → `ShearCheck` |
| `required_stirrup_spacing(...)` | 필요한 스터럽 간격 |
| `cracking_torque(fck, a_cp, p_cp, lambda_c)` | $T_{cr}$ |
| `torsion_negligible(...)` | 비틀림 무시 가능 여부 |
| `torsional_strength(a_t, s, a_oh, fyt, theta)` | $T_n$ |
| `longitudinal_torsion_reinforcement(...)` | $A_l$ |
| `check_torsion_section(...)` | 단면 크기 검토 |
| `PHI_SHEAR` | 0.75 |
