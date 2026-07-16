# SPDX-License-Identifier: BSD-3-Clause
"""Korean script normalization and detection helpers."""

from __future__ import annotations

import re
import unicodedata


def normalize_hangul(text: str) -> str:
    """Normalize a hangul string for identity/dedup (NFC + collapsed whitespace).

    Args:
        text: Raw hangul (or mixed) text.

    Returns:
        NFC-normalized text with collapsed whitespace.
    """
    collapsed = re.sub(r"\s+", " ", text.strip())
    return unicodedata.normalize("NFC", collapsed)


def has_hangul(text: str) -> bool:
    """Return True if ``text`` contains hangul syllables or jamo.

    Args:
        text: Arbitrary string.

    Returns:
        Whether hangul characters are present.
    """
    return bool(re.search(r"[\uAC00-\uD7A3\u1100-\u11FF\u3130-\u318F]", text))
