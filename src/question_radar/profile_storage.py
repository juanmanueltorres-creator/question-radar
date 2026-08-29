from pathlib import Path
import sqlite3

from question_radar.profiles import QUESTION_TYPES, QuestionProfile

_COLUMNS = (
    "id",
    "question",
    "question_type",
    "readiness",
    "clarity",
    "boundedness",
    "investigability",
    "epistemic_openness",
    "purpose_fit",
    "formulation_score",
    "depth",
    "connections",
    "generativity",
    "strengths",
    "gap",
    "assumptions",
    "evidence_required",
    "next_question",
    "topic",
    "evaluator",
    "rubric_version",
    "created_at",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS question_profiles_v02 (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    question_type TEXT NOT NULL,
    readiness TEXT NOT NULL,
    clarity INTEGER NOT NULL CHECK (clarity BETWEEN 0 AND 5),
    boundedness INTEGER NOT NULL CHECK (boundedness BETWEEN 0 AND 5),
    investigability INTEGER NOT NULL CHECK (investigability BETWEEN 0 AND 5),
    epistemic_openness INTEGER NOT NULL CHECK (epistemic_openness BETWEEN 0 AND 5),
    purpose_fit INTEGER NOT NULL CHECK (purpose_fit BETWEEN 0 AND 5),
    formulation_score INTEGER NOT NULL CHECK (formulation_score BETWEEN 0 AND 100),
    depth INTEGER NOT NULL CHECK (depth BETWEEN 0 AND 5),
    connections INTEGER NOT NULL CHECK (connections BETWEEN 0 AND 5),
    generativity INTEGER NOT NULL CHECK (generativity BETWEEN 0 AND 5),
    strengths TEXT NOT NULL,
    gap TEXT NOT NULL,
    assumptions TEXT NOT NULL,
    evidence_required TEXT NOT NULL,
    next_question TEXT NOT NULL,
    topic TEXT,
    evaluator TEXT NOT NULL,
    rubric_version TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""


class QuestionProfileStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self.db_path)
            connection.row_factory = sqlite3.Row
            return connection
        except (OSError, sqlite3.Error) as exc:
            raise RuntimeError(
                f"cannot open SQLite database at {self.db_path}: {exc}"
            ) from exc

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(_SCHEMA)

    def insert(self, profile: QuestionProfile) -> None:
        self.insert_many([profile])

    def insert_many(self, profiles: list[QuestionProfile]) -> None:
        self.initialize()
        placeholders = ", ".join("?" for _ in _COLUMNS)
        columns = ", ".join(_COLUMNS)
        sql = (
            f"INSERT INTO question_profiles_v02 ({columns}) "
            f"VALUES ({placeholders})"
        )
        rows = [
            tuple(profile.to_dict()[column] for column in _COLUMNS)
            for profile in profiles
        ]
        try:
            with self._connect() as connection:
                connection.executemany(sql, rows)
        except sqlite3.IntegrityError as exc:
            raise ValueError(
                "a profile id already exists or violates the schema"
            ) from exc

    def list_all(self) -> list[QuestionProfile]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM question_profiles_v02 "
                "ORDER BY created_at ASC, id ASC"
            ).fetchall()
        return [QuestionProfile.from_dict(dict(row)) for row in rows]

    def top(self, question_type: str, limit: int = 10) -> list[QuestionProfile]:
        if question_type not in QUESTION_TYPES:
            raise ValueError(
                "question_type must be one of: " + ", ".join(QUESTION_TYPES)
            )
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM question_profiles_v02 "
                "WHERE question_type = ? "
                "ORDER BY formulation_score DESC, created_at ASC, id ASC LIMIT ?",
                (question_type, limit),
            ).fetchall()
        return [QuestionProfile.from_dict(dict(row)) for row in rows]
