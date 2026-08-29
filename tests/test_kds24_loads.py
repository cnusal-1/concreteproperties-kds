"""KDS 24 12 11 하중조합 시험.

값은 표 4.1-1, 표 4.1-2 및 KDS 24 10 11 1.3 과 대조한다.
"""

from __future__ import annotations

import pytest

from concreteproperties_kds.kds24 import (
    COMBINATIONS_BY_NAME,
    LOAD_COMBINATIONS,
    bridge_grade_factor,
    evaluate_all,
    governing_combination,
    load_modifier,
    permanent_load_factor,
)


def test_all_thirteen_combinations_present():
    """표 4.1-1 도로교의 하중조합은 13 가지다."""
    names = [c.name for c in LOAD_COMBINATIONS]

    assert len(names) == 13
    assert names[:5] == ["극한Ⅰ", "극한Ⅱ", "극한Ⅲ", "극한Ⅳ", "극한Ⅴ"]
    assert "극단상황Ⅰ" in names
    assert "피로" in names


@pytest.mark.parametrize(
    ("kind", "maximum", "expected"),
    [
        ("DC", True, 1.25),
        ("DC", False, 0.90),
        ("DW", True, 1.50),
        ("DW", False, 0.65),
        ("DD", True, 1.80),
        ("EH", True, 1.50),
        ("EH_정지", True, 1.35),
        ("EV_연성암거", True, 1.95),
        ("ES", False, 0.75),
        ("PS", True, 1.00),
    ],
)
def test_permanent_load_factors(kind, maximum, expected):
    """표 4.1-2 의 값을 그대로 돌려준다."""
    assert permanent_load_factor(kind=kind, maximum=maximum) == pytest.approx(expected)

    with pytest.raises(ValueError, match="표 4.1-2"):
        permanent_load_factor(kind="XX")


def test_strength_i_is_the_familiar_combination():
    """극한Ⅰ = 1.25 DC + 1.50 DW + 1.80 (LL+IM)."""
    loads = {"DC": 100.0, "DW": 20.0, "LL": 50.0, "IM": 12.5}

    got = COMBINATIONS_BY_NAME["극한Ⅰ"].evaluate(loads=loads)
    hand = 1.25 * 100 + 1.50 * 20 + 1.80 * (50 + 12.5)

    assert got == pytest.approx(hand)


def test_minimum_permanent_factors_when_load_helps():
    """상시하중이 유리하게 작용하면 최소계수를 쓴다 (4.1(4))."""
    loads = {"DC": 100.0, "DW": 20.0}

    maximised = COMBINATIONS_BY_NAME["극한Ⅰ"].evaluate(loads=loads, maximise=True)
    minimised = COMBINATIONS_BY_NAME["극한Ⅰ"].evaluate(loads=loads, maximise=False)

    assert maximised == pytest.approx(1.25 * 100 + 1.50 * 20)
    assert minimised == pytest.approx(0.90 * 100 + 0.65 * 20)


def test_service_combinations_use_unit_permanent_factor():
    """사용한계상태에서는 상시하중계수가 1.00 이다."""
    loads = {"DC": 100.0, "DW": 20.0, "LL": 50.0}

    assert COMBINATIONS_BY_NAME["사용Ⅰ"].evaluate(loads=loads) == pytest.approx(
        100 + 20 + 1.00 * 50
    )
    assert COMBINATIONS_BY_NAME["사용Ⅲ"].evaluate(loads=loads) == pytest.approx(
        100 + 20 + 0.80 * 50
    )


def test_fatigue_combination_sees_live_load_only():
    """피로조합은 활하중의 0.75 배만 본다."""
    loads = {"DC": 100.0, "LL": 50.0, "IM": 7.5}

    assert COMBINATIONS_BY_NAME["피로"].evaluate(loads=loads) == pytest.approx(
        0.75 * (50 + 7.5)
    )


def test_strength_iii_drops_live_load_and_adds_wind():
    """극한Ⅲ 은 활하중이 없고 풍하중계수가 1.40 이다."""
    loads = {"DC": 100.0, "LL": 50.0, "WS": 30.0}

    assert COMBINATIONS_BY_NAME["극한Ⅲ"].evaluate(loads=loads) == pytest.approx(
        1.25 * 100 + 1.40 * 30
    )


def test_tu_factor_depends_on_deformation():
    """TU·CR·SH 는 변형량 계산에 큰 값, 그 밖에는 작은 값 (4.1(5))."""
    loads = {"TU": 10.0}
    strength_i = COMBINATIONS_BY_NAME["극한Ⅰ"]

    assert strength_i.evaluate(loads=loads) == pytest.approx(0.50 * 10)
    assert strength_i.evaluate(loads=loads, deformation=True) == pytest.approx(
        1.20 * 10
    )


