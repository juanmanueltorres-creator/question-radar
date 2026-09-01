import json

import pytest

from question_radar.lineage_export import load_lineage_bundle


VALID_LINES = [
    {
        "record_type": "node",
        "id": "q-1",
        "question": "First?",
        "source": "corpus",
        "source_ref": "fixture",
        "created_at": "2026-08-29T18:00:00-03:00",
    },
    {
        "record_type": "node",
        "id": "q-2",
        "question": "Second?",
        "source": "corpus",
        "source_ref": "fixture",
        "created_at": "2026-08-29T18:01:00-03:00",
    },
    {
        "record_type": "relation",
        "id": "r-1",
        "source_question_id": "q-1",
        "target_question_id": "q-2",
        "relation_type": "refines",
        "created_at": "2026-08-29T18:02:00-03:00",
    },
]


def write_jsonl(path, records):
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8",
    )


def test_load_lineage_bundle_dispatches_nodes_and_relations(tmp_path):
    path = tmp_path / "lineage.jsonl"
    write_jsonl(path, VALID_LINES)
    nodes, relations = load_lineage_bundle(path)
    assert [node.id for node in nodes] == ["q-1", "q-2"]
    assert [relation.id for relation in relations] == ["r-1"]
    assert "record_type" not in nodes[0].to_dict()
    assert "record_type" not in relations[0].to_dict()


def test_blank_lines_are_ignored(tmp_path):
    path = tmp_path / "lineage.jsonl"
    path.write_text("\n\n" + json.dumps(VALID_LINES[0]) + "\n\n", encoding="utf-8")
    nodes, relations = load_lineage_bundle(path)
    assert [node.id for node in nodes] == ["q-1"]
    assert relations == []


def test_empty_file_returns_empty_bundle(tmp_path):
    path = tmp_path / "lineage.jsonl"
    path.write_text("", encoding="utf-8")
    assert load_lineage_bundle(path) == ([], [])


def test_malformed_json_reports_line_number(tmp_path):
    path = tmp_path / "lineage.jsonl"
    path.write_text(json.dumps(VALID_LINES[0]) + "\n{broken\n", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed JSONL at line 2"):
        load_lineage_bundle(path)


@pytest.mark.parametrize("record_type", [None, "edge", 7])
def test_unknown_or_missing_record_type_is_rejected(tmp_path, record_type):
    path = tmp_path / "lineage.jsonl"
    record = dict(VALID_LINES[0])
    if record_type is None:
        record.pop("record_type")
    else:
        record["record_type"] = record_type
    write_jsonl(path, [record])
    with pytest.raises(ValueError, match="unknown record_type at line 1"):
        load_lineage_bundle(path)


def test_invalid_node_payload_is_rejected_by_domain_contract(tmp_path):
    path = tmp_path / "lineage.jsonl"
    record = dict(VALID_LINES[0])
    record["source"] = "invalid"
    write_jsonl(path, [record])
    with pytest.raises(ValueError, match="source must be one of"):
        load_lineage_bundle(path)


def test_invalid_relation_payload_is_rejected_by_domain_contract(tmp_path):
    path = tmp_path / "lineage.jsonl"
    record = dict(VALID_LINES[2])
    record["relation_type"] = "causes"
    write_jsonl(path, [record])
    with pytest.raises(ValueError, match="relation_type must be one of"):
        load_lineage_bundle(path)
