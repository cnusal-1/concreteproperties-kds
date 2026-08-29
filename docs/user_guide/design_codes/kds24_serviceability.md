# KDS 24 — 사용성과 피로

`concreteproperties_kds.kds24.serviceability` 는 **KDS 24 14 21 4.2 (사용한계상태)**
와 **4.3 (피로한계상태)** 를 구현한다.

[KDS 14 — 사용성](kds_serviceability.md)과 뼈대는 같지만 두 가지가 다르다.

* **재료계수가 1.0 이다** (표 1.4-1). 사용·피로한계상태에서는 안전율을 재료에
  걸지 않고, 응력과 균열폭을 직접 제한한다.
* **노출 환경이 설계등급을 정하고, 설계등급이 검증할 하중조합을 정한다.**
  KDS 14 는 균열폭 한계를 환경별로 주는 데 그치지만, KDS 24 는 "어느 하중조합에서
  인장을 아예 허용하지 않을 것인가"까지 등급으로 묶는다.

## 노출 환경 → 설계 등급 → 검증 하중조합

**표 4.2-1** — 노출 환경에 따라 요구되는 최소 설계 등급

| 노출 환경 | 포스트텐션 | 프리텐션 | 비부착 | 철근콘크리트 |
|---|---|---|---|---|
| 건조 또는 영구 수중 (EC1) | D | D | E | E |
| 부식성 (EC2~EC4) | C | C | E | E |
| 고부식성 (ED1~3, ES1~3) | C | **B** | E | E |

**표 4.2-2** — 설계 등급에 따른 사용 한계값

| 등급 | 영(0)응력 한계상태 | 균열폭 한계상태 | 한계균열폭 |
|---|---|---|---|
| A | 사용Ⅰ | — | — |
| B | 사용Ⅲ/Ⅳ | 사용Ⅰ | 0.2 mm |
| C | 사용Ⅴ | 사용Ⅲ/Ⅳ | 0.2 mm |
| D | — | 사용Ⅲ/Ⅳ | 0.3 mm |
| E | — | 사용Ⅴ | 0.3 mm |

"영응력 상태"란 인장측 연단 콘크리트가 압축인 상태를 말한다. 두 한계상태를
**동시에** 만족시켜야 한다.

```python
from concreteproperties_kds.kds24 import minimum_design_grade

grade = minimum_design_grade(exposure="고부식성", member="프리텐션")
grade.grade                       # "B"
grade.zero_stress_combination     # "사용Ⅲ/Ⅳ"
grade.crack_combination           # "사용Ⅰ"
grade.crack_width                 # 0.2
```

**설계의 의도.** 해상 교량의 프리텐션 거더가 B 등급이 되는 이유는 이렇다. 프리텐션
강선은 콘크리트에 직접 묻혀 있어 균열이 곧 부식 경로가 된다. 포스트텐션은 덕트와
그라우트라는 껍질이 한 겹 더 있어 C 로 한 단계 완화된다. 철근콘크리트는 애초에
균열을 전제로 설계하므로 환경과 무관하게 E 다.

## 응력 한계 (4.2.2.1)

| 대상 | 한계 | 하중조합 |
|---|---|---|
| 콘크리트 압축응력 | $0.45 f_{ck}$ | 유효 프리스트레스 + 사용Ⅴ |
| 콘크리트 압축응력 | $0.60 f_{ck}$ | 유효 프리스트레스 + 사용Ⅰ, 제작·운반 시 |
| 철근 인장응력 | $0.80 f_y$ | 사용Ⅰ |
| 긴장재 응력 | $0.65 f_{pu}$ | 유효 프리스트레스 + 사용Ⅴ |

$0.45 f_{ck}$ 는 **크리프가 선형에서 벗어나기 시작하는 지점**이다. 오래 걸려 있는
하중에는 이 선을, 잠깐 지나가는 하중에는 $0.6 f_{ck}$ 를 적용한다.

```python
from concreteproperties_kds.kds24 import (
    concrete_stress_limit, steel_stress_limit, tendon_stress_limit,
)

concrete_stress_limit(fck=40, sustained=True)   # 18.0 MPa
concrete_stress_limit(fck=40)                   # 24.0 MPa
steel_stress_limit(fy=400)                      # 320.0 MPa
tendon_stress_limit(fpu=1860)                   # 1209.0 MPa
```

## 균열 제어

### 최소철근량 (식 (4.2-1))

$$
A_{s,min} = k_c\, k\, A_{ct} \frac{f_{ct}}{f_s}
$$

