import json
from pathlib import Path

from question_radar.lineage import QuestionNode, QuestionRelation


def load_lineage_bundle(
    path: str | Path,
) -> tuple[list[QuestionNode], list[QuestionRelation]]:
    nodes: list[QuestionNode] = []
    relations: list[QuestionRelation] = []

    for line_number, raw_line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw_line.strip():
            continue
        try:
            payload = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"malformed JSONL at line {line_number}") from exc

        if not isinstance(payload, dict):
            raise ValueError(f"unknown record_type at line {line_number}: None")

        record_type = payload.pop("record_type", None)
        if record_type == "node":
            nodes.append(QuestionNode.from_dict(payload))
        elif record_type == "relation":
            relations.append(QuestionRelation.from_dict(payload))
        else:
            raise ValueError(
                f"unknown record_type at line {line_number}: {record_type}"
            )

    return nodes, relations
