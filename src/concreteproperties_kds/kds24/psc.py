r"""프리스트레스트 콘크리트 (KDS 24 14 21 1.5.7, 3.3).

KDS 14 20 60 과 **손실을 세는 방식이 다르다.**

* KDS 14 20 60 — 항목별 손실을 각각 구해 더한다. 릴랙세이션은
  :math:`f_{pj}(\log t / 10)(f_{pj}/f_{py} - 0.55)` 같은 경험식이다.
* KDS 24 14 21 — 장기 손실을 **식 (1.5-12) 하나로 묶어** 푼다. 크리프·건조수축·
  릴랙세이션이 서로를 줄인다는 사실을 분모의 상호작용 항으로 반영하고, 그 위에
  감소계수 0.8 을 또 곱한다.

왜 묶는가. 콘크리트가 크리프로 줄어들면 긴장재가 느슨해지고, 느슨해진 긴장재는
릴랙세이션이 덜 일어난다. 세 손실을 따로 구해 더하면 이 상쇄를 놓쳐 **손실을
과대평가**한다. 식 (1.5-12) 의 분모가 그 되먹임을 담고 있다.

근거: KDS 24 14 21 1.5.7.2 (식 (1.5-7), (1.5-8)), 1.5.7.3 (식 (1.5-9)),
1.5.7.4 (식 (1.5-10) ~ (1.5-12), 표 1.5-2), 3.3.2 (식 (3.3-1) ~ (3.3-3))
"""

from __future__ import annotations

import math
from dataclasses import dataclass

E_P = 200.0e3
"""프리스트레싱 강재의 탄성계수 (MPa), 3.3.3(2), (3)."""

JACKING_RATIO_FPU = 0.80
JACKING_RATIO_FPY = 0.90
"""식 (1.5-7) — :math:`f_{o,max} = \\min(0.8 f_{pu},\\ 0.9 f_{py})`."""

OVERTENSION_RATIO_FPY = 0.95
"""1.5.7.2(1)② — 긴장력을 ±5 % 정확도로 계측하면 여기까지 올릴 수 있다."""

TRANSFER_RATIO_LOW = 0.75
TRANSFER_RATIO_HIGH = 0.85
"""식 (1.5-9) 의 두 계수. 원문은 **둘 다** :math:`f_{py}` 에 곱한다."""

CONCRETE_TRANSFER_RATIO = 0.60
CONCRETE_TRANSFER_RATIO_PRE = 0.70
CONCRETE_CREEP_LINEAR_RATIO = 0.45
"""식 (1.5-8) — 긴장·전달 시 콘크리트 압축응력의 한계 (:math:`f_{ck}(t)` 배)."""

CURVATURE_FRICTION: dict[str, dict[str, float]] = {
    "냉간압연강선": {
        "강재덕트_비윤활": 0.17,
        "폴리에틸렌덕트_비윤활": 0.25,
        "강재덕트_윤활": 0.14,
        "폴리에틸렌덕트_윤활": 0.18,
        "비부착외부": 0.12,
    },
    "강연선": {
        "강재덕트_비윤활": 0.19,
        "폴리에틸렌덕트_비윤활": 0.24,
        "강재덕트_윤활": 0.12,
        "폴리에틸렌덕트_윤활": 0.16,
        "비부착외부": 0.10,
    },
    "이형강봉": {"강재덕트_비윤활": 0.65},
    "원형강봉": {"강재덕트_비윤활": 0.33},
}
"""표 1.5-2 — 곡률마찰계수 :math:`\\mu`."""

WOBBLE_RANGE = (0.001, 0.007)
"""1.5.7.4(2)②다 — 파상마찰계수 :math:`k` 의 일반적인 범위 (/m)."""

RHO_1000: dict[int, float] = {1: 8.0, 2: 2.5, 3: 4.0}
"""3.3.2(7)③ — 릴랙세이션 등급별 :math:`\\rho_{1000}` (%).

Class 1 은 보통 릴랙세이션 강선·강연선, Class 2 는 저릴랙세이션, Class 3 은
열연 강봉이다.
"""

