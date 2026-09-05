from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class QuestionResearchHandoff:
    _payload: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "QuestionResearchHandoff":
        return cls(_payload=payload)

    def to_dict(self) -> dict[str, Any]:
        return self._payload
