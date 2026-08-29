r"""KDS 24 14 21 4.2 사용한계상태, 4.3 피로한계상태.

KDS 14 20 30 의 사용성과 뼈대는 같지만 두 가지가 다르다.

* **재료계수가 1.0 이다** (표 1.4-1). 사용·피로한계상태에서는 안전율을 재료에
  걸지 않고, 대신 응력과 균열폭을 직접 제한한다.
* **노출 환경이 설계등급을 정하고, 설계등급이 검증할 하중조합을 정한다**
  (표 4.2-1, 표 4.2-2). KDS 14 는 균열폭 한계를 환경별로 주지만, KDS 24 는
  "어느 하중조합에서 인장을 아예 허용하지 않을 것인가"까지 등급으로 묶는다.
  해상 교량의 프리텐션 부재가 B 등급이 되어 사용하중조합-I 에서 균열폭
  0.2 mm 이하이면서 사용하중조합-III/IV 에서는 연단이 압축이어야 하는 식이다.

근거: KDS 24 14 21 4.2 (표 4.2-1 ~ 표 4.2-5, 식 (4.2-1) ~ 식 (4.2-8)),
4.3 (식 (4.3-1), 식 (4.3-2), 표 4.3-1)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .materials import ES, characteristic_tensile_strength, mean_tensile_strength

# ── 표 4.2-1 노출 환경에 따라 요구되는 최소 설계 등급 ──────────────────────
EXPOSURE_MINIMUM_GRADE: dict[str, dict[str, str]] = {
    "건조/수중": {
        "포스트텐션": "D",
        "프리텐션": "D",
        "비부착": "E",
        "철근콘크리트": "E",
    },
    "부식성": {
        "포스트텐션": "C",
        "프리텐션": "C",
        "비부착": "E",
        "철근콘크리트": "E",
    },
    "고부식성": {
        "포스트텐션": "C",
        "프리텐션": "B",
        "비부착": "E",
        "철근콘크리트": "E",
    },
}
"""표 4.2-1 — 노출 환경 × 부재 종류 → 최소 설계 등급.

