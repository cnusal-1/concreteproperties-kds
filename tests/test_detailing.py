"""철근상세·정착·이음 검증 시험 (KDS 14 20 50, KDS 14 20 52)."""

from __future__ import annotations

import numpy as np
import pytest

from concreteproperties_kds.detailing import (
    BAR_PROPERTIES,
    LD_MIN,
    LDC_MIN,
    LDH_MIN,
    bar_area,
    bar_diameter,
    development_length_compression,
    development_length_hook,
    development_length_tension,
    development_length_tension_detailed,
    lap_splice_compression,
    lap_splice_tension,
    minimum_bar_spacing,
    minimum_cover,
    summarise_detailing,
)


def test_bar_properties():
    """철근 호칭별 지름·단면적을 확인한다."""
    assert bar_diameter("D22") == pytest.approx(22.2)
    assert bar_area("D22") == pytest.approx(387.1)
    assert bar_diameter("D10") == pytest.approx(9.53)
    assert len(BAR_PROPERTIES) == 12


def test_bar_area_consistent():
    """공칭 단면적이 공칭 지름의 원 면적과 대체로 일치한다."""
    for bar, (d_b, area) in BAR_PROPERTIES.items():
        assert area == pytest.approx(np.pi * d_b**2 / 4, rel=0.03), bar


def test_bar_invalid():
    """정의되지 않은 호칭은 예외가 발생한다."""
    with pytest.raises(ValueError, match="bar"):
        bar_diameter("D99")

    with pytest.raises(ValueError, match="bar"):
        bar_area("D99")


def test_minimum_cover():
    """최소 피복두께 표를 확인한다."""
    assert minimum_cover(condition="흙에영구히묻힘") == pytest.approx(75.0)
    assert minimum_cover(condition="옥내_보기둥") == pytest.approx(40.0)
    assert minimum_cover(
        condition="흙에접하거나옥외노출", bar="D22"
    ) == pytest.approx(50.0)
    assert minimum_cover(
        condition="흙에접하거나옥외노출", bar="D13"
    ) == pytest.approx(40.0)
    assert minimum_cover(
        condition="옥내_슬래브벽체장선", bar="D25"
    ) == pytest.approx(20.0)
    assert minimum_cover(
        condition="옥내_슬래브벽체장선", bar="D38"
    ) == pytest.approx(40.0)


def test_minimum_cover_high_strength():
    """fck >= 40 MPa 이면 10 mm 저감할 수 있다."""
    assert minimum_cover(condition="옥내_보기둥", fck=40) == pytest.approx(30.0)
    assert minimum_cover(condition="옥내_보기둥", fck=27) == pytest.approx(40.0)


def test_minimum_cover_invalid():
    """조건이 정의되지 않았거나 철근을 주지 않으면 예외가 발생한다."""
    with pytest.raises(ValueError, match="condition"):
        minimum_cover(condition="수중")

    with pytest.raises(ValueError, match="bar"):
        minimum_cover(condition="흙에접하거나옥외노출")


def test_minimum_bar_spacing():
    """철근 최소 순간격을 확인한다."""
    # 보 : max(db, 25)
    assert minimum_bar_spacing(bar="D22", member="보") == pytest.approx(25.0)
    assert minimum_bar_spacing(bar="D32", member="보") == pytest.approx(31.8)

    # 기둥 : max(1.5db, 40)
    assert minimum_bar_spacing(bar="D22", member="기둥") == pytest.approx(40.0)
    assert minimum_bar_spacing(bar="D32", member="기둥") == pytest.approx(1.5 * 31.8)

    # 골재 조건이 지배하는 경우
    assert minimum_bar_spacing(
        bar="D22", member="보", aggregate_size=25
    ) == pytest.approx(4 / 3 * 25)


def test_minimum_bar_spacing_invalid():
    """정의되지 않은 부재는 예외가 발생한다."""
    with pytest.raises(ValueError, match="member"):
        minimum_bar_spacing(bar="D22", member="슬래브")


