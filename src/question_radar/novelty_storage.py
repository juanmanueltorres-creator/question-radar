from pathlib import Path
import sqlite3

from question_radar.lineage import QuestionNode, QuestionRelation, timestamp_sort_key


_NODE_TABLE = "question_nodes_v04"
_RELATION_TABLE = "question_relations_v04"


def load_lineage_snapshot(
    db_path: str | Path,
) -> tuple[list[QuestionNode], list[QuestionRelation]]:
    """Read v0.4 lineage through a SQLite read-only connection.

    Unlike QuestionLineageStore read methods, this loader must never initialize
    a database or add missing lineage tables. v0.5 analysis fails closed when
    its source corpus does not already exist.
    """

    path = Path(db_path)
    if not path.is_file():
        raise ValueError(f"database does not exist: {path}")

    uri = path.resolve().as_uri() + "?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as connection:
            connection.row_factory = sqlite3.Row
            table_rows = connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name IN (?, ?)",
                (_NODE_TABLE, _RELATION_TABLE),
            ).fetchall()
            tables = {row["name"] for row in table_rows}
            if tables != {_NODE_TABLE, _RELATION_TABLE}:
                raise ValueError("v0.4 lineage tables not found")

            node_rows = connection.execute(
                f"SELECT id, question, source, source_ref, created_at FROM {_NODE_TABLE}"
            ).fetchall()
            relation_rows = connection.execute(
                "SELECT id, source_question_id, target_question_id, "
                f"relation_type, created_at FROM {_RELATION_TABLE}"
            ).fetchall()
    except ValueError:
        raise
    except sqlite3.Error as exc:
        raise RuntimeError(f"cannot read SQLite database at {path}: {exc}") from exc

    nodes = [QuestionNode.from_dict(dict(row)) for row in node_rows]
    relations = [QuestionRelation.from_dict(dict(row)) for row in relation_rows]

    return (
        sorted(nodes, key=lambda node: (timestamp_sort_key(node.created_at), node.id)),
        sorted(
            relations,
            key=lambda relation: (
                timestamp_sort_key(relation.created_at),
                relation.id,
            ),
        ),
    )
