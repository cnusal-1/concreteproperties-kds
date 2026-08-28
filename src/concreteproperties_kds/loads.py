"""하중조합과 소요강도 (KDS 14 20 10 4.2.2).

강도설계법의 하중계수 조합을 정의하고, 하중 성분으로부터 소요강도 U 를 계산한다.

조합은 KDS 14 20 10 4.2.2 의 식 (4.2-1) ~ 식 (4.2-8) 을 그대로 옮긴 것이다.
"또는" 으로 택일하는 항은 각각 별도의 조합으로 전개하여, 어느 쪽이 지배하는지
확인할 수 있게 하였다.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# 하중 기호 (KDS 14 20 10 4.1, 4.2.2)
LOAD_SYMBOLS: dict[str, str] = {
    "D": "고정하중",
    "L": "활하중",
    "L_r": "지붕활하중",
    "S": "적설하중",
    "R": "강우하중",
    "W": "풍하중",
    "E": "지진하중",
    "F": "유체압",
    "H_h": "횡방향 토압",
    "H_v": "연직방향 토압",
    "T": "온도·크리프·건조수축·부등침하 등의 영향",
}

# 지붕에 작용하는 변동하중 (택일)
ROOF_LOADS = ("L_r", "S", "R")

# 활하중 계수를 저감할 수 있는 하중의 크기 (KDS 14 20 10 4.2.2(2))
LIVE_LOAD_REDUCTION_THRESHOLD = 5.0  # kN/m^2
LIVE_LOAD_FACTOR_REDUCED = 0.5


def alpha_h(depth: float) -> float:
    r"""연직방향 토압에 대한 보정계수 :math:`\alpha_H` 를 반환한다.

    KDS 14 20 10 4.2.2(1)

    .. math::
        \alpha_H = \begin{cases}
        1.0 & h \le 2\ \text{m} \\
        1.05 - 0.025 h \ \ge 0.875 & h > 2\ \text{m}
        \end{cases}

    Args:
        depth: 토피 깊이 :math:`h` (m)

    Returns:
        연직방향 토압 보정계수
    """
    if depth <= 2.0:
        return 1.0

    return float(max(1.05 - 0.025 * depth, 0.875))


@dataclass(frozen=True)
class LoadCombination:
    """하나의 하중조합.

    Args:
        name: 조합 이름
        equation: KDS 의 식 번호
        factors: 하중 기호별 계수
        roof: 지붕 변동하중 :math:`(L_r` 또는 :math:`S` 또는 :math:`R)` 의 계수
        alpha_h_symbols: :math:`\\alpha_H` 를 함께 곱하는 하중 기호
        live_load_reducible: 활하중 계수를 저감할 수 있는 조합인지 여부
        description: 조합 식의 문자 표현
    """

    name: str
    equation: str
    factors: dict[str, float] = field(default_factory=dict)
    roof: float = 0.0
    alpha_h_symbols: frozenset[str] = frozenset()
    live_load_reducible: bool = False
    description: str = ""

    def evaluate(
        self,
        loads: dict[str, float],
        depth: float = 0.0,
        reduce_live_load: bool = False,
    ) -> float:
        """주어진 하중 성분에 대해 조합 하중을 계산한다.

        Args:
            loads: 하중 기호별 크기. 정의되지 않은 기호는 0 으로 본다.
            depth: 토피 깊이 (m). :math:`\\alpha_H` 계산에 사용한다.
                기본값 ``0``.
            reduce_live_load: 활하중 계수 저감 적용 여부. 기본값 ``False``.

        Returns:
            조합 하중
        """
        total = 0.0
        a_h = alpha_h(depth=depth)

        for symbol, factor in self.factors.items():
            value = loads.get(symbol, 0.0)

            if symbol == "L" and reduce_live_load and self.live_load_reducible:
                factor = LIVE_LOAD_FACTOR_REDUCED

            if symbol in self.alpha_h_symbols:
                factor *= a_h

            total += factor * value

        if self.roof:
            total += self.roof * max(loads.get(s, 0.0) for s in ROOF_LOADS)

        return total


# KDS 14 20 10 4.2.2 소요강도
# "또는" 으로 택일하는 항은 별도의 조합으로 전개하였다.
LOAD_COMBINATIONS: tuple[LoadCombination, ...] = (
    LoadCombination(
        name="U1",
        equation="4.2-1",
        factors={"D": 1.4, "F": 1.4},
        description="U = 1.4(D + F)",
    ),
    LoadCombination(
        name="U2",
        equation="4.2-2",
        factors={"D": 1.2, "F": 1.2, "T": 1.2, "L": 1.6, "H_v": 1.6, "H_h": 1.6},
        roof=0.5,
        alpha_h_symbols=frozenset({"H_v"}),
        description=(
            "U = 1.2(D+F+T) + 1.6(L + aH*H_v + H_h) + 0.5(L_r or S or R)"
        ),
    ),
    LoadCombination(
        name="U3-L",
        equation="4.2-3",
        factors={"D": 1.2, "L": 1.0},
        roof=1.6,
        live_load_reducible=True,
        description="U = 1.2D + 1.6(L_r or S or R) + 1.0L",
    ),
    LoadCombination(
        name="U3-W",
        equation="4.2-3",
        factors={"D": 1.2, "W": 0.65},
        roof=1.6,
        description="U = 1.2D + 1.6(L_r or S or R) + 0.65W",
    ),
    LoadCombination(
        name="U4",
        equation="4.2-4",
        factors={"D": 1.2, "W": 1.3, "L": 1.0},
        roof=0.5,
        live_load_reducible=True,
        description="U = 1.2D + 1.3W + 1.0L + 0.5(L_r or S or R)",
    ),
    LoadCombination(
        name="U5-a",
        equation="4.2-5",
        factors={"D": 1.2, "H_v": 1.2, "E": 1.0, "L": 1.0, "S": 0.2, "H_h": 1.0},
        live_load_reducible=True,
        description="U = 1.2(D+H_v) + 1.0E + 1.0L + 0.2S + 1.0H_h",
    ),
    LoadCombination(
        name="U5-b",
        equation="4.2-5",
        factors={"D": 1.2, "H_v": 1.2, "E": 1.0, "L": 1.0, "S": 0.2, "H_h": 0.5},
        live_load_reducible=True,
        description="U = 1.2(D+H_v) + 1.0E + 1.0L + 0.2S + 0.5H_h",
    ),
    LoadCombination(
        name="U6",
        equation="4.2-6",
        factors={"D": 1.2, "F": 1.2, "T": 1.2, "L": 1.6, "H_v": 1.6, "H_h": 0.8},
        roof=0.5,
        alpha_h_symbols=frozenset({"H_v"}),
        description=(
            "U = 1.2(D+F+T) + 1.6(L + aH*H_v) + 0.8H_h + 0.5(L_r or S or R)"
        ),
    ),
    LoadCombination(
        name="U7-a",
        equation="4.2-7",
        factors={"D": 0.9, "H_v": 0.9, "W": 1.3, "H_h": 1.6},
        description="U = 0.9(D + H_v) + 1.3W + 1.6H_h",
    ),
    LoadCombination(
        name="U7-b",
        equation="4.2-7",
        factors={"D": 0.9, "H_v": 0.9, "W": 1.3, "H_h": 0.8},
        description="U = 0.9(D + H_v) + 1.3W + 0.8H_h",
    ),
    LoadCombination(
        name="U8-a",
        equation="4.2-8",
        factors={"D": 0.9, "H_v": 0.9, "E": 1.0, "H_h": 1.0},
        description="U = 0.9(D + H_v) + 1.0E + 1.0H_h",
    ),
    LoadCombination(
        name="U8-b",
        equation="4.2-8",
        factors={"D": 0.9, "H_v": 0.9, "E": 1.0, "H_h": 0.5},
        description="U = 0.9(D + H_v) + 1.0E + 0.5H_h",
    ),
)


def evaluate_all(
    loads: dict[str, float],
    combinations: tuple[LoadCombination, ...] = LOAD_COMBINATIONS,
    depth: float = 0.0,
    reduce_live_load: bool = False,
) -> list[tuple[LoadCombination, float]]:
    """모든 하중조합의 결과를 큰 순서대로 반환한다.

    Args:
        loads: 하중 기호별 크기
        combinations: 평가할 하중조합. 기본값 :data:`LOAD_COMBINATIONS`.
        depth: 토피 깊이 (m). 기본값 ``0``.
        reduce_live_load: 활하중 계수 저감 적용 여부. 활하중이
            5.0 kN/m\\ :sup:`2` 미만이고 차고·공공집회 장소가 아닌 경우에
            식 (4.2-3), (4.2-4), (4.2-5) 에 적용할 수 있다. 기본값 ``False``.

    Returns:
        (하중조합, 조합 하중) 목록, 조합 하중이 큰 순서
    """
    results = [
        (
            combo,
            combo.evaluate(
                loads=loads, depth=depth, reduce_live_load=reduce_live_load
            ),
        )
        for combo in combinations
    ]
    results.sort(key=lambda item: item[1], reverse=True)

    return results


def required_strength(
    loads: dict[str, float],
    combinations: tuple[LoadCombination, ...] = LOAD_COMBINATIONS,
    depth: float = 0.0,
    reduce_live_load: bool = False,
) -> tuple[float, LoadCombination]:
    """모든 하중조합을 평가하여 소요강도와 지배 조합을 반환한다.

    Args:
        loads: 하중 기호별 크기. :data:`LOAD_SYMBOLS` 의 기호를 사용한다.
        combinations: 평가할 하중조합. 기본값 :data:`LOAD_COMBINATIONS`.
        depth: 토피 깊이 (m). 기본값 ``0``.
        reduce_live_load: 활하중 계수 저감 적용 여부. 기본값 ``False``.

    Raises:
        ValueError: ``combinations`` 가 비어 있는 경우

    Returns:
        소요강도의 최댓값과 그 값을 준 하중조합 (``u_max``, ``governing``)
    """
    if not combinations:
        msg = "combinations 는 하나 이상의 하중조합을 포함해야 합니다."
        raise ValueError(msg)

    results = evaluate_all(
        loads=loads,
        combinations=combinations,
        depth=depth,
        reduce_live_load=reduce_live_load,
    )

    return results[0][1], results[0][0]


def minimum_strength(
    loads: dict[str, float],
    combinations: tuple[LoadCombination, ...] = LOAD_COMBINATIONS,
    depth: float = 0.0,
    reduce_live_load: bool = False,
) -> tuple[float, LoadCombination]:
    """가장 작은 조합 하중과 그 조합을 반환한다.

    풍하중·지진하중에 의한 부양이나 전도를 검토할 때 사용한다
    (식 (4.2-7), (4.2-8)).

    Args:
        loads: 하중 기호별 크기
        combinations: 평가할 하중조합. 기본값 :data:`LOAD_COMBINATIONS`.
        depth: 토피 깊이 (m). 기본값 ``0``.
        reduce_live_load: 활하중 계수 저감 적용 여부. 기본값 ``False``.

    Raises:
        ValueError: ``combinations`` 가 비어 있는 경우

    Returns:
        조합 하중의 최솟값과 그 값을 준 하중조합 (``u_min``, ``governing``)
    """
    if not combinations:
        msg = "combinations 는 하나 이상의 하중조합을 포함해야 합니다."
        raise ValueError(msg)

    results = evaluate_all(
        loads=loads,
        combinations=combinations,
        depth=depth,
        reduce_live_load=reduce_live_load,
    )

    return results[-1][1], results[-1][0]


def print_combinations(
    loads: dict[str, float],
    combinations: tuple[LoadCombination, ...] = LOAD_COMBINATIONS,
    depth: float = 0.0,
    reduce_live_load: bool = False,
) -> None:
    """하중조합 평가 결과를 표로 출력한다.

    Args:
        loads: 하중 기호별 크기
        combinations: 평가할 하중조합. 기본값 :data:`LOAD_COMBINATIONS`.
        depth: 토피 깊이 (m). 기본값 ``0``.
        reduce_live_load: 활하중 계수 저감 적용 여부. 기본값 ``False``.
    """
    results = evaluate_all(
        loads=loads,
        combinations=combinations,
        depth=depth,
        reduce_live_load=reduce_live_load,
    )

    width = 96
    print("=" * width)
    print("하중조합 (KDS 14 20 10 4.2.2)")
    print("=" * width)
    print(f"{'조합':>7} {'식':>8} {'U':>12}  {'':<58}")
    print("-" * width)

    for idx, (combo, value) in enumerate(results):
        mark = " <= 지배" if idx == 0 else ""
        print(
            f"{combo.name:>7} {combo.equation:>8} {value:12.2f}  "
            f"{combo.description:<58}{mark}"
        )
