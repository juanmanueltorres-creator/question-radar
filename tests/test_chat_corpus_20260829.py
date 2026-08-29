import json
from pathlib import Path

from question_radar.profiles import QuestionProfile


CORPUS = Path("corpus/chat-2026-08-29.jsonl")


def test_chat_20260829_corpus_preserves_and_validates_real_questions():
    lines = [line for line in CORPUS.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 12

    profiles = [QuestionProfile.from_dict(json.loads(line)) for line in lines]
    assert len({profile.id for profile in profiles}) == 12
    assert all(profile.id.startswith("chat-2026-08-29-") for profile in profiles)
    assert all(profile.next_question != profile.question for profile in profiles)
    assert {profile.question_type for profile in profiles} >= {
        "scientific_explanatory",
        "decision_risk",
        "operational_diagnostic",
        "epistemological_meta",
        "factual_conceptual",
    }
    assert min(profile.formulation_score for profile in profiles) < 90
    assert max(profile.formulation_score for profile in profiles) == 100
