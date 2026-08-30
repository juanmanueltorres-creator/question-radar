# Question Lineage v0.4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit, versioned question-lineage graph and deterministic Context Pack output without changing Question Radar v0.1, v0.2, or v0.3 contracts.

**Architecture:** Add five focused v0.4 modules: immutable domain contracts, SQLite persistence, mixed-JSONL import, pure bounded graph traversal, and derived Context Pack rendering. Extend the existing CLI with a `lineage` namespace. Join v0.4 nodes to v0.2 profiles and v0.3 learning observations by stable question IDs only while building a Context Pack.

**Tech Stack:** Python 3.11+, standard library only at runtime (`dataclasses`, `datetime`, `json`, `sqlite3`, `argparse`, `pathlib`, collections), pytest 8.x for development.

**Spec:** `docs/superpowers/specs/2026-08-29-question-lineage-v0.4-design.md`

## Global Constraints

- Keep `requires-python = ">=3.11"` and `dependencies = []` unchanged in `pyproject.toml`.
- Keep v0.1 `QuestionEvaluation`, v0.2 `QuestionProfile`, and v0.3 `LearningObservation` contracts unchanged.
- Do not auto-migrate historical SQLite databases.
- `QuestionNode` has exactly five fields: `id`, `question`, `source`, `source_ref`, `created_at`.
- `QuestionRelation` has exactly five fields: `id`, `source_question_id`, `target_question_id`, `relation_type`, `created_at`.
- Source vocabulary is exactly `manual`, `conversation`, `corpus`, `external`.
- Relation vocabulary is exactly `refines`, `decomposes`, `generalizes`, `operationalizes`, `challenges_assumption`, `contrasts`, `follows_from`.
- Graph cycles are valid; self-relations are invalid.
- Imports are explicit, fail-fast, and atomic.
- Context Packs are derived and never persisted.
- Context Pack defaults are `ancestors=3`, `descendants=1`, `format=markdown`.
- Context Pack construction makes no new epistemic inference.
- Rubric Git blob SHAs must remain exactly: `rubric/v0.1.json = cf769869a8af8cbc34abbcae3381100f78dae9ac`; `rubric/v0.2.json = 1b4d3b556b69603217db1c0c67b5b8c11f8fb226`.
- All 170 pre-v0.4 tests must remain green.
- Do not claim GitHub CI because this repository has no GitHub Actions workflow.

---

## File Map

**Create production files**

- `src/question_radar/lineage.py` — v0.4 immutable domain contracts and closed vocabularies.
- `src/question_radar/lineage_storage.py` — v0.4 SQLite schema, CRUD, referential integrity, atomic bundle insertion.
- `src/question_radar/lineage_export.py` — explicit mixed JSONL parsing with `record_type` discrimination.
- `src/question_radar/lineage_graph.py` — bounded ancestor/descendant traversal with cycle protection.
- `src/question_radar/context_pack.py` — Context Pack assembly plus Markdown/JSON rendering.

**Modify production files**

- `src/question_radar/cli.py` — add `lineage` namespace while preserving every existing command.
- `README.md` — document v0.4 and update the verified test total after final verification.

**Create data**

- `corpus/question-lineage-v0.4.jsonl` — 12 historical question nodes plus manually reviewed relations.

**Create tests**

- `tests/test_lineage.py`
- `tests/test_lineage_storage.py`
- `tests/test_lineage_export.py`
- `tests/test_lineage_graph.py`
- `tests/test_context_pack.py`
- `tests/test_lineage_cli.py`
- `tests/test_lineage_calibration_v04.py`
- `tests/test_lineage_e2e.py`

---

### Task 1: Strict v0.4 domain contracts

**Files:**
- Create: `src/question_radar/lineage.py`
- Test: `tests/test_lineage.py`

**Interfaces:**
- Produces constants `SOURCE_TYPES` and `RELATION_TYPES`.
- Produces immutable `QuestionNode` and `QuestionRelation` dataclasses.
- Produces `from_dict()` and `to_dict()` on both dataclasses.
- Consumed by Tasks 2–8.

