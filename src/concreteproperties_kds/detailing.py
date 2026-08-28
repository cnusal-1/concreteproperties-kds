"""철근상세·정착·이음 (KDS 14 20 50, KDS 14 20 52).

최소 피복두께, 철근 간격 제한, 인장·압축 이형철근의 정착길이, 표준갈고리
정착길이, 겹침이음 길이를 다룬다.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# 이형철근의 공칭 지름과 단면적 (KS D 3504)
BAR_PROPERTIES: dict[str, tuple[float, float]] = {
    # 호칭 : (공칭지름 mm, 공칭단면적 mm^2)
    "D10": (9.53, 71.33),
    "D13": (12.7, 126.7),
    "D16": (15.9, 198.6),
    "D19": (19.1, 286.5),
    "D22": (22.2, 387.1),
    "D25": (25.4, 506.7),
    "D29": (28.6, 642.4),
    "D32": (31.8, 794.2),
    "D35": (34.9, 956.6),
    "D38": (38.1, 1140.0),
    "D41": (41.3, 1340.0),
    "D51": (50.8, 2027.0),
}

# 프리스트레스하지 않는 부재의 현장치기콘크리트 최소 피복두께
# (KDS 14 20 50 4.3.1) [mm]
MINIMUM_COVER: dict[str, dict[str, float]] = {
    "수중": {"전체": 100.0},
    "흙에영구히묻힘": {"전체": 75.0},
    "흙에접하거나옥외노출": {"D19이상": 50.0, "D16이하": 40.0},
    "옥내_슬래브벽체장선": {"D35초과": 40.0, "D35이하": 20.0},
    "옥내_보기둥": {"전체": 40.0},
    "옥내_셸절판": {"전체": 20.0},
}

# fck >= 40 MPa 일 때 10 mm 를 저감할 수 있는 조건 (KDS 14 20 50 4.3.1(1)④나)
COVER_REDUCTION_CONDITIONS = frozenset({"옥내_보기둥"})

# 인장 이형철근의 기본정착길이 계수 (KDS 14 20 52 식 4.1-1)
#   l_db = LDB_FACTOR * d_b * f_y / (lambda * sqrt(f_ck))
LDB_FACTOR = 0.6

# 기본정착길이에 곱하는 보정계수 (KDS 14 20 52 표 4.1-1)
# (배근 조건 만족 여부, 철근 크기) : alpha*beta 에 곱하는 계수
DEVELOPMENT_TABLE_FACTOR: dict[tuple[bool, str], float] = {
    (True, "D19이하"): 0.8,
    (True, "D22이상"): 1.0,
    (False, "D19이하"): 1.2,
    (False, "D22이상"): 1.5,
}

# 최소 정착길이 (mm)
LD_MIN = 300.0
LDC_MIN = 200.0
LDH_MIN = 150.0
LAP_MIN = 300.0


def bar_diameter(bar: str) -> float:
    """철근 호칭으로부터 공칭 지름을 반환한다.

    Args:
        bar: 철근 호칭 (예: ``"D22"``)

    Raises:
        ValueError: 정의되지 않은 호칭인 경우

    Returns:
        공칭 지름 (mm)
    """
    if bar not in BAR_PROPERTIES:
        msg = f"bar 는 {list(BAR_PROPERTIES)} 중 하나여야 합니다."
        raise ValueError(msg)

    return BAR_PROPERTIES[bar][0]


def bar_area(bar: str) -> float:
    """철근 호칭으로부터 공칭 단면적을 반환한다.

    Args:
        bar: 철근 호칭 (예: ``"D22"``)

    Raises:
        ValueError: 정의되지 않은 호칭인 경우

    Returns:
        공칭 단면적 (mm\\ :sup:`2`)
    """
    if bar not in BAR_PROPERTIES:
        msg = f"bar 는 {list(BAR_PROPERTIES)} 중 하나여야 합니다."
        raise ValueError(msg)

    return BAR_PROPERTIES[bar][1]


def minimum_cover(
    condition: str,
    bar: str | None = None,
    fck: float | None = None,
) -> float:
    r"""현장치기 콘크리트의 최소 피복두께를 반환한다.

    **KDS 14 20 50 4.3.1(1)**

    :math:`f_{ck} \\ge 40` MPa 인 경우 **옥내 보·기둥**\ 에 한하여 10 mm 를
    저감할 수 있다.

    Args:
        condition: :data:`MINIMUM_COVER` 의 키
        bar: 철근 호칭. 조건에 따라 필요. 기본값 ``None``.
        fck: 콘크리트 설계기준압축강도 (MPa). 40 MPa 이상이고 조건이
            ``"옥내_보기둥"`` 이면 10 mm 저감한다. 기본값 ``None``.

    Raises:
        ValueError: ``condition`` 이 정의되지 않았거나, 철근 구분이 필요한데
            ``bar`` 를 주지 않은 경우

    Returns:
        최소 피복두께 (mm)
    """
    if condition not in MINIMUM_COVER:
        msg = f"condition 은 {list(MINIMUM_COVER)} 중 하나여야 합니다."
        raise ValueError(msg)

    table = MINIMUM_COVER[condition]

    if "전체" in table:
        cover = table["전체"]
    else:
        if bar is None:
            msg = f"condition='{condition}' 에는 bar 를 주어야 합니다."
            raise ValueError(msg)

        d_b = bar_diameter(bar=bar)

        if "D19이상" in table:
            cover = table["D19이상"] if d_b >= 19.0 else table["D16이하"]
        else:
            cover = table["D35초과"] if d_b > 34.9 else table["D35이하"]

    # fck >= 40 MPa 저감은 옥내 보·기둥에만 적용된다 (KDS 14 20 50 4.3.1(1)④나)
    if (
        fck is not None
        and fck >= 40.0
        and condition in COVER_REDUCTION_CONDITIONS
    ):
        cover = max(cover - 10.0, 0.0)

    return float(cover)


def minimum_bar_spacing(
    bar: str,
    aggregate_size: float | None = None,
    member: str = "보",
) -> float:
    """철근의 최소 순간격을 반환한다.

    **KDS 14 20 50 4.2**

    보 : :math:`\\max(d_b,\\ 25\\ \\text{mm},\\ 4/3 \\times \\text{굵은골재 최대치수})`

    기둥 : :math:`\\max(1.5 d_b,\\ 40\\ \\text{mm},\\
    4/3 \\times \\text{굵은골재 최대치수})`

    Args:
        bar: 철근 호칭
        aggregate_size: 굵은골재의 최대치수 (mm). 기본값 ``None``.
        member: ``"보"`` 또는 ``"기둥"``. 기본값 ``"보"``.

    Raises:
        ValueError: ``member`` 가 ``"보"`` 또는 ``"기둥"`` 이 아닌 경우

    Returns:
        최소 순간격 (mm)
    """
    if member not in ("보", "기둥"):
        msg = 'member 는 "보" 또는 "기둥" 이어야 합니다.'
        raise ValueError(msg)

    d_b = bar_diameter(bar=bar)

    candidates = [d_b, 25.0] if member == "보" else [1.5 * d_b, 40.0]

    if aggregate_size is not None:
        candidates.append(4.0 / 3.0 * aggregate_size)

    return float(max(candidates))


def development_length_tension(
    bar: str,
    fy: float,
    fck: float,
    lambda_c: float = 1.0,
    top_bar: bool = False,
    epoxy_coated: bool = False,
    favourable_spacing: bool = True,
    excess_reinforcement: float = 1.0,
) -> float:
    r"""인장 이형철근의 정착길이를 반환한다.

    **KDS 14 20 52 4.1.2(2), 식 (4.1-1), 표 4.1-1**

    기본정착길이 (식 4.1-1)

    .. math::
        l_{db} = \frac{0.6 d_b f_y}{\lambda \sqrt{f_{ck}}}

    에 표 4.1-1 의 보정계수를 곱한다.

    .. list-table:: 표 4.1-1 보정계수
       :header-rows: 1
       :widths: 46 27 27

       * - 조건
         - D19 이하·이형철선
         - D22 이상
       * - 순간격 :math:`\ge d_b`, 피복 :math:`\ge d_b`, 최소 스터럽·띠철근
           배치; 또는 순간격 :math:`\ge 2d_b`, 피복 :math:`\ge d_b`
         - :math:`0.8\alpha\beta`
         - :math:`\alpha\beta`
       * - 기타
         - :math:`1.2\alpha\beta`
         - :math:`1.5\alpha\beta`

    :math:`\alpha` 는 철근배치 위치계수(상부철근 1.3, 기타 1.0),
    :math:`\beta` 는 도막계수(피복 :math:`< 3d_b` 또는 순간격 :math:`< 6d_b`
    인 에폭시 도막 1.5, 기타 에폭시 도막 1.2, 도막하지 않은 철근 1.0)이며,
    에폭시 도막철근이 상부철근인 경우 :math:`\alpha\beta \le 1.7` 이다.
    정착길이는 항상 300 mm 이상이어야 한다.

    Args:
        bar: 철근 호칭
        fy: 철근의 설계기준항복강도 (MPa)
        fck: 콘크리트 설계기준압축강도 (MPa)
        lambda_c: 경량콘크리트계수 (KDS 14 20 10 4.3.4). 기본값 ``1.0``.
        top_bar: 상부철근이면 ``True`` (:math:`\alpha = 1.3`). 기본값 ``False``.
        epoxy_coated: 에폭시 도막철근이면 ``True``. 기본값 ``False``.
        favourable_spacing: 표 4.1-1 의 첫 번째 조건을 만족하면 ``True``.
            기본값 ``True``.
        excess_reinforcement: 소요 철근량 / 배치 철근량. 1.0 미만이면 정착길이를
            저감할 수 있다 (KDS 14 20 52 4.1.2(4)). 기본값 ``1.0``.

    Returns:
        인장 이형철근의 정착길이 (mm)
    """
    d_b = bar_diameter(bar=bar)
    size_key = "D19이하" if d_b < 19.0 else "D22이상"
    table_factor = DEVELOPMENT_TABLE_FACTOR[(favourable_spacing, size_key)]

    alpha = 1.3 if top_bar else 1.0
    # 도막계수 : 피복이 3db 미만이거나 순간격이 6db 미만이면 1.5, 그 밖에는 1.2
    beta = (1.2 if favourable_spacing else 1.5) if epoxy_coated else 1.0

    alpha_beta = alpha * beta
    if top_bar and epoxy_coated:
        alpha_beta = min(alpha_beta, 1.7)

    l_db = LDB_FACTOR * d_b * fy / (lambda_c * np.sqrt(fck))
    l_d = l_db * table_factor * alpha_beta * excess_reinforcement

    return float(max(l_d, LD_MIN))


def development_length_tension_detailed(
    bar: str,
    fy: float,
    fck: float,
    c: float,
    k_tr: float = 0.0,
    lambda_c: float = 1.0,
    top_bar: bool = False,
    epoxy_coated: bool = False,
    excess_reinforcement: float = 1.0,
) -> float:
    r"""인장 이형철근의 정착길이를 반환한다 (정밀식).

    **KDS 14 20 52 4.1.2(3), 식 (4.1-2)**

    .. math::
        l_d = \frac{0.90 d_b f_y}{\lambda\sqrt{f_{ck}}}
        \cdot \frac{\alpha\beta\gamma}{\left(\dfrac{c + K_{tr}}{d_b}\right)}
        \ \ge 300\ \text{mm}

    여기서 :math:`(c + K_{tr})/d_b \le 2.5` 이고, :math:`\gamma` 는 철근
    크기계수(D19 이하 0.8, D22 이상 1.0)이다.

    Args:
        bar: 철근 호칭
        fy: 철근의 설계기준항복강도 (MPa)
        fck: 콘크리트 설계기준압축강도 (MPa)
        c: 피복두께와 철근 순간격의 1/2 중 작은 값 (mm)
        k_tr: 횡방향 철근지수 (mm). 안전측으로 0 을 쓸 수 있다. 기본값 ``0``.
        lambda_c: 경량콘크리트계수. 기본값 ``1.0``.
        top_bar: 상부철근 여부. 기본값 ``False``.
        epoxy_coated: 에폭시 도막철근 여부. 기본값 ``False``.
        excess_reinforcement: 소요 철근량 / 배치 철근량. 기본값 ``1.0``.

    Returns:
        인장 이형철근의 정착길이 (mm)
    """
    d_b = bar_diameter(bar=bar)

    alpha = 1.3 if top_bar else 1.0
    beta = 1.5 if epoxy_coated else 1.0
    alpha_beta = min(alpha * beta, 1.7)
    gamma = 0.8 if d_b < 19.0 else 1.0

    confinement = min((c + k_tr) / d_b, 2.5)

    l_d = (
        0.90
        * d_b
        * fy
        / (lambda_c * np.sqrt(fck))
        * alpha_beta
        * gamma
        / confinement
    )
    l_d *= excess_reinforcement

    return float(max(l_d, LD_MIN))


def development_length_compression(
    bar: str,
    fy: float,
    fck: float,
    lambda_c: float = 1.0,
    excess_reinforcement: float = 1.0,
    confined: bool = False,
) -> float:
    r"""압축 이형철근의 정착길이를 반환한다.

    **KDS 14 20 52 4.1.3, 식 (4.1-3)**

    .. math::
        l_{dc} = \max\left(\frac{0.25 d_b f_y}{\lambda\sqrt{f_{ck}}},\
        0.043 d_b f_y\right) \ \ge 200\ \text{mm}

    나선철근 또는 D13 이상의 띠철근이 100 mm 이하 간격으로 배치된 경우
    0.75 를 곱할 수 있다.

    Args:
        bar: 철근 호칭
        fy: 철근의 설계기준항복강도 (MPa)
        fck: 콘크리트 설계기준압축강도 (MPa)
        lambda_c: 경량콘크리트계수. 기본값 ``1.0``.
        excess_reinforcement: 소요 철근량 / 배치 철근량. 기본값 ``1.0``.
        confined: 나선철근·조밀한 띠철근으로 구속되면 ``True``. 기본값 ``False``.

    Returns:
        압축 이형철근의 정착길이 (mm)
    """
    d_b = bar_diameter(bar=bar)

    l_dc = max(0.25 * d_b * fy / (lambda_c * np.sqrt(fck)), 0.043 * d_b * fy)
    l_dc *= excess_reinforcement

    if confined:
        l_dc *= 0.75

    return float(max(l_dc, LDC_MIN))


def development_length_hook(
    bar: str,
    fy: float,
    fck: float,
    lambda_c: float = 1.0,
    epoxy_coated: bool = False,
    side_cover: bool = False,
    confined: bool = False,
    excess_reinforcement: float = 1.0,
) -> float:
    r"""표준갈고리를 갖는 인장 이형철근의 정착길이를 반환한다.

    **KDS 14 20 52 4.1.5**

    .. math::
        l_{dh} = \frac{0.24 \beta d_b f_y}{\lambda\sqrt{f_{ck}}}
        \ \ge \max(8 d_b,\ 150\ \text{mm})

    보정계수는 다음과 같다.

    - 측면 피복 :math:`\ge 70` mm 이고 갈고리 끝 피복 :math:`\ge 50` mm : 0.7
    - 갈고리를 3\ :math:`d_b` 이하 간격의 띠철근·스터럽으로 구속 : 0.8

    Args:
        bar: 철근 호칭
        fy: 철근의 설계기준항복강도 (MPa)
        fck: 콘크리트 설계기준압축강도 (MPa)
        lambda_c: 경량콘크리트계수. 기본값 ``1.0``.
        epoxy_coated: 에폭시 도막철근이면 ``True`` (:math:`\beta = 1.2`).
            기본값 ``False``.
        side_cover: 측면 피복 조건을 만족하면 ``True`` (0.7 배).
            기본값 ``False``.
        confined: 갈고리가 구속되면 ``True`` (0.8 배). 기본값 ``False``.
        excess_reinforcement: 소요 철근량 / 배치 철근량. 기본값 ``1.0``.

    Returns:
        표준갈고리 정착길이 (mm)
    """
    d_b = bar_diameter(bar=bar)
    beta = 1.2 if epoxy_coated else 1.0

    l_dh = 0.24 * beta * d_b * fy / (lambda_c * np.sqrt(fck))

    if side_cover:
        l_dh *= 0.7

    if confined:
        l_dh *= 0.8

    l_dh *= excess_reinforcement

    return float(max(l_dh, 8.0 * d_b, LDH_MIN))


def lap_splice_tension(
    l_d: float,
    splice_class: str = "B",
) -> float:
    r"""인장 겹침이음 길이를 반환한다.

    **KDS 14 20 52 4.5**

    - A급 이음 : :math:`1.0 l_d` — 배치 철근량이 소요 철근량의 2배 이상이고,
      겹침이음된 철근량이 전체의 1/2 이하
    - B급 이음 : :math:`1.3 l_d` — 그 밖의 경우

    어느 경우든 300 mm 이상이어야 한다.

    Args:
        l_d: 인장 이형철근의 정착길이 (mm)
        splice_class: ``"A"`` 또는 ``"B"``. 기본값 ``"B"``.

    Raises:
        ValueError: ``splice_class`` 가 ``"A"`` 또는 ``"B"`` 가 아닌 경우

    Returns:
        인장 겹침이음 길이 (mm)
    """
    if splice_class not in ("A", "B"):
        msg = 'splice_class 는 "A" 또는 "B" 여야 합니다.'
        raise ValueError(msg)

    factor = 1.0 if splice_class == "A" else 1.3

    return float(max(factor * l_d, LAP_MIN))


def lap_splice_compression(
    bar: str,
    fy: float,
    fck: float,
    l_dc: float | None = None,
) -> float:
    r"""압축 겹침이음 길이를 반환한다.

    **KDS 14 20 52 4.5**

    .. math::
        l_s = \begin{cases}
        0.072 f_y d_b & f_y \le 400 \text{ MPa} \\
        (0.13 f_y - 24) d_b & f_y > 400 \text{ MPa}
        \end{cases}
        \ \ge \max(l_{dc},\ 300\ \text{mm})

    :math:`f_{ck} < 21` MPa 인 경우 겹침이음 길이를 1/3 증가시켜야 한다.

    Args:
        bar: 철근 호칭
        fy: 철근의 설계기준항복강도 (MPa)
        fck: 콘크리트 설계기준압축강도 (MPa)
        l_dc: 압축 이형철근의 정착길이 (mm). 주지 않으면 계산한다.
            기본값 ``None``.

    Returns:
        압축 겹침이음 길이 (mm)
    """
    d_b = bar_diameter(bar=bar)

    l_s = 0.072 * fy * d_b if fy <= 400 else (0.13 * fy - 24.0) * d_b

    if fck < 21.0:
        l_s *= 4.0 / 3.0

    if l_dc is None:
        l_dc = development_length_compression(bar=bar, fy=fy, fck=fck)

    return float(max(l_s, l_dc, LAP_MIN))


@dataclass
class DetailingSummary:
    """정착·이음 길이 요약.

    Args:
        bar: 철근 호칭
        d_b: 공칭 지름 (mm)
        l_d: 인장 정착길이 (mm)
        l_dc: 압축 정착길이 (mm)
        l_dh: 표준갈고리 정착길이 (mm)
        l_s_tension_a: A급 인장 겹침이음 길이 (mm)
        l_s_tension_b: B급 인장 겹침이음 길이 (mm)
        l_s_compression: 압축 겹침이음 길이 (mm)
    """

    bar: str
    d_b: float
    l_d: float
    l_dc: float
    l_dh: float
    l_s_tension_a: float
    l_s_tension_b: float
    l_s_compression: float

    def print_results(self) -> None:
        """요약을 출력한다."""
        width = 58
        print("=" * width)
        print(f"정착·이음 길이 - {self.bar} (KDS 14 20 52)")
        print("=" * width)
        print(f"공칭 지름              db   = {self.d_b:9.2f} mm")
        print(f"인장 정착길이          ld   = {self.l_d:9.1f} mm")
        print(f"압축 정착길이          ldc  = {self.l_dc:9.1f} mm")
        print(f"표준갈고리 정착길이    ldh  = {self.l_dh:9.1f} mm")
        print(f"인장 겹침이음 (A급)         = {self.l_s_tension_a:9.1f} mm")
        print(f"인장 겹침이음 (B급)         = {self.l_s_tension_b:9.1f} mm")
        print(f"압축 겹침이음               = {self.l_s_compression:9.1f} mm")


def summarise_detailing(
    bar: str,
    fy: float,
    fck: float,
    lambda_c: float = 1.0,
    top_bar: bool = False,
    favourable_spacing: bool = True,
) -> DetailingSummary:
    """하나의 철근에 대한 정착·이음 길이를 모두 계산한다.

    Args:
        bar: 철근 호칭
        fy: 철근의 설계기준항복강도 (MPa)
        fck: 콘크리트 설계기준압축강도 (MPa)
        lambda_c: 경량콘크리트계수. 기본값 ``1.0``.
        top_bar: 상부철근 여부. 기본값 ``False``.
        favourable_spacing: 배근 조건 만족 여부. 기본값 ``True``.

    Returns:
        정착·이음 길이 요약 객체
    """
    l_d = development_length_tension(
        bar=bar,
        fy=fy,
        fck=fck,
        lambda_c=lambda_c,
        top_bar=top_bar,
        favourable_spacing=favourable_spacing,
    )
    l_dc = development_length_compression(
        bar=bar, fy=fy, fck=fck, lambda_c=lambda_c
    )
    l_dh = development_length_hook(bar=bar, fy=fy, fck=fck, lambda_c=lambda_c)

    return DetailingSummary(
        bar=bar,
        d_b=bar_diameter(bar=bar),
        l_d=l_d,
        l_dc=l_dc,
        l_dh=l_dh,
        l_s_tension_a=lap_splice_tension(l_d=l_d, splice_class="A"),
        l_s_tension_b=lap_splice_tension(l_d=l_d, splice_class="B"),
        l_s_compression=lap_splice_compression(
            bar=bar, fy=fy, fck=fck, l_dc=l_dc
        ),
    )
