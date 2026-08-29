import json

from question_radar.cli import main


def payload(identifier: str = "cli-001") -> dict:
    return {
        "id": identifier,
        "question": "Why are we assuming this variable is independent?",
        "clarity": 4,
        "depth": 5,
        "investigability": 4,
        "assumption_challenge": 5,
        "connections": 4,
        "score": 88,
        "strengths": "Surfaces a hidden assumption.",
        "gap": "Needs the variables to be named.",
        "next_question": "What observation would reveal dependence between the variables?",
        "topic": "reasoning",
        "evaluator": "manual",
        "rubric_version": "v0.1",
        "created_at": "2026-08-29T21:00:00-03:00",
    }


def test_add_then_list(tmp_path, capsys):
    db = tmp_path / "questions.sqlite3"
    evaluation_file = tmp_path / "evaluation.json"
    evaluation_file.write_text(json.dumps(payload()), encoding="utf-8")
    assert main(["--db", str(db), "add", str(evaluation_file)]) == 0
    assert main(["--db", str(db), "list"]) == 0
    output = capsys.readouterr().out
    assert "cli-001" in output
    assert "88" in output


def test_malformed_json_returns_nonzero(tmp_path, capsys):
    db = tmp_path / "questions.sqlite3"
    evaluation_file = tmp_path / "broken.json"
    evaluation_file.write_text("{broken", encoding="utf-8")
    assert main(["--db", str(db), "add", str(evaluation_file)]) == 2
    assert "malformed JSON" in capsys.readouterr().err


def test_export_command_writes_ranked_corpus(tmp_path):
    db = tmp_path / "questions.sqlite3"
    evaluation_file = tmp_path / "evaluation.json"
    evaluation_file.write_text(json.dumps(payload()), encoding="utf-8")
    output = tmp_path / "questions.jsonl"
    assert main(["--db", str(db), "add", str(evaluation_file)]) == 0
    assert main(["--db", str(db), "export", str(output), "--format", "jsonl"]) == 0
    assert output.exists()
    assert "cli-001" in output.read_text(encoding="utf-8")
