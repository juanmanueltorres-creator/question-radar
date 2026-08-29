import json
from pathlib import Path

from question_radar.learning import LearningObservation


SOURCE_CORPUS = Path("corpus/chat-2026-08-29.jsonl")
LEARNING_CORPUS = Path("corpus/learning-frontier-chat-2026-08-29-v0.3.jsonl")


def _load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_learning_frontier_calibration_uses_only_real_chat_evidence():
    source_ids = {item["id"] for item in _load_jsonl(SOURCE_CORPUS)}
    assert len(source_ids) == 12

    observations = [
        LearningObservation.from_dict(item) for item in _load_jsonl(LEARNING_CORPUS)
    ]
    assert len(observations) == 3
    assert {item.concept for item in observations} == {
        "question_evaluation_models",
        "question_sequence_analysis",
        "educational_question_formulation",
    }

    for observation in observations:
        assert set(observation.evidence_question_ids) <= source_ids

    repeated_education = next(
        item
        for item in observations
        if item.concept == "educational_question_formulation"
    )
    assert len(repeated_education.evidence_question_ids) >= 2
    assert repeated_education.state != "recurring_gap"
    assert "repetition alone" in repeated_education.interpretation.lower()
