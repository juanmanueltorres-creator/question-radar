# Question Lineage v0.4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit, versioned question-lineage graph and deterministic Context Pack output without changing Question Radar v0.1, v0.2, or v0.3 contracts.

**Architecture:** Add five focused v0.4 modules: immutable domain contracts, SQLite persistence, mixed-JSONL import, pure bounded graph traversal, and derived Context Pack rendering. Extend the existing CLI with a `lineage` namespace; join v0.4 nodes to v0.2 profiles and v0.3 learning observations by stable question IDs only at Context Pack build time.

**Tech Stack:** Python 3.11+, standard library (`dataclasses`, `datetime`, `json`, `sqlite3`, `argparse`, `pathlib`, collections), pytest 8.x for development. No runtime dependencies, graph libraries, external APIs, or LLM calls.

**Spec:** `docs/superpowers/specs/2026-08-29-question-lineage-v0.4-design.md`

## Global Constraints

- Python requirement remains `>=3.11`.
- Runtime `dependencies = []` remains unchanged.
- Existing v0.1 `QuestionEvaluation`, v0.2 `QuestionProfile`, and v0.3 `LearningObservation` contracts remain unchanged.
- No automatic migration of historical SQLite databases.
- `QuestionNode` has exactly: `id`, `question`, `source`, `source_ref`, `created_at`.
- `QuestionRelation` has exactly: `id`, `source_question_id`, `target_question_id`, `relation_type`, `created_at`.
- Source vocabulary is exactly: `manual`, `conversation`, `corpus`, `external`.
- Relation vocabulary is exactly: `refines`, `decomposes`, `generalizes`, `operationalizes`, `challenges_assumption`, `contrasts`, `follows_from`.
- Graph cycles are valid; self-relations are invalid.
- Imports are explicit, fail-fast, and atomic.
- Context Packs are derived and never persisted.
- Context Pack defaults are `ancestors=3`, `descendants=1`, `format=markdown`.
- Context Pack construction makes no new epistemic inference.
- Existing rubric Git blob SHAs must remain unchanged: `rubric/v0.1.json = cf769869a8af8cbc34abbcae3381100f78dae9ac`; `rubric/v0.2.json = 1b4d3b556b69603217db1c0c67b5b8c11f8fb226`.
- The 170 pre-v0.4 tests must remain green throughout implementation.
- No GitHub Actions claim is introduced; verification remains accurately described as local/test-suite verification unless a separately approved workflow is added.

---

## File Map

### New production files

- `src/question_radar/lineage.py` — v0.4 immutable domain contracts and closed vocabularies.
- `src/question_radar/lineage_storage.py` — v0.4 SQLite schemas, CRUD, referential integrity, and atomic bundle insertion.
- `src/question_radar/lineage_export.py` — mixed JSONL parsing and `record_type` dispatch.
- `src/question_radar/lineage_graph.py` — pure bounded ancestor/descendant traversal with cycle protection.
- `src/question_radar/context_pack.py` — derived Context Pack assembly plus deterministic Markdown/JSON rendering.

### Modified production files

- `src/question_radar/cli.py` — add the `lineage` command namespace and handlers; preserve all existing commands.
- `README.md` — document v0.4, CLI examples, Context Pack behavior, and update the verified test count only after the final full-suite run.

### New data

- `corpus/question-lineage-v0.4.jsonl` — explicit nodes for the 12 historical chat questions plus manually reviewed relations.

### New tests

- `tests/test_lineage.py`
- `tests/test_lineage_storage.py`
- `tests/test_lineage_export.py`
- `tests/test_lineage_graph.py`
- `tests/test_context_pack.py`
- `tests/test_lineage_cli.py`
- `tests/test_lineage_calibration_v04.py`
- `tests/test_lineage_e2e.py`

---

### Task 1: Define strict v0.4 domain contracts

**Files:**
- Create: `src/question_radar/lineage.py`
- Test: `tests/test_lineage.py`

**Interfaces:**
- Produces: `SOURCE_TYPES: tuple[str, ...]`.
- Produces: `RELATION_TYPES: tuple[str, ...]`.
- Produces: `QuestionNode.from_dict(payload: dict[str, Any]) -> QuestionNode`.
- Produces: `QuestionNode.to_dict() -> dict[str, Any]`.
- Produces: `QuestionRelation.from_dict(payload: dict[str, Any]) -> QuestionRelation`.
- Produces: `QuestionRelation.to_dict() -> dict[str, Any]`.
- Consumed by: Tasks 2, 3, 4, 5, 6, and 7.

- [ ] **Step 1: Write failing tests for `QuestionNode` happy path and closed source vocabulary**

