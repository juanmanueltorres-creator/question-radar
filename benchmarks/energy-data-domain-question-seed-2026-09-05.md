# Energy Data + Domain Knowledge Question Seed — 2026-09-05

## Purpose

Capture an externally triggered question about the intersection of energy operations, data engineering, and domain knowledge.

The trigger is a public discussion around YPF's demand for people who can work with large operational datasets. The signal is useful because it points toward a possible labor and operational bottleneck, but it does **not** by itself prove which teams are hiring, which exact skills are missing, whether a specific role is open, or whether any particular candidate is a fit.

This entry is a **question seed**, not an opportunity record, not a job application, not evidence of hiring intent toward the operator, and not a persisted `InvestigationDecision`.

## External signal

A 2026-09-04 news report quotes YPF president Horacio Marín describing a large human-resources bottleneck around data, data analytics, machine learning, and handling very large volumes of operational information. The report states that YPF gathers billions of data points per day through real-time systems and that Marín publicly encouraged people with relevant data skills to send a CV.

Source reviewed during intake: Diario Crónica, 2026-09-04, "El presidente de YPF aseguró que necesitan especialistas en datos y pidió que envíen sus CV".

The source supports the existence of a broad public signal of demand. It does **not** establish a specific vacancy, hiring SLA, team match, recruiter ownership, or candidate suitability.

## Epistemic boundary

```text
public demand signal != specific vacancy
large data volume != validated business problem
technical skill demand != candidate fit
industry knowledge != authority to interpret every process
interesting employer != permission to infer hiring outcome
"data" != one homogeneous role
```

The useful question is therefore not "how do we get into YPF?" but "what concrete operational decisions are currently constrained by the translation between physical processes, data architecture, and evidence?"

---

## Primary question

> ¿Qué decisiones concretas de minería y energía están hoy limitadas no por falta de datos, sino por la dificultad de conectar conocimiento del dominio, arquitectura de datos y evidencia operacional?

## Why this belongs in Question Radar

The public signal is broad enough to be tempting but too underspecified to act on directly.

A statement such as "we need data people" can hide several very different needs:

- ingestion and streaming;
- data quality and lineage;
- process analytics;
- geospatial integration;
- production optimization;
- anomaly detection;
- maintenance and reliability;
- cloud architecture;
- ML experimentation;
- decision support;
- reporting and auditability.

Question Radar should keep the investigation upstream of role labels and tools.

```text
more data
    !=
better decision

cloud stack
    !=
understanding the process

business knowledge
    !=
automatic technical authority
```

The important unit of analysis is a decision chain:

```text
physical process / asset
→ observation or sensor
→ data capture
→ cleaning / contextualization
→ model or rule
→ evidence presented
→ operator / engineer judgment
→ action / no-action
→ measured outcome
```

The investigation should identify where that chain currently breaks.

---

## Decomposition questions

### Upstream

> ¿Qué decisiones de exploración, perforación, completación o producción requieren integrar datos geológicos, espaciales y operacionales que hoy viven en sistemas o escalas distintas?

### Midstream

> ¿Qué decisiones de transporte, almacenamiento, integridad o capacidad dependen de datos cuya calidad, latencia o contexto operacional todavía dificulta explicar desvíos?

### Downstream

> ¿Qué decisiones de proceso, mantenimiento, calidad o eficiencia energética requieren combinar conocimiento de ingeniería con series temporales y datos de activos para distinguir una desviación real de ruido o mala medición?

### Cross-domain

> ¿En qué problemas el cuello de botella es realmente técnico y en cuáles es semántico: no saber qué significa una variable, qué relación física debería cumplir, quién confía en ella o qué acción debería cambiar?

---

## Evidence needed

Before treating this as a real problem class, collect evidence from at least three layers:

1. **Operational evidence**
   - one recurring decision;
   - the asset or process involved;
   - the current data used;
   - the current failure mode or delay;
   - who makes the decision;
   - what consequence follows from getting it wrong or late.

2. **Technical evidence**
   - source systems;
   - data frequency and volume;
   - missing context or joins;
   - lineage / quality constraints;
   - existing stack;
   - whether the issue is ingestion, modeling, access, interpretation, or trust.

3. **Organizational evidence**
   - role/team ownership;
   - whether the problem is acknowledged internally;
   - whether an existing workflow already handles it adequately;
   - whether hiring, consulting, internal tooling, or process redesign is the actual response.

---

## Suggested next test

Do not start by applying a generic "data" profile everywhere.

Pick one concrete energy workflow and reconstruct it end to end. Good candidate classes include:

- production surveillance;
- well / reservoir data integration;
- geospatial infrastructure monitoring;
- equipment condition / maintenance;
- process deviation analysis;
- environmental monitoring;
- field-to-cloud data traceability.

For the selected workflow, ask:

```text
What decision is being made?
What physical variable is the decision trying to understand?
What data represents that variable?
What context is currently missing?
What would make the evidence trustworthy enough to act?
Who owns the decision?
```

A useful first external interview would be with an engineer, geoscientist, operations analyst, or data engineer who works close enough to the asset to describe a recent real decision rather than a generic technology roadmap.

## Stop condition

Stop the investigation or reframe it if:

- no recurrent decision can be named;
- the problem is already solved adequately by an existing platform/process;
- the only evidence is generic hiring rhetoric;
- the proposed contribution is merely "build a dashboard" without a validated decision need;
- the operator cannot explain what business or physical interpretation would improve.

---

## Candidate investigation posture

This should enter operator review as a **RESEARCH candidate**, not as `DO_NOW` by default.

```text
public demand signal
    ↓
question seed
    ↓
identify one operational decision
    ↓
collect domain + technical + organizational evidence
    ↓
RESEARCH / PARKED / KILLED / DO_NOW
```

Do not route this through the current `PUBLIC_CONTRIBUTION_RESEARCH` handoff merely because an employer or repository may later appear. The current signal is about industrial data work, not an identified public contribution task.

If a concrete territorial or environmental subproblem emerges, a later reviewed question may qualify for `TERRITORIAL_RESEARCH`. If a specific public GitHub task emerges, that separate question may qualify for `PUBLIC_CONTRIBUTION_RESEARCH`.

The intended bias is conservative: use the labor-market signal to discover a real operational decision problem, not to manufacture a role match from a broad executive statement.