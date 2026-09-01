# Corpus-Relative Novelty v0.5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic, read-only corpus-relative novelty layer that retrieves nearby existing questions, exposes lexical evidence and residual terms, and surfaces provisional clusters without creating lineage or promotion decisions.

**Architecture:** v0.5 is a derived analysis layer beside v0.4 Context Packs. `novelty.py` owns normalization, similarity, candidate ranking, interpretation prompts and batch clustering; `novelty_export.py` owns JSONL loading plus deterministic Markdown/JSON rendering. The CLI reads existing `QuestionNode` records and invokes these pure functions without writing to SQLite.

**Tech Stack:** Python 3.11+, standard library only, SQLite through existing stores, argparse CLI, pytest.

**Spec:** `docs/superpowers/specs/2026-09-01-corpus-relative-novelty-v0.5-design.md`

## Global Constraints

- Preserve all v0.1, v0.2, v0.3 and v0.4 domain contracts unchanged.
- Add no runtime dependencies beyond the Python standard library.
- Novelty outputs are derived review evidence, never semantic truth.
- `novelty compare` and `novelty batch` must not mutate SQLite or canonical corpora.
- No automatic `QuestionRelation` creation or master promotion.
- Output ordering and serialization must be deterministic.
- `challenges_assumption` may only be surfaced as a review prompt under explicit challenge syntax; it is never stored automatically.

---

### Task 1: Pure normalization and lexical similarity

**Files:**
- Create: `src/question_radar/novelty.py`
- Create: `tests/test_novelty.py`

**Interfaces:**
- Produces: `normalize_tokens(text: str) -> tuple[str, ...]`
- Produces: `token_bigrams(tokens: tuple[str, ...]) -> tuple[str, ...]`
- Produces: `SimilarityEvidence`
- Produces: `compare_questions(candidate: str, corpus_question: str, question_id: str) -> SimilarityEvidence`

- [ ] **Step 1: Write failing normalization tests**

```python
from question_radar.novelty import normalize_tokens


def test_normalize_tokens_is_accent_insensitive_and_deterministic():
    assert normalize_tokens("¿Qué información está ACÁ?") == ("informacion", "esta", "aca")


def test_normalize_tokens_drops_short_function_words():
    assert normalize_tokens("¿Y si la IA lo hace?") == ("hace",)
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
pytest tests/test_novelty.py -q
```

Expected: import failure because `question_radar.novelty` does not exist.

- [ ] **Step 3: Implement normalization minimally**

Create `src/question_radar/novelty.py` with a small frozen stopword set, NFKD normalization, combining-mark removal, alphanumeric filtering, whitespace splitting, stopword removal and minimum token length 3.

Public signature:

```python
def normalize_tokens(text: str) -> tuple[str, ...]:
    ...
```

Reject non-string or blank candidate input with `ValueError("question must be a non-empty string")`.

- [ ] **Step 4: Add failing similarity tests**

```python
from question_radar.novelty import compare_questions


def test_identical_normalized_questions_score_one():
    evidence = compare_questions(
        "¿Cómo usamos memoria y trazabilidad?",
        "Como usamos memoria y trazabilidad",
        "q-1",
    )
    assert evidence.score == 1.0
    assert evidence.question_id == "q-1"


def test_unrelated_questions_have_low_similarity():
    evidence = compare_questions(
        "¿Qué debería recordar una organización?",
        "¿Cómo reconstruimos rocas antiguas?",
        "q-2",
    )
    assert evidence.score < 0.25
```

- [ ] **Step 5: Run the tests and verify RED for missing comparison**

```bash
pytest tests/test_novelty.py -q
```

Expected: normalization tests pass; similarity tests fail because comparison structures/functions are missing.

- [ ] **Step 6: Implement `SimilarityEvidence` and weighted Jaccard**

Use:

```python
@dataclass(frozen=True, slots=True)
class SimilarityEvidence:
    question_id: str
    score: float
    shared_tokens: tuple[str, ...]
    shared_bigrams: tuple[str, ...]
    candidate_only_tokens: tuple[str, ...]
    corpus_only_tokens: tuple[str, ...]
```

Score formula:

```python
score = round(0.7 * token_jaccard + 0.3 * bigram_jaccard, 6)
```

All evidence tuples must be sorted deterministically.

- [ ] **Step 7: Run focused tests and verify GREEN**

```bash
pytest tests/test_novelty.py -q
```

Expected: all Task 1 tests pass.

- [ ] **Step 8: Commit Task 1**

```bash
git add src/question_radar/novelty.py tests/test_novelty.py
git commit -m "feat: add deterministic novelty similarity evidence"
```