```python
import pytest

from question_radar.lineage import SOURCE_TYPES, QuestionNode


def node_payload(**overrides):
    payload = {
        "id": "q-001",
        "question": "¿Qué evidencia necesitamos?",
        "source": "conversation",
        "source_ref": "corpus/example.jsonl",
        "created_at": "2026-08-29T18:29:00-03:00",
    }
    payload.update(overrides)
    return payload


def test_question_node_round_trip():
    node = QuestionNode.from_dict(node_payload())
    assert node.to_dict() == node_payload()


@pytest.mark.parametrize("source", ("manual", "conversation", "corpus", "external"))
def test_question_node_accepts_all_source_types(source):
    assert QuestionNode.from_dict(node_payload(source=source)).source == source


def test_source_types_are_frozen_v04_vocabulary():
    assert SOURCE_TYPES == ("manual", "conversation", "corpus", "external")
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
pytest tests/test_lineage.py -v
```

Expected: collection/import failure because `question_radar.lineage` does not exist.

- [ ] **Step 3: Add failing validation tests for unknown/missing fields, timestamps, nullable provenance, and immutable original wording**

Add tests that assert:

```python
with pytest.raises(ValueError, match="unknown fields"):
    QuestionNode.from_dict(node_payload(extra="x"))

with pytest.raises(ValueError, match="missing required fields"):
    payload = node_payload(); payload.pop("question")
    QuestionNode.from_dict(payload)

with pytest.raises(ValueError, match="source must be one of"):
    QuestionNode.from_dict(node_payload(source="chatgpt_memory"))

with pytest.raises(ValueError, match="timezone-aware"):
    QuestionNode.from_dict(node_payload(created_at="2026-08-29T18:29:00"))

assert QuestionNode.from_dict(node_payload(source_ref=None)).source_ref is None
assert QuestionNode.from_dict(node_payload(question="  original wording  ")).question == "original wording"
```

Also reject blank `id`, blank `question`, and blank-string `source_ref`.

- [ ] **Step 4: Implement the minimal `QuestionNode` contract**

Use an immutable dataclass:

```python
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

SOURCE_TYPES = ("manual", "conversation", "corpus", "external")

@dataclass(frozen=True, slots=True)
class QuestionNode:
    id: str
    question: str
    source: str
    source_ref: str | None
    created_at: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "QuestionNode":
        ...

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

Implement strict exact-field validation, outer whitespace trimming for text, `source_ref` nullable-or-non-empty validation, closed-source validation, and timezone-aware ISO timestamp validation using the same `datetime.fromisoformat(value.replace("Z", "+00:00"))` convention already used by v0.2/v0.3.

- [ ] **Step 5: Add failing `QuestionRelation` tests**

```python
from question_radar.lineage import RELATION_TYPES, QuestionRelation


def relation_payload(**overrides):
    payload = {
        "id": "rel-001-002",
        "source_question_id": "q-001",
        "target_question_id": "q-002",
        "relation_type": "refines",
        "created_at": "2026-08-29T18:30:00-03:00",
    }
    payload.update(overrides)
    return payload


def test_relation_types_are_frozen_v04_vocabulary():
    assert RELATION_TYPES == (
        "refines",
        "decomposes",
        "generalizes",
        "operationalizes",
        "challenges_assumption",
        "contrasts",
        "follows_from",
    )


@pytest.mark.parametrize("relation_type", RELATION_TYPES)
def test_relation_accepts_every_v04_type(relation_type):
    relation = QuestionRelation.from_dict(relation_payload(relation_type=relation_type))
    assert relation.relation_type == relation_type


def test_relation_rejects_self_reference():
    with pytest.raises(ValueError, match="same question"):
        QuestionRelation.from_dict(
            relation_payload(source_question_id="q-001", target_question_id="q-001")
        )
```

Also test missing/unknown fields, blank endpoint IDs, invalid relation type, and naive timestamp.

- [ ] **Step 6: Implement `QuestionRelation` and make all model tests GREEN**

Use:

```python
RELATION_TYPES = (
    "refines",
    "decomposes",
    "generalizes",
    "operationalizes",
    "challenges_assumption",
    "contrasts",
    "follows_from",
)

@dataclass(frozen=True, slots=True)
class QuestionRelation:
    id: str
    source_question_id: str
    target_question_id: str
    relation_type: str
    created_at: str
