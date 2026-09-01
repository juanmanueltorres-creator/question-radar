from __future__ import annotations

from dataclasses import dataclass

from question_radar.benchmark_io import GoldCase, GoldJudgment
from question_radar.retrieval import CorpusEntry, retrieve_candidates


EVALUATION_VERSION = "v0.8"
RETRIEVAL_VERSION = "v0.7"
PRECISION_UNAVAILABLE_REASON = (
    "precision requires exhaustive relevance judgments; positive_only cases contain unjudged entries"
)


@dataclass(frozen=True, slots=True)
class RetrievedRef:
    source_version: str
    entry_id: str


@dataclass(frozen=True, slots=True)
class FoundJudgment:
    source_version: str
    entry_id: str
    relevance: str
    rank: int


@dataclass(frozen=True, slots=True)
class CaseEvaluation:
    candidate_id: str
    question: str
    judgment_scope: str
    expected_abstention: bool
    abstained: bool
    abstention_reason: str | None
    retrieved_refs: tuple[RetrievedRef, ...]
    useful_gold_count: int
    useful_found_count: int
    found_judgments: tuple[FoundJudgment, ...]
    hit_at_k: bool | None
    recall_at_k: float | None
    first_useful_rank: int | None
    reciprocal_rank: float
    false_abstention: bool
    correct_expected_abstention: bool | None


@dataclass(frozen=True, slots=True)
class BenchmarkEvaluation:
    evaluation_version: str
    retrieval_version: str
    benchmark_name: str
    gold_version: str
    corpus_size: int
    k: int
    cases: tuple[CaseEvaluation, ...]
    positive_case_count: int
    hit_rate_at_k: float
    recall_at_k: float
    mrr: float
    false_abstentions: int
    abstention_control_count: int
    correct_abstentions: int
    false_non_abstentions: int
    abstention_accuracy: float | None
    precision_at_k: float | None
    precision_unavailable_reason: str | None


def _useful_judgments(case: GoldCase) -> tuple[GoldJudgment, ...]:
    return tuple(
        judgment
        for judgment in case.judgments
        if judgment.relevance in {"relevant", "partially_relevant"}
    )


def _round_metric(value: float) -> float:
    return round(value, 6)


def _evaluate_case(
    case: GoldCase,
    corpus: tuple[CorpusEntry, ...],
    k: int,
) -> CaseEvaluation:
    pack = retrieve_candidates(case.question, corpus, limit=k)
    retrieved_refs = tuple(
        RetrievedRef(
            source_version=result.entry.source_version,
            entry_id=result.entry.id,
        )
        for result in pack.results
    )

    useful = _useful_judgments(case)
    useful_by_ref = {
        (judgment.source_version, judgment.entry_id): judgment
        for judgment in useful
    }
    found: list[FoundJudgment] = []
    for rank, ref in enumerate(retrieved_refs, start=1):
        judgment = useful_by_ref.get((ref.source_version, ref.entry_id))
        if judgment is None:
            continue
        found.append(
            FoundJudgment(
                source_version=judgment.source_version,
                entry_id=judgment.entry_id,
                relevance=judgment.relevance,
                rank=rank,
            )
        )

    useful_gold_count = len(useful)
    useful_found_count = len(found)
    positive = useful_gold_count > 0
    first_useful_rank = min((item.rank for item in found), default=None)
    reciprocal_rank = (
        _round_metric(1.0 / first_useful_rank)
        if first_useful_rank is not None
        else 0.0
    )
    recall = (
        _round_metric(useful_found_count / useful_gold_count)
        if positive
        else None
    )
    false_abstention = positive and pack.abstained
    correct_expected_abstention = (
        pack.abstained if case.expected_abstention else None
    )

    return CaseEvaluation(
        candidate_id=case.candidate_id,
        question=case.question,
        judgment_scope=case.judgment_scope,
        expected_abstention=case.expected_abstention,
        abstained=pack.abstained,
        abstention_reason=pack.abstention_reason,
        retrieved_refs=retrieved_refs,
        useful_gold_count=useful_gold_count,
        useful_found_count=useful_found_count,
        found_judgments=tuple(found),
        hit_at_k=(useful_found_count > 0) if positive else None,
        recall_at_k=recall,
        first_useful_rank=first_useful_rank,
        reciprocal_rank=reciprocal_rank,
        false_abstention=false_abstention,
        correct_expected_abstention=correct_expected_abstention,
    )


def _precision_for_exhaustive_cases(
    cases: tuple[GoldCase, ...],
    evaluations: tuple[CaseEvaluation, ...],
) -> float:
    useful_refs_by_candidate = {
        case.candidate_id: {
            (judgment.source_version, judgment.entry_id)
            for judgment in _useful_judgments(case)
        }
        for case in cases
    }
    useful_retrieved = 0
    total_retrieved = 0
    for evaluation in evaluations:
        useful_refs = useful_refs_by_candidate[evaluation.candidate_id]
        for ref in evaluation.retrieved_refs:
            total_retrieved += 1
            if (ref.source_version, ref.entry_id) in useful_refs:
                useful_retrieved += 1
    if total_retrieved == 0:
        any_useful = any(useful_refs_by_candidate.values())
        return 0.0 if any_useful else 1.0
    return _round_metric(useful_retrieved / total_retrieved)


def evaluate_benchmark(
    gold_cases: tuple[GoldCase, ...],
    corpus: tuple[CorpusEntry, ...],
    k: int = 5,
    *,
    benchmark_name: str = "benchmark",
    gold_version: str = "gold",
) -> BenchmarkEvaluation:
    if k < 1:
        raise ValueError("k must be at least 1")

    evaluations = tuple(
        _evaluate_case(case, corpus, k)
        for case in gold_cases
    )
    positive = tuple(
        evaluation
        for evaluation in evaluations
        if evaluation.useful_gold_count > 0
    )
    controls = tuple(
        evaluation
        for evaluation in evaluations
        if evaluation.expected_abstention
    )

    positive_count = len(positive)
    hit_rate = _round_metric(
        sum(bool(item.hit_at_k) for item in positive) / positive_count
    ) if positive_count else 0.0
    recall = _round_metric(
        sum(item.recall_at_k or 0.0 for item in positive) / positive_count
    ) if positive_count else 0.0
    mrr = _round_metric(
        sum(item.reciprocal_rank for item in positive) / positive_count
    ) if positive_count else 0.0

    control_count = len(controls)
    correct_abstentions = sum(item.abstained for item in controls)
    false_non_abstentions = control_count - correct_abstentions
    abstention_accuracy = (
        _round_metric(correct_abstentions / control_count)
        if control_count
        else None
    )

    has_sparse = any(case.judgment_scope == "positive_only" for case in gold_cases)
    precision = None if has_sparse else _precision_for_exhaustive_cases(gold_cases, evaluations)
    precision_reason = PRECISION_UNAVAILABLE_REASON if has_sparse else None

    return BenchmarkEvaluation(
        evaluation_version=EVALUATION_VERSION,
        retrieval_version=RETRIEVAL_VERSION,
        benchmark_name=benchmark_name,
        gold_version=gold_version,
        corpus_size=len(corpus),
        k=k,
        cases=evaluations,
        positive_case_count=positive_count,
        hit_rate_at_k=hit_rate,
        recall_at_k=recall,
        mrr=mrr,
        false_abstentions=sum(item.false_abstention for item in evaluations),
        abstention_control_count=control_count,
        correct_abstentions=correct_abstentions,
        false_non_abstentions=false_non_abstentions,
        abstention_accuracy=abstention_accuracy,
        precision_at_k=precision,
        precision_unavailable_reason=precision_reason,
    )
