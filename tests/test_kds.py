"""KDS 14 20 설계기준 클래스의 검증 시험.

기준값은 KDS 14 20 의 조문을 손계산으로 적용하여 산정하였다.
"""

from __future__ import annotations

import numpy as np
import pytest
from concreteproperties import ConcreteSection, add_bar_rectangular_array
from concreteproperties.utils import AnalysisError
from sectionproperties.pre.library import (
    concrete_rectangular_section,
    rectangular_section,
)

from concreteproperties_kds import (
    KDS,
    compression_controlled_strain_limit,
    elastic_modulus,
    minimum_flexural_moment,
    minimum_flexural_moment_alternative,
    minimum_net_tensile_strain,
    modulus_of_rupture,
    stress_block_parameters,
    tension_controlled_strain_limit,
)

# 계산 허용오차
TOL = 1e-3


# ---------------------------------------------------------------------------
# 재료 특성 (KDS 14 20 10, KDS 14 20 20, KDS 14 20 30)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("fck", "e_c"),
    [
        (21, 24854),
        (24, 25811),
        (27, 26702),
        (30, 27537),
        (35, 28825),
        (40, 30008),
        (50, 32325),
        (60, 34351),
    ],
)
def test_elastic_modulus(fck, e_c):
    """탄성계수가 KDS 14 20 10 4.3.3 의 값과 일치하는지 확인한다."""
    assert elastic_modulus(fck=fck) == pytest.approx(e_c, rel=1e-3)


@pytest.mark.parametrize(
    ("fck", "eps_cu", "eta", "beta_1"),
    [
        (24, 0.0033, 1.00, 0.80),
        (40, 0.0033, 1.00, 0.80),
        (50, 0.0032, 0.97, 0.80),
        (60, 0.0031, 0.95, 0.76),
        (70, 0.0030, 0.91, 0.74),
        (80, 0.0029, 0.87, 0.72),
        (90, 0.0028, 0.84, 0.70),
    ],
)
def test_stress_block_parameters(fck, eps_cu, eta, beta_1):
    """등가직사각형 응력블록 계수가 KDS 14 20 20 표 4.1-2 과 일치하는지 확인한다."""
    res = stress_block_parameters(fck=fck)

    assert res[0] == pytest.approx(eps_cu)
    assert res[1] == pytest.approx(eta)
    assert res[2] == pytest.approx(beta_1)


def test_stress_block_interpolation():
    """표에 없는 강도는 선형보간되는지 확인한다."""
    eps_cu, eta, beta_1 = stress_block_parameters(fck=55)

    assert eps_cu == pytest.approx(0.5 * (0.0032 + 0.0031))
    assert eta == pytest.approx(0.5 * (0.97 + 0.95))
    assert beta_1 == pytest.approx(0.5 * (0.80 + 0.76))


def test_modulus_of_rupture():
    """파괴계수가 0.63*lambda*sqrt(fck) 인지 확인한다."""
    assert modulus_of_rupture(fck=24) == pytest.approx(0.63 * np.sqrt(24))
    assert modulus_of_rupture(fck=24, lambda_c=0.75) == pytest.approx(
        0.75 * 0.63 * np.sqrt(24)
    )


@pytest.mark.parametrize(
    ("fy", "eps_y", "eps_tl"),
    [
        (300, 0.0015, 0.005),
        (400, 0.0020, 0.005),
        (500, 0.0025, 0.00625),
        (600, 0.0030, 0.0075),
    ],
)
def test_strain_limits(fy, eps_y, eps_tl):
    """압축지배·인장지배 변형률한계를 확인한다 (KDS 14 20 20 4.1.2)."""
    assert compression_controlled_strain_limit(fy=fy) == pytest.approx(eps_y)
    assert tension_controlled_strain_limit(fy=fy) == pytest.approx(eps_tl)


def test_minimum_net_tensile_strain():
    """휨부재 최소허용변형률을 확인한다 (KDS 14 20 20 4.1.2)."""
    assert minimum_net_tensile_strain(fy=400) == pytest.approx(0.004)
    assert minimum_net_tensile_strain(fy=500) == pytest.approx(0.005)


def test_minimum_flexural_moment():
    """최소 철근량 조건 phi*Mn >= 1.2Mcr 를 확인한다 (KDS 14 20 20 4.2.2)."""
    assert minimum_flexural_moment(m_cr=88.4e6) == pytest.approx(1.2 * 88.4e6)


