"""내구성 설계 (KDS 14 20 40).

노출등급에 따른 콘크리트의 최소 설계기준압축강도, 최대 물-결합재비, 최대
염화물량과 최소 피복두께를 다룬다.

.. warning::

    노출등급별 요구값은 개정 이력이 잦고 표의 구성도 바뀐다. 이 모듈의
    :data:`EXPOSURE_REQUIREMENTS` 는 편집 가능한 표로 구현되어 있으니, 현행
    KDS 14 20 40 과 대조한 뒤 사용한다.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExposureClass:
    """노출등급 하나의 내구성 요구사항.

    Args:
        code: 노출등급 기호 (예: ``"EC2"``)
        category: 노출범주 이름
        description: 노출 환경 설명
        fck_min: 최소 설계기준압축강도 (MPa)
        wb_max: 최대 물-결합재비. 규정이 없으면 ``None``
        cover_min: 최소 피복두께 (mm). 규정이 없으면 ``None``
    """

    code: str
    category: str
    description: str
    fck_min: float
    wb_max: float | None = None
    cover_min: float | None = None


# KDS 14 20 40 노출등급별 내구성 요구사항
EXPOSURE_REQUIREMENTS: dict[str, ExposureClass] = {
    "E0": ExposureClass(
        code="E0",
        category="일반",
        description="콘크리트 내부에 철근이 없거나 유해한 환경에 노출되지 않음",
        fck_min=21.0,
    ),
    "EC1": ExposureClass(
        code="EC1",
        category="탄산화",
        description="건조하거나 항상 수중",
        fck_min=21.0,
        cover_min=20.0,
    ),
    "EC2": ExposureClass(
        code="EC2",
        category="탄산화",
        description="습윤하고 드물게 건조",
        fck_min=24.0,
        wb_max=0.55,
        cover_min=30.0,
    ),
    "EC3": ExposureClass(
        code="EC3",
        category="탄산화",
        description="보통 습도",
        fck_min=27.0,
        wb_max=0.50,
        cover_min=30.0,
    ),
    "EC4": ExposureClass(
        code="EC4",
        category="탄산화",
        description="주기적인 건습 반복",
        fck_min=30.0,
        wb_max=0.45,
        cover_min=40.0,
    ),
    "ES1": ExposureClass(
        code="ES1",
        category="염화물",
        description="해양 대기 중 (직접 접촉 없음)",
        fck_min=30.0,
        wb_max=0.45,
        cover_min=40.0,
    ),
    "ES2": ExposureClass(
        code="ES2",
        category="염화물",
        description="영구히 수중",
        fck_min=30.0,
        wb_max=0.45,
        cover_min=40.0,
    ),
    "ES3": ExposureClass(
        code="ES3",
        category="염화물",
        description="간만대 또는 물보라 지역",
        fck_min=35.0,
        wb_max=0.40,
        cover_min=60.0,
    ),
    "ES4": ExposureClass(
        code="ES4",
        category="염화물",
        description="제설염 등 염화물에 노출",
        fck_min=35.0,
        wb_max=0.40,
        cover_min=60.0,
    ),
    "EF1": ExposureClass(
        code="EF1",
        category="동결융해",
        description="수분과 접촉하나 제빙화학제 없음, 동결융해 반복",
        fck_min=24.0,
        wb_max=0.55,
        cover_min=40.0,
    ),
    "EF2": ExposureClass(
        code="EF2",
        category="동결융해",
        description="제빙화학제 노출, 동결융해 반복",
        fck_min=27.0,
        wb_max=0.50,
        cover_min=40.0,
    ),
    "EF3": ExposureClass(
        code="EF3",
        category="동결융해",
        description="수분과 자주 접촉, 동결융해 반복",
        fck_min=30.0,
        wb_max=0.45,
        cover_min=40.0,
    ),
    "EF4": ExposureClass(
        code="EF4",
        category="동결융해",
        description="해수 또는 제빙화학제에 노출, 동결융해 반복",
        fck_min=30.0,
        wb_max=0.45,
        cover_min=40.0,
    ),
    "EA1": ExposureClass(
        code="EA1",
        category="황산염",
        description="약한 황산염 침해 (토양 SO4 2000~3000 ppm)",
        fck_min=27.0,
        wb_max=0.50,
        cover_min=40.0,
    ),
    "EA2": ExposureClass(
        code="EA2",
        category="황산염",
        description="보통 황산염 침해",
        fck_min=30.0,
        wb_max=0.45,
        cover_min=40.0,
    ),
    "EA3": ExposureClass(
        code="EA3",
        category="황산염",
        description="심한 황산염 침해",
        fck_min=30.0,
        wb_max=0.45,
        cover_min=40.0,
    ),
}

# 콘크리트 중 최대 염화물 이온량 (KDS 14 20 40) - 결합재 질량에 대한 비 (%)
MAX_CHLORIDE_ION: dict[str, float] = {
    "철근콘크리트_건조": 0.30,
    "철근콘크리트_습윤": 0.15,
    "프리스트레스트콘크리트": 0.06,
}


@dataclass
class DurabilityCheck:
    """내구성 검토 결과.

    Args:
        exposure: 적용한 노출등급
        fck: 설계에 사용한 설계기준압축강도 (MPa)
        fck_min: 요구 최소 설계기준압축강도 (MPa)
        wb: 배합의 물-결합재비. 확인하지 않으면 ``None``
        wb_max: 요구 최대 물-결합재비. 규정이 없으면 ``None``
        cover: 설계 피복두께 (mm). 확인하지 않으면 ``None``
        cover_min: 요구 최소 피복두께 (mm). 규정이 없으면 ``None``
        ok_fck: 강도 조건 만족 여부
        ok_wb: 물-결합재비 조건 만족 여부
        ok_cover: 피복두께 조건 만족 여부
    """

    exposure: ExposureClass
    fck: float
    fck_min: float
    wb: float | None
    wb_max: float | None
    cover: float | None
    cover_min: float | None
    ok_fck: bool
    ok_wb: bool
    ok_cover: bool

    @property
    def ok(self) -> bool:
        """모든 조건을 만족하는지 여부.

        Returns:
            전체 판정
        """
        return self.ok_fck and self.ok_wb and self.ok_cover

    def print_results(self) -> None:
        """검토 결과를 출력한다."""
        width = 68
        print("=" * width)
        print("내구성 검토 (KDS 14 20 40)")
        print("=" * width)
        print(f"노출등급  {self.exposure.code} ({self.exposure.category})")
        print(f"          {self.exposure.description}")
        print("-" * width)
        print(
            f"설계기준압축강도  fck    = {self.fck:8.1f} MPa "
            f"(요구 {self.fck_min:.1f} 이상)  "
            f"{'만족' if self.ok_fck else '불만족'}"
        )

        if self.wb_max is None:
            print("물-결합재비                                  규정 없음")
        else:
            wb_str = f"{self.wb:.3f}" if self.wb is not None else "미확인"
            print(
                f"물-결합재비       W/B    = {wb_str:>8} "
                f"(요구 {self.wb_max:.2f} 이하) "
                f"{'만족' if self.ok_wb else '불만족'}"
            )

        if self.cover_min is None:
            print("최소 피복두께                                규정 없음")
        else:
            cover_str = f"{self.cover:.1f}" if self.cover is not None else "미확인"
            print(
                f"피복두께          cc     = {cover_str:>8} mm  "
                f"(요구 {self.cover_min:.1f} 이상)  "
                f"{'만족' if self.ok_cover else '불만족'}"
            )

        print("-" * width)
        verdict = "만족" if self.ok else "불만족"
        print(f"종합                                         {verdict}")


def check_durability(
    exposure_class: str,
    fck: float,
    water_binder_ratio: float | None = None,
    cover: float | None = None,
) -> DurabilityCheck:
    """노출등급에 대한 내구성 요구사항을 검토한다 (KDS 14 20 40).

    Args:
        exposure_class: 노출등급 기호. :data:`EXPOSURE_REQUIREMENTS` 의 키.
        fck: 설계기준압축강도 (MPa)
        water_binder_ratio: 배합의 물-결합재비. 기본값 ``None`` (확인하지 않음).
        cover: 설계 피복두께 (mm). 기본값 ``None`` (확인하지 않음).

    Raises:
        ValueError: ``exposure_class`` 가 정의되지 않은 값인 경우

    Returns:
        내구성 검토 결과 객체
    """
    if exposure_class not in EXPOSURE_REQUIREMENTS:
        msg = (
            f"exposure_class 는 {list(EXPOSURE_REQUIREMENTS)} 중 하나여야 합니다."
        )
        raise ValueError(msg)

    req = EXPOSURE_REQUIREMENTS[exposure_class]

    ok_wb = True
    if req.wb_max is not None and water_binder_ratio is not None:
        ok_wb = water_binder_ratio <= req.wb_max + 1e-9

    ok_cover = True
    if req.cover_min is not None and cover is not None:
        ok_cover = cover >= req.cover_min - 1e-9

    return DurabilityCheck(
        exposure=req,
        fck=fck,
        fck_min=req.fck_min,
        wb=water_binder_ratio,
        wb_max=req.wb_max,
        cover=cover,
        cover_min=req.cover_min,
        ok_fck=fck >= req.fck_min - 1e-9,
        ok_wb=ok_wb,
        ok_cover=ok_cover,
    )


def governing_requirements(
    exposure_classes: list[str],
) -> tuple[float, float | None, float | None]:
    """여러 노출등급이 동시에 적용될 때 지배하는 요구값을 반환한다.

    Args:
        exposure_classes: 적용되는 노출등급 기호 목록

    Raises:
        ValueError: 목록이 비었거나 정의되지 않은 등급이 있는 경우

    Returns:
        최소 설계기준압축강도, 최대 물-결합재비, 최소 피복두께
        (``fck_min``, ``wb_max``, ``cover_min``)
    """
    if not exposure_classes:
        msg = "exposure_classes 는 하나 이상의 노출등급을 포함해야 합니다."
        raise ValueError(msg)

    unknown = [c for c in exposure_classes if c not in EXPOSURE_REQUIREMENTS]

    if unknown:
        msg = f"정의되지 않은 노출등급: {unknown}"
        raise ValueError(msg)

    reqs = [EXPOSURE_REQUIREMENTS[c] for c in exposure_classes]

    fck_min = max(r.fck_min for r in reqs)

    wb_values = [r.wb_max for r in reqs if r.wb_max is not None]
    wb_max = min(wb_values) if wb_values else None

    cover_values = [r.cover_min for r in reqs if r.cover_min is not None]
    cover_min = max(cover_values) if cover_values else None

    return fck_min, wb_max, cover_min


def print_exposure_table() -> None:
    """노출등급별 요구사항을 표로 출력한다."""
    width = 92
    print("=" * width)
    print("노출등급별 내구성 요구사항 (KDS 14 20 40)")
    print("=" * width)
    print(
        f"{'등급':>5} {'범주':>6} {'fck,min':>9} {'W/B,max':>9} "
        f"{'cc,min':>8}  {'환경':<44}"
    )
    print("-" * width)

    for req in EXPOSURE_REQUIREMENTS.values():
        wb = f"{req.wb_max:.2f}" if req.wb_max is not None else "-"
        cc = f"{req.cover_min:.0f}" if req.cover_min is not None else "-"
        print(
            f"{req.code:>5} {req.category:>6} {req.fck_min:9.0f} {wb:>9} "
            f"{cc:>8}  {req.description:<44}"
        )
