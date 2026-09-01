# Retrieval Calibration & Abstention v0.7 — Design

**Status:** approved in conversation on 2026-09-01 and calibrated during TDD against Blind Benchmark #4.

## Problem

v0.6 solved corpus visibility across v0.2 profiles and v0.4 lineage, but Blind Benchmark #4 exposed three retrieval-quality failures:

1. weak function-word matches can outrank more meaningful evidence;
2. simple Spanish morphology such as `costos/costo` and `sistemas/sistema` can cause false negatives;
3. when every candidate has zero lexical evidence, retrieval still returns arbitrary top-N rows.

v0.7 improves evidence quality without introducing semantic authority.

## Goals

- give retrieval its own normalization contract rather than reusing v0.5 novelty normalization;
- remove retrieval-specific low-information function words conservatively;
- normalize only a narrow set of high-confidence Spanish noun/adjective plurals;
- expose match count and query coverage as evidence;
- abstain when no lexical evidence exists;
- preserve BM25 and the frozen v0.5 Jaccard as inspectable signals;
- preserve the v0.6 unified read-only corpus and persistence contract;
- keep human review mandatory.

## Non-goals

v0.7 does **not** add general Spanish stemming, conjugated-verb normalization, synonym expansion, embeddings, vector search, LLM runtime inference, semantic equivalence, automatic lineage creation, automatic master promotion, benchmark ingestion into canonical corpus, or a new SQLite table.

## Architecture

```text
raw candidate
    ↓
retrieval_text.normalize_retrieval_tokens
    ├─ accent/lower normalization
    ├─ retrieval-specific function-word filtering
    └─ narrow noun-focused plural normalization
    ↓
unified v0.2 + v0.4 corpus
    ↓
BM25 + frozen v0.5 weighted-Jaccard evidence
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

`src/question_radar/retrieval_text.py` owns the v0.7 normalization contract. v0.5 `novelty.normalize_tokens()` remains unchanged.

Normalization is deterministic and dependency-free:

1. Unicode NFKD;
2. lowercase;
3. strip combining marks;
4. keep alphanumeric and whitespace;
5. remove tokens shorter than 3 characters;
6. remove retrieval-specific function words;
7. apply only the approved narrow plural rules below.

The retrieval stopword set contains the existing v0.5 function words plus benchmark-exposed low-information Spanish terms including `pero`, `tan`, `sus`, `sin`, `mas`, `sobre`, `principal`, `cuando`, and `quien`.

## Narrow plural morphology

An initial generic `vowel+s` / `consonant+es` design was rejected during self-review because it incorrectly stemmed conjugated verbs such as `puedes`, `tomas`, and `trabajas`. The final implementation deliberately uses a small set of suffixes that cover the observed noun/adjective cases without pretending to be a Spanish stemmer:

```text
-iones → remove final "es"   decisiones → decision
-ores  → remove final "es"   errores → error; sensores → sensor
-emas  → remove final "s"    sistemas → sistema
-onas  → remove final "s"    personas → persona
-os    → remove final "s"    costos → costo
         except tokens ending in -mos
```

Regression tests explicitly preserve these verb forms unchanged:

```text
entienden
modifica
pierde
puedes
tomas
usas
trabajas
```

In particular, v0.7 does **not** attempt `entienden → entender` or `modifica → modificar`.

## Retrieval evidence contract

`RetrievalEvidence` adds:

- `matched_token_count: int`
- `query_token_count: int`
- `query_coverage: float`

`query_coverage = matched_token_count / max(1, query_token_count)` using unique normalized query tokens, rounded to 6 decimals.

`RetrievalPack` adds:

- `abstained: bool`
- `abstention_reason: str | None`

The v0.7 abstention reason vocabulary currently contains:

```text
no_lexical_evidence
```

If every corpus entry has zero matched retrieval tokens, return:

```text
retrieval_version = "v0.7"
abstained = true
abstention_reason = "no_lexical_evidence"
results = ()
review_required = true
```

A single genuine content-token match is weak evidence, not zero evidence. v0.7 exposes the low coverage instead of hiding it.

## Ranking

Results with evidence are ordered by:

1. descending `matched_token_count`;
2. descending `query_coverage`;
3. descending `bm25_score`;
4. descending frozen v0.5 `jaccard_score`;
5. ascending stable ID/source keys.

This ordering is inspectable lexical evidence, not a probability of semantic relevance. `query_coverage` is intentionally surfaced even though, for one fixed query, it is monotonically related to matched-token count; it is useful to the human reviewer as an absolute evidence-strength signal.

## Compatibility and persistence

- v0.5 novelty normalization remains frozen and separately regression-tested.
- v0.6 unified corpus loading remains read-only through SQLite `mode=ro`.
- no new persisted table is added.
- runtime dependencies remain empty.
- the public CLI namespace remains `question-radar retrieval compare` through the existing facade.
- Markdown and JSON expose coverage and abstention explicitly.
- no semantic relation or promotion is written automatically.

## Blind Benchmark #4

`corpus/blind-system-trust-2026-09-01.jsonl` freezes the 24 blind questions exactly. It is external calibration input and is never imported into canonical lineage/profile tables.

### Strong retrieval labels retained

- Blind #4 Q1 must retrieve `vault-2026-08-31-001` within top 5.
- Blind #4 Q14 must retrieve `qv2-cal-013` within top 5.
- Blind #3 Q7 must continue retrieving `qv2-cal-013` within top 5.

These labels assert candidate retrieval only; they do not assert semantic equivalence or lineage relations.

### Diagnostic controls preserved instead of forcing success

**Q16** was initially proposed as an abstention gold. That expectation was withdrawn before production closure because the approved `personas → persona` normalization creates legitimate weak lexical evidence against the corpus. Forcing Q16 to abstain would contradict the normalization contract. True abstention is tested independently using a genuinely zero-overlap query.

**Q24** was initially proposed as a `vault-2026-08-31-001` top-five gold. CI showed that, after the approved noun morphology, Q24 still depends materially on the unimplemented relation `entienden ↔ entender`. Forcing the target into top five would require general verb stemming, semantic assistance, or an ad hoc boost. Q24 is therefore preserved as a negative control for a future retrieval layer rather than hidden behind scope creep.

## Acceptance criteria

v0.7 is acceptable when:

1. all historical tests remain green;
2. retrieval-specific normalization is separately tested from frozen v0.5 normalization;
3. the approved noun-focused morphology passes while conjugated verbs remain unchanged;
4. Blind #4 Q14 recovers `qv2-cal-013` without hard-coded IDs or synonyms;
5. Blind #4 Q1 and Blind #3 Q7 remain top-five hits;
6. genuinely zero-evidence inputs explicitly abstain with no arbitrary results;
7. Q16 remains visible as weak evidence rather than being forced into an unsupported abstention;
8. Q24 remains a documented lexical/semantic negative control rather than being overfit;
9. Markdown/JSON expose coverage and abstention deterministically;
10. CLI remains fail-closed and read-only;
11. `dependencies = []` remains unchanged;
12. no semantic relation or promotion is created automatically.
