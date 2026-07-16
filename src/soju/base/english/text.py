# SPDX-License-Identifier: BSD-3-Clause
"""English base-language text normalization (gloss / identity)."""

from __future__ import annotations

import re

# Proper names kept capitalized in vocabulary glosses (not example sentences).
# Longer phrases first so matching prefers e.g. "south korea" over "korea".
PROPER_NAME_GLOSS_WORDS: dict[str, str] = {
    # Multi-word places
    "new york": "New York",
    "south korea": "South Korea",
    "north korea": "North Korea",
    "united states": "United States",
    "united kingdom": "United Kingdom",
    "hong kong": "Hong Kong",
    "los angeles": "Los Angeles",
    "san francisco": "San Francisco",
    "harry potter": "Harry Potter",
    # Languages and demonyms
    "korean": "Korean",
    "english": "English",
    "japanese": "Japanese",
    "chinese": "Chinese",
    "french": "French",
    "german": "German",
    "spanish": "Spanish",
    "italian": "Italian",
    "russian": "Russian",
    "vietnamese": "Vietnamese",
    "thai": "Thai",
    "hindi": "Hindi",
    "arabic": "Arabic",
    "portuguese": "Portuguese",
    "american": "American",
    "british": "British",
    # Countries and regions
    "korea": "Korea",
    "japan": "Japan",
    "china": "China",
    "america": "America",
    "france": "France",
    "germany": "Germany",
    "spain": "Spain",
    "italy": "Italy",
    "russia": "Russia",
    "vietnam": "Vietnam",
    "thailand": "Thailand",
    "india": "India",
    "mexico": "Mexico",
    "canada": "Canada",
    "australia": "Australia",
    "britain": "Britain",
    "europe": "Europe",
    "asia": "Asia",
    "africa": "Africa",
    # Korean cities
    "seoul": "Seoul",
    "busan": "Busan",
    "incheon": "Incheon",
    "daegu": "Daegu",
    "gwangju": "Gwangju",
    "daejeon": "Daejeon",
    "ulsan": "Ulsan",
    "jeju": "Jeju",
    "pyongyang": "Pyongyang",
    # Other cities
    "tokyo": "Tokyo",
    "osaka": "Osaka",
    "beijing": "Beijing",
    "shanghai": "Shanghai",
    "paris": "Paris",
    "london": "London",
    # Short forms
    "uk": "UK",
    "usa": "USA",
}


def normalize_english(text: str) -> str:
    """Collapse whitespace in an English string.

    Args:
        text: Raw English text.

    Returns:
        Trimmed text with internal whitespace collapsed to single spaces.
    """
    return re.sub(r"\s+", " ", text.strip())


def normalize_english_gloss(text: str) -> str:
    """Normalize a vocabulary meaning: lowercase gloss, restore proper-name caps.

    Args:
        text: Raw English gloss / meaning.

    Returns:
        Lowercased gloss with known proper names re-capitalized.
    """
    gloss = normalize_english(text).lower()
    if not gloss:
        return gloss
    for lower, proper in sorted(PROPER_NAME_GLOSS_WORDS.items(), key=lambda item: -len(item[0])):
        gloss = re.sub(rf"\b{re.escape(lower)}\b", proper, gloss, flags=re.IGNORECASE)
    return gloss
