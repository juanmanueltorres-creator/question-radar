import sqlite3

import pytest

from question_radar.decision_storage import InvestigationDecisionStore
from question_radar.decisions import InvestigationDecision
from question_radar.lineage import QuestionNode
from question_radar.lineage_storage import QuestionLineageStore


def node(node_id: str) -> QuestionNode:
    return QuestionNode.from_dict(
        {
            "id": node_id,
            "question": f"Question {node_id}?",
            "source": "manual",
            "source_ref": None,
            "created_at": "2026-09-04T12:00:00-03:00",
        }
    )


def decision(decision_id: str, question_id: str, **overrides) -> InvestigationDecision:
    payload = {
        "id": decision_id,
        "question_id": question_id,
        "decision": "DO_NOW",
        "rationale": "Bounded current investigation.",
        "goal_alignment": True,
        "external_signal": True,
        "testable_now": True,
        "leverage": True,
        "cost": "medium",
        "confidence": "medium",
        "next_test": "Run one bounded test.",
        "resume_when": None,
        "kill_condition": None,
        "supersedes_decision_id": None,
        "created_at": "2026-09-04T12:05:00-03:00",
    }
    payload.update(overrides)
    return InvestigationDecision.from_dict(payload)


def prepared_store(tmp_path, *nodes):
    db = tmp_path / "questions.sqlite3"
    QuestionLineageStore(db).insert_bundle(list(nodes), [])
    return InvestigationDecisionStore(db)


def test_missing_database_does_not_create_file(tmp_path):
    db = tmp_path / "missing.sqlite3"
    with pytest.raises(RuntimeError, match="database does not exist"):
        InvestigationDecisionStore(db).initialize()
    assert not db.exists()


def test_missing_v04_table_does_not_create_v09_table(tmp_path):
    db = tmp_path / "empty.sqlite3"
    sqlite3.connect(db).close()
    with pytest.raises(RuntimeError, match="question_nodes_v04 prerequisite"):
        InvestigationDecisionStore(db).initialize()
    with sqlite3.connect(db) as connection:
        names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert "investigation_decisions_v09" not in names


def test_unsupported_v04_shape_fails_closed(tmp_path):
    db = tmp_path / "bad.sqlite3"
    with sqlite3.connect(db) as connection:
        connection.execute("CREATE TABLE question_nodes_v04 (id TEXT PRIMARY KEY)")
    with pytest.raises(RuntimeError, match="structurally unsupported"):
        InvestigationDecisionStore(db).initialize()


def test_insert_requires_question_and_rejects_duplicate_id(tmp_path):
    store = prepared_store(tmp_path, node("q-a"))
    store.insert(decision("dec-1", "q-a"))
    stored = store.get("dec-1")
    assert stored is not None
    assert stored.id == "dec-1"
    assert stored.goal_alignment is True
    with pytest.raises(ValueError, match="decision id already exists: dec-1"):
        store.insert(decision("dec-1", "q-a"))
    with pytest.raises(ValueError, match="question node not found: missing"):
        store.insert(decision("dec-2", "missing"))


def test_first_decision_must_be_root_and_revision_must_supersede_leaf(tmp_path):
    store = prepared_store(tmp_path, node("q-a"))
    with pytest.raises(ValueError, match="first decision must not supersede"):
        store.insert(decision("bad-root", "q-a", supersedes_decision_id="x"))

    store.insert(decision("dec-1", "q-a"))
    with pytest.raises(ValueError, match="revision must supersede current decision: dec-1"):
        store.insert(decision("dec-2", "q-a"))

    store.insert(
        decision(
            "dec-2",
            "q-a",
            decision="PARKED",
            next_test=None,
            resume_when="A real workload appears.",
            supersedes_decision_id="dec-1",
            created_at="2026-09-04T12:10:00-03:00",
        )
    )
    current = store.get_current("q-a")
    assert current is not None
    assert current.id == "dec-2"


def test_revision_cannot_cross_questions_or_skip_current_leaf(tmp_path):
    store = prepared_store(tmp_path, node("q-a"), node("q-b"))
    store.insert(decision("a-1", "q-a"))
    store.insert(decision("b-1", "q-b"))
    with pytest.raises(ValueError, match="belongs to another question"):
        store.insert(
            decision(
                "a-2",
                "q-a",
                decision="RESEARCH",
                supersedes_decision_id="b-1",
            )
        )
    store.insert(
        decision(
            "a-2",
            "q-a",
            decision="RESEARCH",
            supersedes_decision_id="a-1",
            created_at="2026-09-04T12:10:00-03:00",
        )
    )
    with pytest.raises(ValueError, match="revision must supersede current decision: a-2"):
        store.insert(
            decision(
                "a-3",
                "q-a",
                decision="KILLED",
                next_test=None,
                supersedes_decision_id="a-1",
            )
        )


def test_history_and_current_are_deterministic(tmp_path):
    store = prepared_store(tmp_path, node("q-a"))
    store.insert(
        decision("dec-a", "q-a", created_at="2026-09-04T13:00:00+01:00")
    )
    store.insert(
        decision(
            "dec-b",
            "q-a",
            decision="RESEARCH",
            supersedes_decision_id="dec-a",
            created_at="2026-09-04T09:00:00-03:00",
        )
    )
    assert [item.id for item in store.list_history("q-a")] == ["dec-a", "dec-b"]
    current = store.get_current("q-a")
    assert current is not None
    assert current.id == "dec-b"


def test_get_question_node_and_empty_projections(tmp_path):
    store = prepared_store(tmp_path, node("q-a"))
    assert store.get_question_node("q-a") == node("q-a")
    assert store.get_question_node("missing") is None
    assert store.get_current("q-a") is None
    assert store.list_history("q-a") == []
    assert store.list_current_decisions() == []


def test_list_current_decisions_returns_one_leaf_per_question(tmp_path):
    store = prepared_store(tmp_path, node("q-a"), node("q-b"))
    store.insert(decision("a-1", "q-a", created_at="2026-09-04T12:05:00-03:00"))
    store.insert(
        decision(
            "a-2",
            "q-a",
            decision="PARKED",
            next_test=None,
            resume_when="Condition changes.",
            supersedes_decision_id="a-1",
            created_at="2026-09-04T12:07:00-03:00",
        )
    )
    store.insert(decision("b-1", "q-b", created_at="2026-09-04T12:06:00-03:00"))
    assert [item.id for item in store.list_current_decisions()] == ["b-1", "a-2"]


def test_corrupt_multiple_roots_fail_closed(tmp_path):
    store = prepared_store(tmp_path, node("q-a"))
    store.initialize()
    columns = (
        "id",
        "question_id",
        "decision",
        "rationale",
        "goal_alignment",
        "external_signal",
        "testable_now",
        "leverage",
        "cost",
        "confidence",
        "next_test",
        "resume_when",
        "kill_condition",
        "supersedes_decision_id",
        "created_at",
    )
    with sqlite3.connect(store.db_path) as connection:
        for item in (
            decision("dec-1", "q-a"),
            decision("dec-2", "q-a", created_at="2026-09-04T12:06:00-03:00"),
        ):
            payload = item.to_dict()
            connection.execute(
                "INSERT INTO investigation_decisions_v09 ("
                + ", ".join(columns)
                + ") VALUES ("
                + ", ".join("?" for _ in columns)
                + ")",
                tuple(payload[column] for column in columns),
            )
    with pytest.raises(RuntimeError, match="ambiguous decision history for q-a"):
        store.get_current("q-a")
