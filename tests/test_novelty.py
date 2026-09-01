from question_radar.lineage import QuestionNode
from question_radar.novelty import (
    build_novelty_pack,
    compare_questions,
    normalize_tokens,
)


def node(node_id: str, question: str) -> QuestionNode:
    return QuestionNode(
        id=node_id,
        question=question,
        source="corpus",
        source_ref=None,
        created_at="2026-09-01T12:00:00-03:00",
    )


def test_normalize_tokens_is_accent_insensitive_and_deterministic():
    assert normalize_tokens("¿Qué información está ACÁ?") == (
        "informacion",
        "esta",
        "aca",
    )


def test_normalize_tokens_drops_short_function_words():
    assert normalize_tokens("¿Y si la IA lo hace?") == ("hace",)


def test_identical_normalized_questions_score_one():
    evidence = compare_questions(
        "¿Cómo usamos memoria y trazabilidad?",
        "Como usamos memoria y trazabilidad",
        "q-1",
    )
    assert evidence.score == 1.0
    assert evidence.question_id == "q-1"


def test_unrelated_questions_have_low_similarity():
    evidence = compare_questions(
        "¿Qué debería recordar una organización?",
        "¿Cómo reconstruimos rocas antiguas?",
        "q-2",
    )
    assert evidence.score < 0.25


def test_neighbors_rank_by_score_then_id():
    nodes = [
        node("b", "¿Cómo usamos memoria organizacional?"),
        node("a", "¿Cómo usamos memoria institucional?"),
    ]
    pack = build_novelty_pack("¿Cómo usamos memoria?", nodes, [], limit=2)
    assert [neighbor.node.id for neighbor in pack.neighbors] == ["a", "b"]


def test_distinctive_tokens_expose_residual_mechanism():
    nodes = [node("q1", "¿Cómo usamos memoria y trazabilidad?")]
    pack = build_novelty_pack(
        "¿Qué debería recordar una organización y qué debería olvidar por obsolescencia?",
        nodes,
        [],
        limit=1,
    )
    assert "olvidar" in pack.candidate_distinctive_tokens
    assert "obsolescencia" in pack.candidate_distinctive_tokens


def test_every_pack_requires_human_review():
    pack = build_novelty_pack("¿Qué debería recordar una organización?", [], [])
    assert pack.review_required is True


def test_challenge_prompt_requires_explicit_challenge_syntax():
    nodes = [node("q1", "¿Cómo usamos memoria?")]
    ordinary = build_novelty_pack("¿Cómo mejoramos la memoria?", nodes, [])
    challenged = build_novelty_pack(
        "¿Y si olvidar fuera necesario para adaptarse?", nodes, []
    )
    assert "challenges_assumption" not in ordinary.possible_interpretations
    assert "challenges_assumption" in challenged.possible_interpretations


def test_challenge_prompt_requires_neighbor_evidence():
    pack = build_novelty_pack(
        "¿Y si olvidar fuera necesario para adaptarse?",
        [],
        [],
    )
    assert "challenges_assumption" not in pack.possible_interpretations
    assert "possible_new_branch" in pack.possible_interpretations
