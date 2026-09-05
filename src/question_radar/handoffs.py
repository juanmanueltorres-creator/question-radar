from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from typing import Any

from question_radar.decisions import InvestigationDecision
from question_radar.lineage import QuestionNode


HANDOFF_CONTRACT = "question-research-handoff/v0.1"
ACTIONABLE_DECISIONS = ("DO_NOW", "RESEARCH")
DESTINATION_BY_ROUTE = {
    "TERRITORIAL_RESEARCH": "andes-context-os",
    "PUBLIC_CONTRIBUTION_RESEARCH": "opportunity-os",
}

_TOP_LEVEL_FIELDS = {
    "contract",
    "handoff_id",
    "created_at",
    "source",
    "question",
    "investigation",
    "routing",
    "constraints",
}
_SOURCE_FIELDS = {
    "system",
    "question_id",
    "question_profile_ref",
    "decision_id",
    "decision_fingerprint",
}
_QUESTION_FIELDS = {"raw", "canonical"}
_INVESTIGATION_FIELDS = {"decision", "rationale", "next_test"}
_ROUTING_FIELDS = {"kind", "destination"}


def _require_fields(
    payload: dict[str, Any], *, required: set[str], allowed: set[str]
) -> None:
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")
    unknown = sorted(payload.keys() - allowed)
    if unknown:
        raise ValueError(f"unknown fields: {', '.join(unknown)}")


def _require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a JSON object")
    return value


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field)


def _require_aware_iso8601(value: Any, field: str) -> str:
    text = _require_text(value, field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be a timezone-aware ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must be a timezone-aware ISO timestamp")
    return text


def _require_string_list(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    return tuple(_require_text(item, field) for item in value)


def _require_fingerprint(value: Any) -> str:
    text = _require_text(value, "source.decision_fingerprint")
    prefix = "sha256:"
    digest = text.removeprefix(prefix)
    if not text.startswith(prefix) or len(digest) != 64:
        raise ValueError("source.decision_fingerprint must be sha256:<64 hex chars>")
    try:
        int(digest, 16)
    except ValueError as exc:
        raise ValueError(
            "source.decision_fingerprint must be sha256:<64 hex chars>"
        ) from exc
    return text


@dataclass(frozen=True, slots=True)
class HandoffSource:
    system: str
    question_id: str
    question_profile_ref: str | None
    decision_id: str
    decision_fingerprint: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "HandoffSource":
        _require_fields(payload, required=_SOURCE_FIELDS, allowed=_SOURCE_FIELDS)
        system = _require_text(payload["system"], "source.system")
        if system != "question-radar":
            raise ValueError("source.system must be question-radar")
        return cls(
            system=system,
            question_id=_require_text(payload["question_id"], "source.question_id"),
            question_profile_ref=_optional_text(
                payload["question_profile_ref"], "source.question_profile_ref"
            ),
            decision_id=_require_text(payload["decision_id"], "source.decision_id"),
            decision_fingerprint=_require_fingerprint(payload["decision_fingerprint"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "system": self.system,
            "question_id": self.question_id,
            "question_profile_ref": self.question_profile_ref,
            "decision_id": self.decision_id,
            "decision_fingerprint": self.decision_fingerprint,
        }


@dataclass(frozen=True, slots=True)
class HandoffQuestion:
    raw: str
    canonical: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "HandoffQuestion":
        _require_fields(payload, required=_QUESTION_FIELDS, allowed=_QUESTION_FIELDS)
        return cls(
            raw=_require_text(payload["raw"], "question.raw"),
            canonical=_require_text(payload["canonical"], "question.canonical"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"raw": self.raw, "canonical": self.canonical}


@dataclass(frozen=True, slots=True)
class HandoffInvestigation:
    decision: str
    rationale: str
    next_test: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "HandoffInvestigation":
        _require_fields(
            payload,
            required=_INVESTIGATION_FIELDS,
            allowed=_INVESTIGATION_FIELDS,
        )
        decision = _require_text(payload["decision"], "investigation.decision")
        if decision not in ACTIONABLE_DECISIONS:
            raise ValueError(
                "investigation.decision must be one of: "
                + ", ".join(ACTIONABLE_DECISIONS)
            )
        return cls(
            decision=decision,
            rationale=_require_text(payload["rationale"], "investigation.rationale"),
            next_test=_require_text(payload["next_test"], "investigation.next_test"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "rationale": self.rationale,
            "next_test": self.next_test,
        }


@dataclass(frozen=True, slots=True)
class HandoffRouting:
    kind: str
    destination: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "HandoffRouting":
        _require_fields(payload, required=_ROUTING_FIELDS, allowed=_ROUTING_FIELDS)
        kind = _require_text(payload["kind"], "routing.kind")
        if kind not in DESTINATION_BY_ROUTE:
            raise ValueError("routing.kind is unsupported")
        destination = _require_text(payload["destination"], "routing.destination")
        if destination != DESTINATION_BY_ROUTE[kind]:
            raise ValueError("routing.destination does not match routing.kind")
        return cls(kind=kind, destination=destination)

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "destination": self.destination}


@dataclass(frozen=True, slots=True)
class QuestionResearchHandoff:
    contract: str
    handoff_id: str
    created_at: str
    source: HandoffSource
    question: HandoffQuestion
    investigation: HandoffInvestigation
    routing: HandoffRouting
    constraints: tuple[str, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "QuestionResearchHandoff":
        payload = _require_object(payload, "handoff")
        _require_fields(
            payload,
            required=_TOP_LEVEL_FIELDS,
            allowed=_TOP_LEVEL_FIELDS,
        )
        contract = _require_text(payload["contract"], "contract")
        if contract != HANDOFF_CONTRACT:
            raise ValueError(f"contract must be {HANDOFF_CONTRACT}")
        return cls(
            contract=contract,
            handoff_id=_require_text(payload["handoff_id"], "handoff_id"),
            created_at=_require_aware_iso8601(payload["created_at"], "created_at"),
            source=HandoffSource.from_dict(
                _require_object(payload["source"], "source")
            ),
            question=HandoffQuestion.from_dict(
                _require_object(payload["question"], "question")
            ),
            investigation=HandoffInvestigation.from_dict(
                _require_object(payload["investigation"], "investigation")
            ),
            routing=HandoffRouting.from_dict(
                _require_object(payload["routing"], "routing")
            ),
            constraints=_require_string_list(payload["constraints"], "constraints"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "handoff_id": self.handoff_id,
            "created_at": self.created_at,
            "source": self.source.to_dict(),
            "question": self.question.to_dict(),
            "investigation": self.investigation.to_dict(),
            "routing": self.routing.to_dict(),
            "constraints": list(self.constraints),
        }


def decision_fingerprint(
    node: QuestionNode, decision: InvestigationDecision
) -> str:
    payload = {
        "question": node.to_dict(),
        "decision": decision.to_dict(),
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()
