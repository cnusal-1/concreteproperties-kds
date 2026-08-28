"""2축 휨 간략식 검증 시험."""

from __future__ import annotations

import pytest

from concreteproperties_kds.biaxial import (
    bresler_reciprocal,
    check_bresler_reciprocal,
    check_load_contour,
    compare_with_exact,
    load_contour,
)


def test_bresler_reciprocal():
    """역하중법의 식을 손계산과 대조한다."""
    p_n = bresler_reciprocal(p_nx=2000e3, p_ny=1500e3, p_o=5000e3)

    assert p_n == pytest.approx(1.0 / (1 / 2000e3 + 1 / 1500e3 - 1 / 5000e3))
    # 2축 휨 강도는 각 1축 강도보다 작다
    assert p_n < 1500e3


def test_bresler_reciprocal_invalid():
    """0 이하의 입력은 예외가 발생한다."""
    with pytest.raises(ValueError, match="p_nx"):
        bresler_reciprocal(p_nx=0, p_ny=1500e3, p_o=5000e3)

    with pytest.raises(ValueError, match="역수"):
        bresler_reciprocal(p_nx=5000e3, p_ny=5000e3, p_o=1000e3)


def test_load_contour_alpha_one():
    """alpha = 1.0 은 직선 상관이다."""
    value = load_contour(m_ux=100e6, m_uy=100e6, m_nx=200e6, m_ny=200e6, alpha=1.0)

    assert value == pytest.approx(1.0)


def test_load_contour_alpha_two():
    """alpha = 2.0 은 alpha = 1.0 보다 여유가 크다."""
    v1 = load_contour(m_ux=100e6, m_uy=100e6, m_nx=200e6, m_ny=200e6, alpha=1.0)
    v2 = load_contour(m_ux=100e6, m_uy=100e6, m_nx=200e6, m_ny=200e6, alpha=2.0)

    assert v2 < v1


def test_load_contour_sign():
    """모멘트의 부호는 결과에 영향을 주지 않는다."""
    v_pos = load_contour(m_ux=100e6, m_uy=80e6, m_nx=200e6, m_ny=150e6)
    v_neg = load_contour(m_ux=-100e6, m_uy=-80e6, m_nx=200e6, m_ny=150e6)

    assert v_pos == pytest.approx(v_neg)


def test_load_contour_invalid():
    """강도가 0 이하이면 예외가 발생한다."""
    with pytest.raises(ValueError, match="m_nx"):
        load_contour(m_ux=1, m_uy=1, m_nx=0, m_ny=1)


def test_check_load_contour():
    """등하중선법 검토 결과를 확인한다."""
    res = check_load_contour(
        m_ux=100e6, m_uy=60e6, phi_m_nx=250e6, phi_m_ny=250e6
    )

    assert res.ok
    assert res.ratio == pytest.approx(100 / 250 + 60 / 250)

    res_ng = check_load_contour(
        m_ux=200e6, m_uy=150e6, phi_m_nx=250e6, phi_m_ny=250e6
    )
    assert not res_ng.ok


def test_check_bresler_reciprocal():
    """역하중법 검토와 적용 범위 경고를 확인한다."""
    res = check_bresler_reciprocal(
        p_u=800e3, phi_p_nx=2000e3, phi_p_ny=1500e3, phi_p_o=5000e3
    )

    assert res.ok
    assert res.note == ""

    # 적용 범위 밖 (Pu < 0.1*fck*Ag)
    res_low = check_bresler_reciprocal(
        p_u=100e3,
        phi_p_nx=2000e3,
        phi_p_ny=1500e3,
        phi_p_o=5000e3,
        fck=27,
        a_g=250000,
    )
    assert "적용 범위" in res_low.note


def test_compare_with_exact():
    """alpha 가 커질수록 등하중선법 값이 작아진다."""
    results = compare_with_exact(
        m_ux=100e6,
        m_uy=100e6,
        phi_m_nx=200e6,
        phi_m_ny=200e6,
        exact_ratio=0.85,
    )

    values = [v for _, v, _ in results]
    assert values == sorted(values, reverse=True)

    # alpha = 1.0 은 엄밀해보다 보수적
    assert results[0][2] is True
