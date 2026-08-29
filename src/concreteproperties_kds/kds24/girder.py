r"""프리스트레스트 콘크리트 I형 거더 (KDS 24).

거더는 바닥판과 정반대다. 바닥판은 기준이 근사식을 주어 해석을 면제해 주지만,
거더는 **직접 풀어야 한다** — 트럭을 지간 위로 굴려 최대 단면력을 찾고
(:mod:`~concreteproperties_kds.kds24.live_load`), 프리스트레스 손실을 시간에 따라
쫓고(:mod:`~concreteproperties_kds.kds24.psc`), 긴장 직후와 사용 시의 응력을
단면의 위아래에서 각각 확인해야 한다.

**시공 단계가 단면을 바꾼다.** 이것이 PSC 거더 설계에서 가장 헷갈리는 대목이다.

1. **긴장 직후** — 거더만 있다. 바닥판은 아직 없다. 프리스트레스와 거더 자중만
   거더 단면에 작용한다. 이때는 **하연이 압축, 상연이 인장**이 되기 쉽다.
2. **바닥판 타설 중** — 여전히 거더 단면이다. 굳지 않은 바닥판은 하중일 뿐이다.
3. **합성 후** — 바닥판이 굳어 합성 단면이 된다. 2차 고정하중과 활하중만
   이 커진 단면이 받는다.

같은 거더의 같은 위치를 세 번 다른 단면 성질로 계산해야 한다는 뜻이다.

.. warning::
    :data:`EXAMPLE_SECTIONS` 의 단면 치수는 **예시이며 어떤 표준도가 아니다.**
    복부두께·하부플랜지 단부두께·경사면 높이만 한국도로공사 EX거더 연구보고서
    (2017)에서 확인한 값을 기본값으로 썼고, 형고와 플랜지 폭은 일반적인 PSC
    I형 거더의 비례로 잡은 것이다. 실제 설계에는 발주자의 표준도를 쓴다.

근거: KDS 24 14 21 1.5.7, 3.3, 4.1.1, 4.1.2 · KDS 24 10 11 4.6.3
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .materials import (
    PHI_C_ULS,
    PHI_S_ULS,
    characteristic_tensile_strength,
    design_compressive_strength,
    design_yield_strength,
    elastic_modulus,
    equivalent_block,
)
from .psc import (
    E_P,
    PrestressLosses,
    anchorage_set_loss,
    concrete_stress_limit_at_transfer,
    elastic_shortening_loss,
    friction_loss,
    long_term_loss,
    max_jacking_stress,
    relaxation_loss,
)
from .serviceability import concrete_stress_limit, tendon_stress_limit

# EX거더 연구보고서(한국도로공사, 2017)에서 확인한 값
EX_WEB_THICKNESS = 290.0
"""한계상태설계 최적화에 쓴 복부두께 (mm). 최소값은 240 mm 이다."""

EX_BOTTOM_FLANGE_TIP = 200.0
"""하부플랜지 단부 두께 (mm)."""

EX_BOTTOM_TAPER = 160.0
"""하부플랜지 상면 경사면 높이 (mm). 보고서의 범위는 120 ~ 160 mm 다."""

TENDON_COVER = 200.0
"""기본 긴장재 피복 (mm). 지간 중앙에서 거더 하연부터 긴장재 도심까지의 거리."""

EX_MAX_SPAN = 60.0
EX_MAX_DEPTH = 2700.0
"""EX거더의 적용 한계 — 경간장 60 m, 형고 2.7 m."""


def _segment_properties(
    y0: float, height: float, b0: float, b1: float
) -> tuple[float, float, float]:
    r"""폭이 선형으로 변하는 한 구간의 (면적, 단면1차, 단면2차) 를 정확히 적분한다.

    .. math::
        b(y) = b_0 + (b_1 - b_0)\frac{y - y_0}{h}

    Args:
        y0: 구간의 아래쪽 좌표 (mm)
        height: 구간의 높이 (mm)
        b0: 아래쪽 폭 (mm)
        b1: 위쪽 폭 (mm)

    Returns:
        (면적 mm², 밑면 기준 단면1차모멘트 mm³, 밑면 기준 단면2차모멘트 mm⁴)
    """
    h, db = height, b1 - b0

    if h <= 0:
        return 0.0, 0.0, 0.0

    area = h * (b0 + b1) / 2.0
    first = b0 * (y0 * h + h**2 / 2.0) + db * (y0 * h / 2.0 + h**2 / 3.0)
    second = b0 * (y0**2 * h + y0 * h**2 + h**3 / 3.0) + db * (
        y0**2 * h / 2.0 + 2.0 * y0 * h**2 / 3.0 + h**3 / 4.0
    )

    return area, first, second


@dataclass(frozen=True)
class SectionProperties:
    """한 단면의 기하 성질.

    Args:
        area: 단면적 (mm²)
        y_b: 밑면에서 도심까지의 거리 (mm)
        y_t: 도심에서 윗면까지의 거리 (mm)
        inertia: 도심축에 대한 단면2차모멘트 (mm⁴)
        height: 전체 높이 (mm)
    """

    area: float
    y_b: float
    y_t: float
    inertia: float
    height: float

    @property
    def z_b(self) -> float:
        """하연 단면계수 (mm³)."""
        return self.inertia / self.y_b

    @property
    def z_t(self) -> float:
        """상연 단면계수 (mm³)."""
        return self.inertia / self.y_t


@dataclass(frozen=True)
class IGirder:
    """프리스트레스트 콘크리트 I형 거더의 단면 형상.

    아래에서 위로 하부플랜지 → 경사부 → 복부 → 경사부 → 상부플랜지 순이다.

    Args:
        name: 단면 이름
        height: 형고 :math:`H` (mm)
        top_width: 상부플랜지 폭 (mm)
        top_thickness: 상부플랜지 단부 두께 (mm)
        top_taper: 상부플랜지 하면 경사면 높이 (mm)
        web: 복부 두께 (mm)
        bottom_width: 하부플랜지 폭 (mm)
        bottom_thickness: 하부플랜지 단부 두께 (mm)
        bottom_taper: 하부플랜지 상면 경사면 높이 (mm)
    """

    name: str
    height: float
    top_width: float
    top_thickness: float = 180.0
    top_taper: float = 150.0
    web: float = EX_WEB_THICKNESS
    bottom_width: float = 700.0
    bottom_thickness: float = EX_BOTTOM_FLANGE_TIP
    bottom_taper: float = EX_BOTTOM_TAPER

    def segments(self) -> list[tuple[float, float, float, float]]:
        """아래에서 위로 (시작 y, 높이, 아래 폭, 위 폭) 목록을 돌려준다.

        Raises:
            ValueError: 플랜지와 경사부의 합이 형고를 넘는 경우

        Returns:
            구간 목록
        """
        web_height = self.height - (
            self.bottom_thickness
            + self.bottom_taper
            + self.top_taper
            + self.top_thickness
        )

        if web_height < 0:
            msg = (
                f"플랜지와 경사부의 합이 형고 {self.height:.0f} mm 를 넘는다. "
                "형고를 키우거나 플랜지를 줄여야 한다."
            )
            raise ValueError(msg)

        y = 0.0
        out = []
        for h, b0, b1 in (
            (self.bottom_thickness, self.bottom_width, self.bottom_width),
            (self.bottom_taper, self.bottom_width, self.web),
            (web_height, self.web, self.web),
            (self.top_taper, self.web, self.top_width),
            (self.top_thickness, self.top_width, self.top_width),
        ):
            out.append((y, h, b0, b1))
            y += h

        return out

    def properties(self) -> SectionProperties:
        """단면 성질을 정확히 적분해 돌려준다.

        Returns:
            :class:`SectionProperties`
        """
        area = first = second = 0.0
        for y0, h, b0, b1 in self.segments():
            a, q, i = _segment_properties(y0=y0, height=h, b0=b0, b1=b1)
            area += a
            first += q
            second += i

        y_b = first / area

        return SectionProperties(
            area=area,
            y_b=y_b,
            y_t=self.height - y_b,
            inertia=second - area * y_b**2,
            height=self.height,
        )

    def first_moment_above(self, y: float) -> float:
        """높이 ``y`` 위쪽 면적의 도심축에 대한 단면1차모멘트 (mm³).

        비균열 전단강도 식 (4.1-9) 의 :math:`Q` 에 쓴다. 세그먼트를 정확히
        적분하므로 근사가 아니다.

        Args:
            y: 기준 높이. 거더 하연에서 잰다 (mm).

        Returns:
            단면1차모멘트 (mm³). ``y`` 가 형고 이상이면 0 이다.
        """
        props = self.properties()
        total = 0.0

        for y0, h, b0, b1 in self.segments():
            if h <= 0 or y0 + h <= y:
                continue

            # 세그먼트가 y 에 걸치면 윗부분만 잘라 쓴다
            cut = max(y, y0)
            b_cut = b0 + (b1 - b0) * (cut - y0) / h
            area, first, _ = _segment_properties(
                y0=cut, height=y0 + h - cut, b0=b_cut, b1=b1
            )
            total += first - area * props.y_b

        return total

    def composite(
        self,
        deck_width: float,
        deck_thickness: float,
        modular_ratio: float = 1.0,
        haunch: float = 0.0,
    ) -> SectionProperties:
        """바닥판을 얹은 합성 단면의 성질을 돌려준다.

        바닥판은 강도가 낮으므로 탄성계수비로 폭을 환산해 붙인다.

        Args:
            deck_width: 바닥판의 유효폭 (mm)
            deck_thickness: 바닥판 두께 (mm)
            modular_ratio: 바닥판 / 거더의 탄성계수비. 기본값 ``1.0``.
            haunch: 거더 상면과 바닥판 하면 사이의 헌치 높이 (mm). 기본값 ``0``.

        Returns:
            :class:`SectionProperties`. 밑면은 거더 하연이다.
        """
        girder = self.properties()
        b_eff = deck_width * modular_ratio
        y_deck = self.height + haunch + deck_thickness / 2.0
        a_deck = b_eff * deck_thickness

        area = girder.area + a_deck
        y_b = (girder.area * girder.y_b + a_deck * y_deck) / area
        inertia = (
            girder.inertia
            + girder.area * (y_b - girder.y_b) ** 2
            + b_eff * deck_thickness**3 / 12.0
            + a_deck * (y_deck - y_b) ** 2
        )
        height = self.height + haunch + deck_thickness

        return SectionProperties(
            area=area, y_b=y_b, y_t=height - y_b, inertia=inertia, height=height
        )


EXAMPLE_SECTIONS: dict[str, IGirder] = {
    "PSC-I 1.4m": IGirder(
        name="PSC-I 1.4m", height=1400.0, top_width=700.0, bottom_width=800.0
    ),
    "PSC-I 1.7m": IGirder(
        name="PSC-I 1.7m", height=1700.0, top_width=750.0, bottom_width=850.0
    ),
    "PSC-I 2.0m": IGirder(
        name="PSC-I 2.0m", height=2000.0, top_width=800.0, bottom_width=900.0
    ),
    "PSC-I 2.3m": IGirder(
        name="PSC-I 2.3m", height=2300.0, top_width=850.0, bottom_width=1000.0
    ),
    "PSC-I 2.7m": IGirder(
        name="PSC-I 2.7m", height=2700.0, top_width=900.0, bottom_width=1100.0
    ),
}
"""**예시 단면이며 어떤 표준도가 아니다.**

