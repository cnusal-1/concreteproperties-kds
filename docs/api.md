# API 참조

`concreteproperties_kds` 가 제공하는 것만 정리한다. `concreteproperties` 본체의
API 는 [원 문서](https://robbievanleeuwen.github.io/concrete-properties/api.html) 를
참고한다.

## 클래스

### `KDS14202022` (별칭 `KDS`)

```python
KDS14202022(column_type: str = "tie")
```

KDS 14 20 설계기준 클래스. `column_type` 은 `"tie"`(띠철근) 또는
`"spiral"`(나선철근).

#### 속성

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

#### 메서드

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

## 함수

단면 없이 재료 상수만 구할 때 쓴다.

| 함수 | 반환 | 근거 |
|---|---|---|
| `stress_block_parameters(fck)` | `(eps_cu, eta, beta_1)` | KDS 14 20 20 표 4.1-1 |
| `elastic_modulus(fck, m_c=2300.0)` | 콘크리트 탄성계수 (MPa) | KDS 14 20 10 4.3.3 |
| `modulus_of_rupture(fck, lambda_c=1.0)` | 파괴계수 (MPa) | KDS 14 20 30 4.2.1 |
| `compression_controlled_strain_limit(fy)` | $\varepsilon_y$ | KDS 14 20 20 4.1.2 |
| `tension_controlled_strain_limit(fy)` | $\varepsilon_{t,tl}$ | KDS 14 20 20 4.1.2 |
| `minimum_net_tensile_strain(fy)` | $\varepsilon_{t,min}$ | KDS 14 20 20 4.1.2 |
| `minimum_flexural_reinforcement(fck, fy, b_w, d)` | $A_{s,min}$ (mm²) | KDS 14 20 20 4.2.2 |

## 모듈 상수

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

## 예외

| 상황 | 예외 |
|---|---|
| `column_type` 이 `"tie"`/`"spiral"` 이 아님 | `ValueError` |
| $f_{ck}$ 가 18~90 MPa 범위 밖 | `ValueError` |
| $f_y$ 가 300~600 MPa 범위 밖 | `ValueError` |
| 단면에 요소망 철근(`Steel`)이 포함됨 | `ValueError` |
| 단면에 격점철근(`SteelBar`)이 없음 | `ValueError` |
| 계수 축력이 최대 설계 축강도 초과 | `AnalysisError` |
| 계수 축력이 설계 인장강도 초과 | `AnalysisError` |
