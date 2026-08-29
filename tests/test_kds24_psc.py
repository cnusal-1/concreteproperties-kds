"""KDS 24 14 21 프리스트레스 규정 시험.

값은 KDS 24 14 21 원문(1.5.7 도입응력과 손실, 3.3 릴랙세이션)과 대조한다.
"""

from __future__ import annotations

import math

import pytest

from concreteproperties_kds.kds24 import (
    CURVATURE_FRICTION,
    E_P,
    RELAXATION_COEFFICIENTS,
    RHO_1000,
    PrestressLosses,
    anchorage_set_loss,
    concrete_stress_limit_at_transfer,
    elastic_shortening_loss,
    friction_loss,
    long_term_loss,
    max_jacking_stress,
    relaxation_loss,
    stress_after_transfer,
)

# SWPC 7B 15.2 mm 강연선 — f_pu 1860, f_py 1600 MPa
FPU = 1860.0
FPY = 1600.0


def test_max_jacking_stress():
    """식 (1.5-7) — f_o,max = min(0.8 f_pu, 0.9 f_py)."""
    # 0.8 x 1860 = 1488, 0.9 x 1600 = 1440 -> f_py 조건이 지배
    assert max_jacking_stress(fpu=FPU, fpy=FPY) == pytest.approx(1440.0)

    # f_py 가 높으면 f_pu 조건이 지배한다
    assert max_jacking_stress(fpu=1860.0, fpy=1750.0) == pytest.approx(1488.0)


def test_overtension_allowance():
    """초과 긴장은 0.95 f_py 까지 허용한다."""
    assert max_jacking_stress(fpu=FPU, fpy=FPY, overtension=True) == pytest.approx(
        0.95 * FPY
    )


def test_stress_after_transfer():
    """식 (1.5-9) — 도입 직후 f_pmo.

    원문은 두 계수를 모두 f_py 에 곱하므로 작은 쪽인 0.75 f_py 가 지배한다.
    """
    assert stress_after_transfer(fpy=FPY) == pytest.approx(1200.0)
    assert stress_after_transfer(fpy=FPY) < max_jacking_stress(fpu=FPU, fpy=FPY)


def test_concrete_stress_limit_at_transfer():
    """식 (1.5-8) — 포스트텐션 0.6 f_ck(t), 프리텐션 0.7 f_ck(t)."""
    assert concrete_stress_limit_at_transfer(fck_t=30.0) == pytest.approx(18.0)
    assert concrete_stress_limit_at_transfer(
        fck_t=30.0, pretension=True
    ) == pytest.approx(21.0)


def test_friction_loss_matches_formula():
    """식 (1.5-11) — dP = P_o (1 - e^(-(mu theta + k x)))."""
    p_o = 1.0e6  # N
    theta, x, mu, k = 0.12, 30.0, 0.19, 0.004
    expected = p_o * (1.0 - math.exp(-(mu * theta + k * x)))

    got = friction_loss(p_o=p_o, theta=theta, x=x, mu=mu, k=k)

    assert got == pytest.approx(expected)
    assert got / 1e3 == pytest.approx(133.1, abs=0.1)


def test_friction_loss_grows_with_length_and_angle():
    """마찰손실은 곡률각과 길이에 대해 단조증가한다."""
    base = friction_loss(p_o=1.0e6, theta=0.10, x=20.0)

    assert friction_loss(p_o=1.0e6, theta=0.20, x=20.0) > base
    assert friction_loss(p_o=1.0e6, theta=0.10, x=40.0) > base


def test_friction_loss_zero_without_curvature_or_length():
    """곡률과 길이가 없으면 마찰손실도 없다."""
    assert friction_loss(p_o=1.0e6, theta=0.0, x=0.0) == pytest.approx(0.0)


def test_curvature_friction_table():
    """표 1.5-2 — 긴장재 종류별·덕트 종류별 곡률마찰계수."""
    # 가장 흔한 조합: 강연선 + 비윤활 강재덕트
    assert CURVATURE_FRICTION["강연선"]["강재덕트_비윤활"] == pytest.approx(0.19)
    assert CURVATURE_FRICTION["냉간압연강선"]["강재덕트_비윤활"] == pytest.approx(0.17)

    # 강봉은 마찰이 훨씬 크고, 덕트 종류가 나뉘어 있지 않다
    assert CURVATURE_FRICTION["이형강봉"]["강재덕트_비윤활"] == pytest.approx(0.65)
    assert CURVATURE_FRICTION["원형강봉"]["강재덕트_비윤활"] == pytest.approx(0.33)

    # 강선·강연선은 윤활하면 마찰이 줄고, 비부착 외부 텐던이 가장 작다
    for kind in ("냉간압연강선", "강연선"):
        table = CURVATURE_FRICTION[kind]
        assert table["강재덕트_윤활"] < table["강재덕트_비윤활"], kind
        assert table["폴리에틸렌덕트_윤활"] < table["폴리에틸렌덕트_비윤활"], kind
        assert table["비부착외부"] == min(table.values()), kind


