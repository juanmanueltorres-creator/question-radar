# Retrieval Calibration & Abstention v0.7 — Design

**Status:** approved in conversation on 2026-09-01; benchmark contract corrected before production implementation when plural normalization was found to create legitimate lexical evidence for Blind #4 Q16.

## Problem

v0.6 solved corpus visibility across v0.2 profiles and v0.4 lineage, but Blind Benchmark #4 exposed three retrieval-quality failures:

1. weak function-word matches can outrank more meaningful evidence;
2. simple Spanish morphology (`costos`/`costo`, `sistemas`/`sistema`) causes false negatives;
3. when every candidate has zero lexical evidence, retrieval still returns arbitrary top-N rows.

v0.7 must improve evidence quality without introducing semantic authority.

## Goals

- give retrieval its own normalization contract rather than reusing v0.5 novelty normalization;
- remove retrieval-specific low-information function words conservatively;
- normalize only high-confidence Spanish plural morphology;
- expose match count and query coverage as evidence;
- abstain when no lexical evidence exists;
- preserve BM25 and Jaccard as inspectable signals;
- preserve the v0.6 unified read-only corpus and persistence contract;
- keep human review mandatory.

## Non-goals

v0.7 does **not** add stemming of conjugated verbs, synonym expansion, embeddings, vector search, LLM runtime inference, semantic equivalence, automatic lineage creation, automatic master promotion, benchmark ingestion into canonical corpus, or a new SQLite table.

## Architecture

```text
raw candidate
    ↓
retrieval_text.normalize_retrieval_tokens
    ├─ accent/lower normalization
    ├─ retrieval-specific function-word filtering
    └─ conservative plural normalization
    ↓
unified v0.2 + v0.4 corpus
    ↓
BM25 + weighted Jaccard evidence
    ↓
matched_token_count + query_coverage
    ↓
┌───────────────────┬────────────────────┐
│ lexical evidence  │ no lexical evidence│
│ present           │                    │
▼                   ▼
ranked candidates   ABSTAIN
        ↓
    HUMAN REVIEW
```

## Retrieval-specific normalization

Create `src/question_radar/retrieval_text.py`.

Normalization remains deterministic and dependency-free:

1. Unicode NFKD;
2. lowercase;
3. strip combining marks;
4. keep alphanumeric and whitespace;
5. remove tokens shorter than 3 characters;
6. remove retrieval-specific function words;
7. apply conservative plural normalization.

The retrieval stopword set must include the existing v0.5 function words plus benchmark-exposed low-information Spanish terms such as `pero`, `tan`, `sus`, `sin`, `mas`, `sobre`, `principal`, `cuando`, and `quien`.

### Conservative plural morphology

Only high-confidence nominal/adjectival plural rules are permitted:

- vowel + `s` → remove final `s` when the stem remains at least 4 characters;
- consonant + `es` → remove final `es` when the stem remains at least 4 characters.

Examples required by regression:

```text
costos     → costo
sistemas   → sistema
personas   → persona
errores    → error
decisiones → decision
sensores   → sensor
```

Do not attempt conjugation normalization such as `entienden → entender` or `modifica → modificar`.

## Retrieval evidence contract

Extend `RetrievalEvidence` with:

- `matched_token_count: int`
- `query_token_count: int`
- `query_coverage: float`

`query_coverage = matched_token_count / max(1, query_token_count)` using unique normalized query tokens and rounded to 6 decimals.

Extend `RetrievalPack` with:

- `abstained: bool`
- `abstention_reason: str | None`

Closed v0.7 abstention reason vocabulary:

```text
no_lexical_evidence
```

If every corpus entry has `bm25_score == 0` and `matched_token_count == 0`, return:

```text
abstained = true
abstention_reason = "no_lexical_evidence"
results = ()
```

Otherwise `abstained = false` and `abstention_reason = null`.

A single genuine content-token match is weak evidence, not zero evidence. v0.7 exposes its low coverage rather than hiding it. This matters for Blind #4 Q16: plural normalization can legitimately connect `persona` with corpus `personas`, so Q16 is a diagnostic weak-evidence case and must not be forced to abstain.

## Ranking

Primary ordering should reward actual query coverage before statistical rarity:

1. descending `matched_token_count`;
2. descending `query_coverage`;
3. descending `bm25_score`;
4. descending `jaccard_score`;
5. ascending stable ID/source keys.

This is evidence ordering, not a probability of semantic relevance.

## Compatibility

- v0.5 novelty normalization remains unchanged.
- v0.6 corpus loading remains read-only with SQLite `mode=ro`.
- no new persisted table.
- runtime dependencies remain empty.
- existing CLI namespace remains `question-radar retrieval compare`.
- output explicitly states abstention when applicable.

## Blind Benchmark #4

Freeze the 24 questions in `corpus/blind-system-trust-2026-09-01.jsonl`. They remain external calibration input and are never imported into canonical lineage/profile tables.

Pre-registered strong labels for v0.7:

- Q1 must retrieve `vault-2026-08-31-001` within top 5;
- Q14 must retrieve `qv2-cal-013` within top 5;
- Q24 must retrieve `vault-2026-08-31-001` within top 5;
- Blind Benchmark #3 Q7 must continue retrieving `qv2-cal-013` within top 5.

Blind #4 Q16 is retained as a diagnostic weak-evidence control. It is not a golden abstention label because the approved morphology itself introduces a real `persona`/`personas` token match. Abstention behavior is instead validated independently with genuinely zero-overlap inputs.

These are retrieval expectations only; they do not assert semantic equivalence or lineage relations.

## Acceptance criteria

v0.7 is acceptable when:

1. all historical tests remain green;
2. retrieval-specific normalization is separately tested from novelty normalization;
3. Q14 and Q24 recover from plural mismatch without hard-coded benchmark IDs;
4. genuinely zero-evidence inputs return explicit abstention instead of arbitrary zero-score results;
5. Q1 and Benchmark #3 Q7 remain top-five retrieval hits;
6. Q16 remains inspectable as weak evidence rather than being forced into an unsupported abstention;
7. Markdown/JSON renderers expose coverage and abstention deterministically;
8. CLI remains fail-closed/read-only;
9. `dependencies = []` remains unchanged;
10. no semantic relation or promotion is created automatically.
