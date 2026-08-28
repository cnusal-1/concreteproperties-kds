# 설계식 목록

이 저장소가 구현한 설계식을 KDS 조문·식 번호와 함께 한자리에 모았다. 각 식은
해당 모듈의 함수 docstring 에도 같은 조문이 표기되어 있다.

기호는 KDS 원문을 따른다. 대조에 사용한 기준 판은
[검증 대조표](kds.md#기준-값-출처와-검증)를 참고한다.

---

## 하중조합 — KDS 14 20 10 4.2.2

| 식 | 내용 | 조문 | 구현 |
|---|---|---|---|
| $U = 1.4(D+F)$ | 고정하중 지배 | 식 (4.2-1) | `loads.LOAD_COMBINATIONS` |
| $U = 1.2(D{+}F{+}T) + 1.6(L + \alpha_H H_v + H_h) + 0.5(L_r/S/R)$ | 활하중 지배 | 식 (4.2-2) | 〃 |
| $U = 1.2D + 1.6(L_r/S/R) + (1.0L$ 또는 $0.65W)$ | 지붕하중 지배 | 식 (4.2-3) | 〃 |
| $U = 1.2D + 1.3W + 1.0L + 0.5(L_r/S/R)$ | 풍하중 지배 | 식 (4.2-4) | 〃 |
| $U = 1.2(D{+}H_v) + 1.0E + 1.0L + 0.2S + (1.0H_h$ 또는 $0.5H_h)$ | 지진하중 지배 | 식 (4.2-5) | 〃 |
| $U = 1.2(D{+}F{+}T) + 1.6(L + \alpha_H H_v) + 0.8H_h + 0.5(L_r/S/R)$ | 토압 조합 | 식 (4.2-6) | 〃 |
| $U = 0.9(D{+}H_v) + 1.3W + (1.6H_h$ 또는 $0.8H_h)$ | 풍하중 부양 | 식 (4.2-7) | 〃 |
| $U = 0.9(D{+}H_v) + 1.0E + (1.0H_h$ 또는 $0.5H_h)$ | 지진 부양 | 식 (4.2-8) | 〃 |
| $\alpha_H = 1.0\ (h \le 2\text{m})$, $1.05-0.025h \ge 0.875\ (h > 2\text{m})$ | 연직토압 보정 | 4.2.2(1) | `loads.alpha_h` |
| 활하중 계수 $1.0 \to 0.5$ (식 4.2-3, 4.2-4, 4.2-5) | 활하중 저감 | 4.2.2(2) | `loads.evaluate_all(reduce_live_load=True)` |

---

## 재료 — KDS 14 20 10 4.3

| 식 | 내용 | 조문 | 구현 |
|---|---|---|---|
| $E_c = 0.077 m_c^{1.5}\sqrt[3]{f_{cm}}$ | 콘크리트 할선탄성계수 (일반) | 식 (4.3-1) | `kds.elastic_modulus` |
| $E_c = 8500\sqrt[3]{f_{cm}}$ | 보통중량 콘크리트 ($m_c$ = 2,300) | 식 (4.3-2) | 〃 |
| $f_{cm} = f_{ck} + \Delta f$ | 평균압축강도 | 식 (4.3-3) | 〃 |
| $\Delta f$ = 4 MPa ($f_{ck} \le 40$), 6 MPa ($f_{ck} \ge 60$), 그 사이 직선보간 | — | 4.3.3(1) | 〃 |
| $E_s = 200{,}000$ MPa | 철근 탄성계수 | 식 (4.3-5) | `kds.ES` |
| $E_{ps} = 200{,}000$ MPa | 긴장재 탄성계수 | 식 (4.3-6) | 예제 16 |
| $\lambda$ = 0.75 (전경량), 0.85 (모래경량), 1.0 (보통중량) | 경량콘크리트계수 | 4.3.4(1)① | 각 함수의 `lambda_c` |
| $\lambda = f_{sp}/(0.56\sqrt{f_{ck}}) \le 1.0$ | $f_{sp}$ 가 주어진 경우 | 4.3.4(1)② | 〃 |

---

## 강도감소계수 — KDS 14 20 10 4.3.3(2)

| 값 | 대상 | 조문 | 구현 |
|---|---|---|---|
| 0.85 | 인장지배단면 | 4.3.3(2)① | `kds.PHI_TENSION` |
| 0.70 | 압축지배단면 — 나선철근 | 4.3.3(2)②가 | `kds.PHI_COMP_SPIRAL` |
| 0.65 | 압축지배단면 — 그 외 | 4.3.3(2)②나 | `kds.PHI_COMP_TIE` |
| 압축지배값 → 0.85 선형 증가 | 변화구간단면 | 4.3.3(2)②다 | `KDS.capacity_reduction_factor` |
| 0.75 | 전단력과 비틀림모멘트 | 4.3.3(2)③ | `shear.PHI_SHEAR` |
| 0.65 | 콘크리트의 지압력 | 4.3.3(2)④ | 미구현 |
| 0.85 | 포스트텐션 정착구역 | 4.3.3(2)⑤ | 미구현 |
| 0.75 / 0.85 | 스트럿·절점부·지압부 / 타이 | 4.3.3(2)⑥ | 미구현 |
| 0.55 | 무근콘크리트 | 4.3.3(2)⑧ | 미구현 |

$$\phi = \phi_c + (0.85 - \phi_c)
\frac{\varepsilon_t - \varepsilon_y}{\varepsilon_{t,tl} - \varepsilon_y}$$

---

## 휨 및 압축 — KDS 14 20 20

### 응력-변형률 관계 (4.1.1)

| 식 | 내용 | 조문 | 구현 |
|---|---|---|---|
| $\varepsilon_{cu}$ = 0.0033 ($f_{ck}\le40$), 매 10 MPa 마다 0.0001 감소 | 압축연단 극한변형률 | 4.1.1(3) | `kds.stress_block_parameters` |
| 압축응력 $= \eta(0.85 f_{ck})$, 깊이 $a = \beta_1 c$ | 등가직사각형 응력블록 | 4.1.1(8) | `kds.KDS14202022.create_concrete_material` |
| $f_c = 0.85f_{ck}\left[1-(1-\varepsilon_c/\varepsilon_{co})^{n}\right]$ | 포물선-직선 상승부, 식 (4.1-1) | 4.1.1(7) | `kds.parabolic_stress` |
| $f_c = 0.85f_{ck}$ ($\varepsilon_{co} < \varepsilon_c \le \varepsilon_{cu}$) | 포물선-직선 수평부, 식 (4.1-2) | 4.1.1(7) | `kds.parabolic_stress` |
| $n = 1.2 + 1.5\left(\frac{100-f_{ck}}{60}\right)^{4} \le 2.0$ | 상승 곡선부 지수, 식 (4.1-3) | 4.1.1(7) | `kds.parabolic_parameters` |
| $\varepsilon_{co} = 0.002 + \frac{f_{ck}-40}{100{,}000} \ge 0.002$ | 최대응력 도달 변형률, 식 (4.1-4) | 4.1.1(7) | `kds.parabolic_parameters` |
| $\varepsilon_{cu} = 0.0033 - \frac{f_{ck}-40}{100{,}000} \le 0.0033$ | 극한변형률, 식 (4.1-5) | 4.1.1(7) | `kds.parabolic_parameters` |
| $\alpha$, $\beta$ (평균 압축응력·합력 위치 계수) | 표 4.1-1 | 4.1.1(7) | `kds.parabolic_parameters` |
| $\varepsilon_{cu}$, $\eta$, $\beta_1$ 표 | $f_{ck}$ = ≤40 / 50 / 60 / 70 / 80 / 90 | 표 4.1-2 | `kds.STRESS_BLOCK_*` |

| $f_{ck}$ (MPa) | ≤40 | 50 | 60 | 70 | 80 | 90 |
|---|---:|---:|---:|---:|---:|---:|
| $\varepsilon_{cu}$ | 0.0033 | 0.0032 | 0.0031 | 0.0030 | 0.0029 | 0.0028 |
| $\eta$ | 1.00 | 0.97 | 0.95 | 0.91 | 0.87 | 0.84 |
| $\beta_1$ | 0.80 | 0.80 | 0.76 | 0.74 | 0.72 | 0.70 |

### 단면 분류와 축강도 (4.1.2)

| 식 | 내용 | 조문 | 구현 |
|---|---|---|---|
| $\varepsilon_t \le \varepsilon_y$ | 압축지배단면 (PSC 는 0.002) | 4.1.2(3) | `kds.compression_controlled_strain_limit` |
| $\varepsilon_t \ge 0.005$ 또는 $2.5\varepsilon_y$ ($f_y > 400$) | 인장지배단면 | 4.1.2(4) | `kds.tension_controlled_strain_limit` |
| $\varepsilon_t \ge 0.004$ 또는 $2.0\varepsilon_y$ ($f_y > 400$) | 휨부재 최소허용변형률 | 4.1.2(5) | `kds.minimum_net_tensile_strain` |
| $\phi P_{n,max} = 0.85\phi[0.85f_{ck}(A_g{-}A_{st}) + f_yA_{st}]$ | 나선철근 | 식 (4.1-16) | `KDS.max_axial_strength` |
| $\phi P_{n,max} = 0.80\phi[0.85f_{ck}(A_g{-}A_{st}) + f_yA_{st}]$ | 띠철근 | 식 (4.1-17) | 〃 |
| $\varepsilon_t = \varepsilon_{cu}(d_t - c)/c$ | 순인장변형률 | 4.1.2(3) | `KDS.net_tensile_strain` |

### 휨부재의 제한 (4.2)

| 식 | 내용 | 조문 | 구현 |
|---|---|---|---|
| $\phi M_n \ge 1.2 M_{cr}$ | 최소 철근량 | 식 (4.2-1) | `kds.minimum_flexural_moment` |
| $\phi M_n \ge \frac{4}{3} M_u$ | 대체 조건 | 식 (4.2-2) | `kds.minimum_flexural_moment_alternative` |
| $s = 375(\kappa_{cr}/f_s) - 2.5c_c \le 300(\kappa_{cr}/f_s)$ | 균열 제어 철근 간격 | 식 (4.2-3), (4.2-4) | `serviceability.max_bar_spacing` |
| $\kappa_{cr}$ = 280 (건조환경) / 210 (그 외) | — | 4.2.3(4) | `serviceability.KAPPA_CR_*` |
| $f_s \approx \frac{2}{3} f_y$ | 간이 계산 | 4.2.3(4) | `serviceability.service_steel_stress` |

### 세장 기둥 (4.4)

| 식 | 내용 | 조문 | 구현 |
|---|---|---|---|
| $r = 0.3h$ (직사각형), $0.25D$ (원형) | 회전반지름 | 4.4.1 | `slender.radius_of_gyration` |
| $kl_u/r \le 34 - 12(M_1/M_2) \le 40$ | 횡구속 골조 한계 | 4.4.1 | `slender.slenderness_limit` |
| $kl_u/r \le 22$ | 비횡구속 골조 한계 | 4.4.1 | 〃 |
| $EI = 0.4E_cI_g/(1+\beta_{dns})$ | 휨강성 (간편식) | 4.4.2 | `slender.flexural_stiffness` |
| $EI = (0.2E_cI_g + E_sI_{se})/(1+\beta_{dns})$ | 휨강성 (정밀식) | 4.4.2 | 〃 |
| $P_c = \pi^2 EI/(kl_u)^2$ | 임계좌굴하중 | 4.4.2 | `slender.critical_buckling_load` |
| $\delta_{ns} = C_m/(1 - P_u/0.75P_c) \ge 1.0$ | 모멘트확대계수 | 4.4.2 | `slender.moment_magnifier_braced` |
| $C_m = 0.6 + 0.4(M_1/M_2) \ge 0.4$ | — | 4.4.2 | 〃 |
| $M_{2,min} = P_u(15 + 0.03h)$ | 최소 편심 모멘트 | 4.4.2 | `slender.minimum_moment` |

---

## 전단 및 비틀림 — KDS 14 20 22

### 콘크리트 전단강도 (4.2.1)

| 식 | 내용 | 조문 | 구현 |
|---|---|---|---|
| $V_c = \frac{1}{6}\lambda\sqrt{f_{ck}}\,b_wd$ | 간편식 | 식 (4.2-1) | `shear.concrete_shear_strength` |
| $V_c = \frac{1}{6}\left(1 + \frac{N_u}{14A_g}\right)\lambda\sqrt{f_{ck}}\,b_wd$ | 축압축 | 식 (4.2-2) | 〃 |
| $V_c = \left(0.16\lambda\sqrt{f_{ck}} + 17.6\rho_w\frac{V_ud}{M_u}\right)b_wd$ | 정밀식 | 식 (4.2-3) | 〃 |
| $V_c \le 0.29\lambda\sqrt{f_{ck}}\,b_wd$, $V_ud/M_u \le 1.0$ | 정밀식 상한 | 4.2.1(2)① | 〃 |
| $V_c = \frac{1}{6}\left(1 + \frac{N_u}{3.5A_g}\right)\lambda\sqrt{f_{ck}}\,b_wd$ | 축인장 ($N_u$ 는 음) | 식 (4.2-6) | 〃 |

### 전단철근 (4.3)

| 식 | 내용 | 조문 | 구현 |
|---|---|---|---|
| $A_{v,min} = 0.0625\sqrt{f_{ck}}\,b_ws/f_{yt} \ge 0.35 b_ws/f_{yt}$ | 최소 전단철근 | 식 (4.3-1) | `shear.minimum_shear_reinforcement` |
| $V_s = A_vf_{yt}d/s$ | 수직스터럽 | 식 (4.3-3) | `shear.shear_reinforcement_strength` |
| $V_s = A_vf_{yt}(\sin\alpha+\cos\alpha)d/s$ | 경사스터럽 | 식 (4.3-4) | 〃 |
| $V_s \le \frac{2}{3}\sqrt{f_{ck}}\,b_wd$ | 전단철근 상한 | 4.3.4(9) | `shear.max_shear_reinforcement_strength` |
| $s \le \min(d/2,\ 600\ \text{mm})$ | 간격 제한 | 4.3.2(1) | `shear.max_stirrup_spacing` |
| $V_s > \frac{1}{3}\sqrt{f_{ck}}b_wd$ 이면 위 간격의 1/2 | — | 4.3.2(3) | 〃 |
| $V_u > \frac{1}{2}\phi V_c$ 이면 최소 전단철근 배치 | — | 4.3.3(1) | `shear.check_shear` |

### 비틀림 (4.4, 4.5)

| 식 | 내용 | 조문 | 구현 |
|---|---|---|---|
| $T_u < \phi\frac{\lambda\sqrt{f_{ck}}}{12}\frac{A_{cp}^2}{p_{cp}}$ | 비틀림 무시 | 4.4.1(1)① | `shear.torsion_negligible` |
| $T_{cr} = \frac{1}{3}\lambda\sqrt{f_{ck}}\frac{A_{cp}^2}{p_{cp}}$ | 균열 비틀림모멘트 | 4.4.2 | `shear.cracking_torque` |
| $T_n = \frac{2A_oA_tf_{yt}}{s}\cot\theta$, $A_o = 0.85A_{oh}$ | 비틀림강도 | 4.5 | `shear.torsional_strength` |
| $A_l = \frac{A_t}{s}p_h\frac{f_{yt}}{f_y}\cot^2\theta$ | 종방향 비틀림철근 | 4.5 | `shear.longitudinal_torsion_reinforcement` |
| $\sqrt{\left(\frac{V_u}{b_wd}\right)^2 + \left(\frac{T_up_h}{1.7A_{oh}^2}\right)^2} \le \phi\left(\frac{V_c}{b_wd} + \frac{2}{3}\sqrt{f_{ck}}\right)$ | 단면 크기 | 4.5 | `shear.check_torsion_section` |

---

## 사용성 — KDS 14 20 30

| 식 | 내용 | 조문 | 구현 |
|---|---|---|---|
| $I_e = (M_{cr}/M_a)^3 I_g + [1-(M_{cr}/M_a)^3]I_{cr} \le I_g$ | 유효단면2차모멘트 | 식 (4.2-1) | `serviceability.effective_moment_of_inertia` |
| $M_{cr} = f_r I_g / y_t$ | 균열모멘트 | 식 (4.2-2) | `serviceability.cracking_moment` |
| $f_r = 0.63\lambda\sqrt{f_{ck}}$ | 파괴계수 | 4.2.1(3) | `kds.modulus_of_rupture` |
| $\lambda_\Delta = \xi/(1+50\rho')$ | 장기 추가처짐 계수 | 식 (4.2-4) | `serviceability.long_term_deflection_factor` |
| $\xi$ = 1.0 / 1.2 / 1.4 / 2.0 (3·6·12개월·5년 이상) | 시간경과계수 | 4.2.1(5) | `serviceability.CREEP_FACTOR` |
| 보 $l/16$·$l/18.5$·$l/21$·$l/8$; 1방향 슬래브 $l/20$·$l/24$·$l/28$·$l/10$ | 최소 두께 | 표 4.2-1 | `serviceability.MINIMUM_THICKNESS_RATIO` |
| $\times (0.43 + f_y/700)$ | $f_y \ne 400$ 보정 | 표 4.2-1 주 2) | `serviceability.minimum_thickness` |
| $\times (1.65 - 0.00031 m_c) \ge 1.09$ | 경량콘크리트 보정 | 표 4.2-1 주 1) | 〃 |
| $l/180$·$l/360$ (활하중 즉시처짐), $l/480$·$l/240$ (부착 후 처짐) | 최대 허용처짐 | 표 4.2-2 | `serviceability.DEFLECTION_LIMIT` |

