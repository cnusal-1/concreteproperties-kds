"""예제 02 - 총단면·환산단면 제원.

KDS 14 20 재료를 사용하여 400 x 600 철근콘크리트 보의 총단면 제원과
콘크리트 환산단면 제원을 계산한다.

실행:
    python 02_단면제원.py [--plot]
"""

from __future__ import annotations

import sys

from concreteproperties import ConcreteSection
from sectionproperties.pre.library import concrete_rectangular_section

from concreteproperties_kds import KDS


def build_section() -> tuple[KDS, ConcreteSection]:
    """400 x 600 보 단면을 생성한다.

    Returns:
        설계기준 객체와 콘크리트 단면 객체
    """
    kds = KDS()
    conc = kds.create_concrete_material(compressive_strength=27)
    steel = kds.create_steel_material(yield_strength=400)

    geom = concrete_rectangular_section(
        d=600,
        b=400,
        dia_top=16,
        area_top=198.6,
        n_top=2,
        c_top=50,
        dia_bot=22,
        area_bot=387.1,
        n_bot=4,
        c_bot=50,
        n_circle=16,
        conc_mat=conc,
        steel_mat=steel,
    )

    conc_sec = ConcreteSection(geom)
    kds.assign_concrete_section(conc_sec)

    return kds, conc_sec


def main(plot: bool = False) -> None:
    """예제를 실행한다.

    Args:
        plot: 단면을 도시할지 여부
    """
    kds, conc_sec = build_section()

    print("=" * 70)
    print("총단면 제원")
    print("=" * 70)
    kds.get_gross_properties().print_results()

    print()
    print("=" * 70)
    print("콘크리트 환산단면 제원")
    print("=" * 70)
    kds.get_transformed_gross_properties(
        elastic_modulus=conc_sec.concrete_geometries[0].material.elastic_modulus
    ).print_results()

    if plot:
        conc_sec.plot_section()


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
