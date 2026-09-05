# Cross-Repo Research Handoff v0.1 — Sanitized Dogfood

Date: 2026-09-04

## Purpose

Exercise Question Radar's producer-side `question-research-handoff/v0.1` contract with two realistic but sanitized routing cases before any destination repository consumes them.

This dogfood verifies the handoff boundary. It does **not** verify that a downstream opportunity exists, that an actor is a buyer, that contact is permitted, or that a public GitHub task is currently available.

The executable regression is `tests/test_handoff_dogfood.py`.

## Boundary invariants

The fixtures intentionally carry these three statements as constraints:

```text
route != opportunity
handoff != evidence
current_at_export != current_now
```

Their operational meaning is:

- routing selects the next research surface; it does not prove an opportunity;
- a handoff preserves an operator-authorized investigation state; it does not become territorial, commercial, or repository evidence;
- the source decision is current at export time only; a static JSON artifact cannot claim live current authority later.

## Case 1 — San Juan water research

Question:

> ¿Qué decisión recurrente relacionada con agua en San Juan podría mejorar utilizando evidencia territorial o satelital, quién toma hoy esa decisión y qué información le falta?

Decision: `RESEARCH`

Route: `TERRITORIAL_RESEARCH`

Destination: `andes-context-os`

Next test:

> Definir un territorio explícito de San Juan y localizar una fuente pública trazable que documente una decisión recurrente relacionada con agua.

Expected operational meaning: Andes Context OS may consume the artifact as a bounded research request, but territory, activity, actors, evidence quality, and any opportunity hypothesis remain downstream explicit work.

## Case 2 — Public geospatial GitHub research

Question:

> ¿Qué problema público de software geoespacial puedo resolver en un repositorio externo donde exista una tarea explícita y disponible?

Decision: `RESEARCH`

Route: `PUBLIC_CONTRIBUTION_RESEARCH`

Destination: `opportunity-os`

Next test:

> Encontrar una issue pública geoespacial con necesidad explícita, estado verificable y alcance acotable antes de crear cualquier candidato de contribución.

Expected operational meaning: Opportunity OS may inspect public repository evidence later, but routing alone does not establish a job opening, contact permission, employment interest, task availability, or contribution claim state.

## Sanitization

Both fixtures use fictional IDs, fixed timestamps, synthetic SHA-256-shaped fingerprints, no recipient or contact information, no account credentials, no private database values, and no source content beyond the two explicit dogfood questions.

`question_profile_ref` remains `null` because V0.1 has no explicit structural profile link for these fixtures.

## Valid zero-result outcome

A downstream investigation is allowed to terminate with no actionable candidate.

```text
NO_ACTIONABLE_CANDIDATE != failed research
```

If public evidence cannot support an actor-need hypothesis or an explicitly available contribution task, the correct result is to preserve the missing context and stop. The dogfood must never invent a candidate merely to complete the pipeline.

## What this dogfood proves

The two JSON fixtures:

1. validate through `QuestionResearchHandoff.from_dict()`;
2. preserve the exact questions and operator `RESEARCH` decision;
3. route only through the closed V0.1 routing vocabulary;
4. contain the three authority/freshness constraints above;
5. contain no fields that claim buyer/customer status, a job opening, contact permission, or task availability.

This is producer-side evidence only. Andes Context OS and Opportunity OS remain independent systems and are not imported or called by Question Radar.
