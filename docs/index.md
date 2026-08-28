```{toctree}
:hidden:
:maxdepth: 2

installation
user_guide
examples
lectures
api
```

```{toctree}
:caption: 개발
:hidden:

contributing
행동 강령 <codeofconduct>
라이선스 <license>
```

# concreteproperties (KDS 한글판) 문서

`concreteproperties` 는 임의 형상의 철근콘크리트 단면의 단면 성능을 계산하는
파이썬 패키지이다. 총단면·균열단면·극한단면의 성능을 계산할 수 있고,
모멘트-곡률 해석을 수행하며, P-M 상관도와 2축 휨 상관도를 생성한다.
여기에 더해 단면 내부의 응력 분포도 도시할 수 있다.

이 문서는 원 문서
([robbievanleeuwen.github.io/concrete-properties](https://robbievanleeuwen.github.io/concrete-properties/index.html))
를 한글로 옮기고, **국가건설기준 KDS 14 20 (콘크리트구조 설계기준)** 을 적용할 수
있도록 설계기준 모듈 `concreteproperties_kds` 를 추가한 것이다. 원 패키지가
제공하는 AS 3600(호주), NZS 3101(뉴질랜드) 자리에 KDS 14 20 을 넣었다고 보면 된다.

## 목차

| 문서 | 내용 |
|---|---|
| [설치](installation.md) | 설치 방법과 의존 패키지 |
| [사용자 가이드](user_guide.md) | 전체 작업 흐름과 기능 목록 |
| [재료](user_guide/materials.md) | 재료와 응력-변형률 관계 |
| [형상](user_guide/geometry.md) | 단면 형상 정의와 축 규약 |
| [해석](user_guide/analysis.md) | 해석 수행 방법 |
| [결과](user_guide/results.md) | 결과 객체와 후처리 |
| [프리스트레스트 해석](user_guide/prestressed_analysis.md) | PSC 단면 해석 |
| [설계기준](user_guide/design_codes.md) | 설계기준 모듈 개요 |
| [KDS 14 20 — 휨 및 압축](user_guide/design_codes/kds.md) | **KDS 14 20 20 / 14 20 10 — 단면 해석의 중심** |
| [KDS — 하중조합](user_guide/design_codes/kds_loads.md) | KDS 14 20 10 4.2.2 |
| [KDS — 전단 및 비틀림](user_guide/design_codes/kds_shear.md) | KDS 14 20 22 |
| [KDS — 사용성](user_guide/design_codes/kds_serviceability.md) | KDS 14 20 30 |
| [KDS — 내구성](user_guide/design_codes/kds_durability.md) | KDS 14 20 40 |
| [KDS — 철근상세·정착·이음](user_guide/design_codes/kds_detailing.md) | KDS 14 20 50, 52 |
| [KDS — 세장 기둥](user_guide/design_codes/kds_slender.md) | KDS 14 20 20 4.4 |
| [KDS — 프리스트레스트](user_guide/design_codes/kds_psc.md) | KDS 14 20 60 |
| [KDS — 2축 휨 간략식](user_guide/design_codes/kds_biaxial.md) | Bresler 등 |
| [설계식 목록](user_guide/design_codes/equations.md) | **구현한 설계식 전체와 KDS 조문·식 번호의 대응표** |
| [가정](user_guide/assumptions.md) | 해석에 사용된 가정과 부호 규약 |
| [예제](examples.md) | 실행 가능한 예제 17건 |
| [강의 자료](lectures.md) | 강의용 노트북 — 왜 그런지를 그림으로 |
| [API](api.md) | KDS 모듈 API 참조 |

## KDS 14 20 계열이란

KDS(Korean Design Standard, 국가건설기준 설계기준)의 코드 번호는 세 단계로 읽는다.

```
KDS  14   20   20
     │    │    └── 주제 (휨 및 압축)
     │    └─────── 공종 (콘크리트구조)
     └──────────── 분야 (구조설계)
```

앞의 `14 20` 이 콘크리트구조를 가리키고, 뒤 두 자리가 주제를 나눈다. 하나의
부재를 설계하려면 여러 코드를 함께 봐야 한다 — 예를 들어 보 하나에도 하중조합
(14 20 10), 휨(14 20 20), 전단(14 20 22), 처짐(14 20 30), 정착(14 20 52)이
모두 걸린다.

이 저장소가 다루는 코드는 다음과 같다.

| 코드 | 이름 | 무엇을 정하는가 | 판 |
|---|---|---|---|
| **14 20 01** | 일반사항 | 용어 정의, 강도설계법의 기본 원칙. 실제 계산식은 거의 없고 나머지 코드의 전제를 깔아 준다 | 2022 |
| **14 20 10** | 해석과 설계 원칙 | 재료 상수($E_c$, $E_s$, 경량콘크리트계수 $\lambda$), **하중계수와 하중조합**, 강도감소계수 $\phi$ 의 값. 모든 계산의 출발점 | 2021 |
| **14 20 20** | 휨 및 압축 | 등가직사각형 응력블록($\eta$, $\beta_1$, $\varepsilon_{cu}$), 변형률한계와 단면 분류, 최대 축강도, 최소 휨철근량, 세장 기둥의 모멘트확대법 | 2022 |
| **14 20 22** | 전단 및 비틀림 | 콘크리트가 부담하는 전단강도 $V_c$, 전단철근 $V_s$ 와 최소량·최대 간격, 비틀림 $T_n$ | 2022 |
| **14 20 30** | 사용성 | 처짐 — 유효단면2차모멘트, 장기처짐계수, 최소 두께, 허용처짐. 균열 제어 철근 간격, 수축·온도철근 | 2021 |
| **14 20 40** | 내구성 | 노출등급(EC·ES·EF·EA) 별 최소 설계기준압축강도와 피복두께 | 2022 |
| **14 20 50** | 철근상세 | 최소 피복두께, 철근 최소 순간격, 배근 일반 규정 | 2022 |
| **14 20 52** | 정착 및 이음 | 인장·압축 정착길이, 표준갈고리, 겹침이음 길이 | 2024 |
| **14 20 60** | 프리스트레스트 | 긴장재 허용응력, 프리스트레스 손실, 부착·비부착 긴장재의 $f_{ps}$ | 2022 |

같은 14 20 계열인데도 **판이 섞여 있다.** 14 20 10 과 14 20 30 은 2021 판
(2021-02-18 개정), 나머지는 2022 판, 14 20 52 만 2024 판(2024-12-30 개정)이다.
각 조문과 구현 함수의 대응은 [설계식 목록](user_guide/design_codes/equations.md)
에 전부 정리해 두었다.

### 이 저장소가 다루지 않는 코드

| 코드 | 이름 | 판 |
|---|---|---|
| 14 20 24 | 스트럿-타이 모델 | 2021 |
| 14 20 26 | 피로 | 2022 |
| 14 20 70 | 슬래브와 기초판 (2방향 슬래브, 뚫림전단) | 2021 |
| 14 20 72 | 벽체 | 2021 |
| 14 20 80 | 내진설계 | 2021 |

## 설치

```shell
pip install concreteproperties
```

KDS 모듈은 이 저장소를 내려받아 `pip install -e .` 로 설치하거나, `src` 를
`PYTHONPATH` 에 추가해 쓴다. 자세한 내용은 [설치](installation.md) 를 참고한다.

## 빠른 시작

```python
from concreteproperties import ConcreteSection
from sectionproperties.pre.library import concrete_rectangular_section

from concreteproperties_kds import KDS

# 1) 설계기준 객체 생성 (띠철근 기둥/보)
kds = KDS(column_type="tie")

# 2) KDS 14 20 재료 생성
conc = kds.create_concrete_material(compressive_strength=27)   # fck = 27 MPa
steel = kds.create_steel_material(yield_strength=400)          # SD400

# 3) 단면 형상 정의
geom = concrete_rectangular_section(
    d=600, b=400,
    dia_top=16, area_top=198.6, n_top=2, c_top=50,
    dia_bot=22, area_bot=387.1, n_bot=4, c_bot=50,
    n_circle=16, conc_mat=conc, steel_mat=steel,
)

# 4) 단면 객체 생성 후 설계기준에 할당
conc_sec = ConcreteSection(geom)
kds.assign_concrete_section(conc_sec)

# 5) 설계 휨강도 산정
f_res, u_res, phi = kds.ultimate_bending_capacity()
print(f"Mn = {u_res.m_x / 1e6:.1f} kN.m, phi = {phi:.3f}, "
      f"phiMn = {f_res.m_x / 1e6:.1f} kN.m")
# Mn = 313.3 kN.m, phi = 0.850, phiMn = 266.3 kN.m
```

## 주요 기능

`concreteproperties` 의 기능 전체는 [사용자 가이드](user_guide.md#기능) 를 참고한다.
KDS 모듈은 다음 9개 모듈로 구성된다.

| 모듈 | 대상 기준 | 주요 기능 |
|---|---|---|
| `kds` | KDS 14 20 10, 14 20 20 | 재료, 등가직사각형 응력블록, 강도감소계수, 설계 휨강도, P-M 상관도, 2축 휨 상관도, 최대 축강도, 연성·최소철근량 |
| `loads` | KDS 14 20 10 4.2.2 | 하중조합 식 (4.2-1)~(4.2-8), 소요강도 |
| `shear` | KDS 14 20 22 | $V_c$·$V_s$, 최소 전단철근량, 스터럽 간격, 비틀림 |
| `serviceability` | KDS 14 20 30 | 유효단면2차모멘트, 장기처짐, 최소 두께, 처짐 한계, 균열 제어 |
| `durability` | KDS 14 20 40 | 노출등급 16종, 최소 설계기준압축강도 |
| `detailing` | KDS 14 20 50, 52 | 최소 피복·간격, 정착길이, 표준갈고리, 겹침이음 |
| `slender` | KDS 14 20 20 4.4 | 세장비, 모멘트확대계수, 임계좌굴하중 |
| `psc` | KDS 14 20 60 | 허용응력, 프리스트레스 손실, $f_{ps}$, PSC 강도감소계수 |
| `biaxial` | (문헌) | Bresler 등하중선법·역하중법, 엄밀해 비교 |

## 라이선스

원 패키지 `concreteproperties` 는 MIT 라이선스로 배포된다. 이 문서와 KDS 모듈도
같은 조건을 따른다.

## 면책

`concreteproperties` 는 여러 기여자의 협업으로 만들어진 오픈소스 공학 도구이다.
관련 공학 이론이 올바르게 구현되도록 노력하였으나, 결과의 확인과 채택은 전적으로
사용자의 책임이다.

이 KDS 모듈에 대해서는 다음 사항을 추가로 유의한다.

> 계수와 조문 번호는 **KDS 14 00 00 원문과 직접 대조**하였다. 대조 결과와 대조에
> 사용한 판은 [설계기준 상세 문서](user_guide/design_codes/kds.md#기준-값-출처와-검증)
> 에 정리해 두었다. KDS 는 계속 개정되므로, 그 판 이후 개정이 있었다면 다시
> 대조해야 한다.
