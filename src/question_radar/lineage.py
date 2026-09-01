from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

SOURCE_TYPES = ("manual", "conversation", "corpus", "external")
RELATION_TYPES = (
    "refines",
    "decomposes",
    "generalizes",
    "operationalizes",
    "challenges_assumption",
    "contrasts",
    "follows_from",
)

_NODE_FIELDS = {"id", "question", "source", "source_ref", "created_at"}
_RELATION_FIELDS = {
    "id",
    "source_question_id",
    "target_question_id",
    "relation_type",
    "created_at",
}


def _timezone_aware_timestamp(name: str, value: Any) -> str:
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


def timestamp_sort_key(value: str) -> datetime:
    """Return a UTC instant for deterministic chronological ordering."""
    cleaned = _timezone_aware_timestamp("timestamp", value)
    return datetime.fromisoformat(cleaned.replace("Z", "+00:00")).astimezone(
        timezone.utc
    )


def _required_text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True, slots=True)
class QuestionNode:
    id: str
    question: str
    source: str
    source_ref: str | None
    created_at: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "QuestionNode":
        if not isinstance(payload, dict):
            raise ValueError("question node payload must be a JSON object")
        missing = sorted(_NODE_FIELDS - payload.keys())
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")
        unknown = sorted(payload.keys() - _NODE_FIELDS)
        if unknown:
            raise ValueError(f"unknown fields: {', '.join(unknown)}")

        source = payload["source"]
        if source not in SOURCE_TYPES:
            raise ValueError("source must be one of: " + ", ".join(SOURCE_TYPES))

        source_ref = payload["source_ref"]
        if source_ref is not None and (
            not isinstance(source_ref, str) or not source_ref.strip()
        ):
            raise ValueError("source_ref must be null or a non-empty string")

        return cls(
            id=_required_text("id", payload["id"]),
            question=_required_text("question", payload["question"]),
            source=source,
            source_ref=source_ref.strip() if isinstance(source_ref, str) else None,
            created_at=_timezone_aware_timestamp("created_at", payload["created_at"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class QuestionRelation:
    id: str
    source_question_id: str
    target_question_id: str
    relation_type: str
    created_at: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "QuestionRelation":
        if not isinstance(payload, dict):
            raise ValueError("question relation payload must be a JSON object")
        missing = sorted(_RELATION_FIELDS - payload.keys())
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")
        unknown = sorted(payload.keys() - _RELATION_FIELDS)
        if unknown:
            raise ValueError(f"unknown fields: {', '.join(unknown)}")

        relation_id = _required_text("id", payload["id"])
        source_question_id = _required_text(
            "source_question_id", payload["source_question_id"]
        )
        target_question_id = _required_text(
            "target_question_id", payload["target_question_id"]
        )
        if source_question_id == target_question_id:
            raise ValueError("relation cannot reference the same question twice")

        relation_type = payload["relation_type"]
        if relation_type not in RELATION_TYPES:
            raise ValueError(
                "relation_type must be one of: " + ", ".join(RELATION_TYPES)
            )

        return cls(
            id=relation_id,
            source_question_id=source_question_id,
            target_question_id=target_question_id,
            relation_type=relation_type,
            created_at=_timezone_aware_timestamp("created_at", payload["created_at"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
