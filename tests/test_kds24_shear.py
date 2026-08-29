"""KDS 24 14 21 4.1.2 전단 시험.

값은 식 (4.1-7) ~ 식 (4.1-23), 식 (4.6-7), 식 (4.6-8) 과 대조하고, 같은 단면을
KDS 14 20 22 로도 풀어 두 기준의 차이를 고정한다.
"""

from __future__ import annotations

import math

import pytest

from concreteproperties_kds.kds24 import (
    COT_THETA_MAX,
    COT_THETA_MIN,
    PHI_C_ULS,
    PHI_S_ULS,
    alpha_cw,
    axial_stress,
    characteristic_tensile_strength,
    check_shear,
    concrete_shear_strength,
    design_concrete_shear_strength,
    kappa,
    max_shear_strength,
    maximum_shear_reinforcement,
    maximum_stirrup_spacing,
    minimum_concrete_shear_strength,
    minimum_shear_reinforcement_ratio,
    nu,
    required_stirrup_spacing,
    shear_reinforcement_strength,
    uncracked_shear_strength,
)
from concreteproperties_kds.shear import (
    concrete_shear_strength as v_c_kds14,
)

# 400 x 700 단면, 유효깊이 640 mm, 인장철근 4-D25 (2,026.8 mm2)
FCK = 40.0
B_W = 400.0
D = 640.0
A_S = 2026.8


def test_kappa_size_effect():
    """kappa = 1 + sqrt(200/d) <= 2.0."""
    assert kappa(d=200.0) == pytest.approx(2.0)
    assert kappa(d=100.0) == pytest.approx(2.0)  # 상한
    assert kappa(d=800.0) == pytest.approx(1.0 + math.sqrt(0.25))
    assert kappa(d=2000.0) == pytest.approx(1.0 + math.sqrt(0.1))

    with pytest.raises(ValueError, match="d"):
        kappa(d=0.0)


def test_nu_decreases_with_strength():
    """식 (4.1-12) — nu = 0.6(1 - fck/250)."""
    assert nu(fck=0.0) == pytest.approx(0.6)
    assert nu(fck=40.0) == pytest.approx(0.6 * 0.84)
    assert nu(fck=60.0) == pytest.approx(0.6 * 0.76)
    assert nu(fck=60.0) < nu(fck=40.0)


def test_concrete_shear_strength_is_hand_checkable():
    """식 (4.1-7) 을 손으로 따라간다."""
    rho = A_S / (B_W * D)
    k = 1.0 + math.sqrt(200.0 / D)
    hand = 0.85 * PHI_C_ULS * k * (rho * FCK) ** (1 / 3) * B_W * D

    assert rho == pytest.approx(0.007917, abs=1e-6)
    assert concrete_shear_strength(fck=FCK, b_w=B_W, d=D, a_s=A_S) == pytest.approx(
        hand
    )


def test_reinforcement_ratio_is_capped_at_two_percent():
    """4.1.2.2(1) — rho <= 0.02."""
    heavy = concrete_shear_strength(fck=FCK, b_w=B_W, d=D, a_s=0.02 * B_W * D)
    heavier = concrete_shear_strength(fck=FCK, b_w=B_W, d=D, a_s=0.10 * B_W * D)

    assert heavy == pytest.approx(heavier)


def test_minimum_strength_is_a_floor():
    """식 (4.1-8) 은 철근비가 아주 작을 때 걸린다."""
    tiny = 1.0
    v_cd = concrete_shear_strength(fck=FCK, b_w=B_W, d=D, a_s=tiny)
    v_min = minimum_concrete_shear_strength(fck=FCK, b_w=B_W, d=D)

    assert v_min > v_cd
    assert design_concrete_shear_strength(
        fck=FCK, b_w=B_W, d=D, a_s=tiny
    ) == pytest.approx(v_min)

    hand = 0.4 * PHI_C_ULS * characteristic_tensile_strength(fck=FCK) * B_W * D

    assert v_min == pytest.approx(hand)


def test_axial_compression_helps_and_is_capped():
    """f_n = N_u/A_c <= 0.2 phi_c f_ck."""
    a_c = B_W * 700.0

    assert axial_stress(n_u=1.0e6, a_c=a_c, fck=FCK) == pytest.approx(1.0e6 / a_c)
    # 상한에 걸리는 큰 축력
    assert axial_stress(n_u=1.0e9, a_c=a_c, fck=FCK) == pytest.approx(
        0.2 * PHI_C_ULS * FCK
    )

    with_axial = concrete_shear_strength(fck=FCK, b_w=B_W, d=D, a_s=A_S, f_n=2.0)
    without = concrete_shear_strength(fck=FCK, b_w=B_W, d=D, a_s=A_S)

    assert with_axial - without == pytest.approx(0.15 * 2.0 * B_W * D)


