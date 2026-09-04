# Cross-Repo Problem → Opportunity Handoff V0.1 Design

## Status

Design-only specification for a bounded integration across:

- `question-radar`
- `andes-context-os`
- `opportunity-os`

This document defines handoff contracts, routing, authority boundaries and two dogfood paths. It does not authorize runtime implementation, cross-repo imports, outreach, contact discovery, sending, applying, or autonomous GitHub mutation.

## Goal

Turn a high-value question into a traceable investigation and, only when evidence supports it, into a bounded opportunity or contribution candidate without collapsing question, signal, evidence, hypothesis, actor, opportunity, or action authority into the same thing.

```text
question
  ↓
explicit investigation decision
  ↓
versioned handoff
  ↓
territorial research when required
  ↓
versioned opportunity candidate
  ↓
Opportunity OS read-only preview
  ↓
human disposition
```

## Product Questions

The integration is organized around three operator questions:

1. **What decision is actually being made?**
2. **What evidence could change that decision?**
3. **Who has that problem and enough incentive to act?**

These remain questions for investigation and judgment. V0.1 does not convert them into a global score.

## Core Boundaries

```text
question != problem
signal != evidence
evidence != conclusion
actor != problem owner
problem owner != buyer
movement != need
need != confirmed demand
opportunity hypothesis != confirmed opportunity
public issue != job opening
PR opened != employment interest
opportunity != permission to contact
draft != send
```

No handoff may silently strengthen epistemic or action authority.

## Repository Responsibilities

### Question Radar

Owns inquiry structure and attention decisions:

- stable question identity and lineage;
- assumptions;
- evidence requirements;
- stronger next questions;
- explicit `DO_NOW / RESEARCH / PARKED / KILLED` decisions;
- operator-authored `next_test`.

It does not decide that a real-world need, buyer or contribution opportunity exists.

### Andes Context OS

Owns territorial research boundaries:

- `ResearchIntent`;
- territorial scope;
- registered sources and runtime observations;
- evidence candidates and quality vectors;
- missing / contradictory context;
- actor and movement interpretation;
- conservative `OpportunityHypothesis` state.

It does not decide that a hypothesis is a job, procurement package, buyer commitment, or contact permission.

### Opportunity OS

Owns action-oriented opportunity state:

- real vacancies;
- target accounts;
- public GitHub contribution entries;
- relationship context;
- bounded contribution lifecycle;
- read-only preview / explicit import boundaries;
- evidence-backed application and outreach preparation.

It does not infer that research grants send, apply, follow-up or contribution authority.

## Architectural Decision

V0.1 uses **versioned JSON artifacts as handoff contracts**.

V0.1 explicitly rejects:

- Python imports across repositories;
- a shared runtime package;
- a shared database;
- a central orchestration service;
- cross-repo RPC;
- automatic chaining;
- background workers;
- event buses;
- direct external actions.

Each repository remains independently installable, testable and understandable.

A handoff is a snapshot exported by one repository and strictly validated by another. It is not shared live state.

## Routing

Not every question traverses all three repositories.

```text
Question Radar
     ↓
InvestigationDecision
     ↓
operator-confirmed route
  ┌──┴─────────────────────────────┐
  │                                │
territorial / mining /         public software /
water / environment            GitHub contribution
  │                                │
  ▼                                │
Andes Context OS                   │
  │                                │
  └────────────────┬───────────────┘
                   ▼
             Opportunity OS
```

### Route vocabulary V0.1

```text
TERRITORIAL_RESEARCH
PUBLIC_CONTRIBUTION_RESEARCH
```

No automatic classifier chooses a route in V0.1. The operator supplies and confirms it.

### Territorial route

Use Andes Context OS when the question materially depends on territorial scope, geoscience / environmental evidence, project movement, operational context or actor interpretation.

Examples:

- recurrent water-management decisions in San Juan;
- remote-sensing signals that could change a field decision;
- mining project movements that may indicate a bounded service need;
- environmental / access / logistics research tied to explicit territory.

### Direct public-contribution route

Question Radar may route directly toward Opportunity OS contribution research when the problem is already expressed through a public software contribution surface.

Examples:

- explicit GitHub issue;
- maintainer-stated help wanted;
- collaboration call;
- repository research that yields a bounded candidate task.

A direct route does not imply availability, fit, permission to work on the task, or employment interest.

# Contract 1 — Question → Research Handoff

Canonical identifier:

```text
question-research-handoff/v0.1
```

## Schema

