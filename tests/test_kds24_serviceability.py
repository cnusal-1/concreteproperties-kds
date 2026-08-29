"""KDS 24 14 21 4.2 사용한계상태, 4.3 피로한계상태 시험.

값은 표 4.2-1 ~ 표 4.2-5, 식 (4.2-1) ~ 식 (4.2-7), 식 (4.3-1) ~ (4.3-2),
표 4.3-1 과 대조한다.
"""

from __future__ import annotations

import math

import pytest

from concreteproperties_kds.kds24 import (
    ES,
    concrete_stress_limit,
    coupler_fatigue_strength,
    crack_spacing,
    crack_spacing_unreinforced,
    crack_width,
    deflection_limit,
    effective_tension_depth,
    fatigue_check_required,
    fatigue_stress_range_limit,
    max_bar_diameter,
    max_bar_spacing,
    mean_tensile_strength,
    minimum_crack_reinforcement,
    minimum_design_grade,
    nonuniform_stress_factor,
    steel_stress_limit,
    strain_difference,
    stress_distribution_factor,
    tendon_stress_limit,
    web_effective_tensile_strength,
)


def test_exposure_sets_the_design_grade():
    """표 4.2-1 — 환경이 나쁠수록 등급이 올라간다."""
    dry_pt = minimum_design_grade(exposure="건조/수중", member="포스트텐션")
    marine_pt = minimum_design_grade(exposure="고부식성", member="포스트텐션")
    marine_pre = minimum_design_grade(exposure="고부식성", member="프리텐션")
    rc = minimum_design_grade(exposure="고부식성", member="철근콘크리트")

    assert dry_pt.grade == "D"
    assert marine_pt.grade == "C"
    assert marine_pre.grade == "B"
    assert rc.grade == "E"


def test_design_grade_carries_combination_and_crack_width():
    """표 4.2-2 — 등급이 검증 하중조합과 한계균열폭을 함께 정한다."""
    grade_b = minimum_design_grade(exposure="고부식성", member="프리텐션")
    grade_e = minimum_design_grade(exposure="건조/수중", member="철근콘크리트")

    assert grade_b.zero_stress_combination == "사용Ⅲ/Ⅳ"
    assert grade_b.crack_combination == "사용Ⅰ"
    assert grade_b.crack_width == pytest.approx(0.2)

    assert grade_e.zero_stress_combination is None
    assert grade_e.crack_combination == "사용Ⅴ"
    assert grade_e.crack_width == pytest.approx(0.3)


def test_unknown_exposure_or_member_raises():
    """표에 없는 값은 거부한다."""
    with pytest.raises(ValueError, match="노출 환경"):
        minimum_design_grade(exposure="보통", member="철근콘크리트")

    with pytest.raises(ValueError, match="부재 종류"):
        minimum_design_grade(exposure="부식성", member="강교")


def test_stress_limits():
    """4.2.2.1 — 0.45fck, 0.6fck, 0.8fy, 0.65fpu."""
    assert concrete_stress_limit(fck=40, sustained=True) == pytest.approx(18.0)
    assert concrete_stress_limit(fck=40) == pytest.approx(24.0)
    assert steel_stress_limit(fy=400) == pytest.approx(320.0)
    assert tendon_stress_limit(fpu=1860) == pytest.approx(1209.0)


def test_minimum_crack_reinforcement_is_a_force_balance():
    """식 (4.2-1) — 균열 직전 콘크리트 인장력을 철근이 받는다."""
    a_ct = 400.0 * 350.0
    f_ct = 2.6
    f_s = 400.0

    hand = 0.4 * 1.0 * a_ct * f_ct / f_s

    assert minimum_crack_reinforcement(a_ct=a_ct, f_ct=f_ct, f_s=f_s) == pytest.approx(
        hand
    )

    # 철근 응력을 낮추어 잡으면 더 많은 철근이 필요하다
    assert minimum_crack_reinforcement(
        a_ct=a_ct, f_ct=f_ct, f_s=200.0
    ) == pytest.approx(2.0 * hand)

    with pytest.raises(ValueError, match="f_s"):
        minimum_crack_reinforcement(a_ct=a_ct, f_ct=f_ct, f_s=0.0)


def test_stress_distribution_factor():
    """4.2.3.2(2) — 순수인장 1.0, 휨 복부는 0.4 에서 시작해 축압축으로 준다."""
    assert stress_distribution_factor(pure_tension=True) == pytest.approx(1.0)
    assert stress_distribution_factor(f_n=0.0, f_ct=3.0, h=500.0) == pytest.approx(0.4)

    # 축압축이 걸리면 인장영역이 줄어 k_c 가 작아진다
    with_axial = stress_distribution_factor(f_n=2.0, f_ct=3.0, h=500.0)

    assert 0.0 < with_axial < 0.4

    # h* 는 1,000 mm 에서 멈춘다
    deep = stress_distribution_factor(f_n=2.0, f_ct=3.0, h=2000.0)

    assert deep != with_axial


