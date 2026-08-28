"""예제 16 - 프리스트레스트 콘크리트.

프리스트레스 손실을 항목별로 계산하고, 허용응력과 설계 휨강도를 검토한다.
(KDS 14 20 62)

실행:
    python 16_PSC.py
"""

from __future__ import annotations

from concreteproperties import (
    PrestressedSection,
    SteelStrand,
    StrandHardening,
    add_bar_rectangular_array,
)
from sectionproperties.pre.library import rectangular_section

from concreteproperties_kds import KDS
from concreteproperties_kds.psc import (
    KDSPrestressed,
    PrestressLosses,
    allowable_concrete_stress_service,
    allowable_concrete_stress_transfer,
    allowable_tendon_stress,
    anchorage_set_loss,
    capacity_reduction_factor_psc,
    creep_loss,
    elastic_shortening_loss,
    friction_loss,
    relaxation_loss,
    shrinkage_loss,
    tendon_stress_bonded,
    tendon_stress_unbonded,
)

FPU = 1860.0
FPY = 0.9 * FPU
E_P = 195e3
FCK = 40.0
FCI = 30.0
N_STRAND = 4
A_STRAND = 138.7  # SWPC 7B 15.2 mm 1가닥
SPAN = 20000.0


def main() -> None:
    """예제를 실행한다."""
    kds = KDS()
    conc = kds.create_concrete_material(compressive_strength=FCK)

    width = 66

    # ------------------------------------------------------------------
    # 허용응력
    # ------------------------------------------------------------------
    print("=" * width)
    print("허용응력 (KDS 14 20 62 4.2)")
    print("=" * width)
    f_pj_allow = allowable_tendon_stress(fpu=FPU, fpy=FPY, stage="jacking")
    f_pa_allow = allowable_tendon_stress(fpu=FPU, fpy=FPY, stage="anchorage")
    print(f"긴장재 긴장 중       = {f_pj_allow:8.1f} MPa  (min(0.80fpu, 0.94fpy))")
    print(f"긴장재 정착 직후     = {f_pa_allow:8.1f} MPa  (0.70fpu)")

    c_t, t_t = allowable_concrete_stress_transfer(fci=FCI)
    print(f"콘크리트 도입 직후   = {c_t:8.1f} / {t_t:7.2f} MPa  (압축/인장)")

    c_s, t_s = allowable_concrete_stress_service(fck=FCK, crack_class="U")
    c_sus, _ = allowable_concrete_stress_service(fck=FCK, sustained=True)
    print(f"콘크리트 사용 전체   = {c_s:8.1f} / {t_s:7.2f} MPa  (비균열등급 U)")
    print(f"콘크리트 사용 지속   = {c_sus:8.1f} MPa")
    print()

    # ------------------------------------------------------------------
    # 프리스트레스 손실
    # ------------------------------------------------------------------
    f_pj = 0.75 * FPU  # 잭킹 응력
    a_ps = N_STRAND * A_STRAND
    p_pj = f_pj * a_ps

    _, friction_force = friction_loss(
        p_pj=p_pj, mu_p=0.20, alpha_px=0.15, k_wobble=6.6e-7, l_px=SPAN / 2
    )

    losses = PrestressLosses(
        f_pj=f_pj,
        friction=friction_force / a_ps,
        anchorage=anchorage_set_loss(slip=6.0, e_p=E_P, length=SPAN / 2),
        elastic=elastic_shortening_loss(
            f_cgp=8.0,
            e_p=E_P,
            e_ci=kds.create_concrete_material(
                compressive_strength=FCI
            ).elastic_modulus,
            post_tensioned=True,
            n_tendons=N_STRAND,
        ),
        creep=creep_loss(
            f_cgp=8.0, e_p=E_P, e_c=conc.elastic_modulus, creep_coefficient=2.0
        ),
        shrinkage=shrinkage_loss(e_p=E_P, eps_sh=300e-6),
        relaxation=relaxation_loss(f_pi=0.70 * FPU, fpy=FPY),
    )
    losses.print_results()
    print()

    # ------------------------------------------------------------------
    # 긴장재의 극한 응력
    # ------------------------------------------------------------------
    d_p = 680.0
    b = 400.0
    rho_p = a_ps / (b * d_p)

    f_ps_bonded = tendon_stress_bonded(
        fpu=FPU, fck=FCK, rho_p=rho_p, gamma_p=0.28, beta_1=0.80
    )
    f_ps_unbonded = tendon_stress_unbonded(
        f_pe=losses.f_pe,
        fck=FCK,
        rho_p=rho_p,
        fpy=FPY,
        span_depth_ratio=SPAN / 800.0,
    )

    print("=" * width)
    print("긴장재의 극한 응력 (KDS 14 20 62 4.1)")
    print("=" * width)
    print(f"긴장재비             rho_p = {rho_p:10.5f}")
    print(f"부착   긴장재        fps   = {f_ps_bonded:10.1f} MPa")
    print(f"비부착 긴장재        fps   = {f_ps_unbonded:10.1f} MPa")
    print(f"유효 프리스트레스    fpe   = {losses.f_pe:10.1f} MPa")
    print()

    # ------------------------------------------------------------------
    # 단면 해석
    # ------------------------------------------------------------------
    strand = SteelStrand(
        name="SWPC 7B 15.2mm",
        density=7.85e-6,
        stress_strain_profile=StrandHardening(
            yield_strength=FPY,
            elastic_modulus=E_P,
            fracture_strain=0.035,
            breaking_strength=FPU,
        ),
        colour="slategrey",
        prestress_stress=losses.f_pe,
    )

    geom = rectangular_section(d=800, b=400, material=conc)
    geom = add_bar_rectangular_array(
        geometry=geom,
        area=A_STRAND,
        material=strand,
        n_x=N_STRAND,
        x_s=80,
        anchor=(80, 120),
        n=8,
    )
    ps_sec = PrestressedSection(geom)

    kds_ps = KDSPrestressed(column_type="tie")
    kds_ps.assign_prestressed_section(ps_sec)

    f_res, u_res, phi = kds_ps.ultimate_bending_capacity(positive=True)
    eps_t = kds_ps.net_tensile_strain(theta=0, d_n=u_res.d_n)

    print("=" * width)
    print("설계 휨강도")
    print("=" * width)
    print(f"중립축 깊이          c     = {u_res.d_n:10.2f} mm")
    print(f"순인장변형률         et    = {eps_t:10.5f}")
    print(f"강도감소계수         phi   = {phi:10.3f}")
    print(f"공칭 휨강도          Mn    = {u_res.m_x / 1e6:10.2f} kN.m")
    print(f"설계 휨강도      phi*Mn    = {f_res.m_x / 1e6:10.2f} kN.m")
    print()
    print("강도감소계수 (KDS 14 20 10 표 4.2-1, 프리스트레스트 부재)")
    print(f"{'et':>10} {'phi':>8}")
    print("-" * width)
    for e in [0.001, 0.002, 0.003, 0.0035, 0.004, 0.005, 0.010]:
        print(f"{e:10.4f} {capacity_reduction_factor_psc(eps_t=e):8.3f}")


if __name__ == "__main__":
    main()
