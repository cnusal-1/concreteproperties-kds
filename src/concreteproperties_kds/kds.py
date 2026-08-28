"""KDS 14 20 콘크리트구조 설계기준에 따른 설계기준 클래스.

``concreteproperties`` 의
:class:`~concreteproperties.design_codes.design_code.DesignCode` 를 상속하여,
국가건설기준 **KDS 14 20 (콘크리트구조 설계기준)** 의 강도설계법 규정을 임의
형상의 철근콘크리트 단면 해석에 적용한다.

적용 기준
---------
* KDS 14 20 01 : 콘크리트구조 설계(강도설계법) 일반사항
* KDS 14 20 10 : 콘크리트구조 해석과 설계 원칙
* KDS 14 20 20 : 콘크리트구조 휨 및 압축 설계기준
* KDS 14 20 30 : 콘크리트구조 사용성 설계기준
"""

from __future__ import annotations

from copy import deepcopy
from math import inf, isinf
from typing import TYPE_CHECKING

import concreteproperties.results as res
import concreteproperties.stress_strain_profile as ssp
import numpy as np
from concreteproperties.design_codes.design_code import DesignCode
from concreteproperties.material import Concrete, SteelBar
from concreteproperties.post import DEFAULT_UNITS, si_n_mm
from concreteproperties.utils import AnalysisError, create_known_progress
from rich.live import Live
from scipy.interpolate import interp1d
from scipy.optimize import brentq

if TYPE_CHECKING:
    from concreteproperties.concrete_section import ConcreteSection


# KDS 14 20 20 표 4.1-2 등가직사각형 응력블록의 계수
# fck (MPa) : 콘크리트 설계기준압축강도
# eps_cu    : 콘크리트 압축연단의 극한변형률
# eta       : 콘크리트 등가직사각형 압축응력블록의 크기를 나타내는 계수
#             (압축응력 = eta * 0.85 * fck)
# beta_1    : 등가직사각형 응력블록의 깊이 계수 (a = beta_1 * c)
STRESS_BLOCK_FCK = [40.0, 50.0, 60.0, 70.0, 80.0, 90.0]
STRESS_BLOCK_EPS_CU = [0.0033, 0.0032, 0.0031, 0.0030, 0.0029, 0.0028]
STRESS_BLOCK_ETA = [1.00, 0.97, 0.95, 0.91, 0.87, 0.84]
STRESS_BLOCK_BETA_1 = [0.80, 0.80, 0.76, 0.74, 0.72, 0.70]

# 철근 탄성계수 (KDS 14 20 10 4.3.3(2), 식 4.3-5) [MPa]
ES = 200.0e3

# KDS 14 20 10 4.3.3(2) 강도감소계수
PHI_TENSION = 0.85  # 인장지배단면
PHI_COMP_TIE = 0.65  # 압축지배단면 - 띠철근
PHI_COMP_SPIRAL = 0.70  # 압축지배단면 - 나선철근

# KDS 14 20 20 4.1.2 최대 설계 축강도 저감계수
ALPHA_MAX_TIE = 0.80  # 띠철근 기둥
ALPHA_MAX_SPIRAL = 0.85  # 나선철근 기둥


def stress_block_parameters(fck: float) -> tuple[float, float, float]:
    r"""등가직사각형 응력블록의 계수를 반환한다 (KDS 14 20 20 표 4.1-2).

    표에 없는 중간 강도는 선형보간하며, :math:`f_{ck} \leq 40` MPa 인 경우
    :math:`\varepsilon_{cu} = 0.0033`, :math:`\eta = 1.00`, :math:`\beta_1 = 0.80`
    으로 일정하다.

    Args:
        fck: 콘크리트 설계기준압축강도 (MPa)

    Returns:
        ``(eps_cu, eta, beta_1)`` — 극한변형률, 응력 강도 계수, 응력블록 깊이 계수
    """
    fck_c = max(fck, STRESS_BLOCK_FCK[0])

    eps_cu = float(interp1d(STRESS_BLOCK_FCK, STRESS_BLOCK_EPS_CU)(fck_c))
    eta = float(interp1d(STRESS_BLOCK_FCK, STRESS_BLOCK_ETA)(fck_c))
    beta_1 = float(interp1d(STRESS_BLOCK_FCK, STRESS_BLOCK_BETA_1)(fck_c))

    return eps_cu, eta, beta_1


