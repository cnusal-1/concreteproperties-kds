"""하중조합 검증 시험 (KDS 14 20 10 4.2.2).

기준값은 KDS 14 20 10 4.2.2 식 (4.2-1) ~ 식 (4.2-8) 원문에 따른다.
"""

from __future__ import annotations

import pytest

from concreteproperties_kds.loads import (
    LOAD_COMBINATIONS,
    LoadCombination,
    alpha_h,
    evaluate_all,
    minimum_strength,
    required_strength,
)


def combo(name: str) -> LoadCombination:
    """이름으로 하중조합을 찾는다.

    Args:
        name: 조합 이름

    Returns:
        하중조합 객체
    """
    return next(c for c in LOAD_COMBINATIONS if c.name == name)


def test_all_equations_present():
    """식 (4.2-1) ~ (4.2-8) 이 모두 정의되어 있는지 확인한다."""
    equations = {c.equation for c in LOAD_COMBINATIONS}

    assert equations == {f"4.2-{i}" for i in range(1, 9)}


def test_alpha_h():
    """연직토압 보정계수를 확인한다 (KDS 14 20 10 4.2.2(1))."""
    assert alpha_h(depth=0.0) == pytest.approx(1.0)
    assert alpha_h(depth=2.0) == pytest.approx(1.0)
    assert alpha_h(depth=3.0) == pytest.approx(1.05 - 0.025 * 3.0)
    # 하한 0.875
    assert alpha_h(depth=10.0) == pytest.approx(0.875)
    assert alpha_h(depth=100.0) == pytest.approx(0.875)


def test_eq_4_2_1():
    """U = 1.4(D + F)"""
    assert combo("U1").evaluate(loads={"D": 100.0, "F": 20.0}) == pytest.approx(
        1.4 * 120.0
    )


def test_eq_4_2_2():
    """U = 1.2(D+F+T) + 1.6(L + aH*H_v + H_h) + 0.5(L_r or S or R)"""
    loads = {"D": 100.0, "F": 10.0, "T": 5.0, "L": 80.0, "H_v": 30.0,
             "H_h": 20.0, "L_r": 10.0, "S": 25.0}

    value = combo("U2").evaluate(loads=loads, depth=0.0)

    assert value == pytest.approx(
        1.2 * (100 + 10 + 5) + 1.6 * (80 + 1.0 * 30 + 20) + 0.5 * 25
    )


def test_eq_4_2_2_alpha_h_applied():
    """식 (4.2-2) 의 H_v 에만 alpha_H 가 곱해진다."""
    loads = {"D": 100.0, "H_v": 50.0, "H_h": 50.0}

    shallow = combo("U2").evaluate(loads=loads, depth=1.0)
    deep = combo("U2").evaluate(loads=loads, depth=6.0)

    a_h = alpha_h(depth=6.0)
    assert deep == pytest.approx(
        1.2 * 100 + 1.6 * (a_h * 50 + 50)
    )
    assert deep < shallow


def test_eq_4_2_3_alternatives():
    """식 (4.2-3) 은 (1.0L 또는 0.65W) 로 택일한다."""
    loads = {"D": 100.0, "L": 80.0, "W": 60.0, "S": 30.0}

    assert combo("U3-L").evaluate(loads=loads) == pytest.approx(
        1.2 * 100 + 1.6 * 30 + 1.0 * 80
    )
    assert combo("U3-W").evaluate(loads=loads) == pytest.approx(
        1.2 * 100 + 1.6 * 30 + 0.65 * 60
    )


def test_eq_4_2_4_wind():
    """U = 1.2D + 1.3W + 1.0L + 0.5(L_r or S or R) — 풍하중 계수 1.3"""
    loads = {"D": 100.0, "W": 60.0, "L": 80.0, "S": 30.0}

    assert combo("U4").evaluate(loads=loads) == pytest.approx(
        1.2 * 100 + 1.3 * 60 + 1.0 * 80 + 0.5 * 30
    )


def test_eq_4_2_5_seismic():
    """U = 1.2(D+H_v) + 1.0E + 1.0L + 0.2S + (1.0H_h 또는 0.5H_h)"""
    loads = {"D": 100.0, "H_v": 20.0, "E": 150.0, "L": 80.0, "S": 30.0,
             "H_h": 40.0}

    base = 1.2 * (100 + 20) + 1.0 * 150 + 1.0 * 80 + 0.2 * 30

    assert combo("U5-a").evaluate(loads=loads) == pytest.approx(base + 1.0 * 40)
    assert combo("U5-b").evaluate(loads=loads) == pytest.approx(base + 0.5 * 40)


