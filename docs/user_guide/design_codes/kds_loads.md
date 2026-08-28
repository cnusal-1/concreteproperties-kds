# 하중조합 (KDS 14 20 01)

`concreteproperties_kds.loads` 는 강도설계법의 하중계수 조합을 정의하고, 하중
성분으로부터 소요강도 $U$ 를 계산한다.

> **주의** — 하중계수는 개정 이력이 잦다. `LOAD_COMBINATIONS` 에 정의된 조합을
> 현행 KDS 14 20 01 및 KDS 41(건축구조기준)과 대조한 뒤 사용한다.

## 하중 기호

| 기호 | 의미 |
|---|---|
| `D` | 고정하중 |
| `L` | 활하중 |
| `L_r` | 지붕활하중 |
| `S` | 적설하중 |
| `R` | 강우하중 |
| `W` | 풍하중 |
| `E` | 지진하중 |
| `F` | 유체압 |
| `H_h` | 토압 (수평) |
| `H_v` | 토압 (연직) |
| `T` | 온도·건조수축·크리프·부등침하 등의 영향 |

`L_r`, `S`, `R` 은 지붕에 작용하는 변동하중으로 **택일**하며, 조합에서는 세 값 중
큰 것을 쓴다.

## 하중조합

| 조합 | 식 |
|---|---|
| U1 | $1.4(D + F)$ |
| U2 | $1.2(D + F + T) + 1.6(L + H_v + H_h) + 0.5(L_r \text{ or } S \text{ or } R)$ |
| U3 | $1.2D + 1.6(L_r \text{ or } S \text{ or } R) + 1.0L$ |
| U4 | $1.2D + 1.6(L_r \text{ or } S \text{ or } R) + 0.65W$ |
| U5 | $1.2D + 1.3W + 1.0L + 0.5(L_r \text{ or } S \text{ or } R)$ |
| U6 | $1.2(D + T) + 1.0E + 1.0L + 0.2S$ |
| U7 | $0.9(D + H_h) + 1.3W$ |
| U8 | $0.9(D + H_h) + 1.0E$ |

U7·U8 은 고정하중 계수를 0.9 로 낮춘 조합으로, 풍하중·지진하중에 의한 **부양이나
전도**를 검토할 때 지배한다.

## 사용법

```python
from concreteproperties_kds.loads import print_combinations, required_strength

loads = {"D": 25.0, "L": 18.0, "L_r": 3.0, "S": 5.0, "W": 12.0, "E": 20.0}

print_combinations(loads=loads)

u_max, governing = required_strength(loads=loads)
print(f"{governing.name} : wu = {u_max:.2f} kN/m")
# U6 : wu = 69.00 kN/m
```

출력 예:

```
   조합              U  식
----------------------------------------------------------------------------
   U6          69.00  U = 1.2(D + T) + 1.0E + 1.0L + 0.2S                  <= 지배
   U5          66.10  U = 1.2D + 1.3W + 1.0L + 0.5(L_r or S or R)
   U2          61.30  U = 1.2(D + F + T) + 1.6(L + H_v + H_h) + 0.5(...)
   U3          56.00  U = 1.2D + 1.6(L_r or S or R) + 1.0L
   U4          45.80  U = 1.2D + 1.6(L_r or S or R) + 0.65W
   U8          42.50  U = 0.9(D + H_h) + 1.0E
   U7          38.10  U = 0.9(D + H_h) + 1.3W
   U1          35.00  U = 1.4(D + F)
```

## 활하중 계수 저감

활하중이 5 kN/m² 이하이고 주차장·공중집회 장소가 아니면 U5·U6 의 활하중 계수를
1.0 에서 0.5 로 낮출 수 있다.

```python
u_max, governing = required_strength(loads=loads, reduce_live_load=True)
```

## 하중조합 수정

기준 개정이나 특수한 검토를 위해 조합을 바꾸려면 `LoadCombination` 을 직접
만들어 넘긴다.

```python
from concreteproperties_kds.loads import LoadCombination, required_strength

custom = (
    LoadCombination(name="C1", factors={"D": 1.4}, description="U = 1.4D"),
    LoadCombination(
        name="C2", factors={"D": 1.2, "L": 1.6}, description="U = 1.2D + 1.6L"
    ),
)

u_max, governing = required_strength(loads={"D": 25.0, "L": 18.0}, combinations=custom)
```

## API

| 함수/클래스 | 내용 |
|---|---|
| `LoadCombination(name, factors, description)` | 하중조합 하나. `evaluate(loads)` 로 조합 하중 계산 |
| `LOAD_COMBINATIONS` | KDS 14 20 10 4.2.2 의 조합 8개 |
| `required_strength(loads, combinations, reduce_live_load)` | `(최대 U, 지배 조합)` |
| `evaluate_all(loads, ...)` | 모든 조합의 결과를 큰 순서로 |
| `print_combinations(loads, ...)` | 결과를 표로 출력 |
| `LOAD_SYMBOLS` | 하중 기호와 이름 |
| `ROOF_LOADS` | 지붕 변동하중 기호 `("L_r", "S", "R")` |
