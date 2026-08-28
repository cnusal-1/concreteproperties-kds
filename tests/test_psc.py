"""프리스트레스트 콘크리트 검증 시험 (KDS 14 20 60)."""

from __future__ import annotations

import numpy as np
import pytest
from concreteproperties import (
    PrestressedSection,
    SteelStrand,
    StrandHardening,
    add_bar_rectangular_array,
)
from sectionproperties.pre.library import rectangular_section

from concreteproperties_kds import KDS
from concreteproperties_kds.psc import (
    EPS_TL_PSC,
    EPS_Y_PSC,
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

FPU = 1860.0
FPY = 0.9 * FPU  # 저릴랙세이션 강연선


# ---------------------------------------------------------------------------
# 허용응력
# ---------------------------------------------------------------------------


def test_allowable_tendon_stress():
    """긴장재의 허용응력을 확인한다 (KDS 14 20 60 4.2.2)."""
    assert allowable_tendon_stress(
        fpu=FPU, fpy=FPY, stage="jacking"
    ) == pytest.approx(min(0.80 * FPU, 0.94 * FPY))

    assert allowable_tendon_stress(
        fpu=FPU, fpy=FPY, stage="anchorage"
    ) == pytest.approx(min(0.74 * FPU, 0.82 * FPY))

    assert allowable_tendon_stress(
        fpu=FPU, fpy=FPY, stage="anchorage_device"
    ) == pytest.approx(0.70 * FPU)

    with pytest.raises(ValueError, match="stage"):
        allowable_tendon_stress(fpu=FPU, fpy=FPY, stage="service")


def test_allowable_concrete_transfer():
    """프리스트레스 도입 직후 콘크리트 허용응력을 확인한다."""
    f_c, f_t = allowable_concrete_stress_transfer(fci=30)

    assert f_c == pytest.approx(0.60 * 30)
    assert f_t == pytest.approx(-0.25 * np.sqrt(30))

    _, f_t_end = allowable_concrete_stress_transfer(
        fci=30, simply_supported_end=True
    )
    assert f_t_end == pytest.approx(-0.50 * np.sqrt(30))

    f_c_hi, _ = allowable_concrete_stress_transfer(fci=30, reinforced_zone=True)
    assert f_c_hi == pytest.approx(0.70 * 30)


def test_allowable_concrete_service():
    """사용하중 상태 콘크리트 허용응력을 확인한다."""
    f_c_full, f_t = allowable_concrete_stress_service(fck=40)
    f_c_sus, _ = allowable_concrete_stress_service(fck=40, sustained=True)

    assert f_c_full == pytest.approx(0.60 * 40)
    assert f_c_sus == pytest.approx(0.45 * 40)
    assert f_t == pytest.approx(-0.63 * np.sqrt(40))

    _, f_t_partial = allowable_concrete_stress_service(fck=40, crack_class="T")
    assert f_t_partial == pytest.approx(-1.00 * np.sqrt(40))

    _, f_t_cracked = allowable_concrete_stress_service(fck=40, crack_class="C")
    assert f_t_cracked == float("-inf")

    with pytest.raises(ValueError, match="crack_class"):
        allowable_concrete_stress_service(fck=40, crack_class="X")


# ---------------------------------------------------------------------------
# 프리스트레스 손실
# ---------------------------------------------------------------------------


def test_friction_loss():
    """마찰 손실의 지수식과 근사식을 확인한다."""
    p_pj = 1000e3
    mu, alpha, k, length = 0.20, 0.15, 6.6e-7, 20000.0

    p_px, loss = friction_loss(
        p_pj=p_pj, mu_p=mu, alpha_px=alpha, k_wobble=k, l_px=length
    )

    exponent = mu * alpha + k * length
    assert p_px == pytest.approx(p_pj * np.exp(-exponent))
    assert loss == pytest.approx(p_pj - p_px)

    p_approx, _ = friction_loss(
        p_pj=p_pj,
        mu_p=mu,
        alpha_px=alpha,
        k_wobble=k,
        l_px=length,
        approximate=True,
    )
    # 지수 <= 0.3 이면 근사식과 지수식이 가깝다
    assert p_approx == pytest.approx(p_px, rel=1e-2)


def test_anchorage_set_loss():
    """정착장치 활동 손실을 확인한다."""
    assert anchorage_set_loss(slip=6.0, e_p=195e3, length=20000) == pytest.approx(
        6.0 / 20000 * 195e3
    )

    with pytest.raises(ValueError, match="length"):
        anchorage_set_loss(slip=6.0, e_p=195e3, length=0)


def test_elastic_shortening_loss():
    """탄성변형 손실의 프리텐션·포스트텐션 식을 확인한다."""
    f_cgp, e_p, e_ci = 12.0, 195e3, 30000.0

    loss_pre = elastic_shortening_loss(f_cgp=f_cgp, e_p=e_p, e_ci=e_ci)
    assert loss_pre == pytest.approx(e_p / e_ci * f_cgp)

    loss_post = elastic_shortening_loss(
        f_cgp=f_cgp, e_p=e_p, e_ci=e_ci, post_tensioned=True, n_tendons=4
    )
    assert loss_post == pytest.approx(3 / 8 * loss_pre)

    # 긴장재가 1개면 포스트텐션 손실은 0
    loss_single = elastic_shortening_loss(
        f_cgp=f_cgp, e_p=e_p, e_ci=e_ci, post_tensioned=True, n_tendons=1
    )
    assert loss_single == pytest.approx(0.0)

    with pytest.raises(ValueError, match="e_ci"):
        elastic_shortening_loss(f_cgp=f_cgp, e_p=e_p, e_ci=0)


def test_creep_and_shrinkage_loss():
    """크리프·건조수축 손실을 확인한다."""
    assert creep_loss(
        f_cgp=12.0, e_p=195e3, e_c=33000, creep_coefficient=2.0
    ) == pytest.approx(2.0 * 195e3 / 33000 * 12.0)

    assert shrinkage_loss(e_p=195e3, eps_sh=300e-6) == pytest.approx(
        300e-6 * 195e3
    )


def test_relaxation_loss():
    """릴랙세이션 손실을 확인한다."""
    f_pi = 0.70 * FPU

    loss_low = relaxation_loss(f_pi=f_pi, fpy=FPY, low_relaxation=True)
    loss_normal = relaxation_loss(f_pi=f_pi, fpy=FPY, low_relaxation=False)

    assert loss_low > 0
    # 저릴랙세이션 강연선의 손실이 훨씬 작다
    assert loss_low == pytest.approx(loss_normal * 10 / 45)

    # fpi/fpy <= 0.55 이면 손실이 없다
    assert relaxation_loss(f_pi=0.5 * FPY, fpy=FPY) == pytest.approx(0.0)

    with pytest.raises(ValueError, match="fpy"):
        relaxation_loss(f_pi=f_pi, fpy=0)


def test_prestress_losses_summary():
    """손실 요약 객체의 합산이 맞는지 확인한다."""
    losses = PrestressLosses(
        f_pj=1400.0,
        friction=40.0,
        anchorage=30.0,
        elastic=50.0,
        creep=80.0,
        shrinkage=60.0,
        relaxation=25.0,
    )

    assert losses.immediate == pytest.approx(120.0)
    assert losses.time_dependent == pytest.approx(165.0)
    assert losses.total == pytest.approx(285.0)
    assert losses.f_pe == pytest.approx(1115.0)
    assert losses.loss_ratio == pytest.approx(285.0 / 1400.0)


# ---------------------------------------------------------------------------
# 긴장재의 극한 응력
# ---------------------------------------------------------------------------


def test_tendon_stress_bonded():
    """부착 긴장재의 fps 를 손계산과 대조한다."""
    f_ps = tendon_stress_bonded(
        fpu=FPU, fck=40, rho_p=0.004, gamma_p=0.28, beta_1=0.80
    )

    expected = FPU * (1 - 0.28 / 0.80 * (0.004 * FPU / 40))
    assert f_ps == pytest.approx(expected)
    assert f_ps < FPU


def test_tendon_stress_bonded_with_rebar():
    """인장철근이 있으면 fps 가 낮아진다."""
    f_ps_0 = tendon_stress_bonded(fpu=FPU, fck=40, rho_p=0.004)
    f_ps_1 = tendon_stress_bonded(
        fpu=FPU, fck=40, rho_p=0.004, d=600, d_p=650, omega=0.10
    )

    assert f_ps_1 < f_ps_0

    with pytest.raises(ValueError, match="fck"):
        tendon_stress_bonded(fpu=FPU, fck=0, rho_p=0.004)


def test_tendon_stress_unbonded():
    """비부착 긴장재의 fps 와 상한을 확인한다."""
    f_pe = 1100.0

    f_ps = tendon_stress_unbonded(
        f_pe=f_pe, fck=40, rho_p=0.004, fpy=FPY, span_depth_ratio=30
    )
    assert f_ps == pytest.approx(
        min(f_pe + 70 + 40 / (100 * 0.004), FPY, f_pe + 420)
    )

    # 세장한 부재는 증가분이 작다
    f_ps_slender = tendon_stress_unbonded(
        f_pe=f_pe, fck=40, rho_p=0.004, fpy=FPY, span_depth_ratio=40
    )
    assert f_ps_slender < f_ps

    # fpy 상한
    f_ps_cap = tendon_stress_unbonded(
        f_pe=1650.0, fck=40, rho_p=0.001, fpy=FPY
    )
    assert f_ps_cap == pytest.approx(FPY)

    with pytest.raises(ValueError, match="rho_p"):
        tendon_stress_unbonded(f_pe=f_pe, fck=40, rho_p=0, fpy=FPY)


# ---------------------------------------------------------------------------
# 강도감소계수
# ---------------------------------------------------------------------------


def test_capacity_reduction_factor_psc():
    """PSC 부재의 강도감소계수를 확인한다."""
    assert capacity_reduction_factor_psc(eps_t=0.001) == pytest.approx(0.65)
    assert capacity_reduction_factor_psc(eps_t=EPS_Y_PSC) == pytest.approx(0.65)
    assert capacity_reduction_factor_psc(eps_t=EPS_TL_PSC) == pytest.approx(0.85)
    assert capacity_reduction_factor_psc(eps_t=0.010) == pytest.approx(0.85)
    # 변화구간 중앙
    assert capacity_reduction_factor_psc(eps_t=0.0035) == pytest.approx(0.75)

    # 나선철근
    assert capacity_reduction_factor_psc(
        eps_t=0.001, column_type="spiral"
    ) == pytest.approx(0.70)

    with pytest.raises(ValueError, match="column_type"):
        capacity_reduction_factor_psc(eps_t=0.001, column_type="hoop")


# ---------------------------------------------------------------------------
# PrestressedSection 통합
# ---------------------------------------------------------------------------


def psc_beam():
    """400 x 800 포스트텐션 보 단면을 생성한다."""
    kds = KDS()
    conc = kds.create_concrete_material(compressive_strength=40)

    strand = SteelStrand(
        name="SWPC 7B 15.2mm",
        density=7.85e-6,
        stress_strain_profile=StrandHardening(
            yield_strength=FPY,
            elastic_modulus=195e3,
            fracture_strain=0.035,
            breaking_strength=FPU,
        ),
        colour="slategrey",
        prestress_stress=1100.0,
    )

    geom = rectangular_section(d=800, b=400, material=conc)
    geom = add_bar_rectangular_array(
        geometry=geom,
        area=138.7,  # SWPC 7B 15.2 mm 1가닥
        material=strand,
        n_x=4,
        x_s=80,
        anchor=(80, 120),
        n=8,
    )

    return kds, PrestressedSection(geom)


def test_kds_prestressed_flexural_capacity():
    """PSC 단면의 설계 휨강도가 공칭강도에 phi 를 곱한 값인지 확인한다."""
    _, ps_sec = psc_beam()

    kds_ps = KDSPrestressed(column_type="tie")
    kds_ps.assign_prestressed_section(ps_sec)

    f_res, u_res, phi = kds_ps.ultimate_bending_capacity(positive=True)

    assert 0.65 - 1e-9 <= phi <= 0.85 + 1e-9
    assert f_res.m_x == pytest.approx(phi * u_res.m_x)
    assert u_res.m_x > 0


def test_kds_prestressed_strain_and_phi_consistent():
    """반환된 phi 가 순인장변형률과 정합한지 확인한다."""
    _, ps_sec = psc_beam()

    kds_ps = KDSPrestressed()
    kds_ps.assign_prestressed_section(ps_sec)

    _, u_res, phi = kds_ps.ultimate_bending_capacity(positive=True)
    eps_t = kds_ps.net_tensile_strain(theta=0, d_n=u_res.d_n)

    assert phi == pytest.approx(capacity_reduction_factor_psc(eps_t=eps_t))


def test_kds_prestressed_invalid_column_type():
    """정의되지 않은 횡철근 종류는 예외가 발생한다."""
    with pytest.raises(ValueError, match="column_type"):
        KDSPrestressed(column_type="hoop")
