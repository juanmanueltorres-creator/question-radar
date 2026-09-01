# Corpus-Relative Novelty v0.5 — Design Specification

Date: 2026-09-01
Status: approved in conversation
Repository: `juanmanueltorres-creator/question-radar`
Target branch: `feat/corpus-relative-novelty-v0.5`

## 1. Summary

Question Radar v0.5 adds a derived, evidence-first layer for comparing a new question against the existing question corpus without silently creating semantic truth, lineage edges, or master promotions.

The new layer answers a narrower question than an LLM: not “is this a good question?”, but “what evidence in the existing corpus suggests that this question is already represented, refines an existing branch, operationalizes one, challenges an assumption, or may open a new branch?”

v0.5 preserves the v0.4 rule that semantic relations remain explicit, revisable human judgments. The runtime may retrieve candidates and surface deterministic similarity evidence; it must not write `QuestionRelation` records, infer master status, or mutate canonical corpus state.

## 2. Motivation from blind benchmarks

Two blind benchmarks on 2026-08-31/2026-09-01 showed a repeated pattern:

- a general-purpose LLM can generate strong questions;
- some top-ranked questions are already represented by existing masters;
- non-top-ranked questions may have high structural value because they challenge an assumption;
- several questions may form a meaningful cluster that reveals a new branch;
- v0.4 can store explicit lineage after review, but does not surface corpus-relative novelty automatically.

The second benchmark exposed a cluster around organizational forgetting and obsolescence: several questions were individually related to memory, but together introduced a distinct mechanism — forgetting can sometimes be adaptive. This establishes a requirement for cluster-level evidence, not only pairwise matching.

## 3. Goals

v0.5 must:

1. accept one candidate question as raw text;
2. compare it deterministically against stored `QuestionNode` questions;
3. rank nearby corpus questions using dependency-free lexical evidence;
4. expose why each candidate ranked where it did;
5. expose terms/concepts present in the candidate but weakly represented in the nearest corpus questions;
6. surface nearby graph context when matching nodes already have v0.4 lineage;
7. support batch analysis so a set of candidate questions can be grouped into possible clusters;
8. label all semantic interpretations as proposals requiring review;
9. produce deterministic Markdown and JSON outputs;
10. remain read-only with respect to SQLite and canonical JSONL corpora;
11. preserve v0.1–v0.4 contracts and tests unchanged;
12. keep runtime dependencies limited to the Python standard library.

## 4. Non-goals

v0.5 will not add:

- embeddings;
- vector databases;
- external LLM or AI API calls;
- automatic semantic equivalence claims;
- automatic `QuestionRelation` creation;
- automatic master promotion;
- automatic corpus mutation;
- hidden thresholds that assert “duplicate” as fact;
- learner/person scoring;
- internet retrieval;
- language-model-based paraphrase generation.

## 5. Core principle

> Question Radar may surface evidence that two questions occupy similar or different parts of the corpus. It does not decide that they mean the same thing.

The v0.5 output is therefore a `NoveltyPack`, not a persisted judgment.

## 6. Data contracts

### 6.1 `SimilarityEvidence`

Derived immutable record:

```text
question_id
score
shared_tokens
shared_bigrams
candidate_only_tokens
corpus_only_tokens
```

Rules:

- `score` is a deterministic float in `[0.0, 1.0]`;
- token lists are normalized, deduplicated and sorted;
- evidence must be inspectable from the two original strings;
- no semantic label is stored in this structure.

### 6.2 `NoveltyNeighbor`

```text
node
similarity
lineage_degree
```

`lineage_degree` is the count of explicit v0.4 relations touching the node. It is contextual evidence only and must not alter the lexical similarity score.

### 6.3 `NoveltyPack`

```text
novelty_version
candidate_question
neighbors
candidate_distinctive_tokens
possible_interpretations
review_required
```

`possible_interpretations` is a tuple drawn from:

```text
already_represented
refines_existing
operationalizes_existing
challenges_assumption
possible_new_branch
```

Important: these are **review prompts**, not assertions. The deterministic runtime may include an interpretation only when a transparent heuristic fires and must expose the supporting evidence. The output must always contain `review_required = true`.

## 7. Text normalization

The comparison layer must be dependency-free and deterministic.

Normalization pipeline:

1. Unicode normalize with `unicodedata.normalize("NFKD", text)`;
2. lowercase;
3. remove combining marks so accents do not split equivalent Spanish words;
4. retain alphanumeric characters and whitespace;
5. split on whitespace;
6. drop a small checked-in Spanish/English stopword set focused on function words only;
7. drop tokens shorter than 3 characters;
8. preserve all remaining tokens exactly; no stemming and no synonym expansion.

No domain dictionaries are introduced in v0.5. That avoids silently encoding semantic authority into a hand-maintained ontology.

## 8. Similarity algorithm

Use weighted lexical overlap:

```text
token_jaccard = |A ∩ B| / |A ∪ B|
bigram_jaccard = |BA ∩ BB| / |BA ∪ BB|
score = round(0.7 * token_jaccard + 0.3 * bigram_jaccard, 6)
```

If both token sets are empty, score is `0.0`.

If normalized token sequences are identical, score is `1.0`.

