# Investigation Decision Gate v0.9 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a persistent, auditable, append-only investigation decision layer that records `DO_NOW`, `RESEARCH`, `PARKED`, and `KILLED` judgments for existing v0.4 question nodes without granting Question Radar automatic prioritization authority.

**Architecture:** Add four isolated v0.9 modules: an immutable decision contract, a SQLite-backed decision store with fail-closed v0.4 prerequisite checks and linear supersession history, deterministic Markdown/JSON rendering, and a new CLI facade that delegates all historical commands to the existing v0.8 facade. v0.9 owns only `investigation_decisions_v09`; current state is always derived from immutable history, and the WIP rule is advisory only.

**Tech Stack:** Python 3.11+, standard library only, `dataclasses`, `sqlite3`, `argparse`, `json`, `uuid`, `datetime`, `pytest>=8,<9` for development.

**Spec:** `docs/superpowers/specs/2026-09-04-investigation-decision-gate-v0.9-design.md`

## Global Constraints

- Decision states are exactly `DO_NOW`, `RESEARCH`, `PARKED`, `KILLED`.
- Cost values are exactly `low`, `medium`, `high`.
- Confidence values are exactly `low`, `medium`, `high`.
- Runtime dependencies remain empty: `dependencies = []`.
- `DO_NOW` and `RESEARCH` require non-empty `next_test`.
- `PARKED` requires non-empty `resume_when`.
- Gates are explicit operator booleans and must never determine or rewrite the decision automatically.
- Decision rows are append-only; revisions occur only through explicit `supersedes_decision_id`.
- Each question has one root decision and at most one current leaf.
- A revision may supersede only the exact current leaf for the same question.
- The decision path must fail closed if `question_nodes_v04` is absent or structurally unsupported.
- v0.9 may create only `investigation_decisions_v09`; it must not call `QuestionLineageStore.initialize()` merely to satisfy its prerequisite.
- Duplicate decision ids are rejected strictly, even when incoming content matches the stored row.
- Current state is derived from immutable history; no mutable `current_state` field/table is allowed.
- `RECOMMENDED_DO_NOW_LIMIT = 3` is advisory only; exceeding it emits a warning but never blocks or mutates decisions.
- No embeddings, LLM runtime calls, agents, schedulers, automatic reactivation, remote databases, web UI, retrieval changes, novelty changes, or benchmark changes.
- Existing v0.1-v0.8 commands and tests remain backward compatible.

---

## File Structure

### New files

- `src/question_radar/decisions.py` — immutable `InvestigationDecision` contract, closed vocabularies, validation helpers, timestamp sort key, WIP constant.
- `src/question_radar/decision_storage.py` — v0.4 prerequisite validation, v0.9 schema, append-only inserts, supersession validation, current/history projections, read-only question lookup.
- `src/question_radar/decision_export.py` — deterministic Markdown/JSON renderers and advisory WIP projection.
- `src/question_radar/cli_v09.py` — additive `decision` namespace; delegates every other command to `cli_v06`.
- `tests/test_decisions.py`
- `tests/test_decision_storage.py`
- `tests/test_decision_export.py`
- `tests/test_decision_cli.py`
- `benchmarks/dogfood-investigation-decision-gate-2026-09-04.md`

### Modified files

- `pyproject.toml` — console-script target becomes `question_radar.cli_v09:main`; `dependencies = []` remains unchanged.
- `README.md` — document v0.8/v0.9, decision semantics, CLI, append-only history, authority boundary.

---

### Task 1: Immutable decision contract

**Files:**
- Create: `src/question_radar/decisions.py`
- Create: `tests/test_decisions.py`

**Interfaces:**
- Produces `DECISION_STATES`, `COST_LEVELS`, `CONFIDENCE_LEVELS`, `RECOMMENDED_DO_NOW_LIMIT`.
- Produces `InvestigationDecision.from_dict(payload: dict[str, Any]) -> InvestigationDecision`.
- Produces `InvestigationDecision.to_dict() -> dict[str, Any]`.
- Produces `decision_timestamp_sort_key(value: str) -> datetime`.

- [ ] **Step 1: Write the first failing contract tests**

```python
# tests/test_decisions.py
import pytest

from question_radar.decisions import (
    CONFIDENCE_LEVELS,
    COST_LEVELS,
    DECISION_STATES,
    RECOMMENDED_DO_NOW_LIMIT,
    InvestigationDecision,
)


def valid_payload(**overrides):
    payload = {
        "id": "dec-001",
        "question_id": "q-001",
        "decision": "DO_NOW",
        "rationale": "This question serves the current objective.",
        "goal_alignment": True,
        "external_signal": True,
        "testable_now": True,
        "leverage": True,
        "cost": "medium",
        "confidence": "medium",
        "next_test": "Run one bounded evidence review.",
        "resume_when": None,
        "kill_condition": None,
        "supersedes_decision_id": None,
        "created_at": "2026-09-04T15:00:00-03:00",
    }
    payload.update(overrides)
    return payload


def test_decision_contract_round_trips():
    item = InvestigationDecision.from_dict(valid_payload())
    assert item.to_dict() == valid_payload()


def test_closed_vocabularies_are_frozen():
    assert DECISION_STATES == ("DO_NOW", "RESEARCH", "PARKED", "KILLED")
    assert COST_LEVELS == ("low", "medium", "high")
    assert CONFIDENCE_LEVELS == ("low", "medium", "high")
    assert RECOMMENDED_DO_NOW_LIMIT == 3
```

- [ ] **Step 2: Run RED**

```bash
pytest tests/test_decisions.py -v
```

Expected: import/collection failure because `question_radar.decisions` does not exist.

- [ ] **Step 3: Add failing validation tests**

```python
@pytest.mark.parametrize("field", ["id", "question_id", "rationale"])
def test_required_text_rejects_blank(field):
    with pytest.raises(ValueError, match=field):
        InvestigationDecision.from_dict(valid_payload(**{field: "   "}))


@pytest.mark.parametrize("field", ["goal_alignment", "external_signal", "testable_now", "leverage"])
def test_gates_require_real_booleans(field):
    with pytest.raises(ValueError, match=f"{field} must be a boolean"):
        InvestigationDecision.from_dict(valid_payload(**{field: 1}))


@pytest.mark.parametrize("state", ["DO_NOW", "RESEARCH"])
def test_active_states_require_next_test(state):
    with pytest.raises(ValueError, match="next_test"):
        InvestigationDecision.from_dict(valid_payload(decision=state, next_test=None))


def test_parked_requires_resume_when():
    with pytest.raises(ValueError, match="resume_when"):
        InvestigationDecision.from_dict(
            valid_payload(decision="PARKED", next_test=None, resume_when=None)
        )


def test_killed_allows_optional_kill_condition():
    item = InvestigationDecision.from_dict(
        valid_payload(decision="KILLED", next_test=None, kill_condition=None)
    )
    assert item.kill_condition is None


def test_naive_timestamp_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware ISO timestamp"):
        InvestigationDecision.from_dict(valid_payload(created_at="2026-09-04T15:00:00"))


def test_unknown_field_fails_closed():
    payload = valid_payload()
    payload["priority_score"] = 99
    with pytest.raises(ValueError, match="unknown fields: priority_score"):
        InvestigationDecision.from_dict(payload)
```