def test_minimum_flexural_moment_alternative():
    """대체 조건 phi*Mn >= (4/3)Mu 를 확인한다 (KDS 14 20 20 4.2.2(2))."""
    assert minimum_flexural_moment_alternative(m_u=300e6) == pytest.approx(
        4 / 3 * 300e6
    )


def test_material_limits():
    """재료 강도의 적용범위를 벗어나면 예외가 발생하는지 확인한다."""
    kds = KDS()

    with pytest.raises(ValueError, match="compressive_strength"):
        kds.create_concrete_material(compressive_strength=17)

    with pytest.raises(ValueError, match="compressive_strength"):
        kds.create_concrete_material(compressive_strength=100)

    with pytest.raises(ValueError, match="yield_strength"):
        kds.create_steel_material(yield_strength=700)

    with pytest.raises(ValueError, match="column_type"):
        KDS(column_type="hoop")


# ---------------------------------------------------------------------------
# 단철근 직사각형 보 - 손계산 대조
# ---------------------------------------------------------------------------


def singly_reinforced_beam(fck=24, fy=400, n_bar=4, area=387.1):
    """b=300, h=600, d=540 단철근 보를 생성한다."""
    kds = KDS()
    conc = kds.create_concrete_material(compressive_strength=fck)
    steel = kds.create_steel_material(yield_strength=fy)

    geom = rectangular_section(d=600, b=300, material=conc)
    geom = add_bar_rectangular_array(
        geometry=geom,
        area=area,
        material=steel,
        n_x=n_bar,
        x_s=(300 - 2 * 60) / (n_bar - 1),
        anchor=(60, 60),
        n=16,
    )
    conc_sec = ConcreteSection(geom)
    kds.assign_concrete_section(conc_sec)

    return kds, conc_sec


def test_beam_flexural_capacity():
    """단철근 보의 설계 휨강도를 손계산과 대조한다.

    b = 300 mm, d = 540 mm, fck = 24 MPa, fy = 400 MPa, As = 4-D22 = 1548.4 mm^2

    a  = As*fy / (eta*0.85*fck*b) = 101.20 mm
    c  = a / beta_1 = 126.50 mm
    et = 0.0033 * (540 - 126.50) / 126.50 = 0.010786 > 0.005  -> 인장지배단면
    Mn = As*fy*(d - a/2) = 303.11 kN.m
    phi*Mn = 0.85 * 303.11 = 257.65 kN.m
    """
    kds, _ = singly_reinforced_beam()
    f_res, u_res, phi = kds.ultimate_bending_capacity()

    a_s = 4 * 387.1
    a = a_s * 400 / (0.85 * 24 * 300)
    c = a / 0.80
    eps_t = 0.0033 * (540 - c) / c
    m_n = a_s * 400 * (540 - a / 2)

    assert u_res.d_n == pytest.approx(c, rel=TOL)
    assert kds.net_tensile_strain(theta=0, d_n=u_res.d_n) == pytest.approx(
        eps_t, rel=TOL
    )
    assert phi == pytest.approx(0.85)
    assert u_res.m_x == pytest.approx(m_n, rel=TOL)
    assert f_res.m_x == pytest.approx(0.85 * m_n, rel=TOL)


def test_beam_section_classification():
    """철근비에 따른 단면 분류와 강도감소계수를 확인한다."""
    # 저철근비 -> 인장지배단면
    kds, _ = singly_reinforced_beam(n_bar=4)
    _, u_res, phi = kds.ultimate_bending_capacity()
    eps_t = kds.net_tensile_strain(theta=0, d_n=u_res.d_n)
    assert kds.section_classification(eps_t=eps_t) == "인장지배단면"
    assert phi == pytest.approx(0.85)

    # 과다철근비 -> 변화구간 또는 압축지배단면, phi < 0.85
    kds, _ = singly_reinforced_beam(n_bar=8, area=794.2)
    _, u_res, phi = kds.ultimate_bending_capacity()
    eps_t = kds.net_tensile_strain(theta=0, d_n=u_res.d_n)
    assert kds.section_classification(eps_t=eps_t) != "인장지배단면"
    assert phi < 0.85


def test_flexural_ductility_check():
    """휨부재의 최소허용변형률 검토를 확인한다."""
    kds, _ = singly_reinforced_beam(n_bar=4)
    eps_t, eps_min, ok = kds.check_flexural_ductility()
    assert eps_min == pytest.approx(0.004)
    assert ok is True
    assert eps_t > eps_min

    kds, _ = singly_reinforced_beam(n_bar=8, area=794.2)
    _, _, ok = kds.check_flexural_ductility()
    assert ok is False


