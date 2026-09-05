# San Juan Water Project Question Seeds — 2026-09-05

## Purpose

Capture two externally triggered territorial questions for Question Radar after reviewing public UNSJ project pages related to water stress, monitoring, and decision support in San Juan.

These entries are **question seeds**, not evidence of adoption, not commercial opportunities, not collaboration invitations, and not persisted `InvestigationDecision` records. They are useful because they sharpen what must be validated with operators before proposing software, remote sensing, or automation.

## Epistemic boundary

```text
project proposal != deployed system
technology capability != validated operational need
monitoring != actionable decision
public project page != permission to contact
interesting actor != problem owner
problem owner != buyer
```

Both source projects are publicly presented as under evaluation / pending approval. Their existence justifies better questions; it does not establish that the proposed systems are funded, deployed, adopted, or available for external collaboration.

---

## Seed A — CHAZE-Agro: early water-stress detection to operational action

### Question

> ¿Qué decisión operativa de riego o manejo de cultivo cambiaría realmente si el estrés hídrico pudiera detectarse antes mediante información hiperespectral, quién toma esa decisión y con qué latencia y confiabilidad necesita recibir la señal?

### External signal

UNSJ LED&T project: **CHAZE-Agro — Instrumentación hiperespectral NEU UAV/Satélite para agricultura de precisión en zonas áridas**  
Source: https://ledyt.fi.unsj.edu.ar/proyectos/chaze-agro

The public project page describes a hyperspectral payload for UAV use and future satellite scaling, aimed at early detection of water stress in major San Juan crops. It proposes field validation against physiological reference measurements and explicitly frames the work around irrigation agriculture under structural water scarcity.

### Why this belongs in Question Radar

The project demonstrates that early water-stress sensing is an active technical research direction in San Juan. What remains unresolved for our work is the decision boundary: a better spectral signal is only useful if it arrives early enough, is trusted enough, and changes a concrete irrigation or crop-management action.

Question Radar should therefore keep the problem upstream of implementation:

```text
earlier spectral signal
    !=
useful operational decision
```

### Suggested next test

Interview one agronomic or irrigation operator and ask for a specific recent decision where earlier detection of crop water stress would have changed:

- when irrigation occurred;
- how much water was applied;
- which plot was prioritized;
- whether a field inspection was triggered; or
- whether no action would have changed at all.

Record the required lead time, acceptable false-positive/false-negative cost, current evidence used, and who has authority to act.

### Stop condition

If operators cannot name a recurrent decision that changes because the signal arrives earlier, do not create a new remote-sensing feature merely because the sensing technology is technically interesting.

---

## Seed B — SAT-PAE Jáchal: from continuous monitoring to an actionable alert

### Question

> ¿Qué evento observable en la cuenca del Río Jáchal debería disparar qué acción institucional concreta, quién valida la alerta y qué evidencia necesita esa persona para actuar sin confundir una anomalía de sensor con una emergencia real?

### External signal

UNSJ LED&T project: **SAT-PAE Jáchal — Sistema de Alerta Temprana para la Cuenca del Río Jáchal**  
Source: https://ledyt.fi.unsj.edu.ar/proyectos/sat-pae-jachal

The public proposal describes 20 continuous monitoring stations, multiparameter water-quality sensing, biosensors, satellite telemetry, a custom SCADA layer, historical traceability, and threshold-based alerts. Its stated objective is to support auditable and actionable decisions by public agencies, productive actors, and local communities.

### Why this belongs in Question Radar

This project makes the monitoring-to-decision gap explicit. Continuous telemetry and alarm rules do not by themselves answer:

- who receives an alert;
- who is authorized to validate it;
- which corroborating evidence is required;
- how stale or missing data affects the decision;
- which action follows each severity level; or
- what happens when institutions disagree.

That is directly aligned with the broader Question Radar boundary:

```text
signal != evidence
evidence != conclusion
alert != authority to act
```

### Suggested next test

Take one plausible event class — for example an abrupt water-quality anomaly or hydrological deviation — and reconstruct the smallest operational chain:

```text
observation
→ sensor/telemetry quality check
→ corroboration
→ institutional recipient
→ human validation
→ action / no-action
→ audit record
```

Then identify the first point where the current public project description does not tell us enough to know what a real operator would do.

### Stop condition

If the responsible institutions already have a documented and operational alert-to-action protocol that fully covers validation, authority, escalation, and auditability, treat that as existing capability and do not invent a parallel decision layer.

---

## Candidate investigation posture

Both seeds should enter operator review as **RESEARCH candidates**, not implementation commitments and not opportunity records.

```text
public territorial project
    ↓
external signal
    ↓
question seed
    ↓
operator review
    ↓
RESEARCH / PARKED / KILLED / DO_NOW
    ↓
only if warranted: TERRITORIAL_RESEARCH handoff
```

The intended bias is conservative: these projects are valuable because they reveal where sophisticated sensing is already being proposed in San Juan. Our job is to find the unresolved decision problem around that sensing, not to duplicate the proposed technology stack.