```

Run:

```bash
pytest tests/test_lineage.py -v
pytest -q
```

Expected: new model tests pass and all historical tests remain green.

- [ ] **Step 7: Commit Task 1**

```bash
git add src/question_radar/lineage.py tests/test_lineage.py
git commit -m "feat: add Question Lineage v0.4 contracts"
```

---

### Task 2: Add normalized SQLite lineage storage and atomic bundle insertion

**Files:**
- Create: `src/question_radar/lineage_storage.py`
- Test: `tests/test_lineage_storage.py`

**Interfaces:**
- Consumes: `QuestionNode`, `QuestionRelation` from Task 1.
- Produces: `QuestionLineageStore(db_path: str | Path)`.
- Produces: `insert_node(node: QuestionNode) -> None`.
- Produces: `insert_relation(relation: QuestionRelation) -> None`.
- Produces: `insert_bundle(nodes: list[QuestionNode], relations: list[QuestionRelation]) -> None`.
- Produces: `get_node(node_id: str) -> QuestionNode | None`.
- Produces: `list_nodes() -> list[QuestionNode]`.
- Produces: `get_relation(relation_id: str) -> QuestionRelation | None`.
- Produces: `list_relations(question_id: str | None = None) -> list[QuestionRelation]`.
- Consumed by: Tasks 3, 5, 6, 7, and 8.

- [ ] **Step 1: Write RED tests for schema-backed node CRUD and deterministic ordering**

Create two nodes out of insertion order and assert:

```python
store.insert_node(node_b)
store.insert_node(node_a)
assert [node.id for node in store.list_nodes()] == ["q-a", "q-b"]
assert store.get_node("q-a") == node_a
assert store.get_node("missing") is None
```

Use different `created_at` values so expected order is explicitly `created_at ASC, id ASC`.

- [ ] **Step 2: Run RED storage test**

```bash
pytest tests/test_lineage_storage.py -v
```

Expected: import failure because `lineage_storage.py` does not exist.

- [ ] **Step 3: Implement the two v0.4 schemas and connection helper**

Create:

```sql
CREATE TABLE IF NOT EXISTS question_nodes_v04 (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('manual','conversation','corpus','external')),
    source_ref TEXT,
    created_at TEXT NOT NULL
)
```

and:

```sql
CREATE TABLE IF NOT EXISTS question_relations_v04 (
    id TEXT PRIMARY KEY,
    source_question_id TEXT NOT NULL,
    target_question_id TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK (
        relation_type IN (
            'refines','decomposes','generalizes','operationalizes',
            'challenges_assumption','contrasts','follows_from'
        )
    ),
    created_at TEXT NOT NULL,
    UNIQUE (source_question_id, target_question_id, relation_type),
    CHECK (source_question_id <> target_question_id),
    FOREIGN KEY (source_question_id) REFERENCES question_nodes_v04(id),
    FOREIGN KEY (target_question_id) REFERENCES question_nodes_v04(id)
)
```

Every connection must execute:

```python
connection.execute("PRAGMA foreign_keys = ON")
connection.row_factory = sqlite3.Row
```

- [ ] **Step 4: Add RED tests for relation integrity**

Test:

```python
store.insert_node(node_a)
store.insert_node(node_b)
store.insert_relation(relation_ab)
assert store.get_relation(relation_ab.id) == relation_ab
```

Then assert `ValueError` for:

- unknown source endpoint;
- unknown target endpoint;
- duplicate relation ID;
- duplicate `(source, target, relation_type)` under a different relation ID;
- a direct SQL self-relation attempt, proving SQLite defense in depth.

- [ ] **Step 5: Implement relation CRUD using `insert_bundle` as the integrity path**

`insert_node` may delegate to `insert_bundle([node], [])` and `insert_relation` to `insert_bundle([], [relation])` so all writes share one transactional integrity implementation.

Before opening the insertion transaction, compute:

```python
batch_node_ids = [node.id for node in nodes]
batch_relation_ids = [relation.id for relation in relations]
batch_triples = [
    (r.source_question_id, r.target_question_id, r.relation_type)
    for r in relations
]
```

Reject duplicate IDs/triples within the incoming bundle with clear `ValueError` messages.

Within one connection/transaction, query existing node IDs, validate every relation endpoint against `existing_node_ids | set(batch_node_ids)`, then insert nodes before relations.

- [ ] **Step 6: Add RED atomic rollback test**

Build a bundle with two valid nodes and two relations where the second relation points to `missing-q`.

```python
with pytest.raises(ValueError, match="question node not found: missing-q"):
    store.insert_bundle([node_a, node_b], [valid_relation, invalid_relation])

