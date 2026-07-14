CLI reference
=============

Console tools live in ``src/soju/`` and install with ``uv sync``. Run from the repo root unless noted.

**Validate after any data change:** ``uv run poe validate`` or ``docker compose --profile validate run --rm validate``

``soju-validate-schemas``
-------------------------

**Purpose:** Run ``check-jsonschema`` over all canonical YAML files (paths discovered
from manifests). Includes staging exercise/story files and verb construction files when
present on disk.

.. list-table::
   :widths: 20 80

   * - **Reads**
     - ``data/content/registry/``, ``data/content/topics/``, ``data/content/verbs/``, ``data/content/grammar/``, ``data/content/words/table.yaml``, ``data/staging/``
   * - **Writes**
     - Nothing
   * - **Exit codes**
     - ``0`` pass · ``1`` validation failure

.. code-block:: bash

   uv run soju-validate-schemas
   # or
   uv run poe validate-schemas

Included in ``uv run poe validate``.

``soju-align``
--------------

**Purpose:** Verify verb vocabulary entries appear in every forms file required by
``data/content/verbs/manifest.yaml`` and ``data/content/verbs/table.yaml``. When examples
exist in ``data/content/registry/examples.yaml`` for a tense, all table variants for that
tense must be present; **examples are optional** (verbs may be forms-only).

.. list-table::
   :widths: 20 80

   * - **Reads**
     - ``data/content/registry/vocabulary.yaml``, ``data/content/verbs/manifest.yaml``, ``data/content/verbs/table.yaml``, ``data/content/verbs/forms/*.yaml``, ``data/content/registry/examples.yaml``
   * - **Writes**
     - Nothing
   * - **Exit codes**
     - ``0`` OK · ``1`` alignment errors

.. code-block:: bash

   uv run soju-align
   uv run poe validate-align
   docker compose --profile validate run --rm validate   # runs full validate

**AI commands:** none (automatic in ``poe validate``).

``soju-registry``
-----------------

**Purpose:** Check UUID uniqueness, sense uniqueness, dangling topic refs, and local entry shape.

.. list-table::
   :widths: 20 80

   * - **Reads**
     - ``data/content/registry/``, ``data/content/topics/manifest.yaml``, ``data/content/topics/*/topic.yaml``
   * - **Writes**
     - Nothing
   * - **Checks**
     - UUID uniqueness, duplicate **hangul+english** senses, dangling refs, duplicate refs within a topic, local entry shape
   * - **Exit codes**
     - ``0`` OK · ``1`` registry errors

.. code-block:: bash

   uv run soju-registry
   uv run poe validate-registry

``soju-import``
---------------

**Purpose:** **Only supported write path** for canonical vocabulary. Merges words (vocabulary + examples + topic refs) and verbs (vocabulary + forms + examples store).

.. list-table::
   :widths: 20 80

   * - **Reads**
     - stdin JSON, plain-text ``--file``, or staging YAML
   * - **Writes**
     - ``data/content/registry/vocabulary.yaml``, ``data/content/registry/examples.yaml``, ``data/content/topics/``, ``data/content/verbs/forms/``
   * - **Exit codes**
     - ``0`` success · ``1`` errors / nothing imported · ``2`` usage error

Words
~~~~~

.. code-block:: bash

   # New words (AI workflow) — full records required
   cat records.json | uv run soju-import words --topic common --stdin-json

   # Preview
   uv run soju-import words --topic family --stdin-json --dry-run < records.json

   # Merge examples only for existing registry words
   uv run soju-import words --topic common --file words.txt

   # From staging
   uv run soju-import words --from-staging data/staging/vocabulary-candidates.yaml --topic common

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Flag
     - Description
   * - ``--topic``
     - Topics manifest id (default ``common``)
   * - ``--section``
     - Section id within topic (required when topic has multiple sections)
   * - ``--stdin-json``
     - JSON array or ``{"records":[...]}`` on stdin
   * - ``--file``
     - Plain-text lines; **existing words only**
   * - ``--from-staging``
     - Staging vocabulary YAML path
   * - ``--dry-run``
     - Report without writing

**Uniqueness:** registry entries are keyed by **hangul + English meaning**. Same hangul with
a different English gloss (e.g. 배 “pear” vs 배 “ship / boat”) is a separate entry (homonym).
Re-importing the same sense merges examples and topic refs.

**Gloss style:** vocabulary ``english`` meanings are lowercased except proper names
(e.g. ``Korean language``, ``Seoul``, ``Japanese``). Example sentences keep normal sentence
capitalization and punctuation.

**Visibility:** optional ``visibility: hidden`` hides an entry from Word types, Topics, and
Flashcards while keeping it available to Practice and chat. Grammar practice phrases use
``type: phrase`` and ``visibility: hidden``, with optional ``grammar_pattern`` linking to a
Grammar lesson id.

Verbs
~~~~~

.. code-block:: bash

   cat verbs.json | uv run soju-import verbs --stdin-json

Requires ``hangul``, ``romanization``, ``english``, ``forms`` (and optional ``examples``) per record. ``--file`` without JSON is not supported for new verbs.