def test_development_length_tension_simple():
    """인장 정착길이 약산식을 손계산과 대조한다.

    D22, fy = 400, fck = 27, 배근 조건 만족 :
    ld = 0.75 * 22.2 * 400 / sqrt(27) = 1281.7 mm
    """
    l_d = development_length_tension(bar="D22", fy=400, fck=27)

    assert l_d == pytest.approx(0.75 * 22.2 * 400 / np.sqrt(27), rel=1e-6)
    assert l_d == pytest.approx(1281.7, rel=1e-3)


def test_development_length_small_bar():
    """D19 미만은 계수가 작다."""
    l_d16 = development_length_tension(bar="D16", fy=400, fck=27)

    assert l_d16 == pytest.approx(0.60 * 15.9 * 400 / np.sqrt(27), rel=1e-6)


def test_development_length_unfavourable():
    """배근 조건을 만족하지 않으면 계수가 커진다."""
    l_ok = development_length_tension(bar="D22", fy=400, fck=27)
    l_ng = development_length_tension(
        bar="D22", fy=400, fck=27, favourable_spacing=False
    )

    assert l_ng == pytest.approx(l_ok * 1.13 / 0.75)


def test_development_length_top_bar():
    """상부철근은 1.3 배이다."""
    l_bot = development_length_tension(bar="D22", fy=400, fck=27)
    l_top = development_length_tension(bar="D22", fy=400, fck=27, top_bar=True)

    assert l_top == pytest.approx(1.3 * l_bot)


def test_development_length_alpha_beta_capped():
    """alpha*beta 는 1.7 을 넘지 않는다."""
    l_bot = development_length_tension(bar="D22", fy=400, fck=27)
    l_top_epoxy = development_length_tension(
        bar="D22", fy=400, fck=27, top_bar=True, epoxy_coated=True
    )

    # 1.3 * 1.2 = 1.56 <= 1.7
    assert l_top_epoxy == pytest.approx(1.56 * l_bot)

    l_top_epoxy_ng = development_length_tension(
        bar="D22",
        fy=400,
        fck=27,
        top_bar=True,
        epoxy_coated=True,
        favourable_spacing=False,
    )
    # 1.3 * 1.5 = 1.95 -> 1.7 로 제한
    l_ng = development_length_tension(
        bar="D22", fy=400, fck=27, favourable_spacing=False
    )
    assert l_top_epoxy_ng == pytest.approx(1.7 * l_ng)


def test_development_length_minimum():
    """정착길이는 300 mm 이상이다."""
    l_d = development_length_tension(bar="D10", fy=300, fck=60)

    assert l_d >= LD_MIN


def test_development_length_excess_reinforcement():
    """배치 철근량이 많으면 정착길이를 저감할 수 있다."""
    l_full = development_length_tension(bar="D22", fy=400, fck=27)
    l_reduced = development_length_tension(
        bar="D22", fy=400, fck=27, excess_reinforcement=0.8
    )

    assert l_reduced == pytest.approx(0.8 * l_full)


def test_development_length_detailed():
    """정밀식이 약산식보다 짧거나 비슷한지 확인한다."""
    l_simple = development_length_tension(bar="D22", fy=400, fck=27)
    l_detailed = development_length_tension_detailed(
        bar="D22", fy=400, fck=27, c=40, k_tr=15
    )

    # (c+Ktr)/db = 55/22.2 = 2.48
    confinement = min((40 + 15) / 22.2, 2.5)
    assert l_detailed == pytest.approx(
        0.90 * 22.2 * 400 / np.sqrt(27) / confinement
    )
    assert l_detailed < l_simple


def test_development_length_detailed_capped():
    """(c+Ktr)/db 는 2.5 로 제한된다."""
    l_a = development_length_tension_detailed(
        bar="D22", fy=400, fck=27, c=100, k_tr=100
    )
    l_b = development_length_tension_detailed(
        bar="D22", fy=400, fck=27, c=55.5, k_tr=0
    )

    assert l_a == pytest.approx(l_b)


