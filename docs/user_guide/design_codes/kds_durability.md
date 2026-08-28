# 내구성 (KDS 14 20 40)

`concreteproperties_kds.durability` 는 노출등급(표 4.1-1)과 그에 따른 최소
설계기준압축강도(표 4.1-3)를 다룬다.

> **KDS 14 20 40 이 수치로 규정하는 것은 최소 설계기준압축강도뿐이다.**
>
> - 물-결합재비, 결합재 종류, 연행공기량, 염화물 함유량은 **KCS 14 20 10(1.10)**
>   에 위임되어 있다 (KDS 14 20 40 4.1.4(3)).
> - 피복두께는 노출범주 EC·ES 에 대해 **KDS 14 20 50(4.3)** 의 최소 피복두께
>   이상으로 하도록 규정한다 (KDS 14 20 40 4.1.4(2)).
>
> 따라서 이 모듈은 물-결합재비와 피복두께의 수치 기준을 스스로 정하지 않고,
> 사용자가 시방서·KDS 14 20 50 에서 얻은 값을 넣어 검토하도록 한다.

## 노출등급과 최소 설계기준압축강도

| 등급 | 범주 | 환경 | $f_{ck,min}$ (MPa) | 피복 규정 |
|---|---|---|---:|---|
| E0 | 일반 | 철근이 없거나 유해환경 아님 | 21 | – |
| EC1 | 탄산화 | 건조하거나 항상 수중 | 21 | 14 20 50 |
| EC2 | 탄산화 | 습윤하고 드물게 건조 | 24 | 14 20 50 |
| EC3 | 탄산화 | 보통 습도 | 27 | 14 20 50 |
| EC4 | 탄산화 | 주기적인 건습 반복 | 30 | 14 20 50 |
| ES1 | 염화물 | 해양 대기 중 | 30 | 14 20 50 |
| ES2 | 염화물 | 영구히 수중 | 30 | 14 20 50 |
| ES3 | 염화물 | 간만대·물보라 지역 | 35 | 14 20 50 |
| ES4 | 염화물 | 제설염 노출 | 35 | 14 20 50 |
| EF1 | 동결융해 | 수분 접촉, 제빙화학제 없음 | 24 | – |
| EF2 | 동결융해 | 제빙화학제 노출 | 27 | – |
| EF3 | 동결융해 | 수분과 자주 접촉 | 30 | – |
| EF4 | 동결융해 | 해수·제빙화학제 노출 | 30 | – |
| EA1 | 황산염 | 약한 침해 | 27 | – |
| EA2 | 황산염 | 보통 침해 | 30 | – |
| EA3 | 황산염 | 심한 침해 | 30 | – |

강도값은 KDS 14 20 40 표 4.1-3 원문과 대조하였다.

```python
from concreteproperties_kds.durability import print_exposure_table

print_exposure_table()
```

## 검토

```python
from concreteproperties_kds.detailing import minimum_cover
from concreteproperties_kds.durability import check_durability

# 피복두께 요구값은 KDS 14 20 50 에서 구해 넘긴다
cover_min = minimum_cover(condition="흙에접하거나옥외노출", bar="D22")

res = check_durability(
    exposure_class="EC3",
    fck=30,
    cover=40,
    cover_min=cover_min,
    water_binder_ratio=0.45,   # 참고 정보 (KCS 14 20 10 에서 확인)
)
res.print_results()
print(res.ok)
```

```
노출등급  EC3 (탄산화)
          보통 습도
------------------------------------------------------------------------
설계기준압축강도  fck =     30.0 MPa (표 4.1-3 요구 27.0 이상)  만족
피복두께          cc  =     40.0 mm (KDS 14 20 50 요구 50.0 이상)  불만족
물-결합재비       W/B =    0.450   (KCS 14 20 10(1.10) 에서 확인할 것)
------------------------------------------------------------------------
종합                                                불만족
```

`cover` 나 `cover_min` 을 주지 않으면 피복두께는 확인하지 않은 것으로 처리한다
(판정에서 만족으로 본다). `water_binder_ratio` 는 판정에 쓰이지 않고 기록만 된다.

## 복합 노출

하나의 부재가 여러 노출등급에 동시에 해당하면 가장 큰 최소 강도가 지배한다.

```python
from concreteproperties_kds.durability import governing_requirements

governing_requirements(exposure_classes=["EC4", "ES1", "EF2"])   # 30.0 MPa
governing_requirements(exposure_classes=["EC3", "ES3"])          # 35.0 MPa
```

## 피복두께 결정

내구성 요구(EC·ES)와 구조 요구는 같은 표(KDS 14 20 50 4.3)를 가리키므로,
설계 피복두께는 KDS 14 20 50 의 값 이상으로 정하면 된다.

```python
from concreteproperties_kds.detailing import minimum_cover

cover_min = minimum_cover(condition="흙에접하거나옥외노출", bar="D22", fck=35)
cover_design = max(cover_min, 50.0)   # 시공 여유 등을 고려한 설계값
```

## API

| 함수/클래스 | 내용 |
|---|---|
| `ExposureClass` | 노출등급 하나의 요구사항 (`code`, `category`, `description`, `fck_min`, `cover_required`) |
| `EXPOSURE_REQUIREMENTS` | 등급 16종의 표 |
| `check_durability(exposure_class, fck, cover, cover_min, water_binder_ratio)` | 검토 → `DurabilityCheck` |
| `governing_requirements(exposure_classes)` | 복합 노출의 지배 최소 강도 (MPa) |
| `print_exposure_table()` | 등급표 출력 |
| `MAX_CHLORIDE_ION` | 참고용 최대 염화물 이온량 (KDS 규정 아님) |
