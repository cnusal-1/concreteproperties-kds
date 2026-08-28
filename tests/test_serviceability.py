"""사용성 검증 시험 (KDS 14 20 30)."""

from __future__ import annotations

import numpy as np
import pytest

from concreteproperties_kds.serviceability import (
    DEFLECTION_LIMIT,
    KAPPA_CR_DRY,
    KAPPA_CR_OTHER,
    check_crack_control,
    check_deflection,
    cracking_moment,
    deflection_limit,
    deflection_target,
    effective_moment_of_inertia,
    long_term_deflection_factor,
    max_bar_spacing,
    minimum_thickness,
    service_steel_stress,
    shrinkage_temperature_reinforcement,
    total_deflection,
)

I_G = 7.2e9
I_CR = 2.2e9
M_CR = 88.4e6


def test_ie_uncracked():
    """Ma <= Mcr 이면 Ie = Ig 이다."""
    assert effective_moment_of_inertia(
        m_a=0.8 * M_CR, m_cr=M_CR, i_g=I_G, i_cr=I_CR
    ) == pytest.approx(I_G)
    assert effective_moment_of_inertia(
        m_a=M_CR, m_cr=M_CR, i_g=I_G, i_cr=I_CR
    ) == pytest.approx(I_G)


def test_ie_branson():
    """Branson 식을 손계산과 대조한다."""
    m_a = 2.0 * M_CR
    i_e = effective_moment_of_inertia(m_a=m_a, m_cr=M_CR, i_g=I_G, i_cr=I_CR)

    ratio = (M_CR / m_a) ** 3
    assert i_e == pytest.approx(ratio * I_G + (1 - ratio) * I_CR)
    assert I_CR < i_e < I_G


def test_ie_monotonic():
    """모멘트가 커질수록 Ie 는 Icr 로 수렴한다."""
    values = [
        effective_moment_of_inertia(m_a=r * M_CR, m_cr=M_CR, i_g=I_G, i_cr=I_CR)
        for r in [1.0, 1.5, 2.0, 3.0, 10.0]
    ]

    assert np.all(np.diff(values) <= 0)
    assert values[-1] == pytest.approx(I_CR, rel=1e-2)


def test_ie_negative_moment():
    """모멘트의 부호에 관계없이 절댓값으로 계산한다."""
    assert effective_moment_of_inertia(
        m_a=-2.0 * M_CR, m_cr=M_CR, i_g=I_G, i_cr=I_CR
    ) == pytest.approx(
        effective_moment_of_inertia(m_a=2.0 * M_CR, m_cr=M_CR, i_g=I_G, i_cr=I_CR)
    )


@pytest.mark.parametrize(
    ("duration", "xi"),
    [("3개월", 1.0), ("6개월", 1.2), ("12개월", 1.4), ("5년이상", 2.0)],
)
def test_long_term_factor(duration, xi):
    """장기처짐 계수 lambda = xi / (1 + 50*rho') 를 확인한다."""
    assert long_term_deflection_factor(duration=duration) == pytest.approx(xi)
    assert long_term_deflection_factor(
        rho_prime=0.01, duration=duration
    ) == pytest.approx(xi / 1.5)


def test_long_term_factor_invalid():
    """정의되지 않은 재하기간은 예외가 발생한다."""
    with pytest.raises(ValueError, match="duration"):
        long_term_deflection_factor(duration="10년")


def test_total_deflection():
    """전체 처짐 = 활하중 즉시 + 지속 즉시 + 장기추가 를 확인한다."""
    delta_lt, delta_total = total_deflection(
        delta_immediate_sustained=10.0, delta_immediate_live=5.0
    )

    assert delta_lt == pytest.approx(20.0)
    assert delta_total == pytest.approx(5.0 + 10.0 + 20.0)


@pytest.mark.parametrize(
    ("member", "support", "ratio"),
    [
        ("보", "단순지지", 16.0),
        ("보", "1단연속", 18.5),
        ("보", "양단연속", 21.0),
        ("보", "캔틸레버", 8.0),
        ("1방향슬래브", "단순지지", 20.0),
        ("1방향슬래브", "캔틸레버", 10.0),
    ],
)
def test_minimum_thickness(member, support, ratio):
    """최소 두께 표를 확인한다."""
    assert minimum_thickness(
        span=8000, member=member, support=support
    ) == pytest.approx(8000 / ratio)


def test_minimum_thickness_fy_correction():
    """fy != 400 이면 (0.43 + fy/700) 을 곱한다."""
    h_400 = minimum_thickness(span=8000, fy=400)
    h_500 = minimum_thickness(span=8000, fy=500)

    assert h_500 == pytest.approx(h_400 * (0.43 + 500 / 700))
    assert h_500 > h_400


def test_minimum_thickness_invalid():
    """정의되지 않은 부재·지지조건은 예외가 발생한다."""
    with pytest.raises(ValueError, match="member"):
        minimum_thickness(span=8000, member="2방향슬래브")

    with pytest.raises(ValueError, match="support"):
        minimum_thickness(span=8000, support="고정")


def test_deflection_limit():
    """허용처짐을 확인한다."""
    assert deflection_limit(span=8000, condition="바닥_비구조재없음") == pytest.approx(
        8000 / 360
    )
    assert deflection_limit(
        span=8000, condition="손상되기쉬운_비구조재"
    ) == pytest.approx(8000 / 480)

    with pytest.raises(ValueError, match="condition"):
        deflection_limit(span=8000, condition="지붕")