def test_phi_varies_continuously():
    """변화구간에서 강도감소계수가 0.65~0.85 사이에서 연속적으로 변함을 확인한다."""
    kds, _ = singly_reinforced_beam()

    phis = []
    for eps_t in np.linspace(0.0, 0.008, 41):
        phis.append(kds.capacity_reduction_factor(eps_t=float(eps_t)))

    phis_arr = np.array(phis)

    assert phis_arr.min() == pytest.approx(0.65)
    assert phis_arr.max() == pytest.approx(0.85)
    # 단조 증가
    assert np.all(np.diff(phis_arr) >= -1e-12)
    # 변형률한계에서의 값
    assert kds.capacity_reduction_factor(eps_t=0.002) == pytest.approx(0.65)
    assert kds.capacity_reduction_factor(eps_t=0.005) == pytest.approx(0.85)
    assert kds.capacity_reduction_factor(eps_t=0.0035) == pytest.approx(0.75)


# ---------------------------------------------------------------------------
# 기둥 - 축강도와 P-M 상관도
# ---------------------------------------------------------------------------


def column(column_type="tie", fck=27, fy=400):
    """500x500 기둥 (8-D22) 을 생성한다."""
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


def test_squash_and_tensile_load():
    """순수압축·순수인장 하중을 손계산과 대조한다.

    Po  = 0.85*fck*(Ag - Ast) + fy*Ast
    Pnt = -fy*Ast
    """
    kds, conc_sec = column()

    a_st = 8 * 387.1
    a_g = 500 * 500
    p_o = 0.85 * 27 * (a_g - a_st) + 400 * a_st

    assert kds.squash_load == pytest.approx(p_o, rel=TOL)
    assert kds.tensile_load == pytest.approx(-400 * a_st, rel=TOL)


@pytest.mark.parametrize(
    ("column_type", "alpha", "phi"),
    [("tie", 0.80, 0.65), ("spiral", 0.85, 0.70)],
)
def test_max_axial_strength(column_type, alpha, phi):
    """최대 설계 축강도를 확인한다 (KDS 14 20 20 4.1.2)."""
    kds, _ = column(column_type=column_type)
    n_nom, n_des = kds.max_axial_strength()

    assert n_nom == pytest.approx(alpha * kds.squash_load)
    assert n_des == pytest.approx(phi * alpha * kds.squash_load)


def test_moment_interaction_diagram():
    """P-M 상관도의 형태와 강도감소계수 적용을 확인한다."""
    kds, _ = column()
    f_mi, mi, phis = kds.moment_interaction_diagram(n_points=8, progress_bar=False)

    # 점의 개수가 일치
    assert len(f_mi.results) == len(mi.results) == len(phis)

    # 축력이 단조 감소
    n_list = [r.n for r in mi.results]
    assert np.all(np.diff(n_list) <= 1e-6)

    # 첫 점은 최대 공칭 축강도, 무모멘트
    assert mi.results[0].n == pytest.approx(kds.max_axial_strength()[0])
    assert mi.results[0].m_x == pytest.approx(0)
    assert phis[0] == pytest.approx(0.65)

    # 마지막 점은 순수인장, 인장지배단면
    assert mi.results[-1].n == pytest.approx(kds.tensile_load)
    assert phis[-1] == pytest.approx(0.85)

    # 설계강도 = 공칭강도 * phi
    for r_f, r_u, phi in zip(f_mi.results, mi.results, phis, strict=True):
        assert r_f.n == pytest.approx(phi * r_u.n)
        assert r_f.m_x == pytest.approx(phi * r_u.m_x)

    # 강도감소계수는 항상 범위 내
    assert min(phis) >= 0.65 - 1e-9
    assert max(phis) <= 0.85 + 1e-9


