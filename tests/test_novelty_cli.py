import json
import sqlite3

from question_radar import cli
from question_radar.lineage import QuestionNode
from question_radar.lineage_storage import QuestionLineageStore


def _seed_db(db_path):
    store = QuestionLineageStore(db_path)
    store.insert_node(
        QuestionNode(
            id="memory-master",
            question="¿Cómo usamos memoria y trazabilidad?",
            source="corpus",
            source_ref=None,
            created_at="2026-09-01T12:00:00-03:00",
        )
    )


def test_novelty_compare_markdown_is_read_only(tmp_path, capsys):
    db_path = tmp_path / "questions.sqlite3"
    _seed_db(db_path)
    before = db_path.read_bytes()

    exit_code = cli.main(
        [
            "--db",
            str(db_path),
            "novelty",
            "compare",
            "¿Qué debería recordar una organización?",
            "--limit",
            "5",
            "--format",
            "markdown",
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "# Question Radar Novelty Pack" in output
    assert "memory-master" in output
    assert "No lineage relation or master promotion was created." in output
    assert db_path.read_bytes() == before


def test_novelty_compare_does_not_create_missing_database(tmp_path, capsys):
    db_path = tmp_path / "missing.sqlite3"

    exit_code = cli.main(
        [
            "--db",
            str(db_path),
            "novelty",
            "compare",
            "¿Qué debería recordar una organización?",
        ]
    )

    assert exit_code == 2
    assert not db_path.exists()
    assert "database does not exist" in capsys.readouterr().err


def test_novelty_compare_does_not_migrate_legacy_database(tmp_path, capsys):
    db_path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE legacy_questions (id TEXT PRIMARY KEY)")
    before = db_path.read_bytes()

    exit_code = cli.main(
        [
            "--db",
            str(db_path),
            "novelty",
            "compare",
            "¿Qué debería recordar una organización?",
        ]
    )

    assert exit_code == 2
    assert db_path.read_bytes() == before
    assert "v0.4 lineage tables not found" in capsys.readouterr().err


def test_novelty_compare_json_is_deterministic(tmp_path, capsys):
    db_path = tmp_path / "questions.sqlite3"
    _seed_db(db_path)

    args = [
        "--db",
        str(db_path),
        "novelty",
        "compare",
        "¿Qué debería recordar una organización?",
        "--format",
        "json",
    ]
    assert cli.main(args) == 0
    first = capsys.readouterr().out
    assert cli.main(args) == 0
    second = capsys.readouterr().out

    assert first == second
    payload = json.loads(first)
    assert payload["novelty_version"] == "v0.5"
    assert payload["review_required"] is True
    assert first.endswith("\n")


def test_novelty_batch_is_read_only(tmp_path, capsys):
    db_path = tmp_path / "questions.sqlite3"
    _seed_db(db_path)
    candidates = tmp_path / "candidates.jsonl"
    candidates.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "q8",
                        "question": "¿Cómo distinguimos conocimiento válido de conocimiento obsoleto?",
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "id": "q9",
                        "question": "¿Puede una documentación conservar procedimientos obsoletos?",
                    },
                    ensure_ascii=False,
                ),
            ]
        ),
        encoding="utf-8",
    )
    before = db_path.read_bytes()

    exit_code = cli.main(
        [
            "--db",
            str(db_path),
            "novelty",
            "batch",
            str(candidates),
            "--format",
            "json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["novelty_version"] == "v0.5"
    assert payload["review_required"] is True
    assert db_path.read_bytes() == before
