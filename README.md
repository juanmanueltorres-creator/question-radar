# Question Radar

> **Education records answers. Question Radar preserves the questions that make the next investigation possible.**

We routinely store grades, assignments, correct answers, mistakes, tickets, search results, and chat responses. We much less often preserve **how a question changes**: what it is trying to understand, what assumptions it carries, what evidence it needs, and what stronger question follows.

Question Radar is a small, local-first Python system for turning questions into structured, inspectable data — **without turning them into a score of the person asking them**.

**Version:** v0.9 · Investigation Decision Gate + v0.8 Gold Evaluation Harness + v0.7 Retrieval Calibration & Abstention

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

The point is not to reward people for asking *more* questions. It is to make the **purpose, formulation, evidence needs, evolution, corpus-relative position, and attention decision around questions visible**.

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
     ↓
explicit question lineage
     ↓
deterministic Context Pack

new candidate question
     ↓
retrieval-specific normalization
     ↓
unified candidate retrieval (v0.2 + v0.4)
     ↓
coverage + BM25 + frozen v0.5 Jaccard evidence
     ↓
┌─────────────────────┬──────────────────────┐
│ lexical evidence    │ no lexical evidence  │
│ present             │                      │
▼                     ▼
ranked candidates     ABSTAIN
     ↓
human review
     ↓
optional v0.5 novelty review against lineage
     ↓
optional explicit v0.4 lineage decision

explicit question identity
     ↓
operator investigation decision (v0.9)
     ↓
DO_NOW / RESEARCH / PARKED / KILLED
     ↓
append-only supersession when judgment changes
```

Question Radar helps answer practical questions such as:

1. **What kind of question is this?**
2. **Is it ready to answer, ready to investigate, or missing context?**
3. **What assumptions or evidence still need to be surfaced?**
4. **What stronger question could come next?**
5. **How does this question relate explicitly to earlier or later questions?**
6. **What bounded, inspectable context is useful for the next investigation?**
7. **Which existing questions are lexically close to a new candidate, and what evidence explains that proximity?**
8. **What terms remain unexplained by the nearest corpus questions and may deserve human review as a new mechanism or branch?**
9. **Which prior questions exist outside the lineage graph and should be reviewed before treating a candidate as new?**
10. **When is there no lexical retrieval evidence at all, so the system should abstain rather than fabricate a shortlist?**
11. **Should a preserved question consume attention now, bounded research, no current action, or explicit abandonment?**

The system is deliberately transparent. There is no external LLM deciding what somebody knows, no learner ranking, no hidden intelligence or mastery score, no automatic semantic relation, and no automatic v0.9 prioritization decision.

---

## What this project demonstrates

- **Versioned data contracts** with backward compatibility from v0.1 through v0.9.
- **Strict runtime validation** for required fields, closed vocabularies, booleans, numeric ranges, timestamps, and malformed input.
- **Normalized SQLite storage** with separate tables for historical evaluations, typed profiles, learning observations, question lineage, and v0.9 investigation decisions.
- **Ordered evidence relationships** preserved across database and JSONL round trips.
- **Explicit directed question relations** with bounded, cycle-safe graph traversal.
- **Derived Context Packs** with deterministic Markdown and JSON output.
- **Read-only corpus-relative novelty packs** with inspectable lexical overlap and residual-token evidence.
- **Unified read-only retrieval** across v0.2 profiles and v0.4 lineage without creating a new persistence layer.
- **Dependency-free BM25 retrieval** with per-token contribution evidence and frozen v0.5 Jaccard as a secondary signal.
- **Retrieval-specific lexical normalization** that does not silently alter the frozen novelty contract.
- **Coverage-aware retrieval evidence** with matched-token count and query coverage.
- **Explicit abstention** when the lexical layer finds no supported overlap.
- **Gold evaluation** against frozen editorial expectations without redefining sparse unjudged entries as negatives.
- **Append-only investigation decisions** linked to existing v0.4 question identity.
- **Explicit supersession history** so changed judgment does not rewrite earlier context.
- **Advisory WIP visibility** when more than three investigations are marked `DO_NOW`, without automatic demotion or prioritization.
- **Fail-closed v0.4 prerequisite checks** so v0.9 never creates historical lineage tables merely to satisfy itself.
- **Explicit import/export boundaries** so local data stays local unless it is intentionally exported.
- **Regression and end-to-end testing** across models, persistence, serialization, CLI behavior, blind calibration inputs, historical compatibility, and v0.9 dogfood.

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

A profile can describe clarity, boundedness, investigability, epistemic openness, purpose fit, assumptions, evidence requirements, and a possible next question.

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

A repeated question may reflect a weak previous explanation, disagreement, changed context, missing evidence, or a genuinely unresolved concept. Question Radar stores a **revisable observation plus the question IDs that support it**, rather than diagnosing the learner.

---

## v0.4: Question Lineage and Context Pack

v0.4 makes the question itself a stable entity and connects questions with explicit, directed relations.

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

Defaults are **3 ancestor hops** and **1 descendant hop**. Traversal is cycle-safe, and the Context Pack is derived rather than persisted.

---

## v0.5: Corpus-Relative Novelty

v0.5 addresses a different failure mode: a question can be excellent and still be redundant relative to what a corpus already contains.

The layer compares a candidate against stored v0.4 `QuestionNode` text using dependency-free, deterministic lexical evidence. It reports nearest questions, shared tokens and bigrams, residual candidate terms, lineage degree as context, and conservative review prompts.

> **Question Radar may surface evidence that two questions occupy similar or different lexical neighborhoods of the corpus. It does not decide that they mean the same thing.**

Normalization performs no embeddings, vector search, synonym expansion, or LLM inference. Every `NoveltyPack` requires human review.

---

## v0.6: Unified Candidate Retrieval

v0.6 adds unified read-only visibility across supported question-bearing tables:

```text
question_profiles_v02 ──┐
                        ├──> CorpusEntry[] ──> BM25 retrieval
