"""예제 19 - PSC I형 거더 전단설계 (KDS 24 한계상태설계법).

예제 18 에서 휨으로 설계한 그 거더의 전단을 검토한다. 휨에서 프리스트레스는
하중을 상쇄하는 역할이었지만, 전단에서는 콘크리트 강도식에 직접 들어간다.

    ① 거더와 유효 프리스트레스     예제 18 의 결과
    ② 설계전단력 V_Ed              KDS 24 12 21 4.3, 24 12 11 표 4.1-1
    ③ 복부 축압축 f_n              KDS 24 14 21 4.1.2.2
    ④ 콘크리트 전단강도 V_cd       KDS 24 14 21 식 (4.1-7), (4.1-8)
    ⑤ 전단철근 필요 구간           KDS 24 14 21 4.1.2.2
    ⑥ 변각 트러스 - cot 세타 선택  KDS 24 14 21 4.1.2.3
    ⑦ 스터럽 배치                  KDS 24 14 21 식 (4.1-16)
    ⑧ 최소 전단철근과 최대 간격    KDS 24 14 21 4.6.3
    ⑨ KDS 14 대조

주의: 여기 쓰는 단면은 **예시이며 어떤 표준도도 아니다.**

실행:
    python 19_PSC거더전단설계.py
"""

from __future__ import annotations

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

# ── 거더 제원 (예제 18 과 같다) ────────────────────────────────────────────
SECTION = EXAMPLE_SECTIONS["PSC-I 2.0m"]
SPAN = 30.0
GIRDER_SPACING = 2.5
DECK_THICKNESS = 240.0
STRAND_AREA, N_STRAND = 138.7, 25
FCK = 40.0
W_SDL, DIST_FACTOR = 3.0, 0.6

# ── 전단 설계 변수 ────────────────────────────────────────────────────────
B_W = 290.0  # 복부 두께 (mm)
STIRRUP_DIA = 13.0  # 스터럽 지름
STIRRUP_LEGS = 2  # 가닥 수
F_VY = 400.0  # 스터럽 기준항복강도 (MPa)
COT_THETA = 2.0  # 스트럿 경사

BAR_AREA = {10: 71.33, 13: 126.7, 16: 198.6, 19: 286.5}


def rule(title: str) -> None:
    """구분선과 제목을 출력한다."""
    print(f"\n{title}")
    print("-" * 78)