def test_ultimate_bending_capacity_with_axial_force():
    """축력에 따라 강도감소계수가 올바르게 변하는지 확인한다."""
    kds, _ = column()

    results = {}
    for n_d in [0, 600e3, 1200e3, 2400e3]:
        f_res, u_res, phi = kds.ultimate_bending_capacity(n_design=n_d)
        eps_t = kds.net_tensile_strain(theta=0, d_n=u_res.d_n)
        results[n_d] = (phi, eps_t)

        # 설계 축력이 요구값과 일치 (해석 수렴 오차 범위 내)
        assert f_res.n == pytest.approx(n_d, abs=kds.squash_load * 1e-5)
        # 설계강도 = 공칭강도 * phi
        assert f_res.m_x == pytest.approx(phi * u_res.m_x)
        # phi 가 순인장변형률과 정합
        assert phi == pytest.approx(
            kds.capacity_reduction_factor(eps_t=eps_t), abs=1e-3
        )

    # 축력이 커질수록 순인장변형률이 감소하고 phi 가 감소
    phis = [results[n][0] for n in sorted(results)]
    eps = [results[n][1] for n in sorted(results)]
    assert np.all(np.diff(phis) <= 1e-9)
    assert np.all(np.diff(eps) <= 0)


def test_axial_load_limits():
    """축강도 범위를 벗어나면 예외가 발생하는지 확인한다."""
    kds, _ = column()
    _, n_max_design = kds.max_axial_strength()

    with pytest.raises(AnalysisError, match="최대 설계 축강도"):
        kds.ultimate_bending_capacity(n_design=n_max_design * 1.05)

    with pytest.raises(AnalysisError, match="설계 인장강도"):
        kds.ultimate_bending_capacity(n_design=0.85 * kds.tensile_load * 1.05)


def test_biaxial_bending_diagram():
    """2축 휨 상관도가 생성되는지 확인한다."""
    kds, _ = column()
    f_bb, phis = kds.biaxial_bending_diagram(
        n_design=1000e3, n_points=8, progress_bar=False
    )

    assert len(f_bb.results) == 9  # 첫 점을 마지막에 반복
    assert len(phis) == 9
    assert all(0.65 - 1e-9 <= p <= 0.85 + 1e-9 for p in phis)

    # 정사각형 대칭 단면이므로 90도 회전에 대해 강도가 동일
    m_res = [np.hypot(r.m_x, r.m_y) for r in f_bb.results[:8]]
    assert m_res[0] == pytest.approx(m_res[2], rel=1e-2)
    assert m_res[0] == pytest.approx(m_res[4], rel=1e-2)


def test_meshed_reinforcement_rejected():
    """메시화된 철근이 있으면 예외가 발생하는지 확인한다."""
    from concreteproperties.material import Steel
    from concreteproperties.stress_strain_profile import SteelElasticPlastic

    kds = KDS()
    conc = kds.create_concrete_material(compressive_strength=24)
    bar = kds.create_steel_material(yield_strength=400)
    plate_mat = Steel(
        name="plate",
        density=7.85e-6,
        stress_strain_profile=SteelElasticPlastic(
            yield_strength=300, elastic_modulus=200e3, fracture_strain=0.05
        ),
        colour="tan",
    )

    geom = rectangular_section(d=600, b=300, material=conc)
    geom = add_bar_rectangular_array(
        geometry=geom, area=387.1, material=bar, n_x=2, x_s=180, anchor=(60, 60), n=16
    )
    geom = geom + rectangular_section(d=10, b=300, material=plate_mat).shift_section(
        y_offset=600
    )

    with pytest.raises(ValueError, match="메시화된 철근"):
        kds.assign_concrete_section(ConcreteSection(geom))


def test_check_minimum_flexural_reinforcement():
    """단면의 설계휨강도가 1.2Mcr 이상인지 검토한다 (KDS 14 20 20 4.2.2)."""
    kds, _ = singly_reinforced_beam(n_bar=4)
    phi_m_n, m_cr, m_required, ok = kds.check_minimum_flexural_reinforcement()

    assert m_required == pytest.approx(1.2 * m_cr)
    assert phi_m_n > 0
    assert ok is True

    # 철근이 매우 적으면 조건을 만족하지 못한다
    kds, _ = singly_reinforced_beam(n_bar=2, area=71.33)
    _, m_cr, m_required, ok = kds.check_minimum_flexural_reinforcement()
    assert m_required == pytest.approx(1.2 * m_cr)
    assert ok is False


def test_check_minimum_flexural_reinforcement_alternative():
    """(4/3)Mu 대체 조건이 적용되는지 확인한다 (KDS 14 20 20 4.2.2(2))."""
    kds, _ = singly_reinforced_beam(n_bar=2, area=71.33)

    _, _, _, ok_strict = kds.check_minimum_flexural_reinforcement()
    phi_m_n, _, _, ok_alt = kds.check_minimum_flexural_reinforcement(
        m_u=0.5 * 20e6
    )

    assert ok_strict is False
    assert ok_alt is (phi_m_n >= 4 / 3 * 0.5 * 20e6)
