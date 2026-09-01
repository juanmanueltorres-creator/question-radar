from __future__ import annotations

import json

from question_radar.benchmark_eval import evaluate_benchmark
from question_radar.benchmark_export import (
    EVALUATION_BOUNDARY,
    render_benchmark_json,
    render_benchmark_markdown,
)
from question_radar.benchmark_io import GoldCase, GoldJudgment
from question_radar.retrieval import CorpusEntry


def _evaluation():
    corpus = (
        CorpusEntry("gold", "alpha beta", "v0.2", "profile", None),
        CorpusEntry("noise", "alpha gamma", "v0.2", "profile", None),
    )
    case = GoldCase(
        candidate_id="q1",
        question="alpha beta",
        judgment_scope="positive_only",
        expected_abstention=False,
        judgments=(GoldJudgment("gold", "v0.2", "relevant"),),
    )
    return evaluate_benchmark(
        (case,),
        corpus,
        k=5,
        benchmark_name="blind-test",
        gold_version="gold-v1",
    )


def test_json_export_is_deterministic_and_exposes_sparse_precision_boundary() -> None:
    evaluation = _evaluation()
    first = render_benchmark_json(evaluation)
    second = render_benchmark_json(evaluation)

    assert first == second
    assert first.endswith("\n")
    payload = json.loads(first)
    assert payload["evaluation_version"] == "v0.8"
    assert payload["retrieval_version"] == "v0.7"
    assert payload["benchmark_name"] == "blind-test"
    assert payload["gold_version"] == "gold-v1"
    assert payload["metrics"]["precision_at_k"] is None
    assert payload["metrics"]["precision_unavailable_reason"].startswith(
        "precision requires exhaustive relevance judgments"
    )
    assert payload["evaluation_boundary"] == EVALUATION_BOUNDARY
    assert payload["cases"][0]["retrieved_refs"][0] == {
        "entry_id": "gold",
        "source_version": "v0.2",
    }
    assert payload["cases"][0]["found_judgments"][0] == {
        "entry_id": "gold",
        "rank": 1,
        "relevance": "relevant",
        "source_version": "v0.2",
    }


def test_markdown_export_contains_metrics_cases_and_exact_boundary() -> None:
    text = render_benchmark_markdown(_evaluation())

    assert text.startswith("# Benchmark Evaluation — blind-test\n")
    assert "## Aggregate Metrics" in text
    assert "- Hit Rate@5: 1.0" in text
    assert "- Recall@5: 1.0" in text
    assert "- MRR: 1.0" in text
    assert "- Precision@5: unavailable" in text
    assert "## Case Results" in text
    assert "### q1" in text
    assert "v0.2:gold" in text
    assert "## Evaluation Boundary" in text
    assert EVALUATION_BOUNDARY in text


def test_json_keys_are_sorted_for_stable_baseline_diffs() -> None:
    text = render_benchmark_json(_evaluation())
    first_object_lines = text.splitlines()
    assert first_object_lines[1].lstrip().startswith('"benchmark_name"')
