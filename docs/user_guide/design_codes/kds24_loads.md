# KDS 24 — 하중조합과 설계하중

`concreteproperties_kds.kds24.loads` 와 `kds24.live_load` 는 교량 설계의 하중 쪽을
다룬다. 근거는 **KDS 24 12 11 (설계하중조합)**, **KDS 24 12 21 (설계하중)**,
**KDS 24 10 11 1.3 (한계상태와 하중수정계수)** 이다.

KDS 14 의 하중조합([KDS 14 — 하중조합](kds_loads.md))과 형식이 완전히 다르다.
건축은 $U = 1.2D + 1.6L$ 한 줄로 끝나지만, 교량은 한계상태를 넷으로 쪼개고
상시하중마다 최대·최소 두 계수를 두며, 활하중은 등분포가 아니라 **트럭을 다리
위로 굴려 가며** 찾는다.

## 설계식

$$
\sum \eta_i \gamma_i Q_i \le \phi R_n
\qquad \text{(KDS 24 10 11 식 (1.3-1))}
$$

우변의 $\phi R_n$ 은 콘크리트 부재에서 재료계수가 이미 반영된 설계강도이므로,
[`KDS24`](kds24.md#kds24-설계기준-클래스) 가 돌려주는 값을 그대로 쓴다.

## 하중조합 13가지 (표 4.1-1)

| 조합 | 뜻 | 활하중 계수 |
|---|---|---|
| 극한Ⅰ | 일반적인 차량통행. 풍하중 없음 | 1.80 |
| 극한Ⅱ | 특수차량·통행허가차량. 풍하중 없음 | 1.40 |
| 극한Ⅲ | 거더 높이 풍속 25 m/s 초과. 활하중 없음 | — (WS 1.40) |
| 극한Ⅳ | 활하중에 비해 고정하중이 매우 큰 경우 | — (**DC 1.50**) |
| 극한Ⅴ | 통행 가능한 최대 풍속 + 일상적인 통행 | 1.40 |
| 극단상황Ⅰ | 지진 | 발주자 결정 |
| 극단상황Ⅱ | 빙·선박·차량 충돌 | 0.50 |
| 사용Ⅰ | 정상 운용. RC 사용성 검증 | 1.00 |
| 사용Ⅱ | 강구조물 항복·마찰이음부 미끄러짐 | 1.30 |
| 사용Ⅲ | 부착 긴장재 상부구조의 균열폭·인장응력 | 0.80 |
| 사용Ⅳ | 하부구조. 연직 활하중 대신 수평 풍하중 | — (WS 0.70) |
| 사용Ⅴ | 고정하중 + 수명의 50 % 지속하중 | — |
| 피로 | 피로설계트럭. LL, IM, CF 만 | 0.75 |

```python
from concreteproperties_kds.kds24 import (
    COMBINATIONS_BY_NAME, evaluate_all, governing_combination,
)

loads = {"DC": 100.0, "DW": 20.0, "LL": 50.0, "IM": 12.5}

COMBINATIONS_BY_NAME["극한Ⅰ"].evaluate(loads=loads)
# 1.25*100 + 1.50*20 + 1.80*62.5 = 267.5

governing_combination(loads=loads)     # ("극한Ⅰ", 267.5)
evaluate_all(loads=loads, limit_state="사용")   # 사용 Ⅰ~Ⅴ 만
```

## 상시하중의 최대·최소 계수 (표 4.1-2)

| 하중 | 최대 | 최소 |
|---|---|---|
| DC 구조부재 자중 | 1.25 (극한Ⅳ 에서만 1.50) | 0.90 |
| DD 말뚝 부마찰력 | 1.80 | 0.45 |
| DW 포장·시설물 | 1.50 | 0.65 |
| EH 수평토압 (주동 / 정지) | 1.50 / 1.35 | 0.90 |
| EV 연직토압 (옹벽·교대) | 1.35 | 1.00 |
| EV 연직토압 (연성암거) | 1.95 | 0.90 |
| ES 상재토하중 | 1.50 | 0.75 |
| EL, PS, CR, SH | 1.00 | 1.00 |

**설계의 의도.** 상시하중이 늘 불리하지만은 않다. 옹벽의 뒤채움 흙은 전도에는
불리하고 활동 저항에는 유리하다. 그래서 KDS 24 는 계수를 하나로 고정하지 않고,
**검토하는 파괴 모드에서 불리한 쪽을 고르게** 한다 (4.1(4)).

```python
from concreteproperties_kds.kds24 import COMBINATIONS_BY_NAME, permanent_load_factor

permanent_load_factor("DC")                    # 1.25
permanent_load_factor("DC", maximum=False)     # 0.90
permanent_load_factor("EV_연성암거")            # 1.95

loads = {"DC": 100.0, "DW": 20.0}
COMBINATIONS_BY_NAME["극한Ⅰ"].evaluate(loads=loads, maximise=True)   # 155.0
COMBINATIONS_BY_NAME["극한Ⅰ"].evaluate(loads=loads, maximise=False)  #  103.0
```

극한Ⅳ 가 따로 있는 이유도 여기서 나온다. 고정하중이 지배하는 장대교에서는
DC 1.50 이 극한Ⅰ 의 (DC 1.25 + LL 1.80)을 넘어선다.

```python
loads = {"DC": 1000.0, "LL": 5.0}
governing_combination(loads=loads)     # ("극한Ⅳ", 1500.0)
```

## 하중수정계수 $\eta$

$$
\eta = \eta_D \eta_R \eta_I \ge 0.95 \ (\text{최대하중계수}),
\qquad
\eta = \frac{1}{\eta_D \eta_R \eta_I} \le 1.0 \ (\text{최소하중계수})
$$

| 계수 | 1.05 | 1.00 | 0.95 |
|---|---|---|---|
| 연성 $\eta_D$ | 비연성 부재 | 통상 설계 | 추가 연성보강 |
| 여용성 $\eta_R$ | 비여용부재 | 통상 여용수준 | 특별한 여용수준 |
| 중요도 $\eta_I$ | 중요 교량 | 일반 교량 | 중요도 낮음 |

같은 불확실성이라도 **부재가 망가졌을 때 다리 전체가 어떻게 되는가**는 다르다.
대체 하중경로가 없는 부재, 연성이 없는 부재, 중요한 다리에는 5 % 를 더 준다.
기타 한계상태에서는 모두 1.0 이다.

```python
from concreteproperties_kds.kds24 import load_modifier

load_modifier(ductility=1.05, redundancy=1.05, importance=1.00)   # 1.1025
load_modifier(0.95, 0.95, 0.95)                                   # 0.95 (하한)
```

## 차량활하중 KL-510

**KDS 24 12 21 4.3.1.3** — 활하중은 표준트럭하중과 표준차로하중으로 이루어진다.

### 표준트럭하중 (그림 4.3-1)

```
   48 kN      192 kN            135 kN  135 kN
     │          │                  │      │
     ●──3.6 m───●──────7.2 m───────●─1.2─●
     └───────────── 12.0 m ─────────────┘     합계 510 kN → "KL-510"
```

### 표준차로하중 (표 4.3-2)

$$
\omega = 12.7\ \text{kN/m} \ (L \le 60\ \text{m}),
\qquad
\omega = 12.7 \left( \frac{60}{L} \right)^{0.10} \ (L > 60\ \text{m})
$$

횡방향으로 3,000 mm 폭에 균등 분포하며, **충격하중을 적용하지 않는다.**

### 주거더 설계 (4.3.1.5)

다음 둘 중 **큰 값**을 쓴다.

1. 표준트럭하중의 영향
2. 표준트럭하중 영향의 **75 %** 와 표준차로하중 영향의 합

```python
from concreteproperties_kds.kds24 import girder_live_load, truck_moment, lane_moment

effect = girder_live_load(span=30.0)
print(f"설계 M = {effect.moment:.0f} kN.m  ({effect.governed_by})")
# 설계 M = 4094 kN.m  (트럭 75 % + 차로)

truck_moment(span=30.0)    # 2843.0 kN.m — Barre 정리로 손검산되는 값
lane_moment(span=30.0)     # 1428.8 kN.m
```

`truck_moment()` 는 트럭을 지간 위로 촘촘히 옮겨 가며 각 축 아래의 모멘트를 모두
살핀다. 단순보의 최대 휨모멘트는 언제나 어느 한 축 바로 아래에서 생기므로 이렇게
훑으면 정확한 값이 나온다. 지간 밖으로 나간 축은 세지 않는다.

**왜 두 가지를 다 보는가.** 지간이 짧으면 트럭 한 대의 국부적인 집중이 지배하고,
길어지면 줄지어 선 차량의 총 무게가 이긴다. 실제로 10 m 지간에서는 차로하중이
설계값의 21 % 지만, 80 m 에서는 53 % 까지 올라간다.

| 지간 | 트럭 $M$ | 차로 $M$ | 설계 $M$ | 지배 |
|---|---|---|---|---|
| 10 m | 596 kN·m | 159 kN·m | 746 kN·m | 트럭 |
| 30 m | 2,843 kN·m | 1,429 kN·m | 4,094 kN·m | 트럭 75 % + 차로 |
| 80 m | 9,187 kN·m | 9,872 kN·m | 18,485 kN·m | 트럭 75 % + 차로 |

### 재하차로와 다차로 재하계수

$$
N = \left\lfloor \frac{W_C}{W_P} \right\rfloor,
\qquad
W = \frac{W_C}{N} \le 3.6\ \text{m}
$$

다만 $N = 1$ 이고 $W_C \ge 6.0$ m 이면 2 로 한다. 차선이 그려져 있든 아니든 폭이
6 m 넘게 열려 있으면 차 두 대가 나란히 설 수 있기 때문이다.

| 재하차로 수 | 1 | 2 | 3 | 4 | 5 이상 |
|---|---|---|---|---|---|
| 다차로 재하계수 $m$ | 1.00 | 0.90 | 0.80 | 0.70 | 0.65 |

```python
from concreteproperties_kds.kds24 import lane_width, multiple_presence, number_of_lanes

number_of_lanes(roadway_width=10.8)   # 3
number_of_lanes(roadway_width=6.0)    # 2 (단서 조항)
lane_width(roadway_width=10.8, n_lanes=3)   # 3.6 m
multiple_presence(n_lanes=3)          # 0.80
```

### 충격하중 (표 4.4-1)

| 성분 | IM |
|---|---|
| 피로한계상태를 제외한 모든 한계상태 | 25 % |
| 피로한계상태 | 15 % |

정적 하중에 $(1 + IM/100)$ 을 곱한다. **표준트럭하중에만** 적용하고, 보도하중과
표준차로하중에는 적용하지 않는다.

암거·매설 구조물은 토피가 깊을수록 충격이 준다.

$$
IM = 40 \left( 1.0 - 4.1 \times 10^{-4} D_E \right) \ge 0\ \%
\qquad \text{(식 (4.4-1))}
$$

2,439 mm 에서 0 이 된다.

```python
from concreteproperties_kds.kds24 import impact_buried, impact_factor

impact_factor()                     # 1.25
impact_factor(limit_state="피로")    # 1.15
impact_buried(cover_depth=1000)     # 23.6 %
```

### 피로하중 (4.3.2)

피로검토용 활하중은 표준트럭하중의 **80 %** 이고 충격은 15 % 를 쓴다. 다차로
재하계수는 적용하지 않는다.

$$
ADTT_{SL} = p \times ADTT
$$

| 트럭 통행 가능 차로 수 | 1 | 2 | 3 이상 |
|---|---|---|---|
| $p$ | 1.00 | 0.85 | 0.80 |

```python
from concreteproperties_kds.kds24 import adtt_single_lane, fatigue_truck_moment

fatigue_truck_moment(span=30.0)                        # 2615.6 kN.m
adtt_single_lane(adtt=2000, n_truck_lanes=2)           # 1700.0
```

## 교량의 등급 (KDS 24 10 11 1.4)

| 등급 | 활하중효과 |
|---|---|
| 1등교 | KL-510 전체 (100 %) |
| 2등교 | 1등교의 75 % |
| 3등교 | 2등교의 75 % = 56.25 % |

```python
from concreteproperties_kds.kds24 import bridge_grade_factor

bridge_grade_factor(2)    # 0.75
bridge_grade_factor(3)    # 0.5625
```
