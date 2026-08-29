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

from nbbuild import FLOWCHART, code, execute, md, write

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




# ══════════════════════════════════════════════════════════════════════════
DECK_SETUP = r'''
from concreteproperties_kds.kds import stress_block_parameters
from concreteproperties_kds.kds24 import (
    BAR_SPACING_MAX,
    BAR_SPACING_MIN,
    MIN_THICKNESS_RC,
    WHEEL_LOAD,
    bar_area,
    cantilever_live_load_moment,
    dead_load_moment,
    deck_span,
    design_compressive_strength,
    design_deck,
    design_yield_strength,
    distribution_steel_ratio,
    equivalent_block,
    impact_factor,
    live_load_moment,
    max_bar_diameter,
    max_bar_spacing,
    minimum_flexural_steel,
    nominal_cover,
    provided_steel_area,
    required_steel_area,
)

# 기준 조건 — 앞으로 이 값을 하나씩 바꿔 가며 비교한다
BASE = dict(
    girder_spacing=2.5,   # 거더 중심 간격 (m)   ← 바꿔 보라
    thickness=240.0,      # 바닥판 두께 (mm)     ← 바꿔 보라
    bar_diameter=16.0,    # 주철근 지름 (mm)     ← 바꿔 보라
    bar_spacing=150.0,    # 주철근 간격 (mm)     ← 바꿔 보라
    exposure="EC1",       # 노출등급             ← 바꿔 보라
    pavement=80.0,        # 포장 두께 (mm)       ← 바꿔 보라
)

C_DEAD = "#5b6472"
C_LIVE = "#1f6feb"
C_CAP = "#1f7a4d"
C_K14 = "#b3372c"

print("바닥판 설계 함수를 불러왔다.")
print(f"윤하중 P = {WHEEL_LOAD:.0f} kN   (KL-510 의 192 kN 축의 절반)")
'''

L14_DEF = r'''
def required_steel_kds14(m_u, d, fck=27.0, fy=400.0, b=1000.0, phi=0.85):
    """같은 설계휨모멘트를 KDS 14 강도설계법으로 풀어 필요 철근량을 구한다.

    등가직사각형 응력블록으로 단철근 단면의 평형을 푼다.

        phi*As*fy*(d - a/2) = M_u,   a = As*fy / (eta*0.85*fck*b)
    """
    _, eta, _ = stress_block_parameters(fck=fck)
    k = fy / (eta * 0.85 * fck * b)
    # (phi*k*fy/2) As^2 - phi*fy*d*As + M_u = 0
    a2 = phi * k * fy / 2.0
    a1 = -phi * fy * d
    disc = a1**2 - 4 * a2 * m_u
    if disc < 0:
        raise ValueError("단철근으로는 저항할 수 없다")
    return (-a1 - (disc) ** 0.5) / (2 * a2)


print("KDS 14 대조용 함수를 정의했다.")
'''


