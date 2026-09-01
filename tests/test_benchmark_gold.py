from __future__ import annotations

import json
from pathlib import Path


BENCHMARK_PATH = Path("corpus/blind-representations-2026-09-01.jsonl")
GOLD_PATH = Path("corpus/gold/blind-representations-2026-09-01-gold-v1.jsonl")


def _rows(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_blind_representations_benchmark_is_frozen_with_23_unique_questions() -> None:
    rows = _rows(BENCHMARK_PATH)
    assert len(rows) == 23
    assert len({row["id"] for row in rows}) == 23
    assert rows[0] == {
        "id": "representation-blind-2026-09-01-001",
        "question": "¿Qué se pierde exactamente cuando una situación compleja se convierte en una métrica, un mapa, una categoría o un indicador?",
    }
    assert rows[-1] == {
        "id": "representation-blind-2026-09-01-023",
        "question": "¿En qué situaciones una representación imperfecta puede ser más útil que intentar representar la realidad con mayor fidelidad?",
    }


def test_gold_v1_freezes_only_the_eight_preselected_cases() -> None:
    rows = _rows(GOLD_PATH)
    assert len(rows) == 8
    assert [row["candidate_id"] for row in rows] == [
        "representation-blind-2026-09-01-001",
        "representation-blind-2026-09-01-010",
        "representation-blind-2026-09-01-011",
        "representation-blind-2026-09-01-012",
        "representation-blind-2026-09-01-013",
        "representation-blind-2026-09-01-016",
        "representation-blind-2026-09-01-017",
        "representation-blind-2026-09-01-022",
    ]


def test_gold_v1_judgments_match_the_preregistered_editorial_contract() -> None:
    by_id = {row["candidate_id"]: row for row in _rows(GOLD_PATH)}

    assert by_id["representation-blind-2026-09-01-001"] == {
        "candidate_id": "representation-blind-2026-09-01-001",
        "judgment_scope": "positive_only",
        "expected_abstention": False,
        "judgments": [
            {"entry_id": "qv2-cal-019", "source_version": "v0.2", "relevance": "relevant"},
            {"entry_id": "vault-2026-08-31-008", "source_version": "v0.4", "relevance": "partially_relevant"},
        ],
    }
    assert by_id["representation-blind-2026-09-01-010"]["judgments"] == [
        {"entry_id": "qv2-cal-015", "source_version": "v0.2", "relevance": "relevant"}
    ]
    assert by_id["representation-blind-2026-09-01-011"]["judgments"] == [
        {"entry_id": "qv2-cal-020", "source_version": "v0.2", "relevance": "relevant"},
        {"entry_id": "qv2-cal-021", "source_version": "v0.2", "relevance": "relevant"},
    ]
    assert by_id["representation-blind-2026-09-01-012"]["judgments"] == [
        {"entry_id": "qv2-cal-022", "source_version": "v0.2", "relevance": "relevant"}
    ]
    assert by_id["representation-blind-2026-09-01-016"]["judgments"] == [
        {"entry_id": "chat-2026-08-29-010", "source_version": "v0.4", "relevance": "relevant"}
    ]
    assert by_id["representation-blind-2026-09-01-017"]["judgments"] == [
        {"entry_id": "chat-2026-08-29-006", "source_version": "v0.4", "relevance": "partially_relevant"}
    ]

    for candidate_id in (
        "representation-blind-2026-09-01-013",
        "representation-blind-2026-09-01-022",
    ):
        assert by_id[candidate_id] == {
            "candidate_id": candidate_id,
            "judgment_scope": "exhaustive",
            "expected_abstention": True,
            "judgments": [],
        }


def test_gold_v1_uses_only_allowed_contract_values() -> None:
    allowed_scopes = {"positive_only", "exhaustive"}
    allowed_relevance = {"relevant", "partially_relevant", "not_relevant"}
    for row in _rows(GOLD_PATH):
        assert row["judgment_scope"] in allowed_scopes
        assert isinstance(row["expected_abstention"], bool)
        for judgment in row["judgments"]:
            assert judgment["source_version"] in {"v0.2", "v0.4"}
            assert judgment["relevance"] in allowed_relevance