```json
{
  "contract": "question-research-handoff/v0.1",
  "handoff_id": "qrh:2026-09-04:001",
  "created_at": "2026-09-04T20:30:00-03:00",
  "source": {
    "system": "question-radar",
    "question_id": "question:001",
    "question_profile_ref": "profile:001",
    "decision_id": "decision:001",
    "decision_fingerprint": "sha256:..."
  },
  "question": {
    "raw": "¿Qué decisión hídrica recurrente podría mejorar con evidencia territorial o satelital?",
    "canonical": "¿Qué decisión hídrica recurrente en San Juan podría mejorar mediante evidencia territorial o satelital?"
  },
  "investigation": {
    "decision": "RESEARCH",
    "rationale": "Existe señal externa y la pregunta es testeable sin asumir demanda.",
    "next_test": "Identificar una decisión recurrente concreta, su owner y la evidencia usada actualmente."
  },
  "routing": {
    "kind": "TERRITORIAL_RESEARCH",
    "destination": "andes-context-os"
  },
  "constraints": [
    "No inferir buyer desde actor observado.",
    "No convertir señal pública en necesidad confirmada."
  ]
}
```

`question_profile_ref` is nullable. It is populated only when the exported question has an explicit compatible profile reference.

## Required semantics

- `source.question_id` identifies an existing Question Radar question.
- `source.decision_id` identifies the explicit investigation decision used for export.
- `decision_fingerprint` deterministically identifies that decision payload / lineage state at export time.
- `investigation.decision` must be `DO_NOW` or `RESEARCH`.
- `investigation.next_test` must be non-empty.
- `routing.kind` must use the V0.1 closed vocabulary.
- `PARKED` and `KILLED` cannot produce an actionable handoff.
- the source exporter must verify the selected decision is current at the moment of export.
- the handoff does not claim that the destination can answer the question.

## Freshness Semantics

A JSON handoff is **current as of export**, not a live authorization lease.

```text
current_at_export != current_now
```

Because V0.1 intentionally has no cross-repo RPC, the destination cannot prove that no newer Question Radar decision exists.

Therefore:

- Question Radar verifies currentness before export;
- the artifact preserves `decision_id`, `decision_fingerprint` and `created_at`;
- destinations show `source_freshness = AS_OF_EXPORT` in previews;
- no destination may describe the artifact as live/current source authority;
- an operator may re-export when a newer source decision is suspected or known.

V0.1 does not invent a network freshness check merely to eliminate this limitation.

# Andes Context OS Intake

For `TERRITORIAL_RESEARCH`, Contract 1 may seed a new Andes `ResearchIntent`.

## Exact mapping

```text
question.raw               → ResearchIntent.question_raw
question.canonical         → ResearchIntent.question_canonical
source.question_profile_ref → ResearchIntent.question_profile_ref
constraints[]              → ResearchIntent.constraints
```

`ResearchIntent.goal` is operator-supplied from `investigation.next_test` or an explicitly refined research goal. The intake preview must display that choice before creating the intent.

The destination must still receive explicit:

- `domain`;
- `activity`;
- territorial scope.

It must not guess them from free text.

The handoff is context, not evidence.

## Andes ResearchActivity compatibility gap

The current Andes `ResearchDomain` includes `water`, but the current `ResearchActivity` vocabulary is operationally narrow and has no semantically correct activity for the primary water-management decision-support dogfood.

Using `FIELD_OPERATIONS`, `ROUTE_PLANNING` or another existing activity merely to satisfy validation would corrupt the meaning of the research record.

V0.1 therefore includes one additive Andes contract change:

```text
DECISION_SUPPORT = "decision_support"
```

This is deliberately generic rather than water-specific. It supports a research task whose purpose is to assemble evidence for a recurring decision without claiming field operations, route planning or procurement.

Compatibility requirement:

- existing activity values remain unchanged;
- existing serialized records remain valid;
- no existing behavior is reinterpreted;
- tests must prove the new value is additive only.

# Contract 2 — Research → Opportunity Handoff

Canonical identifier:

```text
research-opportunity-handoff/v0.1
```

Contract 2 is a tagged union with exactly two V0.1 candidate kinds:

```text
ACTOR_NEED_HYPOTHESIS
PUBLIC_CONTRIBUTION_CANDIDATE
```

The kind determines the required payload and legal Opportunity OS disposition.

## Candidate A — ACTOR_NEED_HYPOTHESIS

Used for Andes territorial research.