def test_eq_4_2_6():
    """U = 1.2(D+F+T) + 1.6(L + aH*H_v) + 0.8H_h + 0.5(L_r or S or R)"""
    loads = {"D": 100.0, "F": 10.0, "T": 5.0, "L": 80.0, "H_v": 30.0,
             "H_h": 20.0, "S": 25.0}

    assert combo("U6").evaluate(loads=loads, depth=0.0) == pytest.approx(
        1.2 * 115 + 1.6 * (80 + 30) + 0.8 * 20 + 0.5 * 25
    )


def test_eq_4_2_7_uplift():
    """U = 0.9(D + H_v) + 1.3W + (1.6H_h 또는 0.8H_h)"""
    loads = {"D": 100.0, "H_v": 10.0, "W": -200.0, "H_h": 30.0}

    assert combo("U7-a").evaluate(loads=loads) == pytest.approx(
        0.9 * 110 + 1.3 * (-200) + 1.6 * 30
    )
    assert combo("U7-b").evaluate(loads=loads) == pytest.approx(
        0.9 * 110 + 1.3 * (-200) + 0.8 * 30
    )


def test_eq_4_2_8_uplift_seismic():
    """U = 0.9(D + H_v) + 1.0E + (1.0H_h 또는 0.5H_h)"""
    loads = {"D": 100.0, "H_v": 10.0, "E": -150.0, "H_h": 30.0}

    assert combo("U8-a").evaluate(loads=loads) == pytest.approx(
        0.9 * 110 + 1.0 * (-150) + 1.0 * 30
    )


def test_roof_load_maximum():
    """지붕 변동하중은 L_r, S, R 중 큰 값을 택한다."""
    value = combo("U3-L").evaluate(
        loads={"D": 100.0, "L_r": 20.0, "S": 50.0, "R": 10.0}
    )

    assert value == pytest.approx(1.2 * 100 + 1.6 * 50)


def test_dead_load_only():
    """고정하중만 있으면 U1 = 1.4D 가 지배한다."""
    u, governing = required_strength(loads={"D": 100.0})

    assert u == pytest.approx(140.0)
    assert governing.name == "U1"


def test_dead_and_live():
    """고정+활하중은 식 (4.2-2) 가 지배한다."""
    u, governing = required_strength(loads={"D": 100.0, "L": 80.0})

    assert u == pytest.approx(1.2 * 100 + 1.6 * 80)
    assert governing.equation == "4.2-2"


def test_live_load_reduction_scope():
    """활하중 저감은 식 (4.2-3), (4.2-4), (4.2-5) 에만 적용된다."""
    reducible = {
        c.equation for c in LOAD_COMBINATIONS if c.live_load_reducible
    }

    assert reducible == {"4.2-3", "4.2-4", "4.2-5"}


def test_live_load_reduction_value():
    """저감 시 활하중 계수가 1.0 에서 0.5 로 낮아진다."""
    loads = {"D": 100.0, "L": 80.0, "W": 50.0}

    full = {c.name: v for c, v in evaluate_all(loads=loads)}
    reduced = {
        c.name: v for c, v in evaluate_all(loads=loads, reduce_live_load=True)
    }

    # 식 (4.2-2) 의 활하중 계수는 1.6 이므로 변하지 않는다
    assert full["U2"] == pytest.approx(reduced["U2"])
    # 식 (4.2-4) 는 1.0 -> 0.5
    assert reduced["U4"] == pytest.approx(full["U4"] - 0.5 * 80)


def test_results_sorted():
    """evaluate_all 이 큰 순서로 정렬되는지 확인한다."""
    values = [v for _, v in evaluate_all(loads={"D": 100.0, "L": 80.0, "W": 60.0})]

    assert values == sorted(values, reverse=True)


def test_minimum_strength_for_uplift():
    """부양 검토에서는 0.9D 조합이 가장 작은 값을 준다."""
    _, governing = minimum_strength(loads={"D": 100.0, "W": -300.0})

    assert governing.equation in ("4.2-7", "4.2-8")


def test_missing_loads_treated_as_zero():
    """정의되지 않은 하중은 0 으로 처리된다."""
    assert combo("U1").evaluate(loads={"D": 10.0}) == pytest.approx(14.0)


def test_empty_combinations():
    """조합이 비어 있으면 예외가 발생한다."""
    with pytest.raises(ValueError, match="combinations"):
        required_strength(loads={"D": 1.0}, combinations=())

    with pytest.raises(ValueError, match="combinations"):
        minimum_strength(loads={"D": 1.0}, combinations=())