Ranking order:

1. descending score;
2. ascending `QuestionNode.id` for deterministic ties.

The algorithm deliberately favors transparency over semantic recall. v0.5 is a candidate-retrieval layer, not a complete semantic search engine.

## 9. Distinctive-token evidence

For the top `k` neighbors, compute:

```text
candidate_distinctive_tokens = candidate_tokens - union(neighbor_tokens)
```

This is important because novelty can live in the residual. A question may strongly overlap with an existing branch while introducing a new mechanism such as `olvido`, `obsolescencia`, or `vigencia`.

The output must show these tokens explicitly rather than converting them into an opaque novelty score.

## 10. Interpretation heuristics

Heuristics are intentionally conservative and framed as possible interpretations.

Given highest similarity `s1` and candidate distinctive-token ratio `d`:

- `already_represented` may be proposed when `s1 >= 0.75` and `d <= 0.20`;
- `refines_existing` may be proposed when `0.45 <= s1 < 0.75` and candidate token count is greater than the top neighbor token count;
- `operationalizes_existing` may be proposed when `0.35 <= s1 < 0.75` and the candidate contains at least one concrete operational marker from a tiny closed set (`como`, `cuando`, `cuanto`, `quien`, `donde`) after raw-text inspection;
- `possible_new_branch` may be proposed when `s1 < 0.45` or `d >= 0.40`;
- `challenges_assumption` is **never inferred from lexical similarity alone** in v0.5. It may only appear in batch review when a candidate contains explicit challenge syntax (`y si`, `que pasa si`, `podria ser que`) and nearest-neighbor evidence is included. Even then it remains a review prompt.

These thresholds are calibration defaults and are versioned behavior. Tests must lock them down.

## 11. Batch clustering

For a batch of candidate questions:

1. normalize every candidate;
2. compute pairwise lexical scores;
3. create an undirected provisional edge when score `>= 0.35`;
4. connected components with at least two questions become `PossibleCluster` records;
5. cluster ordering is deterministic by the lexicographically smallest candidate ID;
6. a cluster is an analysis artifact only and is never written to lineage.

`PossibleCluster` contains:

```text
cluster_id
question_ids
shared_tokens
```

The cluster mechanism is designed to surface patterns like Q8/Q9/Q10/Q25 in the organizational-memory benchmark without calling the cluster a new master.

## 12. CLI

Add namespace:

```bash
question-radar novelty compare "QUESTION" --limit 5 --format markdown
question-radar novelty compare "QUESTION" --limit 5 --format json
question-radar novelty batch INPUT.jsonl --format markdown
question-radar novelty batch INPUT.jsonl --format json
```

`compare` reads the existing v0.4 question-node store from `--db` and performs no writes.

`batch` input JSONL uses:

```json
{"id":"candidate-001","question":"..."}
```

Unknown fields, duplicate IDs, malformed JSON, empty IDs and empty questions are rejected.

## 13. Rendering

Markdown must contain:

```text
# Question Radar Novelty Pack
## CANDIDATE QUESTION
## NEAREST CORPUS QUESTIONS
## DISTINCTIVE TOKENS
## POSSIBLE INTERPRETATIONS
## REVIEW BOUNDARY
```

The review boundary text must state that no lineage or promotion was created.

JSON output must be sorted-key deterministic and end with a newline, matching existing project conventions.

## 14. Persistence and safety boundary

v0.5 introduces no new SQLite tables.

`novelty compare` and `novelty batch` are read-only. Tests must snapshot database contents before and after analysis and verify no mutation.

No existing `QuestionNode`, `QuestionProfile`, `LearningObservation`, `QuestionRelation`, Context Pack, rubric or corpus contract changes.

## 15. Files

Create:

- `src/question_radar/novelty.py`
- `src/question_radar/novelty_export.py`
- `tests/test_novelty.py`
- `tests/test_novelty_export.py`
- `tests/test_novelty_cli.py`
- `tests/test_novelty_benchmarks.py`
- `corpus/blind-memory-2026-09-01.jsonl`

Modify:

- `src/question_radar/cli.py`
- `README.md`
- `corpus/README.md`

No v0.1–v0.4 files are rewritten for the feature.

## 16. Benchmark regressions

The existing software-domain blind benchmark and the new organizational-memory blind benchmark become calibration evidence.

Required regression expectations are intentionally modest because v0.5 is lexical:

- exact/near-exact restatements rank their known corpus neighbor highly;
- the runtime exposes distinctive residual terms instead of falsely asserting equivalence;
- the memory benchmark batch produces at least one multi-question possible cluster around forgetting/obsolescence terms;
- no benchmark assertion may require the runtime to infer a human-reviewed semantic relation that lexical evidence cannot justify.

## 17. Acceptance criteria

v0.5 is acceptable when:

1. all historical tests still pass;
2. new normalization/similarity tests pass;
3. ranking is deterministic;
4. Markdown and JSON are deterministic;
5. compare and batch commands are read-only;
6. no automatic lineage is created;
7. benchmark regression tests pass without overstating semantic authority;
8. README clearly distinguishes v0.5 retrieval evidence from human semantic review;
9. CI is green on Python 3.11.
