# Question Radar

> **A good answer can close a task. A good question can open an investigation.**

Question Radar is a local-first system for **keeping useful questions alive long enough to investigate them well**.

Instead of letting a question disappear inside a chat, note, meeting or search session, it can preserve the question, make its assumptions and evidence needs visible, connect it to earlier questions, check whether the corpus already contains something relevant, and record whether a human actually wants to spend attention on it now.

When that decision is `DO_NOW` or `RESEARCH`, Question Radar can also export a **bounded, versioned research handoff** to another independent workflow without pretending that the question is already a problem, an opportunity or evidence.

```text
question appears
      ↓
preserve it
      ↓
what is it really asking?
      ↓
what assumptions / evidence does it need?
      ↓
have we asked something related before?
      ↓
how does it connect to the question history?
      ↓
should this consume attention now?
      ↓
DO_NOW / RESEARCH / PARKED / KILLED
      ↓
optional explicit research handoff
```

**Current product line:** v0.9 Investigation Decision Gate + Cross-Repo Research Handoff v0.1  
**Stack:** Python 3.11+ · SQLite · CLI · JSONL/CSV · standard-library runtime only

Question Radar is deliberately conservative: **it structures inquiry; it does not score the person asking the question and it does not manufacture certainty to keep a pipeline moving.**

---

## The problem

We routinely preserve answers: tickets, grades, documents, search results, chat responses and decisions.

We much less often preserve **how a question evolves**:

- what it is trying to understand;
- what assumption may be hiding inside it;
- what evidence would change the answer;
- whether an older question already covers part of the same ground;
- what stronger question follows;
- whether the question deserves attention now;
- and, if it does, where the investigation should continue.

Question Radar treats the question itself as a durable research artifact.

That does **not** mean every question is profound, novel or worth acting on. A useful system must also be able to say:

```text
we already have a related question
there is not enough lexical evidence
this needs more context
this should be researched later
this should be killed
no actionable downstream candidate was found
```

Those are valid outcomes.

---

## What it does today

| Capability | What it is for |
| --- | --- |
| **Question Profile** | make question type, readiness, formulation, assumptions and evidence needs explicit |
| **Personal Learning Frontier** | preserve revisable observations about recurring concepts without diagnosing the learner |
| **Question Lineage** | connect stable questions through explicit reviewed relations and derive bounded Context Packs |
| **Corpus-Relative Novelty** | expose inspectable lexical overlap and residual terms without claiming semantic equivalence |
| **Unified Retrieval** | search v0.2 + v0.4 question corpora with dependency-free BM25 and frozen Jaccard evidence |
| **Retrieval Calibration & Abstention** | prefer supported lexical coverage and abstain when no lexical evidence exists |
| **Gold Evaluation Harness** | evaluate retrieval against frozen editorial expectations without treating sparse judgments as negatives |
| **Investigation Decision Gate** | record `DO_NOW`, `RESEARCH`, `PARKED` or `KILLED` as explicit operator judgments |
| **Cross-Repo Research Handoff** | export an authorized current investigation state as deterministic JSON to a closed downstream route |

The detailed milestone history lives in [`ROADMAP.md`](ROADMAP.md).

---

## The boundaries matter more than the score

Question Radar grew out of question-quality experiments, but the core design is now broader than a scoring rubric.

The important distinctions are explicit:

```text
question != problem
formulation score != score of a person
repeated question != proven learning gap
lexical similarity != semantic equivalence
retrieval hit != automatic lineage
abstention != proof of novelty
gold judgment != ground truth
interesting question != priority
decision != automatic action
route != opportunity
handoff != evidence
current at export != current now
```

The system is designed to **surface evidence for a human judgment**, not silently replace that judgment.

---

## From a question to an investigation

### 1. Preserve and describe the question

The v0.2 profile separates question type from formulation quality for that purpose.

Current question types include:

```text
factual_conceptual
operational_diagnostic
scientific_explanatory
decision_risk
epistemological_meta
normative_political
generative_philosophical
```

Readiness is explicit:

```text
ready_to_answer
ready_to_investigate
needs_context
exploratory
```

A profile can describe clarity, boundedness, investigability, epistemic openness, purpose fit, assumptions, evidence requirements and a possible next question.

