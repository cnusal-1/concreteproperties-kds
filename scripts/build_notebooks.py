"""`docs/examples/*.ipynb` 를 생성한다.

실행:
    python scripts/build_notebooks.py           # 생성만
    python scripts/build_notebooks.py --run     # 생성 후 실행하여 출력 저장
"""

from __future__ import annotations

import sys

from nbbuild import code, execute, md, write

# 모든 노트북 앞머리에 붙는 준비 코드
SETUP = """
%matplotlib inline

import matplotlib.pyplot as plt
import numpy as np

# 한글 글꼴이 없는 환경에서도 그림이 깨지지 않도록 축 라벨은 ASCII 로 둔다
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 96
"""

COMMON_SECTIONS = """
from concreteproperties import ConcreteSection
from sectionproperties.pre.library import concrete_rectangular_section

from concreteproperties_kds import KDS


def beam_section(fck=27, fy=400):
    \"\"\"400 x 600 보 단면 (상부 2-D16, 하부 4-D22, 피복 50 mm).\"\"\"
    kds = KDS(column_type="tie")
    conc = kds.create_concrete_material(compressive_strength=fck)
    steel = kds.create_steel_material(yield_strength=fy)

    geom = concrete_rectangular_section(
        d=600, b=400,
        dia_top=16, area_top=198.6, n_top=2, c_top=50,
        dia_bot=22, area_bot=387.1, n_bot=4, c_bot=50,
        n_circle=16, conc_mat=conc, steel_mat=steel,
    )
    conc_sec = ConcreteSection(geom)
    kds.assign_concrete_section(conc_sec)
    return kds, conc_sec


def column_section(fck=27, fy=400, column_type="tie"):
    \"\"\"500 x 500 기둥 단면 (8-D22, 피복 50 mm).\"\"\"
    kds = KDS(column_type=column_type)
    conc = kds.create_concrete_material(compressive_strength=fck)
    steel = kds.create_steel_material(yield_strength=fy)

    geom = concrete_rectangular_section(
        d=500, b=500,
        dia_top=22, area_top=387.1, n_top=3, c_top=50,
        dia_bot=22, area_bot=387.1, n_bot=3, c_bot=50,
        dia_side=22, area_side=387.1, n_side=1, c_side=50,
        n_circle=16, conc_mat=conc, steel_mat=steel,
    )
    conc_sec = ConcreteSection(geom)
    kds.assign_concrete_section(conc_sec)
    return kds, conc_sec
"""


def nb_01_materials():
    """예제 01 - KDS 재료 특성."""
    return write(
        "01_materials",
        [
            md("""
        # 01 · 재료 — KDS 14 20 재료 특성

        KDS 14 20 이 규정하는 콘크리트·철근의 재료 상수를 확인하고, 응력-변형률
        관계를 그린다.

        | 항목 | 식 | 조문 |
        |---|---|---|
        | 콘크리트 탄성계수 | $E_c = 8500\\sqrt[3]{f_{cm}}$ | KDS 14 20 10 4.3.3, 식 (4.3-2) |
        | 평균압축강도 | $f_{cm} = f_{ck} + \\Delta f$ | KDS 14 20 10 식 (4.3-3) |
        | 등가직사각형 응력블록 | $\\eta(0.85f_{ck})$, $a = \\beta_1 c$ | KDS 14 20 20 4.1.1(8), 표 4.1-2 |
        | 파괴계수 | $f_r = 0.63\\lambda\\sqrt{f_{ck}}$ | KDS 14 20 30 4.2.1 |
        | 철근 탄성계수 | $E_s = 200{,}000$ MPa | KDS 14 20 10 4.3.3(2), 식 (4.3-5) |
        """),
            code(SETUP),
            md("""
        ## 재료 상수 표

        `stress_block_parameters` 는 KDS 14 20 20 표 4.1-2 의 값을 반환한다.
        표에 없는 강도는 선형보간한다.
        """),
            code("""
        from concreteproperties_kds import (
            elastic_modulus,
            modulus_of_rupture,
            stress_block_parameters,
        )

        print(f"{'fck':>6} {'Ec':>10} {'eps_cu':>9} {'eta':>7} {'beta_1':>8}"
              f" {'0.85*eta*fck':>13} {'fr':>7}")
        print("-" * 66)

        for fck in [18, 21, 24, 27, 30, 35, 40, 50, 60, 70, 80, 90]:
            eps_cu, eta, beta_1 = stress_block_parameters(fck=fck)
            print(
                f"{fck:6.0f} {elastic_modulus(fck=fck):10.0f} {eps_cu:9.4f}"
                f" {eta:7.2f} {beta_1:8.2f} {0.85 * eta * fck:13.2f}"
                f" {modulus_of_rupture(fck=fck):7.2f}"
            )
        """),
            md("""
        고강도로 갈수록 $\\varepsilon_{cu}$ 와 $\\eta$, $\\beta_1$ 이 모두 줄어든다.
        콘크리트가 취성적이 되는 것을 반영한 것이다.
        """),
            code("""
        fck = np.linspace(18, 90, 200)
        eps_cu = [stress_block_parameters(f)[0] for f in fck]
        eta = [stress_block_parameters(f)[1] for f in fck]
        beta_1 = [stress_block_parameters(f)[2] for f in fck]

        fig, axes = plt.subplots(1, 3, figsize=(11, 3.2))
        for ax, y, name in zip(
            axes, [eps_cu, eta, beta_1], ["eps_cu", "eta", "beta_1"], strict=True
        ):
            ax.plot(fck, y)
            ax.set_xlabel("fck (MPa)")
            ax.set_ylabel(name)
            ax.grid(alpha=0.3)
        fig.suptitle("KDS 14 20 20 Table 4.1-2")
        fig.tight_layout()
        """),
            md("""
        ## 변형률한계 (KDS 14 20 20 4.1.2)

        - 압축지배변형률한계 $\\varepsilon_y = f_y / E_s$ — 4.1.2(3)
        - 인장지배변형률한계 0.005 ($f_y \\le 400$) 또는 $2.5\\varepsilon_y$ — 4.1.2(4)
        - 휨부재 최소허용변형률 0.004 ($f_y \\le 400$) 또는 $2.0\\varepsilon_y$ — 4.1.2(5)
        """),
            code("""
        from concreteproperties_kds import (
            compression_controlled_strain_limit,
            minimum_net_tensile_strain,
            tension_controlled_strain_limit,
        )

        print(f"{'강종':>8} {'fy':>6} {'eps_y':>9} {'eps_t,tl':>10} {'eps_t,min':>11}")
        print("-" * 48)
        for fy in [300, 400, 500, 600]:
            print(
                f"{'SD' + str(fy):>8} {fy:6.0f}"
                f" {compression_controlled_strain_limit(fy=fy):9.4f}"
                f" {tension_controlled_strain_limit(fy=fy):10.5f}"
                f" {minimum_net_tensile_strain(fy=fy):11.5f}"
            )
        """),
            md("""
        ## 재료 객체와 응력-변형률 관계

        `KDS.create_concrete_material` 은 사용(service)·극한(ultimate) 두 관계를
        모두 갖춘 콘크리트 객체를 만든다.
        """),
            code("""
        from concreteproperties_kds import KDS

        kds = KDS()
        conc = kds.create_concrete_material(compressive_strength=27)
        steel = kds.create_steel_material(yield_strength=400)

        print(conc.name)
        print(f"  Ec = {conc.elastic_modulus:,.0f} MPa")
        print(f"  fr = {conc.flexural_tensile_strength:.3f} MPa")
        print(f"  단위질량 = {conc.density * 1e9:,.0f} kg/m^3")
        print(steel.name)
        print(f"  Es = {steel.elastic_modulus:,.0f} MPa")
        """),
            code("""
        fig, axes = plt.subplots(1, 3, figsize=(12, 3.4))

        conc.stress_strain_profile.plot_stress_strain(
            ax=axes[0], render=False, title="Concrete - service"
        )
        conc.ultimate_stress_strain_profile.plot_stress_strain(
            ax=axes[1], render=False, title="Concrete - ultimate"
        )
        steel.stress_strain_profile.plot_stress_strain(
            ax=axes[2], render=False, title="Steel SD400"
        )
        fig.tight_layout()
        """),
            md("""
        극한 관계의 압축응력이 $\\eta(0.85 f_{ck}) = 1.0 \\times 0.85 \\times 27
        = 22.95$ MPa 로 일정한 것을 볼 수 있다. 응력블록이 시작되는 변형률은
        $\\varepsilon_{cu}(1-\\beta_1) = 0.0033 \\times 0.2 = 0.00066$ 이다.
        """),
        ],
    )


def nb_02_area_properties():
    """예제 02 - 단면 제원."""
    return write(
        "02_area_properties",
        [
            md("""
        # 02 · 단면 제원 — 총단면과 환산단면

        `ConcreteSection` 객체를 만들면 총단면 제원이 자동으로 계산된다.
        원 문서의 `area_properties.ipynb` 에 대응한다.
        """),
            code(SETUP),
            code(COMMON_SECTIONS),
            code("""
        kds, conc_sec = beam_section()
        conc_sec.plot_section()
        """),
            md("""
        ## 총단면 제원

        `GrossProperties` 의 단면2차모멘트는 탄성계수가 곱해진 **휨강성** ($EI$)
        이다. 순수한 $I$ 가 필요하면 환산단면 제원을 쓴다.
        """),
            code("""
        gross = kds.get_gross_properties()
        gross.print_results()
        """),
            md("""
        ## 콘크리트 환산단면 제원
        """),
            code("""
        conc = conc_sec.concrete_geometries[0].material

        transformed = kds.get_transformed_gross_properties(
            elastic_modulus=conc.elastic_modulus
        )
        transformed.print_results()
        """),
            code("""
        print(f"환산 도심축 단면2차모멘트  Ixx_c = {transformed.ixx_c:,.0f} mm^4")
        print(f"총단면 (400x600) 기준       bh^3/12 = {400 * 600 ** 3 / 12:,.0f} mm^4")
        print(f"비                                  = "
              f"{transformed.ixx_c / (400 * 600 ** 3 / 12):.4f}")
        """),
            md("""
        철근이 환산되어 들어오므로 환산단면의 $I$ 가 콘크리트만의 $bh^3/12$ 보다
        크다.
        """),
        ],
    )


def nb_03_cracked_properties():
    """예제 03 - 균열단면."""
    return write(
        "03_cracked_properties",
        [
            md("""
        # 03 · 균열단면 — 균열모멘트와 유효단면2차모멘트

        원 문서의 `cracked_properties.ipynb` 에 대응한다.

        | 항목 | 식 | 조문 |
        |---|---|---|
        | 파괴계수 | $f_r = 0.63\\lambda\\sqrt{f_{ck}}$ | KDS 14 20 30 4.2.1 |
        | 균열모멘트 | $M_{cr} = f_r I_g / y_t$ | KDS 14 20 30 식 (4.2-2) |
        | 유효단면2차모멘트 | Branson 식 | KDS 14 20 30 식 (4.2-1) |
        """),
            code(SETUP),
            code(COMMON_SECTIONS),
            code("""
        kds, conc_sec = beam_section()
        conc = conc_sec.concrete_geometries[0].material

        gross = kds.get_transformed_gross_properties(
            elastic_modulus=conc.elastic_modulus
        )

        cracked = kds.calculate_cracked_properties(theta=0)
        cracked.calculate_transformed_properties(
            elastic_modulus=conc.elastic_modulus
        )

        print(f"파괴계수           fr   = {conc.flexural_tensile_strength:.3f} MPa")
        print(f"총단면 2차모멘트   Ig   = {gross.ixx_c:,.0f} mm^4")
        print(f"균열모멘트         Mcr  = {cracked.m_cr / 1e6:.2f} kN.m")
        print(f"중립축 깊이        d_nc = {cracked.d_nc:.2f} mm")
        print(f"균열단면 2차모멘트 Icr  = {cracked.ixx_c_cr:,.0f} mm^4")
        print(f"Icr / Ig                = {cracked.ixx_c_cr / gross.ixx_c:.3f}")
        """),
            md("""
        ## 유효단면2차모멘트 (Branson 식)

        $$I_e = \\left(\\frac{M_{cr}}{M_a}\\right)^3 I_g
        + \\left[1 - \\left(\\frac{M_{cr}}{M_a}\\right)^3\\right] I_{cr} \\le I_g$$

        KDS 14 20 30 식 (4.2-1)
        """),
            code("""
        from concreteproperties_kds import effective_moment_of_inertia

        ratios = np.linspace(1.0, 4.0, 100)
        i_e = [
            effective_moment_of_inertia(
                m_a=r * cracked.m_cr, m_cr=cracked.m_cr,
                i_g=gross.ixx_c, i_cr=cracked.ixx_c_cr,
            )
            for r in ratios
        ]

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(ratios, np.array(i_e) / gross.ixx_c, label="Ie / Ig")
        ax.axhline(
            cracked.ixx_c_cr / gross.ixx_c, ls="--", color="grey", label="Icr / Ig"
        )
        ax.set_xlabel("Ma / Mcr")
        ax.set_ylabel("Ie / Ig")
        ax.set_title("Effective moment of inertia (Branson)")
        ax.legend()
        ax.grid(alpha=0.3)
        """),
            md("""
        모멘트가 커질수록 $I_e$ 가 $I_{cr}$ 로 수렴한다.

        ## 균열단면 응력
        """),
            code("""
        stress = kds.calculate_cracked_stress(
            cracked_results=cracked, m=1.5 * cracked.m_cr
        )
        stress.plot_stress()
        """),
        ],
    )


