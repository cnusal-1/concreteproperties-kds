"""PSC I형 거더 단면과 설계 시험.

단면 성질은 손계산(사다리꼴 적분)과, 설계는 KDS 24 14 21 의 각 한계상태와
대조한다. :data:`EXAMPLE_SECTIONS` 는 표준도가 아니라 예시 단면이므로
치수 자체를 시험하지는 않고, 형상이 성립하는지만 확인한다.
"""

from __future__ import annotations

import pytest

from concreteproperties_kds.kds24 import (
    EX_MAX_DEPTH,
    EX_MAX_SPAN,
    EXAMPLE_SECTIONS,
    GAMMA_CONCRETE,
    TENDON_COVER,
    IGirder,
    design_girder,
)

STRAND = 138.7  # 15.2 mm 7연선 1가닥 (mm²)


# ── 단면 성질 ────────────────────────────────────────────────────────────
def test_rectangle_properties_are_exact():
    """직사각형으로 퇴화시키면 해석해와 정확히 같아야 한다.

    폭 400, 높이 1000 인 직사각형: A = 4.0e5, y_b = 500,
    I = 400 x 1000³/12 = 3.3333e10.
    """
    rect = IGirder(
        name="사각형",
        height=1000.0,
        top_width=400.0,
        top_thickness=0.0,
        top_taper=0.0,
        web=400.0,
        bottom_width=400.0,
        bottom_thickness=0.0,
        bottom_taper=0.0,
    )
    props = rect.properties()

    assert props.area == pytest.approx(400_000.0)
    assert props.y_b == pytest.approx(500.0)
    assert props.y_t == pytest.approx(500.0)
    assert props.inertia == pytest.approx(400.0 * 1000.0**3 / 12.0)


def test_section_modulus_and_height():
    """단면계수는 I / y 이고, y_b + y_t = 높이다."""
    props = EXAMPLE_SECTIONS["PSC-I 2.0m"].properties()

    assert props.y_b + props.y_t == pytest.approx(props.height)
    assert props.z_b == pytest.approx(props.inertia / props.y_b)
    assert props.z_t == pytest.approx(props.inertia / props.y_t)


def test_i_girder_centroid_is_below_mid_height():
    """하부플랜지가 상부보다 넓으므로 도심이 중앙보다 아래에 온다.

    PSC 거더에서 이 성질이 중요한 이유는 편심 때문이다. 도심이 낮아야
    긴장재를 도심에서 멀리 둘 수 있고, 그만큼 프리스트레스가 효율적이다.
    """
    for section in EXAMPLE_SECTIONS.values():
        props = section.properties()
        assert section.bottom_width > section.top_width, section.name
        assert props.y_b < props.height / 2.0, section.name


def test_segments_cover_full_height():
    """세그먼트의 높이 합이 거더 높이와 같아야 한다."""
    for section in EXAMPLE_SECTIONS.values():
        total = sum(height for _, height, _, _ in section.segments())
        assert total == pytest.approx(section.height), section.name


def test_example_sections_within_ex_girder_limits():
    """예시 단면의 형고가 EX거더 적용 한계(2.7 m) 안에 든다."""
    for section in EXAMPLE_SECTIONS.values():
        assert section.height <= EX_MAX_DEPTH, section.name

    assert EX_MAX_SPAN == 60.0


def test_deeper_section_has_larger_inertia():
    """형고가 커지면 단면2차모멘트도 커진다."""
    ordered = sorted(EXAMPLE_SECTIONS.values(), key=lambda s: s.height)
    inertias = [s.properties().inertia for s in ordered]

    assert inertias == sorted(inertias)


# ── 합성 단면 ────────────────────────────────────────────────────────────
def test_composite_adds_deck_area_by_modular_ratio():
    """합성 단면적 = 거더 + 환산 바닥판."""
    section = EXAMPLE_SECTIONS["PSC-I 2.0m"]
    girder = section.properties()
    n, b, t = 0.86, 2500.0, 240.0

    composite = section.composite(
        deck_width=b, deck_thickness=t, modular_ratio=n, haunch=50.0
    )

    assert composite.area == pytest.approx(girder.area + n * b * t)
    assert composite.height == pytest.approx(section.height + 50.0 + t)


