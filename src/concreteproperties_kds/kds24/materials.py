r"""KDS 24 14 21 콘크리트교 설계기준(한계상태설계법)의 재료 규정.

KDS 14 와 KDS 24 는 **안전율을 거는 자리가 다르다.**

- KDS 14 (강도설계법) — 재료의 기준값으로 공칭강도를 구한 뒤, 단면 전체에
  강도감소계수 :math:`\phi` 를 한 번 곱한다.
- KDS 24 (한계상태설계법) — 재료마다 **재료계수**를 곱해 설계 재료강도를 만들고,
  그 재료로 단면을 풀면 결과가 곧 설계강도다. 단면에 다시 곱하는 계수는 없다.

그래서 이 모듈은 재료 쪽에서 끝난다. 단면 해석은 재료계수가 이미 반영된
재료를 그대로 쓴다.

근거: KDS 24 14 21 표 1.4-1, 3.1.2, 3.1.2.5, 3.1.2.6
"""

from __future__ import annotations

import concreteproperties.stress_strain_profile as ssp
from scipy.interpolate import interp1d

# ── 재료계수 (표 1.4-1) ───────────────────────────────────────────────────
# 하중조합에 따라 달라진다. 사용·피로한계상태에서는 1.0 이다.
MATERIAL_FACTORS: dict[str, tuple[float, float]] = {
    "극한": (0.65, 0.90),
    "극단상황": (0.65, 0.90),
    "사용": (1.00, 1.00),
    "피로": (1.00, 1.00),
}

PHI_C_ULS = 0.65
"""극한·극단상황한계상태의 콘크리트 재료계수 (표 1.4-1)."""

PHI_S_ULS = 0.90
"""극한·극단상황한계상태의 철근·프리스트레싱 강재 재료계수 (표 1.4-1)."""

ALPHA_CC = 0.85
"""설계압축강도의 유효계수 :math:`\\alpha` (식 (3.1-47))."""

ES = 200.0e3
"""철근의 탄성계수 (MPa)."""

# ── 단면설계용 응력-변형률 곡선의 계수 (표 3.1-3) ─────────────────────────
# 값 자체는 KDS 14 20 20 표 4.1-1 과 같다. 다른 것은 곡선의 최대값이
# 0.85fck 이 아니라 설계압축강도 phi_c(0.85fck) 라는 점이다.
CURVE_FCK = [40.0, 50.0, 60.0, 70.0, 80.0, 90.0]
CURVE_N = [2.00, 1.92, 1.50, 1.29, 1.22, 1.20]
CURVE_EPS_CO = [0.0020, 0.0021, 0.0022, 0.0023, 0.0024, 0.0025]
CURVE_EPS_CU = [0.0033, 0.0032, 0.0031, 0.0030, 0.0029, 0.0028]


def material_factors(limit_state: str = "극한") -> tuple[float, float]:
    r"""한계상태에 따른 재료계수를 반환한다.

    **KDS 24 14 21 1.4.2.3, 표 1.4-1**

    Args:
        limit_state: ``"극한"``, ``"극단상황"``, ``"사용"``, ``"피로"`` 중 하나.
            기본값 ``"극한"``.

    Raises:
        ValueError: 정의되지 않은 한계상태인 경우

    Returns:
        :math:`(\phi_c,\ \phi_s)` — 콘크리트와 강재의 재료계수
    """
    if limit_state not in MATERIAL_FACTORS:
        msg = f"limit_state 는 {list(MATERIAL_FACTORS)} 중 하나여야 합니다."
        raise ValueError(msg)

    return MATERIAL_FACTORS[limit_state]


