"""예제 01 - KDS 14 20 재료 특성.

KDS 14 20 에 따른 콘크리트·철근 재료를 생성하고, 설계기준이 규정하는
재료 상수(탄성계수, 등가직사각형 응력블록 계수, 파괴계수, 변형률한계)를 표로
출력한다.

실행:
    python 01_재료.py [--plot]
"""

from __future__ import annotations

import sys

from concreteproperties_kds import (
    KDS,
    compression_controlled_strain_limit,
    elastic_modulus,
    modulus_of_rupture,
    stress_block_parameters,
    tension_controlled_strain_limit,
)


def main(plot: bool = False) -> None:
    """예제를 실행한다.

    Args:
        plot: 응력-변형률 관계를 도시할지 여부
    """
    print("=" * 78)
    print("콘크리트 재료 상수 (KDS 14 20 10 4.3.3, KDS 14 20 20 표 4.1-1)")
    print("=" * 78)
    print(
        f"{'fck':>6} {'Ec':>10} {'eps_cu':>9} {'eta':>7} {'beta_1':>8} "
        f"{'0.85*eta*fck':>13} {'fr':>7}"
    )
    print(
        f"{'(MPa)':>6} {'(MPa)':>10} {'':>9} {'':>7} {'':>8} "
        f"{'(MPa)':>13} {'(MPa)':>7}"
    )
    print("-" * 78)

    for fck in [18, 21, 24, 27, 30, 35, 40, 50, 60, 70, 80, 90]:
        e_c = elastic_modulus(fck=fck)
        eps_cu, eta, beta_1 = stress_block_parameters(fck=fck)
        f_r = modulus_of_rupture(fck=fck)
        print(
            f"{fck:6.0f} {e_c:10.0f} {eps_cu:9.4f} {eta:7.2f} {beta_1:8.2f} "
            f"{0.85 * eta * fck:13.2f} {f_r:7.2f}"
        )

    print()
    print("=" * 78)
    print("철근 변형률한계 (KDS 14 20 20 4.1.2)")
    print("=" * 78)
    print(f"{'강종':>8} {'fy(MPa)':>9} {'eps_y':>9} {'eps_t,tl':>10} {'eps_t,min':>11}")
    print("-" * 78)

    for fy in [300, 400, 500, 600]:
        eps_y = compression_controlled_strain_limit(fy=fy)
        eps_tl = tension_controlled_strain_limit(fy=fy)
        eps_min = 0.004 if fy <= 400 else 2.0 * fy / 200e3
        print(
            f"{'SD' + str(fy):>8} {fy:9.0f} {eps_y:9.4f} "
            f"{eps_tl:10.5f} {eps_min:11.5f}"
        )

    print()
    print("=" * 78)
    print("재료 객체 생성")
    print("=" * 78)

    kds = KDS()
    conc = kds.create_concrete_material(compressive_strength=27)
    steel = kds.create_steel_material(yield_strength=400)

    print(f"콘크리트 : {conc.name}")
    print(f"  탄성계수          Ec = {conc.elastic_modulus:,.0f} MPa")
    print(f"  파괴계수          fr = {conc.flexural_tensile_strength:.2f} MPa")
    print(f"  단위질량               = {conc.density * 1e9:,.0f} kg/m^3")
    print(f"철근     : {steel.name}")
    print(f"  탄성계수          Es = {steel.elastic_modulus:,.0f} MPa")

    if plot:
        conc.stress_strain_profile.plot_stress_strain(
            title="콘크리트 사용 응력-변형률 관계"
        )
        conc.ultimate_stress_strain_profile.plot_stress_strain(
            title="콘크리트 등가직사각형 응력블록"
        )
        steel.stress_strain_profile.plot_stress_strain(title="철근 응력-변형률 관계")


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
