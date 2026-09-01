import json

import pytest

from question_radar.context_pack import build_context_pack, render_context_json, render_context_markdown
from question_radar.learning import LearningObservation
from question_radar.learning_storage import LearningObservationStore
from question_radar.lineage import QuestionNode, QuestionRelation
from question_radar.lineage_storage import QuestionLineageStore
from question_radar.profile_storage import QuestionProfileStore
from question_radar.profiles import QuestionProfile


def node(node_id: str, minute: int) -> QuestionNode:
    return QuestionNode.from_dict({"id": node_id, "question": f"Pregunta {node_id}?", "source": "conversation", "source_ref": "corpus/chat.jsonl", "created_at": f"2026-08-29T18:{minute:02d}:00-03:00"})


def relation(relation_id: str, source: str, target: str, minute: int) -> QuestionRelation:
    return QuestionRelation.from_dict({"id": relation_id, "source_question_id": source, "target_question_id": target, "relation_type": "follows_from", "created_at": f"2026-08-29T19:{minute:02d}:00-03:00"})


def profile(question_id: str, minute: int, suffix: str = "") -> QuestionProfile:
    return QuestionProfile.from_dict({"id": question_id, "question": f"Pregunta {question_id}?", "question_type": "epistemological_meta", "readiness": "ready_to_investigate", "clarity": 5, "boundedness": 5, "investigability": 5, "epistemic_openness": 5, "purpose_fit": 5, "formulation_score": 100, "depth": 5, "connections": 5, "generativity": 5, "strengths": f"strength {suffix}", "gap": f"gap {suffix}", "assumptions": f"assumption {question_id}{suffix}", "evidence_required": f"evidence {question_id}{suffix}", "next_question": f"next {question_id}{suffix}?", "topic": "question_radar", "evaluator": "test", "rubric_version": "v0.2", "created_at": f"2026-08-29T18:{minute:02d}:00-03:00"})


def observation(observation_id: str, evidence_ids: list[str], minute: int) -> LearningObservation:
    return LearningObservation.from_dict({"id": observation_id, "concept": f"concept-{observation_id}", "gap_type": "connection", "state": "possible_gap", "confidence": "low", "evidence_question_ids": evidence_ids, "interpretation": "evidence-backed interpretation", "suggested_next_step": "ask a stronger question", "created_at": f"2026-08-29T20:{minute:02d}:00-03:00", "updated_at": f"2026-08-29T20:{minute:02d}:00-03:00"})


def stores(tmp_path):
    db = tmp_path / "context.sqlite3"
    return QuestionLineageStore(db), QuestionProfileStore(db), LearningObservationStore(db)


def test_minimal_context_pack_has_current_question_and_empty_optional_layers(tmp_path):
    lineage_store, profile_store, learning_store = stores(tmp_path)
    lineage_store.insert_node(node("q-current", 10))
    pack = build_context_pack("q-current", lineage_store, profile_store, learning_store)
    assert pack.context_version == "v0.4"
    assert pack.current_question.id == "q-current"
    assert pack.ancestors == ()
    assert pack.descendants == ()
    assert pack.relations == ()
    assert pack.profiles == ()
    assert pack.learning_observations == ()
    assert pack.unresolved_assumptions == ()
    assert pack.evidence_still_needed == ()
    assert pack.existing_next_questions == ()


def test_missing_current_node_is_an_error(tmp_path):
    lineage_store, profile_store, learning_store = stores(tmp_path)
    with pytest.raises(ValueError, match="question node not found: missing"):
        build_context_pack("missing", lineage_store, profile_store, learning_store)


def test_pack_uses_default_three_ancestors_one_descendant(tmp_path):
    lineage_store, profile_store, learning_store = stores(tmp_path)
    nodes = [node(f"q{i}", i) for i in range(1, 7)]
    relations = [relation("r12", "q1", "q2", 1), relation("r23", "q2", "q3", 2), relation("r34", "q3", "q4", 3), relation("r45", "q4", "q5", 4), relation("r56", "q5", "q6", 5)]
    lineage_store.insert_bundle(nodes, relations)
    pack = build_context_pack("q5", lineage_store, profile_store, learning_store)
    assert [(item.id, distance) for item, distance in pack.ancestors] == [("q4", 1), ("q3", 2), ("q2", 3)]
    assert [(item.id, distance) for item, distance in pack.descendants] == [("q6", 1)]
    assert [item.id for item in pack.relations] == ["r23", "r34", "r45", "r56"]