def elastic_modulus(fck: float, m_c: float = 2300.0) -> float:
    r"""콘크리트의 탄성계수를 반환한다 (KDS 14 20 10 4.3.3).

    .. math::
        E_c = 0.077 \, m_c^{1.5} \sqrt[3]{f_{cm}}

    보통중량 콘크리트(:math:`m_c = 2300` kg/m\ :sup:`3`)에 대해서는 기준이 제시하는
    간편식 :math:`E_c = 8500 \sqrt[3]{f_{cm}}` 을 사용한다. 여기서
    :math:`f_{cm} = f_{ck} + \Delta f` 이며 :math:`\Delta f` 는
    :math:`f_{ck} \leq 40` MPa 일 때 4 MPa, :math:`f_{ck} \geq 60` MPa 일 때 6 MPa,
    그 사이는 선형보간한다.

    Args:
        fck: 콘크리트 설계기준압축강도 (MPa)
        m_c: 콘크리트의 단위질량 (kg/m\ :sup:`3`). 기본값 ``2300``.

    Returns:
        콘크리트 탄성계수 (MPa)
    """
    if fck <= 40:
        delta_f = 4.0
    elif fck >= 60:
        delta_f = 6.0
    else:
        delta_f = 4.0 + 2.0 * (fck - 40.0) / 20.0

    fcm = fck + delta_f

    # 보통중량 콘크리트(mc = 2300 kg/m^3)에 대해 기준이 제시하는 간편식
    if m_c == 2300.0:
        return 8500.0 * fcm ** (1 / 3)

    return 0.077 * m_c**1.5 * fcm ** (1 / 3)


def modulus_of_rupture(fck: float, lambda_c: float = 1.0) -> float:
    r"""콘크리트의 파괴계수(휨인장강도)를 반환한다 (KDS 14 20 30 4.2.1).

    .. math::
        f_r = 0.63 \lambda \sqrt{f_{ck}}

    Args:
        fck: 콘크리트 설계기준압축강도 (MPa)
        lambda_c: 경량콘크리트계수 :math:`\lambda` (KDS 14 20 10 4.3.3(2)). 보통중량
            콘크리트 ``1.0``, 모래경량 ``0.85``, 전경량 ``0.75``. 기본값 ``1.0``.

    Returns:
        파괴계수 (MPa)
    """
    return 0.63 * lambda_c * np.sqrt(fck)


def compression_controlled_strain_limit(fy: float) -> float:
    r"""압축지배변형률한계를 반환한다 (KDS 14 20 20 4.1.2).

    균형변형률상태에서의 최외단 인장철근의 순인장변형률, 즉 철근의 항복변형률
    :math:`\varepsilon_y = f_y / E_s` 이다.

    Args:
        fy: 철근의 설계기준항복강도 (MPa)

    Returns:
        압축지배변형률한계
    """
    return fy / ES


def tension_controlled_strain_limit(fy: float) -> float:
    r"""인장지배변형률한계를 반환한다 (KDS 14 20 20 4.1.2).

    :math:`f_y \leq 400` MPa 인 경우 0.005, :math:`f_y > 400` MPa 인 경우
    철근 항복변형률의 2.5배로 한다.

    Args:
        fy: 철근의 설계기준항복강도 (MPa)

    Returns:
        인장지배변형률한계
    """
    if fy <= 400:
        return 0.005

    return 2.5 * fy / ES


def minimum_net_tensile_strain(fy: float) -> float:
    r"""휨부재의 최소허용 순인장변형률을 반환한다 (KDS 14 20 20 4.1.2).

    계수 축력이 :math:`0.10 f_{ck} A_g` 보다 작은 휨부재의 최외단 인장철근의
    순인장변형률은 :math:`f_y \leq 400` MPa 인 경우 0.004 이상,
    :math:`f_y > 400` MPa 인 경우 항복변형률의 2.0배 이상이어야 한다.

    Args:
        fy: 철근의 설계기준항복강도 (MPa)

    Returns:
        최소허용 순인장변형률
    """
    if fy <= 400:
        return 0.004

    return 2.0 * fy / ES


def minimum_flexural_moment(m_cr: float) -> float:
    r"""휨부재가 확보해야 할 최소 설계휨강도를 반환한다 (KDS 14 20 20 4.2.2).

    .. math::
        \phi M_n \ge 1.2 M_{cr}

    :math:`M_{cr}` 은 KDS 14 20 30 식 (4.2-2) 에 따른 균열휨모멘트이다.

    Args:
        m_cr: 균열휨모멘트 (N·mm)

    Returns:
        요구 최소 설계휨강도 (N·mm)
    """
    return float(1.2 * m_cr)


def minimum_flexural_moment_alternative(m_u: float) -> float:
    r"""최소 철근량 규정의 대체 조건을 반환한다 (KDS 14 20 20 4.2.2(2)).

    해석에 필요한 철근량보다 1/3 이상 인장철근을 더 배치하여

    .. math::
        \phi M_n \ge \frac{4}{3} M_u

    를 만족하면 :func:`minimum_flexural_moment` 의 조건을 적용하지 않을 수 있다.

    Args:
        m_u: 계수 휨모멘트 (N·mm)

    Returns:
        요구 최소 설계휨강도 (N·mm)
    """
    return float(4.0 / 3.0 * m_u)


