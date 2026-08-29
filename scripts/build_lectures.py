"""`docs/lectures/*.ipynb` 를 생성한다.

강의용 노트북은 `docs/examples/` 의 사용 예제와 목적이 다르다. 예제가 "이
함수를 이렇게 쓴다"를 보인다면, 강의용은 "이 현상이 왜 이런가"와 "기준이 왜
이렇게 정했는가"를 설명한다. 그래서 다음 규칙을 지킨다.

- 코드 셀 앞에는 반드시 그 코드가 무엇을 하는지 적는다.
- 절마다 설계의 의도(기준이 그렇게 정한 까닭)를 한 문단 이상 둔다.
- 학생이 바꿔 볼 값에는 ``← 바꿔 보라`` 주석을 단다.
- 그림 라벨은 한글과 유니코드 그리스문자로 쓴다.

실행:
    python scripts/build_lectures.py           # 생성만
    python scripts/build_lectures.py --run     # 생성 후 실행하여 출력 저장
"""

from __future__ import annotations

import sys
from pathlib import Path

from nbbuild import code, execute, md, write

LECTURES = Path(__file__).resolve().parents[1] / "docs" / "lectures"

EXPLORER_NOTE = """
:::{tip}
같은 내용을 슬라이더로 움직여 보려면
[대화형 탐색기](../_static/explorer.html)를 연다. 값을 바꾸면 그래프가 바로
따라 바뀐다.
:::
"""

# 모든 강의 노트북의 준비 셀
SETUP = '''
%matplotlib inline

import glob
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager


def use_korean_font():
    """설치된 한글 글꼴을 찾아 matplotlib 에 등록한다."""
    site = Path(sys.prefix, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages")
    for pattern in (
        str(site / "koreanize_matplotlib/fonts/*.ttf"),
        "/usr/share/fonts/**/*Nanum*.ttf",
        "/usr/share/fonts/**/*NotoSansCJK*.ot[fc]",
        "/usr/share/fonts/**/*NotoSansKR*.otf",
    ):
        for path in glob.glob(pattern, recursive=True):
            font_manager.fontManager.addfont(path)

    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in ("NanumGothic", "Malgun Gothic", "AppleGothic",
                 "Noto Sans CJK KR", "Noto Sans KR", "WenQuanYi Zen Hei"):
        if name in installed:
            plt.rcParams["font.family"] = name
            return name

    warnings.warn(
        "한글 글꼴을 찾지 못했다. 그림의 한글이 깨진다면 "
        "`pip install koreanize-matplotlib` 로 글꼴만 내려받거나, "
        "나눔고딕·Noto Sans KR 을 시스템에 설치한다.",
        stacklevel=2,
    )
    return None


print("사용 글꼴:", use_korean_font())

plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 110
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.3

# 단면 분류에 쓰는 색 (압축지배 · 변화구간 · 인장지배)
C_COMP, C_TRAN, C_TENS = "#ad3327", "#b5811f", "#2a7355"
BAND = {"압축지배단면": C_COMP, "변화구간단면": C_TRAN, "인장지배단면": C_TENS}
'''

BEAM_DEF = '''
from concreteproperties import ConcreteSection
from sectionproperties.pre.library import concrete_rectangular_section

from concreteproperties_kds import KDS


def beam(fck=27, fy=400, n_bar=4, d=600, b=400, cover=50, profile="block"):
    """단철근 직사각형 보. 압축철근이 없어 손계산과 조건이 정확히 같다."""
    kds = KDS()
    conc = kds.create_concrete_material(
        compressive_strength=fck, ultimate_profile=profile
    )
    steel = kds.create_steel_material(yield_strength=fy)

    geom = concrete_rectangular_section(
        d=d, b=b,
        dia_top=22, area_top=387.1, n_top=0, c_top=cover,
        dia_bot=22, area_bot=387.1, n_bot=n_bar, c_bot=cover,
        n_circle=16, conc_mat=conc, steel_mat=steel,
    )
    kds.assign_concrete_section(ConcreteSection(geom))
    return kds


def column(fck=27, fy=400, column_type="tie", profile="block"):
    """500 x 500 기둥 (8-D22, 피복 50 mm)."""
    kds = KDS(column_type=column_type)
    conc = kds.create_concrete_material(
        compressive_strength=fck, ultimate_profile=profile
    )
    steel = kds.create_steel_material(yield_strength=fy)

    geom = concrete_rectangular_section(
        d=500, b=500,
        dia_top=22, area_top=387.1, n_top=3, c_top=50,
        dia_bot=22, area_bot=387.1, n_bot=3, c_bot=50,
        dia_side=22, area_side=387.1, n_side=1, c_side=50,
        n_circle=16, conc_mat=conc, steel_mat=steel,
    )
    kds.assign_concrete_section(ConcreteSection(geom))
    return kds


def depth(kds):
    """단면 상단에서 최하단 철근 도심까지의 유효깊이 d."""
    sec = kds.concrete_section
    top = sec.compound_geometry.geom.bounds[3]
    return top - min(g.calculate_centroid()[1] for g in sec.reinf_geometries_lumped)


print("보와 기둥을 만드는 함수를 정의했다.")
'''


