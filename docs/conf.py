"""Sphinx 설정 — concreteproperties KDS 한글판."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

# 프로젝트 정보
project = "concreteproperties KDS"
author = "concreteproperties-kds contributors"
copyright = f"{datetime.now(tz=UTC).year}, {author}"  # noqa: A001
language = "ko"

# sphinx 설정
templates_path = ["_templates"]
exclude_patterns = ["_build", "**.ipynb_checkpoints", "Thumbs.db", ".DS_Store"]

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "matplotlib.sphinxext.plot_directive",
    "myst_nb",
    "sphinx_copybutton",
    "sphinxext.opengraph",
]

# myst 설정 (myst_nb 가 myst_parser 를 포함한다)
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_image",
    "linkify",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 4

# 노트북의 마크다운 셀은 조각 단위로 파싱되므로, 절 제목(##)으로 시작하는 셀마다
# "문서가 H1 이 아닌 H2 로 시작한다"는 경고가 난다. 강의 노트북은 설명을 절마다
# 나눠 담는 구성이라 이 경고가 정상 동작이다.
suppress_warnings = ["myst.header"]

# 노트북은 미리 실행된 출력을 그대로 쓴다 (빌드 시간과 재현성)
nb_execution_mode = "off"
nb_execution_timeout = 300

# autodoc 설정
autodoc_member_order = "bysource"
autodoc_typehints = "both"
autodoc_typehints_description_target = "documented_params"
autosummary_generate = True

# napoleon 설정
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_ivar = True

# intersphinx
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "shapely": ("https://shapely.readthedocs.io/en/stable/", None),
    "sectionproperties": (
        "https://sectionproperties.readthedocs.io/en/stable",
        None,
    ),
    "concreteproperties": (
        "https://concrete-properties.readthedocs.io/en/stable",
        None,
    ),
}

# html 테마
html_theme = "furo"
html_static_path = ["_static"]
html_title = "concreteproperties KDS 한글판"
html_theme_options = {
    "sidebar_hide_name": False,
    "source_repository": "https://github.com/cnusal-1/concreteproperties-kds",
    "source_branch": "main",
    "source_directory": "docs/",
}
pygments_style = "sphinx"
pygments_dark_style = "monokai"

# 한글 글꼴이 없는 환경에서도 그림이 깨지지 않도록
plot_rcparams = {"axes.unicode_minus": False}
plot_html_show_source_link = False
plot_html_show_formats = False


# 사이드바에 절 제목까지 펼쳐 보이기
#
# furo 는 왼쪽 사이드바를 titles_only=True 로 만들어 문서 제목만 보여 준다.
# 강의 노트북은 절(0. 준비, 1. …, 정리)까지 왼쪽 메뉴에서 펼쳐 볼 수 있어야
# 하므로, furo 가 만든 트리를 titles_only 를 끈 것으로 바꿔 넣는다. furo 의
# html-page-context 처리기보다 나중에 돌아야 하므로 우선순위를 뒤로 준다.
def _sidebar_with_sections(app, pagename, templatename, context, doctree):
    """사이드바 트리를 절 제목까지 포함한 것으로 교체한다."""
    from furo.navigation import get_navigation_tree

    toctree = context.get("toctree")
    if toctree is None:
        return

    context["furo_navigation_tree"] = get_navigation_tree(
        toctree(collapse=False, titles_only=False, maxdepth=-1, includehidden=True)
    )


def setup(app):
    """Sphinx 확장 지점.

    Args:
        app: Sphinx 응용 객체

    Returns:
        확장 메타데이터
    """
    app.connect("html-page-context", _sidebar_with_sections, priority=900)

    return {"parallel_read_safe": True, "parallel_write_safe": True}
