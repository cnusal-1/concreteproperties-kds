"""포물선-직선 응력-변형률 관계 시험 (KDS 14 20 20 4.1.1(7)).

값은 KDS 14 20 20 표 4.1-1 원문과 대조한다.
"""

from __future__ import annotations

import pytest
from concreteproperties import ConcreteSection
from sectionproperties.pre.library import concrete_rectangular_section

from concreteproperties_kds import (
    KDS,
    parabolic_parameters,
    parabolic_profile,
    parabolic_stress,
    stress_block_parameters,
)

# KDS 14 20 20 표 4.1-1 — (fck, n, eps_co, eps_cu, alpha, beta)
TABLE_4_1_1 = [
    (40, 2.00, 0.0020, 0.0033, 0.80, 0.40),
    (50, 1.92, 0.0021, 0.0032, 0.78, 0.40),
    (60, 1.50, 0.0022, 0.0031, 0.72, 0.38),
    (70, 1.29, 0.0023, 0.0030, 0.67, 0.37),
    (80, 1.22, 0.0024, 0.0029, 0.63, 0.36),
    (90, 1.20, 0.0025, 0.0028, 0.59, 0.35),
]


@pytest.mark.parametrize(("fck", "n", "eps_co", "eps_cu", "alpha", "beta"), TABLE_4_1_1)
def test_parameters_match_table(fck, n, eps_co, eps_cu, alpha, beta):
    """식 (4.1-3)~(4.1-5) 가 표 4.1-1 을 그대로 재현한다."""
    got = parabolic_parameters(fck=fck)

    assert got[0] == pytest.approx(n, abs=0.005)
    assert got[1] == pytest.approx(eps_co, abs=1e-6)
    assert got[2] == pytest.approx(eps_cu, abs=1e-6)
    assert got[3] == pytest.approx(alpha, abs=0.005)
    assert got[4] == pytest.approx(beta, abs=0.005)


def test_parameters_below_40mpa_are_fixed():
    """40 MPa 이하는 n = 2.0, eps_co = 0.002, eps_cu = 0.0033 로 고정된다."""
    for fck in (18, 21, 24, 27, 30, 35, 40):
        n, eps_co, eps_cu, _, _ = parabolic_parameters(fck=fck)

        assert n == pytest.approx(2.0, abs=0.005)
        assert eps_co == pytest.approx(0.002)
        assert eps_cu == pytest.approx(0.0033)


def test_parameters_above_90mpa_raises():
    """90 MPa 를 넘으면 4.1.1(7)② 에 따라 별도 조사가 필요하다."""
    with pytest.raises(ValueError, match="90 MPa"):
        parabolic_parameters(fck=95)


def test_stress_at_boundaries():
    """식 (4.1-1), (4.1-2) 의 경계값을 확인한다."""
    fck = 27
    _, eps_co, eps_cu, _, _ = parabolic_parameters(fck=fck)

    assert parabolic_stress(fck=fck, eps_c=0.0) == pytest.approx(0.0)
    assert parabolic_stress(fck=fck, eps_c=-0.001) == pytest.approx(0.0)
    assert parabolic_stress(fck=fck, eps_c=eps_co) == pytest.approx(0.85 * fck)
    assert parabolic_stress(fck=fck, eps_c=eps_cu) == pytest.approx(0.85 * fck)


def test_stress_is_monotonic_up_to_eps_co():
    """상승 곡선부는 단조증가한다."""
    fck = 27
    _, eps_co, _, _, _ = parabolic_parameters(fck=fck)

    prev = -1.0
    for i in range(41):
        f_c = parabolic_stress(fck=fck, eps_c=eps_co * i / 40)
        assert f_c > prev
        prev = f_c


def test_profile_carries_no_tension():
    """인장측(음의 변형률)에서 응력이 0 이어야 한다."""
    profile = parabolic_profile(fck=27)

    for eps in (-0.0001, -0.001, -0.01):
        assert profile.get_stress(strain=eps) == pytest.approx(0.0)


def _beam(profile: str) -> KDS:
    """400 x 600 단철근 보 (하부 4-D22)."""
    kds = KDS()
    conc = kds.create_concrete_material(
        compressive_strength=27, ultimate_profile=profile
    )
    steel = kds.create_steel_material(yield_strength=400)
    geom = concrete_rectangular_section(
        d=600,
        b=400,
        dia_top=22,
        area_top=387.1,
        n_top=0,
        c_top=50,
        dia_bot=22,
        area_bot=387.1,
        n_bot=4,
        c_bot=50,
        n_circle=16,
        conc_mat=conc,
        steel_mat=steel,
    )
    kds.assign_concrete_section(ConcreteSection(geom))

    return kds


def test_flexure_agrees_with_stress_block():
    """휨부재에서는 두 관계의 차이가 1 % 이내다.

    지렛대 팔이 지배하고, 두 분포는 합력의 크기와 위치를 맞춰 두었기 때문이다.
    """
    m_block = _beam("block").ultimate_bending_capacity()[1].m_x
    m_para = _beam("parabolic").ultimate_bending_capacity()[1].m_x

    assert abs(m_para / m_block - 1) < 0.01


def test_invalid_ultimate_profile_raises():
    """정의되지 않은 극한 응력-변형률 관계 이름은 거부한다."""
    kds = KDS()

    with pytest.raises(ValueError, match="ultimate_profile"):
        kds.create_concrete_material(compressive_strength=27, ultimate_profile="포물선")


def test_block_remains_the_default():
    """인자를 주지 않으면 등가직사각형 응력블록을 쓴다."""
    kds = KDS()
    conc = kds.create_concrete_material(compressive_strength=27)
    eps_cu, eta, beta_1 = stress_block_parameters(fck=27)

    profile = conc.ultimate_stress_strain_profile

    assert profile.get_ultimate_compressive_strain() == pytest.approx(eps_cu)
    assert profile.get_stress(strain=eps_cu) == pytest.approx(0.85 * eta * 27)
    assert profile.get_stress(strain=(1 - beta_1) * eps_cu * 0.99) == pytest.approx(0.0)
