``soju align``
==============

**Purpose:** Verify verb vocabulary entries appear in every forms file required by
``data/content/verbs/manifest.yaml`` and ``data/content/verbs/table.yaml``. When examples
exist in ``data/content/registry/examples.yaml`` for a tense, all table variants for that
tense must be present; **examples are optional** (verbs may be forms-only).

.. list-table::
   :widths: 20 80

   * - **Reads**
     - ``data/content/registry/vocabulary.yaml``, ``data/content/verbs/manifest.yaml``, ``data/content/verbs/table.yaml``, ``data/content/verbs/forms/*.yaml``, ``data/content/registry/examples.yaml``
   * - **Writes**
     - Nothing
   * - **Exit codes**
     - ``0`` OK · ``1`` alignment errors

.. typer:: soju.cli.validate.align_app
   :prog: soju align
   :preferred: text
   :markup-mode: markdown
   :width: 78

.. code-block:: bash

   uv run soju align
   uv run poe validate-align

**AI commands:** none (automatic in ``poe validate``).