**균열 직전에 콘크리트가 들고 있던 인장력을, 균열 직후에 철근이 받아 낼 수 있어야
한다**는 평형 조건이다. 그렇지 않으면 첫 균열에서 철근이 곧바로 항복해 균열 하나가
크게 벌어진다.

| 계수 | 값 |
|---|---|
| $k_c$ 순수인장 | 1.0 |
| $k_c$ 휨·축력을 받는 복부 | $0.4\left[1 - f_n / (k_1 (h/h^*) f_{ct})\right] \le 1$ |
| $k$ 부등 응력 분포 | 폭 300 mm 이하 1.0, 800 mm 이상 0.65, 사이는 보간 |

```python
from concreteproperties_kds.kds24 import (
    minimum_crack_reinforcement, nonuniform_stress_factor,
    stress_distribution_factor,
)

stress_distribution_factor(f_n=0.0, f_ct=3.0, h=500)   # 0.4 (휨)
stress_distribution_factor(pure_tension=True)          # 1.0
nonuniform_stress_factor(width=550)                    # 0.825

minimum_crack_reinforcement(a_ct=400 * 350, f_ct=2.6, f_s=400)   # 364.0 mm2
```

### 간접 균열 제어 (표 4.2-4, 표 4.2-5)

균열폭을 직접 계산하는 대신 **철근 지름이나 간격 중 하나**를 제한해 대신할 수 있다.

| 철근 응력 (MPa) | 160 | 200 | 240 | 280 | 320 | 360 |
|---|---|---|---|---|---|---|
| 최대 지름 — 철근콘크리트 (mm) | 32 | 25 | 16 | 14 | 10 | 8 |
| 최대 지름 — 프리스트레스트 (mm) | 25 | 16 | 13 | 8 | 6 | 5 |
| 최대 간격 — RC 순수휨 (mm) | 300 | 250 | 200 | 150 | 100 | 50 |
| 최대 간격 — RC 순수인장 (mm) | 200 | 150 | 125 | 75 | — | — |
| 최대 간격 — PSC (mm) | 200 | 150 | 100 | 50 | — | — |

```python
from concreteproperties_kds.kds24 import max_bar_diameter, max_bar_spacing

max_bar_diameter(f_s=240)                              # 16.0 mm
max_bar_diameter(f_s=180)                              # 28.5 mm (보간)
max_bar_spacing(f_s=240)                               # 200.0 mm
max_bar_spacing(f_s=240, member="프리스트레스트")        # 100.0 mm
```

표에 값이 없는 구간은 **거부한다.** 철근 응력이 그만큼 높으면 간접 방법으로는
균열폭을 담보할 수 없다는 뜻이므로, 철근량을 늘려 응력을 낮추어야 한다.

```python
max_bar_spacing(f_s=300, member="프리스트레스트")
# ValueError: 표 4.2-5 는 철근 응력 300 MPa 를 다루지 않는다. ...
```

### 균열폭 계산 (4.2.3.4)

$$
w_k = l_{r,max} \left( \varepsilon_{sm} - \varepsilon_{cm} \right)
\qquad \text{(식 (4.2-4))}
$$

$$
\varepsilon_{sm} - \varepsilon_{cm}
= \frac{f_{so}}{E_s} - k_t \frac{f_{cte}}{E_s \rho_e} (1 + n \rho_e)
\ \ge 0.6 \frac{f_{so}}{E_s}
\qquad \text{(식 (4.2-5))}
$$

$$
l_{r,max} = 3.4 c_c + \frac{0.425 k_1 k_2 d_b}{\rho_e}
\qquad \text{(식 (4.2-7a))}
$$

빼는 항이 **인장강화효과**다. 균열과 균열 사이의 콘크리트가 아직 인장을 나눠 지고
있어 철근 변형률이 균열면 값보다 작다는 뜻이며, 하한 $0.6 f_{so}/E_s$ 는 그 효과를
지나치게 크게 보지 않도록 막는다.

균열 간격 쪽은 **피복이 두껍고, 철근이 굵고, 철근비가 낮을수록** 커진다. 균열이
드문드문 생기면 그만큼 하나하나가 넓어진다.

| 계수 | 값 |
|---|---|
| $k_t$ | 단기하중 0.6, 장기하중 0.4 |
| $k_1$ | 이형철근 0.8, 원형철근·긴장재 1.6 |
| $k_2$ | 휨 0.5, 직접인장 1.0 |

