from __future__ import annotations


def _valid_payload() -> dict[str, object]:
    return {
        "contract": "question-research-handoff/v0.1",
        "handoff_id": "qrh:test:001",
        "created_at": "2026-09-04T20:30:00-03:00",
        "source": {
            "system": "question-radar",
            "question_id": "question:001",
            "question_profile_ref": None,
            "decision_id": "decision:001",
            "decision_fingerprint": "sha256:" + "0" * 64,
        },
        "question": {
            "raw": "What decision should we investigate?",
            "canonical": "What decision should we investigate?",
        },
        "investigation": {
            "decision": "RESEARCH",
            "rationale": "The question is testable without assuming demand.",
            "next_test": "Identify the decision owner and evidence used today.",
        },
        "routing": {
            "kind": "TERRITORIAL_RESEARCH",
            "destination": "andes-context-os",
        },
        "constraints": ["Do not infer a buyer from an observed actor."],
    }


def test_valid_question_research_handoff_round_trips() -> None:
    from question_radar.handoffs import QuestionResearchHandoff

    payload = _valid_payload()
    handoff = QuestionResearchHandoff.from_dict(payload)

    assert handoff.to_dict() == payload
