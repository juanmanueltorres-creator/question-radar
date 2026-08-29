import pytest

from question_radar.scoring import normalized_score


def dims(value: int) -> dict[str, int]:
    return {
        "clarity": value,
        "depth": value,
        "investigability": value,
        "assumption_challenge": value,
        "connections": value,
    }


def test_zero_dimensions_return_zero():
    assert normalized_score(dims(0)) == 0


def test_max_dimensions_return_100():
    assert normalized_score(dims(5)) == 100


def test_mixed_dimensions_normalize_deterministically():
    values = {
        "clarity": 4,
        "depth": 4,
        "investigability": 5,
        "assumption_challenge": 5,
        "connections": 5,
    }
    assert normalized_score(values) == 92


@pytest.mark.parametrize("bad_value", [-1, 6, 2.5, True, "5"])
def test_invalid_dimension_is_rejected(bad_value):
    values = dims(3)
    values["clarity"] = bad_value

    with pytest.raises(ValueError, match="clarity"):
        normalized_score(values)
