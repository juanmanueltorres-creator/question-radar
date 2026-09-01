# Question Radar

> **Education records answers. Question Radar preserves the questions that make the next investigation possible.**

We routinely store grades, assignments, correct answers, mistakes, tickets, search results, and chat responses. We much less often preserve **how a question changes**: what it is trying to understand, what assumptions it carries, what evidence it needs, and what stronger question follows.

Question Radar is a small, local-first Python system for turning questions into structured, inspectable data — **without turning them into a score of the person asking them**.

**Version:** v0.6 · Unified Candidate Retrieval + v0.5 Corpus-Relative Novelty

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

The point is not to reward people for asking *more* questions. It is to make the **purpose, formulation, evidence needs, evolution, and corpus-relative position of questions visible**.

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
unified candidate retrieval (v0.2 + v0.4)
     ↓
BM25 evidence + v0.5 Jaccard evidence
     ↓
retrieved prior questions + residual terms
     ↓
human review
     ↓
optional v0.5 novelty review against lineage
     ↓
optional explicit v0.4 lineage decision
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

The system is deliberately transparent. There is no external LLM deciding what somebody knows, no learner ranking, no hidden intelligence or mastery score, and no automatic semantic relation written by v0.5 or v0.6.

---

## What this project demonstrates

- **Versioned data contracts** with backward compatibility across v0.1, v0.2, v0.3, v0.4, v0.5, and v0.6 derived outputs.
- **Strict runtime validation** for required fields, closed vocabularies, numeric ranges, timestamps, and malformed input.
- **Normalized SQLite storage** with separate tables for historical evaluations, typed profiles, learning observations, and question lineage.
- **Ordered evidence relationships** preserved across database and JSONL round trips.
- **Explicit directed question relations** with bounded, cycle-safe graph traversal.
- **Derived Context Packs** with deterministic Markdown and JSON output.
- **Read-only corpus-relative novelty packs** with inspectable lexical overlap and residual-token evidence.
- **Unified read-only retrieval** across v0.2 profiles and v0.4 lineage without creating a new persistence layer.
- **Dependency-free BM25 retrieval** with per-token contribution evidence and v0.5 Jaccard as a secondary signal.
- **Fail-closed SQLite reads** using `mode=ro`: analysis never creates a missing database or migrates a legacy one.
- **Provisional lexical clustering** that remains an analysis artifact rather than a persisted claim.
- **CLI isolation** through a v0.6 facade that handles retrieval while delegating historical commands unchanged.
- **Explicit import/export boundaries** so local data stays local unless it is intentionally exported.
- **Regression and end-to-end testing** across models, persistence, serialization, CLI behavior, blind calibration inputs, and historical compatibility.

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

## v0.4: Question Lineage and Context Pack

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

## v0.5: Corpus-Relative Novelty

v0.5 addresses a different failure mode: a question can be excellent and still be redundant relative to what a corpus already contains.

The layer compares a new candidate against stored v0.4 `QuestionNode` text using dependency-free, deterministic lexical evidence. It reports nearest questions, shared tokens and bigrams, residual candidate terms, lineage degree as context, and conservative review prompts.

The central boundary is:

> **Question Radar may surface evidence that two questions occupy similar or different lexical neighborhoods of the corpus. It does not decide that they mean the same thing.**

Similarity is intentionally transparent:

```text
token_jaccard = |A ∩ B| / |A ∪ B|
bigram_jaccard = |BA ∩ BB| / |BA ∪ BB|
score = 0.7 * token_jaccard + 0.3 * bigram_jaccard
```

Normalization removes accents and a small set of function words, but v0.5 performs **no stemming, synonym expansion, embeddings, vector search, or LLM inference**.

Every `NoveltyPack` has `review_required = true`. Possible labels such as `already_represented`, `refines_existing`, `operationalizes_existing`, `challenges_assumption`, and `possible_new_branch` are review prompts only. They do not create `QuestionRelation` records or promote questions into a master library.

Batch analysis can surface provisional **lexical** clusters, but a cluster is likewise not a semantic truth or a master branch. The blind organizational-memory benchmark is deliberately kept as a negative control: human review connects Q8/Q9/Q10/Q25 around obsolescence and adaptive forgetting, while the original strings do not share enough lexical evidence to form that cluster at the default threshold. v0.5 preserves that miss instead of hiding it behind uninspectable semantic inference.

