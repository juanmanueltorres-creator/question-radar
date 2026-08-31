# Question Lineage v0.4 — Design Specification

Date: 2026-08-29
Status: Design approved in conversation; implementation not started
Repository: `juanmanueltorres-creator/question-radar`

## 1. Summary

Question Radar v0.4 introduces **Question Lineage**: a versioned graph layer that treats the question itself as a stable first-class entity and records explicit relationships between questions.

The purpose is twofold:

1. make sequences of questions inspectable as evolving reasoning rather than isolated records;
2. produce a deterministic **Context Pack** that can be reused to formulate stronger future questions and prompts without adding an LLM runtime to Question Radar.

v0.4 must preserve the existing v0.1, v0.2, and v0.3 contracts unchanged.

The core model becomes:

```text
QuestionNode = what was asked
QuestionProfile = how it is formulated
QuestionRelation = how it connects to another question
LearningObservation = what evidence-backed learning pattern may be present
Context Pack = what context is useful for the next question or prompt
```

## 2. Goals

v0.4 must:

- introduce a stable base entity, `QuestionNode`;
- introduce explicit, typed, directed `QuestionRelation` edges;
- preserve original question wording;
- support graph branching and cycles safely;
- import historical questions explicitly and reproducibly;
- keep imports atomic and fail-fast;
- derive bounded lineage neighborhoods deterministically;
- join lineage data with existing v0.2 profiles and v0.3 learning observations by question ID;
- produce a non-persisted Context Pack;
- render Context Packs as Markdown and JSON;
- keep the runtime dependency-free beyond the Python standard library;
- preserve all historical tests and versioned rubrics.

## 3. Non-goals

v0.4 will not add:

- automatic migration of historical databases;
- automatic extraction of questions from chat history;
- automatic inference of graph relations;
- automatic prompt generation;
- automatic answers;
- an LLM runtime or external AI API;
- embeddings or vector search;
- semantic similarity ranking;
- NetworkX, Neo4j, or another graph database;
- a web frontend;
- interactive editing;
- delete commands;
- learner scoring, intelligence scoring, mastery percentages, or hidden personality inference;
- global graph relevance heuristics;
- `answers`, `proves`, `causes`, or other conclusion-strength relations.

These exclusions are intentional. v0.4 first establishes an auditable graph and deterministic context layer.

## 4. Compatibility rule

Existing contracts remain frozen.

```text
v0.1 QuestionEvaluation     unchanged
v0.2 QuestionProfile        unchanged
v0.3 LearningObservation    unchanged
v0.4 QuestionNode           new
v0.4 QuestionRelation       new
```

No fields are added to v0.1, v0.2, or v0.3 models.

No foreign keys are retrofitted into historical tables.

A database created before v0.4 must continue working exactly as before. It gains lineage only after an explicit v0.4 import or explicit lineage commands.

## 5. `QuestionNode` contract

`QuestionNode` is the stable base representation of a question.

It has exactly five fields in v0.4:

```text
id
question
source
source_ref
created_at
```

Example:

```json
{
  "id": "chat-2026-08-29-010",
  "question": "¿Tiene sentido comparar una pregunta filosófica y una factual con el mismo score?",
  "source": "conversation",
  "source_ref": "corpus/chat-2026-08-29.jsonl",
  "created_at": "2026-08-29T18:26:00-03:00"
}
```

### 5.1 Field rules

#### `id`

- required;
- non-empty string;
- stable identity;
- unique within `question_nodes_v04`.

#### `question`

- required;
- non-empty string;
- stores the original wording;
- must not be silently normalized, rewritten, or improved.

Whitespace at the outer boundary may be trimmed during validation, consistent with existing models.

#### `source`

Closed vocabulary:

```text
manual
conversation
corpus
external
```

No arbitrary source strings are accepted in v0.4.

#### `source_ref`

- optional;
- either `null` or a non-empty string;
- records an explicit origin reference such as a corpus path or external identifier;
- is descriptive provenance, not an automatically dereferenced URL.

#### `created_at`

- required;
- valid timezone-aware ISO timestamp;
- naive timestamps are rejected.

### 5.2 Deliberately excluded fields

`QuestionNode` does not contain:

- topic;
- score;
- tags;
- language;
- summary;
- embedding;
- readiness;
- assumptions;
- evidence requirements;
- learning state.

Those belong to other layers or future derived views.

## 6. `QuestionRelation` contract

`QuestionRelation` records one explicit directed semantic relationship between two `QuestionNode` records.

Fields:

```text
id
source_question_id
target_question_id
relation_type
created_at
```

Example:

```json
{
  "id": "rel-010-011",
  "source_question_id": "chat-2026-08-29-010",
  "target_question_id": "chat-2026-08-29-011",
  "relation_type": "challenges_assumption",
  "created_at": "2026-08-29T18:30:00-03:00"
}
```

### 6.1 Closed relation vocabulary

v0.4 supports exactly seven relation types:

```text
refines
decomposes
generalizes
operationalizes
challenges_assumption
contrasts
follows_from
```

### 6.2 Semantics

#### `refines`

The target makes the source more precise or better bounded.

#### `decomposes`

The target breaks one part of the source into a smaller investigable question.

A source may have multiple `decomposes` targets.

#### `generalizes`

The target moves from a narrower case to a broader formulation.

#### `operationalizes`

The target converts an abstract or conceptual question into something testable, observable, or actionable.

#### `challenges_assumption`

The target explicitly questions an assumption inherited or asserted by the source.

#### `contrasts`

The target introduces an alternative framing, explanation, or comparison.

Although semantically contrast can feel symmetric, storage remains directed. No reverse edge is created automatically.

#### `follows_from`

The target is a reasonable next question produced by the source question's unresolved state, evidence, or result.

It does not imply that the source was answered correctly or completely.

### 6.3 Relation rules

- `id` must be a unique non-empty string.
- both endpoint IDs must exist as `QuestionNode` records, either already stored or included in the same atomic import bundle;
- source and target must be different IDs;
- `relation_type` must be one of the seven allowed values;
- `created_at` must be timezone-aware;
- the tuple `(source_question_id, target_question_id, relation_type)` must be unique;
- no reverse relation is inferred automatically;
- no relation is inferred silently from text, timestamps, profiles, or learning observations.

## 7. Graph model

Question Lineage is a directed graph.

It is **not required to be a DAG**.

Cycles are allowed because real reasoning may return to earlier questions or concepts.

Example:

```text
q1 -> q2 -> q3 -> q1
```

A cycle is not an error by itself.

Graph traversal must maintain a visited-ID set and a bounded depth so cycles cannot create infinite traversal.

All seven relation types participate in lineage traversal in v0.4. Relation-type filtering is deferred until there is evidence that it is needed.

## 8. Historical import policy

There is no automatic migration.

Historical questions become v0.4 nodes only through an explicit, reproducible import.

The first public v0.4 calibration corpus will represent the existing 12-question real chat corpus as `QuestionNode` records and explicit `QuestionRelation` records.

Existing IDs must be preserved whenever they already provide stable question identity.

Opening an old SQLite database must not create, rewrite, or infer v0.4 records.

## 9. JSONL interchange format

v0.4 uses a mixed JSONL corpus for explicit lineage import.

Every line is a JSON object with a required discriminator:

```text
record_type = "node" | "relation"
```

### 9.1 Node line

```json
{
  "record_type": "node",
  "id": "chat-2026-08-29-010",
  "question": "¿Tiene sentido comparar una pregunta filosófica y una factual con el mismo score?",
  "source": "conversation",
  "source_ref": "corpus/chat-2026-08-29.jsonl",
  "created_at": "2026-08-29T18:26:00-03:00"
}
```

### 9.2 Relation line

```json
{
  "record_type": "relation",
  "id": "rel-010-011",
  "source_question_id": "chat-2026-08-29-010",
  "target_question_id": "chat-2026-08-29-011",
  "relation_type": "challenges_assumption",
  "created_at": "2026-08-29T18:30:00-03:00"
}
```

`record_type` is an interchange discriminator. It is not stored as part of the `QuestionNode` or `QuestionRelation` domain contracts.

Unknown record types are rejected.

## 10. Storage design

v0.4 adds two tables.

### 10.1 `question_nodes_v04`

Conceptual schema:

```sql
CREATE TABLE question_nodes_v04 (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    source TEXT NOT NULL,
    source_ref TEXT,
    created_at TEXT NOT NULL
);
```

Python validation remains the primary closed-vocabulary validator for `source`; SQLite may additionally use a CHECK constraint for defense in depth.

### 10.2 `question_relations_v04`

Conceptual schema:

```sql
CREATE TABLE question_relations_v04 (
    id TEXT PRIMARY KEY,
    source_question_id TEXT NOT NULL,
    target_question_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (source_question_id, target_question_id, relation_type),
    CHECK (source_question_id <> target_question_id),
    FOREIGN KEY (source_question_id)
        REFERENCES question_nodes_v04(id),
    FOREIGN KEY (target_question_id)
        REFERENCES question_nodes_v04(id)
);
```

