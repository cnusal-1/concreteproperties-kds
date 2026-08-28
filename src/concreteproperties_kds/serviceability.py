"""사용성 설계 (KDS 14 20 30).

처짐 계산(유효단면2차모멘트, 장기처짐), 처짐 한계, 처짐 계산을 생략할 수 있는
최소 두께를 다룬다.

균열 제어를 위한 휨철근 간격은 KDS 14 20 30 4.1(1) 이 KDS 14 20 20(4.2.3) 으로
위임하므로, 그 조문의 식 (4.2-3)·(4.2-4) 를 구현하였다. 수축·온도철근은
KDS 14 20 50(4.6.2) 에 따른다.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# 장기처짐 계수 (KDS 14 20 30 4.2.1(5), 식 4.2-4) - 시간경과계수
CREEP_FACTOR: dict[str, float] = {
    "3개월": 1.0,
    "6개월": 1.2,
    "12개월": 1.4,
    "5년이상": 2.0,
}

# 처짐을 계산하지 않는 경우의 보 또는 1방향 슬래브의 최소 두께
# (KDS 14 20 30 표 4.2-1)
# fy = 400 MPa 기준, 경간 l 에 대한 비
MINIMUM_THICKNESS_RATIO: dict[str, dict[str, float]] = {
    "1방향슬래브": {
        "단순지지": 20.0,
        "1단연속": 24.0,
        "양단연속": 28.0,
        "캔틸레버": 10.0,
    },
    "보": {
        "단순지지": 16.0,
        "1단연속": 18.5,
        "양단연속": 21.0,
        "캔틸레버": 8.0,
    },
}

# 최대 허용처짐 (KDS 14 20 30 표 4.2-2)
# 조건 : (경간 l 에 대한 분모, 비교 대상 처짐)
#   "live"     - 활하중 L 에 의한 즉시처짐
#   "attached" - 비구조 요소가 부착된 후에 발생하는 처짐
#                (장기 추가처짐 + 추가 활하중에 의한 즉시처짐)
DEFLECTION_LIMIT: dict[str, tuple[float, str]] = {
    "지붕_비구조재없음": (180.0, "live"),
    "바닥_비구조재없음": (360.0, "live"),
    "손상되기쉬운_비구조재": (480.0, "attached"),
    "손상되지않는_비구조재": (240.0, "attached"),
}

# 비교 대상 처짐의 설명
DEFLECTION_TARGET_LABEL: dict[str, str] = {
    "live": "활하중에 의한 즉시처짐",
    "attached": "비구조 요소 부착 후 발생 처짐",
}

# 균열 제어 계수 kappa_cr (KDS 14 20 20 4.2.3(4))
KAPPA_CR_DRY = 280.0  # 건조환경
KAPPA_CR_OTHER = 210.0  # 그 밖의 환경


def effective_moment_of_inertia(
    m_a: float,
    m_cr: float,
    i_g: float,
    i_cr: float,
) -> float:
    r"""유효단면2차모멘트를 반환한다 (KDS 14 20 30 4.2.1, Branson 식).

    .. math::
        I_e = \left(\frac{M_{cr}}{M_a}\right)^3 I_g
        + \left[1 - \left(\frac{M_{cr}}{M_a}\right)^3\right] I_{cr}
        \le I_g

    :math:`M_a \le M_{cr}` 이면 :math:`I_e = I_g` 이다.

    Args:
        m_a: 처짐을 계산할 때의 최대 휨모멘트 (N·mm)
        m_cr: 균열모멘트 (N·mm)
        i_g: 총단면 2차모멘트 (mm\ :sup:`4`)
        i_cr: 균열단면 2차모멘트 (mm\ :sup:`4`)

    Returns:
        유효단면2차모멘트 (mm\ :sup:`4`)
    """
    if abs(m_a) <= abs(m_cr) or m_a == 0:
        return float(i_g)

    ratio = (abs(m_cr) / abs(m_a)) ** 3

    return float(min(ratio * i_g + (1.0 - ratio) * i_cr, i_g))


def long_term_deflection_factor(
    rho_prime: float = 0.0,
    duration: str = "5년이상",
) -> float:
    r"""장기 추가처짐 계수를 반환한다 (KDS 14 20 30 4.2.1).

    .. math::
        \lambda_\Delta = \frac{\xi}{1 + 50\rho'}

    Args:
        rho_prime: 압축철근비 :math:`A_s' / (b d)`. 기본값 ``0``.
        duration: 지속하중 재하기간. :data:`CREEP_FACTOR` 의 키.
            기본값 ``"5년이상"``.

    Raises:
        ValueError: ``duration`` 이 정의되지 않은 값인 경우

    Returns:
        장기 추가처짐 계수 :math:`\lambda_\Delta`
    """
    if duration not in CREEP_FACTOR:
        msg = f"duration 은 {list(CREEP_FACTOR)} 중 하나여야 합니다."
        raise ValueError(msg)

    return float(CREEP_FACTOR[duration] / (1.0 + 50.0 * rho_prime))


def total_deflection(
    delta_immediate_sustained: float,
    delta_immediate_live: float,
    rho_prime: float = 0.0,
    duration: str = "5년이상",
) -> tuple[float, float]:
    r"""장기처짐을 포함한 전체 처짐을 반환한다 (KDS 14 20 30 4.2.1).

    .. math::
        \Delta_{total} = \Delta_{L} + (1 + \lambda_\Delta)\Delta_{D}

    여기서 :math:`\Delta_D` 는 지속하중에 의한 즉시처짐,
    :math:`\Delta_L` 은 활하중에 의한 즉시처짐이다.

    Args:
        delta_immediate_sustained: 지속하중에 의한 즉시처짐 (mm)
        delta_immediate_live: 활하중에 의한 즉시처짐 (mm)
        rho_prime: 압축철근비. 기본값 ``0``.
        duration: 지속하중 재하기간. 기본값 ``"5년이상"``.

    Returns:
        장기 추가처짐과 전체 처짐 (``delta_long_term``, ``delta_total``)
    """
    lambda_delta = long_term_deflection_factor(
        rho_prime=rho_prime, duration=duration
    )
    delta_long_term = lambda_delta * delta_immediate_sustained
    delta_total = delta_immediate_live + delta_immediate_sustained + delta_long_term

    return float(delta_long_term), float(delta_total)


def minimum_thickness(
    span: float,
    member: str = "보",
    support: str = "단순지지",
    fy: float = 400.0,
    m_c: float = 2300.0,
) -> float:
    r"""처짐을 계산하지 않는 경우의 최소 두께를 반환한다 (KDS 14 20 30 표 4.2-1).

    표의 값은 보통중량콘크리트(:math:`m_c = 2300` kg/m\ :sup:`3`)와
    :math:`f_y = 400` MPa 철근을 사용한 부재에 대한 값이며, 다른 조건에는
    다음 보정을 적용한다.

    - 단위질량 1,500~2,000 kg/m\ :sup:`3` 의 구조용 경량콘크리트 :
      :math:`(1.65 - 0.00031 m_c) \ge 1.09` 를 곱한다.
    - :math:`f_y \ne 400` MPa : :math:`(0.43 + f_y / 700)` 을 곱한다.

    Args:
        span: 경간 :math:`l` (mm)
        member: ``"보"`` 또는 ``"1방향슬래브"``. 기본값 ``"보"``.
        support: ``"단순지지"``, ``"1단연속"``, ``"양단연속"``, ``"캔틸레버"``.
            기본값 ``"단순지지"``.
        fy: 철근의 설계기준항복강도 (MPa). 기본값 ``400``.
        m_c: 콘크리트의 단위질량 (kg/m\ :sup:`3`). 기본값 ``2300``.

    Raises:
        ValueError: ``member`` 또는 ``support`` 가 정의되지 않은 값인 경우

    Returns:
        최소 두께 (mm)
    """
    if member not in MINIMUM_THICKNESS_RATIO:
        msg = f"member 는 {list(MINIMUM_THICKNESS_RATIO)} 중 하나여야 합니다."
        raise ValueError(msg)

    ratios = MINIMUM_THICKNESS_RATIO[member]

    if support not in ratios:
        msg = f"support 는 {list(ratios)} 중 하나여야 합니다."
        raise ValueError(msg)

    h_min = span / ratios[support]

    # 구조용 경량콘크리트 보정
    if 1500.0 <= m_c <= 2000.0:
        h_min *= max(1.65 - 0.00031 * m_c, 1.09)

    if abs(fy - 400.0) > 1e-9:
        h_min *= 0.43 + fy / 700.0

    return float(h_min)


def deflection_limit(
    span: float,
    condition: str = "바닥_비구조재없음",
) -> float:
    r"""최대 허용처짐을 반환한다 (KDS 14 20 30 표 4.2-2).

    .. note::

        조건마다 **비교 대상 처짐이 다르다**. 어떤 처짐과 비교해야 하는지는
        :func:`deflection_target` 로 확인한다.

    Args:
        span: 경간 :math:`l` (mm)
        condition: :data:`DEFLECTION_LIMIT` 의 키.
            기본값 ``"바닥_비구조재없음"``.

    Raises:
        ValueError: ``condition`` 이 정의되지 않은 값인 경우

    Returns:
        최대 허용처짐 (mm)
    """
    if condition not in DEFLECTION_LIMIT:
        msg = f"condition 은 {list(DEFLECTION_LIMIT)} 중 하나여야 합니다."
        raise ValueError(msg)

    return float(span / DEFLECTION_LIMIT[condition][0])


def deflection_target(condition: str = "바닥_비구조재없음") -> str:
    """허용처짐과 비교해야 할 처짐의 종류를 반환한다 (KDS 14 20 30 표 4.2-2).

    - ``"live"`` : 활하중 L 에 의한 즉시처짐
    - ``"attached"`` : 비구조 요소가 부착된 후에 발생하는 처짐
      (장기 추가처짐 + 추가 활하중에 의한 즉시처짐)

    Args:
        condition: :data:`DEFLECTION_LIMIT` 의 키.
            기본값 ``"바닥_비구조재없음"``.

    Raises:
        ValueError: ``condition`` 이 정의되지 않은 값인 경우

    Returns:
        ``"live"`` 또는 ``"attached"``
    """
    if condition not in DEFLECTION_LIMIT:
        msg = f"condition 은 {list(DEFLECTION_LIMIT)} 중 하나여야 합니다."
        raise ValueError(msg)

    return DEFLECTION_LIMIT[condition][1]


def max_bar_spacing(
    fs: float,
    c_c: float,
    dry_environment: bool = True,
) -> float:
    r"""균열 제어를 위한 휨철근의 최대 간격을 반환한다 (KDS 14 20 20 4.2.3(4)).

    .. math::
        s = 375\left(\frac{\kappa_{cr}}{f_s}\right) - 2.5 c_c
        \le 300\left(\frac{\kappa_{cr}}{f_s}\right)

    Args:
        fs: 사용하중 상태의 인장철근 응력 (MPa). 계산하지 않는 경우
            :math:`f_s = \frac{2}{3} f_y` 를 사용할 수 있다.
        c_c: 인장철근 표면과 콘크리트 표면 사이의 최소 두께 (mm)
        dry_environment: 건조환경이면 ``True`` (:math:`\kappa_{cr} = 280`),
            그 밖의 환경이면 ``False`` (:math:`\kappa_{cr} = 210`).
            기본값 ``True``.

    Raises:
        ValueError: ``fs`` 가 0 이하인 경우

    Returns:
        휨철근의 최대 간격 (mm)
    """
    if fs <= 0:
        msg = "fs 는 0 보다 커야 합니다."
        raise ValueError(msg)

    kappa_cr = KAPPA_CR_DRY if dry_environment else KAPPA_CR_OTHER

    s = 375.0 * (kappa_cr / fs) - 2.5 * c_c
    s_limit = 300.0 * (kappa_cr / fs)

    return float(min(s, s_limit))


def service_steel_stress(fy: float) -> float:
    r"""사용하중 상태의 인장철근 응력 근사값을 반환한다 (KDS 14 20 20 4.2.3(4)).

    .. math::
        f_s = \frac{2}{3} f_y

    Args:
        fy: 철근의 설계기준항복강도 (MPa)

    Returns:
        사용하중 상태의 인장철근 응력 (MPa)
    """
    return float(2.0 / 3.0 * fy)


@dataclass
class DeflectionCheck:
    """처짐 검토 결과.

    Args:
        i_e: 유효단면2차모멘트 (mm^4)
        i_g: 총단면 2차모멘트 (mm^4)
        i_cr: 균열단면 2차모멘트 (mm^4)
        delta_sustained: 지속하중에 의한 즉시처짐 (mm)
        delta_live: 활하중에 의한 즉시처짐 (mm)
        delta_long_term: 장기 추가처짐 (mm)
        delta_total: 전체 처짐 (mm)
        condition: 적용한 허용처짐 조건
        target: 허용처짐과 비교한 처짐의 종류 ("live" 또는 "attached")
        delta_check: 허용처짐과 실제로 비교한 처짐 (mm)
        limit: 최대 허용처짐 (mm)
        ok: 만족 여부
    """

    i_e: float
    i_g: float
    i_cr: float
    delta_sustained: float
    delta_live: float
    delta_long_term: float
    delta_total: float
    condition: str
    target: str
    delta_check: float
    limit: float
    ok: bool

    def print_results(self) -> None:
        """검토 결과를 출력한다."""
        width = 66
        print("=" * width)
        print("처짐 검토 (KDS 14 20 30 4.2)")
        print("=" * width)
        print(f"총단면 2차모멘트     Ig    = {self.i_g:16,.0f} mm^4")
        print(f"균열단면 2차모멘트   Icr   = {self.i_cr:16,.0f} mm^4")
        print(f"유효단면2차모멘트    Ie    = {self.i_e:16,.0f} mm^4")
        print(f"                     Ie/Ig = {self.i_e / self.i_g:16.3f}")
        print("-" * width)
        print(f"지속하중 즉시처짐          = {self.delta_sustained:16.3f} mm")
        print(f"활하중   즉시처짐          = {self.delta_live:16.3f} mm")
        print(f"장기 추가처짐              = {self.delta_long_term:16.3f} mm")
        print(f"전체 처짐 (참고)           = {self.delta_total:16.3f} mm")
        print("-" * width)
        print(f"허용처짐 조건 : {self.condition}")
        print(f"비교 대상     : {DEFLECTION_TARGET_LABEL[self.target]}")
        print(f"검토 처짐                  = {self.delta_check:16.3f} mm")
        print(f"허용 처짐                  = {self.limit:16.3f} mm")
        print(f"판정                       = {'만족' if self.ok else '불만족':>16}")


def check_deflection(
    span: float,
    m_sustained: float,
    m_live: float,
    m_cr: float,
    i_g: float,
    i_cr: float,
    e_c: float,
    support_coefficient: float = 5.0 / 384.0,
    rho_prime: float = 0.0,
    duration: str = "5년이상",
    condition: str = "바닥_비구조재없음",
) -> DeflectionCheck:
    r"""등분포하중을 받는 부재의 처짐을 검토한다 (KDS 14 20 30 4.2).

    처짐은 모멘트로부터 역산한 등가 등분포하중을 이용하여

    .. math::
        \Delta = k \frac{w l^4}{E_c I_e},
        \qquad w = \frac{8 M}{l^2}\ (\text{단순지지})

    로 계산한다. 기본값 :math:`k = 5/384` 는 단순지지 등분포하중에 해당한다.

    Args:
        span: 경간 :math:`l` (mm)
        m_sustained: 지속하중에 의한 최대 휨모멘트 (N·mm)
        m_live: 활하중에 의한 최대 휨모멘트 (N·mm)
        m_cr: 균열모멘트 (N·mm)
        i_g: 총단면 2차모멘트 (mm\ :sup:`4`)
        i_cr: 균열단면 2차모멘트 (mm\ :sup:`4`)
        e_c: 콘크리트 탄성계수 (MPa)
        support_coefficient: 처짐 계수 :math:`k`. 기본값 ``5/384``.
        rho_prime: 압축철근비. 기본값 ``0``.
        duration: 지속하중 재하기간. 기본값 ``"5년이상"``.
        condition: 허용처짐 조건. 조건에 따라 허용처짐과 비교하는 처짐이
            달라진다 (:func:`deflection_target` 참고).
            기본값 ``"바닥_비구조재없음"``.

    Returns:
        처짐 검토 결과 객체
    """
    m_total = m_sustained + m_live

    # 전체 하중에 대한 유효단면2차모멘트를 사용 (보수측)
    i_e = effective_moment_of_inertia(m_a=m_total, m_cr=m_cr, i_g=i_g, i_cr=i_cr)

    def deflection(moment: float) -> float:
        w = 8.0 * moment / span**2
        return support_coefficient * w * span**4 / (e_c * i_e)

    delta_sustained = deflection(m_sustained)
    delta_live = deflection(m_live)
    delta_long_term, delta_total = total_deflection(
        delta_immediate_sustained=delta_sustained,
        delta_immediate_live=delta_live,
        rho_prime=rho_prime,
        duration=duration,
    )
    limit = deflection_limit(span=span, condition=condition)
    target = deflection_target(condition=condition)

    # 조건마다 허용처짐과 비교하는 처짐이 다르다 (KDS 14 20 30 표 4.2-2)
    delta_check = (
        delta_live if target == "live" else delta_long_term + delta_live
    )

    return DeflectionCheck(
        i_e=i_e,
        i_g=i_g,
        i_cr=i_cr,
        delta_sustained=delta_sustained,
        delta_live=delta_live,
        delta_long_term=delta_long_term,
        delta_total=delta_total,
        condition=condition,
        target=target,
        delta_check=delta_check,
        limit=limit,
        ok=bool(delta_check <= limit),
    )


def check_crack_control(
    bar_spacing: float,
    fy: float,
    c_c: float,
    fs: float | None = None,
    dry_environment: bool = True,
) -> tuple[float, float, bool]:
    r"""균열 제어를 위한 철근 간격 조건을 검토한다 (KDS 14 20 20 4.2.3(4)).

    Args:
        bar_spacing: 배치된 휨철근의 중심 간격 (mm)
        fy: 철근의 설계기준항복강도 (MPa)
        c_c: 인장철근 표면과 콘크리트 표면 사이의 최소 두께 (mm)
        fs: 사용하중 상태의 인장철근 응력 (MPa). 주지 않으면
            :math:`\frac{2}{3} f_y` 를 사용. 기본값 ``None``.
        dry_environment: 건조환경 여부. 기본값 ``True``.

    Returns:
        사용된 철근응력, 최대 간격, 만족 여부 (``fs``, ``s_max``, ``ok``)
    """
    if fs is None:
        fs = service_steel_stress(fy=fy)

    s_max = max_bar_spacing(fs=fs, c_c=c_c, dry_environment=dry_environment)

    return float(fs), s_max, bool(bar_spacing <= s_max + 1e-9)


def shrinkage_temperature_reinforcement(
    fy: float,
    a_g: float,
    width: float = 1000.0,
) -> float:
    r"""건조수축·온도철근량을 반환한다 (KDS 14 20 50 4.6.2).

    1방향 철근콘크리트 슬래브의 수축·온도철근비는 다음 값 이상이어야 하나,
    어떤 경우에도 0.0014 이상이어야 한다.

    .. math::

ho = egin{cases}
        0.0020 & f_y \le 400 	ext{ MPa} \
        0.0020 	imes \dfrac{400}{f_y} & f_y > 400 	ext{ MPa}
        \end{cases}

    다만 단위 폭 1 m 당 1,800 mm\ :sup:`2` 보다 크게 취할 필요는 없다.

    Args:
        fy: 철근의 설계기준항복강도 (MPa)
        a_g: 콘크리트 전체 단면적 (mm\ :sup:`2`)
        width: ``a_g`` 에 해당하는 폭 (mm). 1,800 mm\ :sup:`2`/m 상한을
            적용하기 위해 사용한다. 기본값 ``1000``.

    Returns:
        수축·온도철근량 (mm\ :sup:`2`)
    """
    rho = max(0.0020 if fy <= 400 else 0.0020 * 400.0 / fy, 0.0014)
    a_s = rho * a_g

    # 단위 폭 m 당 1,800 mm^2 상한
    if width > 0:
        a_s = min(a_s, 1800.0 * width / 1000.0)

    return float(a_s)


def shrinkage_temperature_spacing(thickness: float) -> float:
    """수축·온도철근의 최대 간격을 반환한다 (KDS 14 20 50 4.6.2(3)).

    슬래브 두께의 5배 이하, 또한 450 mm 이하로 한다.

    Args:
        thickness: 슬래브 두께 (mm)

    Returns:
        최대 간격 (mm)
    """
    return float(min(5.0 * thickness, 450.0))


def cracking_moment(
    fck: float,
    i_g: float,
    y_t: float,
    lambda_c: float = 1.0,
) -> float:
    r"""균열모멘트를 반환한다 (KDS 14 20 30 4.2.1).

    .. math::
        M_{cr} = \frac{f_r I_g}{y_t}, \qquad f_r = 0.63\lambda\sqrt{f_{ck}}

    Args:
        fck: 콘크리트 설계기준압축강도 (MPa)
        i_g: 총단면 2차모멘트 (mm\ :sup:`4`)
        y_t: 도심축에서 인장연단까지의 거리 (mm)
        lambda_c: 경량콘크리트계수. 기본값 ``1.0``.

    Returns:
        균열모멘트 (N·mm)
    """
    f_r = 0.63 * lambda_c * np.sqrt(fck)

    return float(f_r * i_g / y_t)
