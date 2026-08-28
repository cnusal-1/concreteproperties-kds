# KDS 14 20 (콘크리트구조 설계기준)

`concreteproperties_kds.KDS` (정식 이름 `KDS14202022`) 는 국가건설기준
**KDS 14 20 콘크리트구조 설계기준**의 강도설계법을 임의 형상의 철근콘크리트 단면
해석에 적용하는 설계기준 클래스이다.

## 적용 기준

| 코드 | 제목 | 이 모듈에서 사용한 부분 |
|---|---|---|
| KDS 14 20 01 | 콘크리트구조 설계(강도설계법) 일반사항 | 설계 원칙 |
| KDS 14 20 10 | 콘크리트구조 해석과 설계 원칙 | 재료 상수(4.3), 강도감소계수(4.2), 경량콘크리트계수(4.4) |
| KDS 14 20 20 | 콘크리트구조 휨 및 압축 설계기준 | 등가직사각형 응력블록(4.1.1), 변형률한계·최대 축강도(4.1.2), 최소철근량(4.2.2) |
| KDS 14 20 30 | 콘크리트구조 사용성 설계기준 | 파괴계수(4.2.1) |

전단·비틀림(KDS 14 20 22), 철근상세(KDS 14 20 50), 정착·이음(KDS 14 20 52),
프리스트레스트(KDS 14 20 62) 는 **다루지 않는다**. 이 모듈은 단면의 휨·축력
거동만을 대상으로 한다.

## 사용법

```python
from concreteproperties import ConcreteSection
from sectionproperties.pre.library import concrete_rectangular_section

from concreteproperties_kds import KDS

kds = KDS(column_type="tie")          # "tie"(띠철근) 또는 "spiral"(나선철근)

conc = kds.create_concrete_material(compressive_strength=27)
steel = kds.create_steel_material(yield_strength=400)

geom = concrete_rectangular_section(
    d=600, b=400,
    dia_top=16, area_top=198.6, n_top=2, c_top=50,
    dia_bot=22, area_bot=387.1, n_bot=4, c_bot=50,
    n_circle=16, conc_mat=conc, steel_mat=steel,
)

conc_sec = ConcreteSection(geom)
kds.assign_concrete_section(conc_sec)
```

`column_type` 은 압축지배단면의 강도감소계수와 최대 설계 축강도의 저감계수를
결정한다. 보에도 값을 주어야 하지만, 인장지배단면에서는 결과에 영향을 주지 않는다.

## 재료

### 콘크리트

**탄성계수 (KDS 14 20 10 4.3.3)**

$$E_c = 0.077\, m_c^{1.5}\, \sqrt[3]{f_{cm}} \quad \text{(MPa)}$$

보통중량 콘크리트($m_c = 2300$ kg/m³)에 대해서는 기준이 제시하는 간편식
$E_c = 8500 \sqrt[3]{f_{cm}}$ 을 사용한다.

$$f_{cm} = f_{ck} + \Delta f, \qquad
\Delta f = \begin{cases}
4 \text{ MPa} & f_{ck} \le 40 \\
4 + 2\dfrac{f_{ck}-40}{20} & 40 < f_{ck} < 60 \\
6 \text{ MPa} & f_{ck} \ge 60
\end{cases}$$

**등가직사각형 응력블록 (KDS 14 20 20 4.1.1, 표 4.1-1)**

압축응력을 $\eta(0.85 f_{ck})$ 로, 압축영역 깊이를 $a = \beta_1 c$ 로 본다.

| $f_{ck}$ (MPa) | ≤ 40 | 50 | 60 | 70 | 80 | 90 |
|---|---:|---:|---:|---:|---:|---:|
| $\varepsilon_{cu}$ | 0.0033 | 0.0032 | 0.0031 | 0.0030 | 0.0029 | 0.0028 |
| $\eta$ | 1.00 | 0.97 | 0.95 | 0.91 | 0.87 | 0.84 |
| $\beta_1$ | 0.80 | 0.80 | 0.76 | 0.74 | 0.72 | 0.70 |

표에 없는 강도는 선형보간한다.

