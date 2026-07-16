# SPDX-License-Identifier: BSD-3-Clause
"""English gloss converter: dictionary gloss → tense-shaped clause.

Free functions keep historical names (``english_for_tense``, ``_english_clause``)
so callers and snapshot tests stay stable. :class:`~soju.base.english.plugin.EnglishBase`
delegates ``clause_for_tense`` to :func:`english_for_tense`.
"""

from __future__ import annotations

import re

PAREN_ENGLISH = re.compile(r"\s*\([^)]*\)")

# Gloss stem (after stripping "to ") -> (present, past, future) English verb phrases for "I …"
_ENGLISH_FORMS: dict[str, tuple[str, str, str]] = {
    "come": ("come", "came", "come"),
    "go": ("go", "went", "go"),
    "shop": ("shop", "shopped", "shop"),
    "talk": ("talk", "talked", "talk"),
    "read": ("read", "read", "read"),
    "eat": ("eat", "ate", "eat"),
    "learn": ("learn", "learned", "learn"),
    "teach": ("teach", "taught", "teach"),
    "meet": ("meet", "met", "meet"),
    "drink": ("drink", "drank", "drink"),
    "drink water": ("drink water", "drank water", "drink water"),
    "read a book": ("read a book", "read a book", "read a book"),
    "watch / see": ("watch a movie", "watched a movie", "watch a movie"),
    "watch / to see": ("watch a movie", "watched a movie", "watch a movie"),
    "receive": ("receive a package", "received a package", "receive a package"),
    "wait": ("wait", "waited", "wait"),
    "receive a visa": ("receive a visa", "received a visa", "receive a visa"),
    "watch a movie": ("watch a movie", "watched a movie", "watch a movie"),
    "dance": ("dance", "danced", "dance"),
    "listen": ("listen", "listened", "listen"),
    "listen to music": ("listen to music", "listened to music", "listen to music"),
    "play tennis": ("play tennis", "played tennis", "play tennis"),
    "play drums": ("play drums", "played drums", "play drums"),
    "play guitar": ("play guitar", "played guitar", "play guitar"),
    "buy": ("buy clothes", "bought clothes", "buy clothes"),
    "borrow": ("borrow a book", "borrowed a book", "borrow a book"),
    "give": ("give a gift", "gave a gift", "give a gift"),
    "hit / strike / beat": ("hit the ball", "hit the ball", "hit the ball"),
    "go to swimming pool": (
        "go to the swimming pool",
        "went to the swimming pool",
        "go to the swimming pool",
    ),
    "go home": ("go home", "went home", "go home"),
    "go to the friend's house": (
        "go to a friend's house",
        "went to a friend's house",
        "go to a friend's house",
    ),
    "have breakfast": ("have breakfast", "had breakfast", "have breakfast"),
    "eat breakfast": ("eat breakfast", "ate breakfast", "eat breakfast"),
    "have lunch": ("have lunch", "had lunch", "have lunch"),
    "have dinner": ("have dinner", "had dinner", "have dinner"),
    "eat at a restaurant": (
        "eat at a restaurant",
        "ate at a restaurant",
        "eat at a restaurant",
    ),
    "study korean": ("study Korean", "studied Korean", "study Korean"),
    "drink coffee": ("drink coffee", "drank coffee", "drink coffee"),
    "do homework": ("do homework", "did homework", "do homework"),
    "work out": ("work out", "worked out", "work out"),
    "study": ("study", "studied", "study"),
    "think": ("think", "thought", "think"),
    "work": ("work", "worked", "work"),
    "use the computer": ("use the computer", "used the computer", "use the computer"),
    "surf the internet": (
        "surf the internet",
        "surfed the internet",
        "surf the internet",
    ),
    "like something": ("like kimchi", "liked kimchi", "like kimchi"),
    "dislike / hate": ("dislike coffee", "disliked coffee", "dislike coffee"),
    "wash one's face": ("wash my face", "washed my face", "wash my face"),
    "talk on the phone": (
        "talk on the phone",
        "talked on the phone",
        "talk on the phone",
    ),
    "swim": ("swim", "swam", "swim"),
    "travel": ("travel", "traveled", "travel"),
    "hike / climb a mountain": ("hike", "hiked", "hike"),
    "start / begin": ("start", "started", "start"),
    "finish / end": ("finish", "finished", "finish"),
    "not know": ("do not know", "did not know", "not know"),
    "know": ("know", "knew", "know"),
    "play basketball": ("play basketball", "played basketball", "play basketball"),
    "move / relocate": ("move house", "moved house", "move house"),
    "get married / marry": ("get married", "got married", "get married"),
    "graduate from school": (
        "graduate from school",
        "graduated from school",
        "graduate from school",
    ),
    "play a computer game": (
        "play a computer game",
        "played a computer game",
        "play a computer game",
    ),
    "read newspaper": (
        "read the newspaper",
        "read the newspaper",
        "read the newspaper",
    ),
    "cook": ("cook", "cooked", "cook"),
    "clean": ("clean", "cleaned", "clean"),
    "organize / tidy up": ("tidy up", "tidied up", "tidy up"),
    "wash": ("wash my hands", "washed my hands", "wash my hands"),
    "do laundry": ("do laundry", "did laundry", "do laundry"),
    "walk / stroll": ("take a walk", "took a walk", "take a walk"),
    "send": ("send a letter", "sent a letter", "send a letter"),
    "arrive": ("arrive", "arrived", "arrive"),
    "withdraw money": ("withdraw money", "withdrew money", "withdraw money"),
    "deposit money": ("deposit money", "deposited money", "deposit money"),
    "send money": ("send money", "sent money", "send money"),
    "speak / tell / say": ("speak Korean", "spoke Korean", "speak Korean"),
    "bring / keep and come": ("bring a book", "brought a book", "bring a book"),
    "love": ("love my family", "loved my family", "love my family"),
}


