from __future__ import annotations

import json

import pytest

from question_radar.decisions import InvestigationDecision
from question_radar.handoffs import decision_fingerprint
from question_radar.lineage import QuestionNode


def _node() -> QuestionNode:
    return QuestionNode(
        id="question:water:001",
        question="¿Qué decisión hídrica recurrente vale investigar?",
        source="manual",
        source_ref=None,
        created_at="2026-09-04T20:00:00-03:00",
    )


def _decision(state: str = "RESEARCH") -> InvestigationDecision:
    return InvestigationDecision(
        id=f"decision:{state.lower()}:001",
        question_id="question:water:001",
        decision=state,
        rationale="La pregunta es testeable sin asumir demanda.",
        goal_alignment=True,
        external_signal=True,
        testable_now=True,
        leverage=True,
        cost="medium",
        confidence="medium",
        next_test=(
            "Identificar quién toma hoy la decisión y qué evidencia usa."
            if state in {"DO_NOW", "RESEARCH"}
            else None
        ),
        resume_when=("Aparezca nueva evidencia pública." if state == "PARKED" else None),
        kill_condition=None,
        supersedes_decision_id=None,
        created_at="2026-09-04T20:05:00-03:00",
    )


def _build(**overrides):
    from question_radar.handoff_export import build_question_research_handoff

    params = {
        "node": _node(),
        "decision": _decision(),
        "route": "TERRITORIAL_RESEARCH",
        "handoff_id": "qrh:test:001",
        "created_at": "2026-09-04T20:10:00-03:00",
    }
    params.update(overrides)
    return build_question_research_handoff(**params)


def test_builder_uses_raw_question_as_canonical_when_no_override() -> None:
    handoff = _build()

    assert handoff.question.raw == _node().question
    assert handoff.question.canonical == _node().question


def test_builder_preserves_explicit_canonical_question() -> None:
    handoff = _build(canonical_question="  Decisión hídrica prioritaria en San Juan  ")

    assert handoff.question.raw == _node().question
    assert handoff.question.canonical == "Decisión hídrica prioritaria en San Juan"


def test_builder_rejects_empty_explicit_canonical_question() -> None:
    with pytest.raises(ValueError):
        _build(canonical_question="   ")


def test_builder_keeps_question_profile_ref_null_without_explicit_link() -> None:
    handoff = _build()

    assert handoff.source.question_profile_ref is None


def test_builder_rejects_parked_decision() -> None:
    with pytest.raises(ValueError):
        _build(decision=_decision("PARKED"))


def test_builder_derives_destination_from_route() -> None:
    territorial = _build(route="TERRITORIAL_RESEARCH")
    contribution = _build(route="PUBLIC_CONTRIBUTION_RESEARCH")

    assert territorial.routing.destination == "andes-context-os"
    assert contribution.routing.destination == "opportunity-os"


def test_builder_rejects_unknown_route() -> None:
    with pytest.raises(ValueError):
        _build(route="MAGIC_ROUTE")


def test_builder_preserves_decision_identity_and_fingerprint() -> None:
    node = _node()
    decision = _decision()

    handoff = _build(node=node, decision=decision)

    assert handoff.source.question_id == node.id
    assert handoff.source.decision_id == decision.id
    assert handoff.source.decision_fingerprint == decision_fingerprint(node, decision)


def test_builder_preserves_constraints_in_order() -> None:
    handoff = _build(constraints=("first", "second"))

    assert handoff.constraints == ("first", "second")


def test_json_export_is_byte_deterministic_for_same_inputs() -> None:
    from question_radar.handoff_export import render_question_research_handoff_json

    handoff = _build(constraints=("No inferir comprador.",))

    first = render_question_research_handoff_json(handoff)
    second = render_question_research_handoff_json(handoff)

    assert first == second
    assert first.endswith("\n")
    assert json.loads(first) == handoff.to_dict()
