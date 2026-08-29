import json

import pytest

from question_radar.profile_export import export_profiles, load_profiles
from question_radar.profiles import QuestionProfile


def sample() -> QuestionProfile:
    return QuestionProfile.from_dict(
        {
            "id": "pv2-export",
            "question": "¿Qué es un KPI?",
            "question_type": "factual_conceptual",
            "readiness": "ready_to_answer",
            "clarity": 5,
            "boundedness": 5,
            "investigability": 5,
            "epistemic_openness": 5,
            "purpose_fit": 5,
            "formulation_score": 100,
            "depth": 1,
            "connections": 2,
            "generativity": 2,
            "strengths": "Direct and precise.",
            "gap": "Domain context can improve the answer.",
            "assumptions": "KPI is relevant to the user's domain.",
            "evidence_required": "Reliable definition and domain examples.",
            "next_question": "Which KPI matters for this decision?",
            "topic": "alfabetizacion_tecnica",
            "evaluator": "manual",
            "rubric_version": "v0.2",
            "created_at": "2026-08-29T18:26:00-03:00",
        }
    )


def test_jsonl_round_trip_preserves_profile(tmp_path):
    path = tmp_path / "profiles.jsonl"
    item = sample()
    export_profiles([item], path, "jsonl")
    assert load_profiles(path, "jsonl") == [item]


def test_csv_round_trip_preserves_profile(tmp_path):
    path = tmp_path / "profiles.csv"
    item = sample()
    export_profiles([item], path, "csv")
    assert load_profiles(path, "csv") == [item]


def test_jsonl_is_utf8_and_contains_full_contract(tmp_path):
    path = tmp_path / "profiles.jsonl"
    export_profiles([sample()], path, "jsonl")
    payload = json.loads(path.read_text(encoding="utf-8").strip())
    assert payload["question"] == "¿Qué es un KPI?"
    assert payload["question_type"] == "factual_conceptual"
    assert payload["formulation_score"] == 100
    assert payload["evidence_required"]


@pytest.mark.parametrize("mode", ["import", "export"])
def test_unsupported_format_is_rejected(tmp_path, mode):
    if mode == "export":
        with pytest.raises(ValueError, match="unsupported export format"):
            export_profiles([sample()], tmp_path / "profiles.txt", "txt")
    else:
        with pytest.raises(ValueError, match="unsupported import format"):
            load_profiles(tmp_path / "profiles.txt", "txt")


def test_malformed_jsonl_is_rejected_with_line_number(tmp_path):
    path = tmp_path / "broken.jsonl"
    first = json.dumps(sample().to_dict(), ensure_ascii=False)
    path.write_text(first + "\n{broken\n", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed JSONL at line 2"):
        load_profiles(path, "jsonl")


def test_invalid_csv_numeric_field_is_rejected(tmp_path):
    path = tmp_path / "profiles.csv"
    export_profiles([sample()], path, "csv")
    text = path.read_text(encoding="utf-8").replace(",5,5,5,5,5,100,", ",banana,5,5,5,5,100,", 1)
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="invalid numeric field"):
        load_profiles(path, "csv")
