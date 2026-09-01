# Gold Evaluation Harness v0.8 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic evaluation harness around frozen v0.7 retrieval so Blind Benchmark #5 can serve as an auditable pre-semantic baseline.

**Architecture:** Keep retrieval untouched. Add evaluation-only JSONL loaders, immutable gold/evaluation models, aggregate metrics, deterministic renderers, and a benchmark CLI facade. Canonical source JSONLs provide a read-only 51-entry evaluation corpus snapshot; sparse positive labels never imply negatives.

**Tech Stack:** Python 3.11 stdlib only, pytest for development, existing Question Radar v0.7 retrieval API.

**Spec:** `docs/superpowers/specs/2026-09-01-gold-evaluation-harness-v0.8-design.md`

## Global Constraints

- `dependencies = []` remains unchanged.
- Do not modify v0.7 retrieval ranking, normalization, abstention, or storage behavior.
- Do not add embeddings, vector DBs, LLM runtime calls, synonym expansion, or general stemming.
- Evaluation paths are read-only; no SQLite writes, corpus writes, lineage writes, or master promotion.
- Gold identity is `(source_version, entry_id)`.
- `positive_only` absence means unjudged, never negative.
- Precision@k must be withheld when the selected evaluation contains non-exhaustive relevance judgments.

---

### Task 1: Freeze Benchmark #5 and Gold v1

**Files:**
- Create: `corpus/blind-representations-2026-09-01.jsonl`
- Create: `corpus/gold/blind-representations-2026-09-01-gold-v1.jsonl`
- Modify: `corpus/README.md`
- Test: `tests/test_benchmark_gold.py`

**Interfaces:**
- Consumes: raw Blind Benchmark #5 questions from the approved chat output.
- Produces: deterministic benchmark IDs and Gold v1 rows consumed by later loaders.

- [ ] **Step 1: Write failing schema tests**

Test that the benchmark has exactly 23 unique IDs and the gold file has exactly eight unique candidate IDs with allowed scopes/relevance values. Assert Q13 and Q22 are exhaustive abstention controls and Q1/Q10/Q11/Q12/Q16/Q17 match the frozen judgments from the spec.

- [ ] **Step 2: Run RED**

Run: `pytest tests/test_benchmark_gold.py -q`
Expected: FAIL because benchmark/gold files do not exist.

- [ ] **Step 3: Add exact benchmark and gold JSONL files**

Use IDs `representation-blind-2026-09-01-001` through `...-023`. Preserve each question verbatim. Add the eight gold rows specified by the design.

- [ ] **Step 4: Run GREEN**

Run: `pytest tests/test_benchmark_gold.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "test: freeze representations benchmark gold v1"`

---

### Task 2: Add Evaluation-Only Loaders

**Files:**
- Create: `src/question_radar/benchmark_io.py`
- Test: `tests/test_benchmark_io.py`

**Interfaces:**
- Produces:
  - `load_benchmark(path: str | Path) -> tuple[BenchmarkQuestion, ...]`
  - `load_gold(path: str | Path, benchmark: tuple[BenchmarkQuestion, ...]) -> tuple[GoldCase, ...]`
  - `load_evaluation_corpus(paths: tuple[str | Path, ...]) -> tuple[CorpusEntry, ...]`
- Types:
  - `BenchmarkQuestion(id: str, question: str)`
  - `GoldJudgment(entry_id: str, source_version: str, relevance: str)`
  - `GoldCase(candidate_id: str, question: str, judgment_scope: str, expected_abstention: bool, judgments: tuple[GoldJudgment, ...])`

- [ ] **Step 1: Write failing loader tests**

Cover valid rows, malformed JSON, duplicate IDs, missing benchmark candidate, invalid source/relevance/scope, relation-row filtering, and deterministic 51-entry corpus reconstruction from the three canonical files.

- [ ] **Step 2: Run RED**

Run: `pytest tests/test_benchmark_io.py -q`
Expected: FAIL with missing module.

- [ ] **Step 3: Implement minimal stdlib JSONL loaders**

Use `json.loads` line-by-line, fail closed with `ValueError` for malformed content/contracts, and return immutable tuples. Map v0.2 profiles and v0.4 nodes exactly as specified; ignore v0.4 relation rows.

- [ ] **Step 4: Run GREEN**

Run: `pytest tests/test_benchmark_io.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat: add benchmark and gold loaders"`

---

### Task 3: Implement Evaluation Metrics

**Files:**
- Create: `src/question_radar/benchmark_eval.py`
- Test: `tests/test_benchmark_eval.py`

**Interfaces:**
- Consumes: `tuple[GoldCase, ...]`, `tuple[CorpusEntry, ...]`, cutoff `k`.
- Produces:
  - `CaseEvaluation`
  - `BenchmarkEvaluation`
  - `evaluate_benchmark(gold_cases, corpus, k=5) -> BenchmarkEvaluation`

- [ ] **Step 1: Write failing metric tests**

Use a small synthetic corpus to prove:
- a first-rank useful hit yields reciprocal rank 1.0;
- second-rank first hit yields 0.5;
- partially relevant counts as useful for recall;
- positive abstention increments false abstention;
- exhaustive abstention control is correct only when retrieval abstains;
- `precision_at_k is None` when any positive-only case is present;
- unjudged retrieved rows never count as negative in sparse cases.