**파괴계수 (KDS 14 20 30 4.2.1)**

$$f_r = 0.63\,\lambda\,\sqrt{f_{ck}} \quad \text{(MPa)}$$

$\lambda$ 는 경량콘크리트계수 (KDS 14 20 10 4.4) 로, 보통중량 1.0, 모래경량 0.85,
전경량 0.75 이다.

적용 범위는 $18 \le f_{ck} \le 90$ MPa 이다.

### 철근

| 항목 | 값 | 근거 |
|---|---|---|
| 탄성계수 | $E_s = 200{,}000$ MPa | KDS 14 20 10 4.3.4 |
| 응력-변형률 | 완전탄소성 | KDS 14 20 20 4.1.1 |
| 항복강도 범위 | $300 \le f_y \le 600$ MPa | KDS 14 20 20 4.1.1 |

## 강도감소계수

### 변형률한계 (KDS 14 20 20 4.1.2)

**압축지배변형률한계** — 균형변형률상태의 순인장변형률, 즉 항복변형률

$$\varepsilon_y = \frac{f_y}{E_s}$$

**인장지배변형률한계**

$$\varepsilon_{t,tl} = \begin{cases}
0.005 & f_y \le 400 \text{ MPa} \\
2.5\,\varepsilon_y & f_y > 400 \text{ MPa}
\end{cases}$$

| 강종 | $f_y$ (MPa) | $\varepsilon_y$ | $\varepsilon_{t,tl}$ | $\varepsilon_{t,min}$ |
|---|---:|---:|---:|---:|
| SD300 | 300 | 0.0015 | 0.00500 | 0.00400 |
| SD400 | 400 | 0.0020 | 0.00500 | 0.00400 |
| SD500 | 500 | 0.0025 | 0.00625 | 0.00500 |
| SD600 | 600 | 0.0030 | 0.00750 | 0.00600 |

