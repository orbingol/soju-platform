Poe tasks (shortcuts)
=====================

`poethepoet <https://poethepoet.natn.io/>`_ tasks, defined in ``pyproject.toml``, wrap the
CLIs under :doc:`/cli/index` for common workflows. Run any of them with ``uv run poe <task>``.

Validate
--------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Task
     - Command
   * - Full validate
     - ``uv run poe validate``
   * - Schema / align / registry only
     - ``uv run poe validate-schemas`` · ``validate-align`` · ``validate-registry``
   * - Validate in Docker
     - ``uv run poe validate-docker``

Compose
-------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Task
     - Command
   * - Dev (Vite :5173, API :8000)
     - ``uv run poe up``
   * - Prod (nginx :8080)
     - ``uv run poe up-prod``

See :doc:`docker` for the full Compose layout.

Import, translate & embed
-------------------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Task
     - Command
   * - Import words (file, merge-only)
     - ``uv run poe import-words --file words.txt --topic common``
   * - Import verbs (stdin JSON)
     - ``uv run poe import-verbs``
   * - Translate words → JSON
     - ``uv run poe translate-words --file words.txt``
   * - Build Practice embedding cache
     - ``uv run poe embed-index``

Test & docs
-----------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Task
     - Command
   * - Python tests (unit + offline system)
     - ``uv run poe test``
   * - System / LLM / all / coverage
     - ``uv run poe test-system`` · ``test-llm`` · ``test-all`` · ``coverage``
   * - Build docs
     - ``uv run poe docs``
   * - Serve docs (live reload)
     - ``uv run poe docs-serve``

Lint & pre-commit
-----------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Task
     - Command
   * - Lint
     - ``uv run poe lint``
   * - Pre-commit (all hooks)
     - ``uv run poe pre-commit``
