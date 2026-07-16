# SPDX-License-Identifier: BSD-3-Clause
"""Korean morphology helpers: particles, copula, and verb example surfaces."""

from __future__ import annotations

from soju.base import get_base_language
from soju.languages.korean.conjugation import _split_prefix_and_root

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
    base = get_base_language().clause_for_tense(english, tense, term=verb_hangul)
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
