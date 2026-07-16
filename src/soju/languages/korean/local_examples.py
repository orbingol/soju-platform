# SPDX-License-Identifier: BSD-3-Clause
"""Deterministic Korean 1A/1B example sentences (no Ollama)."""

from __future__ import annotations

from typing import Any

from soju.base import get_base_language
from soju.core.models import EXAMPLE_TENSES as TENSES
from soju.core.models import EXAMPLE_VARIANTS as VARIANTS
from soju.languages.korean.morphology import (
    _copula,
    _object_particle,
    _subject_particle,
    _topic_particle,
    build_verb_english,
    build_verb_hangul,
)
from soju.languages.korean.text import normalize_hangul
from soju.levels import LanguageLevel


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
                english = get_base_language().scrub_example_gloss(english)
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
    english = get_base_language().scrub_example_gloss(noun["english"])
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
                "hangul": normalize_hangul(ex["hangul"]),
                "english": get_base_language().normalize(ex["english"]),
            }
        )
    return cleaned
