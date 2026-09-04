# Investigation Decision Gate v0.9 — Sanitized Dogfood

Date: 2026-09-04

## Purpose

Exercise the v0.9 decision layer against three realistic but sanitized investigation patterns using a disposable SQLite database and the public CLI surface.

This dogfood is intentionally not a benchmark of whether the operator's choices are objectively correct. It verifies that Question Radar can preserve different attention judgments without acquiring prioritization authority.

The executable regression is `tests/test_decision_dogfood.py`.

## Cases

### 1. Infrastructure scaling — PARKED

Question:

> When does horizontal PostgreSQL scaling become justified by a real workload?

Recorded decision: `PARKED`

Rationale: high learning value, but no current production workload requires the investigation.

Return condition:

> A real PostgreSQL workload requires horizontal scaling.

Expected operational meaning: the question remains preserved without consuming active attention.

### 2. Lithium / GeoAI problem discovery — RESEARCH

Question:

> Which lithium GeoAI problem is narrow enough for a bounded evidence-gathering test?

Recorded decision: `RESEARCH`

Next test:

> Collect ten repeated operational problems from public lithium project evidence and classify which are observable with GeoAI.

Expected operational meaning: bounded evidence gathering is allowed, but the system does not promote the investigation to `DO_NOW` automatically.

### 3. Existing-product feedback — DO_NOW

Question:

> Which existing product demonstration can produce external feedback this week?

Recorded decision: `DO_NOW`

Next test:

> Publish one existing product demonstration and record one external response or explicit no-response outcome.

Expected operational meaning: the operator explicitly permits immediate execution.

## Verified projection

The disposable-database dogfood asserts this current-state projection:

```text
DO_NOW:   1
RESEARCH: 1
PARKED:   1
KILLED:   0
```

The active list contains only `RESEARCH` and `DO_NOW`. No WIP warning is emitted because only one investigation is marked `DO_NOW`.

The parked rendering contains:

```text
No action is currently requested.
```

The history JSON for the research case contains `automatic_decision: false` and no `priority_score` field.

## Verification evidence

GitHub Actions run `33904668043` executed the complete test suite, including `tests/test_decision_dogfood.py`, followed by source compilation. Both steps completed successfully on Python 3.11.

The test uses a temporary SQLite database and sanitized public fixtures. No private operator state, external service, LLM call, network request, or persistent local database is required.

## Boundary demonstrated

The dogfood demonstrates the intended distinction:

> Preserving a question is not the same as committing attention to it.

Question Radar records the operator's decision and its rationale. It does not infer which decision should be chosen.