def test_development_length_compression():
    """압축 정착길이를 손계산과 대조한다."""
    l_dc = development_length_compression(bar="D22", fy=400, fck=27)

    assert l_dc == pytest.approx(
        max(0.25 * 22.2 * 400 / np.sqrt(27), 0.043 * 22.2 * 400)
    )
    assert l_dc >= LDC_MIN


def test_development_length_compression_confined():
    """구속되면 0.75 배로 저감한다."""
    l_free = development_length_compression(bar="D32", fy=400, fck=27)
    l_conf = development_length_compression(
        bar="D32", fy=400, fck=27, confined=True
    )

    assert l_conf == pytest.approx(0.75 * l_free)


def test_development_length_hook():
    """표준갈고리 정착길이를 손계산과 대조한다."""
    l_dh = development_length_hook(bar="D22", fy=400, fck=27)

    assert l_dh == pytest.approx(0.24 * 22.2 * 400 / np.sqrt(27))
    assert l_dh >= max(8 * 22.2, LDH_MIN)


def test_development_length_hook_modifiers():
    """측면 피복과 구속에 의한 보정계수를 확인한다."""
    l_base = development_length_hook(bar="D32", fy=400, fck=27)
    l_cover = development_length_hook(
        bar="D32", fy=400, fck=27, side_cover=True
    )
    l_both = development_length_hook(
        bar="D32", fy=400, fck=27, side_cover=True, confined=True
    )

    assert l_cover == pytest.approx(0.7 * l_base)
    assert l_both == pytest.approx(max(0.7 * 0.8 * l_base, 8 * 31.8, LDH_MIN))


def test_development_length_hook_minimum():
    """갈고리 정착길이는 8db 와 150 mm 이상이다."""
    l_dh = development_length_hook(bar="D10", fy=300, fck=60)

    assert l_dh >= max(8 * 9.53, LDH_MIN)


def test_lap_splice_tension():
    """인장 겹침이음 길이를 확인한다."""
    l_d = development_length_tension(bar="D22", fy=400, fck=27)

    assert lap_splice_tension(l_d=l_d, splice_class="A") == pytest.approx(l_d)
    assert lap_splice_tension(l_d=l_d, splice_class="B") == pytest.approx(1.3 * l_d)
    assert lap_splice_tension(l_d=100.0, splice_class="A") == pytest.approx(300.0)

    with pytest.raises(ValueError, match="splice_class"):
        lap_splice_tension(l_d=l_d, splice_class="C")


def test_lap_splice_compression():
    """압축 겹침이음 길이를 확인한다."""
    l_s = lap_splice_compression(bar="D22", fy=400, fck=27)
    l_dc = development_length_compression(bar="D22", fy=400, fck=27)

    assert l_s == pytest.approx(max(0.072 * 400 * 22.2, l_dc, 300.0))


def test_lap_splice_compression_high_fy():
    """fy > 400 MPa 이면 다른 식을 쓴다."""
    l_s = lap_splice_compression(bar="D22", fy=500, fck=27)

    assert l_s >= (0.13 * 500 - 24) * 22.2 - 1e-6


def test_lap_splice_compression_low_fck():
    """fck < 21 MPa 이면 1/3 증가시킨다."""
    l_low = lap_splice_compression(bar="D22", fy=400, fck=18)
    l_norm = lap_splice_compression(bar="D22", fy=400, fck=21)

    assert l_low > l_norm


def test_summarise_detailing():
    """요약 객체의 각 값이 개별 함수와 일치한다."""
    summary = summarise_detailing(bar="D22", fy=400, fck=27)

    assert summary.d_b == pytest.approx(22.2)
    assert summary.l_d == pytest.approx(
        development_length_tension(bar="D22", fy=400, fck=27)
    )
    assert summary.l_dc == pytest.approx(
        development_length_compression(bar="D22", fy=400, fck=27)
    )
    assert summary.l_dh == pytest.approx(
        development_length_hook(bar="D22", fy=400, fck=27)
    )
    assert summary.l_s_tension_b == pytest.approx(1.3 * summary.l_d)
