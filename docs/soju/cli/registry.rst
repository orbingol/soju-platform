``soju registry``
=================

**Purpose:** Check UUID uniqueness, sense uniqueness, dangling topic refs, and local entry shape.

.. list-table::
   :widths: 20 80

   * - **Reads**
     - ``data/content/registry/``, ``data/content/topics/manifest.yaml``, ``data/content/topics/*/topic.yaml``
   * - **Writes**
     - Nothing
   * - **Checks**
     - UUID uniqueness, duplicate **hangul+english** senses, dangling refs, duplicate refs within a topic, local entry shape
   * - **Exit codes**
     - ``0`` OK · ``1`` registry errors

.. typer:: soju.cli.validate.registry_app
   :prog: soju registry
   :preferred: text
   :markup-mode: markdown
   :width: 78

.. code-block:: bash

   uv run soju registry
   uv run poe validate-registry
