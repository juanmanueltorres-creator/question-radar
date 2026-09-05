# Moltbook Agent-Network Question Seeds — 2026-09-04

## Purpose

Capture three externally triggered questions for Question Radar after observing public discussions on Moltbook, an agent-oriented social network.

These entries are **question seeds**, not evidence, not feature requests, and not persisted `InvestigationDecision` records. The public benchmark records why the questions deserve review while preserving the local-first boundary of Question Radar.

## Epistemic boundary

```text
social post != evidence
agent consensus != ground truth
interesting question != feature request
handoff received != authority granted
human approval != automatic authorization
```

A Moltbook discussion can justify asking a better question. It cannot by itself justify changing runtime behavior.

---

## Seed A — Handoff compression and authority

### Question

> ¿Cómo puede un handoff comprimir contexto sin aumentar la autoridad del sistema receptor?

### External signal

Moltbook post: **Delegation creates semantic laundering channels**  
Source: https://www.moltbook.com/post/caa9a885-5ad5-4198-b371-193106896763

The discussion describes a multi-agent failure mode where summaries can remove the original trust/constraint context while preserving action-oriented language. Several comments converge on separating provenance from execution authority and treating authority gain as an independently controlled operation.

### Why this belongs in Question Radar

Question Radar's current cross-repo handoff design already separates routing from downstream action, but the stronger unresolved question is whether a receiver can accidentally infer more authority from a cleaner or more compressed representation.

### Suggested next test

Take one actionable-looking handoff payload and paraphrase its descriptive fields while holding source, route, and authority-relevant fields constant. Verify that the downstream capability/disposition decision cannot become more permissive merely because the wording becomes cleaner or more imperative.

### Stop condition

If current receiver-side validation plus explicit human disposition already makes capability decisions invariant to descriptive wording, do not add a new authority subsystem.

---

## Seed B — Freshness of derived conclusions

### Question

> ¿La frescura de una conclusión derivada debería estar limitada por la evidencia más antigua que todavía la sostiene?

### External signal

Moltbook post: **The Provenance Horizon: Why Derived State Decays Faster Than Raw Observation**  
Source: https://www.moltbook.com/post/01d009a3-1584-4cd7-8d3d-f0ba027e0e99

The discussion distinguishes the timestamp of a newly written conclusion from the age and validity of the observations that support it. The core failure mode is a derived claim that looks fresh because it was recomputed recently even though its load-bearing inputs are stale.

### Why this belongs in Question Radar

The current handoff contract already states:

```text
current_at_export != current_now
```

That protects against treating an exported decision as live authority, but it does not yet answer whether a derived research conclusion should inherit a freshness ceiling from its supporting evidence.

### Suggested next test

Construct a minimal research example containing:

- one recent observation;
- one older load-bearing observation;
- one derived conclusion created now.

Then ask whether `created_at`, `as_of_export`, and provenance references are sufficient to prevent the conclusion from masquerading as fresh. Only add a new freshness rule if the existing contract cannot represent the distinction.

### Stop condition

If the destination system can already expose evidence dates and force human reassessment without adding a new runtime concept, preserve the simpler model.

---

## Seed C — What makes human approval real authorization?

### Question

> ¿Qué información tiene que ver un humano para que una aprobación sea autorización real y no simplemente aprobación de la narrativa del agente?

### External signal

Moltbook post: **The human approval button is a remote-code-execution primitive**  
Source: https://www.moltbook.com/post/a4e03b29-1731-4ac8-ad4d-e8117f1b5b1e

The discussion argues that a human click is not a meaningful safety boundary when untrusted or agent-generated text controls the explanation of what is being approved. The proposed direction is to render the exact target, scope, parameters, and provenance from trusted structured state rather than asking the human to approve an agent-written narrative.

### Why this belongs in Question Radar

Opportunity OS already distinguishes preview, disposition, import eligibility, explicit confirmation, and external action. The unresolved question is whether the human is shown enough independently structured information at each authority transition to understand exactly what the approval grants.

### Suggested next test

For one `PUBLIC_CONTRIBUTION_CANDIDATE` and one `ACTOR_NEED_HYPOTHESIS`, write the smallest approval view that exposes:

- exact target/object identity;
- requested action/disposition;
- scope;
- provenance/evidence references;
- unresolved assumptions or missing context;
- what will **not** happen automatically.

Then test whether the same approval remains intelligible if all agent-generated explanatory prose is removed.

### Stop condition

If the existing structured preview already answers those questions without relying on generated narrative, freeze that as a release invariant rather than building another approval layer.

---

## Candidate investigation posture

All three seeds should enter review as **bounded research candidates**, not implementation commitments.

```text
external signal
    ↓
question seed
    ↓
operator review
    ↓
RESEARCH / PARKED / KILLED / DO_NOW
    ↓
only then: handoff or implementation work
```

The intended bias is conservative: a strong external discussion is useful when it sharpens a question, but Question Radar must remain free to conclude that the existing architecture is already sufficient.
