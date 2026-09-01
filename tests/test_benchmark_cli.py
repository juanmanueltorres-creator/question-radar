from __future__ import annotations

import json
from pathlib import Path
import subprocess

from question_radar import cli_v06 as cli


BENCHMARK = "corpus/blind-representations-2026-09-01.jsonl"
GOLD = "corpus/gold/blind-representations-2026-09-01-gold-v1.jsonl"


def test_cli_benchmark_evaluate_json_uses_canonical_51_entry_snapshot(capsys) -> None:
    exit_code = cli.main(
        [
            "benchmark",
            "evaluate",
            "--benchmark",
            BENCHMARK,
            "--gold",
            GOLD,
            "--k",
            "5",
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert captured.err == ""
    assert payload["evaluation_version"] == "v0.8"
    assert payload["retrieval_version"] == "v0.7"
    assert payload["corpus_size"] == 51
    assert payload["k"] == 5
    assert len(payload["cases"]) == 8
    assert payload["metrics"]["precision_at_k"] is None


def test_cli_benchmark_evaluate_markdown_exposes_boundary(capsys) -> None:
    exit_code = cli.main(
        [
            "benchmark",
            "evaluate",
            "--benchmark",
            BENCHMARK,
            "--gold",
            GOLD,
            "--format",
            "markdown",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "# Benchmark Evaluation" in captured.out
    assert "## Aggregate Metrics" in captured.out
    assert "## Evaluation Boundary" in captured.out
    assert "Unjudged entries in positive-only cases are unknown, not negative." in captured.out


def test_cli_benchmark_bad_file_fails_closed(tmp_path: Path, capsys) -> None:
    missing = tmp_path / "missing.jsonl"
    exit_code = cli.main(
        [
            "benchmark",
            "evaluate",
            "--benchmark",
            str(missing),
            "--gold",
            GOLD,
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "error:" in captured.err
    assert "missing.jsonl" in captured.err
    assert not missing.exists()


def test_cli_benchmark_can_override_evaluation_corpus_paths(tmp_path: Path, capsys) -> None:
    profile = tmp_path / "profiles.jsonl"
    lineage = tmp_path / "lineage.jsonl"
    gold = tmp_path / "gold.jsonl"
    profile.write_text(
        '{"id":"qv2-cal-019","question":"¿Puede un sistema representar conocimiento?","rubric_version":"v0.2"}\n',
        encoding="utf-8",
    )
    lineage.write_text(
        '{"record_type":"node","id":"vault-2026-08-31-008","question":"¿Cuál es la brecha entre conocer profundamente un dominio y poder representarlo como un sistema ejecutable?","source_ref":"source.md"}\n',
        encoding="utf-8",
    )
    gold.write_text(
        '{"candidate_id":"representation-blind-2026-09-01-001","judgment_scope":"positive_only","expected_abstention":false,"judgments":[{"entry_id":"qv2-cal-019","source_version":"v0.2","relevance":"relevant"},{"entry_id":"vault-2026-08-31-008","source_version":"v0.4","relevance":"partially_relevant"}]}\n',
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "benchmark",
            "evaluate",
            "--benchmark",
            BENCHMARK,
            "--gold",
            str(gold),
            "--corpus",
            str(profile),
            "--corpus",
            str(lineage),
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert captured.err == ""
    assert payload["corpus_size"] == 2
    assert len(payload["cases"]) == 1


def test_installed_cli_exposes_benchmark_help_commands() -> None:
    for args in (
        ["benchmark", "--help"],
        ["benchmark", "evaluate", "--help"],
    ):
        completed = subprocess.run(
            ["question-radar", *args],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert "usage:" in completed.stdout.lower()


def test_root_help_mentions_benchmark_and_retrieval() -> None:
    completed = subprocess.run(
        ["question-radar", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "benchmark" in completed.stdout
    assert "retrieval" in completed.stdout
