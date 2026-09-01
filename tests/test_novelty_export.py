import json

import pytest

from question_radar.novelty import CandidateQuestion, cluster_candidates
from question_radar.novelty_export import load_candidate_questions


def test_candidate_jsonl_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "candidates.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps({"id": "q1", "question": "¿Qué recordar?"}),
                json.dumps({"id": "q1", "question": "¿Qué olvidar?"}),
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate candidate id: q1"):
        load_candidate_questions(path)


def test_candidate_jsonl_rejects_unknown_fields(tmp_path):
    path = tmp_path / "candidates.jsonl"
    path.write_text(
        json.dumps({"id": "q1", "question": "¿Qué recordar?", "extra": True}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown fields"):
        load_candidate_questions(path)


def test_candidate_jsonl_rejects_blank_id_and_question(tmp_path):
    blank_id = tmp_path / "blank-id.jsonl"
    blank_id.write_text(json.dumps({"id": " ", "question": "¿Qué recordar?"}), encoding="utf-8")
    with pytest.raises(ValueError, match="candidate id must be a non-empty string"):
        load_candidate_questions(blank_id)

    blank_question = tmp_path / "blank-question.jsonl"
    blank_question.write_text(json.dumps({"id": "q1", "question": " "}), encoding="utf-8")
    with pytest.raises(ValueError, match="candidate question must be a non-empty string"):
        load_candidate_questions(blank_question)


def test_related_forgetting_questions_form_possible_cluster():
    candidates = (
        CandidateQuestion(
            "q8", "¿Cómo distinguimos conocimiento válido de conocimiento obsoleto?"
        ),
        CandidateQuestion(
            "q9", "¿Puede una documentación conservar procedimientos obsoletos?"
        ),
        CandidateQuestion(
            "q25", "¿Y si olvidar prácticas anteriores ayudara a adaptarse?"
        ),
        CandidateQuestion("qx", "¿Cómo calibramos un sensor satelital?"),
    )
    clusters = cluster_candidates(candidates, threshold=0.20)
    assert any(set(cluster.question_ids) >= {"q8", "q9"} for cluster in clusters)


def test_clusters_are_deterministic_and_have_no_singletons():
    candidates = (
        CandidateQuestion("b", "memoria conocimiento organizacion"),
        CandidateQuestion("a", "memoria conocimiento institucional"),
        CandidateQuestion("z", "sensor satelital calibracion"),
    )
    clusters = cluster_candidates(candidates, threshold=0.20)
    assert [cluster.cluster_id for cluster in clusters] == sorted(
        cluster.cluster_id for cluster in clusters
    )
    assert all(len(cluster.question_ids) >= 2 for cluster in clusters)
