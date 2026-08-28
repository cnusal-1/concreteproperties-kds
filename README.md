# concreteproperties — KDS 14 20 한글판

[`concreteproperties`](https://robbievanleeuwen.github.io/concrete-properties/index.html)
는 임의 형상의 철근콘크리트 단면 성능을 계산하는 파이썬 패키지이다. 총단면·균열단면·
극한단면 성능, 모멘트-곡률 해석, P-M 상관도와 2축 휨 상관도, 단면 응력 분포를 다룬다.

이 저장소는 원 패키지의 문서를 한글로 옮기고, 국가건설기준
**KDS 14 20 (콘크리트구조 설계기준)** 을 적용하는 설계기준 모듈을 추가한 것이다.
단면 해석에서 그치지 않고 **하중조합부터 전단·사용성·내구성·철근상세까지**
KDS 의 주요 검토를 함께 제공한다.

문서 사이트: <https://cnusal-1.github.io/concreteproperties-kds/>

## 구성

```
concreteproperties-kds/
├── src/concreteproperties_kds/
│   ├── kds.py             휨 및 압축      KDS 14 20 10, 14 20 20
│   ├── loads.py           하중조합        KDS 14 20 01
│   ├── shear.py           전단·비틀림     KDS 14 20 22
│   ├── serviceability.py  사용성          KDS 14 20 30
│   ├── durability.py      내구성          KDS 14 20 40
│   ├── detailing.py       철근상세·정착   KDS 14 20 50, 52
│   ├── slender.py         세장 기둥       KDS 14 20 20 4.4
│   ├── psc.py             프리스트레스트  KDS 14 20 60
│   └── biaxial.py         2축 휨 간략식   (문헌)
├── docs/                  한글 문서 21편
├── examples/              실행 가능한 예제 17건
└── tests/                 검증 시험 184건
```

## 설치

```shell
pip install concreteproperties
pip install -e .
```

또는 설치 없이:

```shell
export PYTHONPATH=$PWD/src:$PYTHONPATH
```

## 사용 예 — 단면 해석

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

## 사용 예 — 설계 검토

```python
from concreteproperties_kds import (
    check_deflection, check_durability, check_shear, check_slenderness,
    required_strength, summarise_detailing,
)

# 하중조합                                             KDS 14 20 01
w_u, governing = required_strength(loads={"D": 22.0, "L": 14.0, "S": 3.0})

# 전단                                                 KDS 14 20 22
check_shear(v_u=201e3, fck=27, b_w=400, d=635, a_v=253.4, s=250, fyt=400).print_results()

# 내구성                                               KDS 14 20 40
check_durability(exposure_class="EC3", fck=27, cover=40).print_results()

# 정착·이음                                            KDS 14 20 52
summarise_detailing(bar="D25", fy=400, fck=27).print_results()
```

전체 흐름은 [`examples/17_종합설계.py`](examples/17_종합설계.py) 를 참고한다.

## 구현 범위

| 모듈 | 구현한 규정 | 조문 |
|---|---|---|
| `kds` | $E_c = 8500\sqrt[3]{f_{cm}}$ | KDS 14 20 10 4.3.3 |
| | 등가직사각형 응력블록 $\eta(0.85f_{ck})$, $a = \beta_1 c$ | KDS 14 20 20 4.1.1, 표 4.1-1 |
| | 강도감소계수 (압축지배 0.65/0.70, 인장지배 0.85, 변화구간 보간) | KDS 14 20 10 4.3.3(2) |
| | 압축지배·인장지배 변형률한계 | KDS 14 20 20 4.1.2 |
| | 최대 설계 축강도 $\alpha\phi P_o$ | KDS 14 20 20 4.1.2 |
| | 휨부재 최소허용변형률, 최소 휨철근량 | KDS 14 20 20 4.1.2, 4.2.2 |
| `loads` | 하중조합 U1~U8, 활하중 저감 | KDS 14 20 10 4.2.2 |
| `shear` | $V_c$ (간편식·상세식·축력 효과), $V_s$ 와 상한 | KDS 14 20 22 4.2, 4.3 |
| | 최소 전단철근량, 스터럽 최대 간격 | KDS 14 20 22 4.3.2, 4.3.3 |
| | $T_{cr}$, $T_n$, 종방향 철근, 단면 크기 규정 | KDS 14 20 22 4.4 |
| `serviceability` | 유효단면2차모멘트 (Branson), 장기처짐 | KDS 14 20 30 4.2.1 |
| | 최소 두께, 허용처짐과 **조건별 비교 대상** | KDS 14 20 30 표 4.2-1, 4.2-2 |
| | 균열 제어 철근 간격, 수축·온도철근 | KDS 14 20 20 4.2.3, 4.4 |
| `durability` | 노출등급 16종의 최소 강도·물결합재비·피복 | KDS 14 20 40 |
| `detailing` | 최소 피복두께, 철근 최소 순간격 | KDS 14 20 50 4.2, 4.3 |
| | 인장·압축 정착길이 (약산식·정밀식), 표준갈고리 | KDS 14 20 52 4.1~4.3 |
| | 인장 A/B급·압축 겹침이음 | KDS 14 20 52 4.5 |
| `slender` | 세장비 한계, $EI$, $P_c$, $\delta_{ns}$, $M_{2,min}$ | KDS 14 20 20 4.4 |
| `psc` | 긴장재·콘크리트 허용응력, 균열등급 | KDS 14 20 60 4.2 |
| | 프리스트레스 손실 6종 | KDS 14 20 60 4.3 |
| | 부착·비부착 $f_{ps}$, PSC 강도감소계수 | KDS 14 20 60 4.1 |
| `biaxial` | Bresler 등하중선법·역하중법, 엄밀해 비교 | (문헌) |

**다루지 않는 것** — 2방향 슬래브(KDS 14 20 70), 스트럿-타이(14 20 24),
뚫림전단, 내진상세(14 20 80), 벽체·기초·옹벽 부재별 규정, 비횡구속 골조의
$\delta_s$, 2차 해석(P-Δ), PSC 정착부 설계, 시간 종속 해석.

## 검증

단철근 직사각형 보 ($b=300$, $d=540$, $f_{ck}=24$, SD400, 4-D22) 의 손계산 대조:

| 항목 | 손계산 | 모듈 |
|---|---:|---:|
| 중립축 깊이 $c$ (mm) | 126.50 | 126.504 |
| 순인장변형률 $\varepsilon_t$ | 0.010786 | 0.010787 |
| 강도감소계수 $\phi$ | 0.850 | 0.850 |
| 공칭 휨강도 $M_n$ (kN·m) | 303.115 | 303.115 |
| 설계 휨강도 $\phi M_n$ (kN·m) | 257.648 | 257.647 |

전단·정착·처짐 등도 각 조문의 식을 손계산으로 대조하는 시험을 갖추고 있다.

```shell
PYTHONPATH=src python -m pytest tests/ -q
# 184 passed
```

| 시험 파일 | 건수 | 대상 |
|---|---:|---|
| `test_kds.py` | 36 | 재료, 휨강도, P-M 상관도, 2축 휨 |
| `test_loads.py` | 10 | 하중조합 |
| `test_shear.py` | 25 | 전단·비틀림 |
| `test_serviceability.py` | 30 | 처짐·균열 |
| `test_durability.py` | 10 | 내구성 |
| `test_detailing.py` | 27 | 정착·이음·피복 |
| `test_slender.py` | 21 | 세장 기둥 |
| `test_biaxial.py` | 9 | 2축 휨 간략식 |
| `test_psc.py` | 16 | 프리스트레스트 |

## 예제 실행

```shell
cd examples
PYTHONPATH=../src:. python 04_휨강도.py
PYTHONPATH=../src:. python 17_종합설계.py
PYTHONPATH=../src:. python 05_PM상관도.py --plot
```

| 예제 | 내용 |
|---|---|
| 01~08 | 재료, 단면 제원, 균열단면, 휨강도, P-M 상관도, 2축 휨, 모멘트-곡률, 응력 |
| 09~16 | 하중조합, 전단·비틀림, 처짐·균열, 내구성, 정착·이음, 세장 기둥, 2축 휨 간략식, PSC |
| 17 | **보 하나를 하중조합부터 상세까지 전부 검토** |

## 문서

원 문서 사이트와 같은 형태의 정적 사이트로 빌드된다. `main` 에 반영되면
`.github/workflows/docs.yml` 이 빌드해 GitHub Pages 로 배포한다.

직접 빌드하려면:

```shell
pip install -e ".[docs]"
sphinx-build -b html docs docs/_build/html
# docs/_build/html/index.html 을 브라우저로 연다
```

노트북 예제는 실행 결과까지 저장해 두고 `conf.py` 의
`nb_execution_mode = "off"` 로 그대로 쓰므로, 문서 빌드에는 노트북 실행이
필요 없다. 노트북을 고칠 때는 `.ipynb` 를 직접 고치지 말고
`scripts/build_notebooks.py` 를 고친 뒤 다시 생성한다.

```shell
python scripts/build_notebooks.py --run
```

내용만 읽으려면 [`docs/index.md`](docs/index.md) 에서 시작한다.

| 문서 | 내용 |
|---|---|
| [설치](docs/installation.md) | 설치와 한글 도시 설정 |
| [사용자 가이드](docs/user_guide.md) | 작업 흐름과 기능 목록 |
| [재료](docs/user_guide/materials.md) · [형상](docs/user_guide/geometry.md) · [해석](docs/user_guide/analysis.md) · [결과](docs/user_guide/results.md) | 단면 해석 |
| [설계기준](docs/user_guide/design_codes.md) | 모듈 구성 |
| [KDS 휨 및 압축](docs/user_guide/design_codes/kds.md) | 조문별 계수와 **검증 대조표** |
| [하중조합](docs/user_guide/design_codes/kds_loads.md) · [전단·비틀림](docs/user_guide/design_codes/kds_shear.md) · [사용성](docs/user_guide/design_codes/kds_serviceability.md) · [내구성](docs/user_guide/design_codes/kds_durability.md) | 검토별 상세 |
| [철근상세·정착](docs/user_guide/design_codes/kds_detailing.md) · [세장 기둥](docs/user_guide/design_codes/kds_slender.md) · [프리스트레스트](docs/user_guide/design_codes/kds_psc.md) · [2축 휨 간략식](docs/user_guide/design_codes/kds_biaxial.md) | |
| [예제](docs/examples.md) · [API](docs/api.md) · [가정](docs/user_guide/assumptions.md) | |

## 주의

> KDS 14 20 은 개정된다. 이 저장소가 사용한 계수와 조문 번호는
> [docs/user_guide/design_codes/kds.md](docs/user_guide/design_codes/kds.md#기준-값-출처와-검증)
> 의 **검증 대조표**(항목 70여 개)에 모두 정리해 두었으니, 실무 적용 전에
> **현행 KDS 14 20 원문과 대조**하기 바란다. 이 저장소는 기준 원문 데이터베이스에
> 직접 접근하지 않고 작성되었다.
>
> 특히 확인이 필요한 곳:
> - KDS 14 20 20 표 4.1-2 의 $\eta$, $\beta_1$, $\varepsilon_{cu}$ (fck 50~90)
> - KDS 14 20 01 의 하중계수 (특히 풍하중 계수 1.3)
> - KDS 14 20 22 의 전단 규정 (2021년 개정 내용)
> - KDS 14 20 40 의 노출등급별 요구값

원 패키지 `concreteproperties` 는 MIT 라이선스로 배포된다.
