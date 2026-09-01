from dataclasses import dataclass
import json

from question_radar.learning import LearningObservation
from question_radar.learning_storage import LearningObservationStore
from question_radar.lineage import QuestionNode, QuestionRelation
from question_radar.lineage_graph import ancestors, descendants
from question_radar.lineage_storage import QuestionLineageStore
from question_radar.profile_storage import QuestionProfileStore
from question_radar.profiles import QuestionProfile


@dataclass(frozen=True, slots=True)
class ContextPack:
    context_version: str
    current_question: QuestionNode
    ancestors: tuple[tuple[QuestionNode, int], ...]
    descendants: tuple[tuple[QuestionNode, int], ...]
    relations: tuple[QuestionRelation, ...]
    profiles: tuple[QuestionProfile, ...]
    learning_observations: tuple[LearningObservation, ...]
    unresolved_assumptions: tuple[tuple[str, str], ...]
    evidence_still_needed: tuple[tuple[str, str], ...]
    existing_next_questions: tuple[tuple[str, str], ...]


def build_context_pack(
    current_question_id: str,
    lineage_store: QuestionLineageStore,
    profile_store: QuestionProfileStore,
    learning_store: LearningObservationStore,
    ancestor_depth: int = 3,
    descendant_depth: int = 1,
) -> ContextPack:
    current = lineage_store.get_node(current_question_id)
    if current is None:
        raise ValueError(f"question node not found: {current_question_id}")

    nodes = lineage_store.list_nodes()
    relations = lineage_store.list_relations()
    ancestor_items = tuple(ancestors(current_question_id, nodes, relations, ancestor_depth))
    descendant_items = tuple(descendants(current_question_id, nodes, relations, descendant_depth))

    ordered_ids: list[str] = []
    for node_id in [current_question_id, *(item.id for item, _ in ancestor_items), *(item.id for item, _ in descendant_items)]:
        if node_id not in ordered_ids:
            ordered_ids.append(node_id)
    selected_ids = set(ordered_ids)

    selected_relations = tuple(
        relation
        for relation in relations
        if relation.source_question_id in selected_ids
        and relation.target_question_id in selected_ids
    )

    profiles_by_id = {profile.id: profile for profile in profile_store.list_all()}
    selected_profiles = tuple(profiles_by_id[node_id] for node_id in ordered_ids if node_id in profiles_by_id)
    selected_learning = tuple(
        sorted(
            (observation for observation in learning_store.list_all() if selected_ids.intersection(observation.evidence_question_ids)),
            key=lambda observation: (observation.created_at, observation.id),
        )
    )

    return ContextPack(
        context_version="v0.4",
        current_question=current,
        ancestors=ancestor_items,
        descendants=descendant_items,
        relations=selected_relations,
        profiles=selected_profiles,
        learning_observations=selected_learning,
        unresolved_assumptions=tuple((profile.id, profile.assumptions) for profile in selected_profiles),
        evidence_still_needed=tuple((profile.id, profile.evidence_required) for profile in selected_profiles),
        existing_next_questions=tuple((profile.id, profile.next_question) for profile in selected_profiles),
    )


def render_context_markdown(pack: ContextPack) -> str:
    current = pack.current_question
    lines = [
        "# Question Radar Context Pack", "", "## CURRENT QUESTION",
        f"id: {current.id}", f"question: {current.question}", f"source: {current.source}",
        f"source_ref: {current.source_ref if current.source_ref is not None else 'none'}",
        f"created_at: {current.created_at}", "", "## LINEAGE",
    ]
    lineage_lines = [f"- {node.id} (ancestor, distance={distance}): {node.question}" for node, distance in pack.ancestors] + [f"- {node.id} (descendant, distance={distance}): {node.question}" for node, distance in pack.descendants]
    lines.extend(lineage_lines or ["none"])
    lines.extend(["", "## RELATIONS"])
    lines.extend([f"- {relation.source_question_id} --{relation.relation_type}--> {relation.target_question_id}" for relation in pack.relations] or ["none"])
    lines.extend(["", "## KNOWN PROFILES"])
    lines.extend([f"- {profile.id} | {profile.question_type} | {profile.readiness} | formulation_score={profile.formulation_score}" for profile in pack.profiles] or ["none"])
    lines.extend(["", "## LEARNING SIGNALS"])
    lines.extend([f"- {observation.id} | {observation.concept} | {observation.state} | {observation.confidence}" for observation in pack.learning_observations] or ["none"])
    lines.extend(["", "## UNRESOLVED ASSUMPTIONS"])
    lines.extend([f"- {question_id}: {text}" for question_id, text in pack.unresolved_assumptions] or ["none"])
    lines.extend(["", "## EVIDENCE STILL NEEDED"])
    lines.extend([f"- {question_id}: {text}" for question_id, text in pack.evidence_still_needed] or ["none"])
    lines.extend(["", "## EXISTING NEXT QUESTIONS"])
    lines.extend([f"- {question_id}: {text}" for question_id, text in pack.existing_next_questions] or ["none"])
    return "\n".join(lines) + "\n"


def render_context_json(pack: ContextPack) -> str:
    def graph_node(node_with_distance: tuple[QuestionNode, int]) -> dict:
        node, distance = node_with_distance
        return {**node.to_dict(), "distance": distance}

    payload = {
        "context_version": pack.context_version,
        "current_question": pack.current_question.to_dict(),
        "ancestors": [graph_node(item) for item in pack.ancestors],
        "descendants": [graph_node(item) for item in pack.descendants],
        "relations": [relation.to_dict() for relation in pack.relations],
        "profiles": [profile.to_dict() for profile in pack.profiles],
        "learning_observations": [observation.to_dict() for observation in pack.learning_observations],
        "unresolved_assumptions": [{"question_id": question_id, "text": text} for question_id, text in pack.unresolved_assumptions],
        "evidence_still_needed": [{"question_id": question_id, "text": text} for question_id, text in pack.evidence_still_needed],
        "existing_next_questions": [{"question_id": question_id, "text": text} for question_id, text in pack.existing_next_questions],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
