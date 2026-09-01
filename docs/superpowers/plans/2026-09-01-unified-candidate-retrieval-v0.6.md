# Unified Candidate Retrieval v0.6 Implementation Plan

> **For agentic workers:** this document records both the intended TDD sequence and implementation discoveries made while executing it.

**Goal:** Add deterministic, read-only candidate retrieval across v0.2 profiles and v0.4 lineage so earlier questions can be surfaced before a new candidate is treated as novel.

**Architecture:** `retrieval_storage.py` builds an immutable unified corpus snapshot from existing SQLite tables in `mode=ro`. `retrieval.py` implements BM25 plus existing v0.5 weighted-Jaccard evidence. `retrieval_export.py` renders deterministic Markdown/JSON. `cli_v06.py` is a narrow public facade: it handles only `retrieval` and delegates all historical commands unchanged to `cli.main`.

**Tech Stack:** Python 3.11+, SQLite, argparse, pytest, standard library only.

**Spec:** `docs/superpowers/specs/2026-09-01-unified-candidate-retrieval-v0.6-design.md`

## Global constraints

- Preserve v0.1–v0.5 persisted contracts unchanged.
- Add no runtime dependency beyond the Python standard library.
- Retrieval evidence is not semantic truth.
- No automatic `QuestionRelation` creation or master promotion.
- Retrieval must never initialize, create, or migrate SQLite.
- v0.5 novelty behavior remains unchanged.
- Blind benchmark files are calibration inputs, never canonical lineage.
- Output ordering and serialization are deterministic.
- A source-local question ID must not be treated as a globally unique document key across versions.

---

## Task 1 — Unified corpus model and read-only loader

**Files**

- `src/question_radar/retrieval.py`
- `src/question_radar/retrieval_storage.py`
- `tests/test_retrieval_storage.py`

### TDD sequence

- [x] Write model/loader tests before production code.
- [x] Verify RED in GitHub Actions: `ModuleNotFoundError: question_radar.retrieval`.
- [x] Implement immutable `CorpusEntry` with exact source pair validation:
  - `v0.2/profile`
  - `v0.4/lineage_node`
- [x] Implement SQLite `mode=ro` loader.
- [x] Support v0.2-only, v0.4-only, and mixed databases.
- [x] Fail closed when the DB is missing or contains neither supported table.
- [x] Prove byte-for-byte non-mutation.

The loader reads only the fields required for retrieval:

```text
question_profiles_v02 → id, question
question_nodes_v04    → id, question, source_ref
```

No unified table is persisted.

---

## Task 2 — BM25 retrieval evidence and ranking

**Files**

- `src/question_radar/retrieval.py`
- `tests/test_retrieval.py`

### Contract

```text
BM25_K1 = 1.5
BM25_B  = 0.75
```

For every candidate result expose:

- raw rounded BM25 score;
- v0.5 Jaccard score;
- matched query tokens;
- residual query tokens;
- per-token document frequency, term frequency, and contribution.

Ranking:

```text
BM25 desc
Jaccard desc
id asc
source_version asc
source_kind asc
```

### TDD sequence

- [x] Write rare-term, ranking, residual, contribution, blank-input, and limit tests.
- [x] Verify RED for missing retrieval structures/functions.
- [x] Implement dependency-free BM25.
- [x] Reuse v0.5 `compare_questions` only as secondary evidence.
- [x] Verify the historical + new suite remains GREEN.

### Review-discovered regression

Engineering review found that the first implementation indexed normalized document tokens as:

```python
{entry.id: tokens}
```

That silently collapses two documents when a v0.2 profile and v0.4 node share the same ID.

- [x] Add a failing cross-version duplicate-ID test first.
- [x] Observe RED: `1 failed, 298 passed`.
- [x] Replace ID-keyed token storage with a per-entry token tuple.
- [x] Verify GREEN: `299 passed` before the final installed-CLI verification was added.

No ranking weight or benchmark expectation was changed to fix this bug.

---

## Task 3 — Deterministic renderers and isolated public CLI

**Files**

