# SPDX-License-Identifier: BSD-3-Clause
"""Heuristic Korean verb conjugation for polite present, past, and future."""

from __future__ import annotations

import re

VariantForms = dict[str, str]
TenseForms = dict[str, VariantForms]

PAREN_ENGLISH = re.compile(r"\s*\([^)]*\)")

# Dictionary-form hangul -> (casual_present, formal_present, casual_past, formal_past, casual_future, formal_future) stems after prefix
_ROOT_FORMS: dict[str, tuple[str, str, str, str, str, str]] = {
    "가다": ("가요", "갑니다", "갔어요", "갔습니다", "갈 거예요", "가겠습니다"),
    "오다": ("와요", "옵니다", "왔어요", "왔습니다", "올 거예요", "오겠습니다"),
    "먹다": (
        "먹어요",
        "먹습니다",
        "먹었어요",
        "먹었습니다",
        "먹을 거예요",
        "먹겠습니다",
    ),
    "마시다": (
        "마셔요",
        "마십니다",
        "마셨어요",
        "마셨습니다",
        "마실 거예요",
        "마시겠습니다",
    ),
    "읽다": (
        "읽어요",
        "읽습니다",
        "읽었어요",
        "읽었습니다",
        "읽을 거예요",
        "읽겠습니다",
    ),
    "보다": ("봐요", "봅니다", "봤어요", "봤습니다", "볼 거예요", "보겠습니다"),
    "받다": (
        "받아요",
        "받습니다",
        "받았어요",
        "받았습니다",
        "받을 거예요",
        "받겠습니다",
    ),
    "듣다": (
        "들어요",
        "듣습니다",
        "들었어요",
        "들었습니다",
        "들을 거예요",
        "듣겠습니다",
    ),
    "쓰다": ("써요", "씁니다", "썼어요", "썼습니다", "쓸 거예요", "쓰겠습니다"),
    "주다": ("줘요", "줍니다", "줬어요", "줬습니다", "줄 거예요", "주겠습니다"),
    "사다": ("사요", "삽니다", "샀어요", "샀습니다", "살 거예요", "사겠습니다"),
    "치다": ("쳐요", "칩니다", "쳤어요", "쳤습니다", "칠 거예요", "치겠습니다"),
    "만나다": (
        "만나요",
        "만납니다",
        "만났어요",
        "만났습니다",
        "만날 거예요",
        "만나겠습니다",
    ),
    "기다리다": (
        "기다려요",
        "기다립니다",
        "기다렸어요",
        "기다렸습니다",
        "기다릴 거예요",
        "기다리겠습니다",
    ),
    "배우다": (
        "배워요",
        "배웁니다",
        "배웠어요",
        "배웠습니다",
        "배울 거예요",
        "배우겠습니다",
    ),
    "가르치다": (
        "가르쳐요",
        "가르칩니다",
        "가르쳤어요",
        "가르쳤습니다",
        "가르칠 거예요",
        "가르치겠습니다",
    ),
    "모르다": (
        "몰라요",
        "모릅니다",
        "몰랐어요",
        "몰랐습니다",
        "모를 거예요",
        "모르겠습니다",
    ),
    "알다": ("알아요", "압니다", "알았어요", "알았습니다", "알 거예요", "알겠습니다"),
    "끝나다": (
        "끝나요",
        "끝납니다",
        "끝났어요",
        "끝났습니다",
        "끝날 거예요",
        "끝나겠습니다",
    ),
    "씻다": (
        "씻어요",
        "씻습니다",
        "씻었어요",
        "씻었습니다",
        "씻을 거예요",
        "씻겠습니다",
    ),
    "보내다": (
        "보내요",
        "보냅니다",
        "보냈어요",
        "보냈습니다",
        "보낼 거예요",
        "보내겠습니다",
    ),
    "빌리다": (
        "빌려요",
        "빌립니다",
        "빌렸어요",
        "빌렸습니다",
        "빌릴 거예요",
        "빌리겠습니다",
    ),
    "춤추다": (
        "춤춰요",
        "춤춥니다",
        "춤췄어요",
        "춤췄습니다",
        "춤출 거예요",
        "춤추겠습니다",
    ),
}

_ROOT_SUFFIXES = tuple(sorted(_ROOT_FORMS, key=len, reverse=True))

# Pattern-only dictionary forms expanded with registry vocabulary for conjugation/examples.
_CANONICAL_HANGUL: dict[str, str] = {
    "에 오다": "학교에 오다",
    "에 가다": "학교에 가다",
}


def _effective_hangul(hangul: str) -> str:
    return _CANONICAL_HANGUL.get(hangul.strip(), hangul.strip())