```json
{
  "contract": "research-opportunity-handoff/v0.1",
  "handoff_id": "roh:2026-09-04:001",
  "created_at": "2026-09-04T22:00:00-03:00",
  "source": {
    "system": "andes-context-os",
    "source_question_ref": "question:001",
    "research_intent_ref": "intent:water-sj:001",
    "hypothesis_ref": "hypothesis:water-sj:001"
  },
  "candidate": {
    "kind": "ACTOR_NEED_HYPOTHESIS",
    "need_category": "water_decision_support",
    "statement": "A recurrent provincial water-management workflow may benefit from consolidated territorial evidence.",
    "actor_refs": ["actor:example"],
    "evidence_refs": ["evidence:001", "evidence:002"],
    "assumptions": [
      "The identified actor owns or materially influences the decision."
    ],
    "missing_context": [
      "Current workflow owner",
      "Current evidence assembly cost",
      "Procurement or collaboration path"
    ],
    "research_status": "researching"
  }
}
```

### Semantics

- source hypothesis state is preserved verbatim;
- `researching` is never promoted to `supported` by export/import;
- `actor_refs` may be empty;
- empty actors prevent actor-oriented dispositions but do not invalidate research;
- `assumptions` and `missing_context` are required fields even when empty;
- evidence references remain references, not copied source bodies;
- no field asserts willingness to pay, procurement intent, hiring intent or contact permission.

## Candidate B — PUBLIC_CONTRIBUTION_CANDIDATE

Used by the direct GitHub path.

```json
{
  "contract": "research-opportunity-handoff/v0.1",
  "handoff_id": "roh:2026-09-04:002",
  "created_at": "2026-09-04T22:10:00-03:00",
  "source": {
    "system": "question-radar",
    "source_question_ref": "question:002",
    "research_intent_ref": null,
    "hypothesis_ref": null
  },
  "candidate": {
    "kind": "PUBLIC_CONTRIBUTION_CANDIDATE",
    "repository_full_name": "example/project",
    "repository_url": "https://github.com/example/project",
    "origin": "PUBLIC_ISSUE",
    "need_basis": "MAINTAINER_STATED",
    "need_statement": "Add support for the documented geospatial format.",
    "evidence_refs": ["github:example/project/issues/42"],
    "task_ref": "github:example/project/issues/42",
    "bounded_task": "Implement the explicitly requested format support.",
    "task_claim_state": "AVAILABLE",
    "expected_effort": "S",
    "risk_level": "LOW"
  }
}
```

### Semantics

The payload must preserve only facts supported by public evidence:

- repository identity;
- public source reference;
- `OBSERVED`, `MAINTAINER_STATED` or `HYPOTHESIZED` need basis;
- task reference only when an explicit public task exists;
- availability / claim state only when observed;
- bounded task only when defensible;
- effort / risk may remain `UNKNOWN`.

Existing Opportunity OS contribution invariants remain authoritative:

```text
PUBLIC_CONTRIBUTION_ENTRY != JOB_OPENING
PR_OPENED != EMPLOYMENT_INTEREST
PR_MERGED != EMPLOYMENT_INTEREST
GOOD_PROBLEM != AVAILABLE_PROBLEM
```

# Opportunity OS Intake Boundary

Every Contract 2 artifact is a **candidate observation** first.

```text
handoff artifact
      ↓
strict validation
      ↓
read-only normalized preview
      ↓
evidence + assumptions + missing context
      ↓
explicit operator disposition
```

## Territorial candidate disposition

For `ACTOR_NEED_HYPOTHESIS`, V0.1 does **not** create a new generic actor/opportunity persistence model.

Legal preview dispositions are:

```text
RESEARCH_ACTOR
WATCH
DISCARD
```

These are preview outcomes only in V0.1. They do not create a `TargetAccount`, Relationship record, outreach brief or draft.

If later evidence shows that an organization independently satisfies an existing Opportunity OS domain contract, it may enter that domain through that domain's normal intake path. The cross-repo handoff itself does not coerce it.

`PREPARE_COLLABORATION` is intentionally deferred because Opportunity OS currently has no dedicated territorial-collaboration persistence contract. Adding one would require a separate design.

## Public contribution disposition

For `PUBLIC_CONTRIBUTION_CANDIDATE`, the preview may offer:

```text
IMPORT_PUBLIC_CONTRIBUTION
WATCH
DISCARD
```

`IMPORT_PUBLIC_CONTRIBUTION` is legal only when the existing `PublicContributionEntry` contract can be satisfied without inventing fields.

Import must remain behind explicit operator confirmation and existing contribution-bridge stale / conflict protections.

## Actor semantics

Territorial research can identify organizations that are not employment target accounts.

Examples:

- provincial water authority;
- environmental regulator;
- mine operator;
- public research institute;
- municipality;
- supplier;
- university group.

V0.1 carries actor references without forcing persistence into `TargetAccount`.

# Provenance

Every handoff contains:

