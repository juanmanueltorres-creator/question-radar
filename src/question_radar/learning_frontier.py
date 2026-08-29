from question_radar.learning import LearningObservation


_SECTIONS = (
    ("recurring_gap", "RECURRING SIGNALS"),
    ("consolidating", "CONSOLIDATING"),
    ("applied", "APPLIED"),
    ("possible_gap", "EMERGING FRONTIER"),
    ("no_longer_observed", "NO LONGER OBSERVED"),
)


def render_learning_frontier(
    observations: list[LearningObservation],
) -> str:
    lines: list[str] = []
    for state, heading in _SECTIONS:
        lines.append(heading)
        matching = sorted(
            (item for item in observations if item.state == state),
            key=lambda item: (item.concept, item.id),
        )
        if not matching:
            lines.append("(none)")
        else:
            for item in matching:
                evidence = ", ".join(item.evidence_question_ids)
                lines.append(
                    f"- {item.concept} "
                    f"[{item.gap_type}; {item.confidence}; "
                    f"evidence={len(item.evidence_question_ids)}] "
                    f"{evidence}"
                )
        lines.append("")
    return "\n".join(lines).rstrip()
