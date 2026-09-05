# Question Radar — Roadmap

Question Radar exists to preserve useful questions, expose what they need, connect them to prior inquiry and let a human decide whether they deserve attention.

The project does **not** aim to maximize the number of questions, rank people by curiosity, or turn every interesting signal into work.

The design rule is:

> preserve the question, expose the evidence boundary, and keep semantic or action authority explicit.

## How to read the versions

The `v0.x` labels below are **public contract milestones**, not Python package semantic-version releases. The package metadata remains intentionally conservative while the research contracts evolve additively.

---

## Implemented

### ✅ v0.1 — Historical Question Evaluation

The original five-dimension question rubric and historical CLI/storage contract.

This layer remains frozen for compatibility. Later versions do not silently reinterpret old evaluations.

### ✅ v0.2 — Question Profile

Separates question type and readiness from formulation quality.

Adds explicit:

- question types;
- readiness states;
- formulation dimensions;
- assumptions;
- evidence requirements;
- possible next question;
- local SQLite persistence and public calibration data.

Boundary:

```text
formulation score != score of a person
```

### ✅ v0.3 — Personal Learning Frontier

Adds revisable `LearningObservation` records grounded in explicit question IDs.

Boundary:

```text
repeated question != proven learning gap
```

A recurring concept may reflect missing evidence, disagreement, a weak prior explanation, changed context or a genuine learning gap. The system records an observation; it does not diagnose the learner.

### ✅ v0.4 — Question Lineage + Context Pack

Makes the question a stable entity and adds explicit directed relations:

```text
refines
decomposes
generalizes
operationalizes
challenges_assumption
contrasts
follows_from
```

Adds bounded, cycle-safe traversal and deterministic Context Packs.

Relations remain reviewed editorial judgments. No automatic semantic graph is written.

### ✅ v0.5 — Corpus-Relative Novelty

Adds deterministic read-only lexical comparison against v0.4 lineage using frozen token/bigram Jaccard evidence.

It surfaces nearest questions, shared terms, residual terms and provisional review prompts.

Boundary:

```text
lexical neighborhood != semantic equivalence
novelty prompt != automatic lineage
```

### ✅ v0.6 — Unified Candidate Retrieval

Expands read-only retrieval across both v0.2 profiles and v0.4 question nodes.

Adds dependency-free BM25 plus inspectable token contributions while preserving v0.5 evidence as a secondary signal.

No unified persistence table is created.

### ✅ v0.7 — Retrieval Calibration & Abstention

Improves retrieval evidence without adding a semantic black box.

Adds:

- retrieval-specific normalization;
- narrow noun-focused Spanish plural handling;
- query coverage;
- zero-evidence filtering;
- explicit `no_lexical_evidence` abstention.

Boundary:

```text
retrieval hit != semantic equivalence
abstention != proof of novelty
```

### ✅ v0.8 — Gold Evaluation Harness

Freezes an auditable evaluation layer around retrieval before any future semantic layer is considered.

Adds Hit Rate, Recall, MRR, false-abstention accounting and deterministic evidence exports.

Sparse editorial judgments remain sparse: unjudged entries are not silently treated as negatives.

Boundary:

```text
gold judgment != ground truth
```

### ✅ v0.9 — Investigation Decision Gate

Adds an explicit operator-controlled attention decision:

```text
DO_NOW
RESEARCH
PARKED
KILLED
```

Decisions are immutable and append-only. Changed judgment supersedes the current decision without rewriting history.

`DO_NOW` and `RESEARCH` require a concrete next test. `PARKED` requires a resume condition.

Boundary:

```text
interesting question != priority
decision != automatic action
```

### ✅ Cross-Repo Research Handoff v0.1

Adds a strict producer-side boundary for continuing an explicitly authorized investigation in another independent repository.

Supported routes:

```text
TERRITORIAL_RESEARCH          -> andes-context-os
PUBLIC_CONTRIBUTION_RESEARCH -> opportunity-os
```

