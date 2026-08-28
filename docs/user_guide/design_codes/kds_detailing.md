# 철근상세·정착·이음 (KDS 14 20 50, KDS 14 20 52)

`concreteproperties_kds.detailing` 은 최소 피복두께, 철근 간격 제한, 정착길이,
겹침이음 길이를 다룬다.

## 철근 규격 (KS D 3504)

| 호칭 | $d_b$ (mm) | $A_b$ (mm²) | | 호칭 | $d_b$ (mm) | $A_b$ (mm²) |
|---|---:|---:|---|---|---:|---:|
| D10 | 9.53 | 71.33 | | D29 | 28.6 | 642.4 |
| D13 | 12.7 | 126.7 | | D32 | 31.8 | 794.2 |
| D16 | 15.9 | 198.6 | | D35 | 34.9 | 956.6 |
| D19 | 19.1 | 286.5 | | D38 | 38.1 | 1140 |
| D22 | 22.2 | 387.1 | | D41 | 41.3 | 1340 |
| D25 | 25.4 | 506.7 | | D51 | 50.8 | 2027 |

```python
from concreteproperties_kds.detailing import bar_area, bar_diameter

bar_diameter("D22")   # 22.2
bar_area("D22")       # 387.1
```

## 최소 피복두께 (KDS 14 20 50 4.3.1)

프리스트레스하지 않는 부재의 현장치기콘크리트 기준이다.

| 조건 | 철근 | 피복 (mm) | 키 |
|---|---|---:|---|
| 수중에서 치는 콘크리트 | 전체 | 100 | `"수중"` |
| 흙에 접하여 친 후 영구히 흙에 묻힘 | 전체 | 75 | `"흙에영구히묻힘"` |
| 흙에 접하거나 옥외 공기에 직접 노출 | D19 이상 | 50 | `"흙에접하거나옥외노출"` |
| | D16 이하·지름 16 mm 이하 철선 | 40 | |
| 옥내 — 슬래브·벽체·장선 | D35 초과 | 40 | `"옥내_슬래브벽체장선"` |
| | D35 이하 | 20 | |
| 옥내 — 보·기둥 | 전체 | 40 | `"옥내_보기둥"` |
| 옥내 — 쉘·절판 | 전체 | 20 | `"옥내_셸절판"` |

$f_{ck} \ge 40$ MPa 인 경우 **옥내 보·기둥에 한하여** 10 mm 를 저감할 수 있다.

```python
from concreteproperties_kds.detailing import minimum_cover

minimum_cover(condition="수중")                                   # 100.0
minimum_cover(condition="옥내_보기둥")                            # 40.0
minimum_cover(condition="옥내_보기둥", fck=40)                    # 30.0  (저감)
minimum_cover(condition="흙에접하거나옥외노출", bar="D22", fck=40) # 50.0  (저감 없음)
```

내구성 요구(KDS 14 20 40 4.1.4(2))는 노출범주 EC·ES 에 대해 이 표의 값 이상을
요구한다.

내구성 요구 피복두께(KDS 14 20 40)와 비교하여 **큰 값**을 쓴다.

## 철근 최소 순간격 (KDS 14 20 50 4.2)

- 보 : $\max(d_b,\ 25\text{ mm},\ \frac{4}{3} \times \text{굵은골재 최대치수})$
- 기둥 : $\max(1.5 d_b,\ 40\text{ mm},\ \frac{4}{3} \times \text{굵은골재 최대치수})$

```python
from concreteproperties_kds.detailing import minimum_bar_spacing

minimum_bar_spacing(bar="D22", member="보", aggregate_size=25)   # 33.3
minimum_bar_spacing(bar="D32", member="기둥")                    # 47.7
```

## 인장 이형철근의 정착길이 (KDS 14 20 52 4.1.2)

**기본정착길이에 보정계수를 곱하는 방법** (식 4.1-1, 표 4.1-1)

$$l_{db} = \frac{0.6 d_b f_y}{\lambda\sqrt{f_{ck}}}$$

에 표 4.1-1 의 계수를 곱한다.

| 조건 | D19 이하·이형철선 | D22 이상 |
|---|---:|---:|
| 순간격 $\ge d_b$, 피복 $\ge d_b$, 최소 스터럽·띠철근 배치;<br>또는 순간격 $\ge 2d_b$, 피복 $\ge d_b$ | $0.8\alpha\beta$ | $\alpha\beta$ |
| 기타 | $1.2\alpha\beta$ | $1.5\alpha\beta$ |

$\alpha$ 는 철근배치 위치계수(상부철근 1.3, 기타 1.0), $\beta$ 는 도막계수
(피복 $< 3d_b$ 또는 순간격 $< 6d_b$ 인 에폭시 도막 1.5, 기타 에폭시 도막 1.2,
도막하지 않은 철근 1.0)이다. **에폭시 도막철근이 상부철근인 경우**
$\alpha\beta \le 1.7$ 이다. 정착길이는 항상 300 mm 이상이어야 한다.

