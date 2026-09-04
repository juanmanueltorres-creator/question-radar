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

The system is deliberately transparent. There is no external LLM deciding what somebody knows, no learner ranking, no hidden intelligence or mastery score, no automatic semantic relation written by v0.5, v0.6, or v0.7, and no automatic v0.9 prioritization decision.

---

## What this project demonstrates

- **Versioned data contracts** with backward compatibility across v0.1 through v0.9.
- **Strict runtime validation** for required fields, closed vocabularies, numeric ranges, booleans, timestamps, and malformed input.
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
- **Fail-closed SQLite reads** using `mode=ro`: analysis never creates a missing database or migrates a legacy one.
- **Provisional lexical clustering** that remains an analysis artifact rather than a persisted claim.
- **CLI isolation** through additive facades while historical commands remain delegated unchanged.
- **Gold evaluation** against frozen editorial expectations without treating sparse unjudged entries as implicit negatives.
- **Append-only investigation decisions** linked to existing v0.4 question identity.
- **Explicit supersession history** so changed judgment does not rewrite earlier context.
- **Advisory WIP visibility** when more than three investigations are marked `DO_NOW`, without automatic demotion or prioritization.
- **Fail-closed v0.4 prerequisite checks** so v0.9 never initializes historical lineage tables merely to satisfy itself.
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

BM25 is the primary statistical retrieval signal:

```text
k1 = 1.5
b = 0.75
idf(t) = ln(1 + (N - df(t) + 0.5) / (df(t) + 0.5))
```

For each retrieved question, v0.6 reports raw BM25, the frozen v0.5 weighted-Jaccard score, matched and residual query terms, per-token BM25 contributions, and source/provenance.

The central boundary is:

> **Retrieval means “review this prior question before calling the candidate new.” It does not mean “these questions are semantically equivalent.”**

The decision-under-uncertainty blind benchmark supplies the original golden regression. Blind Q7 asks:

> ¿Qué pesa más cuando el tiempo es limitado: la probabilidad de equivocarse o el costo de no actuar?

Against the public calibration corpus, retrieval must surface `qv2-cal-013` — `¿Cuál es el costo de actuar y de no actuar?` — within the top five without hard-coded IDs, synonym tables, embeddings, semantic boosts, or threshold relaxation.

---

## v0.7: Retrieval Calibration & Abstention

Blind Benchmark #4 showed that corpus visibility was no longer the main problem. BM25 could still promote low-information lexical collisions, simple Spanish plurals could hide useful prior questions, and a zero-overlap query could still receive arbitrary results.

v0.7 gives retrieval a normalization contract separate from v0.5 novelty. It filters additional low-information retrieval terms and applies only a narrow set of noun-focused plural transformations:

```text
decisiones → decision
errores     → error
sensores    → sensor
sistemas    → sistema
personas    → persona
costos      → costo
```

It is deliberately **not** a general Spanish stemmer. Regression tests preserve forms such as `entienden`, `modifica`, `pierde`, `puedes`, `tomas`, `usas`, and `trabajas` unchanged.

Each result now exposes:

- `matched_token_count`;
- `query_token_count`;
- `query_coverage`;
- BM25 score and per-token contributions;
- frozen v0.5 Jaccard evidence;
- residual query tokens;
- provenance.

Ranking rewards lexical coverage before BM25 rarity. If the entire corpus has zero matched retrieval tokens, v0.7 returns:

```text
abstained = true
abstention_reason = no_lexical_evidence
results = []
review_required = true
```

That abstention is not a claim of conceptual novelty. It means only that this lexical retrieval layer found no supported overlap.

Blind Benchmark #4 retains strong labels that fit this scope: Q1 must retrieve `vault-2026-08-31-001`, Q14 must retrieve `qv2-cal-013`, and the previous Blind #3 Q7 regression must remain green. Q16 and Q24 are preserved as diagnostic controls rather than overfit: Q16 gains weak `persona/personas` evidence, while Q24 still depends on the unimplemented verbal relation `entienden/entender`.

v0.7 still adds **no embeddings, vector search, synonym expansion, general verb stemming, LLM runtime inference, automatic relation creation, or master promotion**.

---

## v0.8: Gold Evaluation Harness

v0.8 adds a reproducible evaluation layer around the frozen v0.7 retrieval system without changing retrieval behavior, ranking, normalization, storage, or semantic interpretation.

Editorial judgments distinguish `relevant`, `partially_relevant`, and `not_relevant`. Sparse positive-only judgments must never be interpreted as exhaustive negatives, so Precision@k is withheld unless the selected relevance set is exhaustive.

The evaluator reports Hit Rate@k, Recall@k, MRR, false abstentions, abstention-control accuracy, and inspectable per-case retrieval evidence.

The boundary is explicit:

> **Gold judgments encode editorial review expectations, not semantic equivalence or lineage.**

