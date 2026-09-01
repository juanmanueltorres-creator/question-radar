from __future__ import annotations

from pathlib import Path

import pytest

from question_radar.benchmark_io import (
    load_benchmark,
    load_evaluation_corpus,
    load_gold,
)


BENCHMARK = Path("corpus/blind-representations-2026-09-01.jsonl")
GOLD = Path("corpus/gold/blind-representations-2026-09-01-gold-v1.jsonl")
CORPUS_PATHS = (
    Path("corpus/anti-ia-calibration-v0.2.jsonl"),
    Path("corpus/question-lineage-v0.4.jsonl"),
    Path("corpus/chat-2026-08-31-software-recruiting-ai-lineage-v0.4.jsonl"),
)


def test_load_benchmark_preserves_frozen_order_and_text() -> None:
    rows = load_benchmark(BENCHMARK)
    assert len(rows) == 23
    assert rows[0].id == "representation-blind-2026-09-01-001"
    assert rows[0].question.startswith("¿Qué se pierde exactamente")
    assert rows[-1].id == "representation-blind-2026-09-01-023"


def test_load_gold_joins_questions_without_treating_absence_as_negative() -> None:
    benchmark = load_benchmark(BENCHMARK)
    gold = load_gold(GOLD, benchmark)
    assert len(gold) == 8
    q1 = gold[0]
    assert q1.question == benchmark[0].question
    assert q1.judgment_scope == "positive_only"
    assert [judgment.relevance for judgment in q1.judgments] == [
        "relevant",
        "partially_relevant",
    ]
    assert all(judgment.relevance != "not_relevant" for judgment in q1.judgments)


def test_load_evaluation_corpus_reconstructs_51_canonical_entries() -> None:
    corpus = load_evaluation_corpus(CORPUS_PATHS)
    assert len(corpus) == 51
    assert sum(entry.source_version == "v0.2" for entry in corpus) == 25
    assert sum(entry.source_version == "v0.4" for entry in corpus) == 26
    assert ("v0.2", "qv2-cal-019") in {
        (entry.source_version, entry.id) for entry in corpus
    }
    assert ("v0.4", "vault-2026-08-31-008") in {
        (entry.source_version, entry.id) for entry in corpus
    }
    assert all(entry.source_kind == ("profile" if entry.source_version == "v0.2" else "lineage_node") for entry in corpus)


def test_load_evaluation_corpus_ignores_v04_relation_rows() -> None:
    corpus = load_evaluation_corpus(CORPUS_PATHS)
    assert not any(entry.id.startswith("rel-") for entry in corpus)


def test_loaders_fail_closed_on_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text('{"id":', encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        load_benchmark(path)


def test_load_benchmark_rejects_duplicate_ids(tmp_path: Path) -> None:
    path = tmp_path / "benchmark.jsonl"
    path.write_text(
        '{"id":"x","question":"one"}\n{"id":"x","question":"two"}\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate benchmark id"):
        load_benchmark(path)


def test_load_gold_rejects_unknown_candidate(tmp_path: Path) -> None:
    benchmark = load_benchmark(BENCHMARK)
    path = tmp_path / "gold.jsonl"
    path.write_text(
        '{"candidate_id":"missing","judgment_scope":"positive_only","expected_abstention":false,"judgments":[]}\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown benchmark candidate"):
        load_gold(path, benchmark)


def test_load_gold_rejects_invalid_scope_and_relevance(tmp_path: Path) -> None:
    benchmark = load_benchmark(BENCHMARK)
    candidate_id = benchmark[0].id
    scope_path = tmp_path / "scope.jsonl"
    scope_path.write_text(
        f'{{"candidate_id":"{candidate_id}","judgment_scope":"all","expected_abstention":false,"judgments":[]}}\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="judgment_scope"):
        load_gold(scope_path, benchmark)

    relevance_path = tmp_path / "relevance.jsonl"
    relevance_path.write_text(
        f'{{"candidate_id":"{candidate_id}","judgment_scope":"positive_only","expected_abstention":false,"judgments":[{{"entry_id":"x","source_version":"v0.2","relevance":"maybe"}}]}}\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="relevance"):
        load_gold(relevance_path, benchmark)


def test_load_gold_rejects_duplicate_candidate_rows(tmp_path: Path) -> None:
    benchmark = load_benchmark(BENCHMARK)
    candidate_id = benchmark[0].id
    row = f'{{"candidate_id":"{candidate_id}","judgment_scope":"positive_only","expected_abstention":false,"judgments":[]}}\n'
    path = tmp_path / "gold.jsonl"
    path.write_text(row + row, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate gold candidate"):
        load_gold(path, benchmark)
