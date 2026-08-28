# 하중조합 (KDS 14 20 10 4.2.2)

`concreteproperties_kds.loads` 는 강도설계법의 하중계수 조합을 정의하고, 하중
성분으로부터 소요강도 $U$ 를 계산한다. 조합은 KDS 14 20 10 4.2.2 의 식
(4.2-1) ~ 식 (4.2-8) 원문을 그대로 옮긴 것이다.

## 하중 기호

| 기호 | 의미 | | 기호 | 의미 |
|---|---|---|---|---|
| `D` | 고정하중 | | `W` | 풍하중 |
| `L` | 활하중 | | `E` | 지진하중 |
| `L_r` | 지붕활하중 | | `F` | 유체압 |
| `S` | 적설하중 | | `H_h` | 횡방향 토압 |
| `R` | 강우하중 | | `H_v` | 연직방향 토압 |
| `T` | 온도·크리프·건조수축·부등침하 등의 영향 | | | |

`L_r`, `S`, `R` 은 지붕에 작용하는 변동하중으로 **택일**하며, 조합에서는 세 값 중
큰 것을 쓴다.

## 하중조합

| 식 | 조합 |
|---|---|
| (4.2-1) | $U = 1.4(D + F)$ |
| (4.2-2) | $U = 1.2(D+F+T) + 1.6(L + \alpha_H H_v + H_h) + 0.5(L_r \text{ or } S \text{ or } R)$ |
| (4.2-3) | $U = 1.2D + 1.6(L_r \text{ or } S \text{ or } R) + (1.0L \text{ or } 0.65W)$ |
| (4.2-4) | $U = 1.2D + 1.3W + 1.0L + 0.5(L_r \text{ or } S \text{ or } R)$ |
| (4.2-5) | $U = 1.2(D+H_v) + 1.0E + 1.0L + 0.2S + (1.0H_h \text{ or } 0.5H_h)$ |
| (4.2-6) | $U = 1.2(D+F+T) + 1.6(L + \alpha_H H_v) + 0.8H_h + 0.5(L_r \text{ or } S \text{ or } R)$ |
| (4.2-7) | $U = 0.9(D+H_v) + 1.3W + (1.6H_h \text{ or } 0.8H_h)$ |
| (4.2-8) | $U = 0.9(D+H_v) + 1.0E + (1.0H_h \text{ or } 0.5H_h)$ |

"또는" 으로 택일하는 항은 각각 별도의 조합으로 전개하여 (`U3-L`/`U3-W`,
`U5-a`/`U5-b`, `U7-a`/`U7-b`, `U8-a`/`U8-b`), 어느 쪽이 지배하는지 확인할 수 있다.

식 (4.2-7)·(4.2-8) 은 고정하중 계수를 0.9 로 낮춘 조합으로, 풍하중·지진하중에
의한 **부양이나 전도**를 검토할 때 쓴다.

## 연직토압 보정계수

$$\alpha_H = \begin{cases}
1.0 & h \le 2\ \text{m} \\
1.05 - 0.025h \ \ge 0.875 & h > 2\ \text{m}
\end{cases}$$

$h$ 는 토피 깊이(m)이다. 식 (4.2-2)·(4.2-6) 의 $H_v$ 에만 곱해진다.

```python
from concreteproperties_kds.loads import alpha_h

alpha_h(depth=1.5)    # 1.0
alpha_h(depth=3.0)    # 0.975
alpha_h(depth=10.0)   # 0.875 (하한)
```

## 사용법

```python
from concreteproperties_kds.loads import print_combinations, required_strength

loads = {"D": 25.0, "L": 18.0, "L_r": 3.0, "S": 5.0, "W": 12.0, "E": 20.0}

print_combinations(loads=loads)

u_max, governing = required_strength(loads=loads)
print(f"{governing.name} ({governing.equation}) : wu = {u_max:.2f} kN/m")
# U5-a (4.2-5) : wu = 69.00 kN/m
```

출력 예:

