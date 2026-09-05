from __future__ import annotations

import json

from question_radar import cli_v09 as cli
from question_radar.decision_storage import InvestigationDecisionStore
from question_radar.decisions import InvestigationDecision
from question_radar.handoffs import QuestionResearchHandoff
from question_radar.lineage import QuestionNode
from question_radar.lineage_storage import QuestionLineageStore


def _seed_node(db, *, node_id: str = "q-water") -> QuestionNode:
    node = QuestionNode.from_dict(
        {
            "id": node_id,
            "question": "¿Qué decisión hídrica recurrente vale investigar?",
            "source": "manual",
            "source_ref": None,
            "created_at": "2026-09-04T20:00:00-03:00",
        }
    )
    QuestionLineageStore(db).insert_node(node)
    return node


def _decision(
    *,
    state: str = "RESEARCH",
    decision_id: str = "dec-a",
    question_id: str = "q-water",
    supersedes: str | None = None,
    created_at: str = "2026-09-04T20:05:00-03:00",
) -> InvestigationDecision:
    return InvestigationDecision.from_dict(
        {
            "id": decision_id,
            "question_id": question_id,
            "decision": state,
            "rationale": "Hay una decisión concreta por investigar.",
            "goal_alignment": True,
            "external_signal": True,
            "testable_now": True,
            "leverage": True,
            "cost": "low",
            "confidence": "medium",
            "next_test": (
                "Identificar quién decide y qué evidencia usa hoy."
                if state in {"DO_NOW", "RESEARCH"}
                else None
            ),
            "resume_when": "Aparezca nueva evidencia." if state == "PARKED" else None,
            "kill_condition": None,
            "supersedes_decision_id": supersedes,
            "created_at": created_at,
        }
    )


def _seed_current(db, *, state: str = "RESEARCH") -> InvestigationDecision:
    _seed_node(db)
    decision = _decision(state=state)
    InvestigationDecisionStore(db).insert(decision)
    return decision


def _handoff_args(out, *, route: str = "TERRITORIAL_RESEARCH") -> list[str]:
    return [
        "decision",
        "handoff",
        "q-water",
        "--route",
        route,
        "--out",
        str(out),
        "--handoff-id",
        "qrh:test:001",
        "--created-at",
        "2026-09-04T20:30:00-03:00",
    ]


def test_research_current_decision_writes_valid_handoff(tmp_path, capsys) -> None:
    db = tmp_path / "questions.sqlite3"
    decision = _seed_current(db, state="RESEARCH")
    out = tmp_path / "exports" / "handoff.json"

    assert cli.main(["--db", str(db), *_handoff_args(out)]) == 0

    payload = json.loads(out.read_text(encoding="utf-8"))
    handoff = QuestionResearchHandoff.from_dict(payload)
    assert handoff.source.decision_id == decision.id
    assert handoff.routing.kind == "TERRITORIAL_RESEARCH"
    assert handoff.routing.destination == "andes-context-os"
    assert capsys.readouterr().err == ""


def test_do_now_current_decision_also_exports(tmp_path) -> None:
    db = tmp_path / "questions.sqlite3"
    _seed_current(db, state="DO_NOW")
    out = tmp_path / "handoff.json"

    assert cli.main(["--db", str(db), *_handoff_args(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["investigation"]["decision"] == "DO_NOW"


def test_parked_and_killed_fail_without_creating_output(tmp_path, capsys) -> None:
    for state in ("PARKED", "KILLED"):
        db = tmp_path / f"{state.lower()}.sqlite3"
        _seed_current(db, state=state)
        out = tmp_path / state.lower() / "handoff.json"

        assert cli.main(["--db", str(db), *_handoff_args(out)]) == 2
        assert not out.exists()
        assert not out.parent.exists()
        assert "investigation.decision" in capsys.readouterr().err


def test_export_always_references_current_superseding_decision(tmp_path) -> None:
    db = tmp_path / "questions.sqlite3"
    _seed_node(db)
    store = InvestigationDecisionStore(db)
    first = _decision(decision_id="dec-a")
    second = _decision(
        decision_id="dec-b",
        supersedes="dec-a",
        created_at="2026-09-04T20:10:00-03:00",
    )
    store.insert(first)
    store.insert(second)
    out = tmp_path / "handoff.json"

    assert cli.main(["--db", str(db), *_handoff_args(out)]) == 0

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["source"]["decision_id"] == "dec-b"
    assert payload["source"]["decision_id"] != "dec-a"


def test_repeated_constraints_preserve_cli_order(tmp_path) -> None:
    db = tmp_path / "questions.sqlite3"
    _seed_current(db)
    out = tmp_path / "handoff.json"
    args = _handoff_args(out) + [
        "--constraint",
        "first",
        "--constraint",
        "second",
    ]

    assert cli.main(["--db", str(db), *args]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["constraints"] == [
        "first",
        "second",
    ]


def test_explicit_metadata_makes_exported_bytes_deterministic(tmp_path) -> None:
    db = tmp_path / "questions.sqlite3"
    _seed_current(db)
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    assert cli.main(["--db", str(db), *_handoff_args(first)]) == 0
    assert cli.main(["--db", str(db), *_handoff_args(second)]) == 0

    assert first.read_bytes() == second.read_bytes()


def test_handoff_parser_accepts_canonical_question_and_public_route(tmp_path) -> None:
    args = cli.build_decision_parser().parse_args(
        [
            "decision",
            "handoff",
            "q-water",
            "--route",
            "PUBLIC_CONTRIBUTION_RESEARCH",
            "--out",
            str(tmp_path / "handoff.json"),
            "--canonical-question",
            "Pregunta canónica explícita",
        ]
    )

    assert args.question_id == "q-water"
    assert args.route == "PUBLIC_CONTRIBUTION_RESEARCH"
    assert args.canonical_question == "Pregunta canónica explícita"