---

## 내구성 — KDS 14 20 40

| 내용 | 조문 | 구현 |
|---|---|---|
| 노출등급 16종 (E0, EC1~4, ES1~4, EF1~4, EA1~3) | 표 4.1-1 | `durability.EXPOSURE_REQUIREMENTS` |
| 노출등급별 최소 설계기준압축강도 21~35 MPa | 표 4.1-3 | 〃 |
| 노출범주 EC·ES 는 KDS 14 20 50(4.3) 피복 이상 | 4.1.4(2) | `durability.check_durability(cover_min=...)` |
| 물-결합재비·결합재·공기량·염화물량은 KCS 14 20 10(1.10) | 4.1.4(3) | 위임 (구현 없음) |

---

## 철근상세 — KDS 14 20 50

| 내용 | 조문 | 구현 |
|---|---|---|
| 최소 피복두께 (수중 100, 흙 75, 옥외 50/40, 옥내 40/20, 쉘 20 mm) | 4.3.1(1) | `detailing.MINIMUM_COVER` |
| $f_{ck} \ge 40$ MPa 이면 옥내 보·기둥 10 mm 저감 | 4.3.1(1)④나 | `detailing.minimum_cover` |
| 보 $\max(d_b, 25\ \text{mm}, \frac{4}{3}$ 골재$)$; 기둥 $\max(1.5d_b, 40\ \text{mm}, \cdots)$ | 4.2 | `detailing.minimum_bar_spacing` |
| 수축·온도철근비 0.0020 ($f_y\le400$), $0.0020\cdot400/f_y$, 하한 0.0014 | 4.6.2(1) | `serviceability.shrinkage_temperature_reinforcement` |
| 단위 폭 m 당 1,800 mm² 상한 | 4.6.2(2) | 〃 |
| 간격 $\le \min(5h,\ 450\ \text{mm})$ | 4.6.2(3) | `serviceability.shrinkage_temperature_spacing` |

