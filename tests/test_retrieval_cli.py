import json
from pathlib import Path
import sqlite3
import subprocess

from question_radar import cli_v06 as cli
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


def test_retrieval_markdown_has_explicit_review_boundary_and_coverage():
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

    assert "# Unified Candidate Retrieval v0.7" in rendered
    assert "## Candidate" in rendered
    assert "## Retrieved Prior Questions" in rendered
    assert "matched_token_count:" in rendered
    assert "query_token_count:" in rendered
    assert "query_coverage:" in rendered
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
    assert payload["retrieval_version"] == "v0.7"
    assert payload["review_required"] is True
    assert payload["abstained"] is False
    assert payload["abstention_reason"] is None
    assert payload["results"][0]["entry"]["source_version"] == "v0.2"
    assert payload["results"][0]["token_contributions"]
    assert payload["results"][0]["matched_token_count"] >= 1
    assert payload["results"][0]["query_token_count"] >= 1
    assert 0.0 < payload["results"][0]["query_coverage"] <= 1.0


def test_abstention_is_explicit_in_json_and_markdown():
    corpus = (
        CorpusEntry("a", "costo actuar", "v0.2", "profile", None),
        CorpusEntry("b", "memoria trazabilidad", "v0.2", "profile", None),
    )
    pack = retrieve_candidates("xilofono marmol orbital", corpus)

    payload = json.loads(render_retrieval_json(pack))
    markdown = render_retrieval_markdown(pack)

    assert payload["abstained"] is True
    assert payload["abstention_reason"] == "no_lexical_evidence"
    assert payload["results"] == []
    assert "ABSTAINED" in markdown
    assert "no_lexical_evidence" in markdown


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
    assert payload["retrieval_version"] == "v0.7"
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


def test_installed_cli_exposes_retrieval_help_commands():
    for args in (
        ["retrieval", "--help"],
        ["retrieval", "compare", "--help"],
    ):
        completed = subprocess.run(
            ["question-radar", *args],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert "usage:" in completed.stdout.lower()


def test_root_help_mentions_retrieval_namespace():
    completed = subprocess.run(
        ["question-radar", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "retrieval" in completed.stdout
