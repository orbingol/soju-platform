``soju-import``
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
   :prog: soju-import
   :show-nested:
   :make-sections:
   :preferred: text
   :markup-mode: markdown
   :width: 78

Words
-----

.. code-block:: bash

   # New words (AI workflow) — full records required
   cat records.json | uv run soju-import words --topic common --stdin-json

   # Preview
   uv run soju-import words --topic family --stdin-json --dry-run < records.json

   # Merge examples only for existing registry words
   uv run soju-import words --topic common --file words.txt

   # From staging
   uv run soju-import words --from-staging data/staging/vocabulary-candidates.yaml --topic common

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
-----

.. code-block:: bash

   cat verbs.json | uv run soju-import verbs --stdin-json

Requires ``hangul``, ``romanization``, ``english``, ``forms`` (and optional ``examples``) per record. ``--file`` without JSON is not supported for new verbs.

**Limitation:** Re-importing an existing verb with the same hangul **and** English meaning is
not supported — the CLI returns an error. Same hangul with a different English gloss is allowed
as a homonym. Update existing verb senses by editing split files or extend ``soju-import`` when
merge is needed.

**AI commands:** ``import-words``, ``import-words-to``, ``import-verbs``, ``import-staging``