- [ ] **Step 1: Write failing node tests**

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
    assert QuestionNode.from_dict(node_payload()).to_dict() == node_payload()


@pytest.mark.parametrize("source", ("manual", "conversation", "corpus", "external"))
def test_question_node_accepts_every_source(source):
    assert QuestionNode.from_dict(node_payload(source=source)).source == source


def test_source_vocabulary_is_frozen():
    assert SOURCE_TYPES == ("manual", "conversation", "corpus", "external")
```

Add tests that reject missing/unknown fields, blank `id`, blank `question`, blank-string `source_ref`, invalid source, invalid timestamp, and timezone-naive timestamp. Add a test that accepts `source_ref=None`.

- [ ] **Step 2: Run node tests and verify RED**

```bash
pytest tests/test_lineage.py -v
```

Expected: import failure because `question_radar.lineage` does not exist.

- [ ] **Step 3: Implement shared timestamp validation and `QuestionNode`**

```python
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

SOURCE_TYPES = ("manual", "conversation", "corpus", "external")
NODE_FIELDS = {"id", "question", "source", "source_ref", "created_at"}


def _timezone_aware_timestamp(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a timezone-aware ISO timestamp")
    cleaned = value.strip()
    try:
        parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be a timezone-aware ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must be a timezone-aware ISO timestamp")
    return cleaned


@dataclass(frozen=True, slots=True)
class QuestionNode:
    id: str
    question: str
    source: str
    source_ref: str | None
    created_at: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "QuestionNode":
        if not isinstance(payload, dict):
            raise ValueError("question node payload must be a JSON object")
        missing = sorted(NODE_FIELDS - payload.keys())
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")
        unknown = sorted(payload.keys() - NODE_FIELDS)
        if unknown:
            raise ValueError(f"unknown fields: {', '.join(unknown)}")
        node_id = payload["id"]
        question = payload["question"]
        source = payload["source"]
        source_ref = payload["source_ref"]
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError("id must be a non-empty string")
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question must be a non-empty string")
        if source not in SOURCE_TYPES:
            raise ValueError("source must be one of: " + ", ".join(SOURCE_TYPES))
        if source_ref is not None and (
            not isinstance(source_ref, str) or not source_ref.strip()
        ):
            raise ValueError("source_ref must be null or a non-empty string")
        return cls(
            id=node_id.strip(),
            question=question.strip(),
            source=source,
            source_ref=source_ref.strip() if isinstance(source_ref, str) else None,
            created_at=_timezone_aware_timestamp("created_at", payload["created_at"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

- [ ] **Step 4: Write failing relation tests**

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


def test_relation_vocabulary_is_frozen():
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
def test_relation_accepts_every_type(relation_type):
    assert QuestionRelation.from_dict(
        relation_payload(relation_type=relation_type)
    ).relation_type == relation_type


def test_relation_rejects_self_reference():
    with pytest.raises(ValueError, match="same question"):
        QuestionRelation.from_dict(
            relation_payload(source_question_id="q-001", target_question_id="q-001")
        )
```

Add tests for missing/unknown fields, blank IDs, invalid relation type, invalid timestamp, and timezone-naive timestamp.

- [ ] **Step 5: Implement `QuestionRelation` with the exact five-field contract**

Use `RELATION_FIELDS = {"id", "source_question_id", "target_question_id", "relation_type", "created_at"}` and the same strict missing/unknown-field pattern as `QuestionNode`. Strip outer whitespace on IDs. Reject `source_question_id == target_question_id` with `ValueError("relation cannot reference the same question twice")`. Validate `relation_type` against the frozen tuple and `created_at` with `_timezone_aware_timestamp`.

- [ ] **Step 6: Run focused and historical tests**

```bash
pytest tests/test_lineage.py -v
pytest -q
```

Expected: new tests pass and all 170 historical tests remain green.

- [ ] **Step 7: Commit Task 1**

```bash
git add src/question_radar/lineage.py tests/test_lineage.py
git commit -m "feat: add Question Lineage v0.4 contracts"
```

---

### Task 2: Normalized SQLite storage and atomic writes

**Files:**
- Create: `src/question_radar/lineage_storage.py`
- Test: `tests/test_lineage_storage.py`

**Interfaces:**
- Produces `QuestionLineageStore(db_path)`.
- Produces `insert_node`, `insert_relation`, `insert_bundle`, `get_node`, `list_nodes`, `get_relation`, `list_relations`.
- `list_relations(question_id=None)` returns every relation; with an ID it returns relations where that ID is either endpoint.
- Consumed by Tasks 3–8.

- [ ] **Step 1: Write RED node CRUD/order tests**

Insert nodes in reverse chronological order and assert `list_nodes()` returns `created_at ASC, id ASC`. Assert `get_node()` returns the exact dataclass and returns `None` for a missing ID.

- [ ] **Step 2: Run storage tests and verify RED**

```bash
pytest tests/test_lineage_storage.py -v
```

- [ ] **Step 3: Implement schemas and connection policy**

```sql
CREATE TABLE IF NOT EXISTS question_nodes_v04 (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('manual','conversation','corpus','external')),
    source_ref TEXT,
    created_at TEXT NOT NULL
)
```

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

Every `_connect()` call executes `PRAGMA foreign_keys = ON` and sets `row_factory = sqlite3.Row`.

- [ ] **Step 4: Write RED relation-integrity tests**

Cover valid insert/get/list, missing source endpoint, missing target endpoint, duplicate relation ID, duplicate `(source,target,type)` under another ID, and SQLite rejection of a self-relation.

- [ ] **Step 5: Implement one transactional integrity path**

Make `insert_node(node)` call `insert_bundle([node], [])` and `insert_relation(relation)` call `insert_bundle([], [relation])`.

Inside `insert_bundle`, build `node_ids`, `relation_ids`, and `(source,target,type)` triples. Reject duplicates inside the incoming bundle before writes. In one connection, read existing node IDs, validate every relation endpoint against `existing_ids | set(node_ids)`, insert nodes first, then relations. Convert `sqlite3.IntegrityError` into a clear `ValueError`; the connection context manager must rollback the whole transaction on failure.

- [ ] **Step 6: Write RED rollback test**

```python
with pytest.raises(ValueError, match="question node not found: missing-q"):
    store.insert_bundle(
        [node_a, node_b],
        [valid_relation, relation_to_missing_q],
    )
assert store.list_nodes() == []
assert store.list_relations() == []
```

- [ ] **Step 7: Make rollback/filter/order tests GREEN**

Order relations by `created_at ASC, id ASC`. Run:

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

### Task 3: Explicit mixed JSONL import

**Files:**
- Create: `src/question_radar/lineage_export.py`
- Test: `tests/test_lineage_export.py`

**Interfaces:**
- Produces `load_lineage_bundle(path: str | Path) -> tuple[list[QuestionNode], list[QuestionRelation]]`.
- Parsing never writes SQLite.
- Consumed by Tasks 6–8.

- [ ] **Step 1: Write RED happy-path parser test**

Use this exact fixture:

```jsonl
{"record_type":"node","id":"q-1","question":"First?","source":"corpus","source_ref":"fixture","created_at":"2026-08-29T18:00:00-03:00"}
{"record_type":"node","id":"q-2","question":"Second?","source":"corpus","source_ref":"fixture","created_at":"2026-08-29T18:01:00-03:00"}
{"record_type":"relation","id":"r-1","source_question_id":"q-1","target_question_id":"q-2","relation_type":"refines","created_at":"2026-08-29T18:02:00-03:00"}
```

Assert two nodes and one relation are returned and `record_type` is absent from domain `to_dict()` output.

- [ ] **Step 2: Run parser test and verify RED**

```bash
pytest tests/test_lineage_export.py -v
```

- [ ] **Step 3: Implement deterministic line parsing**

Use `Path(path).read_text(encoding="utf-8").splitlines()`. Ignore blank lines. For each nonblank line, parse JSON, remove `record_type`, dispatch to `QuestionNode.from_dict` or `QuestionRelation.from_dict`, and preserve file order inside each returned list. Raise `ValueError(f"malformed JSONL at line {line_number}")` for decoding failures and `ValueError(f"unknown record_type at line {line_number}: {record_type}")` for missing/unknown discriminators.

- [ ] **Step 4: Add error tests**

Cover malformed JSON, missing discriminator, unknown discriminator, invalid node payload, invalid relation payload, and a blank file returning `([], [])`.

- [ ] **Step 5: Run focused and full suites**

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

### Task 4: Cycle-safe bounded graph traversal

**Files:**
- Create: `src/question_radar/lineage_graph.py`
- Test: `tests/test_lineage_graph.py`

**Interfaces:**
- Produces `ancestors(current_id, nodes, relations, max_depth) -> list[tuple[QuestionNode, int]]`.
- Produces `descendants(current_id, nodes, relations, max_depth) -> list[tuple[QuestionNode, int]]`.
- Hop distance starts at 1. Current node is never returned.
- Consumed by Task 5.

- [ ] **Step 1: Write RED branching-graph tests**

Use:

```text
q1 -> q2 -> q4
q1 -> q3 -> q4
q4 -> q5
```

Give q2 an earlier timestamp than q3. Assert ancestors of q4 at depth 3 are `(q2,1)`, `(q3,1)`, `(q1,2)`. Assert descendants of q1 at depth 1 are `(q2,1)`, `(q3,1)`.

- [ ] **Step 2: Run graph tests and verify RED**

```bash
pytest tests/test_lineage_graph.py -v
```

- [ ] **Step 3: Implement breadth-first traversal**

```python
if isinstance(max_depth, bool) or not isinstance(max_depth, int) or max_depth < 0:
    raise ValueError("max_depth must be a non-negative integer")
```

Use a queue of `(node_id, distance)` and a `visited` set initialized with the current ID. Incoming edges define ancestors; outgoing edges define descendants. Return `[]` for depth 0. Sort results by `(distance, node.created_at, node.id)`.

- [ ] **Step 4: Add cycle/duplicate-path tests**

Use:

```text
q1 -> q2 -> q3 -> q1
q2 -> q4
q3 -> q4
```

Assert traversal terminates, q1 is excluded when q1 is current, q4 appears once, and shortest discovered distance wins.

- [ ] **Step 5: Run focused and full suites**

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

### Task 5: Deterministic Context Pack assembly and rendering

**Files:**
- Create: `src/question_radar/context_pack.py`
- Test: `tests/test_context_pack.py`

**Interfaces:**
- Produces immutable derived `ContextPack`.
- Produces `build_context_pack(current_question_id, lineage_store, profile_store, learning_store, ancestor_depth=3, descendant_depth=1) -> ContextPack`.
- Produces `render_context_markdown(pack) -> str`.
- Produces `render_context_json(pack) -> str`.
- Context Packs are never stored in SQLite.
- Consumed by Tasks 6 and 8.

- [ ] **Step 1: Write RED minimal-pack tests**

For one node with no relations/profile/learning data assert current node is present and every optional tuple is empty. Assert a missing current ID raises `ValueError("question node not found: missing")`.

- [ ] **Step 2: Run Context Pack tests and verify RED**

```bash
pytest tests/test_context_pack.py -v
```

- [ ] **Step 3: Implement the derived type and node selection**

Use this exact dataclass shape:

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

Here the `...` token is Python variadic-tuple syntax, not omitted plan content.

Build `nodes_by_id` from `lineage_store.list_nodes()`, fetch the current node, calculate ancestors/descendants, then create `selected_ids` from current + traversed nodes. Keep only relations whose source and target are both selected.

- [ ] **Step 4: Write RED v0.2/v0.3 join tests**

Insert one matching and one nonmatching `QuestionProfile`; insert one intersecting and one nonintersecting `LearningObservation`. Assert profile selection uses exact node ID equality and learning selection uses non-empty evidence-ID intersection.

Aggregate profile `assumptions`, `evidence_required`, and `next_question` as `(question_id, text)` pairs in selected-node order. Do not change v0.2/v0.3 contracts; use their existing `list_all()` APIs.

- [ ] **Step 5: Make joins and ordering GREEN**

Relations order by `(created_at, id)`. Learning observations order by `(created_at, id)`. Profiles follow selected-node order. Set `context_version="v0.4"`.

- [ ] **Step 6: Write RED Markdown renderer tests**

Assert these headings occur once and in this order:

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

Render relation lines exactly as `source_id --relation_type--> target_id`. Under an empty optional section render `none`. Include node ID, original question, provenance, and hop distance where applicable. Always end output with one newline character.

- [ ] **Step 7: Implement Markdown and byte-stability test**

Call `render_context_markdown(pack)` twice and assert exact string equality.

- [ ] **Step 8: Write RED JSON renderer test and implement exact output keys**

The decoded JSON object must contain exactly:

```python
{
    "context_version",
    "current_question",
    "ancestors",
    "descendants",
    "relations",
    "profiles",
    "learning_observations",
    "unresolved_assumptions",
    "evidence_still_needed",
    "existing_next_questions",
}
```

Ancestor and descendant entries contain a `distance` integer plus all five node fields. Assumption/evidence/next-question entries contain exactly `question_id` and `text`. Serialize with `json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)` and append exactly one newline character to the returned string. Assert original Spanish text remains readable rather than Unicode-escaped.

- [ ] **Step 9: Test depth overrides and cycles through the pack builder**

Cover default 3/1, explicit 0/0, negative depth rejection, and a valid graph cycle.

- [ ] **Step 10: Run focused and full suites**

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

### Task 6: Add the `lineage` CLI namespace

**Files:**
- Modify: `src/question_radar/cli.py`
- Test: `tests/test_lineage_cli.py`

**Interfaces:**
- Public commands:
  - `lineage node add <question_json>`
  - `lineage node list`
  - `lineage node show <question_id>`
  - `lineage relation add <relation_json>`
  - `lineage relation list [--question <question_id>]`
  - `lineage import <jsonl>`
  - `lineage context <question_id> [--format markdown|json] [--ancestors N] [--descendants N]`

- [ ] **Step 1: Write RED parser tests**

Assert `build_parser().parse_args(["lineage", "context", "q-12"])` yields `format="markdown"`, `ancestors=3`, `descendants=1`. Parse every node/relation/import form listed above.

- [ ] **Step 2: Run CLI tests and verify RED**

```bash
pytest tests/test_lineage_cli.py -v
```

- [ ] **Step 3: Extend `build_parser()` using the existing nested namespace pattern**

Follow the existing `profile` and `learning` parser structure. Use `choices=("markdown", "json")` for context format and `type=int` for depths; semantic non-negative validation remains in graph/context code.

- [ ] **Step 4: Add single-record loaders**

```python
def _load_single_lineage_node_json(path: str | Path) -> QuestionNode:
    return QuestionNode.from_dict(_load_json(path))


def _load_single_lineage_relation_json(path: str | Path) -> QuestionRelation:
    return QuestionRelation.from_dict(_load_json(path))
```

Node `show` prints all five fields. Relation list prints `relation_type`, `source_question_id`, `target_question_id`, and `id` separated by tabs.

- [ ] **Step 5: Write RED behavior tests using `main()` and a temp DB**

Cover node add/list/show, missing node return code 2, relation add/list/filter, bundle import count, Markdown context, JSON context, and negative depth returning code 2 with human-readable stderr and no traceback.

- [ ] **Step 6: Implement `_handle_lineage_command`**

Instantiate `QuestionLineageStore(args.db)` beside the existing stores. For import:

```python
nodes, relations = load_lineage_bundle(args.input)
lineage_store.insert_bundle(nodes, relations)
print(f"imported {len(nodes)} nodes and {len(relations)} relations")
```

For context, call `build_context_pack`, choose the renderer, and print with `end=""` because each renderer owns one trailing newline.

- [ ] **Step 7: Verify new and historical CLI behavior**

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
- Test: `tests/test_lineage_calibration_v04.py`

**Interfaces:**
- Source of truth for node wording/IDs/timestamps: `corpus/chat-2026-08-29.jsonl`.
- Produces exactly 12 node records and 11 explicit relation records.
- Consumed by Task 8.

- [ ] **Step 1: Write RED corpus test**

```python
expected_ids = {f"chat-2026-08-29-{number:03d}" for number in range(1, 13)}
assert {node.id for node in nodes} == expected_ids
assert len(nodes) == 12
```

Load the historical chat corpus with the existing v0.2 loader and assert each v0.4 node has exactly the matching historical `question` and `created_at`.

- [ ] **Step 2: Run and verify RED because the corpus file does not exist**

```bash
pytest tests/test_lineage_calibration_v04.py -v
```

- [ ] **Step 3: Add the 12 node records**

For IDs `chat-2026-08-29-001` through `chat-2026-08-29-012`, copy only `id`, `question`, and `created_at` from the matching historical profile. Set `record_type="node"`, `source="conversation"`, and `source_ref="corpus/chat-2026-08-29.jsonl"`. Do not copy score, type, topic, assumptions, or any other v0.2 field.

- [ ] **Step 4: Add these exact 11 editorial relation judgments**

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

Use full `chat-2026-08-29-NNN` endpoint IDs. Assign relation timestamps in listed order from `2026-08-29T18:30:00-03:00` to `2026-08-29T18:40:00-03:00`, increasing one minute each record. `contrasts` remains absent from this real corpus; synthetic contract tests cover it rather than manufacturing a weak editorial edge.

- [ ] **Step 5: Test referential integrity and atomic import**

Assert every relation endpoint belongs to the 12-node set and every type belongs to `RELATION_TYPES`. Insert the complete bundle and assert 12 stored nodes and 11 stored relations.

- [ ] **Step 6: Run calibration and historical-corpus tests**

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

### Task 8: E2E acceptance, README, and regression gates

**Files:**
- Create: `tests/test_lineage_e2e.py`
- Modify: `README.md`

**Interfaces:**
- Proves `JSONL -> SQLite -> graph traversal -> v0.2/v0.3 join -> Context Pack -> Markdown/JSON`.
- Produces final public v0.4 documentation based only on observed verification results.

- [ ] **Step 1: Write the E2E test on a clean temporary DB**

```python
nodes, relations = load_lineage_bundle("corpus/question-lineage-v0.4.jsonl")
lineage_store.insert_bundle(nodes, relations)
profiles = load_profiles("corpus/chat-2026-08-29.jsonl", "jsonl")
profile_store.insert_many(profiles)
observations = load_learning_observations(
    "corpus/learning-frontier-chat-2026-08-29-v0.3.jsonl",
    "jsonl",
)
learning_store.insert_many(observations)
pack = build_context_pack(
    "chat-2026-08-29-012",
    lineage_store,
    profile_store,
    learning_store,
)
```

Assert current question is `-012`; bounded ancestors are present; relation `011 -> 012` with type `operationalizes` is present; matching profiles are present; at least one learning observation is present when its evidence intersects selected nodes; Markdown includes `CURRENT QUESTION`, `LEARNING SIGNALS`, and the original Spanish question; parsed JSON has `context_version == "v0.4"`.

- [ ] **Step 2: Run the E2E test**

```bash
pytest tests/test_lineage_e2e.py -v
```

If it fails, fix only the smallest production defect demonstrated by that failure, then rerun the E2E test plus the focused test for the affected module.

- [ ] **Step 3: Run the complete v0.4 focused suite**

```bash
pytest tests/test_lineage.py tests/test_lineage_storage.py tests/test_lineage_export.py tests/test_lineage_graph.py tests/test_context_pack.py tests/test_lineage_cli.py tests/test_lineage_calibration_v04.py tests/test_lineage_e2e.py -v
```

Expected: all v0.4 tests pass.

- [ ] **Step 4: Run the full repository suite and record the exact observed total**

```bash
pytest -q
```

Expected: all 170 historical tests plus all new v0.4 tests pass. Record the exact `N passed` emitted by pytest; do not estimate it.

- [ ] **Step 5: Verify frozen historical artifacts**

```bash
git hash-object rubric/v0.1.json
git hash-object rubric/v0.2.json
```

Expected exactly:

```text
cf769869a8af8cbc34abbcae3381100f78dae9ac
1b4d3b556b69603217db1c0c67b5b8c11f8fb226
```

Also run:

```bash
pytest tests/test_models.py tests/test_profile_storage.py tests/test_learning_storage.py -v
```

- [ ] **Step 6: Update README from observed behavior**

Add a concise v0.4 section showing `QuestionNode -> QuestionRelation -> bounded lineage -> Context Pack` and document:

```bash
question-radar lineage import corpus/question-lineage-v0.4.jsonl
question-radar lineage context chat-2026-08-29-012 --format markdown
question-radar lineage context chat-2026-08-29-012 --format json
```

State: no automatic migration; relations are explicit; cycles are allowed but traversal is bounded; Context Packs are derived; defaults are 3 ancestors/1 descendant; no LLM/runtime dependency is added. Replace `Latest verified suite: 170 tests passing.` with the exact total observed in Step 4. Do not claim CI.

- [ ] **Step 7: Run syntax, install, whitespace, and privacy checks**

```bash
python -m compileall -q src
python -m pip install -e ".[dev]"
question-radar --help
question-radar lineage --help
git diff --check
git status --short
```

Verify no local/private DB or environment files are tracked:

```bash
git ls-files | grep -E '(^|/)(\.env|.*\.sqlite3?|.*\.db)$' && exit 1 || true
```

Expected: compile/install/help succeed, `git diff --check` prints nothing, and the tracked-private-file check finds nothing.

- [ ] **Step 8: Run the acceptance workflow on a temporary DB**

Linux/macOS:

```bash
TMP_DIR="$(mktemp -d)"
TMP_DB="$TMP_DIR/question-radar-v04.sqlite3"
question-radar --db "$TMP_DB" profile import corpus/chat-2026-08-29.jsonl --format jsonl
question-radar --db "$TMP_DB" learning import corpus/learning-frontier-chat-2026-08-29-v0.3.jsonl --format jsonl
question-radar --db "$TMP_DB" lineage import corpus/question-lineage-v0.4.jsonl
question-radar --db "$TMP_DB" lineage context chat-2026-08-29-012 --format markdown
question-radar --db "$TMP_DB" lineage context chat-2026-08-29-012 --format json
```

On Windows PowerShell, create the DB path under `[System.IO.Path]::GetTempPath()` and run the same five `question-radar --db` operations. Re-run both context commands and assert outputs are byte-identical to their first run.

- [ ] **Step 9: Run final verification after README edits**

```bash
pytest -q
python -m compileall -q src
git diff --check
```

Expected: the same exact passing total recorded in Step 4, clean compile, and clean whitespace check.

- [ ] **Step 10: Commit Task 8**

```bash
git add README.md tests/test_lineage_e2e.py
git commit -m "docs: document Question Lineage v0.4 verification"
```

---

## Final Review Gate

Before opening the implementation PR, compare the feature branch against its base and confirm that changed files are restricted to the planned v0.4 modules, eight test files, calibration corpus, README, and approved spec/plan documentation.

The PR description must include observed evidence in this form, replacing `N` only with the actual pytest total obtained during verification:

```text
- full pytest result: N passed
- v0.4 focused suite: passed
- historical compatibility subset: passed
- rubric blob SHAs unchanged
- compileall: passed
- git diff --check: passed
- no tracked DB/.env files
- acceptance CLI workflow: passed
- GitHub Actions: not present; no CI claim
```

Do not merge the implementation PR until the user explicitly requests merge.