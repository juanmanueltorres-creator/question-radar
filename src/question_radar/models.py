from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from question_radar.scoring import DIMENSION_FIELDS, normalized_score

_REQUIRED_FIELDS = {
    "id",
    "question",
    *DIMENSION_FIELDS,
    "score",
    "strengths",
    "gap",
    "next_question",
    "evaluator",
    "rubric_version",
    "created_at",
}

_REQUIRED_TEXT_FIELDS = (
    "id",
    "question",
    "strengths",
    "gap",
    "next_question",
    "evaluator",
    "rubric_version",
    "created_at",
)


@dataclass(frozen=True, slots=True)
class QuestionEvaluation:
    id: str
    question: str
    clarity: int
    depth: int
    investigability: int
    assumption_challenge: int
    connections: int
    score: int
    strengths: str
    gap: str
    next_question: str
    topic: str | None
    evaluator: str
    rubric_version: str
    created_at: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "QuestionEvaluation":
        missing = sorted(_REQUIRED_FIELDS - payload.keys())
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")

        for field in _REQUIRED_TEXT_FIELDS:
            value = payload[field]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty string")

        topic = payload.get("topic")
        if topic is not None and (not isinstance(topic, str) or not topic.strip()):
            raise ValueError("topic must be null or a non-empty string")

        if payload["rubric_version"] != "v0.1":
            raise ValueError("rubric_version must be v0.1")

        try:
            datetime.fromisoformat(payload["created_at"].replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("created_at must be a valid ISO timestamp") from exc

        dimension_values = {name: payload[name] for name in DIMENSION_FIELDS}
        expected_score = normalized_score(dimension_values)

        supplied_score = payload["score"]
        if isinstance(supplied_score, bool) or not isinstance(supplied_score, int):
            raise ValueError("score must be an integer")
        if supplied_score != expected_score:
            raise ValueError(
                f"score mismatch: supplied {supplied_score}, expected {expected_score}"
            )

        return cls(
            id=payload["id"].strip(),
            question=payload["question"].strip(),
            clarity=payload["clarity"],
            depth=payload["depth"],
            investigability=payload["investigability"],
            assumption_challenge=payload["assumption_challenge"],
            connections=payload["connections"],
            score=supplied_score,
            strengths=payload["strengths"].strip(),
            gap=payload["gap"].strip(),
            next_question=payload["next_question"].strip(),
            topic=topic.strip() if isinstance(topic, str) else None,
            evaluator=payload["evaluator"].strip(),
            rubric_version=payload["rubric_version"],
            created_at=payload["created_at"],
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
