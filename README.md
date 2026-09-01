# Question Radar

> **Education records answers. Question Radar preserves the questions that make the next investigation possible.**

We routinely store grades, assignments, correct answers, mistakes, tickets, search results, and chat responses. We much less often preserve **how a question changes**: what it is trying to understand, what assumptions it carries, what evidence it needs, and what stronger question follows.

Question Radar is a small, local-first Python system for turning questions into structured, inspectable data — **without turning them into a score of the person asking them**.

**Current `main`: v0.3 · Question Profiles + Personal Learning Frontier**  
**This PR proposes:** v0.4 · Question Lineage + deterministic Context Packs

**Stack:** Python 3.11+ · SQLite · CLI · JSONL/CSV · standard-library runtime only

---

## Why questions?

A good answer can close a task. A good question can open an investigation.

That distinction matters because educational and evaluation systems need outputs that can be recorded and compared, while inquiry often starts from something harder to standardize: uncertainty, a missing assumption, a contradiction, or a question that does not yet have a clean answer.

Question Radar does **not** claim that schools are universally hostile to curiosity or that tests are inherently bad. The narrower critique is this:

> **What is easy to grade can become easier to preserve than what is valuable to investigate.**

Research gives that concern some grounding:

- **Chin & Osborne (2008)** review student questioning in science and describe students' questions as an important resource for meaningful learning and scientific inquiry. They also note that much of this potential remains untapped. [DOI: 10.1080/03057260701828101](https://doi.org/10.1080/03057260701828101)
- **Graesser & Person (1994)** found student questions were approximately **240× as frequent in tutoring as in classroom settings** in the environments they studied. After students gained tutoring experience, question **quality** correlated positively with achievement, while question frequency did not. [DOI: 10.3102/00028312031001104](https://doi.org/10.3102/00028312031001104)
- **OECD PISA 2022, Volume V** reports that only **47%** of students across OECD countries frequently ask questions when they do not understand mathematics material; among low performers, the average is below 40%. The OECD treats active questioning as an important learning strategy. [PISA 2022 Results — Learning strategies](https://www.oecd.org/en/publications/pisa-2022-results-volume-v_c2e44201-en/full-report/component-10.html)
- **Au (2007)** synthesized 49 qualitative studies of high-stakes testing. The most common pattern was curriculum narrowing, fragmentation into test-related knowledge, and more teacher-centred pedagogy, while also noting important counterexamples depending on test design. [DOI: 10.3102/0013189X07306523](https://doi.org/10.3102/0013189X07306523)

The point is not to reward people for asking *more* questions. It is to make the **purpose, formulation, evidence needs, and evolution of questions visible**.

---

## What Question Radar does

```text
raw question
     ↓
question type + readiness
     ↓
formulation profile
     ↓
assumptions + evidence needed
     ↓
stronger next question
     ↓
optional learning observation
```

On `main` (v0.3), it currently helps answer four practical questions:

1. **What kind of question is this?**
2. **Is it ready to answer, ready to investigate, or missing context?**
3. **What assumptions or evidence still need to be surfaced?**
4. **What stronger question could come next?**

The proposed v0.4 extends that flow with explicit question lineage and deterministic Context Packs; those capabilities remain part of this PR until it is merged.

The system is deliberately transparent. There is no external LLM deciding what somebody knows, no learner ranking, and no hidden intelligence or mastery score.

---

## What this project demonstrates

Current and proposed versioned capabilities include:

- **Versioned data contracts** with backward compatibility across v0.1, v0.2, v0.3, and the proposed v0.4.
- **Strict runtime validation** for required fields, closed vocabularies, numeric ranges, timestamps, and malformed input.
- **Normalized SQLite storage** with separate tables for historical evaluations, typed profiles, learning observations, and proposed question lineage.
- **Ordered evidence relationships** preserved across database and JSONL round trips.
- **Explicit directed question relations** with bounded, cycle-safe graph traversal in v0.4.
- **Derived Context Packs** with deterministic Markdown and JSON output in v0.4.
- **CLI design** with namespaced commands for scoring, profiling, learning-frontier, and proposed lineage workflows.
- **Explicit import/export boundaries** so local data stays local unless it is intentionally exported.
- **Regression and end-to-end testing** across models, persistence, serialization, CLI behavior, calibration corpora, and historical compatibility.

---

## Not all questions should compete on one leaderboard

Question Radar does not assume that a factual question, a diagnostic question, and a philosophical question should be judged by the same notion of "depth".

The v0.2 profile separates **question type** from **formulation quality for that purpose**.

Current types include:

```text
factual_conceptual
operational_diagnostic
scientific_explanatory
decision_risk
epistemological_meta
normative_political
generative_philosophical
```

Readiness is also explicit:

```text
ready_to_answer
ready_to_investigate
needs_context
exploratory
```

A profile can then describe clarity, boundedness, investigability, epistemic openness, purpose fit, assumptions, evidence requirements, and a possible next question.

```json
{
  "question": "¿Cómo distinguimos una pregunta profunda de una simplemente amplia?",
  "question_type": "epistemological_meta",
  "readiness": "ready_to_investigate",
  "clarity": 5,
  "boundedness": 5,
  "investigability": 5,
  "epistemic_openness": 5,
  "purpose_fit": 5,
  "formulation_score": 100
}
```

`formulation_score` is **not** a score of the person and is not used as a global ranking across question types.

---

## Personal Learning Frontier

v0.3 adds a separate evidence-first layer for tracking how questions around a concept appear to change over time.

```text
question A ──┐
question B ──┼──> LearningObservation
question C ──┘
```

The key rule is:

```text
repeated question != proven learning gap
```

A repeated question may reflect a weak previous explanation, disagreement, changed context, missing evidence, or a genuinely unresolved concept.

So Question Radar stores a **revisable observation plus the question IDs that support it**, rather than diagnosing the learner.

Possible gap types include conceptual, terminology, procedural, connection, evidence, and transfer. Observation states remain revisable: `possible_gap`, `recurring_gap`, `consolidating`, `applied`, and `no_longer_observed`.

---

## Proposed v0.4: Question Lineage and Context Pack

v0.4 makes the question itself a stable entity and connects questions with explicit, directed relations.

```text
¿Cómo puntuamos la calidad de una pregunta?
        │
        └── challenges_assumption ──>
            ¿Tiene sentido comparar con el mismo score
            una pregunta filosófica, factual y operacional?
                         │
                         └── decomposes ──>
                             ¿Estamos puntuando calidad
                             o readiness?
```

The closed v0.4 relation vocabulary is:

- `refines`
- `decomposes`
- `generalizes`
- `operationalizes`
- `challenges_assumption`
- `contrasts`
- `follows_from`

Relations are explicit calibration judgments: the runtime does not infer them silently.

From any stored question, Question Radar can derive a bounded Context Pack:

```bash
question-radar lineage context chat-2026-08-29-012 --format markdown
question-radar lineage context chat-2026-08-29-012 --format json
```

Defaults are **3 ancestor hops** and **1 descendant hop**. Traversal is cycle-safe, and the Context Pack is derived rather than persisted. It assembles stored lineage, matching profiles, learning observations, assumptions, evidence requirements, and existing next questions without inventing new epistemic claims.

---

## Architecture

```text
Question Radar
│
├── v0.1 QuestionEvaluation
│   └── frozen historical five-dimension rubric
│
├── v0.2 QuestionProfile
│   ├── type + readiness
│   ├── formulation dimensions
│   ├── assumptions
│   ├── evidence required
│   └── next question
│
├── v0.3 LearningObservation
│   ├── concept
│   ├── gap type
│   ├── state
│   ├── confidence
│   └── ordered evidence question IDs
│
└── v0.4 Question Lineage (proposed in this PR)
    ├── QuestionNode
    ├── QuestionRelation
    ├── bounded graph traversal
    └── derived Context Pack
```

Persistence after the proposed v0.4 merge would include:

```text
evaluations
question_profiles_v02
learning_observations_v03
learning_observation_evidence_v03
question_nodes_v04
question_relations_v04
```

All versions can coexist in the same database without rewriting historical contracts. Existing databases are not automatically migrated into v0.4 lineage.

---

## Tests & verification

The repository is tested as a small software system, not only as a collection of scoring examples.

**Latest verified CI suite for this PR: 252 tests passing on Python 3.11.**

That total contains **170 historical v0.1–v0.3 tests** plus **82 proposed v0.4 tests**.

Coverage includes:

- v0.1 historical model and CLI behavior;
- v0.2 profile validation and score consistency;
- v0.3 `LearningObservation` validation;
- v0.4 `QuestionNode` and `QuestionRelation` strict contracts;
- timezone-aware timestamp validation and chronological ordering across UTC offsets;
- SQLite insert/read round trips, foreign-key integrity, and initialization error handling;
- normalized evidence ordering;
- atomic lineage imports and rollback;
- duplicate and malformed input rejection;
- bounded, cycle-safe lineage traversal;
- deterministic Context Pack Markdown and JSON;
- JSONL/CSV serialization where supported;
- CLI `add`, `list`, `show`, `top`, `frontier`, `import`, `export`, and `lineage` flows;
- compatibility between v0.1, v0.2, v0.3, and v0.4 in one SQLite database;
- public calibration corpus validation;
- end-to-end lineage import → storage → traversal → v0.2/v0.3 join → Context Pack flow.

Run the full suite:

```bash
pytest -q
```

GitHub Actions runs the same suite on pull requests and on pushes to `main`, followed by `python -m compileall -q src`.

---

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate

python -m pip install -e ".[dev]"
pytest -q
```

---

## CLI

### v0.1 — historical evaluations

```bash
question-radar add examples/evaluation.example.json
question-radar list
question-radar top --limit 5
```

### v0.2 — typed profiles

```bash
question-radar profile add examples/profile.example.json
question-radar profile list
question-radar profile show qv2-001
question-radar profile top --type factual_conceptual --limit 10
question-radar profile import corpus/anti-ia-calibration-v0.2.jsonl --format jsonl
question-radar profile export exports/profiles.jsonl --format jsonl
```

### v0.3 — learning observations

```bash
question-radar learning add examples/learning_observation.example.json
question-radar learning list
question-radar learning show learning-001
question-radar learning frontier
question-radar learning import corpus/learning-frontier-chat-2026-08-29-v0.3.jsonl --format jsonl
question-radar learning export exports/learning.jsonl --format jsonl
```

### v0.4 — Question Lineage (proposed)

```bash
question-radar lineage node add question.json
question-radar lineage node list
question-radar lineage node show chat-2026-08-29-012

question-radar lineage relation add relation.json
question-radar lineage relation list
question-radar lineage relation list --question chat-2026-08-29-012

question-radar lineage import corpus/question-lineage-v0.4.jsonl
question-radar lineage context chat-2026-08-29-012 --format markdown
question-radar lineage context chat-2026-08-29-012 --format json
```

Use a different local database at any time:

```bash
question-radar --db /path/to/questions.sqlite3 profile list
```

---

## Versioned contracts

### v0.1 — historical `QuestionEvaluation`

The original rubric remains frozen as a historical contract. It should not be silently retrofitted to match later versions.

### v0.2 — `QuestionProfile`

Each profile stores:

- stable `id`;
- original `question`;
- `question_type`;
- `readiness`;
- five formulation dimensions;
- `formulation_score`;
- descriptive traits (`depth`, `connections`, `generativity`);
- `strengths`;
- `gap`;
- `assumptions`;
- `evidence_required`;
- `next_question`;
- optional `topic`;
- evaluator and rubric version;
- timestamp.

### v0.3 — `LearningObservation`

Each observation stores:

- `concept`;
- gap type;
- revisable state;
- confidence;
- ordered `evidence_question_ids`;
- interpretation;
- suggested next step;
- created/updated timestamps.

Confidence:

```text
low
medium
high
```

See `examples/learning_observation.example.json` and `corpus/learning-frontier-chat-2026-08-29-v0.3.jsonl`.

### v0.4 — question lineage (proposed)

`QuestionNode` stores exactly:

- `id`
- `question`
- `source`
- `source_ref`
- `created_at`

`QuestionRelation` stores exactly:

- `id`
- `source_question_id`
- `target_question_id`
- `relation_type`
- `created_at`

The graph allows semantic cycles but rejects self-relations and exact duplicate edges. Historical questions enter lineage only through explicit import.

---

## Public calibration data

The repository includes intentionally public calibration corpora. They are small enough to inspect directly and versioned by contract.

Current datasets include:

- `anti-ia-seed-v0.1.jsonl`
- `anti-ia-calibration-v0.2.jsonl`
- `chat-2026-08-29.jsonl`
- `learning-frontier-chat-2026-08-29-v0.3.jsonl`
- `question-lineage-v0.4.jsonl` (proposed in this PR)

They are **calibration judgments, not truth labels and not scores of people**.

---

## Data and privacy boundaries

Question Radar is local-first by design:

- SQLite databases are ignored by Git;
- questions become public only through explicit export/share actions;
- no complete chat history is ingested automatically;
- no API key or external account is required;
- no user identity model or learner ranking exists;
- published corpora are calibration judgments, not truth labels and not scores of people;
- v0.4 performs no automatic historical migration or chat ingestion.

---

## Scope

Question Radar intentionally stays small.

Not included in the current version or proposed v0.4: web frontend, Supabase, authentication, embeddings, LangGraph, NetworkX, Neo4j, external LLM API calls, automatic chat scraping, automatic relation inference, multi-user analytics, or direct GeoPlatform / Anti IA runtime integration.

The proposed v0.4 extends the core data model to: **questions → profiles → evidence → revisable learning observations → explicit lineage → deterministic context for the next question**.

---

## What Question Radar is not

It is not:

- a student grading system;
- an intelligence, mastery, curiosity, or creativity score;
- a claim that question quality can be reduced to one universal number;
- an automatic diagnosis of learning deficits;
- an LLM judge of people;
- automatic chat surveillance;
- a replacement for teachers, tutors, researchers, or domain review.

It is a small experiment in treating **questions themselves as durable learning and research artifacts**.

## License

MIT License.