- [ ] **Step 2: Run RED**

Run: `pytest tests/test_benchmark_eval.py -q`
Expected: FAIL with missing module.

- [ ] **Step 3: Implement evaluator without modifying retrieval**

Call existing `retrieve_candidates(question, corpus, limit=k)`. Match gold using `(source_version, entry_id)`. Aggregate macro Recall@k, Hit Rate@k, MRR, false abstentions, and exhaustive abstention controls. Preserve per-case returned ranks and raw relevance labels.

- [ ] **Step 4: Run GREEN**

Run: `pytest tests/test_benchmark_eval.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat: evaluate frozen retrieval benchmarks"`

---

### Task 4: Add Deterministic Benchmark Rendering

**Files:**
- Create: `src/question_radar/benchmark_export.py`
- Test: `tests/test_benchmark_export.py`

**Interfaces:**
- `render_benchmark_json(evaluation: BenchmarkEvaluation) -> str`
- `render_benchmark_markdown(evaluation: BenchmarkEvaluation) -> str`

- [ ] **Step 1: Write failing renderer tests**

Assert deterministic JSON (`ensure_ascii=False`, sorted keys, trailing newline), stable case ordering, explicit null/reason for unavailable Precision@k, metric values, retrieved composite references, and the exact editorial-boundary statement.

- [ ] **Step 2: Run RED**

Run: `pytest tests/test_benchmark_export.py -q`
Expected: FAIL with missing module.

- [ ] **Step 3: Implement renderers**

Markdown sections: Benchmark, Aggregate Metrics, Case Results, Evaluation Boundary. JSON must expose the same facts without hidden derived assumptions.

- [ ] **Step 4: Run GREEN**

Run: `pytest tests/test_benchmark_export.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat: render benchmark evaluation evidence"`

---

### Task 5: Add Benchmark CLI Without Breaking Legacy Commands

**Files:**
- Modify: `src/question_radar/cli_v06.py`
- Test: `tests/test_benchmark_cli.py`
- Test: existing `tests/test_retrieval_cli.py`

**Interfaces:**
- New command: `question-radar benchmark evaluate`.
- Existing `retrieval` and legacy commands remain delegated unchanged.

- [ ] **Step 1: Write failing CLI tests**

Cover benchmark JSON/Markdown output, `--k`, bad file error exit 2, root help containing benchmark + retrieval, and legacy/retrieval delegation regressions.

- [ ] **Step 2: Run RED**

Run: `pytest tests/test_benchmark_cli.py tests/test_retrieval_cli.py -q`
Expected: FAIL because benchmark command is absent.

- [ ] **Step 3: Extend facade minimally**

Recognize `benchmark` in `_top_level_command`, add parser and handler, default the three corpus source paths, load benchmark/gold/corpus through `benchmark_io`, evaluate, render, print, and preserve error handling.

- [ ] **Step 4: Run GREEN**

Run: `pytest tests/test_benchmark_cli.py tests/test_retrieval_cli.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat: expose benchmark evaluation CLI"`

---

### Task 6: Freeze v0.7 Baseline and Documentation

**Files:**
- Create: `corpus/baselines/blind-representations-2026-09-01-v0.7-baseline.json`
- Modify: `README.md`
- Modify: `corpus/README.md`
- Test: `tests/test_benchmark_baseline.py`

**Interfaces:**
- Baseline JSON is the deterministic JSON rendering of Gold v1 against the 51-entry canonical evaluation corpus at `k=5` using retrieval version v0.7.

- [ ] **Step 1: Write failing baseline regression**

Load the committed baseline JSON and compare it byte-for-byte to `render_benchmark_json(evaluate_benchmark(...))` generated from the frozen benchmark/gold/canonical corpus.

- [ ] **Step 2: Run RED**

Run: `pytest tests/test_benchmark_baseline.py -q`
Expected: FAIL because baseline file does not exist.

- [ ] **Step 3: Generate and commit the baseline output**

Use the completed CLI/evaluator at `k=5`. Do not hand-edit metric values. Document that this is the pre-semantic v0.7 baseline and that sparse labels make Precision@5 unavailable.

- [ ] **Step 4: Run full verification**

Run:
- `pytest -q`
- `python -m compileall -q src`

Expected: all tests pass; compileall exits 0.

- [ ] **Step 5: Review diff against main**

Verify no changes to `retrieval.py`, `retrieval_text.py`, `retrieval_storage.py`, dependencies, SQLite schemas, or write paths.

- [ ] **Step 6: Commit**

`git commit -m "docs: freeze v0.7 benchmark baseline"`

---

### Task 7: CI and Pull Request Gate

**Files:** none beyond PR metadata.

- [ ] **Step 1: Open a draft PR against `main`**

Title: `feat: add gold evaluation harness v0.8`.

- [ ] **Step 2: Require GitHub Actions RED/GREEN evidence during development**

CI must execute the full pytest suite and compile source tree.

- [ ] **Step 3: Run final CI on the exact final head**

Record head SHA, test count, Python version, and compile result in PR body.

- [ ] **Step 4: Stop before merge**

PR remains open/draft pending explicit human integration approval.