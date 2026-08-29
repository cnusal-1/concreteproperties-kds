"""예제 17 - 교량 바닥판 설계 (KDS 24 한계상태설계법).

PSC 거더교의 콘크리트 바닥판을 내측부와 캔틸레버부로 나누어 설계한다.
거더는 KL-510 트럭을 굴려 풀지만 바닥판은 기준이 주는 근사식으로 끝난다.

    ① 교량 제원과 노출환경    KDS 24 12 21 4.3.1.1
    ② 두께와 피복             KDS 24 14 21 4.6.5.1, 4.4.4
    ③ 내측부 하중             KDS 24 10 11 4.6.2.4, 4.6.2.7
    ④ 하중조합                KDS 24 12 11 표 4.1-1
    ⑤ 내측부 휨 설계          KDS 24 14 21 4.1.1
    ⑥ 캔틸레버부              KDS 24 10 11 4.6.2.5
    ⑦ 배력철근                KDS 24 14 21 4.6.5.3(2)
    ⑧ 사용성                  KDS 24 14 21 4.2
    ⑨ KDS 14 대조

실행:
    python 17_바닥판설계.py
"""

from __future__ import annotations

import math

from concreteproperties_kds.kds import stress_block_parameters
from concreteproperties_kds.kds24 import (
    BAR_SPACING_MAX,
    BAR_SPACING_MIN,
    COMBINATIONS_BY_NAME,
    MIN_THICKNESS_RC,
    bar_area,
    cantilever_live_load_moment,
    cantilever_wheel_width,
    dead_load_moment,
    deck_deflection_limit,
    deck_span,
    design_compressive_strength,
    design_deck,
    design_yield_strength,
    distribution_steel_ratio,
    equivalent_block,
    impact_factor,
    lane_width,
    live_load_moment,
    max_bar_diameter,
    max_bar_spacing,
    minimum_flexural_steel,
    nominal_cover,
    number_of_lanes,
    provided_steel_area,
    required_steel_area,
)

# ── 교량 제원 ──────────────────────────────────────────────────────────────
TOTAL_WIDTH = 12.6  # 총 폭 (m)
ROADWAY_WIDTH = 11.2  # 연석·방호울타리 사이 교폭 W_C (m)
PLAN_LANE = 3.5  # 계획차로의 폭 W_P (m)
N_GIRDER = 5
GIRDER_SPACING = 2.5  # 거더 중심 간격 (m)
CANTILEVER = 1.3  # 캔틸레버 길이 (m)

FCK, FY = 27.0, 400.0  # KDS 24 10 11 4.6.2.2(2) 는 바닥판을 27 MPa 로 정한다
EXPOSURE = "ED1"  # 제설염에 노출되는 고속도로 바닥판
PAVEMENT = 80.0  # 포장 두께 (mm)

GAMMA_C, GAMMA_P = 24.5, 22.5  # 콘크리트·포장 단위중량 (kN/m³)
BARRIER_LOAD = 8.0  # 콘크리트 방호벽 자중 (kN/m)
BARRIER_ARM = 0.25  # 방호벽 도심의 캔틸레버 끝단으로부터의 거리 (m)

THICKNESS = 240.0  # 내측부 바닥판 두께 (mm)
HAUNCH = 280.0  # 캔틸레버 고정단의 헌치 포함 두께 (mm)


def rule(title: str) -> None:
    """구분선과 제목을 출력한다."""
    print(f"\n{title}")
    print("-" * 78)


def flexural_capacity(a_s: float, d: float, fck: float = FCK, fy: float = FY) -> float:
    """배치 철근량으로 설계휨강도를 구한다 (kN·m/m).

    Args:
        a_s: 철근량 (mm²/m)
        d: 유효깊이 (mm)
        fck: 콘크리트 기준압축강도 (MPa)
        fy: 철근의 기준항복강도 (MPa)

    Returns:
        설계휨강도 (kN·m/m)
    """
    f_cd = design_compressive_strength(fck=fck)
    f_yd = design_yield_strength(fy=fy)
    alpha, beta = equivalent_block(fck=fck)
    c = a_s * f_yd / (alpha * f_cd * 1000.0)

    return a_s * f_yd * (d - beta * c) / 1e6


def steel_stress(m_service: float, a_s: float, d: float, n_ratio: float = 7.0) -> float:
    """균열단면의 철근 인장응력을 구한다 (MPa).

    Args:
        m_service: 사용하중 휨모멘트 (kN·m/m)
        a_s: 철근량 (mm²/m)
        d: 유효깊이 (mm)
        n_ratio: 탄성계수비. 기본값 ``7.0``.

    Returns:
        철근 인장응력 (MPa)
    """
    rho = a_s / (1000.0 * d)
    k = math.sqrt((n_ratio * rho) ** 2 + 2 * n_ratio * rho) - n_ratio * rho

    return m_service * 1e6 / (a_s * (1.0 - k / 3.0) * d)