# ══════════════════════════════════════════════════════════════════════════
def nb_l1_block():
    """강의 L1 - 등가직사각형 응력블록의 근거와 한계."""
    return write("L1_등가응력블록", [
        md(r"""
        # L1 · 등가직사각형 응력블록 — 근사를 어디까지 믿을 것인가

        ## 이 시간에 답할 질문

        1. 콘크리트 압축응력은 실제로 곡선인데, 왜 직사각형으로 바꿔 놓고 푸는가?
        2. $\eta$ 와 $\beta_1$ 은 어디서 나온 숫자인가?
        3. 그 근사는 얼마나 정확한가. 그리고 **어디서 깨지는가**?
        4. 근사가 위험한 쪽으로 틀리는 경우가 있는가?

        ## 기준이 허용하는 것

        KDS 14 20 20 4.1.1(6)은 압축응력 분포를 **직사각형·사다리꼴·포물선 등
        실험과 일치하는 어떤 형상으로도 가정할 수 있다**고 규정한다. 그리고
        구체적으로 두 가지를 제시한다.

        | 조문 | 관계 | 성격 |
        |---|---|---|
        | 4.1.1(7), 표 4.1-1 | **포물선-직선** — 식 (4.1-1), (4.1-2) | 실제 거동에 가까운 쪽 |
        | 4.1.1(8), 표 4.1-2 | **등가직사각형 응력블록** — $\eta(0.85f_{ck})$, $a=\beta_1 c$ | 손으로 풀기 위한 근사 |

        둘 중 어느 쪽을 써도 좋다. 이 시간에는 두 관계를 직접 그려 비교하고,
        차이가 어디서 커지는지 확인한다.
        """, EXPLORER_NOTE),

        md("""
        ## 0. 준비

        **아래 코드가 하는 일** — 그림에 쓸 한글 글꼴을 찾아 등록하고, 단면
        분류에 쓸 색을 정한다. 글꼴을 못 찾으면 경고만 내고 넘어가므로 셀이
        실패하지는 않는다.
        """),
        code(SETUP),

        md("""
        **아래 코드가 하는 일** — 이 노트북 전체에서 쓸 보·기둥 단면을 만드는
        함수를 정의한다. `profile` 인자로 극한 응력-변형률 관계를 고를 수 있게
        해 두었다. `"block"` 은 등가직사각형 응력블록, `"parabolic"` 은
        포물선-직선 관계다.

        보는 **압축철근을 두지 않았다**(`n_top=0`). 손계산 공식과 조건을 정확히
        맞추기 위해서다. 압축철근이 있으면 차이가 근사 때문인지 압축철근 때문인지
        구분할 수 없다.
        """),
        code(BEAM_DEF),

        md(r"""
        ## 1. 실제 응력분포 — 포물선-직선 관계

        KDS 14 20 20 식 (4.1-1), (4.1-2)는 압축응력을 이렇게 정의한다.

        $$
        f_c = 0.85 f_{ck}\left[1 - \left(1 - \frac{\varepsilon_c}
        {\varepsilon_{co}}\right)^{n}\right]
        \qquad (\varepsilon_c \leq \varepsilon_{co})
        $$

        $$
        f_c = 0.85 f_{ck}
        \qquad (\varepsilon_{co} < \varepsilon_c \leq \varepsilon_{cu})
        $$

        변형률 $\varepsilon_{co}$ 까지는 포물선으로 올라가고, 그 뒤 극한변형률
        $\varepsilon_{cu}$ 까지는 최대값을 유지한다. 지수 $n$, $\varepsilon_{co}$,
        $\varepsilon_{cu}$ 는 강도에 따라 달라진다 — 식 (4.1-3)~(4.1-5).

        **왜 강도가 높을수록 $n$ 이 작아지는가.** 고강도 콘크리트는 파괴가
        취성적이라 응력-변형률 곡선이 더 뾰족해지고 하강이 급하다. $n$ 이 작아지면
        곡선이 더 빨리 최대값에 도달하는 모양이 되어 그 거동을 반영한다. 동시에
        $\varepsilon_{cu}$ 는 줄어든다 — 덜 늘어나고 깨진다는 뜻이다.

        **아래 코드가 하는 일** — 강도별로 $n$, $\varepsilon_{co}$,
        $\varepsilon_{cu}$, $\alpha$, $\beta$ 를 뽑아 KDS 표 4.1-1 과 대조한다.
        """),
        code("""
        from concreteproperties_kds import parabolic_parameters, parabolic_stress
        from concreteproperties_kds import stress_block_parameters

        print("KDS 14 20 20 표 4.1-1 — 포물선-직선 관계")
        print(f"{'fck':>5} {'n':>7} {'εco':>9} {'εcu':>9} {'α':>7} {'β':>7}")
        print("-" * 48)
        for fck in (40, 50, 60, 70, 80, 90):
            n, eps_co, eps_cu, alpha, beta = parabolic_parameters(fck)
            print(f"{fck:5.0f} {n:7.2f} {eps_co:9.4f} {eps_cu:9.4f} {alpha:7.2f} {beta:7.2f}")

        print()
        print("KDS 14 20 20 표 4.1-2 — 등가직사각형 응력블록")
        print(f"{'fck':>5} {'εcu':>9} {'η':>7} {'β1':>7}")
        print("-" * 32)
        for fck in (40, 50, 60, 70, 80, 90):
            eps_cu, eta, beta_1 = stress_block_parameters(fck)
            print(f"{fck:5.0f} {eps_cu:9.4f} {eta:7.2f} {beta_1:7.2f}")
        """),

        md(r"""
        **아래 코드가 하는 일** — 포물선-직선 곡선을 강도별로 그린다. 최대값을
        $0.85f_{ck}$ 로 나눠 정규화했으므로, 곡선의 **모양**만 비교된다.
        """),
        code("""
        fig, ax = plt.subplots(figsize=(7.2, 4.2))

        for fck, colour in zip([27, 40, 60, 80], ["#1b4f7f", "#2a7355", "#b5811f", "#ad3327"]):
            n, eps_co, eps_cu, _, _ = parabolic_parameters(fck)
            eps = np.linspace(0, eps_cu, 300)
            f_c = np.array([parabolic_stress(fck, e) for e in eps])
            ax.plot(eps * 1000, f_c / (0.85 * fck), color=colour, lw=2,
                    label=f"fck {fck} MPa  (n={n:.2f})")
            ax.plot([eps_cu * 1000], [1.0], "o", color=colour, ms=5)

        ax.set_xlabel("압축변형률 εc ((x1e-3))")
        ax.set_ylabel("압축응력 / 0.85fck")
        ax.set_title("KDS 14 20 20 식 (4.1-1), (4.1-2) — 포물선-직선 관계")
        ax.legend(fontsize=9)
        ax.set_ylim(0, 1.08)
        """),

        md(r"""
        점으로 찍은 것이 각 곡선의 끝, 즉 극한변형률 $\varepsilon_{cu}$ 다.
        강도가 높을수록 **왼쪽에서 끝난다** — 덜 변형하고 깨진다.

        ## 2. 등가블록은 무엇을 같게 맞춘 것인가

        직사각형으로 바꿔치기해도 되려면 두 가지가 같아야 한다.

        1. **합력의 크기** — 응력분포의 면적
        2. **합력의 작용 위치** — 응력분포의 도심

        이 둘만 같으면 단면의 힘 평형과 모멘트 평형이 그대로 성립한다. 분포의
        모양이 다른 것은 상관없다. 바로 이것이 등가블록의 전부다.

        KDS 는 포물선-직선 분포에 대해 평균 압축응력 계수 $\alpha$ 와 합력
        위치 계수 $\beta$ 를 표 4.1-1 에 주고 있으므로, 직접 확인할 수 있다.

        $$
        \text{합력} = \alpha (0.85 f_{ck})\, b\, c
        \qquad
        \text{작용 위치} = \beta c \ \text{(압축연단에서)}
        $$

        등가블록은 같은 것을 이렇게 쓴다.

        $$
        \text{합력} = \eta (0.85 f_{ck})\, b\, (\beta_1 c)
        \qquad
        \text{작용 위치} = \frac{\beta_1 c}{2}
        $$

        **아래 코드가 하는 일** — 두 표현이 정말 같은 값을 주는지 확인한다.
        합력 비 $\eta\beta_1 / \alpha$ 와 위치 비 $(\beta_1/2)/\beta$ 가 1 에
        가까우면 등가가 성립한다.
        """),
        code("""
        print(f"{'fck':>5} {'α':>7} {'ηβ1':>7} {'합력비':>8}   {'β':>7} {'β1/2':>7} {'위치비':>8}")
        print("-" * 60)
        for fck in (40, 50, 60, 70, 80, 90):
            _, _, _, alpha, beta = parabolic_parameters(fck)
            _, eta, beta_1 = stress_block_parameters(fck)
            print(f"{fck:5.0f} {alpha:7.2f} {eta * beta_1:7.3f} {eta * beta_1 / alpha:8.3f}   "
                  f"{beta:7.2f} {beta_1 / 2:7.3f} {(beta_1 / 2) / beta:8.3f}")
        """),

        md(r"""
        두 도심선이 거의 겹쳐 보인다면 제대로 본 것이다. $\beta c$ 와 $a/2$ 가
        같아지도록 $\beta_1$ 을 정했으니 당연한 결과이고, 이것이 등가블록이
        성립하는 이유 그 자체다.

        **여기서 알 것.** 합력비와 위치비가 모두 1 근처다. 즉 $\eta$, $\beta_1$
        은 임의로 정한 숫자가 아니라 **포물선-직선 분포의 면적과 도심을 맞춘
        결과**다. 완전히 1 이 아닌 것은 표 값을 실용적인 자리수로 반올림했기
        때문이다.

        **아래 코드가 하는 일** — 400 × 600 단철근 보의 극한상태를 실제로 풀어
        중립축 깊이 $c$ 를 구한 뒤, 세 장면을 같은 높이 축에 나란히 그린다.

        1. **단면** — 압축연단이 위, 인장철근이 아래. 중립축 위쪽 빗금이 압축부다.
        2. **변형률** — 평면유지 가정이므로 직선이다. 압축연단에서
           $\varepsilon_{cu}$, 철근 위치에서 $\varepsilon_t$.
        3. **압축응력** — 그 변형률에 대응하는 응력. 포물선-직선과 등가블록을
           겹쳐 놓았다.

        세 그림의 세로 위치가 서로 맞으므로, 어느 높이의 변형률이 어떤 응력을
        만드는지 눈으로 따라갈 수 있다.
        """),
        code("""
        fck, fy, n_bar = 27, 400, 4     # ← 값을 바꿔 보라
        H, B, COVER = 600.0, 400.0, 50.0

        # 실제 극한상태를 풀어 중립축 깊이를 얻는다
        kds_b = beam(fck=fck, fy=fy, n_bar=n_bar, d=H, b=B, cover=COVER)
        _, u_res, _ = kds_b.ultimate_bending_capacity()
        c = u_res.d_n
        d_eff = depth(kds_b)

        n, eps_co, eps_cu, alpha, beta = parabolic_parameters(fck)
        _, eta, beta_1 = stress_block_parameters(fck)
        a = beta_1 * c
        f_blk = eta * 0.85 * fck

        y_na = H - c            # 중립축의 높이 (바닥 기준)
        y_bar = H - d_eff       # 인장철근의 높이
        eps_t = eps_cu * (d_eff - c) / c

        fig = plt.figure(figsize=(12.5, 5.2))
        gs = fig.add_gridspec(1, 4, width_ratios=[1.0, 1.0, 1.0, 1.5], wspace=0.32)
        axes = [fig.add_subplot(gs[0])]
        axes += [fig.add_subplot(gs[k], sharey=axes[0]) for k in (1, 2)]
        zoom = fig.add_subplot(gs[3])

        # ── (1) 단면 ──────────────────────────────────────────────────
        ax = axes[0]
        ax.add_patch(plt.Rectangle((0, 0), B, H, fill=False, ec="k", lw=1.6))
        ax.add_patch(plt.Rectangle((0, y_na), B, c, facecolor="#1b4f7f",
                                   alpha=0.18, ec="none"))
        for i_bar in range(n_bar):
            x = COVER + 11 + i_bar * (B - 2 * (COVER + 11)) / max(n_bar - 1, 1)
            ax.plot([x], [y_bar], "o", color="#333", ms=9)
        ax.axhline(y_na, color=C_COMP, lw=1.4, ls="--")
        ax.text(B / 2, y_na + 12, "중립축", color=C_COMP, ha="center", fontsize=9)
        ax.annotate("", xy=(-34, H), xytext=(-34, y_na),
                    arrowprops=dict(arrowstyle="<->", color=C_COMP, lw=1.1))
        ax.text(-44, (H + y_na) / 2, f"c = {c:.0f}", rotation=90, ha="right",
                va="center", color=C_COMP, fontsize=9)
        ax.set_xlim(-90, B + 100)
        ax.set_title(f"단면  {B:.0f} × {H:.0f}, {n_bar}-D22")
        ax.set_ylabel("단면 바닥에서의 높이 (mm)")
        ax.set_xticks([])
        ax.grid(False)

        # ── (2) 변형률 ────────────────────────────────────────────────
        ax = axes[1]
        ax.axvline(0, color="k", lw=1.0)
        ax.plot([eps_cu, -eps_t], [H, y_bar], color="#1b4f7f", lw=2)
        ax.axhline(y_na, color=C_COMP, lw=1.0, ls="--")
        ax.plot([eps_cu], [H], "o", color="#1b4f7f", ms=6)
        ax.plot([-eps_t], [y_bar], "o", color=C_TENS, ms=6)
        ax.text(eps_cu, H + 14, f"εcu = {eps_cu:.4f}", ha="right",
                color="#1b4f7f", fontsize=9)
        ax.text(-eps_t, y_bar - 30, f"εt = {eps_t:.4f}", ha="left",
                color=C_TENS, fontsize=9)
        ax.set_title("변형률 (평면유지)")
        ax.set_xlabel("변형률")
        ax.set_xlim(-eps_t * 1.35, eps_cu * 2.2)

        # ── (3) 압축응력 (단면 전체 높이) ─────────────────────────────
        yy = np.linspace(y_na, H, 300)
        f_para = np.array([parabolic_stress(fck, eps_cu * (h - y_na) / c) for h in yy])

        ax = axes[2]
        ax.fill_betweenx(yy, 0, f_para, color="#1b4f7f", alpha=0.18)
        ax.plot(f_para, yy, color="#1b4f7f", lw=2)
        ax.plot([0, f_blk, f_blk, 0], [H - a, H - a, H, H],
                color=C_COMP, lw=1.8, ls="--")
        ax.axhline(y_na, color=C_COMP, lw=1.0, ls="--")
        ax.add_patch(plt.Rectangle((0, y_na - 6), f_blk * 1.45, c + 12,
                                   fill=False, ec="#888", lw=1.0, ls=":"))
        ax.set_title("압축응력")
        ax.set_xlabel("압축응력 (MPa)")
        ax.set_xlim(0, f_blk * 1.75)

        # ── (4) 압축부 확대 ───────────────────────────────────────────
        zoom.fill_betweenx(yy, 0, f_para, color="#1b4f7f", alpha=0.18)
        zoom.plot(f_para, yy, color="#1b4f7f", lw=2.4, label="포물선-직선  4.1.1(7)")
        zoom.plot([0, f_blk, f_blk, 0], [H - a, H - a, H, H],
                  color=C_COMP, lw=2, ls="--", label="등가블록  4.1.1(8)")
        zoom.axhline(y_na, color=C_COMP, lw=1.0, ls="--")
        zoom.text(f_blk * 0.02, y_na + 2, "중립축", color=C_COMP, fontsize=9)

        for y_res, colour, lab, dy in [
            (H - beta * c, "#1b4f7f", f"포물선 합력 βc = {beta * c:.1f} mm", 6),
            (H - a / 2, C_COMP, f"블록 합력 a/2 = {a / 2:.1f} mm", -12),
        ]:
            zoom.annotate("", xy=(f_blk * 0.5, y_res), xytext=(f_blk * 0.5, y_res + 26),
                          arrowprops=dict(arrowstyle="-|>", color=colour, lw=1.8))
            zoom.plot([0, f_blk * 1.25], [y_res, y_res], color=colour, lw=0.9, ls=":")
            zoom.text(f_blk * 1.28, y_res + dy, lab, color=colour, fontsize=9, va="center")

        zoom.set_title("압축부 확대 — 면적과 도심이 같다")
        zoom.set_xlabel("압축응력 (MPa)")
        zoom.set_ylabel("높이 (mm)")
        zoom.set_xlim(0, f_blk * 2.4)
        zoom.set_ylim(y_na - 10, H + 10)
        zoom.legend(loc="lower right", fontsize=9)

        axes[0].set_ylim(-25, H + 60)
        fig.tight_layout()

        print(f"중립축 c = {c:.1f} mm,  압축블록 a = {a:.1f} mm,  유효깊이 d = {d_eff:.0f} mm")
        print(f"포물선 합력 = {alpha * 0.85 * fck * B * c / 1e3:,.0f} kN"
              f"   (작용 위치 βc = {beta * c:.1f} mm)")
        print(f"블록  합력 = {f_blk * B * a / 1e3:,.0f} kN"
              f"   (작용 위치 a/2 = {a / 2:.1f} mm)")
        """),

        md(r"""
        ## 3. 설계의 의도 — 왜 굳이 근사를 두는가

        포물선-직선 관계로도 풀 수 있는데 왜 블록을 따로 규정할까.

        **손으로 풀 수 있게 하려는 것이다.** 포물선 분포의 합력을 구하려면 중립축
        깊이를 모르는 상태에서 적분을 해야 하고, 그 적분은 강도마다 다르다.
        직사각형이면 합력이 곧 $\eta(0.85f_{ck}) \cdot b \cdot \beta_1 c$ 이고,
        힘 평형 $C = T$ 에서 $a$ 가 **한 줄로** 나온다.

        $$
        a = \frac{A_s f_y}{\eta (0.85 f_{ck})\, b}
        $$

        설계기준은 계산기가 없던 시절부터 실무자가 종이 위에서 안전한 답을 얻도록
        만들어져 왔다. 등가블록은 그 산물이다. 컴퓨터로 단면을 잘라 적분할 수 있는
        지금도 블록이 남아 있는 이유는, **검산이 가능해야 하기 때문**이다. 남의
        해석 결과를 받아 들었을 때 손으로 짚어 볼 수단이 없으면 검증이 성립하지
        않는다.

        ## 4. 그래서 얼마나 정확한가 — 휨부재

        **아래 코드가 하는 일** — 같은 보를 두 관계로 각각 풀어 설계휨강도를
        비교한다. 철근 개수를 늘려 가며 차이가 어떻게 변하는지 본다.
        """),
        code("""
        rows = []
        for n_bar in range(2, 11):
            m_block = beam(n_bar=n_bar, profile="block").ultimate_bending_capacity()[1].m_x
            m_para = beam(n_bar=n_bar, profile="parabolic").ultimate_bending_capacity()[1].m_x
            rows.append((n_bar, m_block / 1e6, m_para / 1e6))

        print(f"{'철근':>6} {'블록 Mn':>10} {'포물선 Mn':>11} {'차이':>8}")
        print("-" * 38)
        for n_bar, mb, mp in rows:
            print(f"{n_bar:4d}-D22 {mb:10.1f} {mp:11.1f} {(mp / mb - 1) * 100:7.2f} %")
        """),

        md(r"""
        **차이가 0.3 % 를 넘지 않는다.** 근사치고는 놀라울 만큼 잘 맞는다.

        **왜 이렇게 잘 맞는가.** 휨강도는 $M_n = T \cdot z$ 인데, $T = A_s f_y$
        는 응력분포와 **무관하고**, 지렛대 팔 $z = d - (\text{합력 위치})$ 에서
        합력 위치는 두 분포가 같도록 맞춰 놓았다. 남는 오차는 반올림뿐이다.
        게다가 $z$ 자체가 $d$ 에 비해 크게 변하지 않는다 — 압축부는 단면
        깊이의 1/5 안팎이라, 그 안에서 도심이 몇 mm 움직여도 $z$ 는 1 % 도 안
        바뀐다.

        ## 5. 근사가 깨지는 곳 — 압축이 커질 때

        휨만 받는 부재에서 잘 맞는다고 어디서나 잘 맞는 것은 아니다. 축력이
        커지면 중립축이 깊어지고, 결국 **단면 전체가 압축**이 된다. 그러면 압축
        영역 전체에서 변형률이 $\varepsilon_{cu}$ 보다 훨씬 작은 구간이 넓어지고,
        그 구간에서 실제 응력은 $0.85f_{ck}$ 에 한참 못 미친다. 블록은 그 구간까지
        최대응력으로 채워 버린다.

        **아래 코드가 하는 일** — 같은 기둥을 두 관계로 풀어 축력별 설계휨강도를
        비교한다.
        """),
        code("""
        col_block = column(profile="block")
        col_para = column(profile="parabolic")

        n_list = [0, 500, 1000, 1500, 2000, 2500, 3000, 3400]
        rows = []
        for n_d in n_list:
            mb = col_block.ultimate_bending_capacity(n_design=n_d * 1e3)[1].m_x / 1e6
            mp = col_para.ultimate_bending_capacity(n_design=n_d * 1e3)[1].m_x / 1e6
            rows.append((n_d, mb, mp))

        print(f"{'Nd(kN)':>8} {'블록 Mn':>10} {'포물선 Mn':>11} {'차이':>9}")
        print("-" * 42)
        for n_d, mb, mp in rows:
            print(f"{n_d:8.0f} {mb:10.1f} {mp:11.1f} {(mp / mb - 1) * 100:8.2f} %")
        """),

        md("""
        **아래 코드가 하는 일** — 위 표를 그림으로 옮긴다. 왼쪽은 두 상관도,
        오른쪽은 축력에 따른 차이다.
        """),
        code("""
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

        n_arr = np.array([r[0] for r in rows])
        mb_arr = np.array([r[1] for r in rows])
        mp_arr = np.array([r[2] for r in rows])

        axes[0].plot(mb_arr, n_arr, "o-", color="#ad3327", lw=2, ms=4, label="등가블록  4.1.1(8)")
        axes[0].plot(mp_arr, n_arr, "s--", color="#1b4f7f", lw=2, ms=4, label="포물선-직선  4.1.1(7)")
        axes[0].set_xlabel("공칭 휨강도 Mn (kN·m)")
        axes[0].set_ylabel("축력 Nd (kN)")
        axes[0].set_title("두 관계로 구한 상관도")
        axes[0].legend(fontsize=9)

        diff = (mp_arr / mb_arr - 1) * 100
        axes[1].axhline(0, color="grey", lw=0.8)
        axes[1].plot(n_arr, diff, "o-", color="#1b4f7f", lw=2, ms=4)
        axes[1].fill_between(n_arr, diff, 0, where=diff < 0, color=C_COMP, alpha=0.15)
        axes[1].set_xlabel("축력 Nd (kN)")
        axes[1].set_ylabel("포물선 대비 블록의 차이 (%)")
        axes[1].set_title("블록이 강도를 과대평가하는 정도")
        axes[1].text(n_arr[len(n_arr) // 2], diff.min() / 2,
                     "이 영역에서 블록이\\n비보수측(과대평가)", ha="center",
                     color=C_COMP, fontsize=10)

        fig.tight_layout()
        """),

        md(r"""
        ## 6. 이 결과를 어떻게 읽어야 하는가

        축력이 커질수록 등가블록이 강도를 **과대평가**한다. 이 기둥에서는
        3,000 kN 부근에서 5~6 % 다. 방향이 위험측이라는 점이 중요하다.

        그렇다고 기준이 잘못된 것은 아니다. 세 가지를 함께 봐야 한다.

        1. **강도감소계수가 그 영역에서 가장 낮다.** 압축지배단면은
           $\phi = 0.65$ 다. 근사 오차 6 % 는 $\phi$ 가 0.85 에서 0.65 로
           내려가며 확보한 여유 안에 들어간다. 기준은 계수를 따로따로 정한 것이
           아니라 **한 묶음으로** 정했다.
        2. **최대 축강도에서 잘라 낸다.** $\alpha\phi P_o$ 상한(식 (4.1-16),
           (4.1-17)) 때문에 오차가 가장 큰 순압축 근처는 애초에 설계에 쓰이지
           않는다.
        3. **정밀이 필요하면 포물선을 쓰면 된다.** 4.1.1(7)이 그래서 있다.
           기존 구조물의 잔여강도 평가처럼 여유를 정확히 알아야 하는 일에서는
           이쪽이 맞다.

        ## 7. 손계산 공식이 아예 없는 단면

        직사각형과 T형은 손으로 풀 수 있다. 원형·중공·이형 단면은 압축부의
        형상이 중립축 위치에 따라 달라져서, 폐합형 공식이 나오지 않는다.
        이때는 단면을 잘라 적분하는 수밖에 없다.

        **아래 코드가 하는 일** — 원형 기둥을 두 관계로 풀어 본다. 손계산으로는
        어느 쪽도 구할 수 없는 값이다.
        """),
        code("""
        from sectionproperties.pre.library import concrete_circular_section

        def circular(fck=27, fy=400, profile="block"):
            \"\"\"지름 600 mm 원형 기둥, 8-D22, 피복 50 mm.\"\"\"
            kds = KDS()
            conc = kds.create_concrete_material(
                compressive_strength=fck, ultimate_profile=profile
            )
            steel = kds.create_steel_material(yield_strength=fy)
            geom = concrete_circular_section(
                d=600, area_conc=np.pi * 600 ** 2 / 4, n_conc=32,
                dia_bar=22, area_bar=387.1, n_bar=8, cover=50,
                n_circle=16, conc_mat=conc, steel_mat=steel,
            )
            kds.assign_concrete_section(ConcreteSection(geom))
            return kds

        cb, cp = circular(profile="block"), circular(profile="parabolic")

        print(f"{'Nd(kN)':>8} {'블록 Mn':>10} {'포물선 Mn':>11} {'차이':>9}")
        print("-" * 42)
        for n_d in [0, 1000, 2000, 3000]:
            mb = cb.ultimate_bending_capacity(n_design=n_d * 1e3)[1].m_x / 1e6
            mp = cp.ultimate_bending_capacity(n_design=n_d * 1e3)[1].m_x / 1e6
            print(f"{n_d:8.0f} {mb:10.1f} {mp:11.1f} {(mp / mb - 1) * 100:8.2f} %")

        cb.concrete_section.plot_section()
        """),

        md(r"""
        ## 8. 직접 바꿔 보기

        **아래 코드가 하는 일** — 강도를 바꿔 가며 휨부재에서의 오차가 어떻게
        변하는지 본다. 고강도일수록 포물선 곡선이 뾰족해지므로, 근사 오차가
        커질 것이라 예상할 수 있다. 정말 그런지 확인한다.
        """),
        code("""
        fck_list = [21, 27, 35, 40, 50, 60, 80]   # ← 값을 바꿔 보라
        n_bar = 6                                  # ← 철근 개수도 바꿔 보라

        diffs = []
        for fck in fck_list:
            mb = beam(fck=fck, n_bar=n_bar, profile="block").ultimate_bending_capacity()[1].m_x
            mp = beam(fck=fck, n_bar=n_bar, profile="parabolic").ultimate_bending_capacity()[1].m_x
            diffs.append((mp / mb - 1) * 100)

        fig, ax = plt.subplots(figsize=(7.2, 3.8))
        ax.axhline(0, color="grey", lw=0.8)
        ax.plot(fck_list, diffs, "o-", color="#1b4f7f", lw=2)
        ax.set_xlabel("콘크리트 강도 fck (MPa)")
        ax.set_ylabel("포물선 대비 블록의 차이 (%)")
        ax.set_title(f"휨부재({n_bar}-D22)에서 강도에 따른 근사 오차")
        for x, y in zip(fck_list, diffs):
            ax.annotate(f"{y:+.2f}", (x, y), textcoords="offset points",
                        xytext=(0, 8), ha="center", fontsize=8)
        """),

        md(r"""
        ## 9. 생각해 볼 문제

        1. **등가블록의 두 조건(면적·도심)을 맞추면 왜 단면 해석이 정확해지는가?**
           힘 평형과 모멘트 평형을 직접 써서 설명하라. 응력분포의 *모양*은 왜
           결과에 들어오지 않는가?

        2. **위 5절에서 블록이 비보수측이었다.** 그런데도 기준이 블록을
           허용하는 근거를 세 가지 들었다. 그중 어느 것이 가장 결정적이라고
           보는가? 만약 $\phi$ 가 모든 단면에서 0.85 로 일정하다면 블록을
           허용해도 되겠는가?

        3. **$f_{ck}$ 가 40 MPa 이하이면 $n = 2.0$, $\varepsilon_{co} = 0.002$
           로 고정이다.** 왜 40 MPa 를 경계로 삼았을까? 표 4.1-1 에서
           $\alpha$ 가 40 MPa 이후 급히 떨어지는 것과 관련지어 설명하라.

        4. **기존 교량의 잔여강도를 평가하는 일을 맡았다고 하자.** 등가블록과
           포물선-직선 중 무엇을 쓰겠는가? 판단의 근거는 정확도인가, 검증
           가능성인가, 아니면 다른 것인가?

        ## 정리

        - 등가블록은 포물선-직선 분포와 **합력의 크기와 위치를 맞춘** 근사다.
          $\eta$, $\beta_1$ 은 그 결과이지 임의의 숫자가 아니다.
        - 휨부재에서는 0.3 % 이내로 맞는다. 지렛대 팔이 지배하기 때문이다.
        - 축력이 커지면 오차가 커지고 **방향이 비보수측**이다. 그 영역에서
          $\phi$ 가 낮고 최대 축강도 상한이 걸리는 것과 함께 읽어야 한다.
        - 원형·중공 단면에는 손계산 공식이 없다. 섬유 적분이 유일한 길이다.

        조문과 구현 함수의 대응은
        [설계식 목록](../user_guide/design_codes/equations.md) 에 정리되어 있다.
        다음 편은 [L2 · 강도감소계수](L2_강도감소계수.ipynb) 다.
        """),
    ], directory=LECTURES)


