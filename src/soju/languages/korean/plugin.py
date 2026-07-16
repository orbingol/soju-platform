# SPDX-License-Identifier: BSD-3-Clause
"""Korean :class:`~soju.languages.contracts.LanguagePlugin` implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from soju.core.models import Example, TenseForms
from soju.languages.korean import conjugation, example_rules, local_examples, prompts, text
from soju.languages.plugins import register
from soju.levels import get_language_level

if TYPE_CHECKING:
    from soju.levels import LanguageLevel


class KoreanLanguage:
    """Korean target language: script, conjugation, examples, rules, and prompts."""

    code = "ko"
    name = "Korean"

    def normalize(self, value: str) -> str:
        """Normalize hangul for identity/dedup."""
        return text.normalize_hangul(value)

    def is_target_script(self, value: str) -> bool:
        """Return True if ``value`` contains hangul."""
        return text.has_hangul(value)

    def conjugate(self, dictionary_form: str) -> TenseForms:
        """Return polite tense/variant forms for ``dictionary_form``."""
        return conjugation.conjugate_verb(dictionary_form)

    def conjugation_examples(
        self,
        hangul: str,
        english: str,
        forms: TenseForms,
    ) -> dict[str, dict[str, list[dict[str, str]]]]:
        """Short example sentences paired with :meth:`conjugate` (fill-verbs)."""
        return conjugation.examples_for_verb(hangul, english, forms)

    def examples_for_noun(
        self,
        hangul: str,
        english: str,
        *,
        level_id: str,
        examples_per: int,
    ) -> list[Example]:
        """Generate deterministic noun example sentences."""
        level = get_language_level(level_id)
        return local_examples.examples_for_noun(
            {"hangul": hangul, "english": english},
            level=level,
            examples_per=examples_per,
        )

    def examples_for_verb(
        self,
        hangul: str,
        english: str,
        forms: TenseForms,
        *,
        level_id: str,
    ) -> dict[str, dict[str, list[Example]]]:
        """Generate deterministic verb example sentences for each tense/variant."""
        level = get_language_level(level_id)
        return local_examples.examples_for_verb(
            {"hangul": hangul, "english": english},
            forms,
            level=level,
        )

    def form_in_sentence(self, form: str, sentence: str) -> bool:
        """Return True if conjugated ``form`` appears in ``sentence`` (with hada/synonym alts)."""
        return example_rules.form_in_sentence(form, sentence)

    def embedded_form_hint(self, forms: TenseForms) -> str | None:
        """Hint when conjugated forms embed a destination/object prefix the model must keep."""
        return example_rules.embedded_form_hint(forms)

    def translation_system_prompt(self, level: LanguageLevel, vocab_context: str) -> str:
        """Return the lexicographer system prompt for vocabulary translation."""
        return prompts.translation_system_prompt(level, vocab_context)

    def verb_examples_system_prompt(
        self,
        level: LanguageLevel,
        vocab_context: str,
        *,
        examples_per: int,
    ) -> str:
        """Return the system prompt for verb example generation."""
        return prompts.verb_examples_system_prompt(level, vocab_context, examples_per=examples_per)

    def noun_examples_system_prompt(
        self,
        level: LanguageLevel,
        vocab_context: str,
        *,
        examples_per: int,
    ) -> str:
        """Return the system prompt for noun example generation."""
        return prompts.noun_examples_system_prompt(level, vocab_context, examples_per=examples_per)


def get_korean_language() -> KoreanLanguage:
    """Return the singleton Korean language plugin instance."""
    return _KOREAN


_KOREAN = KoreanLanguage()
register(_KOREAN)
