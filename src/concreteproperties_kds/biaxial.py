"""2축 휨 기둥의 간략식.

:meth:`~concreteproperties_kds.kds.KDS14202022.biaxial_bending_diagram` 은
2축 휨 상관면을 엄밀하게 계산한다. 이 모듈은 실무에서 널리 쓰이는 간략식
(Bresler 역하중법, 등하중선법)을 제공하여 엄밀해와 비교할 수 있게 한다.

.. note::

    간략식은 KDS 14 20 의 조문이 아니라 문헌에서 널리 인정되는 근사법이다.
    설계에 사용할 때는 엄밀해와 대조하기를 권한다.
"""

from __future__ import annotations

from dataclasses import dataclass


def bresler_reciprocal(
    p_nx: float,
    p_ny: float,
    p_o: float,
) -> float:
    r"""Bresler 역하중법으로 2축 휨을 받는 기둥의 축강도를 반환한다.

    .. math::
        \frac{1}{P_n} = \frac{1}{P_{nx}} + \frac{1}{P_{ny}} - \frac{1}{P_o}

    여기서

    - :math:`P_{nx}` : 편심 :math:`e_x` 만 작용할 때의 축강도
    - :math:`P_{ny}` : 편심 :math:`e_y` 만 작용할 때의 축강도
    - :math:`P_o` : 순수압축 강도

    적용 범위는 :math:`P_u \ge 0.1 f_{ck} A_g` 이다.

    Args:
        p_nx: x 방향 편심만 작용할 때의 공칭 축강도 (N)
        p_ny: y 방향 편심만 작용할 때의 공칭 축강도 (N)
        p_o: 순수압축 강도 (N)

    Raises:
        ValueError: 인자가 0 이하이거나 역수의 합이 0 이하인 경우

    Returns:
        2축 휨을 받을 때의 공칭 축강도 (N)
    """
    if p_nx <= 0 or p_ny <= 0 or p_o <= 0:
        msg = "p_nx, p_ny, p_o 는 모두 0 보다 커야 합니다."
        raise ValueError(msg)

    inv = 1.0 / p_nx + 1.0 / p_ny - 1.0 / p_o

    if inv <= 0:
        msg = "역수의 합이 0 이하입니다. 입력값을 확인하십시오."
        raise ValueError(msg)

    return float(1.0 / inv)


def load_contour(
    m_ux: float,
    m_uy: float,
    m_nx: float,
    m_ny: float,
    alpha: float = 1.0,
) -> float:
    r"""등하중선법의 상관식 좌변을 반환한다.

    .. math::
        \left(\frac{M_{ux}}{M_{nx}}\right)^\alpha
        + \left(\frac{M_{uy}}{M_{ny}}\right)^\alpha \le 1.0

    :math:`\alpha = 1.0` 은 직선 상관(보수측), :math:`\alpha = 2.0` 은
    원형 상관에 가깝다. 실무에서는 축력 수준에 따라 1.0~2.0 을 쓴다.

    Args:
        m_ux: x 축에 대한 계수 휨모멘트 (N·mm)
        m_uy: y 축에 대한 계수 휨모멘트 (N·mm)
        m_nx: 같은 축력에서 x 축 1축 휨강도 (N·mm)
        m_ny: 같은 축력에서 y 축 1축 휨강도 (N·mm)
        alpha: 상관식의 지수. 기본값 ``1.0``.

    Raises:
        ValueError: ``m_nx`` 또는 ``m_ny`` 가 0 이하인 경우

    Returns:
        상관식의 좌변 값. 1.0 이하이면 안전.
    """
    if m_nx <= 0 or m_ny <= 0:
        msg = "m_nx, m_ny 는 0 보다 커야 합니다."
        raise ValueError(msg)

    return float(
        (abs(m_ux) / m_nx) ** alpha + (abs(m_uy) / m_ny) ** alpha
    )


@dataclass
class BiaxialCheck:
    """2축 휨 검토 결과.

    Args:
        method: 사용한 방법 이름
        demand: 상관식 좌변 (등하중선법) 또는 소요 축력 (역하중법)
        capacity: 상관식 우변 (1.0) 또는 축강도
        ratio: 소요/강도 비
        ok: 만족 여부
        note: 적용 범위 등 비고
    """

    method: str
    demand: float
    capacity: float
    ratio: float
    ok: bool
    note: str = ""

    def print_results(self) -> None:
        """검토 결과를 출력한다."""
        width = 62
        print("=" * width)
        print(f"2축 휨 검토 - {self.method}")
        print("=" * width)
        print(f"소요                = {self.demand:14.4f}")
        print(f"강도                = {self.capacity:14.4f}")
        print(f"소요/강도           = {self.ratio:14.4f}")
        print(f"판정                = {'만족' if self.ok else '불만족':>14}")

        if self.note:
            print(f"비고 : {self.note}")


