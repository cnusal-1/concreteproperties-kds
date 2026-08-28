"""예제 07 - 모멘트-곡률 해석.

사용 응력-변형률 관계를 사용하여 보의 모멘트-곡률 관계를 계산하고,
균열모멘트·항복모멘트·극한모멘트를 비교한다. 모멘트-곡률 해석에는
강도감소계수가 적용되지 않는다.

실행:
    python 07_모멘트곡률.py [--plot]
"""

from __future__ import annotations

import sys

import numpy as np
from examples_common import beam_section


def main(plot: bool = False) -> None:
    """예제를 실행한다.

    Args:
        plot: 모멘트-곡률 곡선을 도시할지 여부
    """
    kds, _ = beam_section()

    mk_res = kds.moment_curvature_analysis(theta=0, kappa_inc=1e-7, progress_bar=False)

    kappa = np.array(mk_res.kappa)
    moment = np.array(mk_res.m_xy)

    cracked = kds.calculate_cracked_properties(theta=0)
    _, u_res, _ = kds.ultimate_bending_capacity()

    print("=" * 70)
    print("모멘트-곡률 해석")
    print("=" * 70)
    print(f"해석 점의 수                     = {len(kappa)}")
    print(f"균열모멘트          Mcr          = {cracked.m_cr / 1e6:.2f} kN.m")
    print(f"최대 모멘트 (해석)  Mmax         = {moment.max() / 1e6:.2f} kN.m")
    print(f"극한 휨강도         Mn           = {u_res.m_x / 1e6:.2f} kN.m")
    print(f"최대 곡률           kappa_max    = {kappa.max():.3e} 1/mm")

    idx = np.linspace(0, len(kappa) - 1, 12, dtype=int)
    print()
    print(f"{'kappa(1/mm)':>14} {'M(kN.m)':>12}")
    print("-" * 70)
    for i in idx:
        print(f"{kappa[i]:14.4e} {moment[i] / 1e6:12.2f}")

    if plot:
        mk_res.plot_results()


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
