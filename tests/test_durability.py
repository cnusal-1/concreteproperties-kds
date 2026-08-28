"""내구성 검증 시험 (KDS 14 20 40)."""

from __future__ import annotations

import pytest

from concreteproperties_kds.durability import (
    EXPOSURE_REQUIREMENTS,
    check_durability,
    governing_requirements,
)


def test_exposure_classes_defined():
    """노출등급이 모두 정의되어 있는지 확인한다."""
    expected = {
        "E0",
        "EC1",
        "EC2",
        "EC3",
        "EC4",
        "ES1",
        "ES2",
        "ES3",
        "ES4",
        "EF1",
        "EF2",
        "EF3",
        "EF4",
        "EA1",
        "EA2",
        "EA3",
    }

    assert set(EXPOSURE_REQUIREMENTS) == expected


def test_requirements_increase_with_severity():
    """같은 범주 안에서 등급이 높을수록 요구가 엄격해진다."""
    ec = [EXPOSURE_REQUIREMENTS[f"EC{i}"] for i in range(1, 5)]

    fck = [r.fck_min for r in ec]
    assert fck == sorted(fck)

    wb = [r.wb_max for r in ec if r.wb_max is not None]
    assert wb == sorted(wb, reverse=True)


def test_check_durability_pass():
    """요구를 만족하는 경우를 확인한다."""
    res = check_durability(
        exposure_class="EC3", fck=30, water_binder_ratio=0.45, cover=40
    )

    assert res.ok
    assert res.ok_fck
    assert res.ok_wb
    assert res.ok_cover


def test_check_durability_fail_strength():
    """강도가 부족하면 불만족으로 판정된다."""
    res = check_durability(exposure_class="ES3", fck=27)

    assert not res.ok
    assert not res.ok_fck


def test_check_durability_fail_wb():
    """물-결합재비가 크면 불만족으로 판정된다."""
    res = check_durability(
        exposure_class="EC4", fck=35, water_binder_ratio=0.55
    )

    assert res.ok_fck
    assert not res.ok_wb
    assert not res.ok


def test_check_durability_unchecked_items():
    """확인하지 않은 항목은 만족으로 처리된다."""
    res = check_durability(exposure_class="EC4", fck=35)

    assert res.ok
    assert res.wb is None
    assert res.cover is None


def test_check_durability_invalid():
    """정의되지 않은 노출등급은 예외가 발생한다."""
    with pytest.raises(ValueError, match="exposure_class"):
        check_durability(exposure_class="EX9", fck=30)


def test_governing_requirements():
    """여러 노출등급이 겹칠 때 가장 엄격한 값이 지배한다."""
    fck_min, wb_max, cover_min = governing_requirements(
        exposure_classes=["EC3", "EF2", "ES3"]
    )

    assert fck_min == pytest.approx(35.0)  # ES3
    assert wb_max == pytest.approx(0.40)  # ES3
    assert cover_min == pytest.approx(60.0)  # ES3


def test_governing_requirements_no_wb():
    """물-결합재비 규정이 없는 등급만 있으면 None 을 반환한다."""
    fck_min, wb_max, cover_min = governing_requirements(
        exposure_classes=["E0", "EC1"]
    )

    assert fck_min == pytest.approx(21.0)
    assert wb_max is None
    assert cover_min == pytest.approx(20.0)


def test_governing_requirements_invalid():
    """빈 목록이나 정의되지 않은 등급은 예외가 발생한다."""
    with pytest.raises(ValueError, match="exposure_classes"):
        governing_requirements(exposure_classes=[])

    with pytest.raises(ValueError, match="정의되지 않은"):
        governing_requirements(exposure_classes=["EC1", "EX9"])