RELAXATION_COEFFICIENTS: dict[int, tuple[float, float]] = {
    1: (5.39, 6.7),
    2: (0.66, 9.1),
    3: (1.98, 8.0),
}
"""식 (3.3-1) ~ (3.3-3) 의 (계수, 지수)."""

FINAL_RELAXATION_HOURS = 500_000.0
"""3.3.2(7)⑤ — 릴랙세이션의 최종값은 500,000 시간(약 57년)으로 본다."""

CREEP_RELAXATION_REDUCTION = 0.8
"""1.5.7.4(3)① — 크리프·건조수축과 릴랙세이션의 상호작용 감소계수."""


def max_jacking_stress(fpu: float, fpy: float, overtension: bool = False) -> float:
    r"""긴장작업 시 긴장단의 최대 응력 :math:`f_{o,max}` 를 반환한다.

    **KDS 24 14 21 1.5.7.2(1) 식 (1.5-7)**

    .. math::
        f_{o,max} = \min \left( 0.8 f_{pu},\ 0.9 f_{py} \right)

    긴장력을 최종 프리스트레스 힘의 ±5 % 정확도로 계측할 수 있으면
    :math:`0.95 f_{py}` 까지 초과 긴장할 수 있다.

    Args:
        fpu: 긴장재의 기준인장강도 (MPa)
        fpy: 긴장재의 기준항복강도 (MPa)
        overtension: 초과 긴장 허용 여부. 기본값 ``False``.

    Returns:
        최대 긴장응력 (MPa)
    """
    if overtension:
        return OVERTENSION_RATIO_FPY * fpy

    return min(JACKING_RATIO_FPU * fpu, JACKING_RATIO_FPY * fpy)


def stress_after_transfer(fpy: float) -> float:
    r"""프리스트레스 도입 직후의 긴장재 응력 :math:`f_{pmo}` 를 반환한다.

    **KDS 24 14 21 1.5.7.3(1) 식 (1.5-9)**

    .. math::
        f_{pmo} = \min \left( 0.75 f_{py},\ 0.85 f_{py} \right) = 0.75 f_{py}

    .. note::
        원문은 두 계수를 **모두** :math:`f_{py}` 에 곱하도록 적고 있어, 작은 쪽인
        :math:`0.75 f_{py}` 가 언제나 이긴다. 바로 앞 식 (1.5-7) 이
        :math:`\min(0.8 f_{pu},\ 0.9 f_{py})` 처럼 인장강도와 항복강도를 짝지어
        쓰는 것과 형태가 다르므로, 실무에서는 발주자·감리와 해석을 맞추기를
        권한다. 이 함수는 **원문 그대로** 구현한다.

    Args:
        fpy: 긴장재의 기준항복강도 (MPa)

    Returns:
        도입 직후의 긴장재 응력 (MPa)
    """
    return min(TRANSFER_RATIO_LOW * fpy, TRANSFER_RATIO_HIGH * fpy)


def concrete_stress_limit_at_transfer(fck_t: float, pretension: bool = False) -> float:
    r"""긴장·전달 시 콘크리트 압축응력의 한계를 반환한다.

    **KDS 24 14 21 1.5.7.2(2)③ 식 (1.5-8)**

    .. math::
        f_c \le 0.6 f_{ck}(t)

    프리텐션 부재는 실험·경험으로 입증되면 :math:`0.7 f_{ck}(t)` 까지 올릴 수
    있다. :math:`0.45 f_{ck}(t)` 를 영구히 넘으면 크리프의 비선형성을 따로
    고려해야 한다.

    Args:
        fck_t: 프리스트레스를 받는 시점의 콘크리트 설계기준압축강도 (MPa)
        pretension: 프리텐션 부재인지 여부. 기본값 ``False``.

    Returns:
        압축응력 한계 (MPa)
    """
    ratio = CONCRETE_TRANSFER_RATIO_PRE if pretension else CONCRETE_TRANSFER_RATIO

    return ratio * fck_t


