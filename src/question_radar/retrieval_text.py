from __future__ import annotations

import unicodedata

from question_radar.novelty import STOPWORDS as NOVELTY_STOPWORDS


RETRIEVAL_STOPWORDS = frozenset(
    set(NOVELTY_STOPWORDS)
    | {
        "cuando",
        "mas",
        "pero",
        "principal",
        "quien",
        "sin",
        "sobre",
        "sus",
        "tan",
    }
)


def _ascii_words(text: str) -> tuple[str, ...]:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("question must be a non-empty string")

    decomposed = unicodedata.normalize("NFKD", text.lower())
    without_marks = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    cleaned = "".join(
        char if (char.isalnum() or char.isspace()) else " " for char in without_marks
    )
    return tuple(cleaned.split())


def _normalize_plural(token: str) -> str:
    # These suffixes intentionally cover only a narrow set of transparent
    # nominal/adjectival plurals. They are not a general Spanish stemmer.
    if len(token) >= 7 and token.endswith("iones"):
        return token[:-2]
    if len(token) >= 6 and token.endswith("ores"):
        return token[:-2]
    if len(token) >= 6 and token.endswith("emas"):
        return token[:-1]
    if len(token) >= 6 and token.endswith("onas"):
        return token[:-1]
    if len(token) >= 5 and token.endswith("os") and not token.endswith("mos"):
        return token[:-1]
    return token


def normalize_retrieval_tokens(text: str) -> tuple[str, ...]:
    words = _ascii_words(text)
    tokens: list[str] = []
    for word in words:
        if len(word) < 3 or word in RETRIEVAL_STOPWORDS:
            continue
        normalized = _normalize_plural(word)
        if normalized in RETRIEVAL_STOPWORDS:
            continue
        tokens.append(normalized)
    return tuple(tokens)
