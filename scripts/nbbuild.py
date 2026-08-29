"""노트북 생성 공용 함수.

`docs/examples/*.ipynb` 는 :mod:`scripts.build_notebooks` 로 생성한다.
노트북을 직접 고치는 대신 생성 스크립트를 고치고 다시 생성한다.

그래프 라벨은 ASCII 로 둔다. 한글 글꼴이 없는 환경에서 축 이름이 깨지는 것을
피하기 위해서이며, 서술은 마크다운 셀에 한글로 쓴다.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import nbformat

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "docs" / "examples"


# 설계 순서도 — 예제와 설계 강의의 시작부에 공통으로 쓴다.
# 별도 Sphinx 확장 없이 사이트에 실리도록 matplotlib 으로 그린다.
FLOWCHART = r'''
def _use_korean_font():
    """설치된 한글 글꼴을 찾아 matplotlib 에 등록한다.

    예제 노트북의 준비 셀은 축 라벨을 ASCII 로 두므로 글꼴을 등록하지 않는다.
    순서도는 한글을 쓰므로 여기서 직접 챙긴다.
    """
    import glob
    import sys
    from pathlib import Path

    from matplotlib import font_manager

    site = Path(sys.prefix, "lib",
                f"python{sys.version_info.major}.{sys.version_info.minor}",
                "site-packages")
    for pattern in (
        str(site / "koreanize_matplotlib/fonts/*.ttf"),
        "/usr/share/fonts/**/*Nanum*.ttf",
        "/usr/share/fonts/**/*NotoSansCJK*.ot[fc]",
        "/usr/share/fonts/**/*NotoSansKR*.otf",
    ):
        for path in glob.glob(pattern, recursive=True):
            font_manager.fontManager.addfont(path)

    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in ("NanumGothic", "Noto Sans CJK KR", "Noto Sans KR", "Malgun Gothic"):
        if name in installed:
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False


def design_flowchart(title, steps, width=9.6, box_h=0.78, gap=0.30):
    """설계 흐름을 세로 순서도로 그린다.

    Args:
        title: 그림 제목
        steps: (단계 이름, KDS 조문) 튜플의 목록. 조문에 여러 개를 적으려면
            줄바꿈 대신 쉼표로 잇는다.
        width: 그림 폭 (in)
        box_h: 상자 하나의 높이 (in 환산 전 좌표 단위)
        gap: 상자 사이 간격
    """
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    _use_korean_font()

    n = len(steps)
    fig_h = n * (box_h + gap) + 0.7
    fig, ax = plt.subplots(figsize=(width, fig_h))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, n * (box_h + gap) + 0.4)
    ax.axis("off")

    face, edge = "#eef2f8", "#1f6feb"
    for i, (name, clause) in enumerate(steps):
        y = (n - 1 - i) * (box_h + gap) + 0.2
        ax.add_patch(FancyBboxPatch(
            (0.15, y), 5.9, box_h, boxstyle="round,pad=0.04,rounding_size=0.10",
            facecolor=face, edgecolor=edge, linewidth=1.3))
        ax.text(0.42, y + box_h / 2, f"{i + 1}", va="center", ha="center",
                fontsize=10.5, color=edge, fontweight="bold")
        ax.text(0.78, y + box_h / 2, name, va="center", ha="left", fontsize=11)
        ax.text(6.25, y + box_h / 2, clause, va="center", ha="left",
                fontsize=9.5, color="#5d6675")

        if i < n - 1:
            ax.add_patch(FancyArrowPatch(
                (3.1, y), (3.1, y - gap),
                arrowstyle="-|>", mutation_scale=13,
                color=edge, linewidth=1.2))

    ax.text(0.15, n * (box_h + gap) + 0.22, title, fontsize=12.5,
            fontweight="bold", va="bottom")
    ax.text(6.25, n * (box_h + gap) + 0.24, "근거 조문", fontsize=10,
            color="#5d6675", va="bottom")
    fig.tight_layout()
    return fig
'''


def md(*parts: str) -> nbformat.NotebookNode:
    """마크다운 셀을 만든다.

    조각을 여러 개 받아 **각각 따로** dedent 한 뒤 이어 붙인다. 들여쓰기가
    다른 문자열을 미리 이어 붙이면 :func:`textwrap.dedent` 가 공통 들여쓰기를
    찾지 못해 아무것도 벗겨내지 못하고, 마크다운 전체가 코드블록이 되어
    버리기 때문이다.

    Args:
        *parts: 셀 내용 조각

    Returns:
        마크다운 셀
    """
    body = "\n\n".join(dedent(part).strip("\n") for part in parts)

    return nbformat.v4.new_markdown_cell(body)


def code(text: str) -> nbformat.NotebookNode:
    """코드 셀을 만든다.

    ``plt.subplots`` 로 그림을 만드는 셀에는 ``plt.show()`` 를 덧붙인다.
    객체지향 API(``ax.plot`` 등)만 쓰면 ``draw_if_interactive`` 가 호출되지
    않아 inline 백엔드가 셀 끝에서 그림을 내보내지 않고, 노트북을 실행해도
    그림 출력이 비어 버린다.

    Args:
        text: 셀 내용

    Returns:
        코드 셀
    """
    src = dedent(text).strip("\n")

    if "plt.subplots(" in src and "plt.show()" not in src:
        src += "\nplt.show()"

    return nbformat.v4.new_code_cell(src)


def write(
    name: str,
    cells: list[nbformat.NotebookNode],
    directory: Path | None = None,
) -> Path:
    """노트북을 파일로 쓴다.

    Args:
        name: 파일 이름 (확장자 제외)
        cells: 셀 목록
        directory: 저장할 디렉터리 (기본값 ``docs/examples``)

    Returns:
        생성된 노트북 경로
    """
    nb = nbformat.v4.new_notebook(cells=cells)
    nb.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    nb.metadata["language_info"] = {"name": "python", "version": "3.12"}

    target = EXAMPLES if directory is None else directory
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{name}.ipynb"
    nbformat.write(nb, path)

    return path


def execute(paths: list[Path], timeout: int = 900) -> int:
    """노트북을 실행하여 출력을 저장한다.

    Args:
        paths: 실행할 노트북 경로 목록
        timeout: 셀 하나의 제한 시간 (초)

    Returns:
        실패한 노트북 수
    """
    failed = 0

    for path in paths:
        result = subprocess.run(  # noqa: S603
            [
                sys.executable,
                "-m",
                "jupyter",
                "nbconvert",
                "--to",
                "notebook",
                "--execute",
                "--inplace",
                f"--ExecutePreprocessor.timeout={timeout}",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            print(f"  실행 완료  {path.name}")
        else:
            failed += 1
            print(f"  실행 실패  {path.name}")
            print(result.stderr[-1500:])

    return failed
