# Cross-Repo Problem → Opportunity Handoff V0.1 Design

## Status

Design-only specification for a bounded integration across:

- `question-radar`
- `andes-context-os`
- `opportunity-os`

This document defines handoff contracts and routing boundaries. It does not authorize runtime implementation, cross-repo imports, outreach, contact discovery, sending, applying, or autonomous GitHub mutation.

## Goal

Turn a high-value question into a traceable investigation and, only when the evidence supports it, into a bounded opportunity or contribution candidate without collapsing question, signal, evidence, hypothesis, actor, opportunity, or external-action authority into the same thing.

The V0.1 success path is:

```text
question
  ↓
explicit investigation decision
  ↓
versioned handoff
  ↓
territorial research when required
  ↓
versioned opportunity handoff
  ↓
Opportunity OS preview
  ↓
human decision about the next action
```

## Product Questions

The integration is organized around three questions:

1. **What decision is actually being made?**
2. **What evidence could change that decision?**
3. **Who has that problem and enough incentive to act?**

These are operator questions, not automatic scoring outputs.

## Core Boundaries

The integration must preserve these distinctions:

```text
question != problem
signal != evidence
evidence != conclusion
actor != problem owner
problem owner != buyer
movement != need
need != confirmed demand
opportunity hypothesis != opportunity authority
public issue != job opening
PR opened != employment interest
opportunity != permission to contact
draft != send
```

No handoff may silently strengthen epistemic or action authority.

## Why Separate Repositories

The three repositories have different responsibilities and should remain independently understandable and testable.

### Question Radar

Question Radar owns inquiry structure and attention decisions:

- question identity and lineage;
- assumptions;
- evidence requirements;
- stronger next questions;
- explicit `DO_NOW / RESEARCH / PARKED / KILLED` investigation decisions;
- operator-authored next test.

It does not decide that a real-world need exists.

### Andes Context OS

Andes Context OS owns territorial research boundaries:

- `ResearchIntent`;
- territorial scope;
- registered sources and runtime observations;
- evidence candidates and quality vectors;
- missing / contradictory context;
- actor and movement interpretation;
- conservative `OpportunityHypothesis` state.

It does not decide that a hypothesis is a job, procurement package, buyer commitment, or contact permission.

### Opportunity OS

Opportunity OS owns action-oriented opportunity state:

- real vacancies;
- target accounts;
- public GitHub contribution entries;
- relationship context;
- bounded contribution lifecycle;
- preview / confirmation boundaries before local imports;
- evidence-backed application and outreach preparation.

It does not infer that a research hypothesis grants send, apply, follow-up, or contribution authority.

## Architectural Decision

V0.1 uses **versioned JSON artifacts as handoff contracts**.

It explicitly rejects for V0.1:

- Python imports across repositories;
- a shared runtime package;
- a central orchestration service;
- a shared database;
- cross-repo network RPC;
- automatic chaining;
- background workers;
- event buses;
- direct external actions.

Each repository remains independently installable and runnable. A handoff is an exported artifact that another repository may validate and preview.

## Routing Model

Not every question must traverse all three repositories.

```text
Question Radar
     ↓
InvestigationDecision
     ↓
route
  ┌──┴──────────────────────────┐
  │                             │
territorial / mining /      public software /
water / environment         GitHub contribution
  │                             │
  ▼                             │
Andes Context OS                │
  │                             │
  └──────────────┬──────────────┘
                 ▼
           Opportunity OS
```

### Territorial route

Use Andes Context OS when the investigation materially depends on territorial scope, public geoscience / environmental evidence, project movement, operational context, or actor interpretation.

Examples:

- recurrent water-management decisions in San Juan;
- remote-sensing signals that could alter a field decision;
- mining project movements that may indicate a bounded service need;
- environmental / access / logistics research tied to an explicit territory.

### Direct contribution route

Question Radar may hand directly to Opportunity OS contribution research when the problem is already expressed through a public software contribution surface.

Examples:

- explicit GitHub issue;
- maintainer-stated help wanted;
- collaboration call;
- repository research that yields a bounded candidate task.

A direct route does not imply the issue is available, appropriate, or employment-related.

## Contract 1: Question → Research Handoff

Canonical contract identifier:

```text
question-research-handoff/v0.1
```

The artifact records an explicit operator decision and the minimum context needed for another system to investigate it.

### Proposed schema

```json
{
  "contract": "question-research-handoff/v0.1",
  "handoff_id": "qrh:2026-09-04:001",
  "created_at": "2026-09-04T20:30:00-03:00",
  "source": {
    "system": "question-radar",
    "question_id": "question:001",
    "decision_id": "decision:001"
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

### Required semantics

- `source.question_id` must identify an existing Question Radar question.
- `source.decision_id` must identify the current explicit investigation decision used for this handoff.
- `investigation.decision` must be `DO_NOW` or `RESEARCH`.
- `investigation.next_test` must be non-empty.
- `routing.kind` must be an explicit closed vocabulary.
- `PARKED` and `KILLED` decisions cannot produce an actionable handoff.
- The handoff does not claim that the destination can answer the question.

### Routing vocabulary V0.1

```text
TERRITORIAL_RESEARCH
PUBLIC_CONTRIBUTION_RESEARCH
```

No automatic classifier chooses this route in V0.1. The operator supplies and confirms it.

## Andes Context OS Intake Mapping

For `TERRITORIAL_RESEARCH`, the handoff can seed a new Andes `ResearchIntent`.

Mapping:

```text
question.raw         → ResearchIntent.question_raw
question.canonical   → ResearchIntent.question_canonical
source.question_id   → ResearchIntent.question_profile_ref
investigation.next_test → ResearchIntent.goal or explicit intake note
constraints[]        → ResearchIntent.constraints
```

The destination still requires an explicit Andes domain, activity, and territorial scope. Missing destination-specific fields must remain missing until supplied; they must not be guessed from the handoff.

The handoff is context, not evidence.

## Contract 2: Research → Opportunity Handoff

Canonical contract identifier:

```text
research-opportunity-handoff/v0.1
```

This artifact is emitted only after an Andes research path produces a reviewable hypothesis or a direct public-contribution research path identifies a bounded candidate.

### Territorial opportunity schema

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
  "opportunity_candidate": {
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

### Required semantics

- The artifact must preserve the source hypothesis state verbatim.
- `researching` must not be transformed into `supported` by the handoff.
- `actor_refs` may be empty when no actor has been defensibly identified.
- Empty actor references do not invalidate a research artifact; they prevent actor-oriented Opportunity OS actions.
- Assumptions and missing context are first-class required fields, even when empty.
- Evidence references are references, not copied source bodies.
- A handoff never asserts willingness to pay, procurement intent, hiring intent, or permission to contact unless those are supported by a separate explicit evidence model in the destination system.

## Direct Public Contribution Handoff

For `PUBLIC_CONTRIBUTION_RESEARCH`, the output should map into the existing Opportunity OS `PublicContributionEntry` boundary rather than inventing a new employment opportunity type.

The handoff must preserve:

- repository identity;
- public source reference;
- observed or maintainer-stated need basis when evidence supports it;
- hypothesized need basis when it does not;
- task reference only when an explicit public task exists;
- claim / availability state only when observed;
- bounded task text only when defensible.

The existing Opportunity OS contribution invariants remain authoritative:

```text
PUBLIC_CONTRIBUTION_ENTRY != JOB_OPENING
PR_OPENED != EMPLOYMENT_INTEREST
PR_MERGED != EMPLOYMENT_INTEREST
GOOD_PROBLEM != AVAILABLE_PROBLEM
```

## Opportunity OS Intake Boundary

Opportunity OS must treat every incoming handoff as a **candidate observation**, not as an immediate domain mutation.

V0.1 intake shape:

```text
handoff artifact
      ↓
strict validation
      ↓
normalize into bounded preview
      ↓
show evidence / assumptions / missing context
      ↓
