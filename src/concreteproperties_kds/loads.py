"""하중조합과 소요강도 (KDS 14 20 01).

강도설계법의 하중계수 조합을 정의하고, 하중 성분으로부터 소요강도 U 를 계산한다.

.. warning::

    하중계수는 개정 이력이 잦다. :data:`LOAD_COMBINATIONS` 에 정의된 조합을
    현행 KDS 14 20 01 및 KDS 41 (건축구조기준) 과 대조한 뒤 사용한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# 하중 기호 (KDS 14 20 01 4.2)
LOAD_SYMBOLS: dict[str, str] = {
    "D": "고정하중",
    "L": "활하중",
    "L_r": "지붕활하중",
    "S": "적설하중",
    "R": "강우하중",
    "W": "풍하중",
    "E": "지진하중",
    "F": "유체압",
    "H_h": "토압(수평)",
    "H_v": "토압(연직)",
    "T": "온도·건조수축·크리프·부등침하 등의 영향",
}

# 지붕에 작용하는 변동하중 (택일)
ROOF_LOADS = ("L_r", "S", "R")


@dataclass(frozen=True)
class LoadCombination:
    """하나의 하중조합.

    Args:
        name: 조합 이름
        factors: 하중 기호별 계수. ``ROOF_LOADS`` 는 ``"ROOF"`` 키 하나로 표현하며,
            세 하중 중 큰 값을 택한다.
        description: 조합에 대한 설명
    """

    name: str
    factors: dict[str, float] = field(default_factory=dict)
    description: str = ""

    def evaluate(self, loads: dict[str, float]) -> float:
        """주어진 하중 성분에 대해 조합 하중을 계산한다.

        Args:
            loads: 하중 기호별 크기. 정의되지 않은 기호는 0 으로 본다.

        Returns:
            조합 하중
        """
        total = 0.0

        for symbol, factor in self.factors.items():
            if symbol == "ROOF":
                total += factor * max(loads.get(s, 0.0) for s in ROOF_LOADS)
            else:
                total += factor * loads.get(symbol, 0.0)

        return total


# KDS 14 20 01 4.2 소요강도
# 활하중 계수 1.0 은 활하중이 5 kN/m^2 를 초과하는 주차장·공중집회장 등에 적용하며,
# 그 밖의 경우 0.5 로 낮출 수 있다 (LIVE_LOAD_FACTOR_REDUCED).
LOAD_COMBINATIONS: tuple[LoadCombination, ...] = (
    LoadCombination(
        name="U1",
        factors={"D": 1.4, "F": 1.4},
        description="U = 1.4(D + F)",
    ),
    LoadCombination(
        name="U2",
        factors={
            "D": 1.2,
            "F": 1.2,
            "T": 1.2,
            "L": 1.6,
            "H_v": 1.6,
            "H_h": 1.6,
            "ROOF": 0.5,
        },
        description="U = 1.2(D + F + T) + 1.6(L + H_v + H_h) + 0.5(L_r or S or R)",
    ),
    LoadCombination(
        name="U3",
        factors={"D": 1.2, "ROOF": 1.6, "L": 1.0},
        description="U = 1.2D + 1.6(L_r or S or R) + 1.0L",
    ),
    LoadCombination(
        name="U4",
        factors={"D": 1.2, "ROOF": 1.6, "W": 0.65},
        description="U = 1.2D + 1.6(L_r or S or R) + 0.65W",
    ),
    LoadCombination(
        name="U5",
        factors={"D": 1.2, "W": 1.3, "L": 1.0, "ROOF": 0.5},
        description="U = 1.2D + 1.3W + 1.0L + 0.5(L_r or S or R)",
    ),
    LoadCombination(
        name="U6",
        factors={"D": 1.2, "T": 1.2, "E": 1.0, "L": 1.0, "S": 0.2},
        description="U = 1.2(D + T) + 1.0E + 1.0L + 0.2S",
    ),
    LoadCombination(
        name="U7",
        factors={"D": 0.9, "H_h": 0.9, "W": 1.3},
        description="U = 0.9(D + H_h) + 1.3W",
    ),
    LoadCombination(
        name="U8",
        factors={"D": 0.9, "H_h": 0.9, "E": 1.0},
        description="U = 0.9(D + H_h) + 1.0E",
    ),
)

# 활하중이 5 kN/m^2 이하이고 주차장·공중집회장이 아닌 경우 사용할 수 있는 계수
LIVE_LOAD_FACTOR_REDUCED = 0.5


def required_strength(
    loads: dict[str, float],
    combinations: tuple[LoadCombination, ...] = LOAD_COMBINATIONS,
    reduce_live_load: bool = False,
) -> tuple[float, LoadCombination]:
    """모든 하중조합을 평가하여 지배 조합과 소요강도를 반환한다.

    Args:
        loads: 하중 기호별 크기. :data:`LOAD_SYMBOLS` 의 기호를 사용한다.
        combinations: 평가할 하중조합. 기본값 :data:`LOAD_COMBINATIONS`.
        reduce_live_load: ``True`` 이면 U5·U6 조합의 활하중 계수를 1.0 에서
            0.5 로 낮춘다. 활하중이 5 kN/m\\ :sup:`2` 이하이고 주차장·공중집회
            장소가 아닌 경우에 사용할 수 있다. 기본값 ``False``.

    Returns:
        소요강도의 최댓값과 그 값을 준 하중조합 (``u_max``, ``governing``)

    Raises:
        ValueError: ``combinations`` 가 비어 있는 경우
    """
    if not combinations:
        msg = "combinations 는 하나 이상의 하중조합을 포함해야 합니다."
        raise ValueError(msg)

    if reduce_live_load:
        combinations = tuple(
            LoadCombination(
                name=c.name,
                factors={
                    k: (LIVE_LOAD_FACTOR_REDUCED if k == "L" and v == 1.0 else v)
                    for k, v in c.factors.items()
                },
                description=c.description,
            )
            for c in combinations
        )

    results = [(c.evaluate(loads=loads), c) for c in combinations]

    return max(results, key=lambda item: item[0])


def evaluate_all(
    loads: dict[str, float],
    combinations: tuple[LoadCombination, ...] = LOAD_COMBINATIONS,
    reduce_live_load: bool = False,
) -> list[tuple[LoadCombination, float]]:
    """모든 하중조합의 결과를 큰 순서대로 반환한다.

    Args:
        loads: 하중 기호별 크기
        combinations: 평가할 하중조합. 기본값 :data:`LOAD_COMBINATIONS`.
        reduce_live_load: 활하중 계수 저감 적용 여부. 기본값 ``False``.

    Returns:
        (하중조합, 조합 하중) 목록, 조합 하중이 큰 순서
    """
    if reduce_live_load:
        combinations = tuple(
            LoadCombination(
                name=c.name,
                factors={
                    k: (LIVE_LOAD_FACTOR_REDUCED if k == "L" and v == 1.0 else v)
                    for k, v in c.factors.items()
                },
                description=c.description,
            )
            for c in combinations
        )

    results = [(c, c.evaluate(loads=loads)) for c in combinations]
    results.sort(key=lambda item: item[1], reverse=True)

    return results


def print_combinations(
    loads: dict[str, float],
    combinations: tuple[LoadCombination, ...] = LOAD_COMBINATIONS,
    reduce_live_load: bool = False,
) -> None:
    """하중조합 평가 결과를 표로 출력한다.

    Args:
        loads: 하중 기호별 크기
        combinations: 평가할 하중조합. 기본값 :data:`LOAD_COMBINATIONS`.
        reduce_live_load: 활하중 계수 저감 적용 여부. 기본값 ``False``.
    """
    results = evaluate_all(
        loads=loads, combinations=combinations, reduce_live_load=reduce_live_load
    )

    width = 76
    print("=" * width)
    print("하중조합 (KDS 14 20 01 4.2)")
    print("=" * width)
    print(f"{'조합':>5} {'U':>14}  {'식':<52}")
    print("-" * width)

    for idx, (combo, value) in enumerate(results):
        mark = " <= 지배" if idx == 0 else ""
        print(f"{combo.name:>5} {value:14.2f}  {combo.description:<52}{mark}")