---

### Task 2: NoveltyPack ranking, distinctive terms and review prompts

**Files:**
- Modify: `src/question_radar/novelty.py`
- Modify: `tests/test_novelty.py`

**Interfaces:**
- Produces: `NoveltyNeighbor`
- Produces: `NoveltyPack`
- Produces: `build_novelty_pack(candidate_question: str, nodes: list[QuestionNode], relations: list[QuestionRelation], limit: int = 5) -> NoveltyPack`

- [ ] **Step 1: Write failing ranking and tie-break tests**

```python
from question_radar.lineage import QuestionNode
from question_radar.novelty import build_novelty_pack


def node(node_id: str, question: str) -> QuestionNode:
    return QuestionNode(
        id=node_id,
        question=question,
        source="corpus",
        source_ref=None,
        created_at="2026-09-01T12:00:00-03:00",
    )


def test_neighbors_rank_by_score_then_id():
    nodes = [
        node("b", "¿Cómo usamos memoria organizacional?"),
        node("a", "¿Cómo usamos memoria institucional?"),
    ]
    pack = build_novelty_pack("¿Cómo usamos memoria?", nodes, [], limit=2)
    assert [neighbor.node.id for neighbor in pack.neighbors] == ["a", "b"]
```

- [ ] **Step 2: Write failing distinctive-token test**

```python
def test_distinctive_tokens_expose_residual_mechanism():
    nodes = [node("q1", "¿Cómo usamos memoria y trazabilidad?")]
    pack = build_novelty_pack(
        "¿Qué debería recordar una organización y qué debería olvidar por obsolescencia?",
        nodes,
        [],
        limit=1,
    )
    assert "olvidar" in pack.candidate_distinctive_tokens
    assert "obsolescencia" in pack.candidate_distinctive_tokens
```

- [ ] **Step 3: Write failing read-only semantic-boundary tests**

```python
def test_every_pack_requires_human_review():
    pack = build_novelty_pack("¿Qué debería recordar una organización?", [], [])
    assert pack.review_required is True


def test_challenge_prompt_requires_explicit_challenge_syntax():
    nodes = [node("q1", "¿Cómo usamos memoria?")]
    ordinary = build_novelty_pack("¿Cómo mejoramos la memoria?", nodes, [])
    challenged = build_novelty_pack("¿Y si olvidar fuera necesario para adaptarse?", nodes, [])
    assert "challenges_assumption" not in ordinary.possible_interpretations
    assert "challenges_assumption" in challenged.possible_interpretations
```

- [ ] **Step 4: Run focused tests and verify RED**

```bash
pytest tests/test_novelty.py -q
```

Expected: new tests fail because pack/ranking structures are missing.

- [ ] **Step 5: Implement pack structures and conservative heuristics**

Add:

```python
INTERPRETATIONS = (
    "already_represented",
    "refines_existing",
    "operationalizes_existing",
    "challenges_assumption",
    "possible_new_branch",
)

@dataclass(frozen=True, slots=True)
class NoveltyNeighbor:
    node: QuestionNode
    similarity: SimilarityEvidence
    lineage_degree: int

@dataclass(frozen=True, slots=True)
class NoveltyPack:
    novelty_version: str
    candidate_question: str
    neighbors: tuple[NoveltyNeighbor, ...]
    candidate_distinctive_tokens: tuple[str, ...]
    possible_interpretations: tuple[str, ...]
    review_required: bool
```

`build_novelty_pack` must calculate relation degree from explicit v0.4 edges but never modify scores using degree.

Implement spec thresholds exactly. Preserve interpretation order using `INTERPRETATIONS`.

- [ ] **Step 6: Run Task 2 tests and verify GREEN**

```bash
pytest tests/test_novelty.py -q
```

Expected: all novelty unit tests pass.

- [ ] **Step 7: Commit Task 2**

```bash
git add src/question_radar/novelty.py tests/test_novelty.py
git commit -m "feat: build corpus-relative novelty packs"
```

---

### Task 3: Batch candidates and provisional clustering

**Files:**
- Modify: `src/question_radar/novelty.py`
- Create: `src/question_radar/novelty_export.py`
- Create: `tests/test_novelty_export.py`

**Interfaces:**
- Produces: `CandidateQuestion`
- Produces: `PossibleCluster`
- Produces: `cluster_candidates(candidates: tuple[CandidateQuestion, ...], threshold: float = 0.35) -> tuple[PossibleCluster, ...]`
- Produces: `load_candidate_questions(path: str | Path) -> tuple[CandidateQuestion, ...]`

- [ ] **Step 1: Write failing JSONL validation tests**

