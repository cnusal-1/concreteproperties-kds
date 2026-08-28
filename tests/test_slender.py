"""세장 기둥 검증 시험 (KDS 14 20 20 4.4)."""

from __future__ import annotations

import numpy as np
import pytest

from concreteproperties_kds.slender import (
    PHI_K,
    check_slenderness,
    critical_buckling_load,
    flexural_stiffness,
    minimum_moment,
    moment_magnifier_braced,
    radius_of_gyration,
    slenderness_limit,
    slenderness_ratio,
)


def test_radius_of_gyration():
    """단면 형태별 회전반지름을 확인한다."""
    assert radius_of_gyration(section="rectangular", h=500) == pytest.approx(150.0)
    assert radius_of_gyration(section="circular", h=500) == pytest.approx(125.0)

    i_g = 500.0**4 / 12
    a_g = 500.0**2
    assert radius_of_gyration(
        section="general", i_g=i_g, a_g=a_g
    ) == pytest.approx(np.sqrt(i_g / a_g))


def test_radius_of_gyration_general_matches_rectangular():
    """직사각형의 정확한 r 은 0.2887h 로 0.3h 근사와 가깝다."""
    h = 500.0
    exact = radius_of_gyration(
        section="general", i_g=h**4 / 12, a_g=h**2
    )

    assert exact == pytest.approx(h / np.sqrt(12))
    assert exact == pytest.approx(0.3 * h, rel=0.04)


def test_radius_of_gyration_invalid():
    """잘못된 입력은 예외가 발생한다."""
    with pytest.raises(ValueError, match="section"):
        radius_of_gyration(section="triangle", h=500)

    with pytest.raises(ValueError, match="i_g"):
        radius_of_gyration(section="general")


def test_slenderness_ratio():
    """세장비 k*lu/r 을 확인한다."""
    assert slenderness_ratio(k=1.0, l_u=4000, r=150) == pytest.approx(4000 / 150)

    with pytest.raises(ValueError, match="r"):
        slenderness_ratio(k=1.0, l_u=4000, r=0)


def test_slenderness_limit_braced():
    """횡구속 골조의 한계 세장비를 확인한다."""
    # 단곡률 M1/M2 = 0.5 -> 34 - 6 = 28
    assert slenderness_limit(braced=True, m1=50, m2=100) == pytest.approx(28.0)
    # 복곡률 M1/M2 = -0.5 -> 34 + 6 = 40 (상한)
    assert slenderness_limit(braced=True, m1=-50, m2=100) == pytest.approx(40.0)
    # M1 = 0 -> 34
    assert slenderness_limit(braced=True, m1=0, m2=100) == pytest.approx(34.0)
    # 상한 40
    assert slenderness_limit(braced=True, m1=-100, m2=100) == pytest.approx(40.0)


def test_slenderness_limit_unbraced():
    """비횡구속 골조의 한계 세장비는 22 이다."""
    assert slenderness_limit(braced=False) == pytest.approx(22.0)


def test_flexural_stiffness_simple():
    """간편식 EI = 0.4*Ec*Ig/(1+beta_dns) 를 확인한다."""
    ei = flexural_stiffness(e_c=26702, i_g=5.2e9, beta_dns=0.6)

    assert ei == pytest.approx(0.4 * 26702 * 5.2e9 / 1.6)


def test_flexural_stiffness_detailed():
    """정밀식이 철근 기여를 포함하는지 확인한다."""
    ei_simple = flexural_stiffness(e_c=26702, i_g=5.2e9, beta_dns=0.6)
    ei_detailed = flexural_stiffness(
        e_c=26702, i_g=5.2e9, beta_dns=0.6, e_s=200e3, i_se=1.5e8
    )

    assert ei_detailed == pytest.approx(
        (0.2 * 26702 * 5.2e9 + 200e3 * 1.5e8) / 1.6
    )
    assert ei_detailed > 0
    assert ei_simple > 0


def test_flexural_stiffness_sustained_load():
    """지속하중 비가 클수록 EI 가 작아진다."""
    ei_low = flexural_stiffness(e_c=26702, i_g=5.2e9, beta_dns=0.2)
    ei_high = flexural_stiffness(e_c=26702, i_g=5.2e9, beta_dns=0.8)

    assert ei_high < ei_low


def test_critical_buckling_load():
    """임계좌굴하중 Pc = pi^2*EI/(k*lu)^2 를 확인한다."""
    ei = 1.0e14
    p_c = critical_buckling_load(ei=ei, k=1.0, l_u=4000)

    assert p_c == pytest.approx(np.pi**2 * ei / 4000**2)

    with pytest.raises(ValueError, match="k"):
        critical_buckling_load(ei=ei, k=0, l_u=4000)


