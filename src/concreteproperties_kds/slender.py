"""세장 기둥의 2차 효과 (KDS 14 20 20 4.4).

세장비 검토와 모멘트확대계수법을 구현한다. 단면 해석 자체는
:class:`~concreteproperties_kds.kds.KDS14202022` 가 담당하고, 이 모듈은
부재 길이 효과에 의한 모멘트 확대만 다룬다.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# 모멘트확대계수에 사용하는 강도감소계수 (KDS 14 20 20 4.4)
PHI_K = 0.75


def radius_of_gyration(
    section: str = "rectangular",
    h: float = 0.0,
    i_g: float | None = None,
    a_g: float | None = None,
) -> float:
    r"""단면의 회전반지름을 반환한다.

    **KDS 14 20 20 4.4.1**

    - 직사각형 단면 : :math:`r = 0.3h`
    - 원형 단면 : :math:`r = 0.25D`
    - 그 밖 : :math:`r = \sqrt{I_g / A_g}`

    Args:
        section: ``"rectangular"``, ``"circular"``, ``"general"``.
            기본값 ``"rectangular"``.
        h: 좌굴을 검토하는 방향의 단면 치수 (직사각형은 높이, 원형은 지름) (mm).
            기본값 ``0``.
        i_g: 총단면 2차모멘트 (mm\ :sup:`4`). ``"general"`` 에 필요.
            기본값 ``None``.
        a_g: 전체 단면적 (mm\ :sup:`2`). ``"general"`` 에 필요. 기본값 ``None``.

    Raises:
        ValueError: ``section`` 이 정의되지 않았거나 필요한 인자가 없는 경우

    Returns:
        회전반지름 (mm)
    """
    if section == "rectangular":
        return float(0.3 * h)

    if section == "circular":
        return float(0.25 * h)

    if section == "general":
        if i_g is None or a_g is None or a_g <= 0:
            msg = 'section="general" 에는 i_g 와 a_g 를 주어야 합니다.'
            raise ValueError(msg)

        return float(np.sqrt(i_g / a_g))

    msg = 'section 은 "rectangular", "circular", "general" 중 하나여야 합니다.'
    raise ValueError(msg)


def slenderness_ratio(k: float, l_u: float, r: float) -> float:
    r"""세장비 :math:`k l_u / r` 를 반환한다.

    Args:
        k: 유효길이계수
        l_u: 기둥의 비지지 길이 (mm)
        r: 회전반지름 (mm)

    Raises:
        ValueError: ``r`` 이 0 이하인 경우

    Returns:
        세장비
    """
    if r <= 0:
        msg = "r 은 0 보다 커야 합니다."
        raise ValueError(msg)

    return float(k * l_u / r)


def slenderness_limit(
    braced: bool = True,
    m1: float = 0.0,
    m2: float = 1.0,
) -> float:
    r"""세장효과를 무시할 수 있는 세장비 한계를 반환한다.

    **KDS 14 20 20 4.4.1**

    - 횡구속 골조 :
      :math:`\dfrac{k l_u}{r} \le 34 - 12\left(\dfrac{M_1}{M_2}\right) \le 40`
    - 비횡구속 골조 : :math:`\dfrac{k l_u}{r} \le 22`

    :math:`M_1/M_2` 는 단곡률이면 양(+), 복곡률이면 음(−) 이다.

    Args:
        braced: 횡구속 골조이면 ``True``. 기본값 ``True``.
        m1: 절댓값이 작은 단부 모멘트 (N·mm). 기본값 ``0``.
        m2: 절댓값이 큰 단부 모멘트 (N·mm). 기본값 ``1``.

    Returns:
        세장비 한계
    """
    if not braced:
        return 22.0

    ratio = m1 / m2 if m2 != 0 else 0.0
    ratio = max(min(ratio, 1.0), -1.0)

    return float(min(34.0 - 12.0 * ratio, 40.0))


def flexural_stiffness(
    e_c: float,
    i_g: float,
    beta_dns: float = 0.6,
    e_s: float | None = None,
    i_se: float | None = None,
) -> float:
    r"""좌굴하중 계산에 사용할 휨강성 :math:`EI` 를 반환한다.

    **KDS 14 20 20 4.4.2**

    철근 배치를 알면 정밀식

    .. math::
        EI = \frac{0.2 E_c I_g + E_s I_{se}}{1 + \beta_{dns}}

    을, 모르면 간편식

    .. math::
        EI = \frac{0.4 E_c I_g}{1 + \beta_{dns}}

    를 사용한다.

    Args:
        e_c: 콘크리트 탄성계수 (MPa)
        i_g: 총단면 2차모멘트 (mm\ :sup:`4`)
        beta_dns: 지속 축하중이 전체 축하중에 차지하는 비. 기본값 ``0.6``.
        e_s: 철근의 탄성계수 (MPa). 기본값 ``None``.
        i_se: 도심축에 대한 철근의 단면2차모멘트 (mm\ :sup:`4`).
            기본값 ``None``.

    Returns:
        휨강성 :math:`EI` (N·mm\ :sup:`2`)
    """
    if e_s is not None and i_se is not None:
        return float((0.2 * e_c * i_g + e_s * i_se) / (1.0 + beta_dns))

    return float(0.4 * e_c * i_g / (1.0 + beta_dns))


def critical_buckling_load(ei: float, k: float, l_u: float) -> float:
    r"""임계좌굴하중 :math:`P_c` 를 반환한다.

    **KDS 14 20 20 4.4.2**

    .. math::
        P_c = \frac{\pi^2 EI}{(k l_u)^2}

    Args:
        ei: 휨강성 (N·mm\ :sup:`2`)
        k: 유효길이계수
        l_u: 기둥의 비지지 길이 (mm)

    Raises:
        ValueError: ``k * l_u`` 가 0 이하인 경우

    Returns:
        임계좌굴하중 (N)
    """
    if k * l_u <= 0:
        msg = "k * l_u 는 0 보다 커야 합니다."
        raise ValueError(msg)

    return float(np.pi**2 * ei / (k * l_u) ** 2)


def moment_magnifier_braced(
    p_u: float,
    p_c: float,
    m1: float = 0.0,
    m2: float = 1.0,
    transverse_load: bool = False,
) -> tuple[float, float]:
    r"""횡구속 골조의 모멘트확대계수를 반환한다.

    **KDS 14 20 20 4.4.2**

    .. math::
        \delta_{ns} = \frac{C_m}{1 - \dfrac{P_u}{0.75 P_c}} \ge 1.0

    .. math::
        C_m = 0.6 + 0.4\frac{M_1}{M_2} \ge 0.4
        \quad (\text{횡하중이 없는 경우})

    횡하중이 작용하면 :math:`C_m = 1.0` 이다.

    Args:
        p_u: 계수 축력 (N)
        p_c: 임계좌굴하중 (N)
        m1: 절댓값이 작은 단부 모멘트 (N·mm). 기본값 ``0``.
        m2: 절댓값이 큰 단부 모멘트 (N·mm). 기본값 ``1``.
        transverse_load: 지점 사이에 횡하중이 작용하면 ``True``.
            기본값 ``False``.

    Raises:
        ValueError: :math:`P_u \ge 0.75 P_c` 로 좌굴이 발생하는 경우

    Returns:
        :math:`C_m` 과 모멘트확대계수 (``c_m``, ``delta_ns``)
    """
    if transverse_load:
        c_m = 1.0
    else:
        ratio = m1 / m2 if m2 != 0 else 0.0
        ratio = max(min(ratio, 1.0), -1.0)
        c_m = max(0.6 + 0.4 * ratio, 0.4)

    denominator = 1.0 - p_u / (PHI_K * p_c)

    if denominator <= 0:
        msg = (
            f"Pu = {p_u / 1e3:.1f} kN 이 0.75Pc = {PHI_K * p_c / 1e3:.1f} kN "
            "이상이어서 좌굴이 발생합니다. 단면 또는 비지지 길이를 조정하십시오."
        )
        raise ValueError(msg)

    return float(c_m), float(max(c_m / denominator, 1.0))


def minimum_moment(p_u: float, h: float) -> float:
    r"""최소 편심에 의한 모멘트를 반환한다.

    **KDS 14 20 20 4.4.2**

    .. math::
        M_{2,min} = P_u (15 + 0.03h) \quad (h\ \text{단위: mm})

    Args:
        p_u: 계수 축력 (N)
        h: 좌굴을 검토하는 방향의 단면 치수 (mm)

    Returns:
        최소 모멘트 (N·mm)
    """
    return float(p_u * (15.0 + 0.03 * h))


@dataclass
class SlendernessCheck:
    """세장 기둥 검토 결과.

    Args:
        r: 회전반지름 (mm)
        slenderness: 세장비 k*lu/r
        limit: 세장효과를 무시할 수 있는 한계 세장비
        slender: 세장 기둥인지 여부
        ei: 휨강성 (N·mm^2)
        p_c: 임계좌굴하중 (N)
        c_m: Cm 계수
        delta_ns: 모멘트확대계수
        m2: 설계에 사용한 M2 (N·mm)
        m2_min: 최소 편심 모멘트 (N·mm)
        m_c: 확대된 설계 모멘트 (N·mm)
    """

    r: float
    slenderness: float
    limit: float
    slender: bool
    ei: float
    p_c: float
    c_m: float
    delta_ns: float
    m2: float
    m2_min: float
    m_c: float

    def print_results(self) -> None:
        """검토 결과를 출력한다."""
        width = 64
        print("=" * width)
        print("세장 기둥 검토 (KDS 14 20 20 4.4)")
        print("=" * width)
        print(f"회전반지름           r      = {self.r:12.2f} mm")
        print(f"세장비           k*lu/r     = {self.slenderness:12.2f}")
        print(f"한계 세장비                 = {self.limit:12.2f}")
        print(f"세장 기둥                   = {'예' if self.slender else '아니오':>12}")

        if not self.slender:
            print("-" * width)
            print("세장효과를 무시할 수 있습니다 (Mc = M2).")
            return

        print("-" * width)
        print(f"휨강성               EI     = {self.ei:12.4e} N.mm^2")
        print(f"임계좌굴하중         Pc     = {self.p_c / 1e3:12.2f} kN")
        print(f"                 0.75Pc     = {PHI_K * self.p_c / 1e3:12.2f} kN")
        print(f"                     Cm     = {self.c_m:12.4f}")
        print(f"모멘트확대계수   delta_ns   = {self.delta_ns:12.4f}")
        print("-" * width)
        print(f"단부 모멘트          M2     = {self.m2 / 1e6:12.2f} kN.m")
        print(f"최소 편심 모멘트     M2,min = {self.m2_min / 1e6:12.2f} kN.m")
        print(f"설계 모멘트          Mc     = {self.m_c / 1e6:12.2f} kN.m")


def check_slenderness(
    p_u: float,
    m1: float,
    m2: float,
    k: float,
    l_u: float,
    h: float,
    e_c: float,
    i_g: float,
    a_g: float | None = None,
    braced: bool = True,
    beta_dns: float = 0.6,
    transverse_load: bool = False,
    section: str = "rectangular",
) -> SlendernessCheck:
    r"""세장 기둥을 검토하고 확대된 설계 모멘트를 반환한다.

    **KDS 14 20 20 4.4**

    Args:
        p_u: 계수 축력 (N)
        m1: 절댓값이 작은 단부 모멘트 (N·mm). 복곡률이면 음(−).
        m2: 절댓값이 큰 단부 모멘트 (N·mm)
        k: 유효길이계수
        l_u: 기둥의 비지지 길이 (mm)
        h: 좌굴을 검토하는 방향의 단면 치수 (mm)
        e_c: 콘크리트 탄성계수 (MPa)
        i_g: 총단면 2차모멘트 (mm\ :sup:`4`)
        a_g: 전체 단면적 (mm\ :sup:`2`). ``section="general"`` 에 필요.
            기본값 ``None``.
        braced: 횡구속 골조 여부. 기본값 ``True``.
        beta_dns: 지속 축하중 비. 기본값 ``0.6``.
        transverse_load: 지점 사이 횡하중 작용 여부. 기본값 ``False``.
        section: 회전반지름 계산에 사용할 단면 형태.
            기본값 ``"rectangular"``.

    Returns:
        세장 기둥 검토 결과 객체
    """
    r = radius_of_gyration(section=section, h=h, i_g=i_g, a_g=a_g)
    ratio = slenderness_ratio(k=k, l_u=l_u, r=r)
    limit = slenderness_limit(braced=braced, m1=m1, m2=m2)
    slender = ratio > limit

    m2_min = minimum_moment(p_u=p_u, h=h)
    m2_design = max(abs(m2), m2_min)

    ei = flexural_stiffness(e_c=e_c, i_g=i_g, beta_dns=beta_dns)
    p_c = critical_buckling_load(ei=ei, k=k, l_u=l_u)

    if slender:
        c_m, delta_ns = moment_magnifier_braced(
            p_u=p_u,
            p_c=p_c,
            m1=m1,
            m2=m2,
            transverse_load=transverse_load,
        )
        m_c = delta_ns * m2_design
    else:
        c_m, delta_ns = 1.0, 1.0
        m_c = m2_design

    return SlendernessCheck(
        r=r,
        slenderness=ratio,
        limit=limit,
        slender=slender,
        ei=ei,
        p_c=p_c,
        c_m=c_m,
        delta_ns=delta_ns,
        m2=m2_design,
        m2_min=m2_min,
        m_c=m_c,
    )