assert store.list_nodes() == []
assert store.list_relations() == []
```

- [ ] **Step 7: Make atomic rollback GREEN and test relation filtering**

Implement `list_relations(question_id="q-a")` as relations where the ID appears on either endpoint, ordered by `created_at ASC, id ASC`.

Run:

```bash
pytest tests/test_lineage_storage.py -v
pytest -q
```

- [ ] **Step 8: Commit Task 2**

```bash
git add src/question_radar/lineage_storage.py tests/test_lineage_storage.py
git commit -m "feat: add atomic lineage storage"
```

---

### Task 3: Parse explicit mixed JSONL lineage bundles

**Files:**
- Create: `src/question_radar/lineage_export.py`
- Test: `tests/test_lineage_export.py`

**Interfaces:**
- Consumes: `QuestionNode`, `QuestionRelation`.
- Produces: `load_lineage_bundle(path: str | Path) -> tuple[list[QuestionNode], list[QuestionRelation]]`.
- Does not write SQLite; storage remains Task 2 responsibility.
- Consumed by: Tasks 6, 7, and 8.

- [ ] **Step 1: Write RED happy-path parser test**

Create a temporary JSONL file containing:

```json
{"record_type":"node","id":"q-1","question":"First?","source":"corpus","source_ref":"fixture","created_at":"2026-08-29T18:00:00-03:00"}
{"record_type":"node","id":"q-2","question":"Second?","source":"corpus","source_ref":"fixture","created_at":"2026-08-29T18:01:00-03:00"}
{"record_type":"relation","id":"r-1","source_question_id":"q-1","target_question_id":"q-2","relation_type":"refines","created_at":"2026-08-29T18:02:00-03:00"}
```

Assert two validated nodes and one validated relation are returned, and `record_type` is not retained in domain `to_dict()` output.

- [ ] **Step 2: Run parser test and verify RED**

```bash
pytest tests/test_lineage_export.py -v
```

- [ ] **Step 3: Implement line-by-line parsing with explicit discrimination**

Algorithm:

```python
for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
    if not raw_line.strip():
        continue
    payload = json.loads(raw_line)
    record_type = payload.pop("record_type", None)
    if record_type == "node":
        nodes.append(QuestionNode.from_dict(payload))
    elif record_type == "relation":
        relations.append(QuestionRelation.from_dict(payload))
    else:
        raise ValueError(f"unknown record_type at line {line_number}: {record_type}")
```

Wrap JSON decoding failures as `ValueError(f"malformed JSONL at line {line_number}")` without leaking a traceback through normal CLI handling.

- [ ] **Step 4: Add RED error tests**

Cover:

- malformed JSON line;
- missing `record_type`;
- unknown `record_type`;
- domain unknown fields after discriminator removal;
- blank file returning `([], [])`.

- [ ] **Step 5: Make parser tests GREEN and run regression suite**

```bash
pytest tests/test_lineage_export.py -v
pytest -q
```

- [ ] **Step 6: Commit Task 3**

```bash
git add src/question_radar/lineage_export.py tests/test_lineage_export.py
git commit -m "feat: parse explicit lineage JSONL bundles"
```

---

### Task 4: Implement cycle-safe deterministic graph traversal

**Files:**
- Create: `src/question_radar/lineage_graph.py`
- Test: `tests/test_lineage_graph.py`

**Interfaces:**
- Consumes: `QuestionNode`, `QuestionRelation`.
- Produces: `ancestors(current_id: str, nodes: dict[str, QuestionNode], relations: list[QuestionRelation], max_depth: int) -> list[tuple[QuestionNode, int]]`.
- Produces: `descendants(current_id: str, nodes: dict[str, QuestionNode], relations: list[QuestionRelation], max_depth: int) -> list[tuple[QuestionNode, int]]`.
- Return tuple second element is hop distance from current node, starting at 1; current node is never returned.
- Consumed by: Task 5.

- [ ] **Step 1: Write RED ancestor/descendant tests on a branching graph**

Use:

```text
q1 -> q2 -> q4
q1 -> q3 -> q4
q4 -> q5
```

Assert:

```python
assert [(n.id, d) for n, d in ancestors("q4", nodes, relations, 3)] == [
    ("q2", 1),
    ("q3", 1),
    ("q1", 2),
]

assert [(n.id, d) for n, d in descendants("q1", nodes, relations, 1)] == [
    ("q2", 1),
    ("q3", 1),
]
```

Give deterministic `created_at` values that support this exact order.

- [ ] **Step 2: Run traversal test and verify RED**

```bash
pytest tests/test_lineage_graph.py -v
```

- [ ] **Step 3: Implement bounded breadth-first traversal**

Use a queue of `(node_id, distance)` and a `visited` set initialized with `current_id`. For ancestors, build adjacency from `target_question_id -> source_question_id`; for descendants, `source_question_id -> target_question_id`.

Reject invalid depth before traversal:

```python
if isinstance(max_depth, bool) or not isinstance(max_depth, int) or max_depth < 0:
    raise ValueError("max_depth must be a non-negative integer")
