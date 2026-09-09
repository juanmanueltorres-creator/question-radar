# Cross-country Territorial Decision Primitives Question Seed — 2026-09-09

## Purpose

Preserve one cross-country territorial research question derived from GeoPlatform Knowledge Base after repeated cases suggested that the same decision structure may recur across different countries and sectors.

This file is a **question seed**, not a persisted `InvestigationDecision`, not a product claim, not evidence of market demand, and not a score of the people represented in the source material.

## Epistemic boundary

```text
repeated narrative != repeated mechanism
contact != independent observation
conversation != validation
country count != representativeness
shared vocabulary != shared decision architecture
pattern candidate != product primitive
question seed != evidence
```

The source corpus is a convenience sample created through GeoPlatform's professional network and projects. It must not be treated as a statistically representative sample of countries, sectors, professionals, institutions, or territorial problems.

---

## Seed — do decision primitives survive country and sector changes?

### Question

> En los casos y contactos de GeoPlatform cuyo contexto territorial está explícitamente documentado, ¿qué estructuras de decisión reaparecen después de normalizar por país y sector, cuáles son específicas del contexto local y qué observaciones refutarían la hipótesis de que existe un núcleo reutilizable de contexto, vigencia, conocimiento humano, validación y trazabilidad?

### Source signal

GeoPlatform Knowledge Base contains documented cases and professional conversations where several themes recur:

- fragmented information;
- mapped objects without current operational state;
- loss of value when data lacks temporal validity;
- local or specialist knowledge as part of the decision system;
- validation and authority requirements;
- provenance and traceability needs;
- public or technical data that still requires a reproducible operational pipeline.

Examples include road-accessibility cases in Kenya and Ethiopia, hydroclimatic work in Argentina, geological / structural workflows involving Venezuela and Argentina, and international geoscience knowledge-management relationships.

These signals justify an investigation. They do **not** establish that one universal architecture exists.

### Candidate hypothesis

A small set of components may recur across otherwise different territorial decisions:

```text
data
→ temporal context
→ human / local knowledge
→ validation / authority
→ decision
→ traceability
```

Country-specific datasets, institutions, regulations, terminology, jurisdiction and procedures may behave mostly as local adapters around that decision core.

This is a candidate hypothesis only.

### Assumptions to expose

1. The documented cases contain enough metadata to compare mechanisms rather than just stories.
2. The contacts represent sufficiently different contexts to test portability at all.
3. Similar concepts are not being introduced by the same interviewer or documentation template.
4. Country and sector can be normalized without erasing important institutional or scientific differences.
5. A small set of primitives can be defined explicitly enough to be falsifiable.
6. Cases that share communities, projects or prior conversations are not automatically independent observations.

### Evidence required

For each case used in the comparison, capture at minimum:

```text
case_id
country
territory
sector
actor_role
decision
observed_problem
available_data
missing_context
temporal_sensitivity
local_knowledge_required
validation_actor
authority_actor
provenance_available
traceability_available
outcome
evidence_strength
source_refs
inference_notes
```

Each field should distinguish:

```text
documented
inferred
pending_validation
unavailable
```

### Suggested next test

Build a first matrix from **5–10 already documented cases**, covering at least two countries and more than one sector.

Then:

1. code only what the source evidence supports;
2. mark inferred fields separately;
3. test candidate primitives such as context, freshness, human knowledge, validation, authority, provenance, decision and traceability;
4. allow a new primitive when a real case does not fit without distortion;
5. compare which structures survive country and sector changes;
6. perform a conceptual leave-one-country-out test when enough cases exist.

For the leave-one-country-out step:

```text
derive candidate primitives from countries A..N-1
→ hold out country N
→ test whether the held-out cases fit
→ record mismatches
→ do not add a primitive unless the evidence requires it
```

### Evidence that would strengthen the hypothesis

- cases from different countries require the same fundamental components;
- most differences occur in datasets, institutions, regulations or local configuration;
- held-out countries can be explained without continuously adding primitives;
- the repeated structure is tied to concrete decisions, not just shared terminology.

### Evidence that would weaken or refute it

- each new country requires a substantially different fundamental decision structure;
- candidate primitives appear only because the analyst forces cases into the template;
- similarities disappear after controlling for sector;
- repeated patterns are mostly interviewer/documentation artifacts;
- source metadata is too sparse to distinguish observed mechanism from interpretation;
- apparently independent cases are strongly dependent on the same network, project or source.

### Stop condition

Do not promote this investigation into a multi-country product architecture or new GeoPlatform module if:

- the source cases cannot support the proposed fields without substantial inference;
- categories require excessive reinterpretation;
- every held-out context requires major changes to the primitive set; or
- the main result is merely that different domains all use "data" and "people" at a generic level.

A valid outcome is:

```text
no stable cross-country primitive set found
```

---

## Candidate investigation posture

This seed should enter operator review as a **RESEARCH candidate**.

```text
GeoPlatform documented cases
    ↓
question seed
    ↓
assumptions + evidence requirements + falsifiers
    ↓
operator review
    ↓
RESEARCH / PARKED / KILLED / DO_NOW
    ↓
only if warranted: TERRITORIAL_RESEARCH handoff
```

Question Radar should not assign priority automatically and should not score the people in the source cases.

## Relationship to existing Question Radar boundaries

This seed intentionally preserves the following distinctions:

```text
question != problem
pattern != ground truth
retrieval hit != semantic equivalence
interesting investigation != priority
handoff != evidence
person != score
```

The research value is in testing whether a decision structure survives meaningful contextual change — and in documenting clearly when it does not.
