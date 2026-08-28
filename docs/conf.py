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
    "source_repository": (
        "https://github.com/cnusal-1/wkclauderepositoty"
    ),
    "source_branch": "claude/kds-korean-version-hhoavw",
    "source_directory": "concreteproperties-kds/docs/",
}
pygments_style = "sphinx"
pygments_dark_style = "monokai"

# 한글 글꼴이 없는 환경에서도 그림이 깨지지 않도록
plot_rcparams = {"axes.unicode_minus": False}
plot_html_show_source_link = False
plot_html_show_formats = False