``"건조/수중"`` 은 EC1, ``"부식성"`` 은 EC2~EC4, ``"고부식성"`` 은 ED1~ED3,
ES1~ES3 에 해당한다.
"""


@dataclass(frozen=True)
class DesignGrade:
    """표 4.2-2 의 설계 등급 한 줄.

    Args:
        grade: 등급 (``"A"`` ~ ``"E"``)
        zero_stress_combination: 영응력 한계상태를 검증할 하중조합
        crack_combination: 균열폭 한계상태를 검증할 하중조합
        crack_width: 한계균열폭 (mm)
    """

    grade: str
    zero_stress_combination: str | None
    crack_combination: str | None
    crack_width: float | None


DESIGN_GRADES: dict[str, DesignGrade] = {
    "A": DesignGrade("A", "사용Ⅰ", None, None),
    "B": DesignGrade("B", "사용Ⅲ/Ⅳ", "사용Ⅰ", 0.2),
    "C": DesignGrade("C", "사용Ⅴ", "사용Ⅲ/Ⅳ", 0.2),
    "D": DesignGrade("D", None, "사용Ⅲ/Ⅳ", 0.3),
    "E": DesignGrade("E", None, "사용Ⅴ", 0.3),
}
"""표 4.2-2 — 설계 등급에 따른 사용 한계값."""


def minimum_design_grade(exposure: str, member: str) -> DesignGrade:
    """노출 환경과 부재 종류로부터 최소 설계 등급을 반환한다.

    **KDS 24 14 21 4.2.1.2(1), 표 4.2-1**

    Args:
        exposure: ``"건조/수중"``, ``"부식성"``, ``"고부식성"`` 중 하나
        member: ``"포스트텐션"``, ``"프리텐션"``, ``"비부착"``,
            ``"철근콘크리트"`` 중 하나

    Raises:
        ValueError: 표에 없는 조합인 경우

    Returns:
        :class:`DesignGrade`
    """
    if exposure not in EXPOSURE_MINIMUM_GRADE:
        msg = f"표 4.2-1 에 없는 노출 환경: {exposure}"
        raise ValueError(msg)

    row = EXPOSURE_MINIMUM_GRADE[exposure]

    if member not in row:
        msg = f"표 4.2-1 에 없는 부재 종류: {member}"
        raise ValueError(msg)

    return DESIGN_GRADES[row[member]]


# ── 4.2.2 응력 한계 ────────────────────────────────────────────────────────
CONCRETE_STRESS_RATIO_SUSTAINED = 0.45
"""사용하중조합-Ⅴ 에서의 콘크리트 압축응력 한계 :math:`0.45 f_{ck}` (4.2.2.1(1)①)."""

CONCRETE_STRESS_RATIO_SERVICE = 0.60
"""사용하중조합-Ⅰ 과 제작·운반 시의 한계 :math:`0.6 f_{ck}` (4.2.2.1(1)②)."""

STEEL_STRESS_RATIO = 0.80
"""사용하중조합-Ⅰ 에서의 철근 인장응력 한계 :math:`0.8 f_y` (4.2.2.1(2)①)."""

TENDON_STRESS_RATIO = 0.65
"""사용하중조합-Ⅴ 에서의 긴장재 응력 한계 :math:`0.65 f_{pu}` (4.2.2.1(2)②)."""


def concrete_stress_limit(fck: float, sustained: bool = False) -> float:
    r"""콘크리트 압축응력의 한계를 반환한다.

    **KDS 24 14 21 4.2.2.1(1)**

    .. math::
        f_c \le 0.45 f_{ck} \ (\text{사용}\,Ⅴ), \qquad
        f_c \le 0.60 f_{ck} \ (\text{사용}\,Ⅰ)

    :math:`0.45 f_{ck}` 는 크리프가 선형에서 벗어나기 시작하는 지점이다. 오래
    걸려 있는 하중에는 이 선을, 잠깐 지나가는 하중에는 :math:`0.6 f_{ck}` 를
    적용한다.

    Args:
        fck: 콘크리트 기준압축강도 (MPa)
        sustained: 지속하중(사용하중조합-Ⅴ)인지 여부. 기본값 ``False``.

    Returns:
        압축응력 한계 (MPa)
    """
    ratio = (
        CONCRETE_STRESS_RATIO_SUSTAINED if sustained else CONCRETE_STRESS_RATIO_SERVICE
    )

    return ratio * fck


def steel_stress_limit(fy: float) -> float:
    """사용하중조합-Ⅰ 의 철근 인장응력 한계 :math:`0.8 f_y` 를 반환한다.

    **KDS 24 14 21 4.2.2.1(2)①**

    Args:
        fy: 철근의 기준항복강도 (MPa)

    Returns:
        인장응력 한계 (MPa)
    """
    return STEEL_STRESS_RATIO * fy


def tendon_stress_limit(fpu: float) -> float:
    """사용하중조합-Ⅴ 의 긴장재 응력 한계 :math:`0.65 f_{pu}` 를 반환한다.

    **KDS 24 14 21 4.2.2.1(2)②**

    Args:
        fpu: 긴장재의 인장강도 (MPa)

    Returns:
        응력 한계 (MPa)
    """
    return TENDON_STRESS_RATIO * fpu


# ── 4.2.3.2 최소철근량 ─────────────────────────────────────────────────────
def stress_distribution_factor(
    f_n: float = 0.0,
    f_ct: float = 3.0,
    h: float = 500.0,
    pure_tension: bool = False,
    compression: bool = True,
) -> float:
    r"""균열 직전 응력 분포를 반영하는 계수 :math:`k_c` 를 반환한다.

    **KDS 24 14 21 4.2.3.2(2)**

    .. math::
        k_c = 0.4 \left[ 1 - \frac{f_n}{k_1 (h/h^*) f_{ct}} \right] \le 1

    순수인장이면 1.0 이다. 휨을 받는 복부는 단면의 절반만 인장이라 0.4 에서
    출발하고, 축압축이 걸릴수록 더 줄어든다.

    Args:
        f_n: 단면의 평균 법선응력 :math:`N_u/bh` (MPa). 압축이 양수.
        f_ct: 첫 균열 시 유효한 콘크리트 인장강도 (MPa)
        h: 단면 깊이 (mm)
        pure_tension: 순수인장인지 여부. 기본값 ``False``.
        compression: 축력이 압축인지 여부. 기본값 ``True``.

    Returns:
        :math:`k_c`
    """
    if pure_tension:
        return 1.0

    h_star = min(h, 1000.0)
    k_1 = 1.5 if compression else 2.0 * h_star / (3.0 * h)

    return min(0.4 * (1.0 - f_n / (k_1 * (h / h_star) * f_ct)), 1.0)


def nonuniform_stress_factor(width: float) -> float:
    """간접하중에 의한 부등 응력 분포 계수 :math:`k` 를 반환한다.

    **KDS 24 14 21 4.2.3.2(2)**

    단면 깊이 또는 플랜지 너비가 300 mm 이하면 1.0, 800 mm 이상이면 0.65 이며
    중간은 직선보간한다.

    Args:
        width: 단면 깊이 또는 복부폭을 포함한 플랜지 너비 (mm)

    Returns:
        :math:`k`
    """
    if width <= 300.0:
        return 1.0

    if width >= 800.0:
        return 0.65

    return 1.0 - 0.35 * (width - 300.0) / 500.0


def minimum_crack_reinforcement(
    a_ct: float,
    f_ct: float,
    f_s: float,
    k_c: float = 0.4,
    k: float = 1.0,
) -> float:
    r"""균열 제어를 위한 최소철근량 :math:`A_{s,min}` 을 반환한다.

    **KDS 24 14 21 4.2.3.2(2) 식 (4.2-1)**

    .. math::
        A_{s,min} = k_c\, k\, A_{ct} \frac{f_{ct}}{f_s}

    설계의 의도는 "균열 직전에 콘크리트가 들고 있던 인장력을, 균열 직후에 철근이
    받아 낼 수 있어야 한다"는 것이다. 그렇지 않으면 첫 균열에서 철근이 곧바로
    항복해 균열 하나가 크게 벌어진다.

    Args:
        a_ct: 첫 균열 직전의 콘크리트 인장 영역 단면적 (mm²)
        f_ct: 첫 균열 시 유효한 콘크리트 인장강도 (MPa)
        f_s: 균열 직후 허용하는 철근의 인장응력 (MPa)
        k_c: 응력 분포 계수. 기본값 ``0.4`` (휨을 받는 복부).
        k: 부등 응력 분포 계수. 기본값 ``1.0``.

    Raises:
        ValueError: 철근 응력이 0 이하인 경우

    Returns:
        최소철근량 (mm²)
    """
    if f_s <= 0:
        msg = f"f_s 는 0 보다 커야 한다: {f_s}"
        raise ValueError(msg)

    return k_c * k * a_ct * f_ct / f_s


# ── 4.2.3.3 간접 균열 제어 (표 4.2-4, 표 4.2-5) ────────────────────────────
_CRACK_CONTROL_STRESSES = (160.0, 200.0, 240.0, 280.0, 320.0, 360.0)

MAX_BAR_DIAMETER: dict[str, tuple[float, ...]] = {
    "철근콘크리트": (32.0, 25.0, 16.0, 14.0, 10.0, 8.0),
    "프리스트레스트": (25.0, 16.0, 13.0, 8.0, 6.0, 5.0),
}
"""표 4.2-4 — 철근 응력별 최대 철근 지름 (mm)."""

MAX_BAR_SPACING: dict[str, tuple[float | None, ...]] = {
    "철근콘크리트_휨": (300.0, 250.0, 200.0, 150.0, 100.0, 50.0),
    "철근콘크리트_인장": (200.0, 150.0, 125.0, 75.0, None, None),
    "프리스트레스트": (200.0, 150.0, 100.0, 50.0, None, None),
}
"""표 4.2-5 — 철근 응력별 최대 철근 간격 (mm). ``None`` 은 표에 값이 없음."""


def _interpolate(stress: float, values: tuple[float | None, ...], label: str) -> float:
    """표 4.2-4·4.2-5 를 철근 응력으로 보간한다."""
    if stress <= _CRACK_CONTROL_STRESSES[0]:
        first = values[0]

        if first is None:
            msg = f"{label} 에 값이 없다"
            raise ValueError(msg)

        return first

    for i in range(len(_CRACK_CONTROL_STRESSES) - 1):
        low, high = _CRACK_CONTROL_STRESSES[i], _CRACK_CONTROL_STRESSES[i + 1]

        if stress <= high:
            v_low, v_high = values[i], values[i + 1]

            if v_low is None or v_high is None:
                msg = (
                    f"{label} 는 철근 응력 {stress:.0f} MPa 를 다루지 않는다. "
                    "철근량을 늘려 응력을 낮추어야 한다."
                )
                raise ValueError(msg)

            ratio = (stress - low) / (high - low)

            return v_low + ratio * (v_high - v_low)

    msg = (
        f"{label} 의 상한(360 MPa)을 넘는 철근 응력: {stress:.0f} MPa. "
        "철근량을 늘려 응력을 낮추어야 한다."
    )
    raise ValueError(msg)


def max_bar_diameter(f_s: float, member: str = "철근콘크리트") -> float:
    """균열 제어를 위한 최대 철근 지름을 반환한다.

    **KDS 24 14 21 4.2.3.3(1), 표 4.2-4**

    Args:
        f_s: 균열 단면 기준으로 계산한 철근 응력 (MPa)
        member: ``"철근콘크리트"`` 또는 ``"프리스트레스트"``.
            기본값 ``"철근콘크리트"``.

    Raises:
        ValueError: 표에 없는 부재 종류이거나 응력이 표의 범위를 벗어난 경우

    Returns:
        최대 철근 지름 (mm)
    """
    if member not in MAX_BAR_DIAMETER:
        msg = f"표 4.2-4 에 없는 부재 종류: {member}"
        raise ValueError(msg)

    return _interpolate(f_s, MAX_BAR_DIAMETER[member], "표 4.2-4")


def max_bar_spacing(f_s: float, member: str = "철근콘크리트_휨") -> float:
    """균열 제어를 위한 최대 철근 간격을 반환한다.

    **KDS 24 14 21 4.2.3.3(1), 표 4.2-5**

    Args:
        f_s: 균열 단면 기준으로 계산한 철근 응력 (MPa)
        member: ``"철근콘크리트_휨"``, ``"철근콘크리트_인장"``,
            ``"프리스트레스트"`` 중 하나. 기본값 ``"철근콘크리트_휨"``.

    Raises:
        ValueError: 표에 없는 부재 종류이거나 응력이 표의 범위를 벗어난 경우

    Returns:
        최대 철근 간격 (mm)
    """
    if member not in MAX_BAR_SPACING:
        msg = f"표 4.2-5 에 없는 부재 종류: {member}"
        raise ValueError(msg)

    return _interpolate(f_s, MAX_BAR_SPACING[member], "표 4.2-5")


# ── 4.2.3.4 균열폭 계산 ────────────────────────────────────────────────────
K_T_SHORT_TERM = 0.6
K_T_LONG_TERM = 0.4
"""식 (4.2-5) 의 :math:`k_t` — 단기하중 0.6, 장기하중 0.4."""

BOND_FACTOR_DEFORMED = 0.8
BOND_FACTOR_PLAIN = 1.6
"""식 (4.2-7a) 의 :math:`k_1` — 이형철근 0.8, 원형철근·긴장재 1.6."""

LOAD_FACTOR_FLEXURE = 0.5
LOAD_FACTOR_TENSION = 1.0
"""식 (4.2-7a) 의 :math:`k_2` — 휨 0.5, 직접인장 1.0."""


def effective_tension_depth(h: float, d: float, c: float) -> float:
    r"""콘크리트 유효 인장깊이 :math:`d_{cte}` 를 반환한다.

    **KDS 24 14 21 4.2.3.4(2), 그림 4.2-1**

    .. math::
        d_{cte} = \min \left[ 2.5 (h - d),\ \frac{h - c}{3},\ \frac{h}{2} \right]

    균열폭을 좌우하는 것은 단면 전체가 아니라 **철근 주위의 콘크리트다**. 그
    범위를 정하는 규정이다.

    Args:
        h: 단면 전체 깊이 (mm)
        d: 유효깊이 (mm)
        c: 중립축 깊이 (mm)

    Returns:
        유효 인장깊이 (mm)
    """
    return min(2.5 * (h - d), (h - c) / 3.0, h / 2.0)


def strain_difference(
    f_so: float,
    f_cte: float,
    rho_e: float,
    n: float,
    k_t: float = K_T_LONG_TERM,
) -> float:
    r"""철근과 콘크리트의 평균 변형률 차이를 반환한다.

    **KDS 24 14 21 4.2.3.4(2) 식 (4.2-5)**

    .. math::
        \varepsilon_{sm} - \varepsilon_{cm}
        = \frac{f_{so}}{E_s}
        - k_t \frac{f_{cte}}{E_s \rho_e} \left( 1 + n \rho_e \right)
        \ge 0.6 \frac{f_{so}}{E_s}

    빼는 항이 **인장강화효과다**. 균열과 균열 사이의 콘크리트가 아직 인장을
    나눠 지고 있어 철근 변형률이 균열면 값보다 작다는 뜻이며, 하한 0.6 은 그
    효과를 지나치게 크게 보지 않도록 막는다.

    Args:
        f_so: 균열면에서 계산한 철근 인장응력 (MPa)
        f_cte: 첫 균열 시 유효한 콘크리트 인장강도 (MPa)
        rho_e: 유효 철근비 :math:`\rho_e`
        n: 탄성계수비 :math:`E_s/E_c`
        k_t: 하중 지속에 따른 계수. 기본값 ``0.4`` (장기하중).

    Raises:
        ValueError: 유효 철근비가 0 이하인 경우

    Returns:
        변형률 차이
    """
    if rho_e <= 0:
        msg = f"rho_e 는 0 보다 커야 한다: {rho_e}"
        raise ValueError(msg)

    value = f_so / ES - k_t * f_cte / (ES * rho_e) * (1.0 + n * rho_e)

    return max(value, 0.6 * f_so / ES)


def crack_spacing(
    c_c: float,
    d_b: float,
    rho_e: float,
    k_1: float = BOND_FACTOR_DEFORMED,
    k_2: float = LOAD_FACTOR_FLEXURE,
) -> float:
    r"""최대 균열 간격 :math:`l_{r,max}` 를 반환한다.

    **KDS 24 14 21 4.2.3.4(3) 식 (4.2-7a)**

    .. math::
        l_{r,max} = 3.4 c_c + \frac{0.425 k_1 k_2 d_b}{\rho_e}

    피복이 두꺼울수록, 철근이 굵을수록, 철근비가 낮을수록 균열이 드문드문
    생기고 그만큼 하나하나가 넓어진다.

    Args:
        c_c: 최외단 인장철근 표면과 콘크리트 표면 사이의 최소 피복두께 (mm)
        d_b: 인장철근의 지름 (mm)
        rho_e: 유효 인장면적 기준 철근비
        k_1: 부착강도 계수. 기본값 ``0.8`` (이형철근).
        k_2: 하중작용 계수. 기본값 ``0.5`` (휨).

    Raises:
        ValueError: 유효 철근비가 0 이하인 경우

    Returns:
        최대 균열 간격 (mm)
    """
    if rho_e <= 0:
        msg = f"rho_e 는 0 보다 커야 한다: {rho_e}"
        raise ValueError(msg)

    return 3.4 * c_c + 0.425 * k_1 * k_2 * d_b / rho_e


def crack_spacing_unreinforced(h: float, c: float) -> float:
    r"""철근 간격이 넓거나 철근이 없을 때의 :math:`l_{r,max}`.

    **KDS 24 14 21 4.2.3.4(3) 식 (4.2-7b)**

    .. math::
        l_{r,max} = 1.3 (h - c)

    부착된 강재의 중심간격이 :math:`5(c_c + d_b/2)` 를 넘으면 이 식을 쓴다.

    Args:
        h: 단면 전체 깊이 (mm)
        c: 중립축 깊이 (mm)

    Returns:
        최대 균열 간격 (mm)
    """
    return 1.3 * (h - c)


@dataclass(frozen=True)
class CrackWidthCheck:
    """균열폭 검토 결과.

    Args:
        w_k: 설계 균열폭 (mm)
        limit: 한계균열폭 (mm)
        crack_spacing: 최대 균열 간격 (mm)
        strain_difference: 평균 변형률 차이
        adequate: 한계값 이내인지 여부
    """

    w_k: float
    limit: float
    crack_spacing: float
    strain_difference: float
    adequate: bool


def crack_width(
    f_so: float,
    fck: float,
    rho_e: float,
    c_c: float,
    d_b: float,
    n: float = 7.0,
    k_t: float = K_T_LONG_TERM,
    k_1: float = BOND_FACTOR_DEFORMED,
    k_2: float = LOAD_FACTOR_FLEXURE,
    limit: float = 0.3,
) -> CrackWidthCheck:
    r"""설계 균열폭 :math:`w_k` 를 계산하고 한계값과 견준다.

    **KDS 24 14 21 4.2.3.4(1) 식 (4.2-4)**

    .. math::
        w_k = l_{r,max} \left( \varepsilon_{sm} - \varepsilon_{cm} \right)

    Args:
        f_so: 균열면의 철근 인장응력 (MPa)
        fck: 콘크리트 기준압축강도 (MPa)
        rho_e: 유효 인장면적 기준 철근비
        c_c: 최소 피복두께 (mm)
        d_b: 인장철근 지름 (mm)
        n: 탄성계수비 :math:`E_s/E_c`. 기본값 ``7.0``.
        k_t: 하중 지속 계수. 기본값 ``0.4``.
        k_1: 부착강도 계수. 기본값 ``0.8``.
        k_2: 하중작용 계수. 기본값 ``0.5``.
        limit: 한계균열폭 (mm). 기본값 ``0.3``.

    Returns:
        :class:`CrackWidthCheck`
    """
    f_cte = mean_tensile_strength(fck=fck)
    l_r = crack_spacing(c_c=c_c, d_b=d_b, rho_e=rho_e, k_1=k_1, k_2=k_2)
    eps = strain_difference(f_so=f_so, f_cte=f_cte, rho_e=rho_e, n=n, k_t=k_t)
    w_k = l_r * eps

    return CrackWidthCheck(
        w_k=w_k,
        limit=limit,
        crack_spacing=l_r,
        strain_difference=eps,
        adequate=w_k <= limit,
    )


def web_effective_tensile_strength(f_2: float, fck: float) -> float:
    r"""2축 응력 상태인 복부의 유효인장강도 :math:`f_{cte}` 를 반환한다.

    **KDS 24 14 21 4.2.3.3(5) 식 (4.2-3)**

    .. math::
        f_{cte} = \left( 1 - 0.8 \frac{f_2}{f_{ck}} \right) f_{ctk}

    복부가 이미 사압축을 받고 있으면 인장 쪽 여력이 준다. PSC 거더의 복부 균열을
    다룰 때 쓴다.

    Args:
        f_2: 주압축응력 (MPa). 압축이 양수이며 :math:`f_2 \le 0.6 f_{ck}`.
        fck: 콘크리트 기준압축강도 (MPa)

    Returns:
        유효인장강도 (MPa)
    """
    return (1.0 - 0.8 * f_2 / fck) * characteristic_tensile_strength(fck=fck)


# ── 4.2.4 처짐 ─────────────────────────────────────────────────────────────
def deflection_limit(
    span: float, pedestrian: bool = False, cantilever: bool = False
) -> float:
    """사용하중과 충격에 의한 처짐 한계를 반환한다.

    **KDS 24 14 21 4.2.4.1(2), (3)**

    단순·연속경간은 :math:`L/800`, 보행자도 쓰는 도시지역 교량은 :math:`L/1{,}000`
    이다. 캔틸레버는 각각 :math:`L/300`, :math:`L/375` 이다.

    Args:
        span: 지간 (mm). 캔틸레버는 내민 길이.
        pedestrian: 보행자가 이용하는지 여부. 기본값 ``False``.
        cantilever: 캔틸레버인지 여부. 기본값 ``False``.

    Returns:
        처짐 한계 (mm)
    """
    if cantilever:
        divisor = 375.0 if pedestrian else 300.0
    else:
        divisor = 1000.0 if pedestrian else 800.0

    return span / divisor


# ── 4.3 피로한계상태 ───────────────────────────────────────────────────────
FATIGUE_INTERCEPT_PLAIN = 166.0
FATIGUE_INTERCEPT_WELDED = 110.0
FATIGUE_SLOPE = 0.33
"""식 (4.3-1), (4.3-2) 의 계수."""

COUPLER_FATIGUE_STRENGTH: dict[str, float] = {
    "그라우트채움": 126.0,
    "냉간압연슬리브": 126.0,
    "일체식단조": 126.0,
    "쐐기식슬리브": 84.0,
    "경사나선": 84.0,
    "V홈용접": 84.0,
    "기타": 28.0,
}
"""표 4.3-1 — 1백만 회를 넘는 경우의 이음부 공칭피로강도 (MPa)."""


def fatigue_stress_range_limit(f_min: float = 0.0, welded: bool = False) -> float:
    r"""철근의 허용 피로응력범위를 반환한다.

    **KDS 24 14 21 4.3.2(1), (2) 식 (4.3-1), 식 (4.3-2)**

    .. math::
        f_{fat} = 166 - 0.33 f_{min} \quad (\text{가로 용접 없음})

    .. math::
        f_{fat} = 110 - 0.33 f_{min} \quad (\text{가로 용접 있음})

    :math:`f_{min}` 은 피로하중조합에 의한 **최소 활하중 응력**, 인장이 양수다.
    이미 인장을 받고 있는 철근일수록 허용 진폭이 줄어든다.

    Args:
        f_min: 최소 활하중 응력 (MPa). 인장이 양수. 기본값 ``0.0``.
        welded: 가로방향 용접이 있는 용접 철선인지 여부. 기본값 ``False``.

    Returns:
        허용 피로응력범위 (MPa)
    """
    intercept = FATIGUE_INTERCEPT_WELDED if welded else FATIGUE_INTERCEPT_PLAIN

    return intercept - FATIGUE_SLOPE * f_min


def coupler_fatigue_strength(kind: str, n_cycles: float | None = None) -> float:
    r"""이음부의 공칭피로강도를 반환한다.

    **KDS 24 14 21 4.3.4, 표 4.3-1**

    재하수가 1백만 회 이하이면 :math:`168 (6 - \log N_{cyc})` MPa 만큼 올릴 수
    있되, 식 (4.3-1) 의 값을 넘지 못한다.

    Args:
        kind: :data:`COUPLER_FATIGUE_STRENGTH` 의 이음부 종류
        n_cycles: 전체 하중재하수 :math:`N_{cyc}`. ``None`` 이면 증가시키지 않는다.

    Raises:
        ValueError: 표에 없는 이음부 종류인 경우

    Returns:
        공칭피로강도 (MPa)
    """
    if kind not in COUPLER_FATIGUE_STRENGTH:
        msg = f"표 4.3-1 에 없는 이음부 종류: {kind}"
        raise ValueError(msg)

    strength = COUPLER_FATIGUE_STRENGTH[kind]

    if n_cycles is not None and 0 < n_cycles <= 1.0e6:
        strength += 168.0 * (6.0 - math.log10(n_cycles))

    return min(strength, fatigue_stress_range_limit())


def fatigue_check_required(f_dead_compression: float, f_live_tension: float) -> bool:
    """피로한계상태를 검증해야 하는지 판단한다.

    **KDS 24 14 21 4.3.1(4)**

    고정하중과 프리스트레스에 의한 압축응력이 피로하중조합의 최대 활하중
    인장응력의 **두 배 미만일** 때만 검증한다. 압축이 충분히 크면 철근이 인장으로
    넘어가지 않아 응력 진폭이 생기지 않기 때문이다.

    Args:
        f_dead_compression: 고정하중과 프리스트레스에 의한 압축응력 (MPa)
        f_live_tension: 피로하중조합의 최대 활하중 인장응력 (MPa)

    Returns:
        검증이 필요하면 ``True``
    """
    return f_dead_compression < 2.0 * f_live_tension
