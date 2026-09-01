from pathlib import Path
import sqlite3

from question_radar.lineage import QuestionNode, QuestionRelation, timestamp_sort_key

_NODE_SCHEMA = """
CREATE TABLE IF NOT EXISTS question_nodes_v04 (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('manual','conversation','corpus','external')),
    source_ref TEXT,
    created_at TEXT NOT NULL
)
"""

_RELATION_SCHEMA = """
CREATE TABLE IF NOT EXISTS question_relations_v04 (
    id TEXT PRIMARY KEY,
    source_question_id TEXT NOT NULL,
    target_question_id TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK (
        relation_type IN (
            'refines','decomposes','generalizes','operationalizes',
            'challenges_assumption','contrasts','follows_from'
        )
    ),
    created_at TEXT NOT NULL,
    UNIQUE (source_question_id, target_question_id, relation_type),
    CHECK (source_question_id <> target_question_id),
    FOREIGN KEY (source_question_id) REFERENCES question_nodes_v04(id),
    FOREIGN KEY (target_question_id) REFERENCES question_nodes_v04(id)
)
"""

_NODE_COLUMNS = ("id", "question", "source", "source_ref", "created_at")
_RELATION_COLUMNS = (
    "id",
    "source_question_id",
    "target_question_id",
    "relation_type",
    "created_at",
)


class QuestionLineageStore:
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
        try:
            with self._connect() as connection:
                connection.execute(_NODE_SCHEMA)
                connection.execute(_RELATION_SCHEMA)
        except sqlite3.Error as exc:
            raise RuntimeError(
                f"cannot initialize SQLite database at {self.db_path}: {exc}"
            ) from exc

    def insert_node(self, node: QuestionNode) -> None:
        self.insert_bundle([node], [])

    def insert_relation(self, relation: QuestionRelation) -> None:
        self.insert_bundle([], [relation])

    def insert_bundle(
        self,
        nodes: list[QuestionNode],
        relations: list[QuestionRelation],
    ) -> None:
        node_ids = [node.id for node in nodes]
        relation_ids = [relation.id for relation in relations]
        triples = [
            (
                relation.source_question_id,
                relation.target_question_id,
                relation.relation_type,
            )
            for relation in relations
        ]

        duplicate_node = _first_duplicate(node_ids)
        if duplicate_node is not None:
            raise ValueError(f"duplicate node id in bundle: {duplicate_node}")
        duplicate_relation_id = _first_duplicate(relation_ids)
        if duplicate_relation_id is not None:
            raise ValueError(f"duplicate relation id in bundle: {duplicate_relation_id}")
        duplicate_triple = _first_duplicate(triples)
        if duplicate_triple is not None:
            source, target, relation_type = duplicate_triple
            raise ValueError(
                f"duplicate relation in bundle: {source} -> {target} [{relation_type}]"
            )

        self.initialize()
        try:
            with self._connect() as connection:
                existing_node_ids = {
                    row["id"]
                    for row in connection.execute(
                        "SELECT id FROM question_nodes_v04"
                    ).fetchall()
                }
                available_node_ids = existing_node_ids | set(node_ids)
                for relation in relations:
                    for endpoint in (
                        relation.source_question_id,
                        relation.target_question_id,
                    ):
                        if endpoint not in available_node_ids:
                            raise ValueError(f"question node not found: {endpoint}")

                if nodes:
                    connection.executemany(
                        "INSERT INTO question_nodes_v04 "
                        "(id, question, source, source_ref, created_at) "
                        "VALUES (?, ?, ?, ?, ?)",
                        [
                            tuple(node.to_dict()[column] for column in _NODE_COLUMNS)
                            for node in nodes
                        ],
                    )
                if relations:
                    connection.executemany(
                        "INSERT INTO question_relations_v04 "
                        "(id, source_question_id, target_question_id, relation_type, created_at) "
                        "VALUES (?, ?, ?, ?, ?)",
                        [
                            tuple(
                                relation.to_dict()[column]
                                for column in _RELATION_COLUMNS
                            )
                            for relation in relations
                        ],
                    )
        except sqlite3.IntegrityError as exc:
            message = str(exc)
            if "question_nodes_v04.id" in message:
                raise ValueError("node id already exists or violates the schema") from exc
            if "question_relations_v04.id" in message:
                raise ValueError("relation id already exists or violates the schema") from exc
            if (
                "question_relations_v04.source_question_id" in message
                and "question_relations_v04.target_question_id" in message
                and "question_relations_v04.relation_type" in message
            ):
                raise ValueError("duplicate relation or relation violates the schema") from exc
            raise ValueError("lineage record violates the schema") from exc

    def get_node(self, node_id: str) -> QuestionNode | None:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM question_nodes_v04 WHERE id = ?",
                (node_id,),
            ).fetchone()
        return QuestionNode.from_dict(dict(row)) if row is not None else None

    def list_nodes(self) -> list[QuestionNode]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM question_nodes_v04").fetchall()
        nodes = [QuestionNode.from_dict(dict(row)) for row in rows]
        return sorted(nodes, key=lambda node: (timestamp_sort_key(node.created_at), node.id))

    def get_relation(self, relation_id: str) -> QuestionRelation | None:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM question_relations_v04 WHERE id = ?",
                (relation_id,),
            ).fetchone()
        return QuestionRelation.from_dict(dict(row)) if row is not None else None

    def list_relations(self, question_id: str | None = None) -> list[QuestionRelation]:
        self.initialize()
        with self._connect() as connection:
            if question_id is None:
                rows = connection.execute(
                    "SELECT * FROM question_relations_v04"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM question_relations_v04 "
                    "WHERE source_question_id = ? OR target_question_id = ?",
                    (question_id, question_id),
                ).fetchall()
        relations = [QuestionRelation.from_dict(dict(row)) for row in rows]
        return sorted(
            relations,
            key=lambda relation: (
                timestamp_sort_key(relation.created_at),
                relation.id,
            ),
        )


def _first_duplicate(values):
    seen = set()
    for value in values:
        if value in seen:
            return value
        seen.add(value)
    return None
