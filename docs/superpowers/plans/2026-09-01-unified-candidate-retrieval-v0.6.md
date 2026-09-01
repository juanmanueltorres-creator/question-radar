# Unified Candidate Retrieval v0.6 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic, read-only candidate retrieval across v0.2 profiles and v0.4 lineage so earlier questions can be surfaced before a new candidate is treated as novel.

**Architecture:** `retrieval_storage.py` builds an immutable unified corpus snapshot from existing SQLite tables in `mode=ro`. `retrieval.py` implements BM25 plus the existing v0.5 weighted Jaccard evidence. `retrieval_export.py` renders deterministic Markdown/JSON. The existing v0.5 novelty path remains unchanged.

**Tech Stack:** Python 3.11+, SQLite, argparse, pytest, standard library only.

**Spec:** `docs/superpowers/specs/2026-09-01-unified-candidate-retrieval-v0.6-design.md`

## Global Constraints

- Preserve v0.1–v0.5 persisted contracts unchanged.
- Add no runtime dependency beyond the Python standard library.
- Retrieval evidence is not semantic truth.
- No automatic `QuestionRelation` creation or master promotion.
- Retrieval must never initialize, create, or migrate SQLite.
- v0.5 novelty behavior remains unchanged.
- Blind benchmark files are calibration inputs, never canonical lineage.
- Output ordering and serialization are deterministic.

---

### Task 1: Unified corpus model and read-only loader

**Files:**
- Create: `src/question_radar/retrieval.py`
- Create: `src/question_radar/retrieval_storage.py`
- Create: `tests/test_retrieval_storage.py`

**Interfaces:**
- Produces: `CorpusEntry`
- Produces: `load_retrieval_corpus(db_path: str | Path) -> tuple[CorpusEntry, ...]`

- [ ] **Step 1: Write failing model and loader tests**

```python
from pathlib import Path
import sqlite3
import pytest

from question_radar.retrieval import CorpusEntry
from question_radar.retrieval_storage import load_retrieval_corpus


def test_corpus_entry_rejects_unknown_source_version():
    with pytest.raises(ValueError, match="source_version"):
        CorpusEntry("q1", "¿Qué sabemos?", "v9", "profile", None)


def test_loader_reads_v02_only_database(tmp_path):
    db = tmp_path / "q.sqlite3"
    with sqlite3.connect(db) as connection:
        connection.execute(
            "CREATE TABLE question_profiles_v02 ("
            "id TEXT PRIMARY KEY, question TEXT NOT NULL, question_type TEXT NOT NULL, "
            "readiness TEXT NOT NULL, clarity INTEGER NOT NULL, boundedness INTEGER NOT NULL, "
            "investigability INTEGER NOT NULL, epistemic_openness INTEGER NOT NULL, "
            "purpose_fit INTEGER NOT NULL, formulation_score INTEGER NOT NULL, depth INTEGER NOT NULL, "
            "connections INTEGER NOT NULL, generativity INTEGER NOT NULL, strengths TEXT NOT NULL, "
            "gap TEXT NOT NULL, assumptions TEXT NOT NULL, evidence_required TEXT NOT NULL, "
            "next_question TEXT NOT NULL, topic TEXT, evaluator TEXT NOT NULL, rubric_version TEXT NOT NULL, "
            "created_at TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO question_profiles_v02 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("qv2", "¿Cuál es el costo de actuar y de no actuar?", "decision_risk", "ready_to_investigate", 5, 4, 5, 5, 5, 96, 5, 5, 5, "x", "x", "x", "x", "x", "decision", "tester", "v0.2", "2026-09-01T00:00:00-03:00"),
        )
    entries = load_retrieval_corpus(db)
    assert [(e.id, e.source_version, e.source_kind) for e in entries] == [("qv2", "v0.2", "profile")]


def test_loader_does_not_create_missing_database(tmp_path):
    db = tmp_path / "missing.sqlite3"
    with pytest.raises(ValueError, match="database does not exist"):
        load_retrieval_corpus(db)
    assert not db.exists()
```

Also add tests for v0.4-only, mixed v0.2+v0.4, no supported tables, and byte-for-byte non-mutation.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
pytest tests/test_retrieval_storage.py -q
```

Expected: import failure for `question_radar.retrieval` or `retrieval_storage`.

- [ ] **Step 3: Implement `CorpusEntry`**

```python
@dataclass(frozen=True, slots=True)
class CorpusEntry:
    id: str
    question: str
    source_version: str
    source_kind: str
    provenance: str | None
```

Validate non-empty `id` and `question`, `source_version in {"v0.2", "v0.4"}`, and exact source-kind pairing (`v0.2/profile`, `v0.4/lineage_node`). Trim string fields.

- [ ] **Step 4: Implement read-only loader**

Use `Path.resolve().as_uri() + "?mode=ro"`, inspect `sqlite_master`, read only available supported tables, fail only when neither exists, and sort by `(source_version, id)`.

- [ ] **Step 5: Run focused tests and verify GREEN**

```bash
pytest tests/test_retrieval_storage.py -q
```

Expected: all Task 1 tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/question_radar/retrieval.py src/question_radar/retrieval_storage.py tests/test_retrieval_storage.py
git commit -m "feat: add unified read-only retrieval corpus"
```

