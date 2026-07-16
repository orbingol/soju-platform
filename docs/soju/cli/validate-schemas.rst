``soju-validate-schemas``
=========================

**Purpose:** Run ``check-jsonschema`` over all canonical YAML files (paths discovered
from manifests). Includes staging exercise/story files and verb construction files when
present on disk.

.. list-table::
   :widths: 20 80

   * - **Reads**
     - ``data/content/registry/``, ``data/content/topics/``, ``data/content/verbs/``, ``data/content/grammar/``, ``data/content/words/table.yaml``, ``data/staging/``
   * - **Writes**
     - Nothing
   * - **Exit codes**
     - ``0`` pass · ``1`` validation failure

.. typer:: soju.cli.validate.schemas_app
   :prog: soju-validate-schemas
   :preferred: text
   :markup-mode: markdown
   :width: 78

.. code-block:: bash

   uv run soju-validate-schemas
   uv run poe validate-schemas

Included in ``uv run poe validate``.