The novelty CLI opens only an already-existing v0.4 lineage database in SQLite read-only mode. A missing database or a database without the v0.4 lineage tables fails closed; v0.5 never initializes or migrates SQLite while analyzing a candidate.

---

## v0.6: Unified Candidate Retrieval

v0.6 addresses the failure exposed by the third blind benchmark: Question Radar may already contain a relevant earlier question even when that question is not a v0.4 lineage node.

The retrieval corpus is derived at runtime from whichever supported tables already exist:

```text
question_profiles_v02 ──┐
                        ├──> CorpusEntry[] ──> BM25 retrieval
question_nodes_v04 ─────┘                     + v0.5 Jaccard evidence
```

No unified table is persisted. SQLite is opened through `mode=ro`, and a database containing only v0.2 or only v0.4 is valid. A missing database is not created.

BM25 is the primary ranking signal:

```text
k1 = 1.5
b = 0.75
idf(t) = ln(1 + (N - df(t) + 0.5) / (df(t) + 0.5))
```

For each retrieved question, v0.6 reports:

- raw BM25 score;
- the existing v0.5 weighted-Jaccard score;
- matched query tokens;
- residual query tokens;
- per-token term frequency, document frequency, and BM25 contribution;
- source version/kind and available provenance.

The central boundary is:

> **Retrieval means “review this prior question before calling the candidate new.” It does not mean “these questions are semantically equivalent.”**

The decision-under-uncertainty blind benchmark supplies the primary golden regression. Blind Q7 asks:

> ¿Qué pesa más cuando el tiempo es limitado: la probabilidad de equivocarse o el costo de no actuar?

Against the public v0.2 calibration corpus, v0.6 must retrieve `qv2-cal-013` — `¿Cuál es el costo de actuar y de no actuar?` — within the top five. The regression passes without hard-coded IDs, synonym tables, embeddings, semantic boosts, or threshold relaxation.

The installed CLI is routed through `cli_v06.py`. That facade handles only the new `retrieval` namespace and delegates every historical command unchanged to the original `cli.main` implementation.

v0.6 still performs **no stemming, synonym expansion, embeddings, vector search, LLM runtime inference, automatic relation creation, or master promotion**.

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
├── v0.4 Question Lineage
│   ├── QuestionNode
│   ├── QuestionRelation
│   ├── bounded graph traversal
│   └── derived Context Pack
│
├── v0.5 Corpus-Relative Novelty
│   ├── SimilarityEvidence
│   ├── NoveltyPack
│   ├── residual candidate tokens
│   ├── PossibleCluster
│   └── mandatory human review boundary
│
└── v0.6 Unified Candidate Retrieval
    ├── CorpusEntry
    ├── TokenContribution
    ├── RetrievalEvidence
    ├── RetrievalPack
    ├── read-only v0.2 + v0.4 corpus snapshot
    └── mandatory human review boundary
```

Persistence still includes only:

```text
evaluations
question_profiles_v02
learning_observations_v03
learning_observation_evidence_v03
question_nodes_v04
question_relations_v04
```

v0.5 and v0.6 add **no SQLite tables**. Novelty and retrieval packs are derived, read-only analysis artifacts. All versions can coexist without rewriting historical contracts.

---

## Tests & verification

The repository is tested as a small software system, not only as a collection of scoring examples.

**Latest verified CI suite: 299 tests passing on Python 3.11.**

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
- v0.5 accent-insensitive lexical normalization and weighted Jaccard similarity;
- deterministic nearest-question ranking and residual-token evidence;
- provisional cluster construction with deterministic connected components;
- strict candidate JSONL validation, including malformed-input rejection;
- deterministic v0.5 Markdown and JSON rendering;
- byte-for-byte SQLite non-mutation checks for existing v0.4 databases;
- fail-closed tests proving novelty analysis does not create a missing database or migrate a legacy database;
- challenge prompts requiring both explicit challenge syntax and corpus-neighbor evidence;
- blind benchmark regressions for software-domain convergence and organizational-memory lexical limits;
- v0.6 unified read-only loading from v0.2-only, v0.4-only, and mixed databases;
- dependency-free BM25 ranking with inspectable token contributions;
- deterministic v0.6 Markdown and JSON rendering;
- cross-version duplicate-ID isolation;
- CLI retrieval fail-closed and byte-for-byte database non-mutation;
- exact preservation of the 25-question decision-under-uncertainty blind benchmark;
- golden Q7 → `qv2-cal-013` top-five candidate retrieval;
- JSONL/CSV serialization where supported;
- CLI historical flows plus `novelty` and `retrieval` namespaces;
- compatibility between v0.1, v0.2, v0.3, v0.4, and derived v0.5/v0.6 analysis;
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

### v0.4 — Question Lineage

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

### v0.5 — corpus-relative novelty

```bash
question-radar novelty compare \
  "¿Qué debería recordar una organización y qué debería poder olvidar?" \
  --limit 5 \
  --format markdown

