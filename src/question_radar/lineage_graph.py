from collections import deque

from question_radar.lineage import QuestionNode, QuestionRelation, timestamp_sort_key


def ancestors(
    current_id: str,
    nodes: list[QuestionNode],
    relations: list[QuestionRelation],
    max_depth: int,
) -> list[tuple[QuestionNode, int]]:
    return _traverse(current_id, nodes, relations, max_depth, direction="incoming")


def descendants(
    current_id: str,
    nodes: list[QuestionNode],
    relations: list[QuestionRelation],
    max_depth: int,
) -> list[tuple[QuestionNode, int]]:
    return _traverse(current_id, nodes, relations, max_depth, direction="outgoing")


def _traverse(
    current_id: str,
    nodes: list[QuestionNode],
    relations: list[QuestionRelation],
    max_depth: int,
    *,
    direction: str,
) -> list[tuple[QuestionNode, int]]:
    if isinstance(max_depth, bool) or not isinstance(max_depth, int) or max_depth < 0:
        raise ValueError("max_depth must be a non-negative integer")
    if max_depth == 0:
        return []

    nodes_by_id = {node.id: node for node in nodes}
    adjacency: dict[str, list[str]] = {}
    for relation in relations:
        if direction == "incoming":
            key = relation.target_question_id
            neighbor = relation.source_question_id
        else:
            key = relation.source_question_id
            neighbor = relation.target_question_id
        adjacency.setdefault(key, []).append(neighbor)

    queue: deque[tuple[str, int]] = deque([(current_id, 0)])
    visited = {current_id}
    found: list[tuple[QuestionNode, int]] = []

    while queue:
        node_id, distance = queue.popleft()
        if distance >= max_depth:
            continue
        for neighbor_id in adjacency.get(node_id, []):
            if neighbor_id in visited:
                continue
            visited.add(neighbor_id)
            neighbor_distance = distance + 1
            node = nodes_by_id.get(neighbor_id)
            if node is not None:
                found.append((node, neighbor_distance))
                queue.append((neighbor_id, neighbor_distance))

    return sorted(
        found,
        key=lambda item: (
            item[1],
            timestamp_sort_key(item[0].created_at),
            item[0].id,
        ),
    )
