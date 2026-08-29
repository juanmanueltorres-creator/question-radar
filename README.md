# Question Radar

Question Radar profiles **questions, not people**.

It is a small, transparent experiment for making question quality inspectable:
what kind of question is being asked, whether it is ready for its purpose,
which assumptions or evidence gaps remain, and what stronger question should
come next.

The output is **diagnostic guidance, not an authority claim**.

## Why

Good questions expose uncertainty, assumptions, evidence gaps, useful
connections, and decision boundaries. Question Radar keeps those features
visible instead of hiding judgment behind an opaque score.

This repository is also a safe laboratory for a future Anti IA question
workflow, but it has **no runtime dependency on Anti IA or GeoPlatform**.

## Compatible layers

### v0.1 — historical question score

v0.1 is frozen and remains supported for historical calibration data.

Its five 0–5 dimensions are:

- `clarity`
- `depth`
- `investigability`
- `assumption_challenge`
- `connections`

Score:

```text
round(sum(dimensions) / 25 * 100)
```

See `rubric/v0.1.json` and `examples/evaluation.example.json`.

### v0.2 — typed question profile

v0.2 does not ask only “how good is this question?”. It asks:

- what purpose the question serves;
- whether it is ready to answer, investigate, needs context, or is intentionally exploratory;
- how well formulated it is for that purpose;
- what assumptions and evidence needs remain;
- what useful next question follows.

Question types:

- `factual_conceptual`
- `operational_diagnostic`
- `scientific_explanatory`
- `decision_risk`
- `epistemological_meta`
- `normative_political`
- `generative_philosophical`

Readiness states:

- `ready_to_answer`
- `ready_to_investigate`
- `needs_context`
- `exploratory`

Universal formulation dimensions, each 0–5:

- `clarity`
- `boundedness`
- `investigability`
- `epistemic_openness`
- `purpose_fit`

Diagnostic formulation score:

```text
round((clarity + boundedness + investigability + epistemic_openness + purpose_fit) / 25 * 100)
```

Descriptive traits are stored separately and do **not** affect that score:

- `depth`
- `connections`
- `generativity`

A factual question is therefore not penalized merely for being intentionally
narrow, and an exploratory philosophical question is not treated as defective
because it is not immediately answerable.

**There is no global leaderboard across question types.** `profile top`
requires an explicit type.

See `rubric/v0.2.json` and `examples/profile.example.json`.

### v0.3 — Personal Learning Frontier

v0.3 adds a separate evidence-first learning layer. It does **not** score a
learner and it does not claim to know what a person understands internally. A
`LearningObservation` is a revisable hypothesis supported by explicit, ordered
question IDs.

Gap types:

- `conceptual`
- `terminology`
- `procedural`
- `connection`
- `evidence`
- `transfer`

Observation states:

- `possible_gap`
- `recurring_gap`
- `consolidating`
- `applied`
- `no_longer_observed`

Confidence values:

- `low`
- `medium`
- `high`

Two rules are intentionally strict: **silence is not evidence of mastery or
ignorance**, and repeated questions do not automatically prove a learning gap.
Evidence IDs remain inspectable and ordered so an observation can always be
checked against the questions that support it.

The Learning Frontier is a deterministic summary of stored observations. It
does not infer new concepts, states, or confidence at render time.

See `examples/learning_observation.example.json` and
`corpus/learning-frontier-chat-2026-08-29-v0.3.jsonl`.

## Privacy model

- Code and rubrics are public.
- `data/questions.sqlite3` is local and ignored by Git.
- v0.1 evaluations, v0.2 profiles, and v0.3 learning observations use separate SQLite tables.
- Questions become public only when you explicitly export and then share or commit a JSONL/CSV file.
- No secrets, API keys, external AI calls, accounts, or paid services are required.

## Install

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## CLI

### v0.1

```bash
question-radar add examples/evaluation.example.json
question-radar list
question-radar top --limit 10
question-radar import questions.jsonl --format jsonl
question-radar export exports/questions.csv --format csv
```

### v0.2 profiles

```bash
question-radar profile add examples/profile.example.json
question-radar profile list
question-radar profile top --type factual_conceptual --limit 10
question-radar profile import corpus/anti-ia-calibration-v0.2.jsonl --format jsonl
question-radar profile export exports/profiles.csv --format csv
```

### v0.3 learning frontier

```bash
question-radar learning add examples/learning_observation.example.json
question-radar learning list
question-radar learning show learning-001
question-radar learning frontier
question-radar learning import corpus/learning-frontier-chat-2026-08-29-v0.3.jsonl --format jsonl
question-radar learning export exports/learning.jsonl --format jsonl
```

v0.3 learning import/export is intentionally JSONL-only. v0.1 and v0.2 remain
historical, supported, and unchanged.

Use another local database for either version:

```bash
question-radar --db /path/to/questions.sqlite3 profile list
```

## Calibration data

`corpus/anti-ia-calibration-v0.2.jsonl` contains a deliberately heterogeneous
set of Anti IA questions across all seven types and all four readiness states.
The profiles are calibration judgments, not truth labels.

`corpus/learning-frontier-chat-2026-08-29-v0.3.jsonl` contains three
evidence-backed observations over the 12-question real chat corpus, including a
repeated-question case that intentionally remains `possible_gap` rather than
being promoted automatically to `recurring_gap`.

## Development

```bash
pytest -q
```

## Boundaries

Not included: web frontend, Supabase, authentication, embeddings, LangGraph,
external LLM API calls, automatic scoring from conversation history, automatic
publication, direct Anti IA runtime integration, or GeoPlatform changes.