---

## 정착 및 이음 — KDS 14 20 52

| 식 | 내용 | 조문 | 구현 |
|---|---|---|---|
| $l_{db} = \dfrac{0.6 d_b f_y}{\lambda\sqrt{f_{ck}}}$ | 인장 기본정착길이 | 식 (4.1-1) | `detailing.LDB_FACTOR` |
| 보정계수 $0.8\alpha\beta$ / $\alpha\beta$ / $1.2\alpha\beta$ / $1.5\alpha\beta$ | 배근 조건 × 철근 크기 | 표 4.1-1 | `detailing.DEVELOPMENT_TABLE_FACTOR` |
| $\alpha$ = 1.3 (상부철근) / 1.0 | 철근배치 위치계수 | 4.1.2(2)① | `detailing.development_length_tension` |
| $\beta$ = 1.5 / 1.2 / 1.0 | 도막계수 | 4.1.2(2)② | 〃 |
| $\alpha\beta \le 1.7$ (에폭시 도막 상부철근) | — | 4.1.2(2)③ | 〃 |
| $l_d = \dfrac{0.90 d_b f_y}{\lambda\sqrt{f_{ck}}}\dfrac{\alpha\beta\gamma}{(c+K_{tr})/d_b}$ | 인장 정밀식 | 식 (4.1-2) | `detailing.development_length_tension_detailed` |
| $(c+K_{tr})/d_b \le 2.5$, $\gamma$ = 0.8 (D19 이하) / 1.0 | — | 4.1.2(3) | 〃 |
| $l_d \ge 300$ mm | 인장 최소 정착길이 | 4.1.2(1) | `detailing.LD_MIN` |
| $l_{db} = \max\left(\dfrac{0.25 d_b f_y}{\lambda\sqrt{f_{ck}}},\ 0.043 d_b f_y\right)$ | 압축 기본정착길이 | 식 (4.1-3) | `detailing.development_length_compression` |
| $\times 0.75$ (나선철근·D13 띠철근 100 mm 이하 구속) | 압축 보정계수 | 4.1.3(3)② | 〃 |
| $l_{dc} \ge 200$ mm | 압축 최소 정착길이 | 4.1.3(1) | `detailing.LDC_MIN` |
| $l_{hb} = \dfrac{0.24\beta d_b f_y}{\lambda\sqrt{f_{ck}}}$ | 표준갈고리 기본정착길이 | 4.1.5(2) | `detailing.development_length_hook` |
| $l_{dh} \ge \max(8d_b,\ 150\ \text{mm})$ | — | 4.1.5(1) | 〃 |
| A급 $1.0l_d$, B급 $1.3l_d$, $\ge 300$ mm | 인장 겹침이음 | 4.5 | `detailing.lap_splice_tension` |
| $l_s = 0.072f_yd_b$ ($f_y\le400$), $(0.13f_y{-}24)d_b$ ($f_y>400$) | 압축 겹침이음 | 4.5 | `detailing.lap_splice_compression` |