`formulation_score` is **not** a learner, intelligence, curiosity or creativity score, and it is not a universal leaderboard across question types.

### 2. Connect it to question history

Question Lineage gives questions stable identity and explicit directed relations:

```text
refines
decomposes
generalizes
operationalizes
challenges_assumption
contrasts
follows_from
```

Relations are reviewed judgments. The runtime does not infer them silently.

From a stored question, the system can derive a bounded Context Pack with ancestors, descendants, matching profiles, learning observations, assumptions and evidence needs.

### 3. Check the corpus before calling it new

Question Radar uses two inspectable lexical layers:

- frozen v0.5 weighted token/bigram Jaccard evidence;
- v0.6/v0.7 dependency-free BM25 retrieval with matched terms, residual terms, per-token contributions and query coverage.

The rule is simple:

> **Retrieval means “review this prior question before treating the candidate as new.” It does not mean the questions are semantically equivalent.**

If the entire corpus has no supported lexical overlap, v0.7 returns an explicit abstention instead of padding the shortlist with arbitrary results:

```text
abstained = true
abstention_reason = no_lexical_evidence
results = []
review_required = true
```

### 4. Decide whether it deserves attention

The v0.9 Investigation Decision Gate records one explicit operator state:

```text
DO_NOW
RESEARCH
PARKED
KILLED
```

`DO_NOW` and `RESEARCH` require a concrete `next_test`. `PARKED` requires a `resume_when` condition.

Changed judgment is append-only: a later decision supersedes the current one without rewriting history.

> **Preserving a question is not the same as committing attention to it.**

The system can warn when more than three investigations are `DO_NOW`, but it does not automatically demote, prioritize or reactivate work.

---

## Cross-repo research handoff v0.1

Question Radar can export a current operator-authorized investigation as a deterministic JSON artifact.

It does **not** import or call another repository at runtime.

Supported routes are closed and explicit:

```text
TERRITORIAL_RESEARCH
    ↓
andes-context-os

PUBLIC_CONTRIBUTION_RESEARCH
    ↓
opportunity-os
```

Only current decisions in `DO_NOW` or `RESEARCH` may be exported. `PARKED` and `KILLED` fail closed.

```text
QuestionNode
    +
current InvestigationDecision
    ↓
explicit route
    ↓
question-research-handoff/v0.1
    ↓
versioned JSON artifact
    ↓
independent downstream validation
```

The handoff preserves the current question identity, decision identity, deterministic decision fingerprint, constraints and export timestamp.

It does **not** establish:

- a buyer or customer;
- actor authority or problem ownership;
- willingness to pay;
- contact permission;
- a job opening or employment interest;
- public-task availability;
- downstream evidence;
- live freshness after export.

### Territorial route

```text
Question Radar
    ↓
TERRITORIAL_RESEARCH
    ↓
Andes Context OS
    ↓
territorial evidence / missing context / conservative hypothesis
```

### Public contribution route

```text
Question Radar
    ↓
PUBLIC_CONTRIBUTION_RESEARCH
    ↓
Opportunity OS
    ↓
public contribution research preview
```

A downstream result of `NO_ACTIONABLE_CANDIDATE` is valid. The pipeline must not invent a problem owner, buyer, job opening or opportunity just to produce an exciting result.

See [`docs/cross-repo-handoff-v0.1.md`](docs/cross-repo-handoff-v0.1.md) and [`benchmarks/dogfood-cross-repo-handoff-2026-09-04.md`](benchmarks/dogfood-cross-repo-handoff-2026-09-04.md).

---

## Architecture

```text
raw question
    ↓
QuestionProfile (v0.2)
    ↓
optional LearningObservation (v0.3)
    ↓
QuestionNode + explicit QuestionRelation (v0.4)
    ↓
Context Pack

candidate question
    ↓
read-only corpus snapshot
    ↓
BM25 + frozen Jaccard evidence (v0.5-v0.7)
    ↓
ranked evidence OR explicit abstention
    ↓
human review

frozen benchmark + editorial gold
    ↓
Gold Evaluation Harness (v0.8)

stable QuestionNode
    ↓
InvestigationDecision (v0.9)
    ↓
DO_NOW / RESEARCH / PARKED / KILLED
    ↓
optional question-research-handoff/v0.1
```

Persistence remains intentionally small:

