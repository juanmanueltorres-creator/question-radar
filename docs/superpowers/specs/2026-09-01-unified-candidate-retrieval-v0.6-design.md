# Unified Candidate Retrieval v0.6 Design

## Status

Approved for implementation on 2026-09-01 after blind benchmark #3 exposed a corpus-visibility and retrieval-recall failure in v0.5.

## Problem

Question Radar v0.5 compares candidate questions only with persisted v0.4 `QuestionNode` records. Question Radar also contains earlier v0.2 `QuestionProfile` questions that may represent relevant prior work but are invisible to v0.5 retrieval.

Blind benchmark #3 demonstrated the failure concretely:

- candidate Q7: `¿Qué pesa más cuando el tiempo es limitado: la probabilidad de equivocarse o el costo de no actuar?`
- existing v0.2 question: `qv2-cal-013 — ¿Cuál es el costo de actuar y de no actuar?`
- v0.5 could not retrieve the existing question because it was not a v0.4 node; even direct lexical Jaccard is too weak to surface it reliably.

The system therefore needs a broader candidate-retrieval layer before any novelty judgment.

## Goal

Add a deterministic, read-only **Unified Candidate Retrieval** layer that searches questions from both v0.2 profiles and v0.4 lineage, returns inspectable retrieval evidence, and never decides semantic equivalence or writes lineage.

## Non-goals

v0.6 does **not**:

- infer semantic equivalence;
- create or modify `QuestionRelation` records;
- promote master questions;
- import blind benchmarks into the canonical corpus;
- read the external vault or master library automatically;
- use embeddings, vector databases, LLM runtime calls, synonym expansion, stemming, or external APIs;
- change v0.1–v0.5 stored contracts;
- add runtime dependencies beyond the Python standard library.

## Core contract

> Question Radar v0.6 retrieves prior questions that may deserve human comparison before a candidate is treated as new. Retrieval evidence is not a semantic relation.

Every retrieval result requires human review.

## Unified corpus model

Introduce a derived immutable record:

```python
@dataclass(frozen=True, slots=True)
class CorpusEntry:
    id: str
    question: str
    source_version: str
    source_kind: str
    provenance: str | None
```

Allowed values:

- `source_version`: `v0.2` or `v0.4`
- `source_kind`: `profile` or `lineage_node`

IDs retain their original IDs. No new persisted unified-corpus table is created.

## Read-only corpus loading

Create `retrieval_storage.py` with a dedicated SQLite read-only snapshot loader.

The loader:

1. requires the SQLite file to already exist;
2. opens it with SQLite URI `mode=ro`;
3. inspects `sqlite_master`;
4. reads `question_profiles_v02` when present;
5. reads `question_nodes_v04` when present;
6. never initializes, migrates, inserts, updates, or deletes anything;
7. fails closed if neither supported table exists;
8. does not require both tables to exist — a database containing only v0.2 or only v0.4 is still a valid retrieval corpus;
9. returns deterministic ordering by `(source_version, id)`.

For v0.2 records, provenance is the best already-stored source information available without changing the v0.2 contract. Since v0.2 does not store a source path, `provenance` may be `None`.

For v0.4 records, `source_ref` is used as provenance.

## Retrieval algorithm

v0.6 combines two deterministic lexical signals:

### 1. Existing v0.5 weighted Jaccard

Reuse the existing `compare_questions` evidence:

```text
token_jaccard = |A ∩ B| / |A ∪ B|
bigram_jaccard = |BA ∩ BB| / |BA ∪ BB|
jaccard_score = 0.7 * token_jaccard + 0.3 * bigram_jaccard
```

This remains visible in output for backward interpretability.

### 2. BM25-style corpus retrieval

Implement dependency-free Okapi BM25 over normalized tokens.

Constants are versioned in code:

```text
k1 = 1.5
b = 0.75
```

For each candidate query token `t`:

```text
idf(t) = ln(1 + (N - df(t) + 0.5) / (df(t) + 0.5))
```

Document contribution:

```text
idf(t) * (tf(t,d) * (k1 + 1)) /
         (tf(t,d) + k1 * (1 - b + b * |d| / avgdl))
```

