import json
from pathlib import Path

from question_radar.learning import LearningObservation


def _prepare_output(path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def _write_jsonl(
    observations: list[LearningObservation], path: str | Path
) -> Path:
    output = _prepare_output(path)
    with output.open("w", encoding="utf-8") as handle:
        for observation in observations:
            handle.write(
                json.dumps(observation.to_dict(), ensure_ascii=False) + "\n"
            )
    return output


def _read_jsonl(path: str | Path) -> list[LearningObservation]:
    observations: list[LearningObservation] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"malformed JSONL at line {line_number}"
                ) from exc
            observations.append(LearningObservation.from_dict(payload))
    return observations


def export_learning_observations(
    observations: list[LearningObservation],
    path: str | Path,
    format_name: str,
) -> Path:
    if format_name == "jsonl":
        return _write_jsonl(observations, path)
    raise ValueError(f"unsupported export format: {format_name}")


def load_learning_observations(
    path: str | Path,
    format_name: str,
) -> list[LearningObservation]:
    if format_name == "jsonl":
        return _read_jsonl(path)
    raise ValueError(f"unsupported import format: {format_name}")
