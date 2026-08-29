from collections.abc import Mapping

DIMENSION_FIELDS = (
    "clarity",
    "depth",
    "investigability",
    "assumption_challenge",
    "connections",
)


def normalized_score(dimensions: Mapping[str, int]) -> int:
    missing = [name for name in DIMENSION_FIELDS if name not in dimensions]
    if missing:
        raise ValueError(f"missing dimensions: {', '.join(missing)}")

    values: list[int] = []
    for name in DIMENSION_FIELDS:
        value = dimensions[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer from 0 to 5")
        if not 0 <= value <= 5:
            raise ValueError(f"{name} must be between 0 and 5")
        values.append(value)

    return int(round(sum(values) / 25 * 100))
