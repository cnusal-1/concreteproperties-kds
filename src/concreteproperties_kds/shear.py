"""전단 및 비틀림 설계 (KDS 14 20 22).

부재의 설계 전단강도와 비틀림강도를 계산하고, 최소 전단철근량과 배치 간격
제한을 검토한다.

이 모듈의 함수는 단면 요소망과 무관한 순수 함수이므로, `concreteproperties` 의
단면 객체 없이도 사용할 수 있다. 폭 ``b_w`` 와 유효깊이 ``d`` 는 사용자가
직접 준다.

.. warning::

    KDS 14 20 22 는 2021년 개정에서 전단 규정이 상당히 바뀌었다. 이 모듈은
    널리 쓰이는 형태의 규정을 구현한 것이므로, 사용 전에
    :doc:`검증 대조표 </user_guide/design_codes/kds>` 를 확인한다.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# 전단과 비틀림의 강도감소계수 (KDS 14 20 10 4.3.3(2))
PHI_SHEAR = 0.75

# 스터럽 최대 간격 (KDS 14 20 22 4.3.2)
S_MAX_ABS = 600.0
S_MAX_ABS_CLOSE = 300.0


def concrete_shear_strength(
    fck: float,
    b_w: float,
    d: float,
    lambda_c: float = 1.0,
    n_u: float = 0.0,
    a_g: float = 0.0,
    rho_w: float | None = None,
    v_u: float | None = None,
    m_u: float | None = None,
) -> float:
    r"""콘크리트가 부담하는 전단강도 :math:`V_c` 를 반환한다.

    **KDS 14 20 22 4.2.1, 식 (4.2-1), (4.2-2), (4.2-3), (4.2-6)**

    간편식

    .. math::
        V_c = \frac{1}{6}\lambda\sqrt{f_{ck}}\, b_w d

    ``rho_w``, ``v_u``, ``m_u`` 를 모두 주면 상세식

    .. math::
        V_c = \left(0.16\lambda\sqrt{f_{ck}}
        + 17.6\,\rho_w \frac{V_u d}{M_u}\right) b_w d
        \le 0.29\lambda\sqrt{f_{ck}}\, b_w d

    을 사용하며, 이때 :math:`V_u d / M_u \le 1.0` 이다.

    축력이 작용하면 (``n_u``, ``a_g`` 지정) 다음 계수를 곱한다.

    .. math::
        \text{압축}\ (N_u > 0):\ 1 + \frac{N_u}{14 A_g}
        \qquad \text{(식 4.2-2)}

    .. math::
        \text{인장}\ (N_u < 0):\ 1 + \frac{N_u}{3.5 A_g}
        \qquad \text{(식 4.2-6)}

    :math:`N_u` 는 인장일 때 음(−)이며, 계수가 음수가 되면
    :math:`V_c = 0` 으로 본다.

    Args:
        fck: 콘크리트 설계기준압축강도 (MPa)
        b_w: 복부 폭 (mm)
        d: 유효깊이 (mm)
        lambda_c: 경량콘크리트계수. 기본값 ``1.0``.
        n_u: 계수 축력 (N). 압축이 양(+). 기본값 ``0``.
        a_g: 전체 단면적 (mm\ :sup:`2`). ``n_u`` 가 0 이 아니면 필요.
            기본값 ``0``.
        rho_w: 인장철근비 :math:`A_s / (b_w d)`. 기본값 ``None``.
        v_u: 계수 전단력 (N). 기본값 ``None``.
        m_u: 계수 휨모멘트 (N·mm). 기본값 ``None``.

    Raises:
        ValueError: ``n_u`` 가 0 이 아닌데 ``a_g`` 가 0 이하인 경우

    Returns:
        콘크리트가 부담하는 전단강도 :math:`V_c` (N)
    """
    sqrt_fck = lambda_c * np.sqrt(fck)

    # 상세식 적용 여부
    if rho_w is not None and v_u is not None and m_u is not None and m_u > 0:
        ratio = min(v_u * d / m_u, 1.0)
        v_c = (0.16 * sqrt_fck + 17.6 * rho_w * ratio) * b_w * d
        v_c = min(v_c, 0.29 * sqrt_fck * b_w * d)
    else:
        v_c = sqrt_fck * b_w * d / 6.0

    # 축력의 영향
    if n_u != 0.0:
        if a_g <= 0:
            msg = "축력이 작용하면 a_g (전체 단면적) 를 주어야 합니다."
            raise ValueError(msg)

        # 압축은 식 (4.2-2), 인장은 식 (4.2-6)
        factor = (
            1.0 + n_u / (14.0 * a_g) if n_u > 0 else 1.0 + n_u / (3.5 * a_g)
        )
        v_c *= max(factor, 0.0)

    return float(v_c)


def shear_reinforcement_strength(
    a_v: float,
    fyt: float,
    d: float,
    s: float,
    alpha: float = 90.0,
) -> float:
    r"""전단철근이 부담하는 전단강도 :math:`V_s` 를 반환한다.

    **KDS 14 20 22 4.3.4, 식 (4.3-3), (4.3-4)**

    수직스터럽 (:math:`\alpha = 90^\circ`)

    .. math::
        V_s = \frac{A_v f_{yt} d}{s}

    경사스터럽

    .. math::
        V_s = \frac{A_v f_{yt} (\sin\alpha + \cos\alpha) d}{s}

    Args:
        a_v: 간격 ``s`` 내 전단철근의 단면적 (mm\ :sup:`2`)
        fyt: 전단철근의 설계기준항복강도 (MPa)
        d: 유효깊이 (mm)
        s: 전단철근의 간격 (mm)
        alpha: 전단철근이 부재축과 이루는 각 (도). 기본값 ``90``.

    Raises:
        ValueError: ``s`` 가 0 이하인 경우

    Returns:
        전단철근이 부담하는 전단강도 :math:`V_s` (N)
    """
    if s <= 0:
        msg = "s 는 0 보다 커야 합니다."
        raise ValueError(msg)

    rad = np.radians(alpha)

    if abs(alpha - 90.0) < 1e-9:
        return float(a_v * fyt * d / s)

    return float(a_v * fyt * (np.sin(rad) + np.cos(rad)) * d / s)


def max_shear_reinforcement_strength(
    fck: float,
    b_w: float,
    d: float,
) -> float:
    r"""전단철근이 부담할 수 있는 전단강도의 상한을 반환한다.

    **KDS 14 20 22 4.3.4(9)**

    .. math::
        V_s \le \frac{2}{3}\sqrt{f_{ck}}\, b_w d

    Args:
        fck: 콘크리트 설계기준압축강도 (MPa)
        b_w: 복부 폭 (mm)
        d: 유효깊이 (mm)

    Returns:
        전단철근 전단강도의 상한 (N)
    """
    return float(2.0 / 3.0 * np.sqrt(fck) * b_w * d)


def minimum_shear_reinforcement(
    fck: float,
    b_w: float,
    s: float,
    fyt: float,
) -> float:
    r"""최소 전단철근량을 반환한다.

    **KDS 14 20 22 4.3.3(3), 식 (4.3-1)**

    .. math::
        A_{v,min} = \max\left(0.0625\sqrt{f_{ck}},\ 0.35\right)
        \frac{b_w s}{f_{yt}}

    Args:
        fck: 콘크리트 설계기준압축강도 (MPa)
        b_w: 복부 폭 (mm)
        s: 전단철근의 간격 (mm)
        fyt: 전단철근의 설계기준항복강도 (MPa)

    Returns:
        최소 전단철근량 (mm\ :sup:`2`)
    """
    return float(max(0.0625 * np.sqrt(fck), 0.35) * b_w * s / fyt)


def max_stirrup_spacing(
    fck: float,
    b_w: float,
    d: float,
    v_s: float,
) -> float:
    r"""전단철근의 최대 간격을 반환한다.

    **KDS 14 20 22 4.3.2(1), (3)**

    .. math::
        V_s \le \frac{1}{3}\sqrt{f_{ck}} b_w d \ \Rightarrow\
        s \le \min(d/2,\ 600\ \text{mm})

    .. math::
        V_s > \frac{1}{3}\sqrt{f_{ck}} b_w d \ \Rightarrow\
        s \le \min(d/4,\ 300\ \text{mm})

    Args:
        fck: 콘크리트 설계기준압축강도 (MPa)
        b_w: 복부 폭 (mm)
        d: 유효깊이 (mm)
        v_s: 전단철근이 부담하는 전단강도 (N)

    Returns:
        최대 간격 (mm)
    """
    threshold = np.sqrt(fck) * b_w * d / 3.0

    if v_s > threshold:
        return float(min(d / 4.0, S_MAX_ABS_CLOSE))

    return float(min(d / 2.0, S_MAX_ABS))


@dataclass
class ShearCheck:
    """전단 검토 결과.

    Args:
        v_u: 계수 전단력 (N)
        v_c: 콘크리트가 부담하는 전단강도 (N)
        v_s: 전단철근이 부담하는 전단강도 (N)
        v_s_max: 전단철근 전단강도의 상한 (N)
        v_n: 공칭 전단강도 (N)
        phi_v_n: 설계 전단강도 (N)
        a_v_min: 최소 전단철근량 (mm^2)
        a_v: 배치된 전단철근량 (mm^2)
        s: 전단철근의 간격 (mm)
        s_max: 전단철근의 최대 간격 (mm)
        stirrup_required: 전단철근이 필요한지 여부
        ok_strength: 강도 조건 만족 여부
        ok_a_v: 최소 전단철근량 만족 여부
        ok_spacing: 간격 제한 만족 여부
        ok_v_s: 전단철근 전단강도 상한 만족 여부
        ok_section: 단면 크기 조건 만족 여부
    """

    v_u: float
    v_c: float
    v_s: float
    v_s_max: float
    v_n: float
    phi_v_n: float
    a_v_min: float
    a_v: float
    s: float
    s_max: float
    stirrup_required: bool
    ok_strength: bool
    ok_a_v: bool
    ok_spacing: bool
    ok_v_s: bool
    ok_section: bool

    @property
    def ok(self) -> bool:
        """모든 조건을 만족하는지 여부.

        Returns:
            전체 판정
        """
        return (
            self.ok_strength
            and self.ok_a_v
            and self.ok_spacing
            and self.ok_v_s
            and self.ok_section
        )

    def print_results(self) -> None:
        """검토 결과를 출력한다."""
        width = 66
        print("=" * width)
        print("전단 검토 (KDS 14 20 22)")
        print("=" * width)
        print(f"계수 전단력          Vu      = {self.v_u / 1e3:10.2f} kN")
        print(f"콘크리트 전단강도    Vc      = {self.v_c / 1e3:10.2f} kN")
        print(f"                 phi*Vc      = {PHI_SHEAR * self.v_c / 1e3:10.2f} kN")
        print(f"전단철근 전단강도    Vs      = {self.v_s / 1e3:10.2f} kN")
        print(f"                     Vs,max  = {self.v_s_max / 1e3:10.2f} kN")
        print(f"공칭 전단강도        Vn      = {self.v_n / 1e3:10.2f} kN")
        print(f"설계 전단강도    phi*Vn      = {self.phi_v_n / 1e3:10.2f} kN")
        print("-" * width)
        req = "예" if self.stirrup_required else "아니오"
        print(f"전단철근 필요                = {req}")
        print(f"배치 전단철근량      Av      = {self.a_v:10.2f} mm^2")
        print(f"최소 전단철근량      Av,min  = {self.a_v_min:10.2f} mm^2")
        print(f"배치 간격            s       = {self.s:10.2f} mm")
        print(f"최대 간격            s,max   = {self.s_max:10.2f} mm")
        print("-" * width)
        v = "만족" if self.ok_strength else "불만족"
        print(f"강도       phi*Vn >= Vu      : {v}")
        v = "만족" if self.ok_a_v else "불만족"
        print(f"최소철근   Av >= Av,min      : {v}")
        v = "만족" if self.ok_spacing else "불만족"
        print(f"간격       s <= s,max        : {v}")
        v = "만족" if self.ok_v_s else "불만족"
        print(f"철근한계   Vs <= Vs,max      : {v}")
        v = "만족" if self.ok_section else "불만족"
        print(f"단면크기                     : {v}")
        v = "만족" if self.ok else "불만족"
        print(f"종합                         : {v}")


def check_shear(
    v_u: float,
    fck: float,
    b_w: float,
    d: float,
    a_v: float = 0.0,
    s: float = 0.0,
    fyt: float = 400.0,
    lambda_c: float = 1.0,
    n_u: float = 0.0,
    a_g: float = 0.0,
    alpha: float = 90.0,
) -> ShearCheck:
    r"""전단 설계를 검토한다.

    **KDS 14 20 22 4.1 ~ 4.3, KDS 14 20 10 4.3.3(2)③**

    다음을 모두 확인한다.

    - 강도: :math:`\phi V_n \ge V_u`, :math:`\phi = 0.75`
    - 전단철근 필요 여부: :math:`V_u > \phi V_c / 2`
    - 최소 전단철근량: :math:`A_v \ge A_{v,min}`
    - 간격 제한: :math:`s \le s_{max}`
    - 전단철근 상한: :math:`V_s \le \frac{2}{3}\sqrt{f_{ck}} b_w d`

    Args:
        v_u: 계수 전단력 (N)
        fck: 콘크리트 설계기준압축강도 (MPa)
        b_w: 복부 폭 (mm)
        d: 유효깊이 (mm)
        a_v: 간격 ``s`` 내 전단철근의 단면적 (mm\ :sup:`2`). 기본값 ``0``.
        s: 전단철근의 간격 (mm). 기본값 ``0`` (전단철근 없음).
        fyt: 전단철근의 설계기준항복강도 (MPa). 기본값 ``400``.
        lambda_c: 경량콘크리트계수. 기본값 ``1.0``.
        n_u: 계수 축력 (N). 기본값 ``0``.
        a_g: 전체 단면적 (mm\ :sup:`2`). 기본값 ``0``.
        alpha: 전단철근이 부재축과 이루는 각 (도). 기본값 ``90``.

    Returns:
        전단 검토 결과 객체
    """
    v_c = concrete_shear_strength(
        fck=fck, b_w=b_w, d=d, lambda_c=lambda_c, n_u=n_u, a_g=a_g
    )

    if a_v > 0 and s > 0:
        v_s = shear_reinforcement_strength(a_v=a_v, fyt=fyt, d=d, s=s, alpha=alpha)
    else:
        v_s = 0.0

    v_s_max = max_shear_reinforcement_strength(fck=fck, b_w=b_w, d=d)
    v_n = v_c + min(v_s, v_s_max)
    phi_v_n = PHI_SHEAR * v_n

    a_v_min = (
        minimum_shear_reinforcement(fck=fck, b_w=b_w, s=s, fyt=fyt) if s > 0 else 0.0
    )
    s_max = max_stirrup_spacing(fck=fck, b_w=b_w, d=d, v_s=v_s) if s > 0 else 0.0

    stirrup_required = v_u > 0.5 * PHI_SHEAR * v_c

    return ShearCheck(
        v_u=v_u,
        v_c=v_c,
        v_s=v_s,
        v_s_max=v_s_max,
        v_n=v_n,
        phi_v_n=phi_v_n,
        a_v_min=a_v_min,
        a_v=a_v,
        s=s,
        s_max=s_max,
        stirrup_required=stirrup_required,
        ok_strength=phi_v_n >= v_u,
        ok_a_v=(not stirrup_required) or a_v >= a_v_min - 1e-9,
        ok_spacing=(s <= 0) or s <= s_max + 1e-9,
        ok_v_s=v_s <= v_s_max + 1e-9,
        ok_section=v_s <= v_s_max + 1e-9,
    )


def required_stirrup_spacing(
    v_u: float,
    fck: float,
    b_w: float,
    d: float,
    a_v: float,
    fyt: float = 400.0,
    lambda_c: float = 1.0,
    n_u: float = 0.0,
    a_g: float = 0.0,
) -> float:
    r"""요구 전단강도를 만족하는 스터럽 간격을 반환한다.

    강도 조건, 최소 전단철근량 조건, 간격 제한을 모두 만족하는 최대 간격을
    계산한다.

    Args:
        v_u: 계수 전단력 (N)
        fck: 콘크리트 설계기준압축강도 (MPa)
        b_w: 복부 폭 (mm)
        d: 유효깊이 (mm)
        a_v: 스터럽 1조의 단면적 (mm\ :sup:`2`)
        fyt: 전단철근의 설계기준항복강도 (MPa). 기본값 ``400``.
        lambda_c: 경량콘크리트계수. 기본값 ``1.0``.
        n_u: 계수 축력 (N). 기본값 ``0``.
        a_g: 전체 단면적 (mm\ :sup:`2`). 기본값 ``0``.

    Raises:
        ValueError: 전단철근으로도 요구 강도를 만족할 수 없는 경우 (단면 확대 필요)

    Returns:
        필요한 스터럽 간격 (mm). 전단철근이 불필요하면 ``inf``.
    """
    v_c = concrete_shear_strength(
        fck=fck, b_w=b_w, d=d, lambda_c=lambda_c, n_u=n_u, a_g=a_g
    )

    # 전단철근이 필요 없는 경우
    if v_u <= 0.5 * PHI_SHEAR * v_c:
        return float("inf")

    v_s_req = max(v_u / PHI_SHEAR - v_c, 0.0)
    v_s_max = max_shear_reinforcement_strength(fck=fck, b_w=b_w, d=d)

    if v_s_req > v_s_max:
        msg = (
            f"Vs = {v_s_req / 1e3:.1f} kN 이 상한 {v_s_max / 1e3:.1f} kN 을 "
            "초과합니다. 단면을 키워야 합니다."
        )
        raise ValueError(msg)

    # 강도 조건
    s_strength = a_v * fyt * d / v_s_req if v_s_req > 0 else float("inf")

    # 최소 전단철근량 조건 : Av >= Av,min -> s <= Av*fyt / (max(...)*b_w)
    s_min_reinf = a_v * fyt / (max(0.0625 * np.sqrt(fck), 0.35) * b_w)

    # 간격 제한
    s_max = max_stirrup_spacing(fck=fck, b_w=b_w, d=d, v_s=v_s_req)

    return float(min(s_strength, s_min_reinf, s_max))


def cracking_torque(
    fck: float,
    a_cp: float,
    p_cp: float,
    lambda_c: float = 1.0,
) -> float:
    r"""균열 비틀림모멘트 :math:`T_{cr}` 를 반환한다.

    **KDS 14 20 22 4.4.2**

    .. math::
        T_{cr} = \frac{1}{3}\lambda\sqrt{f_{ck}}\, \frac{A_{cp}^2}{p_{cp}}

    Args:
        fck: 콘크리트 설계기준압축강도 (MPa)
        a_cp: 전체 단면의 외부 둘레로 둘러싸인 면적 (mm\ :sup:`2`)
        p_cp: 전체 단면의 외부 둘레 길이 (mm)
        lambda_c: 경량콘크리트계수. 기본값 ``1.0``.

    Returns:
        균열 비틀림모멘트 (N·mm)
    """
    return float(lambda_c * np.sqrt(fck) / 3.0 * a_cp**2 / p_cp)


def torsion_negligible(
    t_u: float,
    fck: float,
    a_cp: float,
    p_cp: float,
    lambda_c: float = 1.0,
) -> bool:
    r"""비틀림을 무시할 수 있는지 판정한다.

    **KDS 14 20 22 4.4.1(1)①**

    .. math::
        T_u < \phi \frac{1}{12}\lambda\sqrt{f_{ck}}\,\frac{A_{cp}^2}{p_{cp}}
        = \frac{\phi T_{cr}}{4}

    Args:
        t_u: 계수 비틀림모멘트 (N·mm)
        fck: 콘크리트 설계기준압축강도 (MPa)
        a_cp: 전체 단면의 외부 둘레로 둘러싸인 면적 (mm\ :sup:`2`)
        p_cp: 전체 단면의 외부 둘레 길이 (mm)
        lambda_c: 경량콘크리트계수. 기본값 ``1.0``.

    Returns:
        비틀림을 무시할 수 있으면 ``True``
    """
    t_cr = cracking_torque(fck=fck, a_cp=a_cp, p_cp=p_cp, lambda_c=lambda_c)

    return bool(abs(t_u) < PHI_SHEAR * t_cr / 4.0)


def torsional_strength(
    a_t: float,
    s: float,
    a_oh: float,
    fyt: float,
    theta: float = 45.0,
) -> float:
    r"""비틀림철근이 부담하는 비틀림강도 :math:`T_n` 을 반환한다.

    KDS 14 20 22 4.5.2

    .. math::
        T_n = \frac{2 A_o A_t f_{yt}}{s} \cot\theta, \qquad A_o = 0.85 A_{oh}

    Args:
        a_t: 간격 ``s`` 내 폐쇄스터럽 1가닥의 단면적 (mm\ :sup:`2`)
        s: 비틀림철근의 간격 (mm)
        a_oh: 폐쇄스터럽 중심선으로 둘러싸인 면적 (mm\ :sup:`2`)
        fyt: 횡방향 비틀림철근의 설계기준항복강도 (MPa)
        theta: 압축 스트럿의 경사각 (도). 비프리스트레스트 부재는 45°.
            기본값 ``45``.

    Raises:
        ValueError: ``s`` 가 0 이하인 경우

    Returns:
        공칭 비틀림강도 (N·mm)
    """
    if s <= 0:
        msg = "s 는 0 보다 커야 합니다."
        raise ValueError(msg)

    a_o = 0.85 * a_oh

    return float(2.0 * a_o * a_t * fyt / s / np.tan(np.radians(theta)))


def longitudinal_torsion_reinforcement(
    a_t: float,
    s: float,
    p_h: float,
    fyt: float,
    fy: float,
    theta: float = 45.0,
) -> float:
    r"""비틀림에 필요한 종방향 철근량 :math:`A_l` 을 반환한다.

    **KDS 14 20 22 4.5**

    .. math::
        A_l = \frac{A_t}{s} p_h \frac{f_{yt}}{f_y} \cot^2\theta

    Args:
        a_t: 간격 ``s`` 내 폐쇄스터럽 1가닥의 단면적 (mm\ :sup:`2`)
        s: 비틀림철근의 간격 (mm)
        p_h: 폐쇄스터럽 중심선의 둘레 길이 (mm)
        fyt: 횡방향 비틀림철근의 설계기준항복강도 (MPa)
        fy: 종방향 비틀림철근의 설계기준항복강도 (MPa)
        theta: 압축 스트럿의 경사각 (도). 기본값 ``45``.

    Raises:
        ValueError: ``s`` 가 0 이하인 경우

    Returns:
        종방향 비틀림철근량 (mm\ :sup:`2`)
    """
    if s <= 0:
        msg = "s 는 0 보다 커야 합니다."
        raise ValueError(msg)

    cot_theta = 1.0 / np.tan(np.radians(theta))

    return float(a_t / s * p_h * fyt / fy * cot_theta**2)


def check_torsion_section(
    v_u: float,
    t_u: float,
    fck: float,
    b_w: float,
    d: float,
    a_oh: float,
    p_h: float,
    v_c: float | None = None,
) -> tuple[float, float, bool]:
    r"""전단과 비틀림을 함께 받는 단면의 크기를 검토한다.

    **KDS 14 20 22 4.5**

    .. math::
        \sqrt{\left(\frac{V_u}{b_w d}\right)^2
        + \left(\frac{T_u p_h}{1.7 A_{oh}^2}\right)^2}
        \le \phi\left(\frac{V_c}{b_w d} + \frac{2}{3}\sqrt{f_{ck}}\right)

    Args:
        v_u: 계수 전단력 (N)
        t_u: 계수 비틀림모멘트 (N·mm)
        fck: 콘크리트 설계기준압축강도 (MPa)
        b_w: 복부 폭 (mm)
        d: 유효깊이 (mm)
        a_oh: 폐쇄스터럽 중심선으로 둘러싸인 면적 (mm\ :sup:`2`)
        p_h: 폐쇄스터럽 중심선의 둘레 길이 (mm)
        v_c: 콘크리트가 부담하는 전단강도 (N). 주지 않으면 간편식으로 계산.
            기본값 ``None``.

    Returns:
        좌변 응력, 우변 한계 응력, 만족 여부 (``demand``, ``capacity``, ``ok``)
    """
    if v_c is None:
        v_c = concrete_shear_strength(fck=fck, b_w=b_w, d=d)

    demand = np.sqrt(
        (v_u / (b_w * d)) ** 2 + (abs(t_u) * p_h / (1.7 * a_oh**2)) ** 2
    )
    capacity = PHI_SHEAR * (v_c / (b_w * d) + 2.0 / 3.0 * np.sqrt(fck))

    return float(demand), float(capacity), bool(demand <= capacity)
