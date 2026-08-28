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
    fck_min, wb_max, cover_min = governing_requirements(exposure_classes=exposure)

    width = 68
    print("=" * width)
    print(f"복합 노출 검토 : {', '.join(exposure)}")
    print("=" * width)
    print(f"지배 최소 강도       fck,min = {fck_min:8.1f} MPa")
    print(f"지배 최대 물결합재비 W/B,max = {wb_max:8.2f}")
    print(f"지배 최소 피복       cc,min  = {cover_min:8.1f} mm")
    print()

    # 설계값으로 검토
    fck_design = 35.0
    wb_design = 0.40
    cover_structural = minimum_cover(
        condition="흙에접하거나옥외노출", bar="D22", fck=fck_design
    )
    cover_design = max(cover_structural, cover_min)

    print("=" * width)
    print("피복두께 결정")
    print("=" * width)
    print(f"구조 요구 (KDS 14 20 50)     = {cover_structural:8.1f} mm")
    print(f"내구성 요구 (KDS 14 20 40)   = {cover_min:8.1f} mm")
    print(f"설계 피복두께                = {cover_design:8.1f} mm")
    print()

    for cls in exposure:
        res = check_durability(
            exposure_class=cls,
            fck=fck_design,
            water_binder_ratio=wb_design,
            cover=cover_design,
        )
        res.print_results()
        print()

    # 구조 요구 피복두께 표
    print("=" * width)
    print("현장치기 콘크리트의 최소 피복두께 (KDS 14 20 50 4.3.1)")
    print("=" * width)
    cases = [
        ("흙에영구히묻힘", None),
        ("흙에접하거나옥외노출", "D22"),
        ("흙에접하거나옥외노출", "D13"),
        ("옥내_슬래브벽체장선", "D38"),
        ("옥내_슬래브벽체장선", "D25"),
        ("옥내_보기둥", None),
        ("옥내_셸절판", "D19"),
        ("옥내_셸절판", "D13"),
    ]
    print(f"{'조건':<24} {'철근':>6} {'cc(mm)':>8} {'fck>=40':>9}")
    print("-" * width)
    for condition, bar in cases:
        cc = minimum_cover(condition=condition, bar=bar)
        cc_high = minimum_cover(condition=condition, bar=bar, fck=40)
        print(f"{condition:<24} {bar or '-':>6} {cc:8.0f} {cc_high:9.0f}")


if __name__ == "__main__":
    main()
