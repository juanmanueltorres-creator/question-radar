from __future__ import annotations

from pathlib import Path

from question_radar.benchmark_eval import evaluate_benchmark
from question_radar.benchmark_export import render_benchmark_json
from question_radar.benchmark_io import (
    load_benchmark,
    load_evaluation_corpus,
    load_gold,
)


BENCHMARK_PATH = Path("corpus/blind-representations-2026-09-01.jsonl")
GOLD_PATH = Path("corpus/gold/blind-representations-2026-09-01-gold-v1.jsonl")
BASELINE_PATH = Path("corpus/baselines/blind-representations-2026-09-01-v0.7-baseline.json")
CORPUS_PATHS = (
    Path("corpus/anti-ia-calibration-v0.2.jsonl"),
    Path("corpus/question-lineage-v0.4.jsonl"),
    Path("corpus/chat-2026-08-31-software-recruiting-ai-lineage-v0.4.jsonl"),
)


def _actual_baseline() -> str:
    benchmark = load_benchmark(BENCHMARK_PATH)
    gold = load_gold(GOLD_PATH, benchmark)
    corpus = load_evaluation_corpus(CORPUS_PATHS)
    evaluation = evaluate_benchmark(
        gold,
        corpus,
        k=5,
        benchmark_name=BENCHMARK_PATH.stem,
        gold_version=GOLD_PATH.stem,
    )
    return render_benchmark_json(evaluation)


def test_committed_v07_baseline_matches_current_frozen_evaluation_byte_for_byte() -> None:
    expected = BASELINE_PATH.read_text(encoding="utf-8")
    actual = _actual_baseline()

    assert expected == actual


def test_v07_baseline_is_explicitly_pre_semantic_and_sparse() -> None:
    actual = _actual_baseline()

    assert '"retrieval_version": "v0.7"' in actual
    assert '"evaluation_version": "v0.8"' in actual
    assert '"corpus_size": 51' in actual
    assert '"precision_at_k": null' in actual
    assert "semantic equivalence or lineage" in actual