```python
import json
import pytest
from question_radar.novelty_export import load_candidate_questions


def test_candidate_jsonl_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "candidates.jsonl"
    path.write_text(
        '\n'.join([
            json.dumps({"id": "q1", "question": "¿Qué recordar?"}),
            json.dumps({"id": "q1", "question": "¿Qué olvidar?"}),
        ]),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate candidate id: q1"):
        load_candidate_questions(path)
```

Also test malformed JSON, unknown fields, blank IDs and blank questions.

- [ ] **Step 2: Run export tests and verify RED**

```bash
pytest tests/test_novelty_export.py -q
```

Expected: import failure because `novelty_export.py` does not exist.

- [ ] **Step 3: Implement strict candidate loader**

Use:

```python
@dataclass(frozen=True, slots=True)
class CandidateQuestion:
    id: str
    question: str
```

Only fields `id` and `question` are accepted.

- [ ] **Step 4: Write failing clustering tests**

```python
from question_radar.novelty import CandidateQuestion, cluster_candidates


def test_related_forgetting_questions_form_possible_cluster():
    candidates = (
        CandidateQuestion("q8", "¿Cómo distinguimos conocimiento válido de conocimiento obsoleto?"),
        CandidateQuestion("q9", "¿Puede una documentación conservar procedimientos obsoletos?"),
        CandidateQuestion("q25", "¿Y si olvidar prácticas anteriores ayudara a adaptarse?"),
        CandidateQuestion("qx", "¿Cómo calibramos un sensor satelital?"),
    )
    clusters = cluster_candidates(candidates, threshold=0.20)
    assert any(set(cluster.question_ids) >= {"q8", "q9"} for cluster in clusters)
```

Add deterministic connected-component ordering and no-singleton tests.

- [ ] **Step 5: Run focused tests and verify RED**

```bash
pytest tests/test_novelty_export.py -q
```

Expected: loader tests pass; cluster tests fail until clustering is implemented.

- [ ] **Step 6: Implement `PossibleCluster` and deterministic connected components**

```python
@dataclass(frozen=True, slots=True)
class PossibleCluster:
    cluster_id: str
    question_ids: tuple[str, ...]
    shared_tokens: tuple[str, ...]
```

For each connected component of size >= 2, `cluster_id` is `cluster-` + lexicographically smallest question ID. Sort question IDs and clusters lexicographically.

- [ ] **Step 7: Run Task 3 tests and verify GREEN**

```bash
pytest tests/test_novelty_export.py -q
```

Expected: all loader and clustering tests pass.

- [ ] **Step 8: Commit Task 3**

```bash
git add src/question_radar/novelty.py src/question_radar/novelty_export.py tests/test_novelty_export.py
git commit -m "feat: add novelty batch clustering"
```

---

### Task 4: Deterministic rendering and CLI read-only commands

**Files:**
- Modify: `src/question_radar/novelty_export.py`
- Modify: `src/question_radar/cli.py`
- Create: `tests/test_novelty_cli.py`

**Interfaces:**
- Produces: `render_novelty_markdown(pack: NoveltyPack) -> str`
- Produces: `render_novelty_json(pack: NoveltyPack) -> str`
- Produces: `render_batch_markdown(...) -> str`
- Produces: `render_batch_json(...) -> str`
- CLI: `question-radar novelty compare QUESTION --limit N --format markdown|json`
- CLI: `question-radar novelty batch INPUT --format markdown|json`

- [ ] **Step 1: Write failing renderer tests**

Verify Markdown contains exactly the required section headings and the boundary sentence:

```text
No lineage relation or master promotion was created.
```

Verify JSON parses, uses `novelty_version == "v0.5"`, has `review_required == true`, is deterministic across repeated rendering, and ends with `\n`.

- [ ] **Step 2: Run renderer tests and verify RED**

```bash
pytest tests/test_novelty_cli.py -q
```

Expected: render functions/CLI namespace missing.

- [ ] **Step 3: Implement deterministic renderers**

Follow existing `context_pack.py` rendering conventions: pure functions, `ensure_ascii=False`, `indent=2`, `sort_keys=True`, trailing newline.

- [ ] **Step 4: Add CLI parser and command tests**

Use a temporary SQLite database populated only with v0.4 nodes/relations. Tests must invoke `cli.main([...])` or the existing CLI testing pattern and assert compare output contains nearest corpus questions.

- [ ] **Step 5: Add database non-mutation regression**

Before CLI analysis:

```python
before = db_path.read_bytes()
```

After the command:

```python
assert db_path.read_bytes() == before
```

