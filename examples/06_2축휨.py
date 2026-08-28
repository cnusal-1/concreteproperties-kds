"""예제 06 - 2축 휨 상관도.

계수 축력이 작용하는 기둥에 대해 KDS 14 20 의 강도감소계수를 적용한
2축 휨 상관도(Mx-My 곡선)를 생성한다.

실행:
    python 06_2축휨.py [--plot]
"""

from __future__ import annotations

import sys

import numpy as np
from examples_common import column_section


def main(plot: bool = False) -> None:
    """예제를 실행한다.

    Args:
        plot: 2축 휨 상관도를 도시할지 여부
    """
    kds, _ = column_section()

    n_design = 1200e3
    f_bb, phis = kds.biaxial_bending_diagram(
        n_design=n_design, n_points=16, progress_bar=False
    )

    print("=" * 70)
    print(f"2축 휨 상관도 (Nd = {n_design / 1e3:,.0f} kN)")
    print("=" * 70)
    print(f"{'theta(deg)':>12} {'phiMx(kN.m)':>13} {'phiMy(kN.m)':>13} {'phi':>8}")
    print("-" * 70)

    for r, phi in zip(f_bb.results, phis, strict=True):
        theta = np.degrees(r.theta)
        print(f"{theta:12.1f} {r.m_x / 1e6:13.1f} {r.m_y / 1e6:13.1f} {phi:8.3f}")

    m_x = np.array([r.m_x for r in f_bb.results])
    m_y = np.array([r.m_y for r in f_bb.results])
    print()
    print(f"1축 휨강도 (My=0)  phi*Mnx = {np.max(np.abs(m_x)) / 1e6:.1f} kN.m")
    print(f"1축 휨강도 (Mx=0)  phi*Mny = {np.max(np.abs(m_y)) / 1e6:.1f} kN.m")

    if plot:
        f_bb.plot_diagram()


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