**정밀식** (식 4.1-2)

$$l_d = \frac{0.90 d_b f_y}{\lambda\sqrt{f_{ck}}}
\cdot\frac{\alpha\beta\gamma}{\left(\dfrac{c + K_{tr}}{d_b}\right)}
\ \ge 300\ \text{mm}, \qquad \frac{c + K_{tr}}{d_b} \le 2.5$$

$\gamma$ 는 철근 크기계수(D19 이하 0.8, D22 이상 1.0)이며, $c$ 는 철근 중심부터
콘크리트 표면까지 최단거리와 철근 중심간 거리의 1/2 중 작은 값이다.
설계를 간편하게 하려면 $K_{tr} = 0$ 으로 둘 수 있다.

```python
from concreteproperties_kds.detailing import (
    development_length_tension,
    development_length_tension_detailed,
)

development_length_tension(bar="D22", fy=400, fck=27)                 # 1025.4 mm
development_length_tension(bar="D16", fy=400, fck=27)                 #  587.5 mm
development_length_tension(bar="D22", fy=400, fck=27, top_bar=True)   # 1333.0 mm
development_length_tension_detailed(bar="D22", fy=400, fck=27, c=40, k_tr=15)
#  620.8 mm
```

배치 철근량이 소요 철근량보다 많으면 `excess_reinforcement` 로 저감할 수 있다
(KDS 14 20 52 4.1.2(4)). 저감 후에도 300 mm 이상이어야 한다.

## 압축 이형철근의 정착길이 (KDS 14 20 52 4.2)

$$l_{dc} = \max\left(\frac{0.25 d_b f_y}{\lambda\sqrt{f_{ck}}},\ 0.043 d_b f_y\right)
\ \ge 200\ \text{mm}$$

나선철근이나 D13 이상 띠철근이 100 mm 이하 간격으로 배치되면 0.75 를 곱한다
(`confined=True`).

## 표준갈고리 정착길이 (KDS 14 20 52 4.3)

$$l_{dh} = \frac{0.24\beta d_b f_y}{\lambda\sqrt{f_{ck}}}
\ \ge \max(8 d_b,\ 150\ \text{mm})$$

| 보정계수 | 조건 |
|---|---|
| 0.7 | 측면 피복 $\ge 70$ mm, 갈고리 끝 피복 $\ge 50$ mm |
| 0.8 | 갈고리를 $3d_b$ 이하 간격의 띠철근·스터럽으로 구속 |

## 겹침이음 (KDS 14 20 52 4.5)

**인장**

| 등급 | 길이 | 조건 |
|---|---|---|
| A급 | $1.0 l_d$ | 배치 철근량이 소요의 2배 이상 **그리고** 겹침이음 철근량이 전체의 1/2 이하 |
| B급 | $1.3 l_d$ | 그 밖의 경우 |

어느 경우든 300 mm 이상이다.

**압축**

$$l_s = \begin{cases}
0.072 f_y d_b & f_y \le 400\ \text{MPa} \\
(0.13 f_y - 24) d_b & f_y > 400\ \text{MPa}
\end{cases}
\ \ge \max(l_{dc},\ 300\ \text{mm})$$

$f_{ck} < 21$ MPa 이면 1/3 증가시킨다.

## 한 번에 계산하기

```python
from concreteproperties_kds.detailing import summarise_detailing

summarise_detailing(bar="D22", fy=400, fck=27).print_results()
```

```
공칭 지름              db   =     22.20 mm
인장 정착길이          ld   =    1025.4 mm
압축 정착길이          ldc  =     427.2 mm
표준갈고리 정착길이    ldh  =     410.1 mm
인장 겹침이음 (A급)         =    1025.4 mm
인장 겹침이음 (B급)         =    1333.0 mm
압축 겹침이음               =     639.4 mm
```

## API

| 함수 | 내용 |
|---|---|
| `bar_diameter(bar)`, `bar_area(bar)` | 공칭 지름·단면적 |
| `minimum_cover(condition, bar, fck)` | 최소 피복두께 |
| `minimum_bar_spacing(bar, aggregate_size, member)` | 최소 순간격 |
| `development_length_tension(...)` | 인장 정착길이 (약산식) |
| `development_length_tension_detailed(...)` | 인장 정착길이 (정밀식) |
| `development_length_compression(...)` | 압축 정착길이 |
| `development_length_hook(...)` | 표준갈고리 정착길이 |
| `lap_splice_tension(l_d, splice_class)` | 인장 겹침이음 |
| `lap_splice_compression(bar, fy, fck, l_dc)` | 압축 겹침이음 |
| `summarise_detailing(...)` | 위 값을 한 번에 → `DetailingSummary` |
| `BAR_PROPERTIES`, `MINIMUM_COVER`, `LDB_FACTOR`, `DEVELOPMENT_TABLE_FACTOR` | 편집 가능한 표·상수 |
