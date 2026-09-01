# Retrieval Calibration & Abstention v0.7 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Calibrate lexical retrieval so Spanish plural variants are recoverable, weak lexical collisions are deprioritized, and zero-evidence queries abstain explicitly.

**Architecture:** Keep v0.6 unified corpus loading intact. Add a dedicated dependency-free retrieval normalizer, extend retrieval evidence with coverage fields and abstention state, then update renderers/CLI documentation while preserving read-only behavior and human review.

**Tech Stack:** Python 3.11+, SQLite, stdlib only, pytest.

**Spec:** `docs/superpowers/specs/2026-09-01-retrieval-calibration-abstention-v0.7-design.md`

## Global Constraints

- No embeddings, vector search, LLM runtime inference, synonym expansion, or automatic semantic relations.
- No new SQLite tables or write path.
- SQLite retrieval remains `mode=ro`.
- Runtime dependencies remain empty.
- v0.5 novelty normalization remains unchanged.
- Blind benchmark files are calibration inputs only.
- Human review remains mandatory.

---

### Task 1: Retrieval-specific text normalization

**Files:**
- Create: `src/question_radar/retrieval_text.py`
- Create: `tests/test_retrieval_text.py`

**Interfaces:**
- Produces: `normalize_retrieval_tokens(text: str) -> tuple[str, ...]`

- [ ] **Step 1: Write failing normalization tests**

Test accent/lower handling, retrieval stopwords, blank-input rejection, and exact plural regressions:

```python
assert normalize_retrieval_tokens("costos sistemas personas errores decisiones sensores") == (
    "costo", "sistema", "persona", "error", "decision", "sensor"
)
assert "pero" not in normalize_retrieval_tokens("pero sistema")
```

Also prove `question_radar.novelty.normalize_tokens` has not changed.

- [ ] **Step 2: Run tests and confirm RED**

Run: `pytest tests/test_retrieval_text.py -q`
Expected: import/module failure because v0.7 normalizer does not exist.

- [ ] **Step 3: Implement minimal deterministic normalizer**

Use NFKD, accent stripping, retrieval-specific stopwords, token length guard, and only the approved plural rules.

- [ ] **Step 4: Run focused tests and confirm GREEN**

Run: `pytest tests/test_retrieval_text.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

`git commit -m "feat: add retrieval-specific text normalization"`

---

### Task 2: Coverage-aware ranking and abstention

**Files:**
- Modify: `src/question_radar/retrieval.py`
- Modify: `tests/test_retrieval.py`

**Interfaces:**
- Consumes: `normalize_retrieval_tokens`
- Extends: `RetrievalEvidence`, `RetrievalPack`

- [ ] **Step 1: Write failing tests**

Add tests asserting:

```python
result.matched_token_count == len(result.matched_query_tokens)
result.query_token_count > 0
0.0 <= result.query_coverage <= 1.0
```

Add ranking test where a two-token match outranks a one-token rare match.

Add abstention test:

```python
pack = retrieve_candidates("recomendacion automatica modifica evaluarla", corpus, limit=5)
assert pack.abstained is True
assert pack.abstention_reason == "no_lexical_evidence"
assert pack.results == ()
```

- [ ] **Step 2: Run focused tests and confirm RED**

Run: `pytest tests/test_retrieval.py -q`
Expected: missing fields/behavior.

- [ ] **Step 3: Implement minimal changes**

Use `normalize_retrieval_tokens` for query and document BM25 tokens. Compute coverage from unique query tokens. Sort by matched count, coverage, BM25, Jaccard, then stable keys. If all entries have zero lexical evidence, return an abstained pack with no results.

- [ ] **Step 4: Run focused tests and confirm GREEN**

Run: `pytest tests/test_retrieval.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

`git commit -m "feat: calibrate retrieval ranking and abstention"`

---

### Task 3: Freeze Blind Benchmark #4 and pre-registered regression labels

**Files:**
- Create: `corpus/blind-system-trust-2026-09-01.jsonl`
- Modify: `corpus/README.md`
- Modify: `tests/test_retrieval_benchmarks.py`

**Interfaces:**
- Uses the existing public v0.2/v0.4 calibration corpus fixtures.

- [ ] **Step 1: Write benchmark regressions before production calibration changes are accepted**

Freeze all 24 raw questions exactly. Add strong labels:

```text
Q1  -> vault-2026-08-31-001 top5
Q14 -> qv2-cal-013 top5
Q24 -> vault-2026-08-31-001 top5
Q16 -> abstain
Benchmark #3 Q7 -> qv2-cal-013 top5
```

- [ ] **Step 2: Run benchmark tests**

Run: `pytest tests/test_retrieval_benchmarks.py -q`
Expected before final calibration: at least Q14/Q24/Q16 fail under v0.6 behavior.

- [ ] **Step 3: Make only contract-approved calibration changes if needed**

Do not add IDs, synonyms, per-question boosts, or semantic rules.

- [ ] **Step 4: Re-run and confirm GREEN**

Run: `pytest tests/test_retrieval_benchmarks.py -q`
Expected: all pre-registered labels pass.

- [ ] **Step 5: Commit**

`git commit -m "test: freeze blind system trust retrieval benchmark"`

---

### Task 4: Deterministic renderer and CLI contract

**Files:**
- Modify: `src/question_radar/retrieval_export.py`
- Modify: `src/question_radar/cli_v06.py`
- Modify: `tests/test_retrieval_cli.py`
- Add/modify renderer tests as appropriate.

**Interfaces:**
- Renderer exposes `matched_token_count`, `query_token_count`, `query_coverage`, `abstained`, and `abstention_reason`.

- [ ] **Step 1: Write failing output tests**

Require deterministic Markdown/JSON output for both evidence and abstention cases. Markdown must explicitly say no lexical evidence was found when abstained.

- [ ] **Step 2: Run focused tests and confirm RED**

Run: `pytest tests/test_retrieval_cli.py -q`
Expected: missing v0.7 fields/output.

- [ ] **Step 3: Implement minimal renderer/CLI adaptation**

Keep the public namespace `question-radar retrieval compare`. Do not change historical command semantics.

- [ ] **Step 4: Run focused tests and confirm GREEN**

Run: `pytest tests/test_retrieval_cli.py -q`
Expected: pass.

- [ ] **Step 5: Commit**

`git commit -m "feat: expose retrieval coverage and abstention"`

---

### Task 5: Documentation and complete verification

**Files:**
- Modify: `README.md`
- Update this plan status after verification.

- [ ] **Step 1: Document v0.7 boundaries**

Describe retrieval-specific normalization, conservative morphology, coverage evidence, abstention, benchmark #4, and explicit non-goals.

- [ ] **Step 2: Run full verification**

Run:

```bash
pytest -q
python -m compileall -q src
```

Expected: zero failures and compile success.

- [ ] **Step 3: Verify dependency and persistence boundaries**

Confirm `pyproject.toml` still has `dependencies = []`; confirm no new SQLite table or mutation path; confirm v0.5 novelty tests remain unchanged/green.

- [ ] **Step 4: Review branch diff against main**

Confirm only v0.7 source/tests/docs/calibration data changed.

- [ ] **Step 5: Open PR without merging**

PR title: `feat: add retrieval calibration and abstention v0.7`.

PR body must include final test count, benchmark regressions, epistemic boundary, and exact head SHA.

---

## Self-review

- Spec coverage: all requirements map to Tasks 1–5.
- No semantic layer is introduced.
- Benchmark labels are pre-registered before accepting implementation behavior.
- v0.5 remains frozen.
- No placeholders or hidden persistence changes are permitted.
