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
| [KDS 14 20](user_guide/design_codes/kds.md) | **KDS 14 20 설계기준 모듈 상세** |
| [가정](user_guide/assumptions.md) | 해석에 사용된 가정과 부호 규약 |
| [예제](examples.md) | 실행 가능한 예제 8건 |
| [API](api.md) | KDS 모듈 API 참조 |

## 설치

```shell
pip install concreteproperties
```

KDS 모듈은 이 저장소의 `concreteproperties-kds/src` 를 `PYTHONPATH` 에 추가하거나,
해당 디렉터리에서 `pip install -e .` 로 설치한다. 자세한 내용은
[설치](installation.md) 를 참고한다.

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
KDS 모듈이 추가로 제공하는 것은 다음과 같다.

- KDS 14 20 10 4.3.3 의 콘크리트 탄성계수
- KDS 14 20 20 표 4.1-1 의 등가직사각형 응력블록 계수 ($\varepsilon_{cu}$, $\eta$, $\beta_1$)
- KDS 14 20 30 4.2.1 의 파괴계수
- KDS 14 20 10 표 4.2-1 의 강도감소계수 (압축지배 / 변화구간 / 인장지배)
- KDS 14 20 20 4.1.2 의 최대 설계 축강도로 절단된 P-M 상관도
- KDS 14 20 20 4.1.2 의 휨부재 최소허용변형률 검토
- KDS 14 20 20 4.2.2 의 최소 휨철근량

## 라이선스

원 패키지 `concreteproperties` 는 MIT 라이선스로 배포된다. 이 문서와 KDS 모듈도
같은 조건을 따른다.

## 면책

`concreteproperties` 는 여러 기여자의 협업으로 만들어진 오픈소스 공학 도구이다.
관련 공학 이론이 올바르게 구현되도록 노력하였으나, 결과의 확인과 채택은 전적으로
사용자의 책임이다.

이 KDS 모듈에 대해서는 다음 사항을 추가로 유의한다.

> **주의** — KDS 14 20 의 조문 번호와 계수는 개정에 따라 바뀔 수 있다. 실무에
> 적용하기 전에 [설계기준 상세 문서](user_guide/design_codes/kds.md#기준-값-출처와-검증)
> 의 표에 정리된 값을 **현행 KDS 14 20 원문과 반드시 대조**하기 바란다.