```python
from concreteproperties_kds.kds24 import crack_width, effective_tension_depth

effective_tension_depth(h=700, d=640, c=200)   # 150.0 mm

result = crack_width(
    f_so=200.0, fck=30.0, rho_e=0.03, c_c=40.0, d_b=16.0, limit=0.3
)
result.w_k              # 0.169 mm
result.crack_spacing    # 226.7 mm
result.adequate         # True
```

### 복부의 유효인장강도 (식 (4.2-3))

$$
f_{cte} = \left( 1 - 0.8 \frac{f_2}{f_{ck}} \right) f_{ctk}
$$

복부가 이미 사압축 $f_2$ 를 받고 있으면 인장 쪽 여력이 준다. PSC 거더 복부의
사인장 균열을 다룰 때 쓴다.

## 처짐 (4.2.4.1)

| 조건 | 한계 |
|---|---|
| 단순·연속경간 | $L/800$ |
| 단순·연속경간, 보행자도 이용 | $L/1{,}000$ |
| 캔틸레버 | $L/300$ |
| 캔틸레버, 보행자 이용 | $L/375$ |

```python
from concreteproperties_kds.kds24 import deflection_limit

deflection_limit(span=30000)                     # 37.5 mm
deflection_limit(span=30000, pedestrian=True)    # 30.0 mm
```

처짐 계산용 활하중은 KDS 24 12 21 4.3.1.7 에 따라 **트럭 단독**과 **트럭 25 % +
차로하중** 중 큰 값을 쓴다. 강도 검토의 75 % 와 헷갈리지 않도록 주의한다.

## 피로한계상태 (4.3)

피로 검증은 **철근에 대해서만** 수행한다 (4.3.1(1)). 다중 거더 상부구조의
콘크리트 바닥판은 검증하지 않아도 된다 (4.3.1(2)).

### 검증이 필요한가

고정하중과 프리스트레스에 의한 압축응력이 피로하중조합의 최대 활하중 인장응력의
**두 배 미만**일 때만 검증한다 (4.3.1(4)). 압축이 충분히 크면 철근이 인장으로
넘어가지 않아 응력 진폭 자체가 생기지 않기 때문이다.

```python
from concreteproperties_kds.kds24 import fatigue_check_required

fatigue_check_required(f_dead_compression=5.0, f_live_tension=4.0)    # True
fatigue_check_required(f_dead_compression=10.0, f_live_tension=4.0)   # False
```

### 허용 응력범위 (식 (4.3-1), (4.3-2))

$$
f_{fat} = 166 - 0.33 f_{min} \quad (\text{가로 용접 없음})
$$

$$
f_{fat} = 110 - 0.33 f_{min} \quad (\text{가로 용접 있음})
$$

$f_{min}$ 은 피로하중조합에 의한 **최소 활하중 응력**이며 인장이 양수다. 이미
인장을 받고 있는 철근일수록 허용 진폭이 줄어든다. 휨철근의 고응력영역은 최대모멘트
단면에서 좌우로 지간의 1/3 이다.

```python
from concreteproperties_kds.kds24 import fatigue_stress_range_limit

fatigue_stress_range_limit()                       # 166.0 MPa
fatigue_stress_range_limit(f_min=100.0)            # 133.0 MPa
fatigue_stress_range_limit(f_min=-50.0)            # 182.5 MPa (압축이면 여유가 는다)
fatigue_stress_range_limit(welded=True)            # 110.0 MPa
```

### 이음부 (표 4.3-1)

| 이음부 | $f_{fat}$ (1백만 회 초과) |
|---|---|
| 그라우트 채움 연결부, 냉간-압연 무나선 슬리브, 일체식 단조 | 126 MPa |
| 쐐기식 강재 슬리브, 일체식 경사-나선, V-홈 직접 용접 | 84 MPa |
| 그 외 모든 이음 | 28 MPa |

재하수 $N_{cyc}$ 가 1백만 회 이하이면 $168(6 - \log N_{cyc})$ MPa 만큼 올릴 수
있되, 식 (4.3-1) 의 값을 넘지 못한다.

```python
from concreteproperties_kds.kds24 import coupler_fatigue_strength

coupler_fatigue_strength("그라우트채움")                    # 126.0 MPa
coupler_fatigue_strength("기타")                           # 28.0 MPa
coupler_fatigue_strength("기타", n_cycles=1.0e5)           # 166.0 MPa (상한에 걸림)
```

긴장재의 피로응력범위는 곡률 반경 9,000 mm 이상이면 125 MPa, 3,600 mm 이하이면
70 MPa 이고 그 사이는 선형보간한다 (4.3.3).
