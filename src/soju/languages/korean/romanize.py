# SPDX-License-Identifier: BSD-3-Clause
"""Hangul → Revised Romanization (dictionary-style, lowercase, hyphenated)."""

from __future__ import annotations

import unicodedata

# Unicode hangul syllable block
_S_BASE = 0xAC00
_L_COUNT = 19
_V_COUNT = 21
_T_COUNT = 28
_N_COUNT = _V_COUNT * _T_COUNT  # 588
_S_COUNT = _L_COUNT * _N_COUNT  # 11172

# Choseong / jungseong / jongseong letter romanizations (transliteration-style finals
# keep compound batchim clusters, matching Soju's dictionary forms like ``ilk-da``, ``manh-da``).
_CHO = (
    "g",
    "kk",
    "n",
    "d",
    "tt",
    "r",
    "m",
    "b",
    "pp",
    "s",
    "ss",
    "",
    "j",
    "jj",
    "ch",
    "k",
    "t",
    "p",
    "h",
)
_JUNG = (
    "a",
    "ae",
    "ya",
    "yae",
    "eo",
    "e",
    "yeo",
    "ye",
    "o",
    "wa",
    "wae",
    "oe",
    "yo",
    "u",
    "wo",
    "we",
    "wi",
    "yu",
    "eu",
    "ui",
    "i",
)
_JONG = (
    "",
    "k",
    "kk",
    "ks",
    "n",
    "nj",
    "nh",
    "t",
    "l",
    "lk",
    "lm",
    "lb",
    "ls",
    "lt",
    "lp",
    "lh",
    "m",
    "p",
    "ps",
    "t",
    "t",
    "ng",
    "t",
    "t",
    "k",
    "t",
    "p",
    "h",
)


def _romanize_syllable(code: int) -> str | None:
    """Return RR for one hangul syllable code point, or ``None`` if not a syllable."""
    if not (_S_BASE <= code < _S_BASE + _S_COUNT):
        return None
    s_index = code - _S_BASE
    l_index = s_index // _N_COUNT
    v_index = (s_index % _N_COUNT) // _T_COUNT
    t_index = s_index % _T_COUNT
    return f"{_CHO[l_index]}{_JUNG[v_index]}{_JONG[t_index]}"


def romanize_hangul(text: str) -> str:
    """Romanize hangul with Revised Romanization, lowercase and hyphenated by syllable.

    Spaces (and other non-hangul runs) are preserved as word separators. Hangul
    syllables within a word are joined with ``-`` (e.g. ``학교`` → ``hak-gyo``,
    ``물을 마시다`` → ``mul-eul ma-si-da``).

    Args:
        text: Hangul (or mixed) string.

    Returns:
        Lowercase romanization. Empty/whitespace-only input yields ``""``.
    """
    normalized = unicodedata.normalize("NFC", text.strip())
    if not normalized:
        return ""

    parts: list[str] = []
    syllable_buf: list[str] = []

    def flush_syllables() -> None:
        if syllable_buf:
            parts.append("-".join(syllable_buf))
            syllable_buf.clear()

    for char in normalized:
        syllable = _romanize_syllable(ord(char))
        if syllable is not None:
            syllable_buf.append(syllable)
            continue
        flush_syllables()
        if char.isspace():
            if parts and not parts[-1].endswith(" "):
                parts.append(" ")
            continue
        # Keep ASCII letters/digits as-is (lowercased); drop other punctuation.
        if char.isascii() and char.isalnum():
            parts.append(char.lower())

    flush_syllables()
    return "".join(parts).strip()
