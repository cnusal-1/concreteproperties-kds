"""교량 콘크리트 바닥판 설계 시험.

값은 KDS 24 10 11 4.6.2 (식 (4.6-1) ~ (4.6-9), 표 4.6-2) 와
KDS 24 14 21 4.4.4, 4.6.5 와 대조한다.
"""

from __future__ import annotations

import math

import pytest

from concreteproperties_kds.kds24.deck import (
    BAR_SPACING_MAX,
    BAR_SPACING_MIN,
    DECK_FCK,
    MIN_THICKNESS_EMPIRICAL,
    MIN_THICKNESS_PSC,
    MIN_THICKNESS_RC,
    WHEEL_LOAD,
    bar_area,
    cantilever_live_load_moment,
    cantilever_wheel_width,
    dead_load_moment,
    deck_deflection_limit,
    deck_span,
    design_deck,
    distribution_steel_ratio,
    live_load_moment,
    live_load_moment_parallel,
    minimum_flexural_steel,
    nominal_cover,
    provided_steel_area,
    required_steel_area,
    wheel_width_parallel,
)


def test_wheel_load_is_half_the_kl510_rear_axle():
    """P = 96 kN 은 KL-510 의 192 kN 축을 좌우로 나눈 값이다."""
    from concreteproperties_kds.kds24 import TRUCK_AXLE_LOADS

    assert pytest.approx(192.0 / 2) == WHEEL_LOAD
    assert max(TRUCK_AXLE_LOADS) == pytest.approx(192.0)


def test_minimum_thicknesses():
    """KDS 24 14 21 4.6.5.1(5), 4.6.5.2(3)⑦."""
    assert pytest.approx(220.0) == MIN_THICKNESS_RC
    assert pytest.approx(200.0) == MIN_THICKNESS_PSC
    assert pytest.approx(240.0) == MIN_THICKNESS_EMPIRICAL
    assert pytest.approx(27.0) == DECK_FCK
    assert (BAR_SPACING_MIN, BAR_SPACING_MAX) == (100.0, 300.0)


def test_deck_span_is_capped_by_clear_span_plus_thickness():
    """4.6.2.3(1) — 중심 간격이되 순 지간 + 두께를 넘길 필요는 없다."""
    # 지지보 폭을 주지 않으면 중심 간격 그대로
    assert deck_span(girder_spacing=2.5, thickness=240) == pytest.approx(2.5)

    # 폭 0.6 m 인 두꺼운 거더 → 순 지간 1.9 + 0.24 = 2.14 m 가 이긴다
    assert deck_span(girder_spacing=2.5, thickness=240, web_width=0.6) == pytest.approx(
        2.14
    )

    # 얇은 거더에서는 중심 간격이 이긴다
    assert deck_span(
        girder_spacing=2.5, thickness=240, web_width=0.15
    ) == pytest.approx(2.5)

    with pytest.raises(ValueError, match="girder_spacing"):
        deck_span(girder_spacing=0.0, thickness=240)


@pytest.mark.parametrize(
    ("span", "expected"),
    [(2.0, 26.0), (2.5, 31.0), (3.0, 36.0), (3.6, 42.0)],
)
def test_live_load_moment_matches_equation(span, expected):
    """식 (4.6-1) — M_t = (L + 0.6) P / 9.6."""
    assert live_load_moment(span=span) == pytest.approx(expected)
    assert live_load_moment(span=span) == pytest.approx((span + 0.6) * WHEEL_LOAD / 9.6)


def test_continuous_slab_takes_eighty_percent():
    """4.6.2.4(2)①나 — 3지점 이상 연속슬래브의 정모멘트는 0.8배."""
    simple = live_load_moment(span=2.5)
    continuous = live_load_moment(span=2.5, continuous=True)

    assert continuous == pytest.approx(0.8 * simple)


def test_bridge_grade_scales_the_live_load():
    """KDS 24 10 11 1.4 — 2등교는 75 %, 3등교는 56.25 %."""
    first = live_load_moment(span=2.5)

    assert live_load_moment(span=2.5, grade=2) == pytest.approx(0.75 * first)
    assert live_load_moment(span=2.5, grade=3) == pytest.approx(0.5625 * first)


def test_live_load_moment_rejects_zero_span():
    """지간이 0 이하면 거부한다."""
    with pytest.raises(ValueError, match="span"):
        live_load_moment(span=0.0)


def test_parallel_case_distribution_width_and_moment():
    """식 (4.6-2) — E = 1.2 + 0.06L ≤ 2.1 m, M_l = 18L."""
    assert wheel_width_parallel(span=3.0) == pytest.approx(1.38)
    assert wheel_width_parallel(span=6.0) == pytest.approx(1.56)
    assert wheel_width_parallel(span=20.0) == pytest.approx(2.1)  # 상한

    assert live_load_moment_parallel(span=3.0) == pytest.approx(54.0)


