# SPDX-License-Identifier: BSD-3-Clause
"""Language plugin contracts for the Soju platform.

A *language plugin* bundles every piece of language-specific behaviour behind
small, focused protocols so the generic pipelines in :mod:`soju.services` never
import a concrete language module directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from soju.core.models import Example, TenseForms

if TYPE_CHECKING:
    from soju.levels import LanguageLevel


@runtime_checkable
class ScriptNormalizer(Protocol):
    """Normalize and detect the language's writing system."""

    def normalize(self, text: str) -> str:
        """Return ``text`` normalized for this language's script.

        Args:
            text: Raw term in the target language.

        Returns:
            The canonical, comparison-safe form (e.g. NFC + trimmed).
        """

    def is_target_script(self, text: str) -> bool:
        """Return ``True`` if ``text`` contains the target script (e.g. hangul)."""

    def romanize(self, text: str) -> str:
        """Return romanization for ``text`` (e.g. Revised Romanization for hangul)."""


@runtime_checkable
class Conjugator(Protocol):
    """Produce verb conjugation tables from a dictionary form."""

    def conjugate(self, dictionary_form: str) -> TenseForms:
        """Return the tense/variant table for ``dictionary_form``.

        Args:
            dictionary_form: The verb's dictionary form in the target script.

        Returns:
            Mapping of ``tense -> variant -> surface form`` (see
            :data:`soju.core.models.TenseForms`).
        """


@runtime_checkable
class DeterministicExampleGenerator(Protocol):
    """Generate offline (non-LLM) example sentences."""

    def examples_for_noun(
        self,
        hangul: str,
        english: str,
        *,
        level_id: str,
        examples_per: int,
    ) -> list[Example]: ...

    def examples_for_verb(
        self,
        hangul: str,
        english: str,
        forms: TenseForms,
        *,
        level_id: str,
    ) -> dict[str, dict[str, list[Example]]]: ...


@runtime_checkable
class ExampleValidator(Protocol):
    """Validate LLM-generated examples against language rules."""

    def form_in_sentence(self, form: str, sentence: str) -> bool:
        """Return ``True`` if the conjugated ``form`` actually appears in ``sentence``."""

    def embedded_form_hint(self, forms: TenseForms) -> str | None:
        """Optional hint when conjugated forms embed a fixed destination/object prefix."""


@runtime_checkable
class PromptProvider(Protocol):
    """Supply language-specific LLM system prompts."""

    def translation_system_prompt(self, level: LanguageLevel, vocab_context: str) -> str: ...

    def verb_examples_system_prompt(
        self,
        level: LanguageLevel,
        vocab_context: str,
        *,
        examples_per: int,
    ) -> str: ...

    def noun_examples_system_prompt(
        self,
        level: LanguageLevel,
        vocab_context: str,
        *,
        examples_per: int,
    ) -> str: ...


@runtime_checkable
class LanguagePlugin(
    ScriptNormalizer,
    Conjugator,
    DeterministicExampleGenerator,
    ExampleValidator,
    PromptProvider,
    Protocol,
):
    """The full language contract consumed by :mod:`soju.services`.

    Attributes:
        code: Short language code (e.g. ``"ko"``).
        name: Human-readable name (e.g. ``"Korean"``).
    """

    code: str
    name: str