def nb_04_ultimate_bending():
    """예제 04 - 설계 휨강도."""
    return write(
        "04_ultimate_bending",
        [
            md("""
        # 04 · 설계 휨강도 — 등가직사각형 응력블록과 강도감소계수

        원 문서의 `ultimate_bending.ipynb` 에 대응한다.

        | 항목 | 식 | 조문 |
        |---|---|---|
        | 등가직사각형 응력블록 | $\\eta(0.85f_{ck})$, $a = \\beta_1 c$ | KDS 14 20 20 4.1.1(8) |
        | 순인장변형률 | $\\varepsilon_t = \\varepsilon_{cu}(d_t-c)/c$ | KDS 14 20 20 4.1.2 |
        | 강도감소계수 | 0.65~0.85 선형보간 | KDS 14 20 10 4.3.3(2) |
        | 최소허용변형률 | 0.004 또는 $2.0\\varepsilon_y$ | KDS 14 20 20 4.1.2(5) |
        | 최소 철근량 | $\\phi M_n \\ge 1.2M_{cr}$ | KDS 14 20 20 4.2.2 |
        """),
            code(SETUP),
            code(COMMON_SECTIONS),
            code("""
        kds, conc_sec = beam_section()

        f_res, u_res, phi = kds.ultimate_bending_capacity(theta=0, n_design=0)
        eps_t = kds.net_tensile_strain(theta=0, d_n=u_res.d_n)

        print(f"중립축 깊이       c      = {u_res.d_n:.2f} mm")
        print(f"응력블록 깊이     a      = {u_res.d_n * 0.80:.2f} mm")
        print(f"순인장변형률      et     = {eps_t:.5f}")
        print(f"단면 분류                = {kds.section_classification(eps_t=eps_t)}")
        print(f"강도감소계수      phi    = {phi:.3f}")
        print(f"공칭 휨강도       Mn     = {u_res.m_x / 1e6:.2f} kN.m")
        print(f"설계 휨강도   phi*Mn     = {f_res.m_x / 1e6:.2f} kN.m")
        """),
            md("""
        ## 극한상태 응력 분포
        """),
            code("""
        kds.calculate_ultimate_stress(ultimate_results=u_res).plot_stress()
        """),
            md("""
        콘크리트 압축응력이 $\\eta(0.85f_{ck}) = 22.95$ MPa, 인장철근 응력이
        $-f_y = -400$ MPa 로 나타난다.

        ## 강도감소계수 곡선 (KDS 14 20 10 4.3.3(2))

        $$\\phi = \\phi_c + (0.85 - \\phi_c)
        \\frac{\\varepsilon_t - \\varepsilon_y}{\\varepsilon_{t,tl}-\\varepsilon_y}$$
        """),
            code("""
        eps = np.linspace(0.0, 0.009, 300)
        phi_tie = [kds.capacity_reduction_factor(eps_t=float(e)) for e in eps]

        kds_spiral, _ = column_section(column_type="spiral")
        phi_spiral = [
            kds_spiral.capacity_reduction_factor(eps_t=float(e)) for e in eps
        ]

        fig, ax = plt.subplots(figsize=(6.5, 4))
        ax.plot(eps, phi_tie, label="tie (0.65)")
        ax.plot(eps, phi_spiral, label="spiral (0.70)")
        ax.axvline(kds.eps_y, ls=":", color="grey")
        ax.axvline(kds.eps_tl, ls=":", color="grey")
        ax.text(kds.eps_y, 0.62, " eps_y", fontsize=8)
        ax.text(kds.eps_tl, 0.62, " eps_t,tl", fontsize=8)
        ax.set_xlabel("net tensile strain, eps_t")
        ax.set_ylabel("phi")
        ax.set_title("Strength reduction factor (SD400)")
        ax.legend()
        ax.grid(alpha=0.3)
        """),
            md("""
        ## 연성과 최소 철근량 검토
        """),
            code("""
        eps_t, eps_min, ok_duct = kds.check_flexural_ductility()
        print(f"최소허용변형률  et,min = {eps_min:.5f}   (KDS 14 20 20 4.1.2(5))")
        print(f"순인장변형률    et     = {eps_t:.5f}")
        print(f"판정                   = {'만족' if ok_duct else '불만족'}")
        print()

        phi_m_n, m_cr, m_req, ok_min = kds.check_minimum_flexural_reinforcement()
        print(f"균열휨모멘트    Mcr    = {m_cr / 1e6:.2f} kN.m")
        print(f"요구 강도    1.2*Mcr   = {m_req / 1e6:.2f} kN.m"
              f"   (KDS 14 20 20 4.2.2)")
        print(f"설계 휨강도  phi*Mn    = {phi_m_n / 1e6:.2f} kN.m")
        print(f"판정                   = {'만족' if ok_min else '불만족'}")
        """),
            md("""
        ## 철근비에 따른 거동

        철근량을 늘리면 중립축이 깊어지고 순인장변형률이 줄어, 결국 강도감소계수가
        떨어진다.
        """),
            code("""
        from concreteproperties import ConcreteSection, add_bar_rectangular_array
        from sectionproperties.pre.library import rectangular_section

        rows = []
        for n_bar in [2, 3, 4, 5, 6, 7, 8]:
            k = KDS()
            c = k.create_concrete_material(compressive_strength=27)
            s = k.create_steel_material(yield_strength=400)
            g = rectangular_section(d=600, b=400, material=c)
            g = add_bar_rectangular_array(
                geometry=g, area=387.1, material=s,
                n_x=n_bar, x_s=(400 - 2 * 60) / (n_bar - 1),
                anchor=(60, 60), n=16,
            )
            k.assign_concrete_section(ConcreteSection(g))
            f, u, p = k.ultimate_bending_capacity()
            e = k.net_tensile_strain(theta=0, d_n=u.d_n)
            rows.append((n_bar * 387.1, e, p, u.m_x / 1e6, f.m_x / 1e6))

        print(f"{'As':>8} {'et':>9} {'phi':>7} {'Mn':>9} {'phiMn':>9}")
        print("-" * 46)
        for a_s, e, p, mn, fmn in rows:
            print(f"{a_s:8.0f} {e:9.5f} {p:7.3f} {mn:9.1f} {fmn:9.1f}")
        """),
            code("""
        a_s, e, p, mn, fmn = map(np.array, zip(*rows, strict=True))

        fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
        axes[0].plot(a_s, e, "o-")
        axes[0].axhline(0.005, ls="--", color="grey")
        axes[0].axhline(0.002, ls=":", color="grey")
        axes[0].set_xlabel("As (mm^2)")
        axes[0].set_ylabel("eps_t")
        axes[0].set_title("Net tensile strain")
        axes[0].grid(alpha=0.3)

        axes[1].plot(a_s, mn, "o-", label="Mn")
        axes[1].plot(a_s, fmn, "s-", label="phi*Mn")
        axes[1].set_xlabel("As (mm^2)")
        axes[1].set_ylabel("moment (kN.m)")
        axes[1].set_title("Flexural strength")
        axes[1].legend()
        axes[1].grid(alpha=0.3)
        fig.tight_layout()
        """),
            md("""
        철근을 계속 늘려도 $\\phi M_n$ 의 증가가 둔해진다. 순인장변형률이
        인장지배한계 아래로 내려가 $\\phi$ 가 함께 떨어지기 때문이다. KDS 가
        최소허용변형률(0.004)을 두는 이유이기도 하다.
        """),
        ],
    )


def nb_05_moment_interaction():
    """예제 05 - P-M 상관도."""
    return write(
        "05_moment_interaction",
        [
            md("""
        # 05 · P-M 상관도 — 공칭강도와 설계강도

        원 문서의 `moment_interaction.ipynb` 에 대응한다.

        | 항목 | 식 | 조문 |
        |---|---|---|
        | 순수압축 강도 | $P_o = 0.85f_{ck}(A_g-A_{st}) + f_yA_{st}$ | KDS 14 20 20 4.1.2(7) |
        | 최대 설계 축강도 | $0.80\\phi P_o$ (띠철근), $0.85\\phi P_o$ (나선철근) | KDS 14 20 20 식 (4.1-16), (4.1-17) |
        | 강도감소계수 | $\\varepsilon_t$ 에 따라 0.65~0.85 | KDS 14 20 10 4.3.3(2) |
        """),
            code(SETUP),
            code(COMMON_SECTIONS),
            code("""
        kds, conc_sec = column_section(column_type="tie")
        conc_sec.plot_section()
        """),
            code("""
        n_max_nom, n_max_des = kds.max_axial_strength()

        print(f"공칭 축강도       Po         = {kds.squash_load / 1e3:10,.1f} kN")
        print(f"최대 공칭 축강도  0.80*Po    = {n_max_nom / 1e3:10,.1f} kN")
        print(f"최대 설계 축강도  phi*Pn,max = {n_max_des / 1e3:10,.1f} kN")
        print(f"공칭 인장강도     Pnt        = {kds.tensile_load / 1e3:10,.1f} kN")
        """),
            md("""
        ## 상관도 생성

        `moment_interaction_diagram` 은 (설계 상관도, 공칭 상관도, phi 목록) 을
        반환한다.
        """),
            code("""
        f_mi, mi, phis = kds.moment_interaction_diagram(
            n_points=24, progress_bar=False
        )

        print(f"{'Nn(kN)':>10} {'Mn(kNm)':>10} {'et':>10} {'분류':>10}"
              f" {'phi':>7} {'phiN(kN)':>10} {'phiM(kNm)':>11}")
        print("-" * 76)
        for r_u, r_f, p in zip(mi.results, f_mi.results, phis, strict=True):
            e = kds.net_tensile_strain(theta=0, d_n=r_u.d_n)
            e_str = f"{'inf':>10}" if e == float("inf") else f"{e:10.5f}"
            print(
                f"{r_u.n / 1e3:10.1f} {r_u.m_x / 1e6:10.1f} {e_str}"
                f" {kds.section_classification(eps_t=e):>10} {p:7.3f}"
                f" {r_f.n / 1e3:10.1f} {r_f.m_x / 1e6:11.1f}"
            )
        """),
            code("""
        from concreteproperties.results import MomentInteractionResults

        fig, ax = plt.subplots(figsize=(6.5, 5))
        MomentInteractionResults.plot_multiple_diagrams(
            [mi, f_mi], ["nominal (Mn, Pn)", "design (phi*Mn, phi*Pn)"],
            fmt="-", ax=ax, render=False,
        )
        ax.axhline(n_max_des / 1e3 * 1e3, ls="--", color="grey", lw=0.8)
        ax.set_title("P-M interaction diagram (KDS 14 20)")
        ax.grid(alpha=0.3)
        """),
            md("""
        설계 상관도가 공칭 상관도 안쪽에 있고, 압축측이 최대 설계 축강도에서
        절단된다. 두 곡선의 간격이 일정하지 않은 것은 $\\phi$ 가 축력에 따라
        0.65 에서 0.85 까지 변하기 때문이다.

        ## 축력에 따른 강도감소계수
        """),
            code("""
        n_list = np.array([r.n for r in mi.results]) / 1e3
        fig, ax = plt.subplots(figsize=(6.5, 4))
        ax.plot(n_list, phis, "o-")
        ax.set_xlabel("nominal axial force, Pn (kN)")
        ax.set_ylabel("phi")
        ax.set_title("Strength reduction factor along the diagram")
        ax.grid(alpha=0.3)
        """),
            md("""
        ## 설계 축력별 설계 휨강도
        """),
            code("""
        print(f"{'Nd(kN)':>10} {'phi':>8} {'et':>10} {'분류':>10} {'phiMn(kNm)':>12}")
        print("-" * 56)
        for n_d in [-800, -400, 0, 400, 800, 1200, 1600, 2000, 2800, 3400]:
            f_res, u_res, phi = kds.ultimate_bending_capacity(n_design=n_d * 1e3)
            e = kds.net_tensile_strain(theta=0, d_n=u_res.d_n)
            e_str = f"{'inf':>10}" if e == float("inf") else f"{e:10.5f}"
            print(
                f"{n_d:10.0f} {phi:8.3f} {e_str}"
                f" {kds.section_classification(eps_t=e):>10}"
                f" {f_res.m_x / 1e6:12.1f}"
            )
        """),
            md("""
        ## 띠철근과 나선철근 비교

        나선철근 기둥은 압축지배단면의 $\\phi$ 가 0.70 이고 최대 축강도 저감계수도
        0.85 라 상관도가 바깥쪽에 놓인다.
        """),
            code("""
        kds_s, _ = column_section(column_type="spiral")
        f_mi_s, _, _ = kds_s.moment_interaction_diagram(
            n_points=24, progress_bar=False
        )

        fig, ax = plt.subplots(figsize=(6.5, 5))
        MomentInteractionResults.plot_multiple_diagrams(
            [f_mi, f_mi_s], ["tie", "spiral"], fmt="-", ax=ax, render=False
        )
        ax.set_title("Design diagram: tie vs spiral")
        ax.grid(alpha=0.3)
        """),
            md("""
        ## 설계 단면력 판정
        """),
            code("""
        for n_d, m_d in [(1500e3, 300e6), (1500e3, 450e6), (3000e3, 200e6)]:
            inside = f_mi.point_in_diagram(n=n_d, m=m_d)
            print(f"Nd = {n_d / 1e3:7.0f} kN, Md = {m_d / 1e6:6.0f} kN.m"
                  f"  ->  {'안전' if inside else '불안전'}")
        """),
        ],
    )


def nb_06_biaxial_bending():
    """예제 06 - 2축 휨 상관도."""
    return write(
        "06_biaxial_bending",
        [
            md("""
        # 06 · 2축 휨 상관도

        원 문서의 `biaxial_bending.ipynb` 에 대응한다. 계수 축력이 주어졌을 때
        중립축 각도를 한 바퀴 돌리며 각 방향의 설계 휨강도를 구한다.

        강도감소계수는 방향마다 달라진다. 같은 축력이라도 중립축 방향에 따라
        최외단 인장철근의 순인장변형률이 달라지기 때문이다
        (KDS 14 20 10 4.3.3(2)).
        """),
            code(SETUP),
            code(COMMON_SECTIONS),
            code("""
        kds, _ = column_section()

        n_design = 1200e3
        f_bb, phis = kds.biaxial_bending_diagram(
            n_design=n_design, n_points=32, progress_bar=False
        )

        m_x = np.array([r.m_x for r in f_bb.results]) / 1e6
        m_y = np.array([r.m_y for r in f_bb.results]) / 1e6

        print(f"Nd = {n_design / 1e3:,.0f} kN")
        print(f"phi 범위 : {min(phis):.3f} ~ {max(phis):.3f}")
        print(f"1축 휨강도 phi*Mnx = {np.max(np.abs(m_x)):.1f} kN.m")
        print(f"1축 휨강도 phi*Mny = {np.max(np.abs(m_y)):.1f} kN.m")
        """),
            code("""
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))

        axes[0].plot(m_x, m_y, "-o", ms=3)
        axes[0].set_xlabel("phi*Mx (kN.m)")
        axes[0].set_ylabel("phi*My (kN.m)")
        axes[0].set_title(f"Biaxial bending, Nd = {n_design / 1e3:,.0f} kN")
        axes[0].set_aspect("equal")
        axes[0].grid(alpha=0.3)

        theta = np.degrees([r.theta for r in f_bb.results])
        axes[1].plot(theta, phis, "-o", ms=3)
        axes[1].set_xlabel("theta (deg)")
        axes[1].set_ylabel("phi")
        axes[1].set_title("Strength reduction factor by direction")
        axes[1].grid(alpha=0.3)
        fig.tight_layout()
        """),
            md("""
        정사각형 대칭 단면이라 상관면이 네 방향으로 대칭이다. 45° 방향에서 강도가
        가장 작고, $\\phi$ 도 가장 낮다.

        ## 축력에 따른 상관면 변화
        """),
            code("""
        fig, ax = plt.subplots(figsize=(6, 5.4))

        for n_d in [0, 800e3, 1600e3, 2400e3]:
            bb, _ = kds.biaxial_bending_diagram(
                n_design=n_d, n_points=24, progress_bar=False
            )
            ax.plot(
                np.array([r.m_x for r in bb.results]) / 1e6,
                np.array([r.m_y for r in bb.results]) / 1e6,
                label=f"Nd = {n_d / 1e3:,.0f} kN",
            )

        ax.set_xlabel("phi*Mx (kN.m)")
        ax.set_ylabel("phi*My (kN.m)")
        ax.set_title("Biaxial bending diagrams")
        ax.set_aspect("equal")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        """),
            md("""
        축력이 균형점 부근일 때 상관면이 가장 크다.
        """),
        ],
    )


