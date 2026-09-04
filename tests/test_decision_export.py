import json

from question_radar.decision_export import (
    render_active_json,
    render_active_markdown,
    render_decision_json,
    render_decision_markdown,
    render_history_json,
    render_history_markdown,
)
from question_radar.decisions import InvestigationDecision
from question_radar.lineage import QuestionNode


def node(node_id="q-a", question="Should this consume attention now?"):
    return QuestionNode.from_dict(
        {
            "id": node_id,
            "question": question,
            "source": "manual",
            "source_ref": None,
            "created_at": "2026-09-04T12:00:00-03:00",
        }
    )


def make_decision(decision_id, question_id, state="DO_NOW", **overrides):
    payload = {
        "id": decision_id,
        "question_id": question_id,
        "decision": state,
        "rationale": "Bounded operator judgment.",
        "goal_alignment": state != "PARKED",
        "external_signal": True,
        "testable_now": state in {"DO_NOW", "RESEARCH"},
        "leverage": True,
        "cost": "low",
        "confidence": "medium",
        "next_test": "Run one bounded test."
        if state in {"DO_NOW", "RESEARCH"}
        else None,
        "resume_when": "A relevant condition changes." if state == "PARKED" else None,
        "kill_condition": None,
        "supersedes_decision_id": None,
        "created_at": "2026-09-04T12:05:00-03:00",
    }
    payload.update(overrides)
    return InvestigationDecision.from_dict(payload)


def test_parked_markdown_preserves_authority_boundary():
    rendered = render_decision_markdown(
        node(), make_decision("d-1", "q-a", "PARKED")
    )
    assert "Current decision: PARKED" in rendered
    assert "No action is currently requested." in rendered
    assert "Operator decision recorded; no automatic prioritization was performed." in rendered
    assert rendered.endswith("\n")


def test_show_json_is_deterministic_and_has_no_priority_score():
    first = render_decision_json(node(), make_decision("d-1", "q-a", "PARKED"))
    second = render_decision_json(node(), make_decision("d-1", "q-a", "PARKED"))
    assert first == second
    payload = json.loads(first)
    assert payload["decision_version"] == "v0.9"
    assert payload["automatic_decision"] is False
    assert "priority_score" not in payload


def test_history_rendering_is_deterministic_and_append_only_in_language():
    items = [
        make_decision("d-1", "q-a"),
        make_decision(
            "d-2",
            "q-a",
            "PARKED",
            supersedes_decision_id="d-1",
            created_at="2026-09-04T12:10:00-03:00",
        ),
    ]
    markdown = render_history_markdown(node(), items)
    payload = json.loads(render_history_json(node(), items))
    assert "History is append-only" in markdown
    assert [item["id"] for item in payload["history"]] == ["d-1", "d-2"]
    assert payload["automatic_decision"] is False


def test_active_counts_all_states_and_lists_only_do_now_research():
    entries = [
        (node("q-1"), make_decision("d-1", "q-1", "DO_NOW")),
        (node("q-2"), make_decision("d-2", "q-2", "RESEARCH")),
        (node("q-3"), make_decision("d-3", "q-3", "PARKED")),
        (node("q-4"), make_decision("d-4", "q-4", "KILLED")),
    ]
    payload = json.loads(render_active_json(entries))
    assert payload["counts"] == {
        "DO_NOW": 1,
        "RESEARCH": 1,
        "PARKED": 1,
        "KILLED": 1,
    }
    assert [item["decision"]["decision"] for item in payload["active"]] == [
        "DO_NOW",
        "RESEARCH",
    ]
    assert payload["wip_warning"] is None


def test_zero_decisions_render_explicit_zero_counts_and_empty_active_list():
    payload = json.loads(render_active_json([]))
    assert payload["counts"] == {
        "DO_NOW": 0,
        "RESEARCH": 0,
        "PARKED": 0,
        "KILLED": 0,
    }
    assert payload["active"] == []
    assert payload["wip_warning"] is None
    assert "None." in render_active_markdown([])


def test_wip_warning_only_above_three_do_now_and_does_not_change_records():
    three = [
        (node(f"q-{i}"), make_decision(f"d-{i}", f"q-{i}", "DO_NOW"))
        for i in range(1, 4)
    ]
    four = three + [
        (node("q-4"), make_decision("d-4", "q-4", "DO_NOW"))
    ]
    assert json.loads(render_active_json(three))["wip_warning"] is None
    payload = json.loads(render_active_json(four))
    assert "4 investigations are marked DO_NOW" in payload["wip_warning"]
    assert "No decision was changed automatically." in payload["wip_warning"]
    assert all(item.decision == "DO_NOW" for _, item in four)