def mean_compressive_strength(fck: float) -> float:
    r"""평균압축강도 :math:`f_{cm}` 을 반환한다.

    **KDS 24 14 21 3.1.2.1(2), 식 (3.1-1)**

    .. math::

        f_{cm} = f_{ck} + \Delta f

    :math:`\Delta f` 는 40 MPa 이하에서 4 MPa, 60 MPa 이상에서 6 MPa 이며 그
    사이는 직선보간한다. KDS 14 20 10 과 같은 규정이다.

    Args:
        fck: 콘크리트 기준압축강도 (MPa)

    Returns:
        평균압축강도 (MPa)
    """
    if fck <= 40:
        delta_f = 4.0
    elif fck >= 60:
        delta_f = 6.0
    else:
        delta_f = 4.0 + 2.0 * (fck - 40.0) / 20.0

    return fck + delta_f


def mean_tensile_strength(fck: float) -> float:
    r"""평균인장강도 :math:`f_{ctm}` 을 반환한다.

    **KDS 24 14 21 3.1.2.1(4)**

    .. math::

        f_{ctm} = 0.30\,(f_{cm})^{2/3}

    KDS 14 20 30 의 파괴계수 :math:`f_r = 0.63\lambda\sqrt{f_{ck}}` 와는 다른
    식이다. KDS 24 는 평균인장강도를 기준으로 삼고, 파괴계수와는
    :math:`f_{ctm} = 0.5 f_{rm}` 의 관계로 잇는다.

    Args:
        fck: 콘크리트 기준압축강도 (MPa)

    Returns:
        평균인장강도 (MPa)
    """
    return 0.30 * mean_compressive_strength(fck=fck) ** (2.0 / 3.0)


def characteristic_tensile_strength(fck: float) -> float:
    r"""기준인장강도 :math:`f_{ctk}` 를 반환한다.

    **KDS 24 14 21 3.1.2.1(4)**

    .. math::

        f_{ctk} = 0.70\,f_{ctm}

    Args:
        fck: 콘크리트 기준압축강도 (MPa)

    Returns:
        기준인장강도 (MPa)
    """
    return 0.70 * mean_tensile_strength(fck=fck)


def elastic_modulus(fck: float, m_c: float = 2300.0) -> float:
    r"""콘크리트의 탄성계수를 반환한다.

    **KDS 24 14 21 3.1.2.2(1)**

    .. math::

        E_c = 0.077\, m_c^{1.5} \sqrt[3]{f_{cm}}

    KDS 14 20 10 식 (4.3-1) 과 같은 식이다.

    Args:
        fck: 콘크리트 기준압축강도 (MPa)
        m_c: 콘크리트의 단위질량 (kg/m\ :sup:`3`). 기본값 ``2300``.

    Returns:
        탄성계수 (MPa)
    """
    return 0.077 * m_c**1.5 * mean_compressive_strength(fck=fck) ** (1.0 / 3.0)


def design_compressive_strength(fck: float, phi_c: float = PHI_C_ULS) -> float:
    r"""설계압축강도 :math:`f_{cd}` 를 반환한다.

    **KDS 24 14 21 3.1.2.6(1), 식 (3.1-47)**

    .. math::

        f_{cd} = \phi_c\,\alpha\,f_{ck} \qquad (\alpha = 0.85)

    극한한계상태에서 :math:`\phi_c = 0.65` 이므로
    :math:`f_{cd} = 0.5525\,f_{ck}` 다.

    Args:
        fck: 콘크리트 기준압축강도 (MPa)
        phi_c: 콘크리트의 재료계수. 기본값 ``0.65`` (극한한계상태).

    Returns:
        설계압축강도 (MPa)
    """
    return phi_c * ALPHA_CC * fck


def design_tensile_strength(
    fck: float,
    phi_c: float = PHI_C_ULS,
    alpha_t: float = 1.0,
) -> float:
    r"""설계인장강도 :math:`f_{td}` 를 반환한다.

    **KDS 24 14 21 3.1.2.6(2), 식 (3.1-48)**

    .. math::

        f_{td} = \phi_c\,\alpha_t\,f_{ctk}

    :math:`\alpha_t` 는 콘크리트 압축대의 쪼갬인장강도를 산정할 때 0.85 이고,
    그 밖에는 1.0 이다.

    Args:
        fck: 콘크리트 기준압축강도 (MPa)
        phi_c: 콘크리트의 재료계수. 기본값 ``0.65``.
        alpha_t: 인장강도 유효계수. 기본값 ``1.0``.

    Returns:
        설계인장강도 (MPa)
    """
    return phi_c * alpha_t * characteristic_tensile_strength(fck=fck)


