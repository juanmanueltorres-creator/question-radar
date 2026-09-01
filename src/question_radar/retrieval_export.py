from __future__ import annotations

import json

from question_radar.retrieval import RetrievalPack


_REVIEW_BOUNDARY = (
    "No semantic relation, lineage edge, or master promotion was created."
)


def _entry_payload(result) -> dict:
    return {
        "entry": {
            "id": result.entry.id,
            "question": result.entry.question,
            "source_version": result.entry.source_version,
            "source_kind": result.entry.source_kind,
            "provenance": result.entry.provenance,
        },
        "bm25_score": result.bm25_score,
        "jaccard_score": result.jaccard_score,
        "matched_query_tokens": list(result.matched_query_tokens),
        "residual_query_tokens": list(result.residual_query_tokens),
        "token_contributions": [
            {
                "token": contribution.token,
                "document_frequency": contribution.document_frequency,
                "term_frequency": contribution.term_frequency,
                "contribution": contribution.contribution,
            }
            for contribution in result.token_contributions
        ],
    }


def retrieval_pack_payload(pack: RetrievalPack) -> dict:
    return {
        "retrieval_version": pack.retrieval_version,
        "candidate_question": pack.candidate_question,
        "corpus_size": pack.corpus_size,
        "results": [_entry_payload(result) for result in pack.results],
        "review_required": pack.review_required,
        "review_boundary": _REVIEW_BOUNDARY,
    }


def render_retrieval_json(pack: RetrievalPack) -> str:
    return json.dumps(
        retrieval_pack_payload(pack),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def render_retrieval_markdown(pack: RetrievalPack) -> str:
    lines = [
        "# Unified Candidate Retrieval v0.6",
        "",
        "## Candidate",
        pack.candidate_question,
        "",
        f"Corpus size: {pack.corpus_size}",
        "",
        "## Retrieved Prior Questions",
    ]

    if not pack.results:
        lines.append("none")
    else:
        for index, result in enumerate(pack.results, start=1):
            matched = ", ".join(result.matched_query_tokens) or "none"
            residual = ", ".join(result.residual_query_tokens) or "none"
            provenance = result.entry.provenance or "none"
            lines.extend(
                [
                    f"### {index}. {result.entry.id}",
                    result.entry.question,
                    f"- source: {result.entry.source_version}/{result.entry.source_kind}",
                    f"- provenance: {provenance}",
                    f"- bm25_score: {result.bm25_score:.6f}",
                    f"- jaccard_score: {result.jaccard_score:.6f}",
                    f"- matched_query_tokens: {matched}",
                    f"- residual_query_tokens: {residual}",
                ]
            )
            if result.token_contributions:
                lines.append("- token_contributions:")
                for contribution in result.token_contributions:
                    lines.append(
                        "  - "
                        f"{contribution.token}: contribution={contribution.contribution:.6f}, "
                        f"df={contribution.document_frequency}, tf={contribution.term_frequency}"
                    )
            else:
                lines.append("- token_contributions: none")
            lines.append("")

    lines.extend(
        [
            "## Review Boundary",
            _REVIEW_BOUNDARY,
        ]
    )
    return "\n".join(lines) + "\n"