class KDS14202022(DesignCode):
    """KDS 14 20 (콘크리트구조 설계기준) 설계기준 클래스.

    강도설계법에 따라 공칭강도를 계산하고 KDS 14 20 10 4.3.3(2) 의 강도감소계수
    :math:`\\phi` 를 적용한 설계강도를 산정한다.

    .. note::

        이 설계기준 클래스는 :class:`~concreteproperties.material.Concrete` 와
        :class:`~concreteproperties.material.SteelBar` 재료만 지원한다. 메시화되는
        :class:`~concreteproperties.material.Steel` 재료(합성구조의 형강 등)는
        지원하지 않는다.

    Args:
        column_type: 압축부재의 횡철근 종류. ``"tie"`` (띠철근) 또는 ``"spiral"``
            (나선철근). 압축지배단면의 강도감소계수와 최대 설계 축강도의 저감계수를
            결정한다. 기본값 ``"tie"``.
    """

    def __init__(self, column_type: str = "tie") -> None:
        """KDS14202022 클래스를 초기화한다.

        Args:
            column_type: ``"tie"`` (띠철근) 또는 ``"spiral"`` (나선철근).
                기본값 ``"tie"``.

        Raises:
            ValueError: ``column_type`` 이 ``"tie"`` 또는 ``"spiral"`` 이 아닌 경우
        """
        super().__init__()

        if column_type not in ("tie", "spiral"):
            msg = 'column_type 은 "tie"(띠철근) 또는 "spiral"(나선철근) 이어야 합니다.'
            raise ValueError(msg)

        self.column_type = column_type
        self.phi_comp = PHI_COMP_SPIRAL if column_type == "spiral" else PHI_COMP_TIE
        self.alpha_max = ALPHA_MAX_SPIRAL if column_type == "spiral" else ALPHA_MAX_TIE

    def assign_concrete_section(
        self,
        concrete_section: ConcreteSection,
    ) -> None:
        """설계기준 객체에 콘크리트 단면을 할당한다.

        단면에 사용된 철근의 항복강도로부터 압축지배·인장지배 변형률한계를 결정하고,
        순수압축(squash) 하중과 순수인장 하중을 계산한다.

        Args:
            concrete_section: 해석 대상 콘크리트 단면 객체

        Raises:
            ValueError: 단면에 메시화된 철근(``Steel``)이 포함된 경우
            ValueError: 단면에 격점철근(``SteelBar``)이 없는 경우
        """
        self.concrete_section = concrete_section

        # 메시화된 철근 영역은 지원하지 않음
        if self.concrete_section.reinf_geometries_meshed:
            msg = "메시화된 철근(Steel)은 이 설계기준에서 지원하지 않습니다."
            raise ValueError(msg)

        if not self.concrete_section.reinf_geometries_lumped:
            msg = "단면에 철근(SteelBar)이 하나 이상 있어야 합니다."
            raise ValueError(msg)

        # 단위계가 지정되지 않았다면 SI (N, mm) 를 기본값으로 사용
        if self.concrete_section.default_units is DEFAULT_UNITS:
            self.concrete_section.default_units = si_n_mm
            self.concrete_section.gross_properties.default_units = si_n_mm

        # 단면 내 철근 중 가장 높은 항복강도로 변형률한계 결정 (보수적)
        fy_max = max(
            steel_geom.material.stress_strain_profile.get_yield_strength()
            for steel_geom in self.concrete_section.reinf_geometries_lumped
        )
        self.fy = fy_max
        self.eps_y = compression_controlled_strain_limit(fy=fy_max)
        self.eps_tl = tension_controlled_strain_limit(fy=fy_max)

        # 순수압축 하중과 순수인장 하중
        squash, tensile = self.squash_tensile_load()
        self.squash_load = squash
        self.tensile_load = tensile

    def create_concrete_material(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        compressive_strength: float,
        lambda_c: float = 1.0,
        m_c: float = 2300.0,
        colour: str = "lightgrey",
    ) -> Concrete:
        r"""KDS 14 20 에 따른 콘크리트 재료 객체를 반환한다.

        .. admonition:: 재료 가정

          - *단위질량*: 2300 kg/m\ :sup:`3` (2.3 x 10\ :sup:`-6` kg/mm\ :sup:`3`),
            KDS 14 20 10 4.3.3 의 보통중량 콘크리트

          - *탄성계수*: :math:`E_c = 0.077 m_c^{1.5} \sqrt[3]{f_{cm}}`
            (KDS 14 20 10 4.3.3)

          - *사용 응력-변형률 관계*: 인장을 무시한 선형 관계, 압축응력은
            :math:`0.85 f_{ck}` 에서 일정 (사용하중 상태의 균열단면 해석은
            KDS 14 20 30 에 따라 선형탄성으로 가정)

          - *극한 응력-변형률 관계*: 등가직사각형 응력블록, 압축응력
            :math:`\eta (0.85 f_{ck})`, 깊이 :math:`a = \beta_1 c`
            (KDS 14 20 20 4.1.1(8), 표 4.1-2)

          - *파괴계수*: :math:`f_r = 0.63 \lambda \sqrt{f_{ck}}`
            (KDS 14 20 30 4.2.1)

        Args:
            compressive_strength: 콘크리트 설계기준압축강도 :math:`f_{ck}` (MPa)
            lambda_c: 경량콘크리트계수 :math:`\lambda` (KDS 14 20 10 4.3.3(2)).
                기본값 ``1.0``.
            m_c: 콘크리트의 단위질량 (kg/m\ :sup:`3`). 기본값 ``2300``.
            colour: 도시할 때 사용할 콘크리트의 색. 기본값 ``"lightgrey"``.

        Raises:
            ValueError: ``compressive_strength`` 가 18 MPa 미만이거나 90 MPa 를
                초과하는 경우

        Returns:
            콘크리트 재료 객체
        """
        if compressive_strength < 18 or compressive_strength > 90:
            msg = "compressive_strength 는 18 MPa 이상 90 MPa 이하여야 합니다."
            raise ValueError(msg)

        name = f"fck {compressive_strength:.0f} MPa 콘크리트 (KDS 14 20)"

        e_c = elastic_modulus(fck=compressive_strength, m_c=m_c)
        eps_cu, eta, beta_1 = stress_block_parameters(fck=compressive_strength)
        f_r = modulus_of_rupture(fck=compressive_strength, lambda_c=lambda_c)

        return Concrete(
            name=name,
            density=m_c * 1e-9,
            stress_strain_profile=ssp.ConcreteLinearNoTension(
                elastic_modulus=e_c,
                ultimate_strain=eps_cu,
                compressive_strength=0.85 * compressive_strength,
            ),
            ultimate_stress_strain_profile=ssp.RectangularStressBlock(
                compressive_strength=compressive_strength,
                alpha=0.85 * eta,
                gamma=beta_1,
                ultimate_strain=eps_cu,
            ),
            flexural_tensile_strength=f_r,
            colour=colour,
        )

    def create_steel_material(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        yield_strength: float = 400,
        fracture_strain: float = 0.05,
        colour: str = "grey",
    ) -> SteelBar:
        r"""KDS 14 20 에 따른 철근 재료 객체를 반환한다.

        .. admonition:: 재료 가정

          - *단위질량*: 7850 kg/m\ :sup:`3` (7.85 x 10\ :sup:`-6` kg/mm\ :sup:`3`)

          - *탄성계수*: :math:`E_s = 200{,}000` MPa (KDS 14 20 10 4.3.3(2))

          - *응력-변형률 관계*: 완전탄소성 (KDS 14 20 20 4.1.1)

        Args:
            yield_strength: 철근의 설계기준항복강도 :math:`f_y` (MPa).
                SD300/SD400/SD500/SD600 에 대응. 기본값 ``400``.
            fracture_strain: 철근의 파단변형률. KDS 는 휨강도 산정 시 철근의
                변형률 상한을 규정하지 않으므로, KS D 3504 의 연신율을 참고한
                실용값을 사용한다. 기본값 ``0.05``.
            colour: 도시할 때 사용할 철근의 색. 기본값 ``"grey"``.

        Raises:
            ValueError: ``yield_strength`` 가 300 MPa 미만이거나 600 MPa 를
                초과하는 경우 (KDS 14 20 20 4.1.1: 휨·압축 설계에 사용하는
                :math:`f_y` 는 600 MPa 이하)

        Returns:
            철근 재료 객체
        """
        if yield_strength < 300 or yield_strength > 600:
            msg = "yield_strength 는 300 MPa 이상 600 MPa 이하여야 합니다 "
            msg += "(KDS 14 20 20 4.1.1)."
            raise ValueError(msg)

        return SteelBar(
            name=f"SD{yield_strength:.0f} 철근 (KDS 14 20)",
            density=7.85e-6,
            stress_strain_profile=ssp.SteelElasticPlastic(
                yield_strength=yield_strength,
                elastic_modulus=ES,
                fracture_strain=fracture_strain,
            ),
            colour=colour,
        )

    def squash_tensile_load(self) -> tuple[float, float]:
        r"""단면의 순수압축 하중과 순수인장 하중을 계산한다.

        KDS 14 20 20 4.1.2 의 공칭 축강도

        .. math::
            P_o = 0.85 f_{ck} (A_g - A_{st}) + f_y A_{st}

        를 임의 형상의 단면으로 일반화한 값과, 콘크리트의 인장강도를 무시한
        순수인장 강도 :math:`P_{nt} = -f_y A_{st}` 를 반환한다.

        .. note::

            ``concreteproperties`` 의 철근은 콘크리트 형상에서 해당 면적을 도려낸
            뒤 추가되므로, 콘크리트 형상의 면적은 이미 :math:`A_g - A_{st}` 이다.

        Returns:
            순수압축 하중과 순수인장 하중 (``squash_load``, ``tensile_load``)
        """
        squash_load = 0.0
        tensile_load = 0.0

        # 콘크리트 영역 : 0.85 fck (A_g - A_st)
        for conc_geom in self.concrete_section.concrete_geometries:
            area = conc_geom.calculate_area()
            ult_profile = conc_geom.material.ultimate_stress_strain_profile
            squash_load += area * 0.85 * ult_profile.get_compressive_strength()

        # 철근 영역 : f_y A_st
        for steel_geom in self.concrete_section.reinf_geometries_lumped:
            area = steel_geom.calculate_area()
            f_y = steel_geom.material.stress_strain_profile.get_yield_strength()

            squash_load += area * f_y
            tensile_load -= area * f_y

        return squash_load, tensile_load

    def max_axial_strength(self) -> tuple[float, float]:
        r"""최대 설계 축강도를 계산한다 (KDS 14 20 20 4.1.2).

        .. math::
            \phi P_{n,max} = \alpha \phi
            \left[ 0.85 f_{ck} (A_g - A_{st}) + f_y A_{st} \right]

        여기서 :math:`\alpha` 는 나선철근 기둥 0.85, 띠철근 기둥 0.80 이고,
        :math:`\phi` 는 압축지배단면의 강도감소계수(나선철근 0.70, 띠철근 0.65)이다.

        Returns:
            공칭 최대 축강도와 설계 최대 축강도
            (``n_max_nominal``, ``n_max_design``)
        """
        n_max_nominal = self.alpha_max * self.squash_load
        n_max_design = self.phi_comp * n_max_nominal

        return n_max_nominal, n_max_design

    def net_tensile_strain(
        self,
        theta: float,
        d_n: float,
    ) -> float:
        r"""최외단 인장철근의 순인장변형률 :math:`\varepsilon_t` 를 계산한다.

        .. math::
            \varepsilon_t = \varepsilon_{cu} \frac{d_t - c}{c}

        중립축 깊이가 무한대이면 순수압축 상태로 보아 :math:`-\varepsilon_{cu}` 를,
        0 이하이면 순수인장 상태로 보아 무한대를 반환한다.

        Args:
            theta: 중립축이 수평축과 이루는 각 (radian,
                :math:`-\pi \leq \theta \leq \pi`)
            d_n: 중립축 깊이 :math:`c`

        Returns:
            최외단 인장철근의 순인장변형률 (인장을 양(+)으로 함)
        """
        eps_cu = self.concrete_section.gross_properties.conc_ultimate_strain

        # 순수압축 : 단면 전체가 압축
        if isinf(d_n):
            return -eps_cu

        # 순수인장 : 압축영역이 없음
        if d_n <= 0:
            return inf

        d_t, _ = self.concrete_section.extreme_bar(theta=theta)

        return eps_cu * (d_t - d_n) / d_n

    def capacity_reduction_factor(
        self,
        eps_t: float,
    ) -> float:
        r"""강도감소계수를 반환한다 (KDS 14 20 10 4.3.3(2)).

        최외단 인장철근의 순인장변형률 :math:`\varepsilon_t` 에 따라

        - :math:`\varepsilon_t \leq \varepsilon_y` (압축지배단면):
          :math:`\phi = 0.65` (띠철근) 또는 :math:`0.70` (나선철근)
        - :math:`\varepsilon_t \geq \varepsilon_{t,tl}` (인장지배단면):
          :math:`\phi = 0.85`
        - 그 사이 (변화구간단면): 선형보간

        Args:
            eps_t: 최외단 인장철근의 순인장변형률

        Returns:
            강도감소계수 :math:`\phi`
        """
        if eps_t <= self.eps_y:
            return self.phi_comp

        if eps_t >= self.eps_tl:
            return PHI_TENSION

        return self.phi_comp + (PHI_TENSION - self.phi_comp) * (eps_t - self.eps_y) / (
            self.eps_tl - self.eps_y
        )

    def section_classification(
        self,
        eps_t: float,
    ) -> str:
        r"""단면의 분류를 반환한다 (KDS 14 20 20 4.1.2).

        Args:
            eps_t: 최외단 인장철근의 순인장변형률

        Returns:
            ``"압축지배단면"``, ``"변화구간단면"`` 또는 ``"인장지배단면"``
        """
        if eps_t <= self.eps_y:
            return "압축지배단면"

        if eps_t >= self.eps_tl:
            return "인장지배단면"

        return "변화구간단면"

    def check_flexural_ductility(
        self,
        theta: float = 0,
        n_design: float = 0,
    ) -> tuple[float, float, bool]:
        r"""휨부재의 최소허용변형률 조건을 검토한다 (KDS 14 20 20 4.1.2).

        계수 축력이 :math:`0.10 f_{ck} A_g` 보다 작은 휨부재는 최외단 인장철근의
        순인장변형률이 최소허용변형률 이상이어야 한다.

        Args:
            theta: 중립축이 수평축과 이루는 각 (radian). 기본값 ``0``.
            n_design: 계수 축력 :math:`N_d`. 기본값 ``0``.

        Returns:
            순인장변형률, 최소허용 순인장변형률, 만족 여부
            (``eps_t``, ``eps_t_min``, ``ok``)
        """
        _, ult_res, _ = self.ultimate_bending_capacity(
            theta=theta, n_design=n_design
        )
        eps_t = self.net_tensile_strain(theta=theta, d_n=ult_res.d_n)
        eps_t_min = minimum_net_tensile_strain(fy=self.fy)

        return eps_t, eps_t_min, bool(eps_t >= eps_t_min)

    def check_minimum_flexural_reinforcement(
        self,
        theta: float = 0,
        m_u: float | None = None,
        **kwargs,
    ) -> tuple[float, float, float, bool]:
        r"""휨부재의 최소 철근량 조건을 검토한다 (KDS 14 20 20 4.2.2).

        .. math::
            \phi M_n \ge 1.2 M_{cr}

        ``m_u`` 를 주면 대체 조건 :math:`\phi M_n \ge \frac{4}{3} M_u`
        (KDS 14 20 20 4.2.2(2)) 도 함께 검토하여, 둘 중 하나만 만족하면
        조건을 만족한 것으로 본다.

        Args:
            theta: 중립축이 수평축과 이루는 각 (radian). 기본값 ``0``.
            m_u: 계수 휨모멘트 (N·mm). 주면 대체 조건을 함께 검토한다.
                기본값 ``None``.
            kwargs: :meth:`calculate_cracked_properties` 에 전달할 인자

        Returns:
            설계휨강도, 균열휨모멘트, 요구 설계휨강도, 만족 여부
            (``phi_m_n``, ``m_cr``, ``m_required``, ``ok``)
        """
        f_res, _, _ = self.ultimate_bending_capacity(theta=theta, n_design=0)
        phi_m_n = float(np.hypot(f_res.m_x, f_res.m_y))

        cracked = self.concrete_section.calculate_cracked_properties(
            theta=theta, **kwargs
        )
        m_cr = float(cracked.m_cr)

        m_required = minimum_flexural_moment(m_cr=m_cr)
        ok = phi_m_n >= m_required

        if not ok and m_u is not None:
            m_required = min(
                m_required, minimum_flexural_moment_alternative(m_u=m_u)
            )
            ok = phi_m_n >= m_required

        return phi_m_n, m_cr, m_required, bool(ok)

    def ultimate_bending_capacity(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        theta: float = 0,
        n_design: float = 0,
    ) -> tuple[res.UltimateBendingResults, res.UltimateBendingResults, float]:
        r"""KDS 14 20 의 강도감소계수를 적용한 설계 휨강도를 계산한다.

        강도감소계수 :math:`\phi` 는 최외단 인장철근의 순인장변형률에 의존하고,
        순인장변형률은 다시 공칭 축력 :math:`N_u = N_d / \phi` 에 의존하므로
        :math:`\phi` 를 비선형으로 반복 계산한다.

        Args:
            theta: 중립축이 수평축과 이루는 각 (radian,
                :math:`-\pi \leq \theta \leq \pi`). 기본값 ``0``.
            n_design: 계수 축력 :math:`N_d`. 압축을 양(+)으로 한다. 기본값 ``0``.

        Raises:
            AnalysisError: 계수 축력이 최대 설계 축강도를 초과하는 경우
            AnalysisError: 계수 축력이 설계 인장강도를 초과하는 경우

        Returns:
            설계강도, 공칭강도, 강도감소계수
            (``factored_results``, ``unfactored_results``, ``phi``)
        """
        # 최대 설계 축강도까지 잘라낸 P-M 상관도 (2점) 로 주요 축력을 얻는다
        f_mi_res, _, _ = self.moment_interaction_diagram(
            theta=theta,
            control_points=[("N", 0.0)],
            n_points=2,
            progress_bar=False,
        )

        n_squash = f_mi_res.results[0].n
        n_decomp = f_mi_res.results[1].n
        n_tensile = f_mi_res.results[-1].n

        if n_design > n_squash:
            msg = f"계수 축력 N_d = {n_design:.1f} 이 최대 설계 축강도 "
            msg += f"phi*Pn,max = {n_squash:.1f} 을 초과합니다."
            raise AnalysisError(msg)

        if n_design < n_tensile:
            msg = f"계수 축력 N_d = {n_design:.1f} 이 설계 인장강도 "
            msg += f"phi*Pnt = {n_tensile:.1f} 을 초과합니다."
            raise AnalysisError(msg)

        # 압축지배 구간 (최대 축강도 ~ 무모멘트 압축점) : phi 는 압축지배값으로 일정
        if n_design > n_decomp:
            phi = self.phi_comp
            factor = (n_design - n_decomp) / (n_squash - n_decomp)
            squash = f_mi_res.results[0]
            decomp = f_mi_res.results[1]
            ult_res = res.UltimateBendingResults(
                default_units=self.concrete_section.default_units,
                theta=theta,
                d_n=inf,
                k_u=0,
                n=n_design / phi,
                m_x=(decomp.m_x + factor * (squash.m_x - decomp.m_x)) / phi,
                m_y=(decomp.m_y + factor * (squash.m_y - decomp.m_y)) / phi,
                m_xy=(decomp.m_xy + factor * (squash.m_xy - decomp.m_xy)) / phi,
            )
        # 일반 구간 : phi 를 비선형 반복 계산
        elif n_design >= 0:

            def non_linear_phi(phi_guess: float) -> float:
                trial = self.concrete_section.ultimate_bending_capacity(
                    theta=theta, n=n_design / phi_guess
                )
                eps_t = self.net_tensile_strain(theta=theta, d_n=trial.d_n)

                return self.capacity_reduction_factor(eps_t=eps_t) - phi_guess

            phi = brentq(
                f=non_linear_phi,
                a=self.phi_comp,
                b=PHI_TENSION,
                xtol=1e-4,
                rtol=1e-6,  # pyright: ignore [reportArgumentType]
            )
            ult_res = self.concrete_section.ultimate_bending_capacity(
                theta=theta, n=n_design / phi
            )
        # 인장 구간 : 순인장 상태이므로 인장지배단면
        else:
            phi = PHI_TENSION
            factor = n_design / n_tensile
            pure = f_mi_res.results[-2]
            ult_res = res.UltimateBendingResults(
                default_units=self.concrete_section.default_units,
                theta=theta,
                d_n=0,
                k_u=0,
                n=n_design / phi,
                m_x=(1 - factor) * pure.m_x / phi,
                m_y=(1 - factor) * pure.m_y / phi,
                m_xy=(1 - factor) * pure.m_xy / phi,
            )

        f_ult_res = deepcopy(ult_res)
        f_ult_res.n *= phi
        f_ult_res.m_x *= phi
        f_ult_res.m_y *= phi
        f_ult_res.m_xy *= phi

        return f_ult_res, ult_res, phi

    def moment_interaction_diagram(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        theta: float = 0,
        limits: list[tuple[str, float]] | None = None,
        control_points: list[tuple[str, float]] | None = None,
        labels: list[str] | None = None,
        n_points: int = 24,
        n_spacing: int | None = None,
        progress_bar: bool = True,
    ) -> tuple[res.MomentInteractionResults, res.MomentInteractionResults, list[float]]:
        r"""KDS 14 20 의 강도감소계수를 적용한 P-M 상관도를 생성한다.

        공칭 상관도의 각 점에서 최외단 인장철근의 순인장변형률을 구하고, 그에
        대응하는 강도감소계수를 곱하여 설계 상관도를 만든다. 압축측은
        KDS 14 20 20 4.1.2 의 최대 설계 축강도로 절단된다.

        사용 가능한 제어점은
        :meth:`concreteproperties.concrete_section.ConcreteSection.moment_interaction_diagram`
        를 참고한다.

        .. note::

            ``limits`` 나 ``control_points`` 에 ``"N"`` 을 사용하는 경우, ``"N"`` 은
            계수 축력이 아니라 공칭 축력 :math:`N_d / \phi` 를 의미한다.

        Args:
            theta: 중립축이 수평축과 이루는 각 (radian,
                :math:`-\pi \leq \theta \leq \pi`). 기본값 ``0``.
            limits: 상관도의 시작점과 끝점을 정의하는 제어점 2개. 기본값은 콘크리트
                압축연단 변형률이 0 이 되는 점부터 순수휨점까지인
                ``[("D", 1.0), ("N", 0.0)]``. 기본값 ``None``.
            control_points: 추가할 제어점 목록. 기본값은 균형점 ``[("fy", 1.0)]``.
                기본값 ``None``.
            labels: ``limits`` 와 ``control_points`` 에 붙일 이름. 기본값 ``None``.
            n_points: ``limits`` 사이에서 계산할 점의 수. 기본값 ``24``.
            n_spacing: 지정하면 ``n_points`` 대신 축력을 등간격으로 나누어 계산한다.
                기본값 ``None``.
            progress_bar: 진행바 표시 여부. 기본값 ``True``.

        Returns:
            설계 상관도, 공칭 상관도, 강도감소계수 목록
            (``factored_results``, ``unfactored_results``, ``phis``)
        """
        if limits is None:
            limits = [("D", 1.0), ("N", 0.0)]

        if control_points is None:
            control_points = [("fy", 1.0)]

        mi_res = self.concrete_section.moment_interaction_diagram(
            theta=theta,
            limits=limits,
            control_points=control_points,
            labels=labels,
            n_points=n_points,
            n_spacing=n_spacing,
            progress_bar=progress_bar,
        )

        theta = mi_res.results[0].theta

        # 압축측 : 최대 공칭 축강도 (alpha * Po) 로 상관도를 절단
        n_max_nominal, _ = self.max_axial_strength()

        # 상관도가 최대 축강도를 넘어서면 교점을 구해 수평으로 절단한다
        if mi_res.results[0].n > n_max_nominal:
            cut_res = self.concrete_section.ultimate_bending_capacity(
                theta=theta, n=n_max_nominal
            )
            mi_res.results = [r for r in mi_res.results if r.n < n_max_nominal]
            mi_res.results.insert(0, cut_res)

        # 무모멘트 압축점 (0, alpha * Po) 추가
        mi_res.results.insert(
            0,
            res.UltimateBendingResults(
                default_units=self.concrete_section.default_units,
                theta=theta,
                d_n=inf,
                k_u=0,
                n=n_max_nominal,
                m_x=0,
                m_y=0,
                m_xy=0,
            ),
        )

        # 인장측 : 순수인장 점을 추가
        mi_res.results.append(
            res.UltimateBendingResults(
                default_units=self.concrete_section.default_units,
                theta=theta,
                d_n=0,
                k_u=0,
                n=self.tensile_load,
                m_x=0,
                m_y=0,
                m_xy=0,
            )
        )

        f_mi_res = deepcopy(mi_res)
        phis = []

        for ult_res in f_mi_res.results:
            eps_t = self.net_tensile_strain(theta=theta, d_n=ult_res.d_n)
            phi = self.capacity_reduction_factor(eps_t=eps_t)

            ult_res.n *= phi
            ult_res.m_x *= phi
            ult_res.m_y *= phi
            ult_res.m_xy *= phi
            phis.append(phi)

        return f_mi_res, mi_res, phis

    def biaxial_bending_diagram(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        n_design: float = 0,
        n_points: int = 48,
        progress_bar: bool = True,
    ) -> tuple[res.BiaxialBendingResults, list[float]]:
        r"""KDS 14 20 의 강도감소계수를 적용한 2축 휨 상관도를 생성한다.

        Args:
            n_design: 계수 축력 :math:`N_d`. 기본값 ``0``.
            n_points: 계산할 점의 수. 기본값 ``48``.
            progress_bar: 진행바 표시 여부. 기본값 ``True``.

        Returns:
            설계 2축 휨 상관도와 강도감소계수 목록
            (``factored_results``, ``phis``)
        """
        f_bb_res = res.BiaxialBendingResults(
            default_units=self.concrete_section.default_units, n=n_design
        )
        phis = []

        d_theta = 2 * np.pi / n_points
        theta_list = np.linspace(start=-np.pi, stop=np.pi - d_theta, num=n_points)

        def bbcurve(progress=None):
            for theta in theta_list:
                f_ult_res, _, phi = self.ultimate_bending_capacity(
                    theta=theta, n_design=n_design
                )
                f_bb_res.results.append(f_ult_res)
                phis.append(phi)

                if progress:
                    progress.update(task, advance=1)

        if progress_bar:
            progress = create_known_progress()

            with Live(progress, refresh_per_second=10) as live:
                task = progress.add_task(
                    description="[red]2축 휨 상관도 생성 중",
                    total=n_points,
                )

                bbcurve(progress=progress)

                progress.update(
                    task,
                    description=(
                        "[bold green]:white_check_mark: 2축 휨 상관도 생성 완료"
                    ),
                )
                live.refresh()
        else:
            bbcurve()

        f_bb_res.results.append(f_bb_res.results[0])
        phis.append(phis[0])

        return f_bb_res, phis


# 편의를 위한 별칭
KDS = KDS14202022