def nb_l4_deck_interior():
    """강의 L4 - 바닥판 내측슬래브는 왜 따로 설계하는가."""
    return write("L4_바닥판설계_내측슬래브", [
        md(r"""
        # L4 · 바닥판 (내측슬래브) — 트럭을 굴리지 않고 푸는 법

        ## 이 시간에 답할 질문

        거더는 KL-510 트럭을 다리 위로 굴려 가며 최대 단면력을 찾는다. 그런데
        **바닥판은 그렇게 풀지 않는다.** 기준은 식 한 줄을 준다.

        $$
        M_t = \frac{(L + 0.6)\,P}{9.6}
        \qquad [\text{kN} \cdot \text{m/m}]
        $$

        여기서 $L$ 은 거더 간격, $P$ 는 윤하중 96 kN 이다. **트럭의 위치도,
        축간거리도, 다차로 재하계수도 나오지 않는다.**

        1. 왜 바닥판만 이렇게 간단한가?
        2. 이 식은 무엇을 이미 삼키고 있는가?
        3. 바닥판을 두껍게 하면 정말 안전해지는가?
        4. 강도가 아니라 **균열**이 설계를 지배하는 순간은 언제인가?

        :::{note}
        이 편은 거더 사이의 **내측슬래브**만 다룬다. 바깥으로 내민
        **외측슬래브(캔틸레버)** 는 식도 다르고 지배하는 하중도 달라서
        [L5](L5_바닥판설계_외측슬래브.ipynb) 에서 따로 다룬다.
        :::

        ## 근거 조문

        | 내용 | 조문 |
        |---|---|
        | 바닥판의 지간 | KDS 24 10 11 4.6.2.3 |
        | 활하중 휨모멘트 식 $(4.6\text{-}1)$ | KDS 24 10 11 4.6.2.4 |
        | 캔틸레버 식 $(4.6\text{-}4)$ | KDS 24 10 11 4.6.2.5 |
        | 고정하중 휨모멘트 표 4.6-2 | KDS 24 10 11 4.6.2.7 |
        | 전단 검토 생략 | KDS 24 10 11 4.6.2.2(3) |
        | 최소 두께 220 mm, 처짐 한계 | KDS 24 14 21 4.6.5.1 |
        | 경험적 설계법 | KDS 24 14 21 4.6.5.2 |
        | 배력철근 $120/\sqrt{L} \le 67\,\%$ | KDS 24 14 21 4.6.5.3(2) |
        | 피복두께 식 $(4.4\text{-}1)$, 표 4.4-4 | KDS 24 14 21 4.4.4 |
        | 균열 제어 표 4.2-5 | KDS 24 14 21 4.2.3.3 |
        """, EXPLORER_NOTE),

        md("""
        ## 0. 준비

        **아래 코드가 하는 일** — 한글 글꼴을 등록하고 그림 색을 정한다.
        """),
        code(SETUP),
        md(r"""
        **아래 코드가 하는 일** — 이 편에서 따라갈 설계 흐름을 순서도로
        그린다. 각 단계 옆에 근거 조문을 적었다.
        """),
        code(FLOWCHART + '''
design_flowchart(
"바닥판 내측슬래브 설계 흐름",
[
    ("바닥판 지간 결정", "24 10 11 4.6.2.3"),
    ("두께·피복 결정", "24 14 21 4.6.5.1, 4.4.4"),
    ("활하중 휨모멘트 (식 4.6-1)", "24 10 11 4.6.2.4"),
    ("고정하중 휨모멘트 (표 4.6-2)", "24 10 11 4.6.2.7"),
    ("충격 25 % 와 하중조합 극한Ⅰ", "24 12 21 표 4.4-1 · 24 12 11 표 4.1-1"),
    ("휨 설계 — 소요 철근량", "24 14 21 4.1.1"),
    ("최소 철근량·간격 검토", "24 14 21 4.6.5.3"),
    ("균열 제어 (표 4.2-5)", "24 14 21 4.2.3.3"),
    ("배력철근 120/√L ≤ 67 %", "24 14 21 4.6.5.3(2)"),
],
)
        '''),

        md(r"""
        **아래 코드가 하는 일** — 바닥판 설계 함수를 불러오고 기준 조건을
        정한다. 거더 간격 2.5 m, 두께 240 mm, D16@150, 노출등급 EC1,
        포장 80 mm 의 전형적인 거더교 바닥판이다.
        """),
        code(DECK_SETUP),

        md(r"""
        ## 1. 바닥판은 왜 따로 다루는가

        거더는 **선부재**다. 한 방향으로 길고, 단면력이 한 축을 따라 흐른다.
        그래서 트럭을 굴려 영향선의 최대값을 찾는 것이 자연스럽다.

        바닥판은 **판**이다. 윤하중 한 개가 실리면 힘은 사방으로 퍼지고,
        거더 사이에서 아치처럼 버티기도 한다. 이것을 정직하게 풀려면 판 해석을
        해야 하는데, 다리 하나에 바닥판 단면은 수백 개다.

        그래서 기준은 **실물 실험으로 보정한 근사식**을 준다. 이 식들은
        이미 다음을 삼키고 있다.

        - 윤하중이 폭 방향으로 퍼지는 효과
        - 판의 2방향 거동
        - 인접 윤하중의 겹침

        그래서 **전단은 검토하지 않아도 된다**(4.6.2.2(3)). 근사식 자체가
        전단이 문제되지 않는 두께 범위에서 보정되었기 때문이다. 다만 윤하중의
        **뚫림전단**은 별개라 따로 본다(KDS 24 14 21 4.6.5.1(8)).

        > **설계의 의도** — 바닥판 설계식의 단순함은 게으름이 아니라 **판단의
        > 결과**다. 수백 개 단면을 정밀해석하는 비용보다, 보수적으로 보정된
        > 식 한 줄이 낫다고 본 것이다. 대신 그 식이 성립하는 범위(두께,
        > 지간, 연속성)를 상세 규정으로 꽉 조인다.

        **아래 코드가 하는 일** — 기준 조건의 바닥판을 한 번 풀어 전체 그림을
        본다.
        """),
        code("""
        base = design_deck(**BASE)

        print(f"바닥판 지간 L      {base.span:.2f} m")
        print(f"두께 t             {base.thickness:.0f} mm")
        print(f"공칭피복 t_c,nom   {base.cover:.0f} mm")
        print(f"유효깊이 d         {base.d:.0f} mm")
        print()
        print(f"고정하중 휨모멘트   {base.m_dead:6.2f} kN·m/m")
        print(f"활하중 휨모멘트     {base.m_live:6.2f} kN·m/m  (충격 25 % 포함)")
        print(f"설계휨모멘트 M_Ed   {base.m_ed:6.2f} kN·m/m  (극한 I)")
        print()
        print(f"필요 철근량 As,req  {base.as_required:6.0f} mm²/m")
        print(f"최소 철근량 As,min  {base.as_minimum:6.0f} mm²/m")
        print(f"배치 철근량 As      {base.as_provided:6.0f} mm²/m  (D16@150)")
        print(f"설계휨강도 M_Rd     {base.m_rd:6.2f} kN·m/m")
        print()
        for name, ok in base.checks.items():
            print(f"  {'만족' if ok else '불만족'}  {name}")
        """),

        md(r"""
        ## 2. 지간 — 거더 간격이 모든 것을 정한다

        바닥판 설계에서 **설계자가 고르지 못하는 변수**가 하나 있다. 거더
        간격이다. 그것은 상부구조 계획 단계에서 이미 정해진다.

        기준은 지간을 지지보의 **중심 간격**으로 잡되, 순 지간에 바닥판 두께를
        더한 값을 넘길 필요는 없다고 한다(4.6.2.3(1)). PSC 거더처럼 상부플랜지가
        넓으면 중심 간격이 실제보다 훨씬 불리해지기 때문이다.

        **아래 코드가 하는 일** — 거더 폭이 지간에 어떻게 반영되는지 본다.
        """),
        code("""
        for web in (0.0, 0.15, 0.40, 0.60, 1.00):
            L = deck_span(girder_spacing=2.5, thickness=240, web_width=web)
            note = "중심 간격" if L == 2.5 else "순 지간 + 두께"
            label = "미고려" if web == 0 else f"{web:.2f} m"
            print(f"거더 폭 {label:>8}  →  지간 {L:.3f} m   ({note})")
        """),

        md(r"""
        **아래 코드가 하는 일** — 거더 간격을 바꿔 가며 고정하중·활하중·설계
        휨모멘트가 어떻게 갈라지는지 그린다.
        """),
        code("""
        spans = np.linspace(1.5, 4.5, 61)
        rows = [design_deck(**{**BASE, "girder_spacing": s}) for s in spans]

        fig, (ax, bx) = plt.subplots(1, 2, figsize=(11, 4.2))

        ax.plot(spans, [r.m_dead for r in rows], color=C_DEAD, lw=2, label="고정하중")
        ax.plot(spans, [r.m_live for r in rows], color=C_LIVE, lw=2, label="활하중 + 충격")
        ax.plot(spans, [r.m_ed for r in rows], color="k", lw=2.4, label="설계 M$_{Ed}$ (극한 I)")
        ax.axvline(2.5, color="k", ls=":", lw=1)
        ax.set_xlabel("거더 중심 간격 (m)")
        ax.set_ylabel("휨모멘트 (kN·m/m)")
        ax.set_title("거더 간격이 커지면 무엇이 커지는가")
        ax.legend(fontsize=9)

        share = [r.m_live / (r.m_dead + r.m_live) * 100 for r in rows]
        bx.plot(spans, share, color=C_LIVE, lw=2)
        bx.axvline(2.5, color="k", ls=":", lw=1)
        bx.set_xlabel("거더 중심 간격 (m)")
        bx.set_ylabel("전체 중 활하중의 몫 (%)")
        bx.set_title("바닥판은 끝까지 활하중이 지배한다")
        bx.set_ylim(0, 100)
        """),

        md(r"""
        오른쪽 그림이 바닥판과 거더의 결정적인 차이를 보여 준다. 거더는 지간이
        길어질수록 자중이 커져 고정하중이 지배해 가지만, **바닥판은 어떤 간격에서도
        활하중이 80 % 를 넘는다.** 고정하중은 $L^2$ 로, 활하중은 $L$ 에 비례해
        커지는데도 그렇다 — 애초에 활하중 쪽 절대값이 훨씬 크기 때문이다.

        > **설계의 의도** — 이것이 바닥판을 피로와 내구성 관점에서 다뤄야 하는
        > 이유다. 하중의 대부분이 **반복해서 실렸다 빠지는** 하중이다. 콘크리트
        > 바닥판의 피로한계상태 검증을 면제해 주는 대신
        > (KDS 24 14 21 4.6.5.1(3)), 최소 두께·최소 철근량·균열폭을 빡빡하게
        > 묶는 것으로 갈음한다.
        """),

        md(r"""
        ## 3. 활하중 — 식 하나에 무엇이 들어 있나

        식 $(4.6\text{-}1)$ 을 뜯어 보자.

        $$
        M_t = \frac{(L + 0.6) P}{9.6}
        $$

        $L$ 이 지간이니 $M \propto L$ 이다. 그런데 단순보에 집중하중 하나가
        중앙에 놓이면 $M = PL/4$ 다. 두 식의 비를 보면 이 식이 무엇을 하고
        있는지 드러난다.

        **아래 코드가 하는 일** — 기준식과 "윤하중 하나가 중앙에 놓인 단순보"를
        견준다.
        """),
        code("""
        print(f"{'지간':>6}  {'기준식':>9}  {'PL/4':>9}  {'비':>6}  {'등가 분포폭':>10}")
        for L in (1.5, 2.0, 2.5, 3.0, 3.6, 4.5):
            m_code = live_load_moment(span=L)
            m_point = WHEEL_LOAD * L / 4.0
            print(f"{L:5.1f} m  {m_code:7.1f}  {m_point:7.1f}  "
                  f"{m_code / m_point:5.2f}  {m_point / m_code:8.2f} m")
        """),

        md(r"""
        마지막 열이 핵심이다. 기준식은 **윤하중이 폭 1.7 ~ 2.1 m 에 퍼진 것과
        같은 효과**를 준다. 실제 타이어 접지폭은 30 cm 남짓인데도 그렇다.

        그 차이가 판의 2방향 거동이다. 윤하중은 지간방향으로만 흐르지 않고
        옆으로도 퍼진다. 기준식은 그 퍼짐을 **등가 띠의 폭**으로 환산해 놓은
        것이다.

        지간이 길어질수록 폭이 조금씩 넓어지다 2.1 m 근처로 수렴하는데, 이 값이
        우연이 아니다. 주철근이 차량진행방향에 **평행**한 경우의 분포폭
        $E = 1.2 + 0.06L$ 도 정확히 **2.1 m 에서 상한이 걸린다**(식
        $(4.6\\text{-}2)$). 두 식이 서로 다른 형태로 같은 물리적 상한 —
        하나의 윤하중이 퍼질 수 있는 최대 폭 — 을 담고 있는 셈이다.

        여기에 두 가지 보정이 더 붙는다.

        - **연속판 0.8배** — 3지점 이상이면 정모멘트가 20 % 준다(4.6.2.4(2)①나).
        - **충격 1.25배** — 표준트럭하중에만 적용한다(KDS 24 12 21 표 4.4-1).

        **아래 코드가 하는 일** — 두 보정이 각각 얼마나 움직이는지 본다.
        """),
        code("""
        L = BASE["girder_spacing"]
        m_simple = live_load_moment(span=L)
        m_cont = live_load_moment(span=L, continuous=True)
        im = impact_factor()

        print(f"단순판           {m_simple:6.2f} kN·m/m")
        print(f"연속판 (× 0.8)   {m_cont:6.2f} kN·m/m")
        print(f"충격 (× {im:.2f})    {m_cont * im:6.2f} kN·m/m   ← 설계에 쓰는 값")
        print()
        print(f"두 보정을 합치면 단순판 대비 {m_cont * im / m_simple:.3f} 배")
        print("연속으로 만들어 20 % 벌고, 충격으로 25 % 잃는다 — 거의 상쇄된다.")
        """),

        md(r"""
        ### 캔틸레버는 다르다

        내민 바닥판에서는 윤하중이 지지점에서 $X$ 만큼 떨어져 실린다. 분포폭은
        $E = 0.8X + 1.14$ 로 **$X$ 와 함께 넓어진다**(식 $(4.6\text{-}4)$).

        $$
        M = \frac{P}{E} X = \frac{P X}{0.8 X + 1.14}
        $$

        분자와 분모가 함께 커지므로 모멘트가 $X$ 에 비례하지 않는다. 내밀수록
        불리하지만, 생각만큼은 아니다.

        **아래 코드가 하는 일** — 캔틸레버 길이에 따른 활하중·고정하중 모멘트를
        견준다.
        """),
        code("""
        xs = np.linspace(0.3, 2.5, 45)
        w_dc = 24.5 * BASE["thickness"] / 1000 + 22.5 * BASE["pavement"] / 1000
        m_live_c = [cantilever_live_load_moment(x=x) for x in xs]
        m_dead_c = [abs(dead_load_moment(w=w_dc, span=x, kind="캔틸레버판")) for x in xs]

        fig, ax = plt.subplots(figsize=(6.6, 4.2))
        ax.plot(xs, m_live_c, color=C_LIVE, lw=2, label="활하중 (식 4.6-4)")
        ax.plot(xs, [WHEEL_LOAD * x / 1.14 for x in xs], color=C_LIVE, lw=1,
                ls=":", label="분포폭이 안 넓어진다면")
        ax.plot(xs, m_dead_c, color=C_DEAD, lw=2, label="고정하중 (wX²/2)")
        ax.set_xlabel("지지점에서 하중점까지의 거리 X (m)")
        ax.set_ylabel("휨모멘트 (kN·m/m)")
        ax.set_title("캔틸레버 — 분포폭이 함께 넓어진다")
        ax.legend(fontsize=9)
        """),

        md(r"""
        ## 4. 두께의 두 얼굴

        학생들이 가장 자주 하는 실수가 여기 있다. **"모자라니 두껍게 하자."**

        두께를 키우면 유효깊이 $d$ 가 커져 강도가 오른다. 그런데 동시에
        **자중도 커진다.** $M_{dead} \propto t$ 이고 $M_{Rd} \propto d \approx t$
        이므로 둘 다 1차로 늘어난다. 어느 쪽이 이길까?

        **아래 코드가 하는 일** — 두께를 200 ~ 400 mm 로 바꾸며 설계휨모멘트와
        설계휨강도를 함께 그린다.
        """),
        code("""
        ts = np.linspace(200, 400, 81)
        rows = [design_deck(**{**BASE, "thickness": t}) for t in ts]

        fig, (ax, bx) = plt.subplots(1, 2, figsize=(11, 4.2))

        ax.plot(ts, [r.m_ed for r in rows], color="k", lw=2, label="설계 M$_{Ed}$")
        ax.plot(ts, [r.m_rd for r in rows], color=C_CAP, lw=2, label="설계 M$_{Rd}$ (D16@150)")
        ax.plot(ts, [r.m_dead for r in rows], color=C_DEAD, lw=1.6, ls="--", label="고정하중 몫")
        ax.axvline(MIN_THICKNESS_RC, color=C_K14, ls=":", lw=1.4)
        ax.text(MIN_THICKNESS_RC + 4, ax.get_ylim()[1] * 0.05, "최소 220 mm",
                color=C_K14, fontsize=9)
        ax.set_xlabel("바닥판 두께 t (mm)")
        ax.set_ylabel("휨모멘트 (kN·m/m)")
        ax.set_title("두께를 키우면")
        ax.legend(fontsize=9)

        margin = [r.m_rd - r.m_ed for r in rows]
        bx.plot(ts, margin, color=C_CAP, lw=2)
        bx.axhline(0, color="k", lw=0.9)
        bx.set_xlabel("바닥판 두께 t (mm)")
        bx.set_ylabel("M$_{Rd}$ - M$_{Ed}$ (kN·m/m)")
        bx.set_title("여유는 계속 늘지만 기울기가 완만해진다")
        """),

        md(r"""
        강도가 이긴다 — 두껍게 하면 여유가 는다. 그런데 **얼마나** 이기는지가
        보를 다룰 때(L3)와 사뭇 다르다.

        **아래 코드가 하는 일** — 두께 10 % 를 올렸을 때와 철근량을 10 % 더
        넣었을 때의 여유 증가를 견주고, 두께가 데려온 자중이 그 이득에서
        얼마를 도로 가져가는지 계산한다.
        """),
        code("""
        b0 = design_deck(**BASE)
        thicker = design_deck(**{**BASE, "thickness": BASE["thickness"] * 1.1})
        more_bar = design_deck(**{**BASE, "bar_spacing": BASE["bar_spacing"] / 1.1})

        for label, r in (("기준", b0), ("두께 +10 %", thicker), ("철근량 +10 %", more_bar)):
            gain = (r.m_rd - r.m_ed) - (b0.m_rd - b0.m_ed)
            print(f"{label:>13}   M_Rd {r.m_rd:6.2f}   M_Ed {r.m_ed:6.2f}   "
                  f"여유 {r.m_rd - r.m_ed:6.2f}  ({gain:+5.2f})")

        print()
        d_cap = thicker.m_rd - b0.m_rd
        d_dem = thicker.m_ed - b0.m_ed
        print(f"두께 +10 % 를 뜯어보면")
        print(f"   강도가 {d_cap:+.2f}, 하중이 {d_dem:+.2f} 만큼 늘어")
        print(f"   자중이 이득의 {d_dem / d_cap * 100:.0f} % 만 가져갔다.")
        """),

        md(r"""
        **자중이 가져간 몫은 4 % 뿐이다.** 두께를 10 % 키우면 강도가
        11.58 kN·m/m 오르는데 하중은 0.46 kN·m/m 밖에 늘지 않는다.

        보에서라면 이렇게 되지 않는다. 보는 자중이 하중의 큰 몫을 차지하므로
        단면을 키운 이득을 자중이 상당히 잠식한다. **바닥판은 §2 에서 봤듯이
        활하중이 80 % 를 넘게 지배하는 부재**라, 자중이 늘어도 전체 하중은 거의
        움직이지 않는다.

        그래서 바닥판에서는 두께가 **가장 잘 듣는 수단**이다. 같은 10 % 로
        철근량을 늘리는 것보다 1.4 배 효과가 크다.

        > **설계의 의도** — 그럼에도 기준이 두께를 220 mm 로 묶어 두고 더
        > 키우라고 하지 않는 것은, 두께가 강도만의 문제가 아니기 때문이다.
        > 두꺼운 바닥판은 상부구조 전체 자중을 키워 거더와 하부구조에 전가되고,
        > 형하공간을 잡아먹는다. **바닥판에서 싼 것이 다리 전체에서는 비싸다.**

        ## 5. 피복두께 — 내구성과 유효깊이의 맞교환

        피복은 순수한 손해처럼 보인다. 두께는 그대로인데 $d$ 만 깎이기
        때문이다. 그런데 기준은 해안 교량에서 피복을 80 mm 까지 요구한다.

        $$
        t_{c,nom} = \underbrace{\max\{d_b;\ t_{c,min,dur} + \Delta t_{c,dur,\gamma};\ 10\}}_{\text{최소피복}}
        + \underbrace{\Delta t_{c,dev}}_{10\ \text{mm}}
        $$

        **아래 코드가 하는 일** — 노출등급별 피복과 그로 인한 강도 손실을 본다.
        """),
        code("""
        print(f"{'노출등급':>8}  {'t_c,min':>8}  {'t_c,nom':>8}  {'d':>7}  {'M_Rd':>8}  {'손실':>7}")
        ref = design_deck(**{**BASE, "exposure": "E0"})
        for cls in ("E0", "EC1", "EC2", "EC4", "ED1", "ED2", "ED3",
                    "ES1", "ES2", "ES3"):
            t_min, t_nom = nominal_cover(exposure=cls, bar_diameter=BASE["bar_diameter"])
            r = design_deck(**{**BASE, "exposure": cls})
            loss = (r.m_rd / ref.m_rd - 1) * 100
            print(f"{cls:>8}  {t_min:6.0f}    {t_nom:6.0f}    {r.d:5.0f}  "
                  f"{r.m_rd:7.2f}  {loss:+6.1f} %")
        """),

        md(r"""
        해안 최악 등급(ES3)에서 강도가 20 % 넘게 깎인다. 그런데도 기준이
        그 피복을 요구하는 이유는 분명하다 — **강도는 철근을 더 넣어 되찾을 수
        있지만, 염해로 녹슨 철근은 되돌릴 수 없다.**

        > **설계의 의도** — 피복두께 규정은 강도 규정이 아니라 **수명 규정**이다.
        > 그래서 극한한계상태가 아니라 내구성(4.4)에 들어 있다. 설계자가 할 일은
        > 피복을 아끼는 것이 아니라, 깎인 $d$ 를 두께나 철근으로 메우는 것이다.

        노출 바닥판(방수·표면처리 없음)은 마모 대비로 10 mm 를 더 얹는다
        (4.4.4.2(12)). 아래 코드가 그 차이를 확인한다.
        """),
        code("""
        plain = design_deck(**BASE)
        exposed = design_deck(**{**BASE, "exposed_deck": True})

        print(f"방수 있음   피복 {plain.cover:.0f} mm,  d {plain.d:.0f} mm,  "
              f"M_Rd {plain.m_rd:.2f} kN·m/m")
        print(f"노출 바닥판  피복 {exposed.cover:.0f} mm,  d {exposed.d:.0f} mm,  "
              f"M_Rd {exposed.m_rd:.2f} kN·m/m")
        print(f"차이 {(exposed.m_rd / plain.m_rd - 1) * 100:+.1f} %")
        """),

        md(r"""
        ## 6. 휨 설계 — 1 m 폭 띠판

        여기서부터는 익숙한 단철근 직사각형 보 계산이다. 폭 1,000 mm, 높이
        $t$, 유효깊이 $d$ 의 단면을 푼다.

        KDS 24 이므로 재료계수가 재료에 이미 들어 있다.

        $$
        M_{Rd} = A_s f_{yd} \left( d - \beta_{eq} c \right),
        \qquad c = \frac{A_s f_{yd}}{\alpha_{eq} f_{cd} b}
        $$

        **아래 코드가 하는 일** — 기준 단면의 휨 설계를 손으로 따라간다.
        """),
        code("""
        r = design_deck(**BASE)
        fck, fy = 27.0, 400.0
        f_cd = design_compressive_strength(fck=fck)
        f_yd = design_yield_strength(fy=fy)
        alpha, beta = equivalent_block(fck=fck)

        print(f"f_cd = {f_cd:.2f} MPa   (= 0.65 × 0.85 × {fck:.0f})")
        print(f"f_yd = {f_yd:.1f} MPa   (= 0.90 × {fy:.0f})")
        print(f"등가블록 계수  α = {alpha:.3f},  β = {beta:.3f}")
        print()

        c = r.as_provided * f_yd / (alpha * f_cd * 1000.0)
        arm = r.d - beta * c
        print(f"배치 철근 As   {r.as_provided:.0f} mm²/m  (D16@150)")
        print(f"중립축 깊이 c  {c:.1f} mm      (c/d = {c / r.d:.3f})")
        print(f"팔길이         {arm:.1f} mm")
        print(f"M_Rd = As·f_yd·(d - βc) = {r.as_provided * f_yd * arm / 1e6:.2f} kN·m/m")
        print(f"                          모듈 값 {r.m_rd:.2f} kN·m/m")
        """),

        md(r"""
        ### KDS 14 로 풀면 얼마나 다른가

        하중은 어느 쪽이든 KDS 24 12 21 로 구한다 — 교량이니 KL-510 말고는
        쓸 것이 없다. 갈리는 것은 **단면 저항 쪽뿐**이다.

        **아래 코드가 하는 일** — 같은 $M_{Ed}$ 에 필요한 철근량을 두 기준으로
        구해 견준다.
        """),
        code(L14_DEF),

        code("""
        print(f"{'거더 간격':>9}  {'M_Ed':>8}  {'KDS 24':>9}  {'KDS 14':>9}  {'차이':>7}")
        for s in (2.0, 2.5, 3.0, 3.5, 4.0):
            r = design_deck(**{**BASE, "girder_spacing": s})
            as24 = r.as_required
            as14 = required_steel_kds14(m_u=r.m_ed * 1e6, d=r.d)
            print(f"{s:7.1f} m  {r.m_ed:6.2f}  {as24:7.0f} mm²  {as14:7.0f} mm²  "
                  f"{(as24 / as14 - 1) * 100:+5.1f} %")

        print()
        print("KDS 24 쪽이 철근을 조금 덜 요구한다. 휨은 철근이 지배하는데")
        print("φ_s = 0.90 이 단면 φ = 0.85 보다 덜 깎기 때문이다 (L2 와 같은 이유).")
        """),

        md(r"""
        ## 7. 균열이 설계를 지배하는 순간

        여기까지는 강도 이야기였다. 그런데 바닥판에서 **실제로 설계를 결정하는
        것은 균열인 경우가 많다.**

        기준은 두 가지 길을 준다. 균열폭을 직접 계산하거나(4.2.3.4), 표 4.2-4·
        4.2-5 로 **철근 지름이나 간격 중 하나를 제한**하는 것으로 갈음하거나
        (4.2.3.3). 바닥판에서는 뒤쪽이 실용적이다.

        표는 사용하중조합-Ⅰ 의 **철근 응력**을 입력으로 받는다. 철근이 적으면
        응력이 높아지고, 그러면 허용 간격이 급격히 줄어든다.

        **아래 코드가 하는 일** — 철근 간격을 바꿔 가며 강도 여유와 균열 제어
        한계를 함께 그린다.
        """),
        code("""
        spacings = np.linspace(100, 300, 101)
        rows = [design_deck(**{**BASE, "bar_spacing": s}) for s in spacings]

        def crossing(xs, gap):
            \"\"\"gap 의 부호가 바뀌는 x 를 선형보간으로 찾는다.\"\"\"
            for x0, x1, g0, g1 in zip(xs, xs[1:], gap, gap[1:]):
                if g0 >= 0 >= g1:
                    return x0 + (x1 - x0) * g0 / (g0 - g1)
            return None

        s_strength = crossing(spacings, [r.m_rd - r.m_ed for r in rows])
        s_crack = crossing(spacings, [r.crack_spacing_limit - s
                                      for s, r in zip(spacings, rows)])

        fig, (ax, bx) = plt.subplots(1, 2, figsize=(11, 4.2))

        ax.plot(spacings, [r.m_rd for r in rows], color=C_CAP, lw=2, label="M$_{Rd}$")
        ax.plot(spacings, [r.m_ed for r in rows], color="k", lw=2, ls="--", label="M$_{Ed}$")
        ax.axvline(s_strength, color=C_CAP, ls=":", lw=1.4)
        ax.text(s_strength - 5, 0.06, f"강도 한계 {s_strength:.0f} mm", rotation=90,
                transform=ax.get_xaxis_transform(), ha="right", va="bottom",
                fontsize=9, color=C_CAP)
        ax.set_xlabel("주철근 간격 (mm)")
        ax.set_ylabel("휨모멘트 (kN·m/m)")
        ax.set_title("강도 — 간격이 넓어지면 준다")
        ax.legend(fontsize=9, loc="upper right")

        limits = [r.crack_spacing_limit for r in rows]
        bx.plot(spacings, spacings, color="k", lw=2, ls="--", label="배치 간격")
        bx.plot(spacings, limits, color=C_LIVE, lw=2, label="표 4.2-5 허용 간격")
        bx.fill_between(spacings, spacings, limits,
                        where=[s > lim for s, lim in zip(spacings, limits)],
                        color=C_K14, alpha=0.16)
        bx.axvline(s_crack, color=C_LIVE, ls=":", lw=1.4)
        bx.text(s_crack - 5, 0.06, f"균열 한계 {s_crack:.0f} mm", rotation=90,
                transform=bx.get_xaxis_transform(), ha="right", va="bottom",
                fontsize=9, color=C_LIVE)
        bx.set_xlabel("주철근 간격 (mm)")
        bx.set_ylabel("간격 (mm)")
        bx.set_title("사용성 — 붉은 구간이 균열 제어 불만족")
        bx.legend(fontsize=9, loc="lower left")

        print(f"강도가 걸리는 간격   {s_strength:.0f} mm")
        print(f"균열이 걸리는 간격   {s_crack:.0f} mm")
        print()
        if s_crack < s_strength:
            print("균열이 먼저 걸린다 — 이 조건에서는 사용한계상태가 설계를 지배한다.")
        else:
            print("강도가 먼저 걸린다 — 이 조건에서는 극한한계상태가 설계를 지배한다.")
        """),

        md(r"""
        두 한계가 216 mm 와 225 mm 로 **4 % 밖에 떨어져 있지 않다.** 조건이
        조금만 바뀌면 순서가 뒤집힌다는 뜻이다.

        무엇이 뒤집는가? 표 4.2-5(간격)와 표 4.2-4(지름)는 모두 철근 응력을
        입력으로 받지만, **지름 쪽이 훨씬 가혹하다.** 철근 응력 240 MPa 에서
        허용 간격은 200 mm 인데 허용 지름은 16 mm 다.

        **아래 코드가 하는 일** — 철근 지름을 바꿔 가며 강도 한계와 두 가지
        균열 한계를 함께 찾는다. 같은 철근량이라도 굵게 띄엄띄엄 넣으면 어떻게
        되는지 본다.
        """),
        code("""
        def limiting_spacings(**kwargs):
            \"\"\"강도·균열(간격)·균열(지름) 세 한계가 걸리는 철근 간격을 찾는다.\"\"\"
            grid = np.linspace(100, 300, 201)
            rows = [design_deck(**{**BASE, **kwargs, "bar_spacing": s}) for s in grid]
            dia = kwargs.get("bar_diameter", BASE["bar_diameter"])

            def cross(gap):
                for x0, x1, g0, g1 in zip(grid, grid[1:], gap, gap[1:]):
                    if g0 >= 0 >= g1:
                        return x0 + (x1 - x0) * g0 / (g0 - g1)
                return float("nan")

            return (
                cross([r.m_rd - r.m_ed for r in rows]),
                cross([r.crack_spacing_limit - s for s, r in zip(grid, rows)]),
                cross([(max_bar_diameter(f_s=r.service_stress)
                        if r.service_stress <= 360 else 0.0) - dia for r in rows]),
            )

        print(f"{'지름':>5}  {'강도':>8}  {'균열(간격)':>10}  {'균열(지름)':>10}   지배")
        for dia in (13, 16, 19, 22, 25):
            st, csp, cdi = limiting_spacings(bar_diameter=float(dia))
            found = {"강도": st, "균열(간격)": csp, "균열(지름)": cdi}
            found = {k: v for k, v in found.items() if v == v}
            who = min(found, key=found.get) if found else "-"
            fmt = lambda v: f"{v:8.0f}" if v == v else "   300 밖"
            print(f"  D{dia:<3} {fmt(st)}  {fmt(csp):>10}  {fmt(cdi):>10}   {who}")
        """),

        md(r"""
        D19 부터 순서가 뒤집힌다. 굵은 철근은 강도 면에서는 여유로워
        300 mm 까지 벌려도 견디지만, **균열이 그것을 허락하지 않는다.**

        이것이 표 4.2-4·4.2-5 가 하려는 말이다. 균열폭은 철근량이 아니라
        **철근의 배치**가 정한다. 균열 간격 식 $(4.2\text{-}7\text{a})$ 를 다시
        보면 이유가 분명하다.

        $$
        l_{r,max} = 3.4 c_c + \frac{0.425 k_1 k_2 d_b}{\rho_e}
        $$

        철근 지름 $d_b$ 가 **분자에 직접** 들어간다. 같은 철근량이라도 굵은 철근
        몇 개는 균열을 드문드문 만들고, 드문 균열은 하나하나가 넓다.

        > **설계의 의도** — "가늘게 촘촘히"는 미관 문제가 아니다. 넓은 균열은
        > 염화물의 고속도로가 되고, 바닥판은 제설염을 직접 맞는 부재다.
        > 4 % 밖에 안 되는 두 한계의 간격은, 기준이 강도와 내구성을 **비슷한
        > 수준으로 조여 놓았다**는 뜻이기도 하다.
        """),

        md(r"""
        > **설계의 의도** — 표 4.2-5 는 "철근을 굵게 띄엄띄엄 넣지 말고, 가늘게
        > 촘촘히 넣으라"는 말이다. 같은 철근량이라도 배치가 다르면 균열폭이
        > 달라지기 때문이다. 균열 간격 식 $(4.2\text{-}7\text{a})$ 에
        > $3.4c_c + 0.425 k_1 k_2 d_b / \rho_e$ 처럼 **철근 지름이 직접 들어가는**
        > 이유가 그것이다.

        ## 8. 배력철근과 상세

        주철근만으로는 부족하다. 윤하중은 한 점에 실리는데 바닥판은 폭을 가진
        판이므로, 그 집중을 옆으로 퍼뜨릴 철근이 필요하다.

        $$
        \text{배력철근} = \min\left(\frac{120}{\sqrt{L}},\ 67\right)\% \times \text{주철근량}
        $$

        지간이 짧을수록 비율이 커진다 — 퍼뜨릴 몫이 크기 때문이다. 그래서
        상한 67 % 가 걸린다.

        **아래 코드가 하는 일** — 지간별 배력철근 비율과 실제 배근을 구한다.
        """),
        code("""
        r = design_deck(**BASE)
        ratio = distribution_steel_ratio(span=r.span)
        as_dist = ratio * r.as_provided

        print(f"지간 {r.span:.2f} m  →  배력철근 비율 {ratio * 100:.1f} %")
        print(f"주철근  {r.as_provided:.0f} mm²/m  (D16@150)")
        print(f"배력철근 {as_dist:.0f} mm²/m 이상 필요")
        print()
        for dia in (10, 13, 16):
            need = bar_area(diameter=dia) * 1000 / as_dist
            print(f"  D{dia:<2}  →  간격 {need:.0f} mm 이하  "
                  f"(상한 300 mm 이므로 {'가능' if need >= 100 else '너무 촘촘'})")

        print()
        print(f"{'지간':>6}  {'비율':>7}")
        for L in (1.5, 2.0, 2.5, 3.2, 4.0, 5.0):
            print(f"{L:5.1f}m  {distribution_steel_ratio(span=L) * 100:5.1f} %")
        """),

        md(r"""
        ### 상세 규정이 실제로 설계를 좁힌다

        | 규정 | 값 | 조문 |
        |---|---|---|
        | 최소 두께 (RC) | 220 mm | 4.6.5.1(5) |
        | 최소 두께 (PSC) | 200 mm | 4.6.5.1(5) |
        | 경험적 설계법 최소 두께 | 240 mm | 4.6.5.2(3)⑦ |
        | 철근 중심간격 | 100 ~ 300 mm | 4.6.5.2(5)③ |
        | 하부 주철근 간격 | 바닥판 두께 이하 | 4.6.5.2(5)③ |
        | 철근 종류 | SD400 이상 | 4.6.5.2(5)① |
        | 경험적 설계법 층별 철근비 | 0.3 % 이상 | 4.6.5.2(4)② |

        **아래 코드가 하는 일** — 경험적 설계법이 요구하는 철근량과, 해석으로
        구한 철근량을 견준다.
        """),
        code("""
        r = design_deck(**BASE)
        empirical = 0.003 * 1000 * r.thickness

        print(f"경험적 설계법  0.3 % × 1000 × {r.thickness:.0f} = {empirical:.0f} mm²/m (층마다)")
        print(f"해석으로 구한 필요량                        {r.as_required:.0f} mm²/m")
        print(f"배치량 (D16@150)                          {r.as_provided:.0f} mm²/m")
        print()
        if empirical > r.as_required:
            print("경험적 설계법이 더 많은 철근을 요구한다 — 해석 없이 쓰는 대가다.")
        else:
            print("이 조건에서는 해석 쪽이 더 많이 요구한다.")
        """),

        md(r"""
        ## 9. 무엇을 바꿀 것인가 — 여섯 변수의 민감도

        L3 에서 보와 기둥을 두고 했던 질문을 바닥판에도 던진다. 강도가
        모자랄 때 무엇을 올릴 것인가?

        바닥판에는 손댈 수 있는 변수가 여섯이다. 그중 **거더 간격은 설계자의
        것이 아니고**, 노출등급은 환경이 정한다. 실제로 고를 수 있는 것은
        두께·철근량·포장 두께뿐이다.

        비교를 공정하게 하려면 **같은 것을 10 % 늘려야** 한다. 철근 지름을
        10 % 키우면 단면적은 $1.1^2 = 1.21$ 배가 되므로, 지름이 아니라
        **철근량**을 10 % 늘리는 것으로 맞춘다.

        **아래 코드가 하는 일** — 각 변수를 10 % 씩 유리한 방향으로 바꿔
        여유($M_{Rd} - M_{Ed}$)가 얼마나 느는지 잰다.
        """),
        code("""
        b0 = design_deck(**BASE)
        margin0 = b0.m_rd - b0.m_ed

        cases = [
            ("두께 +10 %", {"thickness": BASE["thickness"] * 1.1}),
            ("철근량 +10 %", {"bar_spacing": BASE["bar_spacing"] / 1.1}),
            ("거더 간격 -10 %", {"girder_spacing": BASE["girder_spacing"] * 0.9}),
            ("포장 -10 %", {"pavement": BASE["pavement"] * 0.9}),
        ]

        labels, gains = [], []
        for label, change in cases:
            r = design_deck(**{**BASE, **change})
            gain = (r.m_rd - r.m_ed) - margin0
            labels.append(label)
            gains.append(gain)
            print(f"{label:>16}   여유 {r.m_rd - r.m_ed:6.2f}  ({gain:+5.2f} kN·m/m)")

        unfair = design_deck(**{**BASE, "bar_diameter": BASE["bar_diameter"] * 1.1})
        print()
        print(f"참고: 철근 '지름' 을 10 % 키우면 철근량이 "
              f"{unfair.as_provided / b0.as_provided:.2f} 배가 되어")
        print(f"      여유가 {unfair.m_rd - unfair.m_ed - margin0:+.2f} 까지 오른다. "
              f"공정한 비교가 아니다.")

        fig, ax = plt.subplots(figsize=(7.6, 3.6))
        ax.barh(labels, gains, color=C_CAP)
        ax.axvline(0, color="k", lw=0.9)
        ax.set_xlabel("여유 M$_{Rd}$ - M$_{Ed}$ 의 증가 (kN·m/m)")
        ax.set_title("같은 10 % 를 어디에 쓸 것인가")
        ax.invert_yaxis()
        for y, g in enumerate(gains):
            ax.text(g + 0.25, y, f"{g:+.2f}", va="center", fontsize=9)
        ax.set_xlim(0, max(gains) * 1.3)
        """),

        md(r"""
        순서가 L3 의 보와 다르다. 보에서는 철근이 가장 잘 들었지만, **바닥판에서는
        두께가 이긴다.** §4 에서 본 이유 그대로다 — 바닥판은 활하중이 지배하는
        부재라 두께가 데려오는 자중의 대가가 거의 없다.

        거더 간격은 세 번째다. 절대값으로는 두께보다 작지만, **성격이 다르다.**
        철근이나 두께는 바닥판 안에서 끝나는 결정이지만 거더 간격은 상부구조
        전체를 바꾼다. 거더를 한 본 더 넣으면 간격이 10 % 가 아니라 20~30 %
        줄고, 대신 거더 값과 하부구조가 함께 늘어난다.

        포장은 사실상 영향이 없다(+0.17). 포장을 얇게 해 바닥판을 구하려는
        시도는 의미가 없다는 뜻이다.

        > **설계의 의도** — 여기서 얻을 교훈은 "두께를 키우라"가 아니다.
        > **같은 부재라도 하중 구성이 다르면 효율의 순서가 뒤집힌다**는 것이다.
        > L3 의 결론을 바닥판에 그대로 옮기면 틀린다.

        ## 정리

        1. **바닥판은 판이지 보가 아니다.** 그래서 트럭을 굴리지 않고 실물
           실험으로 보정한 근사식을 쓴다. 그 식은 이미 2방향 거동과 하중 퍼짐을
           삼키고 있고, 그래서 전단 검토를 면제해 준다.
        2. **끝까지 활하중이 지배한다.** 어떤 거더 간격에서도 활하중이 80 % 를
           넘는다. 피로와 내구성이 바닥판 설계의 본질인 이유다.
        3. **바닥판에서는 두께가 가장 잘 듣는다.** 활하중이 지배하는 부재라
           두께가 데려오는 자중의 대가가 이득의 4 % 뿐이다. 보를 다루던
           직관(L3)을 그대로 옮기면 틀린다.
        4. **피복은 손해가 아니라 수명이다.** ES3 에서 강도가 20 % 넘게
           깎이지만, 녹슨 철근은 되돌릴 수 없다.
        5. **균열이 강도보다 먼저 걸리는 구간이 있다.** 표 4.2-5 는 "가늘게
           촘촘히"를 요구한다.
        6. **거더 간격은 바닥판 설계자의 것이 아니다.** 효과는 세 번째지만
           성격이 다르다 — 거더를 한 본 더 넣는 결정은 상부구조 전체를 바꾼다.

        ## 생각해 볼 문제

        1. 식 $(4.6\text{-}1)$ 의 등가 분포폭이 지간과 거의 무관하게 2.4 m 로
           나왔다. 만약 인접 차로의 윤하중이 1.8 m 옆에 함께 실린다면 이 폭은
           여전히 타당한가? 기준이 다차로 재하계수를 바닥판에 쓰지 않는 이유를
           설명해 보라.
        2. 캔틸레버 분포폭 $E = 0.8X + 1.14$ 에서 $X \to 0$ 이면 $E \to 1.14$ m
           다. 지지점 바로 위에 윤하중이 실려도 1.14 m 에 퍼진다는 뜻인데,
           물리적으로 무엇을 반영한 값이겠는가?
        3. 노출등급 ES3 인 해상 교량 바닥판을 설계한다. 피복 80 mm 를 확보하면서
           $d$ 를 잃지 않으려면 두께를 얼마나 키워야 하는가? 그때 자중 증가로
           잃는 것과 견주어 이득이 있는가? 직접 계산해 보라.
        4. 경험적 설계법(0.3 % × 4층)과 해석 설계법 중 어느 쪽이 철근을 더
           요구하는지는 조건에 따라 갈린다. 어떤 조건에서 경험적 설계법이
           불리해지는가?
        5. 바닥판의 피로한계상태 검증은 면제된다(4.6.5.1(3)). 그런데 하중의
           80 % 가 활하중이다. 이 면제가 정당화되려면 무엇이 전제되어야 하는가?
        """),
    ], directory=LECTURES)