def test_pack_joins_profiles_and_learning_by_explicit_ids_only(tmp_path):
    lineage_store, profile_store, learning_store = stores(tmp_path)
    lineage_store.insert_bundle([node("q-a", 1), node("q-current", 2), node("q-next", 3)], [relation("r-a", "q-a", "q-current", 1), relation("r-next", "q-current", "q-next", 2)])
    profile_store.insert_many([profile("q-a", 1, "-a"), profile("q-current", 2, "-current"), profile("q-other", 4, "-other")])
    learning_store.insert_many([observation("obs-hit", ["q-a", "historical-x"], 1), observation("obs-miss", ["q-other"], 2)])
    pack = build_context_pack("q-current", lineage_store, profile_store, learning_store)
    assert [item.id for item in pack.profiles] == ["q-current", "q-a"]
    assert [item.id for item in pack.learning_observations] == ["obs-hit"]
    assert pack.unresolved_assumptions == (("q-current", "assumption q-current-current"), ("q-a", "assumption q-a-a"))
    assert pack.evidence_still_needed == (("q-current", "evidence q-current-current"), ("q-a", "evidence q-a-a"))
    assert pack.existing_next_questions == (("q-current", "next q-current-current?"), ("q-a", "next q-a-a?"))


def test_depth_overrides_zero_out_lineage_and_reject_negative_values(tmp_path):
    lineage_store, profile_store, learning_store = stores(tmp_path)
    lineage_store.insert_bundle([node("q-a", 1), node("q-current", 2), node("q-next", 3)], [relation("r-a", "q-a", "q-current", 1), relation("r-n", "q-current", "q-next", 2)])
    pack = build_context_pack("q-current", lineage_store, profile_store, learning_store, ancestor_depth=0, descendant_depth=0)
    assert pack.ancestors == () and pack.descendants == () and pack.relations == ()
    with pytest.raises(ValueError, match="max_depth must be a non-negative integer"):
        build_context_pack("q-current", lineage_store, profile_store, learning_store, ancestor_depth=-1)


def test_context_pack_handles_cycle_without_recursion_failure(tmp_path):
    lineage_store, profile_store, learning_store = stores(tmp_path)
    lineage_store.insert_bundle([node("q1", 1), node("q2", 2), node("q3", 3)], [relation("r12", "q1", "q2", 1), relation("r23", "q2", "q3", 2), relation("r31", "q3", "q1", 3)])
    pack = build_context_pack("q1", lineage_store, profile_store, learning_store)
    assert {item.id for item, _ in pack.ancestors} == {"q2", "q3"}
    assert {item.id for item, _ in pack.descendants} == {"q2"}


def test_markdown_rendering_has_fixed_sections_and_explicit_empty_values(tmp_path):
    lineage_store, profile_store, learning_store = stores(tmp_path)
    lineage_store.insert_node(node("q-current", 10))
    pack = build_context_pack("q-current", lineage_store, profile_store, learning_store)
    rendered = render_context_markdown(pack)
    expected_headings = ["# Question Radar Context Pack", "## CURRENT QUESTION", "## LINEAGE", "## RELATIONS", "## KNOWN PROFILES", "## LEARNING SIGNALS", "## UNRESOLVED ASSUMPTIONS", "## EVIDENCE STILL NEEDED", "## EXISTING NEXT QUESTIONS"]
    positions = [rendered.index(heading) for heading in expected_headings]
    assert positions == sorted(positions)
    assert rendered.count("none") == 7
    assert "q-current" in rendered and "Pregunta q-current?" in rendered
    assert "source: conversation" in rendered and "source_ref: corpus/chat.jsonl" in rendered
    assert rendered.endswith("\n")
    assert render_context_markdown(pack) == rendered


def test_markdown_renders_lineage_relations_profiles_and_learning(tmp_path):
    lineage_store, profile_store, learning_store = stores(tmp_path)
    lineage_store.insert_bundle([node("q-a", 1), node("q-current", 2)], [relation("r-a", "q-a", "q-current", 1)])
    profile_store.insert(profile("q-current", 2))
    learning_store.insert(observation("obs-1", ["q-a"], 1))
    rendered = render_context_markdown(build_context_pack("q-current", lineage_store, profile_store, learning_store))
    assert "q-a (ancestor, distance=1)" in rendered
    assert "q-a --follows_from--> q-current" in rendered
    assert "q-current | epistemological_meta | ready_to_investigate" in rendered
    assert "obs-1 | concept-obs-1 | possible_gap | low" in rendered


def test_json_rendering_is_stable_and_has_exact_contract(tmp_path):
    lineage_store, profile_store, learning_store = stores(tmp_path)
    lineage_store.insert_bundle([node("q-a", 1), node("q-current", 2)], [relation("r-a", "q-a", "q-current", 1)])
    profile_store.insert(profile("q-current", 2))
    pack = build_context_pack("q-current", lineage_store, profile_store, learning_store)
    rendered = render_context_json(pack)
    payload = json.loads(rendered)
    assert set(payload) == {"context_version", "current_question", "ancestors", "descendants", "relations", "profiles", "learning_observations", "unresolved_assumptions", "evidence_still_needed", "existing_next_questions"}
    assert payload["context_version"] == "v0.4"
    assert payload["ancestors"][0]["distance"] == 1 and payload["ancestors"][0]["id"] == "q-a"
    assert payload["unresolved_assumptions"] == [{"question_id": "q-current", "text": "assumption q-current"}]
    assert "Pregunta q-current?" in rendered and "\\u00bf" not in rendered
    assert rendered.endswith("\n")
    assert render_context_json(pack) == rendered
