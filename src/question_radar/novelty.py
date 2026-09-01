from __future__ import annotations

from dataclasses import dataclass
import unicodedata

from question_radar.lineage import QuestionNode, QuestionRelation


STOPWORDS = frozenset(
    {
        "a",
        "al",
        "and",
        "como",
        "con",
        "de",
        "del",
        "el",
        "en",
        "es",
        "esta",
        "este",
        "for",
        "la",
        "las",
        "lo",
        "los",
        "of",
        "o",
        "para",
        "por",
        "que",
        "se",
        "si",
        "the",
        "to",
        "un",
        "una",
        "unos",
        "unas",
        "y",
    }
)

INTERPRETATIONS = (
    "already_represented",
    "refines_existing",
    "operationalizes_existing",
    "challenges_assumption",
    "possible_new_branch",
)

_OPERATIONAL_MARKERS = frozenset({"como", "cuando", "cuanto", "quien", "donde"})
_CHALLENGE_PHRASES = ("y si", "que pasa si", "podria ser que")


@dataclass(frozen=True, slots=True)
class SimilarityEvidence:
    question_id: str
    score: float
    shared_tokens: tuple[str, ...]
    shared_bigrams: tuple[str, ...]
    candidate_only_tokens: tuple[str, ...]
    corpus_only_tokens: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NoveltyNeighbor:
    node: QuestionNode
    similarity: SimilarityEvidence
    lineage_degree: int


@dataclass(frozen=True, slots=True)
class NoveltyPack:
    novelty_version: str
    candidate_question: str
    neighbors: tuple[NoveltyNeighbor, ...]
    candidate_distinctive_tokens: tuple[str, ...]
    possible_interpretations: tuple[str, ...]
    review_required: bool


@dataclass(frozen=True, slots=True)
class CandidateQuestion:
    id: str
    question: str

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("candidate id must be a non-empty string")
        if not isinstance(self.question, str) or not self.question.strip():
            raise ValueError("candidate question must be a non-empty string")
        object.__setattr__(self, "id", self.id.strip())
        object.__setattr__(self, "question", self.question.strip())


@dataclass(frozen=True, slots=True)
class PossibleCluster:
    cluster_id: str
    question_ids: tuple[str, ...]
    shared_tokens: tuple[str, ...]


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


def normalize_tokens(text: str) -> tuple[str, ...]:
    words = _ascii_words(text)
    return tuple(
        word for word in words if len(word) >= 3 and word not in STOPWORDS
    )


