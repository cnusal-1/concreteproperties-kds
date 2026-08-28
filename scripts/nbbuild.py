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


def md(text: str) -> nbformat.NotebookNode:
    """마크다운 셀을 만든다.

    Args:
        text: 셀 내용

    Returns:
        마크다운 셀
    """
    return nbformat.v4.new_markdown_cell(dedent(text).strip("\n"))


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


def write(name: str, cells: list[nbformat.NotebookNode]) -> Path:
    """노트북을 파일로 쓴다.

    Args:
        name: 파일 이름 (확장자 제외)
        cells: 셀 목록

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

    EXAMPLES.mkdir(parents=True, exist_ok=True)
    path = EXAMPLES / f"{name}.ipynb"
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