---

## 프리스트레스트 콘크리트 — KDS 14 20 60

### 허용응력 (4.2)

| 값 | 대상 | 조문 | 구현 |
|---|---|---|---|
| $\min(0.80f_{pu},\ 0.94f_{py})$ | 긴장재 — 긴장 중 | 4.2.2 | `psc.allowable_tendon_stress` |
| $\min(0.74f_{pu},\ 0.82f_{py})$ | 긴장재 — 정착 직후 | 4.2.2 | 〃 |
| $0.70f_{pu}$ | 포스트텐션 정착장치·커플러 | 4.2.2 | 〃 |
| 압축 $0.60f_{ci}$ (일부 $0.70f_{ci}$), 인장 $0.25\sqrt{f_{ci}}$ (단순지지 단부 $0.50\sqrt{f_{ci}}$) | 도입 직후 콘크리트 | 4.2.2 | `psc.allowable_concrete_stress_transfer` |
| 압축 $0.45f_{ck}$ (지속), $0.60f_{ck}$ (전체) | 사용하중 콘크리트 | 4.2.2 | `psc.allowable_concrete_stress_service` |
| U: $f_t \le 0.63\sqrt{f_{ck}}$, T: $\le 1.0\sqrt{f_{ck}}$, C: 제한 없음 | 균열등급 | 4.2.1 | 〃 |

