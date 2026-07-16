Validate data
=============

Run after any change under ``data/`` — before committing and in CI:

.. code-block:: bash

   uv run poe validate

Or in the canonical Docker image (no local Python setup needed):

.. code-block:: bash

   docker compose --profile validate run --rm validate

``poe validate`` runs three checks in sequence, each also runnable on its own:

.. list-table::
   :header-rows: 1
   :widths: 30 25 45

   * - Check
     - Command
     - What it catches
   * - JSON Schema
     - ``uv run poe validate-schemas``
     - Malformed/missing fields against ``data/schemas/`` (see :doc:`editor`)
   * - Verb alignment
     - ``uv run poe validate-align``
     - Verb forms out of sync with the registry (``soju-align``)
   * - Registry
     - ``uv run poe validate-registry``
     - UUID/ref integrity and sense uniqueness — hangul + English meaning; homonyms are
       allowed (``soju-registry``)

``uv run poe pre-commit`` (alias: ``lint``) runs these plus the rest of the pre-commit
hooks on all files.

See :doc:`/cli/index` for the individual CLI tools and :doc:`import` for how new data
gets written in the first place.
