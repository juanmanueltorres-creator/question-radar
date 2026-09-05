from __future__ import annotations

from dataclasses import dataclass
from typing import Any


HANDOFF_CONTRACT = "question-research-handoff/v0.1"


@dataclass(frozen=True, slots=True)
class QuestionResearchHandoff:
    _payload: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "QuestionResearchHandoff":
        if payload.get("contract") != HANDOFF_CONTRACT:
            raise ValueError(f"contract must be {HANDOFF_CONTRACT}")
        return cls(_payload=payload)

    def to_dict(self) -> dict[str, Any]:
        return self._payload
