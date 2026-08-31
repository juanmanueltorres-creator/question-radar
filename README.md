# Question Radar

> **Education records answers. Question Radar preserves the questions that make the next investigation possible.**

We routinely store grades, assignments, correct answers, mistakes, tickets, search results, and chat responses. We much less often preserve **how a question changes**: what it is trying to understand, what assumptions it carries, what evidence it needs, and what stronger question follows.

Question Radar is a small, local-first Python system for turning questions into structured, inspectable data — **without turning them into a score of the person asking them**.

**Current `main`: v0.3 · Question Profiles + Personal Learning Frontier**

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

It currently helps answer four practical questions:

1. **What kind of question is this?**
2. **Is it ready to answer, ready to investigate, or missing context?**
3. **What assumptions or evidence still need to be surfaced?**
4. **What stronger question could come next?**

The system is deliberately transparent. There is no external LLM deciding what somebody knows, no learner ranking, and no hidden intelligence or mastery score.

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
└── v0.3 LearningObservation
    ├── concept
    ├── gap type
    ├── state
    ├── confidence
    └── ordered evidence question IDs
```

Persistence is local SQLite. Historical versions coexist without rewriting their contracts.

The runtime intentionally has **no third-party dependencies**. Development uses `pytest`.

---

## Quick start

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate

python -m pip install -e ".[dev]"
pytest -q
```

Example CLI flows:

```bash
# typed profiles
question-radar profile add examples/profile.example.json
question-radar profile list
question-radar profile top --type factual_conceptual --limit 10

# learning observations
question-radar learning add examples/learning_observation.example.json
question-radar learning frontier
```

Use another local database with:

```bash
question-radar --db /path/to/questions.sqlite3 profile list
```

---

## Data and privacy boundaries

Question Radar is local-first by design:

- SQLite databases are ignored by Git;
- questions become public only through explicit export/share actions;
- no complete chat history is ingested automatically;
- no API key or external account is required;
- no user identity model or learner ranking exists;
- published corpora are calibration judgments, not truth labels and not scores of people.

The `corpus/` directory contains intentionally public calibration datasets for the versioned contracts.

---

## Verification

The merged v0.1–v0.3 system has been exercised through model, SQLite, serialization, CLI, calibration, privacy, and end-to-end regression tests.

The latest verified local suite reported for the merged v0.3 work is **170 tests passing**.

There is currently **no GitHub Actions workflow**, so local verification is not presented as remote CI.

---

## In development — Question Lineage v0.4

Question Lineage is implemented in an **open pull request and is not part of `main` yet**.

Its direction is to preserve explicit relationships between questions such as:

```text
Question A
    ↓ challenges_assumption
Question B
    ↓ decomposes
Question C
    ↓ operationalizes
Question D
```

The proposed v0.4 layer adds stable question nodes, explicit directed relations, bounded cycle-safe traversal, and deterministic Context Packs that can assemble relevant question history without silently inferring new relations.

Until that work is reviewed and merged, **v0.3 remains the canonical public implementation**.

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
