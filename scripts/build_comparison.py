"""KDS 14 (강도설계법) 와 KDS 24 (한계상태설계법) 를 비교하는 그림을 만든다.

`docs/user_guide/design_codes/comparison.md` 가 이 그림들을 싣는다. 계산에 쓴
숫자는 그림과 함께 표준출력으로도 내보내, 문서의 표를 손으로 옮길 때 대조할 수
있게 하였다.

사용법::

    python scripts/build_comparison.py
"""

from __future__ import annotations

import glob
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from concreteproperties import ConcreteSection
from matplotlib import font_manager
from sectionproperties.pre.library import concrete_rectangular_section

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from concreteproperties_kds import KDS  # noqa: E402
from concreteproperties_kds import shear as shear14  # noqa: E402
from concreteproperties_kds.kds import (
    parabolic_stress,  # noqa: E402
    stress_block_parameters,  # noqa: E402
)
from concreteproperties_kds.kds24 import (  # noqa: E402
    KDS24,
    PHI_C_ULS,
    PHI_S_ULS,
    design_compressive_strength,
    design_stress,
    design_yield_strength,
    minimum_eccentricity,
)
from concreteproperties_kds.kds24 import shear as shear24  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "docs" / "_static" / "comparison"

# 색 — 두 기준을 문서 전체에서 같은 색으로 쓴다
C14 = "#c0392b"  # KDS 14 (강도설계법)
C24 = "#1f6feb"  # KDS 24 (한계상태설계법)
C_NOMINAL = "#95a5a6"


def use_korean_font() -> str | None:
    """설치된 한글 글꼴을 찾아 matplotlib 에 등록한다."""
    site = Path(
        sys.prefix,
        "lib",
        f"python{sys.version_info.major}.{sys.version_info.minor}",
        "site-packages",
    )
    for pattern in (
        str(site / "koreanize_matplotlib/fonts/*.ttf"),
        "/usr/share/fonts/**/*Nanum*.ttf",
        "/usr/share/fonts/**/*NotoSansCJK*.ot[fc]",
        "/usr/share/fonts/**/*NotoSansKR*.otf",
    ):
        for path in glob.glob(pattern, recursive=True):
            font_manager.fontManager.addfont(path)

    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in (
        "NanumGothic",
        "Malgun Gothic",
        "AppleGothic",
        "Noto Sans CJK KR",
        "Noto Sans KR",
        "WenQuanYi Zen Hei",
    ):
        if name in installed:
            plt.rcParams["font.family"] = name
            return name

    warnings.warn("한글 글꼴을 찾지 못했다.", stacklevel=2)
    return None


D22 = 387.1
D25 = 506.7


def beam(code, fck=40.0, fy=400.0, n_bar=4, d=600.0, b=400.0, n_top=2):
    """같은 형상의 단면을 주어진 설계기준으로 만든다."""
    conc = code.create_concrete_material(compressive_strength=fck)
    steel = code.create_steel_material(yield_strength=fy)
    geom = concrete_rectangular_section(
        d=d,
        b=b,
        dia_top=22,
        area_top=D22,
        n_top=n_top,
        c_top=50,
        dia_bot=22,
        area_bot=D22,
        n_bot=n_bar,
        c_bot=50,
        n_circle=16,
        conc_mat=conc,
        steel_mat=steel,
    )
    code.assign_concrete_section(ConcreteSection(geom))

    return code


