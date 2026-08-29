import json

from question_radar.cli import main
from question_radar.learning import LearningObservation


def learning_payload(identifier: str = "learning-cli-001") -> dict:
    return {
        "id": identifier,
        "concept": "question_evaluation_models",
        "gap_type": "connection",
        "state": "consolidating",
        "confidence": "medium",
        "evidence_question_ids": ["q-2", "q-1"],
        "interpretation": "Several stored questions support a cautious consolidation hypothesis.",
        "suggested_next_step": "Apply the distinction in a different domain.",
        "created_at": "2026-08-29T18:30:00-03:00",
        "updated_at": "2026-08-29T18:35:00-03:00",
    }


def write_json(tmp_path, data: dict, name: str = "observation.json"):
    path = tmp_path / name
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def historical_payload() -> dict:
    return {
        "id": "old-cli-learning-regression",
        "question": "Historical question?",
        "clarity": 5,
        "depth": 5,
        "investigability": 5,
        "assumption_challenge": 5,
        "connections": 5,
        "score": 100,
        "strengths": "Historical.",
        "gap": "None.",
        "next_question": "Next?",
        "topic": None,
        "evaluator": "manual",
        "rubric_version": "v0.1",
        "created_at": "2026-08-29T18:00:00-03:00",
    }


def profile_payload() -> dict:
    return {
        "id": "profile-cli-learning-regression",
        "question": "Typed question?",
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
        "strengths": "Useful.",
        "gap": "Needs context.",
        "assumptions": "One assumption.",
        "evidence_required": "Relevant evidence.",
        "next_question": "What next?",
        "topic": None,
        "evaluator": "manual",
        "rubric_version": "v0.2",
        "created_at": "2026-08-29T18:26:00-03:00",
    }


def test_learning_add_then_list_shows_summary_fields(tmp_path, capsys):
    db = tmp_path / "questions.sqlite3"
    path = write_json(tmp_path, learning_payload())
    assert main(["--db", str(db), "learning", "add", str(path)]) == 0
    capsys.readouterr()

    assert main(["--db", str(db), "learning", "list"]) == 0
    output = capsys.readouterr().out
    assert "question_evaluation_models" in output
    assert "connection" in output
    assert "consolidating" in output
    assert "medium" in output
    assert "evidence=2" in output
    assert "learning-cli-001" in output


def test_learning_show_prints_complete_record(tmp_path, capsys):
    db = tmp_path / "questions.sqlite3"
    path = write_json(tmp_path, learning_payload())
    assert main(["--db", str(db), "learning", "add", str(path)]) == 0
    capsys.readouterr()

    assert main(["--db", str(db), "learning", "show", "learning-cli-001"]) == 0
    output = capsys.readouterr().out
    assert "q-2" in output
    assert "q-1" in output
    assert "Several stored questions" in output
    assert "Apply the distinction" in output
    assert "2026-08-29T18:30:00-03:00" in output
    assert "2026-08-29T18:35:00-03:00" in output


def test_learning_show_missing_returns_two(tmp_path, capsys):
    db = tmp_path / "questions.sqlite3"
    assert main(["--db", str(db), "learning", "show", "missing"]) == 2
    assert "not found" in capsys.readouterr().err


def test_learning_frontier_uses_only_stored_observations(tmp_path, capsys):
    db = tmp_path / "questions.sqlite3"
    path = write_json(tmp_path, learning_payload())
    assert main(["--db", str(db), "learning", "add", str(path)]) == 0
    capsys.readouterr()

    assert main(["--db", str(db), "learning", "frontier"]) == 0
    output = capsys.readouterr().out
    assert "question_evaluation_models" in output
    assert "invented_concept" not in output


def test_learning_import_export_round_trip(tmp_path, capsys):
    db = tmp_path / "questions.sqlite3"
    source = tmp_path / "source.jsonl"
    expected = LearningObservation.from_dict(learning_payload())
    source.write_text(
        json.dumps(expected.to_dict(), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    exported = tmp_path / "exported.jsonl"

    assert main([
        "--db", str(db), "learning", "import", str(source), "--format", "jsonl"
    ]) == 0
    assert main([
        "--db", str(db), "learning", "export", str(exported), "--format", "jsonl"
    ]) == 0
    capsys.readouterr()

    loaded = LearningObservation.from_dict(
        json.loads(exported.read_text(encoding="utf-8"))
    )
    assert loaded == expected


def test_learning_malformed_json_returns_two(tmp_path, capsys):
    db = tmp_path / "questions.sqlite3"
    path = tmp_path / "broken.json"
    path.write_text("{broken", encoding="utf-8")
    assert main(["--db", str(db), "learning", "add", str(path)]) == 2
    assert "malformed JSON" in capsys.readouterr().err


def test_historical_and_profile_cli_still_work_with_learning_namespace(tmp_path, capsys):
    db = tmp_path / "questions.sqlite3"
    old_path = write_json(tmp_path, historical_payload(), "old.json")
    profile_path = write_json(tmp_path, profile_payload(), "profile.json")

    assert main(["--db", str(db), "add", str(old_path)]) == 0
    assert main(["--db", str(db), "profile", "add", str(profile_path)]) == 0
    capsys.readouterr()

    assert main(["--db", str(db), "top", "--limit", "1"]) == 0
    assert main(["--db", str(db), "profile", "list"]) == 0
    output = capsys.readouterr().out
    assert "old-cli-learning-regression" in output
    assert "profile-cli-learning-regression" in output
