# Corpus-Relative Novelty v0.5 — Implementation Plan

**Date:** 2026-09-01  
**Repository:** `juanmanueltorres-creator/question-radar`  
**Branch:** `feat/corpus-relative-novelty-v0.5`  
**PR:** #10  
**Status:** implemented and verified; awaiting merge decision

## Goal

Add a deterministic, read-only corpus-relative novelty layer that retrieves nearby existing questions, exposes lexical evidence and residual terms, and surfaces provisional clusters without creating semantic truth, lineage edges, or master promotions.

## Final architecture

v0.5 is a derived analysis layer beside the v0.4 Context Pack pipeline.

- `src/question_radar/novelty.py` owns normalization, lexical similarity, ranking, residual-token evidence, conservative review prompts, and provisional clustering.
- `src/question_radar/novelty_export.py` owns strict candidate JSONL loading and deterministic Markdown/JSON rendering.
- `src/question_radar/novelty_storage.py` owns the dedicated SQLite **read-only** snapshot loader.
- `src/question_radar/cli.py` exposes `novelty compare` and `novelty batch` and routes both through the read-only snapshot loader before invoking pure analysis functions.

The final implementation intentionally does **not** reuse `QuestionLineageStore.list_nodes()` / `list_relations()` for v0.5 reads. Those v0.4 methods call initialization code and can create missing lineage tables. v0.5 instead opens an already-existing database using SQLite URI `mode=ro` and fails closed when the database or v0.4 lineage tables do not exist.

## Tech stack

Python 3.11+ · standard library only · SQLite `mode=ro` · argparse CLI · pytest

No new runtime dependency is introduced.

## Global constraints

- [x] Preserve all v0.1, v0.2, v0.3, and v0.4 domain contracts unchanged.
- [x] Add no runtime dependencies beyond the Python standard library.
- [x] Treat novelty outputs as derived review evidence, never semantic truth.
- [x] Keep `novelty compare` and `novelty batch` read-only with respect to SQLite and canonical corpora.
- [x] Never create `QuestionRelation` records automatically.
- [x] Never promote candidates to master questions automatically.
- [x] Keep output ordering and serialization deterministic.
- [x] Require human review on every `NoveltyPack`.
- [x] Keep lexical false negatives observable rather than hiding them behind uninspectable semantic inference.

---

## Task 1 — Pure normalization and lexical similarity

**Files**

- `src/question_radar/novelty.py`
- `tests/test_novelty.py`

**Completed**

- [x] NFKD normalization and accent-insensitive tokenization.
- [x] Small checked-in Spanish/English function-word stoplist.
- [x] No stemming, synonym expansion, embeddings, vector search, or LLM inference.
- [x] Deterministic token and bigram Jaccard evidence.
- [x] Weighted score: `0.7 * token_jaccard + 0.3 * bigram_jaccard`.
- [x] Sorted inspectable evidence tuples.
- [x] Deterministic tie-break by `QuestionNode.id`.

## Task 2 — NoveltyPack, residual evidence, and review prompts

**Completed**

- [x] `SimilarityEvidence`.
- [x] `NoveltyNeighbor`.
- [x] `NoveltyPack`.
- [x] `candidate_distinctive_tokens` derived from the candidate minus the union of selected neighbor tokens.
- [x] Lineage degree exposed as context without affecting similarity score.
- [x] Conservative review prompts:
  - `already_represented`
  - `refines_existing`
  - `operationalizes_existing`
  - `challenges_assumption`
  - `possible_new_branch`
- [x] `review_required = true` on every pack.
- [x] `challenges_assumption` requires explicit challenge syntax and an existing corpus neighbor; it remains a review prompt only.

## Task 3 — Batch candidates and provisional lexical clustering

**Files**

- `src/question_radar/novelty.py`
- `src/question_radar/novelty_export.py`
- `tests/test_novelty_export.py`

**Completed**

- [x] Strict `{ "id": str, "question": str }` candidate contract.
- [x] Reject malformed JSON, unknown fields, duplicate IDs, blank IDs, and blank questions.
- [x] Pairwise lexical similarity for candidates.
- [x] Deterministic connected components above a configurable threshold.
- [x] No singleton clusters.
- [x] Cluster IDs and question IDs sorted deterministically.
- [x] Clusters remain derived analysis artifacts and are never written to lineage.