```

Return `[]` for depth `0`.

Sort final `(node, distance)` pairs by:

```python
(distance, node.created_at, node.id)
```

- [ ] **Step 4: Add RED cycle and duplicate-path tests**

Use:

```text
q1 -> q2 -> q3 -> q1
q2 -> q4
q3 -> q4
```

Assert traversal terminates, the current node is excluded, and `q4` appears once at its shortest discovered distance.

- [ ] **Step 5: Make cycle tests GREEN and run full regression**

```bash
pytest tests/test_lineage_graph.py -v
pytest -q
```

- [ ] **Step 6: Commit Task 4**

```bash
git add src/question_radar/lineage_graph.py tests/test_lineage_graph.py
git commit -m "feat: add bounded lineage traversal"
```

---

### Task 5: Build and render deterministic Context Packs

**Files:**
- Create: `src/question_radar/context_pack.py`
- Test: `tests/test_context_pack.py`

**Interfaces:**
- Consumes: `QuestionLineageStore`, `QuestionProfileStore`, `LearningObservationStore`, `ancestors`, `descendants`.
- Produces: immutable derived `ContextPack` dataclass, never persisted.
- Produces: `build_context_pack(current_question_id: str, lineage_store: QuestionLineageStore, profile_store: QuestionProfileStore, learning_store: LearningObservationStore, ancestor_depth: int = 3, descendant_depth: int = 1) -> ContextPack`.
- Produces: `render_context_markdown(pack: ContextPack) -> str`.
- Produces: `render_context_json(pack: ContextPack) -> str`.
- JSON aggregation entries for assumptions/evidence/next questions use `{"question_id": str, "text": str}` to preserve provenance.
- Ancestor/descendant JSON entries use `{"distance": int, **QuestionNode.to_dict()}`.
- Consumed by: Tasks 6 and 8.

- [ ] **Step 1: Write RED test for a node with no optional layers**

Create a DB with one `QuestionNode`, no relations, no profile, no learning observation.

Assert:

```python
pack = build_context_pack("q-1", lineage_store, profile_store, learning_store)
assert pack.current_question.id == "q-1"
assert pack.ancestors == ()
assert pack.descendants == ()
assert pack.profiles == ()
assert pack.learning_observations == ()
```

Also assert missing current node raises `ValueError("question node not found: missing")`.

- [ ] **Step 2: Run Context Pack test and verify RED**

```bash
pytest tests/test_context_pack.py -v
```

- [ ] **Step 3: Implement the derived `ContextPack` shape and selected-node logic**

Use a frozen dataclass with fields in this order:

```python
@dataclass(frozen=True, slots=True)
class ContextPack:
    context_version: str
    current_question: QuestionNode
    ancestors: tuple[tuple[QuestionNode, int], ...]
    descendants: tuple[tuple[QuestionNode, int], ...]
    relations: tuple[QuestionRelation, ...]
    profiles: tuple[QuestionProfile, ...]
    learning_observations: tuple[LearningObservation, ...]
    unresolved_assumptions: tuple[tuple[str, str], ...]
    evidence_still_needed: tuple[tuple[str, str], ...]
    existing_next_questions: tuple[tuple[str, str], ...]
