import json

from question_radar.context_pack import (
    build_context_pack,
    render_context_json,
    render_context_markdown,
)
from question_radar.learning_export import load_learning_observations
from question_radar.learning_storage import LearningObservationStore
from question_radar.lineage_export import load_lineage_bundle
from question_radar.lineage_storage import QuestionLineageStore
from question_radar.profile_export import load_profiles
from question_radar.profile_storage import QuestionProfileStore


def test_question_lineage_v04_end_to_end(tmp_path):
    db_path = tmp_path / 'question-radar.sqlite3'
    lineage_store = QuestionLineageStore(db_path)
    profile_store = QuestionProfileStore(db_path)
    learning_store = LearningObservationStore(db_path)

    nodes, relations = load_lineage_bundle('corpus/question-lineage-v0.4.jsonl')
    lineage_store.insert_bundle(nodes, relations)

    profiles = load_profiles('corpus/chat-2026-08-29.jsonl', 'jsonl')
    profile_store.insert_many(profiles)

    observations = load_learning_observations(
        'corpus/learning-frontier-chat-2026-08-29-v0.3.jsonl', 'jsonl'
    )
    learning_store.insert_many(observations)

    pack = build_context_pack(
        'chat-2026-08-29-012',
        lineage_store,
        profile_store,
        learning_store,
    )

    assert pack.current_question.id == 'chat-2026-08-29-012'
    assert [node.id for node, _ in pack.ancestors] == [
        'chat-2026-08-29-011',
        'chat-2026-08-29-010',
        'chat-2026-08-29-004',
        'chat-2026-08-29-009',
    ]
    assert any(
        relation.source_question_id == 'chat-2026-08-29-011'
        and relation.target_question_id == 'chat-2026-08-29-012'
        and relation.relation_type == 'operationalizes'
        for relation in pack.relations
    )
    assert {profile.id for profile in pack.profiles} >= {
        'chat-2026-08-29-010',
        'chat-2026-08-29-011',
        'chat-2026-08-29-012',
    }
    assert {item.id for item in pack.learning_observations} == {
        'learning-chat-2026-08-29-001',
        'learning-chat-2026-08-29-002',
    }

    markdown = render_context_markdown(pack)
    assert '## CURRENT QUESTION' in markdown
    assert '## LEARNING SIGNALS' in markdown
    assert '¿Podemos reutilizar este sistema' in markdown

    payload = json.loads(render_context_json(pack))
    assert payload['context_version'] == 'v0.4'
    assert payload['current_question']['id'] == 'chat-2026-08-29-012'