# ── 그림 1. 응력-변형률 관계 ───────────────────────────────────────────────
def figure_stress_strain(fck: float = 40.0) -> None:
    """두 기준의 단면설계용 응력-변형률 관계를 겹쳐 그린다."""
    eps_cu, eta, beta_1 = stress_block_parameters(fck=fck)
    f_cd = design_compressive_strength(fck=fck)

    eps = np.linspace(0.0, eps_cu, 400)
    s14 = [parabolic_stress(fck=fck, eps_c=e) for e in eps]
    s24 = [design_stress(fck=fck, eps_c=e) for e in eps]

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(11, 4.2))

    ax.plot(
        eps * 1e3,
        s14,
        color=C14,
        lw=2,
        label=f"KDS 14 포물선-직선 (최대 {0.85 * fck:.1f})",
    )
    ax.plot(eps * 1e3, s24, color=C24, lw=2, label=f"KDS 24 설계곡선 (최대 {f_cd:.1f})")
    ax.axhline(0.85 * fck, color=C14, ls=":", lw=1)
    ax.axhline(f_cd, color=C24, ls=":", lw=1)
    ax.set_xlabel("압축변형률 $\\varepsilon_c$ (‰)")
    ax.set_ylabel("압축응력 (MPa)")
    ax.set_title(f"단면설계용 응력-변형률 ($f_{{ck}}$ = {fck:.0f} MPa)")
    ax.set_xlim(0, eps_cu * 1e3)
    ax.set_ylim(0, 0.85 * fck * 1.15)
    ax.legend(fontsize=9, loc="lower right")

    # 오른쪽 — 곡선 형상이 같다는 것을 정규화해서 보인다
    bx.plot(eps * 1e3, np.array(s14) / (0.85 * fck), color=C14, lw=3, label="KDS 14")
    bx.plot(eps * 1e3, np.array(s24) / f_cd, color=C24, lw=1.6, ls="--", label="KDS 24")
    bx.set_xlabel("압축변형률 $\\varepsilon_c$ (‰)")
    bx.set_ylabel("최대값으로 나눈 응력")
    bx.set_title("최대값으로 정규화하면 두 곡선은 겹친다")
    bx.set_xlim(0, eps_cu * 1e3)
    bx.set_ylim(0, 1.1)
    bx.legend(fontsize=9, loc="lower right")

    fig.tight_layout()
    fig.savefig(OUT / "stress_strain.png", dpi=140)
    plt.close(fig)

    print(
        f"[1] fck {fck:.0f}: KDS 14 최대 {0.85 * fck:.2f} MPa, "
        f"KDS 24 최대 {f_cd:.2f} MPa, 비 {f_cd / (0.85 * fck):.3f}"
        f"  (eta={eta:.2f}, beta1={beta_1:.2f})"
    )


# ── 그림 2. P-M 상관도 ─────────────────────────────────────────────────────
def figure_interaction(fck: float = 40.0, n_bar: int = 6) -> None:
    """같은 단면의 P-M 상관도를 두 기준으로 그린다."""
    kds14 = beam(KDS(column_type="tie"), fck=fck, n_bar=n_bar)
    d14, u14, phis = kds14.moment_interaction_diagram(n_points=28, progress_bar=False)

    kds24 = beam(KDS24(), fck=fck, n_bar=n_bar)
    d24 = kds24.moment_interaction_diagram(n_points=28, progress_bar=False)

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(11, 4.6))

    ax.plot(
        [r.m_x / 1e6 for r in u14.results],
        [r.n / 1e3 for r in u14.results],
        color=C_NOMINAL,
        lw=1.4,
        ls="--",
        label="KDS 14 공칭 $M_n$",
    )
    ax.plot(
        [r.m_x / 1e6 for r in d14.results],
        [r.n / 1e3 for r in d14.results],
        color=C14,
        lw=2,
        label="KDS 14 설계 $\\phi M_n$",
    )
    ax.plot(
        [r.m_x / 1e6 for r in d24.results],
        [r.n / 1e3 for r in d24.results],
        color=C24,
        lw=2,
        label="KDS 24 설계 $M_{Rd}$",
    )
    # KDS 24 에는 최대 축강도 저감계수가 없다. 대신 최소편심이 걸린다.
    e_min = minimum_eccentricity(h=600.0)
    n_line = np.linspace(0, max(r.n for r in d24.results), 50)
    ax.plot(
        n_line * e_min / 1e6,
        n_line / 1e3,
        color=C24,
        lw=1.2,
        ls=":",
        label=f"KDS 24 최소편심 $e_{{min}}$ = {e_min:.0f} mm",
    )

    ax.set_xlabel("휨모멘트 (kN·m)")
    ax.set_ylabel("축력 (kN)")
    ax.set_title(f"P-M 상관도 ($f_{{ck}}$ = {fck:.0f}, {n_bar}-D22 인장측)")
    ax.legend(fontsize=8.5)

    # 강도감소계수가 축력에 따라 변한다는 것
    bx.plot(
        [r.n / 1e3 for r in u14.results],
        phis,
        color=C14,
        lw=2,
        label="KDS 14 $\\phi$ (단면에 곱함)",
    )
    bx.axhline(PHI_S_ULS, color=C24, lw=2, label=f"KDS 24 $\\phi_s$ = {PHI_S_ULS}")
    bx.axhline(
        PHI_C_ULS, color=C24, lw=2, ls="--", label=f"KDS 24 $\\phi_c$ = {PHI_C_ULS}"
    )
    bx.set_xlabel("축력 (kN)")
    bx.set_ylabel("계수")
    bx.set_title("안전율이 어디에 걸리는가")
    bx.set_ylim(0.55, 1.0)
    bx.legend(fontsize=9)

    fig.tight_layout()
    fig.savefig(OUT / "interaction.png", dpi=140)
    plt.close(fig)

    m14 = max(r.m_x for r in d14.results) / 1e6
    m24 = max(r.m_x for r in d24.results) / 1e6
    n14 = max(r.n for r in d14.results) / 1e3
    n24 = max(r.n for r in d24.results) / 1e3
    print(
        f"[2] 최대 설계휨모멘트  KDS 14 {m14:7.1f}  KDS 24 {m24:7.1f} kN·m "
        f"({m24 / m14 - 1:+.1%})"
    )
    print(
        f"[2] 최대 설계축강도    KDS 14 {n14:7.0f}  KDS 24 {n24:7.0f} kN "
        f"({n24 / n14 - 1:+.1%})  — KDS 24 에는 alpha_max 가 없다"
    )

    # 최소편심 선과 KDS 24 상관도가 만나는 축력
    pts = sorted(((r.n, r.m_x) for r in d24.results if r.n > 0), key=lambda t: t[0])
    n_usable = 0.0
    for (n_a, m_a), (n_b, m_b) in zip(pts, pts[1:], strict=False):
        if (m_a - n_a * e_min) * (m_b - n_b * e_min) <= 0:
            t = (m_a - n_a * e_min) / ((m_a - n_a * e_min) - (m_b - n_b * e_min))
            n_usable = n_a + t * (n_b - n_a)
            break

    print(
        f"[2] 최소편심 e_min = {e_min:.0f} mm 를 지키면 KDS 24 축력은 "
        f"{n_usable / 1e3:.0f} kN 까지다 (KDS 14 대비 {n_usable / 1e3 / n14 - 1:+.1%})"
    )


