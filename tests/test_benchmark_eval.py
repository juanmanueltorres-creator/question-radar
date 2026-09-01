from __future__ import annotations

from question_radar.benchmark_eval import evaluate_benchmark
from question_radar.benchmark_io import GoldCase, GoldJudgment
from question_radar.retrieval import CorpusEntry


def _entry(entry_id: str, question: str) -> CorpusEntry:
    return CorpusEntry(
        id=entry_id,
        question=question,
        source_version="v0.2",
        source_kind="profile",
        provenance=None,
    )


def _judgment(entry_id: str, relevance: str = "relevant") -> GoldJudgment:
    return GoldJudgment(
        entry_id=entry_id,
        source_version="v0.2",
        relevance=relevance,
    )


def _positive_case(
    candidate_id: str,
    question: str,
    judgments: tuple[GoldJudgment, ...],
    *,
    scope: str = "positive_only",
) -> GoldCase:
    return GoldCase(
        candidate_id=candidate_id,
        question=question,
        judgment_scope=scope,
        expected_abstention=False,
        judgments=judgments,
    )


def test_first_rank_useful_hit_has_full_hit_recall_and_mrr() -> None:
    corpus = (
        _entry("gold", "alpha beta gamma"),
        _entry("noise", "alpha delta"),
    )
    case = _positive_case("q1", "alpha beta", (_judgment("gold"),))

    result = evaluate_benchmark((case,), corpus, k=5)

    assert result.hit_rate_at_k == 1.0
    assert result.recall_at_k == 1.0
    assert result.mrr == 1.0
    assert result.false_abstentions == 0
    assert result.cases[0].reciprocal_rank == 1.0
    assert result.cases[0].useful_found_count == 1


def test_second_rank_first_useful_hit_has_half_reciprocal_rank() -> None:
    corpus = (
        _entry("noise", "alpha beta gamma"),
        _entry("gold", "alpha beta"),
    )
    case = _positive_case("q1", "alpha beta gamma", (_judgment("gold"),))

    result = evaluate_benchmark((case,), corpus, k=5)

    assert result.hit_rate_at_k == 1.0
    assert result.cases[0].first_useful_rank == 2
    assert result.cases[0].reciprocal_rank == 0.5
    assert result.mrr == 0.5


def test_partially_relevant_counts_as_useful_for_recall() -> None:
    corpus = (_entry("partial", "alpha beta"),)
    case = _positive_case(
        "q1",
        "alpha beta",
        (_judgment("partial", "partially_relevant"),),
    )

    result = evaluate_benchmark((case,), corpus, k=5)

    assert result.recall_at_k == 1.0
    assert result.cases[0].found_judgments[0].relevance == "partially_relevant"


def test_positive_abstention_is_counted_as_false_abstention() -> None:
    corpus = (_entry("gold", "completely unrelated"),)
    case = _positive_case("q1", "alpha beta", (_judgment("gold"),))

    result = evaluate_benchmark((case,), corpus, k=5)

    assert result.cases[0].abstained is True
    assert result.cases[0].false_abstention is True
    assert result.false_abstentions == 1
    assert result.hit_rate_at_k == 0.0
    assert result.recall_at_k == 0.0
    assert result.mrr == 0.0


def test_exhaustive_abstention_control_tracks_correct_and_false_non_abstention() -> None:
    correct = GoldCase(
        candidate_id="control-1",
        question="zeta theta",
        judgment_scope="exhaustive",
        expected_abstention=True,
        judgments=(),
    )
    false_non = GoldCase(
        candidate_id="control-2",
        question="alpha theta",
        judgment_scope="exhaustive",
        expected_abstention=True,
        judgments=(),
    )
    corpus = (_entry("noise", "alpha beta"),)

    result = evaluate_benchmark((correct, false_non), corpus, k=5)

    assert result.abstention_control_count == 2
    assert result.correct_abstentions == 1
    assert result.false_non_abstentions == 1
    assert result.abstention_accuracy == 0.5


def test_sparse_positive_gold_withholds_precision_instead_of_marking_unjudged_negative() -> None:
    corpus = (
        _entry("unjudged", "alpha beta gamma"),
        _entry("gold", "alpha beta"),
    )
    case = _positive_case("q1", "alpha beta gamma", (_judgment("gold"),))

    result = evaluate_benchmark((case,), corpus, k=5)

    assert [ref.entry_id for ref in result.cases[0].retrieved_refs] == [
        "unjudged",
        "gold",
    ]
    assert result.precision_at_k is None
    assert result.precision_unavailable_reason == (
        "precision requires exhaustive relevance judgments; positive_only cases contain unjudged entries"
    )
    assert result.cases[0].useful_found_count == 1


def test_macro_recall_averages_per_positive_case_not_raw_judgment_count() -> None:
    corpus = (
        _entry("a", "alpha beta"),
        _entry("b", "beta gamma"),
        _entry("c", "delta epsilon"),
    )
    case_one = _positive_case(
        "q1",
        "alpha beta gamma",
        (_judgment("a"), _judgment("b")),
    )
    case_two = _positive_case(
        "q2",
        "theta zeta",
        (_judgment("c"),),
    )

    result = evaluate_benchmark((case_one, case_two), corpus, k=1)

    assert result.cases[0].recall_at_k == 0.5
    assert result.cases[1].recall_at_k == 0.0
    assert result.recall_at_k == 0.25


def test_invalid_k_is_rejected() -> None:
    case = _positive_case("q1", "alpha", (_judgment("gold"),))
    corpus = (_entry("gold", "alpha"),)

    try:
        evaluate_benchmark((case,), corpus, k=0)
    except ValueError as exc:
        assert str(exc) == "k must be at least 1"
    else:
        raise AssertionError("expected ValueError")