operator decision
      ↓
optional explicit import into an existing Opportunity OS domain
```

Possible operator decisions may include:

```text
RESEARCH_ACTOR
WATCH
PREPARE_COLLABORATION
PUBLIC_CONTRIBUTION_ENTRY
DISCARD
```

These are intake decisions, not send/apply permissions.

V0.1 should not create a generic mega-entity that mixes target accounts, vacancies, territorial actors and public contribution entries.

## Actor / Organization Semantics

Territorial research will often identify organizations that do not fit the current employment-oriented `TargetAccount` contract.

Therefore V0.1 must **not** coerce every Andes actor into `TargetAccount`.

Examples that may require research without becoming employment targets:

- provincial water authority;
- environmental regulator;
- mine operator;
- public research institute;
- municipality;
- supplier;
- university group;
- open-source maintainer.

The V0.1 handoff may carry actor references and actor context without requiring Opportunity OS to persist them as target accounts.

If a future dedicated actor/relationship domain is needed, that is a separate design.

## Provenance

Every handoff must contain:

- contract identifier and version;
- handoff identity;
- source system;
- source domain identifiers;
- creation timestamp;
- evidence references where evidence claims are made.

V0.1 must not copy private source bodies, Gmail content, private contact data, credentials, local SQLite content, or unrestricted internal notes into public repository fixtures.

Public tests and dogfood fixtures must use sanitized or public evidence only.

## Determinism

Given the same canonical source records, an export should serialize deterministically except for an explicitly supplied handoff identifier and creation timestamp.

Recommended rules:

- UTF-8 JSON;
- stable key ordering for deterministic exports;
- no inferred neighboring resources;
- no fuzzy actor or project matching during import;
- unknown fields fail closed;
- unsupported contract versions fail closed.

## Failure Modes

### Stale source decision

If the Question Radar investigation decision has been superseded after export, the handoff is stale. The destination must not silently treat it as current authority.

### Unsupported route

Unknown routing kinds fail closed.

### Missing territorial scope

A territorial handoff may seed `ResearchIntent`, but Andes research cannot proceed as a defensible territorial run until an explicit valid scope exists.

### Unsupported hypothesis state

The handoff preserves the state rather than upgrading or downgrading it.

### Missing actor

Research may continue. Actor-oriented opportunity actions must remain unavailable.

### Evidence reference unavailable

The destination records the missing evidence reference and blocks any operation that requires that evidence. It does not replace the reference with a guessed source.

### Direct GitHub task already claimed or closed

Opportunity OS must preserve the observed claim state. A good problem that is unavailable remains unavailable.

## V0.1 Dogfood Case

Primary end-to-end question:

> **¿Qué decisión recurrente relacionada con agua en San Juan podría mejorar utilizando evidencia territorial o satelital, quién toma hoy esa decisión y qué información le falta?**

### Step A — Question Radar

Expected output:

- stable question identity;
- explicit assumptions;
- explicit evidence requirements;
- stronger / bounded next question if needed;
- `RESEARCH` or `DO_NOW` decision;
- operator-written `next_test`;
- `question-research-handoff/v0.1` export.

Success is not a high formulation score. Success is a defensible reason to investigate and a concrete next test.

### Step B — Andes Context OS

Expected research focus:

- explicit San Juan territorial scope;
- one recurrent decision candidate;
- public source registry usage;
- evidence candidates with provenance;
- candidate actors;
- explicit missing context;
- zero or more conservative opportunity hypotheses.

Success is not discovering a customer. Success is separating what is observed from what remains hypothesized.

### Step C — Opportunity OS

Expected preview:

- source question lineage;
- candidate actor / need statement;
- evidence refs;
- assumptions;
- missing context;
- explicit disposition such as `RESEARCH_ACTOR`, `WATCH`, `PREPARE_COLLABORATION`, or `DISCARD`.

Success is not sending a message. Success is reaching one justified next action without overstating evidence.

## Secondary Dogfood Case

A direct GitHub path should later prove the routing bifurcation:

> **¿Qué problema público de software geoespacial puedo resolver en un repositorio externo donde exista una tarea explícita y disponible?**

Expected path:

```text
Question Radar
  ↓
