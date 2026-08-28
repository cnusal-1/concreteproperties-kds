"""예제 09 - 하중조합과 소요강도.

KDS 14 20 10 4.2.2 의 하중조합을 평가하여 지배 조합과 소요강도를 구한다.

실행:
    python 09_하중조합.py
"""

from __future__ import annotations

from concreteproperties_kds.loads import (
    LOAD_SYMBOLS,
    evaluate_all,
    print_combinations,
    required_strength,
)


def main() -> None:
    """예제를 실행한다."""
    # 8 m 경간 보의 단위길이당 하중 (kN/m)
    loads = {
        "D": 25.0,  # 고정하중
        "L": 18.0,  # 활하중
        "L_r": 3.0,  # 지붕활하중
        "S": 5.0,  # 적설하중
        "W": 12.0,  # 풍하중
        "E": 20.0,  # 지진하중
    }

    print("입력 하중 (kN/m)")
    print("-" * 40)
    for symbol, value in loads.items():
        print(f"  {symbol:>4} ({LOAD_SYMBOLS[symbol]}) = {value:7.2f}")
    print()

    print_combinations(loads=loads)

    u_max, governing = required_strength(loads=loads)
    print()
    print(f"소요강도 wu = {u_max:.2f} kN/m  ({governing.name})")

    span = 8.0
    m_u = u_max * span**2 / 8
    v_u = u_max * span / 2
    print(f"계수 휨모멘트 Mu = wu*l^2/8 = {m_u:.2f} kN.m")
    print(f"계수 전단력   Vu = wu*l/2   = {v_u:.2f} kN")

    print()
    print("활하중 계수 저감 (활하중 5 kN/m^2 이하, 주차장·집회장 제외)")
    print("-" * 62)
    full = {c.name: v for c, v in evaluate_all(loads=loads)}
    reduced = {
        c.name: v for c, v in evaluate_all(loads=loads, reduce_live_load=True)
    }
    for name in sorted(full):
        if abs(full[name] - reduced[name]) > 1e-9:
            print(f"  {name} : {full[name]:8.2f} -> {reduced[name]:8.2f} kN/m")


if __name__ == "__main__":
    main()
