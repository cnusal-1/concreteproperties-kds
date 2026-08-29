"""대화형 탐색기(`docs/_static/explorer.html`)에 넣을 값을 미리 계산한다.

문서 사이트는 정적 HTML 이라 브라우저에서 파이썬을 돌릴 수 없다. 그래서
매개변수 격자 위의 해석 결과를 여기서 미리 구해 JSON 으로 굳혀 두고, 페이지는
슬라이더를 움직일 때 그 값을 꺼내 쓰기만 한다.

격자를 넓히려면 아래 상수를 고치고 다시 실행한다.
"""

from __future__ import annotations

import json
from pathlib import Path

from concreteproperties import ConcreteSection
from sectionproperties.pre.library import (
    concrete_rectangular_section,
    concrete_tee_section,
)

from concreteproperties_kds import KDS, stress_block_parameters

ROOT = Path(__file__).resolve().parents[1]

# ── 격자 ──────────────────────────────────────────────────────────────────
COL_FCK = [21, 24, 27, 30, 35, 40, 50, 60, 70, 80]
COL_FY = [300, 400, 500, 600]
COL_TYPES = ["tie", "spiral"]
COL_POINTS = 32

BEAM_FCK = [21, 24, 27, 30, 35, 40, 50, 60]
BEAM_FY = [300, 400, 500, 600]
BEAM_NBAR = [2, 3, 4, 5, 6, 7, 8, 9, 10]

# 플랜지를 좁고 얇게 두어야 압축블록이 플랜지를 넘는 경우를 볼 수 있다
TEE_BF = 700.0
TEE_HF = [70, 90, 110, 150]
TEE_NBAR = [4, 6, 8, 10]
TEE_FCK = [24, 27, 35, 40]

# L1 탭 — 등가블록과 포물선-직선을 같은 축력에서 비교한다
PARA_FY = [400, 500]
PARA_STEPS = 13

# L3 탭 — 단면 깊이를 바꿔 가며 보는 민감도
BEAM_D = [450, 500, 550, 600, 650, 700, 750, 800]

D22 = 387.1  # D22 공칭 단면적 (mm^2)
DIA22 = 22.0


def _round(x, n=2):
    """JSON 크기를 줄이기 위해 반올림한다."""
    return None if x is None else round(float(x), n)


def _effective_depth(conc_sec) -> float:
    """단면 상단에서 최하단 철근 도심까지의 거리를 구한다."""
    top = conc_sec.compound_geometry.geom.bounds[3]
    bars = [g.calculate_centroid()[1] for g in conc_sec.reinf_geometries_lumped]
    return top - min(bars)


# ── 기둥 ──────────────────────────────────────────────────────────────────
def column(fck: float, fy: float, column_type: str):
    """500 x 500 기둥 (8-D22, 피복 50 mm)."""
    kds = KDS(column_type=column_type)
    conc = kds.create_concrete_material(compressive_strength=fck)
    steel = kds.create_steel_material(yield_strength=fy)
    geom = concrete_rectangular_section(
        d=500, b=500,
        dia_top=DIA22, area_top=D22, n_top=3, c_top=50,
        dia_bot=DIA22, area_bot=D22, n_bot=3, c_bot=50,
        dia_side=DIA22, area_side=D22, n_side=1, c_side=50,
        n_circle=16, conc_mat=conc, steel_mat=steel,
    )
    kds.assign_concrete_section(ConcreteSection(geom))
    return kds


def column_case(fck, fy, column_type):
    """기둥 하나의 P-M 상관도와 점별 분류를 계산한다."""
    kds = column(fck, fy, column_type)
    f_mi, mi, phis = kds.moment_interaction_diagram(
        n_points=COL_POINTS, progress_bar=False
    )
    n_max_nom, n_max_des = kds.max_axial_strength()

    pts = []
    for r_u, r_f, phi in zip(mi.results, f_mi.results, phis, strict=True):
        eps_t = kds.net_tensile_strain(theta=0, d_n=r_u.d_n)
        pts.append([
            _round(r_u.m_x / 1e6, 1), _round(r_u.n / 1e3, 1),
            _round(r_f.m_x / 1e6, 1), _round(r_f.n / 1e3, 1),
            _round(phi, 4),
            None if eps_t == float("inf") else _round(eps_t, 6),
        ])

    return {
        "epsY": _round(kds.eps_y, 6),
        "epsTl": _round(kds.eps_tl, 6),
        "phiComp": _round(kds.phi_comp, 3),
        "alphaMax": _round(kds.alpha_max, 3),
        "nMaxNom": _round(n_max_nom / 1e3, 1),
        "nMaxDes": _round(n_max_des / 1e3, 1),
        "squash": _round(kds.squash_load / 1e3, 1),
        "tensile": _round(kds.tensile_load / 1e3, 1),
        "pts": pts,
    }