def nb_07_moment_curvature():
    """예제 07 - 모멘트-곡률."""
    return write(
        "07_moment_curvature",
        [
            md("""
        # 07 · 모멘트-곡률 해석

        원 문서의 `moment_curvature.ipynb` 에 대응한다.

        모멘트-곡률 해석은 **사용** 응력-변형률 관계를 쓰고, 실제 거동을 보는
        해석이므로 **강도감소계수를 적용하지 않는다**.
        """),
            code(SETUP),
            code(COMMON_SECTIONS),
            code("""
        kds, conc_sec = beam_section()

        mk_res = kds.moment_curvature_analysis(
            theta=0, kappa_inc=1e-7, progress_bar=False
        )

        kappa = np.array(mk_res.kappa)
        moment = np.array(mk_res.m_xy) / 1e6

        cracked = kds.calculate_cracked_properties(theta=0)
        _, u_res, _ = kds.ultimate_bending_capacity()

        print(f"해석 점의 수                 = {len(kappa)}")
        print(f"균열모멘트         Mcr       = {cracked.m_cr / 1e6:.2f} kN.m")
        print(f"최대 모멘트 (해석) Mmax      = {moment.max():.2f} kN.m")
        print(f"극한 휨강도        Mn        = {u_res.m_x / 1e6:.2f} kN.m")
        print(f"최대 곡률          kappa_max = {kappa.max():.3e} 1/mm")
        """),
            code("""
        fig, ax = plt.subplots(figsize=(6.5, 4.4))
        ax.plot(kappa * 1e6, moment, "-")
        ax.axhline(
            cracked.m_cr / 1e6, ls="--", color="tab:orange", lw=1,
            label=f"Mcr = {cracked.m_cr / 1e6:.1f}",
        )
        ax.axhline(
            u_res.m_x / 1e6, ls=":", color="tab:green", lw=1,
            label=f"Mn (ultimate) = {u_res.m_x / 1e6:.1f}",
        )
        ax.set_xlabel("curvature, kappa (1e-6 /mm)")
        ax.set_ylabel("moment (kN.m)")
        ax.set_title("Moment-curvature")
        ax.legend()
        ax.grid(alpha=0.3)
        """),
            md("""
        사용 관계로 계산한 최대 모멘트가 등가직사각형 응력블록으로 계산한 극한
        휨강도와 0.1 % 이내로 만난다. 서로 다른 두 응력-변형률 관계가 같은 답에
        수렴하는 것이다.

        ## 철근량에 따른 연성
        """),
            code("""
        from concreteproperties import ConcreteSection, add_bar_rectangular_array
        from concreteproperties.results import MomentCurvatureResults
        from sectionproperties.pre.library import rectangular_section

        results = []
        labels = []
        for n_bar in [3, 5, 8]:
            k = KDS()
            c = k.create_concrete_material(compressive_strength=27)
            s = k.create_steel_material(yield_strength=400)
            g = rectangular_section(d=600, b=400, material=c)
            g = add_bar_rectangular_array(
                geometry=g, area=387.1, material=s,
                n_x=n_bar, x_s=(400 - 2 * 60) / (n_bar - 1),
                anchor=(60, 60), n=16,
            )
            k.assign_concrete_section(ConcreteSection(g))
            results.append(
                k.moment_curvature_analysis(kappa_inc=1e-7, progress_bar=False)
            )
            labels.append(f"{n_bar}-D22")

        fig, ax = plt.subplots(figsize=(6.5, 4.4))
        for res, lab in zip(results, labels, strict=True):
            ax.plot(np.array(res.kappa) * 1e6, np.array(res.m_xy) / 1e6, label=lab)
        ax.set_xlabel("curvature, kappa (1e-6 /mm)")
        ax.set_ylabel("moment (kN.m)")
        ax.set_title("Effect of reinforcement ratio")
        ax.legend()
        ax.grid(alpha=0.3)

        del MomentCurvatureResults
        """),
            md("""
        철근이 많을수록 강도는 커지지만 곡률 연성은 줄어든다.
        """),
        ],
    )


def nb_08_stress_analysis():
    """예제 08 - 응력 해석."""
    return write(
        "08_stress_analysis",
        [
            md("""
        # 08 · 응력 해석 — 비균열·균열·사용·극한

        원 문서의 `stress_analysis.ipynb` 에 대응한다.
        """),
            code(SETUP),
            code(COMMON_SECTIONS),
            code("""
        kds, conc_sec = beam_section()

        cracked = kds.calculate_cracked_properties(theta=0)
        m_service = 1.5 * cracked.m_cr
        _, u_res, _ = kds.ultimate_bending_capacity()

        print(f"균열모멘트   Mcr = {cracked.m_cr / 1e6:.2f} kN.m")
        print(f"사용 모멘트  M   = {m_service / 1e6:.2f} kN.m  (= 1.5 Mcr)")
        """),
            code("""
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


        def summarise(label, res):
            conc_s = [float(s) for arr in res.concrete_stresses for s in arr]
            steel_s = [float(s) for s in res.lumped_reinforcement_stresses]
            print(
                f"{label:>8} | concrete {min(conc_s):8.2f} ~ {max(conc_s):7.2f} MPa"
                f" | steel {min(steel_s):9.2f} ~ {max(steel_s):8.2f} MPa"
            )


        summarise("비균열", uncracked)
        summarise("균열", cracked_stress)
        summarise("사용", service)
        summarise("극한", ultimate)
        """),
            md("""
        극한 상태의 콘크리트 압축응력 22.95 MPa 는 $\\eta(0.85f_{ck})$ 와,
        철근 인장응력 −400 MPa 는 SD400 의 항복강도와 일치한다.
        """),
            code("""
        for label, res in [
            ("Uncracked", uncracked),
            ("Cracked", cracked_stress),
            ("Service", service),
            ("Ultimate", ultimate),
        ]:
            res.plot_stress(title=label)
        """),
            md("""
        비균열 해석은 인장측 콘크리트가 응력을 받는 것으로 보고, 균열 해석은
        인장을 무시한다. 사용 해석은 모멘트-곡률 결과를 이용해 실제 응력-변형률
        관계를 따른다.
        """),
        ],
    )


def nb_09_loads():
    """예제 09 - 하중조합."""
    return write(
        "09_loads",
        [
            md("""
        # 09 · 하중조합 — KDS 14 20 10 4.2.2

        강도설계법의 하중계수 조합 식 (4.2-1) ~ 식 (4.2-8) 을 평가한다.

        | 식 | 조합 |
        |---|---|
        | (4.2-1) | $U = 1.4(D+F)$ |
        | (4.2-2) | $U = 1.2(D{+}F{+}T) + 1.6(L + \\alpha_H H_v + H_h) + 0.5(L_r/S/R)$ |
        | (4.2-3) | $U = 1.2D + 1.6(L_r/S/R) + (1.0L$ 또는 $0.65W)$ |
        | (4.2-4) | $U = 1.2D + 1.3W + 1.0L + 0.5(L_r/S/R)$ |
        | (4.2-5) | $U = 1.2(D{+}H_v) + 1.0E + 1.0L + 0.2S + (1.0H_h$ 또는 $0.5H_h)$ |
        | (4.2-6) | $U = 1.2(D{+}F{+}T) + 1.6(L + \\alpha_H H_v) + 0.8H_h + 0.5(L_r/S/R)$ |
        | (4.2-7) | $U = 0.9(D{+}H_v) + 1.3W + (1.6H_h$ 또는 $0.8H_h)$ |
        | (4.2-8) | $U = 0.9(D{+}H_v) + 1.0E + (1.0H_h$ 또는 $0.5H_h)$ |
        """),
            code(SETUP),
            code("""
        from concreteproperties_kds.loads import (
            LOAD_SYMBOLS,
            alpha_h,
            evaluate_all,
            minimum_strength,
            print_combinations,
            required_strength,
        )

        # 8 m 경간 보의 단위길이당 하중 (kN/m)
        loads = {
            "D": 25.0, "L": 18.0, "L_r": 3.0,
            "S": 5.0, "W": 12.0, "E": 20.0,
        }

        for symbol, value in loads.items():
            print(f"  {symbol:>4} ({LOAD_SYMBOLS[symbol]}) = {value:7.2f} kN/m")
        """),
            code("""
        print_combinations(loads=loads)
        """),
            code("""
        u_max, governing = required_strength(loads=loads)
        span = 8.0

        print(f"소요강도 wu = {u_max:.2f} kN/m  "
              f"({governing.name}, 식 {governing.equation})")
        print(f"계수 휨모멘트 Mu = wu*l^2/8 = {u_max * span ** 2 / 8:.2f} kN.m")
        print(f"계수 전단력   Vu = wu*l/2   = {u_max * span / 2:.2f} kN")
        """),
            md("""
        ## 연직토압 보정계수 (KDS 14 20 10 4.2.2(1))

        $$\\alpha_H = \\begin{cases}
        1.0 & h \\le 2\\ \\text{m} \\\\
        1.05 - 0.025h \\ \\ge 0.875 & h > 2\\ \\text{m}
        \\end{cases}$$
        """),
            code("""
        h = np.linspace(0, 12, 200)
        fig, ax = plt.subplots(figsize=(6, 3.6))
        ax.plot(h, [alpha_h(depth=float(x)) for x in h])
        ax.axhline(0.875, ls="--", color="grey", lw=0.8)
        ax.axvline(2.0, ls=":", color="grey", lw=0.8)
        ax.set_xlabel("cover depth, h (m)")
        ax.set_ylabel("alpha_H")
        ax.set_title("Vertical earth pressure factor")
        ax.grid(alpha=0.3)
        """),
            md("""
        ## 활하중 계수 저감 (KDS 14 20 10 4.2.2(2))

        활하중이 5.0 kN/m² 미만이고 차고·공공집회 장소가 아니면 식 (4.2-3),
        (4.2-4), (4.2-5) 의 활하중 계수를 1.0 에서 0.5 로 낮출 수 있다.
        """),
            code("""
        full = {c.name: v for c, v in evaluate_all(loads=loads)}
        reduced = {
            c.name: v for c, v in evaluate_all(loads=loads, reduce_live_load=True)
        }

        for name in sorted(full):
            if abs(full[name] - reduced[name]) > 1e-9:
                print(f"  {name:>6} : {full[name]:8.2f} -> {reduced[name]:8.2f} kN/m")
        """),
            md("""
        ## 부양·전도 검토

        풍하중이 부양으로 작용할 때는 고정하중 계수를 0.9 로 낮춘 식 (4.2-7),
        (4.2-8) 이 지배한다.
        """),
            code("""
        uplift = {"D": 100.0, "W": -300.0}

        u_min, governing_min = minimum_strength(loads=uplift)
        print(f"최소 조합하중 = {u_min:.1f}  "
              f"({governing_min.name}, 식 {governing_min.equation})")
        print(f"  {governing_min.description}")
        """),
        ],
    )


def nb_10_shear_torsion():
    """예제 10 - 전단과 비틀림."""
    return write(
        "10_shear_torsion",
        [
            md("""
        # 10 · 전단과 비틀림 — KDS 14 20 22

        | 항목 | 식 | 조문 |
        |---|---|---|
        | $V_c$ 간편식 | $\\frac{1}{6}\\lambda\\sqrt{f_{ck}}b_wd$ | 식 (4.2-1) |
        | $V_c$ 축압축 | $\\frac{1}{6}(1+N_u/14A_g)\\lambda\\sqrt{f_{ck}}b_wd$ | 식 (4.2-2) |
        | $V_c$ 정밀식 | $(0.16\\lambda\\sqrt{f_{ck}}+17.6\\rho_wV_ud/M_u)b_wd$ | 식 (4.2-3) |
        | $V_c$ 축인장 | $\\frac{1}{6}(1+N_u/3.5A_g)\\lambda\\sqrt{f_{ck}}b_wd$ | 식 (4.2-6) |
        | $V_s$ | $A_vf_{yt}d/s$ | 식 (4.3-3) |
        | $A_{v,min}$ | $0.0625\\sqrt{f_{ck}}b_ws/f_{yt} \\ge 0.35b_ws/f_{yt}$ | 식 (4.3-1) |
        | $T_{cr}$ | $\\frac{1}{3}\\lambda\\sqrt{f_{ck}}A_{cp}^2/p_{cp}$ | 4.4.1 |

        강도감소계수는 $\\phi = 0.75$ 이다 (KDS 14 20 10 4.3.3(2)).
        """),
            code(SETUP),
            code("""
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

        FCK, FY = 27.0, 400.0
        B_W, H, D, COVER = 400.0, 600.0, 550.0, 40.0
        v_u = 320e3

        a_v = 2 * bar_area("D13")   # D13 2가닥 스터럽

        s_req = required_stirrup_spacing(
            v_u=v_u, fck=FCK, b_w=B_W, d=D, a_v=a_v, fyt=FY
        )
        s_use = 25.0 * int(s_req / 25.0)

        print(f"필요 스터럽 간격 s = {s_req:.1f} mm  ->  배치 {s_use:.0f} mm")
        """),
            code("""
        res = check_shear(v_u=v_u, fck=FCK, b_w=B_W, d=D, a_v=a_v, s=s_use, fyt=FY)
        res.print_results()
        """),
            md("""
        ## 축력이 $V_c$ 에 미치는 영향

        압축은 $V_c$ 를 키우고 인장은 줄인다. KDS 는 압축과 인장에 서로 다른 식을
        쓴다 — 식 (4.2-2) 와 식 (4.2-6).
        """),
            code("""
        a_g = B_W * H
        n_u = np.linspace(-1500e3, 3000e3, 300)
        v_c = [
            concrete_shear_strength(
                fck=FCK, b_w=B_W, d=D, n_u=float(n), a_g=a_g
            ) / 1e3
            for n in n_u
        ]

        fig, ax = plt.subplots(figsize=(6.5, 4))
        ax.plot(n_u / 1e3, v_c)
        ax.axvline(0, ls=":", color="grey", lw=0.8)
        ax.axhline(
            concrete_shear_strength(fck=FCK, b_w=B_W, d=D) / 1e3,
            ls="--", color="grey", lw=0.8,
        )
        ax.set_xlabel("axial force, Nu (kN)   [+ compression]")
        ax.set_ylabel("Vc (kN)")
        ax.set_title("Effect of axial force on Vc")
        ax.grid(alpha=0.3)
        """),
            md("""
        인장이 커지면 $V_c$ 가 0 에 도달한다. 그 뒤로는 전단철근이 전체 전단력을
        받아야 한다 (KDS 14 20 22 4.2.1(1)③).

        ## 스터럽 간격에 따른 설계 전단강도
        """),
            code("""
        spacings = np.arange(75, 401, 5.0)
        phi_v_n = [
            check_shear(
                v_u=0, fck=FCK, b_w=B_W, d=D, a_v=a_v, s=float(s), fyt=FY
            ).phi_v_n / 1e3
            for s in spacings
        ]

        fig, ax = plt.subplots(figsize=(6.5, 4))
        ax.plot(spacings, phi_v_n)
        ax.axhline(v_u / 1e3, ls="--", color="tab:red", label=f"Vu = {v_u / 1e3:.0f}")
        ax.axvline(s_use, ls=":", color="tab:green", label=f"s = {s_use:.0f} mm")
        ax.set_xlabel("stirrup spacing, s (mm)")
        ax.set_ylabel("phi*Vn (kN)")
        ax.set_title("Design shear strength vs stirrup spacing")
        ax.legend()
        ax.grid(alpha=0.3)
        """),
            md("""
        ## 비틀림 (KDS 14 20 22 4.4, 4.5)
        """),
            code("""
        a_cp, p_cp = B_W * H, 2 * (B_W + H)
        a_oh = (B_W - 2 * COVER) * (H - 2 * COVER)
        p_h = 2 * ((B_W - 2 * COVER) + (H - 2 * COVER))
        t_u = 30e6

        t_cr = cracking_torque(fck=FCK, a_cp=a_cp, p_cp=p_cp)
        negligible = torsion_negligible(t_u=t_u, fck=FCK, a_cp=a_cp, p_cp=p_cp)

        print(f"계수 비틀림모멘트  Tu           = {t_u / 1e6:8.2f} kN.m")
        print(f"균열 비틀림모멘트  Tcr          = {t_cr / 1e6:8.2f} kN.m")
        print(f"무시 한계      phi*Tcr/4        = "
              f"{PHI_SHEAR * t_cr / 4 / 1e6:8.2f} kN.m")
        print(f"비틀림 무시 가능                = "
              f"{'예' if negligible else '아니오'}")

        if not negligible:
            a_t = bar_area("D13")
            t_n = torsional_strength(a_t=a_t, s=s_use, a_oh=a_oh, fyt=FY)
            a_l = longitudinal_torsion_reinforcement(
                a_t=a_t, s=s_use, p_h=p_h, fyt=FY, fy=FY
            )
            print(f"공칭 비틀림강도    Tn           = {t_n / 1e6:8.2f} kN.m")
            print(f"설계 비틀림강도  phi*Tn         = "
                  f"{PHI_SHEAR * t_n / 1e6:8.2f} kN.m")
            print(f"종방향 비틀림철근  Al           = {a_l:8.1f} mm^2")

        demand, capacity, ok = check_torsion_section(
            v_u=v_u, t_u=t_u, fck=FCK, b_w=B_W, d=D, a_oh=a_oh, p_h=p_h
        )
        print(f"단면 크기  소요 {demand:.3f} <= 한계 {capacity:.3f} MPa"
              f"  {'만족' if ok else '불만족'}")
        """),
        ],
    )


