Static build (GitHub Pages)
=============================

For hosting a public, read-only copy of the site (e.g. GitHub Pages) without exposing
any AI endpoints, build the ``Dockerfile.web`` ``build`` target. Prefer the shared
helper (used by CI as well):

.. code-block:: bash

   scripts/docker-build-web.sh              # image only (soju-web:static)
   scripts/docker-build-web.sh ./site-app   # build + extract /app/build

Equivalent ``docker build``:

.. code-block:: bash

   docker build -f docker/Dockerfile.web --target build -t soju-web:static .

Defaults bake a Pages-safe site: empty ``PUBLIC_BASE_PATH`` (site at ``/``),
``PUBLIC_AI_ENABLED=false``, ``PUBLIC_TTS_ENGINE=browser``. Override any knob with
``--build-arg`` or by exporting the same name before the script:

.. code-block:: bash

   PUBLIC_BASE_PATH=/soju-platform scripts/docker-build-web.sh ./site-app
   PUBLIC_TTS_ENGINE=piper scripts/docker-build-web.sh ./site-app

Controllable build-args: ``PUBLIC_BASE_PATH``, ``PUBLIC_TTS_ENGINE``,
``PUBLIC_TTS_PIPER_BASE_URL``, ``PUBLIC_TTS_PIPER_VOICE``, ``PUBLIC_AI_ENABLED``,
``PUBLIC_AI_API_MODE``, ``PUBLIC_AI_BASE_URL``, ``PUBLIC_AI_MODEL``,
``PUBLIC_AI_EMBED_MODEL``, ``PUBLIC_AI_SYSTEM_PROMPT``, ``PUBLIC_AI_TUTOR_NAME``.

Practice and Chat **routes are included** in the static output but **hidden from
navigation** and show an inert gate if visited directly — no model calls are ever
made from a build produced this way. This is intentional so the same codebase can
serve both a local, AI-enabled deployment (see :doc:`ai`) and a public static one
from a single build pipeline.

Use :doc:`site` for the regular local dev server (``docker compose up``), which keeps
Practice and Chat live when ``PUBLIC_AI_ENABLED=true``. Compose does **not** build
the static export; that is Dockerfile-only (see above).

GitHub Actions layout
---------------------

Four workflows under ``.github/workflows/``:

* **Lint** (``pre-commit.yml``) — ``uv run poe pre-commit`` on every branch push
* **Build docs** (``build-docs.yml``) — ``uv run poe docs`` on every branch push
* **Build app** (``build-app.yml``) — ``scripts/docker-build-web.sh`` on every branch push
* **Publish to GitHub Pages** (``publish.yml``) — Docker web build + Sphinx + deploy on
  **published GitHub Releases** (and manual ``workflow_dispatch``)

Branch-push workflows use a ``branches`` filter (not ``tags-ignore`` alone) so they
run on every branch push and skip tag pushes. The Pages workflow sets
``PUBLIC_BASE_PATH`` to ``/<repository name>`` (e.g. ``/soju-platform``)
and publishes:

* **App** at ``/soju-platform/`` (SvelteKit static export; artifact root + ``paths.base``)
* **Docs** at ``/soju-platform/docs/`` (Sphinx HTML from ``uv run poe docs``)

Live URLs (custom domain aliases ``orbingol.github.io``):

* ``https://onurraufbingol.com/soju-platform/``
* ``https://onurraufbingol.com/soju-platform/docs/``

Enable Pages in the repo settings: **Source → GitHub Actions**. After the first
successful deploy, the site URL appears on the workflow run and under
**Settings → Pages**.