def test_anchorage_set_loss():
    """정착장치 활동 손실은 delta * E_p * A_p / L 이다."""
    slip, length, a_p = 6.0, 35_000.0, 4200.0
    expected = slip / length * E_P * a_p

    assert anchorage_set_loss(slip=slip, length=length, a_p=a_p) == pytest.approx(
        expected
    )


def test_elastic_shortening_post_tension_uses_half_factor():
    """식 (1.5-10) — 포스트텐션은 j = (n-1)/(2n) 을 곱한다.

    긴장재가 1개면 순차 긴장이 없으므로 탄성변형 손실이 0 이다.
    """
    kwargs = {"a_p": 4200.0, "delta_fc": 12.0, "e_cm": 30_000.0}

    assert elastic_shortening_loss(n_tendon=1, **kwargs) == pytest.approx(0.0)

    four = elastic_shortening_loss(n_tendon=4, **kwargs)
    many = elastic_shortening_loss(n_tendon=1000, **kwargs)

    # j 는 0 -> 0.5 로 수렴하므로 4개는 3/8, 무한대는 1/2 에 가깝다
    assert four == pytest.approx(3 / 8 * E_P / 30_000.0 * 12.0 * 4200.0)
    assert many == pytest.approx(0.5 * E_P / 30_000.0 * 12.0 * 4200.0, rel=1e-2)
    assert four < many


def test_elastic_shortening_pretension_is_full():
    """프리텐션은 전체 탄성변형이 손실이 된다 (j = 1)."""
    got = elastic_shortening_loss(
        a_p=4200.0, delta_fc=12.0, e_cm=30_000.0, post_tension=False
    )

    assert got == pytest.approx(E_P / 30_000.0 * 12.0 * 4200.0)


def test_relaxation_matches_hand_calculation():
    """식 (3.3-2) — 저릴랙세이션(2종) 강연선."""
    f_pi = 1300.0
    c, alpha = RELAXATION_COEFFICIENTS[2]
    mu = f_pi / FPU
    expected = (
        c
        * RHO_1000[2]
        * math.exp(alpha * mu)
        * (500_000.0 / 1000.0) ** (0.75 * (1.0 - mu))
        * 1e-5
        * f_pi
    )

    got = relaxation_loss(f_pi=f_pi, fpu=FPU, steel_class=2)

    assert got == pytest.approx(expected)
    assert got == pytest.approx(50.5, abs=0.1)


def test_relaxation_class_1_much_larger_than_class_2():
    """1종(보통 릴랙세이션)은 2종(저릴랙세이션)보다 손실이 훨씬 크다."""
    ordinary = relaxation_loss(f_pi=1300.0, fpu=FPU, steel_class=1)
    low = relaxation_loss(f_pi=1300.0, fpu=FPU, steel_class=2)

    assert ordinary == pytest.approx(246.5, abs=0.5)
    assert ordinary > 4.0 * low


def test_relaxation_grows_with_initial_stress():
    """초기 응력비 mu 가 커지면 릴랙세이션 손실도 커진다."""
    low = relaxation_loss(f_pi=1100.0, fpu=FPU)
    high = relaxation_loss(f_pi=1400.0, fpu=FPU)

    assert high > low


def test_relaxation_rejects_unknown_class():
    """1~3종 외의 강재 종류는 받지 않는다."""
    with pytest.raises(ValueError, match="릴랙세이션 등급"):
        relaxation_loss(f_pi=1300.0, fpu=FPU, steel_class=4)


def test_long_term_loss_components():
    """식 (1.5-12) — 건조수축·크리프·릴랙세이션의 합을 분모로 나눈다."""
    got = long_term_loss(
        eps_shrinkage=300e-6,
        delta_f_pr=50.0,
        phi_creep=2.0,
        f_c_permanent=-3.0,
        f_cpo=12.0,
        a_p=4200.0,
        a_c=0.927e6,
        i_c=0.4435e12,
        z_cp=911.0,
        e_cm=30_000.0,
    )

    # 분자는 세 성분의 합이므로 각 성분보다 크고, 분모(>1)로 나누므로 그보다 작다
    numerator = 300e-6 * E_P + 0.8 * 50.0 + E_P / 30_000.0 * 2.0 * 12.0
    assert 0.0 < got < numerator


