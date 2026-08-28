"""예제 12 - 내구성 검토와 최소 피복두께.

노출등급에 따른 내구성 요구사항을 확인하고, 내구성·구조 요구를 함께 만족하는
피복두께를 결정한다. (KDS 14 20 40, KDS 14 20 50)

실행:
    python 12_내구성.py
"""

from __future__ import annotations

from concreteproperties_kds.detailing import minimum_cover
from concreteproperties_kds.durability import (
    check_durability,
    governing_requirements,
    print_exposure_table,
)


def main() -> None:
    """예제를 실행한다."""
    print_exposure_table()
    print()

    # 해안 지역 옥외 교각 : 탄산화 + 염화물 + 동결융해
    exposure = ["EC4", "ES1", "EF2"]
    fck_min = governing_requirements(exposure_classes=exposure)

    width = 72
    print("=" * width)
    print(f"복합 노출 검토 : {', '.join(exposure)}")
    print("=" * width)
    print(f"지배 최소 설계기준압축강도  fck,min = {fck_min:8.1f} MPa")
    print()
    print("물-결합재비·결합재·공기량·염화물량은 KCS 14 20 10(1.10) 에 따른다.")
    print("피복두께는 노출범주 EC·ES 에 대해 KDS 14 20 50(4.3) 을 따른다.")
    print()

    # 설계값으로 검토
    fck_design = 35.0
    wb_design = 0.40
    cover_min = minimum_cover(
        condition="흙에접하거나옥외노출", bar="D22", fck=fck_design
    )
    cover_design = 50.0

    print("=" * width)
    print("피복두께 결정 (KDS 14 20 50 4.3.1)")
    print("=" * width)
    print(f"최소 피복두께 (옥외 노출, D22)   = {cover_min:8.1f} mm")
    print(f"설계 피복두께                    = {cover_design:8.1f} mm")
    print()

    for cls in exposure:
        res = check_durability(
            exposure_class=cls,
            fck=fck_design,
            cover=cover_design,
            cover_min=cover_min,
            water_binder_ratio=wb_design,
        )
        res.print_results()
        print()

    # 구조 요구 피복두께 표
    print("=" * width)
    print("현장치기 콘크리트의 최소 피복두께 (KDS 14 20 50 4.3.1)")
    print("=" * width)
    cases = [
        ("수중", None),
        ("흙에영구히묻힘", None),
        ("흙에접하거나옥외노출", "D22"),
        ("흙에접하거나옥외노출", "D13"),
        ("옥내_슬래브벽체장선", "D38"),
        ("옥내_슬래브벽체장선", "D25"),
        ("옥내_보기둥", None),
        ("옥내_셸절판", None),
    ]
    print(f"{'조건':<24} {'철근':>6} {'cc(mm)':>8} {'fck>=40':>9}")
    print("-" * width)
    for condition, bar in cases:
        cc = minimum_cover(condition=condition, bar=bar)
        cc_high = minimum_cover(condition=condition, bar=bar, fck=40)
        print(f"{condition:<24} {bar or '-':>6} {cc:8.0f} {cc_high:9.0f}")


if __name__ == "__main__":
    main()
