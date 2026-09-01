from question_radar.lineage import QuestionNode
from question_radar.novelty import CandidateQuestion, build_novelty_pack, cluster_candidates


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
        _node("M-20260831-02", "Si construir código se vuelve barato, ¿qué pasa a ser el verdadero cuello de botella?"),
        _node("M-20260831-01", "¿Cuál es la brecha entre conocer profundamente un dominio y poder representarlo como un sistema ejecutable?"),
    ]
    pack = build_novelty_pack(
        "¿Qué cambia cuando programar deja de ser el cuello de botella y el cuello de botella pasa a ser definir correctamente qué construir?",
        nodes,
        [],
        limit=2,
    )
    assert pack.neighbors[0].node.id == "M-20260831-02"


def test_memory_benchmark_keeps_forgetting_as_residual_evidence():
    nodes = [
        _node("memory-45", "¿Cómo evitamos que una organización redescubra mañana lo que alguien ya aprendió ayer?"),
        _node("memory-41", "¿Cómo usamos memoria y trazabilidad?"),
    ]
    pack = build_novelty_pack(
        "¿Y si parte de la capacidad de una organización para adaptarse dependiera justamente de olvidar prácticas y decisiones anteriores?",
        nodes,
        [],
        limit=2,
    )
    assert "olvidar" in pack.candidate_distinctive_tokens
    assert pack.review_required is True


def test_memory_batch_surfaces_a_possible_cluster_without_promotion():
    candidates = (
        CandidateQuestion("q8", "¿Cómo distinguimos conocimiento válido de conocimiento obsoleto?"),
        CandidateQuestion("q9", "¿Puede documentación conservar conocimiento obsoleto?"),
        CandidateQuestion("q10", "¿Qué información conviene conservar y cuál olvidar?"),
        CandidateQuestion("q25", "¿Y si olvidar prácticas anteriores ayudara a adaptarse?"),
    )
    clusters = cluster_candidates(candidates, threshold=0.10)
    assert any(len(cluster.question_ids) >= 2 for cluster in clusters)
