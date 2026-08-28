"""내구성 설계 (KDS 14 20 40).

노출등급(표 4.1-1)과 그에 따른 최소 설계기준압축강도(표 4.1-3)를 다룬다.

.. note::

    KDS 14 20 40 이 수치로 규정하는 것은 **최소 설계기준압축강도뿐**\\ 이다.

    - 물-결합재비, 결합재 종류, 연행공기량, 염화물 함유량은
      **KCS 14 20 10(1.10)** 에 위임되어 있다 (KDS 14 20 40 4.1.4(3)).
    - 피복두께는 노출범주 EC·ES 에 대해 **KDS 14 20 50(4.3)** 의 최소
      피복두께 이상으로 하도록 규정한다 (KDS 14 20 40 4.1.4(2)).
      :func:`concreteproperties_kds.detailing.minimum_cover` 를 사용한다.

    따라서 이 모듈은 물-결합재비와 피복두께의 수치 기준을 스스로 정하지 않고,
    사용자가 시방서·KDS 14 20 50 에서 얻은 값을 넣어 검토하도록 한다.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExposureClass:
    """노출등급 하나의 내구성 요구사항 (KDS 14 20 40 표 4.1-1, 표 4.1-3).

    Args:
        code: 노출등급 기호 (예: ``"EC2"``)
        category: 노출범주 이름
        description: 노출 환경 설명
        fck_min: 최소 설계기준압축강도 (MPa), 표 4.1-3
        cover_required: 피복두께에 대해 KDS 14 20 50(4.3) 의 최소 피복두께
            이상을 요구하는 노출범주인지 여부 (EC, ES)
    """

    code: str
    category: str
    description: str
    fck_min: float
    cover_required: bool = False


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
        cover_required=True,
    ),
    "EC2": ExposureClass(
        code="EC2",
        category="탄산화",
        description="습윤하고 드물게 건조",
        fck_min=24.0,
        cover_required=True,
    ),
    "EC3": ExposureClass(
        code="EC3",
        category="탄산화",
        description="보통 습도",
        fck_min=27.0,
        cover_required=True,
    ),
    "EC4": ExposureClass(
        code="EC4",
        category="탄산화",
        description="주기적인 건습 반복",
        fck_min=30.0,
        cover_required=True,
    ),
    "ES1": ExposureClass(
        code="ES1",
        category="염화물",
        description="해양 대기 중 (직접 접촉 없음)",
        fck_min=30.0,
        cover_required=True,
    ),
    "ES2": ExposureClass(
        code="ES2",
        category="염화물",
        description="영구히 수중",
        fck_min=30.0,
        cover_required=True,
    ),
    "ES3": ExposureClass(
        code="ES3",
        category="염화물",
        description="간만대 또는 물보라 지역",
        fck_min=35.0,
        cover_required=True,
    ),
    "ES4": ExposureClass(
        code="ES4",
        category="염화물",
        description="제설염 등 염화물에 노출",
        fck_min=35.0,
        cover_required=True,
    ),
    "EF1": ExposureClass(
        code="EF1",
        category="동결융해",
        description="수분과 접촉하나 제빙화학제 없음, 동결융해 반복",
        fck_min=24.0,
    ),
    "EF2": ExposureClass(
        code="EF2",
        category="동결융해",
        description="제빙화학제 노출, 동결융해 반복",
        fck_min=27.0,
    ),
    "EF3": ExposureClass(
        code="EF3",
        category="동결융해",
        description="수분과 자주 접촉, 동결융해 반복",
        fck_min=30.0,
    ),
    "EF4": ExposureClass(
        code="EF4",
        category="동결융해",
        description="해수 또는 제빙화학제에 노출, 동결융해 반복",
        fck_min=30.0,
    ),
    "EA1": ExposureClass(
        code="EA1",
        category="황산염",
        description="약한 황산염 침해 (토양 SO4 2000~3000 ppm)",
        fck_min=27.0,
    ),
    "EA2": ExposureClass(
        code="EA2",
        category="황산염",
        description="보통 황산염 침해",
        fck_min=30.0,
    ),
    "EA3": ExposureClass(
        code="EA3",
        category="황산염",
        description="심한 황산염 침해",
        fck_min=30.0,
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
        fck_min: 요구 최소 설계기준압축강도 (MPa), KDS 14 20 40 표 4.1-3
        cover: 설계 피복두께 (mm). 확인하지 않으면 ``None``
        cover_min: KDS 14 20 50(4.3) 에 따른 최소 피복두께 (mm).
            사용자가 준 값이며, 주지 않으면 ``None``
        water_binder_ratio: 배합의 물-결합재비. KDS 는 KCS 14 20 10(1.10) 에
            위임하므로 참고 정보로만 담는다
        ok_fck: 강도 조건 만족 여부
        ok_cover: 피복두께 조건 만족 여부
    """

    exposure: ExposureClass
    fck: float
    fck_min: float
    cover: float | None
    cover_min: float | None
    water_binder_ratio: float | None
    ok_fck: bool
    ok_cover: bool

    @property
    def ok(self) -> bool:
        """모든 조건을 만족하는지 여부.

        Returns:
            전체 판정
        """
        return self.ok_fck and self.ok_cover

    def print_results(self) -> None:
        """검토 결과를 출력한다."""
        width = 72
        print("=" * width)
        print("내구성 검토 (KDS 14 20 40)")
        print("=" * width)
        print(f"노출등급  {self.exposure.code} ({self.exposure.category})")
        print(f"          {self.exposure.description}")
        print("-" * width)
        verdict = "만족" if self.ok_fck else "불만족"
        print(
            f"설계기준압축강도  fck = {self.fck:8.1f} MPa "
            f"(표 4.1-3 요구 {self.fck_min:.1f} 이상)  {verdict}"
        )

        if not self.exposure.cover_required:
            print("피복두께               노출범주 EC·ES 가 아니므로 규정 없음")
        elif self.cover_min is None:
            print(
                "피복두께               KDS 14 20 50(4.3) 의 최소 피복두께를 "
                "확인할 것"
            )
        else:
            cover_str = f"{self.cover:.1f}" if self.cover is not None else "미확인"
            verdict = "만족" if self.ok_cover else "불만족"
            print(
                f"피복두께          cc  = {cover_str:>8} mm "
                f"(KDS 14 20 50 요구 {self.cover_min:.1f} 이상)  {verdict}"
            )

        if self.water_binder_ratio is not None:
            print(
                f"물-결합재비       W/B = {self.water_binder_ratio:8.3f}   "
                "(KCS 14 20 10(1.10) 에서 확인할 것)"
            )

        print("-" * width)
        verdict = "만족" if self.ok else "불만족"
        print(f"종합                                                {verdict}")