### 프리스트레스 손실 (4.3)

| 식 | 내용 | 조문 | 구현 |
|---|---|---|---|
| $P_{px} = P_{pj}e^{-(Kl_{px} + \mu_p\alpha_{px})}$ | 마찰 손실 | 4.3 | `psc.friction_loss` |
| $P_{px} = P_{pj}/(1 + Kl_{px} + \mu_p\alpha_{px})$ | 근사식 ($\le 0.3$) | 4.3 | 〃 |
| $\Delta f_p = (\Delta l/l)E_p$ | 정착장치 활동 | 4.3 | `psc.anchorage_set_loss` |
| $\Delta f_p = (E_p/E_{ci})f_{cgp}$ | 탄성변형 (프리텐션) | 4.3 | `psc.elastic_shortening_loss` |
| $\Delta f_p = \frac{N-1}{2N}(E_p/E_{ci})f_{cgp}$ | 탄성변형 (포스트텐션) | 4.3 | 〃 |
| $\Delta f_p = \phi_{cr}(E_p/E_c)(f_{cgp}-f_{cds})$ | 크리프 | 4.3 | `psc.creep_loss` |
| $\Delta f_p = \varepsilon_{sh}E_p$ | 건조수축 | 4.3 | `psc.shrinkage_loss` |
| $\Delta f_p = f_{pi}\frac{\log t}{k}\left(\frac{f_{pi}}{f_{py}}-0.55\right)$, $k$ = 45 / 10 | 릴랙세이션 | 4.3 | `psc.relaxation_loss` |

