import argparse
import json
from pathlib import Path
import sys

from question_radar.export import export_evaluations, load_evaluations
from question_radar.models import QuestionEvaluation
from question_radar.profile_export import export_profiles, load_profiles
from question_radar.profile_storage import QuestionProfileStore
from question_radar.profiles import QUESTION_TYPES, QuestionProfile
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

    profile_parser = subparsers.add_parser(
        "profile",
        help="work with typed Question Radar v0.2 profiles",
    )
    profile_subparsers = profile_parser.add_subparsers(
        dest="profile_command",
        required=True,
    )

    profile_add = profile_subparsers.add_parser(
        "add",
        help="validate and store one v0.2 profile JSON",
    )
    profile_add.add_argument("profile_json")

    profile_subparsers.add_parser("list", help="list stored v0.2 profiles")

    profile_top = profile_subparsers.add_parser(
        "top",
        help="show highest formulation scores within one question type",
    )
    profile_top.add_argument("--type", choices=QUESTION_TYPES, required=True)
    profile_top.add_argument("--limit", type=int, default=10)

    profile_import = profile_subparsers.add_parser(
        "import",
        help="import a v0.2 JSONL or CSV corpus",
    )
    profile_import.add_argument("input")
    profile_import.add_argument("--format", choices=("jsonl", "csv"), required=True)

    profile_export = profile_subparsers.add_parser(
        "export",
        help="explicitly export all v0.2 profiles",
    )
    profile_export.add_argument("output")
    profile_export.add_argument("--format", choices=("jsonl", "csv"), required=True)

    return parser


def _print_rows(evaluations: list[QuestionEvaluation]) -> None:
    for evaluation in evaluations:
        print(f"{evaluation.score:>3}\t{evaluation.id}\t{evaluation.question}")


def _print_profiles(profiles: list[QuestionProfile]) -> None:
    for profile in profiles:
        print(
            f"{profile.formulation_score:>3}\t{profile.question_type}\t"
            f"{profile.readiness}\t{profile.id}\t{profile.question}"
        )


def _load_json(path: str | Path) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed JSON in {path}") from exc


def _load_single_json(path: str | Path) -> QuestionEvaluation:
    return QuestionEvaluation.from_dict(_load_json(path))


def _load_single_profile_json(path: str | Path) -> QuestionProfile:
    return QuestionProfile.from_dict(_load_json(path))


def _handle_profile_command(args: argparse.Namespace, store: QuestionProfileStore) -> int:
    if args.profile_command == "add":
        profile = _load_single_profile_json(args.profile_json)
        store.insert(profile)
        print(
            f"added {profile.id} formulation_score={profile.formulation_score} "
            f"type={profile.question_type}"
        )
        return 0

    if args.profile_command == "list":
        _print_profiles(store.list_all())
        return 0

    if args.profile_command == "top":
        _print_profiles(store.top(args.type, args.limit))
        return 0

    if args.profile_command == "import":
        profiles = load_profiles(args.input, args.format)
        store.insert_many(profiles)
        print(f"imported {len(profiles)} profiles")
        return 0

    if args.profile_command == "export":
        output = export_profiles(store.list_all(), args.output, args.format)
        print(f"exported {output}")
        return 0

    raise ValueError("unknown profile command")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = QuestionStore(args.db)
    profile_store = QuestionProfileStore(args.db)

    try:
        if args.command == "profile":
            return _handle_profile_command(args, profile_store)

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