def check_load_contour(
    m_ux: float,
    m_uy: float,
    phi_m_nx: float,
    phi_m_ny: float,
    alpha: float = 1.0,
) -> BiaxialCheck:
    r"""등하중선법으로 2축 휨을 검토한다.

    Args:
        m_ux: x 축에 대한 계수 휨모멘트 (N·mm)
        m_uy: y 축에 대한 계수 휨모멘트 (N·mm)
        phi_m_nx: 같은 계수 축력에서의 x 축 설계 휨강도 (N·mm)
        phi_m_ny: 같은 계수 축력에서의 y 축 설계 휨강도 (N·mm)
        alpha: 상관식의 지수. 기본값 ``1.0`` (보수측).

    Returns:
        2축 휨 검토 결과 객체
    """
    demand = load_contour(
        m_ux=m_ux, m_uy=m_uy, m_nx=phi_m_nx, m_ny=phi_m_ny, alpha=alpha
    )

    return BiaxialCheck(
        method=f"등하중선법 (alpha = {alpha:.1f})",
        demand=demand,
        capacity=1.0,
        ratio=demand,
        ok=bool(demand <= 1.0),
        note="alpha = 1.0 은 보수측, 2.0 은 비보수측에 가깝다.",
    )


def check_bresler_reciprocal(
    p_u: float,
    phi_p_nx: float,
    phi_p_ny: float,
    phi_p_o: float,
    fck: float | None = None,
    a_g: float | None = None,
) -> BiaxialCheck:
    r"""Bresler 역하중법으로 2축 휨을 검토한다.

    Args:
        p_u: 계수 축력 (N)
        phi_p_nx: x 방향 편심만 작용할 때의 설계 축강도 (N)
        phi_p_ny: y 방향 편심만 작용할 때의 설계 축강도 (N)
        phi_p_o: 설계 순수압축 강도 (N)
        fck: 콘크리트 설계기준압축강도 (MPa). 적용 범위 확인용.
            기본값 ``None``.
        a_g: 전체 단면적 (mm\ :sup:`2`). 적용 범위 확인용. 기본값 ``None``.

    Returns:
        2축 휨 검토 결과 객체
    """
    p_n = bresler_reciprocal(p_nx=phi_p_nx, p_ny=phi_p_ny, p_o=phi_p_o)

    note = ""
    if fck is not None and a_g is not None:
        threshold = 0.1 * fck * a_g
        if p_u < threshold:
            note = (
                f"Pu = {p_u / 1e3:.1f} kN 이 0.1*fck*Ag = "
                f"{threshold / 1e3:.1f} kN 미만이므로 역하중법의 적용 범위를 "
                "벗어난다. 등하중선법을 사용할 것."
            )

    return BiaxialCheck(
        method="Bresler 역하중법",
        demand=p_u,
        capacity=p_n,
        ratio=p_u / p_n if p_n > 0 else float("inf"),
        ok=bool(p_u <= p_n),
        note=note,
    )


def compare_with_exact(
    m_ux: float,
    m_uy: float,
    phi_m_nx: float,
    phi_m_ny: float,
    exact_ratio: float,
    alphas: tuple[float, ...] = (1.0, 1.25, 1.5, 2.0),
) -> list[tuple[float, float, bool]]:
    """여러 :math:`\\alpha` 에 대한 등하중선법 결과를 엄밀해와 비교한다.

    Args:
        m_ux: x 축에 대한 계수 휨모멘트 (N·mm)
        m_uy: y 축에 대한 계수 휨모멘트 (N·mm)
        phi_m_nx: x 축 설계 휨강도 (N·mm)
        phi_m_ny: y 축 설계 휨강도 (N·mm)
        exact_ratio: 엄밀 2축 휨 상관면에서 구한 소요/강도 비
        alphas: 비교할 지수 목록. 기본값 ``(1.0, 1.25, 1.5, 2.0)``.

    Returns:
        (alpha, 등하중선법 결과, 엄밀해보다 보수적인지 여부) 목록
    """
    results = []

    for alpha in alphas:
        value = load_contour(
            m_ux=m_ux, m_uy=m_uy, m_nx=phi_m_nx, m_ny=phi_m_ny, alpha=alpha
        )
        results.append((alpha, value, bool(value >= exact_ratio)))

    return results
