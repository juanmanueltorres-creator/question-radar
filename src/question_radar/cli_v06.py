from __future__ import annotations

import argparse
from pathlib import Path
import sys

from question_radar import cli as legacy_cli
from question_radar.benchmark_eval import evaluate_benchmark
from question_radar.benchmark_export import (
    render_benchmark_json,
    render_benchmark_markdown,
)
from question_radar.benchmark_io import (
    load_benchmark,
    load_evaluation_corpus,
    load_gold,
)
from question_radar.retrieval import retrieve_candidates
from question_radar.retrieval_export import (
    render_retrieval_json,
    render_retrieval_markdown,
)
from question_radar.retrieval_storage import load_retrieval_corpus


DEFAULT_EVALUATION_CORPUS = (
    "corpus/anti-ia-calibration-v0.2.jsonl",
    "corpus/question-lineage-v0.4.jsonl",
    "corpus/chat-2026-08-31-software-recruiting-ai-lineage-v0.4.jsonl",
)


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
    print("\nadditional commands:")
    print("  retrieval           retrieve prior questions from v0.2/v0.4 read-only corpus")
    print("  benchmark           evaluate frozen retrieval benchmarks against editorial gold")


def _base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="question-radar",
        description="Score questions transparently; never score people.",
    )
    parser.add_argument(
        "--db",
        default="data/questions.sqlite3",
        help="SQLite database path (default: data/questions.sqlite3)",
    )
    return parser


def build_retrieval_parser() -> argparse.ArgumentParser:
    parser = _base_parser()
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


def build_benchmark_parser() -> argparse.ArgumentParser:
    parser = _base_parser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="evaluate frozen candidate questions against editorial gold",
    )
    benchmark_subparsers = benchmark_parser.add_subparsers(
        dest="benchmark_command",
        required=True,
    )
    evaluate_parser = benchmark_subparsers.add_parser(
        "evaluate",
        help="run the frozen v0.7 retrieval baseline against a gold set",
    )
    evaluate_parser.add_argument("--benchmark", required=True)
    evaluate_parser.add_argument("--gold", required=True)
    evaluate_parser.add_argument(
        "--corpus",
        action="append",
        default=None,
        help="evaluation corpus JSONL path; repeat to override canonical defaults",
    )
    evaluate_parser.add_argument("--k", type=int, default=5)
    evaluate_parser.add_argument(
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


def _handle_benchmark(args: argparse.Namespace) -> int:
    if args.benchmark_command != "evaluate":
        raise ValueError("unknown benchmark command")

    benchmark = load_benchmark(args.benchmark)
    gold = load_gold(args.gold, benchmark)
    corpus_paths = tuple(args.corpus or DEFAULT_EVALUATION_CORPUS)
    corpus = load_evaluation_corpus(corpus_paths)
    evaluation = evaluate_benchmark(
        gold,
        corpus,
        k=args.k,
        benchmark_name=Path(args.benchmark).stem,
        gold_version=Path(args.gold).stem,
    )
    rendered = (
        render_benchmark_json(evaluation)
        if args.format == "json"
        else render_benchmark_markdown(evaluation)
    )
    print(rendered, end="")
    return 0


def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    if _root_help_requested(args_list):
        _print_root_help()
        return 0

    top_level = _top_level_command(args_list)
    if top_level not in {"retrieval", "benchmark"}:
        return legacy_cli.main(args_list)

    parser = (
        build_retrieval_parser()
        if top_level == "retrieval"
        else build_benchmark_parser()
    )
    args = parser.parse_args(args_list)
    try:
        return (
            _handle_retrieval(args)
            if top_level == "retrieval"
            else _handle_benchmark(args)
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
