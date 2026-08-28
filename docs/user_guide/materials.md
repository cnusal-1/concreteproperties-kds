# 재료

`concreteproperties` 는 단면을 구성하는 콘크리트와 강재의 재료 특성을 요구한다.
하나의 단면에 서로 다른 재료를 몇 개든 사용할 수 있다. 예를 들어 고강도 프리캐스트
단면 위에 저강도 현장타설 슬래브를 얹거나, 고장력 철근과 보통 철근을 함께 쓸 수 있다.

> **부호 규약** — 압축의 힘·응력·변형률이 양(+), 인장이 음(−) 이다.

## 재료 클래스

| 클래스 | 요소망 | 용도 |
|---|---|---|
| `Material` | 선택 | 임의 재료 |
| `Concrete` | 요소망 생성 | 콘크리트 |
| `Steel` | 요소망 생성 | 형강 등 큰 강재 단면 (합성구조) |
| `SteelBar` | 격점 처리 | **철근** |
| `SteelStrand` | 격점 처리 | 프리스트레싱 강연선 |

기본적으로 모든 형상은 요소망으로 나뉘어 단면 내 변형률 변화를 반영한다. 다만
철근처럼 작은 형상은 도심에 질량이 집중되고 변형률이 일정한 것으로 처리하는 편이
정확도 손실 없이 훨씬 빠르다. `SteelBar` 와 `SteelStrand` 는 이 처리가 기본값이다.

## KDS 14 20 재료 생성

KDS 모듈은 설계기준이 규정하는 재료 상수를 자동으로 적용한 재료 객체를 만들어 준다.

```python
from concreteproperties_kds import KDS

kds = KDS()

conc = kds.create_concrete_material(compressive_strength=27)  # fck = 27 MPa
steel = kds.create_steel_material(yield_strength=400)         # SD400
```

### 콘크리트

`create_concrete_material(compressive_strength, lambda_c=1.0, m_c=2300, colour=...)`

| 항목 | 값 | 근거 |
|---|---|---|
| 단위질량 | 2300 kg/m³ | KDS 14 20 10 4.3.3 |
| 탄성계수 | $E_c = 8500\sqrt[3]{f_{cm}}$, $f_{cm}=f_{ck}+\Delta f$ | KDS 14 20 10 4.3.3 |
| 사용 응력-변형률 | 인장 무시 선형, 압축 상한 $0.85f_{ck}$ | 구현상의 가정 |
| 극한 응력-변형률 | 등가직사각형 응력블록, $\eta(0.85f_{ck})$, $a=\beta_1 c$ | KDS 14 20 20 4.1.1 |
| 파괴계수 | $f_r = 0.63\lambda\sqrt{f_{ck}}$ | KDS 14 20 30 4.2.1 |

적용 범위는 $18 \le f_{ck} \le 90$ MPa 이다. 범위를 벗어나면 `ValueError` 가 발생한다.

경량콘크리트는 `lambda_c` 로 지정한다 (전경량 0.75, 모래경량 0.85, 보통중량 1.0).
단위질량이 2300 kg/m³ 가 아니면 `m_c` 를 지정하며, 이때 탄성계수는 일반식
$E_c = 0.077 m_c^{1.5}\sqrt[3]{f_{cm}}$ 로 계산된다.

강도별 재료 상수는 다음과 같다.

| $f_{ck}$ (MPa) | $E_c$ (MPa) | $\varepsilon_{cu}$ | $\eta$ | $\beta_1$ | $0.85\eta f_{ck}$ (MPa) | $f_r$ (MPa) |
|---:|---:|---:|---:|---:|---:|---:|
| 18 | 23,817 | 0.0033 | 1.00 | 0.80 | 15.30 | 2.67 |
| 21 | 24,854 | 0.0033 | 1.00 | 0.80 | 17.85 | 2.89 |
| 24 | 25,811 | 0.0033 | 1.00 | 0.80 | 20.40 | 3.09 |
| 27 | 26,702 | 0.0033 | 1.00 | 0.80 | 22.95 | 3.27 |
| 30 | 27,537 | 0.0033 | 1.00 | 0.80 | 25.50 | 3.45 |
| 35 | 28,825 | 0.0033 | 1.00 | 0.80 | 29.75 | 3.73 |
| 40 | 30,008 | 0.0033 | 1.00 | 0.80 | 34.00 | 3.98 |
| 50 | 32,325 | 0.0032 | 0.97 | 0.80 | 41.23 | 4.45 |
| 60 | 34,351 | 0.0031 | 0.95 | 0.76 | 48.45 | 4.88 |
| 70 | 36,005 | 0.0030 | 0.91 | 0.74 | 54.14 | 5.27 |
| 80 | 37,519 | 0.0029 | 0.87 | 0.72 | 59.16 | 5.63 |
| 90 | 38,920 | 0.0028 | 0.84 | 0.70 | 64.26 | 5.98 |