def main() -> None:
    """예제를 실행한다."""
    a_p = N_STRAND * STRAND_AREA
    girder = design_girder(
        section=SECTION,
        span=SPAN,
        girder_spacing=GIRDER_SPACING,
        deck_thickness=DECK_THICKNESS,
        fck=FCK,
        a_p=a_p,
        w_sdl=W_SDL,
        distribution_factor=DIST_FACTOR,
    )
    props = SECTION.properties()
    comp = girder.composite
    d_p = girder.d_p
    a_v = STIRRUP_LEGS * BAR_AREA[int(STIRRUP_DIA)]

    # ── ① 거더 ────────────────────────────────────────────────────────────
    rule("① 거더와 유효 프리스트레스 (예제 18 의 결과)")
    print(f"단면          {SECTION.name}  (예시 단면, 표준도가 아니다)")
    print(f"지간          {SPAN:.0f} m,  거더 간격 {GIRDER_SPACING:.1f} m")
    print(f"복부 두께     b_w = {B_W:.0f} mm")
    print(f"유효깊이      d_p = {d_p:.0f} mm  (합성 상연에서 긴장재까지)")
    print(f"긴장재        {N_STRAND} 가닥, A_p = {a_p:.0f} mm²")
    print(f"유효 프리스트레스  P_e = {girder.p_e / 1e3:.0f} kN")
    print(
        f"  (긴장력의 {(1 - girder.losses.total_ratio) * 100:.0f} % — 손실 "
        f"{girder.losses.total_ratio * 100:.1f} %)"
    )

    # ── ② 설계전단력 ──────────────────────────────────────────────────────
    rule("② 설계전단력 V_Ed (극한Ⅰ)")
    w_girder = GAMMA_CONCRETE * props.area / 1e6
    w_deck = GAMMA_CONCRETE * GIRDER_SPACING * DECK_THICKNESS / 1000.0
    w_total = w_girder + w_deck + W_SDL

    def v_ed(x: float) -> float:
        """지점에서 x (m) 떨어진 곳의 설계전단력 (kN)."""
        v_dc = w_total * (SPAN / 2 - x)
        v_ll = girder_live_load(span=SPAN, section=x).shear * DIST_FACTOR
        return 1.25 * v_dc + 1.80 * v_ll

    print(f"고정하중 합계  w = {w_total:.1f} kN/m")
    print(f"  (거더 {w_girder:.1f} + 바닥판 {w_deck:.1f} + 2차 {W_SDL:.1f})")
    print()
    print(f"{'위치 (m)':>9} {'V_DC':>9} {'V_LL+IM':>10} {'V_Ed':>10}")
    for x in (0.0, 2.0, 5.0, 10.0, 15.0):
        v_dc = w_total * (SPAN / 2 - x)
        v_ll = girder_live_load(span=SPAN, section=x).shear * DIST_FACTOR
        print(f"{x:9.1f} {v_dc:9.0f} {v_ll:10.0f} {v_ed(x):10.0f}")
    print()
    print("휨은 지간 중앙이 최대였지만 전단은 지점이 최대다.")

    # ── ③ 축압축 ──────────────────────────────────────────────────────────
    rule("③ 복부의 평균 축압축 f_n")
    f_n_raw = girder.p_e / comp.area
    f_n = axial_stress(n_u=girder.p_e, a_c=comp.area, fck=FCK)
    print(
        f"P_e / A_comp = {girder.p_e / 1e3:.0f} kN / "
        f"{comp.area / 1e6:.3f} m² = {f_n_raw:.3f} MPa"
    )
    print(f"상한 0.2 phi_c f_ck = {0.2 * 0.65 * FCK:.2f} MPa")
    print(f"  ->  f_n = {f_n:.3f} MPa")
    print()
    print("반드시 '유효' 프리스트레스로 계산해야 한다. 긴장력을 쓰면")
    print(f"손실 {girder.losses.total_ratio * 100:.0f} % 만큼 전단강도를 과대평가한다.")

    # ── ④ 콘크리트 전단강도 ───────────────────────────────────────────────
    rule("④ 콘크리트 전단강도 V_cd — 식 (4.1-7)")
    v_cd_0 = (
        design_concrete_shear_strength(fck=FCK, b_w=B_W, d=d_p, a_s=a_p, f_n=0.0) / 1e3
    )
    v_cd = (
        design_concrete_shear_strength(fck=FCK, b_w=B_W, d=d_p, a_s=a_p, f_n=f_n) / 1e3
    )
    print("V_cd = [0.85 phi_c kappa (rho f_ck)^(1/3) + 0.15 f_n] b_w d")
    print()
    print(f"프리스트레스 무시 (f_n = 0)     V_cd = {v_cd_0:7.1f} kN")
    print(f"프리스트레스 반영 (f_n = {f_n:.2f})  V_cd = {v_cd:7.1f} kN")
    print(f"  ->  {(v_cd / v_cd_0 - 1) * 100:+.0f} %")
    print()
    print("이것이 휨과 결정적으로 다른 점이다. 휨에서 프리스트레스는 하중을")
    print("상쇄할 뿐이지만, 전단에서는 강도식에 직접 들어간다.")

    # ── ⑤ 전단철근 필요 구간 ──────────────────────────────────────────────
    rule("⑤ 전단철근이 필요한 구간")
    x_free = None
    x = 0.0
    while x <= SPAN / 2:
        if v_ed(x) <= v_cd:
            x_free = x
            break
        x += 0.1
    if x_free is not None:
        print(f"x = {x_free:.1f} m 부터 V_Ed <= V_cd 가 되어 계산상 전단철근이")
        print(f"필요 없다 (지간의 {x_free / SPAN * 100:.0f} %).")
    else:
        print("지간 전체에서 전단철근이 필요하다.")
    print()
    print("다만 '필요 없다' 와 '넣지 않는다' 는 다르다 — ⑧ 을 볼 것.")

    # ── ⑥ cot 세타 ────────────────────────────────────────────────────────
    rule("⑥ 변각 트러스 — cot 세타 를 고르는 대가")
    print(f"기준 범위  {COT_THETA_MIN:.1f} <= cot θ <= {COT_THETA_MAX:.1f}")
    print()
    print(f"{'cot θ':>7} {'θ':>7} {'V_sd':>10} {'V_d,max':>10} {'지배':>10}")
    rows = []
    for i in range(11):
        cot = COT_THETA_MIN + (COT_THETA_MAX - COT_THETA_MIN) * i / 10
        v_sd = (
            shear_reinforcement_strength(
                f_vy=F_VY, a_v=a_v, d=d_p, s=150.0, cot_theta=cot
            )
            / 1e3
        )
        v_max = max_shear_strength(fck=FCK, b_w=B_W, d=d_p, cot_theta=cot) / 1e3
        rows.append((cot, v_sd, v_max))
        print(
            f"{cot:7.2f} {math.degrees(math.atan(1 / cot)):6.1f}° "
            f"{v_sd:10.0f} {v_max:10.0f} "
            f"{'스트럿' if v_sd > v_max else '스터럽':>10}"
        )

    cross = None
    for a, b in zip(rows, rows[1:], strict=False):
        if (a[1] - a[2]) * (b[1] - b[2]) < 0:
            t = (a[2] - a[1]) / ((b[1] - a[1]) - (b[2] - a[2]))
            cross = a[0] + t * (b[0] - a[0])
            break
    print()
    if cross:
        print(f"cot θ ≈ {cross:.2f} 를 넘으면 스터럽보다 스트럿이 먼저 깨진다.")
        print("그 위로는 cot θ 를 키워도 강도가 늘지 않고 오히려 준다.")
    print(f"이 예제는 cot θ = {COT_THETA:.1f} 로 설계한다.")

    # ── ⑦ 스터럽 배치 ─────────────────────────────────────────────────────
    rule("⑦ 스터럽 배치")
    s_max = maximum_stirrup_spacing(d=d_p)
    rho_min = minimum_shear_reinforcement_ratio(fck=FCK, f_y=F_VY)
    s_rho = a_v / (rho_min * B_W)
    s_limit = min(s_max, s_rho)

    print(f"스터럽        D{STIRRUP_DIA:.0f} {STIRRUP_LEGS}가닥, A_v = {a_v:.1f} mm²")
    print(f"최대 간격     0.75 d = {s_max:.0f} mm")
    print(f"최소 전단철근비 {rho_min * 100:.3f} %  ->  간격 {s_rho:.0f} mm 이하")
    print(f"간격 상한     {s_limit:.0f} mm")
    print()
    print(f"{'위치':>6} {'V_Ed':>9} {'소요 V_sd':>10} {'필요 간격':>10} {'채택':>8}")
    for x in (0, 1, 2, 3, 4, 5, 7.5, 10, 12, 15):
        v = v_ed(float(x))
        need = v - v_cd
        if need <= 0:
            print(f"{x:6.1f} {v:9.0f} {'-':>10} {'불필요':>10} {s_limit:8.0f}")
            continue
        s_req = required_stirrup_spacing(
            v_ed=need * 1e3, d=d_p, a_v=a_v, cot_theta=COT_THETA
        )
        print(
            f"{x:6.1f} {v:9.0f} {need:10.0f} {s_req:10.0f} {min(s_req, s_limit):8.0f}"
        )

    # ── ⑧ 최소 전단철근 ───────────────────────────────────────────────────
    rule("⑧ 왜 필요 없는 구간에도 넣는가")
    print("휨 파괴는 철근이 항복하며 처짐이 자라 예고가 있지만, 전단 파괴는")
    print("사인장균열이 갑자기 열리며 예고 없이 온다. V_cd 식 자체가 실험의")
    print("회귀식이라 흩어짐도 크다.")
    print()
    print("최소 전단철근은 강도를 위한 것이 아니라 취성 파괴를 막기 위한 것이다.")
    print(f"이 거더에서는 중앙부에도 D{STIRRUP_DIA:.0f}@{s_limit:.0f} 이하를 넣는다.")

    # ── ⑨ KDS 14 대조 ─────────────────────────────────────────────────────
    rule("⑨ KDS 14 강도설계법과의 대조")
    v_c_14 = 0.75 * (1 / 6) * math.sqrt(FCK) * B_W * d_p / 1e3
    print("KDS 14 20 22 간이식  phi V_c = 0.75 x (1/6) sqrt(f_ck) b_w d")
    print(f"                            = {v_c_14:7.1f} kN")
    print(
        f"KDS 24  V_cd (f_n = 0)      = {v_cd_0:7.1f} kN "
        f"({v_cd_0 / v_c_14 * 100:.0f} %)"
    )
    print(
        f"KDS 24  V_cd (f_n = {f_n:.2f})   = {v_cd:7.1f} kN "
        f"({v_cd / v_c_14 * 100:.0f} %)"
    )
    print()
    print("프리스트레스를 빼면 KDS 24 가 더 보수적인데, 넣으면 뒤집힌다.")
    print("PSC 부재에서 두 기준의 차이는 축응력 항이 만든다.")
    print()
    print("(KDS 14 20 60 은 PSC 부재에 V_ci / V_cw 상세식을 따로 둔다.")
    print(" 위 비교는 간이식만 형식적으로 견준 것이다.)")

    # ── 요약 ──────────────────────────────────────────────────────────────
    rule("설계 요약")
    print(f"거더          {SECTION.name}, 지간 {SPAN:.0f} m")
    print(f"복부          b_w {B_W:.0f} mm,  d_p {d_p:.0f} mm")
    print(f"축압축        f_n = {f_n:.2f} MPa  ->  V_cd {v_cd_0:.0f} -> {v_cd:.0f} kN")
    print(f"지점 V_Ed     {v_ed(0.0):.0f} kN")
    v_max_use = max_shear_strength(fck=FCK, b_w=B_W, d=d_p, cot_theta=COT_THETA) / 1e3
    print(f"스트럿 상한   V_d,max = {v_max_use:.0f} kN")
    print(
        f"스터럽        D{STIRRUP_DIA:.0f} {STIRRUP_LEGS}가닥, cot θ = {COT_THETA:.1f}"
    )
    s_support = required_stirrup_spacing(
        v_ed=(v_ed(0.0) - v_cd) * 1e3, d=d_p, a_v=a_v, cot_theta=COT_THETA
    )
    print(
        f"              지점부 @{min(s_support, s_limit):.0f} mm, "
        f"중앙부 @{s_limit:.0f} mm 이하"
    )


if __name__ == "__main__":
    main()
