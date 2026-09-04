import json

from question_radar.decisions import (
    DECISION_STATES,
    RECOMMENDED_DO_NOW_LIMIT,
    InvestigationDecision,
)
from question_radar.lineage import QuestionNode


def _gate_lines(item: InvestigationDecision) -> list[str]:
    pairs = (
        ("goal_alignment", "current goal alignment"),
        ("external_signal", "external signal"),
        ("testable_now", "testable now"),
        ("leverage", "leverage"),
    )
    return [
        f"{'✓' if getattr(item, field) else '✗'} {label}"
        for field, label in pairs
    ]


def render_decision_json(node: QuestionNode, item: InvestigationDecision) -> str:
    return (
        json.dumps(
            {
                "automatic_decision": False,
                "current_decision": item.to_dict(),
                "decision_version": "v0.9",
                "question": node.to_dict(),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def render_decision_markdown(node: QuestionNode, item: InvestigationDecision) -> str:
    lines = [
        "# Investigation Decision v0.9",
        "",
        f"Question: {node.question}",
        f"Question id: {node.id}",
        "",
        f"Current decision: {item.decision}",
        f"Decision: {item.id}",
        "",
        "Why:",
        item.rationale,
    ]
    if item.next_test is not None:
        lines += ["", "Next test:", item.next_test]
    if item.resume_when is not None:
        lines += ["", "Resume when:", item.resume_when]
    if item.kill_condition is not None:
        lines += ["", "Kill condition:", item.kill_condition]
    lines += ["", "Gates:", *_gate_lines(item)]
    if item.decision == "PARKED":
        lines += ["", "No action is currently requested."]
    lines += [
        "",
        "Operator decision recorded; no automatic prioritization was performed.",
    ]
    return "\n".join(lines) + "\n"


def render_history_json(
    node: QuestionNode, decisions: list[InvestigationDecision]
) -> str:
    return (
        json.dumps(
            {
                "automatic_decision": False,
                "decision_version": "v0.9",
                "question": node.to_dict(),
                "history": [item.to_dict() for item in decisions],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def render_history_markdown(
    node: QuestionNode, decisions: list[InvestigationDecision]
) -> str:
    lines = [
        "# Investigation Decision History v0.9",
        "",
        f"Question: {node.question}",
        "",
    ]
    for item in decisions:
        lines += [
            f"## {item.id} — {item.decision}",
            f"created_at: {item.created_at}",
            f"supersedes: {item.supersedes_decision_id}",
            f"rationale: {item.rationale}",
            "",
        ]
    lines += ["History is append-only; no automatic prioritization was performed."]
    return "\n".join(lines) + "\n"


def _active_projection(
    entries: list[tuple[QuestionNode, InvestigationDecision]],
) -> tuple[dict[str, int], list[dict], str | None]:
    counts = {state: 0 for state in DECISION_STATES}
    for _, item in entries:
        counts[item.decision] += 1
    active = [
        {"question": node.to_dict(), "decision": item.to_dict()}
        for node, item in entries
        if item.decision in {"DO_NOW", "RESEARCH"}
    ]
    warning = None
    if counts["DO_NOW"] > RECOMMENDED_DO_NOW_LIMIT:
        warning = (
            f"WARNING: {counts['DO_NOW']} investigations are marked DO_NOW. "
            f"Recommended operating limit: {RECOMMENDED_DO_NOW_LIMIT}. "
            "No decision was changed automatically."
        )
    return counts, active, warning


def render_active_json(
    entries: list[tuple[QuestionNode, InvestigationDecision]],
) -> str:
    counts, active, warning = _active_projection(entries)
    return (
        json.dumps(
            {
                "active": active,
                "automatic_decision": False,
                "counts": counts,
                "decision_version": "v0.9",
                "recommended_do_now_limit": RECOMMENDED_DO_NOW_LIMIT,
                "wip_warning": warning,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def render_active_markdown(
    entries: list[tuple[QuestionNode, InvestigationDecision]],
) -> str:
    counts, active, warning = _active_projection(entries)
    lines = [
        "# Active Investigation Decisions v0.9",
        "",
        f"DO_NOW: {counts['DO_NOW']}",
        f"RESEARCH: {counts['RESEARCH']}",
        f"PARKED: {counts['PARKED']}",
        f"KILLED: {counts['KILLED']}",
        "",
        "## Active",
    ]
    if active:
        for item in active:
            lines.append(
                f"- {item['decision']['decision']} — {item['question']['question']} "
                f"({item['decision']['id']})"
            )
    else:
        lines.append("None.")
    if warning is not None:
        lines += ["", warning]
    lines += ["", "No decision was changed automatically."]
    return "\n".join(lines) + "\n"