def nb_11_serviceability():
    """예제 11 - 처짐과 균열."""
    return write(
        "11_serviceability",
        [
            md("""
        # 11 · 처짐과 균열 — KDS 14 20 30

        | 항목 | 조문 |
        |---|---|
        | 최소 두께 (처짐 계산 생략) | KDS 14 20 30 표 4.2-1 |
        | 유효단면2차모멘트 (Branson) | KDS 14 20 30 식 (4.2-1) |
        | 장기처짐 계수 $\\lambda_\\Delta = \\xi/(1+50\\rho')$ | KDS 14 20 30 식 (4.2-4) |
        | 최대 허용처짐 | KDS 14 20 30 표 4.2-2 |
        | 균열 제어 철근 간격 | KDS 14 20 20 4.2.3(4) |
        | 수축·온도철근 | KDS 14 20 50 4.6.2 |
        """),
            code(SETUP),
            code(COMMON_SECTIONS),
            code("""
        from concreteproperties_kds.serviceability import (
            check_crack_control,
            check_deflection,
            long_term_deflection_factor,
            minimum_thickness,
            shrinkage_temperature_reinforcement,
            shrinkage_temperature_spacing,
        )

        SPAN, FY = 8000.0, 400.0

        kds, conc_sec = beam_section()
        conc = conc_sec.concrete_geometries[0].material

        gross = kds.get_transformed_gross_properties(
            elastic_modulus=conc.elastic_modulus
        )
        cracked = kds.calculate_cracked_properties(theta=0)
        cracked.calculate_transformed_properties(
            elastic_modulus=conc.elastic_modulus
        )

        h_min = minimum_thickness(span=SPAN, member="보", support="단순지지", fy=FY)
        print(f"최소 두께  l/16 = {h_min:.1f} mm,  h = 600.0 mm"
              f"  ->  {'생략 가능' if h_min <= 600 else '처짐 계산 필요'}")
        """),
            md("""
        ## 허용처짐은 조건마다 비교 대상이 다르다

        KDS 14 20 30 표 4.2-2 는 조건마다 **비교하는 처짐의 종류**를 달리 정한다.
        이 점을 놓치면 검토가 과도하게 보수적이 된다.

        | 조건 | 허용처짐 | 비교 대상 |
        |---|---|---|
        | 지붕, 비구조재 없음 | $l/180$ | 활하중 즉시처짐 |
        | 바닥, 비구조재 없음 | $l/360$ | 활하중 즉시처짐 |
        | 손상되기 쉬운 비구조재 | $l/480$ | 부착 후 발생 처짐 |
        | 손상되지 않는 비구조재 | $l/240$ | 부착 후 발생 처짐 |
        """),
            code("""
        for condition in [
            "바닥_비구조재없음", "손상되기쉬운_비구조재", "손상되지않는_비구조재",
        ]:
            res = check_deflection(
                span=SPAN, m_sustained=120e6, m_live=60e6,
                m_cr=cracked.m_cr, i_g=gross.ixx_c, i_cr=cracked.ixx_c_cr,
                e_c=conc.elastic_modulus,
                rho_prime=2 * 198.6 / (400 * 550),
                duration="5년이상", condition=condition,
            )
            res.print_results()
            print()
        """),
            md("""
        전체 처짐 34.4 mm 를 모든 한계와 비교하면 세 조건 모두 불만족이 되지만,
        기준이 정한 비교 대상을 쓰면 결과가 달라진다.

        ## 장기처짐 계수
        """),
            code("""
        rho_prime = np.linspace(0, 0.02, 200)
        fig, ax = plt.subplots(figsize=(6.5, 4))
        for duration in ["3개월", "6개월", "12개월", "5년이상"]:
            ax.plot(
                rho_prime,
                [
                    long_term_deflection_factor(rho_prime=float(r), duration=duration)
                    for r in rho_prime
                ],
                label=duration,
            )
        ax.set_xlabel("compression steel ratio, rho'")
        ax.set_ylabel("lambda_delta")
        ax.set_title("Long-term deflection factor")
        ax.legend()
        ax.grid(alpha=0.3)
        """),
            md("""
        압축철근이 있으면 크리프·건조수축에 의한 장기처짐이 줄어든다.

        ## 균열 제어 (KDS 14 20 20 4.2.3(4))

        $$s = 375\\left(\\frac{\\kappa_{cr}}{f_s}\\right) - 2.5c_c
        \\le 300\\left(\\frac{\\kappa_{cr}}{f_s}\\right)$$
        """),
            code("""
        fs, s_max, ok = check_crack_control(
            bar_spacing=(400 - 2 * 50) / 3, fy=FY, c_c=50 - 22.2 / 2
        )
        print(f"철근응력       fs = 2/3*fy = {fs:8.1f} MPa")
        print(f"최대 철근 간격 s,max       = {s_max:8.1f} mm")
        print(f"배치 철근 간격 s           = {(400 - 2 * 50) / 3:8.1f} mm")
        print(f"판정                       = {'만족' if ok else '불만족'}")
        """),
            code("""
        c_c = np.linspace(20, 90, 200)
        fig, ax = plt.subplots(figsize=(6.5, 4))
        for fy, label in [(400, "SD400"), (500, "SD500"), (600, "SD600")]:
            ax.plot(
                c_c,
                [check_crack_control(bar_spacing=0, fy=fy, c_c=float(c))[1] for c in c_c],
                label=label,
            )
        ax.set_xlabel("cover to bar surface, cc (mm)")
        ax.set_ylabel("max bar spacing, s (mm)")
        ax.set_title("Crack control bar spacing (dry environment)")
        ax.legend()
        ax.grid(alpha=0.3)
        """),
            md("""
        ## 수축·온도철근 (KDS 14 20 50 4.6.2)
        """),
            code("""
        a_st = shrinkage_temperature_reinforcement(fy=FY, a_g=1000.0 * 200.0)
        print(f"수축·온도철근 (t = 200 mm 슬래브, 1 m 폭) = {a_st:.1f} mm^2/m")
        print(f"최대 간격                                 = "
              f"{shrinkage_temperature_spacing(thickness=200):.1f} mm")
        """),
        ],
    )


def nb_12_durability():
    """예제 12 - 내구성과 피복두께."""
    return write(
        "12_durability",
        [
            md("""
        # 12 · 내구성과 피복두께 — KDS 14 20 40, KDS 14 20 50

        KDS 14 20 40 이 수치로 규정하는 것은 **표 4.1-3 의 최소 설계기준압축강도**
        뿐이다.

        - 물-결합재비·결합재·공기량·염화물량 → **KCS 14 20 10(1.10)** (4.1.4(3))
        - 피복두께 → 노출범주 EC·ES 는 **KDS 14 20 50(4.3)** 이상 (4.1.4(2))
        """),
            code(SETUP),
            code("""
        from concreteproperties_kds.detailing import MINIMUM_COVER, minimum_cover
        from concreteproperties_kds.durability import (
            check_durability,
            governing_requirements,
            print_exposure_table,
        )

        print_exposure_table()
        """),
            md("""
        ## 복합 노출

        해안 지역 옥외 교각은 탄산화 · 염화물 · 동결융해가 동시에 걸린다.
        """),
            code("""
        exposure = ["EC4", "ES1", "EF2"]
        fck_min = governing_requirements(exposure_classes=exposure)

        print(f"적용 노출등급 : {', '.join(exposure)}")
        print(f"지배 최소 설계기준압축강도 = {fck_min:.1f} MPa")
        """),
            code("""
        fck_design = 35.0
        cover_min = minimum_cover(
            condition="흙에접하거나옥외노출", bar="D22", fck=fck_design
        )
        cover_design = 50.0

        for cls in exposure:
            check_durability(
                exposure_class=cls, fck=fck_design,
                cover=cover_design, cover_min=cover_min,
                water_binder_ratio=0.40,
            ).print_results()
            print()
        """),
            md("""
        ## 최소 피복두께 (KDS 14 20 50 4.3.1)

        프리스트레스하지 않는 부재의 현장치기콘크리트 기준이다.
        $f_{ck} \\ge 40$ MPa 저감(10 mm)은 **옥내 보·기둥에만** 적용된다.
        """),
            code("""
        cases = [
            ("수중", None),
            ("흙에영구히묻힘", None),
            ("흙에접하거나옥외노출", "D22"),
            ("흙에접하거나옥외노출", "D13"),
            ("옥내_슬래브벽체장선", "D38"),
            ("옥내_슬래브벽체장선", "D25"),
            ("옥내_보기둥", None),
            ("옥내_셸절판", None),
        ]

        print(f"{'조건':<24} {'철근':>6} {'cc':>7} {'fck>=40':>9}")
        print("-" * 50)
        for condition, bar in cases:
            print(
                f"{condition:<24} {bar or '-':>6}"
                f" {minimum_cover(condition=condition, bar=bar):7.0f}"
                f" {minimum_cover(condition=condition, bar=bar, fck=40):9.0f}"
            )

        del MINIMUM_COVER
        """),
        ],
    )


def nb_13_detailing():
    """예제 13 - 정착과 이음."""
    return write(
        "13_detailing",
        [
            md("""
        # 13 · 정착과 이음 — KDS 14 20 52

        | 항목 | 식 | 조문 |
        |---|---|---|
        | 인장 기본정착길이 | $l_{db} = 0.6d_bf_y/(\\lambda\\sqrt{f_{ck}})$ | 식 (4.1-1) |
        | 보정계수 | 0.8/1.0/1.2/1.5 $\\times \\alpha\\beta$ | 표 4.1-1 |
        | 인장 정밀식 | $0.90d_bf_y\\alpha\\beta\\gamma/(\\lambda\\sqrt{f_{ck}}\\cdot(c{+}K_{tr})/d_b)$ | 식 (4.1-2) |
        | 압축 정착길이 | $\\max(0.25d_bf_y/(\\lambda\\sqrt{f_{ck}}),\\ 0.043d_bf_y)$ | 식 (4.1-3) |
        | 표준갈고리 | $0.24\\beta d_bf_y/(\\lambda\\sqrt{f_{ck}})$ | 4.1.5 |
        | 압축 겹침이음 | $0.072f_yd_b$ / $(0.13f_y{-}24)d_b$ | 4.5 |
        """),
            code(SETUP),
            code("""
        from concreteproperties_kds.detailing import (
            BAR_PROPERTIES,
            development_length_tension,
            development_length_tension_detailed,
            minimum_bar_spacing,
            summarise_detailing,
        )

        FCK, FY = 27.0, 400.0

        summarise_detailing(bar="D22", fy=FY, fck=FCK).print_results()
        """),
            md("""
        ## 철근 호칭별 정착·이음 길이
        """),
            code("""
        print(f"{'호칭':>6} {'db':>7} {'ld':>9} {'ld(상부)':>10} {'ldc':>8}"
              f" {'ldh':>8} {'이음B급':>9}")
        print("-" * 62)
        for bar in BAR_PROPERTIES:
            summary = summarise_detailing(bar=bar, fy=FY, fck=FCK)
            l_top = development_length_tension(
                bar=bar, fy=FY, fck=FCK, top_bar=True
            )
            print(
                f"{bar:>6} {summary.d_b:7.2f} {summary.l_d:9.1f} {l_top:10.1f}"
                f" {summary.l_dc:8.1f} {summary.l_dh:8.1f}"
                f" {summary.l_s_tension_b:9.1f}"
            )
        """),
            md("""
        ## 콘크리트 강도의 영향

        정착길이는 $1/\\sqrt{f_{ck}}$ 에 비례해 줄어든다.
        """),
            code("""
        fck = np.linspace(21, 60, 200)
        fig, ax = plt.subplots(figsize=(6.5, 4))
        ax.plot(
            fck,
            [development_length_tension(bar="D22", fy=FY, fck=float(f)) for f in fck],
            label="ld (favourable, D22)",
        )
        ax.plot(
            fck,
            [
                development_length_tension(
                    bar="D22", fy=FY, fck=float(f), favourable_spacing=False
                )
                for f in fck
            ],
            label="ld (other)",
        )
        ax.plot(
            fck,
            [
                development_length_tension_detailed(
                    bar="D22", fy=FY, fck=float(f), c=40, k_tr=15
                )
                for f in fck
            ],
            label="ld (detailed eq.)",
        )
        ax.axhline(300, ls=":", color="grey", lw=0.8, label="min 300 mm")
        ax.set_xlabel("fck (MPa)")
        ax.set_ylabel("development length (mm)")
        ax.set_title("Tension development length, SD400 D22")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        """),
            md("""
        정밀식은 횡방향 철근에 의한 구속을 반영해 기본식보다 짧게 나온다.

        ## 철근 최소 순간격 (KDS 14 20 50 4.2)
        """),
            code("""
        print(f"{'호칭':>6} {'보':>10} {'기둥':>10} {'보(골재25)':>13}")
        print("-" * 44)
        for bar in ["D13", "D16", "D22", "D25", "D32", "D38"]:
            print(
                f"{bar:>6}"
                f" {minimum_bar_spacing(bar=bar, member='보'):10.1f}"
                f" {minimum_bar_spacing(bar=bar, member='기둥'):10.1f}"
                f" {minimum_bar_spacing(bar=bar, member='보', aggregate_size=25):13.1f}"
            )
        """),
        ],
    )