def test_strut_limit_peaks_at_45_degrees():
    r"""식 (4.1-17) — :math:`V_{d,max}` 는 :math:`\cot\theta = 1` 에서 최대다.

    철근을 아끼려 스트럿을 눕히면(cot theta 를 키우면) 복부 압축 한계가 낮아진다.
    변각 트러스 모델의 두 요구가 반대로 움직인다는 것이 이 시험의 요지다.
    """
    at_45 = max_shear_strength(fck=FCK, b_w=B_W, d=D, cot_theta=1.0)
    at_flat = max_shear_strength(fck=FCK, b_w=B_W, d=D, cot_theta=2.5)

    assert at_45 > at_flat
    assert at_flat / at_45 == pytest.approx(2.0 / (2.5 + 0.4), rel=1e-6)

    hand = nu(fck=FCK) * PHI_C_ULS * FCK * B_W * (0.9 * D) / 2.0

    assert at_45 == pytest.approx(hand)


def test_stirrup_strength_grows_with_cot_theta():
    """식 (4.1-16) — 스트럿을 눕히면 스터럽 기여가 커진다."""
    a_v = 2 * 126.7  # D13 2 가닥
    steep = shear_reinforcement_strength(
        f_vy=400.0, a_v=a_v, d=D, s=200.0, cot_theta=1.0
    )
    flat = shear_reinforcement_strength(
        f_vy=400.0, a_v=a_v, d=D, s=200.0, cot_theta=2.5
    )

    assert flat / steep == pytest.approx(2.5)

    hand = PHI_S_ULS * 400.0 * a_v * (0.9 * D) / 200.0

    assert steep == pytest.approx(hand)


def test_cot_theta_range_is_enforced():
    """식 (4.1-15) — 1 <= cot theta <= 2.5."""
    assert pytest.approx(1.0) == COT_THETA_MIN
    assert pytest.approx(2.5) == COT_THETA_MAX

    for bad in (0.9, 2.6):
        with pytest.raises(ValueError, match="cot_theta"):
            max_shear_strength(fck=FCK, b_w=B_W, d=D, cot_theta=bad)

        with pytest.raises(ValueError, match="cot_theta"):
            shear_reinforcement_strength(
                f_vy=400.0, a_v=250.0, d=D, s=200.0, cot_theta=bad
            )


def test_alpha_cw_branches():
    """식 (4.1-23a), (4.1-23b), (4.1-23c)."""
    f_cd = PHI_C_ULS * FCK

    assert alpha_cw(f_n=0.0, fck=FCK) == pytest.approx(1.0)
    assert alpha_cw(f_n=0.10 * f_cd, fck=FCK) == pytest.approx(1.10)
    assert alpha_cw(f_n=0.25 * f_cd, fck=FCK) == pytest.approx(1.25)
    assert alpha_cw(f_n=0.40 * f_cd, fck=FCK) == pytest.approx(1.25)
    assert alpha_cw(f_n=0.75 * f_cd, fck=FCK) == pytest.approx(0.625)
    assert alpha_cw(f_n=1.00 * f_cd, fck=FCK) == pytest.approx(0.0)


def test_detailing_limits():
    """식 (4.6-7), 식 (4.6-8), 식 (4.1-18)."""
    assert minimum_shear_reinforcement_ratio(fck=FCK, f_y=400.0) == pytest.approx(
        0.08 * math.sqrt(40.0) / 400.0
    )
    assert maximum_stirrup_spacing(d=D) == pytest.approx(0.75 * D)
    assert maximum_stirrup_spacing(d=D, alpha=45.0) == pytest.approx(1.5 * D)

    a_v_max = maximum_shear_reinforcement(fck=FCK, b_w=B_W, s=200.0, f_y=400.0)

    assert PHI_S_ULS * 400.0 * a_v_max / (B_W * 200.0) == pytest.approx(
        0.5 * nu(fck=FCK) * PHI_C_ULS * FCK
    )


def test_required_spacing_round_trips():
    """요구 간격을 다시 넣으면 그 전단력이 나온다."""
    a_v = 2 * 126.7
    v_ed = 600.0e3

    s = required_stirrup_spacing(v_ed=v_ed, d=D, a_v=a_v)

    assert shear_reinforcement_strength(f_vy=400.0, a_v=a_v, d=D, s=s) == pytest.approx(
        v_ed
    )

    with pytest.raises(ValueError, match="v_ed"):
        required_stirrup_spacing(v_ed=0.0, d=D, a_v=a_v)


def test_check_shear_without_stirrups():
    """전단철근이 없으면 V_cd 가 곧 강도다."""
    v_cd = design_concrete_shear_strength(fck=FCK, b_w=B_W, d=D, a_s=A_S)

    ok = check_shear(v_ed=0.9 * v_cd, fck=FCK, b_w=B_W, d=D, a_s=A_S)
    ng = check_shear(v_ed=1.1 * v_cd, fck=FCK, b_w=B_W, d=D, a_s=A_S)

    assert ok.adequate
    assert not ok.stirrups_required
    assert ng.stirrups_required
    assert not ng.adequate
    assert ng.ratio == pytest.approx(1.1)


