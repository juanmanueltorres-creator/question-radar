import json

import pytest

from question_radar.learning import LearningObservation
from question_radar.learning_export import (
    export_learning_observations,
    load_learning_observations,
)


def observation(identifier: str = "learning-export-001") -> LearningObservation:
    return LearningObservation.from_dict(
        {
            "id": identifier,
            "concept": "question_sequence_analysis",
            "gap_type": "connection",
            "state": "possible_gap",
            "confidence": "low",
            "evidence_question_ids": ["q-3", "q-1", "q-2"],
            "interpretation": "Sequence evidence is still limited.",
            "suggested_next_step": "Collect consecutive questions before increasing confidence.",
            "created_at": "2026-08-29T18:30:00-03:00",
            "updated_at": "2026-08-29T18:31:00-03:00",
        }
    )


def test_jsonl_round_trip_preserves_exact_observation_and_evidence_order(tmp_path):
    item = observation()
    output = tmp_path / "nested" / "learning.jsonl"
    assert export_learning_observations([item], output, "jsonl") == output
    assert load_learning_observations(output, "jsonl") == [item]
    raw = json.loads(output.read_text(encoding="utf-8"))
    assert raw["evidence_question_ids"] == ["q-3", "q-1", "q-2"]


def test_blank_jsonl_lines_are_ignored(tmp_path):
    item = observation()
    path = tmp_path / "learning.jsonl"
    path.write_text(
        "\n" + json.dumps(item.to_dict(), ensure_ascii=False) + "\n\n",
        encoding="utf-8",
    )
    assert load_learning_observations(path, "jsonl") == [item]


def test_malformed_jsonl_reports_line_number(tmp_path):
    path = tmp_path / "learning.jsonl"
    path.write_text(
        json.dumps(observation().to_dict()) + "\n{broken\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="malformed JSONL at line 2"):
        load_learning_observations(path, "jsonl")


@pytest.mark.parametrize("function_name", ["load", "export"])
def test_csv_is_not_supported(tmp_path, function_name):
    if function_name == "load":
        path = tmp_path / "input.csv"
        path.write_text("id\nlearning-1\n", encoding="utf-8")
        with pytest.raises(ValueError, match="unsupported import format: csv"):
            load_learning_observations(path, "csv")
    else:
        with pytest.raises(ValueError, match="unsupported export format: csv"):
            export_learning_observations([observation()], tmp_path / "out.csv", "csv")
