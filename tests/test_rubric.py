import json
from pathlib import Path


_V01_HISTORICAL = '''{
  "version": "v0.1",
  "scale": {"min": 0, "max": 5},
  "dimensions": {
    "clarity": "Is the question understandable and sufficiently bounded?",
    "depth": "Does it move beyond superficial lookup toward causes, mechanisms, implications, or structure?",
    "investigability": "Can evidence, data, experiments, documents, or observations be used to address it?",
    "assumption_challenge": "Does it surface or question assumptions that may otherwise remain implicit?",
    "connections": "Does it connect concepts, scales, domains, evidence types, or prior knowledge meaningfully?"
  },
  "formula": "round(sum(dimensions) / 25 * 100)",
  "principle": "Scores questions, not people. The score is diagnostic guidance, not an authority claim."
}
'''


def test_rubric_v01_has_expected_dimensions_and_scale():
    path = Path("rubric/v0.1.json")
    rubric = json.loads(path.read_text(encoding="utf-8"))

    assert rubric["version"] == "v0.1"
    assert rubric["scale"] == {"min": 0, "max": 5}
    assert list(rubric["dimensions"]) == [
        "clarity",
        "depth",
        "investigability",
        "assumption_challenge",
        "connections",
    ]
    assert rubric["formula"] == "round(sum(dimensions) / 25 * 100)"


def test_rubric_v01_is_byte_for_byte_frozen():
    assert Path("rubric/v0.1.json").read_text(encoding="utf-8") == _V01_HISTORICAL


def test_rubric_v02_defines_profile_contract():
    rubric = json.loads(Path("rubric/v0.2.json").read_text(encoding="utf-8"))

    assert rubric["version"] == "v0.2"
    assert rubric["scale"] == {"min": 0, "max": 5}
    assert rubric["question_types"] == [
        "factual_conceptual",
        "operational_diagnostic",
        "scientific_explanatory",
        "decision_risk",
        "epistemological_meta",
        "normative_political",
        "generative_philosophical",
    ]
    assert rubric["readiness_states"] == [
        "ready_to_answer",
        "ready_to_investigate",
        "needs_context",
        "exploratory",
    ]
    assert list(rubric["formulation_dimensions"]) == [
        "clarity",
        "boundedness",
        "investigability",
        "epistemic_openness",
        "purpose_fit",
    ]
    assert list(rubric["descriptive_traits"]) == [
        "depth",
        "connections",
        "generativity",
    ]
    assert rubric["formula"] == (
        "round((clarity + boundedness + investigability + "
        "epistemic_openness + purpose_fit) / 25 * 100)"
    )