# ── 그림 3. 휨강도가 철근량에 따라 어떻게 갈리는가 ─────────────────────────
def figure_flexure_sweep(fck: float = 40.0) -> None:
    """인장철근 개수를 바꾸며 두 기준의 설계휨강도를 견준다."""
    counts = [2, 3, 4, 5, 6, 7, 8]
    m14, m24 = [], []

    for n in counts:
        f_res, _, _ = beam(KDS(), fck=fck, n_bar=n, n_top=0).ultimate_bending_capacity()
        m14.append(f_res.m_x / 1e6)
        m24.append(
            beam(KDS24(), fck=fck, n_bar=n, n_top=0).design_bending_capacity().m_x / 1e6
        )

    m14 = np.array(m14)
    m24 = np.array(m24)

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(11, 4.2))

    ax.plot(counts, m14, "o-", color=C14, lw=2, label="KDS 14 $\\phi M_n$")
    ax.plot(counts, m24, "s-", color=C24, lw=2, label="KDS 24 $M_{Rd}$")
    ax.set_xlabel("인장철근 개수 (D22)")
    ax.set_ylabel("설계휨강도 (kN·m)")
    ax.set_title(f"400×600 단철근 보 ($f_{{ck}}$ = {fck:.0f}, SD400)")
    ax.legend(fontsize=9)

    bx.plot(counts, (m24 / m14 - 1.0) * 100, "d-", color="#6c3483", lw=2)
    bx.axhline(0, color="k", lw=0.8)
    bx.set_xlabel("인장철근 개수 (D22)")
    bx.set_ylabel("KDS 24 가 큰 정도 (%)")
    bx.set_title("철근이 많아질수록 차이가 줄어든다")

    fig.tight_layout()
    fig.savefig(OUT / "flexure_sweep.png", dpi=140)
    plt.close(fig)

    for n, a, b in zip(counts, m14, m24, strict=True):
        print(f"[3] {n}-D22: KDS 14 {a:7.1f}  KDS 24 {b:7.1f} kN·m ({b / a - 1:+.1%})")


