import pytest

from question_radar.learning import (
    CONFIDENCE_LEVELS,
    GAP_TYPES,
    LEARNING_STATES,
    LearningObservation,
)


def payload(**changes):
    data = {
        "id": "learning-001",
        "concept": "question_evaluation_models",
        "gap_type": "connection",
        "state": "consolidating",
        "confidence": "medium",
        "evidence_question_ids": [
            "chat-2026-08-29-004",
            "chat-2026-08-29-009",
        ],
        "interpretation": (
            "Several questions separate quality, breadth, and readiness, "
            "compatible with active consolidation."
        ),
        "suggested_next_step": (
            "Apply the same distinctions to a new domain and explain which criteria change."
        ),
        "created_at": "2026-08-29T18:30:00-03:00",
        "updated_at": "2026-08-29T18:35:00-03:00",
    }
    data.update(changes)
    return data


def test_closed_vocabularies_are_exact():
    assert GAP_TYPES == (
        "conceptual",
        "terminology",
        "procedural",
        "connection",
        "evidence",
        "transfer",
    )
    assert LEARNING_STATES == (
        "possible_gap",
        "recurring_gap",
        "consolidating",
        "applied",
        "no_longer_observed",
    )
    assert CONFIDENCE_LEVELS == ("low", "medium", "high")


def test_round_trip_preserves_order():
    item = LearningObservation.from_dict(payload())
    assert item.evidence_question_ids == (
        "chat-2026-08-29-004",
        "chat-2026-08-29-009",
    )
    assert item.to_dict()["evidence_question_ids"] == [
        "chat-2026-08-29-004",
        "chat-2026-08-29-009",
    ]


def test_unknown_but_nonempty_evidence_id_is_allowed():
    item = LearningObservation.from_dict(
        payload(evidence_question_ids=["not-loaded-here"])
    )
    assert item.evidence_question_ids == ("not-loaded-here",)


def test_duplicate_evidence_after_trimming_is_rejected():
    with pytest.raises(ValueError, match="duplicate evidence"):
        LearningObservation.from_dict(
            payload(evidence_question_ids=["q-1", " q-1 "])
        )


def test_empty_evidence_is_rejected():
    with pytest.raises(ValueError, match="evidence_question_ids"):
        LearningObservation.from_dict(payload(evidence_question_ids=[]))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("gap_type", "memory"),
        ("state", "mastered"),
        ("confidence", "certain"),
    ],
)
def test_unknown_closed_vocabulary_is_rejected(field, value):
    with pytest.raises(ValueError, match=field):
        LearningObservation.from_dict(payload(**{field: value}))


@pytest.mark.parametrize(
    "field",
    ["id", "concept", "interpretation", "suggested_next_step"],
)
def test_empty_required_text_is_rejected(field):
    with pytest.raises(ValueError, match=field):
        LearningObservation.from_dict(payload(**{field: "   "}))


def test_missing_field_is_rejected():
    data = payload()
    data.pop("concept")
    with pytest.raises(ValueError, match="missing required fields: concept"):
        LearningObservation.from_dict(data)


def test_unknown_field_is_rejected():
    with pytest.raises(ValueError, match="unknown fields: learner_score"):
        LearningObservation.from_dict(payload(learner_score=99))


def test_evidence_must_be_a_list():
    with pytest.raises(ValueError, match="non-empty list"):
        LearningObservation.from_dict(payload(evidence_question_ids=("q-1",)))


def test_evidence_ids_must_be_nonempty_strings():
    with pytest.raises(ValueError, match="non-empty strings"):
        LearningObservation.from_dict(payload(evidence_question_ids=["q-1", " "]))


def test_naive_timestamp_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        LearningObservation.from_dict(payload(created_at="2026-08-29T18:30:00"))


def test_malformed_timestamp_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        LearningObservation.from_dict(payload(updated_at="not-a-date"))


def test_updated_before_created_is_rejected():
    with pytest.raises(ValueError, match="updated_at"):
        LearningObservation.from_dict(
            payload(
                created_at="2026-08-29T19:00:00-03:00",
                updated_at="2026-08-29T18:00:00-03:00",
            )
        )


def test_non_object_payload_is_rejected():
    with pytest.raises(ValueError, match="JSON object"):
        LearningObservation.from_dict([])