```

Set `context_version="v0.4"`.

Load all v0.4 nodes/relations once, traverse 3/1 by default, and build `selected_ids = {current_id} | ancestor_ids | descendant_ids`.

Include only relations whose source and target are both in `selected_ids`.

- [ ] **Step 4: Add RED join tests for v0.2 and v0.3**

Insert a `QuestionProfile` whose `id` equals a selected node ID and a `LearningObservation` whose `evidence_question_ids` intersects `selected_ids`.

Assert:

- exact-ID profile is included;
- nonmatching profile is excluded;
- intersecting learning observation is included;
- nonintersecting observation is excluded;
- `assumptions`, `evidence_required`, and `next_question` are aggregated as `(question_id, text)` in selected-node order.

Do not modify v0.2/v0.3 stores; use their existing `list_all()` APIs and filter in the Context Pack layer.

- [ ] **Step 5: Make joins GREEN and add deterministic relation/profile ordering**

Selected node order is:

1. current question for current-only sections where relevant;
2. ancestor entries sorted by `(distance, created_at, id)`;
3. descendant entries sorted by `(distance, created_at, id)`.

Relations sort by `(created_at, id)`. Learning observations sort by `(created_at, id)`.

- [ ] **Step 6: Write RED Markdown rendering test**

Assert fixed headings occur exactly in this order:

```text
# Question Radar Context Pack
## CURRENT QUESTION
## LINEAGE
## RELATIONS
## KNOWN PROFILES
## LEARNING SIGNALS
## UNRESOLVED ASSUMPTIONS
## EVIDENCE STILL NEEDED
## EXISTING NEXT QUESTIONS
```

For empty optional sections assert the literal line `none` appears under that heading.

Render each node with ID, question text, provenance, and distance where applicable. Render relation lines as:

```text
source_id --relation_type--> target_id
```

- [ ] **Step 7: Implement deterministic Markdown rendering and verify byte stability**

```python
first = render_context_markdown(pack)
second = render_context_markdown(pack)
assert first == second
```

Always return a single trailing newline.

- [ ] **Step 8: Write RED JSON rendering test and implement stable serialization**

`render_context_json(pack)` must serialize this key structure:

```python
{
    "context_version": "v0.4",
    "current_question": {...},
    "ancestors": [{"distance": 1, ...}],
    "descendants": [{"distance": 1, ...}],
    "relations": [...],
    "profiles": [...],
    "learning_observations": [...],
    "unresolved_assumptions": [{"question_id": "...", "text": "..."}],
    "evidence_still_needed": [{"question_id": "...", "text": "..."}],
    "existing_next_questions": [{"question_id": "...", "text": "..."}],
}
```

Use:

```python
json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
```

Assert repeated rendering is byte-identical and Unicode questions remain readable rather than escaped.

- [ ] **Step 9: Add depth override and cycle integration tests**

Assert default `3/1`, explicit `0/0`, and a graph cycle produce bounded deterministic packs without recursion failure.

- [ ] **Step 10: Run Context Pack tests and regression suite**

```bash
pytest tests/test_context_pack.py -v
pytest -q
```

- [ ] **Step 11: Commit Task 5**

```bash
git add src/question_radar/context_pack.py tests/test_context_pack.py
git commit -m "feat: build deterministic context packs"
```

---

### Task 6: Expose v0.4 through the existing CLI

**Files:**
- Modify: `src/question_radar/cli.py`
- Test: `tests/test_lineage_cli.py`

**Interfaces:**
- Consumes: Tasks 1–5 APIs.
- Produces public commands:
  - `lineage node add <question_json>`
  - `lineage node list`
  - `lineage node show <question_id>`
  - `lineage relation add <relation_json>`
  - `lineage relation list [--question <question_id>]`
  - `lineage import <jsonl>`
  - `lineage context <question_id> [--format markdown|json] [--ancestors N] [--descendants N]`

- [ ] **Step 1: Write RED parser tests for the full lineage command surface**

Use `build_parser().parse_args(...)` and assert defaults:

```python
args = build_parser().parse_args(["lineage", "context", "q-12"])
assert args.format == "markdown"
assert args.ancestors == 3
assert args.descendants == 1
```

Also verify all node/relation/import subcommands parse.

- [ ] **Step 2: Run CLI test and verify RED**

```bash
pytest tests/test_lineage_cli.py -v
```

- [ ] **Step 3: Extend `build_parser()` with nested `lineage` subparsers**

Follow the existing `profile` and `learning` namespace pattern rather than introducing a separate executable.

For depth arguments use `type=int`; semantic non-negative validation remains in graph/context code so negative values return through the existing `ValueError -> stderr -> return 2` path.

- [ ] **Step 4: Add JSON loaders and output helpers**

Add:

```python
def _load_single_lineage_node_json(path: str | Path) -> QuestionNode:
    return QuestionNode.from_dict(_load_json(path))


def _load_single_lineage_relation_json(path: str | Path) -> QuestionRelation:
    return QuestionRelation.from_dict(_load_json(path))
