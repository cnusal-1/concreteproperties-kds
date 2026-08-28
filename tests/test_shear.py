"""전단·비틀림 검증 시험 (KDS 14 20 22)."""

from __future__ import annotations

import numpy as np
import pytest

from concreteproperties_kds.shear import (
    PHI_SHEAR,
    check_shear,
    check_torsion_section,
    concrete_shear_strength,
    cracking_torque,
    longitudinal_torsion_reinforcement,
    max_shear_reinforcement_strength,
    max_stirrup_spacing,
    minimum_shear_reinforcement,
    required_stirrup_spacing,
    shear_reinforcement_strength,
    torsion_negligible,
    torsional_strength,
)

FCK = 27.0
B_W = 400.0
D = 550.0


def test_phi_shear():
    """전단의 강도감소계수는 0.75 이다."""
    assert PHI_SHEAR == pytest.approx(0.75)  # noqa: SIM300


def test_concrete_shear_simple():
    """간편식 Vc = (1/6)*lambda*sqrt(fck)*bw*d 를 확인한다."""
    v_c = concrete_shear_strength(fck=FCK, b_w=B_W, d=D)

    assert v_c == pytest.approx(np.sqrt(FCK) * B_W * D / 6.0)


def test_concrete_shear_lightweight():
    """경량콘크리트계수가 선형으로 적용되는지 확인한다."""
    v_full = concrete_shear_strength(fck=FCK, b_w=B_W, d=D)
    v_light = concrete_shear_strength(fck=FCK, b_w=B_W, d=D, lambda_c=0.75)

    assert v_light == pytest.approx(0.75 * v_full)


def test_concrete_shear_detailed_capped():
    """상세식이 0.29*lambda*sqrt(fck)*bw*d 로 제한되는지 확인한다."""
    # Vu*d/Mu 를 1.0 으로 만들고 철근비를 크게 하여 상한을 넘긴다
    v_c = concrete_shear_strength(
        fck=FCK, b_w=B_W, d=D, rho_w=0.06, v_u=1e6, m_u=1e6 * D
    )

    assert v_c == pytest.approx(0.29 * np.sqrt(FCK) * B_W * D)


def test_concrete_shear_detailed_within_bounds():
    """상세식의 결과가 0 과 상한 사이에 있는지 확인한다."""
    v_detailed = concrete_shear_strength(
        fck=FCK, b_w=B_W, d=D, rho_w=0.01, v_u=200e3, m_u=300e6
    )

    assert v_detailed > 0
    assert v_detailed <= 0.29 * np.sqrt(FCK) * B_W * D


def test_axial_compression_increases_vc():
    """압축 축력은 Vc 를 증가시킨다."""
    a_g = B_W * 600.0
    v_0 = concrete_shear_strength(fck=FCK, b_w=B_W, d=D)
    v_c = concrete_shear_strength(
        fck=FCK, b_w=B_W, d=D, n_u=500e3, a_g=a_g
    )

    assert v_c == pytest.approx(v_0 * (1.0 + 500e3 / (14.0 * a_g)))
    assert v_c > v_0


def test_axial_tension_reduces_vc():
    """인장 축력은 Vc 를 감소시키며, 과대하면 0 이 된다."""
    a_g = B_W * 600.0
    v_c = concrete_shear_strength(
        fck=FCK, b_w=B_W, d=D, n_u=-200e3, a_g=a_g
    )
    v_0 = concrete_shear_strength(fck=FCK, b_w=B_W, d=D)

    assert v_c < v_0

    v_zero = concrete_shear_strength(
        fck=FCK, b_w=B_W, d=D, n_u=-10e6, a_g=a_g
    )
    assert v_zero == pytest.approx(0.0)


def test_axial_without_area_raises():
    """축력을 주면서 단면적을 주지 않으면 예외가 발생한다."""
    with pytest.raises(ValueError, match="a_g"):
        concrete_shear_strength(fck=FCK, b_w=B_W, d=D, n_u=100e3)


