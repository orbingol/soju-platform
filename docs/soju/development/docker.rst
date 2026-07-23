Docker
======

Compose services run the web app and validate data. The Compose **project name** is
``soju``: containers use the ``soju-`` prefix, named volumes use ``soju_``.

Core services
-------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Goal
     - Command
   * - Web + Soju API (nginx :8080)
     - ``docker compose up``
   * - Web unit tests
     - ``docker compose exec web npm test``
   * - Validate (canonical image)
     - ``docker compose --profile validate run --rm validate``
   * - Static web build
     - ``scripts/docker-build-web.sh`` (see :doc:`static-build`)

``docker compose up`` starts ``web`` (:5173), ``backend`` (FastAPI), and ``nginx``
(:8080 → backend). Do not revive the old ``docker/piper`` TTS image — speech is
served by the Soju backend.

Optional profiles
------------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Goal
     - Command
   * - Ollama (AI features, containerized)
     - ``docker compose --profile ollama up ollama ollama-pull web``

See :doc:`ai` for Practice/Chat setup and :doc:`tts` for local speech.

Python CLIs on Docker
----------------------

Python CLIs (``soju import``, etc.) normally run on the host via ``uv run`` with
``./data`` bind-mounted paths — see :doc:`/cli/index`. They also work inside any
container with the repo mounted at ``/workspace`` and ``uv sync`` run once.

**Node / npm:** never run ``npm install`` on the host — use the ``web_node_modules``
Compose volume. If ``apps/web/node_modules/`` exists locally, delete it.
