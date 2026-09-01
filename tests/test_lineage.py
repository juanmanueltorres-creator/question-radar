import pytest

from question_radar.lineage import (
    RELATION_TYPES,
    SOURCE_TYPES,
    QuestionNode,
    QuestionRelation,
)


def node_payload(**overrides):
    payload = {
        "id": "q-001",
        "question": "¿Qué evidencia necesitamos?",
        "source": "conversation",
        "source_ref": "corpus/example.jsonl",
        "created_at": "2026-08-29T18:29:00-03:00",
    }
    payload.update(overrides)
    return payload


def relation_payload(**overrides):
    payload = {
        "id": "rel-001-002",
        "source_question_id": "q-001",
        "target_question_id": "q-002",
        "relation_type": "refines",
        "created_at": "2026-08-29T18:30:00-03:00",
    }
    payload.update(overrides)
    return payload


def test_question_node_round_trip():
    assert QuestionNode.from_dict(node_payload()).to_dict() == node_payload()


@pytest.mark.parametrize("source", ("manual", "conversation", "corpus", "external"))
def test_question_node_accepts_every_source(source):
    assert QuestionNode.from_dict(node_payload(source=source)).source == source


def test_source_vocabulary_is_frozen():
    assert SOURCE_TYPES == ("manual", "conversation", "corpus", "external")


def test_question_node_accepts_null_source_ref():
    assert QuestionNode.from_dict(node_payload(source_ref=None)).source_ref is None


def test_question_node_trims_outer_whitespace_without_rewriting_wording():
    node = QuestionNode.from_dict(node_payload(question="  ¿Qué evidencia necesitamos?  "))
    assert node.question == "¿Qué evidencia necesitamos?"


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({k: v for k, v in node_payload().items() if k != "question"}, "missing required fields"),
        (node_payload(extra="x"), "unknown fields"),
        (node_payload(id="   "), "id must be a non-empty string"),
        (node_payload(question="   "), "question must be a non-empty string"),
        (node_payload(source_ref="   "), "source_ref must be null or a non-empty string"),
        (node_payload(source="chatgpt_memory"), "source must be one of"),
        (node_payload(created_at="not-a-time"), "timezone-aware"),
        (node_payload(created_at="2026-08-29T18:29:00"), "timezone-aware"),
    ],
)
def test_question_node_rejects_invalid_payloads(payload, message):
    with pytest.raises(ValueError, match=message):
        QuestionNode.from_dict(payload)


def test_relation_vocabulary_is_frozen():
    assert RELATION_TYPES == (
        "refines",
        "decomposes",
        "generalizes",
        "operationalizes",
        "challenges_assumption",
        "contrasts",
        "follows_from",
    )


@pytest.mark.parametrize("relation_type", RELATION_TYPES)
def test_relation_accepts_every_type(relation_type):
    relation = QuestionRelation.from_dict(relation_payload(relation_type=relation_type))
    assert relation.relation_type == relation_type


def test_relation_round_trip():
    assert QuestionRelation.from_dict(relation_payload()).to_dict() == relation_payload()


def test_relation_rejects_self_reference():
    with pytest.raises(ValueError, match="same question"):
        QuestionRelation.from_dict(
            relation_payload(source_question_id="q-001", target_question_id="q-001")
        )


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({k: v for k, v in relation_payload().items() if k != "relation_type"}, "missing required fields"),
        (relation_payload(extra="x"), "unknown fields"),
        (relation_payload(id="   "), "id must be a non-empty string"),
        (relation_payload(source_question_id="   "), "source_question_id must be a non-empty string"),
        (relation_payload(target_question_id="   "), "target_question_id must be a non-empty string"),
        (relation_payload(relation_type="causes"), "relation_type must be one of"),
        (relation_payload(created_at="not-a-time"), "timezone-aware"),
        (relation_payload(created_at="2026-08-29T18:30:00"), "timezone-aware"),
    ],
)
def test_relation_rejects_invalid_payloads(payload, message):
    with pytest.raises(ValueError, match=message):
        QuestionRelation.from_dict(payload)