def nb_14_slender_column():
    """예제 14 - 세장 기둥."""
    return write(
        "14_slender_column",
        [
            md("""
        # 14 · 세장 기둥 — KDS 14 20 20 4.4

        | 항목 | 식 | 조문 |
        |---|---|---|
        | 회전반지름 | $r = 0.3h$ (직사각형) | 4.4.1 |
        | 세장비 한계 | $34 - 12(M_1/M_2) \\le 40$ / 22 | 4.4.1 |
        | 휨강성 | $EI = 0.4E_cI_g/(1+\\beta_{dns})$ | 4.4 |
        | 임계좌굴하중 | $P_c = \\pi^2EI/(kl_u)^2$ | 4.4 |
        | 모멘트확대계수 | $\\delta_{ns} = C_m/(1-P_u/0.75P_c) \\ge 1.0$ | 4.4.2 |
        | 최소 편심 모멘트 | $M_{2,min} = P_u(15+0.03h)$ | 4.4.2 |
        """),
            code(SETUP),
            code(COMMON_SECTIONS),
            code("""
        from concreteproperties_kds.slender import check_slenderness

        P_U, M1, M2, H = 1500e3, 90e6, 150e6, 500.0

        kds, conc_sec = column_section()
        conc = conc_sec.concrete_geometries[0].material
        gross = kds.get_transformed_gross_properties(
            elastic_modulus=conc.elastic_modulus
        )

        for l_u in [3000.0, 6000.0, 9000.0]:
            res = check_slenderness(
                p_u=P_U, m1=M1, m2=M2, k=1.0, l_u=l_u, h=H,
                e_c=conc.elastic_modulus, i_g=gross.ixx_c,
                braced=True, beta_dns=0.6,
            )
            print(f"### lu = {l_u:.0f} mm")
            res.print_results()

            f_res, _, phi = kds.ultimate_bending_capacity(n_design=P_U)
            ratio = res.m_c / f_res.m_x
            print(f"설계 휨강도 phi*Mn = {f_res.m_x / 1e6:.2f} kN.m (phi = {phi:.3f})")
            print(f"소요/강도          = {ratio:.3f}"
                  f"  {'만족' if ratio <= 1.0 else '불만족'}")
            print()
        """),
            md("""
        ## 비지지 길이에 따른 모멘트 확대
        """),
            code("""
        l_u = np.linspace(2000, 11000, 200)
        delta, m_c, slender = [], [], []

        for length in l_u:
            r = check_slenderness(
                p_u=P_U, m1=M1, m2=M2, k=1.0, l_u=float(length), h=H,
                e_c=conc.elastic_modulus, i_g=gross.ixx_c,
            )
            delta.append(r.delta_ns)
            m_c.append(r.m_c / 1e6)
            slender.append(r.slender)

        f_res, _, _ = kds.ultimate_bending_capacity(n_design=P_U)

        fig, axes = plt.subplots(1, 2, figsize=(11, 4))
        axes[0].plot(l_u, delta)
        axes[0].axhline(1.0, ls=":", color="grey", lw=0.8)
        axes[0].set_xlabel("unsupported length, lu (mm)")
        axes[0].set_ylabel("delta_ns")
        axes[0].set_title("Moment magnifier")
        axes[0].grid(alpha=0.3)

        axes[1].plot(l_u, m_c, label="Mc")
        axes[1].axhline(
            f_res.m_x / 1e6, ls="--", color="tab:red",
            label=f"phi*Mn = {f_res.m_x / 1e6:.0f}",
        )
        axes[1].axhline(M2 / 1e6, ls=":", color="grey", lw=0.8, label="M2")
        axes[1].set_xlabel("unsupported length, lu (mm)")
        axes[1].set_ylabel("design moment (kN.m)")
        axes[1].set_title("Magnified design moment")
        axes[1].legend(fontsize=8)
        axes[1].grid(alpha=0.3)
        fig.tight_layout()

        first_slender = l_u[np.argmax(slender)]
        print(f"세장 기둥이 되는 비지지 길이 ~ {first_slender:.0f} mm")
        """),
            md("""
        비지지 길이가 길어질수록 $\\delta_{ns}$ 가 급격히 커진다. $P_u$ 가
        $0.75P_c$ 에 접근하면 분모가 0 에 가까워지기 때문이다. 그 지점을 넘으면
        좌굴이므로 `check_slenderness` 가 `ValueError` 를 낸다.
        """),
        ],
    )


def nb_15_biaxial_simplified():
    """예제 15 - 2축 휨 간략식."""
    return write(
        "15_biaxial_simplified",
        [
            md("""
        # 15 · 2축 휨 간략식과 엄밀해 비교

        `KDS.biaxial_bending_diagram` 은 상관면을 엄밀하게 계산한다. 여기서는
        실무에서 널리 쓰이는 Bresler 간략식과 비교한다.

        간략식은 KDS 14 20 의 조문이 아니라 문헌에서 인정되는 근사법이다.
        """),
            code(SETUP),
            code(COMMON_SECTIONS),
            code("""
        from concreteproperties_kds.biaxial import (
            check_bresler_reciprocal,
            check_load_contour,
            compare_with_exact,
        )

        N_DESIGN, M_UX, M_UY = 1200e3, 200e6, 120e6

        kds, _ = column_section()

        f_x, _, phi_x = kds.ultimate_bending_capacity(theta=0, n_design=N_DESIGN)
        f_y, _, phi_y = kds.ultimate_bending_capacity(
            theta=-np.pi / 2, n_design=N_DESIGN
        )

        phi_m_nx, phi_m_ny = abs(f_x.m_x), abs(f_y.m_y)

        print(f"Nd = {N_DESIGN / 1e3:,.0f} kN")
        print(f"x 축  phi*Mnx = {phi_m_nx / 1e6:8.2f} kN.m  (phi = {phi_x:.3f})")
        print(f"y 축  phi*Mny = {phi_m_ny / 1e6:8.2f} kN.m  (phi = {phi_y:.3f})")
        print(f"소요  Mux = {M_UX / 1e6:.1f},  Muy = {M_UY / 1e6:.1f} kN.m")
        """),
            code("""
        check_load_contour(
            m_ux=M_UX, m_uy=M_UY,
            phi_m_nx=phi_m_nx, phi_m_ny=phi_m_ny, alpha=1.0,
        ).print_results()
        """),
            md("""
        ## 엄밀 상관면과 비교
        """),
            code("""
        f_bb, _ = kds.biaxial_bending_diagram(
            n_design=N_DESIGN, n_points=48, progress_bar=False
        )
        m_x = np.array([r.m_x for r in f_bb.results])
        m_y = np.array([r.m_y for r in f_bb.results])

        target = np.arctan2(M_UY, M_UX)
        angles = np.arctan2(m_y, m_x)
        idx = int(np.argmin(np.abs(np.angle(np.exp(1j * (angles - target))))))

        exact = float(np.hypot(M_UX, M_UY)) / float(np.hypot(m_x[idx], m_y[idx]))
        print(f"엄밀해 소요/강도 = {exact:.4f}")
        print()
        print(f"{'alpha':>8} {'등하중선법':>12} {'보수적':>8}")
        print("-" * 32)
        for alpha, value, conservative in compare_with_exact(
            m_ux=M_UX, m_uy=M_UY,
            phi_m_nx=phi_m_nx, phi_m_ny=phi_m_ny, exact_ratio=exact,
        ):
            print(f"{alpha:8.2f} {value:12.4f} {'예' if conservative else '아니오':>8}")
        """),
            code("""
        fig, ax = plt.subplots(figsize=(6.4, 5.6))
        ax.plot(m_x / 1e6, m_y / 1e6, "k-", lw=1.6, label="exact (KDS analysis)")

        mx = np.linspace(0, phi_m_nx, 200)
        for alpha in [1.0, 1.25, 1.5, 2.0]:
            inner = np.clip(1 - (mx / phi_m_nx) ** alpha, 0, None)
            ax.plot(
                mx / 1e6, phi_m_ny * inner ** (1 / alpha) / 1e6,
                "--", lw=1, label=f"contour alpha = {alpha:.2f}",
            )

        ax.plot(M_UX / 1e6, M_UY / 1e6, "r*", ms=13, label="demand")
        ax.set_xlim(0, phi_m_nx / 1e6 * 1.05)
        ax.set_ylim(0, phi_m_ny / 1e6 * 1.05)
        ax.set_xlabel("phi*Mx (kN.m)")
        ax.set_ylabel("phi*My (kN.m)")
        ax.set_title(f"Exact vs load contour, Nd = {N_DESIGN / 1e3:,.0f} kN")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        """),
            md("""
        엄밀 상관면(검은 실선)은 $\\alpha = 1.0$ 직선보다 바깥, $\\alpha = 1.25$
        곡선보다 안쪽에 있다. 즉 **$\\alpha = 1.0$ 만 보수적**이고 그 이상은
        위험측이다. $\\alpha$ 를 임의로 키우지 말고 엄밀해로 확인하는 편이 낫다.

        ## Bresler 역하중법
        """),
            code("""
        n_max_nom, n_max_des = kds.max_axial_strength()
        f_mi, _, _ = kds.moment_interaction_diagram(
            theta=0, n_points=32, progress_bar=False
        )
        n_list = np.array([r.n for r in f_mi.results])
        m_list = np.array([r.m_x for r in f_mi.results])


        def axial_capacity_at_eccentricity(e):
            residual = m_list - n_list * e
            for i in range(len(residual) - 1):
                if residual[i] * residual[i + 1] <= 0:
                    t = residual[i] / (residual[i] - residual[i + 1])
                    return float(n_list[i] + t * (n_list[i + 1] - n_list[i]))
            return float(n_list[0])


        check_bresler_reciprocal(
            p_u=N_DESIGN,
            phi_p_nx=axial_capacity_at_eccentricity(M_UX / N_DESIGN),
            phi_p_ny=axial_capacity_at_eccentricity(M_UY / N_DESIGN),
            phi_p_o=n_max_des,
            fck=27, a_g=500.0 * 500.0,
        ).print_results()
        """),
        ],
    )


def nb_16_prestressed():
    """예제 16 - 프리스트레스트 콘크리트."""
    return write(
        "16_prestressed",
        [
            md("""
        # 16 · 프리스트레스트 콘크리트 — KDS 14 20 60

        원 문서의 `prestressed_section.ipynb` 에 대응한다.

        | 항목 | 조문 |
        |---|---|
        | 긴장재 허용응력 $\\min(0.80f_{pu}, 0.94f_{py})$ 등 | KDS 14 20 60 4.2.2 |
        | 콘크리트 허용응력, 균열등급 U/T/C | KDS 14 20 60 4.2.1, 4.2.2 |
        | 마찰 손실 $P_{px}=P_{pj}e^{-(Kl_{px}+\\mu_p\\alpha_{px})}$ | KDS 14 20 60 4.3 |
        | 부착 긴장재 $f_{ps}$ | KDS 14 20 60 4.4.2(3) |
        | PSC 변형률한계 0.002 / 0.005 | KDS 14 20 20 4.1.2(3), (4) |
        """),
            code(SETUP),
            code("""
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

        FPU, E_P = 1860.0, 200e3      # Eps = 200,000 MPa (KDS 14 20 10 식 4.3-6)
        FPY = 0.9 * FPU               # 저릴랙세이션
        FCK, FCI = 40.0, 30.0
        N_STRAND, A_STRAND, SPAN = 4, 138.7, 20000.0
        """),
            md("""
        ## 허용응력 (KDS 14 20 60 4.2)
        """),
            code("""
        print(f"긴장 중        = {allowable_tendon_stress(FPU, FPY, 'jacking'):8.1f} MPa"
              f"   min(0.80fpu, 0.94fpy)")
        print(f"정착 직후      = {allowable_tendon_stress(FPU, FPY, 'anchorage'):8.1f} MPa"
              f"   min(0.74fpu, 0.82fpy)")
        print(f"정착장치       = "
              f"{allowable_tendon_stress(FPU, FPY, 'anchorage_device'):8.1f} MPa"
              f"   0.70fpu")
        print()

        c_t, t_t = allowable_concrete_stress_transfer(fci=FCI)
        c_s, t_s = allowable_concrete_stress_service(fck=FCK, crack_class="U")
        c_sus, _ = allowable_concrete_stress_service(fck=FCK, sustained=True)

        print(f"도입 직후 콘크리트 = {c_t:7.2f} / {t_t:7.2f} MPa  (압축/인장)")
        print(f"사용 전체하중      = {c_s:7.2f} / {t_s:7.2f} MPa  (비균열등급 U)")
        print(f"사용 지속하중 압축 = {c_sus:7.2f} MPa")
        """),
            md("""
        ## 프리스트레스 손실 (KDS 14 20 60 4.3)
        """),
            code("""
        kds = KDS()
        conc = kds.create_concrete_material(compressive_strength=FCK)
        conc_i = kds.create_concrete_material(compressive_strength=FCI)

        f_pj = 0.75 * FPU
        a_ps = N_STRAND * A_STRAND

        _, friction_force = friction_loss(
            p_pj=f_pj * a_ps, mu_p=0.20, alpha_px=0.15,
            k_wobble=6.6e-7, l_px=SPAN / 2,
        )

        losses = PrestressLosses(
            f_pj=f_pj,
            friction=friction_force / a_ps,
            anchorage=anchorage_set_loss(slip=6.0, e_p=E_P, length=SPAN / 2),
            elastic=elastic_shortening_loss(
                f_cgp=8.0, e_p=E_P, e_ci=conc_i.elastic_modulus,
                post_tensioned=True, n_tendons=N_STRAND,
            ),
            creep=creep_loss(
                f_cgp=8.0, e_p=E_P, e_c=conc.elastic_modulus,
                creep_coefficient=2.0,
            ),
            shrinkage=shrinkage_loss(e_p=E_P, eps_sh=300e-6),
            relaxation=relaxation_loss(f_pi=0.70 * FPU, fpy=FPY),
        )
        losses.print_results()
        """),
            code("""
        labels = ["friction", "anchorage", "elastic", "creep", "shrinkage", "relax."]
        values = [
            losses.friction, losses.anchorage, losses.elastic,
            losses.creep, losses.shrinkage, losses.relaxation,
        ]

        fig, ax = plt.subplots(figsize=(6.5, 3.8))
        ax.bar(labels, values)
        ax.set_ylabel("stress loss (MPa)")
        ax.set_title(
            f"Prestress losses (total {losses.total:.0f} MPa, "
            f"{losses.loss_ratio * 100:.1f} %)"
        )
        ax.grid(alpha=0.3, axis="y")
        """),
            md("""
        ## 긴장재의 극한 응력 (KDS 14 20 60 4.4.2)
        """),
            code("""
        d_p, b = 680.0, 400.0
        rho_p = a_ps / (b * d_p)

        print(f"긴장재비  rho_p = {rho_p:.5f}")
        print(f"부착   fps = {tendon_stress_bonded(FPU, FCK, rho_p, 0.28):8.1f} MPa")
        print(f"비부착 fps = "
              f"{tendon_stress_unbonded(losses.f_pe, FCK, rho_p, FPY, SPAN / 800):8.1f} MPa")
        print(f"유효 프리스트레스 fpe = {losses.f_pe:8.1f} MPa")
        """),
            md("""
        ## 단면 해석
        """),
            code("""
        strand = SteelStrand(
            name="SWPC 7B 15.2mm",
            density=7.85e-6,
            stress_strain_profile=StrandHardening(
                yield_strength=FPY, elastic_modulus=E_P,
                fracture_strain=0.035, breaking_strength=FPU,
            ),
            colour="slategrey",
            prestress_stress=losses.f_pe,
        )

        geom = rectangular_section(d=800, b=400, material=conc)
        geom = add_bar_rectangular_array(
            geometry=geom, area=A_STRAND, material=strand,
            n_x=N_STRAND, x_s=80, anchor=(80, 120), n=8,
        )
        ps_sec = PrestressedSection(geom)
        ps_sec.plot_section()
        """),
            code("""
        kds_ps = KDSPrestressed(column_type="tie")
        kds_ps.assign_prestressed_section(ps_sec)

        f_res, u_res, phi = kds_ps.ultimate_bending_capacity(positive=True)
        eps_t = kds_ps.net_tensile_strain(theta=0, d_n=u_res.d_n)

        print(f"중립축 깊이   c      = {u_res.d_n:8.2f} mm")
        print(f"순인장변형률  et     = {eps_t:8.5f}")
        print(f"강도감소계수  phi    = {phi:8.3f}")
        print(f"공칭 휨강도   Mn     = {u_res.m_x / 1e6:8.2f} kN.m")
        print(f"설계 휨강도   phi*Mn = {f_res.m_x / 1e6:8.2f} kN.m")
        """),
            md("""
        ## PSC 부재의 강도감소계수

        프리스트레스트 부재는 변형률한계가 $f_y$ 에 의존하지 않고 **0.002 / 0.005
        고정값**이다 (KDS 14 20 20 4.1.2(3), (4)).
        """),
            code("""
        eps = np.linspace(0, 0.008, 300)
        fig, ax = plt.subplots(figsize=(6.5, 4))
        for ctype, label in [("tie", "tie (0.65)"), ("spiral", "spiral (0.70)")]:
            ax.plot(
                eps,
                [
                    capacity_reduction_factor_psc(eps_t=float(e), column_type=ctype)
                    for e in eps
                ],
                label=label,
            )
        ax.axvline(0.002, ls=":", color="grey", lw=0.8)
        ax.axvline(0.005, ls=":", color="grey", lw=0.8)
        ax.set_xlabel("net tensile strain, eps_t")
        ax.set_ylabel("phi")
        ax.set_title("Strength reduction factor, prestressed members")
        ax.legend()
        ax.grid(alpha=0.3)
        """),
        ],
    )


