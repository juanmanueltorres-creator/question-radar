from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math

from question_radar.novelty import compare_questions, normalize_tokens


BM25_K1 = 1.5
BM25_B = 0.75
_SOURCE_PAIRS = {
    ("v0.2", "profile"),
    ("v0.4", "lineage_node"),
}


@dataclass(frozen=True, slots=True)
class CorpusEntry:
    id: str
    question: str
    source_version: str
    source_kind: str
    provenance: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("id must be a non-empty string")
        if not isinstance(self.question, str) or not self.question.strip():
            raise ValueError("question must be a non-empty string")
        if (self.source_version, self.source_kind) not in _SOURCE_PAIRS:
            if self.source_version not in {"v0.2", "v0.4"}:
                raise ValueError("source_version must be v0.2 or v0.4")
            raise ValueError("source_kind does not match source_version")
        if self.provenance is not None and not isinstance(self.provenance, str):
            raise ValueError("provenance must be a string or null")

        object.__setattr__(self, "id", self.id.strip())
        object.__setattr__(self, "question", self.question.strip())
        if self.provenance is not None:
            provenance = self.provenance.strip()
            object.__setattr__(self, "provenance", provenance or None)


@dataclass(frozen=True, slots=True)
class TokenContribution:
    token: str
    document_frequency: int
    term_frequency: int
    contribution: float


@dataclass(frozen=True, slots=True)
class RetrievalEvidence:
    entry: CorpusEntry
    bm25_score: float
    jaccard_score: float
    matched_query_tokens: tuple[str, ...]
    residual_query_tokens: tuple[str, ...]
    token_contributions: tuple[TokenContribution, ...]


@dataclass(frozen=True, slots=True)
class RetrievalPack:
    retrieval_version: str
    candidate_question: str
    corpus_size: int
    results: tuple[RetrievalEvidence, ...]
    review_required: bool


def _idf(corpus_size: int, document_frequency: int) -> float:
    return math.log(
        1.0
        + (corpus_size - document_frequency + 0.5)
        / (document_frequency + 0.5)
    )


def retrieve_candidates(
    candidate_question: str,
    corpus: tuple[CorpusEntry, ...],
    limit: int = 5,
) -> RetrievalPack:
    query_tokens = normalize_tokens(candidate_question)
    if limit < 1:
        raise ValueError("limit must be at least 1")

    if not corpus:
        return RetrievalPack(
            retrieval_version="v0.6",
            candidate_question=candidate_question.strip(),
            corpus_size=0,
            results=(),
            review_required=True,
        )

    document_tokens = {
        entry.id: normalize_tokens(entry.question)
        for entry in corpus
    }
    corpus_size = len(corpus)
    average_document_length = sum(
        len(tokens) for tokens in document_tokens.values()
    ) / corpus_size

    document_frequency: Counter[str] = Counter()
    for tokens in document_tokens.values():
        document_frequency.update(set(tokens))

    unique_query_tokens = tuple(dict.fromkeys(query_tokens))
    results: list[RetrievalEvidence] = []

    for entry in corpus:
        tokens = document_tokens[entry.id]
        frequencies = Counter(tokens)
        document_length = len(tokens)
        contributions: list[TokenContribution] = []

        for token in unique_query_tokens:
            term_frequency = frequencies[token]
            if term_frequency == 0:
                continue

            df = document_frequency[token]
            idf = _idf(corpus_size, df)
            length_norm = (
                1.0 - BM25_B
                + BM25_B * document_length / average_document_length
                if average_document_length
                else 1.0
            )
            contribution = idf * (
                term_frequency * (BM25_K1 + 1.0)
            ) / (
                term_frequency + BM25_K1 * length_norm
            )
            contributions.append(
                TokenContribution(
                    token=token,
                    document_frequency=df,
                    term_frequency=term_frequency,
                    contribution=round(contribution, 6),
                )
            )

        contributions.sort(key=lambda item: (-item.contribution, item.token))
        bm25_score = round(sum(item.contribution for item in contributions), 6)
        matched = tuple(sorted({item.token for item in contributions}))
        document_token_set = set(tokens)
        residual = tuple(
            sorted(set(unique_query_tokens) - document_token_set)
        )
        jaccard = compare_questions(
            candidate_question,
            entry.question,
            entry.id,
        ).score

        results.append(
            RetrievalEvidence(
                entry=entry,
                bm25_score=bm25_score,
                jaccard_score=jaccard,
                matched_query_tokens=matched,
                residual_query_tokens=residual,
                token_contributions=tuple(contributions),
            )
        )

    results.sort(
        key=lambda result: (
            -result.bm25_score,
            -result.jaccard_score,
            result.entry.id,
        )
    )

    return RetrievalPack(
        retrieval_version="v0.6",
        candidate_question=candidate_question.strip(),
        corpus_size=corpus_size,
        results=tuple(results[:limit]),
        review_required=True,
    )
