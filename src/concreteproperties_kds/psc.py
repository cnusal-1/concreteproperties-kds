"""프리스트레스트 콘크리트 (KDS 14 20 60).

긴장재의 허용응력과 콘크리트의 허용응력, 프리스트레스 손실, 부착·비부착
긴장재의 극한 응력 :math:`f_{ps}`, 그리고 프리스트레스트 단면에 대한
강도감소계수를 다룬다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from concreteproperties_kds.kds import (
    PHI_COMP_SPIRAL,
    PHI_COMP_TIE,
    PHI_TENSION,
)

if TYPE_CHECKING:
    from concreteproperties.prestressed_section import PrestressedSection

# 프리스트레스트 부재의 변형률한계 (KDS 14 20 20 4.1.2)
EPS_Y_PSC = 0.002  # 압축지배변형률한계
EPS_TL_PSC = 0.005  # 인장지배변형률한계

# 긴장재 응력 계수 gamma_p (KDS 14 20 60 4.4.2(3))
GAMMA_P: dict[str, float] = {
    "일반": 0.55,  # fpy/fpu >= 0.80
    "스트레스릴리브드": 0.40,  # fpy/fpu >= 0.85
    "저릴랙세이션": 0.28,  # fpy/fpu >= 0.90
}

# 균열등급 (KDS 14 20 60 4.2.1) - sqrt(fck) 에 곱하는 인장응력 한계 계수
CRACK_CLASS_LIMIT: dict[str, float] = {
    "U": 0.63,  # 비균열등급
    "T": 1.00,  # 부분균열등급
}


def allowable_tendon_stress(
    fpu: float,
    fpy: float,
    stage: str = "jacking",
) -> float:
    r"""긴장재의 허용응력을 반환한다.

    **KDS 14 20 60 4.2.2**

    - 긴장 중 (``"jacking"``) : :math:`\min(0.80 f_{pu},\ 0.94 f_{py})`
    - 정착 직후 (``"anchorage"``) : :math:`\min(0.74 f_{pu},\ 0.82 f_{py})`
    - 포스트텐션 정착장치·커플러 (``"anchorage_device"``) :
      :math:`0.70 f_{pu}`

    Args:
        fpu: 긴장재의 인장강도 (MPa)
        fpy: 긴장재의 항복강도 (MPa)
        stage: ``"jacking"``, ``"anchorage"``, ``"anchorage_device"``.
            기본값 ``"jacking"``.

    Raises:
        ValueError: ``stage`` 가 정의되지 않은 값인 경우

    Returns:
        긴장재의 허용응력 (MPa)
    """
    if stage == "jacking":
        return float(min(0.80 * fpu, 0.94 * fpy))

    if stage == "anchorage":
        return float(min(0.74 * fpu, 0.82 * fpy))

    if stage == "anchorage_device":
        return float(0.70 * fpu)

    msg = (
        'stage 는 "jacking", "anchorage", "anchorage_device" 중 '
        "하나여야 합니다."
    )
    raise ValueError(msg)


def allowable_concrete_stress_transfer(
    fci: float,
    simply_supported_end: bool = False,
    reinforced_zone: bool = False,
) -> tuple[float, float]:
    r"""프리스트레스 도입 직후 콘크리트의 허용응력을 반환한다.

    **KDS 14 20 60 4.2.2**

    - 압축 : :math:`0.60 f_{ci}` (단, 프리텐션 부재의 단부 등 일부 위치는
      :math:`0.70 f_{ci}`)
    - 인장 : :math:`0.25\sqrt{f_{ci}}` (단순지지 부재의 단부는
      :math:`0.50\sqrt{f_{ci}}`)

    Args:
        fci: 프리스트레스 도입 시 콘크리트의 압축강도 (MPa)
        simply_supported_end: 단순지지 부재의 단부이면 ``True``.
            기본값 ``False``.
        reinforced_zone: 압축 한계로 :math:`0.70 f_{ci}` 를 적용할 수 있는
            위치이면 ``True``. 기본값 ``False``.

    Returns:
        허용 압축응력과 허용 인장응력 (``f_c_allow``, ``f_t_allow``) (MPa).
        인장은 음(−)의 부호로 반환한다.
    """
    f_c_allow = (0.70 if reinforced_zone else 0.60) * fci
    coeff = 0.50 if simply_supported_end else 0.25
    f_t_allow = -coeff * np.sqrt(fci)

    return float(f_c_allow), float(f_t_allow)


def allowable_concrete_stress_service(
    fck: float,
    sustained: bool = False,
    crack_class: str = "U",
) -> tuple[float, float]:
    r"""사용하중 상태 콘크리트의 허용응력을 반환한다.

    **KDS 14 20 60 4.2.1, 4.2.2**

    - 압축 : 지속하중 :math:`0.45 f_{ck}`, 전체하중 :math:`0.60 f_{ck}`
    - 인장 : 비균열등급(U) :math:`0.63\sqrt{f_{ck}}`,
      부분균열등급(T) :math:`1.0\sqrt{f_{ck}}`,
      균열등급(C) 제한 없음

    Args:
        fck: 콘크리트 설계기준압축강도 (MPa)
        sustained: 지속하중 조합이면 ``True``. 기본값 ``False``.
        crack_class: ``"U"``, ``"T"``, ``"C"``. 기본값 ``"U"``.

    Raises:
        ValueError: ``crack_class`` 가 정의되지 않은 값인 경우

    Returns:
        허용 압축응력과 허용 인장응력 (``f_c_allow``, ``f_t_allow``) (MPa).
        인장은 음(−)의 부호로 반환하며, 균열등급(C)은 ``-inf``.
    """
    f_c_allow = (0.45 if sustained else 0.60) * fck

    if crack_class == "C":
        return float(f_c_allow), float("-inf")

    if crack_class not in CRACK_CLASS_LIMIT:
        msg = 'crack_class 는 "U", "T", "C" 중 하나여야 합니다.'
        raise ValueError(msg)

    f_t_allow = -CRACK_CLASS_LIMIT[crack_class] * np.sqrt(fck)

    return float(f_c_allow), float(f_t_allow)


def friction_loss(
    p_pj: float,
    mu_p: float,
    alpha_px: float,
    k_wobble: float,
    l_px: float,
    approximate: bool = False,
) -> tuple[float, float]:
    r"""마찰에 의한 프리스트레스 손실을 반환한다.

    **KDS 14 20 60 4.3**

    .. math::
        P_{px} = P_{pj}\, e^{-(\mu_p \alpha_{px} + K l_{px})}

    :math:`\mu_p \alpha_{px} + K l_{px} \le 0.3` 이면 근사식

    .. math::
        P_{px} = \frac{P_{pj}}{1 + \mu_p \alpha_{px} + K l_{px}}

    을 쓸 수 있다.

    Args:
        p_pj: 잭킹단의 긴장력 (N)
        mu_p: 곡률마찰계수
        alpha_px: 잭킹단에서 검토 위치까지의 각변화량 (radian)
        k_wobble: 파상마찰계수 (1/mm)
        l_px: 잭킹단에서 검토 위치까지의 긴장재 길이 (mm)
        approximate: 근사식 사용 여부. 기본값 ``False``.

    Returns:
        검토 위치의 긴장력과 손실량 (``p_px``, ``loss``) (N)
    """
    exponent = mu_p * alpha_px + k_wobble * l_px

    p_px = p_pj / (1.0 + exponent) if approximate else p_pj * np.exp(-exponent)

    return float(p_px), float(p_pj - p_px)


def anchorage_set_loss(
    slip: float,
    e_p: float,
    length: float,
) -> float:
    r"""정착장치 활동에 의한 프리스트레스 손실을 반환한다.

    **KDS 14 20 60 4.3**

    .. math::
        \Delta f_p = \frac{\Delta l}{l} E_p

    Args:
        slip: 정착장치의 활동량 :math:`\Delta l` (mm)
        e_p: 긴장재의 탄성계수 (MPa)
        length: 활동의 영향이 미치는 길이 :math:`l` (mm)

    Raises:
        ValueError: ``length`` 가 0 이하인 경우

    Returns:
        응력 손실 (MPa)
    """
    if length <= 0:
        msg = "length 는 0 보다 커야 합니다."
        raise ValueError(msg)

    return float(slip / length * e_p)


def elastic_shortening_loss(
    f_cgp: float,
    e_p: float,
    e_ci: float,
    post_tensioned: bool = False,
    n_tendons: int = 1,
) -> float:
    r"""콘크리트 탄성변형에 의한 프리스트레스 손실을 반환한다.

    **KDS 14 20 60 4.3**

    프리텐션

    .. math::
        \Delta f_p = \frac{E_p}{E_{ci}} f_{cgp}

    포스트텐션 (:math:`N` 개의 긴장재를 순차적으로 긴장)

    .. math::
        \Delta f_p = \frac{N-1}{2N}\frac{E_p}{E_{ci}} f_{cgp}

    Args:
        f_cgp: 긴장재 도심 위치에서 프리스트레스에 의한 콘크리트 압축응력 (MPa)
        e_p: 긴장재의 탄성계수 (MPa)
        e_ci: 프리스트레스 도입 시 콘크리트의 탄성계수 (MPa)
        post_tensioned: 포스트텐션이면 ``True``. 기본값 ``False``.
        n_tendons: 순차적으로 긴장하는 긴장재의 수. 기본값 ``1``.

    Raises:
        ValueError: ``e_ci`` 가 0 이하이거나 ``n_tendons`` 가 1 미만인 경우

    Returns:
        응력 손실 (MPa)
    """
    if e_ci <= 0:
        msg = "e_ci 는 0 보다 커야 합니다."
        raise ValueError(msg)

    if n_tendons < 1:
        msg = "n_tendons 는 1 이상이어야 합니다."
        raise ValueError(msg)

    loss = e_p / e_ci * f_cgp

    if post_tensioned:
        loss *= (n_tendons - 1) / (2.0 * n_tendons)

    return float(loss)


def creep_loss(
    f_cgp: float,
    e_p: float,
    e_c: float,
    creep_coefficient: float = 2.0,
    f_cds: float = 0.0,
) -> float:
    r"""콘크리트 크리프에 의한 프리스트레스 손실을 반환한다.

    **KDS 14 20 60 4.3**

    .. math::
        \Delta f_p = \phi_{cr}\frac{E_p}{E_c}(f_{cgp} - f_{cds})

    Args:
        f_cgp: 긴장재 도심에서 프리스트레스에 의한 콘크리트 압축응력 (MPa)
        e_p: 긴장재의 탄성계수 (MPa)
        e_c: 콘크리트의 탄성계수 (MPa)
        creep_coefficient: 크리프계수 :math:`\phi_{cr}`. 기본값 ``2.0``.
        f_cds: 프리스트레스 도입 후 추가된 지속하중에 의한 콘크리트 응력
            (인장이면 양수) (MPa). 기본값 ``0``.

    Raises:
        ValueError: ``e_c`` 가 0 이하인 경우

    Returns:
        응력 손실 (MPa)
    """
    if e_c <= 0:
        msg = "e_c 는 0 보다 커야 합니다."
        raise ValueError(msg)

    return float(creep_coefficient * e_p / e_c * (f_cgp - f_cds))


def shrinkage_loss(
    e_p: float,
    eps_sh: float = 300e-6,
) -> float:
    r"""콘크리트 건조수축에 의한 프리스트레스 손실을 반환한다.

    **KDS 14 20 60 4.3**

    .. math::
        \Delta f_p = \varepsilon_{sh} E_p

    Args:
        e_p: 긴장재의 탄성계수 (MPa)
        eps_sh: 건조수축 변형률. 기본값 ``300e-6``.

    Returns:
        응력 손실 (MPa)
    """
    return float(eps_sh * e_p)


def relaxation_loss(
    f_pi: float,
    fpy: float,
    hours: float = 1000.0 * 24.0,
    low_relaxation: bool = True,
) -> float:
    r"""긴장재 릴랙세이션에 의한 프리스트레스 손실을 반환한다.

    **KDS 14 20 60 4.3**

    .. math::
        \Delta f_p = f_{pi}\,\frac{\log(t)}{k}
        \left(\frac{f_{pi}}{f_{py}} - 0.55\right)

    :math:`k` 는 저릴랙세이션 강연선 45, 보통 강연선 10 이며,
    :math:`f_{pi}/f_{py} \le 0.55` 이면 손실이 없다.

    Args:
        f_pi: 릴랙세이션 계산 시점의 긴장재 응력 (MPa)
        fpy: 긴장재의 항복강도 (MPa)
        hours: 경과 시간 (시간). 기본값 ``24000`` (1000일).
        low_relaxation: 저릴랙세이션 강연선이면 ``True``. 기본값 ``True``.

    Raises:
        ValueError: ``fpy`` 가 0 이하이거나 ``hours`` 가 1 미만인 경우

    Returns:
        응력 손실 (MPa)
    """
    if fpy <= 0:
        msg = "fpy 는 0 보다 커야 합니다."
        raise ValueError(msg)

    if hours < 1:
        msg = "hours 는 1 이상이어야 합니다."
        raise ValueError(msg)

    ratio = f_pi / fpy

    if ratio <= 0.55:
        return 0.0

    k = 45.0 if low_relaxation else 10.0

    return float(f_pi * np.log10(hours) / k * (ratio - 0.55))


@dataclass
class PrestressLosses:
    """프리스트레스 손실 요약.

    Args:
        f_pj: 잭킹 응력 (MPa)
        friction: 마찰 손실 (MPa)
        anchorage: 정착장치 활동 손실 (MPa)
        elastic: 탄성변형 손실 (MPa)
        creep: 크리프 손실 (MPa)
        shrinkage: 건조수축 손실 (MPa)
        relaxation: 릴랙세이션 손실 (MPa)
    """

    f_pj: float
    friction: float = 0.0
    anchorage: float = 0.0
    elastic: float = 0.0
    creep: float = 0.0
    shrinkage: float = 0.0
    relaxation: float = 0.0

    @property
    def immediate(self) -> float:
        """즉시 손실의 합.

        Returns:
            즉시 손실 (MPa)
        """
        return self.friction + self.anchorage + self.elastic

    @property
    def time_dependent(self) -> float:
        """시간적 손실의 합.

        Returns:
            시간적 손실 (MPa)
        """
        return self.creep + self.shrinkage + self.relaxation

    @property
    def total(self) -> float:
        """전체 손실.

        Returns:
            전체 손실 (MPa)
        """
        return self.immediate + self.time_dependent

    @property
    def f_pe(self) -> float:
        """유효 프리스트레스.

        Returns:
            유효 프리스트레스 (MPa)
        """
        return self.f_pj - self.total

    @property
    def loss_ratio(self) -> float:
        """손실률.

        Returns:
            전체 손실 / 잭킹 응력
        """
        return self.total / self.f_pj if self.f_pj else 0.0

    def print_results(self) -> None:
        """손실 내역을 출력한다."""
        width = 56
        print("=" * width)
        print("프리스트레스 손실 (KDS 14 20 60 4.3)")
        print("=" * width)
        print(f"잭킹 응력          fpj    = {self.f_pj:10.2f} MPa")
        print("-" * width)
        print(f"마찰                      = {self.friction:10.2f} MPa")
        print(f"정착장치 활동             = {self.anchorage:10.2f} MPa")
        print(f"탄성변형                  = {self.elastic:10.2f} MPa")
        print(f"  즉시 손실 소계          = {self.immediate:10.2f} MPa")
        print("-" * width)
        print(f"크리프                    = {self.creep:10.2f} MPa")
        print(f"건조수축                  = {self.shrinkage:10.2f} MPa")
        print(f"릴랙세이션                = {self.relaxation:10.2f} MPa")
        print(f"  시간적 손실 소계        = {self.time_dependent:10.2f} MPa")
        print("-" * width)
        print(f"전체 손실                 = {self.total:10.2f} MPa")
        print(f"손실률                    = {self.loss_ratio * 100:10.2f} %")
        print(f"유효 프리스트레스  fpe    = {self.f_pe:10.2f} MPa")


def tendon_stress_bonded(
    fpu: float,
    fck: float,
    rho_p: float,
    gamma_p: float = 0.28,
    beta_1: float = 0.80,
    d: float = 0.0,
    d_p: float = 1.0,
    omega: float = 0.0,
    omega_prime: float = 0.0,
) -> float:
    r"""부착 긴장재의 극한 응력 :math:`f_{ps}` 를 반환한다.

    **KDS 14 20 60 4.4.2(3), 식 (4.4-1)**

    .. math::
        f_{ps} = f_{pu}\left[1 - \frac{\gamma_p}{\beta_1}
        \left(\rho_p \frac{f_{pu}}{f_{ck}}
        + \frac{d}{d_p}(\omega - \omega')\right)\right]

    Args:
        fpu: 긴장재의 인장강도 (MPa)
        fck: 콘크리트 설계기준압축강도 (MPa)
        rho_p: 긴장재비 :math:`A_{ps} / (b d_p)`
        gamma_p: 긴장재 종류 계수. 저릴랙세이션 0.28, 스트레스릴리브드 0.40,
            일반 0.55. 기본값 ``0.28``.
        beta_1: 등가직사각형 응력블록의 깊이 계수. 기본값 ``0.80``.
        d: 압축연단에서 인장철근 도심까지의 거리 (mm). 기본값 ``0``.
        d_p: 압축연단에서 긴장재 도심까지의 거리 (mm). 기본값 ``1``.
        omega: 인장철근지수 :math:`\rho f_y / f_{ck}`. 기본값 ``0``.
        omega_prime: 압축철근지수 :math:`\rho' f_y / f_{ck}`. 기본값 ``0``.

    Raises:
        ValueError: ``fck`` 또는 ``d_p`` 가 0 이하인 경우

    Returns:
        긴장재의 극한 응력 (MPa)
    """
    if fck <= 0 or d_p <= 0:
        msg = "fck 와 d_p 는 0 보다 커야 합니다."
        raise ValueError(msg)

    bracket = rho_p * fpu / fck + d / d_p * (omega - omega_prime)

    return float(fpu * (1.0 - gamma_p / beta_1 * bracket))


def tendon_stress_unbonded(
    f_pe: float,
    fck: float,
    rho_p: float,
    fpy: float,
    span_depth_ratio: float = 30.0,
) -> float:
    r"""비부착 긴장재의 극한 응력 :math:`f_{ps}` 를 반환한다.

    **KDS 14 20 60 4.4.2(4), 식 (4.4-2), (4.4-3)**

    경간/깊이 비 :math:`\le 35`

    .. math::
        f_{ps} = f_{pe} + 70 + \frac{f_{ck}}{100\rho_p}
        \le \min(f_{py},\ f_{pe} + 420)

    경간/깊이 비 :math:`> 35`

    .. math::
        f_{ps} = f_{pe} + 70 + \frac{f_{ck}}{300\rho_p}
        \le \min(f_{py},\ f_{pe} + 210)

    Args:
        f_pe: 유효 프리스트레스 (MPa)
        fck: 콘크리트 설계기준압축강도 (MPa)
        rho_p: 긴장재비 :math:`A_{ps} / (b d_p)`
        fpy: 긴장재의 항복강도 (MPa)
        span_depth_ratio: 경간/깊이 비. 기본값 ``30``.

    Raises:
        ValueError: ``rho_p`` 가 0 이하인 경우

    Returns:
        긴장재의 극한 응력 (MPa)
    """
    if rho_p <= 0:
        msg = "rho_p 는 0 보다 커야 합니다."
        raise ValueError(msg)

    if span_depth_ratio <= 35.0:
        f_ps = f_pe + 70.0 + fck / (100.0 * rho_p)
        cap = min(fpy, f_pe + 420.0)
    else:
        f_ps = f_pe + 70.0 + fck / (300.0 * rho_p)
        cap = min(fpy, f_pe + 210.0)

    return float(min(f_ps, cap))


def capacity_reduction_factor_psc(
    eps_t: float,
    column_type: str = "tie",
) -> float:
    r"""프리스트레스트 부재의 강도감소계수를 반환한다.

    **KDS 14 20 10 4.3.3(2), KDS 14 20 20 4.1.2(3), (4)**

    프리스트레스트 부재는 최외단 인장 긴장재·철근의 순인장변형률
    (프리스트레스에 의한 변형률 제외) 기준으로

    - 압축지배 : :math:`\varepsilon_t \le 0.002`
    - 인장지배 : :math:`\varepsilon_t \ge 0.005`

    Args:
        eps_t: 최외단 인장 긴장재·철근의 순인장변형률
        column_type: ``"tie"`` (띠철근) 또는 ``"spiral"`` (나선철근).
            기본값 ``"tie"``.

    Raises:
        ValueError: ``column_type`` 이 정의되지 않은 값인 경우

    Returns:
        강도감소계수
    """
    if column_type == "spiral":
        phi_c = PHI_COMP_SPIRAL
    elif column_type == "tie":
        phi_c = PHI_COMP_TIE
    else:
        msg = 'column_type 은 "tie" 또는 "spiral" 이어야 합니다.'
        raise ValueError(msg)

    if eps_t <= EPS_Y_PSC:
        return phi_c

    if eps_t >= EPS_TL_PSC:
        return PHI_TENSION

    return phi_c + (PHI_TENSION - phi_c) * (eps_t - EPS_Y_PSC) / (
        EPS_TL_PSC - EPS_Y_PSC
    )


class KDSPrestressed:
    """프리스트레스트 콘크리트 단면에 KDS 14 20 을 적용하는 클래스.

    :class:`~concreteproperties.prestressed_section.PrestressedSection` 이
    계산한 공칭강도에 KDS 의 강도감소계수를 적용한다.

    .. note::

        ``concreteproperties`` 는 프리스트레스트 단면의 P-M 상관도와 2축 휨
        상관도를 아직 지원하지 않는다. 이 클래스도 휨강도만 다룬다.

    Args:
        column_type: ``"tie"`` 또는 ``"spiral"``. 기본값 ``"tie"``.
    """

    def __init__(self, column_type: str = "tie") -> None:
        """KDSPrestressed 클래스를 초기화한다.

        Args:
            column_type: ``"tie"`` 또는 ``"spiral"``. 기본값 ``"tie"``.

        Raises:
            ValueError: ``column_type`` 이 정의되지 않은 값인 경우
        """
        if column_type not in ("tie", "spiral"):
            msg = 'column_type 은 "tie" 또는 "spiral" 이어야 합니다.'
            raise ValueError(msg)

        self.column_type = column_type

    def assign_prestressed_section(
        self,
        prestressed_section: PrestressedSection,
    ) -> None:
        """설계기준 객체에 프리스트레스트 단면을 할당한다.

        Args:
            prestressed_section: 해석 대상 프리스트레스트 단면 객체
        """
        self.prestressed_section = prestressed_section

    def extreme_depth(self, theta: float) -> float:
        r"""압축연단에서 가장 먼 긴장재·철근까지의 깊이를 반환한다.

        ``concreteproperties`` 의
        :meth:`~concreteproperties.concrete_section.ConcreteSection.extreme_bar`
        는 격점철근만 대상으로 하므로, 강연선만 배치된 단면에서는 사용할 수
        없다. 이 메서드는 격점철근과 강연선을 함께 검토한다.

        Args:
            theta: 중립축이 수평축과 이루는 각 (radian)

        Raises:
            ValueError: 단면에 격점철근도 강연선도 없는 경우

        Returns:
            압축연단에서 가장 먼 격점 요소까지의 깊이
        """
        from concreteproperties import utils

        section = self.prestressed_section
        lumped = section.reinf_geometries_lumped + section.strand_geometries

        if not lumped:
            msg = "단면에 격점철근 또는 강연선이 하나 이상 있어야 합니다."
            raise ValueError(msg)

        extreme_fibre, _ = utils.calculate_extreme_fibre(
            points=section.compound_geometry.points, theta=theta
        )
        _, ef_v = utils.global_to_local(
            theta=theta, x=extreme_fibre[0], y=extreme_fibre[1]
        )

        d_ext = 0.0

        for geom in lumped:
            centroid = geom.calculate_centroid()
            _, c_v = utils.global_to_local(theta=theta, x=centroid[0], y=centroid[1])
            d_ext = max(d_ext, ef_v - c_v)

        return float(d_ext)

    def net_tensile_strain(
        self,
        theta: float,
        d_n: float,
    ) -> float:
        r"""최외단 인장 긴장재·철근의 순인장변형률을 계산한다.

        .. math::
            \varepsilon_t = \varepsilon_{cu}\frac{d_t - c}{c}

        프리스트레스에 의한 변형률은 포함하지 않는다.

        Args:
            theta: 중립축이 수평축과 이루는 각 (radian)
            d_n: 중립축 깊이

        Returns:
            순인장변형률
        """
        eps_cu = self.prestressed_section.gross_properties.conc_ultimate_strain

        if np.isinf(d_n):
            return -eps_cu

        if d_n <= 0:
            return float("inf")

        d_t = self.extreme_depth(theta=theta)

        return float(eps_cu * (d_t - d_n) / d_n)

    def ultimate_bending_capacity(
        self,
        positive: bool = True,
        n: float = 0,
    ):
        """KDS 의 강도감소계수를 적용한 설계 휨강도를 계산한다.

        Args:
            positive: 정모멘트이면 ``True``. 기본값 ``True``.
            n: 순 축력. 기본값 ``0``.

        Returns:
            설계강도, 공칭강도, 강도감소계수
            (``factored_results``, ``unfactored_results``, ``phi``)
        """
        from copy import deepcopy

        u_res = self.prestressed_section.ultimate_bending_capacity(
            positive=positive, n=n
        )

        theta = 0.0 if positive else float(np.pi)
        eps_t = self.net_tensile_strain(theta=theta, d_n=u_res.d_n)
        phi = capacity_reduction_factor_psc(
            eps_t=eps_t, column_type=self.column_type
        )

        f_res = deepcopy(u_res)
        f_res.n *= phi
        f_res.m_x *= phi
        f_res.m_y *= phi
        f_res.m_xy *= phi

        return f_res, u_res, phi
