import json
from pathlib import Path

from question_radar.handoffs import QuestionResearchHandoff


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "handoffs"
WATER_FIXTURE = FIXTURE_DIR / "question_research_water_san_juan_v01.json"
GITHUB_FIXTURE = FIXTURE_DIR / "question_research_public_github_v01.json"

WATER_QUESTION = (
    "¿Qué decisión recurrente relacionada con agua en San Juan podría mejorar "
    "utilizando evidencia territorial o satelital, quién toma hoy esa decisión "
    "y qué información le falta?"
)
GITHUB_QUESTION = (
    "¿Qué problema público de software geoespacial puedo resolver en un repositorio "
    "externo donde exista una tarea explícita y disponible?"
)

FORBIDDEN_AUTHORITY_KEYS = {
    "buyer",
    "buyer_confirmed",
    "customer",
    "customer_confirmed",
    "job_opening",
    "job_opening_confirmed",
    "contact_permission",
    "contact_permission_granted",
    "task_available",
    "task_availability_confirmed",
}


def _load(path: Path) -> tuple[dict, QuestionResearchHandoff]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload, QuestionResearchHandoff.from_dict(payload)


def _all_keys(value) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for child in value.values():
            keys.update(_all_keys(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(_all_keys(child))
        return keys
    return set()


def test_water_san_juan_fixture_is_research_routed_to_andes() -> None:
    _, handoff = _load(WATER_FIXTURE)

    assert handoff.question.raw == WATER_QUESTION
    assert handoff.question.canonical == WATER_QUESTION
    assert handoff.investigation.decision == "RESEARCH"
    assert handoff.routing.kind == "TERRITORIAL_RESEARCH"
    assert handoff.routing.destination == "andes-context-os"
    assert handoff.source.question_profile_ref is None


def test_public_github_fixture_is_research_routed_to_opportunity_os() -> None:
    _, handoff = _load(GITHUB_FIXTURE)

    assert handoff.question.raw == GITHUB_QUESTION
    assert handoff.question.canonical == GITHUB_QUESTION
    assert handoff.investigation.decision == "RESEARCH"
    assert handoff.routing.kind == "PUBLIC_CONTRIBUTION_RESEARCH"
    assert handoff.routing.destination == "opportunity-os"
    assert handoff.source.question_profile_ref is None


def test_dogfood_handoffs_do_not_claim_downstream_authority() -> None:
    for path in (WATER_FIXTURE, GITHUB_FIXTURE):
        payload, handoff = _load(path)
        assert not (_all_keys(payload) & FORBIDDEN_AUTHORITY_KEYS)
        assert "route != opportunity" in handoff.constraints
        assert "handoff != evidence" in handoff.constraints
        assert "current_at_export != current_now" in handoff.constraints


def test_dogfood_fixtures_are_deterministic_and_sanitized() -> None:
    water_payload, water = _load(WATER_FIXTURE)
    github_payload, github = _load(GITHUB_FIXTURE)

    assert water.handoff_id == "qrh:fixture:water-san-juan:001"
    assert github.handoff_id == "qrh:fixture:public-github:001"
    assert water.created_at == "2026-09-04T21:00:00-03:00"
    assert github.created_at == "2026-09-04T21:05:00-03:00"
    assert water_payload == water.to_dict()
    assert github_payload == github.to_dict()