def nb_17_deck_design():
    """예제 17 - 교량 바닥판 설계 (KDS 24)."""
    return write(
        "17_deck_design",
        [
            md(r"""
        # 17 · 교량 바닥판 설계 — KDS 24 한계상태설계법

        PSC 거더교의 콘크리트 바닥판을 **내측부**와 **캔틸레버부**로 나누어
        설계한다. 거더는 KL-510 트럭을 다리 위로 굴려 풀지만, 바닥판은 기준이
        주는 근사식으로 끝난다.

        ```
        ① 교량 제원과 재하차로   KDS 24 12 21 4.3.1.1
        ② 두께와 피복            KDS 24 14 21 4.6.5.1, 4.4.4
        ③ 내측부 하중            KDS 24 10 11 4.6.2.4, 4.6.2.7
        ④ 하중조합               KDS 24 12 11 표 4.1-1
        ⑤ 내측부 휨 설계         KDS 24 14 21 4.1.1
        ⑥ 캔틸레버부             KDS 24 10 11 4.6.2.5
        ⑦ 배력철근               KDS 24 14 21 4.6.5.3(2)
        ⑧ 사용성                 KDS 24 14 21 4.2
        ⑨ KDS 14 대조
        ```

        원리를 그림으로 따라가려면
        [강의 L4](../lectures/L4_바닥판설계.ipynb) 를, 값을 슬라이더로 바꿔
        보려면 [대화형 탐색기](../_static/explorer.html)의 L4 탭을 연다.
        """),
            code(SETUP),
            code("""
        import math

        from concreteproperties_kds.kds import stress_block_parameters
        from concreteproperties_kds.kds24 import (
            COMBINATIONS_BY_NAME, MIN_THICKNESS_RC, WHEEL_LOAD,
            bar_area, cantilever_live_load_moment, cantilever_wheel_width,
            dead_load_moment, deck_deflection_limit, deck_span,
            design_compressive_strength, design_yield_strength,
            distribution_steel_ratio, equivalent_block, impact_factor,
            lane_width, live_load_moment, max_bar_diameter, max_bar_spacing,
            minimum_flexural_steel, nominal_cover, number_of_lanes,
            provided_steel_area, required_steel_area,
        )

        # 교량 제원
        TOTAL_WIDTH, ROADWAY_WIDTH, PLAN_LANE = 12.6, 11.2, 3.5
        N_GIRDER, GIRDER_SPACING, CANTILEVER = 5, 2.5, 1.3
        FCK, FY, EXPOSURE, PAVEMENT = 27.0, 400.0, "ED1", 80.0
        GAMMA_C, GAMMA_P = 24.5, 22.5
        BARRIER_LOAD, BARRIER_ARM = 8.0, 0.25
        THICKNESS, HAUNCH = 240.0, 280.0

        print(f"거더 {N_GIRDER} 본 @ {GIRDER_SPACING} m + 캔틸레버 {CANTILEVER} m × 2"
              f" = {(N_GIRDER - 1) * GIRDER_SPACING + 2 * CANTILEVER:.1f} m")
        """),
            md(r"""
        ## ① 교량 제원과 재하차로

        재하차로는 **거더** 설계에 쓴다. 바닥판 근사식(4.6.2.4)에는 다차로
        재하계수를 곱하지 않는다 — 식 자체가 인접 윤하중의 겹침을 이미 담고
        있기 때문이다.
        """),
            code("""
        n_lane = number_of_lanes(roadway_width=ROADWAY_WIDTH, plan_lane_width=PLAN_LANE)
        w_lane = lane_width(roadway_width=ROADWAY_WIDTH, n_lanes=n_lane)

        print(f"교폭 W_C        {ROADWAY_WIDTH:.1f} m")
        print(f"재하차로 수 N   {n_lane}       (식 (4.3-1))")
        print(f"재하차로 폭 W   {w_lane:.2f} m   (식 (4.3-2))")
        print(f"윤하중 P        {WHEEL_LOAD:.0f} kN    (KL-510 의 192 kN 축의 절반)")
        """),
            md(r"""
        ## ② 두께와 피복두께

        제설염을 맞는 고속도로 바닥판이므로 노출등급을 **ED1** 로 잡는다.
        피복이 55 mm 로 두꺼워져 유효깊이를 그만큼 잃는다.
        """),
            code("""
        span = deck_span(girder_spacing=GIRDER_SPACING, thickness=THICKNESS)
        dia_in, spacing_in = 16.0, 150.0
        t_min, cover = nominal_cover(exposure=EXPOSURE, bar_diameter=dia_in)
        d_in = THICKNESS - cover - dia_in / 2

        print(f"바닥판 지간 L    {span:.2f} m      (4.6.2.3(1))")
        print(f"두께 t           {THICKNESS:.0f} mm     (최소 {MIN_THICKNESS_RC:.0f} mm)")
        print(f"두께 / 지간      1 / {span * 1000 / THICKNESS:.1f}")
        print(f"최소피복         {t_min:.0f} mm      (표 4.4-4, {EXPOSURE})")
        print(f"공칭피복         {cover:.0f} mm      (+ 설계 편차 10 mm)")
        print(f"유효깊이 d       {d_in:.0f} mm")
        """),
            md(r"""
        ## ③ 내측부 하중과 ④ 하중조합
        """),
            code("""
        w_dc = GAMMA_C * THICKNESS / 1000.0
        w_dw = GAMMA_P * PAVEMENT / 1000.0
        m_dc = dead_load_moment(w=w_dc, span=span, kind="연속판_지간")
        m_dw = dead_load_moment(w=w_dw, span=span, kind="연속판_지간")
        m_ll = live_load_moment(span=span, continuous=True)
        m_im = m_ll * (impact_factor() - 1.0)

        loads = {"DC": m_dc, "DW": m_dw, "LL": m_ll, "IM": m_im}
        m_ed = COMBINATIONS_BY_NAME["극한Ⅰ"].evaluate(loads=loads)
        m_ser = COMBINATIONS_BY_NAME["사용Ⅰ"].evaluate(loads=loads)
        total = m_dc + m_dw + m_ll + m_im

        print(f"자중 DC     {w_dc:5.2f} kN/m²  ->  M = wL²/10 = {m_dc:5.2f} kN·m/m")
        print(f"포장 DW     {w_dw:5.2f} kN/m²  ->  M = wL²/10 = {m_dw:5.2f} kN·m/m")
        print(f"활하중 LL   (L+0.6)P/9.6 × 0.8    = {m_ll:5.2f} kN·m/m")
        print(f"충격 IM     × 1.25                = {m_im:5.2f} kN·m/m")
        print(f"                          계수 전 합 {total:5.2f}, "
              f"활하중의 몫 {(m_ll + m_im) / total * 100:.0f} %")
        print()
        print(f"극한Ⅰ  1.25 DC + 1.50 DW + 1.80 (LL+IM) = {m_ed:6.2f} kN·m/m")
        print(f"사용Ⅰ  1.00 DC + 1.00 DW + 1.00 (LL+IM) = {m_ser:6.2f} kN·m/m")
        """),
            md(r"""
        ## ⑤ 내측부 휨 설계

        KDS 24 이므로 재료계수가 재료에 이미 들어 있다. 해석 결과가 곧 설계강도다.
        """),
            code("""
        def capacity(a_s, d):
            \"\"\"배치 철근량으로 설계휨강도를 구한다 (kN·m/m).\"\"\"
            f_cd = design_compressive_strength(fck=FCK)
            f_yd = design_yield_strength(fy=FY)
            alpha, beta = equivalent_block(fck=FCK)
            c = a_s * f_yd / (alpha * f_cd * 1000.0)
            return a_s * f_yd * (d - beta * c) / 1e6


        def steel_stress(m_service, a_s, d, n_ratio=7.0):
            \"\"\"균열단면의 철근 인장응력 (MPa).\"\"\"
            rho = a_s / (1000.0 * d)
            k = math.sqrt((n_ratio * rho) ** 2 + 2 * n_ratio * rho) - n_ratio * rho
            return m_service * 1e6 / (a_s * (1.0 - k / 3.0) * d)


        as_req = required_steel_area(m_ed=m_ed * 1e6, d=d_in)
        as_min = minimum_flexural_steel(d=d_in)
        as_prov = provided_steel_area(diameter=dia_in, spacing=spacing_in)
        m_rd = capacity(as_prov, d_in)

        print(f"f_cd = {design_compressive_strength(fck=FCK):.2f} MPa, "
              f"f_yd = {design_yield_strength(fy=FY):.1f} MPa")
        print(f"필요 As    {as_req:6.0f} mm²/m")
        print(f"최소 As    {as_min:6.0f} mm²/m")
        print(f"배치 D16@150 {as_prov:5.0f} mm²/m")
        print(f"M_Rd       {m_rd:6.2f} kN·m/m   ->  M_Rd/M_Ed = {m_rd / m_ed:.2f}")
        """),
            md(r"""
        ## ⑥ 캔틸레버부

        내민 바닥판에는 **방호벽 자중**이 긴 지렛대 팔로 걸린다. 윤하중은 차도
        끝에서 300 mm 안쪽에 놓는다(4.6.2.3(3)⑤).
        """),
            code("""
        x_wheel = CANTILEVER - 0.3
        e_width = cantilever_wheel_width(x=x_wheel)
        dia_c, spacing_c = 19.0, 125.0
        _, cover_c = nominal_cover(exposure=EXPOSURE, bar_diameter=dia_c)
        d_c = HAUNCH - cover_c - dia_c / 2

        w_dc_c = GAMMA_C * HAUNCH / 1000.0
        m_dc_c = abs(dead_load_moment(w=w_dc_c, span=CANTILEVER, kind="캔틸레버판"))
        m_dc_c += BARRIER_LOAD * (CANTILEVER - BARRIER_ARM)
        m_dw_c = abs(dead_load_moment(w=w_dw, span=CANTILEVER - 0.5, kind="캔틸레버판"))
        m_ll_c = cantilever_live_load_moment(x=x_wheel)
        m_im_c = m_ll_c * (impact_factor() - 1.0)

        loads_c = {"DC": m_dc_c, "DW": m_dw_c, "LL": m_ll_c, "IM": m_im_c}
        m_ed_c = COMBINATIONS_BY_NAME["극한Ⅰ"].evaluate(loads=loads_c)
        m_ser_c = COMBINATIONS_BY_NAME["사용Ⅰ"].evaluate(loads=loads_c)
        as_prov_c = provided_steel_area(diameter=dia_c, spacing=spacing_c)
        m_rd_c = capacity(as_prov_c, d_c)

        print(f"윤하중 위치 X   {x_wheel:.2f} m")
        print(f"분포폭 E        {e_width:.2f} m   (식 (4.6-4))")
        print(f"고정단 두께     {HAUNCH:.0f} mm (헌치),  d = {d_c:.0f} mm")
        print()
        print(f"자중 + 방호벽   {m_dc_c:6.2f} kN·m/m")
        print(f"포장            {m_dw_c:6.2f} kN·m/m")
        print(f"활하중 + 충격   {m_ll_c + m_im_c:6.2f} kN·m/m")
        print(f"극한Ⅰ M_Ed    {m_ed_c:6.2f} kN·m/m   "
              f"(내측부의 {m_ed_c / m_ed:.1f} 배)")
        print()
        print(f"배치 D19@125 (상부) {as_prov_c:5.0f} mm²/m")
        print(f"M_Rd            {m_rd_c:6.2f} kN·m/m   ->  M_Rd/M_Ed = {m_rd_c / m_ed_c:.2f}")
        """),
            md(r"""
        **아래 코드가 하는 일** — 두 단면의 하중 구성과 강도를 나란히 그린다.
        캔틸레버가 왜 지배하는지 한눈에 보인다.
        """),
            code("""
        fig, (ax, bx) = plt.subplots(1, 2, figsize=(11, 4.2))

        labels = ["Interior", "Cantilever"]
        parts = [
            ("DC", [1.25 * m_dc, 1.25 * m_dc_c], "#5b6472"),
            ("DW", [1.50 * m_dw, 1.50 * m_dw_c], "#a8681a"),
            ("LL + IM", [1.80 * (m_ll + m_im), 1.80 * (m_ll_c + m_im_c)], "#b3372c"),
        ]
        bottom = np.zeros(2)
        for name, vals, col in parts:
            ax.bar(labels, vals, 0.5, bottom=bottom, label=name, color=col)
            bottom += np.array(vals)
        ax.plot(labels, [m_rd, m_rd_c], "D", color="#1f7a4d", ms=11, label="M_Rd")
        ax.set_ylabel("Moment (kN.m/m)")
        ax.set_title("Design moment vs capacity")
        ax.legend(fontsize=9)

        names = ["DC", "DW", "LL + IM", "M_Ed"]
        ratios = [m_dc_c / m_dc, m_dw_c / m_dw,
                  (m_ll_c + m_im_c) / (m_ll + m_im), m_ed_c / m_ed]
        cols = ["#5b6472", "#a8681a", "#b3372c", "#1f6feb"]
        bx.bar(names, ratios, 0.55, color=cols)
        bx.axhline(1.0, color="k", lw=0.9)
        bx.set_ylabel("Cantilever / Interior")
        bx.set_title("What actually grows on the cantilever")
        for i, v in enumerate(ratios):
            bx.text(i, v + 0.06, f"×{v:.2f}", ha="center", fontsize=10)
        bx.set_ylim(0, max(ratios) * 1.25)

        grow_ll = 1.80 * ((m_ll_c + m_im_c) - (m_ll + m_im)) / (m_ed_c - m_ed) * 100
        print(f"M_Ed 증가분 {m_ed_c - m_ed:.1f} kN·m/m 중 활하중이 {grow_ll:.0f} % 를 차지한다.")
        print(f"고정하중의 몫은 {(m_dc + m_dw) / total * 100:.0f} % 에서 "
              f"{(m_dc_c + m_dw_c) / (m_dc_c + m_dw_c + m_ll_c + m_im_c) * 100:.0f} % 로 늘 뿐이다.")
        """),
            md(r"""
        방호벽 자중 때문에 캔틸레버가 지배한다고 생각하기 쉽지만, 숫자는 다르게
        말한다. 고정하중 몫은 13 % 에서 19 % 로 늘 뿐이고, **M_Ed 증가분의
        82 % 는 활하중**이다.

        활하중이 정확히 2배가 되는 이유는 둘이다.

        - 내측부는 연속판이라 정모멘트에 **0.8배**를 받지만, 캔틸레버는 그
          혜택이 없다.
        - 캔틸레버의 윤하중은 폭 $E = 1.94$ m 에만 퍼진 채 1.0 m 지렛대 팔로
          걸린다.

        방호벽이 기여하는 것은 M_Ed 증가분의 15 % 다. 적지 않지만 주범은
        아니다.

        ## ⑦ 배력철근과 ⑧ 사용성
        """),
            code("""
        ratio = distribution_steel_ratio(span=span)
        as_dist = ratio * as_prov

        print(f"배력철근 비율   120/√L = {120 / math.sqrt(span):.1f} % -> 상한 {ratio * 100:.0f} %")
        print(f"소요            {as_dist:.0f} mm²/m")
        print(f"  D13 -> 간격 {bar_area(diameter=13.0) * 1000 / as_dist:.0f} mm 이하")
        print()

        for label, m_s, a_s, d_eff, dia, sp in (
            ("내측부", m_ser, as_prov, d_in, dia_in, spacing_in),
            ("캔틸레버", m_ser_c, as_prov_c, d_c, dia_c, spacing_c),
        ):
            f_s = steel_stress(m_s, a_s, d_eff)
            s_lim = max_bar_spacing(f_s=f_s)
            d_lim = max_bar_diameter(f_s=f_s)
            ok = "만족" if sp <= s_lim and dia <= d_lim else "불만족"
            print(f"{label:>8}  f_s {f_s:5.1f} MPa  허용간격 {s_lim:5.0f} (배치 {sp:.0f})  "
                  f"허용지름 {d_lim:4.1f} (D{dia:.0f})  {ok}")

        print()
        print(f"처짐 한계   L/800 = {deck_deflection_limit(span=span * 1000):.1f} mm")
        print("피로        검증 불필요 (4.6.5.1(3))")
        print("전단        검토 생략 가능 (KDS 24 10 11 4.6.2.2(3))")
        """),
            md(r"""
        ## ⑨ KDS 14 로 풀면

        하중은 어느 쪽이든 KDS 24 12 21 로 구한다 — 교량이니 KL-510 말고는 쓸
        것이 없다. 갈리는 것은 단면 저항 쪽뿐이다.
        """),
            code("""
        def required_steel_kds14(m_u, d, phi=0.85):
            \"\"\"같은 M_u 를 KDS 14 강도설계법으로 풀어 필요 철근량을 구한다.\"\"\"
            _, eta, _ = stress_block_parameters(fck=FCK)
            k = FY / (eta * 0.85 * FCK * 1000.0)
            a2, a1 = phi * k * FY / 2.0, -phi * FY * d
            return (-a1 - math.sqrt(a1**2 - 4 * a2 * m_u)) / (2 * a2)


        print(f"{'단면':>10}  {'M_Ed':>8}  {'KDS 24':>10}  {'KDS 14':>10}  {'차이':>7}")
        for label, m, d_eff in (("내측부", m_ed, d_in), ("캔틸레버", m_ed_c, d_c)):
            a24 = required_steel_area(m_ed=m * 1e6, d=d_eff)
            a14 = required_steel_kds14(m * 1e6, d_eff)
            print(f"{label:>10}  {m:6.2f}  {a24:8.0f} mm²  {a14:8.0f} mm²  "
                  f"{(a24 / a14 - 1) * 100:+6.1f} %")
        """),
            md(r"""
        ## 설계 요약

        | 항목 | 값 |
        |---|---|
        | 바닥판 두께 | 240 mm (내측) / 280 mm (캔틸레버 고정단, 헌치) |
        | 주철근 | D16@150 (하부, 교축직각방향) |
        | 캔틸레버 상부철근 | D19@125 |
        | 배력철근 | D13@148 이하 |
        | 공칭피복 | 55 mm (ED1, 제설염) |
        | 콘크리트 | $f_{ck}$ 27 MPa (KDS 24 10 11 4.6.2.2(2)) |
        | 철근 | SD400 이상 (4.6.5.2(5)①) |

        **이 예제에서 얻을 것**

        1. 바닥판은 트럭을 굴리지 않는다. 식 $(4.6\text{-}1)$ 한 줄이면 된다.
        2. 캔틸레버의 설계휨모멘트가 내측부의 **2.1 배**다. 증가분의 82 % 는
           방호벽이 아니라 **활하중**이다 — 연속판의 0.8배 혜택이 없고, 윤하중이
           좁은 폭에 1.0 m 지렛대 팔로 걸리기 때문이다. 고정단 헌치는 그 결과다.
        3. 노출등급 ED1 의 피복 55 mm 가 유효깊이를 63 mm 나 깎는다. 내구성의
           대가는 강도로 치른다.
        4. 전단은 검토하지 않아도 되지만(4.6.2.2(3)), 이는 근사식이 이미 그
           범위에서 보정되었다는 전제 위에서다.

        방호벽에 작용하는 **차량 충돌하중**(KDS 24 90 11, 극단상황한계상태)은
        이 예제의 범위 밖이다. 실제 설계에서는 캔틸레버 상부철근이 충돌하중으로
        결정되는 경우가 많다.
        """),
        ],
    )


