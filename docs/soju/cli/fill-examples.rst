``soju-fill-examples``
======================

**Purpose:** Generate missing (or refresh) noun/verb example sentences. Default mode uses Ollama; ``--local`` uses built-in Korean 1A/1B templates (no network).

.. list-table::
   :widths: 20 80

   * - **Reads**
     - ``data/content/registry/vocabulary.yaml``, ``data/content/registry/examples.yaml``, verb forms
   * - **Writes**
     - ``data/content/registry/examples.yaml`` (unless ``--dry-run`` / ``--clean-only`` as applicable)
   * - **Exit codes**
     - ``0`` success · non-zero on error

.. typer:: soju.cli.examples.app
   :prog: soju-fill-examples
   :preferred: text
   :markup-mode: markdown
   :width: 78

.. code-block:: bash

   uv run soju-fill-examples --dry-run
   uv run soju-fill-examples --local --nouns-only
   uv run soju-fill-examples --mode fill-empty --limit 10
   uv run soju-fill-examples --clean-only

Use carefully on large registries; prefer ``--dry-run`` / ``--limit`` first. Prefer ``soju-import`` when you already have curated examples.