def design_yield_strength(fy: float, phi_s: float = PHI_S_ULS) -> float:
    r"""철근의 설계항복강도 :math:`f_{yd}` 를 반환한다.

    **KDS 24 14 21 1.4.2.3, 표 1.4-1**

    .. math::

        f_{yd} = \phi_s\,f_y

    극한한계상태에서 :math:`\phi_s = 0.90` 이다.

    Args:
        fy: 철근의 기준항복강도 (MPa)
        phi_s: 강재의 재료계수. 기본값 ``0.90``.

    Returns:
        설계항복강도 (MPa)
    """
    return phi_s * fy


def curve_parameters(fck: float) -> tuple[float, float, float]:
    r"""단면설계용 응력-변형률 곡선의 계수를 반환한다.

    **KDS 24 14 21 3.1.2.5(2), 표 3.1-3, 식 (3.1-40)~(3.1-42)**

    .. math::

        n = 1.2 + 1.5\left(\frac{100 - f_{ck}}{60}\right)^{4} \leq 2.0

        \varepsilon_{co} = 0.002 + \frac{f_{ck} - 40}{100{,}000} \geq 0.002

        \varepsilon_{cu} = 0.0033 - \frac{f_{ck} - 40}{100{,}000} \leq 0.0033

    값은 KDS 14 20 20 표 4.1-1 과 같다. 두 기준이 같은 곡선 형상을 쓰고,
    차이는 곡선의 최대값(설계압축강도인가 :math:`0.85f_{ck}` 인가)에 있다.

    Args:
        fck: 콘크리트 기준압축강도 (MPa)

    Raises:
        ValueError: ``fck`` 가 90 MPa 를 초과하는 경우

    Returns:
        :math:`(n,\ \varepsilon_{co},\ \varepsilon_{cu})`
    """
    if fck > 90:
        msg = "fck 가 90 MPa 를 초과하면 별도의 조사연구로 값을 정해야 합니다."
        raise ValueError(msg)

    n = min(2.0, 1.2 + 1.5 * ((100.0 - fck) / 60.0) ** 4)
    eps_co = max(0.002, 0.002 + (fck - 40.0) / 100_000.0)
    eps_cu = min(0.0033, 0.0033 - (fck - 40.0) / 100_000.0)

    return n, eps_co, eps_cu


def design_stress(fck: float, eps_c: float, phi_c: float = PHI_C_ULS) -> float:
    r"""단면설계용 응력-변형률 곡선의 압축응력을 반환한다.

    **KDS 24 14 21 3.1.2.5(2)①, 식 (3.1-38), (3.1-39)**

    .. math::

        f_c = \phi_c(0.85 f_{ck})\left[1 - \left(1 -
        \frac{\varepsilon_c}{\varepsilon_{co}}\right)^{n}\right]
        \qquad (\varepsilon_c \leq \varepsilon_{co})

        f_c = \phi_c(0.85 f_{ck})
        \qquad (\varepsilon_{co} < \varepsilon_c \leq \varepsilon_{cu})

    Args:
        fck: 콘크리트 기준압축강도 (MPa)
        eps_c: 콘크리트의 압축변형률 (양수)
        phi_c: 콘크리트의 재료계수. 기본값 ``0.65``.

    Returns:
        압축응력 (MPa). :math:`\varepsilon_c \leq 0` 이면 0.
    """
    n, eps_co, _ = curve_parameters(fck=fck)
    f_cd = design_compressive_strength(fck=fck, phi_c=phi_c)

    if eps_c <= 0:
        return 0.0

    if eps_c >= eps_co:
        return f_cd

    return f_cd * (1.0 - (1.0 - eps_c / eps_co) ** n)


