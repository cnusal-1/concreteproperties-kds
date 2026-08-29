r"""KDS 24 12 21 교량 설계하중(한계상태설계법) — 차량활하중 KL-510.

KDS 14 에는 교량 활하중이 없다. 건축구조물의 활하중은 :math:`\text{kN/m}^2` 의
등분포로 주어지지만, 교량은 **어디에 실리느냐가 곧 설계값이라서** 트럭을 다리 위로
굴려 가며 최대 단면력을 찾아야 한다. 이 모듈이 그 일을 한다.

차량활하중 KL-510 은 두 가지로 이루어진다 (4.3.1.3).

* **표준트럭하중** — 48 / 192 / 135 / 135 kN 의 4 축, 전체 길이 12.0 m.
  합계 510 kN 이라 이름이 KL-510 이다. 충격하중을 적용한다.
* **표준차로하중** — 종방향으로 균등한 등분포하중. 충격하중을 적용하지 않는다.

주거더를 설계할 때는 둘 중 큰 값을 쓰되, 두 번째 경우는 **트럭의 75 % 와 차로하중을
더한다** (4.3.1.5). 트럭 한 대만으로는 긴 지간에서 실제 교통을 대표하지 못하고,
차로하중만으로는 짧은 지간의 국부적인 집중이 빠지기 때문이다.

근거: KDS 24 12 21 4.3.1, 4.3.2, 4.4
"""

from __future__ import annotations

from dataclasses import dataclass

# ── 표준트럭하중 KL-510 (4.3.1.3.1, 그림 4.3-1) ────────────────────────────
TRUCK_AXLE_LOADS = (48.0, 192.0, 135.0, 135.0)
"""축하중 (kN). 앞에서부터 48, 192, 135, 135 — 합계 510 kN."""

TRUCK_AXLE_SPACINGS = (3.6, 7.2, 1.2)
"""축간거리 (m). 전체 길이는 12.0 m 이다."""

TRUCK_AXLE_POSITIONS = (0.0, 3.6, 10.8, 12.0)
"""앞축을 원점으로 한 각 축의 위치 (m)."""

TRUCK_TOTAL_LOAD = 510.0
"""표준트럭 전체 중량 (kN)."""

TRUCK_WHEEL_GAUGE = 1.8
"""윤간거리 (m)."""

TRUCK_OCCUPIED_WIDTH = 3.0
"""트럭·차로하중이 재하차로 안에서 차지하는 횡방향 폭 (m)."""

# ── 표준차로하중 (4.3.1.3.2, 표 4.3-2) ─────────────────────────────────────
LANE_LOAD_BASE = 12.7
"""지간 60 m 이하의 표준차로하중 (kN/m)."""

LANE_LOAD_REFERENCE_SPAN = 60.0
LANE_LOAD_EXPONENT = 0.10

# ── 다차로 재하계수 (표 4.3-1) ─────────────────────────────────────────────
MULTIPLE_PRESENCE_FACTORS: dict[int, float] = {1: 1.00, 2: 0.90, 3: 0.80, 4: 0.70}
MULTIPLE_PRESENCE_MANY = 0.65
"""재하차로가 5 이상일 때의 다차로 재하계수."""

# ── 충격하중 (표 4.4-1) ────────────────────────────────────────────────────
IMPACT_PERCENT = 25.0
"""피로한계상태를 제외한 모든 한계상태의 충격하중계수 IM (%)."""

IMPACT_PERCENT_FATIGUE = 15.0
"""피로한계상태의 충격하중계수 IM (%)."""

# ── 피로하중 (4.3.2) ───────────────────────────────────────────────────────
FATIGUE_TRUCK_RATIO = 0.80
"""피로검토용 활하중은 표준트럭하중의 80 % 이다 (4.3.2.1)."""

TRUCK_LANE_FRACTION: dict[int, float] = {1: 1.00, 2: 0.85}
TRUCK_LANE_FRACTION_MANY = 0.80
"""표 4.3-3 — 한 차로에서의 트럭교통량 비율 p. 3차로 이상은 0.80."""

DEFAULT_PLAN_LANE_WIDTH = 3.6
"""계획차로의 폭 기본값 (m). 원칙적으로 발주자가 정한다."""

MAX_LANE_WIDTH = 3.6
"""재하차로 폭의 상한 (m), 식 (4.3-2)."""


