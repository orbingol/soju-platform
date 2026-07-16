``soju-promote``
================

**Purpose:** Promote ``local: true`` entries in a topic to ``data/content/registry/vocabulary.yaml``.

.. list-table::
   :widths: 20 80

   * - **Reads**
     - ``data/content/topics/<topic>/topic.yaml``
   * - **Writes**
     - ``data/content/registry/vocabulary.yaml``, ``data/content/registry/examples.yaml`` (if locals have examples), topic file (refs replace locals)
   * - **Exit codes**
     - ``0`` success · ``1`` error

.. typer:: soju.cli.promote.app
   :prog: soju-promote
   :preferred: text
   :markup-mode: markdown
   :width: 78

.. code-block:: bash

   uv run soju-promote --topic family
   uv run soju-promote --topic family --dry-run

**AI commands:** ``promote-local``
