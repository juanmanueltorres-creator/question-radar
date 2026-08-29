from pathlib import Path
import sqlite3

from question_radar.models import QuestionEvaluation

_COLUMNS = (
    "id",
    "question",
    "clarity",
    "depth",
    "investigability",
    "assumption_challenge",
    "connections",
    "score",
    "strengths",
    "gap",
    "next_question",
    "topic",
    "evaluator",
    "rubric_version",
    "created_at",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS evaluations (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    clarity INTEGER NOT NULL CHECK (clarity BETWEEN 0 AND 5),
    depth INTEGER NOT NULL CHECK (depth BETWEEN 0 AND 5),
    investigability INTEGER NOT NULL CHECK (investigability BETWEEN 0 AND 5),
    assumption_challenge INTEGER NOT NULL CHECK (assumption_challenge BETWEEN 0 AND 5),
    connections INTEGER NOT NULL CHECK (connections BETWEEN 0 AND 5),
    score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
    strengths TEXT NOT NULL,
    gap TEXT NOT NULL,
    next_question TEXT NOT NULL,
    topic TEXT,
    evaluator TEXT NOT NULL,
    rubric_version TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""


class QuestionStore:
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

    def insert(self, evaluation: QuestionEvaluation) -> None:
        self.insert_many([evaluation])

    def insert_many(self, evaluations: list[QuestionEvaluation]) -> None:
        self.initialize()
        placeholders = ", ".join("?" for _ in _COLUMNS)
        columns = ", ".join(_COLUMNS)
        sql = f"INSERT INTO evaluations ({columns}) VALUES ({placeholders})"
        rows = [
            tuple(evaluation.to_dict()[column] for column in _COLUMNS)
            for evaluation in evaluations
        ]
        try:
            with self._connect() as connection:
                connection.executemany(sql, rows)
        except sqlite3.IntegrityError as exc:
            raise ValueError("an evaluation id already exists or violates the schema") from exc

    def list_all(self) -> list[QuestionEvaluation]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM evaluations ORDER BY created_at ASC, id ASC"
            ).fetchall()
        return [QuestionEvaluation.from_dict(dict(row)) for row in rows]

    def top(self, limit: int = 10) -> list[QuestionEvaluation]:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM evaluations ORDER BY score DESC, created_at ASC, id ASC LIMIT ?",
                (limit,),
            ).fetchall()
        return [QuestionEvaluation.from_dict(dict(row)) for row in rows]
