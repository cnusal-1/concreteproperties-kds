"""KDS 24 (교량설계기준, 한계상태설계법) 모듈.

KDS 14 가 강도설계법이라면 KDS 24 는 한계상태설계법이다. 두 기준은 같은
역학을 쓰지만 **안전율을 거는 자리가 다르다** — KDS 14 는 공칭강도에
강도감소계수를 한 번 곱하고, KDS 24 는 재료마다 재료계수를 곱해 설계
재료강도를 만든다.

구현 범위

- ``materials`` — 재료계수(표 1.4-1), 설계 재료강도, 단면설계용 응력-변형률
  (KDS 24 14 21 1.4, 3.1)
- ``design_code`` — :class:`KDS24` 설계기준 클래스, 극한한계상태 휨·축력
  (KDS 24 14 21 4.1.1)

두 기준의 대응은 문서의 [KDS 14 와 KDS 24 비교] 를 참고한다.
"""

from __future__ import annotations

from .design_code import (
    KDS24,
    biaxial_exponent,
    minimum_eccentricity,
)
from .materials import (
    ALPHA_CC,
    ES,
    MATERIAL_FACTORS,
    PHI_C_ULS,
    PHI_S_ULS,
    characteristic_tensile_strength,
    concrete_curve_table,
    curve_parameters,
    design_compressive_strength,
    design_profile,
    design_stress,
    design_tensile_strength,
    design_yield_strength,
    elastic_modulus,
    equivalent_block,
    material_factors,
    mean_compressive_strength,
    mean_tensile_strength,
)

__all__ = [
    "ALPHA_CC",
    "ES",
    "KDS24",
    "MATERIAL_FACTORS",
    "PHI_C_ULS",
    "PHI_S_ULS",
    "biaxial_exponent",
    "characteristic_tensile_strength",
    "concrete_curve_table",
    "curve_parameters",
    "design_compressive_strength",
    "design_profile",
    "design_stress",
    "design_tensile_strength",
    "design_yield_strength",
    "elastic_modulus",
    "equivalent_block",
    "material_factors",
    "mean_compressive_strength",
    "mean_tensile_strength",
    "minimum_eccentricity",
]