question_nodes_v04 ─────┘                     + v0.5 Jaccard evidence
```

No unified table is persisted. SQLite is opened read-only and a missing database is not created.

> **Retrieval means “review this prior question before calling the candidate new.” It does not mean “these questions are semantically equivalent.”**

---

## v0.7: Retrieval Calibration & Abstention

v0.7 adds retrieval-specific lexical normalization, narrow noun-focused morphology, coverage-aware ranking, and explicit abstention when the corpus has no lexical evidence.

```text
abstained = true
abstention_reason = no_lexical_evidence
results = []
review_required = true
```

An abstention is not a claim of conceptual novelty. It means only that this lexical retrieval layer found no supported overlap.

---

## v0.8: Gold Evaluation Harness

v0.8 freezes editorial retrieval expectations before introducing new retrieval experiments.

Gold judgments distinguish `relevant`, `partially_relevant`, and `not_relevant`, while sparse positive-only judgments never turn unjudged entries into implicit negatives.

The evaluator reports inspectable retrieval metrics such as Hit Rate@k, Recall@k, MRR, false abstentions, and abstention-control accuracy. Precision@k is withheld when the relevance set is not exhaustive.

The boundary remains explicit:

> Gold judgments encode editorial review expectations, not semantic equivalence or lineage.

---

## v0.9: Investigation Decision Gate

v0.9 addresses an operational problem that is different from question quality or retrieval:

```text
interesting question
        ↓
