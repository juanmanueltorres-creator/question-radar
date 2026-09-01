import json

import pytest

from question_radar.cli import build_parser, main


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def node_payload(node_id="q-1", question="¿Primera pregunta?"):
    return {
        "id": node_id,
        "question": question,
        "source": "manual",
        "source_ref": None,
        "created_at": "2026-08-29T18:00:00-03:00",
    }


def relation_payload():
    return {
        "id": "r-1",
        "source_question_id": "q-1",
        "target_question_id": "q-2",
        "relation_type": "refines",
        "created_at": "2026-08-29T18:02:00-03:00",
    }


def test_lineage_context_parser_defaults_and_overrides():
    args = build_parser().parse_args(["lineage", "context", "q-12"])
    assert args.command == "lineage"
    assert args.lineage_command == "context"
    assert args.question_id == "q-12"
    assert args.format == "markdown"
    assert args.ancestors == 3
    assert args.descendants == 1

    args = build_parser().parse_args(
        [
            "lineage", "context", "q-12", "--format", "json",
            "--ancestors", "2", "--descendants", "0",
        ]
    )
    assert args.format == "json"
    assert args.ancestors == 2
    assert args.descendants == 0


def test_lineage_parser_supports_node_relation_and_import_forms():
    parser = build_parser()
    assert parser.parse_args(["lineage", "node", "add", "node.json"]).node_command == "add"
    assert parser.parse_args(["lineage", "node", "list"]).node_command == "list"
    assert parser.parse_args(["lineage", "node", "show", "q-1"]).question_id == "q-1"
    assert parser.parse_args(["lineage", "relation", "add", "relation.json"]).relation_command == "add"
    filtered = parser.parse_args(["lineage", "relation", "list", "--question", "q-1"])
    assert filtered.relation_command == "list"
    assert filtered.question == "q-1"
    assert parser.parse_args(["lineage", "import", "corpus.jsonl"]).input == "corpus.jsonl"


def test_node_add_list_show_and_missing_error(tmp_path, capsys):
    db = tmp_path / "lineage.sqlite3"
    node_file = tmp_path / "node.json"
    write_json(node_file, node_payload())

    assert main(["--db", str(db), "lineage", "node", "add", str(node_file)]) == 0
    assert "added q-1" in capsys.readouterr().out

    assert main(["--db", str(db), "lineage", "node", "list"]) == 0
    assert "q-1\t¿Primera pregunta?" in capsys.readouterr().out

    assert main(["--db", str(db), "lineage", "node", "show", "q-1"]) == 0
    shown = capsys.readouterr().out
    assert "id: q-1" in shown
    assert "question: ¿Primera pregunta?" in shown
    assert "source: manual" in shown
    assert "source_ref: None" in shown
    assert "created_at: 2026-08-29T18:00:00-03:00" in shown

    assert main(["--db", str(db), "lineage", "node", "show", "missing"]) == 2
    assert "error: question node not found: missing" in capsys.readouterr().err


def test_relation_add_list_and_filter(tmp_path, capsys):
    db = tmp_path / "lineage.sqlite3"
    q1 = tmp_path / "q1.json"
    q2 = tmp_path / "q2.json"
    rel_file = tmp_path / "relation.json"
    write_json(q1, node_payload("q-1", "First?"))
    write_json(q2, node_payload("q-2", "Second?"))
    write_json(rel_file, relation_payload())
    for path in (q1, q2):
        assert main(["--db", str(db), "lineage", "node", "add", str(path)]) == 0
        capsys.readouterr()

    assert main(["--db", str(db), "lineage", "relation", "add", str(rel_file)]) == 0
    assert "added r-1" in capsys.readouterr().out

    assert main(["--db", str(db), "lineage", "relation", "list"]) == 0
    assert capsys.readouterr().out.strip() == "refines\tq-1\tq-2\tr-1"

    assert main(["--db", str(db), "lineage", "relation", "list", "--question", "q-1"]) == 0
    assert "r-1" in capsys.readouterr().out

    assert main(["--db", str(db), "lineage", "relation", "list", "--question", "missing"]) == 0
    assert capsys.readouterr().out == ""


def test_bundle_import_and_context_markdown_json(tmp_path, capsys):
    db = tmp_path / "lineage.sqlite3"
    corpus = tmp_path / "lineage.jsonl"
    records = [
        {"record_type": "node", **node_payload("q-1", "¿Primera?")},
        {"record_type": "node", **node_payload("q-2", "¿Segunda?")},
        {"record_type": "relation", **relation_payload()},
    ]
    corpus.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8",
    )

    assert main(["--db", str(db), "lineage", "import", str(corpus)]) == 0
    assert capsys.readouterr().out.strip() == "imported 2 nodes and 1 relations"

    assert main(["--db", str(db), "lineage", "context", "q-2"]) == 0
    markdown = capsys.readouterr().out
    assert "# Question Radar Context Pack" in markdown
    assert "question: ¿Segunda?" in markdown
    assert "q-1 --refines--> q-2" in markdown

    assert main(["--db", str(db), "lineage", "context", "q-2", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["current_question"]["id"] == "q-2"
    assert payload["context_version"] == "v0.4"


def test_negative_context_depth_returns_code_2_without_traceback(tmp_path, capsys):
    db = tmp_path / "lineage.sqlite3"
    node_file = tmp_path / "node.json"
    write_json(node_file, node_payload())
    assert main(["--db", str(db), "lineage", "node", "add", str(node_file)]) == 0
    capsys.readouterr()

    result = main(
        ["--db", str(db), "lineage", "context", "q-1", "--ancestors", "-1"]
    )
    captured = capsys.readouterr()
    assert result == 2
    assert "max_depth must be a non-negative integer" in captured.err
    assert "Traceback" not in captured.err
