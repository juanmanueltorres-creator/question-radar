from __future__ import annotations

import json
from pathlib import Path

from question_radar.novelty import (
    CandidateQuestion,
    NoveltyPack,
    PossibleCluster,
)


_CANDIDATE_FIELDS = {"id", "question"}
_REVIEW_BOUNDARY = "No lineage relation or master promotion was created."


def load_candidate_questions(path: str | Path) -> tuple[CandidateQuestion, ...]:
    source = Path(path)
    candidates: list[CandidateQuestion] = []
    seen_ids: set[str] = set()

    try:
        lines = source.read_text(encoding="utf-8").splitlines()
    except OSError:
        raise

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"malformed JSON on line {line_number} in {source}"
            ) from exc
        if not isinstance(payload, dict):
            raise ValueError(f"candidate line {line_number} must be a JSON object")

        missing = sorted(_CANDIDATE_FIELDS - payload.keys())
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")
        unknown = sorted(payload.keys() - _CANDIDATE_FIELDS)
        if unknown:
            raise ValueError(f"unknown fields: {', '.join(unknown)}")

        candidate = CandidateQuestion(payload["id"], payload["question"])
        if candidate.id in seen_ids:
            raise ValueError(f"duplicate candidate id: {candidate.id}")
        seen_ids.add(candidate.id)
        candidates.append(candidate)

    return tuple(candidates)


def _neighbor_payload(pack: NoveltyPack) -> list[dict]:
    return [
        {
            "node": neighbor.node.to_dict(),
            "similarity": {
                "question_id": neighbor.similarity.question_id,
                "score": neighbor.similarity.score,
                "shared_tokens": list(neighbor.similarity.shared_tokens),
                "shared_bigrams": list(neighbor.similarity.shared_bigrams),
                "candidate_only_tokens": list(
                    neighbor.similarity.candidate_only_tokens
                ),
                "corpus_only_tokens": list(neighbor.similarity.corpus_only_tokens),
            },
            "lineage_degree": neighbor.lineage_degree,
        }
        for neighbor in pack.neighbors
    ]


def novelty_pack_payload(pack: NoveltyPack) -> dict:
    return {
        "novelty_version": pack.novelty_version,
        "candidate_question": pack.candidate_question,
        "neighbors": _neighbor_payload(pack),
        "candidate_distinctive_tokens": list(pack.candidate_distinctive_tokens),
        "possible_interpretations": list(pack.possible_interpretations),
        "review_required": pack.review_required,
        "review_boundary": _REVIEW_BOUNDARY,
    }


def render_novelty_json(pack: NoveltyPack) -> str:
    return json.dumps(
        novelty_pack_payload(pack),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def render_novelty_markdown(pack: NoveltyPack) -> str:
    lines = [
        "# Question Radar Novelty Pack",
        "",
        "## CANDIDATE QUESTION",
        pack.candidate_question,
        "",
        "## NEAREST CORPUS QUESTIONS",
    ]
    if pack.neighbors:
        for neighbor in pack.neighbors:
            shared = ", ".join(neighbor.similarity.shared_tokens) or "none"
            lines.append(
                f"- {neighbor.node.id} | score={neighbor.similarity.score:.6f} | "
                f"lineage_degree={neighbor.lineage_degree} | shared={shared} | "
                f"{neighbor.node.question}"
            )
    else:
        lines.append("none")

    lines.extend(["", "## DISTINCTIVE TOKENS"])
    lines.append(", ".join(pack.candidate_distinctive_tokens) or "none")
    lines.extend(["", "## POSSIBLE INTERPRETATIONS"])
    lines.extend(
        [f"- {item}" for item in pack.possible_interpretations] or ["none"]
    )
    lines.extend(["", "## REVIEW BOUNDARY", _REVIEW_BOUNDARY])
    return "\n".join(lines) + "\n"


def _cluster_payload(cluster: PossibleCluster) -> dict:
    return {
        "cluster_id": cluster.cluster_id,
        "question_ids": list(cluster.question_ids),
        "shared_tokens": list(cluster.shared_tokens),
    }


def render_batch_json(
    candidates: tuple[CandidateQuestion, ...],
    packs: tuple[NoveltyPack, ...],
    clusters: tuple[PossibleCluster, ...],
) -> str:
    payload = {
        "novelty_version": "v0.5",
        "candidates": [
            {"id": candidate.id, "question": candidate.question}
            for candidate in candidates
        ],
        "packs": [novelty_pack_payload(pack) for pack in packs],
        "possible_clusters": [_cluster_payload(cluster) for cluster in clusters],
        "review_required": True,
        "review_boundary": _REVIEW_BOUNDARY,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_batch_markdown(
    candidates: tuple[CandidateQuestion, ...],
    packs: tuple[NoveltyPack, ...],
    clusters: tuple[PossibleCluster, ...],
) -> str:
    lines = ["# Question Radar Novelty Batch", "", "## CANDIDATES"]
    lines.extend(
        [f"- {candidate.id}: {candidate.question}" for candidate in candidates]
        or ["none"]
    )
    lines.extend(["", "## POSSIBLE CLUSTERS"])
    if clusters:
        for cluster in clusters:
            shared = ", ".join(cluster.shared_tokens) or "none"
            lines.append(
                f"- {cluster.cluster_id} | questions={','.join(cluster.question_ids)} "
                f"| shared={shared}"
            )
    else:
        lines.append("none")
    lines.extend(["", "## CORPUS-RELATIVE PACKS"])
    for candidate, pack in zip(candidates, packs):
        nearest = pack.neighbors[0].node.id if pack.neighbors else "none"
        lines.append(
            f"- {candidate.id} | nearest={nearest} | "
            f"distinctive={','.join(pack.candidate_distinctive_tokens) or 'none'}"
        )
    if not packs:
        lines.append("none")
    lines.extend(["", "## REVIEW BOUNDARY", _REVIEW_BOUNDARY])
    return "\n".join(lines) + "\n"