CANTILEVER_SETUP = r'''
from concreteproperties_kds.kds import stress_block_parameters
from concreteproperties_kds.kds24 import (
    COMBINATIONS_BY_NAME,
    WHEEL_LOAD,
    bar_area,
    cantilever_live_load_moment,
    cantilever_wheel_width,
    dead_load_moment,
    design_compressive_strength,
    design_yield_strength,
    equivalent_block,
    impact_factor,
    live_load_moment,
    max_bar_spacing,
    minimum_flexural_steel,
    nominal_cover,
    provided_steel_area,
    required_steel_area,
)

# 기준 조건 — 예제 17 의 교량과 같다
CANTILEVER = 1.30     # 캔틸레버 길이 (m)        ← 바꿔 보라
HAUNCH = 280.0        # 고정단 두께 (mm, 헌치)   ← 바꿔 보라
GIRDER_SPACING = 2.5  # 내측 비교용 거더 간격 (m)
THICKNESS = 240.0     # 내측 바닥판 두께 (mm)
EXPOSURE = "ED1"      # 제설염에 노출               ← 바꿔 보라
PAVEMENT = 80.0       # 포장 두께 (mm)
BARRIER_LOAD = 8.0    # 방호벽 자중 (kN/m)         ← 바꿔 보라
BARRIER_ARM = 0.25    # 방호벽 도심의 끝단 이격 (m)
EDGE_TO_WHEEL = 0.30  # 차도 끝에서 최외측 차륜 (m, 4.6.2.3(3)⑤)
FCK, FY = 27.0, 400.0
GAMMA_C, GAMMA_P = 24.5, 22.5

C_DEAD = "#5b6472"
C_LIVE = "#1f6feb"
C_CAP = "#1f7a4d"
C_K14 = "#b3372c"
C_LOAD = "#b3372c"
C_MUTED = "#5b6472"


def cantilever_moments(x_cant=CANTILEVER, haunch=HAUNCH, barrier=BARRIER_LOAD):
    """캔틸레버 고정단의 하중별 휨모멘트를 돌려준다 (kN·m/m)."""
    x_wheel = x_cant - EDGE_TO_WHEEL
    m_dc = abs(dead_load_moment(w=GAMMA_C * haunch / 1000.0, span=x_cant,
                                kind="캔틸레버판"))
    m_dc += barrier * (x_cant - BARRIER_ARM)
    m_dw = abs(dead_load_moment(w=GAMMA_P * PAVEMENT / 1000.0,
                                span=x_cant - 0.5, kind="캔틸레버판"))
    m_ll = cantilever_live_load_moment(x=x_wheel)
    m_im = m_ll * (impact_factor() - 1.0)
    return {"DC": m_dc, "DW": m_dw, "LL": m_ll, "IM": m_im}


print(f"윤하중 P = {WHEEL_LOAD:.0f} kN,  캔틸레버 {CANTILEVER:.2f} m")
print(f"최외측 차륜 위치 X = {CANTILEVER - EDGE_TO_WHEEL:.2f} m (고정단에서)")
'''


