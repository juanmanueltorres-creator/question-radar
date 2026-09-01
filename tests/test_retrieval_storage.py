from pathlib import Path
import sqlite3

import pytest

from question_radar.retrieval import CorpusEntry
from question_radar.retrieval_storage import load_retrieval_corpus


def test_corpus_entry_rejects_unknown_source_version():
    with pytest.raises(ValueError, match="source_version"):
        CorpusEntry("q1", "¿Qué sabemos?", "v9", "profile", None)


def test_loader_reads_v02_only_database(tmp_path: Path):
    db = tmp_path / "q.sqlite3"
    with sqlite3.connect(db) as connection:
        connection.execute(
            "CREATE TABLE question_profiles_v02 (id TEXT PRIMARY KEY, question TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO question_profiles_v02 (id, question) VALUES (?, ?)",
            ("qv2", "¿Cuál es el costo de actuar y de no actuar?"),
        )

    entries = load_retrieval_corpus(db)

    assert [(e.id, e.source_version, e.source_kind) for e in entries] == [
        ("qv2", "v0.2", "profile")
    ]
    assert entries[0].provenance is None


def test_loader_reads_v04_only_database(tmp_path: Path):
    db = tmp_path / "q.sqlite3"
    with sqlite3.connect(db) as connection:
        connection.execute(
            "CREATE TABLE question_nodes_v04 ("
            "id TEXT PRIMARY KEY, question TEXT NOT NULL, source TEXT NOT NULL, "
            "source_ref TEXT, created_at TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO question_nodes_v04 VALUES (?, ?, ?, ?, ?)",
            (
                "qv4",
                "¿Cómo usamos memoria y trazabilidad?",
                "corpus",
                "corpus/source.jsonl",
                "2026-09-01T00:00:00-03:00",
            ),
        )

    entries = load_retrieval_corpus(db)

    assert [(e.id, e.source_version, e.source_kind) for e in entries] == [
        ("qv4", "v0.4", "lineage_node")
    ]
    assert entries[0].provenance == "corpus/source.jsonl"


def test_loader_reads_mixed_database_in_deterministic_order(tmp_path: Path):
    db = tmp_path / "q.sqlite3"
    with sqlite3.connect(db) as connection:
        connection.execute(
            "CREATE TABLE question_profiles_v02 (id TEXT PRIMARY KEY, question TEXT NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE question_nodes_v04 ("
            "id TEXT PRIMARY KEY, question TEXT NOT NULL, source TEXT NOT NULL, "
            "source_ref TEXT, created_at TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO question_profiles_v02 VALUES (?, ?)",
            ("z-v2", "¿Qué riesgo importa?"),
        )
        connection.execute(
            "INSERT INTO question_nodes_v04 VALUES (?, ?, ?, ?, ?)",
            (
                "a-v4",
                "¿Qué evidencia falta?",
                "corpus",
                None,
                "2026-09-01T00:00:00-03:00",
            ),
        )

    entries = load_retrieval_corpus(db)

    assert [entry.id for entry in entries] == ["z-v2", "a-v4"]


def test_loader_does_not_create_missing_database(tmp_path: Path):
    db = tmp_path / "missing.sqlite3"

    with pytest.raises(ValueError, match="database does not exist"):
        load_retrieval_corpus(db)

    assert not db.exists()


def test_loader_rejects_database_without_supported_tables(tmp_path: Path):
    db = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(db) as connection:
        connection.execute("CREATE TABLE evaluations (id TEXT PRIMARY KEY)")

    before = db.read_bytes()
    with pytest.raises(ValueError, match="no supported retrieval corpus tables found"):
        load_retrieval_corpus(db)
    assert db.read_bytes() == before


def test_loader_is_byte_for_byte_read_only(tmp_path: Path):
    db = tmp_path / "q.sqlite3"
    with sqlite3.connect(db) as connection:
        connection.execute(
            "CREATE TABLE question_profiles_v02 (id TEXT PRIMARY KEY, question TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO question_profiles_v02 VALUES (?, ?)",
            ("q1", "¿Qué evidencia falta?"),
        )

    before = db.read_bytes()
    load_retrieval_corpus(db)
    assert db.read_bytes() == before