Run for both `compare` and `batch`.

- [ ] **Step 6: Implement CLI handlers without insert/update calls**

The compare handler may call only `QuestionLineageStore.list_nodes()` and `list_relations()` before pure analysis/rendering.

The batch handler may read candidate JSONL and corpus state but must perform no store writes.

- [ ] **Step 7: Run Task 4 tests and verify GREEN**

```bash
pytest tests/test_novelty_cli.py -q
```

Expected: all CLI/render/read-only tests pass.

- [ ] **Step 8: Commit Task 4**

```bash
git add src/question_radar/novelty_export.py src/question_radar/cli.py tests/test_novelty_cli.py
git commit -m "feat: expose read-only novelty CLI"
```

---

### Task 5: Blind benchmark regression corpus

**Files:**
- Create: `corpus/blind-memory-2026-09-01.jsonl`
- Create: `tests/test_novelty_benchmarks.py`
- Modify: `corpus/README.md`

**Interfaces:**
- Corpus records use exactly `{ "id": str, "question": str }`.
- Regression tests consume public v0.5 functions only.

- [ ] **Step 1: Add the frozen 25-question memory benchmark**

Use IDs `memory-blind-2026-09-01-001` through `memory-blind-2026-09-01-025` and preserve the original wording exactly.

- [ ] **Step 2: Write regression tests that avoid semantic overclaiming**

Tests must assert evidence-level properties only. Examples:

```python
def test_memory_benchmark_preserves_forgetting_residual_terms():
    ...
    assert {"olvidar", "practicas"}.intersection(pack.candidate_distinctive_tokens)


def test_memory_benchmark_batch_exposes_more_than_one_possible_cluster():
    ...
    assert any(len(cluster.question_ids) >= 2 for cluster in clusters)
```

Do not assert that Q25 is “truly novel” or that a specific v0.4 semantic edge is correct.

- [ ] **Step 3: Run benchmark regressions and verify GREEN**

```bash
pytest tests/test_novelty_benchmarks.py -q
```

- [ ] **Step 4: Document corpus provenance**

Add a `corpus/README.md` entry stating that the benchmark was generated blind in a separate chat and is calibration evidence, not canonical lineage.

- [ ] **Step 5: Commit Task 5**

```bash
git add corpus/blind-memory-2026-09-01.jsonl corpus/README.md tests/test_novelty_benchmarks.py
git commit -m "data: add blind memory novelty benchmark"
```

---

### Task 6: README, compatibility and full verification

**Files:**
- Modify: `README.md`

**Interfaces:**
- Public user-facing contract must describe v0.5 as evidence retrieval plus human review.

- [ ] **Step 1: Update README version and pipeline diagram**

Change current version text to:

```text
Version: v0.5 · Corpus-Relative Novelty + v0.4 Question Lineage
```

Extend the workflow with:

```text
candidate question
     ↓
corpus-relative evidence
     ↓
human-reviewed semantic relation
```

Explicitly state that v0.5 uses lexical evidence rather than embeddings and does not infer semantic truth.

- [ ] **Step 2: Run all novelty tests**

```bash
pytest tests/test_novelty.py tests/test_novelty_export.py tests/test_novelty_cli.py tests/test_novelty_benchmarks.py -q
```

Expected: all pass.

- [ ] **Step 3: Run full historical + new suite**

```bash
pytest -q
```

Expected: zero failures.

- [ ] **Step 4: Verify CLI help**

```bash
question-radar novelty --help
question-radar novelty compare --help
question-radar novelty batch --help
```

Expected: all commands exit 0 and show the documented arguments.

- [ ] **Step 5: Verify no runtime dependency was added**

```bash
python - <<'PY'
import tomllib
from pathlib import Path
p = tomllib.loads(Path('pyproject.toml').read_text())
assert p['project']['dependencies'] == []
print('runtime dependencies: []')
PY
```

- [ ] **Step 6: Commit README**

```bash
git add README.md
git commit -m "docs: document corpus-relative novelty v0.5"
```

- [ ] **Step 7: Review branch diff against main**

```bash
git diff --check main...HEAD
git diff --stat main...HEAD
git log --oneline main..HEAD
```

Expected: no whitespace errors; only v0.5 files/docs/benchmark changes.

- [ ] **Step 8: Push branch and open draft PR**

PR title:

```text
feat: add corpus-relative novelty v0.5
```

PR body must include:

- why the two blind benchmarks motivated v0.5;
- deterministic lexical retrieval design;
- distinctive-token and cluster evidence;
- explicit human-review boundary;
- verification command and observed test count;
- statement that no v0.1–v0.4 contracts changed.