**Limitation:** Re-importing an existing verb with the same hangul **and** English meaning is
not supported — the CLI returns an error. Same hangul with a different English gloss is allowed
as a homonym. Update existing verb senses by editing split files or extend ``soju-import`` when
merge is needed.

**AI commands:** ``import-words``, ``import-words-to``, ``import-verbs``, ``import-staging``

``soju-promote``
----------------

**Purpose:** Promote ``local: true`` entries in a topic to ``data/content/registry/vocabulary.yaml``.

.. list-table::
   :widths: 20 80

   * - **Reads**
     - ``data/content/topics/<topic>/topic.yaml``
   * - **Writes**
     - ``data/content/registry/vocabulary.yaml``, ``data/content/registry/examples.yaml`` (if locals have examples), topic file (refs replace locals)
   * - **Exit codes**
     - ``0`` success · ``1`` error

.. code-block:: bash

   uv run soju-promote --topic family
   uv run soju-promote --topic family --dry-run

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Flag
     - Description
   * - ``--topic``
     - Topics manifest id (required)
   * - ``--dry-run``
     - Report without writing

**AI commands:** ``promote-local``

``soju-translate-words``
------------------------

**Purpose:** Turn a plain-text word list into ``soju-import`` JSON via Ollama (romanization,
English gloss, optional examples). Pipe stdout into ``soju-import``, or write with ``--output``.

.. list-table::
   :widths: 20 80

   * - **Reads**
     - Plain-text ``--file``; registry (for ``--skip-existing``)
   * - **Writes**
     - Nothing (stdout or ``--output`` JSON only)
   * - **Exit codes**
     - ``0`` success · non-zero on error

.. code-block:: bash

   uv run soju-translate-words --file words.txt | uv run soju-import words --topic common --stdin-json
   uv run poe translate-words --file words.txt
   uv run soju-translate-words --file words.txt --dry-run
   uv run soju-translate-words --file words.txt --skip-existing -o records.json

Requires a reachable Ollama (or compatible) server unless ``--dry-run``. Level defaults to ``SOJU_KOREAN_LEVEL`` or ``1A``.

``soju-fill-examples``
----------------------

**Purpose:** Generate missing (or refresh) noun/verb example sentences. Default mode uses Ollama; ``--local`` uses built-in Korean 1A/1B templates (no network).

.. list-table::
   :widths: 20 80

   * - **Reads**
     - ``data/content/registry/vocabulary.yaml``, ``data/content/registry/examples.yaml``, verb forms
   * - **Writes**
     - ``data/content/registry/examples.yaml`` (unless ``--dry-run`` / ``--clean-only`` as applicable)
   * - **Exit codes**
     - ``0`` success · non-zero on error

.. code-block:: bash

   uv run soju-fill-examples --dry-run
   uv run soju-fill-examples --local --nouns-only
   uv run soju-fill-examples --mode fill-empty --limit 10
   uv run soju-fill-examples --clean-only

Use carefully on large registries; prefer ``--dry-run`` / ``--limit`` first. Prefer ``soju-import`` when you already have curated examples.

``soju-fill-verbs``
-------------------

**Purpose:** Bulk-regenerate conjugation forms and example sentences for **all** registry verbs (local conjugator; overwrites forms files and verb examples in the store).

.. list-table::
   :widths: 20 80

   * - **Reads**
     - ``data/content/registry/vocabulary.yaml``
   * - **Writes**
     - ``data/content/verbs/forms/*.yaml``, ``data/content/registry/examples.yaml``
   * - **Exit codes**
     - ``0`` success · non-zero on error

.. code-block:: bash

   uv run soju-fill-verbs --dry-run
   uv run soju-fill-verbs

Development utility — do not run casually over curated data. Prefer ``soju-import verbs`` for new or updated senses.

Poe tasks (shortcuts)
---------------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Task
     - Command
   * - Full validate
     - ``uv run poe validate``
   * - Schema / align / registry only
     - ``uv run poe validate-schemas`` · ``validate-align`` · ``validate-registry``
   * - Import words (file, merge-only)
     - ``uv run poe import-words --file words.txt --topic common``
   * - Import verbs (stdin JSON)
     - ``uv run poe import-verbs``
   * - Translate words → JSON
     - ``uv run poe translate-words --file words.txt``
   * - Validate in Docker
     - ``uv run poe validate-docker``
   * - Run Python unit tests
     - ``uv run poe test``
   * - Build docs
     - ``uv run poe docs``
   * - Serve docs (live reload)
     - ``uv run poe docs-serve``

Docker
------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Goal
     - Command
   * - Validate (canonical image)
     - ``docker compose --profile validate run --rm validate``
   * - Web unit tests
     - ``docker compose exec web npm test``
   * - Web dev
     - ``docker compose up``
   * - Static build
     - ``docker compose --profile build build web-build``

Python CLIs (``soju-import``, etc.) run on the host via ``uv run`` with ``./data`` bind-mounted
paths, or inside any container with the repo mounted at ``/workspace`` and ``uv sync``.
