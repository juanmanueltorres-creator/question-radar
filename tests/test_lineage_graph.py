import pytest

from question_radar.lineage import QuestionNode, QuestionRelation
from question_radar.lineage_graph import ancestors, descendants


def node(node_id: str, minute: int) -> QuestionNode:
    return QuestionNode.from_dict(
        {
            "id": node_id,
            "question": f"{node_id}?",
            "source": "manual",
            "source_ref": None,
            "created_at": f"2026-08-29T18:{minute:02d}:00-03:00",
        }
    )


def rel(relation_id: str, source: str, target: str, minute: int) -> QuestionRelation:
    return QuestionRelation.from_dict(
        {
            "id": relation_id,
            "source_question_id": source,
            "target_question_id": target,
            "relation_type": "follows_from",
            "created_at": f"2026-08-29T19:{minute:02d}:00-03:00",
        }
    )


def test_ancestors_and_descendants_use_bounded_shortest_hops_and_stable_order():
    nodes = [node("q1", 1), node("q2", 2), node("q3", 3), node("q4", 4), node("q5", 5)]
    relations = [rel("r12", "q1", "q2", 1), rel("r13", "q1", "q3", 2), rel("r24", "q2", "q4", 3), rel("r34", "q3", "q4", 4), rel("r45", "q4", "q5", 5)]
    assert [(item.id, distance) for item, distance in ancestors("q4", nodes, relations, 3)] == [("q2", 1), ("q3", 1), ("q1", 2)]
    assert [(item.id, distance) for item, distance in descendants("q1", nodes, relations, 1)] == [("q2", 1), ("q3", 1)]
    assert [(item.id, distance) for item, distance in descendants("q1", nodes, relations, 3)] == [("q2", 1), ("q3", 1), ("q4", 2), ("q5", 3)]


def test_depth_zero_returns_empty_result():
    nodes = [node("q1", 1), node("q2", 2)]
    relations = [rel("r12", "q1", "q2", 1)]
    assert ancestors("q2", nodes, relations, 0) == []
    assert descendants("q1", nodes, relations, 0) == []


@pytest.mark.parametrize("depth", [-1, 1.5, True, "2"])
def test_invalid_depth_is_rejected(depth):
    with pytest.raises(ValueError, match="max_depth must be a non-negative integer"):
        descendants("q1", [node("q1", 1)], [], depth)


def test_cycles_terminate_and_duplicate_paths_return_each_node_once():
    nodes = [node("q1", 1), node("q2", 2), node("q3", 3), node("q4", 4)]
    relations = [rel("r12", "q1", "q2", 1), rel("r23", "q2", "q3", 2), rel("r31", "q3", "q1", 3), rel("r24", "q2", "q4", 4), rel("r34", "q3", "q4", 5)]
    result = descendants("q1", nodes, relations, 10)
    assert [(item.id, distance) for item, distance in result] == [("q2", 1), ("q3", 2), ("q4", 2)]
    assert all(item.id != "q1" for item, _ in result)


def test_order_uses_distance_then_created_at_then_id():
    nodes = [node("root", 1), node("q-b", 3), node("q-c", 2), node("q-a", 2)]
    relations = [rel("rb", "root", "q-b", 1), rel("rc", "root", "q-c", 2), rel("ra", "root", "q-a", 3)]
    assert [item.id for item, _ in descendants("root", nodes, relations, 1)] == ["q-a", "q-c", "q-b"]


def test_order_compares_timezone_aware_timestamps_by_instant():
    root = QuestionNode.from_dict(
        {
            "id": "root",
            "question": "root?",
            "source": "manual",
            "source_ref": None,
            "created_at": "2025-12-31T12:00:00+00:00",
        }
    )
    earlier = QuestionNode.from_dict(
        {
            "id": "earlier",
            "question": "earlier?",
            "source": "manual",
            "source_ref": None,
            "created_at": "2026-01-01T00:00:00+10:00",
        }
    )
    later = QuestionNode.from_dict(
        {
            "id": "later",
            "question": "later?",
            "source": "manual",
            "source_ref": None,
            "created_at": "2025-12-31T20:00:00-10:00",
        }
    )
    relations = [
        QuestionRelation.from_dict(
            {
                "id": "r-earlier",
                "source_question_id": "root",
                "target_question_id": "earlier",
                "relation_type": "follows_from",
                "created_at": "2025-12-31T12:01:00Z",
            }
        ),
        QuestionRelation.from_dict(
            {
                "id": "r-later",
                "source_question_id": "root",
                "target_question_id": "later",
                "relation_type": "follows_from",
                "created_at": "2025-12-31T12:02:00Z",
            }
        ),
    ]

    assert [item.id for item, _ in descendants("root", [root, earlier, later], relations, 1)] == [
        "earlier",
        "later",
    ]
