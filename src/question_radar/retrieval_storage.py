from __future__ import annotations

from pathlib import Path
import sqlite3

from question_radar.retrieval import CorpusEntry


_PROFILE_TABLE = "question_profiles_v02"
_LINEAGE_TABLE = "question_nodes_v04"


def load_retrieval_corpus(db_path: str | Path) -> tuple[CorpusEntry, ...]:
    """Load v0.2 and/or v0.4 question text without mutating SQLite."""

    path = Path(db_path)
    if not path.is_file():
        raise ValueError(f"database does not exist: {path}")

    uri = path.resolve().as_uri() + "?mode=ro"
    entries: list[CorpusEntry] = []

    try:
        with sqlite3.connect(uri, uri=True) as connection:
            connection.row_factory = sqlite3.Row
            table_rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name IN (?, ?)",
                (_PROFILE_TABLE, _LINEAGE_TABLE),
            ).fetchall()
            tables = {row["name"] for row in table_rows}

            if not tables:
                raise ValueError("no supported retrieval corpus tables found")

            if _PROFILE_TABLE in tables:
                rows = connection.execute(
                    f"SELECT id, question FROM {_PROFILE_TABLE}"
                ).fetchall()
                entries.extend(
                    CorpusEntry(
                        id=row["id"],
                        question=row["question"],
                        source_version="v0.2",
                        source_kind="profile",
                        provenance=None,
                    )
                    for row in rows
                )

            if _LINEAGE_TABLE in tables:
                rows = connection.execute(
                    f"SELECT id, question, source_ref FROM {_LINEAGE_TABLE}"
                ).fetchall()
                entries.extend(
                    CorpusEntry(
                        id=row["id"],
                        question=row["question"],
                        source_version="v0.4",
                        source_kind="lineage_node",
                        provenance=row["source_ref"],
                    )
                    for row in rows
                )
    except ValueError:
        raise
    except sqlite3.Error as exc:
        raise RuntimeError(f"cannot read SQLite database at {path}: {exc}") from exc

    entries.sort(key=lambda entry: (entry.source_version, entry.id))
    return tuple(entries)
