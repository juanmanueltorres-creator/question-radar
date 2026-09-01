import json
from pathlib import Path

from question_radar.retrieval import CorpusEntry, retrieve_candidates


ROOT = Path(__file__).resolve().parents[1]
BLIND_DECISION = ROOT / "corpus" / "blind-decision-uncertainty-2026-09-01.jsonl"
BLIND_SYSTEM = ROOT / "corpus" / "blind-system-trust-2026-09-01.jsonl"
V02 = ROOT / "corpus" / "anti-ia-calibration-v0.2.jsonl"
V04_QUESTIONS = ROOT / "corpus" / "question-lineage-v0.4.jsonl"
V04_SOFTWARE = ROOT / "corpus" / "chat-2026-08-31-software-recruiting-ai-lineage-v0.4.jsonl"


def _jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _unified_public_corpus() -> tuple[CorpusEntry, ...]:
    entries: list[CorpusEntry] = []
    for profile in _jsonl(V02):
        entries.append(
            CorpusEntry(
                id=profile["id"],
                question=profile["question"],
                source_version="v0.2",
                source_kind="profile",
                provenance=None,
            )
        )
    for path in (V04_QUESTIONS, V04_SOFTWARE):
        for record in _jsonl(path):
            if record.get("record_type") != "node":
                continue
            entries.append(
                CorpusEntry(
                    id=record["id"],
                    question=record["question"],
                    source_version="v0.4",
                    source_kind="lineage_node",
                    provenance=record.get("source_ref"),
                )
            )
    return tuple(entries)


def _top_ids(question: str, limit: int = 5) -> list[str]:
    pack = retrieve_candidates(question, _unified_public_corpus(), limit=limit)
    return [result.entry.id for result in pack.results]


def test_blind_decision_benchmark_preserves_exact_25_questions():
    records = _jsonl(BLIND_DECISION)

    assert len(records) == 25
    assert records[0]["id"] == "decision-blind-2026-09-01-001"
    assert records[-1]["id"] == "decision-blind-2026-09-01-025"
    assert records[6]["question"] == (
        "¿Qué pesa más cuando el tiempo es limitado: la probabilidad de equivocarse "
        "o el costo de no actuar?"
    )


def test_q7_retrieves_existing_cost_of_action_question_in_top_five():
    q7 = _jsonl(BLIND_DECISION)[6]["question"]

    pack = retrieve_candidates(q7, _unified_public_corpus(), limit=5)
    ids = [result.entry.id for result in pack.results]

    assert "qv2-cal-013" in ids
    matching = next(result for result in pack.results if result.entry.id == "qv2-cal-013")
    assert {"costo", "actuar"}.issubset(set(matching.matched_query_tokens))
    assert matching.bm25_score > 0


def test_blind_system_trust_benchmark_preserves_exact_24_questions():
    records = _jsonl(BLIND_SYSTEM)

    assert len(records) == 24
    assert records[0]["id"] == "system-trust-blind-2026-09-01-001"
    assert records[-1]["id"] == "system-trust-blind-2026-09-01-024"
    assert records[13]["question"] == (
        "¿Qué debería significar que un sistema funciona “bien” cuando los costos de "
        "equivocarse no son iguales para todos los casos?"
    )


def test_system_trust_q1_retrieves_existing_system_understanding_question_top_five():
    q1 = _jsonl(BLIND_SYSTEM)[0]["question"]
    assert "vault-2026-08-31-001" in _top_ids(q1)


def test_system_trust_q14_retrieves_cost_of_action_question_top_five():
    q14 = _jsonl(BLIND_SYSTEM)[13]["question"]
    assert "qv2-cal-013" in _top_ids(q14)


def test_system_trust_q16_is_preserved_as_diagnostic_not_abstention_gold():
    q16 = _jsonl(BLIND_SYSTEM)[15]["question"]
    assert q16 == (
        "¿Hasta qué punto una recomendación automática modifica la decisión antes incluso "
        "de que la persona empiece a evaluarla?"
    )


def test_system_trust_q24_is_preserved_as_semantic_morphology_negative_control():
    q24 = _jsonl(BLIND_SYSTEM)[23]["question"]
    assert q24 == (
        "¿El problema principal es que las personas no entienden los sistemas que usan, o "
        "que tampoco pueden comprender por completo muchas de las decisiones complejas que "
        "toman sin ellos?"
    )
