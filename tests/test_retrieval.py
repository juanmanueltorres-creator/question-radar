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


def test_retrieval_exposes_token_contributions_residuals_and_coverage():
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
    assert result.matched_token_count == len(result.matched_query_tokens)
    assert result.query_token_count > 0
    assert result.query_coverage == round(
        result.matched_token_count / result.query_token_count,
        6,
    )


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


def test_more_matched_query_tokens_outrank_one_rare_token():
    corpus = (
        entry("rare", "principal"),
        entry("covered", "sistema decision"),
    )

    pack = retrieve_candidates("principal sistema decision", corpus, limit=2)

    assert pack.results[0].entry.id == "covered"
    assert pack.results[0].matched_token_count == 2


def test_zero_lexical_evidence_abstains_instead_of_returning_arbitrary_rows():
    corpus = (
        entry("a", "costo actuar"),
        entry("b", "memoria trazabilidad"),
    )

    pack = retrieve_candidates(
        "recomendacion automatica modifica evaluarla",
        corpus,
        limit=5,
    )

    assert pack.retrieval_version == "v0.7"
    assert pack.abstained is True
    assert pack.abstention_reason == "no_lexical_evidence"
    assert pack.results == ()
    assert pack.review_required is True


def test_nonzero_evidence_returns_only_rows_with_evidence():
    corpus = (
        entry("match", "costo actuar"),
        entry("zero-a", "memoria trazabilidad"),
        entry("zero-b", "territorio geologia"),
    )

    pack = retrieve_candidates("costo decidir", corpus, limit=5)

    assert pack.abstained is False
    assert pack.abstention_reason is None
    assert [result.entry.id for result in pack.results] == ["match"]
    assert all(result.matched_token_count > 0 for result in pack.results)


def test_cross_version_duplicate_ids_keep_independent_document_tokens():
    corpus = (
        entry("same", "costo actuar", "v0.2", "profile"),
        entry("same", "memoria trazabilidad", "v0.4", "lineage_node"),
    )

    pack = retrieve_candidates("costo actuar memoria trazabilidad", corpus, limit=2)

    assert pack.corpus_size == 2
    assert {result.entry.source_version for result in pack.results} == {"v0.2", "v0.4"}
    v02 = next(result for result in pack.results if result.entry.source_version == "v0.2")
    v04 = next(result for result in pack.results if result.entry.source_version == "v0.4")
    assert set(v02.matched_query_tokens) == {"actuar", "costo"}
    assert set(v04.matched_query_tokens) == {"memoria", "trazabilidad"}


def test_every_retrieval_pack_requires_human_review():
    pack = retrieve_candidates("¿Qué evidencia falta?", (), limit=5)

    assert pack.retrieval_version == "v0.7"
    assert pack.review_required is True
    assert pack.corpus_size == 0
    assert pack.results == ()
    assert pack.abstained is True
    assert pack.abstention_reason == "no_lexical_evidence"


def test_blank_candidate_is_rejected():
    with pytest.raises(ValueError, match="question must be a non-empty string"):
        retrieve_candidates("   ", (), limit=5)


def test_limit_must_be_positive():
    with pytest.raises(ValueError, match="limit must be at least 1"):
        retrieve_candidates("¿Qué sabemos?", (), limit=0)