def test_parallel_moment_is_close_to_a_single_wheel_at_midspan():
    """M_l = 18L 은 윤하중 한 개가 폭 E 에 퍼져 중앙에 놓인 경우와 거의 같다.

    3 m 지간에서 PL/(4E) = 96 × 3 / (4 × 1.38) = 52.2 kN·m/m 이고
    식은 54.0 을 준다. 3 % 차이다.
    """
    span = 3.0
    e = wheel_width_parallel(span=span)
    hand = WHEEL_LOAD * span / (4.0 * e)

    assert hand == pytest.approx(52.17, abs=0.05)
    assert live_load_moment_parallel(span=span) == pytest.approx(hand, rel=0.04)


def test_cantilever_distribution_widths():
    """식 (4.6-4), (4.6-6)."""
    assert cantilever_wheel_width(x=1.0) == pytest.approx(1.94)
    assert cantilever_wheel_width(x=1.0, parallel=True) == pytest.approx(1.33)
    assert cantilever_wheel_width(x=10.0, parallel=True) == pytest.approx(2.1)


def test_cantilever_live_load_moment():
    """M = (P/E) X."""
    x = 1.0
    hand = WHEEL_LOAD / cantilever_wheel_width(x=x) * x

    assert cantilever_live_load_moment(x=x) == pytest.approx(hand)
    assert hand == pytest.approx(49.48, abs=0.02)

    with pytest.raises(ValueError, match="x"):
        cantilever_live_load_moment(x=0.0)


def test_cantilever_moment_grows_slower_than_linearly():
    """분포폭이 X 와 함께 넓어지므로 모멘트가 X 에 비례하지 않는다."""
    m1 = cantilever_live_load_moment(x=1.0)
    m2 = cantilever_live_load_moment(x=2.0)

    assert m2 > m1
    assert m2 < 2.0 * m1


@pytest.mark.parametrize(
    ("kind", "divisor"),
    [
        ("단순판", 8.0),
        ("연속판_지간", 10.0),
        ("연속판_지점", -10.0),
        ("캔틸레버판", -2.0),
    ],
)
def test_dead_load_moment_table(kind, divisor):
    """표 4.6-2 — w l_d^2 / divisor."""
    w, span = 6.0, 2.5

    assert dead_load_moment(w=w, span=span, kind=kind) == pytest.approx(
        w * span**2 / divisor
    )

    with pytest.raises(ValueError, match="표 4.6-2"):
        dead_load_moment(w=w, span=span, kind="2방향판")


def test_distribution_steel_ratio():
    """4.6.5.3(2)① — 120/√L ≤ 67 %, 55/√L ≤ 50 %."""
    assert distribution_steel_ratio(span=4.0) == pytest.approx(0.60)
    assert distribution_steel_ratio(span=2.5) == pytest.approx(0.67)  # 상한
    assert distribution_steel_ratio(span=9.0, parallel=True) == pytest.approx(
        55.0 / 3.0 / 100.0
    )
    assert distribution_steel_ratio(span=1.0, parallel=True) == pytest.approx(0.50)

    with pytest.raises(ValueError, match="span"):
        distribution_steel_ratio(span=0.0)


def test_nominal_cover():
    """4.4.4 식 (4.4-1), (4.4-2), 표 4.4-4."""
    # EC1, D16 → max(16, 25, 10) = 25, + 10 = 35
    assert nominal_cover(exposure="EC1", bar_diameter=16) == (25.0, 35.0)

    # 부착 요구가 이기는 경우 — D32 는 지름 자체가 25 를 넘는다
    assert nominal_cover(exposure="EC1", bar_diameter=32) == (32.0, 42.0)

    # 해수 노출은 같은 번호의 ED 값에 추가분을 더한다
    assert nominal_cover(exposure="ES3", bar_diameter=16) == (70.0, 80.0)
    assert nominal_cover(exposure="ED3", bar_diameter=16) == (55.0, 65.0)

    # 노출 바닥판은 마모 대비 10 mm 추가
    assert nominal_cover(exposure="EC1", bar_diameter=16, exposed_deck=True) == (
        35.0,
        45.0,
    )

    # 프리스트레싱 강재는 표가 다르다
    assert nominal_cover(exposure="EC1", bar_diameter=16, tendon=True) == (35.0, 45.0)

    with pytest.raises(ValueError, match="노출등급"):
        nominal_cover(exposure="EX1")


def test_deck_deflection_limit():
    """4.6.5.1(2) — L/800, L/1000, L/1200."""
    span = 2400.0

    assert deck_deflection_limit(span=span) == pytest.approx(3.0)
    assert deck_deflection_limit(span=span, pedestrian="제한적") == pytest.approx(2.4)
    assert deck_deflection_limit(span=span, pedestrian="많음") == pytest.approx(2.0)

    with pytest.raises(ValueError, match="보행 조건"):
        deck_deflection_limit(span=span, pedestrian="아주많음")


