# 세장 기둥 (KDS 14 20 20 4.4)

`concreteproperties_kds.slender` 는 세장비 검토와 모멘트확대계수법을 구현한다.
단면 해석 자체는 `KDS` 클래스가 담당하고, 이 모듈은 **부재 길이 효과에 의한
모멘트 확대**만 다룬다.

## 작업 흐름

```
① 세장비 검토       check_slenderness()  ->  세장 기둥인가?
        ↓
② 모멘트 확대       Mc = delta_ns * M2
        ↓
③ 단면 검토         KDS.ultimate_bending_capacity(n_design=Pu) 와 Mc 를 비교
```

## 회전반지름과 세장비

- 직사각형 : $r = 0.3h$
- 원형 : $r = 0.25D$
- 일반 : $r = \sqrt{I_g / A_g}$

$$\text{세장비} = \frac{k l_u}{r}$$

## 세장효과를 무시할 수 있는 조건

| 골조 | 조건 |
|---|---|
| 횡구속 | $\dfrac{k l_u}{r} \le 34 - 12\left(\dfrac{M_1}{M_2}\right) \le 40$ |
| 비횡구속 | $\dfrac{k l_u}{r} \le 22$ |

$M_1/M_2$ 는 단곡률이면 양(+), 복곡률이면 음(−) 이다.

## 모멘트확대계수 (횡구속 골조)

$$\delta_{ns} = \frac{C_m}{1 - \dfrac{P_u}{0.75 P_c}} \ge 1.0$$

$$C_m = 0.6 + 0.4\frac{M_1}{M_2} \ge 0.4 \quad
(\text{지점 사이에 횡하중이 있으면 } C_m = 1.0)$$

$$P_c = \frac{\pi^2 EI}{(k l_u)^2}$$

**휨강성**

$$EI = \frac{0.2 E_c I_g + E_s I_{se}}{1 + \beta_{dns}} \quad\text{또는}\quad
EI = \frac{0.4 E_c I_g}{1 + \beta_{dns}}$$

$\beta_{dns}$ 는 지속 축하중이 전체 축하중에 차지하는 비이다.

$P_u \ge 0.75 P_c$ 이면 좌굴이 발생하므로 `ValueError` 를 낸다 — 단면이나
비지지 길이를 조정해야 한다.

**최소 편심 모멘트**

$$M_{2,min} = P_u (15 + 0.03h) \quad (h\ \text{단위: mm})$$

## 사용법

```python
from concreteproperties_kds.slender import check_slenderness

res = check_slenderness(
    p_u=1500e3,
    m1=90e6,
    m2=150e6,
    k=1.0,
    l_u=9000,
    h=500,
    e_c=conc.elastic_modulus,
    i_g=gross.ixx_c,
    braced=True,
    beta_dns=0.6,
)
res.print_results()
```

```
회전반지름           r      =       150.00 mm
세장비           k*lu/r     =        60.00
한계 세장비                 =        26.80
세장 기둥                   =            예
----------------------------------------------------------------
휨강성               EI     =   3.8366e+13 N.mm^2
임계좌굴하중         Pc     =      4674.84 kN
                 0.75Pc     =      3506.13 kN
                     Cm     =       0.8400
모멘트확대계수   delta_ns   =       1.4681
----------------------------------------------------------------
단부 모멘트          M2     =       150.00 kN.m
최소 편심 모멘트     M2,min =        45.00 kN.m
설계 모멘트          Mc     =       220.21 kN.m
```

확대된 모멘트 `res.m_c` 로 단면을 검토한다.

```python
f_res, _, phi = kds.ultimate_bending_capacity(n_design=1500e3)

ratio = res.m_c / f_res.m_x
print(f"소요/강도 = {ratio:.3f}  {'만족' if ratio <= 1.0 else '불만족'}")
```

## 다루지 않는 범위

- **비횡구속 골조의 $\delta_s$** — 층 전체의 안정성을 다루므로 골조 해석이
  필요하다. 이 모듈은 세장비 한계(22)만 판정한다.
- **2차 해석(P-Δ 해석)** — 모멘트확대계수법의 대안으로 기준이 허용하지만
  구현하지 않았다.
- **비선형 기둥 좌굴** — 단면 해석 범위를 벗어난다.

## API

| 함수 | 내용 |
|---|---|
| `radius_of_gyration(section, h, i_g, a_g)` | 회전반지름 |
| `slenderness_ratio(k, l_u, r)` | 세장비 |
| `slenderness_limit(braced, m1, m2)` | 한계 세장비 |
| `flexural_stiffness(e_c, i_g, beta_dns, e_s, i_se)` | $EI$ |
| `critical_buckling_load(ei, k, l_u)` | $P_c$ |
| `moment_magnifier_braced(...)` | $(C_m,\ \delta_{ns})$ |
| `minimum_moment(p_u, h)` | $M_{2,min}$ |
| `check_slenderness(...)` | 종합 검토 → `SlendernessCheck` |
| `PHI_K` | 0.75 |
