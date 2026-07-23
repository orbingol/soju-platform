``soju import``
===============

**Purpose:** **Only supported write path** for canonical vocabulary. Merges words (vocabulary + examples + topic refs) and verbs (vocabulary + forms + examples store).

.. list-table::
   :widths: 20 80

   * - **Reads**
     - stdin JSON, plain-text ``--file``, or staging YAML
   * - **Writes**
     - ``data/content/registry/vocabulary.yaml``, ``data/content/registry/examples.yaml``, ``data/content/topics/``, ``data/content/verbs/forms/``
   * - **Exit codes**
     - ``0`` success · ``1`` errors / nothing imported · ``2`` usage error

.. typer:: soju.cli.words.app
   :prog: soju import
   :show-nested:
   :make-sections:
   :preferred: text
   :markup-mode: markdown
   :width: 78

Words
-----

.. code-block:: bash

   # New words (AI workflow) — full records required
   cat records.json | uv run soju import words --topic common --stdin-json

   # Preview
   uv run soju import words --topic family --stdin-json --dry-run < records.json

   # Merge examples only for existing registry words
   uv run soju import words --topic common --file words.txt

   # From staging (hangul + english required; romanization optional — autofilled from hangul)
   uv run soju import words --from-staging data/staging/vocabulary-candidates.yaml --topic common

Word records need ``hangul`` and ``english``. If ``romanization`` is omitted or blank, import
fills it with Revised Romanization derived from the hangul (lowercase, hyphenated syllables).

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

**Course level:** optional ``--level`` (or per-record ``level``) tags new words with a course
id from ``data/content/levels.yaml``. Per-record wins over the CLI flag. If both are omitted,
the entry is **unassigned** (no ``level`` field) — not silently ``1A``. Retag existing entries
with :doc:`levels` (``soju levels set``), not by hand-editing the registry.

Practice and course AI prompts exclude unassigned rows unless supplemental content is opted
in. ``soju fill-examples --local`` includes unassigned entries in its generation target so a
fresh import without ``--level`` can still receive examples; stamp with ``soju levels`` (or
pass ``--level`` on import) before relying on course-banded Practice filtering.

Verbs
-----

.. code-block:: bash

   cat verbs.json | uv run soju import verbs --stdin-json

Requires ``hangul``, ``romanization``, ``english``, ``forms`` (and optional ``examples``) per record. ``--file`` without JSON is not supported for new verbs.

Optional ``--level`` / per-record ``level`` follows the same rules as words (omit = unassigned).

**Limitation:** Re-importing an existing verb with the same hangul **and** English meaning is
not supported — the CLI returns an error. Same hangul with a different English gloss is allowed
as a homonym. Update existing verb senses by editing split files or extend ``soju import`` when
merge is needed.

**AI commands:** ``import-words``, ``import-words-to``, ``import-verbs``, ``import-staging``
