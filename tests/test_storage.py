import pytest

from question_radar.models import QuestionEvaluation
from question_radar.storage import QuestionStore


def evaluation(identifier: str, score_values: tuple[int, int, int, int, int]) -> QuestionEvaluation:
    clarity, depth, investigability, assumption_challenge, connections = score_values
    score = (clarity + depth + investigability + assumption_challenge + connections) * 4
    return QuestionEvaluation.from_dict(
        {
            "id": identifier,
            "question": f"Question {identifier}?",
            "clarity": clarity,
            "depth": depth,
            "investigability": investigability,
            "assumption_challenge": assumption_challenge,
            "connections": connections,
            "score": score,
            "strengths": "Useful diagnostic question.",
            "gap": "Needs more context.",
            "next_question": "What evidence would reduce the uncertainty?",
            "topic": None,
            "evaluator": "manual",
            "rubric_version": "v0.1",
            "created_at": "2026-08-29T21:00:00-03:00",
        }
    )


def test_evaluation_can_be_inserted_and_read(tmp_path):
    store = QuestionStore(tmp_path / "questions.sqlite3")
    item = evaluation("q-001", (4, 4, 5, 5, 5))
    store.insert(item)
    assert store.list_all() == [item]


def test_top_orders_score_descending(tmp_path):
    store = QuestionStore(tmp_path / "questions.sqlite3")
    low = evaluation("low", (2, 2, 2, 2, 2))
    high = evaluation("high", (5, 5, 5, 5, 5))
    medium = evaluation("medium", (3, 3, 3, 3, 3))
    store.insert_many([low, high, medium])
    assert [item.id for item in store.top(limit=2)] == ["high", "medium"]


def test_duplicate_id_is_rejected_without_silent_overwrite(tmp_path):
    store = QuestionStore(tmp_path / "questions.sqlite3")
    item = evaluation("same", (4, 4, 4, 4, 4))
    store.insert(item)
    with pytest.raises(ValueError, match="already exists"):
        store.insert(item)
