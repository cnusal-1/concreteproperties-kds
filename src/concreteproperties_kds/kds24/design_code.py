r"""KDS 24 14 21 콘크리트교 설계기준(한계상태설계법)의 단면 해석.

:class:`KDS24` 는 :class:`~concreteproperties_kds.kds.KDS14202022` 와 같은
자리에 놓이는 설계기준 클래스지만, **안전율을 거는 방식이 다르다.**

재료계수가 이미 재료에 반영되어 있으므로 단면을 풀면 그 결과가 곧 설계강도다.
:meth:`design_bending_capacity` 가 :math:`\phi` 를 돌려주지 않는 이유가
여기 있다 — 곱할 것이 남아 있지 않다.

근거: KDS 24 14 21 1.4, 3.1, 4.1.1
"""

from __future__ import annotations

from math import isinf
from typing import TYPE_CHECKING

import concreteproperties.stress_strain_profile as ssp
from concreteproperties.design_codes.design_code import DesignCode
from concreteproperties.material import Concrete, SteelBar
from concreteproperties.post import DEFAULT_UNITS, si_n_mm

from .materials import (
    ES,
    PHI_C_ULS,
    PHI_S_ULS,
    curve_parameters,
    design_compressive_strength,
    design_profile,
    design_tensile_strength,
    design_yield_strength,
    elastic_modulus,
)

if TYPE_CHECKING:
    import concreteproperties.results as res
    from concreteproperties.concrete_section import ConcreteSection

MIN_ECCENTRICITY_RATIO = 30.0
"""최소편심 :math:`e_{min} = h/30` 의 분모 (KDS 24 14 21 4.1.1.2(5))."""

MIN_ECCENTRICITY_ABS = 20.0
"""최소편심의 하한 (mm) — 같은 조문."""


def minimum_eccentricity(h: float) -> float:
    r"""최소편심 :math:`e_{min}` 을 반환한다.

    **KDS 24 14 21 4.1.1.2(5)**

    .. math::

        e_{min} = \max\left(\frac{h}{30},\ 20\ \text{mm}\right)

    축력을 받는 대칭 배근 부재라도 이만큼의 편심이 작용하는 것으로 보고
    휨압축부재로 설계해야 한다. KDS 14 가 최대 축강도를
    :math:`\alpha\phi P_o` 로 잘라 같은 목적을 이루는 것과 대비된다.

    Args:
        h: 단면의 깊이 (mm)

    Returns:
        최소편심 (mm)
    """
    return max(h / MIN_ECCENTRICITY_RATIO, MIN_ECCENTRICITY_ABS)


def biaxial_exponent(n_ed: float, n_rd: float, shape: str = "직사각형") -> float:
    r"""2축 휨 검증식의 지수 :math:`\alpha` 를 반환한다.

    **KDS 24 14 21 4.1.1.3(3), 식 (4.1-4)**

    .. math::

        \left(\frac{M_{Ed,y}}{M_{Rd,y}}\right)^{\alpha} +
        \left(\frac{M_{Ed,z}}{M_{Rd,z}}\right)^{\alpha} \leq 1.0

    원형·타원형 단면은 :math:`\alpha = 2.0` 이고, 직사각형 단면은 축력비
    :math:`N_{Ed}/N_{Rd}` 에 따라 1.0(0.1 이하), 1.5(0.7), 2.0(1.0) 사이를
    선형보간한다.

    Args:
        n_ed: 계수하중에 의한 축력
        n_rd: 단면의 설계중심축압축강도
        shape: ``"직사각형"`` 또는 ``"원형"``. 기본값 ``"직사각형"``.

    Raises:
        ValueError: 정의되지 않은 단면 형상인 경우

    Returns:
        지수 :math:`\alpha`
    """
    if shape not in ("직사각형", "원형"):
        msg = 'shape 는 "직사각형" 또는 "원형" 이어야 합니다.'
        raise ValueError(msg)

    if shape == "원형":
        return 2.0

    ratio = 0.0 if n_rd == 0 else abs(n_ed / n_rd)

    if ratio <= 0.1:
        return 1.0

    if ratio >= 1.0:
        return 2.0

    if ratio <= 0.7:
        return 1.0 + 0.5 * (ratio - 0.1) / 0.6

    return 1.5 + 0.5 * (ratio - 0.7) / 0.3