# ── 그림 4. 전단 ───────────────────────────────────────────────────────────
def figure_shear(fck: float = 40.0, b_w: float = 400.0, d: float = 640.0) -> None:
    """전단철근이 없을 때와 있을 때를 나누어 두 기준을 견준다."""
    rho = np.linspace(0.001, 0.02, 120)
    v24 = np.array(
        [
            shear24.design_concrete_shear_strength(
                fck=fck, b_w=b_w, d=d, a_s=r * b_w * d
            )
            / 1e3
            for r in rho
        ]
    )
    v14 = 0.75 * shear14.concrete_shear_strength(fck=fck, b_w=b_w, d=d) / 1e3

    spacings = np.array([100, 125, 150, 200, 250, 300])
    a_v = 2 * 126.7
    s24 = np.array(
        [
            shear24.shear_reinforcement_strength(
                f_vy=400.0, a_v=a_v, d=d, s=s, cot_theta=2.5
            )
            / 1e3
            for s in spacings
        ]
    )
    v_max = shear24.max_shear_strength(fck=fck, b_w=b_w, d=d, cot_theta=2.5) / 1e3
    s24 = np.minimum(s24, v_max)
    s14 = np.array(
        [
            0.75
            * (
                shear14.concrete_shear_strength(fck=fck, b_w=b_w, d=d)
                + shear14.shear_reinforcement_strength(a_v=a_v, fyt=400.0, d=d, s=s)
            )
            / 1e3
            for s in spacings
        ]
    )

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(11, 4.2))

    ax.plot(rho * 100, v24, color=C24, lw=2, label="KDS 24 $V_{cd}$")
    ax.axhline(v14, color=C14, lw=2, label="KDS 14 $\\phi V_c$")
    ax.set_xlabel("인장철근비 $\\rho$ (%)")
    ax.set_ylabel("전단강도 (kN)")
    ax.set_title("전단철근이 없을 때")
    ax.set_ylim(0, max(v14, v24.max()) * 1.25)
    ax.legend(fontsize=9, loc="lower right")

    width = 0.36
    x = np.arange(len(spacings))
    bx.bar(x - width / 2, s14, width, color=C14, label="KDS 14 $\\phi(V_c + V_s)$")
    bx.bar(
        x + width / 2,
        s24,
        width,
        color=C24,
        label="KDS 24 $V_{sd}$ ($\\cot\\theta$ = 2.5)",
    )
    bx.set_xticks(x)
    bx.set_xticklabels([f"@{int(s)}" for s in spacings])
    bx.axhline(
        v_max,
        color=C24,
        ls=":",
        lw=1.4,
        label=f"KDS 24 스트럿 한계 $V_{{d,max}}$ = {v_max:.0f} kN",
    )
    bx.set_xlabel("스터럽 간격 (mm, D13 2가닥)")
    bx.set_ylabel("전단강도 (kN)")
    bx.set_title("전단철근이 있을 때 — @125 부터는 스트럿 한계에 걸린다")
    bx.legend(fontsize=8.5)

    fig.tight_layout()
    fig.savefig(OUT / "shear.png", dpi=140)
    plt.close(fig)

    print(
        f"[4] 전단철근 없음: KDS 14 φVc = {v14:.1f} kN, "
        f"KDS 24 V_cd = {v24[0]:.1f} ~ {v24[-1]:.1f} kN"
    )
    for s, a, b in zip(spacings, s14, s24, strict=True):
        print(
            f"[4] D13@{int(s):3d}: KDS 14 {a:7.1f}  KDS 24 {b:7.1f} kN "
            f"({b / a - 1:+.1%})"
        )


def main() -> None:
    """모든 그림을 만든다."""
    OUT.mkdir(parents=True, exist_ok=True)
    print("사용 글꼴:", use_korean_font())
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["axes.grid"] = True
    plt.rcParams["grid.alpha"] = 0.3

    print(f"\n재료계수 phi_c = {PHI_C_ULS}, phi_s = {PHI_S_ULS}")
    print(
        f"f_cd(40) = {design_compressive_strength(fck=40):.2f} MPa, "
        f"f_yd(400) = {design_yield_strength(fy=400):.1f} MPa\n"
    )

    figure_stress_strain()
    figure_interaction()
    figure_flexure_sweep()
    figure_shear()

    print(f"\n{OUT} 에 그림 4개를 만들었다.")


if __name__ == "__main__":
    main()
