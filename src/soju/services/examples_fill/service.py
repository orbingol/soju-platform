# SPDX-License-Identifier: BSD-3-Clause
"""Orchestrate vocabulary example fill (LLM or local templates)."""

from __future__ import annotations

from typing import Any

from soju.core.models import EXAMPLE_TENSES as TENSES
from soju.core.models import EXAMPLE_VARIANTS as VARIANTS
from soju.languages import get_language
from soju.languages.contracts import PromptProvider
from soju.levels import get_language_level
from soju.llm.base import LlmClient
from soju.prompts.context import build_vocabulary_context
from soju.registry.examples import load_examples_store, save_examples_store
from soju.registry.verbs import load_verb_forms, load_verb_forms_cache
from soju.registry.vocabulary import vocabulary_by_type
from soju.services.examples_fill.generate import generate_noun_batch, generate_verb_batch
from soju.services.examples_fill.local import fill_examples_local
from soju.services.examples_fill.types import ProgressFn, noop_progress
from soju.services.examples_fill.validate import (
    clean_examples_store,
    filter_nouns_for_fill_mode,
    filter_verbs_for_fill_mode,
)


def dry_run_examples_preview(
    *,
    verbs: bool,
    nouns: bool,
    fill_mode: str,
    verb_batch_size: int,
    noun_batch_size: int,
    examples_per: int,
    level_id: str | None,
    root=None,
) -> str:
    """Return a multi-line human summary of what fill would do (no writes)."""
    course_level = get_language_level(level_id, root)
    verb_count = len(vocabulary_by_type("verb", root))
    noun_count = len(vocabulary_by_type("noun", root))
    store = load_examples_store(root)
    if fill_mode == "fill-empty" and verbs:
        forms_cache = load_verb_forms_cache(root)
        verb_prepared = []
        for verb in vocabulary_by_type("verb", root):
            forms = load_verb_forms(verb["id"], root, cache=forms_cache)
            if all(forms.get(t, {}).get(v) for t in TENSES for v in VARIANTS):
                verb_prepared.append((verb, forms))
        verb_count = len(filter_verbs_for_fill_mode(verb_prepared, store, fill_mode=fill_mode))
    if fill_mode == "fill-empty" and nouns:
        noun_count = len(filter_nouns_for_fill_mode(vocabulary_by_type("noun", root), store, fill_mode=fill_mode))
    verb_batches = (verb_count + verb_batch_size - 1) // verb_batch_size if verb_count else 0
    noun_batches = (noun_count + noun_batch_size - 1) // noun_batch_size if noun_count else 0
    lines = [
        f"Language level: {course_level.label} ({course_level.id})",
        f"Fill mode: {fill_mode}",
        (
            f"Would generate {examples_per} example(s) per variant for "
            f"{verb_count if verbs else 0} verbs "
            f"({verb_batches} batch(es) of up to {verb_batch_size}) and "
            f"{noun_count if nouns else 0} nouns "
            f"({noun_batches} batch(es) of up to {noun_batch_size})."
        ),
    ]
    return "\n".join(lines)


