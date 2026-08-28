# 프리스트레스트 콘크리트 (KDS 14 20 60)

`concreteproperties_kds.psc` 는 긴장재·콘크리트의 허용응력, 프리스트레스 손실,
긴장재의 극한 응력 $f_{ps}$, 그리고 프리스트레스트 단면의 강도감소계수를 다룬다.

단면 해석은 `concreteproperties` 의 `PrestressedSection` 이 담당하고,
`KDSPrestressed` 가 그 공칭강도에 KDS 의 강도감소계수를 적용한다.

## 허용응력 (KDS 14 20 60 4.2)

**긴장재**

| 시점 | 허용응력 |
|---|---|
| 긴장 중 (jacking) | $\min(0.80 f_{pu},\ 0.94 f_{py})$ |
| 정착 직후 (anchorage) | $0.70 f_{pu}$ |

**콘크리트 — 프리스트레스 도입 직후**

| 응력 | 한계 |
|---|---|
| 압축 | $0.60 f_{ci}$ |
| 인장 | $0.25\sqrt{f_{ci}}$ (단순지지 부재 단부 $0.50\sqrt{f_{ci}}$) |

**콘크리트 — 사용하중 상태**

| 응력 | 한계 |
|---|---|
| 압축 (지속하중) | $0.45 f_{ck}$ |
| 압축 (전체하중) | $0.60 f_{ck}$ |
| 인장 — 비균열등급 U | $0.63\sqrt{f_{ck}}$ |
| 인장 — 부분균열등급 T | $1.0\sqrt{f_{ck}}$ |
| 인장 — 균열등급 C | 제한 없음 |

```python
from concreteproperties_kds.psc import (
    allowable_concrete_stress_service,
    allowable_concrete_stress_transfer,
    allowable_tendon_stress,
)

allowable_tendon_stress(fpu=1860, fpy=1674, stage="jacking")     # 1488.0 MPa
allowable_concrete_stress_transfer(fci=30)                       # (18.0, -1.37)
allowable_concrete_stress_service(fck=40, crack_class="U")       # (24.0, -3.98)
```

인장응력은 음(−)의 부호로 반환한다.

## 프리스트레스 손실 (KDS 14 20 60 4.3)

### 즉시 손실

**마찰**

$$P_{px} = P_{pj}\, e^{-(\mu_p \alpha_{px} + K l_{px})}$$

$\mu_p \alpha_{px} + K l_{px} \le 0.3$ 이면 근사식
$P_{px} = P_{pj} / (1 + \mu_p\alpha_{px} + K l_{px})$ 를 쓸 수 있다.

**정착장치 활동**

$$\Delta f_p = \frac{\Delta l}{l} E_p$$

**탄성변형**

$$\Delta f_p = \frac{E_p}{E_{ci}} f_{cgp} \quad (\text{프리텐션}), \qquad
\Delta f_p = \frac{N-1}{2N}\frac{E_p}{E_{ci}} f_{cgp} \quad (\text{포스트텐션})$$

### 시간적 손실

**크리프**

$$\Delta f_p = \phi_{cr}\frac{E_p}{E_c}(f_{cgp} - f_{cds})$$

**건조수축**

$$\Delta f_p = \varepsilon_{sh} E_p$$

**릴랙세이션**

$$\Delta f_p = f_{pi}\frac{\log t}{k}\left(\frac{f_{pi}}{f_{py}} - 0.55\right)$$

$k$ 는 저릴랙세이션 강연선 45, 보통 강연선 10 이며,
$f_{pi}/f_{py} \le 0.55$ 이면 손실이 없다.

### 손실 합산

```python
from concreteproperties_kds.psc import (
    PrestressLosses,
    anchorage_set_loss,
    creep_loss,
    elastic_shortening_loss,
    friction_loss,
    relaxation_loss,
    shrinkage_loss,
)

_, friction_force = friction_loss(
    p_pj=1395 * 554.8, mu_p=0.20, alpha_px=0.15, k_wobble=6.6e-7, l_px=10000
)

losses = PrestressLosses(
    f_pj=1395.0,
    friction=friction_force / 554.8,
    anchorage=anchorage_set_loss(slip=6.0, e_p=195e3, length=10000),
    elastic=elastic_shortening_loss(
        f_cgp=8.0, e_p=195e3, e_ci=27537, post_tensioned=True, n_tendons=4
    ),
    creep=creep_loss(f_cgp=8.0, e_p=195e3, e_c=30008, creep_coefficient=2.0),
    shrinkage=shrinkage_loss(e_p=195e3, eps_sh=300e-6),
    relaxation=relaxation_loss(f_pi=0.70 * 1860, fpy=1674),
)
losses.print_results()

print(losses.f_pe)          # 유효 프리스트레스
print(losses.loss_ratio)    # 손실률
```

```
잭킹 응력          fpj    =    1395.00 MPa
--------------------------------------------------------
마찰                      =      50.94 MPa
정착장치 활동             =     117.00 MPa
탄성변형                  =      21.25 MPa
  즉시 손실 소계          =     189.19 MPa
--------------------------------------------------------
크리프                    =     103.97 MPa
건조수축                  =      58.50 MPa
릴랙세이션                =      28.87 MPa
  시간적 손실 소계        =     191.34 MPa
--------------------------------------------------------
전체 손실                 =     380.53 MPa
손실률                    =      27.28 %
유효 프리스트레스  fpe    =    1014.47 MPa
```

## 긴장재의 극한 응력 (KDS 14 20 60 4.1)

**부착 긴장재**

