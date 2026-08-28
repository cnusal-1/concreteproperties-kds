"""예제에서 공통으로 사용하는 단면 정의."""

from __future__ import annotations

from concreteproperties import ConcreteSection
from sectionproperties.pre.library import concrete_rectangular_section

from concreteproperties_kds import KDS


def beam_section(fck: float = 27, fy: float = 400) -> tuple[KDS, ConcreteSection]:
    """400 x 600 철근콘크리트 보 단면.

    상부 2-D16, 하부 4-D22, 피복 50 mm (철근 중심까지).

    Args:
        fck: 콘크리트 설계기준압축강도 (MPa). 기본값 ``27``.
        fy: 철근의 설계기준항복강도 (MPa). 기본값 ``400``.

    Returns:
        설계기준 객체와 콘크리트 단면 객체
    """
    kds = KDS(column_type="tie")
    conc = kds.create_concrete_material(compressive_strength=fck)
    steel = kds.create_steel_material(yield_strength=fy)

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


def column_section(
    fck: float = 27,
    fy: float = 400,
    column_type: str = "tie",
) -> tuple[KDS, ConcreteSection]:
    """500 x 500 철근콘크리트 기둥 단면 (8-D22, 피복 50 mm).

    Args:
        fck: 콘크리트 설계기준압축강도 (MPa). 기본값 ``27``.
        fy: 철근의 설계기준항복강도 (MPa). 기본값 ``400``.
        column_type: ``"tie"`` (띠철근) 또는 ``"spiral"`` (나선철근).
            기본값 ``"tie"``.

    Returns:
        설계기준 객체와 콘크리트 단면 객체
    """
    kds = KDS(column_type=column_type)
    conc = kds.create_concrete_material(compressive_strength=fck)
    steel = kds.create_steel_material(yield_strength=fy)

    geom = concrete_rectangular_section(
        d=500,
        b=500,
        dia_top=22,
        area_top=387.1,
        n_top=3,
        c_top=50,
        dia_bot=22,
        area_bot=387.1,
        n_bot=3,
        c_bot=50,
        dia_side=22,
        area_side=387.1,
        n_side=1,
        c_side=50,
        n_circle=16,
        conc_mat=conc,
        steel_mat=steel,
    )

    conc_sec = ConcreteSection(geom)
    kds.assign_concrete_section(conc_sec)

    return kds, conc_sec
