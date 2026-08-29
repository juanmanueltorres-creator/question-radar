# Question Radar

**A small Python system for turning questions into structured, inspectable data.**

Question Radar helps answer four practical things:

1. **What kind of question is this?**
2. **Is it ready to answer or investigate?**
3. **What assumptions or evidence are still missing?**
4. **What stronger question should come next?**

It also tracks how questions evolve over time, so repeated doubts can become useful evidence instead of just another chat message.

> **Question Radar evaluates questions, not people.**

**Stack:** Python 3.11+ · SQLite · CLI · JSONL/CSV · standard library runtime only

---

## What it does

A raw question can be useful, but it often mixes together context, assumptions, uncertainty, and intent.

Question Radar makes those parts explicit.

```text
"¿Por qué seguimos preguntando lo mismo?"
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

That makes questions easier to compare, refine, store, audit, and revisit later.

The project is intentionally transparent: there is no hidden learner score and no opaque model deciding what somebody "knows".

---

## What this project demonstrates

- **Versioned data contracts** with backward compatibility across v0.1, v0.2, and v0.3.
- **Strict runtime validation** for required fields, closed vocabularies, numeric ranges, timestamps, and malformed input.
- **Normalized SQLite storage** with separate tables for historical evaluations, typed profiles, and learning observations.
- **Ordered evidence relationships** preserved across database and JSONL round trips.
- **CLI design** with namespaced commands for scoring, profiling, and learning-frontier workflows.
- **Explicit import/export boundaries** so local data stays local unless it is intentionally exported.
- **Regression and end-to-end testing** across models, persistence, serialization, CLI behavior, calibration corpora, and historical compatibility.

No external API, paid service, database server, LLM runtime, or account is required.

---

## Example: typed question profile

A v0.2 profile does not ask whether a question is simply "good" or "bad".

It records what the question is trying to do and how well it is formulated for that purpose.

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

A factual question and a philosophical question are not forced into the same global leaderboard. The score only describes **formulation quality for the declared purpose**.

---

## Example: Personal Learning Frontier

v0.3 adds a second layer: evidence-backed observations about how a sequence of questions is changing.

```text
question-1 ──┐
question-2 ──┼──> LearningObservation
question-3 ──┘

concept: question_evaluation_models
state: consolidating
confidence: medium
```

The important distinction is:

```text
repeated question ≠ proven learning gap
```

Repetition can also mean a weak previous explanation, disagreement, changed context, or a genuinely unresolved problem.

So the system stores a **revisable hypothesis plus the question IDs that support it** instead of making a diagnosis about the person.

---

## Architecture

```text
Question Radar
│
├── v0.1 QuestionEvaluation
│   └── historical five-dimension scoring
│
├── v0.2 QuestionProfile
│   ├── question type
│   ├── readiness
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

Persistence is local SQLite:

```text
evaluations
question_profiles_v02
learning_observations_v03
learning_observation_evidence_v03
```

The three versions can coexist in the same database without ID collisions between their separate contracts.

---

## Tests & verification

The repository is tested as a small software system, not only as a collection of scoring examples.

**Latest verified suite: 170 tests passing.**

Coverage includes:

- v0.1 historical model and CLI behavior;
- v0.2 profile validation and score consistency;
- v0.3 `LearningObservation` validation;
- timezone-aware timestamp checks;
- SQLite insert/read round trips;
- normalized evidence ordering;
- duplicate and malformed input rejection;
- JSONL/CSV serialization where supported;
- CLI `add`, `list`, `show`, `top`, `frontier`, `import`, and `export` flows;
- compatibility between v0.1, v0.2, and v0.3 in one SQLite database;
- public calibration corpus validation;
- end-to-end learning-frontier import → storage → render → export flow.

Run the full suite:

```bash
pytest -q
```

There is currently **no GitHub Actions workflow**, so this README does not present the local test run as remote CI.

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
question-radar top --limit 10
question-radar import questions.jsonl --format jsonl
question-radar export exports/questions.csv --format csv
```

### v0.2 — typed question profiles

```bash
question-radar profile add examples/profile.example.json
question-radar profile list
question-radar profile top --type factual_conceptual --limit 10
question-radar profile import corpus/anti-ia-calibration-v0.2.jsonl --format jsonl
question-radar profile export exports/profiles.csv --format csv
```

### v0.3 — Personal Learning Frontier

```bash
question-radar learning add examples/learning_observation.example.json
question-radar learning list
question-radar learning show learning-001
question-radar learning frontier
question-radar learning import corpus/learning-frontier-chat-2026-08-29-v0.3.jsonl --format jsonl
question-radar learning export exports/learning.jsonl --format jsonl
```

Use a different local database at any time:

```bash
question-radar --db /path/to/questions.sqlite3 profile list
```

---

## Versioned contracts

### v0.1 — frozen historical score

Dimensions, each 0–5:

- `clarity`
- `depth`
- `investigability`
- `assumption_challenge`
- `connections`

```text
score = round(sum(dimensions) / 25 * 100)
```

See `rubric/v0.1.json` and `examples/evaluation.example.json`.

### v0.2 — typed profile

Question types:

- `factual_conceptual`
- `operational_diagnostic`
- `scientific_explanatory`
- `decision_risk`
- `epistemological_meta`
- `normative_political`
- `generative_philosophical`

Readiness:

- `ready_to_answer`
- `ready_to_investigate`
- `needs_context`
- `exploratory`

Formulation dimensions, each 0–5:

- `clarity`
- `boundedness`
- `investigability`
- `epistemic_openness`
- `purpose_fit`

```text
formulation_score =
round((clarity + boundedness + investigability + epistemic_openness + purpose_fit) / 25 * 100)
```

Descriptive traits such as `depth`, `connections`, and `generativity` are stored separately and do not affect that score.

See `rubric/v0.2.json` and `examples/profile.example.json`.

### v0.3 — learning observations

Gap types:

- `conceptual`
- `terminology`
- `procedural`
- `connection`
- `evidence`
- `transfer`

States:

- `possible_gap`
- `recurring_gap`
- `consolidating`
- `applied`
- `no_longer_observed`

Confidence:

- `low`
- `medium`
- `high`

See `examples/learning_observation.example.json` and `corpus/learning-frontier-chat-2026-08-29-v0.3.jsonl`.

---

## Public calibration data

The `corpus/` directory contains intentionally published calibration data.

Current datasets include:

- `anti-ia-seed-v0.1.jsonl`
- `anti-ia-calibration-v0.2.jsonl`
- `chat-2026-08-29.jsonl`
- `learning-frontier-chat-2026-08-29-v0.3.jsonl`

They are **calibration judgments, not truth labels and not scores of people**.

---

## Privacy by default

- SQLite data stays local and is ignored by Git.
- Questions become public only through explicit export and commit/share actions.
- No API keys or secrets are required.
- No complete chat history is ingested automatically.
- No user identity model, learner ranking, intelligence score, or mastery percentage exists.

---

## Scope

Question Radar intentionally stays small.

Not included in the current version: web frontend, Supabase, authentication, embeddings, LangGraph, external LLM API calls, automatic chat scraping, multi-user analytics, or direct GeoPlatform / Anti IA runtime integration.

The current focus is the core data model: **questions → profiles → evidence → stronger questions → revisable learning observations**.
