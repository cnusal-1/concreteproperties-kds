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
    return write("01_materials", [
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
    ])


def nb_02_area_properties():
    """예제 02 - 단면 제원."""
    return write("02_area_properties", [
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
    ])


def nb_03_cracked_properties():
    """예제 03 - 균열단면."""
    return write("03_cracked_properties", [
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
    ])


def nb_04_ultimate_bending():
    """예제 04 - 설계 휨강도."""
    return write("04_ultimate_bending", [
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
    ])


def nb_05_moment_interaction():
    """예제 05 - P-M 상관도."""
    return write("05_moment_interaction", [
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
    ])


def nb_06_biaxial_bending():
    """예제 06 - 2축 휨 상관도."""
    return write("06_biaxial_bending", [
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
    ])


def nb_07_moment_curvature():
    """예제 07 - 모멘트-곡률."""
    return write("07_moment_curvature", [
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
    ])


def nb_08_stress_analysis():
    """예제 08 - 응력 해석."""
    return write("08_stress_analysis", [
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
    ])


def nb_09_loads():
    """예제 09 - 하중조합."""
    return write("09_loads", [
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
    ])


def nb_10_shear_torsion():
    """예제 10 - 전단과 비틀림."""
    return write("10_shear_torsion", [
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
    ])


def nb_11_serviceability():
    """예제 11 - 처짐과 균열."""
    return write("11_serviceability", [
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
    ])


def nb_12_durability():
    """예제 12 - 내구성과 피복두께."""
    return write("12_durability", [
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
    ])


def nb_13_detailing():
    """예제 13 - 정착과 이음."""
    return write("13_detailing", [
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
    ])


def nb_14_slender_column():
    """예제 14 - 세장 기둥."""
    return write("14_slender_column", [
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
    ])


def nb_15_biaxial_simplified():
    """예제 15 - 2축 휨 간략식."""
    return write("15_biaxial_simplified", [
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
    ])


def nb_16_prestressed():
    """예제 16 - 프리스트레스트 콘크리트."""
    return write("16_prestressed", [
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
    ])