def token_bigrams(tokens: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(f"{left} {right}" for left, right in zip(tokens, tokens[1:]))


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 0.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def compare_questions(
    candidate: str,
    corpus_question: str,
    question_id: str,
) -> SimilarityEvidence:
    if not isinstance(question_id, str) or not question_id.strip():
        raise ValueError("question_id must be a non-empty string")

    candidate_tokens = normalize_tokens(candidate)
    corpus_tokens = normalize_tokens(corpus_question)

    candidate_set = set(candidate_tokens)
    corpus_set = set(corpus_tokens)
    candidate_bigrams = set(token_bigrams(candidate_tokens))
    corpus_bigrams = set(token_bigrams(corpus_tokens))

    if candidate_tokens and candidate_tokens == corpus_tokens:
        score = 1.0
    elif not candidate_tokens and not corpus_tokens:
        score = 0.0
    else:
        token_jaccard = _jaccard(candidate_set, corpus_set)
        bigram_jaccard = _jaccard(candidate_bigrams, corpus_bigrams)
        score = round(0.7 * token_jaccard + 0.3 * bigram_jaccard, 6)

    return SimilarityEvidence(
        question_id=question_id.strip(),
        score=score,
        shared_tokens=tuple(sorted(candidate_set & corpus_set)),
        shared_bigrams=tuple(sorted(candidate_bigrams & corpus_bigrams)),
        candidate_only_tokens=tuple(sorted(candidate_set - corpus_set)),
        corpus_only_tokens=tuple(sorted(corpus_set - candidate_set)),
    )


def _lineage_degree(node_id: str, relations: list[QuestionRelation]) -> int:
    return sum(
        1
        for relation in relations
        if relation.source_question_id == node_id
        or relation.target_question_id == node_id
    )


def _raw_marker_tokens(text: str) -> set[str]:
    return set(_ascii_words(text))


def _has_challenge_syntax(text: str) -> bool:
    normalized = " ".join(_ascii_words(text))
    return any(phrase in normalized for phrase in _CHALLENGE_PHRASES)


def _possible_interpretations(
    candidate_question: str,
    candidate_tokens: tuple[str, ...],
    neighbors: tuple[NoveltyNeighbor, ...],
    distinctive_tokens: tuple[str, ...],
) -> tuple[str, ...]:
    top_score = neighbors[0].similarity.score if neighbors else 0.0
    distinctive_ratio = len(distinctive_tokens) / max(1, len(set(candidate_tokens)))
    top_token_count = (
        len(normalize_tokens(neighbors[0].node.question)) if neighbors else 0
    )
    raw_markers = _raw_marker_tokens(candidate_question)

    proposed: set[str] = set()
    if top_score >= 0.75 and distinctive_ratio <= 0.20:
        proposed.add("already_represented")
    if 0.45 <= top_score < 0.75 and len(candidate_tokens) > top_token_count:
        proposed.add("refines_existing")
    if (
        0.35 <= top_score < 0.75
        and bool(raw_markers & _OPERATIONAL_MARKERS)
    ):
        proposed.add("operationalizes_existing")
    if _has_challenge_syntax(candidate_question):
        proposed.add("challenges_assumption")
    if top_score < 0.45 or distinctive_ratio >= 0.40:
        proposed.add("possible_new_branch")

    return tuple(name for name in INTERPRETATIONS if name in proposed)


def build_novelty_pack(
    candidate_question: str,
    nodes: list[QuestionNode],
    relations: list[QuestionRelation],
    limit: int = 5,
) -> NoveltyPack:
    candidate_tokens = normalize_tokens(candidate_question)
    if limit < 1:
        raise ValueError("limit must be at least 1")

    neighbors = [
        NoveltyNeighbor(
            node=node,
            similarity=compare_questions(
                candidate_question,
                node.question,
                node.id,
            ),
            lineage_degree=_lineage_degree(node.id, relations),
        )
        for node in nodes
    ]
    neighbors.sort(key=lambda item: (-item.similarity.score, item.node.id))
    selected = tuple(neighbors[:limit])

    represented_tokens: set[str] = set()
    for neighbor in selected:
        represented_tokens.update(normalize_tokens(neighbor.node.question))
    distinctive_tokens = tuple(sorted(set(candidate_tokens) - represented_tokens))

    return NoveltyPack(
        novelty_version="v0.5",
        candidate_question=candidate_question.strip(),
        neighbors=selected,
        candidate_distinctive_tokens=distinctive_tokens,
        possible_interpretations=_possible_interpretations(
            candidate_question,
            candidate_tokens,
            selected,
            distinctive_tokens,
        ),
        review_required=True,
    )


def cluster_candidates(
    candidates: tuple[CandidateQuestion, ...],
    threshold: float = 0.35,
) -> tuple[PossibleCluster, ...]:
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0.0 and 1.0")

    by_id = {candidate.id: candidate for candidate in candidates}
    if len(by_id) != len(candidates):
        raise ValueError("candidate ids must be unique")

    adjacency: dict[str, set[str]] = {candidate.id: set() for candidate in candidates}
    ordered = sorted(candidates, key=lambda candidate: candidate.id)
    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            evidence = compare_questions(left.question, right.question, right.id)
            if evidence.score >= threshold:
                adjacency[left.id].add(right.id)
                adjacency[right.id].add(left.id)

    visited: set[str] = set()
    clusters: list[PossibleCluster] = []
    for candidate in ordered:
        if candidate.id in visited:
            continue
        stack = [candidate.id]
        component: list[str] = []
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            component.append(current)
            stack.extend(sorted(adjacency[current] - visited, reverse=True))

        if len(component) < 2:
            continue

        question_ids = tuple(sorted(component))
        token_sets = [set(normalize_tokens(by_id[item].question)) for item in question_ids]
        shared = set.intersection(*token_sets) if token_sets else set()
        clusters.append(
            PossibleCluster(
                cluster_id=f"cluster-{question_ids[0]}",
                question_ids=question_ids,
                shared_tokens=tuple(sorted(shared)),
            )
        )

    clusters.sort(key=lambda cluster: cluster.cluster_id)
    return tuple(clusters)