def test_shear_reinforcement_vertical():
    """수직스터럽의 Vs = Av*fyt*d/s 를 확인한다."""
    v_s = shear_reinforcement_strength(a_v=253.4, fyt=400, d=D, s=200)

    assert v_s == pytest.approx(253.4 * 400 * D / 200)


def test_shear_reinforcement_inclined():
    """45도 경사스터럽은 수직스터럽보다 강하다."""
    v_vertical = shear_reinforcement_strength(a_v=253.4, fyt=400, d=D, s=200)
    v_incline = shear_reinforcement_strength(
        a_v=253.4, fyt=400, d=D, s=200, alpha=45
    )

    assert v_incline == pytest.approx(np.sqrt(2.0) * v_vertical)


def test_shear_reinforcement_zero_spacing():
    """간격이 0 이면 예외가 발생한다."""
    with pytest.raises(ValueError, match="s"):
        shear_reinforcement_strength(a_v=253.4, fyt=400, d=D, s=0)


def test_max_shear_reinforcement():
    """Vs 상한 = (2/3)*sqrt(fck)*bw*d 를 확인한다."""
    assert max_shear_reinforcement_strength(fck=FCK, b_w=B_W, d=D) == pytest.approx(
        2.0 / 3.0 * np.sqrt(FCK) * B_W * D
    )


def test_minimum_shear_reinforcement():
    """최소 전단철근량을 확인한다."""
    a_v_min = minimum_shear_reinforcement(fck=FCK, b_w=B_W, s=200, fyt=400)

    assert a_v_min == pytest.approx(
        max(0.0625 * np.sqrt(FCK), 0.35) * B_W * 200 / 400
    )
    # fck = 27 에서는 0.35 가 지배
    assert a_v_min == pytest.approx(0.35 * B_W * 200 / 400)

    # 고강도에서는 0.0625*sqrt(fck) 가 지배
    a_v_high = minimum_shear_reinforcement(fck=60, b_w=B_W, s=200, fyt=400)
    assert a_v_high == pytest.approx(0.0625 * np.sqrt(60) * B_W * 200 / 400)


def test_max_stirrup_spacing():
    """Vs 크기에 따른 최대 간격 규정을 확인한다."""
    threshold = np.sqrt(FCK) * B_W * D / 3.0

    s_wide = max_stirrup_spacing(fck=FCK, b_w=B_W, d=D, v_s=0.5 * threshold)
    s_close = max_stirrup_spacing(fck=FCK, b_w=B_W, d=D, v_s=1.5 * threshold)

    assert s_wide == pytest.approx(min(D / 2, 600.0))
    assert s_close == pytest.approx(min(D / 4, 300.0))

    # 깊은 부재에서는 절대 상한이 지배
    assert max_stirrup_spacing(
        fck=FCK, b_w=B_W, d=2000, v_s=0.0
    ) == pytest.approx(600.0)


def test_check_shear_ok():
    """전단 검토가 통과하는 경우를 확인한다."""
    res = check_shear(
        v_u=250e3, fck=FCK, b_w=B_W, d=D, a_v=2 * 126.7, s=200, fyt=400
    )

    assert res.ok
    assert res.stirrup_required
    assert res.phi_v_n == pytest.approx(PHI_SHEAR * (res.v_c + res.v_s))


def test_check_shear_fails():
    """요구 전단력이 크면 불만족으로 판정된다."""
    res = check_shear(
        v_u=900e3, fck=FCK, b_w=B_W, d=D, a_v=2 * 126.7, s=300, fyt=400
    )

    assert not res.ok
    assert not res.ok_strength