def nb_l5_deck_cantilever():
    """강의 L5 - 바닥판 외측슬래브(캔틸레버)는 왜 더 두꺼운가."""
    return write("L5_바닥판설계_외측슬래브", [
        md(r"""
        # L5 · 바닥판 (외측슬래브) — 왜 캔틸레버가 단면을 정하는가

        ## 이 시간에 답할 질문

        [L4](L4_바닥판설계_내측슬래브.ipynb) 에서 내측슬래브를 풀었다. 같은
        다리의 **바깥으로 내민 부분**을 풀면 설계휨모멘트가 **2.1 배**가 된다.
        철근도 D16@150 에서 D19@125 로 올라간다.

        왜 이렇게 커지는가? 흔한 설명은 두 가지다.

        > "방호벽 자중 때문이다."
        > "윤하중이 좁은 폭에만 퍼지기 때문이다."

        **둘 다 틀렸다.** 이 시간에는 계산으로 그것을 확인하고 진짜 원인을
        찾는다.

        1. 캔틸레버의 등가 분포폭은 내측보다 넓은가, 좁은가?
        2. 방호벽은 증가분의 몇 %를 설명하는가?
        3. 그렇다면 무엇이 캔틸레버를 지배하는가?
        4. 고정단을 두껍게(헌치) 하는 것은 얼마나 효과가 있는가?
        5. 실제 설계에서 캔틸레버 상부철근을 정하는 것은 정말 이 계산인가?

        ## 근거 조문

        | 내용 | 조문 |
        |---|---|
        | 최외측 차륜 위치 (차도 끝에서 300 mm) | KDS 24 10 11 4.6.2.3(3)⑤ |
        | 캔틸레버 등가 분포폭 식 $(4.6\text{-}4)$ | KDS 24 10 11 4.6.2.5 |
        | 내측 등가 분포폭 식 $(4.6\text{-}2)$ | KDS 24 10 11 4.6.2.4 |
        | 고정하중 휨모멘트 표 4.6-2 (캔틸레버 $-wl^2/2$) | KDS 24 10 11 4.6.2.7 |
        | 충격 25 % | KDS 24 12 21 표 4.4-1 |
        | 하중조합 극한Ⅰ | KDS 24 12 11 표 4.1-1 |
        | 피복두께 식 $(4.4\text{-}1)$, 표 4.4-4 | KDS 24 14 21 4.4.4 |
        | 차량 충돌하중 (이 편의 범위 밖) | KDS 24 90 11 |
        """, EXPLORER_NOTE),

        md("""
        ## 0. 준비

        **아래 코드가 하는 일** — 한글 글꼴을 등록하고 그림 색을 정한다.
        """),
        code(SETUP),
        md(r"""
        **아래 코드가 하는 일** — 이 편에서 따라갈 설계 흐름을 순서도로
        그린다. 각 단계 옆에 근거 조문을 적었다.
        """),
        code(FLOWCHART + '''
design_flowchart(
"바닥판 외측슬래브(캔틸레버) 설계 흐름",
[
    ("캔틸레버 길이·최외측 차륜 위치", "24 10 11 4.6.2.3(3)⑤"),
    ("고정단 두께(헌치)·피복 결정", "24 14 21 4.6.5.1, 4.4.4"),
    ("등가 분포폭 E = 0.8X + 1.14", "24 10 11 4.6.2.5"),
    ("활하중 휨모멘트 M = P·X/E", "24 10 11 4.6.2.5"),
    ("자중·방호벽 고정하중 (−wl²/2)", "24 10 11 4.6.2.7"),
    ("충격 25 % 와 하중조합 극한Ⅰ", "24 12 21 표 4.4-1 · 24 12 11 표 4.1-1"),
    ("상부철근 휨 설계", "24 14 21 4.1.1"),
    ("차량 충돌하중 검토 (극단상황)", "24 90 11"),
],
)
        '''),

        md(r"""
        **아래 코드가 하는 일** — 캔틸레버의 하중별 휨모멘트를 구하는 함수를
        정의한다. 예제 17 과 같은 교량(캔틸레버 1.3 m, 고정단 280 mm)이다.
        """),
        code(CANTILEVER_SETUP),

        md(r"""
        ## 1. 분포폭 — 캔틸레버가 정말 좁은가

        기준은 내측과 캔틸레버에 **다른 식**을 준다.

        $$
        \text{내측: } E = 1.2 + 0.06L \le 2.1 \,\text{m}
        \qquad
        \text{캔틸레버: } E = 0.8X + 1.14 \,\text{m}
        $$

        $L$ 은 거더 간격, $X$ 는 고정단에서 윤하중까지의 거리다.
        직관은 "캔틸레버는 한쪽만 지지되니 힘이 퍼질 데가 없다 → 좁다"고
        말한다. 넣어 보자.

        **아래 코드가 하는 일** — 두 식을 나란히 계산한다.
        """),
        code(r'''
        x_wheel = CANTILEVER - EDGE_TO_WHEEL
        e_can = cantilever_wheel_width(x=x_wheel)
        e_int = min(1.2 + 0.06 * GIRDER_SPACING, 2.1)

        print(f"내측    L = {GIRDER_SPACING:.2f} m  ->  E = {e_int:.3f} m")
        print(f"캔틸레버 X = {x_wheel:.2f} m  ->  E = {e_can:.3f} m")
        print()
        print(f"캔틸레버의 분포폭이 {e_can / e_int:.2f} 배 '넓다'.")
        print()
        print(f"{'X (m)':>7} {'캔틸레버 E':>12} | {'L (m)':>7} {'내측 E':>10}")
        print("-" * 44)
        for v in (0.5, 0.8, 1.0, 1.3, 1.6, 2.0):
            print(f"{v:7.2f} {cantilever_wheel_width(x=v):12.3f} | "
                  f"{v:7.2f} {min(1.2 + 0.06 * v, 2.1):10.3f}")
        '''),

        md(r"""
        **읽는 법** — 직관이 틀렸다. 캔틸레버의 분포폭이 **1.44 배 넓다.**
        게다가 $X$ 에 대한 기울기가 0.8 로, 내측의 0.06 보다 **13 배** 가파르다.

        왜 이런가? 두 식이 재는 것이 다르기 때문이다.

        - 내측의 $L$ 은 **지간**이다. 지간이 길어져도 윤하중이 퍼지는 폭은
          크게 달라지지 않는다(그래서 기울기가 완만하고 2.1 m 에서 잘린다).
        - 캔틸레버의 $X$ 는 **고정단에서 하중까지의 거리**다. 하중이 고정단에서
          멀수록 힘이 부채꼴로 퍼질 여유가 생긴다(그래서 기울기가 가파르다).

        분포폭만 보면 캔틸레버가 **유리하다.** 그런데도 모멘트는 크다.

        ## 2. 그렇다면 무엇이 키우는가

        **아래 코드가 하는 일** — 활하중 휨모멘트를 두 식으로 각각 구해
        분해한다.
        """),
        code(r'''
        m_ll_int = live_load_moment(span=GIRDER_SPACING, continuous=True)
        m_ll_can = cantilever_live_load_moment(x=x_wheel)

        print("내측    식 (4.6-1)  M = (L + 0.6) P / 9.6 x 0.8")
        print(f"        = ({GIRDER_SPACING} + 0.6) x {WHEEL_LOAD:.0f} / 9.6 "
              f"x 0.8 = {m_ll_int:.2f} kN·m/m")
        print()
        print("캔틸레버 식 (4.6-4)  M = P x X / E")
        print(f"        = {WHEEL_LOAD:.0f} x {x_wheel:.2f} / {e_can:.3f} "
              f"= {m_ll_can:.2f} kN·m/m")
        print()
        print(f"활하중만으로 이미 {m_ll_can / m_ll_int:.2f} 배다.")
        print()
        # 연속 0.8 배 혜택이 없다면 내측은 얼마였을까
        m_ll_int_simple = live_load_moment(span=GIRDER_SPACING, continuous=False)
        print(f"내측이 단순판이었다면      {m_ll_int_simple:.2f} kN·m/m")
        print(f"연속판이라 0.8 배를 받아  {m_ll_int:.2f} kN·m/m")
        print(f"  -> 연속 혜택만으로 {(1 - 0.8) * 100:.0f} % 를 덜어낸다.")
        '''),

        md(r"""
        **읽는 법** — 활하중만으로 벌써 2.00 배다. 그 차이 24.7 kN·m/m 를
        갈라 보면 이렇다.

        - **연속판 0.8 배 혜택의 부재**: 6.2 (**25 %**). 캔틸레버는 한쪽만
          고정된 외팔보라 모멘트를 나눠 가질 이웃 경간이 없다.
        - **지렛대 팔과 식 자체의 차이**: 18.5 (**75 %**). 내측은 윤하중이
          지간 어디에 놓이든 $(L+0.6)/9.6$ 이라는 완만한 계수로 들어가지만,
          캔틸레버는 $P \cdot X$ 가 그대로 고정단에 걸린다.

        즉 **주된 원인은 지렛대 팔이고, 연속 혜택은 그 다음**이다.

        **아래 코드가 하는 일** — 방호벽이 정말 주범인지 확인한다. 방호벽을
        빼고 다시 계산해 본다.
        """),
        code(r'''
        base = cantilever_moments()
        no_barrier = cantilever_moments(barrier=0.0)

        m_ed = COMBINATIONS_BY_NAME["극한Ⅰ"].evaluate(loads=base)
        m_ed_nb = COMBINATIONS_BY_NAME["극한Ⅰ"].evaluate(loads=no_barrier)

        # 내측부 (L4 와 같은 조건)
        w_dc_i = GAMMA_C * THICKNESS / 1000.0
        w_dw_i = GAMMA_P * PAVEMENT / 1000.0
        loads_int = {
            "DC": abs(dead_load_moment(w=w_dc_i, span=GIRDER_SPACING,
                                       kind="연속판_지간")),
            "DW": abs(dead_load_moment(w=w_dw_i, span=GIRDER_SPACING,
                                       kind="연속판_지간")),
            "LL": m_ll_int,
            "IM": m_ll_int * (impact_factor() - 1.0),
        }
        m_ed_int = COMBINATIONS_BY_NAME["극한Ⅰ"].evaluate(loads=loads_int)

        print(f"내측부        M_Ed = {m_ed_int:7.2f} kN·m/m")
        print(f"캔틸레버      M_Ed = {m_ed:7.2f} kN·m/m"
              f"   ({m_ed / m_ed_int:.2f} 배)")
        print(f"방호벽 없다면 M_Ed = {m_ed_nb:7.2f} kN·m/m")
        print()
        grow = m_ed - m_ed_int
        by_barrier = m_ed - m_ed_nb
        print(f"증가분 {grow:.1f} kN·m/m 중")
        print(f"  방호벽이 설명하는 몫 {by_barrier:.1f} "
              f"({by_barrier / grow * 100:.0f} %)")
        print(f"  나머지               {grow - by_barrier:.1f} "
              f"({(grow - by_barrier) / grow * 100:.0f} %)")
        '''),

        md(r"""
        **읽는 법** — 방호벽이 설명하는 몫은 **15 %** 뿐이다. 나머지 85 % 는
        활하중이다. "방호벽 때문"이라는 설명은 크기를 한참 잘못 짚은 것이다.

        정리하면 캔틸레버가 커지는 이유는 이 순서다.

        1. **지렛대 팔** $P \cdot X$ 가 고정단에 그대로 걸린다 (활하중 차이의 75 %)
        2. **연속판의 0.8 배 혜택이 없다** — 외팔보에는 재분배할 이웃이 없다 (25 %)
        3. 방호벽 자중 — 전체 증가분의 15 % 로, 작지만 있다

        그리고 **분포폭은 오히려 유리하게 작용하고 있다.** 캔틸레버 식이
        1.94 m 로 퍼뜨려 주지 않았다면 모멘트는 훨씬 컸을 것이다.

        **아래 코드가 하는 일** — 세 성분의 기여를 막대로 그린다.
        """),
        code(r'''
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.3))

        # 왼쪽 — 하중 구성 비교
        names = ["내측부", "캔틸레버"]
        dc = [loads_int["DC"], base["DC"]]
        dw = [loads_int["DW"], base["DW"]]
        ll = [loads_int["LL"] + loads_int["IM"], base["LL"] + base["IM"]]

        ax1.bar(names, dc, color=C_DEAD, label="고정 DC")
        ax1.bar(names, dw, bottom=dc, color="#c9a227", label="고정 DW")
        ax1.bar(names, ll, bottom=[a + b for a, b in zip(dc, dw)],
                color=C_LIVE, label="활하중 + 충격")
        for i, (a, b, c) in enumerate(zip(dc, dw, ll)):
            ax1.text(i, a + b + c + 2, f"{a + b + c:.1f}", ha="center",
                     fontsize=9)
        ax1.set_ylabel("휨모멘트 (kN·m/m, 비계수)")
        ax1.set_title("하중 구성 - 커진 것은 활하중이다")
        ax1.legend(fontsize=9)
        ax1.grid(axis="y", alpha=0.3)

        # 오른쪽 — 분포폭
        xs = np.linspace(0.3, 2.2, 100)
        ax2.plot(xs, 0.8 * xs + 1.14, color=C_LIVE, lw=2.2,
                 label="캔틸레버 E = 0.8X + 1.14")
        ax2.plot(xs, np.minimum(1.2 + 0.06 * xs, 2.1), color=C_CAP, lw=2.2,
                 label="내측 E = 1.2 + 0.06L (<= 2.1)")
        ax2.plot([x_wheel], [e_can], "o", color=C_LIVE, ms=8)
        ax2.plot([GIRDER_SPACING], [e_int], "o", color=C_CAP, ms=8)
        ax2.annotate(f"{e_can:.2f} m", (x_wheel, e_can),
                     textcoords="offset points", xytext=(8, -4), fontsize=9)
        ax2.annotate(f"{e_int:.2f} m", (GIRDER_SPACING, e_int),
                     textcoords="offset points", xytext=(-44, 4), fontsize=9)
        ax2.set_xlabel("X 또는 L (m)")
        ax2.set_ylabel("등가 분포폭 E (m)")
        ax2.set_title("분포폭은 캔틸레버가 오히려 넓다")
        ax2.legend(fontsize=8.5)
        ax2.grid(alpha=0.3)

        fig.tight_layout()
        '''),

        md(r"""
        ## 3. 헌치 — 고정단을 두껍게 하면

        캔틸레버는 고정단에서 모멘트가 최대이고 끝으로 갈수록 0 이다. 그래서
        고정단만 두껍게 하는 **헌치**가 자연스럽다. 얼마나 듣는가?

        **아래 코드가 하는 일** — 고정단 두께를 바꿔 가며 소요 철근량과
        설계휨강도를 본다.
        """),
        code(r'''
        def cantilever_design(haunch, dia=19.0, spacing=125.0):
            """고정단 두께에 대한 소요·배치 철근량과 강도를 돌려준다."""
            loads = cantilever_moments(haunch=haunch)
            m_ed = COMBINATIONS_BY_NAME["극한Ⅰ"].evaluate(loads=loads)
            _, cover = nominal_cover(exposure=EXPOSURE, bar_diameter=dia)
            d = haunch - cover - dia / 2
            as_req = required_steel_area(m_ed=m_ed * 1e6, d=d, fck=FCK, fy=FY)
            as_prov = provided_steel_area(diameter=dia, spacing=spacing)
            f_cd = design_compressive_strength(fck=FCK)
            f_yd = design_yield_strength(fy=FY)
            alpha, beta = equivalent_block(fck=FCK)
            c = as_prov * f_yd / (alpha * f_cd * 1000.0)
            m_rd = as_prov * f_yd * (d - beta * c) / 1e6
            return m_ed, d, as_req, as_prov, m_rd

        print(f"{'헌치':>7} {'d':>7} {'M_Ed':>8} {'필요 As':>9} "
              f"{'M_Rd':>8} {'M_Rd/M_Ed':>10}")
        print("-" * 56)
        for h in (240.0, 260.0, 280.0, 300.0, 350.0, 400.0):
            m_ed_h, d_h, as_req, as_prov, m_rd = cantilever_design(h)
            print(f"{h:7.0f} {d_h:7.0f} {m_ed_h:8.1f} {as_req:9.0f} "
                  f"{m_rd:8.1f} {m_rd / m_ed_h:10.2f}")
        '''),

        code(r'''
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.3))

        hs = np.arange(230.0, 405.0, 5.0)
        med = np.array([cantilever_design(float(h))[0] for h in hs])
        mrd = np.array([cantilever_design(float(h))[4] for h in hs])

        ax1.plot(hs, mrd, color=C_CAP, lw=2.4, label="M_Rd (D19@125)")
        ax1.plot(hs, med, color=C_LOAD, lw=2.4, label="M_Ed")
        ax1.fill_between(hs, med, mrd, where=(mrd >= med), color=C_CAP,
                         alpha=0.12, label="여유")
        idx = int(np.argmax(mrd >= med))
        if mrd[idx] >= med[idx]:
            ax1.axvline(hs[idx], color=C_MUTED, ls=":", lw=1.4)
            ax1.annotate(f"{hs[idx]:.0f} mm 부터 만족",
                         (hs[idx], mrd.max() * 0.35), ha="center",
                         fontsize=9, color=C_MUTED)
        ax1.set_xlabel("고정단 두께 (헌치, mm)")
        ax1.set_ylabel("휨모멘트 (kN·m/m)")
        ax1.set_title("헌치는 강도를 올리고 자중도 데려온다")
        ax1.legend(fontsize=9)
        ax1.grid(alpha=0.3)

        gain = (mrd[-1] - mrd[0]) / (hs[-1] - hs[0]) * 10
        cost = (med[-1] - med[0]) / (hs[-1] - hs[0]) * 10
        ax2.bar(["강도 증가", "하중 증가"], [gain, cost],
                color=[C_CAP, C_LOAD], width=0.55)
        for i2, v in enumerate([gain, cost]):
            ax2.text(i2, v + gain * 0.03, f"{v:+.2f}", ha="center", fontsize=10)
        ax2.set_ylabel("두께 10 mm 당 변화 (kN·m/m)")
        ax2.set_title(f"자중이 이득의 {cost / gain * 100:.0f} % 를 가져간다")
        ax2.grid(axis="y", alpha=0.3)

        fig.tight_layout()
        '''),

        md(r"""
        **읽는 법** — 헌치는 **두 방향으로 동시에 듣는다.** 두께가 늘면
        $d$ 가 커져 강도가 오르고, 동시에 자중이 늘어 $M_{Ed}$ 도 오른다.
        L4 의 내측슬래브에서는 자중이 이득의 4 % 만 갉아먹었는데, 캔틸레버는
        자중이 $-wl^2/2$ 로 걸려 **더 많이** 갉아먹는다.

        그래도 순효과는 뚜렷하다. 헌치가 캔틸레버 설계의 표준 수단인 이유다.

        ## 4. 철근 배치 — 위쪽이다

        내측슬래브는 지간부에서 아래가 인장이라 **하부철근**이 주철근이었다.
        캔틸레버는 고정단에서 **위가 인장**이므로 **상부철근**이 주철근이다.

        이 철근은 바닥판 상면 가까이 놓이는데, 그 위가 바로 **제설염이 닿는
        면**이다. 그래서 노출등급이 피복을 크게 밀어올린다.

        **아래 코드가 하는 일** — 노출등급별 피복과 그 대가를 본다.
        """),
        code(r'''
        print(f"{'노출등급':>8} {'피복':>7} {'d':>7} {'M_Rd':>9} {'M_Rd/M_Ed':>10}")
        print("-" * 46)
        for cls in ("E0", "EC1", "EC2", "ED1", "ED3", "ES3"):
            _, cover = nominal_cover(exposure=cls, bar_diameter=19.0)
            d = HAUNCH - cover - 19.0 / 2
            as_prov = provided_steel_area(diameter=19.0, spacing=125.0)
            f_cd = design_compressive_strength(fck=FCK)
            f_yd = design_yield_strength(fy=FY)
            alpha, beta = equivalent_block(fck=FCK)
            c = as_prov * f_yd / (alpha * f_cd * 1000.0)
            m_rd = as_prov * f_yd * (d - beta * c) / 1e6
            mark = "  <- 이 강의" if cls == EXPOSURE else ""
            print(f"{cls:>8} {cover:7.0f} {d:7.0f} {m_rd:9.1f} "
                  f"{m_rd / m_ed:10.2f}{mark}")
        '''),

        md(r"""
        ## 5. 그런데 실제로는 무엇이 상부철근을 정하는가

        여기까지 캔틸레버를 **활하중과 자중**으로 풀었다. 그런데 실무에서
        캔틸레버 상부철근은 대개 이 계산으로 정해지지 않는다.

        **차량 충돌하중**(KDS 24 90 11) 때문이다. 방호벽에 차량이 부딪히면
        그 힘이 캔틸레버 고정단에 모멘트로 전달되는데, 이것은
        **극단상황한계상태**로 검토한다. 등급에 따라 수백 kN 의 횡력이
        방호벽 상단에 걸리므로, 고정단 모멘트가 이 강의의 130 kN·m/m 를
        크게 넘는 경우가 많다.

        > **설계의 의도** — 이 강의가 푼 것은 **하한**이다. 충돌하중은
        > 극단상황이라 하중계수와 검토 방식이 다르고, 방호벽-바닥판 접합부의
        > 상세가 함께 결정된다. 이 편의 범위 밖이지만, **캔틸레버 상부철근을
        > 활하중만으로 확정해서는 안 된다**는 것은 기억해야 한다.

        **아래 코드가 하는 일** — 참고로, 방호벽 상단에 횡력이 걸릴 때
        고정단 모멘트가 어떻게 자라는지 크기만 가늠해 본다.
        """),
        code(r'''
        # 방호벽 높이 (m) 와 가상의 횡력 — 실제 값은 KDS 24 90 11 의 등급을 따른다
        H_BARRIER = 1.27
        print("참고 — 방호벽 상단 횡력이 고정단에 만드는 모멘트")
        print(f"{'횡력 (kN/m)':>12} {'M (kN·m/m)':>12} {'활하중 M_Ed 대비':>16}")
        print("-" * 44)
        for ft in (20.0, 50.0, 100.0, 150.0):
            m_collision = ft * H_BARRIER
            print(f"{ft:12.0f} {m_collision:12.1f} "
                  f"{m_collision / m_ed:15.2f} 배")
        print()
        print("실제 검토는 극단상황한계상태 하중조합과 방호벽 자체의 저항")
        print("(항복선 이론)까지 함께 보아야 한다. KDS 24 90 11 을 볼 것.")
        '''),

        md(r"""
        ## 6. 바꿔 보며 확인할 것

        1. `CANTILEVER` 를 0.8 m 로 줄이면 내측부와 어느 쪽이 지배하는가?
           캔틸레버가 짧아지면 분포폭도 좁아진다는 점을 함께 보라.
        2. `BARRIER_LOAD` 를 두 배로 올리면 $M_{Ed}$ 가 몇 % 오르는가?
           방호벽이 주범이 아니라는 결론이 유지되는가?
        3. `HAUNCH` 를 240 mm(내측과 같게)로 두면 D19@125 로 충분한가?
        4. 노출등급을 `ES3` 로 바꾸면 헌치를 얼마나 키워야 원래 강도를
           되찾는가?

        ## 7. 정리

        1. **캔틸레버의 등가 분포폭은 내측보다 넓다** (1.94 vs 1.35 m).
           "좁은 폭에 몰린다"는 설명은 틀렸다. $X$ 에 대한 기울기가 0.8 로
           내측의 0.06 보다 13 배 가파른데, 두 식이 재는 것이 다르기 때문이다.
        2. **방호벽은 주범이 아니다.** 증가분의 대부분은 활하중이다.
        3. **진짜 원인은 지렛대 팔(75 %)과 연속 혜택의 부재(25 %)다.**
           방호벽은 전체 증가분의 15 % 에 그친다.
        4. **헌치는 듣지만 자중을 데려온다.** 캔틸레버는 자중이 $-wl^2/2$ 로
           걸려 내측보다 대가가 크다.
        5. **주철근은 상부철근이고, 그 위가 제설염이 닿는 면이다.**
           노출등급이 피복을 통해 강도를 직접 깎는다.
        6. **이 계산은 하한이다.** 실제 캔틸레버 상부철근은 차량 충돌하중
           (KDS 24 90 11, 극단상황한계상태)이 정하는 경우가 많다.

        ## 8. 생각해 볼 문제

        1. 캔틸레버 분포폭 식의 기울기가 0.8 로 가파른데, $X$ 가 0 에 가까워지면
           $E \to 1.14$ m 로 수렴한다. 이 1.14 m 는 무엇을 뜻하는가?
        2. 캔틸레버를 길게 하면 활하중 모멘트는 $P X / (0.8X + 1.14)$ 로
           자란다. $X$ 가 매우 커지면 이 값은 어디로 수렴하는가? 그 극한값이
           설계에 시사하는 바는?
        3. 내측슬래브는 연속판이라 0.8 배를 받는다. 그런데 **최외측 거더 위**의
           단면은 한쪽은 캔틸레버, 한쪽은 내측 경간이다. 이 지점의 부모멘트는
           어느 쪽 규정을 따라야 하는가?
        4. 헌치를 키우는 대신 캔틸레버를 짧게 하고 거더를 하나 더 놓는 방법도
           있다. 두 선택의 대가를 무엇으로 견주어야 하는가?
        5. 충돌하중이 상부철근을 정한다면, 이 강의가 푼 활하중 검토는 무의미한가?
           그렇지 않다면 어떤 역할을 하는가?
        """),
    ], directory=LECTURES)