### 휨강도 (4.4)

| 식 | 내용 | 조문 | 구현 |
|---|---|---|---|
| $f_{ps} = f_{pu}\left[1 - \frac{\gamma_p}{\beta_1}\left\{\rho_p\frac{f_{pu}}{f_{ck}} + \frac{d}{d_p}(\omega-\omega')\right\}\right]$ | 부착 긴장재 | 식 (4.4-1) | `psc.tendon_stress_bonded` |
| $\gamma_p$ = 0.55 ($f_{py}/f_{pu}\ge0.80$), 0.40 ($\ge0.85$), 0.28 ($\ge0.90$) | — | 4.4.2(3) | `psc.GAMMA_P` |
| $f_{ps} = f_{pe} + 70 + \frac{f_{ck}}{100\rho_p} \le \min(f_{py},\ f_{pe}{+}420)$ | 비부착, $l/h \le 35$ | 식 (4.4-2) | `psc.tendon_stress_unbonded` |
| $f_{ps} = f_{pe} + 70 + \frac{f_{ck}}{300\rho_p} \le \min(f_{py},\ f_{pe}{+}210)$ | 비부착, $l/h > 35$ | 식 (4.4-3) | 〃 |
| 압축지배 0.002, 인장지배 0.005 (고정값) | PSC 변형률한계 | KDS 14 20 20 4.1.2(3), (4) | `psc.EPS_Y_PSC`, `psc.EPS_TL_PSC` |

---

## KDS 조문이 아닌 것

다음은 KDS 의 조문이 아니라 문헌에서 널리 쓰이는 근사법이다. 설계에 쓸 때는
엄밀해와 대조하기를 권한다.

| 식 | 내용 | 출처 | 구현 |
|---|---|---|---|
| $\left(\frac{M_{ux}}{\phi M_{nx}}\right)^\alpha + \left(\frac{M_{uy}}{\phi M_{ny}}\right)^\alpha \le 1.0$ | 등하중선법 | 문헌 | `biaxial.load_contour` |
| $\frac{1}{P_n} = \frac{1}{P_{nx}} + \frac{1}{P_{ny}} - \frac{1}{P_o}$ | Bresler 역하중법 | 문헌 | `biaxial.bresler_reciprocal` |

또한 다음은 구현상의 가정이며 KDS 조문이 아니다.

| 항목 | 채택한 값 | 이유 |
|---|---|---|
| 사용 응력-변형률 압축 상한 | $0.85f_{ck}$ | 모멘트-곡률 해석의 발산 방지 |
| 철근 파단변형률 | 0.05 (변경 가능) | KDS 는 휨강도 산정 시 상한을 규정하지 않음 |
| 단면 내 철근 강도가 여럿일 때 | 가장 높은 $f_y$ 기준 | 보수측 |

자세한 내용은 [구현 시 채택한 가정](kds.md#구현-시-채택한-가정)을 참고한다.