# ══════════════════════════════════════════════════════════════════════════
def nb_l2_phi():
    """강의 L2 - 강도감소계수는 왜 상수가 아닌가."""
    return write("L2_강도감소계수", [
        md(r"""
        # L2 · 강도감소계수 $\phi$ 는 왜 상수가 아닌가

        ## 이 시간에 답할 질문

        1. $\phi$ 를 표에서 찾는 숫자로 외우는데, 실은 무엇의 함수인가?
        2. 왜 압축지배단면은 $\phi = 0.65$ 로 **벌점**을 받는가?
        3. P-M 상관도에서 설계 곡선은 왜 공칭 곡선과 **평행하지 않은가**?
        4. 나선철근 기둥은 왜 $\phi$ 와 $\alpha$ 를 모두 우대받는가?

        ## 필요한 배경

        변형률 적합조건, 등가직사각형 응력블록([L1](L1_등가응력블록.ipynb)),
        P-M 상관도의 개념.

        ## 근거 조문

        | 내용 | 조문 |
        |---|---|
        | 강도감소계수 $\phi$ 의 값과 변화구간 보간 | KDS 14 20 10 4.3.3(2) |
        | 압축지배변형률한계 $\varepsilon_y$ | KDS 14 20 20 4.1.2(3) |
        | 인장지배변형률한계 $\varepsilon_{t,tl}$ | KDS 14 20 20 4.1.2(4) |
        | 최대 설계 축강도 $\alpha\phi P_o$ | KDS 14 20 20 식 (4.1-16), (4.1-17) |
        """, EXPLORER_NOTE),

        md("""
        ## 0. 준비

        **아래 코드가 하는 일** — 한글 글꼴을 등록하고 단면 분류 색을 정한다.
        """),
        code(SETUP),

        md(r"""
        ## 1. 단면 하나로 시작한다

        **아래 코드가 하는 일** — 이 노트북에서 쓸 보와 기둥을 만드는 함수를
        정의한다. 기둥은 500 × 500, 8-D22, 피복 50 mm, $f_{ck}$ 27 MPa,
        SD400 이다.
        """),
        code(BEAM_DEF),

        md(r"""
        **아래 코드가 하는 일** — 기둥을 만들고 KDS 가 정한 두 변형률 한계와
        강도감소계수의 양 끝값을 출력한다.

        SD400 이므로 $\varepsilon_y = f_y/E_s = 400/200{,}000 = 0.002$ 이고,
        인장지배한계는 $\max(0.005,\ 2.5\varepsilon_y) = 0.005$ 다.
        """),
        code("""
        kds = column()
        conc_sec = kds.concrete_section

        print(f"압축지배변형률한계  εy   = {kds.eps_y:.5f}   (= fy / 200,000)")
        print(f"인장지배변형률한계  εt,tl = {kds.eps_tl:.5f}   (= max(0.005, 2.5·εy))")
        print(f"압축지배단면의 φ          = {kds.phi_comp:.2f}   (띠철근)")
        print(f"인장지배단면의 φ          = 0.85")
        print(f"최대 축강도 저감계수 α     = {kds.alpha_max:.2f}")

        conc_sec.plot_section()
        """),

        md(r"""
        ## 2. $\phi$ 는 무엇의 함수인가

        먼저 답부터 보자. $\phi$ 는 **최외단 인장철근의 순인장변형률
        $\varepsilon_t$ 의 함수**다. 축력이나 단면 크기의 함수가 아니다.

        $$
        \phi(\varepsilon_t) =
        \begin{cases}
        0.65 & \varepsilon_t \le \varepsilon_y \quad \text{(압축지배)} \\[4pt]
        0.65 + 0.20\,\dfrac{\varepsilon_t - \varepsilon_y}{\varepsilon_{t,tl} - \varepsilon_y}
              & \varepsilon_y < \varepsilon_t < \varepsilon_{t,tl} \quad \text{(변화구간)} \\[8pt]
        0.85 & \varepsilon_t \ge \varepsilon_{t,tl} \quad \text{(인장지배)}
        \end{cases}
        $$

        **아래 코드가 하는 일** — $\varepsilon_t$ 를 0 부터 0.01 까지 훑으며
        $\phi$ 를 계산해 곡선으로 그린다. 세 구간을 색으로 칠하고, 경계에
        $\varepsilon_y$ 와 $\varepsilon_{t,tl}$ 를 표시한다.

        **볼 것** — $\phi$ 가 계단이 아니라 **경사로**라는 점.
        """),
        code("""
        eps = np.linspace(0.0, 0.010, 400)
        phi = np.array([kds.capacity_reduction_factor(e) for e in eps])

        fig, ax = plt.subplots(figsize=(7.2, 4.4))

        ax.axvspan(0, kds.eps_y, color=C_COMP, alpha=0.12)
        ax.axvspan(kds.eps_y, kds.eps_tl, color=C_TRAN, alpha=0.12)
        ax.axvspan(kds.eps_tl, eps[-1], color=C_TENS, alpha=0.12)

        ax.plot(eps, phi, color="k", lw=2)

        for x, label in [(kds.eps_y, "εy"), (kds.eps_tl, "εt,tl")]:
            ax.axvline(x, color="grey", ls="--", lw=0.8)
            ax.annotate(f"{label}\\n{x:.4f}", xy=(x, 0.606),
                        ha="center", va="bottom", fontsize=9)

        ax.text(kds.eps_y / 2, 0.86, "압축지배\\n(취성)", ha="center", color=C_COMP)
        ax.text((kds.eps_y + kds.eps_tl) / 2, 0.86, "변화구간", ha="center", color=C_TRAN)
        ax.text((kds.eps_tl + eps[-1]) / 2, 0.86, "인장지배\\n(연성)", ha="center", color=C_TENS)

        ax.set_xlabel("최외단 인장철근의 순인장변형률 εt")
        ax.set_ylabel("강도감소계수 φ")
        ax.set_title("KDS 14 20 10 4.3.3(2) — 강도감소계수는 변형률의 함수다")
        ax.set_ylim(0.60, 0.92)
        ax.set_xlim(0, eps[-1])
        """),

        md(r"""
        **여기서 알 것.** 표에 적힌 0.65 와 0.85 는 이 함수의 **양 끝값**일
        뿐이다. 실제 기둥은 대부분 그 사이 어딘가에 있다.

        "압축지배단면은 $\phi = 0.65$" 만 외운 학생은 변화구간에 있는 기둥에서
        $\phi$ 를 0.65 로 잡아 강도를 과소평가하거나, 반대로 0.85 로 잡아
        **위험측 설계**를 하게 된다.

        ## 3. 설계의 의도 — 왜 취성 파괴에 벌점을 주는가

        $\phi$ 는 "재료가 약할까 봐" 곱하는 계수가 아니다. 그건 재료계수의
        역할이고(KDS 14 20 20 부록이 재료계수 방식을 따로 규정한다), KDS 본문의
        $\phi$ 에는 **파괴 양상에 대한 벌점**이 섞여 있다.

        - **인장지배**($\varepsilon_t \ge 0.005$) — 철근이 충분히 항복한 뒤
          콘크리트가 압괴한다. 처짐과 균열로 미리 경고가 오고, 파괴까지 변형
          여유가 크다. 사람이 대피할 시간이 있고, 부재가 힘을 옆으로 넘겨줄
          기회도 있다. → $\phi = 0.85$
        - **압축지배**($\varepsilon_t \le \varepsilon_y$) — 철근이 항복하기
          전에 콘크리트가 먼저 깨진다. 경고 없이 갑자기 무너진다. → $\phi = 0.65$

        같은 공칭강도라도 **경고 없이 무너지는 단면은 더 큰 안전여유를
        요구한다**는 뜻이다. 이것이 강도설계법의 핵심 사고다. 안전율을 재료와
        하중에만 걸지 않고, **파괴의 성격**에도 건다.

        변화구간을 둔 까닭도 같은 맥락이다. 파괴 양상은 경계에서 뚝 바뀌지 않고
        서서히 옮겨 간다. $\phi$ 가 계단이면 $\varepsilon_t$ 가 0.0049 인 단면과
        0.0051 인 단면의 설계강도가 30 % 나 벌어져, 물리적 근거가 없는 불연속이
        생긴다.

        ## 4. 단면 위에서 확인하기

        **아래 코드가 하는 일** — 축력을 인장에서 압축까지 훑으면서, 각 축력에서
        중립축 깊이 $d_n$, 순인장변형률 $\varepsilon_t$, 단면 분류, $\phi$,
        설계휨강도를 한 줄씩 출력한다.

        `ultimate_bending_capacity(n_design=...)` 는 주어진 축력에서 극한상태를
        푼다. $\phi$ 가 $\varepsilon_t$ 에 의존하고 $\varepsilon_t$ 는 다시
        $N_u = N_d/\phi$ 에 의존하므로, 내부에서 비선형 해를 구한다.

        **볼 것** — 축력이 커질수록 중립축이 깊어져 $\varepsilon_t$ 가 줄고,
        어느 지점에서 인장지배 → 변화구간 → 압축지배로 넘어간다.
        """),
        code("""
        rows = []
        for n_d in [-800, -400, 0, 300, 600, 900, 1200, 1600, 2000, 2600, 3200]:
            f_res, u_res, phi_i = kds.ultimate_bending_capacity(n_design=n_d * 1e3)
            e_t = kds.net_tensile_strain(theta=0, d_n=u_res.d_n)
            rows.append((n_d, u_res.d_n, e_t, kds.section_classification(e_t),
                         phi_i, f_res.m_x / 1e6))

        print(f"{'Nd(kN)':>8} {'중립축 dn(mm)':>13} {'εt':>9} {'단면 분류':>12}"
              f" {'φ':>6} {'φMn(kNm)':>11}")
        print("-" * 66)
        for n_d, d_n, e_t, cls, phi_i, m in rows:
            e_str = "    inf" if e_t == float("inf") else f"{e_t:7.5f}"
            print(f"{n_d:8.0f} {d_n:13.1f} {e_str:>9} {cls:>12} {phi_i:6.3f} {m:11.1f}")
        """),

        md(r"""
        ## 5. P-M 상관도 위에 칠해 보기

        **아래 코드가 하는 일** — 상관도를 48 점으로 생성하고, 각 점의
        $\varepsilon_t$ 를 구해 단면 분류에 따라 색을 입힌다.
        `moment_interaction_diagram` 은 (설계 상관도, 공칭 상관도, φ 목록)
        세 가지를 함께 돌려준다.

        **볼 것** — 상관도의 **아래쪽(인장측)은 초록, 위쪽(압축측)은 빨강**이다.
        축력이 클수록 취성 파괴에 가까워진다는 사실이 곡선 하나에 담긴다.
        빨강과 노랑이 만나는 곳이 대략 균형점이다.
        """),
        code("""
        f_mi, mi, phis = kds.moment_interaction_diagram(n_points=48, progress_bar=False)

        n_nom = np.array([r.n for r in mi.results]) / 1e3
        m_nom = np.array([r.m_x for r in mi.results]) / 1e6
        n_des = np.array([r.n for r in f_mi.results]) / 1e3
        m_des = np.array([r.m_x for r in f_mi.results]) / 1e6

        eps_t = np.array([kds.net_tensile_strain(theta=0, d_n=r.d_n) for r in mi.results])
        cls = [kds.section_classification(e) for e in eps_t]

        fig, ax = plt.subplots(figsize=(7.0, 5.6))
        ax.plot(m_nom, n_nom, color="grey", lw=1.0, zorder=1, label="공칭 상관도")
        for name, colour in BAND.items():
            sel = [i for i, c in enumerate(cls) if c == name]
            ax.scatter(m_nom[sel], n_nom[sel], s=26, color=colour, zorder=3, label=name)

        ax.axhline(0, color="k", lw=0.6)
        ax.set_xlabel("휨모멘트 Mn (kN·m)")
        ax.set_ylabel("축력 Pn (kN)")
        ax.set_title("공칭 상관도를 순인장변형률로 분류하면")
        ax.legend(loc="lower right", fontsize=9)
        """),

        md(r"""
        ## 6. 상관도를 따라 $\phi$ 가 어떻게 변하는가

        **아래 코드가 하는 일** — 같은 상관도의 각 점에서 $\phi$ 만 뽑아 축력에
        대해 그린다.

        **볼 것** — 2절의 $\phi(\varepsilon_t)$ 곡선과 **같은 모양이 좌우로
        뒤집혀** 나타난다. 축력이 커질수록 $\varepsilon_t$ 가 줄기 때문이다.
        """),
        code("""
        fig, ax = plt.subplots(figsize=(7.2, 4.2))

        phis_arr = np.array(phis)
        for name, colour in BAND.items():
            sel = [i for i, c in enumerate(cls) if c == name]
            ax.scatter(n_nom[sel], phis_arr[sel], s=26, color=colour, label=name)

        ax.plot(n_nom, phis_arr, color="k", lw=0.8, zorder=0)
        ax.axhline(0.85, color=C_TENS, ls="--", lw=0.8)
        ax.axhline(kds.phi_comp, color=C_COMP, ls="--", lw=0.8)
        ax.set_xlabel("공칭 축력 Pn (kN)")
        ax.set_ylabel("강도감소계수 φ")
        ax.set_title("상관도를 따라가며 본 φ")
        ax.set_ylim(0.60, 0.90)
        ax.legend(fontsize=9)
        """),

        md(r"""
        ## 7. 설계 곡선은 왜 공칭 곡선과 평행하지 않은가

        여기가 이 시간의 핵심이다. 설계 상관도는 공칭 상관도에 **일정한 수를
        곱한 것이 아니다.** 점마다 다른 $\phi$ 가 곱해진다.

        게다가 압축측은 최대 설계 축강도 $\alpha\phi P_o$ 에서 **잘린다**
        (KDS 14 20 20 식 (4.1-16), (4.1-17)). 띠철근 $\alpha = 0.80$,
        나선철근 $0.85$ 다.

        **왜 이 상한이 따로 필요한가.** $\phi$ 는 파괴 양상에 대한 벌점이지,
        **편심에 대한 보험이 아니다.** 순수압축으로 설계한 기둥이라도 시공
        오차, 하중의 우발적 편심, 기둥의 초기 휨 때문에 실제로는 약간의 모멘트를
        받는다. 상관도 꼭짓점 근처는 기울기가 매우 가팔라서, 작은 모멘트가
        생기면 축강도가 급격히 떨어진다. 그래서 기준은 아예 그 영역을 쓰지 못하게
        잘라 놓았다. 이것이 $\alpha$ 의 정체다 — 최소 편심을 강제하는 장치다.

        **아래 코드가 하는 일** — 공칭과 설계 상관도를 겹쳐 그리고, 같은 축력
        지점을 점선으로 이어 간격을 보인다. 최대 설계 축강도를 가로 파선으로
        표시한다.
        """),
        code("""
        n_max_nom, n_max_des = kds.max_axial_strength()

        fig, ax = plt.subplots(figsize=(7.0, 5.6))
        ax.plot(m_nom, n_nom, color="grey", lw=1.6, label="공칭 (Mn, Pn)")
        ax.plot(m_des, n_des, color="#1b4f7f", lw=1.8, label="설계 (φMn, φPn)")

        for i in range(0, len(m_nom), 4):
            ax.plot([m_nom[i], m_des[i]], [n_nom[i], n_des[i]],
                    color="grey", lw=0.6, ls=":")

        ax.axhline(n_max_des / 1e3, color=C_COMP, ls="--", lw=1.0)
        ax.annotate(f"최대 설계 축강도  {kds.alpha_max:.2f}·φPo = {n_max_des / 1e3:,.0f} kN",
                    xy=(8, n_max_des / 1e3 + 90), fontsize=9,
                    ha="left", va="bottom", color=C_COMP)

        ax.axhline(0, color="k", lw=0.6)
        ax.set_xlabel("휨모멘트 (kN·m)")
        ax.set_ylabel("축력 (kN)")
        ax.set_title("공칭 상관도와 설계 상관도 — 간격이 일정하지 않다")
        ax.legend(loc="upper right", fontsize=9)
        """),

        md(r"""
        **아래 코드가 하는 일** — 두 곡선의 **비**를 그린다. 그 비가 곧
        $\phi$ 임을 확인한다.
        """),
        code("""
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(np.abs(m_nom) > 1e-6, m_des / m_nom, np.nan)

        fig, ax = plt.subplots(figsize=(7.2, 3.8))
        ax.plot(n_nom, ratio, "o-", ms=3, color="#1b4f7f", label="φMn / Mn")
        ax.plot(n_nom, phis_arr, lw=1.0, color=C_TRAN, label="φ")
        ax.set_xlabel("공칭 축력 Pn (kN)")
        ax.set_ylabel("비")
        ax.set_title("두 곡선의 비 = 그 점의 φ")
        ax.legend(fontsize=9)
        """),

        md(r"""
        ## 8. 띠철근과 나선철근

        | | 띠철근 | 나선철근 |
        |---|---|---|
        | 압축지배단면의 $\phi$ | 0.65 | **0.70** |
        | 최대 축강도 계수 $\alpha$ | 0.80 | **0.85** |

        **왜 우대하는가.** 나선철근은 심부 콘크리트를 **원주 방향으로 구속**한다.
        피복이 떨어져 나간 뒤에도 심부가 삼축응력 상태에 놓여 축력을 유지하며
        변형을 이어 간다. 즉 압축파괴가 덜 급작스럽다 — 3절에서 말한 "경고"가
        생긴다. $\phi$ 가 파괴 양상에 대한 벌점이므로, 양상이 나아지면 벌점도
        줄어드는 것이 일관된다.

        띠철근은 모서리에서만 구속이 걸려서 같은 효과를 내지 못한다. 나선철근의
        우대를 받으려면 KDS 14 20 50 의 나선철근 상세 규정(간격, 철근비, 겹침)을
        만족해야 한다.

        **아래 코드가 하는 일** — 같은 단면을 띠철근과 나선철근으로 각각 풀어
        설계 상관도를 겹쳐 그리고, 몇 개 지점의 값을 표로 비교한다.
        """),
        code("""
        kds_s = column(column_type="spiral")
        f_mi_s, _, _ = kds_s.moment_interaction_diagram(n_points=48, progress_bar=False)

        m_s = np.array([r.m_x for r in f_mi_s.results]) / 1e6
        n_s = np.array([r.n for r in f_mi_s.results]) / 1e3

        fig, ax = plt.subplots(figsize=(7.0, 5.6))
        ax.plot(m_des, n_des, lw=1.8, color="#1b4f7f", label="띠철근  (φ=0.65, α=0.80)")
        ax.plot(m_s, n_s, lw=1.8, color="#7a3b9c", label="나선철근  (φ=0.70, α=0.85)")
        ax.axhline(0, color="k", lw=0.6)
        ax.set_xlabel("설계 휨모멘트 φMn (kN·m)")
        ax.set_ylabel("설계 축력 φPn (kN)")
        ax.set_title("같은 단면, 횡보강 방식만 다를 때")
        ax.legend(loc="upper right", fontsize=9)
        """),
        code("""
        _, n_max_t = kds.max_axial_strength()
        _, n_max_s = kds_s.max_axial_strength()

        print(f"{'':16}{'띠철근':>13}{'나선철근':>13}{'차이':>9}")
        print("-" * 52)
        print(f"{'최대 설계 축강도':16}{n_max_t / 1e3:10,.0f} kN"
              f"{n_max_s / 1e3:10,.0f} kN{(n_max_s / n_max_t - 1) * 100:8.1f} %")

        for n_d in [1500, 2500]:
            m_t = kds.ultimate_bending_capacity(n_design=n_d * 1e3)[0].m_x / 1e6
            m_sp = kds_s.ultimate_bending_capacity(n_design=n_d * 1e3)[0].m_x / 1e6
            print(f"{f'φMn @ {n_d} kN':16}{m_t:9,.1f} kN·m{m_sp:9,.1f} kN·m"
                  f"{(m_sp / m_t - 1) * 100:8.1f} %")
        """),

        md(r"""
        **볼 것** — 나선철근 상관도가 압축측에서 바깥으로 밀려난다. 휨이
        지배하는 아래쪽에서는 두 곡선이 겹친다. 그쪽은 어차피 $\phi = 0.85$ 로
        같기 때문이다. **우대는 취성 파괴 영역에서만 주어진다.**

        ## 9. 직접 바꿔 보기

        **아래 코드가 하는 일** — 철근 항복강도를 바꿔 $\varepsilon_y$ 와
        $\varepsilon_{t,tl}$ 이 어떻게 움직이는지, 그래서 변화구간이 어떻게
        넓어지는지 본다.
        """),
        code("""
        fy = 600     # ← 400, 500, 600 으로 바꿔 보라
        fck = 27     # ← 27, 40, 60 으로 바꿔 보라

        kds_x = column(fck=fck, fy=fy)

        print(f"fy = {fy} MPa,  fck = {fck} MPa")
        print(f"  εy    = {kds_x.eps_y:.5f}   (= fy / 200,000)")
        print(f"  εt,tl = {kds_x.eps_tl:.5f}   (= max(0.005, 2.5·εy))")
        print(f"  변화구간 폭 = {kds_x.eps_tl - kds_x.eps_y:.5f}"
              f"   (SD400 기준 {kds.eps_tl - kds.eps_y:.5f})")

        eps_x = np.linspace(0, 0.012, 300)
        fig, ax = plt.subplots(figsize=(7.2, 4.0))
        ax.plot(eps_x, [kds.capacity_reduction_factor(e) for e in eps_x],
                lw=1.6, label="SD400 (기준)")
        ax.plot(eps_x, [kds_x.capacity_reduction_factor(e) for e in eps_x],
                lw=1.6, ls="--", label=f"SD{fy} (바꾼 값)")
        ax.set_xlabel("순인장변형률 εt")
        ax.set_ylabel("강도감소계수 φ")
        ax.set_title("철근 항복강도가 바뀌면 변화구간이 어떻게 움직이나")
        ax.set_ylim(0.60, 0.90)
        ax.legend(fontsize=9)
        """),

        md(r"""
        ## 10. 생각해 볼 문제

        1. **SD600 을 쓰면 왜 인장지배단면을 만들기 어려워지는가?**
           SD600 의 $\varepsilon_y = 0.003$ 이므로 인장지배한계가
           $2.5 \times 0.003 = 0.0075$ 로 올라간다. 같은 단면에서 이 조건을
           만족시키려면 무엇을 바꿔야 하는가? 고강도 철근을 쓰는 이득과 이
           부담을 견줘 보라.

        2. **철근비를 늘리면 $\phi M_n$ 은 계속 커지는가?**
           휨부재에서 인장철근을 계속 늘려 보라. 어느 지점부터 $\phi$ 가 떨어지고
           $\phi M_n$ 의 증가가 둔해진다. 그 지점의 물리적 의미는?
           ([L3](L3_설계파라미터.ipynb) 에서 직접 확인한다.)

        3. **$\phi$ 를 곱한 뒤에도 압축측 상한 $\alpha\phi P_o$ 가 왜 또
           필요한가?** 7절의 설명을 자기 말로 다시 써 보라. $\phi$ 만으로는
           무엇을 막지 못하는가?

        4. **나선철근의 우대를 받으려면 어떤 조건을 만족해야 하는가?**
           KDS 14 20 50 의 나선철근 상세 규정을 찾아보고, 조건을 못 지킨
           나선철근 기둥은 어떻게 취급해야 할지 논하라.

        ## 정리

        - $\phi$ 는 표에서 찾는 상수가 아니라 $\varepsilon_t$ 의 **연속 함수**다.
        - 벌점의 근거는 재료의 불확실성이 아니라 **파괴의 예고 여부**다.
        - 그래서 설계 상관도는 공칭 상관도와 평행할 수 없다.
        - 압축측 절단($\alpha\phi P_o$)은 $\phi$ 와 별개의 장치로, 최소 편심을
          강제한다.
        - 나선철근의 우대는 구속 효과로 파괴 양상이 나아진 데 대한 보상이며,
          취성 영역에서만 주어진다.

        조문과 구현 함수의 대응은
        [설계식 목록](../user_guide/design_codes/equations.md) 에 정리되어 있다.
        다음 편은 [L3 · 설계 파라미터](L3_설계파라미터.ipynb) 다.
        """),
    ], directory=LECTURES)