```text
evaluations
question_profiles_v02
learning_observations_v03
learning_observation_evidence_v03
question_nodes_v04
question_relations_v04
investigation_decisions_v09
```

Novelty, retrieval, benchmark and handoff artifacts do not add a second semantic database.

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

### Useful CLI paths

Profiles:

```bash
question-radar profile add examples/profile.example.json
question-radar profile list
```

Lineage and context:

```bash
question-radar lineage import corpus/question-lineage-v0.4.jsonl
question-radar lineage context chat-2026-08-29-012 --format markdown
```

Retrieval:

```bash
question-radar retrieval compare \
  "¿Qué pregunta anterior debería revisar antes de tratar esta como nueva?" \
  --limit 5 \
  --format markdown
```

Investigation decision:

```bash
question-radar decision show <question_id> --format markdown
question-radar decision history <question_id> --format json
question-radar decision active --format markdown
```

Research handoff:

```bash
question-radar --db data/questions.sqlite3 \
  decision handoff <question_id> \
  --route TERRITORIAL_RESEARCH \
  --out exports/handoff.json
```

The handoff command always reads the **current** decision for the selected question. A caller cannot select a stale historical decision for export.

---

## Benchmarks are evidence, not decoration

Question Radar keeps blind inputs, gold judgments and dogfood cases separate from production claims.

The repository includes:

- public calibration corpora for historical question profiles and lineage;
- blind retrieval benchmarks that preserve known lexical successes and failures;
- a frozen v0.8 Gold Evaluation Harness baseline;
- sanitized v0.9 decision dogfood;
- cross-repo handoff fixtures for San Juan water research and public GitHub contribution research;
- external question seeds such as the San Juan water-project and agent-network cases.

Gold judgments encode **editorial review expectations**, not semantic equivalence or ground truth. Dogfood can reveal that no feature or opportunity is justified.

That is a successful research outcome when the evidence supports it.

---

## Tests and verification

The repository is tested as a small software system rather than as a collection of prompt examples.

The handoff identity-hardening release reached **423 passing tests** on Python 3.11, and the subsequent docs-only San Juan water seed change kept `main` GitHub Actions green.

Coverage includes strict contracts, SQLite round trips, fail-closed read-only analysis, deterministic exports, historical compatibility, retrieval regressions, abstention, benchmark evaluation, append-only decision history, handoff routing/identity and sanitized dogfood.

Run locally:

```bash
pytest -q
python -m compileall -q src
```

GitHub Actions runs the same verification on pull requests and pushes to `main`.

---

## Data and privacy

Question Radar is local-first by design:

- SQLite databases are ignored by Git;
- questions become public only through explicit export/share actions;
- no complete chat history is ingested automatically;
- no API key or external account is required for the core runtime;
- no user identity model or learner ranking exists;
- novelty and retrieval use fail-closed read-only SQLite paths;
- handoff export writes only the explicit versioned artifact requested by the operator;
- Question Radar does not call Andes Context OS or Opportunity OS at runtime.

The public repository contains inspectable contracts, calibration data, benchmarks and sanitized fixtures — not a private conversation archive.

---

## What Question Radar is not

It is not:

- a student grading system;
- an intelligence, mastery, curiosity or creativity score;
- an LLM judge of people;
- an automatic semantic-equivalence oracle;
- an automatic master-question curator;
- an automatic prioritization engine;
- automatic chat surveillance;
- a problem detector that turns every question into a business opportunity;
- an orchestration service that silently moves work between repositories;
- a replacement for teachers, researchers, domain review or operator judgment.

It is a small experiment in treating **questions as durable inputs to learning, investigation and evidence-driven decisions**.

---

## Documentation

- [`ROADMAP.md`](ROADMAP.md) — product evolution, current state and near-term direction;
- [`docs/cross-repo-handoff-v0.1.md`](docs/cross-repo-handoff-v0.1.md) — exact handoff CLI and authority boundaries;
- [`docs/superpowers/specs/`](docs/superpowers/specs/) — approved design specifications;
- [`docs/superpowers/plans/`](docs/superpowers/plans/) — implementation plans;
- [`corpus/README.md`](corpus/README.md) — calibration and corpus conventions;
- [`benchmarks/`](benchmarks/) — blind tests, dogfood and research seeds.

## License

MIT License.
