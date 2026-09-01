from pathlib import Path

from question_radar.lineage import QuestionNode
from question_radar.novelty import build_novelty_pack, cluster_candidates
from question_radar.novelty_export import load_candidate_questions


BLIND_MEMORY_PATH = Path("corpus/blind-memory-2026-09-01.jsonl")


def _node(node_id: str, question: str) -> QuestionNode:
    return QuestionNode(
        id=node_id,
        question=question,
        source="corpus",
        source_ref=None,
        created_at="2026-09-01T12:00:00-03:00",
    )


def test_blind_software_bottleneck_retrieves_existing_master():
    nodes = [
        _node(
            "M-20260831-02",
            "Si construir código se vuelve barato, ¿qué pasa a ser el verdadero cuello de botella?",
        ),
        _node(
            "M-20260831-01",
            "¿Cuál es la brecha entre conocer profundamente un dominio y poder representarlo como un sistema ejecutable?",
        ),
    ]
    pack = build_novelty_pack(
        "¿Qué cambia cuando programar deja de ser el cuello de botella y el cuello de botella pasa a ser definir correctamente qué construir?",
        nodes,
        [],
        limit=2,
    )
    assert pack.neighbors[0].node.id == "M-20260831-02"


def test_blind_memory_source_is_preserved_as_25_raw_candidates():
    candidates = load_candidate_questions(BLIND_MEMORY_PATH)
    assert len(candidates) == 25
    assert candidates[0].id == "blind-memory-2026-09-01-001"
    assert candidates[-1].id == "blind-memory-2026-09-01-025"
    assert candidates[-1].question == (
        "¿Y si parte de la capacidad de una organización para adaptarse "
        "dependiera justamente de olvidar prácticas, explicaciones y decisiones anteriores?"
    )


def test_memory_benchmark_keeps_forgetting_as_residual_evidence():
    candidate = load_candidate_questions(BLIND_MEMORY_PATH)[-1]
    nodes = [
        _node(
            "memory-45",
            "¿Cómo evitamos que una organización redescubra mañana lo que alguien ya aprendió ayer?",
        ),
        _node("memory-41", "¿Cómo usamos memoria y trazabilidad?"),
    ]
    pack = build_novelty_pack(candidate.question, nodes, [], limit=2)
    assert "olvidar" in pack.candidate_distinctive_tokens
    assert pack.review_required is True


def test_real_memory_semantic_family_is_a_known_lexical_false_negative():
    candidates = load_candidate_questions(BLIND_MEMORY_PATH)
    clusters = cluster_candidates(candidates)

    # Human review connected Q8/Q9/Q10/Q25 around obsolescence and adaptive
    # forgetting, but the original strings do not share enough lexical evidence
    # for the transparent v0.5 threshold. Preserve the miss instead of rewriting
    # benchmark wording until it passes.
    assert clusters == ()
