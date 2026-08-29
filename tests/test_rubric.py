import json
from pathlib import Path


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
