r"""KDS 24 12 11 교량 설계하중조합(한계상태설계법).

KDS 14 의 하중조합(:mod:`concreteproperties_kds.loads`)과 형식이 다르다.

* KDS 14 — 건축·일반 구조물의 조합. :math:`U = 1.2D + 1.6L` 처럼 한 줄로 끝난다.
* KDS 24 — 교량의 조합. 한계상태를 **극한 I~V, 극단상황 I~II, 사용 I~V, 피로**
  로 나누고, 상시하중에는 하중의 종류마다 최대·최소 두 계수(표 4.1-2)를 두어
  **불리한 쪽을 골라 쓴다.** 또 연성·여용성·중요도를 반영한 하중수정계수
  :math:`\eta` 를 전체에 곱한다(KDS 24 10 11 1.3.2).

설계식은 다음과 같다.

.. math::
    \sum \eta_i \gamma_i Q_i \le \phi R_n \qquad \text{(KDS 24 10 11 식 (1.3-1))}

우변의 :math:`\phi R_n` 은 콘크리트 부재에서 재료계수가 이미 반영된 설계강도이므로
:mod:`concreteproperties_kds.kds24.design_code` 가 돌려주는 값을 그대로 쓴다.

근거: KDS 24 12 11 4.1 (표 4.1-1, 표 4.1-2), KDS 24 10 11 1.3.2~1.3.5, 1.4
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ── 하중 기호 (KDS 24 12 11 표 4.1-1) ──────────────────────────────────────
LOAD_SYMBOLS: dict[str, str] = {
    # 상시하중
    "DC": "구조부재와 비구조적 부착물의 자중",
    "DD": "말뚝 부마찰력",
    "DW": "포장과 시설물의 자중",
    "EH": "수평토압",
    "EV": "연직토압",
    "ES": "상재토하중",
    "EL": "시공 중 발생하는 구속응력",
    "PS": "프리스트레스힘",
    "CR": "크리프",
    "SH": "건조수축",
    # 변동하중
    "LL": "차량활하중 (KL-510)",
    "IM": "충격하중",
    "BR": "차량 제동하중",
    "PL": "보도하중",
    "LS": "활하중에 의한 상재하중",
    "CF": "원심하중",
    "WA": "유수압과 정수압",
    "WS": "풍하중 (구조물)",
    "WL": "풍하중 (활하중)",
    "FR": "마찰력",
    "TU": "온도의 균등 변화",
    "TG": "온도경사",
    "SD": "부등침하",
    # 극단상황
    "EQ": "지진하중",
    "IC": "빙하중",
    "CT": "차량 충돌하중",
    "CV": "선박 충돌하중",
}

PERMANENT_SYMBOLS = ("DC", "DD", "DW", "EH", "EV", "ES", "EL", "PS", "CR", "SH")
"""상시하중. 표 4.1-2 의 최대·최소 계수 중 불리한 쪽을 쓴다."""

LIVE_SYMBOLS = ("LL", "IM", "BR", "PL", "LS", "CF")
"""활하중 무리. 표 4.1-1 에서 한 칸(한 계수)으로 묶여 있다."""

# ── 표 4.1-2 상시하중의 하중계수 gamma_p (최대, 최소) ──────────────────────
PERMANENT_LOAD_FACTORS: dict[str, tuple[float, float]] = {
    "DC": (1.25, 0.90),
    "DD": (1.80, 0.45),
    "DW": (1.50, 0.65),
    "EH_주동": (1.50, 0.90),
    "EH_정지": (1.35, 0.90),
    "EV_전체안정성": (1.00, 1.00),
    "EV_옹벽및교대": (1.35, 1.00),
    "EV_강성암거": (1.30, 0.90),
    "EV_뼈대형강성구조물": (1.35, 0.90),
    "EV_연성암거": (1.95, 0.90),
    "EV_박스형연성강재암거": (1.50, 0.90),
    "ES": (1.50, 0.75),
    "EL": (1.00, 1.00),
    "PS": (1.00, 1.00),
    "CR": (1.00, 1.00),
    "SH": (1.00, 1.00),
}
"""표 4.1-2 — 상시하중 종류별 (최대, 최소) 하중계수.

