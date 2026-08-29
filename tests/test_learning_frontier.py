from question_radar.learning import LearningObservation
from question_radar.learning_frontier import render_learning_frontier


SECTIONS = (
    "RECURRING SIGNALS",
    "CONSOLIDATING",
    "APPLIED",
    "EMERGING FRONTIER",
    "NO LONGER OBSERVED",
)


def observation(identifier: str, concept: str, state: str) -> LearningObservation:
    return LearningObservation.from_dict(
        {
            "id": identifier,
            "concept": concept,
            "gap_type": "connection",
            "state": state,
            "confidence": "medium",
            "evidence_question_ids": [f"{identifier}-q2", f"{identifier}-q1"],
            "interpretation": "Stored evidence supports this revisable observation.",
            "suggested_next_step": "Generate new evidence in another context.",
            "created_at": "2026-08-29T18:30:00-03:00",
            "updated_at": "2026-08-29T18:35:00-03:00",
        }
    )


def test_frontier_renders_all_sections_in_fixed_order():
    observations = [
        observation("r", "recurring", "recurring_gap"),
        observation("c", "consolidating", "consolidating"),
        observation("a", "applied", "applied"),
        observation("p", "emerging", "possible_gap"),
        observation("n", "old", "no_longer_observed"),
    ]
    rendered = render_learning_frontier(observations)
    positions = [rendered.index(section) for section in SECTIONS]
    assert positions == sorted(positions)
    for item in observations:
        assert item.concept in rendered
        assert item.gap_type in rendered
        assert item.confidence in rendered
        assert "evidence=2" in rendered
        assert ", ".join(item.evidence_question_ids) in rendered


def test_frontier_sorts_items_by_concept_then_id_within_section():
    rendered = render_learning_frontier(
        [
            observation("z-2", "zeta", "possible_gap"),
            observation("a-2", "alpha", "possible_gap"),
            observation("a-1", "alpha", "possible_gap"),
        ]
    )
    assert rendered.index("a-1-q2") < rendered.index("a-2-q2") < rendered.index("z-2-q2")


def test_empty_frontier_shows_none_in_every_section():
    rendered = render_learning_frontier([])
    assert all(section in rendered for section in SECTIONS)
    assert rendered.count("(none)") == 5


def test_frontier_never_invents_concepts():
    rendered = render_learning_frontier(
        [observation("real", "stored_concept", "possible_gap")]
    )
    assert "stored_concept" in rendered
    assert "invented_concept" not in rendered
