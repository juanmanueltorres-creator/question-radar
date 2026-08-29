import argparse
import json
from pathlib import Path
import sys

from question_radar.export import export_evaluations, load_evaluations
from question_radar.models import QuestionEvaluation
from question_radar.storage import QuestionStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="question-radar",
        description="Score questions transparently; never score people.",
    )
    parser.add_argument(
        "--db",
        default="data/questions.sqlite3",
        help="SQLite database path (default: data/questions.sqlite3)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="validate and store one JSON evaluation")
    add_parser.add_argument("evaluation_json")

    subparsers.add_parser("list", help="list stored evaluations")

    top_parser = subparsers.add_parser("top", help="show highest-scoring questions")
    top_parser.add_argument("--limit", type=int, default=10)

    import_parser = subparsers.add_parser("import", help="import a JSONL or CSV corpus")
    import_parser.add_argument("input")
    import_parser.add_argument("--format", choices=("jsonl", "csv"), required=True)

    export_parser = subparsers.add_parser("export", help="explicitly export the corpus")
    export_parser.add_argument("output")
    export_parser.add_argument("--format", choices=("jsonl", "csv"), required=True)

    return parser


def _print_rows(evaluations: list[QuestionEvaluation]) -> None:
    for evaluation in evaluations:
        print(f"{evaluation.score:>3}\t{evaluation.id}\t{evaluation.question}")


def _load_single_json(path: str | Path) -> QuestionEvaluation:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed JSON in {path}") from exc
    return QuestionEvaluation.from_dict(payload)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = QuestionStore(args.db)

    try:
        if args.command == "add":
            evaluation = _load_single_json(args.evaluation_json)
            store.insert(evaluation)
            print(f"added {evaluation.id} score={evaluation.score}")
            return 0

        if args.command == "list":
            _print_rows(store.list_all())
            return 0

        if args.command == "top":
            _print_rows(store.top(args.limit))
            return 0

        if args.command == "import":
            evaluations = load_evaluations(args.input, args.format)
            store.insert_many(evaluations)
            print(f"imported {len(evaluations)} evaluations")
            return 0

        if args.command == "export":
            output = export_evaluations(store.top(limit=1_000_000), args.output, args.format)
            print(f"exported {output}")
            return 0

    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