---

## v0.9: Investigation Decision Gate

v0.9 adds a persistent, auditable layer for an operational question that earlier versions intentionally did not answer:

```text
interesting question
        ↓
should this consume attention now?
```

The operator records exactly one of:

```text
DO_NOW
RESEARCH
PARKED
KILLED
```

Each immutable decision stores rationale, explicit boolean gates (`goal_alignment`, `external_signal`, `testable_now`, `leverage`), qualitative `cost` and `confidence`, and state-specific next conditions.

`DO_NOW` and `RESEARCH` require an explicit `next_test`. `PARKED` requires an explicit `resume_when` condition.

Changed judgment is append-only: a new record supersedes the exact current leaf through `supersedes_decision_id`; historical rows are never rewritten.

> **Decision gates are operator judgments. Question Radar records and validates them; it does not decide automatically what deserves attention.**

`decision active` exposes current WIP and emits an advisory warning when `DO_NOW > 3`. It does not block the fourth decision, demote work, or choose what to park.

The core distinction is:

> **Preserving a question is not the same as committing attention to it.**

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
├── v0.6 Unified Candidate Retrieval
│   ├── CorpusEntry
│   ├── read-only v0.2 + v0.4 corpus snapshot
│   └── BM25 + frozen v0.5 evidence
│
├── v0.7 Retrieval Calibration & Abstention
│   ├── retrieval-specific normalization
│   ├── narrow noun-focused morphology
│   ├── TokenContribution
│   ├── RetrievalEvidence + coverage
│   ├── RetrievalPack + abstention
│   └── mandatory human review boundary
│
├── v0.8 Gold Evaluation Harness
│   └── frozen editorial retrieval expectations + deterministic metrics
│
└── v0.9 Investigation Decision Gate
    ├── immutable InvestigationDecision
    ├── append-only supersession chain
    ├── derived current projection
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

v0.5, v0.6, v0.7, and v0.8 add **no production SQLite tables**. Novelty, retrieval, and benchmark packs are derived analysis artifacts. v0.9 owns only `investigation_decisions_v09` and requires the canonical v0.4 question identity table to already exist.

---

## Tests & verification

The repository is tested as a small software system, not only as a collection of scoring examples.

**Latest verified implementation CI suite: 393 tests passing on Python 3.11.**

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
- fail-closed novelty reads;
- v0.6 unified read-only loading from v0.2-only, v0.4-only, and mixed databases;
- dependency-free BM25 ranking with inspectable token contributions;
- cross-version duplicate-ID isolation;
- CLI retrieval fail-closed and byte-for-byte database non-mutation;
- installed retrieval help execution;
- exact preservation of the Blind #3 and Blind #4 question sets;
- golden Q7 → `qv2-cal-013` retrieval;
- v0.7 retrieval-specific stopword and plural normalization;
- explicit guard against accidental conjugated-verb stemming;
- coverage-aware ranking;
- explicit zero-evidence abstention;
- Blind #4 Q1 and Q14 retrieval regressions;
- deterministic v0.7 Markdown/JSON coverage and abstention output;
- v0.8 frozen gold evaluation and sparse-judgment boundaries;
- immutable v0.9 decision validation and closed vocabularies;
- fail-closed v0.4 prerequisite checks for decision persistence;
- append-only, same-question, current-leaf-only supersession;
- deterministic decision/history/active rendering;
- advisory WIP warning with no automatic mutation;
- installed v0.9 CLI plus historical CLI namespace compatibility;
- sanitized three-case v0.9 dogfood;
- JSONL/CSV serialization where supported;
- compatibility between historical persistence and later derived/decision layers.

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

question-radar novelty batch corpus/blind-memory-2026-09-01.jsonl \
  --cluster-threshold 0.35 \
  --format markdown
```

The novelty commands only read existing v0.4 question nodes and relations through SQLite `mode=ro`. They do not insert, update, delete, initialize tables, create lineage, migrate legacy databases, or promote questions.

### v0.7 — calibrated unified candidate retrieval

```bash
question-radar retrieval compare \
  "¿Qué debería significar que un sistema funciona bien cuando los costos de equivocarse no son iguales?" \
  --limit 5 \
  --format markdown

question-radar --db /path/to/questions.sqlite3 retrieval compare \
  "¿Qué pregunta anterior debería revisar antes de tratar esta como nueva?" \
  --format json
```

Retrieval reads whichever supported corpus tables already exist (`question_profiles_v02`, `question_nodes_v04`) through SQLite `mode=ro`. It does not initialize missing tables, mutate the database, create semantic relations, or promote masters. v0.7 may explicitly abstain when no lexical evidence exists.

### v0.8 — gold evaluation

```bash
question-radar benchmark evaluate \
  --benchmark corpus/blind-representations-2026-09-01.jsonl \
  --gold corpus/gold/blind-representations-2026-09-01-gold-v1.jsonl \
  --k 5 \
  --format markdown