- `src/question_radar/retrieval_export.py`
- `src/question_radar/cli_v06.py`
- `tests/test_retrieval_cli.py`
- `pyproject.toml`

### Renderer contract

Markdown includes:

```text
# Unified Candidate Retrieval v0.6
## Candidate
## Retrieved Prior Questions
## Review Boundary
```

Every output carries the boundary:

```text
No semantic relation, lineage edge, or master promotion was created.
```

JSON is deterministic with `ensure_ascii=False`, `indent=2`, `sort_keys=True`, and one trailing newline.

### CLI isolation

The original plan proposed editing the historical `cli.py`. During implementation review, the safer boundary was to leave that module untouched.

`pyproject.toml` routes the installed command to:

```text
question-radar = question_radar.cli_v06:main
```

`cli_v06.py`:

1. detects whether the top-level command is `retrieval`;
2. handles `retrieval compare` locally;
3. delegates every non-retrieval argv unchanged to `question_radar.cli.main`.

This reduces regression risk while keeping the public executable name stable.

### TDD / verification sequence

- [x] Write renderer + CLI tests before the facade exists.
- [x] Verify RED for missing `retrieval_export`.
- [x] Implement deterministic renderers.
- [x] Change test import to require `cli_v06` before creating it.
- [x] Verify RED for missing `cli_v06`.
- [x] Implement the facade and update the console-script entrypoint.
- [x] Verify mixed-corpus CLI retrieval and missing-DB fail-closed behavior.
- [x] Execute the installed `question-radar retrieval --help` and `question-radar retrieval compare --help` commands from pytest.

---

## Task 4 — Blind decision-under-uncertainty benchmark

**Files**

- `corpus/blind-decision-uncertainty-2026-09-01.jsonl`
- `corpus/README.md`
- `tests/test_retrieval_benchmarks.py`

### Frozen input

- [x] Preserve exactly 25 raw questions.
- [x] Use IDs `decision-blind-2026-09-01-001` through `025`.
- [x] Keep the benchmark outside canonical lineage/storage.

### Golden regression

Blind Q7:

```text
¿Qué pesa más cuando el tiempo es limitado: la probabilidad de equivocarse o el costo de no actuar?
```

Existing v0.2 candidate:

```text
qv2-cal-013
¿Cuál es el costo de actuar y de no actuar?
```

Requirement:

```python
assert "qv2-cal-013" in top_5_ids
```

- [x] Golden regression passes against the public v0.2 calibration corpus.
- [x] It passed with ordinary BM25; no hard-coded ID, synonym, semantic boost, or threshold relaxation was required.
- [x] The test asserts retrieval only, not equivalence or lineage type.

---

## Task 5 — Documentation, compatibility, verification, PR

**Files**

- `README.md`
- v0.6 spec/plan docs
- PR #12 metadata

### Documentation

- [x] Set README current version to `v0.6 · Unified Candidate Retrieval + v0.5 Corpus-Relative Novelty`.
- [x] Document v0.2 + v0.4 visibility.
- [x] Document BM25 primary / Jaccard secondary evidence.
- [x] Document `cli_v06.py` delegation boundary.
- [x] Document blind Q7 golden regression and calibration provenance.
- [x] Document exclusions: vault auto-read, embeddings, LLM runtime, automatic semantic relations.

### Verification completed before final diff review

- [x] `pytest -q` → **300 passed** on Python 3.11.
- [x] `python -m compileall -q src` → success.
- [x] installed `question-radar retrieval --help` → exit 0.
- [x] installed `question-radar retrieval compare --help` → exit 0.
- [x] `project.dependencies == []` remains true in `pyproject.toml`.
- [x] SQLite read-only/fail-closed tests pass for v0.6.
- [x] golden Q7 retrieval regression passes.

### PR

PR #12 remains draft for final human review. Its final body must state:

- blind #3 / Q7 motivation;
- v0.2 + v0.4 corpus scope;
- BM25 + Jaccard design;
- SQLite read-only/fail-closed boundary;
- no semantic authority or persistence side effects;
- golden Q7 result;
- final test count: **300**;
- no v0.1–v0.5 persisted contract changes.

Do not merge without a separate explicit user instruction.
