Import vocabulary
==================

``soju import`` is the **only** supported write path for canonical vocabulary — it
updates the registry, the examples store, and topic/verb files atomically. **Never
hand-edit** ``data/content/registry/``, topic entry lists, verb forms, or examples
directly; see :doc:`data-layout` for what lives where.

.. code-block:: bash

   cat records.json | uv run soju import words --topic common --stdin-json
   cat verbs.json   | uv run soju import verbs --stdin-json
   uv run poe validate

Always finish with ``uv run poe validate`` (or the Docker validate profile) after an
import — see :doc:`validate`.

Course levels on import
-----------------------

New words and verbs may take an optional course level via ``--level`` or a per-record
``level`` field (ids from ``data/content/levels.yaml``). Per-record wins. If both are
omitted, the entry is **unassigned**. To stamp or retag existing vocabulary or grammar
patterns, use ``soju levels`` — see :doc:`/cli/levels`.

Staging workflow
-----------------

Content that needs review before it becomes canonical goes through ``data/staging/``
instead of straight into the registry:

1. Draft candidates in ``data/staging/vocabulary-candidates.yaml`` (schema-checked, see
   :doc:`editor`).
2. Review and edit as needed.
3. Import the reviewed staging file: ``soju import words --from-staging
   data/staging/vocabulary-candidates.yaml --topic <id>``.
4. Or, for entries already marked ``local: true`` on a topic, promote them into the
   registry with ``soju promote --topic <id>`` (``--dry-run`` first is recommended).

AI-assisted workflow
----------------------

The slash commands under ``.ai/commands/`` (``import-words``, ``import-words-to``,
``import-verbs``, ``import-staging``, ``promote-local``, ``translate-words``,
``embed-index``) parse free-form input, call the matching ``soju`` CLI, and run
validation where appropriate — read the matching ``.ai/commands/*.md`` file before
invoking one.

Grammar lessons
-----------------

Grammar lesson YAML under ``data/content/grammar/`` is authored directly (schemas still
apply, see :doc:`editor`) — only vocabulary and verbs go through ``soju import``. Assign
or retag pattern ``level`` with ``soju levels --kind grammar`` rather than hand-mass-
editing levels across pattern files.

See :doc:`/cli/import`, :doc:`/cli/promote`, and :doc:`/cli/levels` for flags and record shapes.
