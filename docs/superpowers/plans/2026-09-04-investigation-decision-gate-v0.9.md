# Investigation Decision Gate v0.9 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a persistent, auditable, append-only investigation decision layer that records `DO_NOW`, `RESEARCH`, `PARKED`, and `KILLED` judgments for existing v0.4 question nodes without granting Question Radar automatic prioritization authority.

**Architecture:** Add four isolated v0.9 modules: an immutable decision contract, a SQLite-backed decision store with fail-closed v0.4 prerequisite checks and linear supersession history, deterministic Markdown/JSON rendering, and a new CLI facade that delegates every historical command to the existing v0.8 facade. The feature owns only `investigation_decisions_v09`; current state is always derived from immutable history, and the WIP rule is advisory only.

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
- A new revision may supersede only the exact current leaf for the same question.
- The decision path must fail closed if `question_nodes_v04` is absent or structurally unsupported.
- v0.9 may create only `investigation_decisions_v09`; it must not call `QuestionLineageStore.initialize()` to manufacture historical prerequisites.
- Duplicate decision ids are rejected strictly, even when the incoming payload matches the stored row.
- Current state is derived from immutable history; no mutable `current_state` table or column is allowed.
- `recommended_do_now_limit = 3` is advisory only; exceeding it emits a warning but never blocks or mutates decisions.
- No embeddings, LLM runtime calls, agents, schedulers, automatic reactivation, remote databases, web UI, retrieval changes, novelty changes, or benchmark changes.
- Existing v0.1-v0.8 commands and tests remain backward compatible.

---

## File Structure

### New files

- `src/question_radar/decisions.py` — immutable `InvestigationDecision` contract, closed vocabularies, validation helpers, timestamp ordering key, WIP constant.
- `src/question_radar/decision_storage.py` — fail-closed v0.4 prerequisite validation, v0.9 schema ownership, append-only inserts, supersession validation, current/history projections, question lookup.
- `src/question_radar/decision_export.py` — deterministic Markdown/JSON renderers for show/history/active and WIP warning generation.
- `src/question_radar/cli_v09.py` — new facade for `question-radar decision ...`; delegates all non-decision commands to `cli_v06`.
- `tests/test_decisions.py` — domain-contract and state-specific validation tests.
- `tests/test_decision_storage.py` — persistence, prerequisite, supersession, projection, corruption, ordering, active-state tests.
- `tests/test_decision_export.py` — deterministic Markdown/JSON and advisory WIP rendering tests.
- `tests/test_decision_cli.py` — parser, record/show/history/active, metadata generation, fail-closed and installed-entrypoint tests.
- `benchmarks/dogfood-investigation-decision-gate-2026-09-04.md` — sanitized temporary-database dogfood record for three real investigation patterns.

### Modified files

- `pyproject.toml` — switch console-script target from `question_radar.cli_v06:main` to `question_radar.cli_v09:main`; keep `dependencies = []`.
- `README.md` — document v0.8/v0.9, the decision gate, authority boundary, CLI examples, and append-only decision semantics.

---

### Task 1: Immutable `InvestigationDecision` contract

**Files:**
- Create: `src/question_radar/decisions.py`
- Create: `tests/test_decisions.py`

**Interfaces:**
- Consumes: no new v0.9 interfaces; standard-library `dataclass`, `datetime`.
- Produces:
  - `DECISION_STATES: tuple[str, ...]`
  - `COST_LEVELS: tuple[str, ...]`
  - `CONFIDENCE_LEVELS: tuple[str, ...]`
  - `RECOMMENDED_DO_NOW_LIMIT: int = 3`
  - `InvestigationDecision.from_dict(payload: dict[str, Any]) -> InvestigationDecision`
  - `InvestigationDecision.to_dict() -> dict[str, Any]`
  - `decision_timestamp_sort_key(value: str) -> datetime`

- [ ] **Step 1: Write failing tests for the valid round trip and closed vocabularies**

```python
# tests/test_decisions.py
import pytest

from question_radar.decisions import (
    CONFIDENCE_LEVELS,
    COST_LEVELS,
    DECISION_STATES,
    InvestigationDecision,
    RECOMMENDED_DO_NOW_LIMIT,
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


def test_decision_contract_round_trips_without_hidden_fields():
    decision = InvestigationDecision.from_dict(valid_payload())
    assert decision.to_dict() == valid_payload()


def test_closed_vocabularies_and_wip_limit_are_frozen():
    assert DECISION_STATES == ("DO_NOW", "RESEARCH", "PARKED", "KILLED")
    assert COST_LEVELS == ("low", "medium", "high")
    assert CONFIDENCE_LEVELS == ("low", "medium", "high")
    assert RECOMMENDED_DO_NOW_LIMIT == 3
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
pytest tests/test_decisions.py -v
```

Expected: collection/import failure because `question_radar.decisions` does not exist.

- [ ] **Step 3: Add failing validation tests for required fields, booleans, timestamps, and state-specific requirements**

```python
@pytest.mark.parametrize("field", ["id", "question_id", "rationale"])
def test_required_text_fields_reject_blank_values(field):
    with pytest.raises(ValueError, match=field):
        InvestigationDecision.from_dict(valid_payload(**{field: "   "}))


@pytest.mark.parametrize("field", ["goal_alignment", "external_signal", "testable_now", "leverage"])
def test_gate_fields_require_real_booleans(field):
    with pytest.raises(ValueError, match=f"{field} must be a boolean"):
        InvestigationDecision.from_dict(valid_payload(**{field: 1}))


@pytest.mark.parametrize("decision", ["DO_NOW", "RESEARCH"])
def test_active_work_states_require_next_test(decision):
    with pytest.raises(ValueError, match="next_test must be a non-empty string"):
        InvestigationDecision.from_dict(valid_payload(decision=decision, next_test=None))


def test_parked_requires_resume_when():
    with pytest.raises(ValueError, match="resume_when must be a non-empty string"):
        InvestigationDecision.from_dict(
            valid_payload(decision="PARKED", next_test=None, resume_when=None)
        )


def test_killed_allows_optional_kill_condition():
    decision = InvestigationDecision.from_dict(
        valid_payload(decision="KILLED", next_test=None, kill_condition=None)
    )
    assert decision.decision == "KILLED"
    assert decision.kill_condition is None


def test_timezone_naive_created_at_is_rejected():
    with pytest.raises(ValueError, match="created_at must be a timezone-aware ISO timestamp"):
        InvestigationDecision.from_dict(valid_payload(created_at="2026-09-04T15:00:00"))


def test_unknown_fields_fail_closed():
    payload = valid_payload()
    payload["priority_score"] = 99
    with pytest.raises(ValueError, match="unknown fields: priority_score"):
        InvestigationDecision.from_dict(payload)
```

