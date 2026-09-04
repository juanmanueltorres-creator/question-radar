import json
import subprocess

import pytest

from question_radar import cli_v09 as cli
from question_radar.lineage import QuestionNode
from question_radar.lineage_storage import QuestionLineageStore


def seed_node(db, node_id="q-a", question="Should this consume attention now?"):
    QuestionLineageStore(db).insert_node(
        QuestionNode.from_dict(
            {
                "id": node_id,
                "question": question,
                "source": "manual",
                "source_ref": None,
                "created_at": "2026-09-04T12:00:00-03:00",
            }
        )
    )


def record_args(question_id="q-a", state="DO_NOW"):
    args = [
        "decision",
        "record",
        "--question-id",
        question_id,
        "--decision",
        state,
        "--rationale",
        "Bounded current investigation.",
        "--goal-alignment",
        "true",
        "--external-signal",
        "true",
        "--testable-now",
        "true",
        "--leverage",
        "true",
        "--cost",
        "low",
        "--confidence",
        "medium",
    ]
    if state in {"DO_NOW", "RESEARCH"}:
        args += ["--next-test", "Run one bounded test."]
    if state == "PARKED":
        args += ["--resume-when", "A relevant condition changes."]
    return args


def test_record_parser_accepts_operator_and_audit_fields():
    args = cli.build_decision_parser().parse_args(
        [
            "decision",
            "record",
            "--question-id",
            "q-a",
            "--decision",
            "PARKED",
            "--rationale",
            "Not needed now.",
            "--goal-alignment",
            "false",
            "--external-signal",
            "true",
            "--testable-now",
            "false",
            "--leverage",
            "true",
            "--cost",
            "medium",
            "--confidence",
            "medium",
            "--resume-when",
            "A workload exists.",
            "--id",
            "dec-explicit",
            "--created-at",
            "2026-09-04T15:00:00-03:00",
        ]
    )
    assert args.id == "dec-explicit"
    assert args.goal_alignment is False
    assert args.external_signal is True


def test_boolean_parser_rejects_non_explicit_values():
    parser = cli.build_decision_parser()
    args = record_args()
    index = args.index("--goal-alignment") + 1
    args[index] = "yes"
    with pytest.raises(SystemExit):
        parser.parse_args(args)


def test_record_show_history_active_round_trip(tmp_path, capsys):
    db = tmp_path / "questions.sqlite3"
    seed_node(db)
    first = record_args() + [
        "--id",
        "dec-1",
        "--created-at",
        "2026-09-04T12:05:00-03:00",
    ]
    assert cli.main(["--db", str(db), *first]) == 0
    assert capsys.readouterr().out.strip() == "recorded dec-1"

    assert (
        cli.main(
            ["--db", str(db), "decision", "show", "q-a", "--format", "json"]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["current_decision"]["id"] == "dec-1"

    second = record_args(state="PARKED") + [
        "--supersedes",
        "dec-1",
        "--id",
        "dec-2",
        "--created-at",
        "2026-09-04T12:10:00-03:00",
    ]
    assert cli.main(["--db", str(db), *second]) == 0
    capsys.readouterr()

    assert (
        cli.main(
            ["--db", str(db), "decision", "history", "q-a", "--format", "json"]
        )
        == 0
    )
    history = json.loads(capsys.readouterr().out)
    assert [item["id"] for item in history["history"]] == ["dec-1", "dec-2"]

    assert cli.main(["--db", str(db), "decision", "active", "--format", "json"]) == 0
    active = json.loads(capsys.readouterr().out)
    assert active["counts"]["PARKED"] == 1
    assert active["active"] == []


def test_generated_metadata_is_injectable(tmp_path, capsys, monkeypatch):
    db = tmp_path / "questions.sqlite3"
    seed_node(db)
    monkeypatch.setattr(cli, "_new_decision_id", lambda: "dec-generated")
    monkeypatch.setattr(cli, "_now_iso", lambda: "2026-09-04T18:00:00+00:00")
    assert cli.main(["--db", str(db), *record_args()]) == 0
    capsys.readouterr()
    assert (
        cli.main(
            ["--db", str(db), "decision", "show", "q-a", "--format", "json"]
        )
        == 0
    )
    item = json.loads(capsys.readouterr().out)["current_decision"]
    assert item["id"] == "dec-generated"
    assert item["created_at"] == "2026-09-04T18:00:00+00:00"


def test_missing_lineage_prerequisite_fails_closed(tmp_path, capsys):
    db = tmp_path / "empty.sqlite3"
    db.touch()
    assert cli.main(["--db", str(db), "decision", "active"]) == 2
    assert "question_nodes_v04 prerequisite" in capsys.readouterr().err


def test_show_without_decision_is_explicit(tmp_path, capsys):
    db = tmp_path / "questions.sqlite3"
    seed_node(db)
    assert cli.main(["--db", str(db), "decision", "show", "q-a"]) == 2
    assert "no investigation decision recorded for: q-a" in capsys.readouterr().err


def test_installed_cli_exposes_decision_and_preserves_existing_namespaces():
    for args, expected in (
        (["--help"], "decision"),
        (["decision", "--help"], "record"),
        (["decision", "record", "--help"], "--question-id"),
        (["retrieval", "--help"], "compare"),
        (["benchmark", "--help"], "evaluate"),
        (["lineage", "--help"], "node"),
    ):
        completed = subprocess.run(
            ["question-radar", *args], capture_output=True, text=True, check=False
        )
        assert completed.returncode == 0, completed.stderr
        assert expected in completed.stdout