def test_stirrup_not_required():
    """Vu <= phi*Vc/2 이면 전단철근이 불필요하다."""
    v_c = concrete_shear_strength(fck=FCK, b_w=B_W, d=D)
    res = check_shear(v_u=0.4 * PHI_SHEAR * v_c, fck=FCK, b_w=B_W, d=D)

    assert not res.stirrup_required
    assert res.ok


def test_required_stirrup_spacing():
    """계산된 간격으로 배치하면 강도 조건을 만족한다."""
    s = required_stirrup_spacing(
        v_u=350e3, fck=FCK, b_w=B_W, d=D, a_v=2 * 126.7, fyt=400
    )

    assert s > 0
    res = check_shear(
        v_u=350e3, fck=FCK, b_w=B_W, d=D, a_v=2 * 126.7, s=s, fyt=400
    )
    assert res.ok


def test_required_stirrup_spacing_no_stirrup():
    """전단철근이 불필요하면 inf 를 반환한다."""
    v_c = concrete_shear_strength(fck=FCK, b_w=B_W, d=D)
    s = required_stirrup_spacing(
        v_u=0.3 * PHI_SHEAR * v_c, fck=FCK, b_w=B_W, d=D, a_v=253.4
    )

    assert s == float("inf")


def test_required_stirrup_spacing_section_too_small():
    """전단철근으로도 부족하면 예외가 발생한다."""
    with pytest.raises(ValueError, match="단면"):
        required_stirrup_spacing(
            v_u=3000e3, fck=FCK, b_w=B_W, d=D, a_v=253.4, fyt=400
        )


def test_cracking_torque():
    """균열 비틀림모멘트를 확인한다."""
    a_cp = 400.0 * 600.0
    p_cp = 2 * (400.0 + 600.0)

    t_cr = cracking_torque(fck=FCK, a_cp=a_cp, p_cp=p_cp)

    assert t_cr == pytest.approx(np.sqrt(FCK) / 3.0 * a_cp**2 / p_cp)


def test_torsion_negligible():
    """비틀림 무시 판정 경계를 확인한다."""
    a_cp = 400.0 * 600.0
    p_cp = 2 * (400.0 + 600.0)
    t_cr = cracking_torque(fck=FCK, a_cp=a_cp, p_cp=p_cp)
    limit = PHI_SHEAR * t_cr / 4.0

    assert torsion_negligible(t_u=0.9 * limit, fck=FCK, a_cp=a_cp, p_cp=p_cp)
    assert not torsion_negligible(t_u=1.1 * limit, fck=FCK, a_cp=a_cp, p_cp=p_cp)


def test_torsional_strength():
    """비틀림강도 Tn = 2*Ao*At*fyt*cot(theta)/s 를 확인한다."""
    a_oh = 320.0 * 520.0
    t_n = torsional_strength(a_t=126.7, s=150, a_oh=a_oh, fyt=400)

    assert t_n == pytest.approx(2 * 0.85 * a_oh * 126.7 * 400 / 150)


def test_longitudinal_torsion_reinforcement():
    """종방향 비틀림철근량을 확인한다."""
    p_h = 2 * (320.0 + 520.0)
    a_l = longitudinal_torsion_reinforcement(
        a_t=126.7, s=150, p_h=p_h, fyt=400, fy=400
    )

    assert a_l == pytest.approx(126.7 / 150 * p_h)


def test_torsion_section_check():
    """전단+비틀림 단면 크기 검토를 확인한다."""
    a_oh = 320.0 * 520.0
    p_h = 2 * (320.0 + 520.0)

    demand, capacity, ok = check_torsion_section(
        v_u=200e3, t_u=20e6, fck=FCK, b_w=B_W, d=D, a_oh=a_oh, p_h=p_h
    )

    assert demand > 0
    assert capacity > 0
    assert ok

    # 과대 비틀림
    _, _, ok_big = check_torsion_section(
        v_u=200e3, t_u=500e6, fck=FCK, b_w=B_W, d=D, a_oh=a_oh, p_h=p_h
    )
    assert not ok_big
