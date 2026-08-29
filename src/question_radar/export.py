import csv
import json
from pathlib import Path

from question_radar.models import QuestionEvaluation

_FIELDNAMES = [
    "id",
    "question",
    "clarity",
    "depth",
    "investigability",
    "assumption_challenge",
    "connections",
    "score",
    "strengths",
    "gap",
    "next_question",
    "topic",
    "evaluator",
    "rubric_version",
    "created_at",
]

_INTEGER_FIELDS = {
    "clarity",
    "depth",
    "investigability",
    "assumption_challenge",
    "connections",
    "score",
}


def _prepare_output(path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def write_jsonl(evaluations: list[QuestionEvaluation], path: str | Path) -> Path:
    output = _prepare_output(path)
    with output.open("w", encoding="utf-8") as handle:
        for evaluation in evaluations:
            handle.write(json.dumps(evaluation.to_dict(), ensure_ascii=False) + "\n")
    return output


def write_csv(evaluations: list[QuestionEvaluation], path: str | Path) -> Path:
    output = _prepare_output(path)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_FIELDNAMES)
        writer.writeheader()
        for evaluation in evaluations:
            writer.writerow(evaluation.to_dict())
    return output


def read_jsonl(path: str | Path) -> list[QuestionEvaluation]:
    items: list[QuestionEvaluation] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"malformed JSONL at line {line_number}") from exc
            items.append(QuestionEvaluation.from_dict(payload))
    return items


def read_csv(path: str | Path) -> list[QuestionEvaluation]:
    items: list[QuestionEvaluation] = []
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row_number, row in enumerate(reader, start=2):
            payload = dict(row)
            try:
                for field in _INTEGER_FIELDS:
                    payload[field] = int(payload[field])
            except (TypeError, ValueError, KeyError) as exc:
                raise ValueError(f"invalid numeric field in CSV row {row_number}") from exc
            if payload.get("topic") == "":
                payload["topic"] = None
            items.append(QuestionEvaluation.from_dict(payload))
    return items


def export_evaluations(
    evaluations: list[QuestionEvaluation], path: str | Path, format_name: str
) -> Path:
    if format_name == "jsonl":
        return write_jsonl(evaluations, path)
    if format_name == "csv":
        return write_csv(evaluations, path)
    raise ValueError(f"unsupported export format: {format_name}")


def load_evaluations(path: str | Path, format_name: str) -> list[QuestionEvaluation]:
    if format_name == "jsonl":
        return read_jsonl(path)
    if format_name == "csv":
        return read_csv(path)
    raise ValueError(f"unsupported import format: {format_name}")