$\varepsilon_{t,min}$ 은 휨부재의 최소허용변형률이다 (아래 [연성 검토](#연성-검토) 참고).

### 강도감소계수 (KDS 14 20 10 표 4.2-1)

최외단 인장철근의 순인장변형률

$$\varepsilon_t = \varepsilon_{cu}\,\frac{d_t - c}{c}$$

에 따라 다음과 같이 결정된다.

| 구간 | 조건 | $\phi$ |
|---|---|---|
| 압축지배단면 | $\varepsilon_t \le \varepsilon_y$ | 0.65 (띠철근) / 0.70 (나선철근) |
| 변화구간단면 | $\varepsilon_y < \varepsilon_t < \varepsilon_{t,tl}$ | 선형보간 |
| 인장지배단면 | $\varepsilon_t \ge \varepsilon_{t,tl}$ | 0.85 |

$$\phi = \phi_c + (0.85 - \phi_c)\,
\frac{\varepsilon_t - \varepsilon_y}{\varepsilon_{t,tl} - \varepsilon_y}$$

SD400 · 띠철근의 경우:

| $\varepsilon_t$ | 0.0010 | 0.0020 | 0.0030 | 0.0035 | 0.0040 | 0.0050 | 0.0100 |
|---|---:|---:|---:|---:|---:|---:|---:|
| $\phi$ | 0.650 | 0.650 | 0.717 | 0.750 | 0.783 | 0.850 | 0.850 |

```python
kds.capacity_reduction_factor(eps_t=0.0035)   # 0.75
kds.section_classification(eps_t=0.0035)      # '변화구간단면'
```

> 이 모듈이 다루지 않는 전단·비틀림($\phi = 0.75$), 지압($\phi = 0.65$),
> 스트럿-타이($\phi = 0.75$), 무근콘크리트($\phi = 0.55$) 의 강도감소계수는
> 사용자가 직접 적용해야 한다.

### 강도감소계수의 비선형 반복

$\phi$ 는 $\varepsilon_t$ 에 의존하고, $\varepsilon_t$ 는 다시 공칭 축력
$N_u = N_d / \phi$ 에 의존한다. 따라서 계수 축력이 주어지면 다음 방정식을
$\phi$ 에 대해 푼다.

$$g(\phi) = \phi_{KDS}\!\left(\varepsilon_t\!\left(N_u = \frac{N_d}{\phi}\right)\right) - \phi = 0$$

$\phi_{KDS} \in [\phi_c,\ 0.85]$ 이므로 $g(\phi_c) \ge 0$, $g(0.85) \le 0$ 이 항상
성립하여 구간 $[\phi_c,\ 0.85]$ 에서 해가 반드시 존재한다. `scipy.optimize.brentq`
로 푼다.

반복 1회마다 단면 해석이 한 번 수행되므로, `ultimate_bending_capacity()` 는
축력이 압축·인장 극단에 있지 않은 경우 상대적으로 느리다.

## 축강도

### 순수압축 하중 (KDS 14 20 20 4.1.2)

$$P_o = 0.85 f_{ck}(A_g - A_{st}) + f_y A_{st}$$

임의 형상 단면에서는 콘크리트 형상별로 $0.85 f_{ck} A_c$ 를, 철근별로 $f_y A_s$ 를
합산한다. `concreteproperties` 는 철근을 넣을 때 콘크리트를 도려내므로 콘크리트
형상의 면적이 이미 $A_g - A_{st}$ 이다.

### 최대 설계 축강도 (KDS 14 20 20 4.1.2)

$$\phi P_{n,max} = \alpha \phi \left[0.85 f_{ck}(A_g - A_{st}) + f_y A_{st}\right]$$

| 횡철근 | $\alpha$ | $\phi$ |
|---|---:|---:|
| 나선철근 | 0.85 | 0.70 |
| 띠철근 | 0.80 | 0.65 |

```python
n_max_nominal, n_max_design = kds.max_axial_strength()
```

P-M 상관도는 압축측에서 $\alpha P_o$ 로 절단된다. 상관도의 첫 점이 이 값을
넘어서면 교점을 계산하여 수평으로 자른다.

### 순수인장 하중

$$P_{nt} = -f_y A_{st}$$

콘크리트의 인장강도는 무시한다. 순수인장 상태는 인장지배단면이므로 $\phi = 0.85$
가 적용된다.

## 연성 검토

**최소허용변형률 (KDS 14 20 20 4.1.2)** — 계수 축력이 $0.10 f_{ck} A_g$ 보다 작은
휨부재의 최외단 인장철근의 순인장변형률은 다음 값 이상이어야 한다.

$$\varepsilon_{t,min} = \begin{cases}
0.004 & f_y \le 400 \text{ MPa} \\
2.0\,\varepsilon_y & f_y > 400 \text{ MPa}
\end{cases}$$

```python
eps_t, eps_t_min, ok = kds.check_flexural_ductility()
# (0.019918, 0.004, True)
```

**최소철근량 (KDS 14 20 20 4.2.2)**

$$A_{s,min} = \max\left(\frac{0.25\sqrt{f_{ck}}}{f_y},\ \frac{1.4}{f_y}\right) b_w d$$

```python
from concreteproperties_kds import minimum_flexural_reinforcement

minimum_flexural_reinforcement(fck=27, fy=400, b_w=400, d=550)   # 770.0 mm^2
```

## 검증 예제

### 단철근 직사각형 보

$b = 300$ mm, $h = 600$ mm, $d = 540$ mm, $f_{ck} = 24$ MPa, $f_y = 400$ MPa,
$A_s$ = 4-D22 = 1548.4 mm²

**손계산**

$$a = \frac{A_s f_y}{\eta(0.85 f_{ck}) b}
= \frac{1548.4 \times 400}{1.0 \times 0.85 \times 24 \times 300} = 101.20 \text{ mm}$$

$$c = \frac{a}{\beta_1} = \frac{101.20}{0.80} = 126.50 \text{ mm}$$

$$\varepsilon_t = 0.0033 \times \frac{540 - 126.50}{126.50} = 0.010786
> 0.005 \ \Rightarrow\ \text{인장지배단면},\ \phi = 0.85$$

$$M_n = A_s f_y \left(d - \frac{a}{2}\right) = 303.11 \text{ kN·m},
\qquad \phi M_n = 257.65 \text{ kN·m}$$

**모듈 계산 결과**

| 항목 | 손계산 | 모듈 |
|---|---:|---:|
| $c$ (mm) | 126.50 | 126.504 |
| $\varepsilon_t$ | 0.010786 | 0.010787 |
| $\phi$ | 0.850 | 0.850 |
| $M_n$ (kN·m) | 303.115 | 303.115 |
| $\phi M_n$ (kN·m) | 257.648 | 257.647 |

이 대조는 `tests/test_kds.py::test_beam_flexural_capacity` 로 자동 검증된다.

### 기둥의 P-M 상관도

500 × 500 띠철근 기둥, 8-D22, $f_{ck} = 27$ MPa, SD400, 피복 50 mm
($A_{st} = 3096.8$ mm²)

$$P_o = 0.85 \times 27 \times (250000 - 3096.8) + 400 \times 3096.8
= 6905.1 \text{ kN}$$

$$\phi P_{n,max} = 0.65 \times 0.80 \times 6905.1 = 3590.7 \text{ kN}$$

$$P_{nt} = -400 \times 3096.8 = -1238.7 \text{ kN}$$

설계 축력별 결과 (`examples/05_PM상관도.py`):

| $N_d$ (kN) | $\phi$ | $\varepsilon_t$ | 단면 분류 | $\phi M_n$ (kN·m) |
|---:|---:|---:|---|---:|
| −800 | 0.850 | ∞ | 인장지배단면 | 52.1 |
| −400 | 0.850 | ∞ | 인장지배단면 | 134.6 |
| 0 | 0.850 | 0.01675 | 인장지배단면 | 217.0 |
| 400 | 0.850 | 0.01063 | 인장지배단면 | 290.3 |
| 800 | 0.850 | 0.00689 | 인장지배단면 | 354.8 |
| 1200 | 0.828 | 0.00467 | 변화구간단면 | 386.2 |
| 1600 | 0.665 | 0.00222 | 변화구간단면 | 345.6 |
| 2000 | 0.650 | 0.00135 | 압축지배단면 | 325.4 |
| 2800 | 0.650 | 0.00025 | 압축지배단면 | 272.1 |
| 3400 | 0.650 | −0.00033 | 압축지배단면 | 203.5 |

## 구현 시 채택한 가정

기준 조문만으로 정해지지 않아 구현에서 판단한 사항을 밝힌다.

| 항목 | 채택한 처리 | 사유 |
|---|---|---|
| 사용 응력-변형률의 압축 상한 | $0.85 f_{ck}$ | KDS 조문이 아니라, 모멘트-곡률 해석에서 콘크리트 압축응력이 무한히 커지지 않도록 두는 값. 사용하중 상태의 균열단면 해석에서는 응력이 이 값에 도달하지 않으므로 결과에 영향이 없다 |
| 철근의 파단변형률 | 0.05 (변경 가능) | KDS 는 휨강도 산정 시 철근 변형률의 상한을 규정하지 않는다. KS D 3504 의 연신율을 참고한 실용값 |
| 단면 내 철근 강도가 여러 종류일 때의 변형률한계 | 가장 **높은** $f_y$ 기준 | $\varepsilon_y$ 와 $\varepsilon_{t,tl}$ 이 커져 $\phi$ 가 작아지는 보수측 |
| $d_t$ 의 정의 | 압축연단에서 가장 먼 **격점철근**(`SteelBar`) 중심까지의 거리 | 기준의 "최외단 인장철근" 에 대응 |
| 순인장 구간($N_d < 0$)의 $\phi$ | 0.85 로 일정 | 순인장 상태는 인장지배단면 |
| 압축 보간 구간($N_d > N_{decomp}$)의 $\phi$ | $\phi_c$ 로 일정 | 해당 구간은 압축지배 |
| 순수압축 하중 $P_o$ 의 $\eta$ 적용 | 적용하지 않음 ($0.85 f_{ck}$) | KDS 14 20 20 4.1.2 의 $P_o$ 식이 $0.85 f_{ck}$ 로 표기되어 있음. 고강도 콘크리트에서 $\eta < 1$ 을 함께 적용해야 한다고 보는 해석도 있으므로, $f_{ck} > 40$ MPa 기둥에서는 값을 확인할 것 |

## 기준 값 출처와 검증

> **중요** — 이 모듈이 구현한 계수와 조문 번호는 아래 표와 같다. KDS 는 개정되므로,
> 실무 적용 전에 **현행 KDS 14 20 원문과 대조**하기 바란다. 특히 이 모듈은 원문
> 데이터베이스에 직접 접근하지 않고 작성되었으므로, 조문 번호가 최신 개정판과
> 다를 수 있다.

| 항목 | 구현값 | 조문 | 확인 |
|---|---|---|---|
| 콘크리트 탄성계수 | $8500\sqrt[3]{f_{ck}+\Delta f}$ | KDS 14 20 10 4.3.3 | ☐ |
| $\Delta f$ | 4 / 선형보간 / 6 MPa | KDS 14 20 10 4.3.3 | ☐ |
| $\varepsilon_{cu}$, $\eta$, $\beta_1$ | 위 표 | KDS 14 20 20 표 4.1-1 | ☐ |
| 파괴계수 | $0.63\lambda\sqrt{f_{ck}}$ | KDS 14 20 30 4.2.1 | ☐ |
| 철근 탄성계수 | 200,000 MPa | KDS 14 20 10 4.3.4 | ☐ |
| $f_y$ 상한 | 600 MPa | KDS 14 20 20 4.1.1 | ☐ |
| 강도감소계수 | 0.85 / 0.70 / 0.65 | KDS 14 20 10 표 4.2-1 | ☐ |
| 압축지배변형률한계 | $\varepsilon_y$ | KDS 14 20 20 4.1.2 | ☐ |
| 인장지배변형률한계 | 0.005 또는 $2.5\varepsilon_y$ | KDS 14 20 20 4.1.2 | ☐ |
| 최소허용변형률 | 0.004 또는 $2.0\varepsilon_y$ | KDS 14 20 20 4.1.2 | ☐ |
| 최대 축강도 저감계수 | 0.80 / 0.85 | KDS 14 20 20 4.1.2 | ☐ |
| 최소 휨철근량 | $\max(0.25\sqrt{f_{ck}}/f_y,\ 1.4/f_y)b_w d$ | KDS 14 20 20 4.2.2 | ☐ |

계수를 바꾸려면 `src/concreteproperties_kds/kds.py` 상단의 상수와 표를 수정한다.

```python
STRESS_BLOCK_FCK = [40.0, 50.0, 60.0, 70.0, 80.0, 90.0]
STRESS_BLOCK_EPS_CU = [0.0033, 0.0032, 0.0031, 0.0030, 0.0029, 0.0028]
STRESS_BLOCK_ETA = [1.00, 0.97, 0.95, 0.91, 0.87, 0.84]
STRESS_BLOCK_BETA_1 = [0.80, 0.80, 0.76, 0.74, 0.72, 0.70]

ES = 200.0e3

PHI_TENSION = 0.85
PHI_COMP_TIE = 0.65
PHI_COMP_SPIRAL = 0.70

ALPHA_MAX_TIE = 0.80
ALPHA_MAX_SPIRAL = 0.85
```

수정 후에는 반드시 시험을 다시 돌린다.

```shell
PYTHONPATH=src python -m pytest tests/ -q
```

## 다루지 않는 범위

- 전단·비틀림 (KDS 14 20 22)
- 처짐·균열폭 등 사용성 상세 검토 (KDS 14 20 30) — 균열모멘트와 균열단면 제원만 제공
- 내구성 (KDS 14 20 40)
- 철근상세·정착·이음 (KDS 14 20 50, 52)
- 프리스트레스트 콘크리트의 강도감소계수 (KDS 14 20 62)
- 2축 휨 기둥의 간략식 (Bresler 등) — 이 모듈은 엄밀 해석으로 상관면을 직접 구한다
- 세장 기둥의 2차 효과(모멘트 확대) — 단면 해석만 수행한다
- 하중조합과 하중계수 (KDS 14 20 01) — 계수 단면력은 사용자가 계산하여 입력한다
