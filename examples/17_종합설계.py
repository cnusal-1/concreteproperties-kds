"""예제 17 - 보 종합 설계.

하중조합부터 휨·전단·사용성·상세·내구성까지 KDS 14 20 의 검토를 한 번에
수행한다. 실무의 설계 흐름을 그대로 따라간다.

실행:
    python 17_종합설계.py
"""

from __future__ import annotations

from concreteproperties import ConcreteSection
from sectionproperties.pre.library import concrete_rectangular_section

from concreteproperties_kds import KDS
from concreteproperties_kds.detailing import (
    bar_area,
    minimum_bar_spacing,
    minimum_cover,
    summarise_detailing,
)
from concreteproperties_kds.durability import check_durability
from concreteproperties_kds.kds import minimum_flexural_reinforcement
from concreteproperties_kds.loads import print_combinations, required_strength
from concreteproperties_kds.serviceability import (
    check_crack_control,
    check_deflection,
    minimum_thickness,
)
from concreteproperties_kds.shear import check_shear, required_stirrup_spacing

# 설계 조건
SPAN = 8000.0  # 경간 (mm)
B = 400.0  # 폭 (mm)
H = 700.0  # 높이 (mm)
FCK = 27.0
FY = 400.0
EXPOSURE = "EC3"  # 노출등급 (보통 습도, 옥내)
MAIN_BAR = "D25"
STIRRUP = "D13"
N_BOT = 5
N_TOP = 2


def banner(title: str) -> None:
    """구분선과 함께 제목을 출력한다.

    Args:
        title: 제목
    """
    print()
    print("#" * 72)
    print(f"# {title}")
    print("#" * 72)