- contract identifier and version;
- handoff identity;
- source system;
- source domain identifiers;
- creation timestamp;
- source snapshot / fingerprint where applicable;
- evidence references wherever evidence claims are made.

Handoffs must not copy:

- credentials;
- provider tokens;
- Gmail bodies;
- private candidate profiles;
- private actor contact data;
- unrestricted internal notes;
- local SQLite databases;
- raw authorized private-source content.

Public fixtures use sanitized or public evidence only.

# Determinism

Given the same canonical source records, an export serializes deterministically except for explicitly supplied handoff identity and creation timestamp.

Rules:

- UTF-8 JSON;
- stable key ordering;
- strict closed vocabularies;
- unknown fields fail closed;
- unsupported contract versions fail closed;
- no fuzzy actor / project matching during intake;
- no inferred neighboring resources;
- no automatic route inference.

# Failure Modes

## Source decision superseded after export

The artifact remains a valid historical snapshot but cannot claim live source authority. The preview exposes `AS_OF_EXPORT` freshness. Re-export is the V0.1 refresh mechanism.

## Unsupported route

Fail closed.

## Missing territorial scope

Contract 1 may seed an intake preview, but Andes cannot create a defensible territorial research run until explicit scope is supplied.

## Missing / invalid Andes domain or activity

Fail closed. The importer does not infer them from question text.

## Missing actor

Research may continue. `RESEARCH_ACTOR` is unavailable when there is no actor reference to research; the valid outcomes are `WATCH` or `DISCARD`.

## Evidence reference unavailable

The preview identifies the missing reference and blocks any path whose contract requires that evidence. It does not guess a replacement.

## Hypothesis state unsupported

Preserve source state or fail closed. Never upgrade or downgrade silently.

## GitHub task claimed or closed

Preserve observed claim state. A good but unavailable problem remains unavailable.

# Primary Dogfood — San Juan Water Decision

Question:

> **¿Qué decisión recurrente relacionada con agua en San Juan podría mejorar utilizando evidencia territorial o satelital, quién toma hoy esa decisión y qué información le falta?**

## Step A — Question Radar

Expected:

- stable question identity;
- assumptions;
- evidence requirements;
- stronger / bounded next question when needed;
- `RESEARCH` or `DO_NOW`;
- explicit `next_test`;
- `question-research-handoff/v0.1` export.

Success is a defensible reason to investigate plus a concrete next test, not a high formulation score.

## Step B — Andes Context OS

Explicit intake choices for this dogfood:

```text
domain   = water
activity = decision_support
```

Territorial scope must be explicitly selected; `San Juan` in the question is a hint, not automatically a valid `TerritorialScope` record.

Expected research slice:

- one explicit territorial scope;
- one recurrent decision candidate;
- public source registry usage;
- evidence candidates with provenance;
- candidate actors when evidence supports them;
- explicit missing context;
- zero or more conservative `OpportunityHypothesis` records.

Success is separating observed evidence from interpretation.

## Step C — Opportunity OS

If Andes emits one defensible `ACTOR_NEED_HYPOTHESIS`, Opportunity OS previews:

- source question lineage;
- candidate actor / need;
- evidence refs;
- assumptions;
- missing context;
- `AS_OF_EXPORT` source freshness;
- one explicit disposition: `RESEARCH_ACTOR`, `WATCH` or `DISCARD`.

No contact is created or sent.

### Legitimate zero-candidate outcome

Real dogfood is allowed to conclude that no defensible opportunity candidate exists.

```text
no supported candidate != failed research
```

If Andes emits no candidate, the live dogfood terminates with an explicit `NO_ACTIONABLE_CANDIDATE` research outcome outside Opportunity OS.

That outcome validates epistemic discipline but does not exercise Contract 2 intake. Contract 2 is therefore also covered by sanitized deterministic fixtures so integration correctness does not depend on forcing the live research to discover an opportunity.

# Secondary Dogfood — Public GitHub Contribution

Question:

> **¿Qué problema público de software geoespacial puedo resolver en un repositorio externo donde exista una tarea explícita y disponible?**

Expected path:

```text
Question Radar
  ↓
PUBLIC_CONTRIBUTION_RESEARCH
  ↓
public GitHub evidence
  ↓
research-opportunity-handoff/v0.1
candidate.kind = PUBLIC_CONTRIBUTION_CANDIDATE
  ↓
Opportunity OS preview
  ↓
IMPORT_PUBLIC_CONTRIBUTION only if existing contract is satisfied
```

Andes Context OS is intentionally absent.

`TASK_READY` may be projected only when explicit public evidence supports task availability / self-claim semantics under the existing Opportunity OS contribution model.

