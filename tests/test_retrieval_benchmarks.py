import json
from pathlib import Path

from question_radar.retrieval import CorpusEntry, retrieve_candidates


ROOT = Path(__file__).resolve().parents[1]
BLIND = ROOT / "corpus" / "blind-decision-uncertainty-2026-09-01.jsonl"
V02 = ROOT / "corpus" / "anti-ia-calibration-v0.2.jsonl"


def _jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_blind_decision_benchmark_preserves_exact_25_questions():
    records = _jsonl(BLIND)

    assert len(records) == 25
    assert records[0]["id"] == "decision-blind-2026-09-01-001"
    assert records[-1]["id"] == "decision-blind-2026-09-01-025"
    assert records[6]["question"] == (
        "¿Qué pesa más cuando el tiempo es limitado: la probabilidad de equivocarse "
        "o el costo de no actuar?"
    )


def test_q7_retrieves_existing_cost_of_action_question_in_top_five():
    profiles = _jsonl(V02)
    corpus = tuple(
        CorpusEntry(
            id=profile["id"],
            question=profile["question"],
            source_version="v0.2",
            source_kind="profile",
            provenance=None,
        )
        for profile in profiles
    )
    q7 = _jsonl(BLIND)[6]["question"]

    pack = retrieve_candidates(q7, corpus, limit=5)
    ids = [result.entry.id for result in pack.results]

    assert "qv2-cal-013" in ids
    matching = next(result for result in pack.results if result.entry.id == "qv2-cal-013")
    assert {"costo", "actuar"}.issubset(set(matching.matched_query_tokens))
    assert matching.bm25_score > 0