def main() -> None:
    """예제를 실행한다."""
    # ------------------------------------------------------------------
    banner("1. 하중조합 (KDS 14 20 01)")
    # ------------------------------------------------------------------
    loads = {"D": 22.0, "L": 14.0, "S": 3.0}
    print_combinations(loads=loads)

    w_u, governing = required_strength(loads=loads)
    m_u = w_u * (SPAN / 1000.0) ** 2 / 8 * 1e6  # N.mm
    v_u = w_u * (SPAN / 1000.0) / 2 * 1e3  # N

    print()
    print(f"지배 조합 {governing.name} : wu = {w_u:.2f} kN/m")
    print(f"Mu = {m_u / 1e6:.2f} kN.m,  Vu = {v_u / 1e3:.2f} kN")

    # 사용하중 (처짐 검토용)
    m_sustained = loads["D"] * (SPAN / 1000.0) ** 2 / 8 * 1e6
    m_live = loads["L"] * (SPAN / 1000.0) ** 2 / 8 * 1e6

    # ------------------------------------------------------------------
    banner("2. 내구성과 피복두께 (KDS 14 20 40, KDS 14 20 50)")
    # ------------------------------------------------------------------
    cover_structural = minimum_cover(condition="옥내_보기둥", fck=FCK)
    dur = check_durability(
        exposure_class=EXPOSURE,
        fck=FCK,
        water_binder_ratio=0.48,
        cover=cover_structural,
    )
    dur.print_results()

    # 철근 중심까지의 피복
    d_stirrup = 12.7
    d_main = 25.4
    cover_to_centre = cover_structural + d_stirrup + d_main / 2
    d_eff = H - cover_to_centre

    print()
    print(f"구조 피복  cc      = {cover_structural:.1f} mm")
    print(f"철근 중심까지      = {cover_to_centre:.1f} mm")
    print(f"유효깊이   d       = {d_eff:.1f} mm")

    # ------------------------------------------------------------------
    banner("3. 단면과 재료 (KDS 14 20 10, KDS 14 20 20)")
    # ------------------------------------------------------------------
    kds = KDS(column_type="tie")
    conc = kds.create_concrete_material(compressive_strength=FCK)
    steel = kds.create_steel_material(yield_strength=FY)

    geom = concrete_rectangular_section(
        d=H,
        b=B,
        dia_top=15.9,
        area_top=bar_area("D16"),
        n_top=N_TOP,
        c_top=cover_to_centre,
        dia_bot=d_main,
        area_bot=bar_area(MAIN_BAR),
        n_bot=N_BOT,
        c_bot=cover_to_centre,
        n_circle=16,
        conc_mat=conc,
        steel_mat=steel,
    )
    conc_sec = ConcreteSection(geom)
    kds.assign_concrete_section(conc_sec)

    a_s = N_BOT * bar_area(MAIN_BAR)
    clear_spacing = (B - 2 * cover_structural - 2 * d_stirrup - N_BOT * d_main) / (
        N_BOT - 1
    )
    s_min = minimum_bar_spacing(bar=MAIN_BAR, member="보", aggregate_size=25)

    print(f"단면      {B:.0f} x {H:.0f} mm")
    print(f"인장철근  {N_BOT}-{MAIN_BAR} = {a_s:.1f} mm^2")
    print(f"압축철근  {N_TOP}-D16")
    print(f"콘크리트  {conc.name},  Ec = {conc.elastic_modulus:,.0f} MPa")
    print(f"철근      {steel.name}")
    print()
    print(f"철근 순간격        = {clear_spacing:.1f} mm  (최소 {s_min:.1f} mm) "
          f"{'만족' if clear_spacing >= s_min else '불만족'}")

    # ------------------------------------------------------------------
    banner("4. 휨 설계 (KDS 14 20 20)")
    # ------------------------------------------------------------------
    f_res, u_res, phi = kds.ultimate_bending_capacity(theta=0, n_design=0)
    eps_t = kds.net_tensile_strain(theta=0, d_n=u_res.d_n)

    print(f"중립축 깊이        c      = {u_res.d_n:10.2f} mm")
    print(f"순인장변형률       et     = {eps_t:10.5f}")
    print(f"단면 분류                 = {kds.section_classification(eps_t=eps_t):>10}")
    print(f"강도감소계수       phi    = {phi:10.3f}")
    print(f"공칭 휨강도        Mn     = {u_res.m_x / 1e6:10.2f} kN.m")
    print(f"설계 휨강도    phi*Mn     = {f_res.m_x / 1e6:10.2f} kN.m")
    print(f"소요 휨모멘트      Mu     = {m_u / 1e6:10.2f} kN.m")
    print(f"소요/강도                 = {m_u / f_res.m_x:10.3f}")
    print(f"판정                      = {'만족' if f_res.m_x >= m_u else '불만족':>10}")

    print()
    eps_t, eps_min, ok_duct = kds.check_flexural_ductility()
    a_s_min = minimum_flexural_reinforcement(fck=FCK, fy=FY, b_w=B, d=d_eff)
    print(f"최소허용변형률     et,min = {eps_min:10.5f}  "
          f"{'만족' if ok_duct else '불만족'}")
    print(f"최소철근량         As,min = {a_s_min:10.1f} mm^2  "
          f"{'만족' if a_s >= a_s_min else '불만족'}")

    # ------------------------------------------------------------------
    banner("5. 전단 설계 (KDS 14 20 22)")
    # ------------------------------------------------------------------
    a_v = 2 * bar_area(STIRRUP)
    s_req = required_stirrup_spacing(
        v_u=v_u, fck=FCK, b_w=B, d=d_eff, a_v=a_v, fyt=FY
    )
    s_use = min(25.0 * int(s_req / 25.0), 250.0)

    print(f"스터럽 {STIRRUP} 2가닥, 필요 간격 {s_req:.1f} mm -> 배치 {s_use:.0f} mm")
    print()
    shear = check_shear(
        v_u=v_u, fck=FCK, b_w=B, d=d_eff, a_v=a_v, s=s_use, fyt=FY
    )
    shear.print_results()

    # ------------------------------------------------------------------
    banner("6. 사용성 (KDS 14 20 30)")
    # ------------------------------------------------------------------
    h_min = minimum_thickness(span=SPAN, member="보", support="단순지지", fy=FY)
    verdict = "처짐 계산 생략 가능" if h_min <= H else "처짐 계산 필요"
    print(f"최소 두께  l/16 = {h_min:.1f} mm,  h = {H:.1f} mm  {verdict}")
    print()

    gross = kds.get_transformed_gross_properties(
        elastic_modulus=conc.elastic_modulus
    )
    cracked = kds.calculate_cracked_properties(theta=0)
    cracked.calculate_transformed_properties(elastic_modulus=conc.elastic_modulus)

    defl = check_deflection(
        span=SPAN,
        m_sustained=m_sustained,
        m_live=m_live,
        m_cr=cracked.m_cr,
        i_g=gross.ixx_c,
        i_cr=cracked.ixx_c_cr,
        e_c=conc.elastic_modulus,
        rho_prime=N_TOP * bar_area("D16") / (B * d_eff),
    )
    defl.print_results()

    print()
    bar_spacing = (B - 2 * cover_structural - 2 * d_stirrup - d_main) / (N_BOT - 1)
    fs, s_max, ok_crack = check_crack_control(
        bar_spacing=bar_spacing, fy=FY, c_c=cover_structural + d_stirrup
    )
    print(f"균열 제어  fs = {fs:.1f} MPa,  s,max = {s_max:.1f} mm,  "
          f"배치 s = {bar_spacing:.1f} mm  {'만족' if ok_crack else '불만족'}")

    # ------------------------------------------------------------------
    banner("7. 정착·이음 (KDS 14 20 52)")
    # ------------------------------------------------------------------
    summarise_detailing(bar=MAIN_BAR, fy=FY, fck=FCK).print_results()

    # ------------------------------------------------------------------
    banner("설계 요약")
    # ------------------------------------------------------------------
    items = [
        ("휨강도", f_res.m_x >= m_u),
        ("연성 (최소허용변형률)", ok_duct),
        ("최소 휨철근량", a_s >= a_s_min),
        ("전단강도", shear.ok),
        ("처짐", defl.ok),
        ("균열 제어", ok_crack),
        ("내구성", dur.ok),
        ("철근 순간격", clear_spacing >= s_min),
    ]

    for name, ok in items:
        print(f"  {name:<24} {'만족' if ok else '불만족'}")

    print()
    print(f"  {'종합':<24} {'만족' if all(ok for _, ok in items) else '불만족'}")


if __name__ == "__main__":
    main()
