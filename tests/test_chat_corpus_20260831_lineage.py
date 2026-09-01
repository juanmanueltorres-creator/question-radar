from question_radar.lineage import RELATION_TYPES
from question_radar.lineage_export import load_lineage_bundle
from question_radar.lineage_storage import QuestionLineageStore


CORPUS = 'corpus/chat-2026-08-31-software-recruiting-ai-lineage-v0.4.jsonl'
SOURCE_REF = (
    'geoplatform-knowledge-base/08 - Ideas/'
    'Preguntas - software, IA, trabajo y recruiting - 2026-08-31.md'
)


def test_aug31_lineage_corpus_preserves_14_canonical_questions():
    nodes, relations = load_lineage_bundle(CORPUS)

    expected_ids = {f'vault-2026-08-31-{number:03d}' for number in range(1, 15)}
    assert len(nodes) == 14
    assert {node.id for node in nodes} == expected_ids
    assert all(node.source == 'vault' for node in nodes)
    assert all(node.source_ref == SOURCE_REF for node in nodes)
    assert len(relations) == 8


def test_aug31_lineage_relations_are_explicit_and_importable(tmp_path):
    nodes, relations = load_lineage_bundle(CORPUS)
    node_ids = {node.id for node in nodes}

    assert all(relation.source_question_id in node_ids for relation in relations)
    assert all(relation.target_question_id in node_ids for relation in relations)
    assert all(relation.relation_type in RELATION_TYPES for relation in relations)

    expected = [
        ('001', '002', 'operationalizes'),
        ('005', '006', 'follows_from'),
        ('007', '009', 'follows_from'),
        ('008', '009', 'follows_from'),
        ('008', '012', 'operationalizes'),
        ('010', '011', 'operationalizes'),
        ('012', '004', 'operationalizes'),
        ('008', '013', 'follows_from'),
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
    assert len(store.list_nodes()) == 14
    assert len(store.list_relations()) == 8