def fill_examples(
    *,
    llm: LlmClient | None,
    prompts: PromptProvider | None = None,
    temperature: float,
    verb_batch_size: int,
    noun_batch_size: int,
    verbs: bool,
    nouns: bool,
    limit: int | None,
    clean_only: bool,
    verbose: bool,
    level_id: str | None,
    local: bool = False,
    examples_per: int = 1,
    max_attempts: int = 3,
    fill_mode: str = "fill-empty",
    root=None,
    progress: ProgressFn | None = None,
) -> tuple[dict[str, Any], list[str], int]:
    log = progress or noop_progress
    examples_store = load_examples_store(root)
    warnings: list[str] = []
    updated = 0

    cleaned = clean_examples_store(examples_store)
    if cleaned:
        log(f"Stripped register notes from {cleaned} example translation(s).")

    if clean_only:
        return examples_store, warnings, cleaned

    if local:
        level = get_language_level(level_id, root)
        log(f"Language level: {level.label} ({level.id}) [local templates]")
        log(f"Fill mode: {fill_mode}")
        examples_store, updated = fill_examples_local(
            level_id=level.id,
            verbs=verbs,
            nouns=nouns,
            examples_per=examples_per,
            fill_mode=fill_mode,
            root=root,
        )
        if limit is not None:
            warnings.append(f"--limit is ignored with --local (generated {updated} entries).")
        return examples_store, warnings, updated

    if llm is None:
        raise ValueError("llm is required unless local=True or clean_only=True")
    prompt_provider = prompts if prompts is not None else get_language()

    level = get_language_level(level_id, root)
    vocabulary_context = build_vocabulary_context(root, compact=True, level=level)
    log(f"Language level: {level.label} ({level.id})")
    log(f"Examples per variant: {examples_per}")
    log(f"Fill mode: {fill_mode}")
    if verb_batch_size >= 10 and verbs:
        log(
            f"Note: verb batch size {verb_batch_size} can take several minutes per batch "
            "before the next status line appears."
        )

    if verbs:
        verb_entries = vocabulary_by_type("verb", root)
        if limit is not None:
            verb_entries = verb_entries[:limit]

        forms_cache = load_verb_forms_cache(root)
        prepared: list[tuple[dict[str, Any], dict[str, dict[str, str]]]] = []
        for verb in verb_entries:
            forms = load_verb_forms(verb["id"], root, cache=forms_cache)
            if not all(forms.get(tense, {}).get(variant) for tense in TENSES for variant in VARIANTS):
                warnings.append(f"Skipped {verb['hangul']}: missing conjugated forms.")
                continue
            prepared.append((verb, forms))

        prepared = filter_verbs_for_fill_mode(prepared, examples_store, fill_mode=fill_mode)
        if fill_mode == "fill-empty" and not prepared and verb_entries:
            log("All verb examples are already complete.")

        batch_size = max(1, verb_batch_size)
        for start in range(0, len(prepared), batch_size):
            batch = prepared[start : start + batch_size]
            end = start + len(batch)
            labels = ", ".join(verb["hangul"] for verb, _ in batch)
            log(f"verbs {start + 1}-{end}/{len(prepared)}: {labels}")

            generated = generate_verb_batch(
                batch,
                level=level,
                vocabulary_context=vocabulary_context,
                llm=llm,
                prompts=prompt_provider,
                temperature=temperature,
                verbose=verbose,
                examples_per=examples_per,
                max_attempts=max_attempts,
                progress=log,
            )

            for verb, forms in batch:
                examples = generated.get(verb["id"])
                if not examples:
                    warnings.append(f"Failed to generate verb examples: {verb['hangul']}")
                    continue
                examples_store[verb["id"]] = examples
                updated += 1

            save_examples_store(examples_store, root)

    if nouns:
        noun_entries = vocabulary_by_type("noun", root)
        if limit is not None and not verbs:
            noun_entries = noun_entries[:limit]
        elif limit is not None:
            noun_entries = noun_entries[: max(0, limit - updated)]

        noun_entries = filter_nouns_for_fill_mode(noun_entries, examples_store, fill_mode=fill_mode)
        if fill_mode == "fill-empty" and not noun_entries and vocabulary_by_type("noun", root):
            log("All noun examples are already complete.")

        batch_size = max(1, noun_batch_size)
        for start in range(0, len(noun_entries), batch_size):
            batch = noun_entries[start : start + batch_size]
            log(f"nouns {start + 1}-{start + len(batch)}/{len(noun_entries)}")
            generated = generate_noun_batch(
                batch,
                level=level,
                vocabulary_context=vocabulary_context,
                llm=llm,
                prompts=prompt_provider,
                temperature=temperature,
                verbose=verbose,
                examples_per=examples_per,
                progress=log,
            )
            for noun in batch:
                examples = generated.get(noun["id"])
                if not examples:
                    warnings.append(f"Failed to generate noun examples: {noun['hangul']}")
                    continue
                examples_store[noun["id"]] = {"default": examples}
                updated += 1

            save_examples_store(examples_store, root)

    return examples_store, warnings, updated
