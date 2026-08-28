"""예제 13 - 정착길이와 겹침이음 길이.

철근 호칭·강도별 정착길이와 겹침이음 길이를 계산한다. (KDS 14 20 52)

실행:
    python 13_정착이음.py
"""

from __future__ import annotations

from concreteproperties_kds.detailing import (
    BAR_PROPERTIES,
    development_length_tension,
    development_length_tension_detailed,
    minimum_bar_spacing,
    summarise_detailing,
)

FCK = 27.0
FY = 400.0


def main() -> None:
    """예제를 실행한다."""
    summary = summarise_detailing(bar="D22", fy=FY, fck=FCK)
    summary.print_results()
    print()

    width = 80
    print("=" * width)
    print(f"철근 호칭별 정착·이음 길이 (fck = {FCK:.0f} MPa, fy = {FY:.0f} MPa)")
    print("=" * width)
    print(
        f"{'호칭':>6} {'db':>7} {'ld':>9} {'ld(상부)':>10} {'ldc':>8} "
        f"{'ldh':>8} {'이음B급':>9}"
    )
    print("-" * width)

    for bar in BAR_PROPERTIES:
        s = summarise_detailing(bar=bar, fy=FY, fck=FCK)
        l_d_top = development_length_tension(
            bar=bar, fy=FY, fck=FCK, top_bar=True
        )
        print(
            f"{bar:>6} {s.d_b:7.2f} {s.l_d:9.1f} {l_d_top:10.1f} "
            f"{s.l_dc:8.1f} {s.l_dh:8.1f} {s.l_s_tension_b:9.1f}"
        )

    print()
    print("=" * width)
    print("콘크리트 강도가 정착길이에 미치는 영향 (D22, SD400)")
    print("=" * width)
    print(f"{'fck':>6} {'ld(조건만족)':>14} {'ld(기타)':>12} {'ld(정밀식)':>13}")
    print("-" * width)

    for fck in [21, 24, 27, 30, 35, 40, 50, 60]:
        l_ok = development_length_tension(bar="D22", fy=FY, fck=fck)
        l_ng = development_length_tension(
            bar="D22", fy=FY, fck=fck, favourable_spacing=False
        )
        l_detail = development_length_tension_detailed(
            bar="D22", fy=FY, fck=fck, c=40, k_tr=15
        )
        print(f"{fck:6.0f} {l_ok:14.1f} {l_ng:12.1f} {l_detail:13.1f}")

    print()
    print("=" * width)
    print("철근 최소 순간격 (KDS 14 20 50 4.2)")
    print("=" * width)
    print(f"{'호칭':>6} {'보':>10} {'기둥':>10} {'보(골재25)':>13}")
    print("-" * width)
    for bar in ["D13", "D16", "D22", "D25", "D32", "D38"]:
        print(
            f"{bar:>6} "
            f"{minimum_bar_spacing(bar=bar, member='보'):10.1f} "
            f"{minimum_bar_spacing(bar=bar, member='기둥'):10.1f} "
            f"{minimum_bar_spacing(bar=bar, member='보', aggregate_size=25):13.1f}"
        )


if __name__ == "__main__":
    main()