def test_bar_area_and_provided_area():
    """공칭 단면적과 배치 철근량."""
    assert bar_area(diameter=16.0) == pytest.approx(201.06, abs=0.01)
    assert provided_steel_area(diameter=16.0, spacing=150.0) == pytest.approx(
        201.06 * 1000 / 150, abs=0.1
    )

    with pytest.raises(ValueError, match="spacing"):
        provided_steel_area(diameter=16.0, spacing=0.0)


def test_required_steel_area_round_trips():
    """구한 철근량을 다시 넣으면 그 휨모멘트가 나온다."""
    from concreteproperties_kds.kds24 import (
        design_compressive_strength,
        design_yield_strength,
        equivalent_block,
    )

    m_ed = 60.0e6  # N.mm
    d = 197.0
    a_s = required_steel_area(m_ed=m_ed, d=d)

    f_cd = design_compressive_strength(fck=DECK_FCK)
    f_yd = design_yield_strength(fy=400.0)
    alpha, beta = equivalent_block(fck=DECK_FCK)
    c = a_s * f_yd / (alpha * f_cd * 1000.0)

    assert a_s * f_yd * (d - beta * c) == pytest.approx(m_ed, rel=1e-9)


def test_required_steel_area_refuses_impossible_moment():
    """단철근으로 저항할 수 없는 휨모멘트는 거부한다."""
    with pytest.raises(ValueError, match="단철근"):
        required_steel_area(m_ed=500.0e6, d=197.0)


def test_minimum_flexural_steel():
    """식 (4.6-1), (4.6-2) 중 큰 값."""
    d = 197.0
    hand = max(0.25 * math.sqrt(27.0) / 400.0, 1.4 / 400.0) * 1000.0 * d

    assert minimum_flexural_steel(d=d) == pytest.approx(hand)
    # fck 27 에서는 0.25√fck/fy = 0.00325 가 1.4/fy = 0.0035 보다 작다
    assert hand == pytest.approx(0.0035 * 1000.0 * d)


def test_design_deck_matches_hand_calculation():
    """전형적인 거더교 바닥판을 손계산과 대조한다.

    거더 간격 2.5 m, 두께 240 mm, D16@150, EC1, 포장 80 mm, 연속판.

    - 활하중  M_t = (2.5 + 0.6) × 96 / 9.6 = 31.0 → 연속 0.8배 = 24.8
    - 충격    × 1.25 → 31.0
    - 고정하중 DC = 24.5 × 0.24 = 5.88 kN/m², M = wL²/10 = 3.675
              DW = 22.5 × 0.08 = 1.80 kN/m², M = 1.125
    - 극한Ⅰ  1.25 × 3.675 + 1.50 × 1.125 + 1.80 × 31.0 = 62.08 kN·m/m
    """
    r = design_deck(girder_spacing=2.5, thickness=240, bar_diameter=16, bar_spacing=150)

    assert r.span == pytest.approx(2.5)
    assert r.cover == pytest.approx(35.0)
    assert r.d == pytest.approx(240 - 35 - 8)
    assert r.m_dead == pytest.approx(3.675 + 1.125)
    assert r.m_live == pytest.approx(24.8 * 1.25)
    assert r.m_ed == pytest.approx(62.081, abs=0.01)
    assert r.as_provided == pytest.approx(1340.4, abs=0.5)
    assert r.m_rd > r.m_ed
    assert r.adequate


def test_thin_deck_fails_the_thickness_check():
    """220 mm 미만은 최소 두께 검토에서 걸린다."""
    r = design_deck(girder_spacing=2.5, thickness=200)

    assert not r.checks["최소 두께"]
    assert not r.adequate


def test_wide_spacing_fails_flexure():
    """거더 간격이 넓어지면 같은 배근으로는 모자란다."""
    tight = design_deck(girder_spacing=2.5, bar_spacing=150)
    wide = design_deck(girder_spacing=4.5, bar_spacing=150)

    assert wide.m_ed > tight.m_ed
    assert tight.checks["설계휨강도"]
    assert not wide.checks["설계휨강도"]


def test_bar_spacing_limits_are_enforced():
    """4.6.5.2(5)③ — 100 ~ 300 mm, 하부 주철근은 두께 이하."""
    too_close = design_deck(girder_spacing=2.5, bar_spacing=80)
    too_far = design_deck(girder_spacing=2.5, bar_spacing=320)
    thicker_than_slab = design_deck(girder_spacing=2.5, thickness=240, bar_spacing=260)

    assert not too_close.checks["철근 간격 하한"]
    assert not too_far.checks["철근 간격 상한"]
    assert not thicker_than_slab.checks["철근 간격 상한"]


def test_marine_exposure_eats_the_effective_depth():
    """고부식성 환경은 피복이 두꺼워져 유효깊이를 갉아먹는다."""
    inland = design_deck(girder_spacing=2.5, exposure="EC1")
    marine = design_deck(girder_spacing=2.5, exposure="ES3")

    assert marine.cover == pytest.approx(80.0)
    assert marine.d < inland.d
    assert marine.m_rd < inland.m_rd
    # 설계휨모멘트는 같다 — 강도만 줄어든다
    assert marine.m_ed == pytest.approx(inland.m_ed)
