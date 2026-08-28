"""예제 08 - 응력 해석.

비균열·균열·사용·극한 상태의 단면 응력을 계산하고, 콘크리트와 철근의
최대·최소 응력을 정리한다.

실행:
    python 08_응력해석.py [--plot]
"""

from __future__ import annotations

import sys

from examples_common import beam_section


def summarise(label: str, stress_res) -> None:
    """응력 결과를 요약 출력한다.

    Args:
        label: 해석 상태 이름
        stress_res: 응력 결과 객체
    """
    conc_stresses = [float(s) for arr in stress_res.concrete_stresses for s in arr]
    steel_stresses = [
        float(s) for s in stress_res.lumped_reinforcement_stresses
    ]

    print(
        f"{label:>10} | 콘크리트 {min(conc_stresses):8.2f} ~ {max(conc_stresses):7.2f}"
        f" MPa | 철근 {min(steel_stresses):9.2f} ~ {max(steel_stresses):8.2f} MPa"
    )


def main(plot: bool = False) -> None:
    """예제를 실행한다.

    Args:
        plot: 응력 분포를 도시할지 여부
    """
    kds, _ = beam_section()

    cracked = kds.calculate_cracked_properties(theta=0)
    m_service = 1.5 * cracked.m_cr
    _, u_res, _ = kds.ultimate_bending_capacity()

    print("=" * 88)
    print(f"응력 해석 (사용 모멘트 M = {m_service / 1e6:.1f} kN.m)")
    print("=" * 88)

    uncracked = kds.calculate_uncracked_stress(m_x=m_service)
    cracked_stress = kds.calculate_cracked_stress(
        cracked_results=cracked, m=m_service
    )
    service = kds.calculate_service_stress(
        moment_curvature_results=kds.moment_curvature_analysis(
            theta=0, kappa_inc=1e-7, progress_bar=False
        ),
        m=m_service,
    )
    ultimate = kds.calculate_ultimate_stress(ultimate_results=u_res)

    summarise("비균열", uncracked)
    summarise("균열", cracked_stress)
    summarise("사용", service)
    summarise("극한", ultimate)

    if plot:
        for res in (uncracked, cracked_stress, service, ultimate):
            res.plot_stress()


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
