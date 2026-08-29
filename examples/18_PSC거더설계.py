"""예제 18 - PSC I형 거더 설계 (KDS 24 한계상태설계법).

지간 30 m 단순 지지 PSC 거더교의 주형을 설계한다. 바닥판(예제 17)이
거더 위에 얹히므로, 합성 전후로 저항 단면이 달라지는 것이 핵심이다.

    ① 교량 제원과 단면          KDS 24 14 21 4.6
    ② 하중과 저항 단면          KDS 24 12 21 4.3, KDS 24 12 11 표 4.1-1
    ③ 도입응력 한계             KDS 24 14 21 1.5.7.2, 1.5.7.3
    ④ 프리스트레스 손실         KDS 24 14 21 1.5.7.4, 1.5.7.5, 3.3.2(7)
    ⑤ 사용한계상태 응력         KDS 24 14 21 4.2.2
    ⑥ 극한한계상태 휨           KDS 24 14 21 4.1.1
    ⑦ 텐던 배치와 핵거리        KDS 24 14 21 1.5.7.3
    ⑧ 강연선 수량 결정          지간별 최소 수량
    ⑨ KDS 14 대조

주의: 여기 쓰는 단면은 **예시이며 어떤 표준도도 아니다.**

실행:
    python 18_PSC거더설계.py
"""

from __future__ import annotations

from concreteproperties_kds.kds import stress_block_parameters
from concreteproperties_kds.kds24 import (
    COMBINATIONS_BY_NAME,
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
    stress_after_transfer,
)

# ── 교량 제원 ──────────────────────────────────────────────────────────────
SPAN = 30.0  # 지간 (m)
GIRDER_SPACING = 2.5  # 거더 중심 간격 (m)
DECK_THICKNESS = 240.0  # 바닥판 두께 (mm) - 예제 17 에서 정한 값
HAUNCH = 50.0  # 헌치 높이 (mm)

FCK = 40.0  # 거더 콘크리트 (MPa)
FCK_TRANSFER = 30.0  # 긴장 시 콘크리트 강도 f_ck(t)
FCK_DECK = 27.0  # 바닥판 콘크리트

FPU, FPY = 1860.0, 1600.0  # SWPC 7B 15.2 mm 강연선
STRAND_AREA = 138.7  # 1 가닥의 단면적 (mm²)
N_STRAND = 25  # 배치 가닥 수

W_SDL = 3.0  # 2차 고정하중 - 포장·방호벽 (kN/m)
DIST_FACTOR = 0.6  # 거더 1 본이 받는 활하중 분배계수

SECTION = EXAMPLE_SECTIONS["PSC-I 2.0m"]


def rule(title: str) -> None:
    """구분선과 제목을 출력한다."""
    print(f"\n{title}")
    print("-" * 78)