- [ ] **Step 4: Implement the minimal domain model**

```python
# src/question_radar/decisions.py
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

DECISION_STATES = ("DO_NOW", "RESEARCH", "PARKED", "KILLED")
COST_LEVELS = ("low", "medium", "high")
CONFIDENCE_LEVELS = ("low", "medium", "high")
RECOMMENDED_DO_NOW_LIMIT = 3

_FIELDS = {
    "id", "question_id", "decision", "rationale",
    "goal_alignment", "external_signal", "testable_now", "leverage",
    "cost", "confidence", "next_test", "resume_when", "kill_condition",
    "supersedes_decision_id", "created_at",
}


def _required_text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _optional_text(name: str, value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be null or a non-empty string")
    return value.strip()


def _required_bool(name: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")
    return value


def _timestamp(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a timezone-aware ISO timestamp")
    cleaned = value.strip()
    try:
        parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be a timezone-aware ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must be a timezone-aware ISO timestamp")
    return cleaned


def decision_timestamp_sort_key(value: str) -> datetime:
    return datetime.fromisoformat(
        _timestamp("timestamp", value).replace("Z", "+00:00")
    ).astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class InvestigationDecision:
    id: str
    question_id: str
    decision: str
    rationale: str
    goal_alignment: bool
    external_signal: bool
    testable_now: bool
    leverage: bool
    cost: str
    confidence: str
    next_test: str | None
    resume_when: str | None
    kill_condition: str | None
    supersedes_decision_id: str | None
    created_at: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "InvestigationDecision":
        if not isinstance(payload, dict):
            raise ValueError("investigation decision payload must be a JSON object")
        missing = sorted(_FIELDS - payload.keys())
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")
        unknown = sorted(payload.keys() - _FIELDS)
        if unknown:
            raise ValueError(f"unknown fields: {', '.join(unknown)}")

        state = payload["decision"]
        if state not in DECISION_STATES:
            raise ValueError("decision must be one of: " + ", ".join(DECISION_STATES))
        cost = payload["cost"]
        if cost not in COST_LEVELS:
            raise ValueError("cost must be one of: " + ", ".join(COST_LEVELS))
        confidence = payload["confidence"]
        if confidence not in CONFIDENCE_LEVELS:
            raise ValueError("confidence must be one of: " + ", ".join(CONFIDENCE_LEVELS))

        next_test = _optional_text("next_test", payload["next_test"])
        resume_when = _optional_text("resume_when", payload["resume_when"])
        if state in {"DO_NOW", "RESEARCH"} and next_test is None:
            raise ValueError("next_test must be a non-empty string for DO_NOW or RESEARCH")
        if state == "PARKED" and resume_when is None:
            raise ValueError("resume_when must be a non-empty string for PARKED")

        return cls(
            id=_required_text("id", payload["id"]),
            question_id=_required_text("question_id", payload["question_id"]),
            decision=state,
            rationale=_required_text("rationale", payload["rationale"]),
            goal_alignment=_required_bool("goal_alignment", payload["goal_alignment"]),
            external_signal=_required_bool("external_signal", payload["external_signal"]),
            testable_now=_required_bool("testable_now", payload["testable_now"]),
            leverage=_required_bool("leverage", payload["leverage"]),
            cost=cost,
            confidence=confidence,
            next_test=next_test,
            resume_when=resume_when,
            kill_condition=_optional_text("kill_condition", payload["kill_condition"]),
            supersedes_decision_id=_optional_text(
                "supersedes_decision_id", payload["supersedes_decision_id"]
            ),
            created_at=_timestamp("created_at", payload["created_at"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

- [ ] **Step 5: Run GREEN and commit**

```bash
pytest tests/test_decisions.py -v
git add src/question_radar/decisions.py tests/test_decisions.py
git commit -m "feat: add investigation decision contract v0.9"
```

Expected: all `test_decisions.py` tests pass before commit.

---

### Task 2: Fail-closed SQLite store and linear history

**Files:**
- Create: `src/question_radar/decision_storage.py`
- Create: `tests/test_decision_storage.py`

**Interfaces:**
- Consumes `InvestigationDecision`, `decision_timestamp_sort_key`, existing `QuestionNode`.
- Produces `InvestigationDecisionStore` with `initialize`, `insert`, `get`, `get_question_node`, `get_current`, `list_history`, `list_current_decisions`.

- [ ] **Step 1: Write RED prerequisite tests**

```python
# tests/test_decision_storage.py
import sqlite3
import pytest

from question_radar.decision_storage import InvestigationDecisionStore
from question_radar.decisions import InvestigationDecision
from question_radar.lineage import QuestionNode
from question_radar.lineage_storage import QuestionLineageStore


def node(node_id: str) -> QuestionNode:
    return QuestionNode.from_dict({
        "id": node_id,
        "question": f"Question {node_id}?",
        "source": "manual",
        "source_ref": None,
        "created_at": "2026-09-04T12:00:00-03:00",
    })


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
        names = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
    assert "investigation_decisions_v09" not in names


def test_unsupported_v04_shape_fails_closed(tmp_path):
    db = tmp_path / "bad.sqlite3"
    with sqlite3.connect(db) as connection:
        connection.execute("CREATE TABLE question_nodes_v04 (id TEXT PRIMARY KEY)")
    with pytest.raises(RuntimeError, match="structurally unsupported"):
        InvestigationDecisionStore(db).initialize()
```

- [ ] **Step 2: Run RED**

```bash
pytest tests/test_decision_storage.py -v
```

Expected: import failure because `decision_storage.py` does not exist.

- [ ] **Step 3: Implement connection, prerequisite check, and owned schema**

```python
# src/question_radar/decision_storage.py
from pathlib import Path
import sqlite3

from question_radar.decisions import InvestigationDecision, decision_timestamp_sort_key
from question_radar.lineage import QuestionNode

_REQUIRED_V04_COLUMNS = {"id", "question", "source", "source_ref", "created_at"}
_DECISION_COLUMNS = (
    "id", "question_id", "decision", "rationale",
    "goal_alignment", "external_signal", "testable_now", "leverage",
    "cost", "confidence", "next_test", "resume_when", "kill_condition",
    "supersedes_decision_id", "created_at",
)
_SCHEMA = """
CREATE TABLE IF NOT EXISTS investigation_decisions_v09 (
    id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('DO_NOW','RESEARCH','PARKED','KILLED')),
    rationale TEXT NOT NULL,
    goal_alignment INTEGER NOT NULL CHECK (goal_alignment IN (0,1)),
    external_signal INTEGER NOT NULL CHECK (external_signal IN (0,1)),
    testable_now INTEGER NOT NULL CHECK (testable_now IN (0,1)),
    leverage INTEGER NOT NULL CHECK (leverage IN (0,1)),
    cost TEXT NOT NULL CHECK (cost IN ('low','medium','high')),
    confidence TEXT NOT NULL CHECK (confidence IN ('low','medium','high')),
    next_test TEXT,
    resume_when TEXT,
    kill_condition TEXT,
    supersedes_decision_id TEXT UNIQUE,
    created_at TEXT NOT NULL,
    FOREIGN KEY (question_id) REFERENCES question_nodes_v04(id),
    FOREIGN KEY (supersedes_decision_id) REFERENCES investigation_decisions_v09(id),
    CHECK (supersedes_decision_id IS NULL OR supersedes_decision_id <> id)
)
"""


class InvestigationDecisionStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def _connect_existing(self) -> sqlite3.Connection:
        if not self.db_path.exists():
            raise RuntimeError(f"database does not exist: {self.db_path}")
        connection = sqlite3.connect(self.db_path)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.row_factory = sqlite3.Row
        return connection

    def _verify_v04_prerequisite(self, connection: sqlite3.Connection) -> None:
        row = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='question_nodes_v04'"
        ).fetchone()
        if row is None:
            raise RuntimeError("question_nodes_v04 prerequisite is missing")
        columns = {row["name"] for row in connection.execute(
            "PRAGMA table_info(question_nodes_v04)"
        )}
        missing = sorted(_REQUIRED_V04_COLUMNS - columns)
        if missing:
            raise RuntimeError(
                "question_nodes_v04 prerequisite is structurally unsupported; missing columns: "
                + ", ".join(missing)
            )

    def initialize(self) -> None:
        with self._connect_existing() as connection:
            self._verify_v04_prerequisite(connection)
            connection.execute(_SCHEMA)
```

- [ ] **Step 4: Verify prerequisite tests GREEN**

```bash
pytest tests/test_decision_storage.py -k "missing_database or missing_v04 or unsupported_v04" -v
```

Expected: all selected prerequisite tests pass.

- [ ] **Step 5: Add RED tests for append-only insert and supersession rules**

```python
def test_insert_requires_question_and_rejects_duplicate_id(tmp_path):
    store = prepared_store(tmp_path, node("q-a"))
    store.insert(decision("dec-1", "q-a"))
    assert store.get("dec-1").id == "dec-1"
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

    store.insert(decision(
        "dec-2",
        "q-a",
        decision="PARKED",
        next_test=None,
        resume_when="A real workload appears.",
        supersedes_decision_id="dec-1",
        created_at="2026-09-04T12:10:00-03:00",
    ))
    assert store.get_current("q-a").id == "dec-2"


def test_revision_cannot_cross_questions_or_skip_current_leaf(tmp_path):
    store = prepared_store(tmp_path, node("q-a"), node("q-b"))
    store.insert(decision("a-1", "q-a"))
    store.insert(decision("b-1", "q-b"))
    with pytest.raises(ValueError, match="belongs to another question"):
        store.insert(decision(
            "a-2", "q-a", decision="RESEARCH", supersedes_decision_id="b-1"
        ))
    store.insert(decision(
        "a-2", "q-a", decision="RESEARCH",
        supersedes_decision_id="a-1",
        created_at="2026-09-04T12:10:00-03:00",
    ))
    with pytest.raises(ValueError, match="revision must supersede current decision: a-2"):
        store.insert(decision(
            "a-3", "q-a", decision="KILLED", next_test=None,
            supersedes_decision_id="a-1",
        ))