Connections used by v0.4 storage must enable:

```sql
PRAGMA foreign_keys = ON;
```

### 10.3 Atomic bundle insertion

`QuestionLineageStore` must support an operation that inserts nodes and relations in one transaction.

The import flow is:

```text
parse entire file
validate all records
split nodes and relations
validate duplicate IDs inside the batch
validate duplicate relation triples inside the batch
validate relation endpoints against existing nodes + imported nodes
BEGIN
insert nodes
insert relations
COMMIT
```

Any failure results in rollback with zero partial records from the bundle.

## 11. Module architecture

v0.4 follows the existing separation between domain models, persistence, serialization, rendering, and CLI.

```text
src/question_radar/
├── lineage.py
├── lineage_storage.py
├── lineage_export.py
├── lineage_graph.py
├── context_pack.py
└── cli.py
```

### 11.1 `lineage.py`

Owns:

- `QuestionNode`;
- `QuestionRelation`;
- `SOURCE_TYPES`;
- `RELATION_TYPES`;
- strict domain validation;
- `to_dict()` / `from_dict()` behavior.

It does not contain SQLite or CLI code.

### 11.2 `lineage_storage.py`

Owns:

- v0.4 SQLite schemas;
- `QuestionLineageStore`;
- insert/get/list operations;
- endpoint integrity;
- atomic node/relation bundle insertion;
- deterministic retrieval ordering.

### 11.3 `lineage_export.py`

Owns:

- mixed JSONL parsing;
- `record_type` handling;
- import validation;
- deterministic JSONL serialization if export support is needed internally for fixtures and round-trip tests.

The public v0.4 CLI requirement is import; a general lineage export command is not required in this release.

### 11.4 `lineage_graph.py`

Owns pure graph traversal behavior:

- `ancestors()`;
- `descendants()`;
- cycle protection;
- bounded depth;
- deterministic ordering.

It should be independently testable without CLI concerns.

### 11.5 `context_pack.py`

Owns:

- building a derived Context Pack;
- logical joining with v0.2 and v0.3 data;
- Markdown rendering;
- JSON rendering;
- deterministic field and item ordering.

A Context Pack is not stored in SQLite.

### 11.6 `cli.py`

Adds the `lineage` namespace while preserving all existing commands.

## 12. Context Pack

A Context Pack is a deterministic derived view centered on one `QuestionNode`.

It exists to prepare better context for future reasoning, questioning, or prompting.

It does not itself infer a better answer or generate a new prompt.

### 12.1 Default neighborhood

Defaults:

```text
ancestors = 3
descendants = 1
```

Definitions:

- ancestors are reached by traversing incoming edges from the current node;
- descendants are reached by traversing outgoing edges from the current node.

Traversal uses all relation types in v0.4.

### 12.2 Overrides

CLI users may override the bounded depth:

```bash
question-radar lineage context q-012 --ancestors 3 --descendants 1
```

Depth values must be non-negative integers.

### 12.3 Included data

The Context Pack includes:

1. current question node;
2. selected ancestor nodes;
3. selected descendant nodes;
4. relations whose endpoints are both within the selected node set;
5. matching v0.2 `QuestionProfile` records, when present;
6. v0.3 `LearningObservation` records when at least one `evidence_question_id` is in the selected node set;
7. assumptions from matching profiles;
8. evidence requirements from matching profiles;
9. existing `next_question` values from matching profiles;
10. provenance (`source`, `source_ref`) from nodes.

Missing optional layers are represented as empty sections or empty arrays, not treated as failure.

### 12.4 No new inference

Context Pack construction must not infer:

- a new relation;
- a new learning state;
- a new confidence value;
- a new assumption;
- a diagnosis;
- mastery;
- a best answer;
- a generated next question.

It only aggregates explicitly stored evidence.

### 12.5 Logical joins

A v0.2 profile belongs to a selected node when:

```text
QuestionProfile.id == QuestionNode.id
```

A v0.3 learning observation is relevant when:

```text
intersection(
    LearningObservation.evidence_question_ids,
    selected QuestionNode IDs
) is not empty
```

v0.4 does not rewrite historical v0.3 evidence IDs into database foreign keys.

## 13. Context Pack output ordering

Markdown sections appear in this fixed order:

```text
CURRENT QUESTION
LINEAGE
RELATIONS
KNOWN PROFILES
LEARNING SIGNALS
UNRESOLVED ASSUMPTIONS
EVIDENCE STILL NEEDED
EXISTING NEXT QUESTIONS
```

The output must explicitly represent empty relevant sections, for example:

```text
KNOWN PROFILES
none
```

The same database state and same command parameters must produce byte-for-byte stable JSON and stable Markdown.

### 13.1 Deterministic ordering rules

Where multiple graph nodes are returned, order by:

1. hop distance from the current node;
2. `created_at` ascending;
3. `id` ascending.

Relations are ordered by:

1. `created_at` ascending;
2. `id` ascending.

Profiles are ordered according to their corresponding selected-node order.

Learning observations are ordered by:

1. `created_at` ascending;
2. `id` ascending.

JSON serialization uses stable key ordering/field construction and stable list ordering.

No output depends on SQLite's accidental row order.

## 14. Context Pack formats

### 14.1 Markdown

Markdown is optimized for human inspection and direct reuse in an LLM conversation.

Example shape:

```text
# Question Radar Context Pack

## CURRENT QUESTION
...

## LINEAGE
...

## RELATIONS
...
```

It must remain evidence-oriented and concise enough to be practical prompt context.

### 14.2 JSON

JSON is optimized for machine integration and future tooling.

Conceptual structure:

```json
{
  "context_version": "v0.4",
  "current_question": {},
  "ancestors": [],
  "descendants": [],
  "relations": [],
  "profiles": [],
  "learning_observations": [],
  "unresolved_assumptions": [],
  "evidence_still_needed": [],
  "existing_next_questions": []
}
```

`context_version` identifies the derived Context Pack format. It does not alter historical rubric versions.

## 15. CLI design

v0.4 adds:

```bash
question-radar lineage node add question.json
question-radar lineage node list
question-radar lineage node show q-012

question-radar lineage relation add relation.json
question-radar lineage relation list
question-radar lineage relation list --question q-012

question-radar lineage import corpus/question-lineage-v0.4.jsonl

question-radar lineage context q-012
question-radar lineage context q-012 --format markdown
question-radar lineage context q-012 --format json
question-radar lineage context q-012 --ancestors 3 --descendants 1
```

### 15.1 Defaults

For `lineage context`:

```text
format = markdown
ancestors = 3
descendants = 1
```

### 15.2 CLI errors

CLI follows the existing Question Radar convention:

- human-readable error written to stderr;
- non-zero return code;
- no traceback for expected validation/storage errors.

Examples:

```text
error: question node not found: q-014
error: relation cannot reference the same question twice
error: duplicate relation: q-010 -> q-011 [refines]
error: unknown relation_type: causes
error: unknown source type: chatgpt_memory
error: created_at must be a timezone-aware ISO timestamp
```

## 16. Error-handling contract

v0.4 is fail-fast.

It must reject:

- malformed JSON;
- malformed JSONL;
- unknown fields in domain payloads;
- missing required fields;
- empty required strings;
- unknown source values;
- unknown relation types;
- naive or invalid timestamps;
- duplicate node IDs;
- duplicate relation IDs;
- duplicate relation triples;
- self-relations;
- relation endpoints that do not exist;
- invalid depth parameters;
- unknown Context Pack target nodes.

It must not treat these as errors:

- a node with no profile;
- a node with no learning observation;
- a node with no relations;
- a valid graph cycle;
- an empty ancestor or descendant result.

## 17. Historical calibration corpus

Add:

```text
corpus/question-lineage-v0.4.jsonl
```

The first corpus represents the existing 12-question real chat sequence.

Requirements:

- all 12 historical questions appear as explicit `node` records;
- original wording is preserved;
- existing stable IDs are preserved;
- relationships are editorial calibration judgments, not truth labels;
- relation choices must be inspectable and manually reviewable;
- no relation is inferred automatically at import time.

The corpus should contain enough relation diversity to exercise the v0.4 vocabulary meaningfully without manufacturing edges solely for coverage.

## 18. Testing strategy

Implementation uses TDD.

Add focused tests:

```text
tests/test_lineage.py
tests/test_lineage_storage.py
tests/test_lineage_export.py
tests/test_lineage_graph.py
tests/test_context_pack.py
tests/test_lineage_cli.py
tests/test_lineage_calibration_v04.py
tests/test_lineage_e2e.py
```

### 18.1 Model tests

Must cover:

- valid `QuestionNode`;
- all four valid source values;
- invalid source;
- missing and unknown fields;
- blank text fields;
- valid timezone-aware timestamps;
- invalid/naive timestamps;
- valid `QuestionRelation`;
- all seven relation types;
- invalid relation type;
- self-relation rejection.

### 18.2 Storage tests

Must cover:

- node insert/get/list;
- relation insert/get/list;
- foreign-key enforcement;
- duplicate node ID rejection;
- duplicate relation ID rejection;
- duplicate relation triple rejection;
- self-relation database defense;
- deterministic retrieval order;
- atomic bundle insert;
- full rollback after one invalid relation in a larger import.

### 18.3 Graph tests

Must cover:

- ancestors;
- descendants;
- default conceptual depth behavior;
- explicit depth 0;
- multiple branches;
- cycles;
- no duplicate nodes in traversal output;
- deterministic ordering.

### 18.4 Context Pack tests

Must cover:

- missing current node;
- current node with no profile;
- current node with a v0.2 profile;
- v0.3 observations selected by evidence-ID intersection;
- observations excluded when no evidence ID intersects;
- assumptions aggregation;
- evidence-needed aggregation;
- existing-next-question aggregation;
- default 3/1 neighborhood;
- depth overrides;
- Markdown deterministic rendering;
- JSON deterministic rendering;
- empty sections represented explicitly;
- cycles do not alter deterministic output or cause recursion failure.

### 18.5 CLI tests

Must cover all new commands and expected error return behavior.

### 18.6 Calibration tests

Must verify:

- the v0.4 corpus contains exactly the expected 12 historical nodes;
- node IDs match the historical chat corpus IDs;
- every relation endpoint exists;
- all records validate;
- relation vocabulary stays inside the frozen seven values;
- corpus can be imported atomically.

### 18.7 End-to-end test

At least one E2E flow must execute:

```text
JSONL corpus
    ↓
atomic import
    ↓
SQLite
    ↓
graph traversal
    ↓
v0.2 profiles + v0.3 observations
    ↓
Context Pack
    ↓
Markdown + JSON
```

## 19. Regression requirements

Before merge:

- all 170 pre-v0.4 tests must remain passing;
- all new v0.4 tests must pass;
- existing v0.1 and v0.2 rubric files must remain byte-identical;
- no historical model contract may gain fields;
- no automatic migration may occur;
- `python -m compileall` must pass;
- `git diff --check` must pass;
- no local SQLite DB, `.env`, secret, or generated private data may be tracked.

There is currently no GitHub Actions workflow, so verification must be described accurately as local/test-suite verification rather than remote CI unless a workflow is added in a separately approved change.

## 20. Acceptance criteria

v0.4 is functionally complete when this workflow succeeds on a clean database:

```bash
question-radar lineage import corpus/question-lineage-v0.4.jsonl
question-radar lineage context chat-2026-08-29-012 --format markdown
question-radar lineage context chat-2026-08-29-012 --format json
```

The resulting Context Pack must:

- identify the exact current question;
- show its bounded lineage;
- show explicit relationships;
- include matching v0.2 profile data when present;
- include matching v0.3 learning signals when supported by evidence IDs;
- surface unresolved assumptions and evidence requirements from stored profiles;
- surface existing `next_question` values;
- preserve provenance;
- produce stable output across repeated identical runs;
- make no new epistemic inference.

The practical product criterion is that the Markdown output can be pasted into a future reasoning or LLM session and provide materially better structured context than the latest question alone.

## 21. Future directions explicitly deferred

Potential later versions may explore:

- question-pressure or recurrence analytics;
- unresolved-question persistence over time;
- lineage-based prompt templates;
- relevance ranking;
- semantic clustering;
- relation-confidence metadata;
- relation provenance/evaluator metadata;
- graph visualization;
- web UI;
- prompt-context budget optimization;
- Anti IA integration;
- import from structured conversation exports.

None of these are part of v0.4.

## 22. Design rationale

The design favors a small auditable graph over an intelligent black box.

`QuestionNode` is intentionally minimal so identity survives future rubric changes.

Relations are explicit because semantic lineage is itself evidence and should not be silently manufactured.

Cycles are allowed because reasoning is not always a tree.

Context Packs are derived rather than stored because they are views over current evidence, and persisting them would create duplicated state and synchronization problems.

The 3-ancestor / 1-descendant default provides enough local history for useful prompt context while bounding noise and output size.

The result is a foundation for studying how questions evolve and for improving future prompts while preserving Question Radar's central principle:

> **Questions are inspectable evidence. They are not a license to score or diagnose people.**
