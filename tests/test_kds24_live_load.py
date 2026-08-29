"""KDS 24 12 21 차량활하중 KL-510 시험.

값은 4.3.1, 4.3.2, 4.4 및 그림 4.3-1, 표 4.3-1, 표 4.3-2, 표 4.3-3, 표 4.4-1 과
대조한다.
"""

from __future__ import annotations

import pytest

from concreteproperties_kds.kds24 import (
    FATIGUE_TRUCK_RATIO,
    TRUCK_AXLE_LOADS,
    TRUCK_AXLE_POSITIONS,
    TRUCK_TOTAL_LOAD,
    adtt_single_lane,
    fatigue_truck_moment,
    girder_live_load,
    impact_buried,
    impact_factor,
    lane_load,
    lane_moment,
    lane_shear,
    lane_width,
    multiple_presence,
    number_of_lanes,
    truck_lane_fraction,
    truck_moment,
    truck_shear,
)

SPAN = 30.0


def test_kl510_axles_match_figure():
    """그림 4.3-1 — 48/192/135/135 kN, 전체 길이 12.0 m, 합계 510 kN."""
    assert TRUCK_AXLE_LOADS == (48.0, 192.0, 135.0, 135.0)
    assert sum(TRUCK_AXLE_LOADS) == pytest.approx(TRUCK_TOTAL_LOAD)
    assert TRUCK_AXLE_POSITIONS == (0.0, 3.6, 10.8, 12.0)
    assert TRUCK_AXLE_POSITIONS[-1] == pytest.approx(12.0)


@pytest.mark.parametrize(
    ("roadway_width", "expected"),
    [
        (3.6, 1),
        (5.9, 1),  # 6 m 미만이라 1 차로
        (6.0, 2),  # 6 m 이상이면 2 차로 (4.3.1.1(1) 단서)
        (7.2, 2),
        (10.8, 3),
        (14.4, 4),
    ],
)
def test_number_of_lanes(roadway_width, expected):
    """식 (4.3-1) 과 그 단서."""
    assert number_of_lanes(roadway_width=roadway_width) == expected


def test_number_of_lanes_rejects_zero_width():
    """폭이 0 이하면 거부한다."""
    with pytest.raises(ValueError, match="roadway_width"):
        number_of_lanes(roadway_width=0.0)


def test_lane_width_is_capped_at_3600():
    """식 (4.3-2) — W = W_C/N 이되 3.6 m 를 넘지 않는다."""
    assert lane_width(roadway_width=10.8, n_lanes=3) == pytest.approx(3.6)
    assert lane_width(roadway_width=20.0, n_lanes=4) == pytest.approx(3.6)
    assert lane_width(roadway_width=9.0, n_lanes=3) == pytest.approx(3.0)


@pytest.mark.parametrize(
    ("n_lanes", "expected"),
    [(1, 1.00), (2, 0.90), (3, 0.80), (4, 0.70), (5, 0.65), (8, 0.65)],
)
def test_multiple_presence(n_lanes, expected):
    """표 4.3-1 다차로 재하계수."""
    assert multiple_presence(n_lanes=n_lanes) == pytest.approx(expected)

    with pytest.raises(ValueError, match="1 이상"):
        multiple_presence(n_lanes=0)


def test_lane_load_table():
    """표 4.3-2 — 60 m 이하는 12.7 kN/m, 그 위는 지간이 길수록 준다."""
    assert lane_load(span=10.0) == pytest.approx(12.7)
    assert lane_load(span=60.0) == pytest.approx(12.7)
    assert lane_load(span=120.0) == pytest.approx(12.7 * 0.5**0.10)
    assert lane_load(span=120.0) < lane_load(span=60.0)

    with pytest.raises(ValueError, match="span"):
        lane_load(span=0.0)


def test_truck_moment_matches_barre_hand_check():
    r"""30 m 단순보의 최대 트럭 휨모멘트.

    Barre 의 정리로 손검산한다. 합력 510 kN 의 작용점은 앞축에서

    .. math::
        \bar{x} = \frac{192 \times 3.6 + 135 \times 10.8 + 135 \times 12.0}{510}
        = 7.3906\ \text{m}

    이고, 여기서 가장 가까운 축은 10.8 m 의 135 kN 축(거리 3.4094 m)이다. 그
    축과 합력이 지간 중앙을 사이에 두고 대칭이 되도록 놓으면 그 축 아래에서
    최대 모멘트가 생긴다.
    """
    x_bar = (192 * 3.6 + 135 * 10.8 + 135 * 12.0) / 510.0

    assert x_bar == pytest.approx(7.3906, abs=1e-4)

    offset = abs(x_bar - 10.8)
    x_critical = SPAN / 2 + offset / 2
    positions = [x_critical - 10.8 + p for p in TRUCK_AXLE_POSITIONS]

    reaction = sum(
        load * (SPAN - a) / SPAN
        for a, load in zip(positions, TRUCK_AXLE_LOADS, strict=True)
    )
    hand = reaction * x_critical - sum(
        load * (x_critical - a)
        for a, load in zip(positions, TRUCK_AXLE_LOADS, strict=True)
        if a < x_critical
    )

    assert hand == pytest.approx(2843.0, abs=1.0)
    assert truck_moment(span=SPAN, step=0.01) == pytest.approx(hand, rel=1e-3)