``EH`` 와 ``EV`` 는 토압의 종류에 따라 값이 달라 접미사로 구분하였다. 기본 조회는
접미사 없는 기호로도 되며, 이때는 가장 흔한 경우(``EH_주동``, ``EV_옹벽및교대``)를
쓴다.
"""

_PERMANENT_ALIAS = {"EH": "EH_주동", "EV": "EV_옹벽및교대"}

DC_MAX_ULS_IV = 1.50
"""극한한계상태 조합 IV 에서만 쓰는 DC 의 최대 하중계수 (표 4.1-2)."""


def permanent_load_factor(kind: str, maximum: bool = True) -> float:
    """상시하중의 하중계수 :math:`\\gamma_p` 를 반환한다.

    **KDS 24 12 11 표 4.1-2**

    상시하중효과가 구조물의 안정성이나 내하성능을 **증가**시키는 쪽이면 최소
    계수를, 그렇지 않으면 최대 계수를 쓴다 (4.1(4)).

    Args:
        kind: 하중 종류. ``"DC"``, ``"DW"``, ``"EH_주동"`` 등.
        maximum: 최대 계수를 쓸지 여부. 기본값 ``True``.

    Raises:
        ValueError: 표에 없는 하중 종류인 경우

    Returns:
        하중계수
    """
    key = _PERMANENT_ALIAS.get(kind, kind)

    if key not in PERMANENT_LOAD_FACTORS:
        msg = f"표 4.1-2 에 없는 상시하중 종류: {kind}"
        raise ValueError(msg)

    factors = PERMANENT_LOAD_FACTORS[key]

    return factors[0] if maximum else factors[1]


# ── 하중수정계수 (KDS 24 10 11 1.3.2~1.3.5) ───────────────────────────────
DUCTILITY_FACTORS: dict[str, float] = {"비연성": 1.05, "통상": 1.00, "추가연성": 0.95}
REDUNDANCY_FACTORS: dict[str, float] = {"비여용": 1.05, "통상": 1.00, "특별": 0.95}
IMPORTANCE_FACTORS: dict[str, float] = {"중요": 1.05, "일반": 1.00, "낮음": 0.95}


def load_modifier(
    ductility: float = 1.0,
    redundancy: float = 1.0,
    importance: float = 1.0,
    maximum: bool = True,
) -> float:
    r"""하중수정계수 :math:`\eta` 를 반환한다.

    **KDS 24 10 11 1.3.2 식 (1.3-2), 식 (1.3-3)**

    .. math::
        \eta = \eta_D \eta_R \eta_I \ge 0.95
        \quad\text{(최대하중계수)}

    .. math::
        \eta = \frac{1}{\eta_D \eta_R \eta_I} \le 1.0
        \quad\text{(최소하중계수)}

    설계의 의도는 이렇다. 하중계수와 재료계수는 "얼마나 불확실한가"를 다루지만,
    같은 불확실성이라도 **부재가 망가졌을 때 다리 전체가 어떻게 되는가**는 다르다.
    연성이 없는 부재, 대체 하중경로가 없는 부재, 중요한 다리는 여유를 5 % 더 준다.
    반대로 여유가 충분하면 5 % 깎아 준다. 기타 한계상태에서는 모두 1.0 이다.

    Args:
        ductility: 연성계수 :math:`\eta_D` (1.3.3). 기본값 ``1.0``.
        redundancy: 여용성계수 :math:`\eta_R` (1.3.4). 기본값 ``1.0``.
        importance: 중요도계수 :math:`\eta_I` (1.3.5). 기본값 ``1.0``.
        maximum: 최대하중계수를 적용하는 하중인지 여부. 기본값 ``True``.

    Returns:
        하중수정계수 :math:`\eta`
    """
    product = ductility * redundancy * importance

    if maximum:
        return max(product, 0.95)

    return min(1.0 / product, 1.0)


# ── 교량의 등급 (KDS 24 10 11 1.4) ────────────────────────────────────────
BRIDGE_GRADE_FACTORS: dict[int, float] = {1: 1.0, 2: 0.75, 3: 0.5625}
"""1등교 = KL-510 전체, 2등교 = 1등교의 75 %, 3등교 = 2등교의 75 %."""


def bridge_grade_factor(grade: int = 1) -> float:
    """교량 등급에 따른 활하중효과 배율을 반환한다.

    **KDS 24 10 11 1.4**

    Args:
        grade: 교량 등급 (1, 2, 3). 기본값 ``1``.

    Raises:
        ValueError: 1~3 이 아닌 등급

    Returns:
        활하중효과에 곱하는 배율
    """
    if grade not in BRIDGE_GRADE_FACTORS:
        msg = f"grade 는 1, 2, 3 중 하나여야 한다: {grade}"
        raise ValueError(msg)

    return BRIDGE_GRADE_FACTORS[grade]


# ── 하중조합 (표 4.1-1) ───────────────────────────────────────────────────
@dataclass(frozen=True)
class LoadCombination:
    """KDS 24 12 11 표 4.1-1 의 하중조합 하나.

    Args:
        name: 조합 이름 (예 ``"극한Ⅰ"``)
        limit_state: 재료계수를 고르는 한계상태 이름. ``"극한"``, ``"극단상황"``,
            ``"사용"``, ``"피로"`` 중 하나.
        factors: 변동하중 기호별 계수
        permanent: 상시하중 계수의 처리 방법. ``None`` 이면 표 4.1-2 의
            :math:`\\gamma_p` 를, 숫자면 그 값을 그대로 쓴다.
        tu_factors: TU·CR·SH 의 (작은 값, 큰 값). 변형량 계산에는 큰 값,
            나머지에는 작은 값을 쓴다 (4.1(5)).
        uses_gamma_tg: 온도경사 계수 :math:`\\gamma_{TG}` 를 쓰는 조합인지
        uses_gamma_sd: 부등침하 계수 :math:`\\gamma_{SD}` 를 쓰는 조합인지
        live_load_by_owner: 활하중계수를 발주자가 정하는 조합인지 (극단상황 I)
        dc_max: 이 조합에서만 쓰는 DC 의 최대 하중계수. ``None`` 이면 표 4.1-2 의
            1.25 를 쓴다. 극한Ⅳ 만 1.50 이다.
        description: 조합의 뜻
    """

    name: str
    limit_state: str
    factors: dict[str, float] = field(default_factory=dict)
    permanent: float | None = None
    tu_factors: tuple[float, float] | None = None
    uses_gamma_tg: bool = False
    uses_gamma_sd: bool = False
    live_load_by_owner: bool = False
    dc_max: float | None = None
    description: str = ""

    def evaluate(
        self,
        loads: dict[str, float],
        permanent_kinds: dict[str, str] | None = None,
        maximise: bool = True,
        deformation: bool = False,
        gamma_tg: float | None = None,
        gamma_sd: float | None = None,
        gamma_eq: float = 0.0,
        eta: float = 1.0,
    ) -> float:
        r"""하중 성분으로부터 조합하중 :math:`\sum \eta \gamma_i Q_i` 를 계산한다.

        Args:
            loads: 하중 기호별 크기. 정의되지 않은 기호는 0 으로 본다.
            permanent_kinds: 상시하중 기호를 표 4.1-2 의 종류로 잇는 사전.
                예 ``{"EV": "EV_강성암거"}``. 없으면 기호를 그대로 쓴다.
            maximise: 상시하중에 최대 계수를 쓸지 여부. 기본값 ``True``.
            deformation: 변형량 계산인지 여부. TU·CR·SH 계수를 고른다 (4.1(5)).
                기본값 ``False``.
            gamma_tg: 온도경사 하중계수. ``None`` 이면 4.1(7) 의 기본값을 쓴다.
            gamma_sd: 부등침하 하중계수. ``None`` 이면 4.1(7) 의 기본값을 쓴다.
            gamma_eq: 극단상황 I 의 활하중계수 (4.1(9)). 기본값 ``0.0``.
            eta: 하중수정계수 :math:`\eta`. 기본값 ``1.0``.

        Returns:
            조합하중
        """
        kinds = permanent_kinds or {}
        total = 0.0

        # 상시하중
        for symbol in PERMANENT_SYMBOLS:
            value = loads.get(symbol, 0.0)

            if not value:
                continue

            if self.permanent is not None:
                factor = self.permanent
            elif symbol == "DC" and maximise and self.dc_max is not None:
                factor = self.dc_max
            elif symbol in ("CR", "SH") and self.tu_factors is not None:
                factor = self.tu_factors[1] if deformation else self.tu_factors[0]
            else:
                factor = permanent_load_factor(
                    kind=kinds.get(symbol, symbol), maximum=maximise
                )

            total += factor * value

        # 변동하중
        for symbol, factor in self.factors.items():
            if self.live_load_by_owner and symbol in LIVE_SYMBOLS:
                factor = gamma_eq

            total += factor * loads.get(symbol, 0.0)

        # TU (온도의 균등 변화)
        if self.tu_factors is not None:
            factor = self.tu_factors[1] if deformation else self.tu_factors[0]
            total += factor * loads.get("TU", 0.0)

        # 온도경사와 부등침하 — 공사별 특별시방이 없으면 4.1(7)
        default = self.default_gamma_tg_sd()

        if self.uses_gamma_tg:
            total += (default if gamma_tg is None else gamma_tg) * loads.get("TG", 0.0)

        if self.uses_gamma_sd:
            total += (default if gamma_sd is None else gamma_sd) * loads.get("SD", 0.0)

        return eta * total

    def default_gamma_tg_sd(self) -> float:
        """공사별 하중계수가 없을 때의 :math:`\\gamma_{TG}`, :math:`\\gamma_{SD}`.

        **KDS 24 12 11 4.1(7)**

        극한·극단상황에서는 0.0 (고려하지 않음), 사용한계상태에서는 활하중이
        있으면 0.5, 없으면 1.0 이다.

        Returns:
            기본 하중계수
        """
        if self.limit_state in ("극한", "극단상황"):
            return 0.0

        has_live = any(self.factors.get(s, 0.0) for s in LIVE_SYMBOLS)

        return 0.5 if has_live else 1.0


def _live(factor: float) -> dict[str, float]:
    """활하중 무리에 같은 계수를 매긴다 (표 4.1-1 은 한 칸으로 묶여 있다)."""
    return dict.fromkeys(LIVE_SYMBOLS, factor)


LOAD_COMBINATIONS: tuple[LoadCombination, ...] = (
    LoadCombination(
        name="극한Ⅰ",
        limit_state="극한",
        factors={**_live(1.80), "WA": 1.00, "FR": 1.00},
        tu_factors=(0.50, 1.20),
        uses_gamma_tg=True,
        uses_gamma_sd=True,
        description="일반적인 차량통행을 고려한 기본조합. 풍하중은 보지 않는다.",
    ),
    LoadCombination(
        name="극한Ⅱ",
        limit_state="극한",
        factors={**_live(1.40), "WA": 1.00, "FR": 1.00},
        tu_factors=(0.50, 1.20),
        uses_gamma_tg=True,
        uses_gamma_sd=True,
        description="발주자가 정하는 특수차량·통행허가차량 조합. 풍하중은 보지 않는다.",
    ),
    LoadCombination(
        name="극한Ⅲ",
        limit_state="극한",
        factors={"WA": 1.00, "WS": 1.40, "FR": 1.00},
        tu_factors=(0.50, 1.20),
        uses_gamma_tg=True,
        uses_gamma_sd=True,
        description="거더 높이에서 풍속 25 m/s 를 넘는 설계풍하중 조합. 활하중은 없다.",
    ),
    LoadCombination(
        name="극한Ⅳ",
        limit_state="극한",
        factors={"WA": 1.00, "FR": 1.00},
        tu_factors=(0.50, 1.20),
        dc_max=DC_MAX_ULS_IV,
        description="활하중에 비해 고정하중이 매우 큰 경우. DC 최대계수는 1.50.",
    ),
    LoadCombination(
        name="극한Ⅴ",
        limit_state="극한",
        factors={**_live(1.40), "WA": 1.00, "WS": 0.40, "WL": 1.00, "FR": 1.00},
        tu_factors=(0.50, 1.20),
        uses_gamma_tg=True,
        uses_gamma_sd=True,
        description="통행이 가능한 최대 풍속과 일상적인 차량통행을 함께 본다.",
    ),
    LoadCombination(
        name="극단상황Ⅰ",
        limit_state="극단상황",
        factors={**_live(0.0), "WA": 1.00, "FR": 1.00, "EQ": 1.00},
        live_load_by_owner=True,
        description="지진하중 조합. 활하중계수는 발주자가 정한다 (4.1(9)).",
    ),
    LoadCombination(
        name="극단상황Ⅱ",
        limit_state="극단상황",
        factors={
            **_live(0.50),
            "WA": 1.00,
            "FR": 1.00,
            "IC": 1.00,
            "CT": 1.00,
            "CV": 1.00,
        },
        description="빙하중·충돌하중과 감소된 활하중. 셋 중 하나만 동시에 본다.",
    ),
    LoadCombination(
        name="사용Ⅰ",
        limit_state="사용",
        factors={**_live(1.00), "WA": 1.00, "WS": 0.30, "WL": 1.00, "FR": 1.00},
        permanent=1.00,
        tu_factors=(1.00, 1.20),
        uses_gamma_tg=True,
        uses_gamma_sd=True,
        description="정상 운용 상태의 모든 하중 표준값. RC 사용성 검증에 쓴다.",
    ),
    LoadCombination(
        name="사용Ⅱ",
        limit_state="사용",
        factors={**_live(1.30), "WA": 1.00, "FR": 1.00},
        permanent=1.00,
        tu_factors=(1.00, 1.20),
        description="강구조물의 항복과 마찰이음부 미끄러짐 조합.",
    ),
    LoadCombination(
        name="사용Ⅲ",
        limit_state="사용",
        factors={**_live(0.80), "WA": 1.00, "FR": 1.00},
        permanent=1.00,
        tu_factors=(1.00, 1.20),
        uses_gamma_tg=True,
        uses_gamma_sd=True,
        description="부착 긴장재가 있는 상부구조의 균열폭·인장응력 검증에 쓴다.",
    ),
    LoadCombination(
        name="사용Ⅳ",
        limit_state="사용",
        factors={"WA": 1.00, "WS": 0.70, "FR": 1.00},
        permanent=1.00,
        tu_factors=(1.00, 1.20),
        uses_gamma_sd=True,
        description="연직 활하중 대신 수평 풍하중을 보는 하부구조의 사용성 조합.",
    ),
    LoadCombination(
        name="사용Ⅴ",
        limit_state="사용",
        factors={},
        permanent=1.00,
        tu_factors=(0.50, 0.50),
        description="고정하중과 수명의 약 50 % 동안 지속하는 하중의 조합.",
    ),
    LoadCombination(
        name="피로",
        limit_state="피로",
        factors=_live(0.75),
        permanent=0.0,
        description="피로설계트럭하중에 의한 반복 하중효과. LL, IM, CF 만 본다.",
    ),
)
"""KDS 24 12 11 표 4.1-1 도로교의 하중조합 13 가지."""

COMBINATIONS_BY_NAME: dict[str, LoadCombination] = {
    combination.name: combination for combination in LOAD_COMBINATIONS
}


def evaluate_all(
    loads: dict[str, float],
    limit_state: str | None = None,
    **kwargs: object,
) -> dict[str, float]:
    """모든 하중조합을 계산해 조합 이름별 결과를 돌려준다.

    Args:
        loads: 하중 기호별 크기
        limit_state: 특정 한계상태만 걸러낼 때 지정한다. 기본값 ``None`` (전부).
        kwargs: :meth:`LoadCombination.evaluate` 로 넘기는 나머지 인자

    Returns:
        조합 이름 → 조합하중
    """
    return {
        combination.name: combination.evaluate(loads=loads, **kwargs)  # type: ignore[arg-type]
        for combination in LOAD_COMBINATIONS
        if limit_state is None or combination.limit_state == limit_state
    }


def governing_combination(
    loads: dict[str, float],
    limit_state: str = "극한",
    **kwargs: object,
) -> tuple[str, float]:
    """지배하는 하중조합과 그 크기를 돌려준다.

    Args:
        loads: 하중 기호별 크기
        limit_state: 대상 한계상태. 기본값 ``"극한"``.
        kwargs: :meth:`LoadCombination.evaluate` 로 넘기는 나머지 인자

    Returns:
        (조합 이름, 조합하중)
    """
    results = evaluate_all(loads=loads, limit_state=limit_state, **kwargs)

    name = max(results, key=lambda key: abs(results[key]))

    return name, results[name]
