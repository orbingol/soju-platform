# SPDX-License-Identifier: BSD-3-Clause
"""Deterministic Korean 1A/1B example sentences (no Ollama)."""

from __future__ import annotations

import re
from typing import Any

from soju import db
from soju.language_levels import LanguageLevel, get_language_level, vocabulary_for_level

TENSES = ("present", "past", "future")
VARIANTS = ("casual_polite", "formal_polite")
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

# Extra hangul wrappers keyed by dictionary hangul (optional object/place already in form)
_TIME_1A = {
    "present": ("지금", "now"),
    "past": ("어제", "yesterday"),
    "future": ("내일", "tomorrow"),
}
_TIME_1B = {
    "present": ("오늘", "today"),
    "past": ("지난주에", "last week"),
    "future": ("다음 주에", "next week"),
}

_SUBJECTS_1A = [
    ("저는", "I"),
    ("친구가", "My friend"),
    ("학생이", "The student"),
]
_SUBJECTS_1B = [
    ("저는", "I"),
    ("친구가", "My friend"),
    ("선생님이", "The teacher"),
    ("동생이", "My younger sibling"),
]


def _gloss_key(english: str) -> str:
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


def _pick_subject(index: int, level_id: str) -> tuple[str, str]:
    subjects = _SUBJECTS_1B if level_id == "1B" else _SUBJECTS_1A
    return subjects[index % len(subjects)]


def _pick_time(tense: str, level_id: str) -> tuple[str, str]:
    table = _TIME_1B if level_id == "1B" else _TIME_1A
    return table[tense]


def _form_already_has_prefix(form: str) -> bool:
    """True when conjugated form already includes object/place (e.g. 집에 가요)."""
    return " " in form.strip()


_DEFAULT_OBJECTS: dict[str, str] = {
    "먹다": "밥을",
    "마시다": "물을",
    "읽다": "책을",
    "보다": "영화를",
    "듣다": "음악을",
    "공부하다": "한국어를",
    "사다": "옷을",
    "만나다": "친구를",
    "기다리다": "버스를",
    "주다": "선물을",
    "빌리다": "책을",
    "보내다": "편지를",
    "말하다": "한국어로",
    "좋아하다": "김치를",
    "싫어하다": "커피를",
    "사랑하다": "가족을",
    "알다": "답을",
    "모르다": "길을",
    "가르치다": "한국어를",
    "배우다": "한국어를",
    "시작하다": "수업을",
    "끝나다": "수업이",
    "생각하다": "친구를",
    "치다": "공을",
}


def build_verb_hangul(
    form: str,
    tense: str,
    variant: str,
    *,
    level_id: str,
    index: int,
    verb_hangul: str = "",
) -> str:
    time_ko, _ = _pick_time(tense, level_id)
    from soju.conjugate import _split_prefix_and_root

    _, root = _split_prefix_and_root(verb_hangul or form)
    obj = ""
    if not _form_already_has_prefix(form):
        obj = _DEFAULT_OBJECTS.get(root, "")
        if obj:
            form_with_obj = f"{obj} {form}"
        else:
            form_with_obj = form
    else:
        form_with_obj = form

    if level_id == "1B":
        return f"저는 {time_ko} {form_with_obj}."
    return f"저는 {time_ko} {form_with_obj}."


def build_verb_english(english: str, tense: str, hangul: str, *, level_id: str, verb_hangul: str) -> str:
    base = english_for_tense(english, tense, hangul=verb_hangul)
    # Enrich with time adverb when present in hangul
    time_map = {
        "어제": " yesterday",
        "내일": " tomorrow",
        "지금": " now",
        "오늘": " today",
        "지난주에": " last week",
        "다음 주에": " next week",
    }
    for ko, en in time_map.items():
        if ko in hangul and en.strip() not in base.lower():
            if tense == "future" and "will" in base:
                return base[:-1] + en + "."
            if tense == "past":
                return base[:-1] + en + "."
            if tense == "present" and ko in ("지금", "오늘"):
                return base[:-1] + en + "."
    return base



def _has_batchim(syllable: str) -> bool:
    if not syllable:
        return False
    code = ord(syllable[-1])
    if code < 0xAC00 or code > 0xD7A3:
        return False
    return (code - 0xAC00) % 28 != 0


def _topic_particle(noun: str) -> str:
    return "은" if _has_batchim(noun) else "는"