def test_composite_raises_centroid_and_inertia():
    """바닥판이 붙으면 도심이 올라가고 단면2차모멘트가 커진다."""
    section = EXAMPLE_SECTIONS["PSC-I 2.0m"]
    girder = section.properties()
    composite = section.composite(
        deck_width=2500.0, deck_thickness=240.0, modular_ratio=0.86, haunch=50.0
    )

    assert composite.y_b > girder.y_b
    assert composite.inertia > girder.inertia
    # 하연 단면계수도 커져야 (합성 후 하중에 유리) 한다
    assert composite.z_b > girder.z_b


def test_first_moment_of_rectangle_is_exact():
    """직사각형의 도심 위 단면1차모멘트는 b (h/2)(h/4) 다.

    400 x 1000 이면 400 x 500 x 250 = 5.0e7 mm³.
    """
    rect = IGirder(
        name="사각형",
        height=1000.0,
        top_width=400.0,
        top_thickness=0.0,
        top_taper=0.0,
        web=400.0,
        bottom_width=400.0,
        bottom_thickness=0.0,
        bottom_taper=0.0,
    )

    assert rect.first_moment_above(500.0) == pytest.approx(5.0e7)


def test_first_moment_vanishes_at_both_edges():
    """전단면(y=0)과 빈 단면(y=H)의 단면1차모멘트는 모두 0 이다."""
    section = EXAMPLE_SECTIONS["PSC-I 2.0m"]

    assert section.first_moment_above(0.0) == pytest.approx(0.0, abs=1.0)
    assert section.first_moment_above(section.height) == pytest.approx(0.0, abs=1.0)


def test_first_moment_is_maximum_at_centroid():
    """단면1차모멘트는 도심에서 최대다 — 전단응력이 도심에서 최대인 이유다."""
    section = EXAMPLE_SECTIONS["PSC-I 2.0m"]
    y_b = section.properties().y_b
    q_max = section.first_moment_above(y_b)

    assert q_max > 0.0
    for y in (200.0, 600.0, 1000.0, 1400.0, 1800.0):
        assert section.first_moment_above(y) <= q_max + 1.0


# ── 설계 ────────────────────────────────────────────────────────────────
def test_design_girder_default_eccentricity():
    """기본 편심은 거더 하연에서 TENDON_COVER 만큼 띄운 위치다."""
    section = EXAMPLE_SECTIONS["PSC-I 2.0m"]
    girder = section.properties()

    result = design_girder(section=section, span=30.0, a_p=25 * STRAND)

    # p_e = f_pe * a_p 이고 하연 응력에 편심이 반영된다
    assert result.p_e < result.p_i
    assert girder.y_b - TENDON_COVER > 0.0


def test_design_girder_losses_are_ordered():
    """긴장 -> 즉시손실 -> 장기손실 순으로 응력이 줄어든다."""
    result = design_girder(
        section=EXAMPLE_SECTIONS["PSC-I 2.0m"], span=30.0, a_p=25 * STRAND
    )
    losses = result.losses

    assert losses.f_jack > losses.f_pi > losses.f_pe
    assert 0.0 < losses.immediate_ratio < losses.total_ratio < 0.35
    # 모든 손실 성분이 양수다
    for component in (
        losses.friction,
        losses.anchorage,
        losses.elastic,
        losses.long_term,
    ):
        assert component > 0.0


def test_design_girder_transfer_compression_within_limit():
    """긴장 직후 하연 압축이 0.6 f_ck(t) 를 넘지 않아야 한다."""
    result = design_girder(
        section=EXAMPLE_SECTIONS["PSC-I 2.0m"],
        span=30.0,
        a_p=25 * STRAND,
        fck_transfer=30.0,
    )

    assert result.stresses["긴장 직후"][1] <= 18.0
    assert result.checks["긴장 직후 압축"]


@pytest.mark.parametrize(
    ("name", "span", "strands"),
    [
        ("PSC-I 1.4m", 20.0, 16),
        ("PSC-I 1.7m", 25.0, 20),
        ("PSC-I 2.0m", 30.0, 25),
        ("PSC-I 2.0m", 35.0, 36),
        ("PSC-I 2.3m", 40.0, 42),
        ("PSC-I 2.7m", 45.0, 48),
        ("PSC-I 2.7m", 50.0, 61),
    ],
)
def test_design_girder_adequate_configurations(name, span, strands):
    """지간별로 정해 둔 강연선 수량이 모든 한계상태를 만족한다."""
    result = design_girder(
        section=EXAMPLE_SECTIONS[name], span=span, a_p=strands * STRAND
    )

    assert result.adequate, [k for k, v in result.checks.items() if not v]
    assert result.m_rd >= result.m_ed