class KDS24(DesignCode):
    r"""KDS 24 14 21 콘크리트교 설계기준(한계상태설계법).

    .. admonition:: KDS 14 와 무엇이 다른가

      두 기준은 같은 역학을 쓰지만 **안전율을 거는 자리가 다르다.**

      .. list-table::
         :header-rows: 1

         * -
           - KDS 14 (강도설계법)
           - KDS 24 (한계상태설계법)
         * - 콘크리트
           - :math:`\eta(0.85f_{ck})`
           - :math:`f_{cd} = \phi_c(0.85f_{ck})`, :math:`\phi_c = 0.65`
         * - 철근
           - :math:`f_y`
           - :math:`f_{yd} = \phi_s f_y`, :math:`\phi_s = 0.90`
         * - 단면
           - 공칭강도에 :math:`\phi` (0.65~0.85) 를 곱함
           - 곱하지 않음 — 재료계수가 이미 들어 있다
         * - 압축 상한
           - :math:`\alpha\phi P_o` 로 절단
           - 최소편심 :math:`e_{min} = \max(h/30,\ 20)` 강제

      그래서 :meth:`design_bending_capacity` 는 :math:`\phi` 를 돌려주지 않는다.

    Example:
        .. code-block:: python

            from concreteproperties import ConcreteSection
            from sectionproperties.pre.library import concrete_rectangular_section

            from concreteproperties_kds.kds24 import KDS24

            kds = KDS24()
            conc = kds.create_concrete_material(compressive_strength=40)
            steel = kds.create_steel_material(yield_strength=400)
            ...
            m_rd = kds.design_bending_capacity().m_x

    Attributes:
        phi_c: 콘크리트의 재료계수
        phi_s: 강재의 재료계수
        concrete_section: 할당된 단면 객체
    """

    def __init__(
        self,
        phi_c: float = PHI_C_ULS,
        phi_s: float = PHI_S_ULS,
    ) -> None:
        r"""설계기준 객체를 만든다.

        Args:
            phi_c: 콘크리트의 재료계수. 기본값 ``0.65`` (극한·극단상황한계상태).
                사용·피로한계상태를 검토할 때는 ``1.0`` 을 준다.
            phi_s: 강재의 재료계수. 기본값 ``0.90``.

        Raises:
            ValueError: 재료계수가 0 보다 크고 1 이하가 아닌 경우
        """
        super().__init__()

        for name, value in (("phi_c", phi_c), ("phi_s", phi_s)):
            if not 0 < value <= 1:
                msg = f"{name} 는 0 보다 크고 1 이하여야 합니다."
                raise ValueError(msg)

        self.phi_c = phi_c
        self.phi_s = phi_s

    def create_concrete_material(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        compressive_strength: float,
        m_c: float = 2300.0,
        colour: str = "lightgrey",
    ) -> Concrete:
        r"""KDS 24 14 21 에 따른 콘크리트 재료 객체를 반환한다.

        .. admonition:: 재료 가정

          - *탄성계수*: :math:`E_c = 0.077 m_c^{1.5}\sqrt[3]{f_{cm}}`
            (3.1.2.2(1))

          - *극한 응력-변형률 관계*: 포물선-직선, 최대값이 설계압축강도
            :math:`f_{cd} = \phi_c(0.85f_{ck})` (3.1.2.5(2), 3.1.2.6(1))

          - *사용 응력-변형률 관계*: 인장을 무시한 선형

          - *휨인장강도*: :math:`f_{td} = \phi_c f_{ctk}`,
            :math:`f_{ctk} = 0.70 \times 0.30 (f_{cm})^{2/3}` (3.1.2.6(2))

        Args:
            compressive_strength: 콘크리트 기준압축강도 :math:`f_{ck}` (MPa)
            m_c: 콘크리트의 단위질량 (kg/m\ :sup:`3`). 기본값 ``2300``.
            colour: 도시할 때 사용할 색. 기본값 ``"lightgrey"``.

        Raises:
            ValueError: ``compressive_strength`` 가 18 MPa 미만이거나 90 MPa 를
                초과하는 경우 (3.1.1(1))

        Returns:
            콘크리트 재료 객체
        """
        if compressive_strength < 18 or compressive_strength > 90:
            msg = "compressive_strength 는 18 MPa 이상 90 MPa 이하여야 합니다."
            raise ValueError(msg)

        e_c = elastic_modulus(fck=compressive_strength, m_c=m_c)
        _, _, eps_cu = curve_parameters(fck=compressive_strength)
        f_cd = design_compressive_strength(fck=compressive_strength, phi_c=self.phi_c)
        f_td = design_tensile_strength(fck=compressive_strength, phi_c=self.phi_c)

        return Concrete(
            name=f"fck {compressive_strength:.0f} MPa 콘크리트 (KDS 24 14 21)",
            density=m_c * 1e-9,
            stress_strain_profile=ssp.ConcreteLinearNoTension(
                elastic_modulus=e_c,
                ultimate_strain=eps_cu,
                compressive_strength=f_cd,
            ),
            ultimate_stress_strain_profile=design_profile(
                fck=compressive_strength, phi_c=self.phi_c
            ),
            flexural_tensile_strength=f_td,
            colour=colour,
        )

    def create_steel_material(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        yield_strength: float = 400,
        fracture_strain: float = 0.05,
        colour: str = "grey",
    ) -> SteelBar:
        r"""KDS 24 14 21 에 따른 철근 재료 객체를 반환한다.

        항복강도에 재료계수 :math:`\phi_s` 가 이미 곱해져 있다
        (:math:`f_{yd} = \phi_s f_y`). 탄성계수는 그대로 200,000 MPa 이므로
        항복변형률도 :math:`\phi_s` 배로 줄어든다.

        Args:
            yield_strength: 철근의 기준항복강도 :math:`f_y` (MPa). 기본값 ``400``.
            fracture_strain: 철근의 파단변형률. 기본값 ``0.05``.
            colour: 도시할 때 사용할 색. 기본값 ``"grey"``.

        Raises:
            ValueError: ``yield_strength`` 가 300 MPa 미만이거나 600 MPa 를
                초과하는 경우

        Returns:
            철근 재료 객체
        """
        if yield_strength < 300 or yield_strength > 600:
            msg = "yield_strength 는 300 MPa 이상 600 MPa 이하여야 합니다."
            raise ValueError(msg)

        f_yd = design_yield_strength(fy=yield_strength, phi_s=self.phi_s)

        return SteelBar(
            name=f"SD{yield_strength:.0f} 철근 (KDS 24 14 21)",
            density=7.85e-6,
            stress_strain_profile=ssp.SteelElasticPlastic(
                yield_strength=f_yd,
                elastic_modulus=ES,
                fracture_strain=fracture_strain,
            ),
            colour=colour,
        )

    def assign_concrete_section(
        self,
        concrete_section: ConcreteSection,
    ) -> None:
        """해석할 콘크리트 단면을 설계기준 객체에 할당한다.

        Args:
            concrete_section: 해석 대상 콘크리트 단면 객체

        Raises:
            ValueError: 단면에 메시화된 철근(``Steel``)이 포함된 경우
            ValueError: 단면에 격점철근(``SteelBar``)이 없는 경우
        """
        self.concrete_section = concrete_section

        if self.concrete_section.reinf_geometries_meshed:
            msg = "메시화된 철근(Steel)은 이 설계기준에서 지원하지 않습니다."
            raise ValueError(msg)

        if not self.concrete_section.reinf_geometries_lumped:
            msg = "단면에 철근(SteelBar)이 하나 이상 있어야 합니다."
            raise ValueError(msg)

        if self.concrete_section.default_units is DEFAULT_UNITS:
            self.concrete_section.default_units = si_n_mm
            self.concrete_section.gross_properties.default_units = si_n_mm

    def design_bending_capacity(
        self,
        theta: float = 0,
        n_design: float = 0,
    ) -> res.UltimateBendingResults:
        r"""설계 휨강도 :math:`M_{Rd}` 를 계산한다.

        **KDS 24 14 21 4.1.1.2**

        재료계수가 재료에 이미 들어 있으므로 결과가 곧 설계강도다. KDS 14 처럼
        뒤에 :math:`\phi` 를 곱하지 않으며, 그래서 축력에 따라 강도감소계수가
        달라지는 비선형 해도 풀 필요가 없다.

        Args:
            theta: 중립축의 각도 (라디안). 기본값 ``0``.
            n_design: 작용 축력 :math:`N_{Ed}` (압축이 양수). 기본값 ``0``.

        Returns:
            설계 휨강도 결과
        """
        return self.concrete_section.ultimate_bending_capacity(theta=theta, n=n_design)

    def moment_interaction_diagram(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        theta: float = 0,
        **kwargs,
    ) -> res.MomentInteractionResults:
        r"""설계 P-M 상관도를 생성한다.

        **KDS 24 14 21 4.1.1.2**

        재료계수가 재료에 들어 있으므로 곡선이 하나만 나온다. KDS 14 의
        상관도가 공칭과 설계 두 줄로 나오고 그 간격이 점마다 다른 것과 대비된다.

        Args:
            theta: 중립축의 각도 (라디안). 기본값 ``0``.
            **kwargs: :meth:`ConcreteSection.moment_interaction_diagram` 에
                그대로 전달할 인자

        Returns:
            설계 상관도
        """
        return self.concrete_section.moment_interaction_diagram(theta=theta, **kwargs)

    def biaxial_bending_diagram(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        n_design: float = 0,
        **kwargs,
    ) -> res.BiaxialBendingResults:
        """설계 2축 휨 상관도를 생성한다.

        Args:
            n_design: 작용 축력 (압축이 양수). 기본값 ``0``.
            **kwargs: 상위 메서드에 그대로 전달할 인자

        Returns:
            설계 2축 휨 상관도
        """
        return self.concrete_section.biaxial_bending_diagram(n=n_design, **kwargs)

    def squash_tensile_load(self) -> tuple[float, float]:
        r"""단면의 설계 순수압축 하중과 순수인장 하중을 계산한다.

        재료계수가 반영된 재료강도를 쓰므로 결과가 곧 설계값이다.

        Returns:
            :math:`(N_{Rd,c},\ N_{Rd,t})` — 압축이 양수
        """
        squash = 0.0
        tensile = 0.0

        for conc_geom in self.concrete_section.concrete_geometries:
            profile = conc_geom.material.ultimate_stress_strain_profile
            # get_compressive_strength() 는 기준압축강도(fck)를 돌려주므로,
            # 재료계수가 반영된 설계압축강도는 곡선의 최대값에서 읽는다.
            f_cd = max(profile.stresses)
            squash += f_cd * conc_geom.calculate_area()

        for steel_geom in self.concrete_section.reinf_geometries_lumped:
            profile = steel_geom.material.stress_strain_profile
            f_yd = profile.get_yield_strength()
            area = steel_geom.calculate_area()
            squash += f_yd * area
            tensile -= f_yd * area

        return squash, tensile

    def net_tensile_strain(self, theta: float = 0, d_n: float = 0) -> float:
        r"""최외단 인장철근의 순인장변형률을 계산한다.

        KDS 24 는 이 값으로 강도를 깎지 않지만, 연성 정도를 읽고 KDS 14 와
        비교하는 데 쓴다.

        Args:
            theta: 중립축의 각도 (라디안). 기본값 ``0``.
            d_n: 중립축 깊이. 기본값 ``0``.

        Returns:
            순인장변형률. 중립축이 단면 밖이면 ``inf`` 또는 ``-eps_cu``.
        """
        eps_cu = self.concrete_section.gross_properties.conc_ultimate_strain

        if isinf(d_n):
            return -eps_cu

        if d_n <= 0:
            return float("inf")

        d_t, _ = self.concrete_section.extreme_bar(theta=theta)

        return eps_cu * (d_t - d_n) / d_n

    def minimum_moment(self, n_design: float, h: float) -> float:
        r"""최소편심에 의한 최소 설계휨모멘트를 반환한다.

        **KDS 24 14 21 4.1.1.2(5)**

        .. math::

            M_{Ed,min} = N_{Ed}\,e_{min},
            \qquad e_{min} = \max(h/30,\ 20\ \text{mm})

        Args:
            n_design: 작용 축력 (N)
            h: 단면의 깊이 (mm)

        Returns:
            최소 설계휨모멘트 (N·mm)
        """
        return abs(n_design) * minimum_eccentricity(h=h)
