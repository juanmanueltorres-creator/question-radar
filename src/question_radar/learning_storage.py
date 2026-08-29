from pathlib import Path
import sqlite3

from question_radar.learning import LearningObservation


_OBSERVATIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS learning_observations_v03 (
    id TEXT PRIMARY KEY,
    concept TEXT NOT NULL,
    gap_type TEXT NOT NULL,
    state TEXT NOT NULL,
    confidence TEXT NOT NULL,
    interpretation TEXT NOT NULL,
    suggested_next_step TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

_EVIDENCE_SCHEMA = """
CREATE TABLE IF NOT EXISTS learning_observation_evidence_v03 (
    observation_id TEXT NOT NULL,
    position INTEGER NOT NULL CHECK (position >= 0),
    evidence_question_id TEXT NOT NULL,
    PRIMARY KEY (observation_id, position),
    UNIQUE (observation_id, evidence_question_id),
    FOREIGN KEY (observation_id)
        REFERENCES learning_observations_v03(id)
        ON DELETE CASCADE
)
"""

_OBSERVATION_COLUMNS = (
    "id",
    "concept",
    "gap_type",
    "state",
    "confidence",
    "interpretation",
    "suggested_next_step",
    "created_at",
    "updated_at",
)


class LearningObservationStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self.db_path)
            connection.execute("PRAGMA foreign_keys = ON")
            connection.row_factory = sqlite3.Row
            return connection
        except (OSError, sqlite3.Error) as exc:
            raise RuntimeError(
                f"cannot open SQLite database at {self.db_path}: {exc}"
            ) from exc

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(_OBSERVATIONS_SCHEMA)
            connection.execute(_EVIDENCE_SCHEMA)

    def insert(self, observation: LearningObservation) -> None:
        self.insert_many([observation])

    def insert_many(self, observations: list[LearningObservation]) -> None:
        self.initialize()
        columns = ", ".join(_OBSERVATION_COLUMNS)
        placeholders = ", ".join("?" for _ in _OBSERVATION_COLUMNS)
        observation_sql = (
            f"INSERT INTO learning_observations_v03 ({columns}) "
            f"VALUES ({placeholders})"
        )
        evidence_sql = (
            "INSERT INTO learning_observation_evidence_v03 "
            "(observation_id, position, evidence_question_id) VALUES (?, ?, ?)"
        )

        try:
            with self._connect() as connection:
                for observation in observations:
                    payload = observation.to_dict()
                    connection.execute(
                        observation_sql,
                        tuple(payload[column] for column in _OBSERVATION_COLUMNS),
                    )
                    connection.executemany(
                        evidence_sql,
                        [
                            (observation.id, position, evidence_id)
                            for position, evidence_id in enumerate(
                                observation.evidence_question_ids
                            )
                        ],
                    )
        except sqlite3.IntegrityError as exc:
            raise ValueError(
                "a learning observation id already exists or violates the schema"
            ) from exc

    def _reconstruct(
        self,
        connection: sqlite3.Connection,
        row: sqlite3.Row,
    ) -> LearningObservation:
        evidence_rows = connection.execute(
            "SELECT evidence_question_id "
            "FROM learning_observation_evidence_v03 "
            "WHERE observation_id = ? ORDER BY position ASC",
            (row["id"],),
        ).fetchall()
        payload = dict(row)
        payload["evidence_question_ids"] = [
            evidence_row["evidence_question_id"] for evidence_row in evidence_rows
        ]
        return LearningObservation.from_dict(payload)

    def list_all(self) -> list[LearningObservation]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM learning_observations_v03 "
                "ORDER BY created_at ASC, id ASC"
            ).fetchall()
            return [self._reconstruct(connection, row) for row in rows]

    def get(self, observation_id: str) -> LearningObservation | None:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM learning_observations_v03 WHERE id = ?",
                (observation_id,),
            ).fetchone()
            if row is None:
                return None
            return self._reconstruct(connection, row)
