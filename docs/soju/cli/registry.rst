``soju registry``
=================

**Purpose:** Check UUID uniqueness, sense uniqueness, dangling topic refs, local entry shape,
and course ``level`` ids on vocabulary and grammar patterns.

.. list-table::
   :widths: 20 80

   * - **Reads**
     - ``data/content/registry/``, ``data/content/topics/manifest.yaml``,
       ``data/content/topics/*/topic.yaml``, ``data/content/levels.yaml``,
       ``data/content/grammar/``
   * - **Writes**
     - Nothing
   * - **Checks**
     - UUID uniqueness, duplicate **hangul+english** senses, dangling refs, duplicate refs
       within a topic, local entry shape, unknown vocabulary or grammar ``level`` ids
       (omitted ``level`` = unassigned, OK)
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
