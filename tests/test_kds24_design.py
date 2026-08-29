"""KDS 24 14 21 단면 해석 시험 (극한한계상태 휨·축력).

KDS 14 와 나란히 풀어 두 안전율 형식의 차이를 고정한다.
"""

from __future__ import annotations

import pytest
from concreteproperties import ConcreteSection
from sectionproperties.pre.library import concrete_rectangular_section

from concreteproperties_kds import KDS
from concreteproperties_kds.kds24 import (
    KDS24,
    biaxial_exponent,
    design_compressive_strength,
    design_yield_strength,
    minimum_eccentricity,
)

D22 = 387.1


def _beam(code, fck: float = 40, fy: float = 400, n_bar: int = 4):
    """400 x 600 단철근 보를 주어진 설계기준으로 만든다."""
    conc = code.create_concrete_material(compressive_strength=fck)
    steel = code.create_steel_material(yield_strength=fy)
    geom = concrete_rectangular_section(
        d=600,
        b=400,
        dia_top=22,
        area_top=D22,
        n_top=0,
        c_top=50,
        dia_bot=22,
        area_bot=D22,
        n_bot=n_bar,
        c_bot=50,
        n_circle=16,
        conc_mat=conc,
        steel_mat=steel,
    )
    code.assign_concrete_section(ConcreteSection(geom))

    return code


def test_materials_carry_the_factors():
    """재료에 재료계수가 이미 들어 있다."""
    code = KDS24()
    conc = code.create_concrete_material(compressive_strength=40)
    steel = code.create_steel_material(yield_strength=400)

    ultimate = conc.ultimate_stress_strain_profile
    # get_compressive_strength() 는 기준압축강도를 돌려준다. 재료계수가 반영된
    # 설계압축강도는 곡선의 최대값이다.
    assert ultimate.get_compressive_strength() == pytest.approx(40.0)
    assert max(ultimate.stresses) == pytest.approx(design_compressive_strength(fck=40))
    assert steel.stress_strain_profile.get_yield_strength() == pytest.approx(
        design_yield_strength(fy=400)
    )


def test_design_bending_capacity_is_hand_checkable():
    """설계휨강도가 등가블록 손계산과 1 % 안에서 맞는다.

    C = f_cd * b * a, T = A_s f_yd, M_Rd = T (d - a/2) 로 검산한다. 등가블록의
    깊이는 alpha/beta 계수를 써서 a = 2 * beta * c 로 환산한다.
    """
    code = _beam(KDS24())
    result = code.design_bending_capacity()

    f_cd = design_compressive_strength(fck=40)
    f_yd = design_yield_strength(fy=400)
    a_s = 4 * D22
    d = 539.0

    # 평형: C = T 로부터 등가블록 깊이
    from concreteproperties_kds.kds24 import equivalent_block

    alpha_eq, beta_eq = equivalent_block(fck=40)
    c_n = a_s * f_yd / (alpha_eq * f_cd * 400.0)
    m_hand = a_s * f_yd * (d - beta_eq * c_n)

    assert result.m_x == pytest.approx(m_hand, rel=0.01)


def test_kds24_gives_more_flexural_strength_than_kds14():
    """휨부재에서는 KDS 24 의 설계강도가 KDS 14 보다 크다.

    휨은 철근이 지배하는데, KDS 24 의 강재 재료계수 0.90 이 KDS 14 의 단면
    강도감소계수 0.85 보다 덜 깎기 때문이다.
    """
    m_rd = _beam(KDS24()).design_bending_capacity().m_x
    f_res, _, phi = _beam(KDS()).ultimate_bending_capacity()

    assert phi == pytest.approx(0.85)
    assert m_rd > f_res.m_x
    assert m_rd / f_res.m_x == pytest.approx(1.04, abs=0.03)


def test_service_factors_recover_nominal_strength():
    """재료계수를 1.0 으로 두면 KDS 14 의 공칭강도에 가까워진다.

    두 기준이 같은 역학을 쓴다는 것을 확인하는 시험이다. 응력-변형률 관계가
    포물선-직선과 등가블록으로 서로 다르므로 완전히 같지는 않다.
    """
    m_unfactored = _beam(KDS24(phi_c=1.0, phi_s=1.0)).design_bending_capacity().m_x
    _, u_res, _ = _beam(KDS()).ultimate_bending_capacity()

    assert m_unfactored == pytest.approx(u_res.m_x, rel=0.02)


def test_squash_load_uses_design_strengths():
    """순수압축 하중이 설계 재료강도로 계산된다."""
    code = _beam(KDS24())
    squash, tensile = code.squash_tensile_load()

    f_yd = design_yield_strength(fy=400)
    assert tensile == pytest.approx(-4 * D22 * f_yd)
    assert squash > 0


def test_minimum_eccentricity():
    """4.1.1.2(5) — e_min = max(h/30, 20 mm)."""
    assert minimum_eccentricity(h=300) == pytest.approx(20.0)
    assert minimum_eccentricity(h=600) == pytest.approx(20.0)
    assert minimum_eccentricity(h=900) == pytest.approx(30.0)
    assert minimum_eccentricity(h=1500) == pytest.approx(50.0)


def test_minimum_moment():
    """최소편심에 의한 최소 설계휨모멘트."""
    code = _beam(KDS24())

    assert code.minimum_moment(n_design=1000e3, h=600) == pytest.approx(1000e3 * 20.0)


def test_biaxial_exponent():
    """4.1.1.3(3) 식 (4.1-4) 의 지수."""
    assert biaxial_exponent(n_ed=0, n_rd=1000, shape="원형") == pytest.approx(2.0)
    assert biaxial_exponent(n_ed=50, n_rd=1000) == pytest.approx(1.0)
    assert biaxial_exponent(n_ed=700, n_rd=1000) == pytest.approx(1.5)
    assert biaxial_exponent(n_ed=1000, n_rd=1000) == pytest.approx(2.0)
    assert 1.0 < biaxial_exponent(n_ed=400, n_rd=1000) < 1.5

    with pytest.raises(ValueError, match="shape"):
        biaxial_exponent(n_ed=0, n_rd=1, shape="T형")


def test_moment_interaction_diagram_has_one_curve():
    """상관도가 하나만 나온다.

    KDS 14 는 공칭과 설계 두 곡선이 나오고 간격이 점마다 다르지만, KDS 24 는
    재료계수가 재료에 들어 있어 설계 상관도 하나로 끝난다.
    """
    code = _beam(KDS24(), n_bar=6)
    diagram = code.moment_interaction_diagram(n_points=12, progress_bar=False)

    assert len(diagram.results) >= 12
    assert max(r.m_x for r in diagram.results) > 0


def test_invalid_material_factor_raises():
    """재료계수는 0 보다 크고 1 이하여야 한다."""
    for kwargs in ({"phi_c": 0.0}, {"phi_c": 1.5}, {"phi_s": -0.1}):
        with pytest.raises(ValueError, match="0 보다"):
            KDS24(**kwargs)


def test_rejects_out_of_range_materials():
    """재료 강도 범위를 벗어나면 거부한다."""
    code = KDS24()

    with pytest.raises(ValueError, match="compressive_strength"):
        code.create_concrete_material(compressive_strength=95)

    with pytest.raises(ValueError, match="yield_strength"):
        code.create_steel_material(yield_strength=700)
