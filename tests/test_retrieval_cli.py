import json
from pathlib import Path
import sqlite3

from question_radar import cli
from question_radar.retrieval import CorpusEntry, retrieve_candidates
from question_radar.retrieval_export import (
    render_retrieval_json,
    render_retrieval_markdown,
)


def _mixed_db(path: Path) -> None:
    with sqlite3.connect(path) as connection:
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
            ("qv2-cal-013", "¿Cuál es el costo de actuar y de no actuar?"),
        )
        connection.execute(
            "INSERT INTO question_nodes_v04 VALUES (?, ?, ?, ?, ?)",
            (
                "qv4-1",
                "¿Cómo usamos memoria y trazabilidad?",
                "corpus",
                "corpus/source.jsonl",
                "2026-09-01T00:00:00-03:00",
            ),
        )


def test_retrieval_markdown_has_explicit_review_boundary():
    corpus = (
        CorpusEntry(
            "q1",
            "¿Cuál es el costo de actuar y de no actuar?",
            "v0.2",
            "profile",
            None,
        ),
    )
    pack = retrieve_candidates("¿Cuál es el costo de no actuar?", corpus)

    rendered = render_retrieval_markdown(pack)

    assert "# Unified Candidate Retrieval v0.6" in rendered
    assert "## Candidate" in rendered
    assert "## Retrieved Prior Questions" in rendered
    assert "## Review Boundary" in rendered
    assert "No semantic relation, lineage edge, or master promotion was created." in rendered
    assert rendered.endswith("\n")


def test_retrieval_json_is_deterministic_and_inspectable():
    corpus = (
        CorpusEntry(
            "q1",
            "¿Cuál es el costo de actuar y de no actuar?",
            "v0.2",
            "profile",
            None,
        ),
    )
    pack = retrieve_candidates("¿Cuál es el costo de no actuar?", corpus)

    first = render_retrieval_json(pack)
    second = render_retrieval_json(pack)
    payload = json.loads(first)

    assert first == second
    assert first.endswith("\n")
    assert payload["retrieval_version"] == "v0.6"
    assert payload["review_required"] is True
    assert payload["results"][0]["entry"]["source_version"] == "v0.2"
    assert payload["results"][0]["token_contributions"]


def test_cli_retrieval_compare_is_read_only(tmp_path: Path, capsys):
    db = tmp_path / "questions.sqlite3"
    _mixed_db(db)
    before = db.read_bytes()

    exit_code = cli.main(
        [
            "--db",
            str(db),
            "retrieval",
            "compare",
            "¿Qué pesa más: el costo de equivocarse o el costo de no actuar?",
            "--limit",
            "5",
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["retrieval_version"] == "v0.6"
    assert payload["results"][0]["entry"]["id"] == "qv2-cal-013"
    assert db.read_bytes() == before


def test_cli_retrieval_missing_database_fails_closed(tmp_path: Path, capsys):
    db = tmp_path / "missing.sqlite3"

    exit_code = cli.main(
        [
            "--db",
            str(db),
            "retrieval",
            "compare",
            "¿Qué sabemos?",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "database does not exist" in captured.err
    assert not db.exists()
