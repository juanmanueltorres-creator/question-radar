from __future__ import annotations

import argparse
from datetime import datetime, timezone
import sys
import uuid

from question_radar import cli_v06 as previous_cli
from question_radar.decision_export import (
    render_active_json,
    render_active_markdown,
    render_decision_json,
    render_decision_markdown,
    render_history_json,
    render_history_markdown,
)
from question_radar.decision_storage import InvestigationDecisionStore
from question_radar.decisions import (
    CONFIDENCE_LEVELS,
    COST_LEVELS,
    DECISION_STATES,
    InvestigationDecision,
)


def _parse_bool(value: str) -> bool:
    cleaned = value.strip().lower()
    if cleaned == "true":
        return True
    if cleaned == "false":
        return False
    raise argparse.ArgumentTypeError("expected true or false")


def _new_decision_id() -> str:
    return f"dec-{uuid.uuid4().hex}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _top_level_command(argv: list[str]) -> str | None:
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--db":
            index += 2
            continue
        if token.startswith("--db="):
            index += 1
            continue
        if token.startswith("-"):
            return None
        return token
    return None


def _root_help_requested(argv: list[str]) -> bool:
    remaining: list[str] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--db":
            if index + 1 >= len(argv):
                return False
            index += 2
            continue
        if token.startswith("--db="):
            index += 1
            continue
        remaining.append(token)
        index += 1
    return remaining in (["--help"], ["-h"])


def build_decision_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="question-radar",
        description="Record and inspect explicit investigation decisions.",
    )
    parser.add_argument(
        "--db",
        default="data/questions.sqlite3",
        help="SQLite database path (default: data/questions.sqlite3)",
    )
    root = parser.add_subparsers(dest="command", required=True)
    decision = root.add_parser(
        "decision",
        help="record and inspect Investigation Decision Gate v0.9 judgments",
    )
    commands = decision.add_subparsers(dest="decision_command", required=True)

    record = commands.add_parser("record", help="append one immutable decision")
    record.add_argument("--question-id", required=True)
    record.add_argument("--decision", choices=DECISION_STATES, required=True)
    record.add_argument("--rationale", required=True)
    record.add_argument("--goal-alignment", type=_parse_bool, required=True)
    record.add_argument("--external-signal", type=_parse_bool, required=True)
    record.add_argument("--testable-now", type=_parse_bool, required=True)
    record.add_argument("--leverage", type=_parse_bool, required=True)
    record.add_argument("--cost", choices=COST_LEVELS, required=True)
    record.add_argument("--confidence", choices=CONFIDENCE_LEVELS, required=True)
    record.add_argument("--next-test")
    record.add_argument("--resume-when")
    record.add_argument("--kill-condition")
    record.add_argument("--supersedes")
    record.add_argument("--id")
    record.add_argument("--created-at")

    for name in ("show", "history"):
        command = commands.add_parser(name)
        command.add_argument("question_id")
        command.add_argument(
            "--format",
            choices=("markdown", "json"),
            default="markdown",
        )

    active = commands.add_parser("active")
    active.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
    )
    return parser


def _print_root_help() -> None:
    previous_cli.main(["--help"])
    print(
        "  decision            record and inspect Investigation Decision Gate v0.9 judgments"
    )


def _handle_record(args: argparse.Namespace) -> int:
    item = InvestigationDecision.from_dict(
        {
            "id": args.id or _new_decision_id(),
            "question_id": args.question_id,
            "decision": args.decision,
            "rationale": args.rationale,
            "goal_alignment": args.goal_alignment,
            "external_signal": args.external_signal,
            "testable_now": args.testable_now,
            "leverage": args.leverage,
            "cost": args.cost,
            "confidence": args.confidence,
            "next_test": args.next_test,
            "resume_when": args.resume_when,
            "kill_condition": args.kill_condition,
            "supersedes_decision_id": args.supersedes,
            "created_at": args.created_at or _now_iso(),
        }
    )
    InvestigationDecisionStore(args.db).insert(item)
    print(f"recorded {item.id}")
    return 0


def _handle_decision(args: argparse.Namespace) -> int:
    if args.decision_command == "record":
        return _handle_record(args)

    store = InvestigationDecisionStore(args.db)
    if args.decision_command == "show":
        node = store.get_question_node(args.question_id)
        if node is None:
            raise ValueError(f"question node not found: {args.question_id}")
        current = store.get_current(args.question_id)
        if current is None:
            raise ValueError(
                f"no investigation decision recorded for: {args.question_id}"
            )
        rendered = (
            render_decision_json(node, current)
            if args.format == "json"
            else render_decision_markdown(node, current)
        )
    elif args.decision_command == "history":
        node = store.get_question_node(args.question_id)
        if node is None:
            raise ValueError(f"question node not found: {args.question_id}")
        history = store.list_history(args.question_id)
        rendered = (
            render_history_json(node, history)
            if args.format == "json"
            else render_history_markdown(node, history)
        )
    elif args.decision_command == "active":
        current = store.list_current_decisions()
        pairs = [(store.get_question_node(item.question_id), item) for item in current]
        if any(node is None for node, _ in pairs):
            raise RuntimeError("current decision references a missing question node")
        entries = [(node, item) for node, item in pairs if node is not None]
        rendered = (
            render_active_json(entries)
            if args.format == "json"
            else render_active_markdown(entries)
        )
    else:
        raise ValueError("unknown decision command")

    print(rendered, end="")
    return 0


def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    if _root_help_requested(args_list):
        _print_root_help()
        return 0
    if _top_level_command(args_list) != "decision":
        return previous_cli.main(args_list)

    parser = build_decision_parser()
    args = parser.parse_args(args_list)
    try:
        return _handle_decision(args)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