question-radar novelty compare \
  "¿Qué cambia cuando programar deja de ser el cuello de botella?" \
  --format json

question-radar novelty batch corpus/blind-memory-2026-09-01.jsonl \
  --cluster-threshold 0.35 \
  --format markdown
```

The novelty commands only read existing v0.4 question nodes and relations through SQLite `mode=ro`. They do not insert, update, delete, initialize tables, create lineage, migrate legacy databases, or promote questions.

### v0.6 — unified candidate retrieval

```bash
question-radar retrieval compare \
  "¿Qué pesa más cuando el tiempo es limitado: la probabilidad de equivocarse o el costo de no actuar?" \
  --limit 5 \
  --format markdown

question-radar --db /path/to/questions.sqlite3 retrieval compare \
  "¿Qué pregunta anterior debería revisar antes de tratar esta como nueva?" \
  --format json
```

Retrieval reads whichever supported corpus tables already exist (`question_profiles_v02`, `question_nodes_v04`) through SQLite `mode=ro`. It does not initialize missing tables, mutate the database, create semantic relations, or promote masters.

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

### v0.4 — question lineage

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

### v0.5 — derived novelty evidence

v0.5 does not add a persisted domain table. Its main derived records are:

- `SimilarityEvidence`
- `NoveltyNeighbor`
- `NoveltyPack`
- `CandidateQuestion`
- `PossibleCluster`

`NoveltyPack` always requires human review. Similarity scores are lexical retrieval evidence, not semantic-equivalence scores, and provisional interpretations are never written into v0.4 lineage automatically.

### v0.6 — derived unified retrieval evidence

v0.6 also adds no persisted domain table. Its main derived records are:

- `CorpusEntry`
- `TokenContribution`
- `RetrievalEvidence`
- `RetrievalPack`

`RetrievalPack` always requires human review. BM25 and Jaccard scores are retrieval evidence, not probabilities or semantic-equivalence scores. A retrieved question is a candidate to inspect, not an automatically inferred relation.

---

## Public calibration data

The repository includes intentionally public calibration corpora and blind inputs. They are small enough to inspect directly and versioned by contract or benchmark purpose.

Current datasets include:

- `anti-ia-seed-v0.1.jsonl`
- `anti-ia-calibration-v0.2.jsonl`
- `chat-2026-08-29.jsonl`
- `learning-frontier-chat-2026-08-29-v0.3.jsonl`
- `question-lineage-v0.4.jsonl`
- `chat-2026-08-31-software-recruiting-ai-lineage-v0.4.jsonl`
- `blind-memory-2026-09-01.jsonl` — external blind v0.5 calibration input, not canonical lineage
- `blind-decision-uncertainty-2026-09-01.jsonl` — external blind v0.6 retrieval calibration input, not canonical lineage

The repository also keeps the software-domain blind experiment in `benchmarks/blind-test-2026-08-31-domain-software.md`.

These artifacts are **calibration evidence, not truth labels and not scores of people**.

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
- v0.5 novelty commands use a fail-closed read-only SQLite path and create no automatic semantic relations or promotions;
- v0.6 retrieval uses a fail-closed read-only SQLite path across v0.2/v0.4 and creates no unified persistence table, semantic relation, or promotion.

---

## Scope

Question Radar intentionally stays small.

Not included in v0.6: web frontend, Supabase, authentication, embeddings, vector databases, LangGraph, NetworkX, Neo4j, external LLM API calls, automatic chat scraping, automatic relation inference, automatic master promotion, automatic vault/master-library ingestion, multi-user analytics, or direct GeoPlatform / Anti IA runtime integration.

The current core model is: **questions → profiles → evidence → revisable learning observations → explicit lineage → deterministic context**, plus **read-only unified retrieval and corpus-relative evidence layers that help a human inspect prior questions before changing the graph**.

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
- automatic chat surveillance;
- a replacement for teachers, tutors, researchers, or domain review.

It is a small experiment in treating **questions themselves as durable learning and research artifacts**.

## License

MIT License.