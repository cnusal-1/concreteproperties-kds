"""하중조합 검증 시험 (KDS 14 20 01)."""

from __future__ import annotations

import pytest

from concreteproperties_kds.loads import (
    LOAD_COMBINATIONS,
    LoadCombination,
    evaluate_all,
    required_strength,
)


def test_combination_count():
    """정의된 하중조합의 수를 확인한다."""
    assert len(LOAD_COMBINATIONS) == 8
    assert {c.name for c in LOAD_COMBINATIONS} == {f"U{i}" for i in range(1, 9)}


def test_dead_load_only():
    """고정하중만 있으면 U1 = 1.4D 가 지배한다."""
    u, combo = required_strength(loads={"D": 100.0})

    assert u == pytest.approx(140.0)
    assert combo.name == "U1"


def test_dead_and_live():
    """고정+활하중은 U2 가 지배한다."""
    u, combo = required_strength(loads={"D": 100.0, "L": 80.0})

    assert u == pytest.approx(1.2 * 100 + 1.6 * 80)
    assert combo.name == "U2"


def test_roof_load_maximum():
    """지붕 변동하중은 L_r, S, R 중 큰 값을 택한다."""
    combo = next(c for c in LOAD_COMBINATIONS if c.name == "U3")

    value = combo.evaluate(loads={"D": 100.0, "L_r": 20.0, "S": 50.0, "R": 10.0})

    assert value == pytest.approx(1.2 * 100 + 1.6 * 50)


def test_uplift_combination():
    """풍하중에 의한 부양은 U7 = 0.9D + 1.3W 로 검토된다."""
    combo = next(c for c in LOAD_COMBINATIONS if c.name == "U7")

    value = combo.evaluate(loads={"D": 100.0, "W": -200.0})

    assert value == pytest.approx(0.9 * 100 + 1.3 * (-200))


def test_seismic_combination():
    """지진하중 조합 U6 를 확인한다."""
    combo = next(c for c in LOAD_COMBINATIONS if c.name == "U6")

    value = combo.evaluate(loads={"D": 100.0, "E": 150.0, "L": 80.0, "S": 30.0})

    assert value == pytest.approx(1.2 * 100 + 1.0 * 150 + 1.0 * 80 + 0.2 * 30)


def test_reduced_live_load():
    """활하중 계수 저감이 U5, U6 에만 적용되는지 확인한다."""
    loads = {"D": 100.0, "L": 80.0, "W": 50.0}

    full = {c.name: v for c, v in evaluate_all(loads=loads)}
    reduced = {
        c.name: v for c, v in evaluate_all(loads=loads, reduce_live_load=True)
    }

    # U2 의 활하중 계수는 1.6 이므로 변하지 않는다
    assert full["U2"] == pytest.approx(reduced["U2"])
    # U5 의 활하중 계수는 1.0 -> 0.5
    assert reduced["U5"] == pytest.approx(full["U5"] - 0.5 * 80)


def test_results_sorted():
    """evaluate_all 이 큰 순서로 정렬되는지 확인한다."""
    results = evaluate_all(loads={"D": 100.0, "L": 80.0, "W": 60.0})
    values = [v for _, v in results]

    assert values == sorted(values, reverse=True)


def test_missing_loads_treated_as_zero():
    """정의되지 않은 하중은 0 으로 처리된다."""
    combo = LoadCombination(name="test", factors={"D": 1.4, "F": 1.4})

    assert combo.evaluate(loads={"D": 10.0}) == pytest.approx(14.0)


def test_empty_combinations():
    """조합이 비어 있으면 예외가 발생한다."""
    with pytest.raises(ValueError, match="combinations"):
        required_strength(loads={"D": 1.0}, combinations=())