GIRDER_SETUP = r'''
from concreteproperties_kds.kds import stress_block_parameters
from concreteproperties_kds.kds24 import (
    EXAMPLE_SECTIONS,
    GAMMA_CONCRETE,
    TENDON_COVER,
    characteristic_tensile_strength,
    design_compressive_strength,
    design_girder,
    design_yield_strength,
    elastic_modulus,
    equivalent_block,
    girder_live_load,
    max_jacking_stress,
)

STRAND = 138.7   # 15.2 mm 7연선 1가닥의 단면적 (mm2)
FPU, FPY = 1860.0, 1600.0

# 기준 조건 — 앞으로 이 값을 하나씩 바꿔 가며 비교한다
SECTION = EXAMPLE_SECTIONS["PSC-I 2.0m"]   # 거더 단면      <- 바꿔 보라
SPAN = 30.0                                # 지간 (m)       <- 바꿔 보라
STRANDS = 25                               # 강연선 가닥 수  <- 바꿔 보라

BASE = dict(section=SECTION, span=SPAN, a_p=STRANDS * STRAND)

C_JACK = "#5b6472"
C_LOSS = "#b3372c"
C_EFF = "#1f6feb"
C_CAP = "#1f7a4d"
C_K14 = "#b3372c"

props = SECTION.properties()
print(f"{SECTION.name}:  A = {props.area / 1e6:.3f} m2,  "
      f"y_b = {props.y_b:.0f} mm,  I = {props.inertia / 1e12:.4f} m4")
print(f"기본 편심 e = y_b - {TENDON_COVER:.0f} = {props.y_b - TENDON_COVER:.0f} mm")
'''