should this consume attention now?
```

The operator records one of four states:

```text
DO_NOW
RESEARCH
PARKED
KILLED
```

Each decision preserves rationale, four explicit gates (`goal_alignment`, `external_signal`, `testable_now`, `leverage`), qualitative cost/confidence, and state-specific next conditions.

`DO_NOW` and `RESEARCH` require a `next_test`. `PARKED` requires a `resume_when` condition.

Decisions are immutable. A changed judgment creates a new row with `supersedes_decision_id`; the previous context is never rewritten.

> **Decision gates are operator judgments. Question Radar records and validates them; it does not decide automatically what deserves attention.**

The `decision active` projection warns when more than three current investigations are `DO_NOW`, but the warning is advisory only. It never blocks the fourth decision, demotes work, or chooses what should be parked.

The key distinction is:

> **Preserving a question is not the same as committing attention to it.**

---

## Architecture

```text
Question Radar
│
├── v0.1 QuestionEvaluation
├── v0.2 QuestionProfile
├── v0.3 LearningObservation
├── v0.4 Question Lineage + Context Pack
├── v0.5 Corpus-Relative Novelty
├── v0.6 Unified Candidate Retrieval
├── v0.7 Retrieval Calibration & Abstention
├── v0.8 Gold Evaluation Harness
└── v0.9 Investigation Decision Gate
    ├── InvestigationDecision
    ├── append-only supersession chain
    ├── derived current-state projection
    ├── deterministic Markdown / JSON
    └── advisory WIP visibility
```

Persistence includes:

```text
evaluations
question_profiles_v02
learning_observations_v03
learning_observation_evidence_v03
question_nodes_v04
question_relations_v04
investigation_decisions_v09
```

v0.5, v0.6, v0.7, and v0.8 add no production SQLite tables. v0.9 owns only `investigation_decisions_v09` and fails closed if the canonical v0.4 question identity prerequisite is absent or structurally unsupported.

---

## Tests & verification

The repository is tested as a small software system, not only as a collection of scoring examples.

**Latest verified implementation CI suite: 392 tests passing on Python 3.11.**

Coverage includes historical v0.1-v0.8 contracts plus:

- immutable v0.9 decision validation;
- closed decision/cost/confidence vocabularies;
- strict real-boolean gates;
- state-specific `next_test` / `resume_when` requirements;
- fail-closed v0.4 prerequisite validation;
- SQLite boolean round-trips;
- append-only inserts and duplicate-id rejection;
- same-question, current-leaf-only supersession;
- ambiguity/corruption failure;
- deterministic current and history projections;
- deterministic Markdown/JSON rendering;
- zero-state and WIP projections;
- installed v0.9 CLI plus historical namespace compatibility;
- sanitized three-case dogfood (`PARKED`, `RESEARCH`, `DO_NOW`).

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
question-radar profile top --type factual_conceptual --limit 10
```

### v0.3 — learning observations

```bash
question-radar learning add examples/learning_observation.example.json
question-radar learning list
question-radar learning show learning-001
question-radar learning frontier
```

### v0.4 — Question Lineage

```bash
question-radar lineage node add question.json
question-radar lineage node list
question-radar lineage relation add relation.json
question-radar lineage context chat-2026-08-29-012 --format markdown
```

### v0.5 — corpus-relative novelty

```bash
question-radar novelty compare \
  "¿Qué debería recordar una organización y qué debería poder olvidar?" \
  --limit 5 \
  --format markdown
```

### v0.7 — calibrated unified candidate retrieval

```bash
question-radar retrieval compare \
  "¿Qué pregunta anterior debería revisar antes de tratar esta como nueva?" \
  --limit 5 \
  --format json
```

### v0.8 — gold evaluation

```bash
question-radar benchmark evaluate \
  --benchmark corpus/blind-representations-2026-09-01.jsonl \
  --gold corpus/gold/blind-representations-2026-09-01-gold-v1.jsonl \
  --k 5 \
  --format markdown
```

### v0.9 — investigation decisions

The decision namespace requires an existing v0.4 question node.