# Testing Strategy

V0.1 uses focused regression tests inside each repository, not a new cross-repo test framework.

## Question Radar

Minimum coverage:

- valid Contract 1 export from current `DO_NOW` / `RESEARCH`;
- reject `PARKED` / `KILLED` actionable export;
- reject unknown route;
- deterministic serialization;
- preserve question/profile/decision refs;
- deterministic decision fingerprint;
- exporter verifies decision currentness at export time.

## Andes Context OS

Minimum coverage:

- additive `decision_support` activity accepts new records without altering historical values;
- strict Contract 1 intake validation;
- exact mapping into `ResearchIntent` without guessing domain/activity/scope;
- fail closed on unsupported contract version;
- preserve source question profile reference when present;
- deterministic `ACTOR_NEED_HYPOTHESIS` export;
- preserve hypothesis status, evidence refs, assumptions and missing context.

## Opportunity OS

Minimum coverage:

- strict Contract 2 tagged-union validation;
- preview is read-only;
- territorial actor is never coerced into `TargetAccount`;
- territorial preview has no send/apply/follow-up/import authority;
- direct contribution mapping preserves need basis and claim state;
- contribution import available only when existing `PublicContributionEntry` validates;
- missing evidence blocks evidence-dependent import;
- PR / merge never becomes employment-interest evidence.

Each repository must keep its existing full suite and compile checks green.

# Security and Privacy

- no credentials or provider tokens in handoffs;
- no email bodies;
- no private candidate profile content;
- no private contact details in public fixtures;
- no automatic web crawl initiated by an artifact;
- no path expansion from an authorized source ref;
- no external action without the destination repository's existing explicit human-approval boundary.

# Compatibility

V0.1 is additive.

It must not:

- change existing Question Radar decision semantics;
- reinterpret any existing Andes `ResearchActivity`, evidence or hypothesis value;
- change Opportunity OS vacancy, target-account, contribution, relationship, application or outreach semantics;
- require one repository as a runtime dependency of another;
- change existing CLI / API behavior when handoff functionality is unused.

The one intentional Andes contract addition is:

```text
ResearchActivity.DECISION_SUPPORT = "decision_support"
```

No new FastAPI route is required by this design. CLI / file-based export and preview is the default implementation direction unless implementation planning finds a concrete reason otherwise.

# Non-Goals

V0.1 does not build:

- a generic agent orchestrator;
- a workflow engine;
- a cross-repo database;
- a semantic actor graph;
- automatic buyer inference;
- automatic contact discovery;
- automatic outreach;
- automatic applications;
- autonomous external PR creation;
- embeddings / vector search solely for handoffs;
- a global confidence score;
- a UI dashboard;
- a shared package;
- a territorial collaboration CRM domain.

# Acceptance Criteria

## Contract acceptance

1. Both handoff contracts have strict, versioned, deterministic schemas.
2. Unsupported versions / fields fail closed.
3. No repository imports runtime code from another repository.
4. Existing tests and compatibility contracts remain green.
5. Source freshness is represented honestly as `AS_OF_EXPORT`.

## Territorial path

Starting from the San Juan water question:

1. Question Radar exports one valid Contract 1 artifact.
2. Andes consumes it without cross-repo imports.
3. Andes uses explicit `domain=water`, `activity=decision_support` and explicit territory.
4. Research produces either:
   - one reviewable `ACTOR_NEED_HYPOTHESIS` handoff; or
   - an explicit `NO_ACTIONABLE_CANDIDATE` live-research outcome.
5. If a handoff exists, Opportunity OS produces a read-only preview.
6. The preview separates evidence, assumptions and missing context.
7. The operator disposition is explicit.
8. No contact, draft, application or external action is executed by this flow.

## GitHub contribution path

Starting from one explicit public repository issue:

1. Question Radar exports the direct contribution route.
2. Public evidence is represented in `PUBLIC_CONTRIBUTION_CANDIDATE`.
3. Opportunity OS validates the candidate through a read-only preview.
4. `PublicContributionEntry` import is offered only if its existing contract is satisfied.
5. Availability / claim state is preserved from evidence.
6. PR or merge activity never becomes employment-interest evidence.

# Design Decision Summary

```text
Question Radar
= attention + investigation intent

Andes Context OS
= territorial evidence + conservative hypothesis

Opportunity OS
= bounded preview + existing opportunity/contribution authority boundaries

Integration
= versioned snapshot artifacts, not shared runtime state
```

V0.1 remains deliberately small: two contracts, two explicit routes, one additive Andes activity value, strict validation, read-only previews, and two dogfood paths. Anything beyond those boundaries requires a separate design decision.