```
     조합        식            U
------------------------------------------------------------------------------
   U5-a    4.2-5        69.00  U = 1.2(D+H_v) + 1.0E + 1.0L + 0.2S + 1.0H_h  <= 지배
   U5-b    4.2-5        69.00  U = 1.2(D+H_v) + 1.0E + 1.0L + 0.2S + 0.5H_h
     U4    4.2-4        66.10  U = 1.2D + 1.3W + 1.0L + 0.5(L_r or S or R)
     U2    4.2-2        61.30  U = 1.2(D+F+T) + 1.6(L + aH*H_v + H_h) + 0.5(...)
     U6    4.2-6        61.30  U = 1.2(D+F+T) + 1.6(L + aH*H_v) + 0.8H_h + 0.5(...)
   U3-L    4.2-3        56.00  U = 1.2D + 1.6(L_r or S or R) + 1.0L
   U3-W    4.2-3        45.80  U = 1.2D + 1.6(L_r or S or R) + 0.65W
   U8-a    4.2-8        42.50  U = 0.9(D + H_v) + 1.0E + 1.0H_h
   U7-a    4.2-7        38.10  U = 0.9(D + H_v) + 1.3W + 1.6H_h
     U1    4.2-1        35.00  U = 1.4(D + F)
```

토피가 있는 구조는 `depth` 를 준다.

```python
u_max, governing = required_strength(
    loads={"D": 25.0, "H_v": 40.0, "H_h": 30.0}, depth=5.0
)
```

## 부양·전도 검토

`minimum_strength` 는 가장 작은 조합 하중과 그 조합을 반환한다.

```python
from concreteproperties_kds.loads import minimum_strength

u_min, governing = minimum_strength(loads={"D": 100.0, "W": -300.0})
print(governing.equation)   # 4.2-7
```

## 활하중 계수 저감

활하중이 5.0 kN/m² 미만이고 차고·공공집회 장소가 아니면 식 (4.2-3), (4.2-4),
(4.2-5) 의 활하중 계수를 1.0 에서 0.5 로 낮출 수 있다 (KDS 14 20 10 4.2.2(2)).

```python
u_max, governing = required_strength(loads=loads, reduce_live_load=True)
```

식 (4.2-2)·(4.2-6) 의 활하중 계수는 1.6 이므로 저감 대상이 아니다.

## 하중조합 수정

기준 개정이나 특수한 검토를 위해 조합을 바꾸려면 `LoadCombination` 을 직접
만들어 넘긴다.

```python
from concreteproperties_kds.loads import LoadCombination, required_strength

custom = (
    LoadCombination(
        name="C1", equation="사용자", factors={"D": 1.4}, description="U = 1.4D"
    ),
    LoadCombination(
        name="C2",
        equation="사용자",
        factors={"D": 1.2, "L": 1.6},
        description="U = 1.2D + 1.6L",
    ),
)

u_max, governing = required_strength(
    loads={"D": 25.0, "L": 18.0}, combinations=custom
)
```

## API

| 함수/클래스 | 내용 |
|---|---|
| `LoadCombination(name, equation, factors, roof, alpha_h_symbols, live_load_reducible, description)` | 하중조합 하나. `evaluate(loads, depth, reduce_live_load)` |
| `LOAD_COMBINATIONS` | 식 (4.2-1) ~ (4.2-8) 을 전개한 12개 조합 |
| `alpha_h(depth)` | 연직토압 보정계수 |
| `required_strength(loads, ...)` | `(최대 U, 지배 조합)` |
| `minimum_strength(loads, ...)` | `(최소 U, 해당 조합)` — 부양·전도 검토 |
| `evaluate_all(loads, ...)` | 모든 조합의 결과를 큰 순서로 |
| `print_combinations(loads, ...)` | 결과를 표로 출력 |
| `LOAD_SYMBOLS`, `ROOF_LOADS` | 하중 기호 |
| `LIVE_LOAD_REDUCTION_THRESHOLD`, `LIVE_LOAD_FACTOR_REDUCED` | 5.0 kN/m², 0.5 |
