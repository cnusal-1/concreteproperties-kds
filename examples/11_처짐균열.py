"""예제 11 - 처짐과 균열 검토.

예제 03 에서 구한 균열단면 제원을 이용하여 장기처짐을 계산하고, 균열 제어를
위한 철근 간격을 검토한다. (KDS 14 20 30)

실행:
    python 11_처짐균열.py
"""

from __future__ import annotations

from examples_common import beam_section

from concreteproperties_kds.serviceability import (
    check_crack_control,
    check_deflection,
    minimum_thickness,
    shrinkage_temperature_reinforcement,
)

SPAN = 8000.0
FY = 400.0


def main() -> None:
    """예제를 실행한다."""
    kds, conc_sec = beam_section()
    conc = conc_sec.concrete_geometries[0].material

    gross = kds.get_transformed_gross_properties(
        elastic_modulus=conc.elastic_modulus
    )
    cracked = kds.calculate_cracked_properties(theta=0)
    cracked.calculate_transformed_properties(elastic_modulus=conc.elastic_modulus)

    # 최소 두께 검토
    h_min = minimum_thickness(span=SPAN, member="보", support="단순지지", fy=FY)
    print("=" * 62)
    print("최소 두께 (KDS 14 20 30 표 4.2-1)")
    print("=" * 62)
    print(f"경간                 l      = {SPAN:12.0f} mm")
    print(f"최소 두께        l/16       = {h_min:12.1f} mm")
    print(f"단면 높이            h      = {600.0:12.1f} mm")
    verdict = "처짐 계산 생략 가능" if h_min <= 600.0 else "처짐 계산 필요"
    print(f"판정                        = {verdict:>12}")
    print()

    # 처짐 검토 - 허용처짐 조건마다 비교 대상 처짐이 다르다
    for condition in [
        "바닥_비구조재없음",
        "손상되기쉬운_비구조재",
        "손상되지않는_비구조재",
    ]:
        res = check_deflection(
            span=SPAN,
            m_sustained=120e6,
            m_live=60e6,
            m_cr=cracked.m_cr,
            i_g=gross.ixx_c,
            i_cr=cracked.ixx_c_cr,
            e_c=conc.elastic_modulus,
            rho_prime=2 * 198.6 / (400 * 550),
            duration="5년이상",
            condition=condition,
        )
        res.print_results()
        print()

    # 균열 제어
    print()
    fs, s_max, ok = check_crack_control(
        bar_spacing=(400 - 2 * 50) / 3, fy=FY, c_c=50 - 22.2 / 2
    )
    width = 62
    print("=" * width)
    print("균열 제어 (KDS 14 20 30 4.3)")
    print("=" * width)
    print(f"철근응력         fs = 2/3*fy = {fs:12.1f} MPa")
    print(f"최대 철근 간격   s,max       = {s_max:12.1f} mm")
    print(f"배치 철근 간격   s           = {(400 - 2 * 50) / 3:12.1f} mm")
    print(f"판정                         = {'만족' if ok else '불만족':>12}")

    # 수축·온도철근 (슬래브)
    print()
    a_st = shrinkage_temperature_reinforcement(fy=FY, a_g=1000.0 * 200.0)
    print(f"수축·온도철근 (t=200 슬래브 1 m 폭) = {a_st:.1f} mm^2/m")
    print("                  (KDS 14 20 30 4.4)")


if __name__ == "__main__":
    main()