def test_moment_magnifier():
    """모멘트확대계수를 손계산과 대조한다."""
    p_u = 3000e3
    p_c = 8000e3

    c_m, delta = moment_magnifier_braced(p_u=p_u, p_c=p_c, m1=50, m2=100)

    assert c_m == pytest.approx(0.6 + 0.4 * 0.5)
    assert delta == pytest.approx(c_m / (1 - p_u / (PHI_K * p_c)))
    assert delta == pytest.approx(1.6)


def test_moment_magnifier_floored():
    """식의 값이 1.0 미만이면 1.0 으로 올린다."""
    p_u = 1000e3
    p_c = 8000e3

    c_m, delta = moment_magnifier_braced(p_u=p_u, p_c=p_c, m1=50, m2=100)

    assert c_m / (1 - p_u / (PHI_K * p_c)) < 1.0
    assert delta == pytest.approx(1.0)


def test_moment_magnifier_minimum_one():
    """확대계수는 1.0 이상이다."""
    _, delta = moment_magnifier_braced(p_u=10e3, p_c=1e9, m1=-100, m2=100)

    assert delta == pytest.approx(1.0)


def test_moment_magnifier_cm_floor():
    """Cm 은 0.4 이상이다."""
    c_m, _ = moment_magnifier_braced(p_u=100e3, p_c=1e7, m1=-100, m2=100)

    assert c_m == pytest.approx(0.4)


def test_moment_magnifier_transverse_load():
    """횡하중이 있으면 Cm = 1.0 이다."""
    c_m, _ = moment_magnifier_braced(
        p_u=100e3, p_c=1e7, m1=50, m2=100, transverse_load=True
    )

    assert c_m == pytest.approx(1.0)


def test_moment_magnifier_buckling():
    """Pu >= 0.75Pc 이면 예외가 발생한다."""
    with pytest.raises(ValueError, match="좌굴"):
        moment_magnifier_braced(p_u=8000e3, p_c=8000e3, m1=0, m2=100)


def test_minimum_moment():
    """최소 편심 모멘트 M2,min = Pu(15 + 0.03h) 를 확인한다."""
    assert minimum_moment(p_u=1000e3, h=500) == pytest.approx(1000e3 * (15 + 15))


def test_check_slenderness_short_column():
    """단주는 세장효과를 무시하고 Mc = M2 가 된다."""
    res = check_slenderness(
        p_u=1500e3,
        m1=0,
        m2=200e6,
        k=1.0,
        l_u=3000,
        h=500,
        e_c=26702,
        i_g=500.0**4 / 12,
    )

    assert res.slenderness == pytest.approx(3000 / 150)
    assert not res.slender
    assert res.delta_ns == pytest.approx(1.0)
    assert res.m_c == pytest.approx(max(200e6, res.m2_min))


def test_check_slenderness_slender_column():
    """장주는 모멘트가 확대된다."""
    res = check_slenderness(
        p_u=1500e3,
        m1=100e6,
        m2=200e6,
        k=1.0,
        l_u=8000,
        h=500,
        e_c=26702,
        i_g=500.0**4 / 12,
    )

    assert res.slender
    assert res.delta_ns > 1.0
    assert res.m_c == pytest.approx(res.delta_ns * res.m2)


def test_check_slenderness_minimum_moment_governs():
    """단부 모멘트가 작으면 최소 편심 모멘트가 지배한다."""
    res = check_slenderness(
        p_u=2000e3,
        m1=0,
        m2=1e6,
        k=1.0,
        l_u=3000,
        h=500,
        e_c=26702,
        i_g=500.0**4 / 12,
    )

    assert res.m2 == pytest.approx(res.m2_min)
    assert res.m2_min == pytest.approx(2000e3 * 30)


def test_check_slenderness_unbraced_more_slender():
    """비횡구속 골조는 한계 세장비가 낮아 더 쉽게 장주가 된다."""
    kwargs = {
        "p_u": 1500e3,
        "m1": 0,
        "m2": 200e6,
        "k": 1.0,
        "l_u": 4000,
        "h": 500,
        "e_c": 26702,
        "i_g": 500.0**4 / 12,
    }

    braced = check_slenderness(**kwargs, braced=True)
    unbraced = check_slenderness(**kwargs, braced=False)

    assert braced.limit == pytest.approx(34.0)
    assert unbraced.limit == pytest.approx(22.0)
    assert not braced.slender
    assert unbraced.slender
