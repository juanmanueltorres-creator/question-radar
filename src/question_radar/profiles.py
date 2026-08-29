from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

QUESTION_TYPES = (
    "factual_conceptual",
    "operational_diagnostic",
    "scientific_explanatory",
    "decision_risk",
    "epistemological_meta",
    "normative_political",
    "generative_philosophical",
)

READINESS_STATES = (
    "ready_to_answer",
    "ready_to_investigate",
    "needs_context",
    "exploratory",
)

FORMULATION_FIELDS = (
    "clarity",
    "boundedness",
    "investigability",
    "epistemic_openness",
    "purpose_fit",
)

TRAIT_FIELDS = (
    "depth",
    "connections",
    "generativity",
)

_PROFILE_FIELDS = {
    "id",
    "question",
    "question_type",
    "readiness",
    *FORMULATION_FIELDS,
    "formulation_score",
    *TRAIT_FIELDS,
    "strengths",
    "gap",
    "assumptions",
    "evidence_required",
    "next_question",
    "topic",
    "evaluator",
    "rubric_version",
    "created_at",
}

_REQUIRED_TEXT_FIELDS = (
    "id",
    "question",
    "strengths",
    "gap",
    "assumptions",
    "evidence_required",
    "next_question",
    "evaluator",
)


def _validated_scale_value(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer from 0 to 5")
    if not 0 <= value <= 5:
        raise ValueError(f"{name} must be between 0 and 5")
    return value


def calculate_formulation_score(dimensions: Mapping[str, int]) -> int:
    missing = [name for name in FORMULATION_FIELDS if name not in dimensions]
    if missing:
        raise ValueError(f"missing formulation dimensions: {', '.join(missing)}")

    values = [
        _validated_scale_value(name, dimensions[name])
        for name in FORMULATION_FIELDS
    ]
    return int(round(sum(values) / 25 * 100))


@dataclass(frozen=True, slots=True)
class QuestionProfile:
    id: str
    question: str
    question_type: str
    readiness: str
    clarity: int
    boundedness: int
    investigability: int
    epistemic_openness: int
    purpose_fit: int
    formulation_score: int
    depth: int
    connections: int
    generativity: int
    strengths: str
    gap: str
    assumptions: str
    evidence_required: str
    next_question: str
    topic: str | None
    evaluator: str
    rubric_version: str
    created_at: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "QuestionProfile":
        missing = sorted(_PROFILE_FIELDS - payload.keys())
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")

        unknown = sorted(payload.keys() - _PROFILE_FIELDS)
        if unknown:
            raise ValueError(f"unknown fields: {', '.join(unknown)}")

        for field in _REQUIRED_TEXT_FIELDS:
            value = payload[field]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty string")

        question_type = payload["question_type"]
        if question_type not in QUESTION_TYPES:
            raise ValueError(
                "question_type must be one of: " + ", ".join(QUESTION_TYPES)
            )

        readiness = payload["readiness"]
        if readiness not in READINESS_STATES:
            raise ValueError(
                "readiness must be one of: " + ", ".join(READINESS_STATES)
            )

        topic = payload["topic"]
        if topic is not None and (not isinstance(topic, str) or not topic.strip()):
            raise ValueError("topic must be null or a non-empty string")

        rubric_version = payload["rubric_version"]
        if rubric_version != "v0.2":
            raise ValueError("rubric_version must be v0.2")

        created_at = payload["created_at"]
        if not isinstance(created_at, str) or not created_at.strip():
            raise ValueError("created_at must be a non-empty string")
        try:
            parsed = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(
                "created_at must be a valid timezone-aware ISO timestamp"
            ) from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("created_at must be a valid timezone-aware ISO timestamp")

        for field in (*FORMULATION_FIELDS, *TRAIT_FIELDS):
            _validated_scale_value(field, payload[field])

        expected_score = calculate_formulation_score(
            {name: payload[name] for name in FORMULATION_FIELDS}
        )
        supplied_score = payload["formulation_score"]
        if isinstance(supplied_score, bool) or not isinstance(supplied_score, int):
            raise ValueError("formulation_score must be an integer")
        if supplied_score != expected_score:
            raise ValueError(
                "formulation_score mismatch: "
                f"supplied {supplied_score}, expected {expected_score}"
            )

        return cls(
            id=payload["id"].strip(),
            question=payload["question"].strip(),
            question_type=question_type,
            readiness=readiness,
            clarity=payload["clarity"],
            boundedness=payload["boundedness"],
            investigability=payload["investigability"],
            epistemic_openness=payload["epistemic_openness"],
            purpose_fit=payload["purpose_fit"],
            formulation_score=supplied_score,
            depth=payload["depth"],
            connections=payload["connections"],
            generativity=payload["generativity"],
            strengths=payload["strengths"].strip(),
            gap=payload["gap"].strip(),
            assumptions=payload["assumptions"].strip(),
            evidence_required=payload["evidence_required"].strip(),
            next_question=payload["next_question"].strip(),
            topic=topic.strip() if isinstance(topic, str) else None,
            evaluator=payload["evaluator"].strip(),
            rubric_version=rubric_version,
            created_at=created_at,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
