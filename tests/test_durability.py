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
    """같은 범주 안에서 등급이 높을수록 요구 강도가 커진다 (표 4.1-3)."""
    ec = [EXPOSURE_REQUIREMENTS[f"EC{i}"] for i in range(1, 5)]

    fck = [r.fck_min for r in ec]
    assert fck == sorted(fck)
    assert fck == [21.0, 24.0, 27.0, 30.0]


def test_minimum_strength_table():
    """표 4.1-3 의 최소 설계기준압축강도를 전부 확인한다."""
    expected = {
        "E0": 21.0,
        "EC1": 21.0, "EC2": 24.0, "EC3": 27.0, "EC4": 30.0,
        "ES1": 30.0, "ES2": 30.0, "ES3": 35.0, "ES4": 35.0,
        "EF1": 24.0, "EF2": 27.0, "EF3": 30.0, "EF4": 30.0,
        "EA1": 27.0, "EA2": 30.0, "EA3": 30.0,
    }

    for code, fck_min in expected.items():
        assert EXPOSURE_REQUIREMENTS[code].fck_min == pytest.approx(fck_min), code


def test_cover_required_categories():
    """피복두께 규정은 노출범주 EC·ES 에만 적용된다 (KDS 14 20 40 4.1.4(2))."""
    for code, req in EXPOSURE_REQUIREMENTS.items():
        assert req.cover_required == code.startswith(("EC", "ES")), code


def test_check_durability_pass():
    """요구를 만족하는 경우를 확인한다."""
    res = check_durability(
        exposure_class="EC3", fck=30, cover=40, cover_min=40
    )

    assert res.ok
    assert res.ok_fck
    assert res.ok_cover


def test_check_durability_fail_strength():
    """강도가 부족하면 불만족으로 판정된다."""
    res = check_durability(exposure_class="ES3", fck=27)

    assert not res.ok
    assert not res.ok_fck


def test_check_durability_fail_cover():
    """피복두께가 부족하면 불만족으로 판정된다."""
    res = check_durability(
        exposure_class="EC4", fck=35, cover=30, cover_min=40
    )

    assert res.ok_fck
    assert not res.ok_cover
    assert not res.ok


def test_water_binder_ratio_is_informational():
    """물-결합재비는 KCS 에 위임되므로 판정에 쓰이지 않는다."""
    res = check_durability(
        exposure_class="EC4", fck=35, water_binder_ratio=0.90
    )

    assert res.water_binder_ratio == pytest.approx(0.90)
    assert res.ok


def test_check_durability_unchecked_items():
    """확인하지 않은 항목은 만족으로 처리된다."""
    res = check_durability(exposure_class="EC4", fck=35)

    assert res.ok
    assert res.cover is None
    assert res.cover_min is None


def test_check_durability_invalid():
    """정의되지 않은 노출등급은 예외가 발생한다."""
    with pytest.raises(ValueError, match="exposure_class"):
        check_durability(exposure_class="EX9", fck=30)


def test_governing_requirements():
    """여러 노출등급이 겹칠 때 가장 큰 최소 강도가 지배한다."""
    assert governing_requirements(
        exposure_classes=["EC3", "EF2", "ES3"]
    ) == pytest.approx(35.0)  # ES3

    assert governing_requirements(
        exposure_classes=["E0", "EC1"]
    ) == pytest.approx(21.0)


def test_governing_requirements_invalid():
    """빈 목록이나 정의되지 않은 등급은 예외가 발생한다."""
    with pytest.raises(ValueError, match="exposure_classes"):
        governing_requirements(exposure_classes=[])

    with pytest.raises(ValueError, match="정의되지 않은"):
        governing_requirements(exposure_classes=["EC1", "EX9"])