def nb_l6_girder_flexure():
    """강의 L6 - PSC 거더 휨설계. 왜 사용한계상태가 단면을 정하는가."""
    return write("L6_PSC거더_휨설계", [
        md(r"""
        # L6 · PSC 거더 휨설계 — 강도가 남는데 왜 단면이 커지는가

        ## 이 시간에 답할 질문

        철근콘크리트 보는 **극한한계상태**가 단면을 정한다. 휨강도가 모자라면
        철근을 늘리고, 그래도 모자라면 단면을 키운다. 사용성은 대개 나중에
        확인만 한다.

        PSC 거더는 그렇지 않다. 이 강의에서 계산해 보면, 30 m 거더의 설계
        휨강도는 소요값의 **1.01 배**로 아슬아슬한데, 45 m 거더는 **1.11 배**로
        여유가 있다. 그런데도 45 m 거더가 강연선을 더 넣어야 한다.
        **강도가 남는데 단면이 결정되지 않는 것이다.**

        1. 프리스트레스는 넣은 만큼 남지 않는다. 어디로, 얼마나 사라지는가?
        2. 편심은 클수록 좋은가? 그렇다면 왜 실제 거더는 텐던을 휘어 놓는가?
        3. 지간이 길어지면 어느 순간 지배하는 한계상태가 바뀐다. 언제, 왜?
        4. 같은 거더를 KDS 14 로 풀면 얼마나 다른가?

        :::{note}
        이 편은 **휨**만 다룬다. 전단은 프리스트레스가 강도에 직접 들어가는
        방식부터 다르므로 [L7](L7_PSC거더_전단설계.ipynb) 에서 따로 다룬다.
        :::

        ## 근거 조문

        | 내용 | 조문 |
        |---|---|
        | 긴장 시 최대 응력 식 $(1.5\text{-}7)$ | KDS 24 14 21 1.5.7.2 |
        | 도입 직후 응력 식 $(1.5\text{-}9)$ | KDS 24 14 21 1.5.7.3 |
        | 긴장 시 콘크리트 압축 한계 식 $(1.5\text{-}8)$ | KDS 24 14 21 1.5.7.3 |
        | 마찰 손실 식 $(1.5\text{-}11)$, 표 1.5-2 | KDS 24 14 21 1.5.7.4 |
        | 탄성변형 손실 식 $(1.5\text{-}10)$ | KDS 24 14 21 1.5.7.4 |
        | 릴랙세이션 식 $(3.3\text{-}1)\sim(3.3\text{-}3)$ | KDS 24 14 21 3.3.2(7) |
        | 장기 손실 식 $(1.5\text{-}12)$ | KDS 24 14 21 1.5.7.5 |
        | 사용한계상태 응력 한계, 표 4.2-2 | KDS 24 14 21 4.2.2 |
        | 극한한계상태 휨 | KDS 24 14 21 4.1.1 |

        :::{warning}
        이 강의가 쓰는 :data:`EXAMPLE_SECTIONS` 는 **예시 단면이며 어떤
        표준도도 아니다.** 형상은 일반적인 PSC I형 거더를 본떴을 뿐이므로,
        실제 설계에는 해당 표준도나 제작사 제원을 써야 한다.
        :::
        """, EXPLORER_NOTE),

        md("""
        ## 0. 준비

        **아래 코드가 하는 일** — 한글 글꼴을 등록하고 그림 색을 정한다.
        """),
        code(SETUP),
        md(r"""
        **아래 코드가 하는 일** — 이 편에서 따라갈 설계 흐름을 순서도로
        그린다. 각 단계 옆에 근거 조문을 적었다.
        """),
        code(FLOWCHART + '''
design_flowchart(
"PSC 거더 휨설계 흐름",
[
    ("거더 단면·합성 단면 성질", "24 14 21 4.6"),
    ("하중별 저항 단면 구분", "24 10 11 4.6.3"),
    ("활하중 KL-510 과 하중조합", "24 12 21 4.3 · 24 12 11 표 4.1-1"),
    ("긴장응력 상한 (식 1.5-7)", "24 14 21 1.5.7.2"),
    ("즉시 손실 — 마찰·정착·탄성", "24 14 21 1.5.7.4"),
    ("장기 손실 (식 1.5-12)", "24 14 21 1.5.7.5, 3.3.2(7)"),
    ("사용한계상태 응력 검토", "24 14 21 4.2.2"),
    ("극한한계상태 휨강도", "24 14 21 4.1.1"),
    ("텐던 배치 — 핵거리와 드레이프", "24 14 21 1.5.7.3"),
],
)
        '''),

        md(r"""
        **아래 코드가 하는 일** — 거더 설계 함수를 불러오고 기준 조건을 정한다.
        형고 2.0 m 의 PSC I형 거더를 지간 30 m 에 거더 간격 2.5 m 로 놓고,
        15.2 mm 강연선 25 가닥을 넣은 경우다.
        """),
        code(GIRDER_SETUP),

        md(r"""
        ## 1. 넣은 만큼 남지 않는다

        프리스트레스 설계가 철근콘크리트와 결정적으로 다른 점은 **넣은 힘이
        시간이 지나면 줄어든다**는 것이다. 철근은 넣어 두면 그대로 있지만,
        긴장재는 그렇지 않다.

        기준은 손실을 두 묶음으로 나눈다.

        **즉시 손실** — 긴장하는 그 순간에 이미 생긴다.

        - **마찰** 식 $(1.5\text{-}11)$: 덕트 안에서 강연선이 끌리며 잃는다.
          곡률각 $\theta$ 와 길이 $x$ 에 지수적으로 붙는다.
        - **정착장치 활동**: 쐐기를 물릴 때 강연선이 몇 mm 끌려 들어간다.
        - **탄성변형** 식 $(1.5\text{-}10)$: 긴장하면 콘크리트가 줄고, 그만큼
          이미 정착된 강연선도 같이 줄어 응력을 잃는다.

        **장기 손실** 식 $(1.5\text{-}12)$ — 몇 년에 걸쳐 진행된다.

        - **크리프**: 압축을 받은 콘크리트가 계속 줄어든다.
        - **건조수축**: 콘크리트가 마르며 줄어든다.
        - **릴랙세이션** 식 $(3.3\text{-}2)$: 강연선 자체가 늘어난 채로
          응력을 잃는다.

        **아래 코드가 하는 일** — 손실을 항목별로 계산해 표로 찍는다.
        """),
        code(r'''
        result = design_girder(**BASE)
        losses = result.losses

        print(f"긴장응력  f_jack = {losses.f_jack:7.1f} MPa"
              f"   = min(0.8 x {FPU:.0f}, 0.9 x {FPY:.0f})")
        print("-" * 58)
        items = [
            ("마찰", losses.friction),
            ("정착장치 활동", losses.anchorage),
            ("탄성변형", losses.elastic),
        ]
        for name, value in items:
            print(f"  {name:14s} -{value:6.1f} MPa   "
                  f"({value / losses.f_jack * 100:5.2f} %)")
        print(f"도입 직후 f_pi   = {losses.f_pi:7.1f} MPa"
              f"   즉시손실 {losses.immediate_ratio * 100:5.2f} %")
        print("-" * 58)
        print(f"  {'장기(크리프+건조수축+릴랙세이션)':s} "
              f"-{losses.long_term:.1f} MPa "
              f"({losses.long_term / losses.f_jack * 100:.2f} %)")
        print(f"유효응력  f_pe   = {losses.f_pe:7.1f} MPa"
              f"   총손실   {losses.total_ratio * 100:5.2f} %")
        print("-" * 58)
        print(f"P_i = {result.p_i / 1e3:6.0f} kN"
              f"      P_e = {result.p_e / 1e3:6.0f} kN")
        '''),

        md(r"""
        **읽는 법** — 긴장할 때 1,440 MPa 를 걸었는데 최종적으로 남는 것은
        1,138 MPa 다. **21 % 가 사라진다.** 그리고 그중 가장 큰 몫은 크리프도
        건조수축도 아닌 **마찰(8.0 %)** 이다.

        이것이 실무에서 중요한 이유가 있다. 크리프와 건조수축은 재료와 환경이
        정하므로 설계자가 크게 손댈 수 없다. 그러나 마찰은 **텐던 배치가
        정한다.** 곡률을 줄이거나, 양쪽에서 긴장하거나, 윤활 덕트를 쓰면
        (표 1.5-2 에서 $\mu$ 가 0.19 → 0.12) 줄일 수 있다. 설계자가 실제로
        움직일 수 있는 손실이 가장 큰 손실인 셈이다.

        **아래 코드가 하는 일** — 손실을 폭포 그림으로 그려 어디서 얼마가
        빠지는지 한눈에 보인다.
        """),
        code(r'''
        fig, ax = plt.subplots(figsize=(9.5, 4.2))

        names = ["긴장", "마찰", "정착", "탄성", "장기", "유효"]
        deltas = [losses.friction, losses.anchorage,
                  losses.elastic, losses.long_term]

        level = losses.f_jack
        ax.bar(0, level, color=C_JACK, width=0.6)
        ax.text(0, level + 25, f"{level:.0f}", ha="center", fontsize=9)

        for i, d in enumerate(deltas, start=1):
            ax.bar(i, d, bottom=level - d, color=C_LOSS, width=0.6)
            ax.text(i, level + 25, f"-{d:.0f}", ha="center",
                    fontsize=9, color=C_LOSS)
            level -= d

        ax.bar(5, level, color=C_EFF, width=0.6)
        ax.text(5, level + 25, f"{level:.0f}", ha="center",
                fontsize=9, color=C_EFF)

        ax.set_xticks(range(6))
        ax.set_xticklabels(names)
        ax.set_ylabel("긴장재 응력 (MPa)")
        ax.set_title(f"프리스트레스 손실 - {SECTION.name}, 지간 {SPAN:.0f} m, "
                     f"{STRANDS}가닥")
        ax.set_ylim(0, losses.f_jack * 1.18)
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        '''),

        md(r"""
        ## 2. 도입응력의 상한은 왜 $f_{py}$ 가 정하는가

        식 $(1.5\text{-}7)$ 은 긴장 시 최대 응력을 이렇게 준다.

        $$
        f_{o,\max} = \min(0.80 f_{pu},\; 0.90 f_{py})
        $$

        SWPC 7B 15.2 mm 강연선은 $f_{pu} = 1{,}860$, $f_{py} = 1{,}600$ MPa 다.
        넣어 보면 $0.80 \times 1860 = 1488$, $0.90 \times 1600 = 1440$ 이므로
        **항복강도 조건이 지배한다.**

        두 조건이 하는 일이 다르다. $0.80 f_{pu}$ 는 **끊어지지 않게** 하는
        조건이고, $0.90 f_{py}$ 는 **항복하지 않게** 하는 조건이다. 긴장재가
        항복해 버리면 프리스트레스가 힘을 잃으므로, 파단보다 항복이 먼저
        막아야 할 사건이다.

        **아래 코드가 하는 일** — 강재 종류를 바꿔 가며 어느 조건이 지배하는지
        본다.
        """),
        code(r'''
        print(f"{'강재':16s} {'f_pu':>7} {'f_py':>7} "
              f"{'0.8f_pu':>9} {'0.9f_py':>9} {'지배':>10}")
        print("-" * 64)
        for name, fpu, fpy in [
            ("SWPC 7B (일반)", 1860.0, 1600.0),
            ("f_py 가 높은 강재", 1860.0, 1750.0),
            ("f_py/f_pu = 0.85", 1860.0, 1581.0),
        ]:
            a, b = 0.80 * fpu, 0.90 * fpy
            governs = "0.8 f_pu" if a < b else "0.9 f_py"
            print(f"{name:16s} {fpu:7.0f} {fpy:7.0f} {a:9.0f} {b:9.0f} "
                  f"{governs:>10}")

        print()
        print("두 조건이 같아지는 항복비:  0.8 f_pu = 0.9 f_py")
        print(f"  ->  f_py / f_pu = 0.8 / 0.9 = {0.8 / 0.9:.4f}")
        print("항복비가 이보다 낮으면 f_py 조건이, 높으면 f_pu 조건이 지배한다.")
        '''),

        md(r"""
        **읽는 법** — 경계는 항복비 $f_{py}/f_{pu} = 0.889$ 다. 보통 강연선의
        항복비는 0.85 ~ 0.86 이므로 **거의 항상 $0.90 f_{py}$ 가 지배한다.**
        $f_{pu}$ 조건은 사실상 예비 조건인 셈이다.

        ## 3. 편심은 클수록 좋은가

        프리스트레스가 휨에 저항하는 원리는 **편심 모멘트** $P \cdot e$ 다.
        같은 힘이라도 도심에서 멀리 걸수록 큰 모멘트를 만든다. 그러면 편심을
        최대한 키우면 되지 않는가?

        **아래 코드가 하는 일** — 편심만 바꿔 가며 응력과 휨강도를 본다.
        """),
        code(r'''
        print(f"{'e (mm)':>8} {'긴장 상연':>10} {'긴장 하연':>10} "
              f"{'사용 하연':>10} {'M_Rd':>9}  판정")
        print("-" * 62)

        eccentricities = [300, 400, 500, 600, 700,
                          props.y_b - TENDON_COVER, 850]
        for e in eccentricities:
            r = design_girder(**{**BASE, "eccentricity": float(e)})
            failed = [k for k, v in r.checks.items() if not v]
            verdict = "OK" if r.adequate else ", ".join(failed)
            mark = " <- 기본값" if abs(e - (props.y_b - TENDON_COVER)) < 1 else ""
            print(f"{e:8.0f} {r.stresses['긴장 직후'][0]:10.2f} "
                  f"{r.stresses['긴장 직후'][1]:10.2f} "
                  f"{r.stresses['사용'][1]:10.2f} {r.m_rd:9.0f}  "
                  f"{verdict}{mark}")
        '''),

        md(r"""
        **읽는 법** — 편심을 키울수록 사용 시 하연 인장이 줄고($-6.53 \to
        -1.65$ MPa) 휨강도도 는다(7,783 → 10,529 kN·m). **지간 중앙만 보면
        편심은 클수록 좋다.** 상한은 응력이 아니라 하부플랜지 안에 강연선을
        넣을 자리가 있느냐는 **기하학적 제약**이다.

        그런데 실제 PSC 거더의 텐던은 곧지 않다. 단부로 갈수록 위로 휘어
        올라간다. 왜인가?

        **지간 중앙에서 편심이 유리했던 이유는 자중 모멘트가 있었기
        때문이다.** 프리스트레스가 상연에 만드는 인장을 자중이 상쇄해 주었다.
        그런데 **단부에서는 자중 모멘트가 0 이다.** 상쇄해 줄 것이 없다.

        **아래 코드가 하는 일** — 단부 단면에서 편심에 따른 상연 응력을 본다.
        """),
        code(r'''
        z_t = props.inertia / props.y_t
        kern = z_t / props.area           # 핵거리 - 이 안이면 전단면 압축
        f_ctk_transfer = characteristic_tensile_strength(fck=30.0)

        print(f"단부 단면 (자중 모멘트 = 0),  P_i = {result.p_i / 1e3:.0f} kN")
        print(f"{'e (mm)':>8} {'상연 응력 (MPa)':>16}   상태")
        print("-" * 46)
        for e in (300, 400, kern, 500, 600, props.y_b - TENDON_COVER):
            top = result.p_i / props.area - result.p_i * e / z_t
            if top >= 0:
                state = "압축"
            elif -top <= f_ctk_transfer:
                state = "인장 (균열 전)"
            else:
                state = "인장 - 균열!"
            print(f"{e:8.0f} {top:16.2f}   {state}")

        print()
        print(f"핵거리  Z_t / A = {kern:.0f} mm")
        print(f"긴장 시 f_ctk (f_ck = 30) = {f_ctk_transfer:.2f} MPa")
        print(f"중앙 편심 {props.y_b - TENDON_COVER:.0f} mm 를 단부까지 "
              f"그대로 끌고 가면 상연 인장이 "
              f"{abs(result.p_i / props.area - result.p_i * (props.y_b - TENDON_COVER) / z_t):.2f} MPa "
              f"로 f_ctk 를 넘는다.")
        '''),

        md(r"""
        **읽는 법** — 여기서 **핵거리** $Z_t/A = 457$ mm 가 나온다. 편심이 이
        안에 있으면 단면 전체가 압축이고, 넘으면 상연에 인장이 생긴다.

        중앙에서 쓰는 편심 762 mm 를 단부까지 그대로 끌고 가면 상연 인장이
        **3.30 MPa** 로, 긴장 시 인장강도 $f_{ctk} = 2.20$ MPa 를 넘어
        **거더 단부 상연이 갈라진다.**

        그래서 텐던을 **드레이프**(휘어 올림)하거나 일부를 **디본딩**한다.
        이것은 시공 편의가 아니라 **응력이 요구하는 형상**이다. 중앙에서는
        편심이 커야 하고 단부에서는 핵 안으로 들어와야 하니, 그 사이를 잇는
        곡선이 곧 텐던 배치도가 된다.

        **아래 코드가 하는 일** — 지간을 따라 필요한 편심의 위·아래 한계를
        그려 텐던이 지나야 할 통로를 보인다.
        """),
        code(r'''
        fig, ax = plt.subplots(figsize=(10, 4.6))

        x = np.linspace(0, SPAN, 200)
        w_self = GAMMA_CONCRETE * props.area / 1e6
        m_self = w_self * x * (SPAN - x) / 2.0        # 자중 모멘트 (kN.m)

        z_b = props.inertia / props.y_b
        p = result.p_i

        # 긴장 직후 상연 응력이 한계를 지킬 편심의 상한.
        #   P/A - P e / Z_t + M_self / Z_t >= -f_lim   을 e 에 대해 푼 것
        def upper(f_lim):
            return z_t / props.area + (m_self * 1e6 + f_lim * z_t) / p

        e_zero = upper(0.0)              # 영응력 - design_girder 가 쓰는 검토
        e_crack = upper(f_ctk_transfer)  # f_ctk 까지 허용하면 여기까지
        e_geom = props.y_b - TENDON_COVER

        ax.fill_between(x, 0, np.minimum(e_zero, e_geom),
                        color=C_EFF, alpha=0.13,
                        label="텐던을 둘 수 있는 영역 (영응력 기준)")
        ax.plot(x, e_zero, color=C_LOSS, lw=2,
                label="상한 - 단부 상연 영응력")
        ax.plot(x, e_crack, color=C_LOSS, lw=1.4, ls="-.", alpha=0.65,
                label="상한 - 인장을 f_ctk 까지 허용할 때")
        ax.axhline(e_geom, color=C_CAP, lw=2, ls="--",
                   label=f"상한 - 하부플랜지 기하 ({e_geom:.0f} mm)")
        ax.axhline(kern, color="#888", lw=1.2, ls=":",
                   label=f"핵거리 {kern:.0f} mm")

        # 전형적인 2차 포물선 드레이프
        e_drape = kern + (e_geom - kern) * (1 - (1 - 2 * x / SPAN) ** 2)
        ax.plot(x, e_drape, color="#111", lw=2.2,
                label="포물선 드레이프 배치 (예)")

        ax.set_xlabel("지간 방향 위치 (m)")
        ax.set_ylabel("편심 e (mm)")
        ax.set_title("텐던이 지나야 할 통로 - 단부는 핵 안으로, 중앙은 최대로")
        ax.set_xlim(0, SPAN)
        ax.set_ylim(0, e_geom * 1.45)
        ax.legend(fontsize=8.5, loc="upper center", ncol=2)
        ax.grid(alpha=0.3)
        fig.tight_layout()
        '''),

        md(r"""
        **읽는 법** — 파란 영역이 텐던을 둘 수 있는 자리다. 단부(x = 0)에서
        상한은 정확히 **핵거리 457 mm** 다. 자중 모멘트가 0 이니 식이
        $Z_t/A$ 로 줄어들기 때문이다. 중앙으로 갈수록 자중 모멘트가 상한을
        밀어올려 넓어지고, 결국 **응력이 아니라 하부플랜지의 기하**가
        상한이 된다.

        점선(-·-)은 인장을 $f_{ctk}$ 까지 허용했을 때의 상한이다. 단부에서
        667 mm 까지 올라간다. 어느 쪽을 쓰느냐는 **설계등급이 정한다** —
        표 4.2-2 에서 긴장 직후 영응력을 요구하는 등급이면 실선이,
        균열폭 제한만 요구하는 등급이면 점선이 상한이 된다. 이 강의의
        `design_girder` 는 보수적인 쪽(영응력)을 쓴다.

        검은 선이 전형적인 포물선 드레이프다. 이 곡선이 통로 안에 있으면
        배치가 성립한다. **텐던을 휘는 것은 관행이 아니라 이 그림이 시키는
        일이다.**

        ## 4. 합성 단면이 하는 일

        PSC 거더교는 보통 **거더를 먼저 놓고 바닥판을 나중에 친다.** 그래서
        하중마다 저항하는 단면이 다르다.

        | 하중 | 저항 단면 |
        |---|---|
        | 거더 자중 | 거더 단독 |
        | 굳지 않은 바닥판 콘크리트 | 거더 단독 |
        | 2차 고정하중 (포장·방호벽) | 합성 단면 |
        | 활하중 | 합성 단면 |

        굳지 않은 바닥판은 하중이지 단면이 아니다. 이 순서를 지키지 않고
        전부 합성 단면으로 풀면 **거더 단독으로 버텨야 하는 시기를 놓친다.**

        **아래 코드가 하는 일** — 거더 단독과 합성 단면의 성질을 비교한다.
        """),
        code(r'''
        # 탄성계수비는 두 콘크리트의 E_c 에서 직접 구한다.
        # design_girder 가 쓰는 값과 같아야 아래 표가 설계와 일치한다.
        e_ratio = elastic_modulus(fck=27.0) / elastic_modulus(fck=40.0)
        print(f"바닥판/거더 탄성계수비  n = {e_ratio:.4f}")
        print()

        composite = SECTION.composite(
            deck_width=2500.0, deck_thickness=240.0,
            modular_ratio=e_ratio, haunch=50.0,
        )

        print(f"{'':10} {'A (m2)':>9} {'y_b (mm)':>10} "
              f"{'I (m4)':>9} {'Z_b (m3)':>10} {'Z_t (m3)':>10}")
        print("-" * 62)
        for label, s in [("거더 단독", props), ("합성 단면", composite)]:
            print(f"{label:10} {s.area / 1e6:9.3f} {s.y_b:10.0f} "
                  f"{s.inertia / 1e12:9.4f} {s.z_b / 1e9:10.4f} "
                  f"{s.z_t / 1e9:10.4f}")

        print()
        print(f"합성으로 Z_b 가 {composite.z_b / props.z_b:.2f} 배가 된다.")
        print("-> 합성 후에 실리는 하중은 하연 인장을 그만큼 덜 만든다.")

        span_m = SPAN
        w_deck = GAMMA_CONCRETE * 2.5 * 0.240
        m_girder = GAMMA_CONCRETE * props.area / 1e6 * span_m**2 / 8
        m_deck = w_deck * span_m**2 / 8
        m_sdl = 3.0 * span_m**2 / 8
        m_live = girder_live_load(span=span_m).moment * 0.6

        print()
        print("하중별 휨모멘트 (비계수, kN.m)")
        total = m_girder + m_deck + m_sdl + m_live
        for label, m, s in [
            ("거더 자중", m_girder, "거더"),
            ("바닥판", m_deck, "거더"),
            ("2차 고정하중", m_sdl, "합성"),
            ("활하중+충격", m_live, "합성"),
        ]:
            print(f"  {label:14s} {m:8.0f}  ({m / total * 100:4.1f} %)  "
                  f"저항 단면: {s}")
        print(f"  {'합계':14s} {total:8.0f}")
        print(f"  거더 단독이 받는 몫: "
              f"{(m_girder + m_deck) / total * 100:.1f} %")
        '''),

        md(r"""
        **읽는 법** — 합성으로 하연 단면계수가 **1.47 배**가 된다. 그런데
        전체 하중의 **59 %** 는 그 혜택을 못 받는다. 거더 자중과 바닥판이
        합성 전에 이미 실리기 때문이다.

        이것이 PSC 거더 설계의 핵심 제약이다. 큰 단면계수는 나중에나 생기는데,
        가장 불리한 순간(긴장 직후)은 가장 작은 단면으로 버텨야 한다.

        ## 5. 지간이 길어지면 무엇이 바뀌는가

        이제 처음의 질문으로 돌아간다. 지간별로 **최소 강연선 수량**을 구하고,
        그때 무엇이 그 수량을 정했는지 본다.

        **아래 코드가 하는 일** — 지간마다 가닥 수를 1 개씩 늘려 가며 모든
        한계상태를 만족하는 최소값을 찾고, 한 가닥 모자랄 때 무엇이 깨지는지
        기록한다.
        """),
        code(r'''
        CASES = [
            ("PSC-I 1.4m", 20.0),
            ("PSC-I 1.7m", 25.0),
            ("PSC-I 2.0m", 30.0),
            ("PSC-I 2.0m", 35.0),
            ("PSC-I 2.3m", 40.0),
            ("PSC-I 2.7m", 45.0),
            ("PSC-I 2.7m", 50.0),
        ]

        table = []
        for name, span in CASES:
            section = EXAMPLE_SECTIONS[name]
            for n in range(6, 141):
                r = design_girder(section=section, span=span, a_p=n * STRAND)
                if r.adequate:
                    break
            short = design_girder(section=section, span=span,
                                  a_p=(n - 1) * STRAND)
            governing = [k for k, v in short.checks.items() if not v]
            table.append((name, span, n, r, governing))

        print(f"{'단면':12s} {'지간':>5} {'가닥':>5} {'손실':>7} "
              f"{'M_Rd/M_Ed':>10}  한 가닥 모자랄 때 깨지는 것")
        print("-" * 78)
        for name, span, n, r, governing in table:
            print(f"{name:12s} {span:5.0f} {n:5d} "
                  f"{r.losses.total_ratio * 100:6.1f} % "
                  f"{r.m_rd / r.m_ed:10.2f}  {', '.join(governing)}")
        '''),

        md(r"""
        **읽는 법** — 전환이 뚜렷하다.

        - **20 m** — 극한 휨강도만 깨진다. 강도가 정한다.
        - **25 ~ 30 m** — 둘이 동시에 깨진다. 균형점이다.
        - **35 m 이상** — 사용한계상태 균열만 깨진다. **극한 휨강도는 1.09 ~
          1.14 배로 남아도는데도** 강연선을 더 넣어야 한다.

        왜 이렇게 되는가? 지간이 길어질 때 두 요구가 같은 속도로 자라지 않기
        때문이다.

        - 극한 휨강도가 요구하는 것은 **긴장재의 인장력** $A_p f_{pd}$ 다.
          강연선을 늘리면 거의 비례해 는다.
        - 사용한계상태가 요구하는 것은 **하연 압축응력** $P/A + Pe/Z_b$ 이고,
          이것을 깎아내리는 것은 $M/Z_b$ 다. 지간이 길어지면 $M$ 은
          $L^2$ 로 느는데 $Z_b$ 는 형고가 허용하는 만큼만 큰다.

        게다가 손실도 지간에 따라 는다(20.5 % → 25.5 %). 마찰이 길이에
        비례하기 때문이다. **긴 거더는 넣은 힘을 더 많이 잃으면서, 더 많은
        힘을 필요로 한다.**

        **아래 코드가 하는 일** — 두 한계상태의 여유를 지간에 대해 그린다.
        """),
        code(r'''
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.4))

        spans = [t[1] for t in table]
        strands = [t[2] for t in table]
        ratio_uls = [t[3].m_rd / t[3].m_ed for t in table]
        tension = [-t[3].stresses["사용"][1] for t in table]
        f_ctk = characteristic_tensile_strength(fck=40.0)

        ax1.plot(spans, ratio_uls, "o-", color=C_CAP, lw=2,
                 label="극한 - M_Rd / M_Ed")
        ax1.axhline(1.0, color="#888", ls=":", lw=1.2)
        ax1.set_xlabel("지간 (m)")
        ax1.set_ylabel("M_Rd / M_Ed")
        ax1.set_title("극한 휨강도의 여유는 지간이 길수록 커진다")
        ax1.set_ylim(0.95, 1.25)
        ax1.grid(alpha=0.3)
        ax1.legend(fontsize=9)

        for x, y, n in zip(spans, ratio_uls, strands):
            ax1.annotate(f"{n}가닥", (x, y), textcoords="offset points",
                         xytext=(0, 8), ha="center", fontsize=8)

        ax2.plot(spans, tension, "o-", color=C_EFF, lw=2,
                 label="사용 시 하연 인장")
        ax2.axhline(f_ctk, color=C_LOSS, lw=2, ls="--",
                    label=f"한계 f_ctk = {f_ctk:.2f} MPa")
        ax2.set_xlabel("지간 (m)")
        ax2.set_ylabel("하연 인장응력 (MPa)")
        ax2.set_title("사용한계상태는 지간마다 한계에 붙어 있다")
        ax2.set_ylim(0, f_ctk * 1.35)
        ax2.grid(alpha=0.3)
        ax2.legend(fontsize=9)

        fig.tight_layout()
        '''),

        md(r"""
        **읽는 법** — 오른쪽부터 보라. **25 m 이상에서는 사용 시 하연 인장이
        한계선($f_{ctk} = 2.62$ MPa)에 거의 닿아 있다.** 한계에 붙어 있는
        쪽이 지배하는 쪽이다. 반면 20 m 는 1.66 MPa 로 한계에서 멀다 —
        거기서는 사용한계상태가 여유롭고 극한이 단면을 정했다는 뜻이다.

        왼쪽에서 극한 여유는 35 m 를 넘으면서 1.09 → 1.14 로 **벌어진다.**
        사용한계상태가 요구하는 긴장력이 극한이 요구하는 것보다 커졌기
        때문이다.

        다만 두 그림 모두 매끄럽지 않다. 20 m 의 1.05, 45 m 의 2.36 처럼
        튀는 점이 있는데, 이는 물리가 아니라 **강연선을 정수로만 넣을 수
        있어서** 생기는 것이다. 16 가닥에서 한 가닥은 6 % 이므로 필요량을
        그만큼 넘겨 버린다. 지간이 길어져 가닥 수가 많아질수록 이 톱니는
        작아진다.

        ## 6. 같은 거더를 KDS 14 로 풀면

        L1 ~ L3 에서 본 대로, 두 기준은 **안전율을 거는 자리**가 다르다.
        같은 단면의 극한 휨강도를 두 방식으로 계산해 본다.

        **아래 코드가 하는 일** — 합성 단면 상연에서 긴장재까지를 유효깊이로
        보고, 등가블록으로 두 기준의 휨강도를 각각 계산한다.
        """),
        code(r'''
        d_p = SECTION.height + 50.0 + 240.0 - TENDON_COVER
        a_p = STRANDS * STRAND
        b_eff = 2500.0
        fck_deck = 27.0

        # KDS 24 - 재료마다 재료계수
        alpha_eq, beta_eq = equivalent_block(fck=fck_deck, phi_c=0.65)
        lam = 2.0 * beta_eq
        eta24 = alpha_eq / lam
        f_cd = design_compressive_strength(fck=fck_deck, phi_c=0.65)
        f_pd = design_yield_strength(fy=FPY, phi_s=0.90)
        t24 = a_p * f_pd
        a24 = t24 / (eta24 * f_cd * b_eff)
        m_rd = t24 * (d_p - a24 / 2.0) / 1e6

        # KDS 14 - 공칭강도에 강도감소계수 한 번
        _, eta14, _ = stress_block_parameters(fck=fck_deck)
        t14 = a_p * FPY
        a14 = t14 / (eta14 * 0.85 * fck_deck * b_eff)
        m_n = t14 * (d_p - a14 / 2.0) / 1e6
        phi = 0.85

        print(f"유효깊이 d_p = {d_p:.0f} mm,  A_p = {a_p:.0f} mm2,  "
              f"b_eff = {b_eff:.0f} mm")
        print()
        print(f"{'':8} {'강재 응력':>10} {'콘크리트':>10} {'a (mm)':>9} "
              f"{'강도 (kN.m)':>12}")
        print("-" * 56)
        print(f"{'KDS 24':8} {f_pd:10.0f} {f_cd:10.2f} {a24:9.0f} "
              f"{m_rd:12.0f}   <- M_Rd")
        print(f"{'KDS 14':8} {FPY:10.0f} {eta14 * 0.85 * fck_deck:10.2f} "
              f"{a14:9.0f} {m_n:12.0f}   <- M_n")
        print(f"{'':8} {'':10} {'':10} {'x phi=0.85':>9} "
              f"{phi * m_n:12.0f}   <- phi M_n")
        print()
        print(f"KDS 24 / KDS 14 = {m_rd / (phi * m_n):.3f}  "
              f"({(m_rd / (phi * m_n) - 1) * 100:+.1f} %)")
        '''),

        md(r"""
        **읽는 법** — KDS 24 가 **4.8 % 크게** 나온다. L2 에서 본 철근콘크리트
        보의 $+3.9\,\%$ 와 같은 방향, 비슷한 크기다.

        이유도 같다. KDS 14 는 공칭강도 전체에 $\phi = 0.85$ 를 한 번 곱한다.
        KDS 24 는 강재에 0.90, 콘크리트에 0.65 를 따로 곱하는데, **휨에서
        지배하는 것은 강재의 인장력**이므로 실질 감소는 0.90 쪽에 가깝다.
        콘크리트에 걸린 0.65 는 압축블록의 깊이 $a$ 만 늘릴 뿐(97 → 138 mm),
        팔길이를 조금 줄이는 데 그친다.

        :::{note}
        위 비교는 두 기준의 **안전율 배치**만 견주려고 강재 응력을 양쪽 모두
        $f_{py}$ 로 두었다. 실제 KDS 14 설계에서는 부착 긴장재의 극한 응력
        $f_{ps}$ 를 따로 산정하므로 값이 달라진다.
        :::

        ## 7. 바꿔 보며 확인할 것

        위 코드에서 `SECTION`, `SPAN`, `STRANDS` 를 바꿔 가며 확인해 보라.

        1. `SPAN = 55.0`, `SECTION = EXAMPLE_SECTIONS["PSC-I 2.7m"]` 로 두고
           가닥 수를 늘려 보라. 어디까지 늘릴 수 있는가? 무엇이 먼저 막는가?
        2. `design_girder(..., theta=0.0)` 로 곡률을 없애면 마찰 손실이 얼마나
           줄고, 필요한 가닥 수는 몇 개 줄어드는가?
        3. `fck=50.0` 으로 올리면 어느 한계상태가 먼저 풀리는가? 강도인가
           균열인가?
        4. `steel_class=1` (보통 릴랙세이션) 로 바꾸면 총손실이 얼마나 커지는가?

        ## 8. 정리

        1. **넣은 프리스트레스의 21 ~ 28 % 는 사라진다.** 지간이 길수록 더
           사라진다(마찰이 길이에 비례하므로).
        2. **가장 큰 손실은 마찰이다.** 그리고 설계자가 가장 크게 줄일 수 있는
           손실도 마찰이다. 크리프·건조수축은 재료가 정하지만 마찰은 배치가
           정한다.
        3. **도입응력 상한은 거의 항상 $0.90 f_{py}$ 가 정한다.** 항복비
           0.889 가 경계인데, 보통 강연선은 0.85 ~ 0.86 이기 때문이다.
        4. **지간 중앙에서 편심은 클수록 좋고, 상한은 응력이 아니라 기하다.**
           반대로 단부에서는 자중 모멘트가 없어 상한이 핵거리(457 mm)까지
           내려온다. 중앙의 762 mm 와 단부의 457 mm — 이 차이가 **텐던을
           휘게 만든다.**
        5. **하중의 59 % 는 합성 단면의 혜택을 못 받는다.** 거더 자중과
           바닥판이 합성 전에 실리기 때문이다.
        6. **35 m 를 넘으면 사용한계상태가 단면을 정한다.** 극한 휨강도가
           1.09 ~ 1.14 배 남는데도 그렇다. 한계상태설계법이라고 해서 극한이
           항상 지배하는 것이 아니다.
        7. **KDS 24 의 휨강도가 KDS 14 보다 4.8 % 크다.** 재료계수를 나눠
           거는 방식이 휨에서는 조금 덜 보수적이다.

        ## 9. 생각해 볼 문제

        1. 45 m 거더의 극한 휨강도 여유가 1.11 배인데도 강연선을 줄일 수 없다.
           이 남는 강도는 낭비인가, 아니면 무언가를 사고 있는가?
        2. 사용한계상태 균열 검토를 완화해 하연 인장을 $f_{ctk}$ 대신
           $2 f_{ctk}$ 까지 허용한다면 강연선이 얼마나 줄어드는가? 그 대신
           무엇을 잃는가?
        3. 손실을 계산할 때 크리프계수 $\varphi$ 를 2.0 으로 가정했다. 이 값이
           3.0 이었다면 설계가 어떻게 달라지는가? 가정 하나가 이만큼
           움직인다면, 설계자는 무엇을 근거로 이 값을 정해야 하는가?
        4. 단부에서 텐던을 핵 안으로 들이는 대신 **디본딩**(부착을 끊음)을
           쓸 수도 있다. 두 방법은 무엇이 다르고, 각각 어디에 유리한가?
        5. 지간 55 m 에서 긴장 직후 하연 압축이 한계에 가까워진다. 이를
           풀려면 (가) 형고를 키우거나 (나) 긴장 시 $f_{ck}(t)$ 를 올리거나
           (다) 단계별로 긴장할 수 있다. 각각의 대가는 무엇인가?
        """),
    ], directory=LECTURES)