# ── 직사각형 보 (단철근) ──────────────────────────────────────────────────
def beam(fck, fy, n_bar):
    """400 x 600 단철근 보. 압축철근을 두지 않아 손계산과 조건이 같다."""
    kds = KDS()
    conc = kds.create_concrete_material(compressive_strength=fck)
    steel = kds.create_steel_material(yield_strength=fy)
    geom = concrete_rectangular_section(
        d=600, b=400,
        dia_top=DIA22, area_top=D22, n_top=0, c_top=50,
        dia_bot=DIA22, area_bot=D22, n_bot=n_bar, c_bot=50,
        n_circle=16, conc_mat=conc, steel_mat=steel,
    )
    kds.assign_concrete_section(ConcreteSection(geom))
    return kds


def hand_rectangular(fck, fy, a_s, b, d):
    """등가직사각형 응력블록 손계산 (단철근 직사각형).

    Returns:
        (a, c, eps_t, m_n) — 압축블록 깊이, 중립축, 순인장변형률, 공칭휨강도
    """
    eps_cu, eta, beta_1 = stress_block_parameters(fck)
    a = a_s * fy / (eta * 0.85 * fck * b)
    c = a / beta_1
    eps_t = eps_cu * (d - c) / c
    m_n = a_s * fy * (d - a / 2)
    return a, c, eps_t, m_n


def beam_case(fck, fy, n_bar):
    """보 하나에 대해 손계산과 섬유해석을 나란히 계산한다."""
    kds = beam(fck, fy, n_bar)
    conc_sec = kds.concrete_section
    d = _effective_depth(conc_sec)
    a_s = n_bar * D22
    b = 400.0

    a, c, eps_t_hand, m_n_hand = hand_rectangular(fck, fy, a_s, b, d)
    phi_hand = kds.capacity_reduction_factor(eps_t_hand)

    f_res, u_res, phi = kds.ultimate_bending_capacity()
    eps_t = kds.net_tensile_strain(theta=0, d_n=u_res.d_n)

    gross = kds.get_gross_properties()
    cracked = kds.calculate_cracked_properties()

    return {
        "d": _round(d, 1),
        "As": _round(a_s, 0),
        "rho": _round(a_s / (b * d), 5),
        "a": _round(a, 1),
        "cHand": _round(c, 1),
        "dnFiber": _round(u_res.d_n, 1),
        "epsTHand": _round(eps_t_hand, 6),
        "epsT": _round(eps_t, 6),
        "phiHand": _round(phi_hand, 4),
        "phi": _round(phi, 4),
        "mnHand": _round(m_n_hand / 1e6, 1),
        "mn": _round(u_res.m_x / 1e6, 1),
        "phiMnHand": _round(phi_hand * m_n_hand / 1e6, 1),
        "phiMn": _round(f_res.m_x / 1e6, 1),
        "cls": kds.section_classification(eps_t),
        "mcr": _round(cracked.m_cr / 1e6, 1),
        "icrRatio": _round(cracked.e_ixx_c_cr / gross.e_ixx_c, 4),
    }


# ── T형보 ─────────────────────────────────────────────────────────────────
def tee(fck, fy, h_f, n_bar):
    """T형보 — 플랜지 700 x h_f, 복부 400, 전체 깊이 600."""
    kds = KDS()
    conc = kds.create_concrete_material(compressive_strength=fck)
    steel = kds.create_steel_material(yield_strength=fy)
    geom = concrete_tee_section(
        d=600, b=400, d_f=h_f, b_f=TEE_BF,
        dia_top=DIA22, area_top=D22, n_top=0, c_top=50,
        dia_bot=DIA22, area_bot=D22, n_bot=n_bar, c_bot=50,
        n_circle=16, conc_mat=conc, steel_mat=steel,
    )
    kds.assign_concrete_section(ConcreteSection(geom))
    return kds


