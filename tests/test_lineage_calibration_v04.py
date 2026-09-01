import json
from pathlib import Path

from question_radar.lineage import RELATION_TYPES
from question_radar.lineage_export import load_lineage_bundle
from question_radar.lineage_storage import QuestionLineageStore


def _historical_questions():
    records = []
    for line in Path('corpus/chat-2026-08-29.jsonl').read_text(encoding='utf-8').splitlines():
        if line.strip():
            records.append(json.loads(line))
    return {record['id']: record for record in records}


def test_v04_corpus_preserves_all_historical_question_nodes():
    nodes, relations = load_lineage_bundle('corpus/question-lineage-v0.4.jsonl')
    expected_ids = {f'chat-2026-08-29-{number:03d}' for number in range(1, 13)}
    historical = _historical_questions()

    assert len(nodes) == 12
    assert {node.id for node in nodes} == expected_ids
    assert set(historical) == expected_ids
    for node in nodes:
        assert node.question == historical[node.id]['question']
        assert node.created_at == historical[node.id]['created_at']
        assert node.source == 'conversation'
        assert node.source_ref == 'corpus/chat-2026-08-29.jsonl'

    assert len(relations) == 11


def test_v04_corpus_relations_are_explicit_and_referentially_valid(tmp_path):
    nodes, relations = load_lineage_bundle('corpus/question-lineage-v0.4.jsonl')
    node_ids = {node.id for node in nodes}

    assert all(relation.source_question_id in node_ids for relation in relations)
    assert all(relation.target_question_id in node_ids for relation in relations)
    assert all(relation.relation_type in RELATION_TYPES for relation in relations)

    expected = [
        ('001','002','refines'),
        ('002','003','operationalizes'),
        ('003','004','follows_from'),
        ('005','006','decomposes'),
        ('005','007','decomposes'),
        ('001','008','generalizes'),
        ('008','009','refines'),
        ('004','010','challenges_assumption'),
        ('009','010','follows_from'),
        ('010','011','decomposes'),
        ('011','012','operationalizes'),
    ]
    actual = [
        (
            relation.source_question_id[-3:],
            relation.target_question_id[-3:],
            relation.relation_type,
        )
        for relation in relations
    ]
    assert actual == expected

    store = QuestionLineageStore(tmp_path / 'lineage.sqlite3')
    store.insert_bundle(nodes, relations)
    assert len(store.list_nodes()) == 12
    assert len(store.list_relations()) == 11