def test_deflection_target():
    """조건별로 비교 대상 처짐이 다른지 확인한다 (KDS 14 20 30 표 4.2-2)."""
    assert deflection_target(condition="지붕_비구조재없음") == "live"
    assert deflection_target(condition="바닥_비구조재없음") == "live"
    assert deflection_target(condition="손상되기쉬운_비구조재") == "attached"
    assert deflection_target(condition="손상되지않는_비구조재") == "attached"

    assert set(DEFLECTION_LIMIT) == {
        "지붕_비구조재없음",
        "바닥_비구조재없음",
        "손상되기쉬운_비구조재",
        "손상되지않는_비구조재",
    }

    with pytest.raises(ValueError, match="condition"):
        deflection_target(condition="지붕")


def test_service_steel_stress():
    """사용하중 철근응력 근사값 fs = 2/3 fy 를 확인한다."""
    assert service_steel_stress(fy=400) == pytest.approx(400 * 2 / 3)


def test_max_bar_spacing():
    """균열 제어 철근 간격 식을 손계산과 대조한다."""
    fs = service_steel_stress(fy=400)
    c_c = 40.0

    s = max_bar_spacing(fs=fs, c_c=c_c)

    expected = min(
        375.0 * KAPPA_CR_DRY / fs - 2.5 * c_c, 300.0 * KAPPA_CR_DRY / fs
    )
    assert s == pytest.approx(expected)


def test_max_bar_spacing_environment():
    """건조환경이 아닌 경우 kappa_cr 이 작아 간격도 작아진다."""
    fs = service_steel_stress(fy=400)

    s_dry = max_bar_spacing(fs=fs, c_c=40, dry_environment=True)
    s_wet = max_bar_spacing(fs=fs, c_c=40, dry_environment=False)

    assert s_wet < s_dry
    assert s_wet == pytest.approx(
        min(375.0 * KAPPA_CR_OTHER / fs - 100.0, 300.0 * KAPPA_CR_OTHER / fs)
    )


def test_max_bar_spacing_invalid():
    """fs 가 0 이하이면 예외가 발생한다."""
    with pytest.raises(ValueError, match="fs"):
        max_bar_spacing(fs=0, c_c=40)


def test_check_crack_control():
    """균열 제어 검토를 확인한다."""
    fs, s_max, ok = check_crack_control(bar_spacing=150, fy=400, c_c=40)

    assert fs == pytest.approx(400 * 2 / 3)
    assert ok

    _, _, ok_wide = check_crack_control(bar_spacing=400, fy=400, c_c=40)
    assert not ok_wide


def test_cracking_moment():
    """균열모멘트 Mcr = fr*Ig/yt 를 확인한다."""
    m_cr = cracking_moment(fck=27, i_g=I_G, y_t=300)

    assert m_cr == pytest.approx(0.63 * np.sqrt(27) * I_G / 300)


def test_shrinkage_temperature_reinforcement():
    """수축·온도철근량을 확인한다."""
    a_g = 1000.0 * 200.0

    assert shrinkage_temperature_reinforcement(fy=400, a_g=a_g) == pytest.approx(
        0.0020 * a_g
    )
    assert shrinkage_temperature_reinforcement(fy=500, a_g=a_g) == pytest.approx(
        max(0.0020 * 400 / 500, 0.0014) * a_g
    )
    # 고강도에서 하한 0.0014 가 지배
    assert shrinkage_temperature_reinforcement(fy=700, a_g=a_g) == pytest.approx(
        0.0014 * a_g
    )


def test_check_deflection():
    """처짐 검토의 각 성분이 정합한지 확인한다."""
    res = check_deflection(
        span=8000,
        m_sustained=120e6,
        m_live=60e6,
        m_cr=M_CR,
        i_g=I_G,
        i_cr=I_CR,
        e_c=26702,
    )

    assert I_CR < res.i_e < I_G
    assert res.delta_live == pytest.approx(res.delta_sustained * 60 / 120)
    assert res.delta_total == pytest.approx(
        res.delta_sustained + res.delta_live + res.delta_long_term
    )
    assert res.limit == pytest.approx(8000 / 360)
    # "바닥_비구조재없음" 은 활하중 즉시처짐과 비교한다
    assert res.target == "live"
    assert res.delta_check == pytest.approx(res.delta_live)
    assert res.ok == (res.delta_check <= res.limit)


def test_check_deflection_attached_condition():
    """비구조 요소 부착 조건은 장기처짐 + 활하중 즉시처짐과 비교한다."""
    res = check_deflection(
        span=8000,
        m_sustained=120e6,
        m_live=60e6,
        m_cr=M_CR,
        i_g=I_G,
        i_cr=I_CR,
        e_c=26702,
        condition="손상되기쉬운_비구조재",
    )

    assert res.target == "attached"
    assert res.delta_check == pytest.approx(res.delta_long_term + res.delta_live)
    assert res.limit == pytest.approx(8000 / 480)
    assert res.ok == (res.delta_check <= res.limit)


def test_check_deflection_compression_steel_helps():
    """압축철근이 있으면 장기처짐이 줄어든다."""
    kwargs = {
        "span": 8000,
        "m_sustained": 120e6,
        "m_live": 60e6,
        "m_cr": M_CR,
        "i_g": I_G,
        "i_cr": I_CR,
        "e_c": 26702,
    }

    res_0 = check_deflection(**kwargs)
    res_1 = check_deflection(**kwargs, rho_prime=0.01)

    assert res_1.delta_long_term < res_0.delta_long_term
