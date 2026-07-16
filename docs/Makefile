# SPDX-License-Identifier: BSD-3-Clause
# Sphinx documentation (run from docs/ or via ``uv run poe docs`` / ``docs-serve``).

SPHINXOPTS      ?=
SPHINXBUILD     ?= sphinx-build
SPHINXAUTOBUILD ?= sphinx-autobuild
SPHINX_THEME    ?= furo
SOURCEDIR       = soju
BUILDDIR        = _build
# conf.py lives in docs/ (this directory), not under SOURCEDIR
SPHINXOPTS      := -c . $(SPHINXOPTS)

export SPHINX_THEME

.PHONY: html clean serve

html:
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O)

clean:
	@rm -rf "$(BUILDDIR)"

serve:
	@$(SPHINXAUTOBUILD) "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O) --open-browser
