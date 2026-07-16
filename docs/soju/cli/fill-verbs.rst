``soju-fill-verbs``
===================

**Purpose:** Bulk-regenerate conjugation forms and example sentences for **all** registry verbs (local conjugator; overwrites forms files and verb examples in the store).

.. list-table::
   :widths: 20 80

   * - **Reads**
     - ``data/content/registry/vocabulary.yaml``
   * - **Writes**
     - ``data/content/verbs/forms/*.yaml``, ``data/content/registry/examples.yaml``
   * - **Exit codes**
     - ``0`` success · non-zero on error

.. typer:: soju.cli.verbs.app
   :prog: soju-fill-verbs
   :preferred: text
   :markup-mode: markdown
   :width: 78

.. code-block:: bash

   uv run soju-fill-verbs --dry-run
   uv run soju-fill-verbs

Development utility — do not run casually over curated data. Prefer ``soju-import verbs`` for new or updated senses.