```bash
question-radar decision record \
  --question-id q-spqr-001 \
  --decision PARKED \
  --rationale "High learning value, no current production need." \
  --goal-alignment false \
  --external-signal true \
  --testable-now false \
  --leverage true \
  --cost high \
  --confidence medium \
  --resume-when "A real PostgreSQL workload requires horizontal scaling."

question-radar decision show q-spqr-001 --format markdown
question-radar decision history q-spqr-001 --format json
question-radar decision active --format markdown
```

If the judgment later changes, create a new decision and pass the exact current decision id through `--supersedes`. Existing decision rows are never overwritten.

---

## Versioned contracts

- **v0.1 — `QuestionEvaluation`:** frozen historical rubric.
- **v0.2 — `QuestionProfile`:** typed purpose/readiness plus formulation evidence.
- **v0.3 — `LearningObservation`:** revisable evidence-backed learning observation.
- **v0.4 — `QuestionNode` / `QuestionRelation`:** explicit durable question identity and lineage.
- **v0.5 — novelty evidence:** derived lexical comparison only.
- **v0.6 — unified retrieval corpus:** derived read-only visibility across v0.2/v0.4.
- **v0.7 — calibrated retrieval evidence:** coverage and explicit abstention.
- **v0.8 — gold evaluation:** frozen editorial retrieval expectations and reproducible metrics.
- **v0.9 — `InvestigationDecision`:** immutable operator decision linked to v0.4 question identity, with append-only supersession.

No later version silently rewrites an earlier contract.

---

## Public calibration data

The repository includes intentionally public calibration corpora and blind inputs. They are small enough to inspect directly and versioned by contract or benchmark purpose.

They include v0.1/v0.2 calibration data, v0.4 lineage corpora, blind retrieval inputs, frozen v0.8 gold judgments, and sanitized dogfood records. These artifacts are **calibration evidence, not truth labels and not scores of people**.

The v0.9 dogfood record is `benchmarks/dogfood-investigation-decision-gate-2026-09-04.md` and its executable regression is `tests/test_decision_dogfood.py`.

---

## Data and privacy boundaries

Question Radar is local-first by design:

- SQLite databases are ignored by Git;
- questions become public only through explicit export/share actions;
- no complete chat history is ingested automatically;
- no API key or external account is required;
- no user identity model or learner ranking exists;
- published corpora are calibration judgments or explicit benchmark inputs, not truth labels and not scores of people;
- v0.4 performs no automatic historical migration or chat ingestion;
- v0.5 novelty and v0.6/v0.7 retrieval preserve fail-closed read boundaries;
- v0.8 evaluation writes no semantic or lineage conclusions;
- v0.9 creates only `investigation_decisions_v09`, requires pre-existing v0.4 question identity, and never automatically changes a decision.

---

## Scope

Question Radar intentionally stays small.

Not included in v0.9: web frontend, Supabase, authentication, embeddings, vector databases, LangGraph, NetworkX, Neo4j, external LLM API calls, synonym expansion, general language stemming, automatic chat scraping, automatic relation inference, automatic master promotion, automatic prioritization, RICE/weighted priority scoring, agents, schedulers, automatic `PARKED` reactivation, background monitoring, or direct GeoPlatform / Opportunity OS / Andes Context OS runtime integration.

The current core model is:

> **questions → profiles → evidence → revisable learning observations → explicit lineage → inspectable retrieval/evaluation → explicit operator attention decision**

---

## What Question Radar is not

It is not:

- a student grading system;
- an intelligence, mastery, curiosity, or creativity score;
- a claim that question quality can be reduced to one universal number;
- an automatic diagnosis of learning deficits;
- an LLM judge of people;
- an automatic semantic-equivalence oracle;
- an automatic master-question curator;
- an automatic prioritization engine;
- automatic chat surveillance;
- a replacement for teachers, tutors, researchers, domain review, or operator judgment.

It is a small experiment in treating **questions themselves as durable learning and research artifacts**, while making the decision to spend attention explicit and auditable.

## License

MIT License.
