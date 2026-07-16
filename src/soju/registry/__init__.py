# SPDX-License-Identifier: BSD-3-Clause
"""Language-agnostic data-access layer for vocabulary, examples, topics, and verbs."""

from soju.registry.examples import (
    load_examples_store,
    merge_default_examples,
    merge_verb_examples,
    noun_entry_needs_fill,
    save_examples_store,
    verb_entry_needs_fill,
    verb_examples_complete,
)
from soju.registry.targets import glob_validate_targets
from soju.registry.topics import (
    find_local_entry,
    find_section,
    iter_topic_entries,
    load_topic,
    load_topics_manifest,
    save_topic,
    topic_has_ref,
    topic_path,
)
from soju.registry.types import load_types
from soju.registry.verbs import (
    iter_verb_columns,
    load_all_verb_forms,
    load_verb_forms,
    load_verb_forms_cache,
    load_verb_forms_file,
    load_verb_manifest,
    save_verb_forms_file,
    verb_forms_path,
    verb_table_path,
)
from soju.registry.vocabulary import (
    build_sense_index,
    entries_for_hangul,
    load_vocabulary,
    save_vocabulary,
    vocabulary_by_id,
    vocabulary_by_sense,
    vocabulary_by_type,
    vocabulary_entries_for_hangul,
)

__all__ = [
    "build_sense_index",
    "entries_for_hangul",
    "find_local_entry",
    "find_section",
    "glob_validate_targets",
    "iter_topic_entries",
    "iter_verb_columns",
    "load_all_verb_forms",
    "load_examples_store",
    "load_topic",
    "load_topics_manifest",
    "load_types",
    "load_verb_forms",
    "load_verb_forms_cache",
    "load_verb_forms_file",
    "load_verb_manifest",
    "load_vocabulary",
    "merge_default_examples",
    "merge_verb_examples",
    "noun_entry_needs_fill",
    "save_examples_store",
    "save_topic",
    "save_verb_forms_file",
    "save_vocabulary",
    "topic_has_ref",
    "topic_path",
    "verb_entry_needs_fill",
    "verb_examples_complete",
    "verb_forms_path",
    "verb_table_path",
    "vocabulary_by_id",
    "vocabulary_by_sense",
    "vocabulary_by_type",
    "vocabulary_entries_for_hangul",
]
