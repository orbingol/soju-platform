Docker
======

Compose services run the web app, validate data, and build static exports. The Compose
**project name** is ``soju``: containers use the ``soju-`` prefix, named volumes use
``soju_``.

Core services
-------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Goal
     - Command
   * - Web dev
     - ``docker compose up``
   * - Web unit tests
     - ``docker compose exec web npm test``
   * - Validate (canonical image)
     - ``docker compose --profile validate run --rm validate``
   * - Static build
     - ``docker compose --profile build build web-build``

Optional profiles
------------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Goal
     - Command
   * - Ollama (AI features, containerized)
     - ``docker compose --profile ollama up ollama ollama-pull web``

See :doc:`ai` for the Ollama/TTS environment variables that control Practice and Chat.

Python CLIs on Docker
----------------------

Python CLIs (``soju-import``, etc.) normally run on the host via ``uv run`` with
``./data`` bind-mounted paths — see :doc:`/cli/index`. They also work inside any
container with the repo mounted at ``/workspace`` and ``uv sync`` run once.

**Node / npm:** never run ``npm install`` on the host — use the ``web_node_modules``
Compose volume. If ``apps/web/node_modules/`` exists locally, delete it.
