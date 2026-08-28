"""예제 10 - 전단과 비틀림 설계.

400 x 600 보의 전단 검토와 스터럽 간격 산정, 비틀림 검토를 수행한다.
(KDS 14 20 22)

실행:
    python 10_전단비틀림.py
"""

from __future__ import annotations

from concreteproperties_kds.detailing import bar_area
from concreteproperties_kds.shear import (
    PHI_SHEAR,
    check_shear,
    check_torsion_section,
    concrete_shear_strength,
    cracking_torque,
    longitudinal_torsion_reinforcement,
    required_stirrup_spacing,
    torsion_negligible,
    torsional_strength,
)

FCK = 27.0
FY = 400.0
B_W = 400.0
H = 600.0
D = 550.0
COVER = 40.0


def main() -> None:
    """예제를 실행한다."""
    v_u = 320e3  # 계수 전단력 (N)
    a_v = 2 * bar_area("D13")  # D13 2가닥 스터럽

    print(f"단면 : b_w = {B_W:.0f} mm, h = {H:.0f} mm, d = {D:.0f} mm")
    print(f"재료 : fck = {FCK:.0f} MPa, fy = {FY:.0f} MPa")
    print(f"하중 : Vu = {v_u / 1e3:.1f} kN")
    print()

    # 필요한 스터럽 간격
    s_req = required_stirrup_spacing(
        v_u=v_u, fck=FCK, b_w=B_W, d=D, a_v=a_v, fyt=FY
    )
    s_use = 25.0 * int(s_req / 25.0)  # 25 mm 단위로 내림

    print(f"필요 스터럽 간격  s = {s_req:.1f} mm  ->  배치 s = {s_use:.0f} mm")
    print()

    res = check_shear(
        v_u=v_u, fck=FCK, b_w=B_W, d=D, a_v=a_v, s=s_use, fyt=FY
    )
    res.print_results()

    # 전단철근이 필요 없는 구간
    v_c = concrete_shear_strength(fck=FCK, b_w=B_W, d=D)
    print()
    print(
        f"전단철근 불필요 구간 : Vu <= phi*Vc/2 = "
        f"{0.5 * PHI_SHEAR * v_c / 1e3:.1f} kN"
    )
    print(f"최소 전단철근 구간   : Vu <= phi*Vc   = {PHI_SHEAR * v_c / 1e3:.1f} kN")

    # 비틀림 검토
    print()
    a_cp = B_W * H
    p_cp = 2 * (B_W + H)
    a_oh = (B_W - 2 * COVER) * (H - 2 * COVER)
    p_h = 2 * ((B_W - 2 * COVER) + (H - 2 * COVER))
    t_u = 30e6  # 계수 비틀림모멘트 (N.mm)

    t_cr = cracking_torque(fck=FCK, a_cp=a_cp, p_cp=p_cp)
    negligible = torsion_negligible(t_u=t_u, fck=FCK, a_cp=a_cp, p_cp=p_cp)

    width = 66
    print("=" * width)
    print("비틀림 검토 (KDS 14 20 22 4.4)")
    print("=" * width)
    print(f"계수 비틀림모멘트    Tu     = {t_u / 1e6:10.2f} kN.m")
    print(f"균열 비틀림모멘트    Tcr    = {t_cr / 1e6:10.2f} kN.m")
    print(f"무시 한계  phi*Tcr/4        = {PHI_SHEAR * t_cr / 4 / 1e6:10.2f} kN.m")
    print(f"비틀림 무시 가능            = {'예' if negligible else '아니오'}")

    if not negligible:
        a_t = bar_area("D13")
        t_n = torsional_strength(a_t=a_t, s=s_use, a_oh=a_oh, fyt=FY)
        a_l = longitudinal_torsion_reinforcement(
            a_t=a_t, s=s_use, p_h=p_h, fyt=FY, fy=FY
        )
        print("-" * width)
        print(f"공칭 비틀림강도      Tn     = {t_n / 1e6:10.2f} kN.m")
        print(f"설계 비틀림강도  phi*Tn     = {PHI_SHEAR * t_n / 1e6:10.2f} kN.m")
        verdict = "만족" if PHI_SHEAR * t_n >= t_u else "불만족"
        print(f"판정                        = {verdict:>10}")
        print(f"종방향 비틀림철근    Al     = {a_l:10.1f} mm^2")

    demand, capacity, ok = check_torsion_section(
        v_u=v_u, t_u=t_u, fck=FCK, b_w=B_W, d=D, a_oh=a_oh, p_h=p_h
    )
    print("-" * width)
    print(f"단면 크기 검토  소요응력      = {demand:10.3f} MPa")
    print(f"                한계응력      = {capacity:10.3f} MPa")
    print(f"                판정          = {'만족' if ok else '불만족':>10}")


if __name__ == "__main__":
    main()