def friction_loss(
    p_o: float,
    theta: float,
    x: float,
    mu: float = 0.19,
    k: float = 0.004,
) -> float:
    r"""포스트텐션 마찰에 의한 프리스트레스 손실을 반환한다.

    **KDS 24 14 21 1.5.7.4(2)② 식 (1.5-11)**

    .. math::
        \Delta P_{\mu}(x) = P_o \left( 1 - e^{-(\mu\theta + kx)} \right)

    :math:`\mu\theta` 는 **곡률** 마찰, :math:`kx` 는 덕트가 설계 위치에서
    조금씩 흔들리는 **파상** 마찰이다. 긴 거더에서는 뒤쪽이 무시 못 할 만큼
    쌓인다.

    Args:
        p_o: 긴장단의 프리스트레스 힘 (N)
        theta: 거리 :math:`x` 에 걸쳐 누적된 각 변화량 (rad, 부호 무관)
        x: 긴장단으로부터의 거리 (m)
        mu: 곡률마찰계수. 기본값 ``0.19`` (강연선·강재덕트·비윤활, 표 1.5-2).
        k: 파상마찰계수 (/m). 기본값 ``0.004``.

    Returns:
        마찰 손실 (N)
    """
    return p_o * (1.0 - math.exp(-(mu * abs(theta) + k * x)))


def anchorage_set_loss(
    slip: float, length: float, a_p: float, e_p: float = E_P
) -> float:
    r"""정착장치 활동에 의한 손실을 반환한다.

    **KDS 24 14 21 1.5.7.4(2)③**

    .. math::
        \Delta P_{sl} = \frac{\Delta_{sl}}{L} E_p A_p

    기준은 "활동량은 제조사 자료를 사용할 수 있다"고만 한다. 이 함수는 마찰이
    없다고 볼 때의 상한값 — 활동이 긴장재 전체 길이에 고르게 퍼진 경우 — 을
    준다. 실제로는 마찰 때문에 활동의 영향이 정착단 부근에만 미치므로 이보다
    작다.

    Args:
        slip: 정착장치 활동량 :math:`\Delta_{sl}` (mm)
        length: 긴장재의 길이 (mm)
        a_p: 긴장재의 단면적 (mm²)
        e_p: 긴장재의 탄성계수 (MPa). 기본값 ``200,000``.

    Raises:
        ValueError: 길이가 0 이하인 경우

    Returns:
        손실 (N)
    """
    if length <= 0:
        msg = f"length 는 0 보다 커야 한다: {length}"
        raise ValueError(msg)

    return slip / length * e_p * a_p


def elastic_shortening_loss(
    a_p: float,
    delta_fc: float,
    e_cm: float,
    n_tendon: int = 1,
    post_tension: bool = True,
    e_p: float = E_P,
) -> float:
    r"""콘크리트 탄성변형에 의한 손실을 반환한다.

    **KDS 24 14 21 1.5.7.4(2)① 식 (1.5-10)**

    .. math::
        \Delta P_c = A_p E_p \sum \left[
        \frac{j \Delta f_c(t)}{E_{cm}(t)} \right],
        \qquad j = \frac{n - 1}{2n}

    포스트텐션에서 :math:`j = (n-1)/2n` 인 것은 **순서** 때문이다. 마지막으로
    긴장하는 긴장재는 앞선 긴장재가 이미 만든 단축을 겪지 않으므로 손실이 없고,
    첫 번째 긴장재가 가장 많이 잃는다. 평균이 그 절반쯤이라는 뜻이며,
    :math:`n` 이 크면 :math:`j \to 1/2` 이다. 프리텐션은 모든 긴장재가 동시에
    풀리므로 :math:`j = 1` 이다.

    Args:
        a_p: 긴장재의 단면적 (mm²)
        delta_fc: 긴장재 도심 위치의 콘크리트 응력 변화량 (MPa)
        e_cm: 그 시점의 콘크리트 탄성계수 (MPa)
        n_tendon: 순차적으로 긴장하는 긴장재의 개수. 기본값 ``1``.
        post_tension: 포스트텐션인지 여부. 기본값 ``True``.
        e_p: 긴장재의 탄성계수 (MPa). 기본값 ``200,000``.

    Returns:
        손실 (N)
    """
    if not post_tension:
        j = 1.0
    elif n_tendon <= 1:
        j = 0.0
    else:
        j = (n_tendon - 1) / (2.0 * n_tendon)

    return a_p * e_p * j * delta_fc / e_cm


