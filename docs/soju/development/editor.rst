Editor support
==============

Install the `YAML extension <https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml>`_
(``redhat.vscode-yaml``) for inline schema validation, hover docs, and autocomplete
while hand-authoring YAML. ``.vscode/settings.json`` maps each JSON Schema under
``data/schemas/`` to the files it validates:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - File(s)
     - Schema
   * - ``data/content/registry/vocabulary.yaml``
     - ``registry_vocabulary``
   * - ``data/content/registry/types.yaml``
     - ``registry_types``
   * - ``data/content/registry/examples.yaml``
     - ``examples_vocabulary``
   * - ``data/content/topics/manifest.yaml``
     - ``topics_manifest``
   * - ``data/content/topics/table.yaml``
     - ``topics_table``
   * - ``data/content/topics/*/topic.yaml``
     - ``topics_topic``
   * - ``data/content/verbs/manifest.yaml``
     - ``verb_manifest``
   * - ``data/content/verbs/table.yaml``
     - ``verb_table``
   * - ``data/content/verbs/forms/*.yaml``
     - ``verbs_forms``
   * - ``data/content/verbs/constructions/*.yaml``
     - ``verbs_construction``
   * - ``data/content/grammar/manifest.yaml``
     - ``grammar_manifest``
   * - ``data/content/grammar/patterns/*.yaml``
     - ``grammar_pattern``
   * - ``data/content/words/table.yaml``
     - ``words_table``
   * - ``data/staging/vocabulary-candidates.yaml``
     - ``staging_vocabulary``
   * - ``data/staging/exercises/*.yaml``
     - ``staging_exercises``
   * - ``data/staging/stories/*.yaml``
     - ``staging_stories``

These are the same schemas ``soju validate-schemas`` runs at commit/CI time (see
:doc:`validate`) — the editor just surfaces the same errors earlier, inline.

``yaml.format.enable`` is set to ``false`` in the workspace so the extension does not
reformat hand-authored YAML (grammar patterns, manifests) on save; canonical vocabulary
files are written exclusively by ``soju import`` anyway (see :doc:`import`), so they are
never hand-formatted.
