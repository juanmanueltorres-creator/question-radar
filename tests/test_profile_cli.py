import json

import pytest

from question_radar.cli import main


def payload(identifier: str = "pv2-cli", question_type: str = "factual_conceptual", score: int = 100) -> dict:
    value = score // 20
    return {
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
        "strengths": "Useful for its purpose.",
        "gap": "Needs context.",
        "assumptions": "One explicit assumption.",
        "evidence_required": "Relevant evidence.",
        "next_question": "What next?",
        "topic": None,
        "evaluator": "manual",
        "rubric_version": "v0.2",
        "created_at": "2026-08-29T18:26:00-03:00",
    }


def write_profile(tmp_path, data: dict, name: str = "profile.json"):
    path = tmp_path / name
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def test_profile_add_then_list_shows_type_readiness_and_score(tmp_path, capsys):
    db = tmp_path / "questions.sqlite3"
    path = write_profile(tmp_path, payload())
    assert main(["--db", str(db), "profile", "add", str(path)]) == 0
    assert main(["--db", str(db), "profile", "list"]) == 0
    output = capsys.readouterr().out
    assert "pv2-cli" in output
    assert "100" in output
    assert "factual_conceptual" in output
    assert "ready_to_answer" in output


def test_profile_top_requires_question_type(tmp_path):
    db = tmp_path / "questions.sqlite3"
    with pytest.raises(SystemExit) as exc:
        main(["--db", str(db), "profile", "top"])
    assert exc.value.code == 2


def test_profile_top_filters_by_type(tmp_path, capsys):
    db = tmp_path / "questions.sqlite3"
    for index, item in enumerate([
        payload("fact-low", "factual_conceptual", 60),
        payload("science", "scientific_explanatory", 100),
        payload("fact-high", "factual_conceptual", 100),
    ]):
        path = write_profile(tmp_path, item, f"profile-{index}.json")
        assert main(["--db", str(db), "profile", "add", str(path)]) == 0
    capsys.readouterr()
    assert main([
        "--db", str(db), "profile", "top", "--type", "factual_conceptual", "--limit", "10"
    ]) == 0
    output = capsys.readouterr().out
    assert "fact-high" in output
    assert "fact-low" in output
    assert "science" not in output


def test_profile_import_and_export_round_trip(tmp_path):
    db = tmp_path / "questions.sqlite3"
    source = tmp_path / "source.jsonl"
    source.write_text(json.dumps(payload(), ensure_ascii=False) + "\n", encoding="utf-8")
    output = tmp_path / "profiles.csv"
    assert main(["--db", str(db), "profile", "import", str(source), "--format", "jsonl"]) == 0
    assert main(["--db", str(db), "profile", "export", str(output), "--format", "csv"]) == 0
    assert output.exists()
    assert "pv2-cli" in output.read_text(encoding="utf-8")


def test_profile_malformed_json_returns_nonzero(tmp_path, capsys):
    db = tmp_path / "questions.sqlite3"
    path = tmp_path / "broken.json"
    path.write_text("{broken", encoding="utf-8")
    assert main(["--db", str(db), "profile", "add", str(path)]) == 2
    assert "malformed JSON" in capsys.readouterr().err


def test_historical_v01_cli_still_works(tmp_path, capsys):
    db = tmp_path / "questions.sqlite3"
    path = tmp_path / "evaluation.json"
    path.write_text(json.dumps({
        "id": "old-cli",
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
    }), encoding="utf-8")
    assert main(["--db", str(db), "add", str(path)]) == 0
    assert main(["--db", str(db), "top", "--limit", "1"]) == 0
    assert "old-cli" in capsys.readouterr().out
