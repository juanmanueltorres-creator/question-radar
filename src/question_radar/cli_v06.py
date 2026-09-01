from __future__ import annotations

import argparse
import sys

from question_radar import cli as legacy_cli
from question_radar.retrieval import retrieve_candidates
from question_radar.retrieval_export import (
    render_retrieval_json,
    render_retrieval_markdown,
)
from question_radar.retrieval_storage import load_retrieval_corpus


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


def _print_root_help() -> None:
    legacy_cli.build_parser().print_help()
    print("\nv0.6 additional command:")
    print("  retrieval           retrieve prior questions from v0.2/v0.4 read-only corpus")


def build_retrieval_parser() -> argparse.ArgumentParser:
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
    retrieval_parser = subparsers.add_parser(
        "retrieval",
        help="retrieve prior questions from the unified read-only corpus",
    )
    retrieval_subparsers = retrieval_parser.add_subparsers(
        dest="retrieval_command",
        required=True,
    )
    compare_parser = retrieval_subparsers.add_parser(
        "compare",
        help="retrieve prior v0.2/v0.4 questions for one candidate",
    )
    compare_parser.add_argument("question")
    compare_parser.add_argument("--limit", type=int, default=5)
    compare_parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
    )
    return parser


def _handle_retrieval(args: argparse.Namespace) -> int:
    if args.retrieval_command != "compare":
        raise ValueError("unknown retrieval command")

    corpus = load_retrieval_corpus(args.db)
    pack = retrieve_candidates(args.question, corpus, limit=args.limit)
    rendered = (
        render_retrieval_json(pack)
        if args.format == "json"
        else render_retrieval_markdown(pack)
    )
    print(rendered, end="")
    return 0


def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    if _root_help_requested(args_list):
        _print_root_help()
        return 0

    if _top_level_command(args_list) != "retrieval":
        return legacy_cli.main(args_list)

    parser = build_retrieval_parser()
    args = parser.parse_args(args_list)
    try:
        return _handle_retrieval(args)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