def design_profile(
    fck: float,
    phi_c: float = PHI_C_ULS,
    n_points: int = 24,
) -> ssp.ConcreteUltimateProfile:
    r"""단면설계용 응력-변형률 곡선을 극한 프로파일로 만든다.

    **KDS 24 14 21 3.1.2.5(2)**

    재료계수가 이미 반영되어 있으므로, 이 재료로 단면을 풀면 결과가 곧
    설계강도다.

    Args:
        fck: 콘크리트 기준압축강도 (MPa)
        phi_c: 콘크리트의 재료계수. 기본값 ``0.65``.
        n_points: 상승 곡선부를 나눌 점의 개수. 기본값 ``24``.

    Returns:
        극한 응력-변형률 프로파일
    """
    _, eps_co, eps_cu = curve_parameters(fck=fck)
    f_cd = design_compressive_strength(fck=fck, phi_c=phi_c)

    # 인장측에 0 응력 점을 두지 않으면 첫 구간이 외삽되어 콘크리트가 인장을
    # 부담하게 된다.
    strains = [-eps_co, 0.0]
    stresses = [0.0, 0.0]

    for i in range(1, n_points + 1):
        eps = eps_co * i / n_points
        strains.append(eps)
        stresses.append(design_stress(fck=fck, eps_c=eps, phi_c=phi_c))

    strains.append(eps_cu)
    stresses.append(f_cd)

    return ssp.ConcreteUltimateProfile(
        strains=strains,
        stresses=stresses,
        compressive_strength=fck,
    )


def equivalent_block(fck: float, phi_c: float = PHI_C_ULS) -> tuple[float, float]:
    r"""포물선-직선 곡선과 등가인 직사각형 응력블록의 계수를 반환한다.

    곡선의 **면적과 도심**을 맞춘 값이며, 손계산 검산에 쓴다.

    .. math::

        C = \alpha_{eq}\,f_{cd}\,b\,c,
        \qquad \text{합력 위치} = \beta_{eq}\,c \ \text{(압축연단에서)}

    Args:
        fck: 콘크리트 기준압축강도 (MPa)
        phi_c: 콘크리트의 재료계수. 기본값 ``0.65``.

    Returns:
        :math:`(\alpha_{eq},\ \beta_{eq})`
    """
    n, eps_co, eps_cu = curve_parameters(fck=fck)
    f_cd = design_compressive_strength(fck=fck, phi_c=phi_c)

    # 중립축 깊이를 1 로 두고 수치적분한다 (변형률은 선형 분포).
    steps = 2000
    area = 0.0
    moment = 0.0
    for i in range(steps):
        y = (i + 0.5) / steps  # 압축연단에서의 상대 거리
        f_c = design_stress(fck=fck, eps_c=eps_cu * (1.0 - y), phi_c=phi_c)
        area += f_c / steps
        moment += f_c * y / steps

    alpha_eq = area / f_cd
    beta_eq = moment / area if area > 0 else 0.0

    return alpha_eq, beta_eq


def concrete_curve_table() -> str:
    """표 3.1-3 을 사람이 읽는 표로 만든다.

    Returns:
        여러 줄 문자열
    """
    header = f"{'fck':>5} {'n':>7} {'eps_co':>9} {'eps_cu':>9} {'fcd':>8}"
    lines = [header, "-" * len(header)]

    for fck in (18, 21, 24, 27, 30, 35, 40, 50, 60, 70, 80, 90):
        n, eps_co, eps_cu = curve_parameters(fck=fck)
        f_cd = design_compressive_strength(fck=fck)
        lines.append(f"{fck:5.0f} {n:7.2f} {eps_co:9.4f} {eps_cu:9.4f} {f_cd:8.2f}")

    return "\n".join(lines)


# interp1d 를 쓰는 표 보간이 필요할 때를 위한 도우미
_CURVE_N = interp1d(CURVE_FCK, CURVE_N)
_CURVE_EPS_CO = interp1d(CURVE_FCK, CURVE_EPS_CO)
_CURVE_EPS_CU = interp1d(CURVE_FCK, CURVE_EPS_CU)