def test_nonuniform_stress_factor_interpolates():
    """4.2.3.2(2) — 300 mm 이하 1.0, 800 mm 이상 0.65, 사이는 보간."""
    assert nonuniform_stress_factor(width=200.0) == pytest.approx(1.0)
    assert nonuniform_stress_factor(width=300.0) == pytest.approx(1.0)
    assert nonuniform_stress_factor(width=550.0) == pytest.approx(0.825)
    assert nonuniform_stress_factor(width=800.0) == pytest.approx(0.65)
    assert nonuniform_stress_factor(width=1500.0) == pytest.approx(0.65)


@pytest.mark.parametrize(
    ("f_s", "expected"),
    [(160, 32), (200, 25), (240, 16), (280, 14), (320, 10), (360, 8)],
)
def test_max_bar_diameter_table(f_s, expected):
    """표 4.2-4 의 철근콘크리트 행."""
    assert max_bar_diameter(f_s=f_s) == pytest.approx(expected)


def test_max_bar_diameter_interpolates_and_limits():
    """표 밖의 응력은 보간하거나 거부한다."""
    assert max_bar_diameter(f_s=180) == pytest.approx(28.5)
    assert max_bar_diameter(f_s=100) == pytest.approx(32.0)  # 표 아래는 첫 행
    assert max_bar_diameter(f_s=200, member="프리스트레스트") == pytest.approx(16.0)

    with pytest.raises(ValueError, match="상한"):
        max_bar_diameter(f_s=400)

    with pytest.raises(ValueError, match="부재 종류"):
        max_bar_diameter(f_s=200, member="강교")


@pytest.mark.parametrize(
    ("f_s", "expected"),
    [(160, 300), (200, 250), (240, 200), (280, 150), (320, 100), (360, 50)],
)
def test_max_bar_spacing_table(f_s, expected):
    """표 4.2-5 의 철근콘크리트 순수휨 행."""
    assert max_bar_spacing(f_s=f_s) == pytest.approx(expected)


def test_max_bar_spacing_refuses_where_the_table_is_blank():
    """순수인장·PSC 는 280 MPa 를 넘으면 표에 값이 없다."""
    assert max_bar_spacing(f_s=280, member="철근콘크리트_인장") == pytest.approx(75.0)

    with pytest.raises(ValueError, match="다루지 않는다"):
        max_bar_spacing(f_s=300, member="철근콘크리트_인장")

    with pytest.raises(ValueError, match="다루지 않는다"):
        max_bar_spacing(f_s=300, member="프리스트레스트")


def test_effective_tension_depth_takes_the_smallest():
    """그림 4.2-1 — 2.5(h-d), (h-c)/3, h/2 중 가장 작은 값.

    철근이 연단 가까이 있으면 2.5(h-d) 가, 깊이 묻혀 있으면 (h-c)/3 이 이긴다.
    세 번째 항 h/2 는 c >= 0 인 한 (h-c)/3 <= h/3 < h/2 이므로 실제로는 결코
    지배하지 않는다.
    """
    assert effective_tension_depth(h=700, d=640, c=200) == pytest.approx(150.0)
    assert effective_tension_depth(h=700, d=600, c=200) == pytest.approx(
        (700 - 200) / 3
    )
    assert effective_tension_depth(h=300, d=200, c=50) == pytest.approx((300 - 50) / 3)

    for h, d, c in ((700, 640, 200), (700, 600, 200), (300, 200, 50)):
        assert effective_tension_depth(h=h, d=d, c=c) < h / 2


def test_crack_spacing_grows_with_cover_and_bar_size():
    """식 (4.2-7a) — 피복과 철근 지름이 크고 철근비가 낮을수록 균열이 드물다."""
    base = crack_spacing(c_c=40.0, d_b=16.0, rho_e=0.03)
    hand = 3.4 * 40.0 + 0.425 * 0.8 * 0.5 * 16.0 / 0.03

    assert base == pytest.approx(hand)
    assert crack_spacing(c_c=60.0, d_b=16.0, rho_e=0.03) > base
    assert crack_spacing(c_c=40.0, d_b=25.0, rho_e=0.03) > base
    assert crack_spacing(c_c=40.0, d_b=16.0, rho_e=0.01) > base

    # 원형철근·긴장재는 부착이 나빠 균열 간격이 두 배가 된다
    assert crack_spacing(
        c_c=40.0, d_b=16.0, rho_e=0.03, k_1=1.6
    ) - 3.4 * 40.0 == pytest.approx(2.0 * (base - 3.4 * 40.0))

    with pytest.raises(ValueError, match="rho_e"):
        crack_spacing(c_c=40.0, d_b=16.0, rho_e=0.0)


def test_crack_spacing_unreinforced():
    """식 (4.2-7b) — 1.3(h - c)."""
    assert crack_spacing_unreinforced(h=700.0, c=200.0) == pytest.approx(650.0)


