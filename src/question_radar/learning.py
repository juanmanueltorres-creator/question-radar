from dataclasses import dataclass
from datetime import datetime
from typing import Any


GAP_TYPES = (
    "conceptual",
    "terminology",
    "procedural",
    "connection",
    "evidence",
    "transfer",
)

LEARNING_STATES = (
    "possible_gap",
    "recurring_gap",
    "consolidating",
    "applied",
    "no_longer_observed",
)

CONFIDENCE_LEVELS = ("low", "medium", "high")

_FIELDS = {
    "id",
    "concept",
    "gap_type",
    "state",
    "confidence",
    "evidence_question_ids",
    "interpretation",
    "suggested_next_step",
    "created_at",
    "updated_at",
}

_REQUIRED_TEXT = (
    "id",
    "concept",
    "interpretation",
    "suggested_next_step",
)


def _parse_timestamp(name: str, value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a timezone-aware ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be a timezone-aware ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must be a timezone-aware ISO timestamp")
    return parsed


@dataclass(frozen=True, slots=True)
class LearningObservation:
    id: str
    concept: str
    gap_type: str
    state: str
    confidence: str
    evidence_question_ids: tuple[str, ...]
    interpretation: str
    suggested_next_step: str
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LearningObservation":
        if not isinstance(payload, dict):
            raise ValueError("learning observation payload must be a JSON object")

        missing = sorted(_FIELDS - payload.keys())
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")

        unknown = sorted(payload.keys() - _FIELDS)
        if unknown:
            raise ValueError(f"unknown fields: {', '.join(unknown)}")

        for field in _REQUIRED_TEXT:
            value = payload[field]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty string")

        gap_type = payload["gap_type"]
        if gap_type not in GAP_TYPES:
            raise ValueError("gap_type must be one of: " + ", ".join(GAP_TYPES))

        state = payload["state"]
        if state not in LEARNING_STATES:
            raise ValueError("state must be one of: " + ", ".join(LEARNING_STATES))

        confidence = payload["confidence"]
        if confidence not in CONFIDENCE_LEVELS:
            raise ValueError(
                "confidence must be one of: " + ", ".join(CONFIDENCE_LEVELS)
            )

        raw_evidence = payload["evidence_question_ids"]
        if not isinstance(raw_evidence, list) or not raw_evidence:
            raise ValueError("evidence_question_ids must be a non-empty list")

        evidence: list[str] = []
        for item in raw_evidence:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(
                    "evidence_question_ids must contain non-empty strings"
                )
            evidence.append(item.strip())
        if len(set(evidence)) != len(evidence):
            raise ValueError("duplicate evidence_question_ids are not allowed")

        created = _parse_timestamp("created_at", payload["created_at"])
        updated = _parse_timestamp("updated_at", payload["updated_at"])
        if updated < created:
            raise ValueError("updated_at must not be earlier than created_at")

        return cls(
            id=payload["id"].strip(),
            concept=payload["concept"].strip(),
            gap_type=gap_type,
            state=state,
            confidence=confidence,
            evidence_question_ids=tuple(evidence),
            interpretation=payload["interpretation"].strip(),
            suggested_next_step=payload["suggested_next_step"].strip(),
            created_at=payload["created_at"],
            updated_at=payload["updated_at"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "concept": self.concept,
            "gap_type": self.gap_type,
            "state": self.state,
            "confidence": self.confidence,
            "evidence_question_ids": list(self.evidence_question_ids),
            "interpretation": self.interpretation,
            "suggested_next_step": self.suggested_next_step,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
