"""예제 14 - 세장 기둥의 2차 효과.

세장비를 검토하고 모멘트확대계수법으로 설계 모멘트를 구한 뒤, 확대된 모멘트로
P-M 상관도를 검토한다. (KDS 14 20 20 4.4)

실행:
    python 14_세장기둥.py
"""

from __future__ import annotations

from examples_common import column_section

from concreteproperties_kds.slender import check_slenderness

P_U = 1500e3  # 계수 축력 (N)
M1 = 90e6  # 작은 단부 모멘트 (N.mm)
M2 = 150e6  # 큰 단부 모멘트 (N.mm)
H = 500.0  # 단면 치수 (mm)


def main() -> None:
    """예제를 실행한다."""
    kds, conc_sec = column_section()
    conc = conc_sec.concrete_geometries[0].material

    gross = kds.get_transformed_gross_properties(
        elastic_modulus=conc.elastic_modulus
    )

    print(f"단면 : {H:.0f} x {H:.0f}, 8-D22, fck 27, SD400")
    print(
        f"하중 : Pu = {P_U / 1e3:.0f} kN, "
        f"M1 = {M1 / 1e6:.0f}, M2 = {M2 / 1e6:.0f} kN.m"
    )
    print()

    for l_u in [3000.0, 6000.0, 9000.0]:
        res = check_slenderness(
            p_u=P_U,
            m1=M1,
            m2=M2,
            k=1.0,
            l_u=l_u,
            h=H,
            e_c=conc.elastic_modulus,
            i_g=gross.ixx_c,
            braced=True,
            beta_dns=0.6,
        )

        print(f"### 비지지 길이 lu = {l_u:.0f} mm")
        res.print_results()

        # 확대된 모멘트로 단면 검토
        f_res, _, phi = kds.ultimate_bending_capacity(n_design=P_U)
        ratio = res.m_c / f_res.m_x

        print("-" * 64)
        print(
            f"설계 휨강도      phi*Mn = {f_res.m_x / 1e6:12.2f} kN.m "
            f"(phi = {phi:.3f})"
        )
        print(f"소요 / 강도             = {ratio:12.3f}")
        print(f"판정                    = {'만족' if ratio <= 1.0 else '불만족':>12}")
        print()


if __name__ == "__main__":
    main()