## Task 4 — Deterministic rendering and truly read-only CLI

**Files**

- `src/question_radar/novelty_export.py`
- `src/question_radar/novelty_storage.py`
- `src/question_radar/cli.py`
- `tests/test_novelty_cli.py`

**Completed**

- [x] `question-radar novelty compare QUESTION --limit N --format markdown|json`.
- [x] `question-radar novelty batch INPUT --limit N --cluster-threshold T --format markdown|json`.
- [x] Deterministic Markdown sections and JSON with sorted keys and trailing newline.
- [x] Review-boundary message: `No lineage relation or master promotion was created.`
- [x] Byte-for-byte database non-mutation tests on an existing v0.4 database.
- [x] Missing database fails closed and is not created.
- [x] Legacy database without v0.4 lineage tables fails closed and is not migrated.
- [x] Dedicated `novelty_storage.load_lineage_snapshot()` opens SQLite through `mode=ro`.

### Important correction discovered during review

The first implementation reused `QuestionLineageStore.list_nodes()` and `list_relations()`. That looked read-only at the call site, but those methods execute store initialization and therefore could create or migrate SQLite state. Two RED regressions exposed the problem. The final implementation does **not** use those methods for novelty analysis.

## Task 5 — Blind benchmark regression corpus

**Files**

- `corpus/blind-memory-2026-09-01.jsonl`
- `corpus/README.md`
- `tests/test_novelty_benchmarks.py`

**Completed**

- [x] Preserve the exact 25-question organizational-memory blind input as external calibration data.
- [x] Keep it outside canonical lineage and master-question promotion.
- [x] Regression coverage for software-domain convergence.
- [x] Regression coverage for organizational-memory residual evidence.
- [x] Preserve Q8/Q9/Q10/Q25 as a documented semantic family that lexical-only v0.5 does **not** fully recover.
- [x] Treat that miss as a negative control instead of rewriting the benchmark until it passes.

## Task 6 — Documentation, compatibility, and verification

**Completed**

- [x] README updated to v0.5.
- [x] Architecture and data boundaries documented.
- [x] Public calibration provenance documented.
- [x] v0.1–v0.4 historical contracts remain unchanged.
- [x] No v0.5 SQLite tables added.
- [x] CI remains Python 3.11 + `pytest -q` + `python -m compileall -q src`.

## TDD / review evidence

The implementation was developed with RED → GREEN cycles and additional review regressions:

1. **Initial RED:** `ModuleNotFoundError: question_radar.novelty` before runtime implementation.
2. **Normalization calibration:** one focused failure exposed an incorrect stopword assumption; fixture/runtime were aligned with the no-stemming design.
3. **Read-only review RED:** `275 passed / 2 failed`. The failures proved that v0.5 could indirectly create a missing database or add v0.4 lineage tables through store initialization.
4. **Read-only GREEN:** dedicated SQLite `mode=ro` loader introduced; regressions passed.
5. **Challenge-evidence RED:** `277 passed / 1 failed`. This proved `challenges_assumption` could appear with no corpus neighbor.
6. **Challenge-evidence GREEN:** prompt now requires explicit challenge syntax plus corpus-neighbor presence.
7. **Final verified suite:** **278 passed** on Python 3.11.
8. **Final compile check:** `python -m compileall -q src` succeeded.

## Acceptance criteria

v0.5 is acceptable when all of the following remain true:

- [x] Historical tests pass.
- [x] Normalization and similarity are deterministic.
- [x] Ranking is deterministic.
- [x] Markdown and JSON are deterministic.
- [x] Compare and batch are genuinely read-only.
- [x] Missing/legacy databases fail closed rather than being created or migrated.
- [x] No automatic lineage or promotion is created.
- [x] Blind benchmark regressions avoid semantic overclaiming.
- [x] The real blind-memory corpus remains unchanged as external calibration input.
- [x] README distinguishes lexical retrieval evidence from human semantic review.
- [x] CI is green on Python 3.11.

## Merge boundary

PR #10 contains the implementation and remains separate from `main` until an explicit merge decision. A merge must use the verified PR head and must not bypass failing checks if the head moves.