def main() -> None:
    """예제를 실행한다."""
    a_p = N_STRAND * STRAND_AREA
    props = SECTION.properties()
    result = design_girder(
        section=SECTION,
        span=SPAN,
        girder_spacing=GIRDER_SPACING,
        deck_thickness=DECK_THICKNESS,
        haunch=HAUNCH,
        fck=FCK,
        fck_transfer=FCK_TRANSFER,
        fck_deck=FCK_DECK,
        a_p=a_p,
        fpu=FPU,
        fpy=FPY,
        w_sdl=W_SDL,
        distribution_factor=DIST_FACTOR,
    )

    # ── ① 단면 ────────────────────────────────────────────────────────────
    rule("① 거더 단면과 합성 단면")
    n_ratio = elastic_modulus(fck=FCK_DECK) / elastic_modulus(fck=FCK)
    comp = result.composite
    print(f"단면        {SECTION.name}  (예시 단면, 표준도가 아니다)")
    ratio = SPAN * 1000 / SECTION.height
    print(f"형고        {SECTION.height:.0f} mm,  지간/형고 = {ratio:.1f}")
    print(f"탄성계수비   n = E_deck / E_girder = {n_ratio:.4f}")
    print()
    print(f"{'':10} {'A (m²)':>9} {'y_b (mm)':>10} {'I (m⁴)':>9} {'Z_b (m³)':>10}")
    for label, s in [("거더 단독", props), ("합성 단면", comp)]:
        print(
            f"{label:10} {s.area / 1e6:9.3f} {s.y_b:10.0f} "
            f"{s.inertia / 1e12:9.4f} {s.z_b / 1e9:10.4f}"
        )
    print()
    print(f"합성으로 하연 단면계수가 {comp.z_b / props.z_b:.2f} 배가 된다.")

    # ── ② 하중 ────────────────────────────────────────────────────────────
    rule("② 하중과 저항 단면")
    w_girder = GAMMA_CONCRETE * props.area / 1e6
    w_deck = GAMMA_CONCRETE * GIRDER_SPACING * DECK_THICKNESS / 1000.0
    m_girder = w_girder * SPAN**2 / 8.0
    m_deck = w_deck * SPAN**2 / 8.0
    m_sdl = W_SDL * SPAN**2 / 8.0
    live = girder_live_load(span=SPAN)
    m_live = live.moment * DIST_FACTOR

    total = m_girder + m_deck + m_sdl + m_live
    print(f"{'하중':16} {'w (kN/m)':>10} {'M (kN·m)':>10} {'몫':>7}  저항 단면")
    rows = [
        ("거더 자중", w_girder, m_girder, "거더 단독"),
        ("굳지 않은 바닥판", w_deck, m_deck, "거더 단독"),
        ("2차 고정하중", W_SDL, m_sdl, "합성 단면"),
        ("활하중 + 충격", float("nan"), m_live, "합성 단면"),
    ]
    for label, w, m, sec in rows:
        wtxt = f"{w:10.2f}" if w == w else f"{'-':>10}"
        print(f"{label:16} {wtxt} {m:10.0f} {m / total * 100:6.1f} %  {sec}")
    print(f"{'합계':16} {'':10} {total:10.0f}")
    print()
    print(
        f"활하중은 {live.governed_by} 가 지배한다 (1 개 차로 {live.moment:.0f} kN·m)."
    )
    print(
        f"거더 단독이 받는 몫이 {(m_girder + m_deck) / total * 100:.1f} % 다. "
        "합성 단면의 이득은 나머지에만 미친다."
    )

    print()
    m_ed = COMBINATIONS_BY_NAME["극한Ⅰ"].evaluate(
        loads={"DC": m_girder + m_deck + m_sdl, "LL": m_live}
    )
    m_dc = m_girder + m_deck + m_sdl
    print(f"극한Ⅰ  M_Ed = 1.25 x {m_dc:.0f} + 1.80 x {m_live:.0f} = {m_ed:.0f} kN·m")

    # ── ③ 도입응력 ────────────────────────────────────────────────────────
    rule("③ 도입응력의 상한")
    f_jack = max_jacking_stress(fpu=FPU, fpy=FPY)
    print(f"식 (1.5-7)  f_o,max = min(0.80 x {FPU:.0f}, 0.90 x {FPY:.0f})")
    print(
        f"                   = min({0.80 * FPU:.0f}, {0.90 * FPY:.0f})"
        f" = {f_jack:.0f} MPa"
    )
    print(f"  -> 항복비 f_py/f_pu = {FPY / FPU:.3f} < 0.889, f_py 조건이 지배한다.")
    print()
    lit = stress_after_transfer(fpy=FPY)
    en = stress_after_transfer(fpy=FPY, fpu=FPU, reading="EN")
    f_pi = result.losses.f_pi
    print()
    print("식 (1.5-9)  도입 직후 f_pmo — 이 조문은 두 가지로 읽힌다")
    print(f"  원문대로  min(0.75 f_py, 0.85 f_py) = {lit:.0f} MPa")
    print(f"  EN 해석   min(0.75 f_pu, 0.85 f_py) = {en:.0f} MPa")
    print(
        f"  계산된 f_pi = {f_pi:.0f} MPa"
        f"  ->  원문 {'만족' if f_pi <= lit else '초과'},"
        f"  EN {'만족' if f_pi <= en else '초과'}"
    )
    print()
    print("  원문대로면 긴장응력 1440 MPa 에서 즉시손실이 16.7 % 를 넘어야 하는데,")
    print(
        f"  이 거더의 즉시손실은 {result.losses.immediate_ratio * 100:.1f} % 다."
        " 즉 식 (1.5-9) 가 식 (1.5-7) 의"
    )
    capped = lit / (1 - result.losses.immediate_ratio)
    print(f"  상한을 사실상 {capped:.0f} MPa 로 끌어내린다.")
    print("  이 예제는 EN 해석을 쓴다. 실무에서는 발주자·감리와 맞추어야 한다.")
    print(f"강연선       {N_STRAND} 가닥 x {STRAND_AREA:.1f} = A_p {a_p:.0f} mm²")
    e_mid0 = props.y_b - TENDON_COVER
    print(f"편심         e = y_b - {TENDON_COVER:.0f} = {e_mid0:.0f} mm")

    # ── ④ 손실 ────────────────────────────────────────────────────────────
    rule("④ 프리스트레스 손실")
    losses = result.losses
    print(f"긴장응력                       {losses.f_jack:8.1f} MPa")
    for label, value, ref in [
        ("마찰 (1.5-11)", losses.friction, "표 1.5-2  mu = 0.19, k = 0.004"),
        ("정착장치 활동", losses.anchorage, "활동량 6 mm"),
        ("탄성변형 (1.5-10)", losses.elastic, "4 개 텐던 순차 긴장"),
    ]:
        pct = value / losses.f_jack * 100
        print(f"  - {label:22} {value:8.1f} MPa  ({pct:4.1f} %)  {ref}")
    print(
        f"도입 직후 f_pi                 {losses.f_pi:8.1f} MPa"
        f"  즉시손실 {losses.immediate_ratio * 100:.1f} %"
    )
    print(
        f"  - {'장기 (1.5-12)':22} {losses.long_term:8.1f} MPa"
        f"  ({losses.long_term / losses.f_jack * 100:4.1f} %)"
        "  크리프+건조수축+릴랙세이션"
    )
    print(
        f"유효응력 f_pe                  {losses.f_pe:8.1f} MPa"
        f"  총손실   {losses.total_ratio * 100:.1f} %"
    )
    print()
    print(f"P_i = {result.p_i / 1e3:.0f} kN   P_e = {result.p_e / 1e3:.0f} kN")
    print("가장 큰 손실은 마찰이다. 크리프·건조수축과 달리 텐던 배치로 줄일 수 있다.")

    # ── ⑤ 사용한계상태 ────────────────────────────────────────────────────
    rule("⑤ 사용한계상태 응력 (압축 양수, MPa)")
    print(f"{'단계':14} {'상연':>9} {'하연':>9}   {'압축 한계':>10} {'인장 한계':>10}")
    for key in ("긴장 직후", "지속하중", "사용"):
        top, bot = result.stresses[key]
        hi, lo = result.limits[key]
        print(f"{key:14} {top:9.2f} {bot:9.2f}   {hi:10.2f} {lo:10.2f}")
    print(
        f"{'바닥판 상연':14} {result.stresses['바닥판 상연'][0]:9.2f} {'-':>9}   "
        f"{result.limits['바닥판 상연'][0]:10.2f} {'-':>10}"
    )
    print()
    print("긴장 직후에는 하연이 눌리고 사용 시에는 하중이 그것을 되돌린다.")
    print(
        f"사용 시 하연 인장 {-result.stresses['사용'][1]:.2f} MPa <= f_ctk "
        f"{characteristic_tensile_strength(fck=FCK):.2f} MPa 이므로 비균열이다."
    )

    # ── ⑥ 극한한계상태 ────────────────────────────────────────────────────
    rule("⑥ 극한한계상태 휨")
    shape = "바닥판을 넘어 T형 단면" if result.flanged else "바닥판 안 (직사각형)"
    print(f"압축부가 {shape}")
    print(f"중립축 c = {result.c_n:.0f} mm  (바닥판 두께 {DECK_THICKNESS:.0f} mm)")
    print(
        f"M_Rd = {result.m_rd:.0f} kN·m  >=  M_Ed = {result.m_ed:.0f} kN·m"
        f"   여유 {result.m_rd / result.m_ed:.2f} 배"
    )

    # ── ⑦ 텐던 배치 ───────────────────────────────────────────────────────
    rule("⑦ 텐던 배치 - 왜 휘어 올리는가")
    z_t = props.inertia / props.y_t
    kern = z_t / props.area
    f_ctk_t = characteristic_tensile_strength(fck=FCK_TRANSFER)
    e_mid = props.y_b - TENDON_COVER
    top_end = result.p_i / props.area - result.p_i * e_mid / z_t
    print(f"핵거리  Z_t / A = {kern:.0f} mm")
    print(f"중앙 편심             {e_mid:.0f} mm")
    print()
    print("단부에서는 자중 모멘트가 0 이므로 프리스트레스를 상쇄할 것이 없다.")
    print(f"중앙 편심을 단부까지 그대로 끌고 가면 상연 응력이 {top_end:.2f} MPa,")
    print(f"즉 인장 {-top_end:.2f} MPa 로 긴장 시 f_ctk {f_ctk_t:.2f} MPa 를 넘는다.")
    print()
    print(f"-> 단부에서 편심을 핵거리 {kern:.0f} mm 안으로 들이도록 드레이프해야 한다.")
    print("   텐던을 휘는 것은 시공 편의가 아니라 응력이 요구하는 형상이다.")

    # ── ⑧ 수량 결정 ───────────────────────────────────────────────────────
    rule("⑧ 지간별 최소 강연선 수량")
    print(
        f"{'단면':12} {'지간':>5} {'가닥':>5} {'손실':>7} "
        f"{'M_Rd/M_Ed':>10}  한 가닥 모자랄 때"
    )
    for name, span in [
        ("PSC-I 1.4m", 20.0),
        ("PSC-I 1.7m", 25.0),
        ("PSC-I 2.0m", 30.0),
        ("PSC-I 2.0m", 35.0),
        ("PSC-I 2.3m", 40.0),
        ("PSC-I 2.7m", 45.0),
        ("PSC-I 2.7m", 50.0),
    ]:
        section = EXAMPLE_SECTIONS[name]
        n = 6
        while n < 141:
            trial = design_girder(section=section, span=span, a_p=n * STRAND_AREA)
            if trial.adequate:
                break
            n += 1
        short = design_girder(section=section, span=span, a_p=(n - 1) * STRAND_AREA)
        governing = ", ".join(k for k, v in short.checks.items() if not v)
        print(
            f"{name:12} {span:5.0f} {n:5d} {trial.losses.total_ratio * 100:6.1f} % "
            f"{trial.m_rd / trial.m_ed:10.2f}  {governing}"
        )
    print()
    print("짧은 지간은 극한 휨강도가, 35 m 이상은 사용한계상태 균열이 수량을 정한다.")
    print("극한 여유가 1.09 ~ 1.14 배로 남는데도 강연선을 더 넣어야 한다.")

    # ── ⑨ KDS 14 대조 ─────────────────────────────────────────────────────
    rule("⑨ KDS 14 강도설계법과의 대조")
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
    phi = 0.85

    print(f"유효깊이 d_p = {d_p:.0f} mm,  b_eff = {b_eff:.0f} mm")
    print()
    print(
        f"{'':8} {'강재 응력':>10} {'콘크리트':>10} {'a (mm)':>9} {'강도 (kN·m)':>13}"
    )
    print(f"{'KDS 24':8} {f_pd:10.0f} {f_cd:10.2f} {a24:9.0f} {m_rd24:13.0f}   M_Rd")
    f_c14 = eta14 * 0.85 * FCK_DECK
    print(f"{'KDS 14':8} {FPY:10.0f} {f_c14:10.2f} {a14:9.0f} {m_n:13.0f}   M_n")
    print(f"{'':8} {'':10} {'':10} {'x 0.85':>9} {phi * m_n:13.0f}   phi M_n")
    print()
    gap = m_rd24 / (phi * m_n)
    print(f"KDS 24 / KDS 14 = {gap:.3f}  ({(gap - 1) * 100:+.1f} %)")
    print("휨은 강재의 인장력이 지배하므로 KDS 24 의 phi_s = 0.90 이 KDS 14 의")
    print("단면 phi = 0.85 보다 덜 깎는다. 0.65 는 압축블록만 깊게 한다.")
    print("(안전율 배치만 견주려고 강재 응력을 양쪽 모두 f_py 로 두었다.)")

    # ── 요약 ──────────────────────────────────────────────────────────────
    rule("설계 요약")
    print(
        f"거더                 {SECTION.name}, 지간 {SPAN:.0f} m, "
        f"간격 {GIRDER_SPACING:.1f} m"
    )
    print(
        f"콘크리트             거더 {FCK:.0f} / 긴장 시 {FCK_TRANSFER:.0f} / "
        f"바닥판 {FCK_DECK:.0f} MPa"
    )
    print(
        f"긴장재               15.2 mm x {N_STRAND} 가닥 (A_p {a_p:.0f} mm²), "
        f"e = {props.y_b - TENDON_COVER:.0f} mm"
    )
    print(
        f"프리스트레스          P_i {result.p_i / 1e3:.0f} kN  ->  "
        f"P_e {result.p_e / 1e3:.0f} kN (손실 {losses.total_ratio * 100:.1f} %)"
    )
    print(f"휨                   M_Ed {result.m_ed:.0f} <= M_Rd {result.m_rd:.0f} kN·m")
    print()
    for name, ok in result.checks.items():
        print(f"  {'만족  ' if ok else '불만족'}  {name}")
    print(f"\n종합 판정: {'만족' if result.adequate else '불만족'}")


if __name__ == "__main__":
    main()
