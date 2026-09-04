from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

DECISION_STATES = ("DO_NOW", "RESEARCH", "PARKED", "KILLED")
COST_LEVELS = ("low", "medium", "high")
CONFIDENCE_LEVELS = ("low", "medium", "high")
RECOMMENDED_DO_NOW_LIMIT = 3

_FIELDS = {
    "id",
    "question_id",
    "decision",
    "rationale",
    "goal_alignment",
    "external_signal",
    "testable_now",
    "leverage",
    "cost",
    "confidence",
    "next_test",
    "resume_when",
    "kill_condition",
    "supersedes_decision_id",
    "created_at",
}


def _required_text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _optional_text(name: str, value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be null or a non-empty string")
    return value.strip()


def _required_bool(name: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")
    return value


def _timestamp(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a timezone-aware ISO timestamp")
    cleaned = value.strip()
    try:
        parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be a timezone-aware ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must be a timezone-aware ISO timestamp")
    return cleaned


def decision_timestamp_sort_key(value: str) -> datetime:
    return datetime.fromisoformat(
        _timestamp("timestamp", value).replace("Z", "+00:00")
    ).astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class InvestigationDecision:
    id: str
    question_id: str
    decision: str
    rationale: str
    goal_alignment: bool
    external_signal: bool
    testable_now: bool
    leverage: bool
    cost: str
    confidence: str
    next_test: str | None
    resume_when: str | None
    kill_condition: str | None
    supersedes_decision_id: str | None
    created_at: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "InvestigationDecision":
        if not isinstance(payload, dict):
            raise ValueError("investigation decision payload must be a JSON object")
        missing = sorted(_FIELDS - payload.keys())
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")
        unknown = sorted(payload.keys() - _FIELDS)
        if unknown:
            raise ValueError(f"unknown fields: {', '.join(unknown)}")

        state = payload["decision"]
        if state not in DECISION_STATES:
            raise ValueError("decision must be one of: " + ", ".join(DECISION_STATES))
        cost = payload["cost"]
        if cost not in COST_LEVELS:
            raise ValueError("cost must be one of: " + ", ".join(COST_LEVELS))
        confidence = payload["confidence"]
        if confidence not in CONFIDENCE_LEVELS:
            raise ValueError(
                "confidence must be one of: " + ", ".join(CONFIDENCE_LEVELS)
            )

        next_test = _optional_text("next_test", payload["next_test"])
        resume_when = _optional_text("resume_when", payload["resume_when"])
        if state in {"DO_NOW", "RESEARCH"} and next_test is None:
            raise ValueError(
                "next_test must be a non-empty string for DO_NOW or RESEARCH"
            )
        if state == "PARKED" and resume_when is None:
            raise ValueError("resume_when must be a non-empty string for PARKED")

        return cls(
            id=_required_text("id", payload["id"]),
            question_id=_required_text("question_id", payload["question_id"]),
            decision=state,
            rationale=_required_text("rationale", payload["rationale"]),
            goal_alignment=_required_bool("goal_alignment", payload["goal_alignment"]),
            external_signal=_required_bool("external_signal", payload["external_signal"]),
            testable_now=_required_bool("testable_now", payload["testable_now"]),
            leverage=_required_bool("leverage", payload["leverage"]),
            cost=cost,
            confidence=confidence,
            next_test=next_test,
            resume_when=resume_when,
            kill_condition=_optional_text("kill_condition", payload["kill_condition"]),
            supersedes_decision_id=_optional_text(
                "supersedes_decision_id", payload["supersedes_decision_id"]
            ),
            created_at=_timestamp("created_at", payload["created_at"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
