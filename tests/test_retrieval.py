import pytest

from question_radar.retrieval import CorpusEntry, retrieve_candidates


def entry(
    entry_id: str,
    question: str,
    version: str = "v0.2",
    kind: str = "profile",
) -> CorpusEntry:
    return CorpusEntry(entry_id, question, version, kind, None)


def test_rare_query_terms_raise_relevant_entry():
    corpus = (
        entry("a", "¿Cuál es el costo de actuar y de no actuar?"),
        entry("b", "¿Cómo evaluamos una decisión general?"),
        entry("c", "¿Cómo documentamos una organización?"),
    )

    pack = retrieve_candidates(
        "¿Qué pesa más: el costo de equivocarse o el costo de no actuar?",
        corpus,
        limit=3,
    )

    assert pack.results[0].entry.id == "a"
    assert pack.results[0].bm25_score > 0
    assert "costo" in pack.results[0].matched_query_tokens


def test_ranking_tie_breaks_by_jaccard_then_id():
    corpus = (
        entry("b", "¿Cómo cambia una decisión?"),
        entry("a", "¿Cómo cambia una decisión?"),
    )

    pack = retrieve_candidates("¿Cómo cambia una decisión?", corpus, limit=2)

    assert [result.entry.id for result in pack.results] == ["a", "b"]


def test_retrieval_exposes_token_contributions_and_residuals():
    corpus = (entry("a", "¿Cuál es el costo de actuar y de no actuar?"),)

    pack = retrieve_candidates(
        "¿Qué pesa más cuando el tiempo es limitado: la probabilidad de equivocarse o el costo de no actuar?",
        corpus,
        limit=1,
    )
    result = pack.results[0]

    assert result.token_contributions
    assert {item.token for item in result.token_contributions} >= {"costo", "actuar"}
    assert "tiempo" in result.residual_query_tokens
    assert result.jaccard_score >= 0


def test_contributions_are_sorted_by_score_then_token():
    corpus = (
        entry("a", "riesgo costo actuar riesgo"),
        entry("b", "costo decidir"),
    )

    pack = retrieve_candidates("riesgo costo actuar", corpus, limit=1)
    contributions = pack.results[0].token_contributions

    assert list(contributions) == sorted(
        contributions,
        key=lambda item: (-item.contribution, item.token),
    )


def test_every_retrieval_pack_requires_human_review():
    pack = retrieve_candidates("¿Qué evidencia falta?", (), limit=5)

    assert pack.retrieval_version == "v0.6"
    assert pack.review_required is True
    assert pack.corpus_size == 0
    assert pack.results == ()


def test_blank_candidate_is_rejected():
    with pytest.raises(ValueError, match="question must be a non-empty string"):
        retrieve_candidates("   ", (), limit=5)


def test_limit_must_be_positive():
    with pytest.raises(ValueError, match="limit must be at least 1"):
        retrieve_candidates("¿Qué sabemos?", (), limit=0)
