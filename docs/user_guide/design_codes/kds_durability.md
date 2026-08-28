# 내구성 (KDS 14 20 40)

`concreteproperties_kds.durability` 는 노출등급에 따른 최소 설계기준압축강도,
최대 물-결합재비, 최소 피복두께를 다룬다.

> **주의** — 노출등급별 요구값은 개정 이력이 잦고 표의 구성도 바뀐다.
> `EXPOSURE_REQUIREMENTS` 는 편집 가능한 표로 구현되어 있으니, 현행
> KDS 14 20 40 과 대조한 뒤 사용한다.

## 노출등급

| 등급 | 범주 | 환경 | $f_{ck,min}$ | $W/B_{max}$ | $c_{c,min}$ |
|---|---|---|---:|---:|---:|
| E0 | 일반 | 철근이 없거나 유해환경 아님 | 21 | – | – |
| EC1 | 탄산화 | 건조하거나 항상 수중 | 21 | – | 20 |
| EC2 | 탄산화 | 습윤하고 드물게 건조 | 24 | 0.55 | 30 |
| EC3 | 탄산화 | 보통 습도 | 27 | 0.50 | 30 |
| EC4 | 탄산화 | 주기적인 건습 반복 | 30 | 0.45 | 40 |
| ES1 | 염화물 | 해양 대기 중 | 30 | 0.45 | 40 |
| ES2 | 염화물 | 영구히 수중 | 30 | 0.45 | 40 |
| ES3 | 염화물 | 간만대·물보라 지역 | 35 | 0.40 | 60 |
| ES4 | 염화물 | 제설염 노출 | 35 | 0.40 | 60 |
| EF1 | 동결융해 | 수분 접촉, 제빙화학제 없음 | 24 | 0.55 | 40 |
| EF2 | 동결융해 | 제빙화학제 노출 | 27 | 0.50 | 40 |
| EF3 | 동결융해 | 수분과 자주 접촉 | 30 | 0.45 | 40 |
| EF4 | 동결융해 | 해수·제빙화학제 노출 | 30 | 0.45 | 40 |
| EA1 | 황산염 | 약한 침해 | 27 | 0.50 | 40 |
| EA2 | 황산염 | 보통 침해 | 30 | 0.45 | 40 |
| EA3 | 황산염 | 심한 침해 | 30 | 0.45 | 40 |

```python
from concreteproperties_kds.durability import print_exposure_table

print_exposure_table()
```

## 검토

```python
from concreteproperties_kds.durability import check_durability

res = check_durability(
    exposure_class="EC3", fck=30, water_binder_ratio=0.45, cover=40
)
res.print_results()
print(res.ok)   # True
```

```
노출등급  EC3 (탄산화)
          보통 습도
--------------------------------------------------------------------
설계기준압축강도  fck    =     30.0 MPa (요구 27.0 이상)  만족
물-결합재비       W/B    =    0.450 (요구 0.50 이하) 만족
피복두께          cc     =     40.0 mm  (요구 30.0 이상)  만족
--------------------------------------------------------------------
종합                                         만족
```

`water_binder_ratio` 나 `cover` 를 주지 않으면 그 항목은 확인하지 않은 것으로
처리한다 (판정에서 만족으로 본다).

## 복합 노출

하나의 부재가 여러 노출등급에 동시에 해당하면 가장 엄격한 값이 지배한다.

```python
from concreteproperties_kds.durability import governing_requirements

fck_min, wb_max, cover_min = governing_requirements(
    exposure_classes=["EC4", "ES1", "EF2"]
)
# (30.0, 0.45, 40.0)
```

## 피복두께 결정

내구성 요구와 구조 요구(KDS 14 20 50) 중 **큰 값**을 설계 피복두께로 쓴다.

```python
from concreteproperties_kds.detailing import minimum_cover
from concreteproperties_kds.durability import governing_requirements

_, _, cover_durability = governing_requirements(exposure_classes=["EC4", "ES1"])
cover_structural = minimum_cover(
    condition="흙에접하거나옥외노출", bar="D22", fck=35
)

cover_design = max(cover_durability, cover_structural)
```

## 최대 염화물 이온량

`MAX_CHLORIDE_ION` 에 결합재 질량에 대한 비(%)로 정의되어 있다.

| 구분 | 최대 염화물 이온량 |
|---|---|
| 철근콘크리트 (건조) | 0.30 % |
| 철근콘크리트 (습윤) | 0.15 % |
| 프리스트레스트 콘크리트 | 0.06 % |

## API

| 함수/클래스 | 내용 |
|---|---|
| `ExposureClass` | 노출등급 하나의 요구사항 |
| `EXPOSURE_REQUIREMENTS` | 등급별 요구사항 표 (편집 가능) |
| `check_durability(exposure_class, fck, water_binder_ratio, cover)` | 검토 → `DurabilityCheck` |
| `governing_requirements(exposure_classes)` | 복합 노출의 지배 요구값 |
| `print_exposure_table()` | 등급표 출력 |
| `MAX_CHLORIDE_ION` | 최대 염화물 이온량 |