def check_durability(
    exposure_class: str,
    fck: float,
    cover: float | None = None,
    cover_min: float | None = None,
    water_binder_ratio: float | None = None,
) -> DurabilityCheck:
    """노출등급에 대한 내구성 요구사항을 검토한다 (KDS 14 20 40).

    KDS 14 20 40 이 수치로 규정하는 것은 표 4.1-3 의 최소 설계기준압축강도뿐이다.
    피복두께는 노출범주 EC·ES 에 대해 KDS 14 20 50(4.3) 의 최소 피복두께 이상을
    요구하므로, 그 값을 ``cover_min`` 으로 넘겨 함께 검토할 수 있다
    (:func:`concreteproperties_kds.detailing.minimum_cover` 로 구한다).

    Args:
        exposure_class: 노출등급 기호. :data:`EXPOSURE_REQUIREMENTS` 의 키.
        fck: 설계기준압축강도 (MPa)
        cover: 설계 피복두께 (mm). 기본값 ``None`` (확인하지 않음).
        cover_min: KDS 14 20 50(4.3) 에 따른 최소 피복두께 (mm).
            기본값 ``None`` (확인하지 않음).
        water_binder_ratio: 배합의 물-결합재비. 참고 정보로만 기록한다.
            기본값 ``None``.

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

    ok_cover = True
    if req.cover_required and cover is not None and cover_min is not None:
        ok_cover = cover >= cover_min - 1e-9

    return DurabilityCheck(
        exposure=req,
        fck=fck,
        fck_min=req.fck_min,
        cover=cover,
        cover_min=cover_min,
        water_binder_ratio=water_binder_ratio,
        ok_fck=fck >= req.fck_min - 1e-9,
        ok_cover=ok_cover,
    )


def governing_requirements(exposure_classes: list[str]) -> float:
    """여러 노출등급이 동시에 적용될 때 지배하는 최소 강도를 반환한다.

    Args:
        exposure_classes: 적용되는 노출등급 기호 목록

    Raises:
        ValueError: 목록이 비었거나 정의되지 않은 등급이 있는 경우

    Returns:
        최소 설계기준압축강도 (MPa)
    """
    if not exposure_classes:
        msg = "exposure_classes 는 하나 이상의 노출등급을 포함해야 합니다."
        raise ValueError(msg)

    unknown = [c for c in exposure_classes if c not in EXPOSURE_REQUIREMENTS]

    if unknown:
        msg = f"정의되지 않은 노출등급: {unknown}"
        raise ValueError(msg)

    return float(
        max(EXPOSURE_REQUIREMENTS[c].fck_min for c in exposure_classes)
    )


def print_exposure_table() -> None:
    """노출등급별 최소 설계기준압축강도를 표로 출력한다."""
    width = 86
    print("=" * width)
    print("노출등급과 최소 설계기준압축강도 (KDS 14 20 40 표 4.1-1, 표 4.1-3)")
    print("=" * width)
    print(f"{'등급':>5} {'범주':>6} {'fck,min':>9} {'피복규정':>9}  {'환경':<44}")
    print("-" * width)

    for req in EXPOSURE_REQUIREMENTS.values():
        cover = "14 20 50" if req.cover_required else "-"
        print(
            f"{req.code:>5} {req.category:>6} {req.fck_min:9.0f} {cover:>9}  "
            f"{req.description:<44}"
        )

    print("-" * width)
    print("물-결합재비·결합재·공기량·염화물량은 KCS 14 20 10(1.10) 에 따른다.")