---

### Task 2: BM25 retrieval evidence and ranking

**Files:**
- Modify: `src/question_radar/retrieval.py`
- Create: `tests/test_retrieval.py`

**Interfaces:**
- Consumes: `CorpusEntry`
- Reuses: `question_radar.novelty.normalize_tokens`, `question_radar.novelty.compare_questions`
- Produces: `TokenContribution`, `RetrievalEvidence`, `RetrievalPack`
- Produces: `retrieve_candidates(candidate_question: str, corpus: tuple[CorpusEntry, ...], limit: int = 5) -> RetrievalPack`

- [ ] **Step 1: Write failing deterministic BM25 tests**

```python
from question_radar.retrieval import CorpusEntry, retrieve_candidates


def entry(i, q, version="v0.2", kind="profile"):
    return CorpusEntry(i, q, version, kind, None)


def test_rare_query_terms_raise_relevant_entry():
    corpus = (
        entry("a", "¿Cuál es el costo de actuar y de no actuar?"),
        entry("b", "¿Cómo evaluamos una decisión general?"),
        entry("c", "¿Cómo documentamos una organización?"),
    )
    pack = retrieve_candidates(
        "¿Qué pesa más: el costo de equivocarse o el costo de no actuar?",
        corpus,
        limit=3,
    )
    assert pack.results[0].entry.id == "a"
    assert pack.results[0].bm25_score > 0
    assert "costo" in pack.results[0].matched_query_tokens


def test_ranking_tie_breaks_by_jaccard_then_id():
    corpus = (
        entry("b", "¿Cómo cambia una decisión?"),
        entry("a", "¿Cómo cambia una decisión?"),
    )
    pack = retrieve_candidates("¿Cómo cambia una decisión?", corpus, limit=2)
    assert [r.entry.id for r in pack.results] == ["a", "b"]
```

Add tests for `limit < 1`, blank question, empty corpus, contribution ordering, residual query tokens, `retrieval_version == "v0.6"`, and `review_required is True`.

- [ ] **Step 2: Run focused tests and verify RED**

```bash
pytest tests/test_retrieval.py -q
```

Expected: missing retrieval structures/functions.

- [ ] **Step 3: Implement BM25 statistics**

Use exact constants:

```python
BM25_K1 = 1.5
BM25_B = 0.75
```

Compute normalized token tuples, document frequencies over token sets, average document length, raw BM25 contribution per query token, rounded public scores to 6 decimals, and deterministic evidence tuples.

- [ ] **Step 4: Reuse v0.5 Jaccard as secondary evidence**

For each `CorpusEntry`, call:

```python
compare_questions(candidate_question, entry.question, entry.id)
```

Store `.score` as `jaccard_score`. Do not change v0.5 code.

- [ ] **Step 5: Implement deterministic ranking**

Sort by:

```python
(-bm25_score, -jaccard_score, entry.id)
```

Return only `limit` results.

- [ ] **Step 6: Run focused tests and verify GREEN**

```bash
pytest tests/test_retrieval.py -q
```

- [ ] **Step 7: Commit**

```bash
git add src/question_radar/retrieval.py tests/test_retrieval.py
git commit -m "feat: add inspectable BM25 candidate retrieval"
```

---

### Task 3: Deterministic renderers and CLI

**Files:**
- Create: `src/question_radar/retrieval_export.py`
- Modify: `src/question_radar/cli.py`
- Create: `tests/test_retrieval_cli.py`

**Interfaces:**
- Produces: `render_retrieval_markdown(pack: RetrievalPack) -> str`
- Produces: `render_retrieval_json(pack: RetrievalPack) -> str`
- CLI: `question-radar retrieval compare QUESTION --limit N --format markdown|json`

- [ ] **Step 1: Write failing renderer tests**

Assert Markdown contains:

```text
# Unified Candidate Retrieval v0.6
## Candidate
## Retrieved Prior Questions
## Review Boundary
No semantic relation, lineage edge, or master promotion was created.
```

Assert JSON parses, contains `retrieval_version: "v0.6"`, `review_required: true`, source metadata, token contributions, deterministic ordering, and a trailing newline.

- [ ] **Step 2: Write failing CLI read-only tests**

Create a temporary mixed v0.2/v0.4 SQLite database, snapshot `read_bytes()`, invoke `cli.main(["--db", str(db), "retrieval", "compare", question, "--format", "json"])`, assert exit 0 and byte-for-byte DB equality.

Also assert a missing database fails without creating a file.

- [ ] **Step 3: Run tests and verify RED**

```bash
pytest tests/test_retrieval_cli.py -q
```

- [ ] **Step 4: Implement renderers**