def test_check_shear_does_not_add_concrete_to_stirrups():
    """전단철근이 있으면 V_cd 를 더하지 않는다.

    이것이 KDS 14 (:math:`\\phi(V_c + V_s)`) 와 가장 크게 다른 점이다.
    """
    a_v = 2 * 126.7
    s = 200.0
    v_sd = shear_reinforcement_strength(f_vy=400.0, a_v=a_v, d=D, s=s)

    result = check_shear(v_ed=v_sd, fck=FCK, b_w=B_W, d=D, a_s=A_S, a_v=a_v, s=s)

    assert result.v_sd == pytest.approx(v_sd)
    assert result.ratio == pytest.approx(1.0)
    assert result.v_cd > 0  # 계산되긴 하지만 강도에 더해지지 않는다


def test_strut_limit_caps_heavy_stirrups():
    """스터럽을 아무리 촘촘히 해도 V_d,max 를 넘지 못한다."""
    result = check_shear(
        v_ed=1.0,
        fck=FCK,
        b_w=B_W,
        d=D,
        a_s=A_S,
        a_v=4 * 126.7,
        s=50.0,
        cot_theta=2.5,
    )

    assert result.v_sd > result.v_d_max

    heavy = check_shear(
        v_ed=result.v_d_max * 1.01,
        fck=FCK,
        b_w=B_W,
        d=D,
        a_s=A_S,
        a_v=4 * 126.7,
        s=50.0,
    )

    assert not heavy.adequate


def test_uncracked_prestressed_strength():
    """식 (4.1-9) — 프리스트레스가 클수록 강도가 커진다."""
    kwargs = {
        "fck": FCK,
        "b_w": B_W,
        "second_moment": 1.14e10,
        "first_moment": 2.45e7,
    }

    low = uncracked_shear_strength(f_n=2.0, **kwargs)
    high = uncracked_shear_strength(f_n=8.0, **kwargs)

    assert high > low

    f_ctd = PHI_C_ULS * characteristic_tensile_strength(fck=FCK)
    hand = 1.14e10 * B_W / 2.45e7 * math.sqrt(f_ctd**2 + 2.0 * f_ctd)

    assert low == pytest.approx(hand)


def test_kds24_shear_versus_kds14():
    """같은 단면을 두 기준으로 풀어 차이를 고정한다.

    400 x 700, d = 640 mm, fck 40 MPa 에서

    * KDS 14 20 22 — :math:`\\phi V_c = 0.75 \\times \\tfrac{1}{6}\\sqrt{40}\\,
      b_w d = 202.4` kN. 철근비와 무관하다.
    * KDS 24 14 21 — 철근비가 1.2 % 아래면 식 (4.1-8) 의 하한 174.2 kN 이
      지배하고(KDS 14 의 86 %), 철근비 상한 2 % 에서야 204.7 kN 으로
      KDS 14 를 겨우 넘어선다.

    KDS 24 가 철근비를 보상하는 대신 전체 수준을 낮게 잡았다는 뜻이다. 대신
    전단철근이 들어가면 :math:`\\cot\\theta` 를 2.5 까지 눕혀 그 몫을 되찾는다.
    """
    phi_v_c = 0.75 * v_c_kds14(fck=FCK, b_w=B_W, d=D)

    assert phi_v_c == pytest.approx(202.4e3, rel=0.01)

    lightly = design_concrete_shear_strength(fck=FCK, b_w=B_W, d=D, a_s=A_S)
    heavily = design_concrete_shear_strength(fck=FCK, b_w=B_W, d=D, a_s=0.02 * B_W * D)

    # 통상적인 철근비에서는 식 (4.1-8) 의 하한이 지배한다
    assert lightly == pytest.approx(
        minimum_concrete_shear_strength(fck=FCK, b_w=B_W, d=D)
    )
    assert lightly / phi_v_c == pytest.approx(0.861, abs=0.01)

    # 철근비 상한에서야 KDS 14 를 넘어선다
    assert heavily / phi_v_c == pytest.approx(1.011, abs=0.01)


def test_stirrups_recover_the_difference():
    """전단철근이 들어가면 KDS 24 쪽이 오히려 유리해진다.

    KDS 14 는 :math:`\\phi(V_c + V_s)` 로 콘크리트 몫을 더해 주지만
    :math:`V_s = A_v f_y d / s` 로 고정이다. KDS 24 는 콘크리트 몫을 버리는 대신
    :math:`\\cot\\theta = 2.5` 로 스터럽 효율을 2.5 배로 올린다.
    """
    a_v = 2 * 126.7
    s = 200.0
    f_y = 400.0

    v_24 = shear_reinforcement_strength(f_vy=f_y, a_v=a_v, d=D, s=s, cot_theta=2.5)
    v_14 = 0.75 * (v_c_kds14(fck=FCK, b_w=B_W, d=D) + a_v * f_y * D / s)

    assert v_24 > v_14
    assert v_24 / v_14 == pytest.approx(1.4, abs=0.15)
