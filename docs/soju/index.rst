Soju (소주) Platform docs
===========================

User guide for running the site, validating data, and using the Python CLIs.
This is a command-oriented guide — there is no Python API / class reference.

.. toctree::
   :maxdepth: 2
   :caption: Guide

   development
   cli

Quick start
-----------

.. code-block:: bash

   uv sync
   uv run poe docs-serve

Build HTML once with ``uv run poe docs`` (output: ``docs/_build/html/``).

For a non-technical overview, see ``README.md`` at the repository root.
Agent-oriented rules live in ``AGENTS.md`` at the repo root.
