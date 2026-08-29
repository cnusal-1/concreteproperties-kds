"""KDS 24 14 21 재료 규정 시험.

값은 KDS 24 14 21 원문(표 1.4-1, 표 3.1-3, 식 (3.1-1), (3.1-38)~(3.1-48))과
대조한다.
"""

from __future__ import annotations

import pytest

from concreteproperties_kds.kds import (
    elastic_modulus as elastic_modulus_kds14,
)
from concreteproperties_kds.kds import (
    parabolic_parameters,
)
from concreteproperties_kds.kds24 import (
    ALPHA_CC,
    PHI_C_ULS,
    PHI_S_ULS,
    characteristic_tensile_strength,
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

# KDS 24 14 21 표 3.1-3 — (fck, n, eps_co, eps_cu)
TABLE_3_1_3 = [
    (40, 2.00, 0.0020, 0.0033),
    (50, 1.92, 0.0021, 0.0032),
    (60, 1.50, 0.0022, 0.0031),
    (70, 1.29, 0.0023, 0.0030),
    (80, 1.22, 0.0024, 0.0029),
    (90, 1.20, 0.0025, 0.0028),
]


@pytest.mark.parametrize(("fck", "n", "eps_co", "eps_cu"), TABLE_3_1_3)
def test_curve_parameters_match_table(fck, n, eps_co, eps_cu):
    """식 (3.1-40)~(3.1-42) 가 표 3.1-3 을 재현한다."""
    got = curve_parameters(fck=fck)

    assert got[0] == pytest.approx(n, abs=0.005)
    assert got[1] == pytest.approx(eps_co, abs=1e-6)
    assert got[2] == pytest.approx(eps_cu, abs=1e-6)


def test_curve_matches_kds14_table():
    """곡선 형상은 KDS 14 20 20 표 4.1-1 과 같다.

    두 기준의 차이는 곡선의 최대값(설계압축강도인가 0.85fck 인가)에 있지,
    형상에 있지 않다.
    """
    for fck in (18, 27, 40, 50, 60, 70, 80, 90):
        n24, co24, cu24 = curve_parameters(fck=fck)
        n14, co14, cu14, _, _ = parabolic_parameters(fck=fck)

        assert n24 == pytest.approx(n14)
        assert co24 == pytest.approx(co14)
        assert cu24 == pytest.approx(cu14)


def test_material_factors():
    """표 1.4-1 — 극한·극단상황은 (0.65, 0.90), 사용·피로는 (1.0, 1.0)."""
    assert material_factors("극한") == (0.65, 0.90)
    assert material_factors("극단상황") == (0.65, 0.90)
    assert material_factors("사용") == (1.00, 1.00)
    assert material_factors("피로") == (1.00, 1.00)

    with pytest.raises(ValueError, match="limit_state"):
        material_factors("보통")


def test_design_compressive_strength():
    """식 (3.1-47) — f_cd = phi_c * 0.85 * f_ck."""
    for fck in (18, 27, 40, 60, 90):
        assert design_compressive_strength(fck=fck) == pytest.approx(
            PHI_C_ULS * ALPHA_CC * fck
        )

    # 사용한계상태에서는 재료계수가 1.0 이므로 0.85fck 가 된다
    assert design_compressive_strength(fck=40, phi_c=1.0) == pytest.approx(34.0)


def test_design_yield_strength():
    """f_yd = phi_s * f_y."""
    assert design_yield_strength(fy=400) == pytest.approx(360.0)
    assert design_yield_strength(fy=500) == pytest.approx(450.0)
    assert design_yield_strength(fy=400, phi_s=1.0) == pytest.approx(400.0)


def test_mean_compressive_strength():
    """식 (3.1-1) — delta f 는 4 / 보간 / 6 MPa."""
    assert mean_compressive_strength(fck=30) == pytest.approx(34.0)
    assert mean_compressive_strength(fck=40) == pytest.approx(44.0)
    assert mean_compressive_strength(fck=50) == pytest.approx(55.0)
    assert mean_compressive_strength(fck=60) == pytest.approx(66.0)
    assert mean_compressive_strength(fck=80) == pytest.approx(86.0)


def test_tensile_strengths():
    """f_ctm = 0.30 f_cm^(2/3), f_ctk = 0.70 f_ctm."""
    fck = 30
    f_cm = mean_compressive_strength(fck=fck)

    assert mean_tensile_strength(fck=fck) == pytest.approx(0.30 * f_cm ** (2 / 3))
    assert characteristic_tensile_strength(fck=fck) == pytest.approx(
        0.70 * mean_tensile_strength(fck=fck)
    )
    assert design_tensile_strength(fck=fck) == pytest.approx(
        PHI_C_ULS * characteristic_tensile_strength(fck=fck)
    )


def test_elastic_modulus_matches_kds14():
    r"""탄성계수 식이 KDS 14 20 10 과 사실상 같다.

    KDS 24 14 21 3.1.2.2(1) 은 일반식 :math:`E_c = 0.077 m_c^{1.5}\sqrt[3]{f_{cm}}`
    만 규정한다. KDS 14 20 10 은 보통중량 콘크리트에 대해 계수를 8,500 으로
    반올림한 식 (4.3-2) 를 따로 두는데, 2300 kg/m3 을 일반식에 넣으면
    8,493 이 나온다. 0.08 % 차이이며 같은 식으로 보아도 된다.
    """
    for fck in (21, 27, 40, 60):
        assert elastic_modulus(fck=fck) == pytest.approx(
            elastic_modulus_kds14(fck=fck, m_c=2300.0), rel=1e-3
        )

    assert pytest.approx(8493.4, abs=0.1) == 0.077 * 2300.0**1.5


def test_design_stress_boundaries():
    """식 (3.1-38), (3.1-39) 의 경계값."""
    fck = 40
    _, eps_co, eps_cu = curve_parameters(fck=fck)
    f_cd = design_compressive_strength(fck=fck)

    assert design_stress(fck=fck, eps_c=0.0) == pytest.approx(0.0)
    assert design_stress(fck=fck, eps_c=-0.001) == pytest.approx(0.0)
    assert design_stress(fck=fck, eps_c=eps_co) == pytest.approx(f_cd)
    assert design_stress(fck=fck, eps_c=eps_cu) == pytest.approx(f_cd)


def test_profile_carries_no_tension():
    """인장측에서 응력이 0 이어야 한다."""
    profile = design_profile(fck=40)

    for eps in (-0.0001, -0.001, -0.01):
        assert profile.get_stress(strain=eps) == pytest.approx(0.0)


def test_equivalent_block_matches_table():
    """포물선-직선과 등가인 블록 계수가 표 4.1-1(KDS 14) 값과 맞는다.

    KDS 는 alpha 0.80, beta 0.40 (fck 40 이하) 으로 반올림해 싣고 있다.
    수치적분 결과는 0.798, 0.412 로, beta 는 표의 반올림 폭이 조금 크다.
    """
    alpha, beta = equivalent_block(fck=40)

    assert alpha == pytest.approx(0.80, abs=0.01)
    assert beta == pytest.approx(0.41, abs=0.01)


def test_service_limit_state_removes_material_factors():
    """사용한계상태에서는 재료계수가 1.0 이라 설계강도가 기준값이 된다."""
    phi_c, phi_s = material_factors("사용")

    assert design_compressive_strength(fck=40, phi_c=phi_c) == pytest.approx(
        ALPHA_CC * 40
    )
    assert design_yield_strength(fy=400, phi_s=phi_s) == pytest.approx(400.0)
    assert PHI_S_ULS == 0.90