The raw BM25 score is inspectable; it is not converted into a probability.

## Ranking

Each candidate entry yields:

```python
@dataclass(frozen=True, slots=True)
class RetrievalEvidence:
    entry: CorpusEntry
    bm25_score: float
    jaccard_score: float
    matched_query_tokens: tuple[str, ...]
    residual_query_tokens: tuple[str, ...]
    token_contributions: tuple[TokenContribution, ...]
```

Ranking is deterministic:

1. `bm25_score` descending;
2. `jaccard_score` descending;
3. `entry.id` ascending.

BM25 is the primary retrieval signal because it rewards rare informative terms without requiring a high global overlap ratio.

No threshold determines semantic labels in v0.6. The command returns the top N retrieval candidates and evidence only.

## Token contribution evidence

For every matched query token report:

```python
@dataclass(frozen=True, slots=True)
class TokenContribution:
    token: str
    document_frequency: int
    term_frequency: int
    contribution: float
```

Contributions are sorted by `(-contribution, token)`.

`residual_query_tokens` contains normalized query tokens not present in the retrieved entry.

## Retrieval pack

```python
@dataclass(frozen=True, slots=True)
class RetrievalPack:
    retrieval_version: str
    candidate_question: str
    corpus_size: int
    results: tuple[RetrievalEvidence, ...]
    review_required: bool
```

Contract:

- `retrieval_version == "v0.6"`
- `review_required is True`
- no persistence side effects.

## CLI

Add a new namespace rather than silently changing `novelty`:

```bash
question-radar retrieval compare \
  "¿Qué pesa más cuando el tiempo es limitado: la probabilidad de equivocarse o el costo de no actuar?" \
  --limit 5 \
  --format markdown
```

Supported formats:

- `markdown`
- `json`

Both outputs end with the explicit boundary:

```text
No semantic relation, lineage edge, or master promotion was created.
```

## Blind benchmark #3

Preserve the exact 25 raw questions from the decision-under-uncertainty blind chat as:

`corpus/blind-decision-uncertainty-2026-09-01.jsonl`

Records contain only:

```json
{"id":"decision-blind-2026-09-01-001","question":"..."}
```

The benchmark is calibration input, not canonical corpus and not imported into SQLite.

## Golden regression

The primary v0.6 regression is:

```text
Candidate:
Q7 ¿Qué pesa más cuando el tiempo es limitado: la probabilidad de equivocarse o el costo de no actuar?

Expected retrieval candidate:
qv2-cal-013 ¿Cuál es el costo de actuar y de no actuar?
```

Requirement:

- when the public v0.2 calibration corpus is loaded into the test database, `qv2-cal-013` must appear in the **top 5** retrieval results for Q7;
- the test does not assert equivalence, relation type, novelty, or promotion.

## Compatibility

- v0.5 `novelty compare` and `novelty batch` remain behaviorally unchanged;
- v0.6 creates no SQLite tables;
- v0.2 and v0.4 storage schemas remain unchanged;
- runtime dependencies remain `[]`;
- existing databases with only one supported retrieval table remain readable;
- missing databases are never created by retrieval.

## Error handling

- blank candidate question -> `ValueError("question must be a non-empty string")`;
- limit < 1 -> `ValueError("limit must be at least 1")`;
- missing database -> `ValueError("database does not exist: ...")`;
- no supported corpus tables -> `ValueError("no supported retrieval corpus tables found")`;
- SQLite read error -> `RuntimeError` with the database path;
- malformed blind candidate JSONL -> fail fast with line-aware `ValueError`.

## Testing strategy

Tests cover:

- deterministic `CorpusEntry` validation;
- read-only loading from v0.2 only, v0.4 only, and mixed databases;
- no database creation or migration;
- BM25 deterministic scoring and tie-breaking;
- token contribution evidence;
- v0.5 Jaccard evidence remains visible;
- deterministic Markdown/JSON rendering;
- CLI read-only behavior;
- golden Q7 -> `qv2-cal-013` top-5 regression;
- exact preservation of all 25 blind benchmark questions;
- full historical suite compatibility;
- `python -m compileall -q src`;
- zero runtime dependencies.