- [ ] **Step 4: Implement the minimal immutable contract**

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


def _timezone_aware_timestamp(name: str, value: Any) -> str:
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
    cleaned = _timezone_aware_timestamp("timestamp", value)
    return datetime.fromisoformat(cleaned.replace("Z", "+00:00")).astimezone(timezone.utc)


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

        decision = payload["decision"]
        if decision not in DECISION_STATES:
            raise ValueError("decision must be one of: " + ", ".join(DECISION_STATES))
        cost = payload["cost"]
        if cost not in COST_LEVELS:
            raise ValueError("cost must be one of: " + ", ".join(COST_LEVELS))
        confidence = payload["confidence"]
        if confidence not in CONFIDENCE_LEVELS:
            raise ValueError("confidence must be one of: " + ", ".join(CONFIDENCE_LEVELS))

        next_test = _optional_text("next_test", payload["next_test"])
        resume_when = _optional_text("resume_when", payload["resume_when"])
        kill_condition = _optional_text("kill_condition", payload["kill_condition"])
        supersedes = _optional_text("supersedes_decision_id", payload["supersedes_decision_id"])

        if decision in {"DO_NOW", "RESEARCH"} and next_test is None:
            raise ValueError("next_test must be a non-empty string for DO_NOW or RESEARCH")
        if decision == "PARKED" and resume_when is None:
            raise ValueError("resume_when must be a non-empty string for PARKED")

        return cls(
            id=_required_text("id", payload["id"]),
            question_id=_required_text("question_id", payload["question_id"]),
            decision=decision,
            rationale=_required_text("rationale", payload["rationale"]),
            goal_alignment=_required_bool("goal_alignment", payload["goal_alignment"]),
            external_signal=_required_bool("external_signal", payload["external_signal"]),
            testable_now=_required_bool("testable_now", payload["testable_now"]),
            leverage=_required_bool("leverage", payload["leverage"]),
            cost=cost,
            confidence=confidence,
            next_test=next_test,
            resume_when=resume_when,
            kill_condition=kill_condition,
            supersedes_decision_id=supersedes,
            created_at=_timezone_aware_timestamp("created_at", payload["created_at"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

- [ ] **Step 5: Run the focused contract suite and verify GREEN**

Run:

```bash
pytest tests/test_decisions.py -v
```

Expected: all `test_decisions.py` tests pass.

- [ ] **Step 6: Commit the contract slice**

```bash
git add src/question_radar/decisions.py tests/test_decisions.py
git commit -m "feat: add investigation decision contract v0.9"
```

---

### Task 2: Fail-closed SQLite decision store and linear supersession history

**Files:**
- Create: `src/question_radar/decision_storage.py`
- Create: `tests/test_decision_storage.py`

**Interfaces:**
- Consumes:
  - `InvestigationDecision`
  - `decision_timestamp_sort_key(value: str) -> datetime`
  - existing `QuestionNode` from `question_radar.lineage`
- Produces:
  - `InvestigationDecisionStore(db_path: str | Path)`
  - `initialize() -> None`
  - `insert(decision: InvestigationDecision) -> None`
  - `get(decision_id: str) -> InvestigationDecision | None`
  - `get_question_node(question_id: str) -> QuestionNode | None`
  - `get_current(question_id: str) -> InvestigationDecision | None`
  - `list_history(question_id: str) -> list[InvestigationDecision]`
  - `list_current_decisions() -> list[InvestigationDecision]`

- [ ] **Step 1: Write RED tests for missing database and missing/unsupported v0.4 prerequisite**

```python
# tests/test_decision_storage.py
import sqlite3

import pytest

from question_radar.decision_storage import InvestigationDecisionStore
from question_radar.decisions import InvestigationDecision
from question_radar.lineage import QuestionNode
from question_radar.lineage_storage import QuestionLineageStore


def node(node_id: str, created_at: str = "2026-09-04T12:00:00-03:00") -> QuestionNode:
    return QuestionNode.from_dict(
        {
            "id": node_id,
            "question": f"Question {node_id}?",
            "source": "manual",
            "source_ref": None,
            "created_at": created_at,
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


def test_missing_database_fails_closed_without_creating_file(tmp_path):
    db = tmp_path / "missing.sqlite3"
    store = InvestigationDecisionStore(db)
    with pytest.raises(RuntimeError, match="database does not exist"):
        store.initialize()
    assert not db.exists()


def test_missing_v04_table_fails_closed_without_creating_v09_table(tmp_path):
    db = tmp_path / "empty.sqlite3"
    sqlite3.connect(db).close()
    store = InvestigationDecisionStore(db)
    with pytest.raises(RuntimeError, match="question_nodes_v04 prerequisite"):
        store.initialize()
    with sqlite3.connect(db) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "investigation_decisions_v09" not in tables


def test_unsupported_v04_shape_fails_closed(tmp_path):
    db = tmp_path / "bad-lineage.sqlite3"
    with sqlite3.connect(db) as connection:
        connection.execute("CREATE TABLE question_nodes_v04 (id TEXT PRIMARY KEY)")
    with pytest.raises(RuntimeError, match="question_nodes_v04 prerequisite"):
        InvestigationDecisionStore(db).initialize()
```

- [ ] **Step 2: Run the prerequisite tests and verify RED**

Run:

```bash
pytest tests/test_decision_storage.py -v
```

Expected: import failure because `question_radar.decision_storage` does not exist.

- [ ] **Step 3: Implement the database connection, prerequisite verification, and v0.9 schema only**

```python
# src/question_radar/decision_storage.py
from pathlib import Path
import sqlite3

from question_radar.decisions import InvestigationDecision, decision_timestamp_sort_key
from question_radar.lineage import QuestionNode

_REQUIRED_V04_COLUMNS = {"id", "question", "source", "source_ref", "created_at"}
_DECISION_COLUMNS = (
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
        try:
            connection = sqlite3.connect(self.db_path)
            connection.execute("PRAGMA foreign_keys = ON")
            connection.row_factory = sqlite3.Row
            return connection
        except sqlite3.Error as exc:
            raise RuntimeError(f"cannot open SQLite database at {self.db_path}: {exc}") from exc

    def _verify_v04_prerequisite(self, connection: sqlite3.Connection) -> None:
        row = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='question_nodes_v04'"
        ).fetchone()
        if row is None:
            raise RuntimeError("question_nodes_v04 prerequisite is missing")
        columns = {item["name"] for item in connection.execute("PRAGMA table_info(question_nodes_v04)")}
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

- [ ] **Step 4: Run only the prerequisite tests and verify GREEN**

Run:

```bash
pytest tests/test_decision_storage.py -k "missing_database or missing_v04 or unsupported_v04" -v
```

Expected: the three prerequisite tests pass.

- [ ] **Step 5: Add RED tests for inserts, duplicate ids, unknown questions, roots, revisions, cross-question supersession, and current-leaf-only rules**

```python
def prepared_store(tmp_path, *nodes):
    db = tmp_path / "questions.sqlite3"
    lineage = QuestionLineageStore(db)
    lineage.insert_bundle(list(nodes), [])
    return InvestigationDecisionStore(db)


def test_insert_requires_existing_question_and_rejects_duplicate_id(tmp_path):
    store = prepared_store(tmp_path, node("q-a"))
    store.insert(decision("dec-1", "q-a"))
    assert store.get("dec-1").id == "dec-1"

    with pytest.raises(ValueError, match="decision id already exists: dec-1"):
        store.insert(decision("dec-1", "q-a"))

    with pytest.raises(ValueError, match="question node not found: missing"):
        store.insert(decision("dec-2", "missing"))


def test_first_decision_must_be_root_and_second_must_supersede_current_leaf(tmp_path):
    store = prepared_store(tmp_path, node("q-a"))

    with pytest.raises(ValueError, match="first decision must not supersede another decision"):
        store.insert(decision("dec-invalid-root", "q-a", supersedes_decision_id="dec-x"))

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
    assert store.get_current("q-a").id == "dec-2"


def test_revision_cannot_supersede_other_question_or_non_current_decision(tmp_path):
    store = prepared_store(tmp_path, node("q-a"), node("q-b"))
    store.insert(decision("a-1", "q-a"))
    store.insert(decision("b-1", "q-b"))

    with pytest.raises(ValueError, match="superseded decision belongs to another question"):
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
```

- [ ] **Step 6: Implement question lookup, immutable insert validation, and strict duplicate-id behavior**

```python
    def get_question_node(self, question_id: str) -> QuestionNode | None:
        self.initialize()
        with self._connect_existing() as connection:
            row = connection.execute(
                "SELECT id, question, source, source_ref, created_at "
                "FROM question_nodes_v04 WHERE id = ?",
                (question_id,),
            ).fetchone()
        return QuestionNode.from_dict(dict(row)) if row is not None else None

    def get(self, decision_id: str) -> InvestigationDecision | None:
        self.initialize()
        with self._connect_existing() as connection:
            row = connection.execute(
                "SELECT * FROM investigation_decisions_v09 WHERE id = ?",
                (decision_id,),
            ).fetchone()
        return InvestigationDecision.from_dict(dict(row)) if row is not None else None

    def insert(self, decision: InvestigationDecision) -> None:
        self.initialize()
        with self._connect_existing() as connection:
            self._verify_v04_prerequisite(connection)
            if connection.execute(
                "SELECT 1 FROM investigation_decisions_v09 WHERE id = ?",
                (decision.id,),
            ).fetchone() is not None:
                raise ValueError(f"decision id already exists: {decision.id}")

            if connection.execute(
                "SELECT 1 FROM question_nodes_v04 WHERE id = ?",
                (decision.question_id,),
            ).fetchone() is None:
                raise ValueError(f"question node not found: {decision.question_id}")

            current = self._get_current_in_connection(connection, decision.question_id)
            if current is None:
                if decision.supersedes_decision_id is not None:
                    raise ValueError("first decision must not supersede another decision")
            else:
                if decision.supersedes_decision_id is None:
                    raise ValueError(
                        f"revision must supersede current decision: {current.id}"
                    )
                prior = self._get_in_connection(connection, decision.supersedes_decision_id)
                if prior is None:
                    raise ValueError(
                        f"superseded decision not found: {decision.supersedes_decision_id}"
                    )
                if prior.question_id != decision.question_id:
                    raise ValueError("superseded decision belongs to another question")
                if prior.id != current.id:
                    raise ValueError(
                        f"revision must supersede current decision: {current.id}"
                    )

            try:
                connection.execute(
                    "INSERT INTO investigation_decisions_v09 "
                    "(" + ", ".join(_DECISION_COLUMNS) + ") VALUES (" + ", ".join("?" for _ in _DECISION_COLUMNS) + ")",
                    tuple(decision.to_dict()[column] for column in _DECISION_COLUMNS),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("investigation decision violates the v0.9 schema") from exc

            self._validate_history_in_connection(connection, decision.question_id)
```

- [ ] **Step 7: Add RED tests for deterministic history/current projection and corrupted ambiguity detection**

```python
def test_history_and_current_are_deterministic_by_instant_then_id(tmp_path):
    store = prepared_store(tmp_path, node("q-a"))
    store.insert(decision("dec-a", "q-a", created_at="2026-09-04T13:00:00+01:00"))
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
    assert store.get_current("q-a").id == "dec-b"


def test_corrupt_multiple_roots_fail_closed(tmp_path):
    store = prepared_store(tmp_path, node("q-a"))
    store.initialize()
    first = decision("dec-1", "q-a")
    second = decision("dec-2", "q-a", created_at="2026-09-04T12:06:00-03:00")
    with sqlite3.connect(store.db_path) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        for item in (first, second):
            payload = item.to_dict()
            connection.execute(
                "INSERT INTO investigation_decisions_v09 "
                "(id, question_id, decision, rationale, goal_alignment, external_signal, "
                "testable_now, leverage, cost, confidence, next_test, resume_when, "
                "kill_condition, supersedes_decision_id, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                tuple(payload[column] for column in (
                    "id", "question_id", "decision", "rationale", "goal_alignment",
                    "external_signal", "testable_now", "leverage", "cost", "confidence",
                    "next_test", "resume_when", "kill_condition", "supersedes_decision_id",
                    "created_at",
                )),
            )
    with pytest.raises(RuntimeError, match="ambiguous decision history for q-a"):
        store.get_current("q-a")
```

- [ ] **Step 8: Implement history validation and projections**

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
        for prior_id in referenced:
            if prior_id not in by_id:
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

    def _get_current_in_connection(self, connection, question_id):
        return self._validate_history_in_connection(connection, question_id)

    def get_current(self, question_id: str) -> InvestigationDecision | None:
        self.initialize()
        with self._connect_existing() as connection:
            return self._get_current_in_connection(connection, question_id)

    def list_history(self, question_id: str) -> list[InvestigationDecision]:
        self.initialize()
        with self._connect_existing() as connection:
            self._validate_history_in_connection(connection, question_id)
            history = self._history_in_connection(connection, question_id)
        return sorted(history, key=lambda item: (decision_timestamp_sort_key(item.created_at), item.id))

    def list_current_decisions(self) -> list[InvestigationDecision]:
        self.initialize()
        with self._connect_existing() as connection:
            question_ids = [
                row["question_id"]
                for row in connection.execute(
                    "SELECT DISTINCT question_id FROM investigation_decisions_v09 ORDER BY question_id"
                )
            ]
            current = [
                self._get_current_in_connection(connection, question_id)
                for question_id in question_ids
            ]
        return sorted(
            [item for item in current if item is not None],
            key=lambda item: (decision_timestamp_sort_key(item.created_at), item.id),
        )
```

- [ ] **Step 9: Add and pass active-state/zero-state tests**

```python
def test_list_current_decisions_returns_zero_or_one_leaf_per_question(tmp_path):
    store = prepared_store(tmp_path, node("q-a"), node("q-b"), node("q-c"))
    assert store.list_current_decisions() == []
    store.insert(decision("a-1", "q-a"))
    store.insert(decision("b-1", "q-b", decision="RESEARCH"))
    store.insert(
        decision(
            "c-1",
            "q-c",
            decision="PARKED",
            next_test=None,
            resume_when="External condition changes.",
        )
    )
    assert [item.id for item in store.list_current_decisions()] == ["a-1", "b-1", "c-1"]
```

Run:

```bash
pytest tests/test_decision_storage.py -v
```

Expected: all decision storage tests pass.

- [ ] **Step 10: Commit the persistence slice**

```bash
git add src/question_radar/decision_storage.py tests/test_decision_storage.py
git commit -m "feat: persist investigation decisions v0.9"
```

---

### Task 3: Deterministic Markdown/JSON rendering and advisory WIP projection

**Files:**
- Create: `src/question_radar/decision_export.py`
- Create: `tests/test_decision_export.py`

**Interfaces:**
- Consumes:
  - `InvestigationDecision`
  - `QuestionNode`
  - `RECOMMENDED_DO_NOW_LIMIT`
  - current decision entries supplied as `list[tuple[QuestionNode, InvestigationDecision]]`
- Produces:
  - `render_decision_markdown(node, decision) -> str`
  - `render_decision_json(node, decision) -> str`
  - `render_history_markdown(node, decisions) -> str`
  - `render_history_json(node, decisions) -> str`
  - `render_active_markdown(entries) -> str`
  - `render_active_json(entries) -> str`

- [ ] **Step 1: Write RED tests for deterministic show/history rendering and parked authority language**

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
    return QuestionNode.from_dict(
        {
            "id": node_id,
            "question": question,
            "source": "manual",
            "source_ref": None,
            "created_at": "2026-09-04T12:00:00-03:00",
        }
    )


def parked(decision_id="dec-1", question_id="q-a"):
    return InvestigationDecision.from_dict(
        {
            "id": decision_id,
            "question_id": question_id,
            "decision": "PARKED",
            "rationale": "Useful later, not required now.",
            "goal_alignment": False,
            "external_signal": True,
            "testable_now": False,
            "leverage": True,
            "cost": "medium",
            "confidence": "medium",
            "next_test": None,
            "resume_when": "A real production workload requires it.",
            "kill_condition": None,
            "supersedes_decision_id": None,
            "created_at": "2026-09-04T12:05:00-03:00",
        }
    )


def test_parked_markdown_is_authority_preserving_and_deterministic():
    first = render_decision_markdown(node(), parked())
    second = render_decision_markdown(node(), parked())
    assert first == second
    assert "Current decision: PARKED" in first
    assert "No action is currently requested." in first
    assert "✗ current goal alignment" in first
    assert "✓ external signal" in first
    assert first.endswith("\n")


def test_show_json_exposes_raw_contract_without_priority_score():
    payload = json.loads(render_decision_json(node(), parked()))
    assert payload["decision_version"] == "v0.9"
    assert payload["question"]["id"] == "q-a"
    assert payload["current_decision"]["decision"] == "PARKED"
    assert "priority_score" not in payload
    assert payload["automatic_decision"] is False
```

- [ ] **Step 2: Run the render tests and verify RED**

Run:

```bash
pytest tests/test_decision_export.py -v
```

Expected: import failure because `question_radar.decision_export` does not exist.

- [ ] **Step 3: Add RED tests for history ordering pass-through, active counts, WIP warning, and no warning at exactly three `DO_NOW` decisions**

```python
def active_decision(decision_id, question_id, state="DO_NOW"):
    return InvestigationDecision.from_dict(
        {
            "id": decision_id,
            "question_id": question_id,
            "decision": state,
            "rationale": "Bounded active work.",
            "goal_alignment": True,
            "external_signal": True,
            "testable_now": True,
            "leverage": True,
            "cost": "low",
            "confidence": "medium",
            "next_test": "Run one bounded test.",
            "resume_when": None,
            "kill_condition": None,
            "supersedes_decision_id": None,
            "created_at": "2026-09-04T12:05:00-03:00",
        }
    )


def test_active_projection_counts_all_states_but_lists_only_do_now_and_research():
    entries = [
        (node("q-1"), active_decision("d-1", "q-1", "DO_NOW")),
        (node("q-2"), active_decision("d-2", "q-2", "RESEARCH")),
        (node("q-3"), parked("d-3", "q-3")),
    ]
    payload = json.loads(render_active_json(entries))
    assert payload["counts"] == {"DO_NOW": 1, "RESEARCH": 1, "PARKED": 1, "KILLED": 0}
    assert [item["decision"]["decision"] for item in payload["active"]] == ["DO_NOW", "RESEARCH"]
    assert payload["wip_warning"] is None


def test_wip_warning_appears_only_above_three_do_now_and_never_changes_records():
    three = [
        (node(f"q-{index}"), active_decision(f"d-{index}", f"q-{index}"))
        for index in range(1, 4)
    ]
    four = three + [(node("q-4"), active_decision("d-4", "q-4"))]
    assert json.loads(render_active_json(three))["wip_warning"] is None
    payload = json.loads(render_active_json(four))
    assert "4 investigations are marked DO_NOW" in payload["wip_warning"]
    assert "No decision was changed automatically." in payload["wip_warning"]
    assert all(item[1].decision == "DO_NOW" for item in four)
```

- [ ] **Step 4: Implement deterministic renderers with one shared active projection helper**

```python
# src/question_radar/decision_export.py
from __future__ import annotations

import json

from question_radar.decisions import (
    DECISION_STATES,
    InvestigationDecision,
    RECOMMENDED_DO_NOW_LIMIT,
)
from question_radar.lineage import QuestionNode


def _gate_lines(decision: InvestigationDecision) -> list[str]:
    labels = (
        ("goal_alignment", "current goal alignment"),
        ("external_signal", "external signal"),
        ("testable_now", "testable now"),
        ("leverage", "leverage"),
    )
    return [
        f"{'✓' if getattr(decision, field) else '✗'} {label}"
        for field, label in labels
    ]


def render_decision_json(node: QuestionNode, decision: InvestigationDecision) -> str:
    payload = {
        "automatic_decision": False,
        "current_decision": decision.to_dict(),
        "decision_version": "v0.9",
        "question": node.to_dict(),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_decision_markdown(node: QuestionNode, decision: InvestigationDecision) -> str:
    lines = [
        "# Investigation Decision v0.9",
        "",
        f"Question: {node.question}",
        f"Question id: {node.id}",
        "",
        f"Current decision: {decision.decision}",
        f"Decision: {decision.id}",
        "",
        "Why:",
        decision.rationale,
    ]
    if decision.next_test is not None:
        lines.extend(["", "Next test:", decision.next_test])
    if decision.resume_when is not None:
        lines.extend(["", "Resume when:", decision.resume_when])
    if decision.kill_condition is not None:
        lines.extend(["", "Kill condition:", decision.kill_condition])
    lines.extend(["", "Gates:", *_gate_lines(decision)])
    if decision.decision == "PARKED":
        lines.extend(["", "No action is currently requested."])
    lines.extend(["", "Operator decision recorded; no automatic prioritization was performed."])
    return "\n".join(lines) + "\n"


def render_history_json(node: QuestionNode, decisions: list[InvestigationDecision]) -> str:
    return json.dumps(
        {
            "decision_version": "v0.9",
            "question": node.to_dict(),
            "history": [item.to_dict() for item in decisions],
            "automatic_decision": False,
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def render_history_markdown(node: QuestionNode, decisions: list[InvestigationDecision]) -> str:
    lines = ["# Investigation Decision History v0.9", "", f"Question: {node.question}", ""]
    for item in decisions:
        lines.extend(
            [
                f"## {item.id} — {item.decision}",
                f"created_at: {item.created_at}",
                f"supersedes: {item.supersedes_decision_id}",
                f"rationale: {item.rationale}",
                "",
            ]
        )
    lines.append("History is append-only; no automatic prioritization was performed.")
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
    do_now = counts["DO_NOW"]
    warning = None
    if do_now > RECOMMENDED_DO_NOW_LIMIT:
        warning = (
            f"WARNING: {do_now} investigations are marked DO_NOW. "
            f"Recommended operating limit: {RECOMMENDED_DO_NOW_LIMIT}. "
            "No decision was changed automatically."
        )
    return counts, active, warning


def render_active_json(entries) -> str:
    counts, active, warning = _active_projection(entries)
    return json.dumps(
        {
            "active": active,
            "automatic_decision": False,
            "counts": counts,
            "decision_version": "v0.9",
            "recommended_do_now_limit": RECOMMENDED_DO_NOW_LIMIT,
            "wip_warning": warning,
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def render_active_markdown(entries) -> str:
    counts, active, warning = _active_projection(entries)
    lines = [
        "# Active Investigation Decisions v0.9",
        "",
        f"DO_NOW: {counts['DO_NOW']}",
        f"RESEARCH: {counts['RESEARCH']}",
        f"PARKED: {counts['PARKED']}",
        f"KILLED: {counts['KILLED']}",
        "",
        "## Active",
    ]
    if not active:
        lines.append("None.")
    else:
        for item in active:
            lines.append(
                f"- {item['decision']['decision']} — {item['question']['question']} "
                f"({item['decision']['id']})"
            )
    if warning is not None:
        lines.extend(["", warning])
    lines.extend(["", "No decision was changed automatically."])
    return "\n".join(lines) + "\n"
```

- [ ] **Step 5: Run render tests and verify GREEN**

Run:

```bash
pytest tests/test_decision_export.py -v
```

Expected: all decision export tests pass.

- [ ] **Step 6: Commit the rendering slice**

```bash
git add src/question_radar/decision_export.py tests/test_decision_export.py
git commit -m "feat: render investigation decisions v0.9"
```

---

### Task 4: New `cli_v09` facade and installed `decision` namespace

**Files:**
- Create: `src/question_radar/cli_v09.py`
- Create: `tests/test_decision_cli.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Consumes:
  - all `decision_storage` store methods
  - all `decision_export` renderers
  - `InvestigationDecision.from_dict`
  - existing `question_radar.cli_v06.main` for every historical command
- Produces CLI commands:
  - `question-radar decision record ...`
  - `question-radar decision show <question_id> --format markdown|json`
  - `question-radar decision history <question_id> --format markdown|json`
  - `question-radar decision active --format markdown|json`
  - `main(argv: list[str] | None = None) -> int`

- [ ] **Step 1: Write RED parser tests for the four decision commands and explicit audit metadata flags**

```python
# tests/test_decision_cli.py
import json
import re
import subprocess

from question_radar import cli_v09 as cli
from question_radar.lineage import QuestionNode
from question_radar.lineage_storage import QuestionLineageStore


def seed_node(db, node_id="q-a", question="Should this consume attention now?"):
    QuestionLineageStore(db).insert_node(
        QuestionNode.from_dict(
            {
                "id": node_id,
                "question": question,
                "source": "manual",
                "source_ref": None,
                "created_at": "2026-09-04T12:00:00-03:00",
            }
        )
    )


def test_record_parser_accepts_explicit_audit_metadata_and_operator_fields():
    args = cli.build_decision_parser().parse_args(
        [
            "decision",
            "record",
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
        ]
    )
    assert args.decision_command == "record"
    assert args.id == "dec-explicit"
    assert args.created_at == "2026-09-04T15:00:00-03:00"
    assert args.goal_alignment is False
    assert args.external_signal is True
```

- [ ] **Step 2: Run the parser test and verify RED**

Run:

```bash
pytest tests/test_decision_cli.py::test_record_parser_accepts_explicit_audit_metadata_and_operator_fields -v
```

Expected: import failure because `question_radar.cli_v09` does not exist.

- [ ] **Step 3: Implement argument parsing, strict boolean parsing, metadata generation helpers, and historical delegation**

```python
# src/question_radar/cli_v09.py
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import sys
import uuid

from question_radar import cli_v06 as previous_cli
from question_radar.decision_export import (
    render_active_json,
    render_active_markdown,
    render_decision_json,
    render_decision_markdown,
    render_history_json,
    render_history_markdown,
)
from question_radar.decision_storage import InvestigationDecisionStore
from question_radar.decisions import (
    CONFIDENCE_LEVELS,
    COST_LEVELS,
    DECISION_STATES,
    InvestigationDecision,
)


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
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


def _print_root_help() -> None:
    previous_cli.main(["--help"])
    print("  decision            record and inspect Investigation Decision Gate v0.9 judgments")


def build_decision_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="question-radar",
        description="Score questions transparently; never score people.",
    )
    parser.add_argument("--db", default="data/questions.sqlite3")
    subparsers = parser.add_subparsers(dest="command", required=True)
    decision_parser = subparsers.add_parser("decision")
    commands = decision_parser.add_subparsers(dest="decision_command", required=True)

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

    for command in ("show", "history"):
        item = commands.add_parser(command)
        item.add_argument("question_id")
        item.add_argument("--format", choices=("markdown", "json"), default="markdown")

    active = commands.add_parser("active")
    active.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser
```

- [ ] **Step 4: Add RED functional tests for record/show/history/active, generated metadata, and fail-closed missing prerequisite**

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


def test_record_show_history_and_active_round_trip(tmp_path, capsys):
    db = tmp_path / "questions.sqlite3"
    seed_node(db)

    first = record_args()
    first += ["--id", "dec-1", "--created-at", "2026-09-04T12:05:00-03:00"]
    assert cli.main(["--db", str(db), *first]) == 0
    assert capsys.readouterr().out.strip() == "recorded dec-1"

    assert cli.main(["--db", str(db), "decision", "show", "q-a", "--format", "json"]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["current_decision"]["id"] == "dec-1"

    second = record_args(state="PARKED")
    second += [
        "--supersedes", "dec-1",
        "--id", "dec-2",
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


def test_generated_id_and_timestamp_are_auditable(tmp_path, capsys, monkeypatch):
    db = tmp_path / "questions.sqlite3"
    seed_node(db)
    monkeypatch.setattr(cli, "_new_decision_id", lambda: "dec-generated")
    monkeypatch.setattr(cli, "_now_iso", lambda: "2026-09-04T18:00:00+00:00")
    assert cli.main(["--db", str(db), *record_args()]) == 0
    assert "recorded dec-generated" in capsys.readouterr().out
    assert cli.main(["--db", str(db), "decision", "show", "q-a", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["current_decision"]["created_at"] == "2026-09-04T18:00:00+00:00"


def test_decision_command_missing_lineage_prerequisite_fails_closed(tmp_path, capsys):
    db = tmp_path / "empty.sqlite3"
    db.touch()
    result = cli.main(["--db", str(db), "decision", "active"])
    captured = capsys.readouterr()
    assert result == 2
    assert "question_nodes_v04 prerequisite" in captured.err
```

- [ ] **Step 5: Implement command handlers and main routing**

```python

def _handle_record(args) -> int:
    item = InvestigationDecision.from_dict(
        {
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
        }
    )
    InvestigationDecisionStore(args.db).insert(item)
    print(f"recorded {item.id}")
    return 0


def _question_and_current(store, question_id):
    node = store.get_question_node(question_id)
    if node is None:
        raise ValueError(f"question node not found: {question_id}")
    current = store.get_current(question_id)
    return node, current


def _handle_decision(args) -> int:
    store = InvestigationDecisionStore(args.db)
    if args.decision_command == "record":
        return _handle_record(args)
    if args.decision_command == "show":
        node, current = _question_and_current(store, args.question_id)
        if current is None:
            raise ValueError(f"no investigation decision recorded for: {args.question_id}")
        rendered = (
            render_decision_json(node, current)
            if args.format == "json"
            else render_decision_markdown(node, current)
        )
        print(rendered, end="")
        return 0
    if args.decision_command == "history":
        node = store.get_question_node(args.question_id)
        if node is None:
            raise ValueError(f"question node not found: {args.question_id}")
        history = store.list_history(args.question_id)
        rendered = (
            render_history_json(node, history)
            if args.format == "json"
            else render_history_markdown(node, history)
        )
        print(rendered, end="")
        return 0
    if args.decision_command == "active":
        current = store.list_current_decisions()
        entries = [(store.get_question_node(item.question_id), item) for item in current]
        if any(node is None for node, _ in entries):
            raise RuntimeError("current decision references a missing question node")
        typed_entries = [(node, item) for node, item in entries if node is not None]
        rendered = (
            render_active_json(typed_entries)
            if args.format == "json"
            else render_active_markdown(typed_entries)
        )
        print(rendered, end="")
        return 0
    raise ValueError("unknown decision command")


def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    if _root_help_requested(args_list):
        _print_root_help()
        return 0
    if _top_level_command(args_list) != "decision":
        return previous_cli.main(args_list)
    parser = build_decision_parser()
    args = parser.parse_args(args_list)
    try:
        return _handle_decision(args)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: Point the installed console script at the v0.9 facade**

Change only this line in `pyproject.toml`:

```toml
[project.scripts]
question-radar = "question_radar.cli_v09:main"
```

Keep:

```toml
dependencies = []
```

unchanged.

- [ ] **Step 7: Add subprocess regression tests for root help, decision help, and historical delegation**

```python
def test_installed_cli_exposes_decision_namespace_and_preserves_historical_help():
    for args, expected in (
        (["--help"], "decision"),
        (["decision", "--help"], "record"),
        (["decision", "record", "--help"], "--question-id"),
        (["retrieval", "--help"], "compare"),
        (["benchmark", "--help"], "evaluate"),
        (["lineage", "--help"], "node"),
    ):
        completed = subprocess.run(
            ["question-radar", *args],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert expected in completed.stdout
```

- [ ] **Step 8: Run CLI-focused and historical CLI regression tests**

Run:

```bash
pytest tests/test_decision_cli.py tests/test_retrieval_cli.py tests/test_benchmark_cli.py tests/test_lineage_cli.py tests/test_cli.py -v
```

Expected: all selected CLI tests pass, including installed-entrypoint checks.

- [ ] **Step 9: Commit the CLI facade slice**

```bash
git add src/question_radar/cli_v09.py tests/test_decision_cli.py pyproject.toml
git commit -m "feat: expose investigation decision cli v0.9"
```

---

### Task 5: README integration and sanitized real-world dogfood

**Files:**
- Modify: `README.md`
- Create: `benchmarks/dogfood-investigation-decision-gate-2026-09-04.md`

**Interfaces:**
- Consumes: installed `question-radar` CLI from Task 4.
- Produces: public documentation and evidence that three distinct operator investigation patterns were exercised in a disposable SQLite database without encoding private canonical state.

- [ ] **Step 1: Update README version and system flow without changing the project thesis**

Replace the stale version line with:

```markdown
**Version:** v0.9 · Investigation Decision Gate + v0.8 Gold Evaluation Harness + v0.7 Retrieval Calibration & Abstention
```

Extend the existing flow after human review with:

```text
explicit question identity
     ↓
operator investigation decision (v0.9)
     ↓
DO_NOW / RESEARCH / PARKED / KILLED
     ↓
append-only supersession when judgment changes
```

Add these bullets under “What this project demonstrates”:

```markdown
- **Append-only investigation decisions** linked to existing v0.4 question identity.
- **Explicit supersession history** so changed judgment does not rewrite earlier context.
- **Advisory WIP visibility** when more than three investigations are marked `DO_NOW`, without automatic demotion or prioritization.
- **Fail-closed v0.4 prerequisite checks** so v0.9 never creates historical lineage tables just to satisfy itself.
```

Add a compact CLI section containing exact examples for `record`, `show`, `history`, and `active`, and repeat the authority boundary:

```markdown
> Decision gates are operator judgments. Question Radar records and validates them; it does not decide automatically what deserves attention.
```

- [ ] **Step 2: Run the historical and new documentation-facing CLI commands against a disposable database**

Run:

```bash
DOGFOOD_DB=/tmp/question-radar-v09-dogfood.sqlite3
rm -f "$DOGFOOD_DB"

question-radar --db "$DOGFOOD_DB" lineage node add <(printf '%s\n' '{"id":"dog-spqr","question":"When does horizontal PostgreSQL scaling become justified by a real workload?","source":"manual","source_ref":"sanitized-dogfood","created_at":"2026-09-04T18:00:00+00:00"}')
question-radar --db "$DOGFOOD_DB" lineage node add <(printf '%s\n' '{"id":"dog-lithium","question":"Which lithium GeoAI problem is narrow enough for a bounded evidence-gathering test?","source":"manual","source_ref":"sanitized-dogfood","created_at":"2026-09-04T18:01:00+00:00"}')
question-radar --db "$DOGFOOD_DB" lineage node add <(printf '%s\n' '{"id":"dog-revenue","question":"Which existing product demonstration can produce external feedback this week?","source":"manual","source_ref":"sanitized-dogfood","created_at":"2026-09-04T18:02:00+00:00"}')

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

question-radar --db "$DOGFOOD_DB" decision active --format markdown
question-radar --db "$DOGFOOD_DB" decision show dog-spqr --format markdown
question-radar --db "$DOGFOOD_DB" decision history dog-lithium --format json
```

Expected:

- SPQR-like case renders `PARKED` plus `No action is currently requested.`
- lithium/GeoAI case appears under active `RESEARCH` with its explicit next test.
- revenue/product case appears under active `DO_NOW`.
- aggregate counts are `DO_NOW: 1`, `RESEARCH: 1`, `PARKED: 1`, `KILLED: 0`.
- no WIP warning appears because `DO_NOW == 1`.
- no command writes a priority score or claims the system made the decision.

- [ ] **Step 3: Write the dogfood benchmark record from the actual observed outputs**

Create `benchmarks/dogfood-investigation-decision-gate-2026-09-04.md` with this structure and replace only the command-output blocks with the exact fresh output captured in Step 2:

```markdown
# Investigation Decision Gate v0.9 — Sanitized Dogfood

## Boundary

This benchmark uses a disposable SQLite database and sanitized public-safe investigation descriptions. It does not persist private operator state or claim that these scenarios are canonical personal decisions.

## Cases

### 1. Infrastructure scaling
Expected operator state: `PARKED`.
Reason: learning value exists, but no current production workload requires horizontal scaling.
Return condition: a real PostgreSQL workload requires it.

### 2. Lithium / GeoAI problem discovery
Expected operator state: `RESEARCH`.
Next test: collect repeated public operational problems and identify which are observable with GeoAI.

### 3. Existing-product external feedback
Expected operator state: `DO_NOW`.
Next test: publish one existing demonstration and record external evidence.

## Active projection

```text
<paste exact `decision active --format markdown` output here during implementation>
```

## Parked rendering

```text
<paste exact `decision show dog-spqr --format markdown` output here during implementation>
```

## Verification

- three different operational states exercised;
- no private canonical state stored;
- no automatic decision changes;
- WIP warning absent at one `DO_NOW`;
- append-only storage used throughout.
```

The implementation worker must paste fresh command output; do not fabricate the benchmark output from expected strings.

- [ ] **Step 4: Run README-sensitive help checks and the dogfood-specific tests**

Run:

```bash
question-radar --help
question-radar decision --help
pytest tests/test_decision_cli.py tests/test_decision_export.py -v
```

Expected: commands succeed and documentation examples correspond to actual flags and output surfaces.

- [ ] **Step 5: Commit docs and dogfood evidence**

```bash
git add README.md benchmarks/dogfood-investigation-decision-gate-2026-09-04.md
git commit -m "docs: dogfood investigation decision gate v0.9"
```

---

### Task 6: Full regression, schema-defense tests, and completion verification

**Files:**
- Modify only if a failing regression exposes a v0.9 defect: the smallest v0.9 file responsible for that defect.
- Do not rewrite historical tests except a root-help expectation that must now include the additive `decision` namespace.

**Interfaces:**
- Consumes: complete repository test suite and installed CLI.
- Produces: fresh evidence that v0.9 satisfies the spec while v0.1-v0.8 remain green.

- [ ] **Step 1: Add one final defense-in-depth test that direct SQL cannot branch the supersession column under the declared schema**

Add to `tests/test_decision_storage.py`:

```python
def test_schema_unique_supersedes_blocks_two_direct_successors(tmp_path):
    store = prepared_store(tmp_path, node("q-a"))
    store.insert(decision("dec-1", "q-a"))
    store.initialize()
    first_successor = decision(
        "dec-2",
        "q-a",
        decision="RESEARCH",
        supersedes_decision_id="dec-1",
        created_at="2026-09-04T12:10:00-03:00",
    )
    second_successor = decision(
        "dec-3",
        "q-a",
        decision="RESEARCH",
        supersedes_decision_id="dec-1",
        created_at="2026-09-04T12:11:00-03:00",
    )
    columns = (
        "id", "question_id", "decision", "rationale", "goal_alignment",
        "external_signal", "testable_now", "leverage", "cost", "confidence",
        "next_test", "resume_when", "kill_condition", "supersedes_decision_id",
        "created_at",
    )
    with sqlite3.connect(store.db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        payload = first_successor.to_dict()
        connection.execute(
            "INSERT INTO investigation_decisions_v09 (" + ", ".join(columns) + ") VALUES (" + ", ".join("?" for _ in columns) + ")",
            tuple(payload[column] for column in columns),
        )
        payload = second_successor.to_dict()
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO investigation_decisions_v09 (" + ", ".join(columns) + ") VALUES (" + ", ".join("?" for _ in columns) + ")",
                tuple(payload[column] for column in columns),
            )
```

- [ ] **Step 2: Run the entire v0.9 focused suite**

Run:

```bash
pytest tests/test_decisions.py tests/test_decision_storage.py tests/test_decision_export.py tests/test_decision_cli.py -v
```

Expected: zero failures.

- [ ] **Step 3: Run the complete historical repository test suite**

Run:

```bash
pytest -q
```

Expected: zero failures across all v0.1-v0.9 tests.

- [ ] **Step 4: Verify installed CLI help for every facade boundary touched by v0.9**

Run:

```bash
question-radar --help
question-radar decision --help
question-radar decision record --help
question-radar retrieval --help
question-radar benchmark --help
question-radar lineage --help
```

Expected: all commands exit `0`; `decision` is additive and retrieval/benchmark/lineage remain available.

- [ ] **Step 5: Verify the package still has no runtime dependencies**

Run:

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

- [ ] **Step 6: Review the final diff against the approved spec before claiming completion**

Run:

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

Check explicitly:

- no mutable current-state field/table exists;
- no score or automatic priority calculation exists;
- no historical schema is modified;
- no call to `QuestionLineageStore.initialize()` exists in the v0.9 decision path;
- no new runtime dependency exists;
- WIP warning does not block or mutate the fourth `DO_NOW` decision;
- public dogfood content is sanitized and non-canonical;
- all four decision states remain closed and exact.

- [ ] **Step 7: Commit any final test-only or minimal corrective changes, then record fresh verification evidence**

If Step 6 required no changes, do not create an empty commit. If a minimal correction was necessary:

```bash
git add <only-the-files-corrected-in-step-6>
git commit -m "fix: close v0.9 verification gap"
```

Then rerun:

```bash
pytest -q
```

Expected: zero failures on the final HEAD.

---

## Execution Notes

- Implement tasks strictly in order because storage depends on the domain contract, renderers depend on the contract, and the CLI depends on all three.
- Use an isolated git worktree at execution time via `superpowers:using-git-worktrees` before touching implementation code.
- Use TDD for every task: RED test, minimal GREEN implementation, focused test pass, commit.
- Do not fold Task 1–4 into one large commit; the commit boundaries are deliberate review gates.
- If implementation reveals that linear supersession cannot be enforced without changing an approved spec invariant, stop and return to design review instead of silently weakening the contract.
- If a historical test fails because v0.9 changes behavior outside the additive `decision` namespace or root-help text, treat that as a regression in v0.9 rather than editing the historical test to fit the new behavior.
