# SPDX-License-Identifier: BSD-3-Clause
"""English gloss/example quality checks for LLM and local example fill."""

from __future__ import annotations

import re

from soju.base.english.gloss import PAREN_ENGLISH

BROKEN_PAST_ENGLISH = re.compile(
    r"\b(?:readed|eated|goed|knowed|teached|meeted|giveed|swimed|arriveed|loveed|"
    r"saied|comeed|shoped|drink watered|buied|danceed|thinked|not knowed|movieed|"
    r"tennised|guitared|drumsed|homeworked|work outed|interneted|moneied|gameed|"
    r"newspapered|laundryed|restauranted|visaed|pooled|houseed|begined|mountained|"
    r"relocateed|schooled|faceed|phoneed|sended|tidy uped)\b",
    re.IGNORECASE,
)


def strip_example_english(text: str) -> str:
    """Remove parenthetical register notes and collapse whitespace."""
    cleaned = PAREN_ENGLISH.sub("", text)
    return re.sub(r"\s+", " ", cleaned).strip()


def is_bad_english(english: str, tense: str | None = None) -> bool:
    """Return True for broken past forms or parenthetical register notes."""
    if tense == "past" and BROKEN_PAST_ENGLISH.search(english):
        return True
    if PAREN_ENGLISH.search(english):
        return True
    return False


def is_bare_english(english: str) -> bool:
    """Reject time-only glosses like 'I talked last week.' with no place/object/context."""
    s = english.strip().rstrip(".")
    if re.match(
        r"^I (?:will )?\w+ (yesterday|today|tomorrow|now|last week|next week)$",
        s,
        re.IGNORECASE,
    ):
        return True
    return bool(re.match(r"^I (?:will )?\w+$", s, re.IGNORECASE))