def required_steel_kds14(m_u: float, d: float, phi: float = 0.85) -> float:
    """같은 설계휨모멘트를 KDS 14 강도설계법으로 풀어 필요 철근량을 구한다.

    Args:
        m_u: 소요 휨강도 (N·mm)
        d: 유효깊이 (mm)
        phi: 강도감소계수. 기본값 ``0.85`` (인장지배단면).

    Raises:
        ValueError: 단철근으로 저항할 수 없는 경우

    Returns:
        필요 철근량 (mm²/m)
    """
    _, eta, _ = stress_block_parameters(fck=FCK)
    k = FY / (eta * 0.85 * FCK * 1000.0)
    a2 = phi * k * FY / 2.0
    a1 = -phi * FY * d
    disc = a1**2 - 4 * a2 * m_u

    if disc < 0:
        msg = "단철근으로는 저항할 수 없다"
        raise ValueError(msg)

    return (-a1 - math.sqrt(disc)) / (2 * a2)


def main() -> None:
    """바닥판 설계 전 과정을 수행한다."""
    print("=" * 78)
    print("예제 17 · 교량 바닥판 설계 (KDS 24 한계상태설계법)")
    print("=" * 78)

    # ── ① 교량 제원 ───────────────────────────────────────────────────────
    rule("① 교량 제원과 재하차로")
    n_lane = number_of_lanes(roadway_width=ROADWAY_WIDTH, plan_lane_width=PLAN_LANE)
    print(f"총 폭                 {TOTAL_WIDTH:.1f} m")
    print(
        f"거더                  {N_GIRDER} 본 @ {GIRDER_SPACING:.1f} m, "
        f"캔틸레버 {CANTILEVER:.1f} m"
    )
    laid = (N_GIRDER - 1) * GIRDER_SPACING + 2 * CANTILEVER
    print(f"배치 검산             {laid:.1f} m")
    print(f"교폭 W_C              {ROADWAY_WIDTH:.1f} m")
    print(f"재하차로 수 N         {n_lane}   (식 (4.3-1))")
    w_lane = lane_width(roadway_width=ROADWAY_WIDTH, n_lanes=n_lane)
    print(f"재하차로 폭 W         {w_lane:.2f} m   (식 (4.3-2))")
    print()
    print("재하차로 수는 거더 설계에 쓴다. 바닥판 근사식(4.6.2.4)에는 다차로")
    print("재하계수를 곱하지 않는다 - 식 자체가 인접 윤하중의 겹침을 이미 담고 있다.")

    # ── ② 두께와 피복 ─────────────────────────────────────────────────────
    rule("② 바닥판 두께와 피복두께")
    span = deck_span(girder_spacing=GIRDER_SPACING, thickness=THICKNESS)
    dia_in, spacing_in = 16.0, 150.0
    t_min, cover = nominal_cover(exposure=EXPOSURE, bar_diameter=dia_in)
    d_in = THICKNESS - cover - dia_in / 2

    print(f"바닥판 지간 L         {span:.2f} m   (4.6.2.3(1))")
    print(
        f"두께 t                {THICKNESS:.0f} mm   "
        f"(최소 {MIN_THICKNESS_RC:.0f} mm, 4.6.5.1(5))"
    )
    print(f"두께 / 지간           1 / {span * 1000 / THICKNESS:.1f}")
    print(f"노출등급              {EXPOSURE}   (제설염)")
    print(f"최소피복 t_c,min      {t_min:.0f} mm   (표 4.4-4)")
    print(f"공칭피복 t_c,nom      {cover:.0f} mm   (+ 설계 편차 10 mm, 식 (4.4-1))")
    print(f"유효깊이 d            {d_in:.0f} mm   (D{dia_in:.0f} 기준)")

    # ── ③ 내측부 하중 ─────────────────────────────────────────────────────
    rule("③ 내측부 하중")
    w_dc = GAMMA_C * THICKNESS / 1000.0
    w_dw = GAMMA_P * PAVEMENT / 1000.0
    m_dc = dead_load_moment(w=w_dc, span=span, kind="연속판_지간")
    m_dw = dead_load_moment(w=w_dw, span=span, kind="연속판_지간")
    m_ll = live_load_moment(span=span, continuous=True)
    m_im = m_ll * (impact_factor() - 1.0)

    print(f"바닥판 자중 DC        {w_dc:5.2f} kN/m²  →  M {m_dc:5.2f} kN·m/m")
    print(f"포장 DW               {w_dw:5.2f} kN/m²  →  M {m_dw:5.2f} kN·m/m")
    print(f"활하중 LL             {m_ll:5.2f} kN·m/m   (식 (4.6-1), 연속 0.8배)")
    print(f"충격 IM               {m_im:5.2f} kN·m/m   (× 1.25, 표 4.4-1)")
    print()
    total = m_dc + m_dw + m_ll + m_im
    print(f"계수 전 합            {total:5.2f} kN·m/m")
    print(f"그중 활하중의 몫       {(m_ll + m_im) / total * 100:.0f} %")

    # ── ④ 하중조합 ────────────────────────────────────────────────────────
    rule("④ 하중조합 (KDS 24 12 11 표 4.1-1)")
    loads = {"DC": m_dc, "DW": m_dw, "LL": m_ll, "IM": m_im}
    m_ed = COMBINATIONS_BY_NAME["극한Ⅰ"].evaluate(loads=loads)
    m_ser = COMBINATIONS_BY_NAME["사용Ⅰ"].evaluate(loads=loads)

    print(f"극한Ⅰ   1.25 DC + 1.50 DW + 1.80 (LL+IM) = {m_ed:6.2f} kN·m/m")
    print(f"사용Ⅰ   1.00 DC + 1.00 DW + 1.00 (LL+IM) = {m_ser:6.2f} kN·m/m")

    # ── ⑤ 내측부 휨 설계 ──────────────────────────────────────────────────
    rule("⑤ 내측부 휨 설계")
    as_req = required_steel_area(m_ed=m_ed * 1e6, d=d_in)
    as_min = minimum_flexural_steel(d=d_in)
    as_prov = provided_steel_area(diameter=dia_in, spacing=spacing_in)
    m_rd = flexural_capacity(a_s=as_prov, d=d_in)

    print(
        f"f_cd                  {design_compressive_strength(fck=FCK):.2f} MPa   "
        f"(0.65 × 0.85 × {FCK:.0f})"
    )
    print(
        f"f_yd                  {design_yield_strength(fy=FY):.1f} MPa   "
        f"(0.90 × {FY:.0f})"
    )
    print(f"필요 철근량 As,req    {as_req:6.0f} mm²/m")
    print(f"최소 철근량 As,min    {as_min:6.0f} mm²/m   (식 (4.6-1), (4.6-2))")
    print(f"배치  D{dia_in:.0f}@{spacing_in:.0f}          {as_prov:6.0f} mm²/m")
    print(f"설계휨강도 M_Rd       {m_rd:6.2f} kN·m/m   → M_Rd/M_Ed = {m_rd / m_ed:.2f}")

    # ── ⑥ 캔틸레버부 ──────────────────────────────────────────────────────
    rule("⑥ 캔틸레버부 (헌치 포함)")
    x_wheel = CANTILEVER - 0.3  # 최외측 차륜은 차도 끝에서 300 mm (4.6.2.3(3)⑤)
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
    m_rd_c = flexural_capacity(a_s=as_prov_c, d=d_c)

    print(f"윤하중 위치 X         {x_wheel:.2f} m   (차도 끝에서 300 mm)")
    print(f"분포폭 E              {e_width:.2f} m   (식 (4.6-4))")
    print(f"고정단 두께           {HAUNCH:.0f} mm (헌치),  d = {d_c:.0f} mm")
    print()
    print(f"자중 + 방호벽 DC      {m_dc_c:6.2f} kN·m/m")
    print(f"포장 DW               {m_dw_c:6.2f} kN·m/m")
    print(f"활하중 + 충격         {m_ll_c + m_im_c:6.2f} kN·m/m")
    print(f"극한Ⅰ M_Ed           {m_ed_c:6.2f} kN·m/m")
    print()
    print(f"배치  D{dia_c:.0f}@{spacing_c:.0f} (상부)   {as_prov_c:6.0f} mm²/m")
    print(
        f"설계휨강도 M_Rd       {m_rd_c:6.2f} kN·m/m   "
        f"→ M_Rd/M_Ed = {m_rd_c / m_ed_c:.2f}"
    )
    grow_ll = 1.80 * ((m_ll_c + m_im_c) - (m_ll + m_im)) / (m_ed_c - m_ed) * 100
    dead_in = (m_dc + m_dw) / total * 100
    dead_c = (m_dc_c + m_dw_c) / (m_dc_c + m_dw_c + m_ll_c + m_im_c) * 100
    print()
    print(f"캔틸레버 M_Ed 가 내측부의 {m_ed_c / m_ed:.1f} 배다.")
    print(f"증가분 {m_ed_c - m_ed:.1f} 중 {grow_ll:.0f} % 가 활하중이다 - 연속판의")
    print("0.8배 혜택이 없고, 윤하중이 좁은 폭에 긴 지렛대 팔로 걸린다.")
    print(f"고정하중의 몫은 {dead_in:.0f} % 에서 {dead_c:.0f} % 로 늘 뿐이다.")

    # ── ⑦ 배력철근 ────────────────────────────────────────────────────────
    rule("⑦ 배력철근 (KDS 24 14 21 4.6.5.3(2))")
    ratio = distribution_steel_ratio(span=span)
    as_dist = ratio * as_prov

    print(
        f"비율                  120/√L = {120 / math.sqrt(span):.1f} %  "
        f"→ 상한 67 % 적용 = {ratio * 100:.0f} %"
    )
    print(f"소요 배력철근량        {as_dist:6.0f} mm²/m")
    for dia in (13.0, 16.0):
        need = bar_area(diameter=dia) * 1000.0 / as_dist
        ok = BAR_SPACING_MIN <= need <= BAR_SPACING_MAX
        print(
            f"  D{dia:.0f} → 간격 {need:5.0f} mm 이하   {'가능' if ok else '범위 밖'}"
        )

    # ── ⑧ 사용성 ──────────────────────────────────────────────────────────
    rule("⑧ 사용성 (KDS 24 14 21 4.2)")
    for label, m_s, a_s, d_eff, dia, sp in (
        ("내측부", m_ser, as_prov, d_in, dia_in, spacing_in),
        ("캔틸레버", m_ser_c, as_prov_c, d_c, dia_c, spacing_c),
    ):
        f_s = steel_stress(m_service=m_s, a_s=a_s, d=d_eff)
        try:
            s_lim = max_bar_spacing(f_s=f_s)
            d_lim = max_bar_diameter(f_s=f_s)
            verdict = "만족" if sp <= s_lim and dia <= d_lim else "불만족"
            print(
                f"{label:>8}  f_s = {f_s:5.1f} MPa  →  허용 간격 {s_lim:5.0f} mm "
                f"(배치 {sp:.0f}), 허용 지름 {d_lim:4.1f} (D{dia:.0f})  {verdict}"
            )
        except ValueError as exc:
            print(f"{label:>8}  f_s = {f_s:5.1f} MPa  →  {exc}")

    defl = deck_deflection_limit(span=span * 1000)
    print()
    print(f"처짐 한계             L/800 = {defl:.1f} mm  (4.6.5.1(2))")
    print("피로한계상태           검증 불필요 (4.6.5.1(3))")
    print("전단                   검토 생략 가능 (KDS 24 10 11 4.6.2.2(3))")

    # ── ⑨ KDS 14 대조 ────────────────────────────────────────────────────
    rule("⑨ KDS 14 로 풀면 (하중은 동일, 단면 저항만 다르다)")
    print(f"{'단면':>10}  {'M_Ed':>8}  {'KDS 24':>10}  {'KDS 14':>10}  {'차이':>7}")
    for label, m, d_eff in (("내측부", m_ed, d_in), ("캔틸레버", m_ed_c, d_c)):
        a24 = required_steel_area(m_ed=m * 1e6, d=d_eff)
        a14 = required_steel_kds14(m_u=m * 1e6, d=d_eff)
        print(
            f"{label:>10}  {m:6.2f}  {a24:8.0f} mm²  {a14:8.0f} mm²  "
            f"{(a24 / a14 - 1) * 100:+6.1f} %"
        )
    print()
    print("휨은 철근이 지배하므로 KDS 24 의 φ_s = 0.90 이 KDS 14 의 단면")
    print("φ = 0.85 보다 덜 깎아, 필요 철근량이 조금 적게 나온다.")

    # ── 요약 ──────────────────────────────────────────────────────────────
    rule("설계 요약")
    summary = design_deck(
        girder_spacing=GIRDER_SPACING,
        thickness=THICKNESS,
        bar_diameter=dia_in,
        bar_spacing=spacing_in,
        exposure=EXPOSURE,
        pavement=PAVEMENT,
    )
    print(f"바닥판 두께           {THICKNESS:.0f} mm 내측 / {HAUNCH:.0f} mm 고정단")
    print(f"주철근                D{dia_in:.0f}@{spacing_in:.0f} (하부, 교축직각방향)")
    print(f"캔틸레버 상부철근      D{dia_c:.0f}@{spacing_c:.0f}")
    print(
        f"배력철근              D13@{bar_area(diameter=13.0) * 1000 / as_dist:.0f} 이하"
    )
    print(f"공칭피복              {cover:.0f} mm ({EXPOSURE})")
    print()
    for name, ok in summary.checks.items():
        print(f"  {'만족  ' if ok else '불만족'}  {name}")
    print(f"\n내측부 종합 판정: {'만족' if summary.adequate else '불만족'}")


if __name__ == "__main__":
    main()