def test_truck_shear_matches_hand_check():
    """받침점 최대 전단력은 192 kN 축을 받침에 올렸을 때 나온다."""
    hand = 192.0 + 135.0 * (SPAN - 7.2) / SPAN + 135.0 * (SPAN - 8.4) / SPAN

    assert hand == pytest.approx(391.8, abs=0.1)
    assert truck_shear(span=SPAN, step=0.01) == pytest.approx(hand, rel=1e-3)


def test_truck_effects_grow_with_span():
    """지간이 길수록 트럭 단면력이 커진다."""
    moments = [truck_moment(span=L, step=0.1) for L in (10, 20, 30, 40)]

    assert moments == sorted(moments)

    # 받침점 전단력은 510 kN 을 넘을 수 없다
    assert truck_shear(span=100.0, step=0.1) < TRUCK_TOTAL_LOAD


def test_short_span_is_governed_by_the_single_heaviest_axle():
    """지간이 짧으면 가장 무거운 축 한 개가 지배한다.

    3 m 지간에 올릴 수 있는 조합은 두 가지다. 192 kN 축 하나를 중앙에 두면
    PL/4 = 144 kN·m, 1.2 m 떨어진 135 kN 두 축을 올리면 129.6 kN·m 이므로
    전자가 이긴다. 축간거리가 지간에 비해 크면 축을 여러 개 올리는 것이
    오히려 손해다.
    """
    one_axle = 192.0 * 3.0 / 4.0
    two_axles = 162.0 * 1.8 - 135.0 * 1.2

    assert one_axle == pytest.approx(144.0)
    assert two_axles == pytest.approx(129.6)
    assert truck_moment(span=3.0, step=0.005) == pytest.approx(one_axle, rel=1e-3)


def test_lane_load_effects():
    """등분포하중의 wL^2/8 과 wL/2."""
    w = lane_load(span=SPAN)

    assert lane_moment(span=SPAN) == pytest.approx(w * SPAN**2 / 8)
    assert lane_shear(span=SPAN) == pytest.approx(w * SPAN / 2)
    assert lane_shear(span=SPAN, section=SPAN / 2) == pytest.approx(w * SPAN / 8)


def test_impact_factor_table():
    """표 4.4-1 — 피로 15 %, 그 밖에는 25 %."""
    assert impact_factor() == pytest.approx(1.25)
    assert impact_factor(limit_state="사용") == pytest.approx(1.25)
    assert impact_factor(limit_state="피로") == pytest.approx(1.15)


def test_impact_buried_decreases_with_cover():
    """식 (4.4-1) — 토피가 깊어지면 충격이 준다. 2,439 mm 에서 0 이 된다."""
    assert impact_buried(cover_depth=0.0) == pytest.approx(40.0)
    assert impact_buried(cover_depth=1000.0) == pytest.approx(40.0 * (1 - 0.41))
    assert impact_buried(cover_depth=3000.0) == pytest.approx(0.0)


def test_fatigue_load():
    """4.3.2 — 트럭의 80 %, 충격 15 %, 표 4.3-3 의 p."""
    assert pytest.approx(0.80) == FATIGUE_TRUCK_RATIO
    assert truck_lane_fraction(1) == pytest.approx(1.00)
    assert truck_lane_fraction(2) == pytest.approx(0.85)
    assert truck_lane_fraction(4) == pytest.approx(0.80)
    assert adtt_single_lane(adtt=2000, n_truck_lanes=2) == pytest.approx(1700.0)

    assert fatigue_truck_moment(span=SPAN, step=0.01) == pytest.approx(
        0.80 * 1.15 * truck_moment(span=SPAN, step=0.01)
    )


def test_girder_live_load_follows_clause_4315():
    """4.3.1.5 — 트럭 단독과 (트럭 75 % + 차로) 중 큰 값."""
    effect = girder_live_load(span=SPAN, step=0.01)

    truck_only = 1.25 * truck_moment(span=SPAN, step=0.01)
    combined = 0.75 * truck_only + lane_moment(span=SPAN)

    assert effect.moment == pytest.approx(max(truck_only, combined))
    assert effect.governed_by == "트럭 75 % + 차로"
    assert effect.impact == pytest.approx(1.25)


def test_lane_load_matters_more_on_long_spans():
    """지간이 길수록 차로하중의 몫이 커진다.

    짧은 지간은 트럭 한 대가 지배하지만, 긴 지간에서는 줄지어 선 차량의 무게가
    이기기 때문이다. 이것이 표준차로하중을 따로 둔 이유다.
    """
    short = girder_live_load(span=10.0, step=0.02)
    long_span = girder_live_load(span=80.0, step=0.05)

    assert short.governed_by == "트럭"
    assert long_span.governed_by == "트럭 75 % + 차로"
    assert short.lane_moment / short.moment < 0.25
    assert long_span.lane_moment / long_span.moment > 0.50
