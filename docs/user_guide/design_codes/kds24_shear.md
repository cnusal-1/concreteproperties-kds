# KDS 24 — 전단

`concreteproperties_kds.kds24.shear` 는 **KDS 24 14 21 4.1.2** 를 구현한다.
[KDS 14 — 전단 및 비틀림](kds_shear.md)과 **모델 자체가 다르다.**

## 두 기준의 전단 모델

| | KDS 14 20 22 | KDS 24 14 21 4.1.2 |
|---|---|---|
| 모델 | 콘크리트 기여분 + 트러스 | 변각 트러스 |
| 설계강도 | $\phi(V_c + V_s)$ | $V_{sd}$ **단독** |
| 콘크리트 몫 | 늘 더한다 | 전단철근이 있으면 더하지 않는다 |
| 스트럿 각도 | 45° 고정 | $1 \le \cot\theta \le 2.5$ 로 선택 |
| $V_c$ 의 변수 | $\sqrt{f_{ck}}$ | $(\rho f_{ck})^{1/3}$ — **철근비가 들어간다** |

**설계 사상.** KDS 14 는 "콘크리트가 얼마쯤 버티고 나머지를 철근이 받는다"고 본다.
KDS 24 는 "균열이 난 뒤에는 철근이 다 받는다. 대신 스트럿 각도를 눕혀 하나의
균열을 더 많은 스터럽이 가로지르게 할 수 있다"고 본다. 그 자유도가
$\cot\theta$ 다.

수치 비교는 {ref}`비교 문서 4절 <전단-비교>` 을 참고한다.

## 전단철근이 없는 부재 (4.1.2.2)

$$
V_{cd} = \left[ 0.85 \phi_c \kappa (\rho f_{ck})^{1/3} + 0.15 f_n \right] b_w d
\qquad \text{(식 (4.1-7))}
$$

$$
V_{cd,min} = \left( 0.4 \phi_c f_{ctk} + 0.15 f_n \right) b_w d
\qquad \text{(식 (4.1-8))}
$$

둘 중 큰 값을 쓴다.

| 기호 | 뜻 | 제한 |
|---|---|---|
| $\kappa$ | 단면 크기 효과 $1 + \sqrt{200/d}$ | $\le 2.0$ ($d$ 는 mm) |
| $\rho$ | 인장철근비 $A_s/(b_w d)$ | $\le 0.02$ |
| $f_n$ | 평균 축응력 $N_u/A_c$ (압축이 +) | $\le 0.2 \phi_c f_{ck}$ |

$(\rho f_{ck})^{1/3}$ 이 이 식의 핵심이다. **철근비가 강도만큼 중요하다.** 철근이
많으면 균열이 촘촘하고 좁게 생겨 골재 맞물림이 잘 살아 있기 때문이다.
$\kappa$ 는 반대로 깊은 단면일수록 단위면적당 강도가 떨어진다는 크기 효과를
반영한다 — $d$ = 200 mm 에서 상한 2.0 에 걸린다.

```python
from concreteproperties_kds.kds24 import (
    axial_stress, design_concrete_shear_strength, kappa,
)

kappa(d=640)     # 1.559
kappa(d=200)     # 2.0 (상한)

design_concrete_shear_strength(fck=40, b_w=400, d=640, a_s=2026.8) / 1e3
# 174.2 kN — 철근비 0.79 % 에서는 식 (4.1-8) 의 하한이 지배한다

f_n = axial_stress(n_u=1.0e6, a_c=400 * 700, fck=40)   # 3.57 MPa
```

### 휨균열이 없는 프리스트레스트 구간 (식 (4.1-9))

$$
V_{cd} = \frac{I b_w}{Q}
\sqrt{(\phi_c f_{ctk})^2 + \alpha_l f_n \phi_c f_{ctk}}
$$

휨균열이 없으면 단면 전체가 살아 있으므로, **주인장응력이 콘크리트 인장강도에
닿는 순간**을 강도로 본다. 프리스트레스에 의한 압축 $f_n$ 이 클수록 그 순간이 늦게
온다. PSC 거더의 받침부 근처가 이 경우다.

```python
from concreteproperties_kds.kds24 import uncracked_shear_strength

uncracked_shear_strength(
    fck=40, b_w=400, second_moment=1.14e10, first_moment=2.45e7, f_n=6.0
) / 1e3
```

## 전단철근이 있는 부재 (4.1.2.3)

$$
V_{sd} = \frac{\phi_s f_{vy} A_v z}{s} \cot\theta
\qquad \text{(식 (4.1-16))}, \qquad z \approx 0.9 d
$$

$$
V_{d,max} = \frac{\nu \phi_c f_{ck} b_w z}{\cot\theta + \tan\theta}
\qquad \text{(식 (4.1-17))}
$$

$$
\nu = 0.6 \left( 1 - \frac{f_{ck}}{250} \right)
\qquad \text{(식 (4.1-12))}
$$

$\nu$ 는 콘크리트 압축강도 유효계수다. 균열이 난 복부의 스트럿은 온전한
압축시험체만큼 강하지 않고, 고강도일수록 취성이 커져 더 깎인다.

### $\cot\theta$ 를 고른다는 것

