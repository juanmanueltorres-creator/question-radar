import pytest

from question_radar.profiles import QuestionProfile, calculate_formulation_score


def valid_payload() -> dict:
    return {
        "id": "qv2-001",
        "question": "¿Qué es un KPI?",
        "question_type": "factual_conceptual",
        "readiness": "ready_to_answer",
        "clarity": 5,
        "boundedness": 5,
        "investigability": 5,
        "epistemic_openness": 5,
        "purpose_fit": 5,
        "formulation_score": 100,
        "depth": 1,
        "connections": 2,
        "generativity": 2,
        "strengths": "Pregunta conceptual precisa y directamente respondible.",
        "gap": "Puede necesitar contexto de dominio para explicar qué KPI importa.",
        "assumptions": "Asume que KPI tiene un significado relevante para el contexto del usuario.",
        "evidence_required": "Definición fiable y ejemplos del dominio si aplica.",
        "next_question": "¿Qué KPI sería útil para esta decisión concreta y por qué?",
        "topic": "alfabetizacion_tecnica",
        "evaluator": "chatgpt-gpt-5.6-sol",
        "rubric_version": "v0.2",
        "created_at": "2026-08-29T18:26:00-03:00",
    }


def test_calculate_formulation_score_is_deterministic():
    assert calculate_formulation_score({
        "clarity": 4,
        "boundedness": 3,
        "investigability": 5,
        "epistemic_openness": 4,
        "purpose_fit": 5,
    }) == 84


def test_valid_profile_round_trips():
    payload = valid_payload()
    profile = QuestionProfile.from_dict(payload)
    assert profile.to_dict() == payload


@pytest.mark.parametrize("field", ["id", "question", "question_type", "readiness", "strengths", "gap", "assumptions", "evidence_required", "next_question", "evaluator", "rubric_version", "created_at"])
def test_missing_required_field_is_rejected(field):
    payload = valid_payload()
    payload.pop(field)
    with pytest.raises(ValueError, match="missing required fields"):
        QuestionProfile.from_dict(payload)


def test_unknown_field_is_rejected():
    payload = valid_payload()
    payload["surprise"] = "nope"
    with pytest.raises(ValueError, match="unknown fields"):
        QuestionProfile.from_dict(payload)


@pytest.mark.parametrize("question_type", ["", "mystery", None])
def test_invalid_question_type_is_rejected(question_type):
    payload = valid_payload()
    payload["question_type"] = question_type
    with pytest.raises(ValueError, match="question_type"):
        QuestionProfile.from_dict(payload)


@pytest.mark.parametrize("readiness", ["", "done", None])
def test_invalid_readiness_is_rejected(readiness):
    payload = valid_payload()
    payload["readiness"] = readiness
    with pytest.raises(ValueError, match="readiness"):
        QuestionProfile.from_dict(payload)


@pytest.mark.parametrize("field", ["clarity", "boundedness", "investigability", "epistemic_openness", "purpose_fit", "depth", "connections", "generativity"])
@pytest.mark.parametrize("bad_value", [-1, 6, 2.5, True, "5"])
def test_invalid_numeric_value_is_rejected(field, bad_value):
    payload = valid_payload()
    payload[field] = bad_value
    with pytest.raises(ValueError, match=field):
        QuestionProfile.from_dict(payload)


@pytest.mark.parametrize("field", ["id", "question", "strengths", "gap", "assumptions", "evidence_required", "next_question", "evaluator"])
def test_empty_required_text_is_rejected(field):
    payload = valid_payload()
    payload[field] = "   "
    with pytest.raises(ValueError, match=field):
        QuestionProfile.from_dict(payload)


def test_topic_may_be_null_but_not_blank():
    payload = valid_payload()
    payload["topic"] = None
    assert QuestionProfile.from_dict(payload).topic is None

    payload = valid_payload()
    payload["topic"] = " "
    with pytest.raises(ValueError, match="topic"):
        QuestionProfile.from_dict(payload)


@pytest.mark.parametrize("created_at", ["not-a-date", "2026-08-29T18:26:00"])
def test_timestamp_must_be_valid_and_timezone_aware(created_at):
    payload = valid_payload()
    payload["created_at"] = created_at
    with pytest.raises(ValueError, match="created_at"):
        QuestionProfile.from_dict(payload)


def test_unsupported_rubric_version_is_rejected():
    payload = valid_payload()
    payload["rubric_version"] = "v0.1"
    with pytest.raises(ValueError, match="rubric_version"):
        QuestionProfile.from_dict(payload)


def test_mismatched_formulation_score_is_rejected():
    payload = valid_payload()
    payload["formulation_score"] = 96
    with pytest.raises(ValueError, match="formulation_score mismatch"):
        QuestionProfile.from_dict(payload)


def test_non_integer_formulation_score_is_rejected():
    payload = valid_payload()
    payload["formulation_score"] = True
    with pytest.raises(ValueError, match="formulation_score must be an integer"):
        QuestionProfile.from_dict(payload)