def _subject_particle(noun: str) -> str:
    return "이" if _has_batchim(noun) else "가"


def _object_particle(noun: str) -> str:
    return "을" if _has_batchim(noun) else "를"


def _copula(noun: str) -> tuple[str, str]:
    if _has_batchim(noun):
        return "이에요", "입니다"
    return "예요", "입니다"


def examples_for_verb(
    verb: dict[str, Any],
    forms: dict[str, dict[str, str]],
    *,
    level: LanguageLevel,
    index: int = 0,
    examples_per: int = 2,
) -> dict[str, dict[str, list[dict[str, str]]]]:
    """Build present/past/future examples. Includes a 1A and 1B sentence per cell when possible."""
    result: dict[str, dict[str, list[dict[str, str]]]] = {}
    for tense in TENSES:
        result[tense] = {}
        for vi, variant in enumerate(VARIANTS):
            form = forms.get(tense, {}).get(variant)
            if not form:
                continue
            examples: list[dict[str, str]] = []
            for level_id in ("1A", "1B"):
                hangul = build_verb_hangul(
                    form,
                    tense,
                    variant,
                    level_id=level_id,
                    index=index + vi,
                    verb_hangul=verb["hangul"],
                )
                if form.replace(" ", "") not in hangul.replace(" ", ""):
                    hangul = f"저는 {form}."
                english = build_verb_english(
                    verb["english"],
                    tense,
                    hangul,
                    level_id=level_id,
                    verb_hangul=verb["hangul"],
                )
                english = PAREN_ENGLISH.sub("", english).strip()
                examples.append({"hangul": hangul, "english": english})
            # Deduplicate if 1A/1B produced the same hangul
            deduped: list[dict[str, str]] = []
            seen: set[str] = set()
            for ex in examples:
                if ex["hangul"] in seen:
                    continue
                seen.add(ex["hangul"])
                deduped.append(ex)
            result[tense][variant] = deduped[: max(1, examples_per)]
    return result


def examples_for_noun(
    noun: dict[str, Any],
    *,
    level: LanguageLevel,
    index: int = 0,
    examples_per: int = 2,
) -> list[dict[str, str]]:
    """Two examples: one 1A-style, one 1B-style."""
    a = _examples_for_noun_level(noun, level_id="1A", index=index)
    b = _examples_for_noun_level(noun, level_id="1B", index=index)
    merged: list[dict[str, str]] = []
    seen: set[str] = set()
    for ex in [a[0], b[0] if b else None, a[1] if len(a) > 1 else None]:
        if not ex or ex["hangul"] in seen:
            continue
        seen.add(ex["hangul"])
        merged.append(ex)
        if len(merged) >= examples_per:
            break
    return merged


