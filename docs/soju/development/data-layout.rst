Data layout (overview)
=======================

Canonical language data lives under ``data/content/``; staging content awaiting review
lives at ``data/staging/``. Both are read via the ``DATA_DIR`` environment variable —
``./data`` on the host, ``/data`` inside Docker containers.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Area
     - Path
   * - Word & verb registry + examples
     - ``data/content/registry/`` (``vocabulary.yaml``, ``examples.yaml``, ``types.yaml``)
   * - Word topics
     - ``data/content/topics/<id>/topic.yaml`` (listed in ``manifest.yaml``)
   * - Verb forms
     - ``data/content/verbs/forms/`` (manifest + table in ``data/content/verbs/``)
   * - Grammar lessons
     - ``data/content/grammar/`` (``manifest.yaml`` + ``patterns/``)
   * - Staging (review before import)
     - ``data/staging/`` (``vocabulary-candidates.yaml``, ``exercises/``, ``stories/``)

JSON Schemas for every file above live in ``data/schemas/`` and are checked by
``soju-validate-schemas`` (see :doc:`validate`) — the same schemas power inline
validation in editors (see :doc:`editor`). The web app reads this tree read-only via
``DATA_DIR``; it never writes back to it.

Writing data
------------

**Never hand-edit** the registry, topic entry lists, verb forms, or examples —
``soju-import`` is the only supported write path, and ``soju-promote`` moves reviewed
staging entries into the registry. See :doc:`import` for the full workflow, and
``AGENTS.md`` at the repo root for the complete list of boundaries.
