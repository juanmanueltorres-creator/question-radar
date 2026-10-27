from question_radar.ui_related import select_related_questions


def hit(id, count, coverage):
    return {
        "entry": {"id": id, "question": f"question {id}"},
        "matched_token_count": count,
        "query_coverage": coverage,
        "matched_query_tokens": ["educacion", "preguntas"][:count],
    }


def test_one_generic_token_does_not_surface_as_related():
    pack = {"results": [hit("weak", 1, 0.5), hit("strong", 2, 0.5)]}
    assert [x["id"] for x in select_related_questions(pack)] == ["strong"]


def test_low_query_coverage_is_excluded():
    assert select_related_questions({"results": [hit("weak", 2, 0.2)]}) == []


def test_empty_and_limit_preserve_frozen_retrieval_results():
    pack = {"results": [hit("a", 2, 0.5), hit("b", 3, 0.75)]}
    before = repr(pack)
    assert [r["id"] for r in select_related_questions(pack, max_results=1)] == ["a"]
    assert repr(pack) == before
    assert select_related_questions({"results": []}) == []
