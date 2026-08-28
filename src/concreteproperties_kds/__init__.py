"""concreteproperties_kds.

``concreteproperties`` 를 국가건설기준 **KDS 14 20 (콘크리트구조 설계기준)** 에
맞추어 사용하기 위한 설계기준 확장 패키지.

모듈 구성
---------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 모듈
     - 대상 기준
   * - :mod:`~concreteproperties_kds.kds`
     - 휨 및 압축 (KDS 14 20 10, KDS 14 20 20)
   * - :mod:`~concreteproperties_kds.loads`
     - 하중조합 (KDS 14 20 10 4.2.2)
   * - :mod:`~concreteproperties_kds.shear`
     - 전단 및 비틀림 (KDS 14 20 22)
   * - :mod:`~concreteproperties_kds.serviceability`
     - 사용성 (KDS 14 20 30)
   * - :mod:`~concreteproperties_kds.durability`
     - 내구성 (KDS 14 20 40)
   * - :mod:`~concreteproperties_kds.detailing`
     - 철근상세·정착·이음 (KDS 14 20 50, KDS 14 20 52)
   * - :mod:`~concreteproperties_kds.slender`
     - 세장 기둥 (KDS 14 20 20 4.4)
   * - :mod:`~concreteproperties_kds.psc`
     - 프리스트레스트 (KDS 14 20 60)
   * - :mod:`~concreteproperties_kds.biaxial`
     - 2축 휨 간략식 (문헌)

설계식에는 KDS 조문과 식 번호를 표기하였다. 전체 목록은 문서의
"설계식 목록" 을 참고한다.
"""

from concreteproperties_kds import (
    biaxial,
    detailing,
    durability,
    loads,
    psc,
    serviceability,
    shear,
    slender,
)
from concreteproperties_kds.biaxial import (
    BiaxialCheck,
    bresler_reciprocal,
    check_bresler_reciprocal,
    check_load_contour,
    load_contour,
)
from concreteproperties_kds.detailing import (
    DetailingSummary,
    bar_area,
    bar_diameter,
    development_length_compression,
    development_length_hook,
    development_length_tension,
    development_length_tension_detailed,
    lap_splice_compression,
    lap_splice_tension,
    minimum_bar_spacing,
    minimum_cover,
    summarise_detailing,
)
from concreteproperties_kds.durability import (
    DurabilityCheck,
    ExposureClass,
    check_durability,
    governing_requirements,
    print_exposure_table,
)
from concreteproperties_kds.kds import (
    KDS,
    KDS14202022,
    compression_controlled_strain_limit,
    elastic_modulus,
    minimum_flexural_moment,
    minimum_flexural_moment_alternative,
    minimum_net_tensile_strain,
    modulus_of_rupture,
    stress_block_parameters,
    tension_controlled_strain_limit,
)
from concreteproperties_kds.loads import (
    LOAD_COMBINATIONS,
    LoadCombination,
    alpha_h,
    evaluate_all,
    minimum_strength,
    print_combinations,
    required_strength,
)
from concreteproperties_kds.psc import (
    KDSPrestressed,
    PrestressLosses,
    allowable_concrete_stress_service,
    allowable_concrete_stress_transfer,
    allowable_tendon_stress,
    anchorage_set_loss,
    capacity_reduction_factor_psc,
    creep_loss,
    elastic_shortening_loss,
    friction_loss,
    relaxation_loss,
    shrinkage_loss,
    tendon_stress_bonded,
    tendon_stress_unbonded,
)
from concreteproperties_kds.serviceability import (
    DeflectionCheck,
    check_crack_control,
    check_deflection,
    cracking_moment,
    deflection_limit,
    deflection_target,
    effective_moment_of_inertia,
    long_term_deflection_factor,
    max_bar_spacing,
    minimum_thickness,
    service_steel_stress,
    shrinkage_temperature_reinforcement,
    shrinkage_temperature_spacing,
    total_deflection,
)
from concreteproperties_kds.shear import (
    ShearCheck,
    check_shear,
    check_torsion_section,
    concrete_shear_strength,
    cracking_torque,
    longitudinal_torsion_reinforcement,
    max_shear_reinforcement_strength,
    max_stirrup_spacing,
    minimum_shear_reinforcement,
    required_stirrup_spacing,
    shear_reinforcement_strength,
    torsion_negligible,
    torsional_strength,
)
from concreteproperties_kds.slender import (
    SlendernessCheck,
    check_slenderness,
    critical_buckling_load,
    flexural_stiffness,
    minimum_moment,
    moment_magnifier_braced,
    radius_of_gyration,
    slenderness_limit,
    slenderness_ratio,
)

__all__ = [
    "KDS",
    "KDS14202022",
    "LOAD_COMBINATIONS",
    "BiaxialCheck",
    "DeflectionCheck",
    "DetailingSummary",
    "DurabilityCheck",
    "ExposureClass",
    "KDSPrestressed",
    "LoadCombination",
    "PrestressLosses",
    "ShearCheck",
    "SlendernessCheck",
    "allowable_concrete_stress_service",
    "allowable_concrete_stress_transfer",
    "allowable_tendon_stress",
    "alpha_h",
    "anchorage_set_loss",
    "bar_area",
    "bar_diameter",
    "biaxial",
    "bresler_reciprocal",
    "capacity_reduction_factor_psc",
    "check_bresler_reciprocal",
    "check_crack_control",
    "check_deflection",
    "check_durability",
    "check_load_contour",
    "check_shear",
    "check_slenderness",
    "check_torsion_section",
    "compression_controlled_strain_limit",
    "concrete_shear_strength",
    "cracking_moment",
    "cracking_torque",
    "creep_loss",
    "critical_buckling_load",
    "deflection_limit",
    "deflection_target",
    "detailing",
    "development_length_compression",
    "development_length_hook",
    "development_length_tension",
    "development_length_tension_detailed",
    "durability",
    "effective_moment_of_inertia",
    "elastic_modulus",
    "elastic_shortening_loss",
    "evaluate_all",
    "flexural_stiffness",
    "friction_loss",
    "governing_requirements",
    "lap_splice_compression",
    "lap_splice_tension",
    "load_contour",
    "loads",
    "long_term_deflection_factor",
    "longitudinal_torsion_reinforcement",
    "max_bar_spacing",
    "max_shear_reinforcement_strength",
    "max_stirrup_spacing",
    "minimum_bar_spacing",
    "minimum_cover",
    "minimum_flexural_moment",
    "minimum_flexural_moment_alternative",
    "minimum_moment",
    "minimum_net_tensile_strain",
    "minimum_shear_reinforcement",
    "minimum_strength",
    "minimum_thickness",
    "modulus_of_rupture",
    "moment_magnifier_braced",
    "print_combinations",
    "print_exposure_table",
    "psc",
    "radius_of_gyration",
    "relaxation_loss",
    "required_stirrup_spacing",
    "required_strength",
    "service_steel_stress",
    "serviceability",
    "shear",
    "shear_reinforcement_strength",
    "shrinkage_loss",
    "shrinkage_temperature_reinforcement",
    "shrinkage_temperature_spacing",
    "slender",
    "slenderness_limit",
    "slenderness_ratio",
    "stress_block_parameters",
    "summarise_detailing",
    "tendon_stress_bonded",
    "tendon_stress_unbonded",
    "tension_controlled_strain_limit",
    "torsion_negligible",
    "torsional_strength",
    "total_deflection",
]
