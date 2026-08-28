"""예제 03 - 균열모멘트와 균열단면 제원.

KDS 14 20 30 의 파괴계수 fr = 0.63*lambda*sqrt(fck) 로부터 균열모멘트를 구하고,
균열단면의 단면2차모멘트와 Branson 식에 의한 유효단면2차모멘트를 계산한다.

실행:
    python 03_균열단면.py [--plot]
"""

from __future__ import annotations

import sys

from examples_common import beam_section


def main(plot: bool = False) -> None:
    """예제를 실행한다.

    Args:
        plot: 균열단면 응력을 도시할지 여부
    """
    kds, conc_sec = beam_section()

    conc = conc_sec.concrete_geometries[0].material
    # 콘크리트 탄성계수를 기준으로 한 환산 총단면 제원
    gross = kds.get_transformed_gross_properties(
        elastic_modulus=conc.elastic_modulus
    )

    print("=" * 70)
    print("균열 검토 (KDS 14 20 30)")
    print("=" * 70)
    print(f"파괴계수           fr   = {conc.flexural_tensile_strength:.3f} MPa")
    print(f"총단면 2차모멘트   Ig   = {gross.ixx_c:,.0f} mm^4")

    cracked = kds.calculate_cracked_properties(theta=0)
    cracked.calculate_transformed_properties(elastic_modulus=conc.elastic_modulus)

    print(f"균열모멘트         Mcr  = {cracked.m_cr / 1e6:.2f} kN.m")
    print(f"중립축 깊이        d_nc = {cracked.d_nc:.2f} mm")
    print(f"균열단면 2차모멘트 Icr  = {cracked.ixx_c_cr:,.0f} mm^4")
    print(f"Icr / Ig                = {cracked.ixx_c_cr / gross.ixx_c:.3f}")

    print()
    print("유효단면2차모멘트 Ie (KDS 14 20 30 4.2.1, Branson 식)")
    print(f"{'Ma/Mcr':>8} {'Ma(kN.m)':>10} {'Ie(mm^4)':>16} {'Ie/Ig':>8}")
    print("-" * 70)

    for ratio in [1.0, 1.2, 1.5, 2.0, 3.0]:
        m_a = ratio * cracked.m_cr
        i_e = (cracked.m_cr / m_a) ** 3 * gross.ixx_c + (
            1 - (cracked.m_cr / m_a) ** 3
        ) * cracked.ixx_c_cr
        i_e = min(i_e, gross.ixx_c)
        print(f"{ratio:8.1f} {m_a / 1e6:10.2f} {i_e:16,.0f} {i_e / gross.ixx_c:8.3f}")

    if plot:
        stress = kds.calculate_cracked_stress(
            cracked_results=cracked, m=1.5 * cracked.m_cr
        )
        stress.plot_stress()


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
