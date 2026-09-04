from pathlib import Path
import sqlite3

from question_radar.decisions import InvestigationDecision, decision_timestamp_sort_key
from question_radar.lineage import QuestionNode

_REQUIRED_V04_COLUMNS = {"id", "question", "source", "source_ref", "created_at"}
_BOOLEAN_COLUMNS = ("goal_alignment", "external_signal", "testable_now", "leverage")
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


def _decision_from_row(row: sqlite3.Row) -> InvestigationDecision:
    payload = dict(row)
    for column in _BOOLEAN_COLUMNS:
        payload[column] = bool(payload[column])
    return InvestigationDecision.from_dict(payload)


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
            raise RuntimeError(
                f"cannot open SQLite database at {self.db_path}: {exc}"
            ) from exc

    def _verify_v04_prerequisite(self, connection: sqlite3.Connection) -> None:
        try:
            row = connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='question_nodes_v04'"
            ).fetchone()
            if row is None:
                raise RuntimeError("question_nodes_v04 prerequisite is missing")
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(question_nodes_v04)")
            }
        except sqlite3.Error as exc:
            raise RuntimeError(
                f"cannot inspect question_nodes_v04 prerequisite: {exc}"
            ) from exc

        missing = sorted(_REQUIRED_V04_COLUMNS - columns)
        if missing:
            raise RuntimeError(
                "question_nodes_v04 prerequisite is structurally unsupported; "
                "missing columns: " + ", ".join(missing)
            )

    def initialize(self) -> None:
        try:
            with self._connect_existing() as connection:
                self._verify_v04_prerequisite(connection)
                connection.execute(_SCHEMA)
        except sqlite3.Error as exc:
            raise RuntimeError(
                f"cannot initialize investigation_decisions_v09 at {self.db_path}: {exc}"
            ) from exc

    def _get_in_connection(
        self, connection: sqlite3.Connection, decision_id: str
    ) -> InvestigationDecision | None:
        row = connection.execute(
            "SELECT * FROM investigation_decisions_v09 WHERE id = ?",
            (decision_id,),
        ).fetchone()
        return _decision_from_row(row) if row is not None else None

    def _history_in_connection(
        self, connection: sqlite3.Connection, question_id: str
    ) -> list[InvestigationDecision]:
        rows = connection.execute(
            "SELECT * FROM investigation_decisions_v09 WHERE question_id = ?",
            (question_id,),
        ).fetchall()
        return [_decision_from_row(row) for row in rows]

    def _validate_history_in_connection(
        self, connection: sqlite3.Connection, question_id: str
    ) -> InvestigationDecision | None:
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

        referenced_set = set(referenced)
        leaves = [item for item in history if item.id not in referenced_set]
        if len(leaves) != 1:
            raise RuntimeError(f"ambiguous decision history for {question_id}")

        seen: set[str] = set()
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
            if (
                connection.execute(
                    "SELECT 1 FROM question_nodes_v04 WHERE id = ?",
                    (item.question_id,),
                ).fetchone()
                is None
            ):
                raise ValueError(f"question node not found: {item.question_id}")

            current = self._validate_history_in_connection(connection, item.question_id)
            if current is None:
                if item.supersedes_decision_id is not None:
                    raise ValueError("first decision must not supersede another decision")
            else:
                if item.supersedes_decision_id is None:
                    raise ValueError(
                        f"revision must supersede current decision: {current.id}"
                    )
                prior = self._get_in_connection(
                    connection, item.supersedes_decision_id
                )
                if prior is None:
                    raise ValueError(
                        f"superseded decision not found: {item.supersedes_decision_id}"
                    )
                if prior.question_id != item.question_id:
                    raise ValueError("superseded decision belongs to another question")
                if prior.id != current.id:
                    raise ValueError(
                        f"revision must supersede current decision: {current.id}"
                    )

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
                raise ValueError(
                    "investigation decision violates the v0.9 schema"
                ) from exc

            self._validate_history_in_connection(connection, item.question_id)

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
            ids = [
                row["question_id"]
                for row in connection.execute(
                    "SELECT DISTINCT question_id FROM investigation_decisions_v09 "
                    "ORDER BY question_id"
                )
            ]
            current = [
                self._validate_history_in_connection(connection, question_id)
                for question_id in ids
            ]
        return sorted(
            [item for item in current if item is not None],
            key=lambda item: (decision_timestamp_sort_key(item.created_at), item.id),
        )
