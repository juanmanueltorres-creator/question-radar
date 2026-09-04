import pytest

from question_radar.decisions import (
    CONFIDENCE_LEVELS,
    COST_LEVELS,
    DECISION_STATES,
    RECOMMENDED_DO_NOW_LIMIT,
    InvestigationDecision,
)


def valid_payload(**overrides):
    payload = {
        "id": "dec-001",
        "question_id": "q-001",
        "decision": "DO_NOW",
        "rationale": "This question serves the current objective.",
        "goal_alignment": True,
        "external_signal": True,
        "testable_now": True,
        "leverage": True,
        "cost": "medium",
        "confidence": "medium",
        "next_test": "Run one bounded evidence review.",
        "resume_when": None,
        "kill_condition": None,
        "supersedes_decision_id": None,
        "created_at": "2026-09-04T15:00:00-03:00",
    }
    payload.update(overrides)
    return payload


def test_decision_contract_round_trips():
    item = InvestigationDecision.from_dict(valid_payload())
    assert item.to_dict() == valid_payload()


def test_closed_vocabularies_are_frozen():
    assert DECISION_STATES == ("DO_NOW", "RESEARCH", "PARKED", "KILLED")
    assert COST_LEVELS == ("low", "medium", "high")
    assert CONFIDENCE_LEVELS == ("low", "medium", "high")
    assert RECOMMENDED_DO_NOW_LIMIT == 3


@pytest.mark.parametrize("field", ["id", "question_id", "rationale"])
def test_required_text_rejects_blank(field):
    with pytest.raises(ValueError, match=field):
        InvestigationDecision.from_dict(valid_payload(**{field: "   "}))


@pytest.mark.parametrize(
    "field", ["goal_alignment", "external_signal", "testable_now", "leverage"]
)
def test_gates_require_real_booleans(field):
    with pytest.raises(ValueError, match=f"{field} must be a boolean"):
        InvestigationDecision.from_dict(valid_payload(**{field: 1}))


@pytest.mark.parametrize("state", ["DO_NOW", "RESEARCH"])
def test_active_states_require_next_test(state):
    with pytest.raises(ValueError, match="next_test"):
        InvestigationDecision.from_dict(valid_payload(decision=state, next_test=None))


def test_parked_requires_resume_when():
    with pytest.raises(ValueError, match="resume_when"):
        InvestigationDecision.from_dict(
            valid_payload(decision="PARKED", next_test=None, resume_when=None)
        )


def test_killed_allows_optional_kill_condition():
    item = InvestigationDecision.from_dict(
        valid_payload(decision="KILLED", next_test=None, kill_condition=None)
    )
    assert item.kill_condition is None


def test_naive_timestamp_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware ISO timestamp"):
        InvestigationDecision.from_dict(valid_payload(created_at="2026-09-04T15:00:00"))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("decision", "SOMEDAY", "decision must be one of"),
        ("cost", "tiny", "cost must be one of"),
        ("confidence", "certain", "confidence must be one of"),
    ],
)
def test_closed_vocabularies_reject_unknown_values(field, value, message):
    with pytest.raises(ValueError, match=message):
        InvestigationDecision.from_dict(valid_payload(**{field: value}))


def test_unknown_field_fails_closed():
    payload = valid_payload()
    payload["priority_score"] = 99
    with pytest.raises(ValueError, match="unknown fields: priority_score"):
        InvestigationDecision.from_dict(payload)