```

Node show output must include all five fields. Relation list output format:

```text
<relation_type>\t<source_question_id>\t<target_question_id>\t<id>
```

- [ ] **Step 5: Write RED command behavior tests**

Use a temp DB and call `main([...])` directly. Cover:

- node add/list/show;
- node show missing -> return `2`, stderr contains `question node not found`;
- relation add/list;
- relation list `--question` filtering;
- import count output;
- context Markdown output;
- context JSON parseability;
- invalid negative depth -> return `2` with human-readable error and no traceback.

- [ ] **Step 6: Implement `_handle_lineage_command(...)`**

Instantiate alongside existing stores in `main`:

```python
lineage_store = QuestionLineageStore(args.db)
```

For `lineage import`:

```python
nodes, relations = load_lineage_bundle(args.input)
lineage_store.insert_bundle(nodes, relations)
print(f"imported {len(nodes)} nodes and {len(relations)} relations")
```

For context, pass the existing `profile_store` and `learning_store` into `build_context_pack`, then print the selected renderer with `end=""` because renderers already include one trailing newline.

- [ ] **Step 7: Run all CLI tests including historical namespaces**

```bash
pytest tests/test_lineage_cli.py tests/test_cli.py tests/test_profile_cli.py tests/test_learning_cli.py -v
pytest -q
```

- [ ] **Step 8: Commit Task 6**

```bash
git add src/question_radar/cli.py tests/test_lineage_cli.py
git commit -m "feat: expose Question Lineage CLI"
```

---

### Task 7: Publish the 12-question v0.4 calibration lineage

**Files:**
- Create: `corpus/question-lineage-v0.4.jsonl`
- Create: `tests/test_lineage_calibration_v04.py`

**Interfaces:**
- Consumes: original source records from `corpus/chat-2026-08-29.jsonl`.
- Consumes: `load_lineage_bundle`, `QuestionLineageStore`.
- Produces: stable public calibration corpus used by Task 8 E2E.

- [ ] **Step 1: Write RED calibration test before creating the corpus**

Assert:

```python
nodes, relations = load_lineage_bundle("corpus/question-lineage-v0.4.jsonl")
assert len(nodes) == 12
assert {node.id for node in nodes} == {
    f"chat-2026-08-29-{i:03d}" for i in range(1, 13)
}
```

Load `corpus/chat-2026-08-29.jsonl` with the existing v0.2 loader and assert each v0.4 node's `question` exactly equals the matching historical profile's `question` and `created_at` exactly equals its historical `created_at`.

- [ ] **Step 2: Run calibration test and verify RED because the corpus is absent**

```bash
pytest tests/test_lineage_calibration_v04.py -v
```

- [ ] **Step 3: Add exactly 12 node records derived from the historical corpus**

For each `chat-2026-08-29-001` through `-012`:

- preserve `id` exactly;
- preserve `question` exactly;
- set `source` to `conversation`;
- set `source_ref` to `corpus/chat-2026-08-29.jsonl`;
- preserve historical `created_at` exactly;
- prefix each JSONL object with `"record_type":"node"`.

Do not copy profile scores, topic, assumptions, or any other v0.2 fields into `QuestionNode`.

- [ ] **Step 4: Add the manually reviewed relation records with these exact edges**

Use these calibration judgments:

```text
rel-001-002  001 -> 002  refines
rel-002-003  002 -> 003  operationalizes
rel-003-004  003 -> 004  follows_from
rel-005-006  005 -> 006  decomposes
rel-005-007  005 -> 007  decomposes
rel-001-008  001 -> 008  generalizes
rel-008-009  008 -> 009  refines
rel-004-010  004 -> 010  challenges_assumption
rel-009-010  009 -> 010  follows_from
rel-010-011  010 -> 011  decomposes
rel-011-012  011 -> 012  operationalizes
```

Use full IDs `chat-2026-08-29-NNN` in endpoints.

Assign deterministic timezone-aware relation timestamps in listed order from `2026-08-29T18:30:00-03:00` through `2026-08-29T18:40:00-03:00`, increasing one minute per relation.

These relations are editorial calibration judgments, not inferred truth labels. `contrasts` is intentionally absent from this real corpus; its contract remains covered by synthetic model tests rather than manufacturing a dubious edge.

- [ ] **Step 5: Add relation-integrity and atomic-import assertions**

Assert every relation endpoint belongs to the 12-node set and every relation type belongs to `RELATION_TYPES`.

Then:

```python
store.insert_bundle(nodes, relations)
assert len(store.list_nodes()) == 12
assert len(store.list_relations()) == 11
```

- [ ] **Step 6: Run calibration + historical corpus tests**

```bash
pytest tests/test_lineage_calibration_v04.py tests/test_chat_corpus_20260829.py -v
pytest -q
```

- [ ] **Step 7: Commit Task 7**

```bash
git add corpus/question-lineage-v0.4.jsonl tests/test_lineage_calibration_v04.py
git commit -m "data: add Question Lineage v0.4 calibration corpus"
```

---

### Task 8: Add end-to-end verification, README v0.4 documentation, and final regression gates

**Files:**
- Create: `tests/test_lineage_e2e.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: all prior task outputs.
- Produces: executable proof of `JSONL -> SQLite -> graph -> v0.2/v0.3 join -> Context Pack -> Markdown/JSON`.
- Produces: public documentation matching actual verified behavior.

- [ ] **Step 1: Write the RED E2E test using a clean temporary database**

The test must:

```python
nodes, relations = load_lineage_bundle("corpus/question-lineage-v0.4.jsonl")
lineage_store.insert_bundle(nodes, relations)

profiles = load_profiles("corpus/chat-2026-08-29.jsonl", "jsonl")
profile_store.insert_many(profiles)

observations = load_learning_observations(
    "corpus/learning-frontier-chat-2026-08-29-v0.3.jsonl", "jsonl"
)
learning_store.insert_many(observations)

pack = build_context_pack(
    "chat-2026-08-29-012",
    lineage_store,
    profile_store,
    learning_store,
)
```

Assert:

- current question is `chat-2026-08-29-012`;
- ancestors are bounded to at most three hops;
- the `011 -> 012 [operationalizes]` relation is present;
- matching v0.2 profiles are present;
- at least one v0.3 observation is present when its evidence IDs intersect selected nodes;
- Markdown contains `CURRENT QUESTION`, `LEARNING SIGNALS`, and original Spanish question text;
- JSON parses and has `context_version == "v0.4"`.

- [ ] **Step 2: Run E2E test and fix only implementation defects revealed by the test**