def number_of_lanes(
    roadway_width: float, plan_lane_width: float = DEFAULT_PLAN_LANE_WIDTH
) -> int:
    r"""재하차로의 수 :math:`N` 을 반환한다.

    **KDS 24 12 21 4.3.1.1 식 (4.3-1)**

    .. math::
        N = \left\lfloor \frac{W_C}{W_P} \right\rfloor

    다만 :math:`N = 1` 이고 :math:`W_C \ge 6.0\ \text{m}` 이면 2 로 한다. 폭이 6 m
    넘게 열려 있으면 차선이 그려져 있든 아니든 차 두 대가 나란히 설 수 있기
    때문이다.

    Args:
        roadway_width: 연석·방호울타리 사이의 교폭 :math:`W_C` (m)
        plan_lane_width: 계획차로의 폭 :math:`W_P` (m). 기본값 ``3.6``.

    Raises:
        ValueError: 폭이 0 이하인 경우

    Returns:
        재하차로의 수
    """
    if roadway_width <= 0 or plan_lane_width <= 0:
        msg = "roadway_width 와 plan_lane_width 는 0 보다 커야 한다"
        raise ValueError(msg)

    n = int(roadway_width // plan_lane_width)

    if n <= 1 and roadway_width >= 6.0:
        return 2

    return max(n, 1)


def lane_width(roadway_width: float, n_lanes: int) -> float:
    r"""재하차로의 폭 :math:`W` 를 반환한다.

    **KDS 24 12 21 4.3.1.1 식 (4.3-2)**

    .. math::
        W = \frac{W_C}{N} \le 3.6\ \text{m}

    Args:
        roadway_width: 교폭 :math:`W_C` (m)
        n_lanes: 재하차로의 수 :math:`N`

    Returns:
        재하차로의 폭 (m)
    """
    return min(roadway_width / n_lanes, MAX_LANE_WIDTH)


def multiple_presence(n_lanes: int) -> float:
    """다차로 재하계수 :math:`m` 을 반환한다.

    **KDS 24 12 21 4.3.1.2, 표 4.3-1**

    차로가 늘수록 모든 차로에 최대 하중이 동시에 실릴 확률이 낮아지므로 계수를
    줄인다. 피로설계에는 적용하지 않는다.

    Args:
        n_lanes: 재하차로의 수

    Raises:
        ValueError: 1 미만인 경우

    Returns:
        다차로 재하계수
    """
    if n_lanes < 1:
        msg = f"재하차로의 수는 1 이상이어야 한다: {n_lanes}"
        raise ValueError(msg)

    return MULTIPLE_PRESENCE_FACTORS.get(n_lanes, MULTIPLE_PRESENCE_MANY)


def lane_load(span: float) -> float:
    r"""표준차로하중 :math:`\omega` 를 반환한다.

    **KDS 24 12 21 4.3.1.3.2, 표 4.3-2**

    .. math::
        \omega = \begin{cases}
        12.7 & L \le 60\ \text{m} \\
        12.7 \left( \dfrac{60}{L} \right)^{0.10} & L > 60\ \text{m}
        \end{cases}

    Args:
        span: 표준차로하중이 재하되는 부분의 지간 :math:`L` (m)

    Raises:
        ValueError: 지간이 0 이하인 경우

    Returns:
        표준차로하중 (kN/m)
    """
    if span <= 0:
        msg = f"span 은 0 보다 커야 한다: {span}"
        raise ValueError(msg)

    if span <= LANE_LOAD_REFERENCE_SPAN:
        return LANE_LOAD_BASE

    ratio = LANE_LOAD_REFERENCE_SPAN / span

    return LANE_LOAD_BASE * ratio**LANE_LOAD_EXPONENT


def impact_factor(limit_state: str = "극한") -> float:
    """충격하중계수 :math:`1 + IM/100` 을 반환한다.

    **KDS 24 12 21 4.4.1, 표 4.4-1**

    표준트럭하중에만 곱한다. 보도하중과 표준차로하중에는 적용하지 않는다.

    Args:
        limit_state: ``"피로"`` 이면 IM = 15 %, 그 밖에는 25 %. 기본값 ``"극한"``.

    Returns:
        정적 하중에 곱하는 배율
    """
    percent = IMPACT_PERCENT_FATIGUE if limit_state == "피로" else IMPACT_PERCENT

    return 1.0 + percent / 100.0


def impact_buried(cover_depth: float) -> float:
    r"""매설 구조물의 충격하중 백분율 :math:`IM` 을 반환한다.

    **KDS 24 12 21 4.4.2 식 (4.4-1)**

    .. math::
        IM = 40 \left( 1.0 - 4.1 \times 10^{-4} D_E \right) \ge 0\ \%

    Args:
        cover_depth: 구조물을 덮고 있는 최소깊이 :math:`D_E` (mm)

    Returns:
        충격하중 백분율 (%)
    """
    return max(40.0 * (1.0 - 4.1e-4 * cover_depth), 0.0)


def truck_lane_fraction(n_truck_lanes: int) -> float:
    """한 차로에서의 트럭교통량 비율 :math:`p` 를 반환한다.

    **KDS 24 12 21 4.3.2.2, 표 4.3-3**

    Args:
        n_truck_lanes: 트럭이 통행 가능한 차로 수

    Returns:
        비율 :math:`p`
    """
    return TRUCK_LANE_FRACTION.get(n_truck_lanes, TRUCK_LANE_FRACTION_MANY)


def adtt_single_lane(adtt: float, n_truck_lanes: int) -> float:
    r"""단일차로 일평균트럭교통량 :math:`ADTT_{SL}` 을 반환한다.

    **KDS 24 12 21 4.3.2.2 식 (4.3-3)**

    .. math::
        ADTT_{SL} = p \times ADTT

    Args:
        adtt: 한 방향 일일트럭교통량의 설계수명 평균 :math:`ADTT`
        n_truck_lanes: 트럭이 통행 가능한 차로 수

    Returns:
        단일차로 일평균트럭교통량
    """
    return truck_lane_fraction(n_truck_lanes=n_truck_lanes) * adtt


# ── 단순보의 활하중 단면력 ─────────────────────────────────────────────────
def _moment_from_axles(
    span: float, positions: list[float], loads: list[float], section: float
) -> float:
    """단순보 위 축하중들이 한 단면에 만드는 휨모멘트."""
    reaction = sum(
        load * (span - a) / span for a, load in zip(positions, loads, strict=True)
    )
    moment = reaction * section

    for a, load in zip(positions, loads, strict=True):
        if a < section:
            moment -= load * (section - a)

    return moment


def truck_moment(span: float, step: float = 0.05) -> float:
    r"""단순 지지 지간에서 표준트럭하중의 최대 휨모멘트를 반환한다.

    영향선 대신 트럭을 지간 위로 굴려 가며 각 축 아래의 모멘트를 모두 살핀다.
    단순보에서 최대 휨모멘트는 언제나 어느 한 축 바로 아래에서 생기므로, 이렇게
    훑으면 정확한 값을 얻는다. 지간 밖으로 나간 축은 세지 않는다.

    Args:
        span: 지간 :math:`L` (m)
        step: 트럭을 옮기는 간격 (m). 기본값 ``0.05``.

    Raises:
        ValueError: 지간이 0 이하인 경우

    Returns:
        최대 휨모멘트 (kN·m)
    """
    if span <= 0:
        msg = f"span 은 0 보다 커야 한다: {span}"
        raise ValueError(msg)

    best = 0.0
    # 트럭 앞축의 위치를 -12 m 부터 지간 끝까지 옮긴다
    n_steps = int((span + TRUCK_AXLE_POSITIONS[-1]) / step) + 1

    for i in range(n_steps + 1):
        front = -TRUCK_AXLE_POSITIONS[-1] + i * step
        positions, loads = [], []

        for offset, load in zip(TRUCK_AXLE_POSITIONS, TRUCK_AXLE_LOADS, strict=True):
            a = front + offset

            if 0.0 <= a <= span:
                positions.append(a)
                loads.append(load)

        if not positions:
            continue

        for section in positions:
            best = max(
                best,
                _moment_from_axles(
                    span=span, positions=positions, loads=loads, section=section
                ),
            )

    return best


def truck_shear(span: float, section: float = 0.0, step: float = 0.05) -> float:
    """단순 지지 지간에서 표준트럭하중의 최대 전단력을 반환한다.

    Args:
        span: 지간 :math:`L` (m)
        section: 전단력을 구할 위치 (m). 기본값 ``0.0`` (받침점).
        step: 트럭을 옮기는 간격 (m). 기본값 ``0.05``.

    Returns:
        최대 전단력 (kN)
    """
    if span <= 0:
        msg = f"span 은 0 보다 커야 한다: {span}"
        raise ValueError(msg)

    best = 0.0
    n_steps = int((span + TRUCK_AXLE_POSITIONS[-1]) / step) + 1

    for i in range(n_steps + 1):
        front = -TRUCK_AXLE_POSITIONS[-1] + i * step
        shear = 0.0

        for offset, load in zip(TRUCK_AXLE_POSITIONS, TRUCK_AXLE_LOADS, strict=True):
            a = front + offset

            if not (0.0 <= a <= span):
                continue

            # 좌측 받침 반력에서 단면 왼쪽의 하중을 뺀 값
            shear += load * (span - a) / span

            if a < section:
                shear -= load

        best = max(best, shear)

    return best


def lane_moment(span: float, section: float | None = None) -> float:
    """표준차로하중이 단순 지지 지간에 만드는 휨모멘트를 반환한다.

    Args:
        span: 지간 :math:`L` (m)
        section: 위치 (m). 기본값 ``None`` (지간 중앙).

    Returns:
        휨모멘트 (kN·m)
    """
    w = lane_load(span=span)
    x = span / 2.0 if section is None else section

    return w * x * (span - x) / 2.0


def lane_shear(span: float, section: float = 0.0) -> float:
    """표준차로하중이 단순 지지 지간에 만드는 최대 전단력을 반환한다.

    Args:
        span: 지간 :math:`L` (m)
        section: 위치 (m). 기본값 ``0.0`` (받침점).

    Returns:
        전단력 (kN)
    """
    w = lane_load(span=span)

    return w * (span - section) ** 2 / (2.0 * span)


@dataclass(frozen=True)
class LiveLoadEffect:
    """한 재하차로가 만드는 활하중 단면력.

    Args:
        moment: 설계 휨모멘트 (kN·m). 충격하중을 포함한다.
        shear: 설계 전단력 (kN). 충격하중을 포함한다.
        governed_by: 휨모멘트를 지배한 경우. ``"트럭"`` 또는
            ``"트럭 75 % + 차로"``. 전단은 두 경우의 큰 값을 따로 취한다.
        truck_moment: 충격 전 트럭 휨모멘트 (kN·m)
        lane_moment: 차로하중 휨모멘트 (kN·m)
        impact: 적용한 충격하중계수 :math:`1 + IM/100`
    """

    moment: float
    shear: float
    governed_by: str
    truck_moment: float
    lane_moment: float
    impact: float


def girder_live_load(
    span: float,
    section: float | None = None,
    limit_state: str = "극한",
    step: float = 0.05,
) -> LiveLoadEffect:
    """주거더 설계용 한 차로분 활하중 단면력을 반환한다.

    **KDS 24 12 21 4.3.1.5**

    다음 둘 중 큰 값을 쓴다.

    1. 표준트럭하중의 영향
    2. 표준트럭하중 영향의 75 % 와 표준차로하중 영향의 합

    충격하중은 트럭 쪽에만 곱한다 (4.4.1(3)).

    Args:
        span: 지간 (m)
        section: 단면력을 구할 위치 (m). 기본값 ``None`` (모멘트는 최대값,
            전단은 받침점).
        limit_state: 충격하중계수를 고르는 한계상태. 기본값 ``"극한"``.
        step: 트럭을 옮기는 간격 (m). 기본값 ``0.05``.

    Returns:
        :class:`LiveLoadEffect`
    """
    impact = impact_factor(limit_state=limit_state)
    x_shear = 0.0 if section is None else section

    m_truck = truck_moment(span=span, step=step)
    v_truck = truck_shear(span=span, section=x_shear, step=step)
    m_lane = lane_moment(span=span, section=section)
    v_lane = lane_shear(span=span, section=x_shear)

    m_only = impact * m_truck
    v_only = impact * v_truck
    m_both = 0.75 * impact * m_truck + m_lane
    v_both = 0.75 * impact * v_truck + v_lane

    if m_both >= m_only:
        return LiveLoadEffect(
            moment=m_both,
            shear=max(v_both, v_only),
            governed_by="트럭 75 % + 차로",
            truck_moment=m_truck,
            lane_moment=m_lane,
            impact=impact,
        )

    return LiveLoadEffect(
        moment=m_only,
        shear=max(v_only, v_both),
        governed_by="트럭",
        truck_moment=m_truck,
        lane_moment=m_lane,
        impact=impact,
    )


def fatigue_truck_moment(span: float, step: float = 0.05) -> float:
    """피로검토용 트럭하중의 최대 휨모멘트를 반환한다.

    **KDS 24 12 21 4.3.2.1**

    표준트럭하중의 80 % 를 쓰고, 충격은 피로한계상태의 15 % 를 적용한다. 다차로
    재하계수는 적용하지 않는다 (4.3.1.2).

    Args:
        span: 지간 (m)
        step: 트럭을 옮기는 간격 (m). 기본값 ``0.05``.

    Returns:
        휨모멘트 (kN·m)
    """
    return (
        FATIGUE_TRUCK_RATIO
        * impact_factor(limit_state="피로")
        * truck_moment(span=span, step=step)
    )
