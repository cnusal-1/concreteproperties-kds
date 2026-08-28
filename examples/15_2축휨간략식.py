"""예제 15 - 2축 휨 간략식과 엄밀해 비교.

Bresler 등하중선법·역하중법의 결과를 `concreteproperties` 로 계산한 엄밀
2축 휨 상관면과 비교한다.

실행:
    python 15_2축휨간략식.py
"""

from __future__ import annotations

import numpy as np
from examples_common import column_section

from concreteproperties_kds.biaxial import (
    check_bresler_reciprocal,
    check_load_contour,
    compare_with_exact,
)

N_DESIGN = 1200e3
M_UX = 200e6
M_UY = 120e6


def exact_ratio(kds, n_design: float, m_ux: float, m_uy: float) -> float:
    """엄밀 2축 휨 상관면에서 소요/강도 비를 구한다.

    소요 모멘트 벡터의 방향으로 상관면까지의 거리를 구하고, 소요 모멘트
    크기와의 비를 반환한다.

    Args:
        kds: 설계기준 객체
        n_design: 계수 축력 (N)
        m_ux: x 축 계수 휨모멘트 (N·mm)
        m_uy: y 축 계수 휨모멘트 (N·mm)

    Returns:
        소요/강도 비
    """
    f_bb, _ = kds.biaxial_bending_diagram(
        n_design=n_design, n_points=48, progress_bar=False
    )

    m_x = np.array([r.m_x for r in f_bb.results])
    m_y = np.array([r.m_y for r in f_bb.results])

    # 소요 모멘트 방향의 각도
    target = np.arctan2(m_uy, m_ux)
    angles = np.arctan2(m_y, m_x)

    # 방향이 가장 가까운 두 점 사이를 보간
    diff = np.abs(np.angle(np.exp(1j * (angles - target))))
    idx = int(np.argmin(diff))

    capacity = float(np.hypot(m_x[idx], m_y[idx]))
    demand = float(np.hypot(m_ux, m_uy))

    return demand / capacity


def main() -> None:
    """예제를 실행한다."""
    kds, _ = column_section()

    # 1축 설계 휨강도
    f_x, _, phi_x = kds.ultimate_bending_capacity(theta=0, n_design=N_DESIGN)
    f_y, _, phi_y = kds.ultimate_bending_capacity(
        theta=-np.pi / 2, n_design=N_DESIGN
    )

    phi_m_nx = abs(f_x.m_x)
    phi_m_ny = abs(f_y.m_y)

    width = 66
    print("=" * width)
    print(f"1축 설계 휨강도 (Nd = {N_DESIGN / 1e3:.0f} kN)")
    print("=" * width)
    print(f"x 축   phi*Mnx = {phi_m_nx / 1e6:9.2f} kN.m  (phi = {phi_x:.3f})")
    print(f"y 축   phi*Mny = {phi_m_ny / 1e6:9.2f} kN.m  (phi = {phi_y:.3f})")
    print()
    print(f"소요   Mux = {M_UX / 1e6:.1f} kN.m,  Muy = {M_UY / 1e6:.1f} kN.m")
    print()

    # 등하중선법
    res = check_load_contour(
        m_ux=M_UX, m_uy=M_UY, phi_m_nx=phi_m_nx, phi_m_ny=phi_m_ny, alpha=1.0
    )
    res.print_results()
    print()

    # 역하중법 (축강도 기준)
    n_max_nom, n_max_des = kds.max_axial_strength()
    # 편심 e = M/N 에 대한 축강도를 상관도에서 역산
    f_mi, _, _ = kds.moment_interaction_diagram(
        theta=0, n_points=32, progress_bar=False
    )
    n_list = np.array([r.n for r in f_mi.results])
    m_list = np.array([r.m_x for r in f_mi.results])

    def axial_capacity_at_eccentricity(e: float) -> float:
        """편심 e 에 대한 설계 축강도를 상관도에서 보간한다.

        Args:
            e: 편심 (mm)

        Returns:
            설계 축강도 (N)
        """
        # N*e = M 인 점을 찾는다
        residual = m_list - n_list * e
        for i in range(len(residual) - 1):
            if residual[i] * residual[i + 1] <= 0:
                t = residual[i] / (residual[i] - residual[i + 1])
                return float(n_list[i] + t * (n_list[i + 1] - n_list[i]))
        return float(n_list[0])

    p_nx = axial_capacity_at_eccentricity(M_UX / N_DESIGN)
    p_ny = axial_capacity_at_eccentricity(M_UY / N_DESIGN)

    res_b = check_bresler_reciprocal(
        p_u=N_DESIGN,
        phi_p_nx=p_nx,
        phi_p_ny=p_ny,
        phi_p_o=n_max_des,
        fck=27,
        a_g=500.0 * 500.0,
    )
    print(f"편심 ex = {M_UX / N_DESIGN:.1f} mm -> phi*Pnx = {p_nx / 1e3:.1f} kN")
    print(f"편심 ey = {M_UY / N_DESIGN:.1f} mm -> phi*Pny = {p_ny / 1e3:.1f} kN")
    print(f"phi*Po = {n_max_des / 1e3:.1f} kN  (Pn,max = {n_max_nom / 1e3:.1f} kN)")
    res_b.print_results()
    print()

    # 엄밀해와 비교
    ratio = exact_ratio(kds, n_design=N_DESIGN, m_ux=M_UX, m_uy=M_UY)

    print("=" * width)
    print("엄밀 2축 휨 상관면과 비교")
    print("=" * width)
    print(f"엄밀해 소요/강도 = {ratio:.4f}")
    print()
    print(f"{'alpha':>8} {'등하중선법':>12} {'보수적':>10}")
    print("-" * width)
    for alpha, value, conservative in compare_with_exact(
        m_ux=M_UX,
        m_uy=M_UY,
        phi_m_nx=phi_m_nx,
        phi_m_ny=phi_m_ny,
        exact_ratio=ratio,
    ):
        print(f"{alpha:8.2f} {value:12.4f} {'예' if conservative else '아니오':>10}")


if __name__ == "__main__":
    main()
