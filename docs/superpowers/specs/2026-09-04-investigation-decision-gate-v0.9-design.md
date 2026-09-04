# Investigation Decision Gate v0.9 Design

## Purpose

Question Radar v0.9 adds a persistent, auditable decision layer for deciding which investigation should receive attention now, which should remain under bounded research, which should be parked, and which should be explicitly killed.

The immediate operational problem is not a shortage of questions. Question Radar already preserves question formulation, assumptions, evidence needs, lineage, retrieval context, novelty evidence, and benchmark behavior. The missing layer is the explicit transition from:

```text
interesting question
        ↓
should this consume attention now?
```

v0.9 records that decision without turning Question Radar into an autonomous prioritization engine.

## Version boundary

The repository already uses v0.8 for the Gold Evaluation Harness. Therefore this capability is introduced as **v0.9**.

v0.9 must preserve all historical contracts from v0.1 through v0.8. Existing question profiles, lineage, retrieval, novelty, benchmark evaluation, CLI commands, and SQLite tables remain backward compatible.

## Epistemic and authority boundary

The decision layer records an operator judgment. It does not claim that a question is objectively important, true, novel, valuable, or correctly prioritized.

The central rule is:

> **Evidence may inform a decision; Question Radar does not acquire authority to make that decision automatically.**

v0.9 may validate structure, preserve rationale, surface inconsistencies, derive the current decision from immutable history, and warn when the active work-in-progress limit is exceeded.

It must not automatically change `DO_NOW`, `RESEARCH`, `PARKED`, or `KILLED` based on a score, heuristic, retrieval result, LLM output, elapsed time, or gate combination.

## Domain model

### InvestigationDecision

Each decision is immutable and references an existing v0.4 `QuestionNode`.

```python
InvestigationDecision(
    id,
    question_id,
    decision,
    rationale,
    goal_alignment,
    external_signal,
    testable_now,
    leverage,
    cost,
    confidence,
    next_test,
    resume_when,
    kill_condition,
    supersedes_decision_id,
    created_at,
)
```

Required fields:

- `id`: non-empty stable identifier;
- `question_id`: id of an existing `QuestionNode`;
- `decision`: one of the closed v0.9 decision states;
- `rationale`: non-empty operator explanation;
- `goal_alignment`: explicit boolean gate;
- `external_signal`: explicit boolean gate;
- `testable_now`: explicit boolean gate;
- `leverage`: explicit boolean gate;
- `cost`: closed qualitative estimate;
- `confidence`: closed qualitative estimate;
- `next_test`: nullable bounded next investigation action;
- `resume_when`: nullable condition for reactivation;
- `kill_condition`: nullable explanation/condition related to abandonment;
- `supersedes_decision_id`: nullable prior decision id for the same question;
- `created_at`: timezone-aware ISO timestamp.

The model is deliberately qualitative. v0.9 does not compute a composite priority score.

## Closed vocabularies

Decision state:

```text
DO_NOW
RESEARCH
PARKED
KILLED
```

Cost:

```text
low
medium
high
```

Confidence:

```text
low
medium
high
```

These vocabularies are schema contracts, not rankings of the operator or guarantees about outcome quality.

## Decision semantics

### DO_NOW

The question is allowed to consume immediate execution time.

Additional structural requirement:

- `next_test` must be non-null and non-empty.

The gates remain descriptive evidence. v0.9 must not require all gates to be `true` and must not rewrite the operator's decision when a gate is `false`.

A `DO_NOW` record with `goal_alignment=false` is valid but should remain visible as a potentially inconsistent operator choice.

### RESEARCH

The question is allowed to consume bounded research effort before a stronger commitment is made.

Additional structural requirement:

- `next_test` must be non-null and non-empty.

v0.9 validates presence, not semantic quality. It must not attempt to determine whether text such as "investigate lithium" is sufficiently narrow using heuristics, embeddings, or LLM inference.

### PARKED

The question should not consume active attention until an explicit future condition is met.

Additional structural requirement:

- `resume_when` must be non-null and non-empty.

`PARKED` is not a hidden backlog or a weak form of `DO_NOW`. Its operational meaning is:

> No action is currently requested until the recorded return condition becomes relevant.

v0.9 does not monitor or automatically evaluate `resume_when`.

### KILLED

The current investigation path is explicitly abandoned.

Structural requirement:

- `rationale` remains mandatory;
- `kill_condition` is optional supporting context.

A killed decision is never deleted. New evidence may later justify a new decision that explicitly supersedes the killed record.

## Immutable decision history

Decision records are append-only.

