"""Presentation-only filter for Question Radar's lexical retrieval results.

Does not alter the frozen v0.7 retrieval algorithm or infer semantic similarity.
"""
from __future__ import annotations


def select_related_questions(retrieval: dict, *, max_results: int = 3) -> list[dict]:
    """Keep only supported multi-term lexical matches for the public UI."""
    results = retrieval.get("results", ())
    candidates = [
        item for item in results
        if item["matched_token_count"] >= 2
        and item["query_coverage"] >= 0.25
    ]
    return [
        {
            "id": item["entry"]["id"],
            "question": item["entry"]["question"],
            "coverage": item["query_coverage"],
            "matched_terms": item["matched_query_tokens"],
        }
        for item in candidates[:max_results]
    ]
