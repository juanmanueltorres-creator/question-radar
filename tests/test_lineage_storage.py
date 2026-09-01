import sqlite3

import pytest

from question_radar.lineage import QuestionNode, QuestionRelation
from question_radar.lineage_storage import QuestionLineageStore


def node(node_id: str, created_at: str = "2026-08-29T18:00:00-03:00") -> QuestionNode:
    return QuestionNode.from_dict(
        {
            "id": node_id,
            "question": f"Question {node_id}?",
            "source": "manual",
            "source_ref": None,
            "created_at": created_at,
        }
    )


def relation(
    relation_id: str,
    source: str,
    target: str,
    relation_type: str = "refines",
    created_at: str = "2026-08-29T18:10:00-03:00",
) -> QuestionRelation:
    return QuestionRelation.from_dict(
        {
            "id": relation_id,
            "source_question_id": source,
            "target_question_id": target,
            "relation_type": relation_type,
            "created_at": created_at,
        }
    )


def test_node_insert_get_and_list_are_deterministic(tmp_path):
    store = QuestionLineageStore(tmp_path / "lineage.sqlite3")
    node_b = node("q-b", "2026-08-29T18:02:00-03:00")
    node_a = node("q-a", "2026-08-29T18:01:00-03:00")
    node_c = node("q-c", "2026-08-29T18:02:00-03:00")

    store.insert_node(node_b)
    store.insert_node(node_c)
    store.insert_node(node_a)

    assert store.get_node("q-a") == node_a
    assert store.get_node("missing") is None
    assert [item.id for item in store.list_nodes()] == ["q-a", "q-b", "q-c"]


def test_relation_insert_get_list_filter_and_order(tmp_path):
    store = QuestionLineageStore(tmp_path / "lineage.sqlite3")
    for item in (node("q-a"), node("q-b"), node("q-c")):
        store.insert_node(item)
    later = relation("r-2", "q-b", "q-c", created_at="2026-08-29T18:12:00-03:00")
    earlier_b = relation("r-b", "q-a", "q-b", created_at="2026-08-29T18:11:00-03:00")
    earlier_a = relation("r-a", "q-c", "q-a", "contrasts", "2026-08-29T18:11:00-03:00")

    store.insert_relation(later)
    store.insert_relation(earlier_b)
    store.insert_relation(earlier_a)

    assert store.get_relation("r-a") == earlier_a
    assert store.get_relation("missing") is None
    assert [item.id for item in store.list_relations()] == ["r-a", "r-b", "r-2"]
    assert [item.id for item in store.list_relations("q-a")] == ["r-a", "r-b"]


def test_relation_requires_existing_source_and_target(tmp_path):
    store = QuestionLineageStore(tmp_path / "lineage.sqlite3")
    store.insert_node(node("q-a"))

    with pytest.raises(ValueError, match="question node not found: missing-source"):
        store.insert_relation(relation("r-source", "missing-source", "q-a"))

    with pytest.raises(ValueError, match="question node not found: missing-target"):
        store.insert_relation(relation("r-target", "q-a", "missing-target"))


def test_duplicate_node_id_is_rejected(tmp_path):
    store = QuestionLineageStore(tmp_path / "lineage.sqlite3")
    store.insert_node(node("q-a"))
    with pytest.raises(ValueError, match="node id already exists"):
        store.insert_node(node("q-a"))


def test_duplicate_relation_id_is_rejected(tmp_path):
    store = QuestionLineageStore(tmp_path / "lineage.sqlite3")
    store.insert_bundle([node("q-a"), node("q-b"), node("q-c")], [])
    store.insert_relation(relation("r-1", "q-a", "q-b"))
    with pytest.raises(ValueError, match="relation id already exists"):
        store.insert_relation(relation("r-1", "q-b", "q-c"))


def test_duplicate_relation_triple_is_rejected(tmp_path):
    store = QuestionLineageStore(tmp_path / "lineage.sqlite3")
    store.insert_bundle([node("q-a"), node("q-b")], [])
    store.insert_relation(relation("r-1", "q-a", "q-b", "refines"))
    with pytest.raises(ValueError, match="duplicate relation"):
        store.insert_relation(relation("r-2", "q-a", "q-b", "refines"))


def test_duplicate_ids_inside_bundle_are_rejected_before_writes(tmp_path):
    store = QuestionLineageStore(tmp_path / "lineage.sqlite3")
    with pytest.raises(ValueError, match="duplicate node id in bundle: q-a"):
        store.insert_bundle([node("q-a"), node("q-a")], [])
    assert store.list_nodes() == []


def test_duplicate_relation_triples_inside_bundle_are_rejected_before_writes(tmp_path):
    store = QuestionLineageStore(tmp_path / "lineage.sqlite3")
    with pytest.raises(ValueError, match="duplicate relation in bundle"):
        store.insert_bundle(
            [node("q-a"), node("q-b")],
            [relation("r-1", "q-a", "q-b"), relation("r-2", "q-a", "q-b")],
        )
    assert store.list_nodes() == []
    assert store.list_relations() == []


def test_invalid_endpoint_rolls_back_entire_bundle(tmp_path):
    store = QuestionLineageStore(tmp_path / "lineage.sqlite3")
    with pytest.raises(ValueError, match="question node not found: missing-q"):
        store.insert_bundle(
            [node("q-a"), node("q-b")],
            [
                relation("r-valid", "q-a", "q-b"),
                relation("r-invalid", "q-b", "missing-q"),
            ],
        )
    assert store.list_nodes() == []
    assert store.list_relations() == []


def test_database_schema_rejects_self_relation_defense_in_depth(tmp_path):
    store = QuestionLineageStore(tmp_path / "lineage.sqlite3")
    store.insert_node(node("q-a"))
    store.initialize()

    with sqlite3.connect(store.db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO question_relations_v04 "
                "(id, source_question_id, target_question_id, relation_type, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    "r-self",
                    "q-a",
                    "q-a",
                    "refines",
                    "2026-08-29T18:20:00-03:00",
                ),
            )


def test_list_order_compares_timezone_aware_timestamps_by_instant(tmp_path):
    store = QuestionLineageStore(tmp_path / "lineage.sqlite3")
    store.insert_bundle(
        [
            node("earlier", "2026-01-01T00:00:00+10:00"),
            node("later", "2025-12-31T20:00:00-10:00"),
        ],
        [
            relation(
                "r-later",
                "earlier",
                "later",
                created_at="2025-12-31T20:00:00-10:00",
            ),
            relation(
                "r-earlier",
                "later",
                "earlier",
                "contrasts",
                "2026-01-01T00:00:00+10:00",
            ),
        ],
    )

    assert [item.id for item in store.list_nodes()] == ["earlier", "later"]
    assert [item.id for item in store.list_relations()] == ["r-earlier", "r-later"]


def test_initialize_wraps_sqlite_database_errors(tmp_path):
    db_path = tmp_path / "broken.sqlite3"
    db_path.write_text("this is not a SQLite database", encoding="utf-8")
    store = QuestionLineageStore(db_path)

    with pytest.raises(RuntimeError, match="cannot initialize SQLite database"):
        store.initialize()
