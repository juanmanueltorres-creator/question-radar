from __future__ import annotations

import hashlib
import json

import pytest


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


def test_handoff_rejects_unknown_contract_version() -> None:
    from question_radar.handoffs import QuestionResearchHandoff

    payload = _valid_payload()
    payload["contract"] = "question-research-handoff/v9.9"

    with pytest.raises(ValueError, match="contract"):
        QuestionResearchHandoff.from_dict(payload)


def test_handoff_rejects_unknown_route() -> None:
    from question_radar.handoffs import QuestionResearchHandoff

    payload = _valid_payload()
    payload["routing"] = {
        "kind": "AUTO_RESEARCH",
        "destination": "andes-context-os",
    }

    with pytest.raises(ValueError, match="routing"):
        QuestionResearchHandoff.from_dict(payload)


@pytest.mark.parametrize("decision", ["PARKED", "KILLED"])
def test_handoff_rejects_non_actionable_decisions(decision: str) -> None:
    from question_radar.handoffs import QuestionResearchHandoff

    payload = _valid_payload()
    payload["investigation"] = {
        "decision": decision,
        "rationale": "Do not continue this investigation now.",
        "next_test": "Reassess only after an explicit new signal.",
    }

    with pytest.raises(ValueError, match="decision"):
        QuestionResearchHandoff.from_dict(payload)


def test_handoff_requires_timezone_aware_created_at() -> None:
    from question_radar.handoffs import QuestionResearchHandoff

    payload = _valid_payload()
    payload["created_at"] = "2026-09-04T20:30:00"

    with pytest.raises(ValueError, match="created_at"):
        QuestionResearchHandoff.from_dict(payload)


def test_handoff_rejects_unknown_fields() -> None:
    from question_radar.handoffs import QuestionResearchHandoff

    payload = _valid_payload()
    payload["buyer"] = "invented"

    with pytest.raises(ValueError, match="unknown fields"):
        QuestionResearchHandoff.from_dict(payload)


def test_decision_fingerprint_is_deterministic() -> None:
    from question_radar.decisions import InvestigationDecision
    from question_radar.handoffs import decision_fingerprint
    from question_radar.lineage import QuestionNode

    node = QuestionNode.from_dict(
        {
            "id": "question:001",
            "question": "What decision should we investigate?",
            "source": "manual",
            "source_ref": None,
            "created_at": "2026-09-04T19:00:00-03:00",
        }
    )
    decision = InvestigationDecision.from_dict(
        {
            "id": "decision:001",
            "question_id": "question:001",
            "decision": "RESEARCH",
            "rationale": "The question is testable without assuming demand.",
            "goal_alignment": True,
            "external_signal": True,
            "testable_now": True,
            "leverage": True,
            "cost": "low",
            "confidence": "medium",
            "next_test": "Identify the decision owner and evidence used today.",
            "resume_when": None,
            "kill_condition": None,
            "supersedes_decision_id": None,
            "created_at": "2026-09-04T20:00:00-03:00",
        }
    )
    canonical = json.dumps(
        {"question": node.to_dict(), "decision": decision.to_dict()},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    expected = "sha256:" + hashlib.sha256(canonical).hexdigest()

    assert decision_fingerprint(node, decision) == expected
    assert decision_fingerprint(node, decision) == expected
