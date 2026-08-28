# 형상

`concreteproperties` 는 [sectionproperties](https://sectionproperties.readthedocs.io)
의 전처리기를 사용해 철근콘크리트 단면을 `CompoundGeometry` 객체로 만든다. 이
객체는 콘크리트와 철근 정보를 모두 담고 있어야 한다.

## 축 규약

단면은 `x-y` 평면에 정의한다. `concreteproperties` 의 중요한 특징은 해석이 `x` 축
또는 `y` 축 휨에 한정되지 않는다는 점이다. 모든 해석은 각 $\theta$ (radian) 로
정의되는 회전된 `u-v` 축에 대해 수행할 수 있다.

| 기호 | 의미 |
|---|---|
| `m_x`, `m_y` | `x`, `y` 축에 대한 휨모멘트 |
| `m_xy` | 합모멘트, $\sqrt{m_x^2 + m_y^2}$ |
| `ixx_g`, `iyy_g` | 전체좌표계(원점 기준) 단면2차모멘트 |
| `ixx_c`, `iyy_c` | 도심축(탄성 도심 `cx`, `cy` 기준) 단면2차모멘트 |
| `i11`, `i22` | 주축 단면2차모멘트 |
| `iuu` | 각 $\theta$ 로 회전한 국부 `u` 축 단면2차모멘트 |

$\theta$ 는 중립축이 수평축과 이루는 각이며, 반시계 방향이 양(+)이다.

## 기본 형상

```python
from sectionproperties.pre.library import rectangular_section

geom = rectangular_section(d=600, b=300, material=conc)
geom.plot_geometry(labels=[], cp=False, legend=False)
```

원형 단면은 요소망 생성을 위해 유한한 수의 변으로 이산화해야 한다. 이때 지름을
그대로 쓰면 면적이 실제보다 작아지므로, 면적이 정확히 맞도록 지름을 보정하는
`circular_section_by_area` 를 쓰는 편이 낫다.

```python
import math
from sectionproperties.pre.library import circular_section, circular_section_by_area

geom = circular_section(d=600, n=32, material=conc)
print(f"{geom.calculate_area():.2f}")          # 280930.06 — 실제보다 작다
print(f"{math.pi * 600**2 / 4:.2f}")           # 282743.34

geom = circular_section_by_area(area=math.pi * 600**2 / 4, n=32, material=conc)
print(f"{geom.calculate_area():.2f}")          # 282743.34
```

## 표준 콘크리트 단면 라이브러리

`sectionproperties` 는 철근이 배치된 콘크리트 단면을 한 번에 만들어 주는 함수를
제공한다. 예제에서 사용하는 직사각형 단면은 다음과 같다.

```python
from sectionproperties.pre.library import concrete_rectangular_section

geom = concrete_rectangular_section(
    d=600,            # 단면 높이
    b=400,            # 단면 폭
    dia_top=16,       # 상부 철근 지름
    area_top=198.6,   # 상부 철근 1본의 면적 (D16)
    n_top=2,          # 상부 철근 본수
    c_top=50,         # 상부 피복 (철근 중심까지)
    dia_bot=22,
    area_bot=387.1,   # D22
    n_bot=4,
    c_bot=50,
    n_circle=16,      # 철근 원의 이산화 점 수
    conc_mat=conc,
    steel_mat=steel,
)
```

이 밖에 `concrete_circular_section`, `concrete_tee_section`,
`concrete_column_section` 등이 있고, 교량용 거더 단면 라이브러리도 제공된다.

## 철근 추가

임의 형상에 철근을 추가할 때는 `concreteproperties.pre` 의 함수를 쓴다.

```python
from concreteproperties import add_bar, add_bar_rectangular_array, add_bar_circular_array

# 철근 1본
geom = add_bar(geometry=geom, area=387.1, material=steel, x=60, y=60, n=16)

# 직사각형 배열
geom = add_bar_rectangular_array(
    geometry=geom, area=387.1, material=steel,
    n_x=4, x_s=80, n_y=2, y_s=480, anchor=(60, 60), n=16,
)

# 원형 배열
geom = add_bar_circular_array(
    geometry=geom, area=387.1, material=steel, n_bar=8, r_array=200, n=16,
)
```

> **주의** — 이 함수들은 `(geometry - bar) + bar` 로 구현되어 있다. 즉 **철근이
> 차지하는 면적만큼 콘크리트를 도려낸 뒤** 철근을 넣는다. 따라서 콘크리트 형상의
> 면적은 이미 $A_g - A_{st}$ 이며, 순수압축 하중을 계산할 때 철근 면적을 다시
> 공제해서는 안 된다.

## 그 밖의 형상 생성 방법

- 점과 요소(facet)로 직접 정의
- `dxf`, `.3dm` 파일에서 가져오기 (`sectionproperties[dxf]`, `[rhino]` 필요)
- 여러 형상의 합집합·차집합 연산

자세한 내용은 `sectionproperties` 문서를 참고한다.

## 합성 단면

형강 등 다른 재료를 콘크리트와 조합해 합성 단면을 만들 수 있다. 이때 강재는
`Steel`(요소망 생성) 재료를 사용한다.

> **주의** — KDS 설계기준 모듈은 격점 처리되는 `SteelBar` 만 지원한다. 요소망이
> 생성되는 `Steel` 재료가 단면에 포함되어 있으면 `assign_concrete_section()` 에서
> `ValueError` 가 발생한다. 합성구조는 KDS 14 31(강구조) 또는 KDS 14 20 의 별도
> 조문에 따라야 하므로, 이 모듈의 강도감소계수 규정을 그대로 적용할 수 없다.

## 단면 확인

```python
conc_sec = ConcreteSection(geom)
conc_sec.plot_section()
```