복부두께 290 mm, 하부플랜지 단부두께 200 mm, 경사면 높이 160 mm 만 한국도로공사
EX거더 연구보고서(2017)에서 확인한 값이고, 형고와 플랜지 폭은 일반적인 비례로
잡았다. 형고 2.7 m 는 EX거더의 적용 한계와 맞춘 것이다.
"""


@dataclass(frozen=True)
class GirderCheck:
    """PSC 거더 한 단면의 검토 결과.

    Args:
        girder: 거더 단면 성질
        composite: 합성 단면 성질
        losses: 프리스트레스 손실 내역
        p_i: 즉시 손실 후의 프리스트레스 힘 (N)
        p_e: 유효 프리스트레스 힘 (N)
        stresses: 단계별 (상연, 하연) 응력. 압축이 양수 (MPa)
        limits: 단계별 (압축 한계, 인장 한계) (MPa)
        m_rd: 설계휨강도 (kN·m)
        m_ed: 설계휨모멘트 (kN·m)
        flanged: 압축부가 바닥판을 넘어 거더로 들어갔는지 여부
        c_n: 중립축 깊이 (mm), 합성 단면 상연 기준
        checks: 검토 항목별 통과 여부
        adequate: 모든 항목을 만족하는지 여부
    """

    girder: SectionProperties
    composite: SectionProperties
    losses: PrestressLosses
    p_i: float
    p_e: float
    stresses: dict[str, tuple[float, float]]
    limits: dict[str, tuple[float, float]]
    m_rd: float
    m_ed: float
    flanged: bool = False
    c_n: float = 0.0
    checks: dict[str, bool] = field(default_factory=dict)
    adequate: bool = False


GAMMA_CONCRETE = 24.5
"""철근콘크리트의 단위중량 (kN/m³)."""


def design_girder(
    section: IGirder,
    span: float,
    girder_spacing: float = 2.5,
    deck_thickness: float = 240.0,
    haunch: float = 50.0,
    fck: float = 40.0,
    fck_transfer: float = 30.0,
    fck_deck: float = 27.0,
    a_p: float = 4200.0,
    fpu: float = 1860.0,
    fpy: float = 1600.0,
    eccentricity: float | None = None,
    n_tendon: int = 4,
    steel_class: int = 2,
    mu: float = 0.19,
    k_wobble: float = 0.004,
    theta: float = 0.12,
    anchorage_slip: float = 6.0,
    phi_creep: float = 2.0,
    eps_shrinkage: float = 300.0e-6,
    w_sdl: float = 3.0,
    distribution_factor: float = 0.6,
    phi_c: float = PHI_C_ULS,
    phi_s: float = PHI_S_ULS,
) -> GirderCheck:
    r"""단순 지지 PSC 거더 한 본을 설계하고 검토한다.

    **KDS 24 14 21 1.5.7, 4.1.1 · KDS 24 10 11 4.6.3 · KDS 24 12 21 4.3**

    시공 단계를 셋으로 나눈다.

    1. **긴장 직후** — 거더 단면이 프리스트레스와 거더 자중을 받는다.
    2. **바닥판 타설** — 여전히 거더 단면. 굳지 않은 바닥판은 하중일 뿐이다.
    3. **합성 후** — 2차 고정하중과 활하중만 합성 단면이 받는다.

    .. note::
        활하중의 거더 분배는 KDS 24 10 11 4.6.3 의 분배계수 표를 따라야 하는데,
        이 모듈은 그 표를 구현하지 않는다. ``distribution_factor`` 로 직접
        넣는다. 기본값 0.6 은 전형적인 다거더교의 값이지만 **설계에 그대로 쓰면
        안 된다.**

    Args:
        section: 거더 단면
        span: 지간 (m)
        girder_spacing: 거더 중심 간격 (m). 기본값 ``2.5``.
        deck_thickness: 바닥판 두께 (mm). 기본값 ``240``.
        haunch: 헌치 높이 (mm). 기본값 ``50``.
        fck: 거더 콘크리트 기준압축강도 (MPa). 기본값 ``40``.
        fck_transfer: 긴장 시점의 콘크리트 강도 (MPa). 기본값 ``30``.
        fck_deck: 바닥판 콘크리트 기준압축강도 (MPa). 기본값 ``27``.
        a_p: 긴장재 전체 단면적 (mm²). 기본값 ``4200``.
        fpu: 긴장재 기준인장강도 (MPa). 기본값 ``1860``.
        fpy: 긴장재 기준항복강도 (MPa). 기본값 ``1600``.
        eccentricity: 지간 중앙에서 거더 도심 아래로의 편심 (mm).
            ``None`` 이면 도심에서 하연까지의 75 % 로 잡는다.
        n_tendon: 순차 긴장하는 긴장재 개수. 기본값 ``4``.
        steel_class: 릴랙세이션 등급. 기본값 ``2`` (저릴랙세이션).
        mu: 곡률마찰계수. 기본값 ``0.19``.
        k_wobble: 파상마찰계수 (/m). 기본값 ``0.004``.
        theta: 누적 각변화량 (rad). 기본값 ``0.12``.
        anchorage_slip: 정착장치 활동량 (mm). 기본값 ``6.0``.
        phi_creep: 크리프계수. 기본값 ``2.0``.
        eps_shrinkage: 건조수축 변형률. 기본값 ``300e-6``.
        w_sdl: 2차 고정하중 (kN/m). 기본값 ``3.0``.
        distribution_factor: 활하중의 거더 분배계수. 기본값 ``0.6``.
        phi_c: 콘크리트 재료계수. 기본값 ``0.65``.
        phi_s: 강재 재료계수. 기본값 ``0.90``.

    Returns:
        :class:`GirderCheck`
    """
    from .live_load import girder_live_load
    from .loads import COMBINATIONS_BY_NAME

    girder = section.properties()
    e_c_girder = elastic_modulus(fck=fck)
    e_c_deck = elastic_modulus(fck=fck_deck)
    e_c_transfer = elastic_modulus(fck=fck_transfer)

    composite = section.composite(
        deck_width=girder_spacing * 1000.0,
        deck_thickness=deck_thickness,
        modular_ratio=e_c_deck / e_c_girder,
        haunch=haunch,
    )

    # 기본 편심 — 긴장재 도심을 거더 하연에서 200 mm 위(하부 플랜지 안)에 둔다
    e = max(girder.y_b - TENDON_COVER, 0.0) if eccentricity is None else eccentricity
    y_p = girder.y_b - e  # 거더 하연에서 긴장재까지 (mm)
    d_p = composite.height - y_p  # 합성 단면 상연에서 긴장재까지

    # ── 하중 (kN/m, kN·m) ────────────────────────────────────────────────
    w_girder = GAMMA_CONCRETE * girder.area / 1e6
    w_deck = GAMMA_CONCRETE * girder_spacing * deck_thickness / 1000.0
    m_girder = w_girder * span**2 / 8.0
    m_deck = w_deck * span**2 / 8.0
    m_sdl = w_sdl * span**2 / 8.0
    m_live = girder_live_load(span=span, step=0.05).moment * distribution_factor

    # ── 프리스트레스 ─────────────────────────────────────────────────────
    f_jack = max_jacking_stress(fpu=fpu, fpy=fpy)
    p_jack = f_jack * a_p

    d_friction = (
        friction_loss(p_o=p_jack, theta=theta, x=span / 2.0, mu=mu, k=k_wobble) / a_p
    )
    d_anchor = (
        anchorage_set_loss(slip=anchorage_slip, length=span * 1000.0, a_p=a_p, e_p=E_P)
        / a_p
    )

    f_after_friction = f_jack - d_friction - d_anchor
    p_after = f_after_friction * a_p

    # 긴장재 위치의 콘크리트 응력 (프리스트레스만)
    f_cpo = p_after / girder.area + p_after * e**2 / girder.inertia
    d_elastic = (
        elastic_shortening_loss(
            a_p=a_p,
            delta_fc=f_cpo,
            e_cm=e_c_transfer,
            n_tendon=n_tendon,
            post_tension=True,
        )
        / a_p
    )

    f_pi = f_after_friction - d_elastic
    p_i = f_pi * a_p

    # 장기 손실
    d_relax = relaxation_loss(f_pi=f_pi, fpu=fpu, steel_class=steel_class)
    f_c_perm = -(m_girder + m_deck + m_sdl) * 1e6 * e / girder.inertia
    d_long = long_term_loss(
        eps_shrinkage=eps_shrinkage,
        delta_f_pr=d_relax,
        phi_creep=phi_creep,
        f_c_permanent=f_c_perm,
        f_cpo=p_i / girder.area + p_i * e**2 / girder.inertia,
        a_p=a_p,
        a_c=girder.area,
        i_c=girder.inertia,
        z_cp=e,
        e_cm=e_c_girder,
    )
    f_pe = f_pi - d_long
    p_e = f_pe * a_p

    losses = PrestressLosses(
        f_jack=f_jack,
        friction=d_friction,
        anchorage=d_anchor,
        elastic=d_elastic,
        f_pi=f_pi,
        long_term=d_long,
        f_pe=f_pe,
        immediate_ratio=1.0 - f_pi / f_jack,
        total_ratio=1.0 - f_pe / f_jack,
    )

    # ── 응력 (압축 양수, MPa) ────────────────────────────────────────────
    def girder_stress(p: float, moment: float) -> tuple[float, float]:
        """거더 단면의 (상연, 하연) 응력."""
        top = p / girder.area - p * e / girder.z_t + moment * 1e6 / girder.z_t
        bot = p / girder.area + p * e / girder.z_b - moment * 1e6 / girder.z_b
        return top, bot

    top_transfer, bot_transfer = girder_stress(p_i, m_girder)

    # 사용 시 — 합성 전 하중은 거더 단면, 합성 후 하중은 합성 단면
    y_girder_top_comp = composite.y_b - section.height
    z_t_girder_in_comp = composite.inertia / abs(y_girder_top_comp)

    def service_stress(m_after: float) -> tuple[float, float]:
        """합성 후 하중 m_after 를 얹은 (거더 상연, 거더 하연) 응력."""
        top, bot = girder_stress(p_e, m_girder + m_deck)
        top += (
            m_after
            * 1e6
            / z_t_girder_in_comp
            * (1.0 if y_girder_top_comp < 0 else -1.0)
        )
        bot -= m_after * 1e6 / composite.z_b
        return top, bot

    # 영응력 한계상태는 지속하중(사용Ⅴ 근사), 균열 여부는 전 하중으로 본다
    top_sustained, bot_sustained = service_stress(m_sdl)
    top_service, bot_service = service_stress(m_sdl + m_live)

    f_deck_top = (m_sdl + m_live) * 1e6 / composite.z_t * (e_c_deck / e_c_girder)

    stresses = {
        "긴장 직후": (top_transfer, bot_transfer),
        "지속하중": (top_sustained, bot_sustained),
        "사용": (top_service, bot_service),
        "바닥판 상연": (f_deck_top, 0.0),
    }
    limits = {
        "긴장 직후": (
            concrete_stress_limit_at_transfer(fck_t=fck_transfer),
            0.0,
        ),
        "지속하중": (concrete_stress_limit(fck=fck, sustained=True), 0.0),
        "사용": (
            concrete_stress_limit(fck=fck),
            -characteristic_tensile_strength(fck=fck),
        ),
        "바닥판 상연": (concrete_stress_limit(fck=fck_deck), 0.0),
    }

    # ── 극한 휨강도 ──────────────────────────────────────────────────────
    f_cd_deck = design_compressive_strength(fck=fck_deck, phi_c=phi_c)
    f_cd_girder = design_compressive_strength(fck=fck, phi_c=phi_c)
    f_pd = design_yield_strength(fy=fpy, phi_s=phi_s)
    alpha_eq, beta_eq = equivalent_block(fck=fck_deck, phi_c=phi_c)

    # (alpha, beta) 를 직사각형 블록 (eta, lambda) 로 환산한다.
    # C = alpha f_cd b c 이고 합력이 연단에서 beta c 이므로,
    # 깊이 a = 2 beta c 에 평균응력 eta f_cd 가 작용하는 블록과 같다.
    lam = 2.0 * beta_eq
    eta = alpha_eq / lam

    t_force = a_p * f_pd
    b_eff = girder_spacing * 1000.0
    c_deck_full = eta * f_cd_deck * b_eff * deck_thickness

    if t_force <= c_deck_full:
        # 압축부가 바닥판 안에서 끝난다
        flanged = False
        a_block = t_force / (eta * f_cd_deck * b_eff)
        m_rd = t_force * (d_p - a_block / 2.0) / 1e6
    else:
        # 바닥판을 다 쓰고 거더 상부플랜지로 들어간다 — T형 해석
        flanged = True
        residual = t_force - c_deck_full
        a_web = residual / (eta * f_cd_girder * section.top_width)
        a_block = deck_thickness + haunch + a_web
        m_rd = (
            c_deck_full * (d_p - deck_thickness / 2.0)
            + residual * (d_p - deck_thickness - haunch - a_web / 2.0)
        ) / 1e6

    c_n = a_block / lam

    loads = {"DC": m_girder + m_deck + m_sdl, "LL": m_live}
    m_ed = COMBINATIONS_BY_NAME["극한Ⅰ"].evaluate(loads=loads)

    checks = {
        "긴장 직후 압축": max(top_transfer, bot_transfer) <= limits["긴장 직후"][0],
        "긴장 직후 인장": min(top_transfer, bot_transfer) >= -0.001,
        "지속하중 압축": max(top_sustained, bot_sustained) <= limits["지속하중"][0],
        "지속하중 영응력": min(top_sustained, bot_sustained) >= -0.001,
        "사용 압축": max(top_service, bot_service) <= limits["사용"][0],
        "사용 비균열": min(top_service, bot_service) >= limits["사용"][1],
        "바닥판 압축": f_deck_top <= limits["바닥판 상연"][0],
        "긴장재 응력": f_pe <= tendon_stress_limit(fpu=fpu),
        "설계휨강도": m_rd >= m_ed,
        "형고/지간": section.height / (span * 1000.0) >= 1 / 25.0,
    }

    return GirderCheck(
        girder=girder,
        composite=composite,
        losses=losses,
        p_i=p_i,
        p_e=p_e,
        stresses=stresses,
        limits=limits,
        m_rd=m_rd,
        m_ed=m_ed,
        flanged=flanged,
        c_n=c_n,
        checks=checks,
        adequate=all(checks.values()),
    )