def test_gamma_tg_defaults_follow_clause_seven():
    """4.1(7) — 극한은 0.0, 활하중 있는 사용은 0.5, 없는 사용은 1.0."""
    assert COMBINATIONS_BY_NAME["극한Ⅰ"].default_gamma_tg_sd() == pytest.approx(0.0)
    assert COMBINATIONS_BY_NAME["사용Ⅰ"].default_gamma_tg_sd() == pytest.approx(0.5)
    assert COMBINATIONS_BY_NAME["사용Ⅳ"].default_gamma_tg_sd() == pytest.approx(1.0)


def test_extreme_event_i_live_load_is_set_by_owner():
    """극단상황Ⅰ 의 활하중계수는 발주자가 정한다 (4.1(9))."""
    loads = {"DC": 100.0, "LL": 50.0, "EQ": 40.0}
    combination = COMBINATIONS_BY_NAME["극단상황Ⅰ"]

    assert combination.evaluate(loads=loads, gamma_eq=0.0) == pytest.approx(
        1.25 * 100 + 1.00 * 40
    )
    assert combination.evaluate(loads=loads, gamma_eq=0.5) == pytest.approx(
        1.25 * 100 + 0.5 * 50 + 1.00 * 40
    )


def test_load_modifier_bounds():
    """식 (1.3-2), (1.3-3) 의 상·하한."""
    assert load_modifier() == pytest.approx(1.0)
    assert load_modifier(ductility=1.05, redundancy=1.05) == pytest.approx(1.1025)

    # 하한 0.95 — 세 계수를 모두 0.95 로 해도 더 내려가지 않는다
    assert load_modifier(0.95, 0.95, 0.95) == pytest.approx(0.95)

    # 최소하중계수 쪽은 역수이고 1.0 을 넘지 못한다
    assert load_modifier(1.05, 1.05, 1.0, maximum=False) == pytest.approx(1.0 / 1.1025)
    assert load_modifier(0.95, 0.95, 0.95, maximum=False) == pytest.approx(1.0)


def test_bridge_grade_factor():
    """1.4 — 2등교는 75 %, 3등교는 그 75 %."""
    assert bridge_grade_factor(1) == pytest.approx(1.0)
    assert bridge_grade_factor(2) == pytest.approx(0.75)
    assert bridge_grade_factor(3) == pytest.approx(0.5625)

    with pytest.raises(ValueError, match="grade"):
        bridge_grade_factor(4)


def test_governing_combination_is_strength_i_for_a_normal_bridge():
    """활하중이 보통이면 극한Ⅰ 이 지배한다."""
    loads = {"DC": 100.0, "DW": 20.0, "LL": 50.0, "IM": 12.5, "WS": 10.0}

    name, value = governing_combination(loads=loads)

    assert name == "극한Ⅰ"
    assert value == pytest.approx(1.25 * 100 + 1.50 * 20 + 1.80 * 62.5)


def test_strength_iv_uses_dc_factor_of_one_point_five():
    """극한Ⅳ 에서만 DC 의 최대계수가 1.50 이다 (표 4.1-2).

    활하중이 작을 때 극한Ⅳ 가 극한Ⅰ 을 넘어서는 것이 이 조합의 존재 이유다.
    """
    loads = {"DC": 1000.0, "LL": 5.0}

    strength_i = COMBINATIONS_BY_NAME["극한Ⅰ"].evaluate(loads=loads)
    strength_iv = COMBINATIONS_BY_NAME["극한Ⅳ"].evaluate(loads=loads)

    assert strength_iv == pytest.approx(1.50 * 1000.0)
    assert strength_i == pytest.approx(1.25 * 1000.0 + 1.80 * 5.0)
    assert strength_iv > strength_i

    # 최소계수 쪽에서는 1.50 을 쓰지 않는다
    assert COMBINATIONS_BY_NAME["극한Ⅳ"].evaluate(
        loads=loads, maximise=False
    ) == pytest.approx(0.90 * 1000.0)

    # 지배조합도 극한Ⅳ 로 뒤집힌다
    assert governing_combination(loads=loads)[0] == "극한Ⅳ"


def test_evaluate_all_can_filter_by_limit_state():
    """한계상태로 걸러낼 수 있다."""
    loads = {"DC": 100.0, "LL": 50.0}

    ultimate = evaluate_all(loads=loads, limit_state="극한")
    service = evaluate_all(loads=loads, limit_state="사용")

    assert len(ultimate) == 5
    assert len(service) == 5
    assert all(name.startswith("극한") for name in ultimate)
