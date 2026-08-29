import json

from question_radar.cli import main
from question_radar.learning import LearningObservation


def test_learning_import_frontier_export_end_to_end(tmp_path, capsys):
    db = tmp_path / "questions.sqlite3"
    source = tmp_path / "source.jsonl"
    exported = tmp_path / "exported.jsonl"
    payload = {
        "id": "learning-e2e-001",
        "concept": "function_return_model",
        "gap_type": "conceptual",
        "state": "recurring_gap",
        "confidence": "medium",
        "evidence_question_ids": ["question-a", "question-b"],
        "interpretation": (
            "Repeated question evidence is compatible with a recurring conceptual "
            "signal, but remains a revisable hypothesis."
        ),
        "suggested_next_step": (
            "Solve a small exercise that distinguishes calculating, printing, and returning."
        ),
        "created_at": "2026-08-29T18:30:00-03:00",
        "updated_at": "2026-08-29T18:35:00-03:00",
    }
    source.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")

    assert main([
        "--db", str(db), "learning", "import", str(source), "--format", "jsonl"
    ]) == 0
    capsys.readouterr()

    assert main(["--db", str(db), "learning", "frontier"]) == 0
    frontier = capsys.readouterr().out
    assert "RECURRING SIGNALS" in frontier
    assert "function_return_model" in frontier
    assert "question-a" in frontier

    assert main([
        "--db", str(db), "learning", "export", str(exported), "--format", "jsonl"
    ]) == 0
    capsys.readouterr()

    loaded = LearningObservation.from_dict(
        json.loads(exported.read_text(encoding="utf-8"))
    )
    assert loaded.evidence_question_ids == ("question-a", "question-b")
