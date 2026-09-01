from __future__ import annotations

import json

from question_radar.benchmark_eval import BenchmarkEvaluation, CaseEvaluation


EVALUATION_BOUNDARY = (
    "Gold judgments encode editorial review expectations, not semantic equivalence or lineage. "
    "Unjudged entries in positive-only cases are unknown, not negative."
)


def _case_payload(case: CaseEvaluation) -> dict[str, object]:
    return {
        "abstained": case.abstained,
        "abstention_reason": case.abstention_reason,
        "candidate_id": case.candidate_id,
        "correct_expected_abstention": case.correct_expected_abstention,
        "expected_abstention": case.expected_abstention,
        "false_abstention": case.false_abstention,
        "first_useful_rank": case.first_useful_rank,
        "found_judgments": [
            {
                "entry_id": item.entry_id,
                "rank": item.rank,
                "relevance": item.relevance,
                "source_version": item.source_version,
            }
            for item in case.found_judgments
        ],
        "hit_at_k": case.hit_at_k,
        "judgment_scope": case.judgment_scope,
        "question": case.question,
        "recall_at_k": case.recall_at_k,
        "reciprocal_rank": case.reciprocal_rank,
        "retrieved_refs": [
            {
                "entry_id": ref.entry_id,
                "source_version": ref.source_version,
            }
            for ref in case.retrieved_refs
        ],
        "useful_found_count": case.useful_found_count,
        "useful_gold_count": case.useful_gold_count,
    }


def _payload(evaluation: BenchmarkEvaluation) -> dict[str, object]:
    return {
        "benchmark_name": evaluation.benchmark_name,
        "cases": [_case_payload(case) for case in evaluation.cases],
        "corpus_size": evaluation.corpus_size,
        "evaluation_boundary": EVALUATION_BOUNDARY,
        "evaluation_version": evaluation.evaluation_version,
        "gold_version": evaluation.gold_version,
        "k": evaluation.k,
        "metrics": {
            "abstention_accuracy": evaluation.abstention_accuracy,
            "abstention_control_count": evaluation.abstention_control_count,
            "correct_abstentions": evaluation.correct_abstentions,
            "false_abstentions": evaluation.false_abstentions,
            "false_non_abstentions": evaluation.false_non_abstentions,
            "hit_rate_at_k": evaluation.hit_rate_at_k,
            "mrr": evaluation.mrr,
            "positive_case_count": evaluation.positive_case_count,
            "precision_at_k": evaluation.precision_at_k,
            "precision_unavailable_reason": evaluation.precision_unavailable_reason,
            "recall_at_k": evaluation.recall_at_k,
        },
        "retrieval_version": evaluation.retrieval_version,
    }


def render_benchmark_json(evaluation: BenchmarkEvaluation) -> str:
    return json.dumps(
        _payload(evaluation),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def _display(value: object) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def render_benchmark_markdown(evaluation: BenchmarkEvaluation) -> str:
    lines = [
        f"# Benchmark Evaluation — {evaluation.benchmark_name}",
        "",
        f"- Evaluation version: {evaluation.evaluation_version}",
        f"- Retrieval version: {evaluation.retrieval_version}",
        f"- Gold version: {evaluation.gold_version}",
        f"- Corpus size: {evaluation.corpus_size}",
        f"- k: {evaluation.k}",
        "",
        "## Aggregate Metrics",
        "",
        f"- Hit Rate@{evaluation.k}: {evaluation.hit_rate_at_k}",
        f"- Recall@{evaluation.k}: {evaluation.recall_at_k}",
        f"- MRR: {evaluation.mrr}",
        (
            f"- Precision@{evaluation.k}: {evaluation.precision_at_k}"
            if evaluation.precision_at_k is not None
            else f"- Precision@{evaluation.k}: unavailable"
        ),
        f"- False abstentions: {evaluation.false_abstentions}",
        f"- Abstention controls: {evaluation.abstention_control_count}",
        f"- Correct abstentions: {evaluation.correct_abstentions}",
        f"- False non-abstentions: {evaluation.false_non_abstentions}",
        f"- Abstention accuracy: {_display(evaluation.abstention_accuracy)}",
    ]
    if evaluation.precision_unavailable_reason:
        lines.append(f"- Precision note: {evaluation.precision_unavailable_reason}")

    lines.extend(["", "## Case Results", ""])
    for case in evaluation.cases:
        refs = ", ".join(
            f"{ref.source_version}:{ref.entry_id}"
            for ref in case.retrieved_refs
        ) or "none"
        found = ", ".join(
            f"{item.source_version}:{item.entry_id}@{item.rank} ({item.relevance})"
            for item in case.found_judgments
        ) or "none"
        lines.extend(
            [
                f"### {case.candidate_id}",
                "",
                case.question,
                "",
                f"- Scope: {case.judgment_scope}",
                f"- Expected abstention: {_display(case.expected_abstention)}",
                f"- Abstained: {_display(case.abstained)}",
                f"- Retrieved: {refs}",
                f"- Useful gold found: {case.useful_found_count}/{case.useful_gold_count}",
                f"- Found judgments: {found}",
                f"- Recall@{evaluation.k}: {_display(case.recall_at_k)}",
                f"- First useful rank: {_display(case.first_useful_rank)}",
                f"- Reciprocal rank: {case.reciprocal_rank}",
                f"- False abstention: {_display(case.false_abstention)}",
                "",
            ]
        )

    lines.extend(
        [
            "## Evaluation Boundary",
            "",
            EVALUATION_BOUNDARY,
            "",
        ]
    )
    return "\n".join(lines)
