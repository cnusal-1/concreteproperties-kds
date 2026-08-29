r"""교량 콘크리트 바닥판 설계 (KDS 24 10 11 4.6.2, KDS 24 14 21 4.6.5).

바닥판은 다리에서 **가장 먼저 망가지는 부재다.** 거더는 50년을 가도 바닥판은
20~30년이면 갈아야 하는 경우가 흔하다. 윤하중이 직접 닿고, 제설염이 스며들고,
피로 반복이 가장 심한 곳이기 때문이다. 기준이 바닥판만 따로 떼어 별도의
근사해석법을 두는 것도 그래서다.

**설계의 뼈대**

1. 거더 간격이 바닥판의 지간을 정한다 (4.6.2.3).
2. 윤하중 96 kN 한 개가 폭 :math:`E` 에 퍼진다고 보고 활하중 휨모멘트를
   간략식으로 구한다 (4.6.2.4). 트럭을 굴릴 필요가 없다.
3. 고정하중 휨모멘트는 :math:`wl^2/8`, :math:`wl^2/10`, :math:`wl^2/2` 로 끝난다
   (4.6.2.7).
4. 두 값을 하중조합으로 묶고 1 m 폭 직사각형 단면으로 휨 설계를 한다.
5. **전단은 검토하지 않아도 된다** (4.6.2.2(3)). 다만 윤하중의 뚫림전단은
   따로 본다 (KDS 24 14 21 4.6.5.1(8)).

전단을 빼도 되는 이유는, 이 근사식들이 이미 뚫림·아치작용을 포함한 실물 실험에
맞춰 보정된 값이기 때문이다. 같은 이유로 **경험적 설계법** (4.6.5.2) 은 아예
해석 없이 단면적의 0.3 % 씩 네 층을 깔라고만 한다 — 바닥판의 실제 거동이 휨이
아니라 아치작용이라는 관찰에 근거한다.

근거: KDS 24 10 11 4.6.2 (식 (4.6-1) ~ (4.6-9), 표 4.6-1, 표 4.6-2),
KDS 24 14 21 4.4.4 (표 4.4-3, 표 4.4-4), 4.6.5
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .materials import (
    PHI_C_ULS,
    PHI_S_ULS,
    design_compressive_strength,
    design_yield_strength,
    equivalent_block,
)
from .serviceability import max_bar_diameter, max_bar_spacing

# ── 상수 ───────────────────────────────────────────────────────────────────
WHEEL_LOAD = 96.0
"""설계차량활하중의 1후륜하중 :math:`P` (kN), 4.6.2.4(2).

KL-510 의 192 kN 축을 좌우로 나눈 값이다.
"""

MIN_THICKNESS_RC = 220.0
"""철근콘크리트 바닥판의 최소 두께 (mm), KDS 24 14 21 4.6.5.1(5).

홈이나 마모 방지 층의 두께를 뺀 값이다.
"""

MIN_THICKNESS_PSC = 200.0
"""프리스트레스트 콘크리트 바닥판의 최소 두께 (mm), 4.6.5.1(5)."""

MIN_THICKNESS_EMPIRICAL = 240.0
"""경험적 설계법을 쓰려면 필요한 최소 두께 (mm), 4.6.5.2(3)⑦."""

DECK_FCK = 27.0
"""철근콘크리트 바닥판의 설계기준압축강도 (MPa), KDS 24 10 11 4.6.2.2(2)."""

BAR_SPACING_MIN = 100.0
BAR_SPACING_MAX = 300.0
"""철근 중심간격의 범위 (mm), KDS 24 14 21 4.6.5.2(5)③."""

EMPIRICAL_STEEL_RATIO = 0.003
"""경험적 설계법의 층별 최소 철근비, 4.6.5.2(4)②."""

DELTA_T_DEV = 10.0
"""설계 편차 허용량 :math:`\\Delta t_{c,dev}` (mm), 4.4.4.3(2)."""

EXPOSED_DECK_EXTRA_COVER = 10.0
"""방수·표면처리를 하지 않은 노출 바닥판의 추가 피복 (mm), 4.4.4.2(12)."""

COVER_DURABILITY: dict[str, float] = {
    "E0": 20.0,
    "EC1": 25.0,
    "EC2": 35.0,
    "EC4": 40.0,
    "ED1": 45.0,
    "ED2": 50.0,
    "ED3": 55.0,
}
"""표 4.4-4 — 철근의 내구성 최소피복두께 :math:`t_{c,min,dur}` (mm).