def relaxation_loss(
    f_pi: float,
    fpu: float,
    steel_class: int = 2,
    hours: float = FINAL_RELAXATION_HOURS,
    rho_1000: float | None = None,
) -> float:
    r"""릴랙세이션에 의한 응력 손실 :math:`\Delta f_{pr}` 를 반환한다.

    **KDS 24 14 21 3.3.2(7)④ 식 (3.3-1) ~ (3.3-3)**

    .. math::
        \frac{\Delta f_{pr}}{f_{pi}} = C \rho_{1000}\, e^{\alpha \mu}
        \left( \frac{t}{1000} \right)^{0.75(1 - \mu)} \times 10^{-5},
        \qquad \mu = \frac{f_{pi}}{f_{pu}}

    | 등급 | 대상 | :math:`C` | :math:`\alpha` | :math:`\rho_{1000}` |
    |---|---|---|---|---|
    | 1 | 보통 릴랙세이션 강선·강연선 | 5.39 | 6.7 | 8.0 % |
    | 2 | 저릴랙세이션 강선·강연선 | 0.66 | 9.1 | 2.5 % |
    | 3 | 열연 강봉 | 1.98 | 8.0 | 4.0 % |

    지수에 :math:`\mu` 가 들어가는 것이 핵심이다. 초기 응력이 높을수록 손실이
    **지수적으로** 커진다. 저릴랙세이션(Class 2)의 계수가 8배 작은 대신 지수가
    더 가파른 것도 그래서다.

    Args:
        f_pi: 초기 프리스트레싱 응력 (MPa)
        fpu: 긴장재의 기준인장강도 (MPa)
        steel_class: 릴랙세이션 등급 (1, 2, 3). 기본값 ``2``.
        hours: 경과 시간 (시간). 기본값 ``500,000`` (최종값).
        rho_1000: 1,000시간 릴랙세이션 손실 (%). ``None`` 이면 등급별 기본값.

    Raises:
        ValueError: 등급이 1~3 이 아닌 경우

    Returns:
        응력 손실 (MPa)
    """
    if steel_class not in RELAXATION_COEFFICIENTS:
        msg = f"릴랙세이션 등급은 1, 2, 3 중 하나여야 한다: {steel_class}"
        raise ValueError(msg)

    coeff, alpha = RELAXATION_COEFFICIENTS[steel_class]
    rho = RHO_1000[steel_class] if rho_1000 is None else rho_1000
    mu = f_pi / fpu

    ratio = (
        coeff
        * rho
        * math.exp(alpha * mu)
        * (hours / 1000.0) ** (0.75 * (1.0 - mu))
        * 1e-5
    )

    return ratio * f_pi


