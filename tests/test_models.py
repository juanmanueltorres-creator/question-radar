import pytest

from question_radar.models import QuestionEvaluation


def valid_payload() -> dict:
    return {
        "id": "q-001",
        "question": "What evidence would falsify this interpretation?",
        "clarity": 4,
        "depth": 4,
        "investigability": 5,
        "assumption_challenge": 5,
        "connections": 5,
        "score": 92,
        "strengths": "Makes falsifiability explicit.",
        "gap": "The interpretation itself still needs to be stated.",
        "next_question": "Which observation would discriminate between the two leading interpretations?",
        "topic": "scientific reasoning",
        "evaluator": "manual",
        "rubric_version": "v0.1",
        "created_at": "2026-08-29T21:00:00-03:00",
    }


def test_valid_payload_builds_immutable_evaluation():
    evaluation = QuestionEvaluation.from_dict(valid_payload())
    assert evaluation.score == 92
    assert evaluation.topic == "scientific reasoning"
    assert evaluation.to_dict()["question"].startswith("What evidence")


def test_mismatched_supplied_score_is_rejected():
    payload = valid_payload()
    payload["score"] = 99

    with pytest.raises(ValueError, match="score mismatch"):
        QuestionEvaluation.from_dict(payload)


def test_missing_required_field_is_rejected():
    payload = valid_payload()
    del payload["question"]

    with pytest.raises(ValueError, match="missing required fields"):
        QuestionEvaluation.from_dict(payload)


def test_invalid_iso_timestamp_is_rejected():
    payload = valid_payload()
    payload["created_at"] = "yesterday"

    with pytest.raises(ValueError, match="created_at"):
        QuestionEvaluation.from_dict(payload)
