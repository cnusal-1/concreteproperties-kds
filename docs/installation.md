# 설치

## 요구 사항

| 항목 | 버전 |
|---|---|
| Python | 3.12 이상 (`concreteproperties` 0.8.0 기준) |
| concreteproperties | 0.7 이상 (0.7.0 · 0.8.0 에서 검증) |

`concreteproperties` 0.7.x 를 사용하는 경우 Python 3.11 에서도 동작한다.

## concreteproperties 설치

`concreteproperties` 는 단면 형상 처리에
[shapely](https://github.com/shapely/shapely) 를, 삼각형 요소망 생성에
[CyTriangle](https://github.com/m-clare/cytriangle) 을 사용한다. 콘크리트 단면
형상은 [sectionproperties](https://github.com/robbievanleeuwen/section-properties)
로 생성하며, 계산에는 [numpy](https://github.com/numpy/numpy) 와
[scipy](https://github.com/scipy/scipy) 를, 후처리에는
[matplotlib](https://github.com/matplotlib/matplotlib) 과
[rich](https://github.com/Textualize/rich) 를 사용한다.

```shell
pip install concreteproperties
```

## KDS 모듈 설치

이 저장소의 `concreteproperties-kds` 디렉터리에서 다음과 같이 설치한다.

```shell
cd concreteproperties-kds
pip install -e .
```

설치하지 않고 `PYTHONPATH` 로 바로 쓸 수도 있다.

```shell
export PYTHONPATH=/경로/concreteproperties-kds/src:$PYTHONPATH
python -c "from concreteproperties_kds import KDS; print(KDS)"
```

## 설치 확인

```python
from concreteproperties_kds import KDS, stress_block_parameters

print(stress_block_parameters(fck=27))
# (0.0033, 1.0, 0.8)

kds = KDS()
print(kds.create_concrete_material(compressive_strength=27).name)
# fck 27 MPa 콘크리트 (KDS 14 20)
```

## 시험 실행

```shell
cd concreteproperties-kds
PYTHONPATH=src python -m pytest tests/ -q
# 36 passed
```

## CAD 파일에서 형상 가져오기

`dxf` 나 `.3dm` 파일에서 단면 형상을 읽으려면 `sectionproperties` 의 선택적
의존 패키지를 설치한다.

```shell
pip install sectionproperties[dxf]
pip install sectionproperties[rhino]
```

## 한글 도시(plot) 설정

`matplotlib` 의 기본 글꼴에는 한글이 없어 그래프의 한글이 깨진다. 다음과 같이
한글 글꼴을 지정한다.

```python
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "NanumGothic"   # 또는 "Malgun Gothic", "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False
```
