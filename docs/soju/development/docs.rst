Build the documentation
========================

This guide (``docs/soju/``, reStructuredText) is command-oriented — there is no Python
API/class reference. Building is a thin wrapper around ``docs/Makefile``, which calls
``sphinx-build`` / ``sphinx-autobuild`` under the hood.

.. code-block:: bash

   uv run poe docs          # HTML → docs/_build/html/
   uv run poe docs-serve    # live-reload preview, opens a browser tab

Equivalent to running ``make`` directly from ``docs/``:

.. code-block:: bash

   make -C docs html
   make -C docs clean
   make -C docs serve
   # Windows: docs\make.bat html

CLI option help (e.g. ``--level``) is generated at build time from the live Typer apps
via ``sphinxcontrib-typer``, which needs ``DATA_DIR`` to resolve; ``docs/conf.py``
defaults it to the repo's ``data/`` directory automatically, so no extra setup is
required.

Theme
-----

The HTML theme defaults to `furo <https://pradyunsg.me/furo/>`_ and is configurable via
the ``SPHINX_THEME`` environment variable (the theme package must already be
installed):

.. code-block:: bash

   make -C docs html SPHINX_THEME=alabaster

Adding a page
--------------

1. Create an ``.rst`` file under ``docs/soju/development/`` or ``docs/soju/cli/``.
2. List it in the matching ``toctree`` in the root :doc:`/index`. Pages intentionally
   left out of every toctree (e.g. section overview pages) need an ``:orphan:`` field
   list at the top, or Sphinx warns that the document "isn't included in any toctree".
3. Rebuild with ``uv run poe docs`` and check the output for warnings before committing.
