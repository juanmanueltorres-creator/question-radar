import json

import pytest

from question_radar.export import export_evaluations, load_evaluations, write_csv, write_jsonl
from question_radar.models import QuestionEvaluation


def sample() -> QuestionEvaluation:
    return QuestionEvaluation.from_dict(
        {
            "id": "q-export",
            "question": "What observation would change our conclusion?",
            "clarity": 5,
            "depth": 5,
            "investigability": 5,
            "assumption_challenge": 5,
            "connections": 5,
            "score": 100,
            "strengths": "Explicitly asks for disconfirming evidence.",
            "gap": "Needs a named conclusion.",
            "next_question": "Which competing explanation predicts a different observation?",
            "topic": "evidence",
            "evaluator": "manual",
            "rubric_version": "v0.1",
            "created_at": "2026-08-29T21:00:00-03:00",
        }
    )


def test_jsonl_export_preserves_required_fields(tmp_path):
    path = tmp_path / "questions.jsonl"
    write_jsonl([sample()], path)
    payload = json.loads(path.read_text(encoding="utf-8").strip())
    assert payload["id"] == "q-export"
    assert payload["score"] == 100
    assert payload["next_question"].startswith("Which competing")


def test_csv_round_trip_preserves_evaluation(tmp_path):
    path = tmp_path / "questions.csv"
    item = sample()
    write_csv([item], path)
    assert load_evaluations(path, "csv") == [item]


def test_jsonl_round_trip_preserves_evaluation(tmp_path):
    path = tmp_path / "questions.jsonl"
    item = sample()
    write_jsonl([item], path)
    assert load_evaluations(path, "jsonl") == [item]


def test_unsupported_export_format_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="unsupported export format"):
        export_evaluations([sample()], tmp_path / "questions.txt", "txt")