# ══════════════════════════════════════════════════════════════════════════
def nb_l3_params():
    """강의 L3 - 무엇을 올려야 하는가."""
    return write("L3_설계파라미터", [
        md(r"""
        # L3 · 강도가 모자란다 — 무엇을 올릴 것인가

        ## 이 시간에 답할 질문

        검토 결과 $\phi M_n < M_u$ 가 나왔다. 손에 쥔 선택지는 넷이다.

        1. 콘크리트 강도 $f_{ck}$ 를 올린다
        2. 철근 항복강도 $f_y$ 를 올린다
        3. 철근을 더 넣는다 ($A_s$)
        4. 단면을 키운다 ($d$)

        **어느 것이 가장 잘 듣는가? 그리고 각각 무엇을 대가로 치르는가?**

        학생들은 대개 1번을 먼저 떠올린다. 콘크리트 구조물이니 콘크리트를
        키우면 될 것 같아서다. 이 시간에는 그 직관이 왜 틀리는지 숫자로 본다.

        ## 근거 조문

        | 내용 | 조문 |
        |---|---|
        | 등가직사각형 응력블록 | KDS 14 20 20 4.1.1(8), 표 4.1-2 |
        | 강도감소계수 | KDS 14 20 10 4.3.3(2) |
        | 최소 휨철근량 $\phi M_n \ge 1.2 M_{cr}$ | KDS 14 20 20 4.2.2 |
        | 파괴계수 $f_r = 0.63\lambda\sqrt{f_{ck}}$ | KDS 14 20 30 4.2.1 |
        | 처짐을 계산하지 않아도 되는 최소 두께 | KDS 14 20 30 표 4.2-1 |
        """, EXPLORER_NOTE),

        md("""
        ## 0. 준비

        **아래 코드가 하는 일** — 한글 글꼴을 등록하고 단면 분류 색을 정한다.
        """),
        code(SETUP),

        md(r"""
        **아래 코드가 하는 일** — 보를 만드는 함수를 정의한다. 이번 편에서는
        $f_{ck}$, $f_y$, 철근 개수, 단면 깊이를 모두 인자로 바꿀 수 있어야
        하므로 함수 하나로 묶는다.
        """),
        code(BEAM_DEF),

        md(r"""
        ## 1. 기준 단면

        **아래 코드가 하는 일** — 기준이 될 보를 만들고 주요 값을 출력한다.
        400 × 600, 하부 4-D22, $f_{ck}$ 27 MPa, SD400 이다. 앞으로 이 값을
        하나씩 바꿔 가며 비교한다.
        """),
        code("""
        BASE = dict(fck=27, fy=400, n_bar=4, d=600)

        def evaluate(**kwargs):
            \"\"\"보 하나를 풀어 설계에 필요한 값을 한 묶음으로 돌려준다.\"\"\"
            opts = {**BASE, **kwargs}
            kds = beam(**opts)
            f_res, u_res, phi = kds.ultimate_bending_capacity()
            eps_t = kds.net_tensile_strain(theta=0, d_n=u_res.d_n)
            cracked = kds.calculate_cracked_properties()
            gross = kds.get_gross_properties()
            return {
                "kds": kds,
                "d_eff": depth(kds),
                "As": opts["n_bar"] * 387.1,
                "eps_t": eps_t,
                "cls": kds.section_classification(eps_t),
                "phi": phi,
                "Mn": u_res.m_x / 1e6,
                "phiMn": f_res.m_x / 1e6,
                "Mcr": cracked.m_cr / 1e6,
                "Icr_Ig": cracked.e_ixx_c_cr / gross.e_ixx_c,
            }

        base = evaluate()
        print(f"단면            400 × {BASE['d']} mm, 하부 {BASE['n_bar']}-D22")
        print(f"유효깊이 d      {base['d_eff']:.0f} mm")
        print(f"철근량 As       {base['As']:.0f} mm²   (ρ = {base['As'] / (400 * base['d_eff']) * 100:.2f} %)")
        print(f"순인장변형률 εt  {base['eps_t']:.5f}  →  {base['cls']}")
        print(f"강도감소계수 φ   {base['phi']:.3f}")
        print(f"공칭휨강도 Mn    {base['Mn']:.1f} kN·m")
        print(f"설계휨강도 φMn   {base['phiMn']:.1f} kN·m")
        print(f"균열모멘트 Mcr   {base['Mcr']:.1f} kN·m")
        """),

        md(r"""
        ## 2. 하나씩 20 % 씩 올려 보기

        가장 공정한 비교는 **같은 비율로 올렸을 때 강도가 몇 % 오르는가**를
        보는 것이다. 공학에서는 이를 민감도 또는 탄성도라 부른다.

        **아래 코드가 하는 일** — 네 변수를 각각 20 % 올려 설계휨강도의 변화를
        계산한다. 철근 개수는 정수라 4 → 5 (25 %) 로 올리고, 비율을 맞춰
        환산해 함께 표시한다.
        """),
        code("""
        cases = [
            ("fck  27 → 32.4 MPa", dict(fck=32.4), 0.20),
            ("fy   400 → 480 MPa", dict(fy=480), 0.20),
            ("As   4 → 5-D22", dict(n_bar=5), 0.25),
            ("d    600 → 720 mm", dict(d=720), 0.20),
        ]

        print(f"{'바꾼 것':22} {'φMn(kNm)':>10} {'증가':>8} {'투입 대비':>10} {'단면 분류':>12}")
        print("-" * 68)
        results = []
        for label, kw, ratio in cases:
            r = evaluate(**kw)
            gain = r["phiMn"] / base["phiMn"] - 1
            results.append((label, r, gain, ratio))
            print(f"{label:22} {r['phiMn']:10.1f} {gain * 100:7.1f} % "
                  f"{gain / ratio:9.2f} {r['cls']:>12}")
        """),

        md(r"""
        **읽는 법.** "투입 대비" 열이 탄성도다. 1.0 이면 20 % 올렸을 때 강도도
        20 % 올랐다는 뜻이다.

        결과의 순서가 직관과 다르다. **$f_{ck}$ 가 압도적으로 꼴찌**다.

        ## 3. 왜 콘크리트 강도는 휨강도에 거의 안 듣는가

        손계산 식을 다시 보면 이유가 바로 보인다.

        $$
        M_n = A_s f_y \left(d - \frac{a}{2}\right),
        \qquad a = \frac{A_s f_y}{\eta (0.85 f_{ck})\, b}
        $$

        $f_{ck}$ 는 **$a$ 의 분모에만** 들어 있다. 인장력 $T = A_s f_y$ 는
        $f_{ck}$ 와 무관하다. 콘크리트를 강하게 하면 압축블록이 얇아져 지렛대 팔
        $d - a/2$ 가 조금 길어질 뿐이다. 그런데 $a$ 는 애초에 $d$ 에 비해 작다 —
        이 보에서는 68 mm 대 539 mm 다. 그 절반이 몇 mm 줄어 봐야 지렛대 팔은
        1 % 도 안 늘어난다.

        **휨강도는 철근이 지배한다.** 콘크리트는 압축력을 받아 주는 역할이고,
        그 역할에는 이미 충분한 강도를 갖고 있다.

        **아래 코드가 하는 일** — 그 사실을 그림으로 확인한다. $f_{ck}$ 를
        21 부터 60 MPa 까지 올리며 $\phi M_n$, 압축블록 깊이 $a$, 지렛대 팔을
        함께 그린다.
        """),
        code("""
        fck_list = [21, 24, 27, 30, 35, 40, 50, 60]
        rows = [(f, evaluate(fck=f)) for f in fck_list]

        from concreteproperties_kds import stress_block_parameters
        a_list = []
        for f, r in rows:
            _, eta, _ = stress_block_parameters(f)
            a_list.append(r["As"] * BASE["fy"] / (eta * 0.85 * f * 400))

        fig, axes = plt.subplots(1, 2, figsize=(11, 3.9))

        axes[0].plot(fck_list, [r["phiMn"] for _, r in rows], "o-", color="#1b4f7f", lw=2)
        axes[0].set_xlabel("콘크리트 강도 fck (MPa)")
        axes[0].set_ylabel("설계휨강도 φMn (kN·m)")
        axes[0].set_title("fck 를 3배 가까이 올려도")
        axes[0].set_ylim(0, max(r["phiMn"] for _, r in rows) * 1.15)

        axes[1].plot(fck_list, a_list, "o-", color=C_COMP, lw=2, label="압축블록 깊이 a")
        axes[1].plot(fck_list, [rows[0][1]["d_eff"] - a / 2 for a in a_list],
                     "s-", color=C_TENS, lw=2, label="지렛대 팔 d - a/2")
        axes[1].set_xlabel("콘크리트 강도 fck (MPa)")
        axes[1].set_ylabel("길이 (mm)")
        axes[1].set_title("정작 바뀌는 것은 이것뿐이다")
        axes[1].legend(fontsize=9)
        axes[1].set_ylim(0, rows[0][1]["d_eff"] * 1.1)

        fig.tight_layout()
        """),

        md(r"""
        ## 4. 그런데 $f_{ck}$ 는 다른 데 잘 듣는다

        휨강도에 안 듣는다고 $f_{ck}$ 를 올리는 것이 헛일은 아니다. **강성과
        균열**에는 매우 잘 듣는다.

        - 탄성계수 $E_c = 8500\sqrt[3]{f_{cm}}$ — 처짐이 준다
        - 파괴계수 $f_r = 0.63\lambda\sqrt{f_{ck}}$ — 균열모멘트 $M_{cr}$ 이 커져
          균열이 늦게 생긴다

        설계에서 지배하는 것이 강도가 아니라 **처짐이나 균열**일 때가 많다.
        특히 장경간 보나 슬래브가 그렇다. 그럴 때는 $f_{ck}$ 가 정답이 된다.

        **아래 코드가 하는 일** — 세 가지를 각자의 기준값(21 MPa)으로 나눠
        정규화해 한 그림에 겹친다. 배율이 1 에서 얼마나 벌어지는지 비교한다.
        """),
        code("""
        base21 = rows[0][1]
        fig, ax = plt.subplots(figsize=(7.4, 4.2))
        ax.axhline(1.0, color="grey", lw=0.8, ls=":")

        for key, colour, label in [
            ("phiMn", "#1b4f7f", "설계휨강도 φMn"),
            ("Mcr", C_TRAN, "균열모멘트 Mcr"),
            ("Icr_Ig", C_TENS, "균열단면 강성비 Icr/Ig"),
        ]:
            ax.plot(fck_list, [r[key] / base21[key] for _, r in rows],
                    "o-", color=colour, lw=2, label=label)

        ax.set_xlabel("콘크리트 강도 fck (MPa)")
        ax.set_ylabel("fck 21 MPa 대비 배율")
        ax.set_title("fck 는 강도가 아니라 강성·균열에 듣는다")
        ax.legend(fontsize=9)
        """),

        md(r"""
        ## 5. 철근을 계속 넣으면 어떻게 되는가

        철근이 휨강도를 지배한다면, 그냥 계속 넣으면 되지 않을까.

        여기서 [L2](L2_강도감소계수.ipynb) 의 $\phi$ 가 되돌아온다. 철근을 넣을수록
        중립축이 깊어져 $\varepsilon_t$ 가 줄고, 어느 지점에서 **인장지배를
        벗어나 $\phi$ 가 떨어지기 시작한다.** 그때부터는 넣은 만큼 강도가
        따라오지 않는다.

        **아래 코드가 하는 일** — 철근 개수를 2 부터 10 까지 늘리며 $M_n$,
        $\phi M_n$, $\varepsilon_t$, $\phi$ 를 계산해 두 장으로 그린다.
        """),
        code("""
        n_list = list(range(2, 11))
        srows = [(n, evaluate(n_bar=n)) for n in n_list]

        fig, axes = plt.subplots(1, 2, figsize=(11, 4.0))

        axes[0].plot(n_list, [r["Mn"] for _, r in srows], "s--", color="grey",
                     lw=1.6, label="공칭 Mn")
        axes[0].plot(n_list, [r["phiMn"] for _, r in srows], "o-", color="#1b4f7f",
                     lw=2.2, label="설계 φMn")
        for n, r in srows:
            axes[0].plot([n], [r["phiMn"]], "o", ms=7, color=BAND[r["cls"]], zorder=3)
        axes[0].set_xlabel("인장철근 개수 (D22)")
        axes[0].set_ylabel("휨강도 (kN·m)")
        axes[0].set_title("점 색은 단면 분류")
        axes[0].legend(fontsize=9)

        kds_ref = srows[0][1]["kds"]
        axes[1].plot(n_list, [r["eps_t"] for _, r in srows], "o-", color="k", lw=2)
        axes[1].axhline(kds_ref.eps_tl, color=C_TENS, ls="--", lw=1.2)
        axes[1].axhline(kds_ref.eps_y, color=C_COMP, ls="--", lw=1.2)
        axes[1].text(n_list[-1], kds_ref.eps_tl, " 인장지배 경계", va="bottom",
                     ha="right", color=C_TENS, fontsize=9)
        axes[1].text(n_list[-1], kds_ref.eps_y, " 압축지배 경계", va="bottom",
                     ha="right", color=C_COMP, fontsize=9)
        for n, r in srows:
            axes[1].plot([n], [r["eps_t"]], "o", ms=7, color=BAND[r["cls"]], zorder=3)
        axes[1].set_xlabel("인장철근 개수 (D22)")
        axes[1].set_ylabel("순인장변형률 εt")
        axes[1].set_title("철근을 넣을수록 εt 가 준다")

        fig.tight_layout()
        """),

        md("""
        **아래 코드가 하는 일** — 철근 하나를 더 넣을 때마다 강도가 얼마나
        늘어나는지, 그 증분을 표로 본다. 수익 체감이 어디서 시작되는지 확인한다.
        """),
        code("""
        print(f"{'철근':>8} {'εt':>9} {'φ':>7} {'φMn':>9} {'직전 대비 증가':>14} {'단면 분류':>12}")
        print("-" * 66)
        prev = None
        for n, r in srows:
            inc = "—" if prev is None else f"{r['phiMn'] - prev:+.1f} kN·m"
            print(f"{n:6d}-D22 {r['eps_t']:9.5f} {r['phi']:7.3f} {r['phiMn']:9.1f} "
                  f"{inc:>14} {r['cls']:>12}")
            prev = r["phiMn"]
        """),

        md(r"""
        **여기서 알 것.** 인장지배를 유지하는 동안은 철근 하나당 증가폭이 거의
        일정하다. 변화구간에 들어서면 증가폭이 눈에 띄게 줄어든다.

        **설계자가 읽어야 할 신호.** 증가폭이 꺾이기 시작했다면 그것은
        "철근을 더 넣지 말고 **단면을 키우라**"는 뜻이다. 기준이 직접 그렇게
        말하지는 않지만, $\phi$ 를 통해 경제적 유인을 만들어 그렇게 유도한다.
        이것이 강도감소계수의 숨은 역할이다 — 안전만이 아니라 **바람직한 설계
        형태를 유도**한다.

        ## 6. 단면 깊이가 가장 잘 듣는다

        2절에서 $d$ 의 탄성도가 1 을 넘었다. 이유는 $M_n = A_s f_y (d - a/2)$
        에서 $d$ 가 **직접** 곱해지기 때문이다. 게다가 $d$ 를 키우면
        $\varepsilon_t$ 도 커져서 $\phi$ 가 유지되거나 오른다. 두 효과가 같은
        방향으로 작용한다.

        **아래 코드가 하는 일** — 단면 깊이를 500 부터 800 mm 까지 바꾸며
        $\phi M_n$ 과 $\varepsilon_t$ 를 함께 본다.
        """),
        code("""
        d_list = [500, 550, 600, 650, 700, 750, 800]
        drows = [(d, evaluate(d=d)) for d in d_list]

        fig, ax = plt.subplots(figsize=(7.4, 4.0))
        ax.plot(d_list, [r["phiMn"] for _, r in drows], "o-", color="#1b4f7f", lw=2.2)
        ax.set_xlabel("단면 깊이 h (mm)")
        ax.set_ylabel("설계휨강도 φMn (kN·m)")
        ax.set_title("깊이를 키우면 강도는 거의 비례해 오른다")

        ax2 = ax.twinx()
        ax2.plot(d_list, [r["eps_t"] for _, r in drows], "s--", color=C_TENS, lw=1.6)
        ax2.set_ylabel("순인장변형률 εt", color=C_TENS)
        ax2.tick_params(axis="y", labelcolor=C_TENS)
        ax2.grid(False)

        ax.text(d_list[1], max(r["phiMn"] for _, r in drows) * 0.35,
                "파랑: φMn (왼쪽 축)\\n초록 점선: εt (오른쪽 축)", fontsize=9)
        """),

        md(r"""
        **대가는 무엇인가.** 자중이 늘고, 층고가 커지고, 공사비가 오른다.
        보 깊이는 대개 건축 계획이 먼저 정해 놓는 값이라, 구조기술자가 마음대로
        바꿀 수 없는 경우가 많다. **가장 잘 듣는 변수가 가장 못 바꾸는 변수**인
        것이 실무의 현실이다.

        ## 7. 설계의 의도 — 왜 최소 두께 표가 따로 있는가

        KDS 14 20 30 표 4.2-1 은 **처짐을 계산하지 않아도 되는 최소 두께**를
        규정한다. 단순지지 보는 $\ell/16$, 1단 연속은 $\ell/18.5$ 같은 식이다.

        왜 강도와 별개로 이런 규정을 둘까. 4절에서 본 것처럼 **처짐을 지배하는
        것과 강도를 지배하는 것이 다르기** 때문이다. 강도는 철근이, 처짐은 강성
        $E_c I$ 가, 즉 사실상 **단면 깊이의 세제곱**이 지배한다. 철근을 아무리
        넣어도 처짐은 별로 안 줄어든다.

        그래서 기준은 순서를 정해 준다.

        1. 먼저 최소 두께로 **깊이를 정한다** (사용성)
        2. 그 깊이에서 필요한 **철근을 계산한다** (강도)

        이 순서를 뒤집어 강도만 보고 얇은 보를 설계하면, 강도 검토는 통과하고
        처짐 검토에서 걸린다. 그때는 이미 다른 것이 다 정해진 뒤라 되돌리기가
        어렵다.

        **아래 코드가 하는 일** — 최소 두께 규정이 실제로 어떤 깊이를 요구하는지
        경간별로 확인한다.
        """),
        code("""
        from concreteproperties_kds import minimum_thickness

        supports = ("단순지지", "1단연속", "양단연속", "캔틸레버")

        print(f"{'경간(m)':>8}" + "".join(f"{s:>11}" for s in supports))
        print("-" * 52)
        for span in (4, 6, 8, 10, 12):
            vals = [minimum_thickness(span=span * 1000, member="보", support=s, fy=400)
                    for s in supports]
            print(f"{span:8.0f} " + " ".join(f"{v:9.0f}mm" for v in vals))
        """),

        md(r"""
        ## 8. 직접 바꿔 보기

        **아래 코드가 하는 일** — 2절의 민감도 비교를 원하는 조건으로 다시
        돌린다. 기준 단면과 증가율을 바꿔 가며, 순위가 뒤집히는 경우가 있는지
        찾아보라.
        """),
        code("""
        BASE = dict(fck=27, fy=400, n_bar=8, d=600)   # ← n_bar 를 4 에서 8 로 바꿨다
        base = evaluate()

        print(f"기준: fck {BASE['fck']}, SD{BASE['fy']}, {BASE['n_bar']}-D22, h {BASE['d']} mm")
        print(f"      φMn = {base['phiMn']:.1f} kN·m,  εt = {base['eps_t']:.5f}"
              f"  →  {base['cls']}\\n")

        print(f"{'바꾼 것':22} {'φMn(kNm)':>10} {'증가':>8} {'투입 대비':>10} {'단면 분류':>12}")
        print("-" * 68)
        for label, kw, ratio in [
            ("fck  +20 %", dict(fck=BASE["fck"] * 1.2), 0.20),
            ("fy   +20 %", dict(fy=min(600, BASE["fy"] * 1.2)), 0.20),
            ("As   +25 %", dict(n_bar=BASE["n_bar"] + 2), 0.25),
            ("d    +20 %", dict(d=int(BASE["d"] * 1.2)), 0.20),
        ]:
            r = evaluate(**kw)
            gain = r["phiMn"] / base["phiMn"] - 1
            print(f"{label:22} {r['phiMn']:10.1f} {gain * 100:7.1f} % "
                  f"{gain / ratio:9.2f} {r['cls']:>12}")

        BASE = dict(fck=27, fy=400, n_bar=4, d=600)   # 기준을 되돌린다
        """),

        md(r"""
        ## 9. 생각해 볼 문제

        1. **8절에서 철근을 8-D22 로 늘린 뒤 민감도 순위가 어떻게 달라졌는가?**
           특히 $A_s$ 의 탄성도가 왜 떨어졌는지 $\phi$ 와 연결해 설명하라.

        2. **$f_y$ 를 올리는 것은 $A_s$ 를 늘리는 것과 수식상 같다**
           ($T = A_s f_y$). 그런데 설계에서 두 선택은 같지 않다. 무엇이
           다른가? ([L2](L2_강도감소계수.ipynb) 10절 1번 문제와 함께 생각하라.)

        3. **경간 10 m 단순지지 보를 설계한다.** 표에서 최소 두께가 625 mm 로
           나왔다. 그런데 건축 계획상 500 mm 밖에 쓸 수 없다면 어떻게 하겠는가?
           KDS 14 20 30 은 이 경우 무엇을 요구하는가?

        4. **"콘크리트 강도를 올려도 휨강도는 거의 안 오른다"는 결론이 항상
           성립하는가?** 압축철근이 많은 복철근 보나, 축력을 함께 받는 기둥에서는
           어떨까? 이유를 들어 예상한 뒤 코드로 확인하라.

        ## 정리

        | 올리는 것 | 휨강도 | 처짐·균열 | 대가 |
        |---|---|---|---|
        | $f_{ck}$ | 거의 안 듦 | **잘 듦** | 배합·품질관리 |
        | $f_y$ | 잘 듦 | 안 듦 | 인장지배 유지가 어려워짐 |
        | $A_s$ | 잘 듦, 그러나 **수익 체감** | 조금 듦 | 배근 간격·정착 |
        | $d$ | **가장 잘 듦** | **가장 잘 듦** | 자중·층고·공사비 |

        - 휨강도는 철근이 지배한다. 콘크리트 강도는 지렛대 팔에만 관여한다.
        - $f_{ck}$ 는 강성과 균열에 듣는다. 처짐이 지배하는 부재에서는 이쪽이
          정답이다.
        - 철근의 수익 체감은 $\phi$ 가 만든다. 증가폭이 꺾이면 단면을 키우라는
          신호다.
        - 기준이 최소 두께를 먼저 정하게 한 것은, 처짐과 강도의 지배 인자가
          다르기 때문이다.

        조문과 구현 함수의 대응은
        [설계식 목록](../user_guide/design_codes/equations.md) 에 정리되어 있다.
        """),
    ], directory=LECTURES)


BUILDERS = [nb_l1_block, nb_l2_phi, nb_l3_params]


def main() -> int:
    """강의 노트북을 생성하고, ``--run`` 이면 실행까지 한다.

    Returns:
        종료 코드
    """
    LECTURES.mkdir(parents=True, exist_ok=True)

    paths = []
    for builder in BUILDERS:
        path = builder()
        paths.append(path)
        print(f"생성  {path.relative_to(LECTURES.parents[1])}")

    if "--run" in sys.argv:
        print("\n노트북 실행")
        return execute(paths)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
