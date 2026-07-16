Local Python setup
===================

Requires `uv <https://docs.astral.sh/uv/>`_ (do not use plain ``pip``/``venv`` — the
project is managed entirely through ``uv``). From the repo root:

.. code-block:: bash

   uv sync

This creates ``.venv/`` and installs the ``soju`` package in editable mode along with
its ``docs`` and ``dev`` dependency groups (both installed by default — CLIs, tests, and
Sphinx are ready right after). Run anything with ``uv run``, no activation needed:

.. code-block:: bash

   uv run poe validate
   uv run soju-import --help

Re-run ``uv sync`` after pulling changes that touch ``pyproject.toml`` or ``uv.lock``.

Project layout
---------------

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Path
     - Contents
   * - ``src/soju/cli/``
     - Typer apps behind each console script (entry points in ``pyproject.toml``)
   * - ``src/soju/services/``
     - Import, promote, translate, and fill logic used by the CLIs
   * - ``src/soju/core/``
     - Shared config, YAML I/O, logging, and text helpers
   * - ``src/soju/languages/``
     - Language-specific rules (Korean conjugation, example generation)
   * - ``src/soju/llm/``
     - Ollama client used by the AI-assisted tools
   * - ``src/soju/registry/``
     - Registry/uniqueness helpers shared by validation and import
   * - ``tests/``
     - Mirrors ``src/soju/``, plus ``tests/system/`` (CLI pipelines) and ``tests/cli/``

See :doc:`/cli/index` for the full command catalog and ``AGENTS.md`` at the repo root
for write-path boundaries (what agents/tools must not hand-edit).