```

### v0.9 — investigation decisions

The decision namespace requires an existing v0.4 `QuestionNode`.

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

If judgment changes later, create a new decision with `--supersedes <current-decision-id>`. The prior row remains unchanged.

> Decision gates are operator judgments. Question Radar records and validates them; it does not decide automatically what deserves attention.

---

## Versioned contracts

### v0.1 — historical `QuestionEvaluation`

The original rubric remains frozen as a historical contract. It should not be silently retrofitted to match later versions.

### v0.2 — `QuestionProfile`

Each profile stores stable identity, original question, type/readiness, formulation dimensions, descriptive traits, assumptions, evidence requirements, a possible next question, optional topic, evaluator/rubric version, and timestamp.

### v0.3 — `LearningObservation`

Each observation stores concept, gap type, revisable state, confidence, ordered evidence question IDs, interpretation, suggested next step, and created/updated timestamps.

### v0.4 — question lineage

`QuestionNode` stores exactly `id`, `question`, `source`, `source_ref`, and `created_at`.

`QuestionRelation` stores exactly `id`, `source_question_id`, `target_question_id`, `relation_type`, and `created_at`.

The graph allows semantic cycles but rejects self-relations and exact duplicate edges. Historical questions enter lineage only through explicit import.

### v0.5 — derived novelty evidence

v0.5 adds no persisted domain table. Its main derived records are `SimilarityEvidence`, `NoveltyNeighbor`, `NoveltyPack`, `CandidateQuestion`, and `PossibleCluster`.

`NoveltyPack` always requires human review. Similarity scores are lexical evidence, not semantic-equivalence scores, and provisional interpretations are never written into v0.4 lineage automatically.

### v0.6 — unified retrieval corpus

v0.6 introduced `CorpusEntry` and unified read-only visibility across v0.2/v0.4. It adds no persisted table.

### v0.7 — calibrated retrieval evidence

v0.7 extends the derived retrieval contract with coverage and abstention. Its principal derived records remain:

- `CorpusEntry`
- `TokenContribution`
- `RetrievalEvidence`
- `RetrievalPack`

`RetrievalPack` always requires human review. BM25, coverage, and Jaccard are retrieval evidence, not probabilities or semantic-equivalence scores. An abstention is likewise a lexical-evidence statement, not proof of novelty.

### v0.8 — gold evaluation

v0.8 adds immutable editorial judgment/evaluation contracts around frozen retrieval inputs. Positive-only omissions remain unjudged, never implicit negatives.

### v0.9 — `InvestigationDecision`

Each v0.9 record stores immutable decision identity, existing v0.4 question identity, one closed decision state, rationale, four explicit operator gates, qualitative cost/confidence, state-specific next conditions, optional supersession, and a timezone-aware timestamp.

Current state is derived from the append-only chain rather than stored in a mutable projection table.

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
- `blind-system-trust-2026-09-01.jsonl` — external blind v0.7 retrieval calibration input, not canonical lineage
- `blind-representations-2026-09-01.jsonl` + `gold/blind-representations-2026-09-01-gold-v1.jsonl` — frozen v0.8 benchmark/gold input

The repository also keeps the software-domain blind experiment in `benchmarks/blind-test-2026-08-31-domain-software.md` and sanitized v0.9 dogfood in `benchmarks/dogfood-investigation-decision-gate-2026-09-04.md`.

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
- v0.5 novelty uses fail-closed read-only SQLite and creates no automatic semantic relations or promotions;
- v0.6/v0.7 retrieval uses fail-closed read-only SQLite across v0.2/v0.4 and creates no unified persistence table, semantic relation, or promotion;
- v0.8 evaluation creates no semantic relation or lineage write;
- v0.9 creates only `investigation_decisions_v09`, requires pre-existing v0.4 question identity, and never changes a decision automatically.

---

## Scope

Question Radar intentionally stays small.

Not included in v0.9: web frontend, Supabase, authentication, embeddings, vector databases, LangGraph, NetworkX, Neo4j, external LLM API calls, synonym expansion, general language stemming, automatic chat scraping, automatic relation inference, automatic master promotion, automatic vault/master-library ingestion, multi-user analytics, automatic prioritization, RICE/weighted priority scoring, agents, schedulers, automatic `PARKED` reactivation, background monitoring, or direct GeoPlatform / Opportunity OS / Andes Context OS runtime integration.

The current core model is: **questions → profiles → evidence → revisable learning observations → explicit lineage → deterministic context**, plus **read-only calibrated retrieval/evaluation layers and an explicit operator-controlled investigation decision layer**.

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

It is a small experiment in treating **questions themselves as durable learning and research artifacts**.

## License

MIT License.