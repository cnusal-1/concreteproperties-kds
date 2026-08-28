# 사용성 (KDS 14 20 30)

`concreteproperties_kds.serviceability` 는 처짐 계산(유효단면2차모멘트, 장기처짐),
처짐 한계, 처짐 계산을 생략할 수 있는 최소 두께, 균열 제어를 위한 휨철근 간격
제한을 다룬다.

## 유효단면2차모멘트 (Branson 식)

$$I_e = \left(\frac{M_{cr}}{M_a}\right)^3 I_g +
\left[1 - \left(\frac{M_{cr}}{M_a}\right)^3\right] I_{cr} \le I_g$$

$M_a \le M_{cr}$ 이면 $I_e = I_g$ 이다.

```python
from concreteproperties_kds.serviceability import effective_moment_of_inertia

i_e = effective_moment_of_inertia(m_a=180e6, m_cr=88.4e6, i_g=7.9e9, i_cr=2.2e9)
```

균열모멘트는 `concreteproperties` 의 균열 해석으로 구하거나, 단면 제원으로부터
직접 계산할 수 있다.

$$M_{cr} = \frac{f_r I_g}{y_t}, \qquad f_r = 0.63\lambda\sqrt{f_{ck}}$$

## 장기처짐

$$\lambda_\Delta = \frac{\xi}{1 + 50\rho'}$$

| 지속하중 재하기간 | $\xi$ |
|---|---|
| 3개월 | 1.0 |
| 6개월 | 1.2 |
| 12개월 | 1.4 |
| 5년 이상 | 2.0 |

$$\Delta_{total} = \Delta_L + \Delta_D + \lambda_\Delta \Delta_D$$

압축철근($\rho'$)이 있으면 장기처짐이 줄어든다.

## 처짐 한계 — 비교 대상이 조건마다 다르다

KDS 14 20 30 표 4.2-2 의 허용처짐은 조건마다 **비교하는 처짐의 종류가 다르다.**
이 점을 놓치면 검토가 과도하게 보수적이 된다.

| 조건 | 허용처짐 | 비교 대상 |
|---|---|---|
| `지붕_비구조재없음` | $l/180$ | 활하중에 의한 즉시처짐 |
| `바닥_비구조재없음` | $l/360$ | 활하중에 의한 즉시처짐 |
| `손상되기쉬운_비구조재` | $l/480$ | 비구조 요소 부착 후 발생 처짐 |
| `손상되지않는_비구조재` | $l/240$ | 비구조 요소 부착 후 발생 처짐 |

"비구조 요소 부착 후 발생 처짐" 은 장기 추가처짐과 추가 활하중에 의한 즉시처짐의
합이다.

```python
from concreteproperties_kds.serviceability import deflection_limit, deflection_target

deflection_limit(span=8000, condition="바닥_비구조재없음")   # 22.22 mm
deflection_target(condition="바닥_비구조재없음")             # 'live'
deflection_target(condition="손상되기쉬운_비구조재")          # 'attached'
```

`check_deflection` 은 조건에 맞는 처짐을 골라 비교하고, 어떤 처짐을 비교했는지
결과에 담는다.

```python
from concreteproperties_kds.serviceability import check_deflection

res = check_deflection(
    span=8000,
    m_sustained=120e6,
    m_live=60e6,
    m_cr=cracked.m_cr,
    i_g=gross.ixx_c,
    i_cr=cracked.ixx_c_cr,
    e_c=conc.elastic_modulus,
    rho_prime=0.0018,
    duration="5년이상",
    condition="바닥_비구조재없음",
)
res.print_results()
```

```
지속하중 즉시처짐          =           10.330 mm
활하중   즉시처짐          =            5.165 mm
장기 추가처짐              =           18.948 mm
전체 처짐 (참고)           =           34.443 mm
------------------------------------------------------------------
허용처짐 조건 : 바닥_비구조재없음
비교 대상     : 활하중에 의한 즉시처짐
검토 처짐                  =            5.165 mm
허용 처짐                  =           22.222 mm
판정                       =               만족
```

처짐은 모멘트로부터 역산한 등가 등분포하중으로 계산한다.

$$\Delta = k\frac{w l^4}{E_c I_e}, \qquad w = \frac{8M}{l^2}$$

`support_coefficient` 로 $k$ 를 바꿀 수 있다 (기본값 $5/384$, 단순지지 등분포).

## 최소 두께 (처짐 계산 생략)

경간 $l$ 에 대한 비로 주어진다 ($f_y = 400$ MPa 기준).

| 지지 조건 | 보 | 1방향 슬래브 |
|---|---|---|
| 단순지지 | $l/16$ | $l/20$ |
| 1단 연속 | $l/18.5$ | $l/24$ |
| 양단 연속 | $l/21$ | $l/28$ |
| 캔틸레버 | $l/8$ | $l/10$ |

표의 값은 보통중량콘크리트($m_c = 2300$ kg/m³)와 $f_y = 400$ MPa 철근 기준이며,
다른 조건에는 다음 보정을 적용한다 (KDS 14 20 30 표 4.2-1 주).

- 단위질량 1,500~2,000 kg/m³ 의 구조용 경량콘크리트 :
  $(1.65 - 0.00031 m_c) \ge 1.09$ 를 곱한다.
- $f_y \ne 400$ MPa : $(0.43 + f_y/700)$ 을 곱한다.

```python
from concreteproperties_kds.serviceability import minimum_thickness

minimum_thickness(span=8000, member="보", support="단순지지")            # 500.0 mm
minimum_thickness(span=8000, member="보", support="단순지지", fy=500)    # 572.1 mm
minimum_thickness(span=8000, member="보", support="단순지지", m_c=1800)  # 546.0 mm
```

## 균열 제어 (KDS 14 20 20 4.2.3(4))

KDS 14 20 30 4.1(1) 은 균열 검토를 KDS 14 20 20(4.2.3) 으로 위임한다.
콘크리트 인장연단에 가장 가까이 배치되는 철근의 중심 간격 $s$ 는 다음 두 식으로
계산한 값 중 **작은 값 이하**여야 한다 (식 4.2-3, 4.2-4).

$$s = 375\left(\frac{\kappa_{cr}}{f_s}\right) - 2.5 c_c
\le 300\left(\frac{\kappa_{cr}}{f_s}\right)$$

$\kappa_{cr}$ 은 건조환경 280, 그 밖의 환경 210 이다. $f_s$ 를 계산하지 않으면
$f_s = \frac{2}{3} f_y$ 를 쓸 수 있다.

```python
from concreteproperties_kds.serviceability import check_crack_control

fs, s_max, ok = check_crack_control(bar_spacing=100, fy=400, c_c=40)
# (266.7, 293.75, True)
```

## 수축·온도철근 (KDS 14 20 50 4.6.2)

1방향 철근콘크리트 슬래브의 수축·온도철근비는 다음 값 이상이어야 하나, 어떤
경우에도 0.0014 이상이어야 한다.

$$\rho = \begin{cases}
0.0020 & f_y \le 400\ \text{MPa} \\
0.0020 \times \dfrac{400}{f_y} & f_y > 400\ \text{MPa}
\end{cases}$$

다만 단위 폭 1 m 당 1,800 mm² 보다 크게 취할 필요는 없고, 간격은 슬래브 두께의
5배 이하이면서 450 mm 이하여야 한다.

```python
from concreteproperties_kds.serviceability import (
    shrinkage_temperature_reinforcement,
    shrinkage_temperature_spacing,
)

shrinkage_temperature_reinforcement(fy=400, a_g=1000 * 200)    #  400.0 mm^2/m
shrinkage_temperature_reinforcement(fy=400, a_g=1000 * 1000)   # 1800.0 (상한)
shrinkage_temperature_spacing(thickness=200)                   #  450.0 mm
```

## API

| 함수 | 내용 |
|---|---|
| `effective_moment_of_inertia(m_a, m_cr, i_g, i_cr)` | $I_e$ (Branson) |
| `cracking_moment(fck, i_g, y_t, lambda_c)` | $M_{cr}$ |
| `long_term_deflection_factor(rho_prime, duration)` | $\lambda_\Delta$ |
| `total_deflection(...)` | 장기 추가처짐과 전체 처짐 |
| `minimum_thickness(span, member, support, fy, m_c)` | 최소 두께 |
| `deflection_limit(span, condition)` | 허용처짐 |
| `deflection_target(condition)` | 비교 대상 처짐 (`"live"` / `"attached"`) |
| `check_deflection(...)` | 처짐 종합 검토 → `DeflectionCheck` |
| `max_bar_spacing(fs, c_c, dry_environment)` | 균열 제어 최대 간격 |
| `service_steel_stress(fy)` | $f_s = \frac{2}{3} f_y$ |
| `check_crack_control(...)` | 균열 제어 검토 |
| `shrinkage_temperature_reinforcement(fy, a_g, width)` | 수축·온도철근량 (1,800 mm²/m 상한) |
| `shrinkage_temperature_spacing(thickness)` | 수축·온도철근 최대 간격 |