PUBLIC_CONTRIBUTION_RESEARCH
  ↓
public GitHub evidence
  ↓
Opportunity OS PublicContributionEntry preview
  ↓
TASK_READY only if availability is explicit
```

Andes Context OS is intentionally absent from this path.

## Testing Strategy

Implementation must use focused regression tests in each repository rather than a new cross-repo integration test framework.

Minimum tests when implementation begins:

### Question Radar

- valid handoff export from current `DO_NOW` / `RESEARCH` decision;
- reject `PARKED` / `KILLED` actionable export;
- reject unknown route;
- deterministic serialization;
- preserve source question and decision refs;
- detect or expose stale superseded decision during export/validation.

### Andes Context OS

- strict intake validation;
- exact mapping into `ResearchIntent` without guessing domain/activity/scope;
- fail closed on unsupported contract version;
- preserve source question reference;
- deterministic research-opportunity export;
- preserve hypothesis status, assumptions and missing context.

### Opportunity OS

- strict handoff validation;
- preview is read-only;
- no automatic `TargetAccount` coercion for territorial actors;
- no send/apply/follow-up authority introduced;
- direct contribution mapping preserves need basis and task claim state;
- stale / missing referenced evidence blocks authority-sensitive intake paths.

Each repository must continue to run its existing full test suite and compile checks.

## Security and Privacy

- no credentials in handoffs;
- no provider tokens;
- no email bodies;
- no private candidate profile content;
- no private actor contact details in public fixtures;
- no automatic web crawling from a handoff;
- no path expansion from an authorized source reference;
- no external action without the destination repository's existing explicit human-approval boundary.

## Compatibility

V0.1 is additive.

It must not:

- change existing Question Radar decision semantics;
- change Andes evidence or hypothesis state semantics;
- change Opportunity OS vacancy, target-account, contribution, relationship, application, or outreach contracts;
- register new FastAPI routes unless separately justified during implementation planning;
- require a runtime dependency from one repository on another.

Existing CLI and API behavior remains valid when the integration feature is unused.

## Non-Goals

V0.1 does not build:

- a generic agent orchestrator;
- a workflow engine;
- a cross-repo database;
- a semantic actor graph;
- automatic buyer inference;
- automatic contact discovery;
- automatic outreach;
- automatic application submission;
- autonomous PR creation in external repositories;
- embeddings / vector search solely for the handoff;
- a generic confidence score;
- a UI dashboard;
- a new shared package.

## Acceptance Criteria

The design is implemented successfully when both paths can be demonstrated without weakening existing boundaries.

### Territorial acceptance

Starting from the San Juan water question:

1. Question Radar exports one valid versioned investigation handoff.
2. Andes consumes it without cross-repo imports and preserves source lineage.
3. Andes research emits zero or one reviewable opportunity handoff for the selected dogfood slice.
4. Opportunity OS produces a read-only preview.
5. The preview clearly separates evidence, assumptions and missing context.
6. The final operator disposition is explicit.
7. No contact is sent and no application or external action is executed by the V0.1 flow.

### GitHub contribution acceptance

Starting from one explicit public repository issue:

1. Question Radar exports a direct contribution-research handoff.
2. Opportunity OS validates public evidence.
3. `PublicContributionEntry` is previewed only when its existing contract can be satisfied.
4. Availability / claim state is preserved from evidence.
5. A PR or merge never becomes employment-interest evidence.

## Design Decision Summary

```text
Question Radar
= attention + investigation intent

Andes Context OS
= territorial evidence + conservative hypothesis

Opportunity OS
= bounded opportunity / contribution preview + operator action boundary

Integration
= versioned artifacts, not shared runtime state
```

The V0.1 implementation should remain deliberately small: two handoff contracts, explicit routing, strict validation, deterministic export/import previews, and two dogfood paths. Anything beyond that requires a separate design decision.
