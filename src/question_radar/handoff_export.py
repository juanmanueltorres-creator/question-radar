from __future__ import annotations

import json

from question_radar.decisions import InvestigationDecision
from question_radar.handoffs import (
    DESTINATION_BY_ROUTE,
    HANDOFF_CONTRACT,
    QuestionResearchHandoff,
    decision_fingerprint,
)
from question_radar.lineage import QuestionNode


def build_question_research_handoff(
    node: QuestionNode,
    decision: InvestigationDecision,
    *,
    route: str,
    handoff_id: str,
    created_at: str,
    canonical_question: str | None = None,
    constraints: tuple[str, ...] = (),
) -> QuestionResearchHandoff:
    if route not in DESTINATION_BY_ROUTE:
        raise ValueError("route is unsupported")

    if canonical_question is None:
        canonical = node.question
    else:
        canonical = canonical_question.strip()
        if not canonical:
            raise ValueError("canonical_question must be a non-empty string")

    payload = {
        "contract": HANDOFF_CONTRACT,
        "handoff_id": handoff_id,
        "created_at": created_at,
        "source": {
            "system": "question-radar",
            "question_id": node.id,
            "question_profile_ref": None,
            "decision_id": decision.id,
            "decision_fingerprint": decision_fingerprint(node, decision),
        },
        "question": {
            "raw": node.question,
            "canonical": canonical,
        },
        "investigation": {
            "decision": decision.decision,
            "rationale": decision.rationale,
            "next_test": decision.next_test,
        },
        "routing": {
            "kind": route,
            "destination": DESTINATION_BY_ROUTE[route],
        },
        "constraints": list(constraints),
    }
    return QuestionResearchHandoff.from_dict(payload)


def render_question_research_handoff_json(
    handoff: QuestionResearchHandoff,
) -> str:
    return (
        json.dumps(
            handoff.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
