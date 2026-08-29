# API 참조

`concreteproperties_kds` 가 제공하는 것만 정리한다. `concreteproperties` 본체의
API 는 [원 문서](https://robbievanleeuwen.github.io/concrete-properties/api.html) 를
참고한다.

모든 이름은 최상위 패키지에서 바로 가져올 수 있고, 모듈로도 접근할 수 있다.

```python
from concreteproperties_kds import KDS, check_shear          # 최상위
from concreteproperties_kds.shear import check_shear         # 모듈
from concreteproperties_kds import shear                     # 모듈 객체
```

**KDS 14 20 (강도설계법)** — 최상위 모듈

| 모듈 | 대상 기준 |
|---|---|
| `kds` | KDS 14 20 10, 14 20 20 — 휨 및 압축 |
| `loads` | KDS 14 20 10 4.2.2 — 하중조합 |
| `shear` | KDS 14 20 22 — 전단 및 비틀림 |
| `serviceability` | KDS 14 20 30 — 사용성 |
| `durability` | KDS 14 20 40 — 내구성 |
| `detailing` | KDS 14 20 50, 52 — 철근상세·정착·이음 |
| `slender` | KDS 14 20 20 4.4 — 세장 기둥 |
| `psc` | KDS 14 20 60 — 프리스트레스트 |
| `biaxial` | 2축 휨 간략식 |

**KDS 24 (한계상태설계법, 교량)** — `kds24` 서브패키지

| 모듈 | 대상 기준 |
|---|---|
| `kds24.materials` | KDS 24 14 21 1.4, 3.1 — 재료계수와 설계 재료강도 |
| `kds24.design_code` | KDS 24 14 21 4.1.1 — `KDS24` 클래스 |
| `kds24.loads` | KDS 24 12 11 4.1 — 하중조합 |
| `kds24.live_load` | KDS 24 12 21 4.3, 4.4 — 차량활하중 KL-510 |
| `kds24.shear` | KDS 24 14 21 4.1.2 — 변각 트러스 전단 |
| `kds24.serviceability` | KDS 24 14 21 4.2, 4.3 — 사용성과 피로 |
| `kds24.deck` | KDS 24 10 11 4.6.2, 24 14 21 4.6.5 — 교량 바닥판 |
| `kds24.psc` | KDS 24 14 21 1.5.7, 3.3 — 도입응력과 손실 |
| `kds24.girder` | KDS 24 14 21 4.1, 4.2 — PSC I형 거더 |

`kds24` 의 이름도 서브패키지에서 바로 가져올 수 있다.

```python
from concreteproperties_kds.kds24 import KDS24, check_shear, girder_live_load
```

## 자동 생성 API 문서

각 모듈의 모든 함수·클래스·상수의 docstring 을 그대로 옮긴 참조 문서이다.
설계식에는 KDS 조문과 식 번호가 표기되어 있다.

```{eval-rst}
.. autosummary::
    :toctree: gen
    :caption: API 참조
    :template: custom-module-template.rst
    :recursive:

    concreteproperties_kds.kds
    concreteproperties_kds.loads
    concreteproperties_kds.shear
    concreteproperties_kds.serviceability
    concreteproperties_kds.durability
    concreteproperties_kds.detailing
    concreteproperties_kds.slender
    concreteproperties_kds.psc
    concreteproperties_kds.biaxial
    concreteproperties_kds.kds24.materials
    concreteproperties_kds.kds24.design_code
    concreteproperties_kds.kds24.loads
    concreteproperties_kds.kds24.live_load
    concreteproperties_kds.kds24.shear
    concreteproperties_kds.kds24.serviceability
    concreteproperties_kds.kds24.deck
    concreteproperties_kds.kds24.psc
    concreteproperties_kds.kds24.girder
```

아래는 손으로 정리한 요약이다. 설계식과 조문의 대응만 보려면
[설계식 목록](user_guide/design_codes/equations.md)이 더 편하다.

---

## `kds` — 휨 및 압축 (KDS 14 20 10, KDS 14 20 20)

### 클래스

#### `KDS14202022` (별칭 `KDS`)

```python
KDS14202022(column_type: str = "tie")
```

KDS 14 20 설계기준 클래스. `column_type` 은 `"tie"`(띠철근) 또는
`"spiral"`(나선철근).

##### 속성

`assign_concrete_section()` 호출 후 사용할 수 있다.

| 속성 | 의미 |
|---|---|
| `column_type` | `"tie"` 또는 `"spiral"` |
| `phi_comp` | 압축지배단면의 강도감소계수 (0.65 / 0.70) |
| `alpha_max` | 최대 축강도 저감계수 (0.80 / 0.85) |
| `fy` | 단면 내 철근의 최대 항복강도 |
| `eps_y` | 압축지배변형률한계 |
| `eps_tl` | 인장지배변형률한계 |
| `squash_load` | 순수압축 하중 $P_o$ |
| `tensile_load` | 순수인장 하중 $P_{nt}$ |
| `concrete_section` | 할당된 `ConcreteSection` 객체 |

##### 메서드

| 메서드 | 반환 |
|---|---|
| `assign_concrete_section(concrete_section)` | — |
| `create_concrete_material(compressive_strength, lambda_c=1.0, m_c=2300.0, colour="lightgrey")` | `Concrete` |
| `create_steel_material(yield_strength=400, fracture_strain=0.05, colour="grey")` | `SteelBar` |
| `squash_tensile_load()` | `(squash_load, tensile_load)` |
| `max_axial_strength()` | `(n_max_nominal, n_max_design)` |
| `net_tensile_strain(theta, d_n)` | `float` — 순인장변형률 $\varepsilon_t$ |
| `capacity_reduction_factor(eps_t)` | `float` — 강도감소계수 $\phi$ |
| `section_classification(eps_t)` | `str` — `"압축지배단면"` / `"변화구간단면"` / `"인장지배단면"` |
| `check_flexural_ductility(theta=0, n_design=0)` | `(eps_t, eps_t_min, ok)` |
| `check_minimum_flexural_reinforcement(theta=0, m_u=None)` | `(phi_m_n, m_cr, m_required, ok)` |
| `ultimate_bending_capacity(theta=0, n_design=0)` | `(설계강도, 공칭강도, phi)` |
| `moment_interaction_diagram(theta=0, limits=None, control_points=None, labels=None, n_points=24, n_spacing=None, progress_bar=True)` | `(설계 상관도, 공칭 상관도, phi 목록)` |
| `biaxial_bending_diagram(n_design=0, n_points=48, progress_bar=True)` | `(설계 상관도, phi 목록)` |

`DesignCode` 로부터 상속되어 강도감소계수 없이 그대로 전달되는 메서드:
`get_gross_properties()`, `get_transformed_gross_properties()`,
`calculate_cracked_properties()`, `moment_curvature_analysis()`,
`calculate_uncracked_stress()`, `calculate_cracked_stress()`,
`calculate_service_stress()`, `calculate_ultimate_stress()`.

### 함수

단면 없이 재료 상수만 구할 때 쓴다.

| 함수 | 반환 | 근거 |
|---|---|---|
| `stress_block_parameters(fck)` | `(eps_cu, eta, beta_1)` | KDS 14 20 20 표 4.1-2 |
| `elastic_modulus(fck, m_c=2300.0)` | 콘크리트 탄성계수 (MPa) | KDS 14 20 10 4.3.3 |
| `modulus_of_rupture(fck, lambda_c=1.0)` | 파괴계수 (MPa) | KDS 14 20 30 4.2.1 |
| `compression_controlled_strain_limit(fy)` | $\varepsilon_y$ | KDS 14 20 20 4.1.2 |
| `tension_controlled_strain_limit(fy)` | $\varepsilon_{t,tl}$ | KDS 14 20 20 4.1.2 |
| `minimum_net_tensile_strain(fy)` | $\varepsilon_{t,min}$ | KDS 14 20 20 4.1.2 |
| `minimum_flexural_moment(m_cr)` | $1.2 M_{cr}$ | KDS 14 20 20 4.2.2 |
| `minimum_flexural_moment_alternative(m_u)` | $\frac{4}{3} M_u$ | KDS 14 20 20 4.2.2(2) |

### 모듈 상수

| 상수 | 값 |
|---|---|
| `STRESS_BLOCK_FCK` | `[40, 50, 60, 70, 80, 90]` |
| `STRESS_BLOCK_EPS_CU` | `[0.0033, 0.0032, 0.0031, 0.0030, 0.0029, 0.0028]` |
| `STRESS_BLOCK_ETA` | `[1.00, 0.97, 0.95, 0.91, 0.87, 0.84]` |
| `STRESS_BLOCK_BETA_1` | `[0.80, 0.80, 0.76, 0.74, 0.72, 0.70]` |
| `ES` | `200000.0` |
| `PHI_TENSION` | `0.85` |
| `PHI_COMP_TIE` | `0.65` |
| `PHI_COMP_SPIRAL` | `0.70` |
| `ALPHA_MAX_TIE` | `0.80` |
| `ALPHA_MAX_SPIRAL` | `0.85` |


---

## `loads` — 하중조합 (KDS 14 20 10 4.2.2)

| 이름 | 내용 |
|---|---|
| `LoadCombination(name, equation, factors, roof, alpha_h_symbols, live_load_reducible, description)` | 하중조합. `evaluate(loads, depth, reduce_live_load)` |
| `LOAD_COMBINATIONS` | 식 (4.2-1)~(4.2-8) 을 전개한 12개 |
| `alpha_h(depth)` | 연직토압 보정계수 |
| `required_strength(loads, combinations, depth, reduce_live_load)` | `(최대 U, 지배 조합)` |
| `minimum_strength(loads, ...)` | `(최소 U, 해당 조합)` — 부양·전도 검토 |
| `evaluate_all(loads, ...)` | 모든 조합 결과 (큰 순서) |
| `print_combinations(loads, ...)` | 표 출력 |
| `LOAD_SYMBOLS`, `ROOF_LOADS` | 하중 기호 |
| `LIVE_LOAD_REDUCTION_THRESHOLD`, `LIVE_LOAD_FACTOR_REDUCED` | 5.0 kN/m², 0.5 |

## `shear` — 전단 및 비틀림 (KDS 14 20 22)

| 이름 | 내용 |
|---|---|
| `concrete_shear_strength(fck, b_w, d, lambda_c, n_u, a_g, rho_w, v_u, m_u)` | $V_c$ |
| `shear_reinforcement_strength(a_v, fyt, d, s, alpha)` | $V_s$ |
| `max_shear_reinforcement_strength(fck, b_w, d)` | $V_s$ 상한 |
| `minimum_shear_reinforcement(fck, b_w, s, fyt)` | $A_{v,min}$ |
| `max_stirrup_spacing(fck, b_w, d, v_s)` | 최대 간격 |
| `check_shear(...)` → `ShearCheck` | 전단 종합 검토 |
| `required_stirrup_spacing(...)` | 필요한 스터럽 간격 |
| `cracking_torque(fck, a_cp, p_cp, lambda_c)` | $T_{cr}$ |
| `torsion_negligible(...)` | 비틀림 무시 가능 여부 |
| `torsional_strength(a_t, s, a_oh, fyt, theta)` | $T_n$ |
| `longitudinal_torsion_reinforcement(...)` | $A_l$ |
| `check_torsion_section(...)` | `(소요응력, 한계응력, ok)` |
| `PHI_SHEAR`, `S_MAX_ABS`, `S_MAX_ABS_CLOSE` | 0.75, 600, 300 |

## `serviceability` — 사용성 (KDS 14 20 30)

| 이름 | 내용 |
|---|---|
| `effective_moment_of_inertia(m_a, m_cr, i_g, i_cr)` | $I_e$ (Branson) |
| `cracking_moment(fck, i_g, y_t, lambda_c)` | $M_{cr}$ |
| `long_term_deflection_factor(rho_prime, duration)` | $\lambda_\Delta$ |
| `total_deflection(...)` | `(장기 추가처짐, 전체 처짐)` |
| `minimum_thickness(span, member, support, fy, m_c)` | 최소 두께 |
| `deflection_limit(span, condition)` | 허용처짐 |
| `deflection_target(condition)` | `"live"` / `"attached"` |
| `check_deflection(...)` → `DeflectionCheck` | 처짐 종합 검토 |
| `max_bar_spacing(fs, c_c, dry_environment)` | 균열 제어 최대 간격 |
| `service_steel_stress(fy)` | $f_s = \frac{2}{3}f_y$ |
| `check_crack_control(...)` | `(fs, s_max, ok)` |
| `shrinkage_temperature_reinforcement(fy, a_g, width)` | 수축·온도철근량 |
| `shrinkage_temperature_spacing(thickness)` | 수축·온도철근 최대 간격 |
| `CREEP_FACTOR`, `MINIMUM_THICKNESS_RATIO`, `DEFLECTION_LIMIT`, `KAPPA_CR_DRY`, `KAPPA_CR_OTHER` | 편집 가능한 표·상수 |

## `durability` — 내구성 (KDS 14 20 40)

| 이름 | 내용 |
|---|---|
| `ExposureClass` | 노출등급 하나의 요구사항 (`fck_min`, `cover_required`) |
| `EXPOSURE_REQUIREMENTS` | 등급 16종의 표 |
| `check_durability(exposure_class, fck, cover, cover_min, water_binder_ratio)` → `DurabilityCheck` | 검토 |
| `governing_requirements(exposure_classes)` | 지배 최소 설계기준압축강도 (MPa) |
| `print_exposure_table()` | 등급표 출력 |
| `MAX_CHLORIDE_ION` | 참고용 최대 염화물 이온량 (KDS 규정 아님) |

## `detailing` — 철근상세·정착·이음 (KDS 14 20 50, 52)

| 이름 | 내용 |
|---|---|
| `bar_diameter(bar)`, `bar_area(bar)` | 공칭 지름·단면적 |
| `minimum_cover(condition, bar, fck)` | 최소 피복두께 |
| `minimum_bar_spacing(bar, aggregate_size, member)` | 최소 순간격 |
| `development_length_tension(...)` | 인장 정착길이 (약산식) |
| `development_length_tension_detailed(...)` | 인장 정착길이 (정밀식) |
| `development_length_compression(...)` | 압축 정착길이 |
| `development_length_hook(...)` | 표준갈고리 정착길이 |
| `lap_splice_tension(l_d, splice_class)` | 인장 겹침이음 |
| `lap_splice_compression(bar, fy, fck, l_dc)` | 압축 겹침이음 |
| `summarise_detailing(...)` → `DetailingSummary` | 위 값을 한 번에 |
| `BAR_PROPERTIES`, `MINIMUM_COVER`, `LDB_FACTOR`, `DEVELOPMENT_TABLE_FACTOR`, `COVER_REDUCTION_CONDITIONS` | 편집 가능한 표·상수 |
| `LD_MIN`, `LDC_MIN`, `LDH_MIN`, `LAP_MIN` | 300, 200, 150, 300 mm |

## `slender` — 세장 기둥 (KDS 14 20 20 4.4)

| 이름 | 내용 |
|---|---|
| `radius_of_gyration(section, h, i_g, a_g)` | 회전반지름 |
| `slenderness_ratio(k, l_u, r)` | 세장비 |
| `slenderness_limit(braced, m1, m2)` | 한계 세장비 |
| `flexural_stiffness(e_c, i_g, beta_dns, e_s, i_se)` | $EI$ |
| `critical_buckling_load(ei, k, l_u)` | $P_c$ |
| `moment_magnifier_braced(...)` | `(c_m, delta_ns)` |
| `minimum_moment(p_u, h)` | $M_{2,min}$ |
| `check_slenderness(...)` → `SlendernessCheck` | 종합 검토 |
| `PHI_K` | 0.75 |

## `psc` — 프리스트레스트 (KDS 14 20 60)

| 이름 | 내용 |
|---|---|
| `allowable_tendon_stress(fpu, fpy, stage)` | 긴장재 허용응력 (`"jacking"` / `"anchorage"` / `"anchorage_device"`) |
| `allowable_concrete_stress_transfer(fci, simply_supported_end, reinforced_zone)` | 도입 직후 허용응력 |
| `allowable_concrete_stress_service(fck, sustained, crack_class)` | 사용하중 허용응력 |
| `friction_loss(...)` | `(p_px, loss)` |
| `anchorage_set_loss(slip, e_p, length)` | 정착장치 활동 손실 |
| `elastic_shortening_loss(...)` | 탄성변형 손실 |
| `creep_loss(...)`, `shrinkage_loss(...)`, `relaxation_loss(...)` | 시간적 손실 |
| `PrestressLosses` | 손실 합산 (`immediate`, `time_dependent`, `total`, `f_pe`, `loss_ratio`) |
| `tendon_stress_bonded(...)`, `tendon_stress_unbonded(...)` | $f_{ps}$ |
| `capacity_reduction_factor_psc(eps_t, column_type)` | PSC 강도감소계수 |
| `KDSPrestressed` | `assign_prestressed_section`, `extreme_depth`, `net_tensile_strain`, `ultimate_bending_capacity` |
| `EPS_Y_PSC`, `EPS_TL_PSC`, `GAMMA_P`, `CRACK_CLASS_LIMIT` | 0.002, 0.005 등 |

## `biaxial` — 2축 휨 간략식

| 이름 | 내용 |
|---|---|
| `load_contour(m_ux, m_uy, m_nx, m_ny, alpha)` | 등하중선법 좌변 |
| `check_load_contour(...)` → `BiaxialCheck` | 등하중선법 검토 |
| `bresler_reciprocal(p_nx, p_ny, p_o)` | 역하중법 축강도 |
| `check_bresler_reciprocal(...)` → `BiaxialCheck` | 역하중법 검토 |
| `compare_with_exact(...)` | 여러 $\alpha$ 를 엄밀해와 비교 |

---

# KDS 24 (한계상태설계법)

## `kds24.materials` — 재료 (KDS 24 14 21 1.4, 3.1)

| 이름 | 내용 |
|---|---|
| `MATERIAL_FACTORS` | 표 1.4-1 — 한계상태별 $(\phi_c, \phi_s)$ |
| `PHI_C_ULS`, `PHI_S_ULS`, `ALPHA_CC`, `ES` | 0.65, 0.90, 0.85, 200,000 |
| `CURVE_FCK`, `CURVE_N`, `CURVE_EPS_CO`, `CURVE_EPS_CU` | 표 3.1-3 |
| `material_factors(limit_state)` | $(\phi_c, \phi_s)$ |
| `mean_compressive_strength(fck)` | $f_{cm}$, 식 (3.1-1) |
| `mean_tensile_strength(fck)`, `characteristic_tensile_strength(fck)` | $f_{ctm}$, $f_{ctk}$ |
| `elastic_modulus(fck, m_c)` | $E_c$ |
| `design_compressive_strength(fck, phi_c)` | $f_{cd}$, 식 (3.1-47) |
| `design_tensile_strength(fck, phi_c, alpha_t)` | $f_{ctd}$, 식 (3.1-48) |
| `design_yield_strength(fy, phi_s)` | $f_{yd}$ |
| `curve_parameters(fck)` | $(n, \varepsilon_{co}, \varepsilon_{cu})$ |
| `design_stress(fck, eps_c, phi_c)` | 식 (3.1-38), (3.1-39) |
| `design_profile(fck, phi_c, n_points)` | `ConcreteUltimateProfile` |
| `equivalent_block(fck, phi_c)` | $(\alpha_{eq}, \beta_{eq})$ — 수치적분 |
| `concrete_curve_table()` | 표 3.1-3 출력 |

## `kds24.design_code` — 설계기준 클래스 (KDS 24 14 21 4.1.1)

| 이름 | 내용 |
|---|---|
| `KDS24(phi_c=0.65, phi_s=0.90)` | 설계기준 객체 |
| `.create_concrete_material(...)`, `.create_steel_material(...)` | 재료계수가 반영된 재료 |
| `.assign_concrete_section(concrete_section)` | 단면 할당 |
| `.design_bending_capacity(theta, n_design)` | 설계휨강도 ($\phi$ 없음) |
| `.moment_interaction_diagram(theta, **kwargs)` | 설계 상관도 **하나** |
| `.biaxial_bending_diagram(n_design, **kwargs)` | 설계 2축 휨 상관도 |
| `.squash_tensile_load()`, `.net_tensile_strain(theta, d_n)` | — |
| `.minimum_moment(n_design, h)` | 최소편심에 의한 최소 휨모멘트 |
| `minimum_eccentricity(h)` | $e_{min} = \max(h/30, 20)$, 4.1.1.2(5) |
| `biaxial_exponent(n_ed, n_rd, shape)` | 식 (4.1-4) 의 지수 |

## `kds24.loads` — 하중조합 (KDS 24 12 11 4.1)

| 이름 | 내용 |
|---|---|
| `LOAD_COMBINATIONS`, `COMBINATIONS_BY_NAME` | 표 4.1-1 의 13개 조합 |
| `LoadCombination` | `evaluate(loads, permanent_kinds, maximise, deformation, gamma_tg, gamma_sd, gamma_eq, eta)` |
| `PERMANENT_LOAD_FACTORS`, `permanent_load_factor(kind, maximum)` | 표 4.1-2 |
| `load_modifier(ductility, redundancy, importance, maximum)` | $\eta$, 식 (1.3-2), (1.3-3) |
| `bridge_grade_factor(grade)`, `BRIDGE_GRADE_FACTORS` | 1 / 0.75 / 0.5625 |
| `evaluate_all(loads, limit_state, ...)`, `governing_combination(...)` | 전체 평가·지배 조합 |
| `LOAD_SYMBOLS`, `PERMANENT_SYMBOLS`, `LIVE_SYMBOLS` | 하중 기호 |

## `kds24.live_load` — 차량활하중 (KDS 24 12 21 4.3, 4.4)

| 이름 | 내용 |
|---|---|
| `TRUCK_AXLE_LOADS`, `TRUCK_AXLE_POSITIONS`, `TRUCK_TOTAL_LOAD` | KL-510 (48/192/135/135 kN, 12.0 m) |
| `number_of_lanes(roadway_width, plan_lane_width)` | 식 (4.3-1) |
| `lane_width(roadway_width, n_lanes)` | 식 (4.3-2) |
| `multiple_presence(n_lanes)` | 표 4.3-1 |
| `lane_load(span)` | 표 4.3-2 표준차로하중 |
| `truck_moment(span, step)`, `truck_shear(span, section, step)` | 단순보 최대 단면력 |
| `lane_moment(span, section)`, `lane_shear(span, section)` | 차로하중 단면력 |
| `girder_live_load(span, section, limit_state, step)` → `LiveLoadEffect` | 4.3.1.5 |
| `impact_factor(limit_state)`, `impact_buried(cover_depth)` | 표 4.4-1, 식 (4.4-1) |
| `fatigue_truck_moment(span, step)`, `truck_lane_fraction(n)`, `adtt_single_lane(adtt, n)` | 4.3.2 |

## `kds24.shear` — 전단 (KDS 24 14 21 4.1.2)

| 이름 | 내용 |
|---|---|
| `kappa(d)` | 크기 효과 $1 + \sqrt{200/d} \le 2$ |
| `nu(fck)` | 식 (4.1-12) 압축강도 유효계수 |
| `axial_stress(n_u, a_c, fck, phi_c)` | $f_n \le 0.2\phi_c f_{ck}$ |
| `concrete_shear_strength(...)` | 식 (4.1-7) |
| `minimum_concrete_shear_strength(...)` | 식 (4.1-8) |
| `design_concrete_shear_strength(...)` | 둘 중 큰 값 |
| `uncracked_shear_strength(...)` | 식 (4.1-9) — 휨균열 없는 PSC 구간 |
| `shear_reinforcement_strength(...)` | 식 (4.1-16) $V_{sd}$ |
| `max_shear_strength(...)` | 식 (4.1-17) $V_{d,max}$ |
| `alpha_cw(f_n, fck, phi_c)` | 식 (4.1-23) |
| `maximum_shear_reinforcement(...)`, `minimum_shear_reinforcement_ratio(...)` | 식 (4.1-18), (4.6-7) |
| `maximum_stirrup_spacing(d, alpha)` | 식 (4.6-8) |
| `check_shear(...)` → `ShearCheck` | 종합 검토 |
| `required_stirrup_spacing(...)` | 요구 간격 |
| `COT_THETA_MIN`, `COT_THETA_MAX`, `RHO_MAX`, `Z_RATIO` | 1.0, 2.5, 0.02, 0.9 |

## `kds24.serviceability` — 사용성과 피로 (KDS 24 14 21 4.2, 4.3)

| 이름 | 내용 |
|---|---|
| `EXPOSURE_MINIMUM_GRADE`, `DESIGN_GRADES`, `DesignGrade` | 표 4.2-1, 표 4.2-2 |
| `minimum_design_grade(exposure, member)` | 노출환경 → 설계등급 |
| `concrete_stress_limit(fck, sustained)` | $0.45f_{ck}$ / $0.6f_{ck}$ |
| `steel_stress_limit(fy)`, `tendon_stress_limit(fpu)` | $0.8f_y$, $0.65f_{pu}$ |
| `minimum_crack_reinforcement(a_ct, f_ct, f_s, k_c, k)` | 식 (4.2-1) |
| `stress_distribution_factor(...)`, `nonuniform_stress_factor(width)` | $k_c$, $k$ |
| `MAX_BAR_DIAMETER`, `max_bar_diameter(f_s, member)` | 표 4.2-4 |
| `MAX_BAR_SPACING`, `max_bar_spacing(f_s, member)` | 표 4.2-5 |
| `effective_tension_depth(h, d, c)` | $d_{cte}$ |
| `strain_difference(f_so, f_cte, rho_e, n, k_t)` | 식 (4.2-5) |
| `crack_spacing(...)`, `crack_spacing_unreinforced(h, c)` | 식 (4.2-7a), (4.2-7b) |
| `crack_width(...)` → `CrackWidthCheck` | 식 (4.2-4) |
| `web_effective_tensile_strength(f_2, fck)` | 식 (4.2-3) |
| `deflection_limit(span, pedestrian, cantilever)` | 4.2.4.1 |
| `fatigue_stress_range_limit(f_min, welded)` | 식 (4.3-1), (4.3-2) |
| `COUPLER_FATIGUE_STRENGTH`, `coupler_fatigue_strength(kind, n_cycles)` | 표 4.3-1 |
| `fatigue_check_required(f_dead_compression, f_live_tension)` | 4.3.1(4) |

---

## `kds24.deck` — 교량 바닥판 (KDS 24 10 11 4.6.2, 24 14 21 4.6.5)

| 이름 | 내용 |
|---|---|
| `WHEEL_LOAD`, `DECK_FCK` | 윤하중 96 kN, 바닥판 $f_{ck}$ 27 MPa |
| `MIN_THICKNESS_RC`, `MIN_THICKNESS_PSC`, `MIN_THICKNESS_EMPIRICAL` | 220 / 200 / 240 mm |
| `deck_span(girder_spacing, thickness, web_width)` | 4.6.2.3 |
| `live_load_moment(span, wheel_load, continuous, grade)` | 식 (4.6-1) |
| `wheel_width_parallel(span)`, `live_load_moment_parallel(span, grade)` | 4.6.2.4 |
| `cantilever_wheel_width(x, parallel)`, `cantilever_live_load_moment(...)` | 식 (4.6-4) |
| `dead_load_moment(w, span, kind)` | 표 4.6-2 |
| `distribution_steel_ratio(span, parallel)` | $120/\sqrt{L} \le 67\,\%$ |
| `nominal_cover(exposure, bar_diameter, exposed_deck, delta_dev, tendon)` | 식 (4.4-1), 표 4.4-4 |
| `deck_deflection_limit(span, pedestrian)` | 4.6.5.1 |
| `required_steel_area(...)`, `provided_steel_area(...)`, `bar_area(diameter)` | 휨 설계 |
| `minimum_flexural_steel(d, fck, fy, width)` | 최소 철근량 |
| `design_deck(...)` → `DeckDesign` | 바닥판 종합 설계 |

---

## `kds24.psc` — 도입응력과 손실 (KDS 24 14 21 1.5.7, 3.3)

| 이름 | 내용 |
|---|---|
| `max_jacking_stress(fpu, fpy, overtension)` | 식 (1.5-7) |
| `stress_after_transfer(fpy, fpu, reading)` | 식 (1.5-9) — **읽기가 갈린다** |
| `concrete_stress_limit_at_transfer(fck_t, pretension)` | 식 (1.5-8) |
| `friction_loss(p_o, theta, x, mu, k)`, `CURVATURE_FRICTION` | 식 (1.5-11), 표 1.5-2 |
| `anchorage_set_loss(slip, length, a_p, e_p)` | 정착장치 활동 |
| `elastic_shortening_loss(a_p, delta_fc, e_cm, n_tendon, post_tension)` | 식 (1.5-10) |
| `relaxation_loss(f_pi, fpu, steel_class, hours, rho_1000)` | 식 (3.3-1)~(3.3-3) |
| `RELAXATION_COEFFICIENTS`, `RHO_1000` | 3.3.2(7)③ |
| `long_term_loss(...)` | 식 (1.5-12) |
| `PrestressLosses` | 손실 내역 |

:::{warning}
`stress_after_transfer` 의 `reading` 인자를 볼 것. 식 $(1.5\text{-}9)$ 는 원문
그대로 읽으면 한계가 $0.75 f_{py}$ 이지만, 대응하는 EN 1992-1-1 5.10.3(2) 와
바로 앞 식 $(1.5\text{-}7)$ 의 방식으로 읽으면 $\min(0.75 f_{pu},\ 0.85 f_{py})$
다. 1,860/1,600 강연선에서 1,200 vs 1,360 MPa 로 차이가 작지 않다.
:::

---

## `kds24.girder` — PSC I형 거더 (KDS 24 14 21 4.1, 4.2)

| 이름 | 내용 |
|---|---|
| `IGirder` | 단면 형상 (사다리꼴 구간 5 개) |
| `IGirder.properties()` → `SectionProperties` | 정확 적분한 단면 성질 |
| `IGirder.composite(deck_width, deck_thickness, modular_ratio, haunch)` | 합성 단면 |
| `IGirder.first_moment_above(y)` | 단면1차모멘트 $Q$ (정확 적분) |
| `EXAMPLE_SECTIONS` | **예시 단면 5 종 — 표준도가 아니다** |
| `TENDON_COVER`, `GAMMA_CONCRETE` | 기본 긴장재 피복 200 mm, 24.5 kN/m³ |
| `design_girder(...)` → `GirderCheck` | 손실·응력·휨강도 종합 검토 |

---

## 예외 정리

| 상황 | 예외 |
|---|---|
| `column_type` 이 `"tie"`/`"spiral"` 이 아님 | `ValueError` |
| $f_{ck}$ 18~90 MPa 범위 밖 | `ValueError` |
| $f_y$ 300~600 MPa 범위 밖 | `ValueError` |
| 단면에 요소망 철근(`Steel`) 포함 | `ValueError` |
| 단면에 격점철근(`SteelBar`) 없음 | `ValueError` |
| 계수 축력이 최대 설계 축강도 초과 | `AnalysisError` |
| 계수 축력이 설계 인장강도 초과 | `AnalysisError` |
| 전단철근으로도 요구 강도를 만족 못함 | `ValueError` |
| $P_u \ge 0.75 P_c$ (좌굴) | `ValueError` |
| 정의되지 않은 노출등급·철근 호칭·재하기간·지지조건·긴장 단계 | `ValueError` |
| (KDS 24) 재료계수가 0 이하이거나 1 초과 | `ValueError` |
| (KDS 24) $\cot\theta$ 가 1.0 ~ 2.5 밖 | `ValueError` |
| (KDS 24) 표 4.2-4·4.2-5 가 다루지 않는 철근 응력 | `ValueError` |
| (KDS 24) 표 4.1-2·표 4.2-1·표 4.3-1 에 없는 종류 | `ValueError` |