def long_term_loss(
    eps_shrinkage: float,
    delta_f_pr: float,
    phi_creep: float,
    f_c_permanent: float,
    f_cpo: float,
    a_p: float,
    a_c: float,
    i_c: float,
    z_cp: float,
    e_cm: float,
    e_p: float = E_P,
) -> float:
    r"""크리프·건조수축·릴랙세이션에 의한 장기 손실을 반환한다.

    **KDS 24 14 21 1.5.7.4(3)② 식 (1.5-12)**

    .. math::
        \Delta f_{p,c+s+r} = \frac{
        \varepsilon_s E_p + 0.8 \Delta f_{pr}
        + \alpha \varphi \left( f_{c(g+q)} + f_{cpo} \right)}{
        1 + \alpha \dfrac{A_p}{A_c}
        \left( 1 + \dfrac{A_c}{I_c} z_{cp}^2 \right)
        \left[ 1 + 0.8 \varphi \right]}

    분자는 세 손실의 단순 합이고, **분모가 되먹임**이다. 긴장재가 느슨해지면
    콘크리트 압축이 줄고, 압축이 줄면 크리프도 줄어 다시 긴장재를 덜 잃게 한다.
    분모를 무시하고 세 항을 그냥 더하면 손실을 과대평가한다.

    :math:`\Delta f_{pr}` 앞의 0.8 도 같은 취지다 — 크리프·건조수축으로 이미
    긴장재가 느슨해진 상태에서는 릴랙세이션이 덜 일어난다.

    Args:
        eps_shrinkage: 건조수축 변형률 :math:`\varepsilon_s(t, t_o)`
        delta_f_pr: 릴랙세이션에 의한 응력 변화량 (MPa)
        phi_creep: 크리프계수 :math:`\varphi(t, t_o)`
        f_c_permanent: 고정하중·지속하중에 의한 긴장재 위치의 콘크리트 응력 (MPa)
        f_cpo: 프리스트레스에 의한 긴장재 위치의 콘크리트 초기응력 (MPa)
        a_p: 긴장재의 단면적 (mm²)
        a_c: 콘크리트 단면적 (mm²)
        i_c: 콘크리트 단면의 단면2차모멘트 (mm⁴)
        z_cp: 콘크리트 도심에서 긴장재까지의 거리 (mm)
        e_cm: 콘크리트 탄성계수 (MPa)
        e_p: 긴장재의 탄성계수 (MPa). 기본값 ``200,000``.

    Raises:
        ValueError: 단면 성질이 0 이하인 경우

    Returns:
        장기 손실 (MPa)
    """
    if a_c <= 0 or i_c <= 0 or e_cm <= 0:
        msg = "a_c, i_c, e_cm 은 0 보다 커야 한다"
        raise ValueError(msg)

    alpha = e_p / e_cm
    numerator = (
        eps_shrinkage * e_p
        + CREEP_RELAXATION_REDUCTION * delta_f_pr
        + alpha * phi_creep * (f_c_permanent + f_cpo)
    )
    denominator = 1.0 + alpha * a_p / a_c * (1.0 + a_c / i_c * z_cp**2) * (
        1.0 + CREEP_RELAXATION_REDUCTION * phi_creep
    )

    return numerator / denominator


@dataclass(frozen=True)
class PrestressLosses:
    """프리스트레스 손실의 내역.

    Args:
        f_jack: 긴장응력 (MPa)
        friction: 마찰 손실 (MPa)
        anchorage: 정착장치 활동 손실 (MPa)
        elastic: 탄성변형 손실 (MPa)
        f_pi: 즉시 손실 후의 응력 (MPa)
        long_term: 장기 손실 (MPa)
        f_pe: 유효 프리스트레스 응력 (MPa)
        immediate_ratio: 즉시 손실률
        total_ratio: 전체 손실률
    """

    f_jack: float
    friction: float
    anchorage: float
    elastic: float
    f_pi: float
    long_term: float
    f_pe: float
    immediate_ratio: float
    total_ratio: float

    def print_results(self) -> None:
        """손실 내역을 표로 출력한다."""
        print(f"{'항목':<16}{'응력 (MPa)':>12}{'비율':>10}")
        print("-" * 40)
        print(f"{'긴장응력':<16}{self.f_jack:12.1f}{'':>10}")
        for name, value in (
            ("마찰", self.friction),
            ("정착장치 활동", self.anchorage),
            ("탄성변형", self.elastic),
        ):
            print(f"{'  - ' + name:<16}{value:12.1f}{value / self.f_jack:9.1%}")
        print(f"{'즉시 손실 후':<16}{self.f_pi:12.1f}{self.immediate_ratio:9.1%}")
        print(
            f"{'  - 장기 손실':<16}{self.long_term:12.1f}"
            f"{self.long_term / self.f_jack:9.1%}"
        )
        print("-" * 40)
        print(f"{'유효 프리스트레스':<16}{self.f_pe:12.1f}{self.total_ratio:9.1%}")