```bash
pytest tests/test_lineage_e2e.py -v
```

Expected after Tasks 1–7 are correct: PASS. If RED, fix the smallest production defect while preserving all prior contracts, then rerun this test and the directly affected focused test.

- [ ] **Step 3: Run the complete v0.4 focused suite**

```bash
pytest \
  tests/test_lineage.py \
  tests/test_lineage_storage.py \
  tests/test_lineage_export.py \
  tests/test_lineage_graph.py \
  tests/test_context_pack.py \
  tests/test_lineage_cli.py \
  tests/test_lineage_calibration_v04.py \
  tests/test_lineage_e2e.py -v
```

Expected: all v0.4 tests pass.

- [ ] **Step 4: Run the entire repository suite and record the exact observed total**

```bash
pytest -q
```

Expected: all historical 170 tests plus all new v0.4 tests pass. Record the exact final `N passed` output; do not estimate the number.

- [ ] **Step 5: Verify historical rubric blobs and model contracts remain untouched**

Run:

```bash
git hash-object rubric/v0.1.json
git hash-object rubric/v0.2.json
```

Expected exactly:

```text
cf769869a8af8cbc34abbcae3381100f78dae9ac
1b4d3b556b69603217db1c0c67b5b8c11f8fb226
```

Also run historical compatibility tests explicitly:

```bash
pytest tests/test_models.py tests/test_profile_storage.py tests/test_learning_storage.py -v
```

- [ ] **Step 6: Update README with verified v0.4 behavior**

Add a concise v0.4 section after Personal Learning Frontier covering:

```text
QuestionNode -> QuestionRelation -> bounded lineage -> Context Pack
```

Document:

```bash
question-radar lineage import corpus/question-lineage-v0.4.jsonl
question-radar lineage context chat-2026-08-29-012 --format markdown
question-radar lineage context chat-2026-08-29-012 --format json
```

State explicitly:

- no automatic migration;
- relations are explicit/manual;
- cycles are allowed and traversal is bounded;
- Context Packs are derived, not persisted;
- default neighborhood is 3 ancestors / 1 descendant;
- no LLM/runtime dependency is added.

Replace the existing README sentence `Latest verified suite: 170 tests passing.` with the exact `N tests passing` value observed in Step 4. Do not claim CI.

- [ ] **Step 7: Run packaging/syntax/whitespace/privacy checks**

```bash
python -m compileall -q src
python -m pip install -e ".[dev]"
question-radar --help
question-radar lineage --help
git diff --check
git status --short
```

Then verify no tracked private/local artifacts:

```bash
git ls-files | grep -E '(^|/)(\.env|.*\.sqlite3?|.*\.db)$' && exit 1 || true
```

Expected: compile/install/help commands succeed, `git diff --check` emits nothing, and the tracked-private-artifact check finds nothing.

- [ ] **Step 8: Run the exact acceptance workflow on a temporary DB**

```bash
TMP_DB="$(mktemp -u)/question-radar-v04.sqlite3"
question-radar --db "$TMP_DB" profile import corpus/chat-2026-08-29.jsonl --format jsonl
question-radar --db "$TMP_DB" learning import corpus/learning-frontier-chat-2026-08-29-v0.3.jsonl --format jsonl
question-radar --db "$TMP_DB" lineage import corpus/question-lineage-v0.4.jsonl
question-radar --db "$TMP_DB" lineage context chat-2026-08-29-012 --format markdown
question-radar --db "$TMP_DB" lineage context chat-2026-08-29-012 --format json
```

On Windows PowerShell, use a temp path from `[System.IO.Path]::GetTempPath()` instead of `mktemp`; command semantics and outputs must be equivalent.

Expected: imports succeed, Markdown is readable prompt context, JSON parses, and repeated context commands produce identical output for the same DB state.

- [ ] **Step 9: Run final full suite after README-only edits and acceptance checks**

```bash
pytest -q
python -m compileall -q src
git diff --check
```

Expected: same exact passing test total observed in Step 4, clean compile, clean whitespace check.

- [ ] **Step 10: Commit Task 8**

```bash
git add README.md tests/test_lineage_e2e.py
git commit -m "docs: document Question Lineage v0.4 verification"
```

---

## Final Review Gate

Before opening the implementation PR, compare the implementation branch against its base and confirm the diff contains only the planned v0.4 modules/tests/corpus/README changes plus the already-approved spec/plan if they travel on the same branch.

Required evidence to include in the PR description:

```text
- full pytest result: exact N passed
- v0.4 focused suite: passed
- historical compatibility subset: passed
- rubric blob SHAs unchanged
- compileall: passed
- git diff --check: passed
- no tracked DB/.env files
- acceptance CLI workflow: passed
- GitHub Actions: not present / not claimed as CI
```

The implementation PR must not be merged until the user explicitly requests merge.