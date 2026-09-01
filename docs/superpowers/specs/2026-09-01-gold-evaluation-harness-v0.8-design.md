# Gold Evaluation Harness v0.8 Design

## Purpose

Question Radar v0.8 adds a reproducible evaluation layer around the frozen v0.7 retrieval system. It does **not** change retrieval behavior, ranking, normalization, storage, or semantic interpretation.

The immediate research goal is to turn Blind Benchmark #5 into an auditable baseline before any semantic retrieval experiment is implemented.

## Epistemic boundary

A gold judgment records an editorial expectation about whether a prior question is useful to review for a frozen candidate. It does not assert semantic equivalence, lineage, or canonical duplication.

The harness must distinguish between:

- `relevant`: a prior question should clearly be reviewed before treating the candidate as new;
- `partially_relevant`: the prior question is useful context but does not represent the same research question;
- `not_relevant`: only allowed in exhaustive judgment sets.

Sparse positive judgments must **not** be interpreted as exhaustive negatives. Therefore Precision@k is unavailable unless a case explicitly declares exhaustive judgments.

## Frozen inputs

### Blind Benchmark #5

Store the 23 raw questions from the representations benchmark exactly as generated in:

`corpus/blind-representations-2026-09-01.jsonl`

Each row contains only:

- `id`
- `question`

The benchmark file is evaluation input and must never be loaded into the canonical retrieval corpus.

### Gold v1

Store editorial judgments in:

`corpus/gold/blind-representations-2026-09-01-gold-v1.jsonl`

Gold v1 covers eight preselected cases:

- Q1: positive-only; `qv2-cal-019` relevant, `vault-2026-08-31-008` partially relevant.
- Q10: positive-only; `qv2-cal-015` relevant.
- Q11: positive-only; `qv2-cal-020` relevant, `qv2-cal-021` relevant.
- Q12: positive-only; `qv2-cal-022` relevant.
- Q13: exhaustive abstention control; no relevant corpus entry identified.
- Q16: positive-only; `chat-2026-08-29-010` relevant.
- Q17: positive-only; `chat-2026-08-29-006` partially relevant.
- Q22: exhaustive abstention control; no relevant corpus entry identified.

These labels are frozen before any semantic candidate retrieval is implemented.

## Gold schema

Each JSONL row must contain:

```json
{
  "candidate_id": "representation-blind-2026-09-01-001",
  "judgment_scope": "positive_only",
  "expected_abstention": false,
  "judgments": [
    {
      "entry_id": "qv2-cal-019",
      "source_version": "v0.2",
      "relevance": "relevant"
    }
  ]
}
```

Allowed `judgment_scope` values:

- `positive_only`
- `exhaustive`

Allowed relevance values:

- `relevant`
- `partially_relevant`
- `not_relevant`

For `positive_only`, absence from `judgments` means **unjudged**, never `not_relevant`.

For exhaustive abstention controls:

- `judgment_scope = "exhaustive"`
- `expected_abstention = true`
- `judgments = []`

## Evaluation-only corpus loader

The harness needs a deterministic snapshot of the 51 canonical question-bearing entries used by v0.7 without creating or mutating SQLite.

Load evaluation entries read-only from these repository files:

- `corpus/anti-ia-calibration-v0.2.jsonl`
- `corpus/question-lineage-v0.4.jsonl`
- `corpus/chat-2026-08-31-software-recruiting-ai-lineage-v0.4.jsonl`

Mapping:

- each v0.2 row -> `CorpusEntry(source_version="v0.2", source_kind="profile", provenance=None)`;
- each v0.4 row with `record_type == "node"` -> `CorpusEntry(source_version="v0.4", source_kind="lineage_node", provenance=source_ref)`;
- v0.4 relation rows are ignored.

The loader is evaluation-only. Production `retrieval_storage.py` remains unchanged and read-only.

## Evaluation model

Add immutable types:

```python
GoldJudgment(entry_id, source_version, relevance)
GoldCase(candidate_id, question, judgment_scope, expected_abstention, judgments)
CaseEvaluation(candidate_id, retrieved_ids, abstained, relevant_found, reciprocal_rank, false_abstention)
BenchmarkEvaluation(... aggregate metrics ...)
```

`relevant` and `partially_relevant` both count as useful antecedents for retrieval recall. The raw relevance label remains visible in exported case details.

## Metrics

For a requested cutoff `k` (default 5), report:

### Hit Rate@k

Fraction of positive gold cases for which at least one useful antecedent is retrieved within top-k.

### Recall@k

Macro-average over positive gold cases:

`useful_gold_entries_found / useful_gold_entries`

### MRR

Mean reciprocal rank of the first useful antecedent across positive gold cases; zero when none is retrieved.

### Abstention controls

For exhaustive cases with `expected_abstention=true` report:

- control count;
- correct abstentions;
- false non-abstentions;
- abstention accuracy.

### False abstention

A positive gold case that returns `abstained=true` is a false abstention.

### Precision@k

Precision@k may only be computed for exhaustive relevance sets. It must be `null` with an explicit reason when the selected evaluation contains positive-only cases. The harness must never silently treat unjudged rows as negatives.

## Deterministic ranking and baseline

The evaluator calls the existing v0.7 `retrieve_candidates()` unchanged. It records retrieved composite references `(source_version, entry_id)` in their returned order.

Gold identity is composite `(source_version, entry_id)` because source-local IDs are not globally unique by contract.

A committed baseline report must record:

- retrieval version;
- benchmark name;
- gold version;
- corpus size;
- k;
- aggregate metrics;
- per-case retrieved references and judgment hits.

## CLI

Extend the current facade with:

```text
question-radar benchmark evaluate \
  --benchmark corpus/blind-representations-2026-09-01.jsonl \
  --gold corpus/gold/blind-representations-2026-09-01-gold-v1.jsonl \
  --k 5 \
  --format markdown|json
```

The evaluation corpus paths default to the three canonical repository JSONLs but may be overridden explicitly for tests.

No benchmark command writes to SQLite or modifies the corpus.

## Output boundary

Markdown and JSON must state:

> Gold judgments encode editorial review expectations, not semantic equivalence or lineage. Unjudged entries in positive-only cases are unknown, not negative.

## Non-goals

v0.8 must not add:

- embeddings;
- vector databases;
- LLM runtime calls;
- synonym expansion;
- general Spanish stemming;
- retrieval score changes;
- new SQLite tables;
- corpus writes;
- automatic lineage;
- automatic master promotion;
- automatic claims of novelty.

Runtime dependencies remain empty: `dependencies = []`.

## Acceptance criteria

1. Blind Benchmark #5 raw questions and Gold v1 are frozen in repository files.
2. Evaluation loader deterministically reconstructs 51 canonical entries from the three source JSONLs.
3. Sparse labels never become implicit negatives.
4. Evaluator reports Hit Rate@5, Recall@5, MRR, false abstentions, and abstention-control accuracy.
5. Precision@5 is withheld when relevance judgments are not exhaustive.
6. Per-case evidence remains inspectable.
7. CLI produces deterministic Markdown and JSON.
8. Existing retrieval behavior and v0.7 regression tests remain unchanged.
9. No runtime dependencies or write paths are added.
10. A frozen v0.7 baseline report is committed only after the implementation passes the full test suite.