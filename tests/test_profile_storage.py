import sqlite3

import pytest

from question_radar.models import QuestionEvaluation
from question_radar.profile_storage import QuestionProfileStore
from question_radar.profiles import QuestionProfile
from question_radar.storage import QuestionStore


def profile(identifier: str, question_type: str = "factual_conceptual", score: int = 100) -> QuestionProfile:
    value = score // 20
    return QuestionProfile.from_dict(
        {
            "id": identifier,
            "question": f"Question {identifier}?",
            "question_type": question_type,
            "readiness": "ready_to_answer" if question_type == "factual_conceptual" else "ready_to_investigate",
            "clarity": value,
            "boundedness": value,
            "investigability": value,
            "epistemic_openness": value,
            "purpose_fit": value,
            "formulation_score": score,
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


def test_profile_can_be_inserted_and_read(tmp_path):
    store = QuestionProfileStore(tmp_path / "questions.sqlite3")
    item = profile("p-001")
    store.insert(item)
    assert store.list_all() == [item]


def test_profile_store_uses_separate_table(tmp_path):
    db = tmp_path / "questions.sqlite3"
    QuestionProfileStore(db).insert(profile("p-001"))
    with sqlite3.connect(db) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "question_profiles_v02" in tables
    assert "evaluations" not in tables


def test_duplicate_profile_id_is_rejected(tmp_path):
    store = QuestionProfileStore(tmp_path / "questions.sqlite3")
    item = profile("same")
    store.insert(item)
    with pytest.raises(ValueError, match="already exists"):
        store.insert(item)


def test_top_requires_one_type_and_orders_within_it(tmp_path):
    store = QuestionProfileStore(tmp_path / "questions.sqlite3")
    store.insert_many(
        [
            profile("fact-low", "factual_conceptual", 60),
            profile("fact-high", "factual_conceptual", 100),
            profile("science", "scientific_explanatory", 100),
            profile("fact-mid", "factual_conceptual", 80),
        ]
    )
    assert [item.id for item in store.top("factual_conceptual", limit=2)] == [
        "fact-high",
        "fact-mid",
    ]


@pytest.mark.parametrize("question_type", ["", "unknown", None])
def test_top_rejects_invalid_question_type(tmp_path, question_type):
    store = QuestionProfileStore(tmp_path / "questions.sqlite3")
    with pytest.raises(ValueError, match="question_type"):
        store.top(question_type, limit=10)


def test_v01_and_v02_can_share_one_database_without_collision(tmp_path):
    db = tmp_path / "questions.sqlite3"
    old = evaluation("same-id")
    new = profile("same-id")
    QuestionStore(db).insert(old)
    QuestionProfileStore(db).insert(new)

    assert QuestionStore(db).list_all() == [old]
    assert QuestionProfileStore(db).list_all() == [new]