Existing rows must never be updated to change state. A later judgment creates a new `InvestigationDecision` with `supersedes_decision_id` pointing to the decision it replaces.

Example:

```text
decision-001: SPQR -> DO_NOW
        ↓ superseded by
decision-002: SPQR -> PARKED
        ↓ superseded by
decision-003: SPQR -> RESEARCH
```

This preserves the original context instead of rewriting history.

## Supersession invariants

For each question, decision history is one linear chain.

1. The first decision for a question must have `supersedes_decision_id = null`.
2. Once a question has a decision, every later decision must supersede the exact current leaf.
3. The referenced decision must already exist.
4. The referenced decision must belong to the same `question_id`.
5. A decision cannot supersede itself.
6. One prior decision may be superseded by at most one direct successor.
7. Chains must remain acyclic.

These rules prevent both multiple roots and branching history such as:

```text
A -> B
A -> C
```

If history is inconsistent or cannot produce exactly one current leaf, the read path must fail closed instead of choosing a state heuristically.

## Current-decision projection

The current decision is derived from immutable history.

For a question with one valid chain, the current decision is the unique leaf that is not superseded by another decision.

No separate mutable `current_state` column or table is introduced.

This prevents divergence between historical records and the current projection.

## SQLite persistence

Add a new versioned table:

```text
investigation_decisions_v09
```

Canonical shape:

```sql
CREATE TABLE investigation_decisions_v09 (
    id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (
        decision IN ('DO_NOW','RESEARCH','PARKED','KILLED')
    ),
    rationale TEXT NOT NULL,
    goal_alignment INTEGER NOT NULL CHECK (goal_alignment IN (0,1)),
    external_signal INTEGER NOT NULL CHECK (external_signal IN (0,1)),
    testable_now INTEGER NOT NULL CHECK (testable_now IN (0,1)),
    leverage INTEGER NOT NULL CHECK (leverage IN (0,1)),
    cost TEXT NOT NULL CHECK (cost IN ('low','medium','high')),
    confidence TEXT NOT NULL CHECK (confidence IN ('low','medium','high')),
    next_test TEXT,
    resume_when TEXT,
    kill_condition TEXT,
    supersedes_decision_id TEXT UNIQUE,
    created_at TEXT NOT NULL,
    FOREIGN KEY (question_id) REFERENCES question_nodes_v04(id),
    FOREIGN KEY (supersedes_decision_id) REFERENCES investigation_decisions_v09(id),
    CHECK (supersedes_decision_id IS NULL OR supersedes_decision_id <> id)
)
```

The store must enable SQLite foreign keys.

Validation that depends on another row — one-root-only history, same-question supersession, current-leaf-only supersession, and cycle prevention — belongs in the storage/service layer rather than being approximated with database CHECK clauses.

## v0.4 prerequisite and fail-closed initialization

v0.9 depends on persisted question identity from Question Lineage v0.4.

Before creating or using `investigation_decisions_v09`, the decision store must verify that the configured SQLite database already contains the canonical `question_nodes_v04` table with the expected required columns.

If the v0.4 lineage table is missing or structurally unsupported, the decision command fails closed.

The v0.9 decision path must **not** call `QuestionLineageStore.initialize()` merely to make its prerequisite exist, because doing so would silently mutate an earlier domain layer.

Once the v0.4 prerequisite has been verified, v0.9 may create its own `investigation_decisions_v09` table.

An unknown `question_id` is rejected before decision insertion.

## Storage isolation

v0.9 must not modify historical schemas:

- `question_profiles_v02`;
- learning-frontier tables;
- `question_nodes_v04`;
- `question_relations_v04`;
- novelty/retrieval read paths;
- benchmark evaluation inputs.

The new decision store may share the same SQLite database file, but it owns only `investigation_decisions_v09`.

Creating the decision table must not migrate, rewrite, normalize, or backfill historical records.

## CLI surface

Add a new top-level command family:

```text
question-radar decision ...
```

The root help must expose `decision` without breaking historical CLI delegation.

### Record

```text
question-radar decision record
```

Purpose: append one immutable decision.

Required inputs:

```text
--question-id
--decision
--rationale
--goal-alignment true|false
--external-signal true|false
--testable-now true|false
--leverage true|false
--cost low|medium|high
--confidence low|medium|high
```

Conditional inputs:

- `DO_NOW` and `RESEARCH` require `--next-test`;
- `PARKED` requires `--resume-when`;
- `--kill-condition` is optional;
- `--supersedes` must be omitted for the first decision and is mandatory for every revision.

Audit metadata:

- `--id` is optional; when omitted, the CLI generates `dec-<uuid4-hex>` using Python's standard-library `uuid` module;
- `--created-at` is optional; when omitted, the CLI uses the current UTC instant from `datetime.now(timezone.utc).isoformat()`;
- tests and explicit imports may supply both values to make fixtures reproducible.

If a question already has a current decision, `record` must reject a new independent decision and require the caller to supply the exact current decision id via `--supersedes`.

This makes revision explicit rather than silently overwriting prior judgment.

### Show

```text
question-radar decision show <question_id>
```

Returns the current decision projection for one question.

If no decision exists, report that no investigation decision has been recorded.

If history is ambiguous or corrupted, fail closed with an explicit error.

### History

```text
question-radar decision history <question_id>
```

Returns every decision for the question in deterministic chronological order, preserving supersession ids and rationale.

Ordering uses the existing timezone-aware timestamp normalization rule and then decision id as a deterministic tie-breaker.

### Active

```text
question-radar decision active
```

Returns current decision projections whose state is:

```text
DO_NOW
RESEARCH
```

It also reports aggregate current-state counts for:

```text
DO_NOW
RESEARCH
PARKED
KILLED
```

When no decisions exist, all aggregate counts are zero and the active list is empty.

## Rendering

Support deterministic Markdown and JSON output for `show`, `history`, and `active`.

Markdown should emphasize operator meaning rather than imply machine authority.

Example parked rendering:

```text
Current decision: PARKED
Decision: dec-2026-09-04-001

Why:
High learning value, no current production need.

Resume when:
A real PostgreSQL workload requires horizontal scaling.

Gates:
✓ external signal
✓ leverage
✗ current goal alignment
✗ testable now

No action is currently requested.
```

JSON must expose the raw validated contract and derived current-state metadata without inventing semantic interpretations.

## Work-in-progress projection

v0.9 introduces a deterministic advisory WIP rule:

```text
recommended_do_now_limit = 3
```

When the current projection contains more than three `DO_NOW` investigations, `decision active` must emit a warning such as:

```text
WARNING: 4 investigations are marked DO_NOW.
Recommended operating limit: 3.
No decision was changed automatically.
```

The limit is advisory only.

v0.9 must not:

- reject the fourth `DO_NOW` record;
- demote an existing decision;
- choose which investigation should be parked;
- alter records automatically.

The warning exists to make attention saturation visible while preserving operator authority.

## Gate semantics

The four v0.9 gates are deliberately simple booleans:

### goal_alignment

Is the investigation connected to an explicit current objective?

### external_signal

Is there an external observation, actor, event, problem, request, or other real-world signal motivating investigation?

### testable_now

Can uncertainty be reduced through a bounded next test using currently available resources?

### leverage

Could resolving this uncertainty unlock or materially inform additional work?

These are operator judgments. v0.9 stores them as explicit context and does not infer them from question text, retrieval results, linked evidence, or external providers.

## Cost and confidence

`cost` is a qualitative estimate of effort/attention required for the next investigation step.

`confidence` describes the operator's confidence in the decision itself, not confidence that the underlying hypothesis is true.

Therefore:

```text
priority != certainty
```

A high-priority question may legitimately have low confidence, and a highly certain conclusion may legitimately remain parked.

## Duplicate-id behavior

Decision ids are immutable primary keys.

Any attempt to insert an already-existing `InvestigationDecision.id` fails with an explicit duplicate-id error, regardless of whether the incoming payload matches the stored payload.

v0.9 does not treat duplicate writes as idempotent success. Callers that need retry-safe behavior must retain the original successful result instead of replaying the same create operation.

This strict rule keeps append-only semantics simple and avoids a second equality contract in v0.9.

## Error handling

All invalid writes must fail closed before persistence where possible.

Representative failures include:

- missing or unsupported v0.4 lineage prerequisite;
- unknown `question_id`;
- unknown decision/cost/confidence value;
- blank rationale;
- missing `next_test` for `DO_NOW` or `RESEARCH`;
- missing `resume_when` for `PARKED`;
- supplying `--supersedes` for the first decision;
- omitting `--supersedes` for a revision;
- superseding a decision from another question;
- superseding a non-current decision;
- attempting to create a second independent root/current decision;
- duplicate decision id;
- malformed timestamp;
- ambiguous decision chain.

No validation failure grants permission to repair or rewrite historical rows automatically.

## Relationship to existing Question Radar layers

The conceptual stack becomes:

```text
QuestionProfile v0.2
    what kind of question is this?

Learning Frontier v0.3
    what learning observation is supported?

Question Lineage v0.4
    how does this question relate to explicit prior questions?

Novelty / Retrieval v0.5-v0.7
    what prior corpus questions should be reviewed?

Gold Evaluation v0.8
    how well does retrieval match frozen editorial expectations?

Investigation Decision Gate v0.9
    should this question consume attention now, bounded research,
    no current action, or explicit abandonment?
```

The new layer consumes question identity but does not alter the semantics of earlier layers.

## Relationship to external systems

v0.9 remains local and self-contained.

It does not directly integrate with:

- GeoPlatform Knowledge Base / Vault;
- Opportunity OS;
- Andes Context OS;
- Gmail;
- GitHub issues/PRs;
- schedulers or automations;
- external LLMs;
- remote databases.

Those systems may later supply operator context, but they do not enter the v0.9 core contract.

## Non-goals

v0.9 must not add:

- automatic prioritization;
- RICE or weighted scoring;
- numerical priority scores;
- Opportunity Solution Trees as a persisted model;
- automatic hypothesis validation;
- semantic quality checks on `next_test`;
- embeddings;
- vector search;
- LLM runtime calls;
- agents;
- dashboards or web UI;
- automatic `PARKED` reactivation;
- calendar/task scheduling;
- evidence fetching;
- background monitoring;
- changes to retrieval ranking;
- changes to v0.8 gold evaluation;
- new runtime dependencies.

Runtime dependencies remain empty: `dependencies = []`.

## Testing strategy

Implementation must follow TDD and add focused test modules for:

1. `InvestigationDecision` contract validation and round-trip serialization;
2. state-specific requirements (`next_test`, `resume_when`);
3. v0.4 prerequisite verification without silent lineage initialization;
4. SQLite v0.9 schema creation and foreign-key enforcement;
5. immutable insert behavior and strict duplicate-id rejection;
6. one-root-only history per question;
7. same-question supersession validation;
8. current-leaf-only supersession;
9. acyclic history and ambiguity failure;
10. deterministic current projection;
11. deterministic chronological history;
12. active-state filtering and zero-decision output;
13. WIP warning above three `DO_NOW` decisions;
14. no automatic decision changes from WIP warnings;
15. deterministic Markdown/JSON rendering;
16. CLI metadata generation plus injectable `--id` / `--created-at`;
17. CLI record/show/history/active behavior;
18. root-help discoverability;
19. regression verification across the complete historical suite.

Historical tests must remain unchanged unless a root-help assertion legitimately needs to include the new command while preserving all previous commands.

## Acceptance criteria

1. `InvestigationDecision` is an immutable validated contract.
2. Only `DO_NOW`, `RESEARCH`, `PARKED`, and `KILLED` are accepted decision states.
3. Decisions reference existing v0.4 question nodes and the decision path fails closed when the v0.4 prerequisite is absent.
4. v0.9 initializes only its own table and never silently initializes or migrates historical layers.
5. Decisions are append-only; revision occurs only through explicit supersession.
6. Each question has exactly one root and at most one current leaf.
7. Supersession is same-question, current-leaf-only, unique, and acyclic.
8. Current state is derived from immutable history, not stored separately.
9. `DO_NOW` and `RESEARCH` require an explicit `next_test`.
10. `PARKED` requires an explicit `resume_when` condition.
11. Gates are stored explicitly but never determine the decision automatically.
12. Duplicate decision ids are rejected strictly.
13. `decision active` exposes current WIP and warns when `DO_NOW > 3` without changing state.
14. Markdown and JSON outputs are deterministic and authority-preserving.
15. No external provider, LLM, scheduler, scoring engine, or runtime dependency is introduced.
16. Existing v0.1-v0.8 behavior and tests remain green.
17. The final implementation is dogfooded with at least three real investigations representing different states before the feature is considered complete.

## Initial dogfood cases

The implementation should be exercised with operator-created question nodes representing at least:

- SPQR infrastructure investigation -> likely `PARKED` unless a current production workload justifies activation;
- lithium / GeoAI problem discovery -> likely `RESEARCH` with a bounded evidence-gathering next test;
- one current revenue/job-search or product investigation -> candidate `DO_NOW`.

These are dogfood scenarios, not hard-coded product behavior. The repository must not encode personal decisions or private operator state in public fixtures unless explicitly sanitized and fictionalized.

## Design principle

The feature exists to reduce open-loop attention without suppressing curiosity.

The intended operating loop is:

```text
question
   ↓
explicit decision
   ↓
DO_NOW / RESEARCH / PARKED / KILLED
   ↓
bounded action or deliberate non-action
   ↓
new evidence
   ↓
new immutable decision when judgment changes
```

The core distinction is:

> **Preserving a question is not the same as committing attention to it.**