@pytest.mark.parametrize(
    ("name", "span", "strands"),
    [
        ("PSC-I 1.4m", 20.0, 16),
        ("PSC-I 1.7m", 25.0, 20),
        ("PSC-I 2.0m", 30.0, 25),
        ("PSC-I 2.0m", 35.0, 36),
        ("PSC-I 2.3m", 40.0, 42),
        ("PSC-I 2.7m", 45.0, 48),
        ("PSC-I 2.7m", 50.0, 61),
    ],
)
def test_design_girder_fails_one_strand_short(name, span, strands):
    """강연선을 한 가닥 줄이면 어딘가 한계상태가 깨진다.

    앞 시험과 짝을 이루어, 위 수량이 그 지간의 최소값임을 뜻한다.
    """
    result = design_girder(
        section=EXAMPLE_SECTIONS[name], span=span, a_p=(strands - 1) * STRAND
    )

    assert not result.adequate


def test_short_span_governed_by_ultimate_long_span_by_service():
    """지간이 짧으면 극한 휨강도가, 길면 사용한계상태 균열이 지배한다.

    한계상태설계에서도 긴 PSC 거더는 사용한계상태가 단면을 정한다는 뜻이다.
    """
    short = design_girder(
        section=EXAMPLE_SECTIONS["PSC-I 1.4m"], span=20.0, a_p=15 * STRAND
    )
    long_span = design_girder(
        section=EXAMPLE_SECTIONS["PSC-I 2.7m"], span=50.0, a_p=60 * STRAND
    )

    assert not short.checks["설계휨강도"]
    assert short.checks["사용 비균열"]

    assert long_span.checks["설계휨강도"]
    assert not long_span.checks["사용 비균열"]


def test_flanged_branch_engages_on_deep_sections():
    """압축부가 바닥판을 넘으면 T형 단면으로 푼다."""
    shallow = design_girder(
        section=EXAMPLE_SECTIONS["PSC-I 1.4m"], span=20.0, a_p=16 * STRAND
    )
    deep = design_girder(
        section=EXAMPLE_SECTIONS["PSC-I 2.7m"], span=50.0, a_p=61 * STRAND
    )

    assert not shallow.flanged
    assert deep.flanged
    # T형으로 풀린 경우 중립축이 바닥판 두께보다 깊다
    assert deep.c_n > 240.0


def test_more_prestress_reduces_bottom_tension():
    """긴장재를 늘리면 사용 시 하연 인장이 줄어든다."""
    section = EXAMPLE_SECTIONS["PSC-I 2.0m"]
    kwargs = {"section": section, "span": 30.0}

    less = design_girder(a_p=24 * STRAND, **kwargs)
    more = design_girder(a_p=30 * STRAND, **kwargs)

    assert more.stresses["사용"][1] > less.stresses["사용"][1]


def test_longer_span_needs_more_prestress():
    """같은 단면에서 지간이 길어지면 필요 긴장력이 커진다."""
    section = EXAMPLE_SECTIONS["PSC-I 2.7m"]

    at_45 = design_girder(section=section, span=45.0, a_p=48 * STRAND)
    at_50 = design_girder(section=section, span=50.0, a_p=48 * STRAND)

    assert at_45.adequate
    assert not at_50.adequate
    assert at_50.m_ed > at_45.m_ed


def test_self_weight_uses_concrete_density():
    """자중은 단위중량 x 단면적으로 계산한다."""
    section = EXAMPLE_SECTIONS["PSC-I 2.0m"]
    props = section.properties()
    span = 30.0

    w_girder = GAMMA_CONCRETE * props.area / 1e6  # kN/m
    m_girder = w_girder * span**2 / 8.0

    # 긴장 직후 하연 응력을 자중 모멘트로 역산해 일치하는지 본다
    result = design_girder(section=section, span=span, a_p=25 * STRAND)
    e = props.y_b - TENDON_COVER
    expected = (
        result.p_i / props.area
        + result.p_i * e / props.z_b
        - m_girder * 1e6 / props.z_b
    )

    assert result.stresses["긴장 직후"][1] == pytest.approx(expected)
