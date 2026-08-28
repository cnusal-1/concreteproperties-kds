"""예제 05 - 기둥의 P-M 상관도.

500 x 500 띠철근 기둥(8-D22)의 공칭 P-M 상관도와, KDS 14 20 10 표 4.2-1 의
강도감소계수를 적용한 설계 P-M 상관도를 생성한다. 압축측은 KDS 14 20 20 4.1.2
의 최대 설계 축강도로 절단된다.

실행:
    python 05_PM상관도.py [--plot]
"""

from __future__ import annotations

import sys

from examples_common import column_section


def main(plot: bool = False) -> None:
    """예제를 실행한다.

    Args:
        plot: P-M 상관도를 도시할지 여부
    """
    kds, _ = column_section(column_type="tie")

    n_max_nom, n_max_des = kds.max_axial_strength()

    print("=" * 84)
    print("축강도 (KDS 14 20 20 4.1.2)")
    print("=" * 84)
    print(f"공칭 축강도        Po        = {kds.squash_load / 1e3:,.1f} kN")
    print(f"최대 공칭 축강도   0.80*Po   = {n_max_nom / 1e3:,.1f} kN")
    print(f"최대 설계 축강도   phi*Pn,max= {n_max_des / 1e3:,.1f} kN")
    print(f"공칭 인장강도      Pnt       = {kds.tensile_load / 1e3:,.1f} kN")

    f_mi, mi, phis = kds.moment_interaction_diagram(n_points=16, progress_bar=False)

    print()
    print("=" * 84)
    print("P-M 상관도")
    print("=" * 84)
    print(
        f"{'Nn(kN)':>12} {'Mn(kN.m)':>12} {'et':>10} {'단면분류':>10} "
        f"{'phi':>7} {'phiNn(kN)':>12} {'phiMn(kN.m)':>13}"
    )
    print("-" * 84)

    for r_u, r_f, phi in zip(mi.results, f_mi.results, phis, strict=True):
        eps_t = kds.net_tensile_strain(theta=0, d_n=r_u.d_n)
        eps_str = "  -inf" if eps_t == float("inf") else f"{eps_t:10.5f}"
        eps_str = f"{'inf':>10}" if eps_t == float("inf") else eps_str
        print(
            f"{r_u.n / 1e3:12.1f} {r_u.m_x / 1e6:12.1f} {eps_str} "
            f"{kds.section_classification(eps_t=eps_t):>10} "
            f"{phi:7.3f} {r_f.n / 1e3:12.1f} {r_f.m_x / 1e6:13.1f}"
        )

    print()
    print("=" * 84)
    print("설계 축력별 설계 휨강도")
    print("=" * 84)
    print(f"{'Nd(kN)':>10} {'phi':>8} {'et':>10} {'단면분류':>10} {'phiMn(kN.m)':>13}")
    print("-" * 84)

    for n_d in [-800, -400, 0, 400, 800, 1200, 1600, 2000, 2800, 3400]:
        f_res, u_res, phi = kds.ultimate_bending_capacity(n_design=n_d * 1e3)
        eps_t = kds.net_tensile_strain(theta=0, d_n=u_res.d_n)
        eps_str = f"{'inf':>10}" if eps_t == float("inf") else f"{eps_t:10.5f}"
        print(
            f"{n_d:10.0f} {phi:8.3f} {eps_str} "
            f"{kds.section_classification(eps_t=eps_t):>10} {f_res.m_x / 1e6:13.1f}"
        )

    if plot:
        import matplotlib.pyplot as plt
        from concreteproperties.results import MomentInteractionResults

        MomentInteractionResults.plot_multiple_diagrams(
            [mi, f_mi],
            ["공칭강도 (Mn, Pn)", "설계강도 (phi*Mn, phi*Pn)"],
            fmt="-",
        )
        plt.show()


if __name__ == "__main__":
    main(plot="--plot" in sys.argv)
