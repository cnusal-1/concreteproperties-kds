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

| 모듈 | 대상 기준 |
|---|---|
| `kds` | KDS 14 20 10, 14 20 20 — 휨 및 압축 |
| `loads` | KDS 14 20 01 — 하중조합 |
| `shear` | KDS 14 20 22 — 전단 및 비틀림 |
| `serviceability` | KDS 14 20 30 — 사용성 |
| `durability` | KDS 14 20 40 — 내구성 |
| `detailing` | KDS 14 20 50, 52 — 철근상세·정착·이음 |
| `slender` | KDS 14 20 20 4.4 — 세장 기둥 |
| `psc` | KDS 14 20 60 — 프리스트레스트 |
| `biaxial` | 2축 휨 간략식 |

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
| `minimum_flexural_reinforcement(fck, fy, b_w, d)` | $A_{s,min}$ (mm²) | KDS 14 20 20 4.2.2 |

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

## `loads` — 하중조합 (KDS 14 20 01)

| 이름 | 내용 |
|---|---|
| `LoadCombination(name, factors, description)` | 하중조합. `evaluate(loads)` |
| `LOAD_COMBINATIONS` | U1~U8 |
| `LOAD_SYMBOLS`, `ROOF_LOADS` | 하중 기호 |
| `required_strength(loads, combinations, reduce_live_load)` | `(최대 U, 지배 조합)` |
| `evaluate_all(loads, ...)` | 모든 조합 결과 (큰 순서) |
| `print_combinations(loads, ...)` | 표 출력 |
| `LIVE_LOAD_FACTOR_REDUCED` | 0.5 |

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
| `minimum_thickness(span, member, support, fy)` | 최소 두께 |
| `deflection_limit(span, condition)` | 허용처짐 |
| `deflection_target(condition)` | `"live"` / `"attached"` |
| `check_deflection(...)` → `DeflectionCheck` | 처짐 종합 검토 |
| `max_bar_spacing(fs, c_c, dry_environment)` | 균열 제어 최대 간격 |
| `service_steel_stress(fy)` | $f_s = \frac{2}{3}f_y$ |
| `check_crack_control(...)` | `(fs, s_max, ok)` |
| `shrinkage_temperature_reinforcement(fy, a_g)` | 수축·온도철근량 |
| `CREEP_FACTOR`, `MINIMUM_THICKNESS_RATIO`, `DEFLECTION_LIMIT`, `KAPPA_CR_DRY`, `KAPPA_CR_OTHER` | 편집 가능한 표·상수 |

## `durability` — 내구성 (KDS 14 20 40)

| 이름 | 내용 |
|---|---|
| `ExposureClass` | 노출등급 하나의 요구사항 |
| `EXPOSURE_REQUIREMENTS` | 등급 16종의 표 |
| `check_durability(exposure_class, fck, water_binder_ratio, cover)` → `DurabilityCheck` | 검토 |
| `governing_requirements(exposure_classes)` | `(fck_min, wb_max, cover_min)` |
| `print_exposure_table()` | 등급표 출력 |
| `MAX_CHLORIDE_ION` | 최대 염화물 이온량 |

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
| `BAR_PROPERTIES`, `MINIMUM_COVER`, `DEVELOPMENT_SIMPLE_FACTOR` | 편집 가능한 표 |
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
| `allowable_tendon_stress(fpu, fpy, stage)` | 긴장재 허용응력 |
| `allowable_concrete_stress_transfer(fci, simply_supported_end)` | 도입 직후 허용응력 |
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
| 정의되지 않은 노출등급·철근 호칭·재하기간·지지조건 | `ValueError` |