Use pure functions, `ensure_ascii=False`, `indent=2`, `sort_keys=True`, deterministic lists, and exactly one trailing newline.

- [ ] **Step 5: Add CLI parser and handler**

Add `retrieval` namespace with required `compare` subcommand. Handler calls only `load_retrieval_corpus`, `retrieve_candidates`, and the selected renderer.

- [ ] **Step 6: Run tests and verify GREEN**

```bash
pytest tests/test_retrieval_cli.py -q
```

- [ ] **Step 7: Commit**

```bash
git add src/question_radar/retrieval_export.py src/question_radar/cli.py tests/test_retrieval_cli.py
git commit -m "feat: expose unified retrieval CLI"
```

---

### Task 4: Blind decision-under-uncertainty benchmark and golden regression

**Files:**
- Create: `corpus/blind-decision-uncertainty-2026-09-01.jsonl`
- Modify: `corpus/README.md`
- Create: `tests/test_retrieval_benchmarks.py`

**Interfaces:**
- Blind records accept exactly `id` and `question`.
- Regression consumes public retrieval functions and the public v0.2 calibration corpus.

- [ ] **Step 1: Add the frozen 25-question blind benchmark**

Use IDs `decision-blind-2026-09-01-001` through `decision-blind-2026-09-01-025`. Preserve every question exactly as returned in the blind chat.

- [ ] **Step 2: Write exact-preservation test**

Load the JSONL as UTF-8 JSON lines and assert 25 records, expected first/last IDs, and exact Q7 text:

```python
assert records[6]["question"] == (
    "¿Qué pesa más cuando el tiempo es limitado: la probabilidad de equivocarse "
    "o el costo de no actuar?"
)
```

- [ ] **Step 3: Write the golden Q7 regression**

Load the public `anti-ia-calibration-v0.2.jsonl` questions into `CorpusEntry` records, retrieve Q7 with `limit=5`, and assert:

```python
ids = [result.entry.id for result in pack.results]
assert "qv2-cal-013" in ids
```

Do not assert equivalence or a semantic relation.

- [ ] **Step 4: Run benchmark tests and verify RED/GREEN as appropriate**

```bash
pytest tests/test_retrieval_benchmarks.py -q
```

If Q7 misses top 5, treat that as a retrieval-algorithm defect: inspect token contributions and make only transparent, corpus-statistical adjustments consistent with the spec. Do not add hard-coded question IDs, synonyms, benchmark-specific boosts, or semantic labels.

- [ ] **Step 5: Document benchmark provenance**

Add a `corpus/README.md` section saying the 25 questions were generated in a separate blind chat after v0.5 was merged; they are calibration input and are not imported into canonical lineage.

- [ ] **Step 6: Commit**

```bash
git add corpus/blind-decision-uncertainty-2026-09-01.jsonl corpus/README.md tests/test_retrieval_benchmarks.py
git commit -m "data: add blind decision retrieval benchmark"
```

---

### Task 5: README, compatibility, full verification and PR

**Files:**
- Modify: `README.md`

**Interfaces:**
- Public contract describes v0.6 as candidate retrieval, not semantic novelty authority.

- [ ] **Step 1: Update README**

Set current version text to:

```text
Version: v0.6 · Unified Candidate Retrieval + v0.5 Corpus-Relative Novelty
```

Document v0.2+v0.4 corpus visibility, BM25 primary ranking, v0.5 Jaccard secondary evidence, CLI example, read-only guarantee, golden blind regression, and explicit exclusions (vault auto-read, embeddings, LLM runtime, semantic relation inference).

- [ ] **Step 2: Run focused v0.6 suite**

```bash
pytest tests/test_retrieval.py tests/test_retrieval_storage.py tests/test_retrieval_cli.py tests/test_retrieval_benchmarks.py -q
```

Expected: zero failures.

- [ ] **Step 3: Run full suite**

```bash
pytest -q
```

Expected: zero failures, including all historical v0.1–v0.5 tests.

- [ ] **Step 4: Compile source tree**

```bash
python -m compileall -q src
```

Expected: exit 0.

- [ ] **Step 5: Verify runtime dependencies remain empty**

```bash
python - <<'PY'
import tomllib
from pathlib import Path
project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]
assert project["dependencies"] == []
print("runtime dependencies: []")
PY
```

- [ ] **Step 6: Verify CLI help**

```bash
question-radar retrieval --help
question-radar retrieval compare --help
```

Expected: both exit 0.

- [ ] **Step 7: Review branch diff**

```bash
git diff --check main...HEAD
git diff --stat main...HEAD
git log --oneline main..HEAD
```

Expected: only v0.6 code, tests, docs, and blind benchmark changes.

- [ ] **Step 8: Open draft PR**

Title:

```text
feat: add unified candidate retrieval v0.6
```

PR body must include the Q7 false-negative motivation, corpus scope (v0.2 + v0.4), deterministic BM25 + Jaccard evidence, read-only boundary, benchmark result, full observed test count, and statement that no v0.1–v0.5 persisted contract changed.
