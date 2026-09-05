from __future__ import annotations

from dataclasses import dataclass
from typing import Any


HANDOFF_CONTRACT = "question-research-handoff/v0.1"
DESTINATION_BY_ROUTE = {
    "TERRITORIAL_RESEARCH": "andes-context-os",
    "PUBLIC_CONTRIBUTION_RESEARCH": "opportunity-os",
}


@dataclass(frozen=True, slots=True)
class QuestionResearchHandoff:
    _payload: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "QuestionResearchHandoff":
        if payload.get("contract") != HANDOFF_CONTRACT:
            raise ValueError(f"contract must be {HANDOFF_CONTRACT}")

        routing = payload.get("routing")
        if not isinstance(routing, dict):
            raise ValueError("routing must be an object")
        kind = routing.get("kind")
        destination = routing.get("destination")
        if kind not in DESTINATION_BY_ROUTE:
            raise ValueError("routing.kind is unsupported")
        if destination != DESTINATION_BY_ROUTE[kind]:
            raise ValueError("routing.destination does not match routing.kind")

        return cls(_payload=payload)

    def to_dict(self) -> dict[str, Any]:
        return self._payload