def test_long_term_loss_relaxation_reduction():
    """릴랙세이션 성분에는 0.8 의 저감계수가 걸린다."""
    kwargs = {
        "eps_shrinkage": 0.0,
        "phi_creep": 0.0,
        "f_c_permanent": 0.0,
        "f_cpo": 0.0,
        "a_p": 4200.0,
        "a_c": 0.927e6,
        "i_c": 0.4435e12,
        "z_cp": 911.0,
        "e_cm": 30_000.0,
    }
    # 크리프·건조수축이 없으면 분자에는 0.8 * delta_f_pr 만 남는다.
    # 분모는 크리프가 0 이어도 단면 항이 남으므로 1 보다 크다.
    alpha = E_P / kwargs["e_cm"]
    denominator = 1.0 + alpha * kwargs["a_p"] / kwargs["a_c"] * (
        1.0 + kwargs["a_c"] / kwargs["i_c"] * kwargs["z_cp"] ** 2
    )

    assert long_term_loss(delta_f_pr=50.0, **kwargs) == pytest.approx(
        0.8 * 50.0 / denominator
    )
    assert long_term_loss(delta_f_pr=50.0, **kwargs) < 0.8 * 50.0


def test_long_term_loss_grows_with_creep():
    """크리프계수가 크면 장기손실도 커진다."""
    kwargs = {
        "eps_shrinkage": 300e-6,
        "delta_f_pr": 50.0,
        "f_c_permanent": -3.0,
        "f_cpo": 12.0,
        "a_p": 4200.0,
        "a_c": 0.927e6,
        "i_c": 0.4435e12,
        "z_cp": 911.0,
        "e_cm": 30_000.0,
    }

    assert long_term_loss(phi_creep=3.0, **kwargs) > long_term_loss(
        phi_creep=1.0, **kwargs
    )


def test_prestress_losses_ratios_are_consistent():
    """PrestressLosses 의 손실률이 응력값과 맞아야 한다."""
    losses = PrestressLosses(
        f_jack=1440.0,
        friction=80.0,
        anchorage=30.0,
        elastic=40.0,
        f_pi=1290.0,
        long_term=100.0,
        f_pe=1190.0,
        immediate_ratio=1.0 - 1290.0 / 1440.0,
        total_ratio=1.0 - 1190.0 / 1440.0,
    )

    assert losses.f_jack - losses.friction - losses.anchorage - losses.elastic == (
        pytest.approx(losses.f_pi)
    )
    assert losses.f_pi - losses.long_term == pytest.approx(losses.f_pe)
    assert losses.immediate_ratio < losses.total_ratio
    assert losses.total_ratio == pytest.approx(0.1736, abs=1e-4)


def test_stress_after_transfer_two_readings():
    """식 (1.5-9) 은 두 가지로 읽히고, 값이 크게 다르다.

    원문은 두 계수를 모두 f_py 에 곱하지만, 앞의 식 (1.5-7) 과 대응하는
    EN 1992-1-1 5.10.3(2) 는 인장강도와 항복강도를 짝짓는다.
    """
    literal = stress_after_transfer(fpy=FPY)
    en = stress_after_transfer(fpy=FPY, fpu=FPU, reading="EN")

    assert literal == pytest.approx(0.75 * FPY)  # 1200
    assert en == pytest.approx(min(0.75 * FPU, 0.85 * FPY))  # 1360
    assert literal < en


def test_literal_reading_conflicts_with_jacking_limit():
    """원문대로 읽으면 식 (1.5-9) 가 식 (1.5-7) 의 상한을 끌어내린다.

    긴장응력 1,440 MPa 에서 1,200 MPa 로 내려오려면 즉시손실이 16.7 % 를
    넘어야 하는데, 통상적인 포스트텐션 거더는 12 ~ 15 % 다.
    """
    f_jack = max_jacking_stress(fpu=FPU, fpy=FPY)
    literal = stress_after_transfer(fpy=FPY)

    required_loss = 1.0 - literal / f_jack

    assert required_loss == pytest.approx(0.1667, abs=1e-3)
    # EN 해석이면 훨씬 느슨하다
    en = stress_after_transfer(fpy=FPY, fpu=FPU, reading="EN")
    assert 1.0 - en / f_jack == pytest.approx(0.0556, abs=1e-3)


def test_stress_after_transfer_rejects_bad_reading():
    """읽는 방식은 두 가지뿐이고, EN 해석에는 f_pu 가 필요하다."""
    with pytest.raises(ValueError, match="reading"):
        stress_after_transfer(fpy=FPY, reading="아무거나")

    with pytest.raises(ValueError, match="fpu"):
        stress_after_transfer(fpy=FPY, reading="EN")