def hand_tee(fck, fy, a_s, b_w, b_f, h_f, d):
    """T형보 손계산. 압축블록이 플랜지를 넘어가면 플랜지와 복부로 나눈다.

    Returns:
        (a, eps_t, m_n, in_flange)
    """
    eps_cu, eta, beta_1 = stress_block_parameters(fck)
    fc = eta * 0.85 * fck

    a = a_s * fy / (fc * b_f)
    if a <= h_f:
        c = a / beta_1
        return a, eps_cu * (d - c) / c, a_s * fy * (d - a / 2), True

    a_sf = fc * (b_f - b_w) * h_f / fy
    a_w = (a_s - a_sf) * fy / (fc * b_w)
    a = a_w
    c = a / beta_1
    m_n = a_sf * fy * (d - h_f / 2) + (a_s - a_sf) * fy * (d - a_w / 2)
    return a, eps_cu * (d - c) / c, m_n, False


def tee_case(fck, fy, h_f, n_bar):
    """T형보 하나에 대해 손계산과 섬유해석을 나란히 계산한다."""
    kds = tee(fck, fy, h_f, n_bar)
    d = _effective_depth(kds.concrete_section)
    a_s = n_bar * D22

    a, eps_t_hand, m_n_hand, in_flange = hand_tee(fck, fy, a_s, 400.0, TEE_BF, h_f, d)
    phi_hand = kds.capacity_reduction_factor(eps_t_hand)

    # 압축블록이 플랜지를 넘는지 확인하지 않고 직사각형으로 푼 경우 (흔한 오류)
    a_w, _, eps_w, m_n_wrong = hand_rectangular(fck, fy, a_s, TEE_BF, d)

    f_res, u_res, phi = kds.ultimate_bending_capacity()
    eps_t = kds.net_tensile_strain(theta=0, d_n=u_res.d_n)

    return {
        "d": _round(d, 1),
        "As": _round(a_s, 0),
        "a": _round(a, 1),
        "inFlange": in_flange,
        "epsTHand": _round(eps_t_hand, 6),
        "epsT": _round(eps_t, 6),
        "phiHand": _round(phi_hand, 4),
        "phi": _round(phi, 4),
        "mnHand": _round(m_n_hand / 1e6, 1),
        "mn": _round(u_res.m_x / 1e6, 1),
        "phiMnHand": _round(phi_hand * m_n_hand / 1e6, 1),
        "phiMn": _round(f_res.m_x / 1e6, 1),
        "cls": kds.section_classification(eps_t),
        "mnWrong": _round(m_n_wrong / 1e6, 1),
        "aWrong": _round(a_w, 1),
    }


# ── L1 · 등가블록 vs 포물선-직선 ──────────────────────────────────────────
def column_profile(fck, fy, profile):
    """500 x 500 띠철근 기둥을 지정한 극한 응력-변형률 관계로 만든다."""
    kds = KDS()
    conc = kds.create_concrete_material(
        compressive_strength=fck, ultimate_profile=profile
    )
    steel = kds.create_steel_material(yield_strength=fy)
    geom = concrete_rectangular_section(
        d=500, b=500,
        dia_top=DIA22, area_top=D22, n_top=3, c_top=50,
        dia_bot=DIA22, area_bot=D22, n_bot=3, c_bot=50,
        dia_side=DIA22, area_side=D22, n_side=1, c_side=50,
        n_circle=16, conc_mat=conc, steel_mat=steel,
    )
    kds.assign_concrete_section(ConcreteSection(geom))
    return kds


def parabolic_case(fck, fy):
    """같은 축력에서 두 관계의 휨강도를 나란히 구한다.

    상관도 생성은 두 관계가 서로 다른 제어점을 잡으므로, 축력을 직접 지정해
    같은 조건에서 비교한다.
    """
    blk = column_profile(fck, fy, "block")
    par = column_profile(fck, fy, "parabolic")

    n_top = min(blk.squash_load, par.squash_load) * 0.82
    pts = []
    for i in range(PARA_STEPS):
        n_d = n_top * i / (PARA_STEPS - 1)
        try:
            m_b = blk.ultimate_bending_capacity(n_design=n_d)[1].m_x
            m_p = par.ultimate_bending_capacity(n_design=n_d)[1].m_x
        except Exception:  # noqa: BLE001 - 축강도를 넘는 점은 건너뛴다
            continue
        pts.append([_round(n_d / 1e3, 1), _round(m_b / 1e6, 1), _round(m_p / 1e6, 1)])

    return {"pts": pts}