$V_{sd}$ 는 $\cot\theta$ 에 **비례**하고, $V_{d,max}$ 는 $\cot\theta + \tan\theta$
에 **반비례**한다. 두 요구가 반대로 움직인다.

| $\cot\theta$ | $\theta$ | $V_{sd}$ (상대) | $V_{d,max}$ (상대) |
|---|---|---|---|
| 1.0 | 45° | 1.00 | 1.00 |
| 1.5 | 33.7° | 1.50 | 0.92 |
| 2.0 | 26.6° | 2.00 | 0.80 |
| 2.5 | 21.8° | 2.50 | 0.69 |

스트럿을 눕히면 스터럽을 아낄 수 있지만 복부가 먼저 깨진다. 복부가 두꺼운
거더라면 $\cot\theta$ = 2.5 로 스터럽을 크게 줄일 수 있고, 복부가 얇으면
$V_{d,max}$ 가 먼저 걸려 눕힐 수 없다.

```python
from concreteproperties_kds.kds24 import (
    check_shear, max_shear_strength, required_stirrup_spacing,
    shear_reinforcement_strength,
)

# D13 2가닥 @200
a_v = 2 * 126.7
shear_reinforcement_strength(f_vy=400, a_v=a_v, d=640, s=200, cot_theta=2.5) / 1e3
# 656.8 kN

max_shear_strength(fck=40, b_w=400, d=640, cot_theta=2.5) / 1e3   # 1041.1 kN
max_shear_strength(fck=40, b_w=400, d=640, cot_theta=1.0) / 1e3   # 1509.6 kN

# 요구 전단력으로부터 필요한 간격
required_stirrup_spacing(v_ed=600e3, d=640, a_v=a_v)   # 218.9 mm
```

### 축방향 압축이 있을 때 (식 (4.1-22), (4.1-23))

$$
V_{d,max,com} = \alpha_{cw} V_{d,max}
$$

$$
\alpha_{cw} = \begin{cases}
1 + f_n / \phi_c f_{ck} & 0 < f_n \le 0.25 \phi_c f_{ck} \\
1.25 & 0.25 \phi_c f_{ck} < f_n \le 0.50 \phi_c f_{ck} \\
2.5 \left( 1 - f_n / \phi_c f_{ck} \right)
& 0.50 \phi_c f_{ck} < f_n \le 1.0 \phi_c f_{ck}
\end{cases}
$$

프리스트레스가 적당하면 스트럿 한계가 최대 25 % 올라간다. 사압축 방향이
스트럿과 맞아떨어져 복부가 유리해지기 때문이다. 그러나 지나치면 복부가 이미
압축으로 차 있어 오히려 떨어진다.

```python
from concreteproperties_kds.kds24 import alpha_cw

alpha_cw(f_n=0.10 * 0.65 * 40, fck=40)   # 1.10
alpha_cw(f_n=0.40 * 0.65 * 40, fck=40)   # 1.25 (평탄 구간)
alpha_cw(f_n=0.75 * 0.65 * 40, fck=40)   # 0.625 (역전)
```

## 종합 검토

```python
result = check_shear(
    v_ed=600e3, fck=40, b_w=400, d=640, a_s=2026.8,
    a_v=2 * 126.7, s=200, cot_theta=2.5,
)

result.v_cd              # 174,208 N — 전단철근 필요 여부의 문턱
result.v_sd              # 656,813 N — 실제 설계강도
result.v_d_max           # 1,041,090 N — 스트럿 한계
result.stirrups_required # True
result.adequate          # True
```

`v_cd` 가 계산되긴 하지만 **강도에 더해지지 않는다.** 이 값은 4.1.2.1(5), (6) 에
따라 "계산에 의한 전단철근이 필요한가, 최소량만 넣으면 되는가"를 가르는 문턱으로만
쓰인다.

## 상세 규정

| 항목 | 식 | 값 |
|---|---|---|
| 최소 전단철근비 | 식 (4.6-7) | $\rho_{v,min} = 0.08\sqrt{f_{ck}}/f_y$ |
| 최대 종방향 간격 | 식 (4.6-8) | $s_{max} = 0.75d(1 + \cot\alpha)$ |
| 최대 전단철근량 | 식 (4.1-18) | $\phi_s f_y A_{v,max}/(b_w s) \le 0.5\nu\phi_c f_{ck}$ |
| 스트럿 각도 | 식 (4.1-15) | $1 \le \cot\theta \le 2.5$ |

```python
from concreteproperties_kds.kds24 import (
    maximum_shear_reinforcement, maximum_stirrup_spacing,
    minimum_shear_reinforcement_ratio,
)

minimum_shear_reinforcement_ratio(fck=40, f_y=400)   # 0.001265
maximum_stirrup_spacing(d=640)                       # 480.0 mm (수직 스터럽)
maximum_stirrup_spacing(d=640, alpha=45)             # 960.0 mm
maximum_shear_reinforcement(fck=40, b_w=400, s=200, f_y=400)   # 1456.0 mm2
```

범위를 벗어난 $\cot\theta$ 는 거부한다.

```python
max_shear_strength(fck=40, b_w=400, d=640, cot_theta=3.0)
# ValueError: cot_theta 는 1.0 이상 2.5 이하여야 한다 (식 (4.1-15)): 3.0
```
