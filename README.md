# concreteproperties — KDS 14 20 한글판

[`concreteproperties`](https://robbievanleeuwen.github.io/concrete-properties/index.html)
는 임의 형상의 철근콘크리트 단면 성능을 계산하는 파이썬 패키지이다. 총단면·균열단면·
극한단면 성능, 모멘트-곡률 해석, P-M 상관도와 2축 휨 상관도, 단면 응력 분포를 다룬다.

이 디렉터리는 원 패키지의 문서를 한글로 옮기고, 국가건설기준
**KDS 14 20 (콘크리트구조 설계기준)** 을 적용하는 설계기준 모듈을 추가한 것이다.
원 패키지가 제공하는 AS 3600(호주), NZS 3101(뉴질랜드) 자리에 KDS 14 20 이 들어간다.

## 구성

```
concreteproperties-kds/
├── src/concreteproperties_kds/
│   ├── __init__.py
│   └── kds.py                 # KDS 14 20 설계기준 클래스
├── docs/                      # 한글 문서
│   ├── index.md
│   ├── installation.md
│   ├── user_guide.md
│   ├── user_guide/
│   │   ├── materials.md
│   │   ├── geometry.md
│   │   ├── analysis.md
│   │   ├── results.md
│   │   ├── prestressed_analysis.md
│   │   ├── design_codes.md
│   │   ├── design_codes/kds.md   ← KDS 상세 (조문·계수·검증)
│   │   └── assumptions.md
│   ├── examples.md
│   └── api.md
├── examples/                  # 실행 가능한 예제 8건
└── tests/test_kds.py          # 검증 시험 36건
```

## 설치

```shell
pip install concreteproperties
cd concreteproperties-kds && pip install -e .
```

또는 설치 없이:

```shell
export PYTHONPATH=$PWD/concreteproperties-kds/src:$PYTHONPATH
```

## 사용 예

```python
from concreteproperties import ConcreteSection
from sectionproperties.pre.library import concrete_rectangular_section

from concreteproperties_kds import KDS

kds = KDS(column_type="tie")
conc = kds.create_concrete_material(compressive_strength=27)   # fck 27 MPa
steel = kds.create_steel_material(yield_strength=400)          # SD400

geom = concrete_rectangular_section(
    d=600, b=400,
    dia_top=16, area_top=198.6, n_top=2, c_top=50,
    dia_bot=22, area_bot=387.1, n_bot=4, c_bot=50,
    n_circle=16, conc_mat=conc, steel_mat=steel,
)

conc_sec = ConcreteSection(geom)
kds.assign_concrete_section(conc_sec)

f_res, u_res, phi = kds.ultimate_bending_capacity()
print(f"Mn = {u_res.m_x / 1e6:.1f} kN.m, phi = {phi:.3f}, phiMn = {f_res.m_x / 1e6:.1f} kN.m")
# Mn = 313.3 kN.m, phi = 0.850, phiMn = 266.3 kN.m
```

## KDS 모듈이 구현한 것

| 항목 | 조문 |
|---|---|
| 콘크리트 탄성계수 $E_c = 8500\sqrt[3]{f_{cm}}$ | KDS 14 20 10 4.3.3 |
| 등가직사각형 응력블록 $\eta(0.85f_{ck})$, $a = \beta_1 c$ | KDS 14 20 20 4.1.1, 표 4.1-1 |
| 파괴계수 $f_r = 0.63\lambda\sqrt{f_{ck}}$ | KDS 14 20 30 4.2.1 |
| 강도감소계수 (압축지배 0.65/0.70, 인장지배 0.85, 변화구간 선형보간) | KDS 14 20 10 표 4.2-1 |
| 압축지배·인장지배 변형률한계 | KDS 14 20 20 4.1.2 |
| 최대 설계 축강도 $\alpha\phi P_o$ ($\alpha$ = 0.80/0.85) | KDS 14 20 20 4.1.2 |
| 휨부재 최소허용변형률 | KDS 14 20 20 4.1.2 |
| 최소 휨철근량 | KDS 14 20 20 4.2.2 |

전단·비틀림, 처짐·균열폭 상세, 내구성, 철근상세, 정착·이음, PSC 강도감소계수,
세장 기둥의 2차 효과, 하중조합은 **다루지 않는다**.

## 검증

단철근 직사각형 보 ($b=300$, $d=540$, $f_{ck}=24$, SD400, 4-D22) 의 손계산 대조:

| 항목 | 손계산 | 모듈 |
|---|---:|---:|
| 중립축 깊이 $c$ (mm) | 126.50 | 126.504 |
| 순인장변형률 $\varepsilon_t$ | 0.010786 | 0.010787 |
| 강도감소계수 $\phi$ | 0.850 | 0.850 |
| 공칭 휨강도 $M_n$ (kN·m) | 303.115 | 303.115 |
| 설계 휨강도 $\phi M_n$ (kN·m) | 257.648 | 257.647 |

```shell
PYTHONPATH=src python -m pytest tests/ -q
# 36 passed
```

## 예제 실행

```shell
cd examples
PYTHONPATH=../src:. python 04_휨강도.py
PYTHONPATH=../src:. python 05_PM상관도.py --plot
```

## 주의

> KDS 14 20 은 개정된다. 이 모듈이 사용한 계수와 조문 번호는
> [docs/user_guide/design_codes/kds.md](docs/user_guide/design_codes/kds.md#기준-값-출처와-검증)
> 의 표에 모두 정리해 두었으니, 실무 적용 전에 **현행 KDS 14 20 원문과 대조**하기
> 바란다. 이 모듈은 기준 원문 데이터베이스에 직접 접근하지 않고 작성되었다.

원 패키지 `concreteproperties` 는 MIT 라이선스로 배포된다.