def nb_17_full_design():
    """예제 17 - 보 종합 설계."""
    return write("17_full_design", [
        md("""
        # 17 · 보 종합 설계 — 하중조합부터 상세까지

        400 × 700 보(8 m 경간)를 KDS 의 검토 순서대로 설계한다.

        ```
        ① 하중조합      KDS 14 20 10 4.2.2
        ② 내구성·피복   KDS 14 20 40, KDS 14 20 50 4.3
        ③ 재료·단면     KDS 14 20 10 4.3, KDS 14 20 20 4.1.1
        ④ 휨 설계       KDS 14 20 20 4.1.2, 4.2.2
        ⑤ 전단 설계     KDS 14 20 22 4.2, 4.3
        ⑥ 사용성        KDS 14 20 30 4.2, KDS 14 20 20 4.2.3
        ⑦ 정착·이음     KDS 14 20 52
        ```
        """),
        code(SETUP),
        code("""
        from concreteproperties import ConcreteSection
        from sectionproperties.pre.library import concrete_rectangular_section

        from concreteproperties_kds import KDS
        from concreteproperties_kds.detailing import (
            bar_area, minimum_bar_spacing, minimum_cover, summarise_detailing,
        )
        from concreteproperties_kds.durability import check_durability
        from concreteproperties_kds.kds import minimum_flexural_moment
        from concreteproperties_kds.loads import print_combinations, required_strength
        from concreteproperties_kds.serviceability import (
            check_crack_control, check_deflection, minimum_thickness,
        )
        from concreteproperties_kds.shear import check_shear, required_stirrup_spacing

        SPAN, B, H = 8000.0, 400.0, 700.0
        FCK, FY, EXPOSURE = 27.0, 400.0, "EC3"
        MAIN_BAR, STIRRUP, N_BOT, N_TOP = "D25", "D13", 5, 2
        """),
        md("""
        ## ① 하중조합 (KDS 14 20 10 4.2.2)
        """),
        code("""
        loads = {"D": 22.0, "L": 14.0, "S": 3.0}
        print_combinations(loads=loads)

        w_u, governing = required_strength(loads=loads)
        m_u = w_u * (SPAN / 1000.0) ** 2 / 8 * 1e6
        v_u = w_u * (SPAN / 1000.0) / 2 * 1e3

        print()
        print(f"지배 {governing.name} (식 {governing.equation}) : wu = {w_u:.2f} kN/m")
        print(f"Mu = {m_u / 1e6:.2f} kN.m,  Vu = {v_u / 1e3:.2f} kN")

        m_sustained = loads["D"] * (SPAN / 1000.0) ** 2 / 8 * 1e6
        m_live = loads["L"] * (SPAN / 1000.0) ** 2 / 8 * 1e6
        """),
        md("""
        ## ② 내구성과 피복두께 (KDS 14 20 40, KDS 14 20 50 4.3)
        """),
        code("""
        cover_structural = minimum_cover(condition="옥내_보기둥", fck=FCK)

        dur = check_durability(
            exposure_class=EXPOSURE, fck=FCK,
            cover=cover_structural, cover_min=cover_structural,
            water_binder_ratio=0.48,
        )
        dur.print_results()

        d_stirrup, d_main = 12.7, 25.4
        cover_to_centre = cover_structural + d_stirrup + d_main / 2
        d_eff = H - cover_to_centre

        print()
        print(f"철근 중심까지 = {cover_to_centre:.1f} mm,  유효깊이 d = {d_eff:.1f} mm")
        """),
        md("""
        ## ③ 재료와 단면
        """),
        code("""
        kds = KDS(column_type="tie")
        conc = kds.create_concrete_material(compressive_strength=FCK)
        steel = kds.create_steel_material(yield_strength=FY)

        geom = concrete_rectangular_section(
            d=H, b=B,
            dia_top=15.9, area_top=bar_area("D16"), n_top=N_TOP,
            c_top=cover_to_centre,
            dia_bot=d_main, area_bot=bar_area(MAIN_BAR), n_bot=N_BOT,
            c_bot=cover_to_centre,
            n_circle=16, conc_mat=conc, steel_mat=steel,
        )
        conc_sec = ConcreteSection(geom)
        kds.assign_concrete_section(conc_sec)

        a_s = N_BOT * bar_area(MAIN_BAR)
        clear_spacing = (
            B - 2 * cover_structural - 2 * d_stirrup - N_BOT * d_main
        ) / (N_BOT - 1)
        s_min = minimum_bar_spacing(bar=MAIN_BAR, member="보", aggregate_size=25)

        print(f"단면 {B:.0f} x {H:.0f},  인장 {N_BOT}-{MAIN_BAR} = {a_s:.0f} mm^2")
        print(f"{conc.name},  Ec = {conc.elastic_modulus:,.0f} MPa")
        print(f"철근 순간격 {clear_spacing:.1f} mm >= 최소 {s_min:.1f} mm"
              f"  {'만족' if clear_spacing >= s_min else '불만족'}")

        conc_sec.plot_section()
        """),
        md("""
        ## ④ 휨 설계 (KDS 14 20 20)
        """),
        code("""
        f_res, u_res, phi = kds.ultimate_bending_capacity(theta=0, n_design=0)
        eps_t = kds.net_tensile_strain(theta=0, d_n=u_res.d_n)

        print(f"중립축 깊이   c      = {u_res.d_n:8.2f} mm")
        print(f"순인장변형률  et     = {eps_t:8.5f}  "
              f"({kds.section_classification(eps_t=eps_t)})")
        print(f"강도감소계수  phi    = {phi:8.3f}")
        print(f"설계 휨강도 phi*Mn   = {f_res.m_x / 1e6:8.2f} kN.m")
        print(f"소요 휨모멘트  Mu    = {m_u / 1e6:8.2f} kN.m")
        print(f"소요/강도            = {m_u / f_res.m_x:8.3f}"
              f"  {'만족' if f_res.m_x >= m_u else '불만족'}")
        print()

        _, eps_min, ok_duct = kds.check_flexural_ductility()
        phi_m_n, m_cr, _, ok_min = kds.check_minimum_flexural_reinforcement()
        print(f"최소허용변형률 et,min = {eps_min:8.5f}  "
              f"{'만족' if ok_duct else '불만족'}   (4.1.2(5))")
        print(f"최소 철근량  1.2*Mcr  = "
              f"{minimum_flexural_moment(m_cr=m_cr) / 1e6:8.2f} kN.m  "
              f"{'만족' if ok_min else '불만족'}   (4.2.2)")
        """),
        md("""
        ## ⑤ 전단 설계 (KDS 14 20 22)
        """),
        code("""
        a_v = 2 * bar_area(STIRRUP)
        s_req = required_stirrup_spacing(
            v_u=v_u, fck=FCK, b_w=B, d=d_eff, a_v=a_v, fyt=FY
        )
        s_use = min(25.0 * int(s_req / 25.0), 250.0)

        print(f"스터럽 {STIRRUP} 2가닥, 필요 {s_req:.1f} mm -> 배치 {s_use:.0f} mm")
        print()

        shear = check_shear(
            v_u=v_u, fck=FCK, b_w=B, d=d_eff, a_v=a_v, s=s_use, fyt=FY
        )
        shear.print_results()
        """),
        md("""
        ## ⑥ 사용성 (KDS 14 20 30)
        """),
        code("""
        h_min = minimum_thickness(span=SPAN, member="보", support="단순지지", fy=FY)
        print(f"최소 두께 l/16 = {h_min:.1f} mm, h = {H:.1f} mm"
              f"  ->  {'생략 가능' if h_min <= H else '처짐 계산 필요'}")
        print()

        gross = kds.get_transformed_gross_properties(
            elastic_modulus=conc.elastic_modulus
        )
        cracked = kds.calculate_cracked_properties(theta=0)
        cracked.calculate_transformed_properties(
            elastic_modulus=conc.elastic_modulus
        )

        defl = check_deflection(
            span=SPAN, m_sustained=m_sustained, m_live=m_live,
            m_cr=cracked.m_cr, i_g=gross.ixx_c, i_cr=cracked.ixx_c_cr,
            e_c=conc.elastic_modulus,
            rho_prime=N_TOP * bar_area("D16") / (B * d_eff),
        )
        defl.print_results()

        bar_spacing = (
            B - 2 * cover_structural - 2 * d_stirrup - d_main
        ) / (N_BOT - 1)
        fs, s_max, ok_crack = check_crack_control(
            bar_spacing=bar_spacing, fy=FY, c_c=cover_structural + d_stirrup
        )
        print()
        print(f"균열 제어  s = {bar_spacing:.1f} <= s,max = {s_max:.1f} mm"
              f"  {'만족' if ok_crack else '불만족'}   (14 20 20 4.2.3(4))")
        """),
        md("""
        ## ⑦ 정착·이음 (KDS 14 20 52)
        """),
        code("""
        summarise_detailing(bar=MAIN_BAR, fy=FY, fck=FCK).print_results()
        """),
        md("""
        ## 설계 요약
        """),
        code("""
        items = [
            ("휨강도 (14 20 20 4.1)", f_res.m_x >= m_u),
            ("연성 (14 20 20 4.1.2(5))", ok_duct),
            ("최소 철근량 (14 20 20 4.2.2)", ok_min),
            ("전단강도 (14 20 22)", shear.ok),
            ("처짐 (14 20 30 4.2)", defl.ok),
            ("균열 제어 (14 20 20 4.2.3)", ok_crack),
            ("내구성 (14 20 40)", dur.ok),
            ("철근 순간격 (14 20 50 4.2)", clear_spacing >= s_min),
        ]

        for name, ok in items:
            print(f"  {name:<32} {'만족' if ok else '불만족'}")
        print()
        print(f"  {'종합':<32} "
              f"{'만족' if all(ok for _, ok in items) else '불만족'}")
        """),
    ])


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
        nb_17_full_design,
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