```

- [ ] **Step 6: Implement append-only insert and linear-history validation**

Add these methods inside `InvestigationDecisionStore`:

```python
    def _get_in_connection(self, connection, decision_id):
        row = connection.execute(
            "SELECT * FROM investigation_decisions_v09 WHERE id = ?",
            (decision_id,),
        ).fetchone()
        return InvestigationDecision.from_dict(dict(row)) if row is not None else None

    def _history_in_connection(self, connection, question_id):
        rows = connection.execute(
            "SELECT * FROM investigation_decisions_v09 WHERE question_id = ?",
            (question_id,),
        ).fetchall()
        return [InvestigationDecision.from_dict(dict(row)) for row in rows]

    def _validate_history_in_connection(self, connection, question_id):
        history = self._history_in_connection(connection, question_id)
        if not history:
            return None
        by_id = {item.id: item for item in history}
        roots = [item for item in history if item.supersedes_decision_id is None]
        referenced = [
            item.supersedes_decision_id
            for item in history
            if item.supersedes_decision_id is not None
        ]
        if len(roots) != 1 or len(referenced) != len(set(referenced)):
            raise RuntimeError(f"ambiguous decision history for {question_id}")
        if any(prior_id not in by_id for prior_id in referenced):
            raise RuntimeError(f"ambiguous decision history for {question_id}")
        leaves = [item for item in history if item.id not in set(referenced)]
        if len(leaves) != 1:
            raise RuntimeError(f"ambiguous decision history for {question_id}")
        seen = set()
        cursor = leaves[0]
        while True:
            if cursor.id in seen:
                raise RuntimeError(f"ambiguous decision history for {question_id}")
            seen.add(cursor.id)
            if cursor.supersedes_decision_id is None:
                break
            cursor = by_id[cursor.supersedes_decision_id]
        if seen != set(by_id):
            raise RuntimeError(f"ambiguous decision history for {question_id}")
        return leaves[0]

    def insert(self, item: InvestigationDecision) -> None:
        self.initialize()
        with self._connect_existing() as connection:
            if self._get_in_connection(connection, item.id) is not None:
                raise ValueError(f"decision id already exists: {item.id}")
            if connection.execute(
                "SELECT 1 FROM question_nodes_v04 WHERE id = ?", (item.question_id,)
            ).fetchone() is None:
                raise ValueError(f"question node not found: {item.question_id}")

            current = self._validate_history_in_connection(connection, item.question_id)
            if current is None:
                if item.supersedes_decision_id is not None:
                    raise ValueError("first decision must not supersede another decision")
            else:
                if item.supersedes_decision_id is None:
                    raise ValueError(f"revision must supersede current decision: {current.id}")
                prior = self._get_in_connection(connection, item.supersedes_decision_id)
                if prior is None:
                    raise ValueError(f"superseded decision not found: {item.supersedes_decision_id}")
                if prior.question_id != item.question_id:
                    raise ValueError("superseded decision belongs to another question")
                if prior.id != current.id:
                    raise ValueError(f"revision must supersede current decision: {current.id}")

            try:
                connection.execute(
                    "INSERT INTO investigation_decisions_v09 ("
                    + ", ".join(_DECISION_COLUMNS)
                    + ") VALUES ("
                    + ", ".join("?" for _ in _DECISION_COLUMNS)
                    + ")",
                    tuple(item.to_dict()[column] for column in _DECISION_COLUMNS),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("investigation decision violates the v0.9 schema") from exc
            self._validate_history_in_connection(connection, item.question_id)
```

- [ ] **Step 7: Add projection/corruption tests**

```python
def test_history_and_current_are_deterministic(tmp_path):
    store = prepared_store(tmp_path, node("q-a"))
    store.insert(decision("dec-a", "q-a", created_at="2026-09-04T13:00:00+01:00"))
    store.insert(decision(
        "dec-b", "q-a", decision="RESEARCH", supersedes_decision_id="dec-a",
        created_at="2026-09-04T09:00:00-03:00",
    ))
    assert [item.id for item in store.list_history("q-a")] == ["dec-a", "dec-b"]
    assert store.get_current("q-a").id == "dec-b"


def test_corrupt_multiple_roots_fail_closed(tmp_path):
    store = prepared_store(tmp_path, node("q-a"))
    store.initialize()
    columns = _DECISION_COLUMNS_FOR_TEST = (
        "id", "question_id", "decision", "rationale", "goal_alignment",
        "external_signal", "testable_now", "leverage", "cost", "confidence",
        "next_test", "resume_when", "kill_condition", "supersedes_decision_id",
        "created_at",
    )
    with sqlite3.connect(store.db_path) as connection:
        for item in (
            decision("dec-1", "q-a"),
            decision("dec-2", "q-a", created_at="2026-09-04T12:06:00-03:00"),
        ):
            payload = item.to_dict()
            connection.execute(
                "INSERT INTO investigation_decisions_v09 (" + ", ".join(columns)
                + ") VALUES (" + ", ".join("?" for _ in columns) + ")",
                tuple(payload[column] for column in columns),
            )
    with pytest.raises(RuntimeError, match="ambiguous decision history for q-a"):
        store.get_current("q-a")
```

- [ ] **Step 8: Implement read/query projections**

```python
    def get(self, decision_id: str) -> InvestigationDecision | None:
        self.initialize()
        with self._connect_existing() as connection:
            return self._get_in_connection(connection, decision_id)

    def get_question_node(self, question_id: str) -> QuestionNode | None:
        self.initialize()
        with self._connect_existing() as connection:
            row = connection.execute(
                "SELECT id, question, source, source_ref, created_at "
                "FROM question_nodes_v04 WHERE id = ?",
                (question_id,),
            ).fetchone()
        return QuestionNode.from_dict(dict(row)) if row is not None else None

    def get_current(self, question_id: str) -> InvestigationDecision | None:
        self.initialize()
        with self._connect_existing() as connection:
            return self._validate_history_in_connection(connection, question_id)

    def list_history(self, question_id: str) -> list[InvestigationDecision]:
        self.initialize()
        with self._connect_existing() as connection:
            self._validate_history_in_connection(connection, question_id)
            history = self._history_in_connection(connection, question_id)
        return sorted(
            history,
            key=lambda item: (decision_timestamp_sort_key(item.created_at), item.id),
        )

    def list_current_decisions(self) -> list[InvestigationDecision]:
        self.initialize()
        with self._connect_existing() as connection:
            ids = [row["question_id"] for row in connection.execute(
                "SELECT DISTINCT question_id FROM investigation_decisions_v09 ORDER BY question_id"
            )]
            current = [self._validate_history_in_connection(connection, qid) for qid in ids]
        return sorted(
            [item for item in current if item is not None],
            key=lambda item: (decision_timestamp_sort_key(item.created_at), item.id),
        )
```

- [ ] **Step 9: Run GREEN and commit**

```bash
pytest tests/test_decision_storage.py -v
git add src/question_radar/decision_storage.py tests/test_decision_storage.py
git commit -m "feat: persist investigation decisions v0.9"
```

Expected: all storage tests pass before commit.

---

### Task 3: Deterministic rendering and WIP projection

**Files:**
- Create: `src/question_radar/decision_export.py`
- Create: `tests/test_decision_export.py`

**Interfaces:**
- Produces `render_decision_markdown/json`, `render_history_markdown/json`, `render_active_markdown/json`.
- Active renderers consume `list[tuple[QuestionNode, InvestigationDecision]]` representing every current leaf, including parked/killed items for counts.

- [ ] **Step 1: Write RED rendering tests**

```python
# tests/test_decision_export.py
import json

from question_radar.decision_export import (
    render_active_json,
    render_active_markdown,
    render_decision_json,
    render_decision_markdown,
    render_history_json,
    render_history_markdown,
)
from question_radar.decisions import InvestigationDecision
from question_radar.lineage import QuestionNode


def node(node_id="q-a", question="Should this consume attention now?"):
    return QuestionNode.from_dict({
        "id": node_id,
        "question": question,
        "source": "manual",
        "source_ref": None,
        "created_at": "2026-09-04T12:00:00-03:00",
    })


def make_decision(decision_id, question_id, state="DO_NOW"):
    payload = {
        "id": decision_id,
        "question_id": question_id,
        "decision": state,
        "rationale": "Bounded operator judgment.",
        "goal_alignment": state != "PARKED",
        "external_signal": True,
        "testable_now": state in {"DO_NOW", "RESEARCH"},
        "leverage": True,
        "cost": "low",
        "confidence": "medium",
        "next_test": "Run one bounded test." if state in {"DO_NOW", "RESEARCH"} else None,
        "resume_when": "A relevant condition changes." if state == "PARKED" else None,
        "kill_condition": None,
        "supersedes_decision_id": None,
        "created_at": "2026-09-04T12:05:00-03:00",
    }
    return InvestigationDecision.from_dict(payload)


def test_parked_markdown_preserves_authority_boundary():
    rendered = render_decision_markdown(node(), make_decision("d-1", "q-a", "PARKED"))
    assert "Current decision: PARKED" in rendered
    assert "No action is currently requested." in rendered
    assert "Operator decision recorded; no automatic prioritization was performed." in rendered
    assert rendered.endswith("\n")


def test_show_json_is_deterministic_and_has_no_priority_score():
    first = render_decision_json(node(), make_decision("d-1", "q-a", "PARKED"))
    second = render_decision_json(node(), make_decision("d-1", "q-a", "PARKED"))
    assert first == second
    payload = json.loads(first)
    assert payload["decision_version"] == "v0.9"
    assert payload["automatic_decision"] is False
    assert "priority_score" not in payload
```

- [ ] **Step 2: Run RED**

```bash
pytest tests/test_decision_export.py -v
```

Expected: import failure because `decision_export.py` does not exist.

- [ ] **Step 3: Add active/WIP tests**

```python
def test_active_counts_all_states_and_lists_only_do_now_research():
    entries = [
        (node("q-1"), make_decision("d-1", "q-1", "DO_NOW")),
        (node("q-2"), make_decision("d-2", "q-2", "RESEARCH")),
        (node("q-3"), make_decision("d-3", "q-3", "PARKED")),
    ]
    payload = json.loads(render_active_json(entries))
    assert payload["counts"] == {
        "DO_NOW": 1, "RESEARCH": 1, "PARKED": 1, "KILLED": 0
    }
    assert [item["decision"]["decision"] for item in payload["active"]] == [
        "DO_NOW", "RESEARCH"
    ]
    assert payload["wip_warning"] is None


def test_wip_warning_only_above_three_do_now_and_does_not_change_records():
    three = [
        (node(f"q-{i}"), make_decision(f"d-{i}", f"q-{i}", "DO_NOW"))
        for i in range(1, 4)
    ]
    four = three + [(node("q-4"), make_decision("d-4", "q-4", "DO_NOW"))]
    assert json.loads(render_active_json(three))["wip_warning"] is None
    payload = json.loads(render_active_json(four))
    assert "4 investigations are marked DO_NOW" in payload["wip_warning"]
    assert "No decision was changed automatically." in payload["wip_warning"]
    assert all(item.decision == "DO_NOW" for _, item in four)
```

- [ ] **Step 4: Implement deterministic renderers**

```python
# src/question_radar/decision_export.py
import json

from question_radar.decisions import (
    DECISION_STATES,
    RECOMMENDED_DO_NOW_LIMIT,
    InvestigationDecision,
)
from question_radar.lineage import QuestionNode


def _gate_lines(item: InvestigationDecision) -> list[str]:
    pairs = (
        ("goal_alignment", "current goal alignment"),
        ("external_signal", "external signal"),
        ("testable_now", "testable now"),
        ("leverage", "leverage"),
    )
    return [
        f"{'✓' if getattr(item, field) else '✗'} {label}"
        for field, label in pairs
    ]


def render_decision_json(node: QuestionNode, item: InvestigationDecision) -> str:
    return json.dumps({
        "automatic_decision": False,
        "current_decision": item.to_dict(),
        "decision_version": "v0.9",
        "question": node.to_dict(),
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_decision_markdown(node: QuestionNode, item: InvestigationDecision) -> str:
    lines = [
        "# Investigation Decision v0.9", "",
        f"Question: {node.question}", f"Question id: {node.id}", "",
        f"Current decision: {item.decision}", f"Decision: {item.id}", "",
        "Why:", item.rationale,
    ]
    if item.next_test is not None:
        lines += ["", "Next test:", item.next_test]
    if item.resume_when is not None:
        lines += ["", "Resume when:", item.resume_when]
    if item.kill_condition is not None:
        lines += ["", "Kill condition:", item.kill_condition]
    lines += ["", "Gates:", *_gate_lines(item)]
    if item.decision == "PARKED":
        lines += ["", "No action is currently requested."]
    lines += ["", "Operator decision recorded; no automatic prioritization was performed."]
    return "\n".join(lines) + "\n"


def render_history_json(node, decisions) -> str:
    return json.dumps({
        "automatic_decision": False,
        "decision_version": "v0.9",
        "question": node.to_dict(),
        "history": [item.to_dict() for item in decisions],
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_history_markdown(node, decisions) -> str:
    lines = ["# Investigation Decision History v0.9", "", f"Question: {node.question}", ""]
    for item in decisions:
        lines += [
            f"## {item.id} — {item.decision}",
            f"created_at: {item.created_at}",
            f"supersedes: {item.supersedes_decision_id}",
            f"rationale: {item.rationale}",
            "",
        ]
    lines += ["History is append-only; no automatic prioritization was performed."]
    return "\n".join(lines) + "\n"


def _active_projection(entries):
    counts = {state: 0 for state in DECISION_STATES}
    for _, item in entries:
        counts[item.decision] += 1
    active = [
        {"question": node.to_dict(), "decision": item.to_dict()}
        for node, item in entries
        if item.decision in {"DO_NOW", "RESEARCH"}
    ]
    warning = None
    if counts["DO_NOW"] > RECOMMENDED_DO_NOW_LIMIT:
        warning = (
            f"WARNING: {counts['DO_NOW']} investigations are marked DO_NOW. "
            f"Recommended operating limit: {RECOMMENDED_DO_NOW_LIMIT}. "
            "No decision was changed automatically."
        )
    return counts, active, warning


def render_active_json(entries) -> str:
    counts, active, warning = _active_projection(entries)
    return json.dumps({
        "active": active,
        "automatic_decision": False,
        "counts": counts,
        "decision_version": "v0.9",
        "recommended_do_now_limit": RECOMMENDED_DO_NOW_LIMIT,
        "wip_warning": warning,
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_active_markdown(entries) -> str:
    counts, active, warning = _active_projection(entries)
    lines = [
        "# Active Investigation Decisions v0.9", "",
        f"DO_NOW: {counts['DO_NOW']}",
        f"RESEARCH: {counts['RESEARCH']}",
        f"PARKED: {counts['PARKED']}",
        f"KILLED: {counts['KILLED']}", "", "## Active",
    ]
    if active:
        for item in active:
            lines.append(
                f"- {item['decision']['decision']} — {item['question']['question']} "
                f"({item['decision']['id']})"
            )
    else:
        lines.append("None.")
    if warning is not None:
        lines += ["", warning]
    lines += ["", "No decision was changed automatically."]
    return "\n".join(lines) + "\n"
```

- [ ] **Step 5: Run GREEN and commit**

```bash
pytest tests/test_decision_export.py -v
git add src/question_radar/decision_export.py tests/test_decision_export.py
git commit -m "feat: render investigation decisions v0.9"
```

Expected: all export tests pass before commit.

---

### Task 4: Additive `cli_v09` facade

**Files:**
- Create: `src/question_radar/cli_v09.py`
- Create: `tests/test_decision_cli.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces `question-radar decision record`.
- Produces `question-radar decision show QUESTION_ID --format markdown|json`.
- Produces `question-radar decision history QUESTION_ID --format markdown|json`.
- Produces `question-radar decision active --format markdown|json`.
- Delegates every non-`decision` command to `question_radar.cli_v06.main`.

- [ ] **Step 1: Write RED parser test**

```python
# tests/test_decision_cli.py
import json
import subprocess

from question_radar import cli_v09 as cli
from question_radar.lineage import QuestionNode
from question_radar.lineage_storage import QuestionLineageStore


def seed_node(db, node_id="q-a", question="Should this consume attention now?"):
    QuestionLineageStore(db).insert_node(QuestionNode.from_dict({
        "id": node_id,
        "question": question,
        "source": "manual",
        "source_ref": None,
        "created_at": "2026-09-04T12:00:00-03:00",
    }))


def test_record_parser_accepts_operator_and_audit_fields():
    args = cli.build_decision_parser().parse_args([
        "decision", "record",
        "--question-id", "q-a",
        "--decision", "PARKED",
        "--rationale", "Not needed now.",
        "--goal-alignment", "false",
        "--external-signal", "true",
        "--testable-now", "false",
        "--leverage", "true",
        "--cost", "medium",
        "--confidence", "medium",
        "--resume-when", "A workload exists.",
        "--id", "dec-explicit",
        "--created-at", "2026-09-04T15:00:00-03:00",
    ])
    assert args.id == "dec-explicit"
    assert args.goal_alignment is False
    assert args.external_signal is True
```

- [ ] **Step 2: Run RED**

```bash
pytest tests/test_decision_cli.py -v
```

Expected: import failure because `cli_v09.py` does not exist.

- [ ] **Step 3: Implement parser and routing skeleton**

```python
# src/question_radar/cli_v09.py
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import sys
import uuid

from question_radar import cli_v06 as previous_cli
from question_radar.decision_export import (
    render_active_json, render_active_markdown,
    render_decision_json, render_decision_markdown,
    render_history_json, render_history_markdown,
)
from question_radar.decision_storage import InvestigationDecisionStore
from question_radar.decisions import (
    CONFIDENCE_LEVELS, COST_LEVELS, DECISION_STATES, InvestigationDecision,
)


def _parse_bool(value: str) -> bool:
    value = value.strip().lower()
    if value == "true":
        return True
    if value == "false":
        return False
    raise argparse.ArgumentTypeError("expected true or false")


def _new_decision_id() -> str:
    return f"dec-{uuid.uuid4().hex}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _top_level_command(argv: list[str]) -> str | None:
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--db":
            index += 2
            continue
        if token.startswith("--db="):
            index += 1
            continue
        if token.startswith("-"):
            return None
        return token
    return None


def _root_help_requested(argv: list[str]) -> bool:
    remaining = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--db":
            if index + 1 >= len(argv):
                return False
            index += 2
            continue
        if token.startswith("--db="):
            index += 1
            continue
        remaining.append(token)
        index += 1
    return remaining in (["--help"], ["-h"])


def build_decision_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="question-radar")
    parser.add_argument("--db", default="data/questions.sqlite3")
    root = parser.add_subparsers(dest="command", required=True)
    decision = root.add_parser("decision")
    commands = decision.add_subparsers(dest="decision_command", required=True)

    record = commands.add_parser("record")
    record.add_argument("--question-id", required=True)
    record.add_argument("--decision", choices=DECISION_STATES, required=True)
    record.add_argument("--rationale", required=True)
    record.add_argument("--goal-alignment", type=_parse_bool, required=True)
    record.add_argument("--external-signal", type=_parse_bool, required=True)
    record.add_argument("--testable-now", type=_parse_bool, required=True)
    record.add_argument("--leverage", type=_parse_bool, required=True)
    record.add_argument("--cost", choices=COST_LEVELS, required=True)
    record.add_argument("--confidence", choices=CONFIDENCE_LEVELS, required=True)
    record.add_argument("--next-test")
    record.add_argument("--resume-when")
    record.add_argument("--kill-condition")
    record.add_argument("--supersedes")
    record.add_argument("--id")
    record.add_argument("--created-at")

    for name in ("show", "history"):
        command = commands.add_parser(name)
        command.add_argument("question_id")
        command.add_argument("--format", choices=("markdown", "json"), default="markdown")

    active = commands.add_parser("active")
    active.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser
```

- [ ] **Step 4: Add RED functional tests**

```python
def record_args(question_id="q-a", state="DO_NOW"):
    args = [
        "decision", "record",
        "--question-id", question_id,
        "--decision", state,
        "--rationale", "Bounded current investigation.",
        "--goal-alignment", "true",
        "--external-signal", "true",
        "--testable-now", "true",
        "--leverage", "true",
        "--cost", "low",
        "--confidence", "medium",
    ]
    if state in {"DO_NOW", "RESEARCH"}:
        args += ["--next-test", "Run one bounded test."]
    if state == "PARKED":
        args += ["--resume-when", "A relevant condition changes."]
    return args


def test_record_show_history_active_round_trip(tmp_path, capsys):
    db = tmp_path / "questions.sqlite3"
    seed_node(db)
    first = record_args() + [
        "--id", "dec-1", "--created-at", "2026-09-04T12:05:00-03:00"
    ]
    assert cli.main(["--db", str(db), *first]) == 0
    assert capsys.readouterr().out.strip() == "recorded dec-1"

    assert cli.main(["--db", str(db), "decision", "show", "q-a", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["current_decision"]["id"] == "dec-1"

    second = record_args(state="PARKED") + [
        "--supersedes", "dec-1", "--id", "dec-2",
        "--created-at", "2026-09-04T12:10:00-03:00",
    ]
    assert cli.main(["--db", str(db), *second]) == 0
    capsys.readouterr()

    assert cli.main(["--db", str(db), "decision", "history", "q-a", "--format", "json"]) == 0
    history = json.loads(capsys.readouterr().out)
    assert [item["id"] for item in history["history"]] == ["dec-1", "dec-2"]

    assert cli.main(["--db", str(db), "decision", "active", "--format", "json"]) == 0
    active = json.loads(capsys.readouterr().out)
    assert active["counts"]["PARKED"] == 1
    assert active["active"] == []


def test_generated_metadata_is_injectable(tmp_path, capsys, monkeypatch):
    db = tmp_path / "questions.sqlite3"
    seed_node(db)
    monkeypatch.setattr(cli, "_new_decision_id", lambda: "dec-generated")
    monkeypatch.setattr(cli, "_now_iso", lambda: "2026-09-04T18:00:00+00:00")
    assert cli.main(["--db", str(db), *record_args()]) == 0
    capsys.readouterr()
    assert cli.main(["--db", str(db), "decision", "show", "q-a", "--format", "json"]) == 0
    item = json.loads(capsys.readouterr().out)["current_decision"]
    assert item["id"] == "dec-generated"
    assert item["created_at"] == "2026-09-04T18:00:00+00:00"


def test_missing_lineage_prerequisite_fails_closed(tmp_path, capsys):
    db = tmp_path / "empty.sqlite3"
    db.touch()
    assert cli.main(["--db", str(db), "decision", "active"]) == 2
    assert "question_nodes_v04 prerequisite" in capsys.readouterr().err
```

- [ ] **Step 5: Implement handlers and delegation**

```python

def _print_root_help() -> None:
    previous_cli.main(["--help"])
    print("  decision            record and inspect Investigation Decision Gate v0.9 judgments")


def _handle_record(args) -> int:
    item = InvestigationDecision.from_dict({
        "id": args.id or _new_decision_id(),
        "question_id": args.question_id,
        "decision": args.decision,
        "rationale": args.rationale,
        "goal_alignment": args.goal_alignment,
        "external_signal": args.external_signal,
        "testable_now": args.testable_now,
        "leverage": args.leverage,
        "cost": args.cost,
        "confidence": args.confidence,
        "next_test": args.next_test,
        "resume_when": args.resume_when,
        "kill_condition": args.kill_condition,
        "supersedes_decision_id": args.supersedes,
        "created_at": args.created_at or _now_iso(),
    })
    InvestigationDecisionStore(args.db).insert(item)
    print(f"recorded {item.id}")
    return 0


def _handle_decision(args) -> int:
    if args.decision_command == "record":
        return _handle_record(args)
    store = InvestigationDecisionStore(args.db)
    if args.decision_command == "show":
        node = store.get_question_node(args.question_id)
        if node is None:
            raise ValueError(f"question node not found: {args.question_id}")
        current = store.get_current(args.question_id)
        if current is None:
            raise ValueError(f"no investigation decision recorded for: {args.question_id}")
        rendered = render_decision_json(node, current) if args.format == "json" else render_decision_markdown(node, current)
    elif args.decision_command == "history":
        node = store.get_question_node(args.question_id)
        if node is None:
            raise ValueError(f"question node not found: {args.question_id}")
        history = store.list_history(args.question_id)
        rendered = render_history_json(node, history) if args.format == "json" else render_history_markdown(node, history)
    elif args.decision_command == "active":
        current = store.list_current_decisions()
        pairs = [(store.get_question_node(item.question_id), item) for item in current]
        if any(node is None for node, _ in pairs):
            raise RuntimeError("current decision references a missing question node")
        entries = [(node, item) for node, item in pairs if node is not None]
        rendered = render_active_json(entries) if args.format == "json" else render_active_markdown(entries)
    else:
        raise ValueError("unknown decision command")
    print(rendered, end="")
    return 0


def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    if _root_help_requested(args_list):
        _print_root_help()
        return 0
    if _top_level_command(args_list) != "decision":
        return previous_cli.main(args_list)
    args = build_decision_parser().parse_args(args_list)
    try:
        return _handle_decision(args)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
```

- [ ] **Step 6: Change only the console-script target**

```toml
[project.scripts]
question-radar = "question_radar.cli_v09:main"
```

Keep `dependencies = []` unchanged.

- [ ] **Step 7: Add installed-CLI regression test**

```python
def test_installed_cli_exposes_decision_and_preserves_existing_namespaces():
    for args, expected in (
        (["--help"], "decision"),
        (["decision", "--help"], "record"),
        (["decision", "record", "--help"], "--question-id"),
        (["retrieval", "--help"], "compare"),
        (["benchmark", "--help"], "evaluate"),
        (["lineage", "--help"], "node"),
    ):
        completed = subprocess.run(
            ["question-radar", *args], capture_output=True, text=True, check=False
        )
        assert completed.returncode == 0, completed.stderr
        assert expected in completed.stdout
```

- [ ] **Step 8: Run GREEN and commit**

```bash
pytest tests/test_decision_cli.py tests/test_retrieval_cli.py tests/test_benchmark_cli.py tests/test_lineage_cli.py tests/test_cli.py -v
git add src/question_radar/cli_v09.py tests/test_decision_cli.py pyproject.toml
git commit -m "feat: expose investigation decision cli v0.9"
```

Expected: all selected CLI tests pass before commit.

---

### Task 5: README and sanitized dogfood

**Files:**
- Modify: `README.md`
- Create: `benchmarks/dogfood-investigation-decision-gate-2026-09-04.md`

**Interfaces:**
- Consumes installed v0.9 CLI.
- Produces public documentation plus reproducible evidence from a disposable database.

- [ ] **Step 1: Update README with exact v0.9 language**

Replace the version line with:

```markdown
**Version:** v0.9 · Investigation Decision Gate + v0.8 Gold Evaluation Harness + v0.7 Retrieval Calibration & Abstention
```

Add to the system flow:

```text
explicit question identity
     ↓
operator investigation decision (v0.9)
     ↓
DO_NOW / RESEARCH / PARKED / KILLED
     ↓
append-only supersession when judgment changes
```

Add these capabilities:

```markdown
- **Append-only investigation decisions** linked to existing v0.4 question identity.
- **Explicit supersession history** so changed judgment does not rewrite earlier context.
- **Advisory WIP visibility** when more than three investigations are marked `DO_NOW`, without automatic demotion or prioritization.
- **Fail-closed v0.4 prerequisite checks** so v0.9 never creates historical lineage tables merely to satisfy itself.
```

Add this authority note near CLI examples:

```markdown
> Decision gates are operator judgments. Question Radar records and validates them; it does not decide automatically what deserves attention.
```

- [ ] **Step 2: Create a disposable dogfood database and capture exact outputs to files**

```bash
DOGFOOD_DB=/tmp/question-radar-v09-dogfood.sqlite3
ACTIVE_OUT=/tmp/question-radar-v09-active.txt
PARKED_OUT=/tmp/question-radar-v09-parked.txt
HISTORY_OUT=/tmp/question-radar-v09-history.json
rm -f "$DOGFOOD_DB" "$ACTIVE_OUT" "$PARKED_OUT" "$HISTORY_OUT"

python - <<'PY'
import json
from pathlib import Path

records = {
    "/tmp/dog-spqr.json": {
        "id": "dog-spqr",
        "question": "When does horizontal PostgreSQL scaling become justified by a real workload?",
        "source": "manual",
        "source_ref": "sanitized-dogfood",
        "created_at": "2026-09-04T18:00:00+00:00",
    },
    "/tmp/dog-lithium.json": {
        "id": "dog-lithium",
        "question": "Which lithium GeoAI problem is narrow enough for a bounded evidence-gathering test?",
        "source": "manual",
        "source_ref": "sanitized-dogfood",
        "created_at": "2026-09-04T18:01:00+00:00",
    },
    "/tmp/dog-revenue.json": {
        "id": "dog-revenue",
        "question": "Which existing product demonstration can produce external feedback this week?",
        "source": "manual",
        "source_ref": "sanitized-dogfood",
        "created_at": "2026-09-04T18:02:00+00:00",
    },
}
for path, payload in records.items():
    Path(path).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
PY

question-radar --db "$DOGFOOD_DB" lineage node add /tmp/dog-spqr.json
question-radar --db "$DOGFOOD_DB" lineage node add /tmp/dog-lithium.json
question-radar --db "$DOGFOOD_DB" lineage node add /tmp/dog-revenue.json

question-radar --db "$DOGFOOD_DB" decision record \
  --question-id dog-spqr \
  --decision PARKED \
  --rationale "High learning value, no current production workload requires it." \
  --goal-alignment false \
  --external-signal true \
  --testable-now false \
  --leverage true \
  --cost high \
  --confidence medium \
  --resume-when "A real PostgreSQL workload requires horizontal scaling." \
  --id dec-dog-spqr \
  --created-at 2026-09-04T18:10:00+00:00

question-radar --db "$DOGFOOD_DB" decision record \
  --question-id dog-lithium \
  --decision RESEARCH \
  --rationale "There is a domain-relevant problem space, but the specific problem still needs evidence." \
  --goal-alignment true \
  --external-signal true \
  --testable-now true \
  --leverage true \
  --cost medium \
  --confidence medium \
  --next-test "Collect ten repeated operational problems from public lithium project evidence and classify which are observable with GeoAI." \
  --id dec-dog-lithium \
  --created-at 2026-09-04T18:11:00+00:00

question-radar --db "$DOGFOOD_DB" decision record \
  --question-id dog-revenue \
  --decision DO_NOW \
  --rationale "This can produce external evidence from work that already exists." \
  --goal-alignment true \
  --external-signal true \
  --testable-now true \
  --leverage true \
  --cost low \
  --confidence high \
  --next-test "Publish one existing product demonstration and record one external response or explicit no-response outcome." \
  --id dec-dog-revenue \
  --created-at 2026-09-04T18:12:00+00:00

question-radar --db "$DOGFOOD_DB" decision active --format markdown | tee "$ACTIVE_OUT"
question-radar --db "$DOGFOOD_DB" decision show dog-spqr --format markdown | tee "$PARKED_OUT"
question-radar --db "$DOGFOOD_DB" decision history dog-lithium --format json | tee "$HISTORY_OUT"
```

Expected semantic checks:

- active counts are `DO_NOW: 1`, `RESEARCH: 1`, `PARKED: 1`, `KILLED: 0`;
- `ACTIVE_OUT` contains no WIP warning;
- `PARKED_OUT` contains `No action is currently requested.`;
- `HISTORY_OUT` contains one `RESEARCH` decision and `automatic_decision: false` in JSON form;
- none of the outputs contains `priority_score`.

- [ ] **Step 3: Assert dogfood output boundaries before documenting them**

```bash
python - <<'PY'
import json
from pathlib import Path

active = Path("/tmp/question-radar-v09-active.txt").read_text(encoding="utf-8")
parked = Path("/tmp/question-radar-v09-parked.txt").read_text(encoding="utf-8")
history_text = Path("/tmp/question-radar-v09-history.json").read_text(encoding="utf-8")
history = json.loads(history_text)

assert "DO_NOW: 1" in active
assert "RESEARCH: 1" in active
assert "PARKED: 1" in active
assert "KILLED: 0" in active
assert "WARNING:" not in active
assert "No action is currently requested." in parked
assert history["automatic_decision"] is False
assert history["history"][0]["decision"] == "RESEARCH"
assert "priority_score" not in active + parked + history_text
print("dogfood boundary: OK")
PY
```

Expected:

```text
dogfood boundary: OK
```

- [ ] **Step 4: Generate the benchmark Markdown from the exact captured files**

```bash
python - <<'PY'
from pathlib import Path

active = Path("/tmp/question-radar-v09-active.txt").read_text(encoding="utf-8").rstrip()
parked = Path("/tmp/question-radar-v09-parked.txt").read_text(encoding="utf-8").rstrip()
history = Path("/tmp/question-radar-v09-history.json").read_text(encoding="utf-8").rstrip()

content = f'''# Investigation Decision Gate v0.9 — Sanitized Dogfood

## Boundary

This benchmark uses a disposable SQLite database and sanitized public-safe investigation descriptions. It does not persist private operator state or claim that these scenarios are canonical personal decisions.

## Cases

### 1. Infrastructure scaling

Expected operator state: `PARKED`.

### 2. Lithium / GeoAI problem discovery

Expected operator state: `RESEARCH` with a bounded evidence-gathering next test.

### 3. Existing-product external feedback

Expected operator state: `DO_NOW` with one externally observable next test.

## Active projection

```text
{active}
```

## Parked rendering

```text
{parked}
```

## Research history

```json
{history}
```

## Verification

- three operational states exercised;
- no private canonical state stored;
- no automatic decision changes;
- no WIP warning at one `DO_NOW`;
- no priority score emitted;
- append-only decision storage used throughout.
'''
Path("benchmarks/dogfood-investigation-decision-gate-2026-09-04.md").write_text(
    content, encoding="utf-8"
)
PY
```

- [ ] **Step 5: Run docs-facing checks and commit**

```bash
question-radar --help
question-radar decision --help
pytest tests/test_decision_cli.py tests/test_decision_export.py -v
git add README.md benchmarks/dogfood-investigation-decision-gate-2026-09-04.md
git commit -m "docs: dogfood investigation decision gate v0.9"
```

Expected: help commands exit 0 and selected tests pass before commit.

---

### Task 6: Full regression and completion verification

**Files:**
- Modify only the smallest v0.9 file responsible if verification exposes a defect.
- Historical tests may change only where additive root-help discoverability legitimately requires the new `decision` namespace.

**Interfaces:**
- Consumes the complete repository suite and installed CLI.
- Produces fresh evidence that v0.9 meets the spec while v0.1-v0.8 remain intact.

- [ ] **Step 1: Add defense-in-depth schema test for branching**

Append to `tests/test_decision_storage.py`:

```python
def test_schema_unique_supersedes_blocks_two_direct_successors(tmp_path):
    store = prepared_store(tmp_path, node("q-a"))
    store.insert(decision("dec-1", "q-a"))
    store.initialize()
    columns = (
        "id", "question_id", "decision", "rationale", "goal_alignment",
        "external_signal", "testable_now", "leverage", "cost", "confidence",
        "next_test", "resume_when", "kill_condition", "supersedes_decision_id",
        "created_at",
    )
    first = decision(
        "dec-2", "q-a", decision="RESEARCH", supersedes_decision_id="dec-1",
        created_at="2026-09-04T12:10:00-03:00",
    )
    second = decision(
        "dec-3", "q-a", decision="RESEARCH", supersedes_decision_id="dec-1",
        created_at="2026-09-04T12:11:00-03:00",
    )
    with sqlite3.connect(store.db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        payload = first.to_dict()
        connection.execute(
            "INSERT INTO investigation_decisions_v09 (" + ", ".join(columns)
            + ") VALUES (" + ", ".join("?" for _ in columns) + ")",
            tuple(payload[column] for column in columns),
        )
        payload = second.to_dict()
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO investigation_decisions_v09 (" + ", ".join(columns)
                + ") VALUES (" + ", ".join("?" for _ in columns) + ")",
                tuple(payload[column] for column in columns),
            )
```

- [ ] **Step 2: Run the v0.9 focused suite**

```bash
pytest tests/test_decisions.py tests/test_decision_storage.py tests/test_decision_export.py tests/test_decision_cli.py -v
```

Expected: zero failures.

- [ ] **Step 3: Run the entire repository suite**

```bash
pytest -q
```

Expected: zero failures across v0.1-v0.9.

- [ ] **Step 4: Verify installed CLI boundaries**

```bash
question-radar --help
question-radar decision --help
question-radar decision record --help
question-radar retrieval --help
question-radar benchmark --help
question-radar lineage --help
```

Expected: every command exits 0; `decision` is additive and all previous namespaces remain available.

- [ ] **Step 5: Verify dependency and entrypoint boundaries**

```bash
python - <<'PY'
from pathlib import Path
text = Path("pyproject.toml").read_text(encoding="utf-8")
assert "dependencies = []" in text
assert 'question-radar = "question_radar.cli_v09:main"' in text
print("dependency boundary: OK")
print("cli facade: OK")
PY
```

Expected:

```text
dependency boundary: OK
cli facade: OK
```

- [ ] **Step 6: Review the final diff against the approved spec**

```bash
git diff main...HEAD -- \
  src/question_radar/decisions.py \
  src/question_radar/decision_storage.py \
  src/question_radar/decision_export.py \
  src/question_radar/cli_v09.py \
  tests/test_decisions.py \
  tests/test_decision_storage.py \
  tests/test_decision_export.py \
  tests/test_decision_cli.py \
  README.md \
  benchmarks/dogfood-investigation-decision-gate-2026-09-04.md \
  pyproject.toml
```

Verify all of these statements directly from the diff:

- no mutable current-state field/table exists;
- no score or automatic priority calculation exists;
- no historical SQLite schema is modified;
- no v0.9 decision-path call to `QuestionLineageStore.initialize()` exists;
- no runtime dependency is added;
- WIP warning cannot block or mutate the fourth `DO_NOW` record;
- dogfood text is sanitized and explicitly non-canonical;
- all decision vocabularies remain closed and exact.

- [ ] **Step 7: If Step 6 exposed a defect, make the smallest correction and rerun the complete suite**

Stage only the known v0.9 surface files:

```bash
git add \
  src/question_radar/decisions.py \
  src/question_radar/decision_storage.py \
  src/question_radar/decision_export.py \
  src/question_radar/cli_v09.py \
  tests/test_decisions.py \
  tests/test_decision_storage.py \
  tests/test_decision_export.py \
  tests/test_decision_cli.py \
  README.md \
  benchmarks/dogfood-investigation-decision-gate-2026-09-04.md \
  pyproject.toml

git diff --cached --quiet || git commit -m "fix: close v0.9 verification gap"
pytest -q
```

Expected: final `pytest -q` exits 0. If no files changed, `git diff --cached --quiet` prevents an empty commit.

---

## Execution Notes

- Implement tasks strictly in order: contract → storage → rendering → CLI → dogfood/docs → full verification.
- At execution time, create an isolated worktree via `superpowers:using-git-worktrees` before touching implementation code.
- Follow RED → GREEN → focused verification → commit for Tasks 1–4.
- Preserve the commit boundaries above; each is an independent review gate.
- If implementation shows that linear supersession cannot be enforced without weakening an approved invariant, stop implementation and return to design review.
- If a historical test fails because behavior changed outside additive root-help text or the new `decision` namespace, treat it as a v0.9 regression rather than rewriting the old test to accept the regression.
