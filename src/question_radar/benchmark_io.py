from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable

from question_radar.retrieval import CorpusEntry


JUDGMENT_SCOPES = ("positive_only", "exhaustive")
RELEVANCE_VALUES = ("relevant", "partially_relevant", "not_relevant")
SOURCE_VERSIONS = ("v0.2", "v0.4")


@dataclass(frozen=True, slots=True)
class BenchmarkQuestion:
    id: str
    question: str

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("benchmark id must be a non-empty string")
        if not isinstance(self.question, str) or not self.question.strip():
            raise ValueError("benchmark question must be a non-empty string")
        object.__setattr__(self, "id", self.id.strip())
        object.__setattr__(self, "question", self.question.strip())


@dataclass(frozen=True, slots=True)
class GoldJudgment:
    entry_id: str
    source_version: str
    relevance: str

    def __post_init__(self) -> None:
        if not isinstance(self.entry_id, str) or not self.entry_id.strip():
            raise ValueError("gold entry_id must be a non-empty string")
        if self.source_version not in SOURCE_VERSIONS:
            raise ValueError("source_version must be v0.2 or v0.4")
        if self.relevance not in RELEVANCE_VALUES:
            raise ValueError("relevance must be relevant, partially_relevant, or not_relevant")
        object.__setattr__(self, "entry_id", self.entry_id.strip())


@dataclass(frozen=True, slots=True)
class GoldCase:
    candidate_id: str
    question: str
    judgment_scope: str
    expected_abstention: bool
    judgments: tuple[GoldJudgment, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.candidate_id, str) or not self.candidate_id.strip():
            raise ValueError("gold candidate_id must be a non-empty string")
        if not isinstance(self.question, str) or not self.question.strip():
            raise ValueError("gold question must be a non-empty string")
        if self.judgment_scope not in JUDGMENT_SCOPES:
            raise ValueError("judgment_scope must be positive_only or exhaustive")
        if not isinstance(self.expected_abstention, bool):
            raise ValueError("expected_abstention must be boolean")

        refs = [(item.source_version, item.entry_id) for item in self.judgments]
        if len(refs) != len(set(refs)):
            raise ValueError("duplicate gold judgment reference")

        if self.expected_abstention:
            if self.judgment_scope != "exhaustive":
                raise ValueError("expected abstention requires exhaustive judgments")
            if any(item.relevance != "not_relevant" for item in self.judgments):
                raise ValueError("expected abstention cannot include useful judgments")

        object.__setattr__(self, "candidate_id", self.candidate_id.strip())
        object.__setattr__(self, "question", self.question.strip())


def _jsonl_rows(path: str | Path) -> Iterable[tuple[int, dict[str, Any]]]:
    source = Path(path)
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON in {source} line {line_number}: {exc.msg}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"JSONL row must be an object in {source} line {line_number}")
        yield line_number, row


def _required_string(row: dict[str, Any], key: str, context: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}: {key} must be a non-empty string")
    return value.strip()


def load_benchmark(path: str | Path) -> tuple[BenchmarkQuestion, ...]:
    questions: list[BenchmarkQuestion] = []
    seen: set[str] = set()
    for line_number, row in _jsonl_rows(path):
        context = f"benchmark line {line_number}"
        item = BenchmarkQuestion(
            id=_required_string(row, "id", context),
            question=_required_string(row, "question", context),
        )
        if item.id in seen:
            raise ValueError(f"duplicate benchmark id: {item.id}")
        seen.add(item.id)
        questions.append(item)
    return tuple(questions)


def _parse_judgments(raw: Any, context: str) -> tuple[GoldJudgment, ...]:
    if not isinstance(raw, list):
        raise ValueError(f"{context}: judgments must be a list")
    judgments: list[GoldJudgment] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"{context}: judgment {index} must be an object")
        judgments.append(
            GoldJudgment(
                entry_id=_required_string(item, "entry_id", context),
                source_version=_required_string(item, "source_version", context),
                relevance=_required_string(item, "relevance", context),
            )
        )
    return tuple(judgments)


def load_gold(
    path: str | Path,
    benchmark: tuple[BenchmarkQuestion, ...],
) -> tuple[GoldCase, ...]:
    benchmark_by_id = {item.id: item for item in benchmark}
    cases: list[GoldCase] = []
    seen: set[str] = set()

    for line_number, row in _jsonl_rows(path):
        context = f"gold line {line_number}"
        candidate_id = _required_string(row, "candidate_id", context)
        if candidate_id in seen:
            raise ValueError(f"duplicate gold candidate: {candidate_id}")
        seen.add(candidate_id)
        if candidate_id not in benchmark_by_id:
            raise ValueError(f"unknown benchmark candidate: {candidate_id}")

        scope = _required_string(row, "judgment_scope", context)
        if scope not in JUDGMENT_SCOPES:
            raise ValueError("judgment_scope must be positive_only or exhaustive")
        expected_abstention = row.get("expected_abstention")
        if not isinstance(expected_abstention, bool):
            raise ValueError(f"{context}: expected_abstention must be boolean")

        cases.append(
            GoldCase(
                candidate_id=candidate_id,
                question=benchmark_by_id[candidate_id].question,
                judgment_scope=scope,
                expected_abstention=expected_abstention,
                judgments=_parse_judgments(row.get("judgments"), context),
            )
        )

    return tuple(cases)


def load_evaluation_corpus(
    paths: tuple[str | Path, ...],
) -> tuple[CorpusEntry, ...]:
    entries: list[CorpusEntry] = []
    seen: set[tuple[str, str]] = set()

    for path in paths:
        for line_number, row in _jsonl_rows(path):
            if "record_type" in row:
                record_type = row.get("record_type")
                if record_type == "relation":
                    continue
                if record_type != "node":
                    raise ValueError(f"unsupported v0.4 record_type at {path} line {line_number}")
                entry = CorpusEntry(
                    id=_required_string(row, "id", f"{path} line {line_number}"),
                    question=_required_string(row, "question", f"{path} line {line_number}"),
                    source_version="v0.4",
                    source_kind="lineage_node",
                    provenance=(
                        row.get("source_ref").strip()
                        if isinstance(row.get("source_ref"), str) and row.get("source_ref").strip()
                        else None
                    ),
                )
            else:
                if row.get("rubric_version") != "v0.2":
                    raise ValueError(f"unsupported profile row at {path} line {line_number}")
                entry = CorpusEntry(
                    id=_required_string(row, "id", f"{path} line {line_number}"),
                    question=_required_string(row, "question", f"{path} line {line_number}"),
                    source_version="v0.2",
                    source_kind="profile",
                    provenance=None,
                )

            ref = (entry.source_version, entry.id)
            if ref in seen:
                raise ValueError(f"duplicate evaluation corpus entry: {ref[0]}:{ref[1]}")
            seen.add(ref)
            entries.append(entry)

    entries.sort(key=lambda item: (item.source_version, item.id, item.source_kind))
    return tuple(entries)
