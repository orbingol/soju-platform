Static build (GitHub Pages)
=============================

For hosting a public, read-only copy of the site (e.g. GitHub Pages) without exposing
any AI endpoints:

.. code-block:: bash

   docker compose --profile build build web-build

The ``web-build`` target sets ``PUBLIC_AI_ENABLED=false`` at build time. Practice and
Chat **routes are included** in the static output but **hidden from navigation** and
show an inert gate if visited directly — no model calls are ever made from a build
produced this way. This is intentional so the same codebase can serve both a local,
AI-enabled deployment (see :doc:`ai`) and a public static one from a single build
pipeline.

Use :doc:`site` for the regular local dev server (``docker compose up``), which keeps
Practice and Chat live when ``PUBLIC_AI_ENABLED=true``.
