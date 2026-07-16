# SPDX-License-Identifier: BSD-3-Clause
"""Sphinx configuration for the Soju user guide (no API autodoc)."""

from __future__ import annotations

import os
import sys
from datetime import date
from importlib.metadata import PackageNotFoundError, version as pkg_version
from pathlib import Path

# -- Path setup --------------------------------------------------------------
# Source RST lives in docs/soju/; conf.py lives in docs/.
DOCS_DIR = Path(__file__).resolve().parent
REPO_ROOT = DOCS_DIR.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

# CLI option help (e.g. ``--level``) reads ``levels.yaml`` at import time.
os.environ.setdefault("DATA_DIR", str(REPO_ROOT / "data"))

# -- Project information -----------------------------------------------------
project = "Soju"
author = "Onur R. Bingol"
copyright = f"{date.today().year}, {author}"

try:
    release = pkg_version("soju")
except PackageNotFoundError:
    release = "1.0.0"
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx_copybutton",
    "sphinxcontrib.typer",
]

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
]

source_suffix = {
    ".rst": "restructuredtext",
}
root_doc = "index"
language = "en"

# Prefer ``literal`` for unmatched single backticks in prose.
default_role = "literal"

# Warn about all references (useful while editing; keep False for quiet CI).
nitpicky = False

# -- Options for todo extension ----------------------------------------------
todo_include_todos = False
todo_emit_warnings = False

# -- Options for extlinks ----------------------------------------------------
# Short links: :repo:`README.md`, :data:`content/topics/manifest.yaml`
extlinks = {
    "repo": ("https://github.com/orbingol/soju-platform/blob/main/%s", "%s"),
    "data": ("https://github.com/orbingol/soju-platform/blob/main/data/%s", "data/%s"),
}

# -- Options for intersphinx -------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master", None),
}

# -- Options for sphinx_copybutton -------------------------------------------
copybutton_prompt_text = r"\$ |>>> |\.\.\. "
copybutton_prompt_is_regexp = True
copybutton_line_continuation_character = "\\"

# -- Options for HTML output -------------------------------------------------
# Override with ``make html SPHINX_THEME=alabaster`` (theme package must be installed).
html_theme = os.environ.get("SPHINX_THEME", "furo")
html_title = "Soju Platform"
html_short_title = "Soju"
html_static_path = ["_static"]

html_theme_options: dict = {}
if html_theme == "furo":
    html_theme_options = {
        "sidebar_hide_name": False,
        "top_of_page_button": "edit",
        "source_repository": "https://github.com/orbingol/soju-platform",
        "source_branch": "main",
        "source_directory": "docs/soju/",
    }

html_copy_source = True
html_show_sourcelink = True
html_show_sphinx = True
html_show_copyright = True

# -- Options for LaTeX output ------------------------------------------------
latex_elements: dict[str, str] = {}
latex_documents = [
    (root_doc, "soju.tex", "Soju Platform Documentation", author, "manual"),
]

# -- Options for manual page output ------------------------------------------
man_pages = [
    (root_doc, "soju", "Soju Platform Documentation", [author], 1),
]

# -- Options for Texinfo output ----------------------------------------------
texinfo_documents = [
    (
        root_doc,
        "soju",
        "Soju Platform Documentation",
        author,
        "Soju",
        "Korean language learning platform development guide.",
        "Miscellaneous",
    ),
]

# -- Options for Epub output -------------------------------------------------
epub_title = project
epub_exclude_files = ["search.html"]