def _gloss_key(english: str) -> str:
    """Normalize a dictionary gloss into a lookup key."""
    cleaned = PAREN_ENGLISH.sub("", english).strip()
    cleaned = re.sub(r"^to\s+", "", cleaned, flags=re.IGNORECASE).strip().rstrip(".")
    return cleaned.lower()


_ENGLISH_BY_HANGUL: dict[str, tuple[str, str, str]] = {
    "씻다": ("wash my hands", "washed my hands", "wash my hands"),
    "세탁하다": ("wash clothes", "washed clothes", "wash clothes"),
    "보다": ("watch a movie", "watched a movie", "watch a movie"),
    "치다": ("hit the ball", "hit the ball", "hit the ball"),
    "에 오다": ("come to school", "came to school", "come to school"),
    "에 가다": ("go to school", "went to school", "go to school"),
}


def english_for_tense(english: str, tense: str, hangul: str | None = None) -> str:
    """Convert a dictionary gloss into an ``I …`` clause for ``tense``.

    Args:
        english: Dictionary English gloss (may include ``to `` / parentheticals).
        tense: ``present``, ``past``, or ``future``.
        hangul: Optional target dictionary form for hangul-specific overrides.

    Returns:
        A tensed English clause ending with a period.
    """
    if hangul and hangul in _ENGLISH_BY_HANGUL:
        present, past, future = _ENGLISH_BY_HANGUL[hangul]
        if tense == "past":
            return f"I {past}."
        if tense == "future":
            return f"I will {future}."
        return f"I {present}."

    key = _gloss_key(english)
    forms = _ENGLISH_FORMS.get(key)
    if forms:
        present, past, future = forms
        if tense == "past":
            phrase = past
        elif tense == "future":
            phrase = future
            return f"I will {phrase}."
        else:
            phrase = present
        if phrase.startswith("do not ") or phrase.startswith("did not "):
            return f"I {phrase}."
        return f"I {phrase}."

    # Fallback: strip parentheticals and avoid naive "ed"
    base = PAREN_ENGLISH.sub("", english.replace("to ", "")).strip().rstrip(".")
    if tense == "past":
        irregular = {
            "go": "went",
            "come": "came",
            "eat": "ate",
            "drink": "drank",
            "read": "read",
            "meet": "met",
            "teach": "taught",
            "buy": "bought",
            "give": "gave",
            "know": "knew",
            "swim": "swam",
            "send": "sent",
            "bring": "brought",
            "think": "thought",
            "have": "had",
            "do": "did",
            "get": "got",
        }
        first = base.split()[0].lower() if base else ""
        if first in irregular:
            rest = " ".join(base.split()[1:])
            return f"I {irregular[first]}{(' ' + rest) if rest else ''}."
        if base.endswith("e"):
            return f"I {base}d."
        if base.endswith("y") and len(base) > 1 and base[-2] not in "aeiou":
            return f"I {base[:-1]}ied."
        return f"I {base}ed."
    if tense == "future":
        return f"I will {base}."
    return f"I {base}."


def _english_clause(english: str, tense: str) -> str:
    """Build a short English clause for an example.

    Past tense uses a naive ``+ed`` / ``y→ied`` rule and is not a full English
    conjugator — see module docstring.
    """
    base = PAREN_ENGLISH.sub("", english.replace("to ", "")).strip().rstrip(".")
    if tense == "past":
        if base.startswith("be "):
            return f"I was {base[3:]}."
        if base.endswith("y"):
            return f"I {base[:-1]}ied."
        return f"I {base}ed."
    if tense == "future":
        if base.startswith("be "):
            return f"I will be {base[3:]}."
        return f"I will {base}."
    if base.startswith("be "):
        return f"I am {base[3:]}."
    return f"I {base}."
