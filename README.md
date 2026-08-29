# Question Radar

Question Radar evaluates **questions, not people**.

It is a small, transparent experiment for recording the quality of a question
across five explicit dimensions, verifying a reproducible 0-100 score, storing
history locally, and suggesting what the next stronger question could be.

The score is **diagnostic guidance, not an authority claim**.

## Why

Good questions expose uncertainty, assumptions, evidence gaps, and useful
connections. Question Radar makes those dimensions visible instead of hiding a
judgment behind a single opaque number.

This repository is also a safe laboratory for a future Anti IA question
workflow, but the MVP has **no runtime dependency on Anti IA or GeoPlatform**.

## Rubric v0.1

Each dimension is scored from 0 to 5:

| Dimension | Question |
| --- | --- |
| clarity | Is the question understandable and sufficiently bounded? |
| depth | Does it move beyond superficial lookup toward causes, mechanisms, implications, or structure? |
| investigability | Can evidence, data, experiments, documents, or observations address it? |
| assumption_challenge | Does it surface or question implicit assumptions? |
| connections | Does it connect concepts, scales, domains, evidence types, or prior knowledge meaningfully? |

Score:

```text
round(sum(dimensions) / 25 * 100)
```

A supplied score that does not match the dimensions is rejected.

## Privacy model

- Code and rubric are public.
- `data/questions.sqlite3` is local and ignored by Git.
- Questions become public only when you explicitly export and then share or commit a JSONL/CSV file.
- The MVP needs no secrets, API keys, external AI calls, accounts, or paid services.

## Install

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Evaluation contract

See `examples/evaluation.example.json`.

An external evaluator — a human, ChatGPT, or another future model — creates the
structured evaluation. Question Radar validates it. The evaluator can change
later without changing the storage contract.

## CLI

```bash
question-radar add examples/evaluation.example.json
question-radar list
question-radar top --limit 10
question-radar import questions.jsonl --format jsonl
question-radar import questions.csv --format csv
question-radar export exports/questions.jsonl --format jsonl
question-radar export exports/questions.csv --format csv
question-radar --db /path/to/questions.sqlite3 list
```

## Development

```bash
pytest -q
```

## MVP boundaries

Not included: web frontend, Supabase, authentication, embeddings, LangGraph,
external LLM API calls, automatic publication, direct Anti IA integration, or
GeoPlatform changes. Those omissions are deliberate: first validate whether the
rubric and question history are useful.
