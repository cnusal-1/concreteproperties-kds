r"""KDS 24 14 21 4.1.2 전단 (한계상태설계법).

KDS 14 와 **전단강도를 보는 방식 자체가 다르다.**

* KDS 14 20 22 — :math:`V_c` (콘크리트 기여분) 와 :math:`V_s` (전단철근 기여분)
  를 **더하고**, 단면에 :math:`\phi = 0.75` 를 곱한다. :math:`V_c` 는
  :math:`\tfrac{1}{6}\sqrt{f_{ck}}\, b_w d` 처럼 압축강도의 제곱근에 비례한다.
* KDS 24 14 21 — 전단철근이 있으면 :math:`V_{cd}` 를 **더하지 않는다.** 변각
  트러스 모델로 전단철근만으로 전단력을 받는다고 보고, 콘크리트는 스트럿의 압축
  파괴 한계 :math:`V_{d,max}` 로만 등장한다. 전단철근이 없을 때의
  :math:`V_{cd}` 는 :math:`(\rho f_{ck})^{1/3}` 에 비례해, 철근비가 강도만큼
  중요하다는 실험 결과를 그대로 담았다.

설계의 의도가 여기서 갈린다. KDS 14 는 "콘크리트가 얼마쯤 버티고 나머지를 철근이
받는다"고 보고, KDS 24 는 "균열이 생긴 뒤에는 철근이 다 받는다. 대신 스트럿 각도를
눕혀 철근을 아낄 수 있다"고 본다. :math:`\cot\theta` 를 1 에서 2.5 까지 고를 수
있게 한 것이 이 자유도다.

근거: KDS 24 14 21 4.1.2 (식 (4.1-7) ~ 식 (4.1-27)), 4.6.2.6
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .materials import (
    PHI_C_ULS,
    PHI_S_ULS,
    characteristic_tensile_strength,
)

COT_THETA_MIN = 1.0
COT_THETA_MAX = 2.5
"""스트럿 경사각의 범위, 식 (4.1-15). :math:`1 \\le \\cot\\theta \\le 2.5`."""

RHO_MAX = 0.02
""":math:`V_{cd}` 식에 넣는 인장철근비의 상한, 4.1.2.2(1)."""

KAPPA_MAX = 2.0
"""단면 크기 효과 계수 :math:`\\kappa` 의 상한."""

Z_RATIO = 0.9
"""단면 내부 팔길이 :math:`z \\approx 0.9d`, 4.1.2.3(2)."""


def kappa(d: float) -> float:
    r"""단면 크기 효과 계수 :math:`\kappa` 를 반환한다.

    **KDS 24 14 21 4.1.2.2(1)**

    .. math::
        \kappa = 1 + \sqrt{200/d} \le 2.0 \qquad (d \text{ 는 mm})

    깊은 단면일수록 단위면적당 전단강도가 떨어진다는 크기 효과를 반영한다.
    :math:`d = 200\ \text{mm}` 에서 2.0 으로 상한에 걸린다.

    Args:
        d: 단면 유효깊이 (mm)

    Raises:
        ValueError: 유효깊이가 0 이하인 경우

    Returns:
        :math:`\kappa`
    """
    if d <= 0:
        msg = f"d 는 0 보다 커야 한다: {d}"
        raise ValueError(msg)

    return min(1.0 + math.sqrt(200.0 / d), KAPPA_MAX)


def nu(fck: float) -> float:
    r"""콘크리트 압축강도 유효계수 :math:`\nu` 를 반환한다.

    **KDS 24 14 21 4.1.2.2(3) 식 (4.1-12)**

    .. math::
        \nu = 0.6 \left( 1 - \frac{f_{ck}}{250} \right)

    균열이 난 복부의 스트럿은 온전한 압축시험체만큼 강하지 않다. 고강도일수록
    취성이 커져 더 깎인다.

    Args:
        fck: 콘크리트 기준압축강도 (MPa)

    Returns:
        :math:`\nu`
    """
    return 0.6 * (1.0 - fck / 250.0)


def axial_stress(n_u: float, a_c: float, fck: float, phi_c: float = PHI_C_ULS) -> float:
    r"""단면의 평균 축응력 :math:`f_n` 을 반환한다.

    **KDS 24 14 21 4.1.2.2(1)**

    .. math::
        f_n = N_u / A_c \le 0.2 \phi_c f_{ck} \qquad (\text{압축일 때 } +)

    Args:
        n_u: 계수 축력 :math:`N_u` (N). 압축이 양수.
        a_c: 콘크리트 단면적 :math:`A_c` (mm²)
        fck: 콘크리트 기준압축강도 (MPa)
        phi_c: 콘크리트 재료계수. 기본값 ``0.65``.

    Raises:
        ValueError: 단면적이 0 이하인 경우

    Returns:
        평균 축응력 (MPa)
    """
    if a_c <= 0:
        msg = f"a_c 는 0 보다 커야 한다: {a_c}"
        raise ValueError(msg)

    return min(n_u / a_c, 0.2 * phi_c * fck)


def concrete_shear_strength(
    fck: float,
    b_w: float,
    d: float,
    a_s: float,
    f_n: float = 0.0,
    phi_c: float = PHI_C_ULS,
) -> float:
    r"""전단철근이 없는 부재의 설계전단강도 :math:`V_{cd}` 를 반환한다.

    **KDS 24 14 21 4.1.2.2(1) 식 (4.1-7)**

    .. math::
        V_{cd} = \left[ 0.85 \phi_c \kappa (\rho f_{ck})^{1/3}
        + 0.15 f_n \right] b_w d

    :math:`(\rho f_{ck})^{1/3}` 가 이 식의 핵심이다. KDS 14 의 :math:`\sqrt{f_{ck}}`
    와 달리 **인장철근비가 함께 들어간다.** 철근이 많으면 균열이 촘촘하고 좁게
    생겨 골재 맞물림이 잘 살아 있기 때문이다.

    Args:
        fck: 콘크리트 기준압축강도 (MPa)
        b_w: 복부폭 (mm)
        d: 단면 유효깊이 (mm)
        a_s: 인장철근량 :math:`A_s` (mm²)
        f_n: 평균 축응력 (MPa). 압축이 양수. 기본값 ``0.0``.
        phi_c: 콘크리트 재료계수. 기본값 ``0.65``.

    Returns:
        설계전단강도 (N)
    """
    rho = min(a_s / (b_w * d), RHO_MAX)
    k = kappa(d=d)

    return (0.85 * phi_c * k * (rho * fck) ** (1 / 3) + 0.15 * f_n) * b_w * d


def minimum_concrete_shear_strength(
    fck: float,
    b_w: float,
    d: float,
    f_n: float = 0.0,
    phi_c: float = PHI_C_ULS,
) -> float:
    r"""최소 설계전단강도 :math:`V_{cd,min}` 을 반환한다.

    **KDS 24 14 21 4.1.2.2(1) 식 (4.1-8)**

    .. math::
        V_{cd,min} = \left( 0.4 \phi_c f_{ctk} + 0.15 f_n \right) b_w d

    철근비가 아주 작아도 콘크리트의 인장강도만큼은 버틴다는 하한이다.

    Args:
        fck: 콘크리트 기준압축강도 (MPa)
        b_w: 복부폭 (mm)
        d: 단면 유효깊이 (mm)
        f_n: 평균 축응력 (MPa). 기본값 ``0.0``.
        phi_c: 콘크리트 재료계수. 기본값 ``0.65``.

    Returns:
        최소 설계전단강도 (N)
    """
    f_ctk = characteristic_tensile_strength(fck=fck)

    return (0.4 * phi_c * f_ctk + 0.15 * f_n) * b_w * d


def design_concrete_shear_strength(
    fck: float,
    b_w: float,
    d: float,
    a_s: float,
    f_n: float = 0.0,
    phi_c: float = PHI_C_ULS,
) -> float:
    """식 (4.1-7) 과 식 (4.1-8) 중 큰 값을 반환한다.

    Args:
        fck: 콘크리트 기준압축강도 (MPa)
        b_w: 복부폭 (mm)
        d: 단면 유효깊이 (mm)
        a_s: 인장철근량 (mm²)
        f_n: 평균 축응력 (MPa). 기본값 ``0.0``.
        phi_c: 콘크리트 재료계수. 기본값 ``0.65``.

    Returns:
        설계전단강도 (N)
    """
    return max(
        concrete_shear_strength(fck=fck, b_w=b_w, d=d, a_s=a_s, f_n=f_n, phi_c=phi_c),
        minimum_concrete_shear_strength(fck=fck, b_w=b_w, d=d, f_n=f_n, phi_c=phi_c),
    )


def uncracked_shear_strength(
    fck: float,
    b_w: float,
    second_moment: float,
    first_moment: float,
    f_n: float,
    alpha_l: float = 1.0,
    phi_c: float = PHI_C_ULS,
) -> float:
    r"""휨균열이 없는 프리스트레스트 구간의 설계전단강도를 반환한다.

    **KDS 24 14 21 4.1.2.2(2) 식 (4.1-9)**

    .. math::
        V_{cd} = \frac{I b_w}{Q}
        \sqrt{(\phi_c f_{ctk})^2 + \alpha_l f_n \phi_c f_{ctk}}

    휨균열이 없으면 단면 전체가 살아 있으므로, 주인장응력이 콘크리트 인장강도에
    닿는 순간을 강도로 본다. 프리스트레스에 의한 압축 :math:`f_n` 이 클수록 그
    순간이 늦게 온다.

    Args:
        fck: 콘크리트 기준압축강도 (MPa)
        b_w: 복부폭 (mm)
        second_moment: 단면2차모멘트 :math:`I` (mm⁴)
        first_moment: 도심축 위쪽 단면의 도심축에 대한 단면1차모멘트
            :math:`Q` (mm³)
        f_n: 평균 압축응력 (MPa). 압축이 양수.
        alpha_l: 전달길이 보정 :math:`\alpha_l \le 1.0`. 기본값 ``1.0``.
        phi_c: 콘크리트 재료계수. 기본값 ``0.65``.

    Returns:
        설계전단강도 (N)
    """
    f_ctd = phi_c * characteristic_tensile_strength(fck=fck)

    return (
        second_moment * b_w / first_moment * math.sqrt(f_ctd**2 + alpha_l * f_n * f_ctd)
    )


def max_shear_strength(
    fck: float,
    b_w: float,
    d: float,
    cot_theta: float = 2.5,
    phi_c: float = PHI_C_ULS,
) -> float:
    r"""복부 스트럿의 압축 파괴로 정해지는 :math:`V_{d,max}` 를 반환한다.

    **KDS 24 14 21 4.1.2.3(2) 식 (4.1-17)**

    .. math::
        V_{d,max} = \frac{\nu \phi_c f_{ck} b_w z}{\cot\theta + \tan\theta}

    전단철근을 아무리 넣어도 넘을 수 없는 한계다. :math:`\cot\theta = 1`
    (:math:`\theta = 45°`) 에서 최대가 되므로, 철근을 아끼려 각을 눕히면
    (:math:`\cot\theta \to 2.5`) 이 한계는 낮아진다. 두 요구가 반대로 움직인다는
    것이 변각 트러스 모델의 핵심이다.

    Args:
        fck: 콘크리트 기준압축강도 (MPa)
        b_w: 복부폭 (mm)
        d: 단면 유효깊이 (mm)
        cot_theta: 스트럿 경사각의 :math:`\cot\theta`. 기본값 ``2.5``.
        phi_c: 콘크리트 재료계수. 기본값 ``0.65``.

    Returns:
        최대 설계전단강도 (N)
    """
    _check_cot_theta(cot_theta)
    z = Z_RATIO * d

    return nu(fck=fck) * phi_c * fck * b_w * z / (cot_theta + 1.0 / cot_theta)


def alpha_cw(f_n: float, fck: float, phi_c: float = PHI_C_ULS) -> float:
    r"""축방향 압축이 있을 때의 :math:`\alpha_{cw}` 를 반환한다.

    **KDS 24 14 21 4.1.2.3(4) 식 (4.1-23)**

    .. math::
        \alpha_{cw} = \begin{cases}
        1 + f_n / \phi_c f_{ck} & 0 < f_n \le 0.25 \phi_c f_{ck} \\
        1.25 & 0.25 \phi_c f_{ck} < f_n \le 0.50 \phi_c f_{ck} \\
        2.5 \left( 1 - f_n / \phi_c f_{ck} \right)
        & 0.50 \phi_c f_{ck} < f_n \le 1.0 \phi_c f_{ck}
        \end{cases}

    프리스트레스가 적당하면 스트럿 한계가 최대 25 % 올라가지만, 지나치면 오히려
    떨어진다. 복부가 이미 압축으로 차 있기 때문이다.

    Args:
        f_n: 계수하중에 의한 평균 압축응력 (MPa)
        fck: 콘크리트 기준압축강도 (MPa)
        phi_c: 콘크리트 재료계수. 기본값 ``0.65``.

    Returns:
        :math:`\alpha_{cw}`
    """
    f_cd = phi_c * fck
    ratio = f_n / f_cd

    if f_n <= 0.0:
        return 1.0

    if ratio <= 0.25:
        return 1.0 + ratio

    if ratio <= 0.50:
        return 1.25

    return max(2.5 * (1.0 - ratio), 0.0)


def shear_reinforcement_strength(
    f_vy: float,
    a_v: float,
    d: float,
    s: float,
    cot_theta: float = 2.5,
    phi_s: float = PHI_S_ULS,
) -> float:
    r"""수직 스터럽이 배치된 부재의 설계전단강도 :math:`V_{sd}` 를 반환한다.

    **KDS 24 14 21 4.1.2.3(2) 식 (4.1-16)**

    .. math::
        V_{sd} = \frac{\phi_s f_{vy} A_v z}{s} \cot\theta

    KDS 14 의 :math:`V_s = A_v f_{yt} d / s` 와 비교하면 :math:`\cot\theta` 만큼
    커진다. 스트럿을 눕히면 균열 하나를 더 많은 스터럽이 가로지르기 때문이다.

    Args:
        f_vy: 전단철근의 항복강도 (MPa)
        a_v: 간격 :math:`s` 안의 전단철근 단면적 (mm²)
        d: 단면 유효깊이 (mm)
        s: 전단철근 간격 (mm)
        cot_theta: :math:`\cot\theta`. 기본값 ``2.5``.
        phi_s: 강재 재료계수. 기본값 ``0.90``.

    Returns:
        설계전단강도 (N)
    """
    _check_cot_theta(cot_theta)
    z = Z_RATIO * d

    return phi_s * f_vy * a_v * z / s * cot_theta


def maximum_shear_reinforcement(
    fck: float,
    b_w: float,
    s: float,
    f_y: float,
    phi_c: float = PHI_C_ULS,
    phi_s: float = PHI_S_ULS,
) -> float:
    r"""최대 허용 전단철근량 :math:`A_{v,max}` 를 반환한다.

    **KDS 24 14 21 4.1.2.3(2) 식 (4.1-18)**

    .. math::
        \frac{\phi_s f_y A_{v,max}}{b_w s} \le 0.5 \nu \phi_c f_{ck}

    Args:
        fck: 콘크리트 기준압축강도 (MPa)
        b_w: 복부폭 (mm)
        s: 전단철근 간격 (mm)
        f_y: 전단철근의 항복강도 (MPa)
        phi_c: 콘크리트 재료계수. 기본값 ``0.65``.
        phi_s: 강재 재료계수. 기본값 ``0.90``.

    Returns:
        최대 전단철근 단면적 (mm²)
    """
    return 0.5 * nu(fck=fck) * phi_c * fck * b_w * s / (phi_s * f_y)


def minimum_shear_reinforcement_ratio(fck: float, f_y: float) -> float:
    r"""최소 전단철근비 :math:`\rho_{v,min}` 을 반환한다.

    **KDS 24 14 21 4.6.2.6(5) 식 (4.6-7)**

    .. math::
        \rho_{v,min} = \frac{0.08 \sqrt{f_{ck}}}{f_y}

    Args:
        fck: 콘크리트 기준압축강도 (MPa)
        f_y: 전단철근의 항복강도 (MPa)

    Returns:
        최소 전단철근비
    """
    return 0.08 * math.sqrt(fck) / f_y


def maximum_stirrup_spacing(d: float, alpha: float = 90.0) -> float:
    r"""전단철근의 최대 종방향 간격 :math:`s_{max}` 를 반환한다.

    **KDS 24 14 21 4.6.2.6(6) 식 (4.6-8)**

    .. math::
        s_{max} = 0.75 d \left( 1 + \cot\alpha \right)

    Args:
        d: 단면 유효깊이 (mm)
        alpha: 전단철근과 부재축의 각 (도). 기본값 ``90.0`` (수직 스터럽).

    Returns:
        최대 간격 (mm)
    """
    cot_alpha = 1.0 / math.tan(math.radians(alpha))

    return 0.75 * d * (1.0 + cot_alpha)


@dataclass(frozen=True)
class ShearCheck:
    """전단 검토 결과.

    Args:
        v_ed: 계수 전단력 :math:`V_d` (N)
        v_cd: 전단철근이 없을 때의 설계전단강도 (N)
        v_sd: 전단철근의 설계전단강도 (N)
        v_d_max: 스트럿 압축 파괴 한계 (N)
        cot_theta: 사용한 :math:`\\cot\\theta`
        stirrups_required: 계산에 의한 전단철근이 필요한지 여부
        adequate: 검토를 만족하는지 여부
        ratio: :math:`V_d / \\min(V_{sd},\\, V_{d,max})`
    """

    v_ed: float
    v_cd: float
    v_sd: float
    v_d_max: float
    cot_theta: float
    stirrups_required: bool
    adequate: bool
    ratio: float


def check_shear(
    v_ed: float,
    fck: float,
    b_w: float,
    d: float,
    a_s: float,
    f_vy: float = 400.0,
    a_v: float = 0.0,
    s: float = 0.0,
    cot_theta: float = 2.5,
    f_n: float = 0.0,
    phi_c: float = PHI_C_ULS,
    phi_s: float = PHI_S_ULS,
) -> ShearCheck:
    r"""한 단면의 전단 검토를 수행한다.

    **KDS 24 14 21 4.1.2.1**

    전단철근이 배치되면 설계전단강도는 :math:`V_{sd}` 하나로 정해진다. KDS 14 처럼
    :math:`V_{cd}` 를 더하지 않는다. :math:`V_{cd}` 는 "전단철근을 계산으로 넣을
    것인가 최소량만 넣을 것인가"를 가르는 문턱으로만 쓰인다 (4.1.2.1(5), (6)).

    Args:
        v_ed: 계수 전단력 (N)
        fck: 콘크리트 기준압축강도 (MPa)
        b_w: 복부폭 (mm)
        d: 단면 유효깊이 (mm)
        a_s: 인장철근량 (mm²)
        f_vy: 전단철근의 항복강도 (MPa). 기본값 ``400.0``.
        a_v: 간격 :math:`s` 안의 전단철근 단면적 (mm²). 기본값 ``0.0``.
        s: 전단철근 간격 (mm). 기본값 ``0.0`` (전단철근 없음).
        cot_theta: :math:`\cot\theta`. 기본값 ``2.5``.
        f_n: 평균 축응력 (MPa). 기본값 ``0.0``.
        phi_c: 콘크리트 재료계수. 기본값 ``0.65``.
        phi_s: 강재 재료계수. 기본값 ``0.90``.

    Returns:
        :class:`ShearCheck`
    """
    v_cd = design_concrete_shear_strength(
        fck=fck, b_w=b_w, d=d, a_s=a_s, f_n=f_n, phi_c=phi_c
    )
    v_max = max_shear_strength(fck=fck, b_w=b_w, d=d, cot_theta=cot_theta, phi_c=phi_c)

    if f_n > 0:
        v_max *= alpha_cw(f_n=f_n, fck=fck, phi_c=phi_c)

    if a_v > 0 and s > 0:
        v_sd = shear_reinforcement_strength(
            f_vy=f_vy, a_v=a_v, d=d, s=s, cot_theta=cot_theta, phi_s=phi_s
        )
        capacity = min(v_sd, v_max)
    else:
        v_sd = 0.0
        capacity = v_cd

    return ShearCheck(
        v_ed=v_ed,
        v_cd=v_cd,
        v_sd=v_sd,
        v_d_max=v_max,
        cot_theta=cot_theta,
        stirrups_required=v_ed > v_cd,
        adequate=v_ed <= capacity,
        ratio=v_ed / capacity if capacity else float("inf"),
    )


def required_stirrup_spacing(
    v_ed: float,
    d: float,
    a_v: float,
    f_vy: float = 400.0,
    cot_theta: float = 2.5,
    phi_s: float = PHI_S_ULS,
) -> float:
    r"""요구 전단강도를 만족하는 전단철근 간격을 반환한다.

    식 (4.1-16) 을 :math:`s` 에 대해 푼 것이다.

    .. math::
        s = \frac{\phi_s f_{vy} A_v z \cot\theta}{V_d}

    Args:
        v_ed: 계수 전단력 (N)
        d: 단면 유효깊이 (mm)
        a_v: 한 단면의 전단철근 단면적 (mm²)
        f_vy: 전단철근의 항복강도 (MPa). 기본값 ``400.0``.
        cot_theta: :math:`\cot\theta`. 기본값 ``2.5``.
        phi_s: 강재 재료계수. 기본값 ``0.90``.

    Raises:
        ValueError: 전단력이 0 이하인 경우

    Returns:
        요구 간격 (mm)
    """
    if v_ed <= 0:
        msg = f"v_ed 는 0 보다 커야 한다: {v_ed}"
        raise ValueError(msg)

    _check_cot_theta(cot_theta)

    return phi_s * f_vy * a_v * Z_RATIO * d * cot_theta / v_ed


def _check_cot_theta(cot_theta: float) -> None:
    """식 (4.1-15) 의 범위를 벗어나면 거부한다."""
    if not COT_THETA_MIN <= cot_theta <= COT_THETA_MAX:
        msg = (
            f"cot_theta 는 {COT_THETA_MIN} 이상 {COT_THETA_MAX} 이하여야 한다 "
            f"(식 (4.1-15)): {cot_theta}"
        )
        raise ValueError(msg)