SHEAR_SETUP = r'''
import math

from concreteproperties_kds.kds24 import (
    COT_THETA_MAX,
    COT_THETA_MIN,
    EXAMPLE_SECTIONS,
    GAMMA_CONCRETE,
    axial_stress,
    design_concrete_shear_strength,
    design_girder,
    girder_live_load,
    max_shear_strength,
    maximum_stirrup_spacing,
    minimum_shear_reinforcement_ratio,
    required_stirrup_spacing,
    shear_reinforcement_strength,
)

# L6 에서 설계한 그 거더다
SECTION = EXAMPLE_SECTIONS["PSC-I 2.0m"]
SPAN = 30.0
STRAND, N_STRAND = 138.7, 25
FCK = 40.0
B_W = 290.0            # 복부 두께 (mm)          ← 바꿔 보라
STIRRUP_AREA = 2 * 126.7   # D13 2가닥 (mm²)    ← 바꿔 보라
F_VY = 400.0           # 스터럽 항복강도 (MPa)
COT_THETA = 2.0        # 스트럿 경사             ← 바꿔 보라

girder = design_girder(section=SECTION, span=SPAN, a_p=N_STRAND * STRAND)
props = SECTION.properties()
comp = girder.composite
D_P = girder.d_p
A_P = N_STRAND * STRAND

# 복부의 평균 축압축 — 유효 프리스트레스를 합성 단면적으로 나눈다
F_N = axial_stress(n_u=girder.p_e, a_c=comp.area, fck=FCK)

# 단위길이 하중 (kN/m)
W_TOTAL = (GAMMA_CONCRETE * props.area / 1e6
           + GAMMA_CONCRETE * 2.5 * 0.24 + 3.0)

C_CONC = "#1f7a4d"
C_STEEL = "#1f6feb"
C_LOAD = "#b3372c"
C_MUTED = "#5b6472"


def v_ed(x):
    """지점에서 x (m) 떨어진 곳의 설계전단력 (kN). 극한Ⅰ."""
    v_dc = W_TOTAL * (SPAN / 2 - x)
    v_ll = girder_live_load(span=SPAN, section=x).shear * 0.6
    return 1.25 * v_dc + 1.80 * v_ll


print(f"{SECTION.name}  지간 {SPAN:.0f} m,  강연선 {N_STRAND} 가닥")
print(f"복부 b_w = {B_W:.0f} mm,  d_p = {D_P:.0f} mm")
print(f"유효 프리스트레스 P_e = {girder.p_e / 1e3:.0f} kN")
print(f"복부 평균 축압축 f_n = {F_N:.2f} MPa")
'''