$$f_{ps} = f_{pu}\left[1 - \frac{\gamma_p}{\beta_1}
\left(\rho_p\frac{f_{pu}}{f_{ck}} + \frac{d}{d_p}(\omega - \omega')\right)\right]$$

| $f_{py}/f_{pu}$ | $\gamma_p$ | 강연선 |
|---|---:|---|
| $\ge 0.80$ | 0.55 | 일반 |
| $\ge 0.85$ | 0.40 | 스트레스릴리브드 |
| $\ge 0.90$ | 0.28 | 저릴랙세이션 |

**비부착 긴장재**

| 경간/깊이 | $f_{ps}$ | 상한 |
|---|---|---|
| $\le 35$ | $f_{pe} + 70 + \dfrac{f_{ck}}{100\rho_p}$ | $\min(f_{py},\ f_{pe} + 420)$ |
| $> 35$ | $f_{pe} + 70 + \dfrac{f_{ck}}{300\rho_p}$ | $\min(f_{py},\ f_{pe} + 210)$ |

```python
from concreteproperties_kds.psc import tendon_stress_bonded, tendon_stress_unbonded

tendon_stress_bonded(fpu=1860, fck=40, rho_p=0.00204, gamma_p=0.28)
# 1798.3 MPa

tendon_stress_unbonded(f_pe=1015, fck=40, rho_p=0.00204, fpy=1674, span_depth_ratio=25)
# 1281.4 MPa
```

## 강도감소계수

프리스트레스트 부재는 최외단 인장 긴장재·철근의 순인장변형률(프리스트레스에 의한
변형률 제외)을 기준으로 한다.

| 구간 | 조건 | $\phi$ |
|---|---|---|
| 압축지배 | $\varepsilon_t \le 0.002$ | 0.65 (띠철근) / 0.70 (나선철근) |
| 변화구간 | $0.002 < \varepsilon_t < 0.005$ | 선형보간 |
| 인장지배 | $\varepsilon_t \ge 0.005$ | 0.85 |

철근콘크리트와 달리 변형률한계가 $f_y$ 에 의존하지 않고 **고정값**이다.

## 단면 해석

```python
from concreteproperties import (
    PrestressedSection,
    SteelStrand,
    StrandHardening,
    add_bar_rectangular_array,
)
from sectionproperties.pre.library import rectangular_section

from concreteproperties_kds import KDS
from concreteproperties_kds.psc import KDSPrestressed

kds = KDS()
conc = kds.create_concrete_material(compressive_strength=40)

strand = SteelStrand(
    name="SWPC 7B 15.2mm",
    density=7.85e-6,
    stress_strain_profile=StrandHardening(
        yield_strength=1674, elastic_modulus=195e3,
        fracture_strain=0.035, breaking_strength=1860,
    ),
    colour="slategrey",
    prestress_stress=losses.f_pe,
)

geom = rectangular_section(d=800, b=400, material=conc)
geom = add_bar_rectangular_array(
    geometry=geom, area=138.7, material=strand,
    n_x=4, x_s=80, anchor=(80, 120), n=8,
)
ps_sec = PrestressedSection(geom)

kds_ps = KDSPrestressed(column_type="tie")
kds_ps.assign_prestressed_section(ps_sec)

f_res, u_res, phi = kds_ps.ultimate_bending_capacity(positive=True)
print(f"Mn = {u_res.m_x / 1e6:.2f}, phi = {phi:.3f}, "
      f"phiMn = {f_res.m_x / 1e6:.2f} kN.m")
# Mn = 642.14, phi = 0.850, phiMn = 545.82 kN.m
```

> `PrestressedSection` 은 **y 축에 대칭인 단면**만 받는다. 대칭이 아니면
> `ValueError` 가 발생한다.

`KDSPrestressed.extreme_depth()` 는 격점철근과 강연선을 함께 고려한다.
`concreteproperties` 의 `extreme_bar()` 는 격점철근만 보므로, 강연선만 배치된
단면에서는 사용할 수 없다.

## 다루지 않는 범위

- P-M 상관도, 2축 휨 상관도 — `concreteproperties` 가 프리스트레스트 단면에
  대해 아직 지원하지 않는다
- 정착부 설계 (지압·할렬)
- 부분 프리스트레싱의 균열폭 검토
- 시간 종속 해석 (단계별 시공)

## API

| 함수/클래스 | 내용 |
|---|---|
| `allowable_tendon_stress(fpu, fpy, stage)` | 긴장재 허용응력 |
| `allowable_concrete_stress_transfer(fci, simply_supported_end)` | 도입 직후 허용응력 |
| `allowable_concrete_stress_service(fck, sustained, crack_class)` | 사용하중 허용응력 |
| `friction_loss(...)` | 마찰 손실 |
| `anchorage_set_loss(slip, e_p, length)` | 정착장치 활동 손실 |
| `elastic_shortening_loss(...)` | 탄성변형 손실 |
| `creep_loss(...)`, `shrinkage_loss(...)`, `relaxation_loss(...)` | 시간적 손실 |
| `PrestressLosses` | 손실 합산 (`immediate`, `time_dependent`, `total`, `f_pe`, `loss_ratio`) |
| `tendon_stress_bonded(...)`, `tendon_stress_unbonded(...)` | $f_{ps}$ |
| `capacity_reduction_factor_psc(eps_t, column_type)` | PSC 강도감소계수 |
| `KDSPrestressed` | `PrestressedSection` 에 $\phi$ 적용 |
| `EPS_Y_PSC`, `EPS_TL_PSC` | 0.002, 0.005 |