def nb_18_girder_design():
    """예제 18 - PSC I형 거더 설계 (KDS 24)."""
    return write(
        "18_girder_design",
        [
            md(r"""
        # 18 · PSC I형 거더 설계 — KDS 24 한계상태설계법

        지간 30 m 단순 지지 PSC 거더교의 주형을 설계한다. 예제 17 에서 설계한
        바닥판이 이 거더 위에 얹히므로, **합성 전후로 저항 단면이 달라지는 것**이
        핵심이다.

        ```
        ① 거더 단면과 합성 단면     KDS 24 14 21 4.6
        ② 하중과 저항 단면          KDS 24 12 21 4.3, KDS 24 12 11 표 4.1-1
        ③ 도입응력 한계             KDS 24 14 21 1.5.7.2, 1.5.7.3
        ④ 프리스트레스 손실         KDS 24 14 21 1.5.7.4, 1.5.7.5, 3.3.2(7)
        ⑤ 사용한계상태 응력         KDS 24 14 21 4.2.2
        ⑥ 극한한계상태 휨           KDS 24 14 21 4.1.1
        ⑦ 텐던 배치와 핵거리        KDS 24 14 21 1.5.7.3
        ⑧ 강연선 수량 결정
        ⑨ KDS 14 대조
        ```

        :::{warning}
        여기 쓰는 단면은 **예시이며 어떤 표준도도 아니다.** 실제 설계에는 해당
        표준도나 제작사 제원을 써야 한다.
        :::

        원리를 그림으로 따라가려면
        [강의 L5](../lectures/L5_PSC거더설계.ipynb) 를, 값을 슬라이더로 바꿔
        보려면 [대화형 탐색기](../_static/explorer.html)의 L5 탭을 연다.
        """),
            code(SETUP),
            code("""
        from concreteproperties_kds.kds import stress_block_parameters
        from concreteproperties_kds.kds24 import (
            COMBINATIONS_BY_NAME, EXAMPLE_SECTIONS, GAMMA_CONCRETE,
            TENDON_COVER, characteristic_tensile_strength,
            design_compressive_strength, design_girder, design_yield_strength,
            elastic_modulus, equivalent_block, girder_live_load,
            max_jacking_stress, stress_after_transfer,
        )

        # 교량 제원
        SPAN, GIRDER_SPACING = 30.0, 2.5
        DECK_THICKNESS, HAUNCH = 240.0, 50.0
        FCK, FCK_TRANSFER, FCK_DECK = 40.0, 30.0, 27.0
        FPU, FPY, STRAND_AREA = 1860.0, 1600.0, 138.7
        N_STRAND = 25
        W_SDL, DIST_FACTOR = 3.0, 0.6

        SECTION = EXAMPLE_SECTIONS["PSC-I 2.0m"]
        a_p = N_STRAND * STRAND_AREA
        props = SECTION.properties()

        result = design_girder(
            section=SECTION, span=SPAN, girder_spacing=GIRDER_SPACING,
            deck_thickness=DECK_THICKNESS, haunch=HAUNCH,
            fck=FCK, fck_transfer=FCK_TRANSFER, fck_deck=FCK_DECK,
            a_p=a_p, fpu=FPU, fpy=FPY,
            w_sdl=W_SDL, distribution_factor=DIST_FACTOR,
        )
        print(f"{SECTION.name}  지간 {SPAN:.0f} m  강연선 {N_STRAND} 가닥")
        """),

            md(r"""
        ## ① 거더 단면과 합성 단면

        바닥판은 강도가 낮으므로 **탄성계수비로 폭을 환산**해 붙인다.
        """),
            code("""
        n_ratio = elastic_modulus(fck=FCK_DECK) / elastic_modulus(fck=FCK)
        comp = result.composite

        print(f"탄성계수비  n = {n_ratio:.4f}")
        print()
        print(f"{'':10} {'A (m²)':>9} {'y_b (mm)':>10} {'I (m⁴)':>9} {'Z_b (m³)':>10}")
        for label, s in [("거더 단독", props), ("합성 단면", comp)]:
            print(f"{label:10} {s.area / 1e6:9.3f} {s.y_b:10.0f} "
                  f"{s.inertia / 1e12:9.4f} {s.z_b / 1e9:10.4f}")
        print()
        print(f"합성으로 하연 단면계수가 {comp.z_b / props.z_b:.2f} 배가 된다.")
        """),

            md(r"""
        ## ② 하중과 저항 단면

        거더를 먼저 놓고 바닥판을 나중에 치므로, **하중마다 저항하는 단면이
        다르다.** 굳지 않은 바닥판 콘크리트는 하중이지 단면이 아니다.
        """),
            code("""
        w_girder = GAMMA_CONCRETE * props.area / 1e6
        w_deck = GAMMA_CONCRETE * GIRDER_SPACING * DECK_THICKNESS / 1000.0
        m_girder = w_girder * SPAN**2 / 8.0
        m_deck = w_deck * SPAN**2 / 8.0
        m_sdl = W_SDL * SPAN**2 / 8.0
        live = girder_live_load(span=SPAN)
        m_live = live.moment * DIST_FACTOR
        total = m_girder + m_deck + m_sdl + m_live

        print(f"{'하중':16} {'M (kN·m)':>10} {'몫':>7}  저항 단면")
        for label, m, sec in [
            ("거더 자중", m_girder, "거더 단독"),
            ("굳지 않은 바닥판", m_deck, "거더 단독"),
            ("2차 고정하중", m_sdl, "합성 단면"),
            ("활하중 + 충격", m_live, "합성 단면"),
        ]:
            print(f"{label:16} {m:10.0f} {m / total * 100:6.1f} %  {sec}")
        print(f"{'합계':16} {total:10.0f}")
        print()
        print(f"활하중은 {live.governed_by} 가 지배한다.")
        print(f"거더 단독이 받는 몫 {(m_girder + m_deck) / total * 100:.1f} % "
              "— 합성의 이득은 나머지에만 미친다.")
        print()
        m_dc = m_girder + m_deck + m_sdl
        print(f"극한Ⅰ  M_Ed = 1.25 x {m_dc:.0f} + 1.80 x {m_live:.0f} "
              f"= {result.m_ed:.0f} kN·m")
        """),

            md(r"""
        ## ③ 도입응력의 상한 — 그리고 읽기가 갈리는 조문

        식 $(1.5\text{-}7)$ 은 명확하다. 그런데 바로 다음 식
        $(1.5\text{-}9)$ 는 **두 가지로 읽힌다.**
        """),
            code("""
        f_jack = max_jacking_stress(fpu=FPU, fpy=FPY)
        print(f"식 (1.5-7)  f_o,max = min(0.80 x {FPU:.0f}, 0.90 x {FPY:.0f}) "
              f"= {f_jack:.0f} MPa")
        print(f"  항복비 f_py/f_pu = {FPY / FPU:.3f} < 0.889 이므로 f_py 가 지배")
        print()

        lit = stress_after_transfer(fpy=FPY)
        en = stress_after_transfer(fpy=FPY, fpu=FPU, reading="EN")
        f_pi = result.losses.f_pi
        immediate = result.losses.immediate_ratio

        print("식 (1.5-9)  도입 직후 f_pmo")
        print(f"  원문대로  min(0.75 f_py, 0.85 f_py) = {lit:.0f} MPa")
        print(f"  EN 해석   min(0.75 f_pu, 0.85 f_py) = {en:.0f} MPa")
        print(f"  계산된 f_pi = {f_pi:.0f} MPa  ->  "
              f"원문 {'만족' if f_pi <= lit else '초과'}, "
              f"EN {'만족' if f_pi <= en else '초과'}")
        print()
        print(f"  원문대로면 즉시손실이 {(1 - lit / f_jack) * 100:.1f} % 를 넘어야 하는데,")
        print(f"  이 거더는 {immediate * 100:.1f} % 다. 즉 식 (1.5-9) 가")
        print(f"  식 (1.5-7) 의 상한을 {lit / (1 - immediate):.0f} MPa 로 끌어내린다.")
        """),

            md(r"""
        :::{warning}
        이 노트북은 **EN 해석**(`transfer_reading="EN"`, `design_girder` 의
        기본값)을 쓴다. 이는 해석상의 선택이며, 실무에서는 발주자·감리와
        맞추어야 한다. 원문 그대로 검토하려면
        `design_girder(..., transfer_reading="원문")` 으로 부른다.
        :::

        ## ④ 프리스트레스 손실

        가장 큰 손실은 크리프도 건조수축도 아닌 **마찰**이다. 그리고 마찰은
        설계자가 텐던 배치로 줄일 수 있는 유일한 큰 손실이다.
        """),
            code("""
        losses = result.losses
        print(f"긴장응력                  {losses.f_jack:8.1f} MPa")
        for label, value in [("마찰 (1.5-11)", losses.friction),
                             ("정착장치 활동", losses.anchorage),
                             ("탄성변형 (1.5-10)", losses.elastic)]:
            print(f"  - {label:20} {value:8.1f} MPa  "
                  f"({value / losses.f_jack * 100:4.1f} %)")
        print(f"도입 직후 f_pi            {losses.f_pi:8.1f} MPa  "
              f"즉시손실 {losses.immediate_ratio * 100:.1f} %")
        print(f"  - {'장기 (1.5-12)':20} {losses.long_term:8.1f} MPa  "
              f"({losses.long_term / losses.f_jack * 100:4.1f} %)")
        print(f"유효응력 f_pe             {losses.f_pe:8.1f} MPa  "
              f"총손실   {losses.total_ratio * 100:.1f} %")
        print()
        print(f"P_i = {result.p_i / 1e3:.0f} kN   P_e = {result.p_e / 1e3:.0f} kN")
        """),
            code("""
        fig, ax = plt.subplots(figsize=(9, 3.8))

        level = losses.f_jack
        ax.bar(0, level, color="#5b6472", width=0.6)
        ax.text(0, level + 25, f"{level:.0f}", ha="center", fontsize=9)
        for i, d in enumerate([losses.friction, losses.anchorage,
                               losses.elastic, losses.long_term], start=1):
            ax.bar(i, d, bottom=level - d, color="#b3372c", width=0.6)
            ax.text(i, level + 25, f"-{d:.0f}", ha="center", fontsize=9,
                    color="#b3372c")
            level -= d
        ax.bar(5, level, color="#1f6feb", width=0.6)
        ax.text(5, level + 25, f"{level:.0f}", ha="center", fontsize=9,
                color="#1f6feb")

        ax.set_xticks(range(6))
        ax.set_xticklabels(["긴장", "마찰", "정착", "탄성", "장기", "유효"])
        ax.set_ylabel("긴장재 응력 (MPa)")
        ax.set_title(f"프리스트레스 손실 - 총 {losses.total_ratio * 100:.1f} %")
        ax.set_ylim(0, losses.f_jack * 1.18)
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        """),

            md(r"""
        ## ⑤ 사용한계상태 응력

        긴장 직후에는 하연이 눌리고, 사용 시에는 하중이 그것을 되돌린다.
        """),
            code("""
        print(f"{'단계':14} {'상연':>9} {'하연':>9}   "
              f"{'압축 한계':>10} {'인장 한계':>10}")
        for key in ("긴장 직후", "지속하중", "사용"):
            top, bot = result.stresses[key]
            hi, lo = result.limits[key]
            print(f"{key:14} {top:9.2f} {bot:9.2f}   {hi:10.2f} {lo:10.2f}")
        print()
        f_ctk = characteristic_tensile_strength(fck=FCK)
        print(f"사용 시 하연 인장 {-result.stresses['사용'][1]:.2f} MPa "
              f"<= f_ctk {f_ctk:.2f} MPa  ->  비균열")
        """),

            md(r"""
        ## ⑥ 극한한계상태 휨
        """),
            code("""
        shape = "바닥판을 넘어 T형" if result.flanged else "바닥판 안 (직사각형)"
        print(f"압축부가 {shape},  중립축 c = {result.c_n:.0f} mm")
        print(f"M_Rd = {result.m_rd:.0f} >= M_Ed = {result.m_ed:.0f} kN·m"
              f"   여유 {result.m_rd / result.m_ed:.2f} 배")
        """),

            md(r"""
        ## ⑦ 텐던 배치 — 왜 휘어 올리는가

        지간 중앙에서는 편심이 클수록 좋다. 그런데 **단부에서는 자중 모멘트가
        0** 이라 프리스트레스가 만드는 상연 인장을 상쇄할 것이 없다.
        """),
            code("""
        z_t = props.inertia / props.y_t
        kern = z_t / props.area
        f_ctk_t = characteristic_tensile_strength(fck=FCK_TRANSFER)
        e_mid = props.y_b - TENDON_COVER
        top_end = result.p_i / props.area - result.p_i * e_mid / z_t

        print(f"핵거리  Z_t / A = {kern:.0f} mm")
        print(f"중앙 편심        {e_mid:.0f} mm")
        print()
        print(f"중앙 편심을 단부까지 끌고 가면 상연 {top_end:.2f} MPa,")
        print(f"즉 인장 {-top_end:.2f} MPa > 긴장 시 f_ctk {f_ctk_t:.2f} MPa")
        print()
        print(f"-> 단부에서 편심을 핵거리 {kern:.0f} mm 안으로 드레이프해야 한다.")
        """),
            code("""
        fig, ax = plt.subplots(figsize=(9.5, 4.0))

        x = np.linspace(0, SPAN, 200)
        w_self = GAMMA_CONCRETE * props.area / 1e6
        m_self = w_self * x * (SPAN - x) / 2.0
        p = result.p_i

        e_zero = z_t / props.area + m_self * 1e6 / p     # 영응력 상한
        ax.fill_between(x, 0, np.minimum(e_zero, e_mid), color="#1f6feb",
                        alpha=0.13, label="텐던을 둘 수 있는 영역")
        ax.plot(x, e_zero, color="#b3372c", lw=2, label="상한 - 단부 상연 영응력")
        ax.axhline(e_mid, color="#1f7a4d", lw=2, ls="--",
                   label=f"상한 - 하부플랜지 기하 ({e_mid:.0f} mm)")
        ax.axhline(kern, color="#888", lw=1.2, ls=":",
                   label=f"핵거리 {kern:.0f} mm")

        e_drape = kern + (e_mid - kern) * (1 - (1 - 2 * x / SPAN) ** 2)
        ax.plot(x, e_drape, color="#111", lw=2.2, label="포물선 드레이프 (예)")

        ax.set_xlabel("지간 방향 위치 (m)")
        ax.set_ylabel("편심 e (mm)")
        ax.set_title("텐던이 지나야 할 통로")
        ax.set_xlim(0, SPAN)
        ax.set_ylim(0, e_mid * 1.4)
        ax.legend(fontsize=8.5, ncol=2, loc="upper center")
        ax.grid(alpha=0.3)
        fig.tight_layout()
        """),

            md(r"""
        ## ⑧ 지간별 최소 강연선 수량

        지간마다 가닥 수를 1 개씩 늘려 모든 한계상태를 만족하는 최소값을 찾고,
        한 가닥 모자랄 때 무엇이 깨지는지 기록한다.
        """),
            code("""
        CASES = [("PSC-I 1.4m", 20.0), ("PSC-I 1.7m", 25.0),
                 ("PSC-I 2.0m", 30.0), ("PSC-I 2.0m", 35.0),
                 ("PSC-I 2.3m", 40.0), ("PSC-I 2.7m", 45.0),
                 ("PSC-I 2.7m", 50.0)]

        table = []
        for name, span in CASES:
            section = EXAMPLE_SECTIONS[name]
            for n in range(6, 141):
                trial = design_girder(section=section, span=span,
                                      a_p=n * STRAND_AREA)
                if trial.adequate:
                    break
            short = design_girder(section=section, span=span,
                                  a_p=(n - 1) * STRAND_AREA)
            gov = ", ".join(k for k, v in short.checks.items() if not v)
            table.append((name, span, n, trial, gov))

        print(f"{'단면':12} {'지간':>5} {'가닥':>5} {'손실':>7} "
              f"{'M_Rd/M_Ed':>10}  한 가닥 모자랄 때")
        for name, span, n, trial, gov in table:
            print(f"{name:12} {span:5.0f} {n:5d} "
                  f"{trial.losses.total_ratio * 100:6.1f} % "
                  f"{trial.m_rd / trial.m_ed:10.2f}  {gov}")
        """),

            md(r"""
        **짧은 지간은 극한 휨강도가, 35 m 이상은 사용한계상태 균열이 수량을
        정한다.** 극한 여유가 1.09 ~ 1.14 배로 남는데도 강연선을 더 넣어야
        한다. 한계상태설계법이라고 해서 극한이 항상 지배하는 것이 아니다.

        ## ⑨ KDS 14 강도설계법과의 대조
        """),
            code("""
        d_p = SECTION.height + HAUNCH + DECK_THICKNESS - TENDON_COVER
        b_eff = GIRDER_SPACING * 1000.0

        alpha_eq, beta_eq = equivalent_block(fck=FCK_DECK)
        lam = 2.0 * beta_eq
        eta24 = alpha_eq / lam
        f_cd = design_compressive_strength(fck=FCK_DECK)
        f_pd = design_yield_strength(fy=FPY)
        t24 = a_p * f_pd
        a24 = t24 / (eta24 * f_cd * b_eff)
        m_rd24 = t24 * (d_p - a24 / 2.0) / 1e6

        _, eta14, _ = stress_block_parameters(fck=FCK_DECK)
        t14 = a_p * FPY
        a14 = t14 / (eta14 * 0.85 * FCK_DECK * b_eff)
        m_n = t14 * (d_p - a14 / 2.0) / 1e6

        print(f"유효깊이 d_p = {d_p:.0f} mm,  b_eff = {b_eff:.0f} mm")
        print()
        print(f"{'':8} {'강재':>9} {'콘크리트':>10} {'a (mm)':>9} {'강도':>12}")
        print(f"{'KDS 24':8} {f_pd:9.0f} {f_cd:10.2f} {a24:9.0f} {m_rd24:12.0f}")
        print(f"{'KDS 14':8} {FPY:9.0f} {eta14 * 0.85 * FCK_DECK:10.2f} "
              f"{a14:9.0f} {m_n:12.0f}")
        print(f"{'':8} {'':9} {'':10} {'x 0.85':>9} {0.85 * m_n:12.0f}")
        print()
        gap = m_rd24 / (0.85 * m_n)
        print(f"KDS 24 / KDS 14 = {gap:.3f}  ({(gap - 1) * 100:+.1f} %)")
        """),

            md(r"""
        휨은 **강재의 인장력이 지배**하므로 KDS 24 의 $\phi_s = 0.90$ 이
        KDS 14 의 단면 $\phi = 0.85$ 보다 덜 깎는다. 콘크리트에 걸린 0.65 는
        압축블록을 깊게 할 뿐(97 → 138 mm) 팔길이를 조금 줄이는 데 그친다.

        L2 에서 본 철근콘크리트 보의 $+3.9\,\%$ 와 같은 방향, 비슷한 크기다.

        :::{note}
        두 기준의 **안전율 배치**만 견주려고 강재 응력을 양쪽 모두 $f_{py}$ 로
        두었다. 실제 KDS 14 설계에서는 부착 긴장재의 극한 응력 $f_{ps}$ 를
        따로 산정한다.
        :::

        ## 설계 요약
        """),
            code("""
        print(f"거더        {SECTION.name}, 지간 {SPAN:.0f} m, "
              f"간격 {GIRDER_SPACING:.1f} m")
        print(f"콘크리트     거더 {FCK:.0f} / 긴장 시 {FCK_TRANSFER:.0f} / "
              f"바닥판 {FCK_DECK:.0f} MPa")
        print(f"긴장재       15.2 mm x {N_STRAND} 가닥 (A_p {a_p:.0f} mm²), "
              f"e = {props.y_b - TENDON_COVER:.0f} mm")
        print(f"프리스트레스  P_i {result.p_i / 1e3:.0f} -> "
              f"P_e {result.p_e / 1e3:.0f} kN "
              f"(손실 {losses.total_ratio * 100:.1f} %)")
        print()
        for name, ok in result.checks.items():
            print(f"  {'만족  ' if ok else '불만족'}  {name}")
        print(f"\\n종합 판정: {'만족' if result.adequate else '불만족'}")
        """),

            md(r"""
        ## 정리

        1. **넣은 프리스트레스의 21 % 가 사라진다.** 가장 큰 몫은 마찰(7.9 %)
           이고, 이것이 설계자가 배치로 줄일 수 있는 유일한 큰 손실이다.
        2. **하중의 59 % 는 합성 단면의 혜택을 못 받는다.** 거더 자중과 바닥판이
           합성 전에 실리기 때문이다.
        3. **단부와 중앙의 허용 편심이 다르다.** 중앙 762 mm, 단부 457 mm —
           이 차이가 텐던을 휘게 만든다.
        4. **35 m 를 넘으면 사용한계상태가 단면을 정한다.** 극한 휨강도가
           남는데도 그렇다.
        5. **식 $(1.5\text{-}9)$ 는 읽기가 갈린다.** 원문대로면 이 거더가
           걸리고, EN 해석이면 통과한다. 설계 전에 정해 두어야 할 사항이다.
        """),
        ],
    )


if __name__ == "__main__":
    builders = [
        nb_01_materials,
        nb_02_area_properties,
        nb_03_cracked_properties,
        nb_04_ultimate_bending,
        nb_05_moment_interaction,
        nb_06_biaxial_bending,
        nb_07_moment_curvature,
        nb_08_stress_analysis,
        nb_09_loads,
        nb_10_shear_torsion,
        nb_11_serviceability,
        nb_12_durability,
        nb_13_detailing,
        nb_14_slender_column,
        nb_15_biaxial_simplified,
        nb_16_prestressed,
        nb_17_deck_design,
        nb_18_girder_design,
    ]

    paths = []
    for build in builders:
        path = build()
        paths.append(path)
        print(f"생성  {path.relative_to(path.parents[2])}")

    if "--run" in sys.argv:
        print("\n노트북 실행")
        failed = execute(paths)
        sys.exit(1 if failed else 0)
