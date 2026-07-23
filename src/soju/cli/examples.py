# SPDX-License-Identifier: BSD-3-Clause
"""``soju fill-examples`` command."""

from __future__ import annotations

import sys
from typing import Annotated, Literal, Optional

import typer

from soju.cli._common import flag, make_app
from soju.core.models import EXAMPLE_TENSES as TENSES
from soju.core.models import EXAMPLE_VARIANTS as VARIANTS
from soju.levels import get_language_level
from soju.llm import LlmError, OllamaClient
from soju.llm.ollama import DEFAULT_BASE_URL, DEFAULT_MODEL
from soju.registry.examples import load_examples_store, save_examples_store
from soju.registry.verbs import load_verb_forms, load_verb_forms_cache
from soju.registry.vocabulary import vocabulary_by_type
from soju.services.examples_fill import (
    fill_examples,
    filter_nouns_for_fill_mode,
    filter_verbs_for_fill_mode,
)

app = make_app()

FillMode = Literal["fill-empty", "refresh-all"]


@app.command()
def fill_examples_cmd(
    model: Annotated[str, typer.Option("--model")] = DEFAULT_MODEL,
    base_url: Annotated[str, typer.Option("--base-url")] = DEFAULT_BASE_URL,
    temperature: Annotated[float, typer.Option("--temperature")] = 0.4,
    verb_batch_size: Annotated[
        int,
        typer.Option("--verb-batch-size", help="Verbs per Ollama request"),
    ] = 4,
    noun_batch_size: Annotated[
        int,
        typer.Option("--noun-batch-size", help="Nouns per Ollama request"),
    ] = 6,
    verbs_only: Annotated[bool, flag("--verbs-only")] = False,
    nouns_only: Annotated[bool, flag("--nouns-only")] = False,
    clean_only: Annotated[
        bool,
        flag("--clean-only", help="Strip (formal)/(casual) notes from example English only"),
    ] = False,
    local: Annotated[
        bool,
        flag("--local", help="Generate examples with local Korean 1A/1B templates (no Ollama)"),
    ] = False,
    level: Annotated[
        Optional[str],
        typer.Option(
            "--level",
            help="Course level (default: SOJU_LANGUAGE_LEVEL or 1A; see data/content/levels.yaml)",
        ),
    ] = None,
    examples: Annotated[
        int,
        typer.Option(
            "--examples",
            metavar="N",
            help="Example sentences per verb tense/variant and per noun (default: 1)",
        ),
    ] = 1,
    max_attempts: Annotated[
        int,
        typer.Option(
            "--max-attempts",
            metavar="N",
            help="Ollama attempts per verb batch before giving up (default: 3)",
        ),
    ] = 3,
    mode: Annotated[
        FillMode,
        typer.Option(
            "--mode",
            help="fill-empty: only entries missing examples (default); refresh-all: regenerate every entry",
            case_sensitive=True,
        ),
    ] = "fill-empty",
    verbose: Annotated[bool, flag("--verbose")] = False,
    limit: Annotated[
        Optional[int],
        typer.Option("--limit", help="Process only the first N entries (testing)"),
    ] = None,
    dry_run: Annotated[bool, flag("--dry-run")] = False,
    strict: Annotated[
        bool,
        flag("--strict", help="Exit non-zero when any generation warnings were produced"),
    ] = False,
) -> None:
    """Generate noun and verb example sentences via Ollama."""
    if examples < 1:
        print("Error: --examples must be at least 1.", file=sys.stderr)
        raise typer.Exit(1)
    if max_attempts < 1:
        print("Error: --max-attempts must be at least 1.", file=sys.stderr)
        raise typer.Exit(1)

    verbs = not nouns_only and not clean_only
    nouns = not verbs_only and not clean_only
    if verbs_only:
        nouns = False

    if dry_run:
        course_level = get_language_level(level)
        verb_count = len(vocabulary_by_type("verb"))
        noun_count = len(vocabulary_by_type("noun"))
        store = load_examples_store()
        if mode == "fill-empty" and verbs:
            forms_cache = load_verb_forms_cache()
            verb_prepared = []
            for verb in vocabulary_by_type("verb"):
                forms = load_verb_forms(verb["id"], cache=forms_cache)
                if all(forms.get(t, {}).get(v) for t in TENSES for v in VARIANTS):
                    verb_prepared.append((verb, forms))
            verb_count = len(
                filter_verbs_for_fill_mode(
                    verb_prepared,
                    store,
                    fill_mode=mode,
                )
            )
        if mode == "fill-empty" and nouns:
            noun_count = len(filter_nouns_for_fill_mode(vocabulary_by_type("noun"), store, fill_mode=mode))
        verb_batches = (verb_count + verb_batch_size - 1) // verb_batch_size if verb_count else 0
        noun_batches = (noun_count + noun_batch_size - 1) // noun_batch_size if noun_count else 0
        print(f"Language level: {course_level.label} ({course_level.id})", file=sys.stderr)
        print(f"Fill mode: {mode}", file=sys.stderr)
        print(
            f"Would generate {examples} example(s) per variant for "
            f"{verb_count if verbs else 0} verbs "
            f"({verb_batches} batch(es) of up to {verb_batch_size}) and "
            f"{noun_count if nouns else 0} nouns "
            f"({noun_batches} batch(es) of up to {noun_batch_size}).",
            file=sys.stderr,
        )
        return

    llm = None
    if not clean_only and not local:
        llm = OllamaClient(model=model, base_url=base_url)
        if not llm.check_available():
            print(f"Error: Ollama is not reachable at {base_url}.", file=sys.stderr)
            raise typer.Exit(1)

    try:
        examples_store, warnings, updated = fill_examples(
            llm=llm,
            temperature=temperature,
            verb_batch_size=verb_batch_size,
            noun_batch_size=noun_batch_size,
            verbs=verbs,
            nouns=nouns,
            limit=limit,
            clean_only=clean_only,
            verbose=verbose,
            level_id=level,
            local=local,
            examples_per=examples,
            max_attempts=max_attempts,
            fill_mode=mode,
            root=None,
        )
    except (LlmError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise typer.Exit(1) from exc

    save_examples_store(examples_store, root=None)

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if clean_only:
        print(
            f"Cleaned example translations ({updated} field(s) updated).",
            file=sys.stderr,
        )
    else:
        print(f"Generated examples for {updated} vocabulary entries.", file=sys.stderr)
    if warnings:
        print(f"{len(warnings)} warning(s).", file=sys.stderr)
    if strict and warnings:
        raise typer.Exit(1)