def _examples_for_noun_level(
    noun: dict[str, Any],
    *,
    level_id: str,
    index: int = 0,
) -> list[dict[str, str]]:
    hangul = noun["hangul"]
    english = PAREN_ENGLISH.sub("", noun["english"]).strip()
    topic = _topic_particle(hangul)
    subject = _subject_particle(hangul)
    obj = _object_particle(hangul)
    casual_cop, _formal_cop = _copula(hangul)

    place_markers = (
        "학교",
        "집",
        "병원",
        "은행",
        "식당",
        "카페",
        "도서관",
        "공원",
        "회사",
        "공항",
        "역",
        "서점",
        "영화관",
        "수영장",
        "화장실",
        "교실",
        "백화점",
        "편의점",
        "우체국",
        "약국",
        "대사관",
        "체육관",
        "헬스장",
        "테니스장",
        "목욕탕",
        "휴게실",
        "사무실",
        "대학교",
        "기차역",
        "지하철역",
        "버스 터미널",
    )
    food_markers = (
        "밥",
        "물",
        "커피",
        "맥주",
        "김치",
        "비빔밥",
        "불고기",
        "라면",
        "우유",
        "사과",
        "빵",
        "케이크",
        "음식",
        "김밥",
        "삼계탕",
        "갈비",
        "초콜릿",
        "아이스크림",
        "오렌지",
        "배",
        "바나나",
        "사이다",
        "콜라",
        "녹차",
        "레몬차",
        "오렌지주스",
    )
    people_markers = (
        "친구",
        "선생님",
        "학생",
        "의사",
        "요리사",
        "회사원",
        "어머니",
        "아버지",
        "엄마",
        "아빠",
        "형",
        "오빠",
        "누나",
        "언니",
        "동생",
        "가족",
        "남편",
        "아내",
        "아이",
        "아기",
        "동료",
    )

    examples: list[dict[str, str]] = []

    if any(hangul == p or hangul.endswith(p) for p in place_markers):
        if level_id == "1B":
            examples.append(
                {
                    "hangul": f"내일 친구하고 {hangul}에 갈 거예요.",
                    "english": f"I will go to the {english} with a friend tomorrow.",
                }
            )
            examples.append(
                {
                    "hangul": f"{hangul}이 어디에 있어요?",
                    "english": f"Where is the {english}?",
                }
            )
        else:
            examples.append(
                {
                    "hangul": f"저는 {hangul}에 가요.",
                    "english": f"I go to the {english}.",
                }
            )
            examples.append(
                {
                    "hangul": f"이 {hangul}{topic} 커요.",
                    "english": f"This {english} is big.",
                }
            )
    elif any(hangul == f or hangul.endswith(f) for f in food_markers):
        examples.append(
            {
                "hangul": f"저는 {hangul}{obj} 좋아해요.",
                "english": f"I like {english}.",
            }
        )
        if level_id == "1B":
            examples.append(
                {
                    "hangul": f"어제 {hangul}{obj} 먹었어요.",
                    "english": f"I ate {english} yesterday.",
                }
            )
        else:
            examples.append(
                {
                    "hangul": f"이것은 {hangul}{casual_cop}.",
                    "english": f"This is {english}.",
                }
            )
    elif any(hangul == p or hangul.endswith(p) for p in people_markers):
        examples.append(
            {
                "hangul": f"제 {hangul}{topic} 친절해요.",
                "english": f"My {english} is kind.",
            }
        )
        examples.append(
            {
                "hangul": f"{hangul}{subject} 학교에 가요.",
                "english": f"My {english} goes to school.",
            }
        )
    else:
        examples.append(
            {
                "hangul": f"이것은 {hangul}{casual_cop}.",
                "english": f"This is {english}.",
            }
        )
        if level_id == "1B":
            examples.append(
                {
                    "hangul": f"저는 {hangul}{obj} 샀어요.",
                    "english": f"I bought {english}.",
                }
            )
        else:
            examples.append(
                {
                    "hangul": f"저는 {hangul}{subject} 있어요.",
                    "english": f"I have {english}.",
                }
            )

    cleaned: list[dict[str, str]] = []
    for ex in examples[:2]:
        cleaned.append(
            {
                "hangul": db.normalize_hangul(ex["hangul"]),
                "english": db.normalize_english(ex["english"]),
            }
        )
    return cleaned


def generate_all_local(
    *,
    level_id: str | None = None,
    verbs: bool = True,
    nouns: bool = True,
    examples_per: int = 2,
    fill_mode: str = "fill-empty",
    root=None,
) -> tuple[dict[str, Any], int]:
    """Fill examples store for verbs and/or nouns using local 1A+1B templates."""
    level = get_language_level(level_id, root)
    examples_store = db.load_examples_store(root)
    updated = 0

    if verbs:
        verb_entries = [e for e in vocabulary_for_level(level.id, root) if e.get("type") == "verb"]
        if not verb_entries:
            verb_entries = db.vocabulary_by_type("verb", root)
        forms_cache = db.load_verb_forms_cache(root)
        for index, verb in enumerate(verb_entries):
            forms = db.load_verb_forms(verb["id"], root, cache=forms_cache)
            if not all(forms.get(t, {}).get(v) for t in TENSES for v in VARIANTS):
                continue
            if fill_mode == "fill-empty" and not db.verb_entry_needs_fill(forms, examples_store.get(verb["id"])):
                continue
            examples_store[verb["id"]] = examples_for_verb(verb, forms, level=level, index=index, examples_per=examples_per)
            updated += 1

    if nouns:
        noun_entries = [e for e in vocabulary_for_level(level.id, root) if e.get("type") == "noun"]
        if not noun_entries:
            noun_entries = db.vocabulary_by_type("noun", root)
        for index, noun in enumerate(noun_entries):
            if fill_mode == "fill-empty" and not db.noun_entry_needs_fill(examples_store.get(noun["id"])):
                continue
            examples_store[noun["id"]] = {"default": examples_for_noun(noun, level=level, index=index, examples_per=examples_per)}
            updated += 1

    return examples_store, updated