def test_strain_difference_has_a_lower_bound():
    """식 (4.2-5) — 인장강화효과를 빼되 0.6 f_so/E_s 아래로는 내리지 않는다."""
    f_so = 200.0
    floor = 0.6 * f_so / ES

    # 철근비가 아주 낮으면 빼는 항이 커져 하한에 걸린다
    assert strain_difference(f_so=f_so, f_cte=2.9, rho_e=0.005, n=7.0) == pytest.approx(
        floor
    )

    # 철근비가 높으면 하한 위에 있다
    rich = strain_difference(f_so=f_so, f_cte=2.9, rho_e=0.05, n=7.0)

    assert rich > floor
    assert rich < f_so / ES

    with pytest.raises(ValueError, match="rho_e"):
        strain_difference(f_so=f_so, f_cte=2.9, rho_e=0.0, n=7.0)


def test_crack_width_is_spacing_times_strain():
    """식 (4.2-4) — w_k = l_r,max (eps_sm - eps_cm)."""
    result = crack_width(f_so=200.0, fck=30.0, rho_e=0.03, c_c=40.0, d_b=16.0)

    assert result.w_k == pytest.approx(result.crack_spacing * result.strain_difference)
    assert result.crack_spacing == pytest.approx(
        crack_spacing(c_c=40.0, d_b=16.0, rho_e=0.03)
    )
    assert result.strain_difference == pytest.approx(
        strain_difference(
            f_so=200.0, f_cte=mean_tensile_strength(fck=30.0), rho_e=0.03, n=7.0
        )
    )
    assert result.adequate


def test_crack_width_fails_at_high_steel_stress():
    """철근 응력이 높으면 균열폭 한계를 넘는다."""
    ok = crack_width(f_so=180.0, fck=30.0, rho_e=0.02, c_c=40.0, d_b=16.0, limit=0.2)
    ng = crack_width(f_so=320.0, fck=30.0, rho_e=0.02, c_c=40.0, d_b=16.0, limit=0.2)

    assert ok.adequate
    assert not ng.adequate
    assert ng.w_k > ok.w_k


def test_web_effective_tensile_strength_drops_under_compression():
    """식 (4.2-3) — 사압축이 클수록 복부의 유효인장강도가 준다."""
    plain = web_effective_tensile_strength(f_2=0.0, fck=40.0)
    stressed = web_effective_tensile_strength(f_2=0.3 * 40.0, fck=40.0)

    assert stressed == pytest.approx(plain * (1.0 - 0.8 * 0.3))
    assert stressed < plain


def test_deflection_limits():
    """4.2.4.1(2), (3)."""
    span = 30000.0

    assert deflection_limit(span=span) == pytest.approx(span / 800)
    assert deflection_limit(span=span, pedestrian=True) == pytest.approx(span / 1000)
    assert deflection_limit(span=span, cantilever=True) == pytest.approx(span / 300)
    assert deflection_limit(
        span=span, pedestrian=True, cantilever=True
    ) == pytest.approx(span / 375)


def test_fatigue_stress_range_limit():
    """식 (4.3-1), (4.3-2)."""
    assert fatigue_stress_range_limit() == pytest.approx(166.0)
    assert fatigue_stress_range_limit(f_min=100.0) == pytest.approx(133.0)
    assert fatigue_stress_range_limit(welded=True) == pytest.approx(110.0)
    assert fatigue_stress_range_limit(f_min=100.0, welded=True) == pytest.approx(77.0)

    # 압축(음수)이면 허용 진폭이 늘어난다
    assert fatigue_stress_range_limit(f_min=-50.0) == pytest.approx(182.5)


def test_coupler_fatigue_strength():
    """표 4.3-1 과 4.3.4(2) 의 증가 규정."""
    assert coupler_fatigue_strength("그라우트채움") == pytest.approx(126.0)
    assert coupler_fatigue_strength("V홈용접") == pytest.approx(84.0)
    assert coupler_fatigue_strength("기타") == pytest.approx(28.0)

    # 10만 회이면 168(6 - 5) = 168 MPa 를 더하지만 166 MPa 상한에 걸린다
    assert 168.0 * (6.0 - math.log10(1.0e5)) == pytest.approx(168.0)
    assert coupler_fatigue_strength("기타", n_cycles=1.0e5) == pytest.approx(166.0)

    # 1백만 회에서는 증가분이 0 이다
    assert coupler_fatigue_strength("기타", n_cycles=1.0e6) == pytest.approx(28.0)

    with pytest.raises(ValueError, match="이음부 종류"):
        coupler_fatigue_strength("접착이음")


def test_fatigue_check_can_be_skipped_when_compression_dominates():
    """4.3.1(4) — 압축이 활하중 인장의 두 배 이상이면 검증하지 않는다."""
    assert fatigue_check_required(f_dead_compression=5.0, f_live_tension=4.0)
    assert not fatigue_check_required(f_dead_compression=10.0, f_live_tension=4.0)