def _split_prefix_and_root(hangul: str) -> tuple[str, str]:
    text = hangul.strip()
    for root in _ROOT_SUFFIXES:
        if text.endswith(root):
            return text[: -len(root)], root
    if text.endswith("하다"):
        return text[:-2], "하다"
    if text.endswith("다"):
        return text[:-1], "다"
    return "", text


def _hada_forms(prefix: str, stem_h: str) -> TenseForms:
    base = f"{prefix}{stem_h}"
    return {
        "present": {"casual_polite": f"{base}해요", "formal_polite": f"{base}합니다"},
        "past": {"casual_polite": f"{base}했어요", "formal_polite": f"{base}했습니다"},
        "future": {
            "casual_polite": f"{base}할 거예요",
            "formal_polite": f"{base}하겠습니다",
        },
    }


def _attach(prefix: str, forms: tuple[str, str, str, str, str, str]) -> TenseForms:
    casual_pres, formal_pres, casual_past, formal_past, casual_fut, formal_fut = forms
    join = prefix
    if join and not join.endswith(" "):
        join = f"{join} "
    return {
        "present": {
            "casual_polite": f"{join}{casual_pres}",
            "formal_polite": f"{join}{formal_pres}",
        },
        "past": {
            "casual_polite": f"{join}{casual_past}",
            "formal_polite": f"{join}{formal_past}",
        },
        "future": {
            "casual_polite": f"{join}{casual_fut}",
            "formal_polite": f"{join}{formal_fut}",
        },
    }


def _generic_da_forms(prefix: str, stem: str) -> TenseForms:
    if not stem:
        stem = "하"
    last = stem[-1]
    code = ord(last) - ord("가")
    jong = code % 28
    jung = (code // 28) % 21

    if jong == 8:  # ㅂ
        stem = stem[:-1]
        casual_pres = stem + "워요"
        formal_pres = stem + "웁니다"
        casual_past = stem + "웠어요"
        formal_past = stem + "웠습니다"
        casual_fut = stem + "울 거예요"
        formal_fut = stem + "우겠습니다"
    elif jung in (0, 9, 13, 18):  # ㅏㅗ
        casual_pres = stem + "아요"
        formal_pres = stem + "습니다"
        casual_past = stem + "았어요"
        formal_past = stem + "았습니다"
        casual_fut = stem + "을 거예요"
        formal_fut = stem + "겠습니다"
    else:
        casual_pres = stem + "어요"
        formal_pres = stem + "습니다"
        casual_past = stem + "었어요"
        formal_past = stem + "었습니다"
        casual_fut = stem + "을 거예요"
        formal_fut = stem + "겠습니다"

    return _attach(
        prefix,
        (casual_pres, formal_pres, casual_past, formal_past, casual_fut, formal_fut),
    )


def conjugate_verb(hangul: str) -> TenseForms:
    hangul = _effective_hangul(hangul)
    prefix, root = _split_prefix_and_root(hangul)
    if root == "하다":
        return _hada_forms(prefix, "")
    if root in _ROOT_FORMS:
        return _attach(prefix, _ROOT_FORMS[root])
    if root == "다":
        return _generic_da_forms(prefix, hangul[: -len("다")] if hangul.endswith("다") else hangul)
    return _generic_da_forms(prefix, root.rstrip("다"))


def _english_clause(english: str, tense: str) -> str:
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


def example_for_form(hangul: str, form: str, english: str, *, tense: str = "present") -> dict[str, str]:
    """Build a short example sentence using the verb's object phrase when present."""
    hangul = _effective_hangul(hangul)
    prefix, root = _split_prefix_and_root(hangul)
    prefix = prefix.strip()
    english_sentence = _english_clause(english, tense)

    # Conjugated forms already include any leading phrase (object, location, etc.).
    if prefix:
        return {"hangul": f"저는 {form}.", "english": english_sentence}

    defaults: dict[str, str] = {
        "먹다": "밥을",
        "마시다": "물을",
        "읽다": "책을",
        "보다": "영화를",
        "듣다": "음악을",
        "공부하다": "한국어를",
        "사다": "옷을",
        "만나다": "친구를",
        "기다리다": "버스를",
        "주다": "선생님에게",
        "빌리다": "책을",
        "보내다": "돈을",
        "말하다": "한국어로",
        "좋아하다": "김치를",
        "싫어하다": "커피를",
        "사랑하다": "가족을",
    }
    obj = defaults.get(root, "")
    if obj:
        return {"hangul": f"저는 {obj} {form}.", "english": english_sentence}

    return {"hangul": f"저는 {form}.", "english": english_sentence}


def examples_for_verb(hangul: str, english: str, forms: TenseForms) -> dict[str, dict[str, list[dict[str, str]]]]:
    result: dict[str, dict[str, list[dict[str, str]]]] = {}
    for tense, variants in forms.items():
        result[tense] = {}
        for variant, form in variants.items():
            result[tense][variant] = [example_for_form(hangul, form, english, tense=tense)]
    return result
