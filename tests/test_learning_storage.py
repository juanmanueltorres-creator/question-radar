import sqlite3

import pytest

from question_radar.learning import LearningObservation
from question_radar.learning_storage import LearningObservationStore
from question_radar.models import QuestionEvaluation
from question_radar.profile_storage import QuestionProfileStore
from question_radar.profiles import QuestionProfile
from question_radar.storage import QuestionStore


def observation(
    identifier: str = "learning-store-001",
    evidence: list[str] | None = None,
) -> LearningObservation:
    return LearningObservation.from_dict(
        {
            "id": identifier,
            "concept": "question_evaluation_models",
            "gap_type": "connection",
            "state": "consolidating",
            "confidence": "medium",
            "evidence_question_ids": evidence or ["q-3", "q-1", "q-2"],
            "interpretation": "Stored evidence supports a cautious learning hypothesis.",
            "suggested_next_step": "Test the distinction in a new domain.",
            "created_at": "2026-08-29T18:30:00-03:00",
            "updated_at": "2026-08-29T18:35:00-03:00",
        }
    )


def evaluation(identifier: str) -> QuestionEvaluation:
    return QuestionEvaluation.from_dict(
        {
            "id": identifier,
            "question": "Historical v0.1 question?",
            "clarity": 5,
            "depth": 5,
            "investigability": 5,
            "assumption_challenge": 5,
            "connections": 5,
            "score": 100,
            "strengths": "Historical record.",
            "gap": "None for test.",
            "next_question": "What next?",
            "topic": None,
            "evaluator": "manual",
            "rubric_version": "v0.1",
            "created_at": "2026-08-29T18:00:00-03:00",
        }
    )


def profile(identifier: str) -> QuestionProfile:
    return QuestionProfile.from_dict(
        {
            "id": identifier,
            "question": f"Question {identifier}?",
            "question_type": "factual_conceptual",
            "readiness": "ready_to_answer",
            "clarity": 5,
            "boundedness": 5,
            "investigability": 5,
            "epistemic_openness": 5,
            "purpose_fit": 5,
            "formulation_score": 100,
            "depth": 2,
            "connections": 3,
            "generativity": 3,
            "strengths": "Useful for its declared purpose.",
            "gap": "Needs domain context.",
            "assumptions": "Carries one explicit assumption.",
            "evidence_required": "Relevant evidence or conceptual analysis.",
            "next_question": "What should be checked next?",
            "topic": None,
            "evaluator": "manual",
            "rubric_version": "v0.2",
            "created_at": "2026-08-29T18:26:00-03:00",
        }
    )


def test_round_trip_preserves_unknown_source_ids_and_order(tmp_path):
    store = LearningObservationStore(tmp_path / "questions.sqlite3")
    item = observation(evidence=["not-loaded-3", "not-loaded-1", "not-loaded-2"])
    store.insert(item)
    assert store.get(item.id) == item
    assert store.list_all() == [item]


def test_normalized_evidence_positions_are_zero_based(tmp_path):
    db = tmp_path / "questions.sqlite3"
    store = LearningObservationStore(db)
    store.insert(observation(evidence=["q-3", "q-1", "q-2"]))
    with sqlite3.connect(db) as connection:
        rows = connection.execute(
            "SELECT position, evidence_question_id "
            "FROM learning_observation_evidence_v03 ORDER BY position"
        ).fetchall()
    assert rows == [(0, "q-3"), (1, "q-1"), (2, "q-2")]


def test_store_uses_separate_normalized_tables(tmp_path):
    db = tmp_path / "questions.sqlite3"
    LearningObservationStore(db).insert(observation())
    with sqlite3.connect(db) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert "learning_observations_v03" in tables
    assert "learning_observation_evidence_v03" in tables
    assert "question_profiles_v02" not in tables


def test_duplicate_observation_id_is_rejected(tmp_path):
    store = LearningObservationStore(tmp_path / "questions.sqlite3")
    store.insert(observation())
    with pytest.raises(ValueError, match="already exists|violates"):
        store.insert(observation())


def test_get_missing_returns_none(tmp_path):
    store = LearningObservationStore(tmp_path / "questions.sqlite3")
    assert store.get("missing") is None


def test_insert_many_is_atomic(tmp_path):
    db = tmp_path / "questions.sqlite3"
    store = LearningObservationStore(db)
    first = observation("same")
    duplicate = observation("same", evidence=["other"])
    with pytest.raises(ValueError):
        store.insert_many([first, duplicate])
    assert store.list_all() == []


def test_v01_v02_v03_can_share_same_database_and_id(tmp_path):
    db = tmp_path / "questions.sqlite3"
    identifier = "shared-id"
    old = evaluation(identifier)
    typed = profile(identifier)
    learning = observation(identifier, evidence=[identifier])

    QuestionStore(db).insert(old)
    QuestionProfileStore(db).insert(typed)
    LearningObservationStore(db).insert(learning)

    assert QuestionStore(db).list_all() == [old]
    assert QuestionProfileStore(db).list_all() == [typed]
    assert LearningObservationStore(db).list_all() == [learning]
