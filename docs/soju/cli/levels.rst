``soju levels``
===============

**Purpose:** List and assign course levels on **vocabulary** registry entries and
**grammar** pattern files. Catalog of valid ids lives in ``data/content/levels.yaml``.

Omitted ``level`` means **unassigned** (not a silent default to ``1A``). Present
``level`` values must be keys in ``levels.yaml``; unlisted ids fail write paths and
``soju registry`` / ``poe validate``.

.. list-table::
   :widths: 20 80

   * - **Reads**
     - ``data/content/levels.yaml``, ``data/content/registry/vocabulary.yaml``,
       ``data/content/grammar/`` (manifest + patterns)
   * - **Writes**
     - Vocabulary ``level`` fields, or grammar pattern ``level`` fields (by ``--kind``)
   * - **Exit codes**
     - ``0`` success · ``1`` error · ``2`` usage error

.. typer:: soju.cli.levels.app
   :prog: soju levels
   :show-nested:
   :make-sections:
   :preferred: text
   :markup-mode: markdown
   :width: 78

Kinds
-----

``--kind vocabulary`` (default) targets registry entries by UUID.
``--kind grammar`` targets grammar pattern ids from the grammar manifest.

Selection for ``set``
---------------------

Exactly one selection mode:

- ``--all-unassigned`` — every entry of the chosen kind with no ``level``
- ``--id`` — one or more ids (repeatable)
- ``--ids-file`` — one id per line (``-`` = stdin)

Use ``--force`` to overwrite an existing level tag. Prefer ``--dry-run`` first.

Examples
--------

.. code-block:: bash

   # List unassigned vocabulary (table or ids-only)
   uv run soju levels list-unassigned
   uv run soju levels list-unassigned --format ids

   # Stamp every unassigned vocab entry to 1A
   uv run soju levels set --level 1A --all-unassigned --dry-run
   uv run soju levels set --level 1A --all-unassigned

   # Partial retag by UUID
   uv run soju levels set --level 1B --id <uuid> --id <uuid>

   # Grammar patterns
   uv run soju levels list-unassigned --kind grammar
   uv run soju levels set --kind grammar --level 1A --all-unassigned

   # Pipe ids
   uv run soju levels list-unassigned --format ids | uv run soju levels set --level 1A --ids-file -

Import vs retag
---------------

New vocabulary can take an optional course level at import time
(``soju import words|verbs --level …`` or per-record ``level``). Omitted = unassigned.
To retag existing vocab or grammar, use ``soju levels`` — do not mass-edit YAML by hand.
See :doc:`import`.

Unassigned vocabulary is excluded from Practice (unless *Include supplemental content*) and
from course AI prompt word lists. ``soju fill-examples --local`` still generates for
unassigned rows in the selected band; stamp or import with ``--level`` when you want them in
the course band — see :doc:`fill-examples`.