# ── L3 · 단면 깊이 ────────────────────────────────────────────────────────
def depth_case(fck, fy, n_bar, d):
    """깊이를 바꾼 보의 설계휨강도와 변형률만 가볍게 구한다."""
    kds = beam_depth(fck, fy, n_bar, d)
    f_res, u_res, phi = kds.ultimate_bending_capacity()
    eps_t = kds.net_tensile_strain(theta=0, d_n=u_res.d_n)

    return {
        "dEff": _round(_effective_depth(kds.concrete_section), 1),
        "epsT": _round(eps_t, 6),
        "phi": _round(phi, 4),
        "mn": _round(u_res.m_x / 1e6, 1),
        "phiMn": _round(f_res.m_x / 1e6, 1),
        "cls": kds.section_classification(eps_t),
    }


def beam_depth(fck, fy, n_bar, d):
    """깊이 d 의 단철근 보."""
    kds = KDS()
    conc = kds.create_concrete_material(compressive_strength=fck)
    steel = kds.create_steel_material(yield_strength=fy)
    geom = concrete_rectangular_section(
        d=d, b=400,
        dia_top=DIA22, area_top=D22, n_top=0, c_top=50,
        dia_bot=DIA22, area_bot=D22, n_bot=n_bar, c_bot=50,
        n_circle=16, conc_mat=conc, steel_mat=steel,
    )
    kds.assign_concrete_section(ConcreteSection(geom))
    return kds


def build() -> dict:
    """격자 전체를 계산해 하나의 사전으로 만든다."""
    data = {
        "columns": {"fck": COL_FCK, "fy": COL_FY, "types": COL_TYPES, "cases": {}},
        "beams": {"fck": BEAM_FCK, "fy": BEAM_FY, "nbar": BEAM_NBAR, "cases": {}},
        "tees": {"fck": TEE_FCK, "hf": TEE_HF, "nbar": TEE_NBAR, "cases": {}},
        "para": {"fck": COL_FCK, "fy": PARA_FY, "cases": {}},
        "depths": {"d": BEAM_D, "cases": {}},
    }

    total = len(COL_FCK) * len(COL_FY) * len(COL_TYPES)
    done = 0
    for fck in COL_FCK:
        for fy in COL_FY:
            for t in COL_TYPES:
                data["columns"]["cases"][f"{fck}|{fy}|{t}"] = column_case(fck, fy, t)
                done += 1
        print(f"  기둥 {done}/{total}", flush=True)

    total = len(BEAM_FCK) * len(BEAM_FY) * len(BEAM_NBAR)
    done = 0
    for fck in BEAM_FCK:
        for fy in BEAM_FY:
            for n in BEAM_NBAR:
                data["beams"]["cases"][f"{fck}|{fy}|{n}"] = beam_case(fck, fy, n)
                done += 1
        print(f"  보 {done}/{total}", flush=True)

    for fck in TEE_FCK:
        for h_f in TEE_HF:
            for n in TEE_NBAR:
                key = f"{fck}|400|{h_f}|{n}"
                data["tees"]["cases"][key] = tee_case(fck, 400, h_f, n)
    print("  T형보 완료", flush=True)

    for fck in COL_FCK:
        for fy in PARA_FY:
            data["para"]["cases"][f"{fck}|{fy}"] = parabolic_case(fck, fy)
    print("  포물선 대조 완료", flush=True)

    total = len(BEAM_FCK) * len(BEAM_FY) * len(BEAM_NBAR) * len(BEAM_D)
    done = 0
    for fck in BEAM_FCK:
        for fy in BEAM_FY:
            for n in BEAM_NBAR:
                for d in BEAM_D:
                    key = f"{fck}|{fy}|{n}|{d}"
                    data["depths"]["cases"][key] = depth_case(fck, fy, n, d)
                    done += 1
        print(f"  깊이 {done}/{total}", flush=True)

    return data


if __name__ == "__main__":
    out = ROOT / "scripts" / "explorer_data.json"
    out.write_text(json.dumps(build(), ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    print(f"저장 {out}  ({out.stat().st_size / 1024:.0f} KB)")