표에 없는 강도는 선형보간한다.

### 철근

`create_steel_material(yield_strength=400, fracture_strain=0.05, colour=...)`

| 항목 | 값 | 근거 |
|---|---|---|
| 단위질량 | 7850 kg/m³ | — |
| 탄성계수 | $E_s = 200{,}000$ MPa | KDS 14 20 10 4.3.4 |
| 응력-변형률 | 완전탄소성 | KDS 14 20 20 4.1.1 |
| 파단변형률 | 0.05 (기본값) | KS D 3504 의 연신율을 참고한 실용값 |

휨·압축 설계에 쓰는 $f_y$ 는 600 MPa 이하여야 하므로(KDS 14 20 20 4.1.1),
`yield_strength` 는 300~600 MPa 로 제한된다.

## 응력-변형률 관계

`Concrete` 객체는 **사용**(사용성 해석: 단면 제원, 모멘트-곡률, 탄성·사용 응력)과
**극한**(극한 휨강도, P-M 상관도, 2축 휨 상관도, 극한 응력) 두 가지 관계를 모두
요구한다. 나머지 재료는 하나의 관계만 있으면 되며 사용·극한 해석에 함께 쓰인다.

### 콘크리트 사용 응력-변형률 관계

| 클래스 | 설명 |
|---|---|
| `ConcreteServiceProfile` | 임의의 점으로 정의하는 일반 관계 |
| `ConcreteLinear` | 대칭 선형 (인장 저항) |
| `ConcreteLinearNoTension` | 인장을 무시한 선형 — **KDS 모듈의 기본값** |
| `EurocodeNonLinear` | Eurocode 2 비선형 |
| `ModifiedMander` | Modified Mander 비선형 (구속·비구속) |

`ConcreteLinear` 는 인장에서도 파괴 없이 큰 응력을 견디므로 모멘트-곡률 해석과 함께
쓰지 않는다.

### 콘크리트 극한 응력-변형률 관계

| 클래스 | 설명 |
|---|---|
| `RectangularStressBlock` | 등가직사각형 응력블록 — **KDS 모듈의 기본값** |
| `BilinearStressStrain` | 이선형 |
| `EurocodeParabolicUltimate` | Eurocode 2 포물선-직선 |

KDS 모듈은 `RectangularStressBlock(compressive_strength=fck, alpha=0.85*eta,
gamma=beta_1, ultimate_strain=eps_cu)` 를 사용한다. 즉 압축응력은
$\eta(0.85 f_{ck})$, 응력블록 깊이는 $a = \beta_1 c$ 이다.

### 강재 응력-변형률 관계

| 클래스 | 설명 |
|---|---|
| `SteelElasticPlastic` | 완전탄소성 — **KDS 모듈의 기본값** |
| `SteelHardening` | 변형경화 포함 |
| `StrandHardening` | 강연선, 변형경화 포함 |
| `StrandPCI1992` | 강연선, PCI Journal (1992) 비선형 |

## 응력-변형률 관계 확인

```python
conc.stress_strain_profile.plot_stress_strain()
conc.ultimate_stress_strain_profile.plot_stress_strain()
steel.stress_strain_profile.plot_stress_strain()

conc.ultimate_stress_strain_profile.print_properties()
```

## 직접 정의하기

설계기준 모듈을 쓰지 않고 재료를 직접 정의할 수도 있다.

```python
import concreteproperties.stress_strain_profile as ssp
from concreteproperties import Concrete, SteelBar

conc = Concrete(
    name="fck 27 MPa",
    density=2.3e-6,
    stress_strain_profile=ssp.ConcreteLinearNoTension(
        elastic_modulus=26702, ultimate_strain=0.0033, compressive_strength=0.85 * 27
    ),
    ultimate_stress_strain_profile=ssp.RectangularStressBlock(
        compressive_strength=27, alpha=0.85, gamma=0.80, ultimate_strain=0.0033
    ),
    flexural_tensile_strength=3.274,
    colour="lightgrey",
)

steel = SteelBar(
    name="SD400",
    density=7.85e-6,
    stress_strain_profile=ssp.SteelElasticPlastic(
        yield_strength=400, elastic_modulus=200e3, fracture_strain=0.05
    ),
    colour="grey",
)
```
