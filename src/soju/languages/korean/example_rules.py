# SPDX-License-Identifier: BSD-3-Clause
"""Korean example-sentence validation rules (form presence, hada splits)."""

from __future__ import annotations

import re

from soju.core.models import EXAMPLE_TENSES as TENSES
from soju.core.models import EXAMPLE_VARIANTS as VARIANTS

_HADA_CONJUGATIONS = (
    "해요",
    "합니다",
    "했어요",
    "했습니다",
    "할 거예요",
    "하겠습니다",
)

_SUBJECT_PREFIXES = (
    "저는",
    "저희는",
    "우리는",
    "제가",
    "친구가",
    "선생님이",
    "학생이",
    "동생이",
    "엄마가",
    "아버지가",
    "할머니가",
    "할아버지가",
    "그가",
    "그녀가",
)

# Same verb, different natural wording (canonical stem -> alternates).
_VERB_STEM_SYNONYMS: dict[str, tuple[str, ...]] = {
    "씻": ("샤워", "목욕"),
}


def _compact_hangul(text: str) -> str:
    return text.replace(" ", "")


def _strip_leading_subjects(hangul: str) -> str:
    text = hangul.strip()
    while True:
        stripped = False
        for prefix in _SUBJECT_PREFIXES:
            if text.startswith(prefix):
                text = text[len(prefix) :].lstrip()
                stripped = True
                break
        if not stripped:
            break
    return text


def _hada_alternate_forms(form: str) -> set[str]:
    """Accept natural 하다 splits and object reordering when conjugation matches."""
    alts = {form}
    obj_match = re.match(
        rf"^(.+)(를|을) ({'|'.join(_HADA_CONJUGATIONS)})$",
        form,
    )
    if obj_match:
        obj, _, ending = obj_match.groups()
        stem = obj
        alts.add(f"{stem}{ending}")
        alts.add(f"{obj} {ending}")
        return alts
    compact_match = re.match(
        rf"^(.+?)({'|'.join(_HADA_CONJUGATIONS)})$",
        form,
    )
    if compact_match:
        stem, ending = compact_match.groups()
        if stem.endswith(("를", "을")):
            return alts
        for particle in ("를", "을"):
            alts.add(f"{stem}{particle} {ending}")
    return alts


def _synonym_alternate_forms(form: str) -> set[str]:
    alts: set[str] = set()
    for canonical, synonyms in _VERB_STEM_SYNONYMS.items():
        if canonical not in form:
            continue
        for synonym in synonyms:
            alts.add(form.replace(canonical, synonym, 1))
            obj_match = re.match(
                rf"^{canonical}(어요|습니다|었어요|었습니다|을 거예요|겠습니다)$",
                form,
            )
            if obj_match and synonym == "샤워":
                ending = obj_match.group(1)
                if ending.startswith("었"):
                    alts.add(f"샤워했{ending[1:]}")
                    alts.add(f"샤워를 했{ending[1:]}")
                elif ending == "어요":
                    alts.add("샤워해요")
                    alts.add("샤워를 해요")
                elif ending == "습니다":
                    alts.add("샤워합니다")
                    alts.add("샤워를 합니다")
                elif ending.startswith("을 "):
                    alts.add(f"샤워{ending}")
                    alts.add(f"샤워를 {ending}")
                elif ending == "겠습니다":
                    alts.add("샤워하겠습니다")
                    alts.add("샤워를 하겠습니다")
    return alts


def _alternate_form_compacts(form: str) -> set[str]:
    compacts = {_compact_hangul(form)}
    for alt in _hada_alternate_forms(form) | _synonym_alternate_forms(form):
        compacts.add(_compact_hangul(alt))
    return compacts


def form_in_sentence(form: str, hangul: str) -> bool:
    form_compacts = _alternate_form_compacts(form)
    for candidate in (hangul, _strip_leading_subjects(hangul)):
        hangul_compact = _compact_hangul(candidate)
        if any(alt in hangul_compact for alt in form_compacts):
            return True
    return False


def embedded_form_hint(forms: dict[str, dict[str, str]]) -> str | None:
    """Hint when conjugated forms embed a destination/object prefix the model must keep."""
    all_forms = [forms[tense][variant] for tense in TENSES for variant in VARIANTS if forms.get(tense, {}).get(variant)]
    if not all_forms or " " not in all_forms[0]:
        return None
    prefix = all_forms[0].rsplit(" ", 1)[0]
    if not all(form.startswith(f"{prefix} ") for form in all_forms):
        return None
    sample = all_forms[0]
    return (
        f"Every hangul example MUST contain the exact form substring for that cell "
        f"(e.g. {sample!r}). The prefix {prefix!r} is fixed in ALL variants including "
        f"formal_polite — add context around it, but do NOT replace {prefix!r} with 회사에, "
        f"집에, 공원에, or any other place."
    )
