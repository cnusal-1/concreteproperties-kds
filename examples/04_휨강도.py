"""예제 04 - 보의 설계 휨강도.

KDS 14 20 20 의 등가직사각형 응력블록으로 공칭 휨강도를 구하고,
KDS 14 20 10 4.3.3(2) 의 강도감소계수를 적용한 설계 휨강도를 산정한다.
아울러 최소철근량과 최소허용변형률 조건을 검토한다.

실행:
    python 04_휨강도.py [--plot]
"""

from __future__ import annotations

import sys

from examples_common import beam_section

from concreteproperties_kds import minimum_flexural_moment


def main(plot: bool = False) -> None:
    """예제를 실행한다.

    Args:
        plot: 극한상태 응력을 도시할지 여부
    """
    kds, conc_sec = beam_section()

    f_res, u_res, phi = kds.ultimate_bending_capacity(theta=0, n_design=0)
    eps_t = kds.net_tensile_strain(theta=0, d_n=u_res.d_n)

    print("=" * 70)
    print("설계 휨강도 (KDS 14 20 20 / KDS 14 20 10)")
    print("=" * 70)
    print(f"중립축 깊이          c   = {u_res.d_n:.2f} mm")
    print(f"등가응력블록 깊이    a   = {u_res.d_n * 0.80:.2f} mm")
    print(f"순인장변형률         et  = {eps_t:.5f}")
    print(f"단면 분류                = {kds.section_classification(eps_t=eps_t)}")
    print(f"강도감소계수         phi = {phi:.3f}")
    print(f"공칭 휨강도          Mn  = {u_res.m_x / 1e6:.2f} kN.m")
    print(f"설계 휨강도      phi*Mn  = {f_res.m_x / 1e6:.2f} kN.m")

    print()
    print("=" * 70)
    print("연성 검토")
    print("=" * 70)
    eps_t, eps_t_min, ok = kds.check_flexural_ductility()
    print(f"최소허용변형률   et,min  = {eps_t_min:.5f}  (KDS 14 20 20 4.1.2)")
    print(f"순인장변형률     et      = {eps_t:.5f}")
    print(f"판정                     = {'만족' if ok else '불만족'}")

    print()
    print("=" * 70)
    print("최소 철근량 (KDS 14 20 20 4.2.2)")
    print("=" * 70)
    phi_m_n, m_cr, m_req, ok_min = kds.check_minimum_flexural_reinforcement()
    print(f"균열휨모멘트     Mcr     = {m_cr / 1e6:.2f} kN.m")
    m_req = minimum_flexural_moment(m_cr=m_cr)
    print(f"요구 설계휨강도  1.2Mcr  = {m_req / 1e6:.2f} kN.m")
    print(f"설계 휨강도      phi*Mn  = {phi_m_n / 1e6:.2f} kN.m")
    print(f"판정                     = {'만족' if ok_min else '불만족'}")

    if plot:
        kds.calculate_ultimate_stress(ultimate_results=u_res).plot_stress()


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