def nb_l7_girder_shear():
    """강의 L7 - PSC 거더 전단설계. 프리스트레스가 강도에 직접 들어간다."""
    return write("L7_PSC거더_전단설계", [
        md(r"""
        # L7 · PSC 거더 전단설계 — 프리스트레스가 강도가 되는 곳

        ## 이 시간에 답할 질문

        [L6](L6_PSC거더_휨설계.ipynb) 에서 휨을 풀었다. 거기서 프리스트레스는
        **하중을 상쇄하는 역할**이었다 — 사용 시 하연 인장을 눌러 주었을 뿐,
        극한 휨강도 $M_{Rd}$ 자체는 $A_p f_{pd}$ 로 정해졌다.

        전단은 다르다. **프리스트레스가 콘크리트 전단강도 식에 직접 들어간다.**
        이 강의에서 계산해 보면 같은 단면의 $V_{cd}$ 가 412 kN 에서
        **666 kN 으로 61 % 오른다.** 프리스트레스를 무시하면 스터럽을
        훨씬 많이 넣게 된다.

        1. 프리스트레스는 왜 전단강도를 직접 올리는가?
        2. **변각 트러스**에서 $\cot\theta$ 를 고르는 것은 설계자의 자유다.
           그 자유의 대가는 무엇인가?
        3. 휨은 지간 중앙이 지배하는데 전단은 어디가 지배하는가?
        4. 스터럽이 필요 없는 구간은 정말 안 넣어도 되는가?

        ## 근거 조문

        | 내용 | 조문 |
        |---|---|
        | 전단철근 없는 부재의 $V_{cd}$ 식 $(4.1\text{-}7)$ | KDS 24 14 21 4.1.2.2 |
        | $V_{cd}$ 하한 식 $(4.1\text{-}8)$ | KDS 24 14 21 4.1.2.2 |
        | 비균열 구간 식 $(4.1\text{-}9)$ | KDS 24 14 21 4.1.2.2 |
        | 변각 트러스 — 스터럽 식 $(4.1\text{-}16)$ | KDS 24 14 21 4.1.2.3 |
        | 스트럿 파괴 상한 식 $(4.1\text{-}17)$ | KDS 24 14 21 4.1.2.3 |
        | 압축강도 유효계수 $\nu$, $\alpha_{cw}$ 식 $(4.1\text{-}23)$ | KDS 24 14 21 4.1.2.3 |
        | $1 \le \cot\theta \le 2.5$ | KDS 24 14 21 4.1.2.3 |
        | 최소 전단철근과 최대 간격 | KDS 24 14 21 4.6.3 |
        """, EXPLORER_NOTE),

        md("""
        ## 0. 준비

        **아래 코드가 하는 일** — 한글 글꼴을 등록하고 그림 색을 정한다.
        """),
        code(SETUP),
        md(r"""
        **아래 코드가 하는 일** — 이 편에서 따라갈 설계 흐름을 순서도로
        그린다. 각 단계 옆에 근거 조문을 적었다.
        """),
        code(FLOWCHART + '''
design_flowchart(
"PSC 거더 전단설계 흐름",
[
    ("설계전단력 V_Ed (극한Ⅰ)", "24 12 21 4.3 · 24 12 11 표 4.1-1"),
    ("복부 축압축 f_n = P_e/A", "24 14 21 4.1.2.2"),
    ("콘크리트 전단강도 V_cd (식 4.1-7)", "24 14 21 4.1.2.2"),
    ("전단철근 필요 구간 판정", "24 14 21 4.1.2.2"),
    ("cot θ 선택 (1 ≤ cot θ ≤ 2.5)", "24 14 21 4.1.2.3"),
    ("스트럿 상한 V_d,max (식 4.1-17)", "24 14 21 4.1.2.3"),
    ("스터럽 간격 (식 4.1-16)", "24 14 21 4.1.2.3"),
    ("최소 전단철근·최대 간격", "24 14 21 4.6.3"),
],
)
        '''),

        md(r"""
        **아래 코드가 하는 일** — L6 에서 설계한 거더를 그대로 불러오고,
        전단 검토에 필요한 값(복부 두께, 유효깊이, 복부 축압축)을 준비한다.
        """),
        code(SHEAR_SETUP),

        md(r"""
        ## 1. 프리스트레스가 전단강도에 들어가는 자리

        전단철근이 없는 부재의 설계전단강도는 식 $(4.1\text{-}7)$ 이다.

        $$
        V_{cd} = \left[ 0.85 \phi_c \kappa (\rho f_{ck})^{1/3}
        + 0.15 f_n \right] b_w d
        $$

        마지막 항 $0.15 f_n$ 이 핵심이다. $f_n$ 은 **단면에 걸린 평균
        축압축응력**이고, 프리스트레스가 바로 그것을 만든다.

        왜 축압축이 전단강도를 올리는가? 전단균열은 복부의 **주인장응력**이
        콘크리트 인장강도를 넘을 때 생긴다. 축압축이 걸려 있으면 모어원이
        통째로 압축 쪽으로 밀려 주인장응력이 줄어든다. 같은 전단력에서
        균열이 늦게 생기는 것이다.

        **아래 코드가 하는 일** — 프리스트레스를 반영할 때와 무시할 때의
        $V_{cd}$ 를 비교한다.
        """),
        code(r'''
        v_cd_0 = design_concrete_shear_strength(
            fck=FCK, b_w=B_W, d=D_P, a_s=A_P, f_n=0.0) / 1e3
        v_cd = design_concrete_shear_strength(
            fck=FCK, b_w=B_W, d=D_P, a_s=A_P, f_n=F_N) / 1e3

        print(f"프리스트레스 무시 (f_n = 0)      V_cd = {v_cd_0:7.1f} kN")
        print(f"프리스트레스 반영 (f_n = {F_N:.2f})   V_cd = {v_cd:7.1f} kN")
        print(f"  -> {(v_cd / v_cd_0 - 1) * 100:+.0f} %")
        print()
        print("f_n 에 따른 V_cd")
        print(f"{'f_n (MPa)':>10} {'V_cd (kN)':>11} {'증가율':>8}")
        for fn in (0.0, 1.0, 2.0, F_N, 4.0, 6.0):
            v = design_concrete_shear_strength(
                fck=FCK, b_w=B_W, d=D_P, a_s=A_P, f_n=fn) / 1e3
            mark = "  <- 이 거더" if abs(fn - F_N) < 1e-9 else ""
            print(f"{fn:10.2f} {v:11.1f} {(v / v_cd_0 - 1) * 100:7.0f} %{mark}")
        '''),

        md(r"""
        **읽는 법** — $f_n$ 이 선형으로 들어가므로 증가도 선형이다.
        이 거더는 $f_n = 2.79$ MPa 로 $V_{cd}$ 가 **61 % 오른다.**

        여기서 주의할 것이 있다. $f_n$ 은 **유효 프리스트레스** $P_e$ 로
        계산해야 한다. L6 에서 본 대로 긴장한 힘의 21 % 는 사라지므로,
        긴장력 $P_{jack}$ 을 쓰면 전단강도를 과대평가한다.

        ## 2. 변각 트러스 — $\cot\theta$ 라는 자유

        전단철근이 들어가면 KDS 24 는 **변각 트러스 모델**을 쓴다. 복부가
        경사 압축 스트럿과 수직 스터럽으로 이루어진 트러스처럼 거동한다고
        보는데, **스트럿의 경사각 $\theta$ 를 설계자가 고른다.**

        $$
        V_{sd} = \phi_s f_{vy} A_v \frac{z \cot\theta}{s}
        \qquad
        V_{d,\max} = \frac{\alpha_{cw} \nu \phi_c f_{ck} b_w z}
        {\cot\theta + \tan\theta}
        $$

        $\cot\theta$ 를 키우면(스트럿을 눕히면) 한 균열을 가로지르는 스터럽이
        많아져 $V_{sd}$ 가 **비례해서 커진다.** 공짜처럼 보인다.

        그런데 같은 $\cot\theta$ 가 $V_{d,\max}$ 의 분모에 들어간다.
        스트럿이 누울수록 **압축력이 커져 스트럿이 먼저 부서진다.**

        **아래 코드가 하는 일** — 두 곡선을 함께 계산해 교차점을 찾는다.
        """),
        code(r'''
        print(f"D13 2가닥 @150 mm 기준")
        print(f"{'cot θ':>7} {'θ':>7} {'V_sd':>9} {'V_d,max':>10} {'지배':>12}")
        print("-" * 50)
        rows = []
        for i in range(11):
            cot = COT_THETA_MIN + (COT_THETA_MAX - COT_THETA_MIN) * i / 10
            v_sd = shear_reinforcement_strength(
                f_vy=F_VY, a_v=STIRRUP_AREA, d=D_P, s=150.0,
                cot_theta=cot) / 1e3
            v_max = max_shear_strength(
                fck=FCK, b_w=B_W, d=D_P, cot_theta=cot) / 1e3
            gov = "스트럿" if v_sd > v_max else "스터럽"
            rows.append((cot, v_sd, v_max))
            print(f"{cot:7.2f} {math.degrees(math.atan(1 / cot)):6.1f}° "
                  f"{v_sd:9.0f} {v_max:10.0f} {gov:>12}")

        # 교차점
        cross = None
        for a, b in zip(rows, rows[1:]):
            if (a[1] - a[2]) * (b[1] - b[2]) < 0:
                t = (a[2] - a[1]) / ((b[1] - a[1]) - (b[2] - a[2]))
                cross = a[0] + t * (b[0] - a[0])
                break
        print()
        if cross:
            print(f"cot θ ≈ {cross:.2f} 를 넘으면 스터럽보다 스트럿이 먼저 깨진다.")
            print("그 위로는 cot θ 를 키워도 강도가 늘지 않고 오히려 준다.")
        '''),

        md(r"""
        **읽는 법** — $\cot\theta$ 를 키우는 것은 공짜가 아니다. 어느 지점을
        넘으면 **스트럿이 먼저 부서져** 강도가 오히려 줄어든다.

        기준이 $1 \le \cot\theta \le 2.5$ 로 범위를 묶어 둔 것도 이 때문이다.
        하한 1.0($45°$)은 균열 방향에서 너무 벗어나지 않게 하는 것이고,
        상한 2.5($21.8°$)는 스트럿이 지나치게 눕는 것을 막는다.

        > **설계의 의도** — 변각 트러스가 주는 자유는 "스터럽을 아낄 자유"가
        > 아니라 **"스터럽과 복부 두께를 맞바꿀 자유"**다. $\cot\theta$ 를
        > 키워 스터럽을 줄이면 복부에 더 큰 압축이 걸리므로, 복부가 얇으면
        > 그 자유를 쓸 수 없다.

        **아래 코드가 하는 일** — 복부 두께를 바꿔 가며 쓸 수 있는
        $\cot\theta$ 의 한계를 본다.
        """),
        code(r'''
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.4))

        cots = np.linspace(1.0, 2.5, 60)
        v_sd_c = [shear_reinforcement_strength(f_vy=F_VY, a_v=STIRRUP_AREA,
                                               d=D_P, s=150.0, cot_theta=c) / 1e3
                  for c in cots]
        v_max_c = [max_shear_strength(fck=FCK, b_w=B_W, d=D_P,
                                      cot_theta=c) / 1e3 for c in cots]

        ax1.plot(cots, v_sd_c, color=C_STEEL, lw=2.2, label="V_sd (스터럽)")
        ax1.plot(cots, v_max_c, color=C_LOAD, lw=2.2, label="V_d,max (스트럿)")
        ax1.fill_between(cots, 0, np.minimum(v_sd_c, v_max_c),
                         color=C_CAP if False else "#1f7a4d", alpha=0.10,
                         label="실제 저항")
        if cross:
            ax1.axvline(cross, color=C_MUTED, ls=":", lw=1.4)
            ax1.annotate(f"교차 {cross:.2f}", (cross, max(v_max_c) * 0.95),
                         ha="center", fontsize=9, color=C_MUTED)
        ax1.set_xlabel("cot θ")
        ax1.set_ylabel("전단강도 (kN)")
        ax1.set_title("cot θ 를 키우면 스트럿이 먼저 걸린다")
        ax1.legend(fontsize=9)
        ax1.grid(alpha=0.3)

        # 복부 두께에 따른 V_d,max
        for bw, colour in [(240.0, "#c0392b"), (290.0, "#1f6feb"),
                           (400.0, "#1f7a4d")]:
            v = [max_shear_strength(fck=FCK, b_w=bw, d=D_P, cot_theta=c) / 1e3
                 for c in cots]
            ax2.plot(cots, v, lw=2.0, color=colour, label=f"b_w = {bw:.0f} mm")
        ax2.plot(cots, v_sd_c, color=C_MUTED, lw=2.0, ls="--",
                 label="V_sd (D13@150)")
        ax2.set_xlabel("cot θ")
        ax2.set_ylabel("V_d,max (kN)")
        ax2.set_title("복부가 얇으면 cot θ 를 쓸 수 없다")
        ax2.legend(fontsize=8.5)
        ax2.grid(alpha=0.3)

        fig.tight_layout()
        '''),

        md(r"""
        ## 3. 어디가 지배하는가 — 휨과 정반대다

        단순 지지 보에서 휨모멘트는 **중앙**에서 최대이고 전단력은
        **지점**에서 최대다. 그래서 같은 거더인데 **설계를 지배하는 위치가
        정반대**다.

        **아래 코드가 하는 일** — 지간을 따라 $V_{Ed}$ 와 $V_{cd}$ 를 그려
        스터럽이 필요한 구간을 찾는다.
        """),
        code(r'''
        print(f"{'위치 (m)':>9} {'V_Ed (kN)':>11} {'V_cd (kN)':>11} {'스터럽':>9}")
        print("-" * 44)
        for x in (0.0, 1.0, 2.0, 3.0, 5.0, 7.5, 10.0, 12.0, 15.0):
            v = v_ed(x)
            print(f"{x:9.1f} {v:11.0f} {v_cd:11.1f} "
                  f"{'필요' if v > v_cd else '불필요':>9}")

        # 스터럽이 필요 없어지는 위치
        xs = np.linspace(0, SPAN / 2, 400)
        vs = np.array([v_ed(float(x)) for x in xs])
        idx = np.argmax(vs <= v_cd)
        x_free = float(xs[idx]) if vs[idx] <= v_cd else None
        print()
        if x_free:
            print(f"x ≈ {x_free:.1f} m 부터 계산상 스터럽이 필요 없다 "
                  f"(지간의 {x_free / SPAN * 100:.0f} %).")
            print("다만 '필요 없다'와 '넣지 않는다'는 다르다 — 5절을 볼 것.")
        '''),
        code(r'''
        fig, ax = plt.subplots(figsize=(10, 4.4))

        ax.plot(xs, vs, color=C_LOAD, lw=2.4, label="V_Ed (극한Ⅰ)")
        ax.axhline(v_cd, color=C_CONC, lw=2.2, label=f"V_cd = {v_cd:.0f} kN")
        ax.fill_between(xs, v_cd, vs, where=(vs > v_cd), color=C_LOAD,
                        alpha=0.14, label="스터럽이 받아야 할 몫")
        if x_free:
            ax.axvline(x_free, color=C_MUTED, ls=":", lw=1.4)
            ax.annotate(f"x = {x_free:.1f} m", (x_free, vs.max() * 0.9),
                        ha="center", fontsize=9, color=C_MUTED)

        # 참고 — 휨모멘트는 반대로 중앙이 최대다
        ax2 = ax.twinx()
        m = [1.25 * W_TOTAL * x * (SPAN - x) / 2
             + 1.80 * girder_live_load(span=SPAN).moment * 0.6
             * (4 * x * (SPAN - x) / SPAN**2) for x in xs]
        ax2.plot(xs, m, color=C_MUTED, lw=1.6, ls="--", alpha=0.75,
                 label="M_Ed (참고, 오른쪽 축)")
        ax2.set_ylabel("휨모멘트 (kN·m)", color=C_MUTED)
        ax2.tick_params(axis="y", labelcolor=C_MUTED)

        ax.set_xlabel("지점에서의 거리 (m)")
        ax.set_ylabel("전단력 (kN)")
        ax.set_title("전단은 지점이, 휨은 중앙이 지배한다")
        ax.set_xlim(0, SPAN / 2)
        ax.set_ylim(0, vs.max() * 1.1)
        ax.legend(loc="upper right", fontsize=9)
        ax.grid(alpha=0.3)
        fig.tight_layout()
        '''),

        md(r"""
        **읽는 법** — 두 곡선이 정확히 반대로 간다. 붉은 영역이 스터럽이
        받아야 할 몫이고, 지간의 약 30 % 구간에만 나타난다.

        이것이 PSC 거더의 배근이 **단부에 촘촘하고 중앙에 성긴** 이유다.
        그리고 L6 에서 본 대로 **텐던은 반대로** 중앙에서 편심이 크고 단부에서
        핵 안으로 들어온다. 두 배근이 서로 어긋나 있는 셈이다.

        ## 4. 스터럽 배치

        **아래 코드가 하는 일** — 위치별로 필요한 스터럽 간격을 구하고,
        최소 전단철근·최대 간격 규정과 견주어 채택값을 정한다.
        """),
        code(r'''
        s_max = maximum_stirrup_spacing(d=D_P)
        rho_min = minimum_shear_reinforcement_ratio(fck=FCK, f_y=F_VY)
        s_rho = STIRRUP_AREA / (rho_min * B_W)

        print(f"최대 간격 규정        {s_max:.0f} mm")
        print(f"최소 전단철근비       {rho_min * 100:.3f} %  ->  간격 {s_rho:.0f} mm 이하")
        print(f"실제 상한 = min       {min(s_max, s_rho):.0f} mm")
        print()
        print(f"{'위치':>6} {'V_Ed':>8} {'V_sd 소요':>10} {'필요 간격':>10} "
              f"{'채택':>8}")
        print("-" * 48)
        layout = []
        for x in (0, 1, 2, 3, 4, 5, 7.5, 10, 12, 15):
            v = v_ed(float(x))
            need = v - v_cd
            if need <= 0:
                s_adopt = min(s_max, s_rho)
                print(f"{x:6.1f} {v:8.0f} {'-':>10} {'불필요':>10} "
                      f"{s_adopt:8.0f}")
            else:
                s_req = required_stirrup_spacing(
                    v_ed=need * 1e3, d=D_P, a_v=STIRRUP_AREA,
                    cot_theta=COT_THETA)
                s_adopt = min(s_req, s_max, s_rho)
                print(f"{x:6.1f} {v:8.0f} {need:10.0f} {s_req:10.0f} "
                      f"{s_adopt:8.0f}")
            layout.append((x, s_adopt))
        '''),

        md(r"""
        **읽는 법** — 지점에서 약 510 mm, 중앙부에서는 **최소 전단철근이
        정하는 691 mm** 다. 계산상 필요 없는 구간에서도 간격의 상한이 걸리는
        것이다.

        ## 5. "필요 없다"와 "넣지 않는다"는 다르다

        3절에서 지간의 70 % 는 계산상 스터럽이 필요 없다고 나왔다. 그렇다고
        정말 안 넣지는 않는다. 기준이 **최소 전단철근**을 요구하기 때문이다.

        이유는 전단 파괴의 성격에 있다. 휨 파괴는 철근이 항복하며 처짐이
        크게 자라 **예고**가 있지만, 전단 파괴는 사인장균열이 갑자기 열리며
        **예고 없이** 온다. $V_{cd}$ 식 자체가 실험의 회귀식이라 흩어짐도 크다.

        > **설계의 의도** — 최소 전단철근은 강도를 위한 것이 아니라 **취성
        > 파괴를 막기 위한 것**이다. $V_{Ed}$ 가 $V_{cd}$ 보다 작아도, 계산이
        > 빗나갔을 때 부재가 조용히 무너지지 않도록 붙잡아 둔다.

        ## 6. KDS 14 로 풀면

        같은 단면을 강도설계법으로 풀면 얼마나 다른가?

        **아래 코드가 하는 일** — KDS 14 20 22 의 $V_c$ 와 견준다. KDS 14 는
        프리스트레스를 $V_c$ 식에 다른 방식으로 반영하므로, 여기서는
        **전단철근이 없을 때의 콘크리트 몫**만 형식적으로 견준다.
        """),
        code(r'''
        # KDS 14 — 간이식 V_c = (1/6) sqrt(f_ck) b_w d, phi = 0.75
        v_c_14 = 0.75 * (1 / 6) * math.sqrt(FCK) * B_W * D_P / 1e3

        print(f"KDS 14  φV_c = 0.75 x (1/6)√f_ck b_w d = {v_c_14:7.1f} kN")
        print(f"KDS 24  V_cd (f_n = 0)                 = {v_cd_0:7.1f} kN")
        print(f"KDS 24  V_cd (f_n = {F_N:.2f})              = {v_cd:7.1f} kN")
        print()
        print(f"프리스트레스를 빼면 KDS 24 가 KDS 14 의 "
              f"{v_cd_0 / v_c_14 * 100:.0f} % 로 낮고,")
        print(f"넣으면 {v_cd / v_c_14 * 100:.0f} % 로 뒤집힌다.")
        print()
        print("KDS 14 의 간이식은 f_ck 만 보고 철근비도 축응력도 보지 않는다.")
        print("KDS 24 는 ρ 와 f_n 을 모두 넣어 부재의 조건을 반영한다.")
        '''),

        md(r"""
        **읽는 법** — 프리스트레스를 무시하면 KDS 24 가 더 보수적인데,
        반영하면 뒤집힌다. **PSC 부재에서 두 기준의 차이는 축응력 항이
        만든다.**

        (KDS 14 20 60 은 PSC 부재에 대해 $V_{ci}$ / $V_{cw}$ 를 따로 두는
        상세식을 갖고 있다. 위 비교는 간이식만 형식적으로 견준 것이므로
        실제 KDS 14 설계값과는 다르다.)

        ## 7. 바꿔 보며 확인할 것

        1. `B_W` 를 240 mm(EX거더 최소 복부두께)로 줄이면 쓸 수 있는
           $\cot\theta$ 의 상한이 얼마나 내려가는가?
        2. `COT_THETA` 를 2.5 로 올리면 스터럽 간격이 얼마나 벌어지는가?
           그때 $V_{d,\max}$ 가 $V_{Ed}$ 를 여전히 넘는가?
        3. `STIRRUP_AREA` 를 D16 2가닥으로 올리면 지점부 간격이 얼마가 되는가?
        4. `N_STRAND` 를 줄여 $f_n$ 을 낮추면 스터럽이 필요한 구간이
           얼마나 길어지는가?

        ## 8. 정리

        1. **프리스트레스는 전단강도에 직접 들어간다.** 식 $(4.1\text{-}7)$ 의
           $0.15 f_n$ 항이 이 거더에서 $V_{cd}$ 를 **61 % 올린다.** 휨에서는
           없던 효과다.
        2. **$f_n$ 은 유효 프리스트레스로 계산해야 한다.** 손실 21 % 를
           빠뜨리면 전단강도를 과대평가한다.
        3. **$\cot\theta$ 는 공짜가 아니다.** 키우면 스터럽이 줄지만 스트럿
           압축이 커져, 어느 지점을 넘으면 스트럿이 먼저 부서진다.
           복부가 얇을수록 그 지점이 빨리 온다.
        4. **전단은 지점이, 휨은 중앙이 지배한다.** 스터럽은 단부에 촘촘하고
           텐던 편심은 중앙에서 크다 — 두 배근이 서로 어긋난다.
        5. **계산상 필요 없어도 최소 전단철근은 넣는다.** 전단 파괴는 예고가
           없기 때문이다.

        ## 9. 생각해 볼 문제

        1. $V_{cd}$ 식의 $f_n$ 항은 축압축이 클수록 무한정 커지는가? 기준이
           상한을 두는 이유는 무엇일까?
        2. 텐던을 드레이프하면 단부에서 텐던이 위로 올라간다. 이때 텐던의
           **수직 성분**이 전단력을 직접 덜어 준다. 이 강의는 그 효과를
           넣지 않았는데, 넣으면 결과가 어떻게 달라지겠는가?
        3. 최소 전단철근이 취성 파괴를 막기 위한 것이라면, 그 양은 무엇을
           기준으로 정해야 하는가? 현재 규정은 $f_{ck}$ 와 $f_y$ 만 본다.
        4. 합성 거더에서 바닥판과 거더 사이의 **수평전단**은 이 강의가 다루지
           않았다. 그 검토가 왜 따로 필요한가?
        5. 지점 근처에서는 하중이 스트럿을 통해 지점으로 직접 흐른다
           (아치작용). 기준이 지점에서 $d$ 이내를 달리 취급하는 근거는
           무엇인가?
        """),
    ], directory=LECTURES)


BUILDERS = [
    nb_l1_block,
    nb_l2_phi,
    nb_l3_params,
    nb_l4_deck_interior,
    nb_l5_deck_cantilever,
    nb_l6_girder_flexure,
    nb_l7_girder_shear,
]


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
