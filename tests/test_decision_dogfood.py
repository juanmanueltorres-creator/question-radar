import json

from question_radar import cli_v09 as cli
from question_radar.lineage import QuestionNode
from question_radar.lineage_storage import QuestionLineageStore


def _seed(db, node_id, question, created_at):
    QuestionLineageStore(db).insert_node(
        QuestionNode.from_dict(
            {
                "id": node_id,
                "question": question,
                "source": "manual",
                "source_ref": "sanitized-dogfood",
                "created_at": created_at,
            }
        )
    )


def _record(db, *args):
    return cli.main(["--db", str(db), "decision", "record", *args])


def test_sanitized_three_case_dogfood(tmp_path, capsys):
    db = tmp_path / "dogfood.sqlite3"
    _seed(
        db,
        "dog-spqr",
        "When does horizontal PostgreSQL scaling become justified by a real workload?",
        "2026-09-04T18:00:00+00:00",
    )
    _seed(
        db,
        "dog-lithium",
        "Which lithium GeoAI problem is narrow enough for a bounded evidence-gathering test?",
        "2026-09-04T18:01:00+00:00",
    )
    _seed(
        db,
        "dog-feedback",
        "Which existing product demonstration can produce external feedback this week?",
        "2026-09-04T18:02:00+00:00",
    )

    assert _record(
        db,
        "--question-id",
        "dog-spqr",
        "--decision",
        "PARKED",
        "--rationale",
        "High learning value, no current production workload requires it.",
        "--goal-alignment",
        "false",
        "--external-signal",
        "true",
        "--testable-now",
        "false",
        "--leverage",
        "true",
        "--cost",
        "high",
        "--confidence",
        "medium",
        "--resume-when",
        "A real PostgreSQL workload requires horizontal scaling.",
        "--id",
        "dec-dog-spqr",
        "--created-at",
        "2026-09-04T18:10:00+00:00",
    ) == 0
    capsys.readouterr()

    assert _record(
        db,
        "--question-id",
        "dog-lithium",
        "--decision",
        "RESEARCH",
        "--rationale",
        "There is a domain-relevant problem space, but the specific problem still needs evidence.",
        "--goal-alignment",
        "true",
        "--external-signal",
        "true",
        "--testable-now",
        "true",
        "--leverage",
        "true",
        "--cost",
        "medium",
        "--confidence",
        "medium",
        "--next-test",
        "Collect ten repeated operational problems from public lithium project evidence and classify which are observable with GeoAI.",
        "--id",
        "dec-dog-lithium",
        "--created-at",
        "2026-09-04T18:11:00+00:00",
    ) == 0
    capsys.readouterr()

    assert _record(
        db,
        "--question-id",
        "dog-feedback",
        "--decision",
        "DO_NOW",
        "--rationale",
        "This can produce external evidence from work that already exists.",
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
        "high",
        "--next-test",
        "Publish one existing product demonstration and record one external response or explicit no-response outcome.",
        "--id",
        "dec-dog-feedback",
        "--created-at",
        "2026-09-04T18:12:00+00:00",
    ) == 0
    capsys.readouterr()

    assert cli.main(["--db", str(db), "decision", "active", "--format", "json"]) == 0
    active_text = capsys.readouterr().out
    active = json.loads(active_text)
    assert active["counts"] == {
        "DO_NOW": 1,
        "RESEARCH": 1,
        "PARKED": 1,
        "KILLED": 0,
    }
    assert [item["decision"]["decision"] for item in active["active"]] == [
        "RESEARCH",
        "DO_NOW",
    ]
    assert active["wip_warning"] is None

    assert cli.main(["--db", str(db), "decision", "show", "dog-spqr"]) == 0
    parked_text = capsys.readouterr().out
    assert "Current decision: PARKED" in parked_text
    assert "No action is currently requested." in parked_text

    assert (
        cli.main(
            [
                "--db",
                str(db),
                "decision",
                "history",
                "dog-lithium",
                "--format",
                "json",
            ]
        )
        == 0
    )
    history_text = capsys.readouterr().out
    history = json.loads(history_text)
    assert history["automatic_decision"] is False
    assert history["history"][0]["decision"] == "RESEARCH"

    assert "priority_score" not in active_text + parked_text + history_text