Only current `DO_NOW` / `RESEARCH` decisions can export.

The artifact is deterministic and versioned. It preserves question identity, current decision identity, decision fingerprint, constraints and export time.

It does **not** call downstream repositories and does not create downstream state.

Boundaries:

```text
question != problem
route != opportunity
handoff != evidence
current at export != current now
```

The implementation was merged in PR #22 and its question/decision identity boundary was hardened in PR #24.

---

## Current system shape

```text
question
  ↓
profile / readiness / evidence needs
  ↓
lineage + prior context
  ↓
read-only retrieval / novelty evidence
  ↓
human review
  ↓
InvestigationDecision
  ↓
┌──────────┬──────────┬──────────┬──────────┐
│ DO_NOW   │ RESEARCH │ PARKED   │ KILLED   │
└────┬─────┴────┬─────┴──────────┴──────────┘
     │          │
     └────┬─────┘
          ↓
optional explicit handoff
     ↙                 ↘
Andes Context OS     Opportunity OS
```

The three repositories remain independent. Integration is through strict JSON artifacts, not shared runtime imports, a shared database, RPC or an orchestration service.

---

## Current dogfood / problem discovery

Recent public dogfood is intentionally allowed to produce uncertainty rather than features.

### San Juan water questions

Public project signals around hyperspectral crop-water stress and basin monitoring are preserved as **question seeds**, not as validated needs.

The next useful tests are operational:

- what recurrent decision actually changes;
- who makes that decision;
- what lead time matters;
- what evidence is missing;
- who validates the signal;
- what authority turns an observation into action or no-action.

Boundary:

```text
project proposal != deployed system
technology capability != validated operational need
monitoring != actionable decision
interesting actor != problem owner
problem owner != buyer
```

### Agent-network / external-signal questions

Public discussions may generate useful questions about authority, freshness or handoff design, but:

```text
social post != evidence
agent consensus != ground truth
interesting question != feature request
```

A research seed can end with “no change justified”.

---

## Near-term direction

These are research directions, **not release promises**.

### 1. Keep the handoff contract exercised, not merely documented

Use additional sanitized cases to test whether Question Radar exports enough context for downstream research without leaking semantic authority.

A valid result may remain `WATCH`, `DISCARD` or `NO_ACTIONABLE_CANDIDATE` downstream.

### 2. Improve retrieval only when benchmarks justify it

The lexical stack has known false negatives. v0.8 intentionally froze an evaluation baseline before introducing any semantic candidate layer.

Any future semantic retrieval work should therefore be justified against the frozen benchmark and preserve inspectable evidence and human review.

No embedding/vector/LLM layer should be added merely because it is available.

### 3. Separate research artifacts from product claims

Continue keeping:

- blind benchmarks;
- gold judgments;
- dogfood;
- external question seeds;
- canonical lineage;

as distinct artifacts with distinct authority.

### 4. Keep documentation synchronized with merged behavior

README should explain the current product. This roadmap should carry milestone history. Detailed design and implementation records remain under `docs/superpowers/`.

---

## Later, only with evidence

Possible future directions include:

- a semantic candidate-retrieval layer evaluated against the frozen v0.8 baseline;
- stronger corpus maintenance / archival workflows;
- better human review ergonomics around lineage and decisions;
- additional explicit handoff routes if a real downstream research workflow requires them;
- richer descriptive reporting over question/decision history without turning it into a person score.

None should enter merely because the architecture can support it.

---

## Out of scope by design

Question Radar is not trying to become:

- an automatic learner ranking system;
- an intelligence or curiosity score;
- an automatic semantic-equivalence engine;
- an autonomous master-question curator;
- a generic agent orchestrator;
- an automatic feature-request generator;
- a job/opportunity detector;
- a contact/outreach system;
- a background monitor that reactivates work automatically;
- a shared database between Question Radar, Andes Context OS and Opportunity OS.

The invariant remains:

> **A system may help preserve, compare, retrieve and route a question. The semantic judgment about what it means and the authority to act on it remain explicit.**