프리스트레싱 강재는 같은 등급에서 20 / 35 / 45 / 50 / 55 / 60 / 65 mm 다.
"""

COVER_DURABILITY_TENDON: dict[str, float] = {
    "E0": 20.0,
    "EC1": 35.0,
    "EC2": 45.0,
    "EC4": 50.0,
    "ED1": 55.0,
    "ED2": 60.0,
    "ED3": 65.0,
}
"""표 4.4-4 — 프리스트레싱 강재의 내구성 최소피복두께 (mm)."""

MARINE_EXTRA_COVER: dict[str, float] = {"ES1": 5.0, "ES2": 10.0, "ES3": 15.0}
"""염화물·해수 노출에서의 추가 피복 :math:`\\Delta t_{c,dur,\\gamma}` (mm), 4.4.4.2(5).

바탕값은 같은 번호의 ED 등급을 쓴다.
"""

DECK_DEFLECTION_DIVISOR: dict[str, float] = {
    "없음": 800.0,
    "제한적": 1000.0,
    "많음": 1200.0,
}
"""바닥판 처짐 한계의 분모, KDS 24 14 21 4.6.5.1(2). 보행량에 따라 달라진다."""


# ── 지간 ───────────────────────────────────────────────────────────────────
def deck_span(girder_spacing: float, thickness: float, web_width: float = 0.0) -> float:
    r"""단순 지지 바닥판의 지간을 반환한다.

    **KDS 24 10 11 4.6.2.3(1)**

    지지보의 중심 간격으로 잡되, **순 지간에 바닥판 두께를 더한 값을 넘길
    필요는 없다.** 지지보가 두꺼우면 중심 간격이 실제보다 불리하게 나오기
    때문이다.

    Args:
        girder_spacing: 지지보의 중심 간격 (m)
        thickness: 바닥판 두께 (mm)
        web_width: 지지보의 폭 (m). 기본값 ``0.0`` (중심 간격을 그대로 쓴다).

    Raises:
        ValueError: 간격이 0 이하인 경우

    Returns:
        바닥판의 지간 (m)
    """
    if girder_spacing <= 0:
        msg = f"girder_spacing 은 0 보다 커야 한다: {girder_spacing}"
        raise ValueError(msg)

    if web_width <= 0:
        return girder_spacing

    clear = girder_spacing - web_width

    return min(girder_spacing, clear + thickness / 1000.0)


# ── 활하중 휨모멘트 (4.6.2.4) ──────────────────────────────────────────────
def live_load_moment(
    span: float,
    wheel_load: float = WHEEL_LOAD,
    continuous: bool = False,
    grade: int = 1,
) -> float:
    r"""주철근이 차량진행방향에 **직각인** 바닥판의 활하중 휨모멘트.

    **KDS 24 10 11 4.6.2.4(2)① 식 (4.6-1)**

    .. math::
        M_t = \frac{(L + 0.6) P}{9.6}
        \qquad [\text{kN} \cdot \text{m/m}]

    지점이 셋 이상인 연속슬래브의 정모멘트는 이 값에 **0.8 배** 를 곱한다.
    충격은 여기에 포함되어 있지 않으므로 따로 곱한다.

    거더교의 바닥판은 거의 언제나 이 경우다 — 거더가 교축방향이니 바닥판은
    교축직각방향으로 휘고, 주철근도 그 방향으로 깔린다.

    Args:
        span: 바닥판의 지간 :math:`L` (m)
        wheel_load: 1후륜하중 :math:`P` (kN). 기본값 ``96.0``.
        continuous: 3지점 이상 연속판인지 여부. 기본값 ``False``.
        grade: 교량 등급 (1, 2, 3). 기본값 ``1``.

    Raises:
        ValueError: 지간이 0 이하인 경우

    Returns:
        휨모멘트 (kN·m/m). 충격 제외.
    """
    if span <= 0:
        msg = f"span 은 0 보다 커야 한다: {span}"
        raise ValueError(msg)

    from .loads import bridge_grade_factor

    moment = (span + 0.6) * wheel_load / 9.6

    if continuous:
        moment *= 0.8

    return moment * bridge_grade_factor(grade=grade)


def wheel_width_parallel(span: float) -> float:
    r"""주철근이 차량진행방향에 **평행할** 때 윤하중이 퍼지는 폭 :math:`E`.

    **KDS 24 10 11 4.6.2.4(2)② 식 (4.6-2)**

    .. math::
        E = 1.2 + 0.06 L \le 2.1\ \text{m}

    Args:
        span: 바닥판의 지간 (m)

    Returns:
        분포폭 (m)
    """
    return min(1.2 + 0.06 * span, 2.1)


def live_load_moment_parallel(span: float, grade: int = 1) -> float:
    r"""주철근이 차량진행방향에 **평행한** 단순판의 활하중 휨모멘트.

    **KDS 24 10 11 4.6.2.4(2)②다**

    .. math::
        M_l = 18 L \qquad [\text{kN} \cdot \text{m/m}]

    지간 6 m 이하에 적용한다. 윤하중 96 kN 이 폭 :math:`E` 에 퍼진 채
    지간 중앙에 놓인 경우와 거의 같은 값이다.

    Args:
        span: 바닥판의 지간 (m)
        grade: 교량 등급. 기본값 ``1``.

    Returns:
        휨모멘트 (kN·m/m). 충격 제외.
    """
    from .loads import bridge_grade_factor

    return 18.0 * span * bridge_grade_factor(grade=grade)


# ── 캔틸레버 (4.6.2.5) ─────────────────────────────────────────────────────
def cantilever_wheel_width(x: float, parallel: bool = False) -> float:
    r"""캔틸레버 바닥판에서 윤하중이 퍼지는 폭 :math:`E`.

    **KDS 24 10 11 4.6.2.5 식 (4.6-4), 식 (4.6-6)**

    .. math::
        E = 0.8 X + 1.14 \quad (\text{주철근이 차량진행방향에 직각})

    .. math::
        E = 0.35 X + 0.98 \le 2.1 \quad (\text{평행})

    Args:
        x: 하중점에서 지지점까지의 거리 :math:`X` (m)
        parallel: 주철근이 차량진행방향에 평행한지 여부. 기본값 ``False``.

    Returns:
        분포폭 (m)
    """
    if parallel:
        return min(0.35 * x + 0.98, 2.1)

    return 0.8 * x + 1.14


def cantilever_live_load_moment(
    x: float,
    wheel_load: float = WHEEL_LOAD,
    parallel: bool = False,
    grade: int = 1,
) -> float:
    r"""캔틸레버 바닥판의 활하중 휨모멘트.

    **KDS 24 10 11 4.6.2.5**

    .. math::
        M = \frac{P}{E} X \qquad [\text{kN} \cdot \text{m/m}]

    윤하중 재하 위치는 차도 끝에서 300 mm 안쪽이다 (4.6.2.3(3)⑤).

    Args:
        x: 하중점에서 지지점까지의 거리 (m)
        wheel_load: 1후륜하중 (kN). 기본값 ``96.0``.
        parallel: 주철근이 차량진행방향에 평행한지 여부. 기본값 ``False``.
        grade: 교량 등급. 기본값 ``1``.

    Raises:
        ValueError: 거리가 0 이하인 경우

    Returns:
        휨모멘트 (kN·m/m). 충격 제외. 부호는 양수로 돌려준다.
    """
    if x <= 0:
        msg = f"x 는 0 보다 커야 한다: {x}"
        raise ValueError(msg)

    from .loads import bridge_grade_factor

    width = cantilever_wheel_width(x=x, parallel=parallel)

    return wheel_load / width * x * bridge_grade_factor(grade=grade)


# ── 고정하중 휨모멘트 (4.6.2.7) ────────────────────────────────────────────
DEAD_LOAD_DIVISORS: dict[str, float] = {
    "단순판": 8.0,
    "연속판_지간": 10.0,
    "연속판_지점": -10.0,
    "캔틸레버판": -2.0,
}
"""표 4.6-2 — :math:`M = w l_d^2 / \\text{divisor}`. 음수는 부모멘트."""


def dead_load_moment(w: float, span: float, kind: str = "단순판") -> float:
    r"""등분포 고정하중에 의한 바닥판의 단위폭 휨모멘트.

    **KDS 24 10 11 4.6.2.7, 표 4.6-2**

    .. math::
        M = +\frac{w l_d^2}{8} \ (\text{단순판}), \quad
        \pm\frac{w l_d^2}{10} \ (\text{연속판}), \quad
        -\frac{w l_d^2}{2} \ (\text{캔틸레버판})

    연속판의 계수 1/10 은 단순판 1/8 과 고정단 1/12 사이의 실용값이다.

    Args:
        w: 등분포 고정하중 (kN/m²)
        span: 고정하중에 대한 바닥판의 지간 :math:`l_d` (m)
        kind: ``"단순판"``, ``"연속판_지간"``, ``"연속판_지점"``,
            ``"캔틸레버판"`` 중 하나. 기본값 ``"단순판"``.

    Raises:
        ValueError: 표에 없는 판의 구분

    Returns:
        휨모멘트 (kN·m/m). 부모멘트는 음수.
    """
    if kind not in DEAD_LOAD_DIVISORS:
        msg = f"표 4.6-2 에 없는 판의 구분: {kind}"
        raise ValueError(msg)

    return w * span**2 / DEAD_LOAD_DIVISORS[kind]


# ── 배력철근 (KDS 24 14 21 4.6.5.3(2)) ─────────────────────────────────────
def distribution_steel_ratio(span: float, parallel: bool = False) -> float:
    r"""배력철근량의 주철근량에 대한 비율을 반환한다.

    **KDS 24 14 21 4.6.5.3(2)①**

    .. math::
        \frac{120}{\sqrt{L}} \le 67\ \% \quad (\text{주철근이 직각})

    .. math::
        \frac{55}{\sqrt{L}} \le 50\ \% \quad (\text{평행})

    윤하중은 한 점에 실리는데 바닥판은 폭을 가진 판이다. 배력철근이 그 집중을
    옆으로 퍼뜨린다. 지간이 짧을수록 퍼뜨릴 몫이 커져 비율이 올라가고, 그래서
    상한이 걸린다.

    Args:
        span: 바닥판의 지간 :math:`L` (m)
        parallel: 주철근이 차량진행방향에 평행한지 여부. 기본값 ``False``.

    Raises:
        ValueError: 지간이 0 이하인 경우

    Returns:
        비율 (0 ~ 0.67)
    """
    if span <= 0:
        msg = f"span 은 0 보다 커야 한다: {span}"
        raise ValueError(msg)

    if parallel:
        return min(55.0 / math.sqrt(span), 50.0) / 100.0

    return min(120.0 / math.sqrt(span), 67.0) / 100.0


# ── 피복두께 (KDS 24 14 21 4.4.4) ──────────────────────────────────────────
def nominal_cover(
    exposure: str = "EC1",
    bar_diameter: float = 16.0,
    exposed_deck: bool = False,
    delta_dev: float = DELTA_T_DEV,
    tendon: bool = False,
) -> tuple[float, float]:
    r"""최소피복두께와 공칭피복두께를 반환한다.

    **KDS 24 14 21 4.4.4 식 (4.4-1), (4.4-2), 표 4.4-3, 표 4.4-4**

    .. math::
        t_{c,min} = \max \left\{ t_{c,min,b};\ t_{c,min,dur}
        + \Delta t_{c,dur,\gamma};\ 10\ \text{mm} \right\}

    .. math::
        t_{c,nom} = t_{c,min} + \Delta t_{c,dev}

    부착에 필요한 최소피복 :math:`t_{c,min,b}` 는 철근 지름과 같다 (표 4.4-3).
    방수·표면처리가 없는 노출 바닥판은 마모 대비로 10 mm 를 더한다 (4.4.4.2(12)).

    Args:
        exposure: 노출등급. ``"E0"``, ``"EC1"``, ``"EC2"``, ``"EC4"``,
            ``"ED1"``~``"ED3"``, ``"ES1"``~``"ES3"``. 기본값 ``"EC1"``.
        bar_diameter: 철근 지름 (mm). 기본값 ``16.0``.
        exposed_deck: 노출 콘크리트 바닥판인지 여부. 기본값 ``False``.
        delta_dev: 설계 편차 허용량 (mm). 기본값 ``10.0``.
        tendon: 프리스트레싱 강재인지 여부. 기본값 ``False``.

    Raises:
        ValueError: 표에 없는 노출등급

    Returns:
        (최소피복두께, 공칭피복두께) — mm
    """
    table = COVER_DURABILITY_TENDON if tendon else COVER_DURABILITY
    extra = 0.0
    key = exposure

    if exposure in MARINE_EXTRA_COVER:
        extra = MARINE_EXTRA_COVER[exposure]
        key = "ED" + exposure[-1]

    if key not in table:
        msg = f"표 4.4-4 에 없는 노출등급: {exposure}"
        raise ValueError(msg)

    t_min = max(bar_diameter, table[key] + extra, 10.0)

    if exposed_deck:
        t_min += EXPOSED_DECK_EXTRA_COVER

    return t_min, t_min + delta_dev


def deck_deflection_limit(span: float, pedestrian: str = "없음") -> float:
    """바닥판의 활하중 처짐 한계를 반환한다.

    **KDS 24 14 21 4.6.5.1(2)**

    Args:
        span: 바닥판 받침부의 중심 간 거리 (mm)
        pedestrian: ``"없음"``, ``"제한적"``, ``"많음"`` 중 하나.
            기본값 ``"없음"``.

    Raises:
        ValueError: 정의되지 않은 보행 조건

    Returns:
        처짐 한계 (mm)
    """
    if pedestrian not in DECK_DEFLECTION_DIVISOR:
        msg = f"정의되지 않은 보행 조건: {pedestrian}"
        raise ValueError(msg)

    return span / DECK_DEFLECTION_DIVISOR[pedestrian]


# ── 휨 설계 ────────────────────────────────────────────────────────────────
def required_steel_area(
    m_ed: float,
    d: float,
    fck: float = DECK_FCK,
    fy: float = 400.0,
    width: float = 1000.0,
    phi_c: float = PHI_C_ULS,
    phi_s: float = PHI_S_ULS,
) -> float:
    r"""주어진 설계휨모멘트에 필요한 인장철근량을 반환한다.

    등가직사각형 블록으로 단철근 단면의 평형을 풀어 :math:`A_s` 를 구한다.
    블록 계수는 포물선-직선을 수치적분한 :func:`equivalent_block` 값을 쓴다.

    .. math::
        M_{Rd} = A_s f_{yd} \left( d - \beta_{eq} c \right),
        \qquad c = \frac{A_s f_{yd}}{\alpha_{eq} f_{cd} b}

    Args:
        m_ed: 설계휨모멘트 (N·mm)
        d: 유효깊이 (mm)
        fck: 콘크리트 기준압축강도 (MPa). 기본값 ``27.0``.
        fy: 철근의 기준항복강도 (MPa). 기본값 ``400.0``.
        width: 설계 폭 (mm). 기본값 ``1000.0`` (1 m 폭).
        phi_c: 콘크리트 재료계수. 기본값 ``0.65``.
        phi_s: 강재 재료계수. 기본값 ``0.90``.

    Raises:
        ValueError: 단철근으로 저항할 수 없는 휨모멘트인 경우

    Returns:
        필요한 인장철근량 (mm²), 주어진 폭에 대하여
    """
    f_cd = design_compressive_strength(fck=fck, phi_c=phi_c)
    f_yd = design_yield_strength(fy=fy, phi_s=phi_s)
    alpha_eq, beta_eq = equivalent_block(fck=fck, phi_c=phi_c)

    # beta k f_yd As^2 - f_yd d As + M = 0,  k = f_yd / (alpha f_cd b)
    k = f_yd / (alpha_eq * f_cd * width)
    a = beta_eq * k * f_yd
    b = -f_yd * d
    disc = b**2 - 4 * a * m_ed

    if disc < 0:
        msg = (
            "단철근 단면으로는 저항할 수 없는 휨모멘트다. 두께를 키우거나 "
            "압축철근을 배치해야 한다."
        )
        raise ValueError(msg)

    return (-b - math.sqrt(disc)) / (2 * a)


def bar_area(diameter: float) -> float:
    """철근 한 개의 공칭 단면적 (mm²).

    Args:
        diameter: 철근 지름 (mm)

    Returns:
        단면적 (mm²)
    """
    return math.pi * diameter**2 / 4.0


def provided_steel_area(
    diameter: float, spacing: float, width: float = 1000.0
) -> float:
    """주어진 지름·간격으로 배치되는 철근량 (mm²/폭).

    Args:
        diameter: 철근 지름 (mm)
        spacing: 철근 중심간격 (mm)
        width: 설계 폭 (mm). 기본값 ``1000.0``.

    Raises:
        ValueError: 간격이 0 이하인 경우

    Returns:
        철근량 (mm²)
    """
    if spacing <= 0:
        msg = f"spacing 은 0 보다 커야 한다: {spacing}"
        raise ValueError(msg)

    return bar_area(diameter=diameter) * width / spacing


def minimum_flexural_steel(
    d: float, fck: float = DECK_FCK, fy: float = 400.0, width: float = 1000.0
) -> float:
    r"""휨부재의 최소 인장철근량을 반환한다.

    **KDS 24 14 21 4.6.2.1(1) 식 (4.6-1), 식 (4.6-2)**

    .. math::
        A_{s,min} = \max \left(
        \frac{0.25 \sqrt{f_{ck}}}{f_y},\ \frac{1.4}{f_y} \right) b_w d

    Args:
        d: 유효깊이 (mm)
        fck: 콘크리트 기준압축강도 (MPa). 기본값 ``27.0``.
        fy: 철근의 기준항복강도 (MPa). 기본값 ``400.0``.
        width: 설계 폭 (mm). 기본값 ``1000.0``.

    Returns:
        최소 철근량 (mm²)
    """
    return max(0.25 * math.sqrt(fck) / fy, 1.4 / fy) * width * d


@dataclass(frozen=True)
class DeckDesign:
    """바닥판 한 단면의 설계 결과.

    Args:
        span: 바닥판의 지간 (m)
        thickness: 바닥판 두께 (mm)
        cover: 공칭피복두께 (mm)
        d: 유효깊이 (mm)
        m_dead: 고정하중 휨모멘트 (kN·m/m)
        m_live: 활하중 휨모멘트 (kN·m/m). 충격 포함.
        m_ed: 설계휨모멘트 (kN·m/m). 극한Ⅰ 조합.
        as_required: 필요 철근량 (mm²/m)
        as_minimum: 최소 철근량 (mm²/m)
        as_provided: 배치 철근량 (mm²/m)
        m_rd: 배치 철근의 설계휨강도 (kN·m/m)
        service_stress: 사용하중조합-Ⅰ 의 철근 인장응력 (MPa)
        crack_spacing_limit: 표 4.2-5 의 최대 철근간격 (mm)
        checks: 검토 항목별 통과 여부
        adequate: 모든 항목을 만족하는지 여부
    """

    span: float
    thickness: float
    cover: float
    d: float
    m_dead: float
    m_live: float
    m_ed: float
    as_required: float
    as_minimum: float
    as_provided: float
    m_rd: float
    service_stress: float
    crack_spacing_limit: float
    checks: dict[str, bool]
    adequate: bool


def design_deck(
    girder_spacing: float,
    thickness: float = 240.0,
    bar_diameter: float = 16.0,
    bar_spacing: float = 150.0,
    exposure: str = "EC1",
    fck: float = DECK_FCK,
    fy: float = 400.0,
    pavement: float = 80.0,
    continuous: bool = True,
    exposed_deck: bool = False,
    grade: int = 1,
    concrete_density: float = 24.5,
    pavement_density: float = 22.5,
    phi_c: float = PHI_C_ULS,
    phi_s: float = PHI_S_ULS,
) -> DeckDesign:
    r"""바닥판 내측부 1 m 폭을 설계하고 검토한다.

    **KDS 24 10 11 4.6.2 + KDS 24 14 21 4.4, 4.6.5**

    주철근이 차량진행방향에 직각인 거더교의 바닥판을 가정한다. 지간부
    정모멘트를 지배 단면으로 본다.

    하중조합은 극한Ⅰ (DC 1.25 / DW 1.50 / LL·IM 1.80), 사용성 검토는
    사용하중조합-Ⅰ (모두 1.00) 을 쓴다.

    Args:
        girder_spacing: 거더의 중심 간격 (m)
        thickness: 바닥판 두께 (mm). 기본값 ``240.0``.
        bar_diameter: 주철근 지름 (mm). 기본값 ``16.0``.
        bar_spacing: 주철근 중심간격 (mm). 기본값 ``150.0``.
        exposure: 노출등급. 기본값 ``"EC1"``.
        fck: 콘크리트 기준압축강도 (MPa). 기본값 ``27.0``.
        fy: 철근의 기준항복강도 (MPa). 기본값 ``400.0``.
        pavement: 포장 두께 (mm). 기본값 ``80.0``.
        continuous: 3지점 이상 연속판인지 여부. 기본값 ``True``.
        exposed_deck: 노출 콘크리트 바닥판인지 여부. 기본값 ``False``.
        grade: 교량 등급. 기본값 ``1``.
        concrete_density: 콘크리트 단위중량 (kN/m³). 기본값 ``24.5``.
        pavement_density: 포장 단위중량 (kN/m³). 기본값 ``22.5``.
        phi_c: 콘크리트 재료계수. 기본값 ``0.65``.
        phi_s: 강재 재료계수. 기본값 ``0.90``.

    Returns:
        :class:`DeckDesign`
    """
    from .live_load import impact_factor
    from .loads import COMBINATIONS_BY_NAME

    span = deck_span(girder_spacing=girder_spacing, thickness=thickness)
    _, cover = nominal_cover(
        exposure=exposure, bar_diameter=bar_diameter, exposed_deck=exposed_deck
    )
    d = thickness - cover - bar_diameter / 2.0

    # 하중 (kN/m2)
    w_dc = concrete_density * thickness / 1000.0
    w_dw = pavement_density * pavement / 1000.0

    kind = "연속판_지간" if continuous else "단순판"
    m_dc = dead_load_moment(w=w_dc, span=span, kind=kind)
    m_dw = dead_load_moment(w=w_dw, span=span, kind=kind)
    m_ll = live_load_moment(span=span, continuous=continuous, grade=grade)
    m_im = m_ll * (impact_factor() - 1.0)

    loads = {"DC": m_dc, "DW": m_dw, "LL": m_ll, "IM": m_im}
    m_ed = COMBINATIONS_BY_NAME["극한Ⅰ"].evaluate(loads=loads)
    m_service = COMBINATIONS_BY_NAME["사용Ⅰ"].evaluate(loads=loads)

    # 휨 설계
    as_required = required_steel_area(
        m_ed=m_ed * 1e6, d=d, fck=fck, fy=fy, phi_c=phi_c, phi_s=phi_s
    )
    as_minimum = minimum_flexural_steel(d=d, fck=fck, fy=fy)
    as_provided = provided_steel_area(diameter=bar_diameter, spacing=bar_spacing)

    # 배치 철근의 설계휨강도
    f_cd = design_compressive_strength(fck=fck, phi_c=phi_c)
    f_yd = design_yield_strength(fy=fy, phi_s=phi_s)
    alpha_eq, beta_eq = equivalent_block(fck=fck, phi_c=phi_c)
    c_n = as_provided * f_yd / (alpha_eq * f_cd * 1000.0)
    m_rd = as_provided * f_yd * (d - beta_eq * c_n) / 1e6

    # 사용성 — 균열단면의 철근 응력 (n = 7 가정, 삼각형 압축분포)
    n_ratio = 7.0
    rho = as_provided / (1000.0 * d)
    k = math.sqrt((n_ratio * rho) ** 2 + 2 * n_ratio * rho) - n_ratio * rho
    j = 1.0 - k / 3.0
    service_stress = m_service * 1e6 / (as_provided * j * d)

    try:
        spacing_limit = max_bar_spacing(f_s=service_stress)
    except ValueError:
        spacing_limit = 0.0

    try:
        diameter_limit = max_bar_diameter(f_s=service_stress)
    except ValueError:
        diameter_limit = 0.0

    checks = {
        "최소 두께": thickness >= MIN_THICKNESS_RC,
        "설계휨강도": m_rd >= m_ed,
        "최소 철근량": as_provided >= min(as_minimum, 1.33 * as_required),
        "철근 간격 하한": bar_spacing >= BAR_SPACING_MIN,
        "철근 간격 상한": bar_spacing <= min(BAR_SPACING_MAX, thickness),
        "균열 제어 (간격)": bar_spacing <= spacing_limit,
        "균열 제어 (지름)": bar_diameter <= diameter_limit,
    }

    return DeckDesign(
        span=span,
        thickness=thickness,
        cover=cover,
        d=d,
        m_dead=m_dc + m_dw,
        m_live=m_ll + m_im,
        m_ed=m_ed,
        as_required=as_required,
        as_minimum=as_minimum,
        as_provided=as_provided,
        m_rd=m_rd,
        service_stress=service_stress,
        crack_spacing_limit=spacing_limit,
        checks=checks,
        adequate=all(checks.values()),
    )
