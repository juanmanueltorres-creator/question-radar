import csv
import json
from pathlib import Path

from question_radar.profiles import QuestionProfile

_FIELDNAMES = [
    "id",
    "question",
    "question_type",
    "readiness",
    "clarity",
    "boundedness",
    "investigability",
    "epistemic_openness",
    "purpose_fit",
    "formulation_score",
    "depth",
    "connections",
    "generativity",
    "strengths",
    "gap",
    "assumptions",
    "evidence_required",
    "next_question",
    "topic",
    "evaluator",
    "rubric_version",
    "created_at",
]

_INTEGER_FIELDS = {
    "clarity",
    "boundedness",
    "investigability",
    "epistemic_openness",
    "purpose_fit",
    "formulation_score",
    "depth",
    "connections",
    "generativity",
}


def _prepare_output(path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def _write_jsonl(profiles: list[QuestionProfile], path: str | Path) -> Path:
    output = _prepare_output(path)
    with output.open("w", encoding="utf-8") as handle:
        for profile in profiles:
            handle.write(json.dumps(profile.to_dict(), ensure_ascii=False) + "\n")
    return output


def _write_csv(profiles: list[QuestionProfile], path: str | Path) -> Path:
    output = _prepare_output(path)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_FIELDNAMES)
        writer.writeheader()
        for profile in profiles:
            writer.writerow(profile.to_dict())
    return output


def _read_jsonl(path: str | Path) -> list[QuestionProfile]:
    items: list[QuestionProfile] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"malformed JSONL at line {line_number}") from exc
            items.append(QuestionProfile.from_dict(payload))
    return items


def _read_csv(path: str | Path) -> list[QuestionProfile]:
    items: list[QuestionProfile] = []
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row_number, row in enumerate(reader, start=2):
            payload = dict(row)
            try:
                for field in _INTEGER_FIELDS:
                    payload[field] = int(payload[field])
            except (TypeError, ValueError, KeyError) as exc:
                raise ValueError(
                    f"invalid numeric field in CSV row {row_number}"
                ) from exc
            if payload.get("topic") == "":
                payload["topic"] = None
            items.append(QuestionProfile.from_dict(payload))
    return items


def export_profiles(
    profiles: list[QuestionProfile], path: str | Path, format_name: str
) -> Path:
    if format_name == "jsonl":
        return _write_jsonl(profiles, path)
    if format_name == "csv":
        return _write_csv(profiles, path)
    raise ValueError(f"unsupported export format: {format_name}")


def load_profiles(path: str | Path, format_name: str) -> list[QuestionProfile]:
    if format_name == "jsonl":
        return _read_jsonl(path)
    if format_name == "csv":
        return _read_csv(path)
    raise ValueError(f"unsupported import format: {format_name}")
